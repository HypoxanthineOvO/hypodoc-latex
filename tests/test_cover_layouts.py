from __future__ import annotations

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEX_PACKAGE_ROOT = PROJECT_ROOT / "tex" / "latex" / "hypolatex"
LAYOUT_FILE = TEX_PACKAGE_ROOT / "hypolatex-layout.sty"
CORE_FILE = TEX_PACKAGE_ROOT / "hypolatex-core.sty"
TEMPLATE_FILE = PROJECT_ROOT / "src" / "hypolatex" / "resources" / "templates" / "hypolatex.tex"
DOC_FILE = PROJECT_ROOT / "docs" / "cover-layouts.md"
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "themes" / "cover-layout-card.md"
MIN_PDF_BYTES = 1024

SUPPORTED_LAYOUTS = (
    "plain",
    "full-bleed-card",
    "integrated-art",
    "top-title-image",
    "info-panel",
    "paper-ink",
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_cover_layout_metadata_is_part_of_conversion_contract(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "cover-layout.tex"

    result = runner.invoke(
        cli_app,
        ["convert", str(FIXTURE), "--output", str(output_path)],
    )

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\HypoSetMetadata{cover_layout}{full-bleed-card}" in tex

    core = _read_text(CORE_FILE)
    assert "\\csdef{Hypo@metadata@cover_layout}" in core
    assert "\\csdef{Hypo@metadata@cover_image}" in core

    template = _read_text(TEMPLATE_FILE)
    assert "$if(cover_layout)$" in template
    assert "$if(cover_image)$" in template


def test_document_start_keeps_template_thin_and_dispatches_by_layout():
    template = _read_text(TEMPLATE_FILE)
    layout = _read_text(LAYOUT_FILE)
    compact_template = re.sub(r"[ \t]+", "", template)
    legacy_startup = "\\HypoMakeCover\n\\clearpage\n\\tableofcontents\n\\clearpage"

    assert "\\HypoDocumentStart" in template
    assert "\\HypoMakeCover" not in template
    assert "\\tableofcontents" not in template
    assert legacy_startup not in compact_template

    standard_start = re.search(
        r"\\newcommand\{\\Hypo@StandardDocumentStart\}\{%\n(?P<body>.*?)\n\}",
        layout,
        flags=re.DOTALL,
    )
    assert standard_start is not None
    compact_standard_start = re.sub(r"[ \t]+", "", standard_start.group("body"))
    assert legacy_startup in compact_standard_start

    assert re.search(
        r"\\ifdefstring\{\\Hypo@metadata@layout\}\{standard\}\{%\s*"
        r"\\Hypo@StandardDocumentStart",
        layout,
        flags=re.DOTALL,
    )
    assert re.search(
        r"\\ifdefstring\{\\Hypo@metadata@layout\}\{cheatsheet\}\{%\s*"
        r"\\Hypo@CheatsheetDocumentStart",
        layout,
        flags=re.DOTALL,
    )


def test_cover_layout_latex_layer_declares_small_template_set():
    source = _read_text(LAYOUT_FILE)

    for layout in SUPPORTED_LAYOUTS:
        assert layout in source

    assert "\\Hypo@ResolveCoverLayout" in source
    assert "\\Hypo@ResolvedCoverLayout" in source
    assert "\\HypoIfMetadataTF{version}" not in source
    assert "Unknown cover_layout" in source
    assert "integrated-art" in source and "classic-readable" in source
    assert "hypolatex-cover-classic-readable-integrated.png" in source


def test_cover_layout_docs_record_reference_patterns_and_ai_selection_rules():
    text = _read_text(DOC_FILE)
    normalized = re.sub(r"\s+", " ", text.casefold())

    for layout in SUPPORTED_LAYOUTS:
        assert layout in normalized

    for expected in (
        "reference image",
        "title safety",
        "full-bleed",
        "exam",
        "longform",
        "cover_layout",
        "cover_image",
    ):
        assert expected in normalized


def test_cover_layout_fixture_builds_pdf(runner, cli_app, tmp_path):
    output_path = tmp_path / "cover-layout.pdf"

    result = runner.invoke(
        cli_app,
        ["build", str(FIXTURE), "--output", str(output_path)],
    )

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES
