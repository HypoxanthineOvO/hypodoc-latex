from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHOWCASE_SOURCE = PROJECT_ROOT / "examples" / "showcase" / "hypolatex-showcase.md"
README = PROJECT_ROOT / "README.md"
BANNER_SCRIPT = PROJECT_ROOT / "scripts" / "release" / "render_showcase_banner.sh"
BANNER_IMAGE = PROJECT_ROOT / "assets" / "readme" / "showcase-banner.png"
MIN_PDF_BYTES = 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

SHOWCASE_REQUIRED_TOPICS = {
    "cover/theme visual system": (
        "cover",
        "封面",
        "theme",
        "主题视觉",
        "visual",
    ),
    "longform prose": ("longform", "长文", "教程", "narrative"),
    "semantic blocks": (":::", "semantic", "语义块", "task", "callout"),
    "Q-A/review questions": ("question", "answer", "q-a", "复习题", "问答"),
    "controlled tables": ("table", "受控表格", "columns:", "表格"),
    "figures/images": ("figure", "image", "图片", "图像", "src="),
    "theme contact sheet": (
        "contact sheet",
        "theme matrix",
        "主题总览",
        "classic-readable",
        "tech-minimal",
        "warm-handbook",
        "academic-clean",
    ),
}

PRIVATE_CORPUS_FORBIDDEN_MARKERS = (
    "/home/",
    "tests/private",
    "private corpus",
    "private_corpus",
    "corpus-" + "ai" + "-guide",
    "tutorial_1_01",
    "wed2025fall",
)

SHOWCASE_PDF_TEXT_MARKERS = (
    "hypo-latex",
    "classic-readable",
    "semantic",
    "question",
    "answer",
    "table",
)


def _read_required_file(path: Path) -> str:
    assert path.is_file(), f"Expected public showcase contract file to exist: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", text, re.DOTALL)
    assert match, "Showcase source must start with YAML frontmatter."
    return _parse_simple_yaml_mapping(match.group("body"))


def _parse_simple_yaml_mapping(frontmatter: str) -> dict[str, str]:
    data: dict[str, str] = {}
    current_block_key: str | None = None

    for line in frontmatter.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        key_match = re.match(r"^(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)$", line)
        if key_match:
            key = key_match.group("key")
            value = key_match.group("value").strip()
            current_block_key = key if value in {"|", ">"} else None
            data[key] = "" if current_block_key else value.strip("\"'")
            continue

        if current_block_key and line.startswith((" ", "\t")):
            data[current_block_key] = (
                f"{data[current_block_key]} {line.strip()}".strip()
            )

    return data


def _require_poppler_tool(name: str) -> str:
    tool = shutil.which(name)
    assert tool is not None, f"{name} is required for showcase PDF evidence tests."
    return tool


def _extract_pdf_text(pdf_path: Path) -> str:
    result = subprocess.run(
        [_require_poppler_tool("pdftotext"), str(pdf_path), "-"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return _normalized(result.stdout)


def test_showcase_source_exists_with_frontmatter_theme():
    from hypolatex import themes

    text = _read_required_file(SHOWCASE_SOURCE)
    frontmatter = _frontmatter(text)

    assert frontmatter.get("title"), "Showcase source must define a title."
    assert frontmatter.get("theme"), "Showcase source must define a theme."
    assert frontmatter["theme"] in themes.valid_theme_ids(), (
        "Showcase source must use a registered Hypo-LaTeX theme, got "
        f"{frontmatter['theme']!r}."
    )


def test_showcase_source_covers_public_rendering_features():
    text = _normalized(_read_required_file(SHOWCASE_SOURCE))

    missing_topics = [
        topic
        for topic, markers in SHOWCASE_REQUIRED_TOPICS.items()
        if not any(marker in text for marker in markers)
    ]
    assert not missing_topics, (
        "Showcase source must exercise the public PDF surface used by the "
        f"README banner. Missing topics: {missing_topics}"
    )


def test_showcase_banner_render_script_has_public_shell_contract():
    script = _read_required_file(BANNER_SCRIPT)
    first_line = script.splitlines()[0] if script.splitlines() else ""
    mode = BANNER_SCRIPT.stat().st_mode
    has_shell_entry = first_line.startswith("#!") and re.search(r"\b(?:ba)?sh\b", first_line)

    assert mode & stat.S_IXUSR or has_shell_entry, (
        "Banner render script must be executable or start with a clear sh/bash "
        "entry point."
    )
    assert "pdftoppm" in script, "Banner script must rasterize PDF pages with pdftoppm."
    assert "montage" in script or "convert" in script, (
        "Banner script must compose the README banner with ImageMagick montage "
        "or convert."
    )
    assert "assets/readme/showcase-banner.png" in script, (
        "Banner script must write the committed README banner asset."
    )


def test_showcase_banner_png_exists_and_is_non_empty():
    assert BANNER_IMAGE.is_file(), f"Expected README banner image: {BANNER_IMAGE}"
    assert BANNER_IMAGE.stat().st_size > len(PNG_MAGIC), "Banner PNG must be non-empty."
    assert BANNER_IMAGE.read_bytes().startswith(PNG_MAGIC), (
        "README banner must be a PNG file with valid PNG magic bytes."
    )


def test_readme_references_self_hosted_pdf_banner():
    text = _normalized(_read_required_file(README))

    assert "assets/readme/showcase-banner.png" in text, (
        "README must embed or link the committed showcase banner image."
    )
    assert "pdf" in text, "README must say the banner comes from the showcase PDF."
    assert any(marker in text for marker in ("render", "rendered", "screenshot", "渲染", "截图")), (
        "README must explain that the banner is derived from a real PDF render "
        "or screenshot, not a mock image."
    )


def test_showcase_and_readme_do_not_reference_private_corpus():
    public_text = _normalized(_read_required_file(README))
    if SHOWCASE_SOURCE.exists():
        public_text += "\n" + _normalized(SHOWCASE_SOURCE.read_text(encoding="utf-8"))

    leaked_markers = [
        marker for marker in PRIVATE_CORPUS_FORBIDDEN_MARKERS if marker in public_text
    ]
    assert not leaked_markers, (
        "Public showcase and README must not reference private corpus paths, "
        f"sample identifiers, or local machine paths. Found: {leaked_markers}"
    )


@pytest.mark.slow
def test_showcase_builds_to_tmp_pdf_with_extractable_text(
    runner,
    cli_app,
    tmp_path,
):
    _read_required_file(SHOWCASE_SOURCE)
    output_path = tmp_path / "hypolatex-showcase.pdf"

    result = runner.invoke(
        cli_app,
        ["build", str(SHOWCASE_SOURCE), "--output", str(output_path)],
    )

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES
    assert "build/showcase" not in os.fspath(output_path)

    pdf_text = _extract_pdf_text(output_path)
    missing_markers = [
        marker for marker in SHOWCASE_PDF_TEXT_MARKERS if marker not in pdf_text
    ]
    assert not missing_markers, (
        "Showcase PDF must expose text evidence for the public features shown "
        f"in the README banner. Missing markers: {missing_markers}"
    )
