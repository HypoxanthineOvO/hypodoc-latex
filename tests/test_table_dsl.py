import re
import shutil
import subprocess
from pathlib import Path


TEST_ROOT = Path(__file__).parent
FIXTURE_ROOT = TEST_ROOT / "fixtures" / "tables"
M3_FIXTURE_ROOT = TEST_ROOT / "fixtures" / "m3"
SNAPSHOT_ROOT = TEST_ROOT / "snapshots" / "tables"
TEX_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "tex" / "latex" / "hypolatex"
HYPOLATEX_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex.sty"
TABLE_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex-tables.sty"
LAYOUT_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex-layout.sty"
CHEATSHEET_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex-cheatsheet.sty"
MIN_PDF_BYTES = 1024


def _read_text(path):
    return path.read_text(encoding="utf-8")


def _document_body_from(tex, marker):
    index = tex.find(marker)
    assert index >= 0, f"Missing expected document body marker: {marker}"
    return tex[index:]


def _source_windows_containing(source, needle, radius=900):
    return [
        source[max(0, match.start() - radius) : match.end() + radius]
        for match in re.finditer(re.escape(needle), source, flags=re.IGNORECASE)
    ]


def _has_any_pattern(source, patterns):
    return any(
        re.search(pattern, source, re.IGNORECASE | re.DOTALL)
        for pattern in patterns
    )


def _invoke_convert(runner, cli_app, input_path, output_path):
    return runner.invoke(
        cli_app, ["convert", str(input_path), "--output", str(output_path)]
    )


def _invoke_build(runner, cli_app, input_path, output_path):
    return runner.invoke(
        cli_app,
        [
            "build",
            str(input_path),
            "--theme",
            "tech-minimal",
            "--output",
            str(output_path),
        ],
    )


def _snapshot_fragments(path):
    return [
        fragment.strip()
        for fragment in _read_text(path).split("\n---\n")
        if fragment.strip()
    ]


def _assert_contains_snapshot_fragments(tex, snapshot_path):
    missing = [
        fragment
        for fragment in _snapshot_fragments(snapshot_path)
        if fragment not in tex
    ]
    assert not missing, "Missing expected TeX fragments:\n" + "\n---\n".join(missing)


def _require_poppler_tool(name):
    tool = shutil.which(name)
    assert tool is not None, f"{name} is required for M5 long-table PDF evidence tests."
    return tool


def _run_pdfinfo(pdf_path):
    result = subprocess.run(
        [_require_poppler_tool("pdfinfo"), str(pdf_path)],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _extract_pdf_text(pdf_path):
    result = subprocess.run(
        [_require_poppler_tool("pdftotext"), str(pdf_path), "-"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _pdf_pages(pdf_path):
    pdfinfo_output = _run_pdfinfo(pdf_path)
    match = re.search(r"^Pages:\s+(\d+)\s*$", pdfinfo_output, re.MULTILINE)
    assert match is not None, pdfinfo_output
    return int(match.group(1))


def _assert_non_empty_pdf(output_path):
    assert output_path.suffix == ".pdf"
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES


def test_ordinary_markdown_table_outside_table_div_keeps_pandoc_snapshot(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "ordinary-compat.md"
    output_path = tmp_path / "ordinary-compat.tex"
    expected_path = SNAPSHOT_ROOT / "ordinary-table-compat.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    body_marker = "\\chapter{Ordinary Markdown Table}"
    assert _document_body_from(tex, body_marker) == _document_body_from(
        _read_text(expected_path),
        body_marker,
    )
    assert "\\begin{longtable}" in tex
    assert "\\HypoTableConfig" not in tex
    assert "\\begin{tblr}" not in tex


def test_controlled_table_attribute_config_converts_to_snapshot_fragments(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "attribute-config.md"
    output_path = tmp_path / "attribute-config.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    _assert_contains_snapshot_fragments(
        tex, SNAPSHOT_ROOT / "attribute-config-fragments.txt"
    )
    assert "The paragraph after the controlled table must remain ordinary text." in tex


def test_controlled_table_yaml_config_converts_columns_to_snapshot_fragments(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "yaml-columns.md"
    output_path = tmp_path / "yaml-columns.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    _assert_contains_snapshot_fragments(
        tex, SNAPSHOT_ROOT / "yaml-columns-fragments.txt"
    )
    assert "columns:" not in tex
    assert "align:" not in tex
    assert "```yaml" not in tex


def test_public_table_patterns_include_comparison_checklist_rubric_and_compact_cheatsheet(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "comparison.md"
    output_path = tmp_path / "comparison.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    _assert_contains_snapshot_fragments(tex, SNAPSHOT_ROOT / "patterns-fragments.txt")
    assert "type=cheatsheet" in tex, (
        "The compact cheatsheet fixture must be implemented as a table pattern, "
        "not only as density=compact on another pattern."
    )


def test_m3_printable_cheatsheet_table_path_converts_to_compact_fragments(
    runner,
    cli_app,
    tmp_path,
):
    input_path = M3_FIXTURE_ROOT / "printable-cheatsheet.md"
    output_path = tmp_path / "printable-cheatsheet.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    _assert_contains_snapshot_fragments(
        tex, SNAPSHOT_ROOT / "cheatsheet-compact-fragments.txt"
    )
    assert "type=cheatsheet" in tex
    assert "density=compact" in tex
    assert "\\begin{tblr}" in tex
    assert "Dense Table Evidence" in tex


def test_m3_cheatsheet_visual_contract_declares_scoped_compact_list_behavior():
    layout_source = _read_text(LAYOUT_PACKAGE_FILE)
    cheatsheet_source = _read_text(CHEATSHEET_PACKAGE_FILE)
    visual_surface = f"{layout_source}\n{cheatsheet_source}"
    cheatsheet_start = re.search(
        r"\\newcommand\{\\Hypo@CheatsheetDocumentStart\}\{%(?P<body>.*?)"
        r"\n\}\n\n\\newcommand\{\\HypoDocumentStart\}",
        layout_source,
        re.DOTALL,
    )

    assert cheatsheet_start is not None, (
        "The cheatsheet layout must keep its own document-start surface so "
        "compact print behavior stays scoped to layout: cheatsheet."
    )
    body = cheatsheet_start.group("body")
    assert "\\Hypo@StandardDocumentStart" not in body

    scoped_windows = _source_windows_containing(visual_surface, "cheatsheet")
    assert scoped_windows, (
        "M3 needs a cheatsheet-specific visual surface so compact print behavior "
        "does not leak into ordinary article layouts."
    )
    compact_list_patterns = (
        r"\\setlist(?:\[[^\]]+\])?\s*\{[^}]*"
        r"(?:itemsep|topsep|parsep|partopsep|leftmargin|nosep|noitemsep)",
        r"\\(?:setlength|addtolength)\s*\{\\"
        r"(?:itemsep|topsep|parsep|partopsep|leftmargini)\}",
        r"(?:itemsep|topsep|parsep|partopsep|leftmargin)\s*=",
        r"\b(?:nosep|noitemsep)\b",
    )
    assert any(
        _has_any_pattern(window, compact_list_patterns) for window in scoped_windows
    ), (
        "M3 printable cheatsheets need scoped compact list behavior in a "
        "cheatsheet-specific visual surface. Page density itself is validated "
        "by the PDF page-count evidence, so this contract should accept any "
        "implementation route that keeps list spacing scoped to cheatsheets."
    )


def test_table_package_contract_declares_tabularray_and_longtable_fallback():
    assert TABLE_PACKAGE_FILE.is_file(), (
        "M5 must add hypolatex-tables.sty as the reusable table package surface."
    )

    package_source = _read_text(HYPOLATEX_PACKAGE_FILE)
    table_source = _read_text(TABLE_PACKAGE_FILE)
    lowered_table_source = table_source.lower()

    assert "\\RequirePackage{hypolatex-tables}" in package_source
    assert "tabularray" in lowered_table_source
    assert "longtable" in lowered_table_source
    assert "fallback" in lowered_table_source
    assert "HypoTableConfig" in table_source
    assert "HypoTableColumn" in table_source


def test_synthetic_long_table_builds_multi_page_pdf_with_terminal_row(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "long-table.md"
    output_path = tmp_path / "synthetic-long-table.pdf"

    result = _invoke_build(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    assert _pdf_pages(output_path) >= 2
    pdf_text = _extract_pdf_text(output_path)
    assert "Row 120" in pdf_text
    assert "长表格" in pdf_text
