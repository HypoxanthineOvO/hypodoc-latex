import re
import shutil
import subprocess
from pathlib import Path


TEST_ROOT = Path(__file__).parent
FIXTURE_ROOT = TEST_ROOT / "fixtures" / "tables"
SNAPSHOT_ROOT = TEST_ROOT / "snapshots" / "tables"
TEX_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "tex" / "latex" / "hypolatex"
HYPOLATEX_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex.sty"
TABLE_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex-tables.sty"
MIN_PDF_BYTES = 1024


def _read_text(path):
    return path.read_text(encoding="utf-8")


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
    assert tex == _read_text(expected_path)
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
