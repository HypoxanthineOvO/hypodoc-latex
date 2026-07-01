from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
README = PROJECT_ROOT / "README.md"
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"
GITIGNORE = PROJECT_ROOT / ".gitignore"

PUBLIC_THEME_IDS = (
    "plain",
    "classic-readable",
    "tech-minimal",
    "warm-handbook",
    "academic-clean",
)
TEX_THEME_FILES = tuple(f"hypolatex-theme-{theme_id}.sty" for theme_id in PUBLIC_THEME_IDS)

PUBLIC_RELEASE_SCAN_TARGETS = (
    "README.md",
    "CHANGELOG.md",
    "docs",
    "skill",
    "src",
    "scripts",
    "pyproject.toml",
    "examples",
    "spec",
    ".gitmodules",
)
PUBLIC_TEXT_SUFFIXES = {
    ".bib",
    ".cls",
    ".json",
    ".lua",
    ".md",
    ".py",
    ".rst",
    ".sh",
    ".sty",
    ".tex",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
PRIVATE_OR_LOCAL_MARKERS = (
    "/" + "home" + "/" + "heyx",
    "Hypo" + "-Courses",
    "Hypo" + "-Writer",
    "SI" + "100B",
)


def _load_pyproject() -> dict[str, Any]:
    with PYPROJECT.open("rb") as pyproject_file:
        return tomllib.load(pyproject_file)


def _read(path: Path) -> str:
    assert path.is_file(), f"Expected release hygiene file to exist: {path}"
    return path.read_text(encoding="utf-8")


def _normalized_path(value: str) -> str:
    return value.replace("\\", "/").strip().strip("/")


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _project_table() -> dict[str, Any]:
    pyproject = _load_pyproject()
    project = pyproject.get("project")
    assert isinstance(project, dict), "pyproject.toml must define [project] metadata."
    return project


def _hatch_target(target_name: str) -> dict[str, Any]:
    pyproject = _load_pyproject()
    target = (
        pyproject.get("tool", {})
        .get("hatch", {})
        .get("build", {})
        .get("targets", {})
        .get(target_name)
    )
    assert isinstance(target, dict), (
        f"pyproject.toml must define [tool.hatch.build.targets.{target_name}]."
    )
    return target


def _path_pattern_mentions(pattern: str, fragment: str) -> bool:
    return _normalized_path(fragment).casefold() in _normalized_path(pattern).casefold()


def _path_covers(configured: str, required: str) -> bool:
    configured_path = _normalized_path(configured)
    required_path = _normalized_path(required)
    return configured_path == required_path or required_path.startswith(
        configured_path.rstrip("/") + "/"
    )


def _section_containing(text: str, marker: str) -> str:
    marker_match = re.search(rf"(?im)^##+\s+.*{re.escape(marker)}.*$", text)
    assert marker_match, f"CHANGELOG.md must contain a section heading for {marker}."

    body_start = marker_match.start()
    next_heading = re.search(r"(?m)^##\s+", text[marker_match.end() :])
    body_end = (
        marker_match.end() + next_heading.start()
        if next_heading is not None
        else len(text)
    )
    return text[body_start:body_end]


def _has_cjk_body(text: str, minimum_chars: int = 20) -> bool:
    return len(re.findall(r"[\u4e00-\u9fff]", text)) >= minimum_chars


def _iter_public_release_text_files() -> list[Path]:
    paths: list[Path] = []
    for target in PUBLIC_RELEASE_SCAN_TARGETS:
        root = PROJECT_ROOT / target
        if not root.exists():
            continue
        if root.is_file():
            paths.append(root)
            continue
        for path in root.rglob("*"):
            if (
                path.is_file()
                and path.suffix.casefold() in PUBLIC_TEXT_SUFFIXES
                and ".git" not in path.parts
            ):
                paths.append(path)
    return paths


def test_changelog_v010_is_truthful_chinese_release_asset_contract():
    text = _read(CHANGELOG)
    section = _section_containing(text, "v0.1.0")
    normalized = re.sub(r"\s+", " ", section.casefold())

    assert _has_cjk_body(section), "v0.1.0 changelog notes should have a Chinese body."
    for label, markers in {
        "wheel": ("wheel", ".whl"),
        "sdist": ("sdist", "source distribution", ".tar.gz"),
        "handbook": ("handbook", "手册"),
        "quickstart": ("quickstart", "快速开始"),
    }.items():
        assert any(marker in normalized for marker in markers), (
            "v0.1.0 changelog must describe the local release asset scope; "
            f"missing {label} marker."
        )

    has_explicit_unpublished_status = (
        re.search(r"(尚未|未|没有|不).{0,20}(ctan|pypi).{0,24}(ctan|pypi)", normalized)
        or re.search(
            r"(not published|not yet published|not uploaded).{0,24}(ctan|pypi)",
            normalized,
        )
    )
    assert has_explicit_unpublished_status, (
        "CHANGELOG.md must make the release status truthful: local assets only, "
        "with no claim that CTAN/PyPI publication has already happened."
    )
    assert not re.search(r"(已|已经).{0,8}(发布|上传).{0,24}(ctan|pypi)", normalized), (
        "CHANGELOG.md must not claim CTAN/PyPI publication has already happened."
    )


def test_pyproject_description_identifies_public_renderer_domain():
    project = _project_table()
    description = str(project.get("description", "")).strip()

    assert description, "pyproject.toml must define a project description."
    assert description.casefold() != "hypo-latex command line tools", (
        "Project description should explain the HypoDoc/LaTeX/PDF renderer "
        "surface, not the generic command-line-tool placeholder."
    )
    assert any(marker in description.casefold() for marker in ("hypodoc", "latex", "pdf")), (
        "Project description should identify the public renderer/domain."
    )


def test_pyproject_has_readme_and_license_metadata():
    project = _project_table()

    assert project.get("readme"), "pyproject.toml must publish README metadata."

    license_value = project.get("license")
    license_files = project.get("license-files")
    has_license_metadata = bool(license_value) or bool(license_files)
    assert has_license_metadata, (
        "pyproject.toml must define license metadata, e.g. license text/file "
        "or license-files pointing at LICENSE."
    )


def test_sdist_rules_keep_private_local_artifacts_out_and_public_resources_in():
    sdist = _hatch_target("sdist")
    include_patterns = _as_string_list(sdist.get("include"))
    exclude_patterns = (
        _as_string_list(sdist.get("exclude"))
        + _as_string_list(sdist.get("artifacts"))
    )

    assert any(_path_pattern_mentions(pattern, "src") for pattern in include_patterns), (
        "sdist must include package source files."
    )
    assert any(_path_pattern_mentions(pattern, "tex") for pattern in include_patterns), (
        "sdist must include LaTeX runtime resources."
    )
    assert any(_path_pattern_mentions(pattern, "themes") for pattern in include_patterns), (
        "sdist must include theme resources."
    )
    assert any(_path_pattern_mentions(pattern, "tests") for pattern in include_patterns), (
        "sdist should retain public tests or an equivalent public test include rule."
    )

    forbidden_direct_includes = [
        pattern
        for pattern in include_patterns
        if any(
            _path_pattern_mentions(pattern, forbidden)
            for forbidden in ("tests/private", "tests/private_corpus.toml")
        )
    ]
    assert not forbidden_direct_includes, (
        "sdist include rules must not directly include private corpus paths: "
        f"{forbidden_direct_includes}"
    )

    required_exclusions = {
        "tests/private/**": ("tests/private",),
        "tests/private_corpus.toml": ("tests/private_corpus.toml",),
    }
    missing_exclusions = [
        label
        for label, fragments in required_exclusions.items()
        if not any(
            _path_pattern_mentions(pattern, fragment)
            for pattern in exclude_patterns
            for fragment in fragments
        )
    ]
    assert not missing_exclusions, (
        "sdist must explicitly exclude private/local/generated artifacts. "
        f"Missing exclusion coverage for: {missing_exclusions}"
    )


def test_wheel_force_include_covers_latex_runtime_and_public_theme_files():
    wheel = _hatch_target("wheel")
    force_include = wheel.get("force-include")
    assert isinstance(force_include, dict), (
        "wheel target must define force-include for non-Python runtime resources."
    )

    def covers(source_fragment: str, destination_fragment: str) -> bool:
        return any(
            _path_covers(source, source_fragment)
            and _path_covers(destination, destination_fragment)
            for source, destination in force_include.items()
            if isinstance(source, str) and isinstance(destination, str)
        )

    assert covers("tex/latex/hypolatex", "hypolatex/tex/latex/hypolatex"), (
        "wheel force-include must package the Hypo-LaTeX LaTeX runtime tree."
    )
    tex_runtime_source = next(
        (
            Path(source)
            for source, destination in force_include.items()
            if isinstance(source, str)
            and isinstance(destination, str)
            and _path_covers(source, "tex/latex/hypolatex")
        ),
        None,
    )
    assert tex_runtime_source is not None
    runtime_root = PROJECT_ROOT / tex_runtime_source
    missing_theme_files = [
        theme_file for theme_file in TEX_THEME_FILES if not (runtime_root / theme_file).is_file()
    ]
    assert not missing_theme_files, (
        "wheel force-include must cover the TeX runtime tree containing every "
        f"public theme .sty file. Missing: {missing_theme_files}"
    )


def test_gitignore_keeps_local_build_outputs_untracked():
    text = _read(GITIGNORE)
    ignored_patterns = {
        _normalized_path(line)
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "dist" in ignored_patterns or "dist/" in ignored_patterns, (
        "dist/ must be ignored so local release artifacts are not committed."
    )
    assert "build" in ignored_patterns or "build/" in ignored_patterns, (
        "build/ must be ignored so local build outputs are not committed."
    )


def test_public_release_surface_has_no_local_paths_or_private_project_names():
    leaked: list[str] = []
    for path in _iter_public_release_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        normalized = text.casefold()
        for marker in PRIVATE_OR_LOCAL_MARKERS:
            if marker.casefold() in normalized:
                leaked.append(f"{path.relative_to(PROJECT_ROOT)}: {marker}")

    assert not leaked, (
        "Public release-facing files must not leak local absolute paths or "
        f"private project names. Found: {leaked}"
    )
