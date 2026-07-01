from pathlib import Path
import shutil
import subprocess


TEST_ROOT = Path(__file__).parent
FIXTURE_ROOT = TEST_ROOT / "fixtures" / "semantics"
SNAPSHOT_ROOT = TEST_ROOT / "snapshots" / "semantics"
TEX_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "tex" / "latex" / "hypolatex"
SEMANTICS_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex-semantics.sty"
REVIEW_QUESTION_FIXTURE = FIXTURE_ROOT / "review-questions.md"
REVIEW_QUESTION_SNAPSHOT = SNAPSHOT_ROOT / "review-questions.tex"
MIN_PDF_BYTES = 1024

QUESTION_TEXT = "What is the derivative of"
HINT_TEXT = "Hint text: Use the power rule before simplifying."
OFFICIAL_ANSWER_TEXT = "Official answer text: The derivative is two x."
OFFICIAL_SOLUTION_TEXT = (
    "Official solution text: Bring down the exponent and subtract one."
)
REVIEW_ENVIRONMENTS = (
    "HypoQuestion",
    "HypoHint",
    "HypoAnswer",
    "HypoSolution",
)


def _read_text(path):
    return path.read_text(encoding="utf-8")


def _invoke_convert(runner, cli_app, input_path, output_path, answer_mode=None):
    args = ["convert", str(input_path), "--output", str(output_path)]
    if answer_mode is not None:
        args.extend(["--answer-mode", answer_mode])
    return runner.invoke(cli_app, args)


def _invoke_build(runner, cli_app, input_path, output_path, answer_mode):
    return runner.invoke(
        cli_app,
        [
            "build",
            str(input_path),
            "--output",
            str(output_path),
            "--answer-mode",
            answer_mode,
        ],
    )


def _require_poppler_tool(name):
    tool = shutil.which(name)
    assert tool is not None, f"{name} is required for M4 review PDF evidence tests."
    return tool


def _extract_pdf_text(pdf_path):
    result = subprocess.run(
        [_require_poppler_tool("pdftotext"), str(pdf_path), "-"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _assert_non_empty_pdf(output_path):
    assert output_path.suffix == ".pdf"
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES


def test_review_question_directives_convert_to_stable_snapshot(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "review-questions.tex"

    result = _invoke_convert(runner, cli_app, REVIEW_QUESTION_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert _read_text(output_path) == _read_text(REVIEW_QUESTION_SNAPSHOT)


def test_review_question_snapshot_preserves_environment_and_label_contract(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "review-questions-contract.tex"

    result = _invoke_convert(runner, cli_app, REVIEW_QUESTION_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    for environment in REVIEW_ENVIRONMENTS:
        assert f"\\begin{{{environment}}}" in tex
        assert f"\\end{{{environment}}}" in tex
    assert "\\begin{HypoQuestion}[rq:power-rule][题目：Power Rule][][card]" in tex
    assert (
        "\\begin{HypoQuestion}[rq:plain-discussion][非 Card 开放推理题][][plain]"
        in tex
    )
    assert "\\begin{HypoHint}[提示][plain]" in tex
    assert "\\begin{HypoAnswer}[参考答案][plain]" in tex
    assert "\\begin{HypoSolution}[解析][plain]" in tex


def test_question_defaults_to_outline_and_qa_container_is_supported(
    runner,
    cli_app,
    tmp_path,
):
    input_path = tmp_path / "qa-container.md"
    input_path.write_text(
        """---
title: QA Container Smoke
---

# Review

::: {.qa title="复习题组"}
::: {.question title="开放题"}
Explain the method briefly.
:::

:::answer
Use the definition first.
:::
:::
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "qa-container.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\begin{HypoQA}[复习题组]" in tex
    assert "\\begin{HypoQuestion}[][开放题]" in tex
    assert "[card]" not in tex


def test_review_question_semantics_package_defines_countered_public_environments():
    source = _read_text(SEMANTICS_PACKAGE_FILE)

    for environment in ("HypoQuestion", "HypoHint", "HypoSolution"):
        assert f"\\NewDocumentEnvironment{{{environment}}}" in source

    assert "\\NewDocumentEnvironment{HypoQA}" in source
    lowered_source = source.lower()
    assert "newcounter" in lowered_source
    assert "question" in lowered_source
    assert "\\refstepcounter" in source
    assert "\\label" in source


def test_review_question_fixture_builds_pdf_variants_from_single_source(
    runner,
    cli_app,
    tmp_path,
):
    extracted_text = {}
    for answer_mode in ("student", "review", "teacher"):
        output_path = tmp_path / f"review-questions-{answer_mode}.pdf"

        result = _invoke_build(
            runner,
            cli_app,
            REVIEW_QUESTION_FIXTURE,
            output_path,
            answer_mode=answer_mode,
        )

        assert result.exit_code == 0, result.output
        _assert_non_empty_pdf(output_path)
        extracted_text[answer_mode] = _extract_pdf_text(output_path)

    for answer_mode, pdf_text in extracted_text.items():
        assert QUESTION_TEXT in pdf_text, answer_mode
        assert HINT_TEXT in pdf_text, answer_mode

    assert OFFICIAL_ANSWER_TEXT not in extracted_text["student"]
    assert OFFICIAL_SOLUTION_TEXT not in extracted_text["student"]
    for answer_mode in ("review", "teacher"):
        assert OFFICIAL_ANSWER_TEXT in extracted_text[answer_mode], answer_mode
        assert OFFICIAL_SOLUTION_TEXT in extracted_text[answer_mode], answer_mode
