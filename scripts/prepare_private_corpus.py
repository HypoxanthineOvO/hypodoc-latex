#!/usr/bin/env python3
"""Prepare local private corpus samples for Hypo-LaTeX tests."""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "tests" / "private_corpus.toml"
PRIVATE_TEST_ROOT = (REPO_ROOT / "tests" / "private").resolve(strict=False)


class CorpusError(Exception):
    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class SourceSpec:
    name: str
    family: str
    paths: tuple[str, ...]
    manifest_dir: Path

    def resolved_paths(self) -> tuple[Path, ...]:
        return tuple(_resolve_user_path(raw, self.manifest_dir) for raw in self.paths)


@dataclass(frozen=True)
class ProfileSpec:
    name: str
    glob: str
    limit: int
    kind: str = "markdown"


@dataclass(frozen=True)
class Manifest:
    path: Path
    sources: dict[str, SourceSpec]
    profiles: dict[str, ProfileSpec]
    default_profile: str | None = None


@dataclass(frozen=True)
class ResolvedSource:
    name: str
    family: str
    root: Path
    checked_paths: tuple[Path, ...]


def load_manifest(manifest_path: str | Path) -> Manifest:
    path = _resolve_user_path(str(manifest_path), Path.cwd())
    if not path.exists():
        raise CorpusError(f"manifest not found: {path}", exit_code=2)

    try:
        with path.open("rb") as manifest_file:
            data = tomllib.load(manifest_file)
    except tomllib.TOMLDecodeError as exc:
        raise CorpusError(f"invalid TOML manifest {path}: {exc}", exit_code=2) from exc
    except OSError as exc:
        raise CorpusError(f"could not read manifest {path}: {exc}", exit_code=2) from exc

    manifest_dir = path.parent
    sources = _parse_sources(data.get("sources"), manifest_dir)
    profiles = _parse_profiles(data.get("profiles"))
    default_profile = _parse_default_profile(data.get("defaults"))
    if default_profile is not None and default_profile not in profiles:
        raise CorpusError(
            f"default profile '{default_profile}' is not defined in {path}",
            exit_code=2,
        )

    return Manifest(
        path=path,
        sources=sources,
        profiles=profiles,
        default_profile=default_profile,
    )


def command_list(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    print(f"manifest: {manifest.path}")
    print("sources:")
    for source in manifest.sources.values():
        print(f"  {source.name} ({source.family})")
        for candidate in source.resolved_paths():
            status = "exists" if candidate.exists() else "missing"
            print(f"    - {candidate} [{status}]")

    print("profiles:")
    for profile in manifest.profiles.values():
        default = " default" if profile.name == manifest.default_profile else ""
        print(
            f"  {profile.name}{default}: kind={profile.kind} "
            f"glob={profile.glob!r} limit={profile.limit}"
        )
    return 0


def command_check(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    if args.profile:
        _select_profile(manifest, args.profile)

    sources = _select_sources_for_check(manifest, args.source)
    missing: list[str] = []
    for source in sources:
        if source.root.exists():
            print(f"ok: source '{source.name}' -> {source.root}")
            continue
        lines = [
            f"missing source '{source.name}' ({source.family}); checked paths:",
            *[f"  - {candidate}" for candidate in source.checked_paths],
        ]
        missing.append("\n".join(lines))

    if missing:
        print("\n\n".join(missing), file=sys.stderr)
        return 1
    return 0


def command_prepare(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    profile = _select_profile(manifest, args.profile)
    source = _select_source_for_prepare(manifest, args.source)
    output_root = _resolve_output_root(args.out)
    if not source.root.exists():
        checked = "\n".join(f"  - {candidate}" for candidate in source.checked_paths)
        raise CorpusError(
            f"missing source '{source.name}' ({source.family}); checked paths:\n{checked}",
            exit_code=1,
        )
    if not source.root.is_file() and not source.root.is_dir():
        raise CorpusError(
            f"source '{source.name}' is not a file or directory: {source.root}",
            exit_code=1,
        )

    matched_files = list(_iter_profile_files(source.root, profile))
    if not matched_files:
        raise CorpusError(
            f"no files matched profile '{profile.name}' ({profile.glob}) in {source.root}",
            exit_code=1,
        )

    output_root.mkdir(parents=True, exist_ok=True)
    materialized: list[Path] = []
    for index, source_file in enumerate(matched_files[: profile.limit], start=1):
        destination = output_root / _sample_filename(index, source_file)
        shutil.copyfile(source_file, destination)
        materialized.append(destination)

    print(
        f"prepared {len(materialized)} sample(s) from source '{source.name}' "
        f"with profile '{profile.name}'"
    )
    print(f"output: {output_root}")
    for path in materialized:
        print(f"  - {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare local private corpus samples for Hypo-LaTeX tests.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List manifest sources and profiles.")
    _add_manifest_arg(list_parser)
    list_parser.set_defaults(func=command_list)

    check_parser = subparsers.add_parser("check", help="Check that configured sources exist.")
    _add_manifest_arg(check_parser)
    check_parser.add_argument("--source", help="Source name from the manifest, or a path.")
    check_parser.add_argument("--profile", help="Validate that this profile exists.")
    check_parser.set_defaults(func=command_check)

    prepare_parser = subparsers.add_parser(
        "prepare",
        help="Materialize private samples under tests/private/.",
    )
    _add_manifest_arg(prepare_parser)
    prepare_parser.add_argument("--source", help="Source name from the manifest, or a path.")
    prepare_parser.add_argument("--profile", help="Profile name to materialize.")
    prepare_parser.add_argument(
        "--out",
        required=True,
        help="Output directory. Must resolve under tests/private/ in this repo.",
    )
    prepare_parser.set_defaults(func=command_prepare)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CorpusError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code


def _add_manifest_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help=f"Path to private corpus manifest. Default: {DEFAULT_MANIFEST}",
    )


def _parse_sources(raw_sources: Any, manifest_dir: Path) -> dict[str, SourceSpec]:
    if raw_sources is None:
        raise CorpusError("manifest must define at least one source", exit_code=2)

    sources: dict[str, SourceSpec] = {}
    items: list[tuple[str | None, Any]]
    if isinstance(raw_sources, dict):
        items = [(name, value) for name, value in raw_sources.items()]
    elif isinstance(raw_sources, list):
        items = [(None, value) for value in raw_sources]
    else:
        raise CorpusError("manifest 'sources' must be a table or array", exit_code=2)

    for table_name, value in items:
        if not isinstance(value, dict):
            raise CorpusError("each source entry must be a table", exit_code=2)
        name = str(value.get("name") or table_name or "").strip()
        if not name:
            raise CorpusError("each source must have a name", exit_code=2)
        family = str(value.get("family") or name).strip()
        paths = _coerce_paths(value)
        if not paths:
            raise CorpusError(f"source '{name}' must define path candidates", exit_code=2)
        sources[name] = SourceSpec(
            name=name,
            family=family,
            paths=tuple(paths),
            manifest_dir=manifest_dir,
        )

    if not sources:
        raise CorpusError("manifest must define at least one source", exit_code=2)
    return sources


def _parse_profiles(raw_profiles: Any) -> dict[str, ProfileSpec]:
    if raw_profiles is None:
        raise CorpusError("manifest must define at least one profile", exit_code=2)

    profiles: dict[str, ProfileSpec] = {}
    items: list[tuple[str | None, Any]]
    if isinstance(raw_profiles, dict):
        items = [(name, value) for name, value in raw_profiles.items()]
    elif isinstance(raw_profiles, list):
        items = [(None, value) for value in raw_profiles]
    else:
        raise CorpusError("manifest 'profiles' must be a table or array", exit_code=2)

    for table_name, value in items:
        if not isinstance(value, dict):
            raise CorpusError("each profile entry must be a table", exit_code=2)
        name = str(value.get("name") or table_name or "").strip()
        if not name:
            raise CorpusError("each profile must have a name", exit_code=2)
        glob = str(value.get("glob") or value.get("pattern") or "**/*.md").strip()
        kind = str(value.get("kind") or "markdown").strip()
        limit = int(value.get("limit") or 1)
        if limit < 1:
            raise CorpusError(f"profile '{name}' limit must be at least 1", exit_code=2)
        profiles[name] = ProfileSpec(name=name, glob=glob, limit=limit, kind=kind)

    if not profiles:
        raise CorpusError("manifest must define at least one profile", exit_code=2)
    return profiles


def _parse_default_profile(raw_defaults: Any) -> str | None:
    if not isinstance(raw_defaults, dict):
        return None
    profile = raw_defaults.get("profile")
    return str(profile).strip() if profile else None


def _coerce_paths(source: dict[str, Any]) -> list[str]:
    raw_paths = (
        source.get("paths")
        or source.get("candidates")
        or source.get("candidate_paths")
        or source.get("path")
    )
    if raw_paths is None:
        return []
    if isinstance(raw_paths, str):
        return [raw_paths]
    if isinstance(raw_paths, list):
        return [str(path) for path in raw_paths if str(path).strip()]
    raise CorpusError("source paths must be a string or list of strings", exit_code=2)


def _select_profile(manifest: Manifest, requested: str | None) -> ProfileSpec:
    if requested:
        profile = manifest.profiles.get(requested)
        if profile is None:
            names = ", ".join(sorted(manifest.profiles))
            raise CorpusError(f"unknown profile '{requested}'. Available profiles: {names}")
        return profile

    if manifest.default_profile:
        return manifest.profiles[manifest.default_profile]
    return next(iter(manifest.profiles.values()))


def _select_sources_for_check(
    manifest: Manifest,
    requested: str | None,
) -> list[ResolvedSource]:
    if requested:
        return [_resolve_source_arg(manifest, requested)]
    return [_resolve_named_source(source) for source in manifest.sources.values()]


def _select_source_for_prepare(manifest: Manifest, requested: str | None) -> ResolvedSource:
    if requested:
        return _resolve_source_arg(manifest, requested)

    for source in manifest.sources.values():
        resolved = _resolve_named_source(source)
        if resolved.root.exists():
            return resolved
    return _resolve_named_source(next(iter(manifest.sources.values())))


def _resolve_source_arg(manifest: Manifest, source_arg: str) -> ResolvedSource:
    if source_arg in manifest.sources:
        return _resolve_named_source(manifest.sources[source_arg])
    if _is_path_like(source_arg):
        root = _resolve_user_path(source_arg, Path.cwd())
        return ResolvedSource(
            name=root.stem or "source",
            family="direct",
            root=root,
            checked_paths=(root,),
        )
    names = ", ".join(sorted(manifest.sources))
    raise CorpusError(f"unknown source '{source_arg}'. Available sources: {names}")


def _resolve_named_source(source: SourceSpec) -> ResolvedSource:
    checked_paths = _dedupe_paths(source.resolved_paths())
    existing = next((candidate for candidate in checked_paths if candidate.exists()), None)
    return ResolvedSource(
        name=source.name,
        family=source.family,
        root=existing or checked_paths[0],
        checked_paths=checked_paths,
    )


def _resolve_output_root(out: str) -> Path:
    output_root = _resolve_user_path(out, REPO_ROOT)
    if not _is_relative_to(output_root, PRIVATE_TEST_ROOT):
        raise CorpusError(
            "prepare output must be under "
            f"{PRIVATE_TEST_ROOT}; refusing path: {output_root}",
            exit_code=2,
        )
    return output_root


def _iter_profile_files(source_root: Path, profile: ProfileSpec):
    if source_root.is_file():
        if _matches_profile(source_root, profile):
            yield source_root
        return

    candidates = set(source_root.glob(profile.glob))
    if "/" not in profile.glob and "\\" not in profile.glob:
        candidates.update(source_root.rglob(profile.glob))

    for candidate in sorted(candidates):
        if candidate.is_file() and _matches_profile(candidate, profile):
            yield candidate


def _matches_profile(path: Path, profile: ProfileSpec) -> bool:
    if not fnmatch.fnmatch(path.name, profile.glob) and not fnmatch.fnmatch(
        str(path),
        profile.glob,
    ):
        if profile.glob.startswith("**/") and fnmatch.fnmatch(
            path.name,
            profile.glob[3:],
        ):
            return True
        return False
    if profile.kind == "markdown":
        return path.suffix.lower() in {".md", ".markdown"}
    return True


def _sample_filename(index: int, source_file: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", source_file.stem).strip(".-")
    stem = stem or "sample"
    suffix = source_file.suffix.lower() or ".md"
    return f"{index:03d}-{stem}{suffix}"


def _resolve_user_path(raw_path: str, base_dir: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(raw_path))
    path = Path(expanded)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve(strict=False)


def _is_path_like(value: str) -> bool:
    return (
        value.startswith((".", "~", os.sep))
        or "/" in value
        or "\\" in value
        or Path(value).exists()
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _dedupe_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return tuple(deduped)


if __name__ == "__main__":
    sys.exit(main())
