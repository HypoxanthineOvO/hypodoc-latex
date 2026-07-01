from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_DOCS_ROOT = PROJECT_ROOT / "docs" / "release"
HANDBOOK = RELEASE_DOCS_ROOT / "handbook.md"
QUICKSTART = RELEASE_DOCS_ROOT / "quickstart.md"
MIN_PDF_BYTES = 1024

HANDBOOK_REQUIRED_TOPICS = {
    "项目定位": ("项目定位", "定位", "hypo-latex 是", "hypolatex 是"),
    "快速开始/构建流程": ("快速开始", "构建流程", "hypolatex build"),
    "CLI": ("cli", "命令行", "hypolatex doctor", "hypolatex convert"),
    "主题": ("主题", "theme", "theme-first"),
    "HypoDoc Markdown 子集": ("hypodoc markdown", "markdown 子集", "hypodoc"),
    "语义模块": ("语义模块", "semantic", "project", "assignment"),
    "复习题/Q-A": ("复习题", "q-a", "问答", "answer-mode"),
    "受控表格": ("受控表格", "table", "表格"),
    "图片": ("图片", "图像", "figure", "figures"),
    "AI 写作/Skill": ("ai 写作", "skill", "ai authoring", "hypolatex skill"),
}

QUICKSTART_REQUIRED_MARKERS = (
    "hypolatex doctor",
    "hypolatex build",
)
QUICKSTART_ALTERNATIVE_NEXT_STEP_MARKERS = (
    "hypolatex convert",
    "convert",
    "answer-mode",
    "--answer-mode review",
)
PRIVATE_CORPUS_FORBIDDEN_MARKERS = (
    "tests/private",
    "private corpus",
    "private_corpus",
    "corpus-" + "ai" + "-guide",
    "tutorial_1_01",
    "wed2025fall",
)


def _read_required_file(path: Path) -> str:
    assert path.is_file(), f"Expected release documentation source to exist: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", text, re.DOTALL)
    assert match, "Release docs must start with YAML frontmatter."
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


def _assert_theme_frontmatter(path: Path, text: str) -> None:
    from hypolatex import themes

    frontmatter = _frontmatter(text)
    assert frontmatter.get("title"), f"{path} must define a title in frontmatter."
    assert frontmatter.get("theme"), f"{path} must define a theme in frontmatter."
    assert frontmatter["theme"] in themes.valid_theme_ids(), (
        f"{path} must use a registered Hypo-LaTeX theme, got "
        f"{frontmatter['theme']!r}."
    )


def _require_poppler_tool(name: str) -> str:
    tool = shutil.which(name)
    assert tool is not None, f"{name} is required for release PDF evidence tests."
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


@pytest.mark.parametrize("path", (HANDBOOK, QUICKSTART))
def test_release_docs_sources_exist_with_frontmatter_theme(path: Path):
    text = _read_required_file(path)

    _assert_theme_frontmatter(path, text)


def test_release_handbook_covers_required_public_topics():
    text = _normalized(_read_required_file(HANDBOOK))

    missing_topics = [
        topic
        for topic, markers in HANDBOOK_REQUIRED_TOPICS.items()
        if not any(marker in text for marker in markers)
    ]
    assert not missing_topics, (
        "Release handbook must cover the M1 public user-facing topics. "
        f"Missing topics: {missing_topics}"
    )
    assert "hypodoc-spec" in text or "spec/hypodoc" in text, (
        "The handbook should identify the HypoDoc spec source as the "
        "authoritative reference instead of becoming an unsourced fork."
    )


def test_release_quickstart_is_short_and_has_minimal_build_path():
    text = _normalized(_read_required_file(QUICKSTART))

    for marker in QUICKSTART_REQUIRED_MARKERS:
        assert marker in text, f"Quickstart must include `{marker}`."
    assert any(marker in text for marker in QUICKSTART_ALTERNATIVE_NEXT_STEP_MARKERS), (
        "Quickstart must include the smallest path after doctor/build: "
        "`hypolatex convert` or review answer-mode."
    )
    assert len(re.findall(r"^#{1,3}\s+", text, flags=re.MULTILINE)) <= 8, (
        "Quickstart should remain a short flow, not a second handbook."
    )


def test_release_docs_do_not_include_private_corpus_markers():
    combined = _normalized(
        "\n".join(_read_required_file(path) for path in (HANDBOOK, QUICKSTART))
    )

    leaked_markers = [
        marker for marker in PRIVATE_CORPUS_FORBIDDEN_MARKERS if marker in combined
    ]
    assert not leaked_markers, (
        "Release docs must be public and must not reference private corpus "
        f"paths or sample identifiers. Found: {leaked_markers}"
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    ("source_path", "pdf_name", "expected_markers"),
    (
        pytest.param(
            HANDBOOK,
            "hypolatex-handbook.pdf",
            ("hypolatex", "hypolatex build", "theme"),
            id="handbook",
        ),
        pytest.param(
            QUICKSTART,
            "hypolatex-quickstart.pdf",
            ("hypolatex doctor", "hypolatex build"),
            id="quickstart",
        ),
    ),
)
def test_release_docs_build_to_pdf_with_extractable_evidence(
    runner,
    cli_app,
    tmp_path,
    source_path: Path,
    pdf_name: str,
    expected_markers: tuple[str, ...],
):
    _read_required_file(source_path)
    output_path = tmp_path / pdf_name

    result = runner.invoke(
        cli_app,
        ["build", str(source_path), "--output", str(output_path)],
    )

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES

    pdf_text = _extract_pdf_text(output_path)
    for marker in expected_markers:
        assert marker in pdf_text, (
            f"Expected release PDF text evidence marker {marker!r} in {output_path}."
        )
