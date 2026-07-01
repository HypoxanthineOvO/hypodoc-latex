import re
import shutil
import subprocess
from pathlib import Path

import pytest


TEST_ROOT = Path(__file__).parent
FIXTURE_ROOT = TEST_ROOT / "fixtures"
MIN_PDF_BYTES = 1024
M2_BILINGUAL_FIXTURE = FIXTURE_ROOT / "m2" / "bilingual-a4.md"
ANSWER_MODE_FIXTURE = FIXTURE_ROOT / "semantics" / "answer-mode.md"
SEMANTIC_PROJECT_FIXTURE = FIXTURE_ROOT / "semantics" / "project-brief.md"


BUILD_FIXTURE_CASES = (
    pytest.param(
        "longform/tutorial.md",
        "longform-tutorial.pdf",
        id="longform-cover-toc-callouts",
    ),
    pytest.param(
        "callouts/all-callouts.md",
        "callouts-all-callouts.pdf",
        id="callout-environments",
    ),
    pytest.param(
        "figures/figure-ref.md",
        "figures-figure-ref.pdf",
        id="figure-ref-macros",
    ),
    pytest.param(
        "bilingual/bilingual.md",
        "bilingual-bilingual.pdf",
        id="bilingual-xelatex",
    ),
)


def _invoke_build(
    runner,
    cli_app,
    input_path,
    output_path,
    paper=None,
    answer_mode=None,
):
    args = ["build", str(input_path), "--output", str(output_path)]
    if paper is not None:
        args.extend(["--paper", paper])
    if answer_mode is not None:
        args.extend(["--answer-mode", answer_mode])
    return runner.invoke(cli_app, args)


def _require_poppler_tool(name):
    tool = shutil.which(name)
    assert tool is not None, f"{name} is required for M2 PDF evidence tests."
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


def _normalize_pdf_text(text):
    return (
        text.replace("\u2010", "-")
        .replace("\u2011", "-")
        .replace("\u2012", "-")
        .replace("\u2212", "-")
    )


def _assert_non_empty_pdf(output_path):
    assert output_path.suffix == ".pdf"
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES


@pytest.mark.parametrize(("fixture_name", "pdf_name"), BUILD_FIXTURE_CASES)
def test_build_compiles_core_fixtures_to_pdf(
    runner,
    cli_app,
    tmp_path,
    fixture_name,
    pdf_name,
):
    input_path = FIXTURE_ROOT / fixture_name
    output_path = tmp_path / pdf_name

    result = _invoke_build(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)


def test_build_defaults_m2_bilingual_fixture_to_a4_pdfinfo(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "m2-bilingual-a4.pdf"

    result = _invoke_build(runner, cli_app, M2_BILINGUAL_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdfinfo_output = _run_pdfinfo(output_path)
    assert re.search(
        r"Page size:\s+595(?:\.\d+)? x 842(?:\.\d+)? pts.*\(A4\)",
        pdfinfo_output,
    ), pdfinfo_output


def test_build_accepts_explicit_letterpaper_override_by_pdfinfo(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "m2-bilingual-letter.pdf"

    result = _invoke_build(
        runner,
        cli_app,
        M2_BILINGUAL_FIXTURE,
        output_path,
        paper="letterpaper",
    )

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdfinfo_output = _run_pdfinfo(output_path)
    assert re.search(
        r"Page size:\s+612(?:\.\d+)? x 792(?:\.\d+)? pts",
        pdfinfo_output,
    ), pdfinfo_output


def test_build_m2_bilingual_fixture_extracts_chinese_and_english_text(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "m2-bilingual-text.pdf"

    result = _invoke_build(runner, cli_app, M2_BILINGUAL_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdf_text = _normalize_pdf_text(_extract_pdf_text(output_path))
    assert "中文证据段落" in pdf_text
    assert "English evidence text" in pdf_text


@pytest.mark.parametrize(
    ("answer_mode", "should_show_answer"),
    (
        pytest.param("student", False, id="student-hides-answer"),
        pytest.param("review", True, id="review-shows-answer"),
        pytest.param("teacher", True, id="teacher-shows-answer"),
    ),
)
def test_build_answer_mode_controls_pdf_answer_visibility(
    runner,
    cli_app,
    tmp_path,
    answer_mode,
    should_show_answer,
):
    output_path = tmp_path / f"answer-mode-{answer_mode}.pdf"

    result = _invoke_build(
        runner,
        cli_app,
        ANSWER_MODE_FIXTURE,
        output_path,
        answer_mode=answer_mode,
    )

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdf_text = _normalize_pdf_text(_extract_pdf_text(output_path))
    assert "Visible prompt text" in pdf_text

    if should_show_answer:
        assert "Teacher-only answer text" in pdf_text
    else:
        assert "Teacher-only answer text" not in pdf_text


def test_build_semantic_project_brief_extracts_semantic_pdf_text(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "semantic-project-brief.pdf"

    result = _invoke_build(runner, cli_app, SEMANTIC_PROJECT_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdf_text = _extract_pdf_text(output_path)
    for expected_text in ("目标", "交付物", "硬性要求", "验收标准", "项目"):
        assert expected_text in pdf_text


def test_build_rejects_conversion_errors_with_actionable_diagnostic(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "callouts" / "unknown-directive.md"
    output_path = tmp_path / "unknown-directive.pdf"

    result = _invoke_build(runner, cli_app, input_path, output_path)

    assert result.exit_code != 0
    assert not output_path.exists()

    diagnostic = f"{result.output}\n{result.exception or ''}".lower()
    assert "unknown directive" in diagnostic or "unsupported directive" in diagnostic
    assert "experiment" in diagnostic
    for supported_directive in ("note", "tip", "warning", "summary", "figure", "ref"):
        assert supported_directive in diagnostic
