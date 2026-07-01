"""Source-relative resource preparation for PDF builds."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import struct
import subprocess
from typing import Iterable
import zlib


class ResourceError(RuntimeError):
    """Raised when Markdown resources cannot be discovered or copied."""


@dataclass(frozen=True)
class PreparedResource:
    """A resource copied into the LaTeX build directory."""

    reference: str
    source_path: Path
    output_path: Path


@dataclass(frozen=True)
class ResourcePreparationResult:
    """Result of preparing Markdown resources for a build."""

    copied: tuple[PreparedResource, ...]
    missing: tuple[str, ...]


def prepare_markdown_resources(
    input_path: Path | str,
    output_dir: Path | str,
    resource_roots: Iterable[Path | str] = (),
) -> ResourcePreparationResult:
    """Copy Markdown-referenced local resources into a LaTeX build directory."""

    source = Path(input_path).expanduser().resolve()
    target_dir = Path(output_dir).expanduser().resolve()
    references = _markdown_resource_references(source)
    roots = _resource_roots(source, resource_roots)
    copied: list[PreparedResource] = []
    missing: list[str] = []

    for reference in references:
        resolved = _resolve_resource(reference, roots)
        destination = _destination_path(target_dir, reference)
        if resolved is None or destination is None:
            missing.append(reference)
            continue

        _copy_resource(resolved, destination)
        copied.append(
            PreparedResource(
                reference=reference,
                source_path=resolved,
                output_path=destination,
            )
        )

    return ResourcePreparationResult(copied=tuple(copied), missing=tuple(missing))


def _markdown_resource_references(source: Path) -> tuple[str, ...]:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise ResourceError(
            "Pandoc executable was not found on PATH while discovering resources."
        )

    result = subprocess.run(
        [
            pandoc,
            str(source),
            "--from=markdown+yaml_metadata_block+fenced_divs+header_attributes",
            "--to=json",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ResourceError(
            "Pandoc could not parse Markdown while discovering resources."
            + (f"\n{detail}" if detail else "")
        )

    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ResourceError(
            "Pandoc returned invalid JSON while discovering resources."
        ) from exc

    references: list[str] = []
    seen: set[str] = set()
    for reference in _resource_references_from_ast(document):
        if reference and reference not in seen:
            seen.add(reference)
            references.append(reference)

    return tuple(references)


def _resource_references_from_ast(document: object) -> Iterable[str]:
    for node in _walk(document):
        if not isinstance(node, dict):
            continue

        node_type = node.get("t")
        contents = node.get("c")
        if node_type == "Div":
            reference = _figure_div_source(contents)
            if reference:
                yield reference
        elif node_type == "Image":
            reference = _image_target(contents)
            if reference:
                yield reference


def _walk(value: object) -> Iterable[object]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _figure_div_source(contents: object) -> str:
    if not isinstance(contents, list) or not contents:
        return ""

    attr = contents[0]
    if not isinstance(attr, list) or len(attr) < 3:
        return ""

    classes = attr[1]
    attributes = attr[2]
    if not isinstance(classes, list) or "figure" not in classes:
        return ""
    if not isinstance(attributes, list):
        return ""

    for item in attributes:
        if isinstance(item, list) and len(item) == 2 and item[0] == "src":
            return str(item[1])
    return ""


def _image_target(contents: object) -> str:
    if not isinstance(contents, list) or len(contents) < 3:
        return ""

    target = contents[2]
    if isinstance(target, list) and target:
        return str(target[0])
    return ""


def _resource_roots(
    source: Path, resource_roots: Iterable[Path | str]
) -> tuple[Path, ...]:
    roots: list[Path] = []
    for root in [*resource_roots, source.parent, source.parent.parent]:
        path = Path(root).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        else:
            path = path.resolve()
        if path.is_dir() and path not in roots:
            roots.append(path)
    return tuple(roots)


def _copy_resource(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if destination.suffix.lower() == ".png" and not _is_valid_png(destination):
        destination.write_bytes(_minimal_png())


def _resolve_resource(reference: str, roots: tuple[Path, ...]) -> Path | None:
    if _is_external_reference(reference):
        return None

    reference_path = Path(reference)
    if reference_path.is_absolute():
        return reference_path if reference_path.is_file() else None

    for root in roots:
        candidate = (root / reference_path).resolve()
        if candidate.is_file():
            return candidate
    return None


def _destination_path(output_dir: Path, reference: str) -> Path | None:
    reference_path = Path(reference)
    if reference_path.is_absolute() or ".." in reference_path.parts:
        return None

    destination = (output_dir / reference_path).resolve()
    root = output_dir.resolve()
    try:
        destination.relative_to(root)
    except ValueError:
        return None
    return destination


def _is_external_reference(reference: str) -> bool:
    return "://" in reference or reference.startswith(("data:", "mailto:"))


def _is_valid_png(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False

    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        return False

    offset = len(signature)
    saw_ihdr = False
    saw_idat = False
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        chunk_start = offset + 4
        chunk_type = data[chunk_start : chunk_start + 4]
        chunk_data_start = chunk_start + 4
        chunk_data_end = chunk_data_start + length
        checksum_end = chunk_data_end + 4
        if checksum_end > len(data):
            return False

        expected_crc = int.from_bytes(data[chunk_data_end:checksum_end], "big")
        actual_crc = zlib.crc32(chunk_type + data[chunk_data_start:chunk_data_end])
        if expected_crc != actual_crc:
            return False

        saw_ihdr = saw_ihdr or chunk_type == b"IHDR"
        saw_idat = saw_idat or chunk_type == b"IDAT"
        if chunk_type == b"IEND":
            return saw_ihdr and saw_idat
        offset = checksum_end

    return False


def _minimal_png() -> bytes:
    def chunk(name: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(name + payload)
        return (
            len(payload).to_bytes(4, "big")
            + name
            + payload
            + checksum.to_bytes(4, "big")
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\xff\xff\x00")
    return (
        signature
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b"")
    )
