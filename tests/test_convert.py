from pathlib import Path

import pytest


TEST_ROOT = Path(__file__).parent
FIXTURE_ROOT = TEST_ROOT / "fixtures"
CONVERT_SNAPSHOT_ROOT = TEST_ROOT / "snapshots" / "convert"
TEX_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "tex" / "latex" / "hypolatex"
CORE_FILE = TEX_PACKAGE_ROOT / "hypolatex-core.sty"
LAYOUT_FILE = TEX_PACKAGE_ROOT / "hypolatex-layout.sty"
ANSWER_MODE_FIXTURE = FIXTURE_ROOT / "semantics" / "answer-mode.md"
CHEATSHEET_LAYOUT_FIXTURE = FIXTURE_ROOT / "m1" / "cheatsheet-layout.md"


CONVERSION_SNAPSHOT_CASES = (
    pytest.param(
        "longform/tutorial.md",
        "longform-tutorial.tex",
        id="longform-frontmatter",
    ),
    pytest.param(
        "callouts/all-callouts.md",
        "callouts-all-callouts.tex",
        id="callout-directives",
    ),
    pytest.param(
        "figures/figure-ref.md",
        "figures-figure-ref.tex",
        id="figure-ref-labels",
    ),
    pytest.param(
        "bilingual/bilingual.md",
        "bilingual-bilingual.tex",
        id="bilingual-text",
    ),
    pytest.param(
        "m1/cheatsheet-layout.md",
        "m1-cheatsheet-layout.tex",
        id="cheatsheet-layout",
    ),
)


def _read_text(path):
    return path.read_text(encoding="utf-8")


def _invoke_convert(runner, cli_app, input_path, output_path, answer_mode=None):
    args = ["convert", str(input_path), "--output", str(output_path)]
    if answer_mode is not None:
        args.extend(["--answer-mode", answer_mode])
    return runner.invoke(cli_app, args)


@pytest.mark.parametrize(("fixture_name", "snapshot_name"), CONVERSION_SNAPSHOT_CASES)
def test_convert_writes_expected_tex_snapshot(
    runner,
    cli_app,
    tmp_path,
    fixture_name,
    snapshot_name,
):
    input_path = FIXTURE_ROOT / fixture_name
    output_path = tmp_path / "actual.tex"
    expected_path = CONVERT_SNAPSHOT_ROOT / snapshot_name

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert _read_text(output_path) == _read_text(expected_path)


def test_convert_is_deterministic_for_same_markdown_input(runner, cli_app, tmp_path):
    input_path = FIXTURE_ROOT / "longform" / "tutorial.md"
    first_output = tmp_path / "first.tex"
    second_output = tmp_path / "second.tex"

    first_result = _invoke_convert(runner, cli_app, input_path, first_output)
    second_result = _invoke_convert(runner, cli_app, input_path, second_output)

    assert first_result.exit_code == 0, first_result.output
    assert second_result.exit_code == 0, second_result.output
    assert _read_text(first_output) == _read_text(second_output)
    assert _read_text(first_output) == _read_text(
        CONVERT_SNAPSHOT_ROOT / "longform-tutorial.tex"
    )


def test_convert_emits_default_student_answer_mode_without_losing_theme_metadata(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "longform" / "tutorial.md"
    output_path = tmp_path / "default-student.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\HypoSetAnswerMode{student}" in tex
    assert "\\HypoSetMetadata{theme}{plain}" in tex
    assert "\\begin{HypoNote}" in tex


def test_convert_standard_layout_uses_layout_metadata_and_document_start(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "longform" / "tutorial.md"
    output_path = tmp_path / "standard-layout.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\documentclass{book}" in tex
    assert "\\HypoSetMetadata{layout}{standard}" in tex
    assert "\\HypoDocumentStart" in tex
    assert "\\chapter{Orientation}" in tex
    assert "\\HypoMakeCover\n\\clearpage\n\\tableofcontents\n\\clearpage" not in tex


def test_convert_article_document_type_uses_article_sections(
    runner,
    cli_app,
    tmp_path,
):
    input_path = tmp_path / "short-manual.md"
    input_path.write_text(
        """---
title: Short Manual
theme: plain
document_type: article
---

# Short Manual

## Setup

Run `hypolatex doctor`.
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "short-manual.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\documentclass{article}" in tex
    assert "\\section{Short Manual}" in tex
    assert "\\subsection{Setup}" in tex
    assert "\\chapter{" not in tex


def test_convert_cheatsheet_layout_keeps_article_document_type_and_startup_contract(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "cheatsheet-layout.tex"

    result = _invoke_convert(runner, cli_app, CHEATSHEET_LAYOUT_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\documentclass{article}" in tex
    assert "\\HypoSetMetadata{layout}{cheatsheet}" in tex
    assert "\\HypoDocumentStart" in tex
    assert "\\section{Quick Operator Cheatsheet}" in tex
    assert "\\subsection{Build}" in tex
    assert "\\chapter{" not in tex
    assert "\\HypoMakeCover\n\\clearpage\n\\tableofcontents\n\\clearpage" not in tex


def test_convert_rejects_invalid_layout_with_supported_values(
    runner,
    cli_app,
    tmp_path,
):
    input_path = tmp_path / "invalid-layout.md"
    input_path.write_text(
        """---
title: Invalid Layout
layout: slide-deck
---

# Invalid Layout
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "invalid-layout.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code != 0
    assert not output_path.exists()
    diagnostic = f"{result.output}\n{result.exception or ''}".lower()
    assert "layout" in diagnostic
    assert "slide-deck" in diagnostic
    for supported_layout in ("standard", "cheatsheet"):
        assert supported_layout in diagnostic


def test_latex_document_start_macro_preserves_standard_cover_and_toc_contract():
    latex_support = "\n".join(
        _read_text(path) for path in (CORE_FILE, LAYOUT_FILE) if path.exists()
    )

    assert "Hypo@metadata@layout" in latex_support
    assert "\\HypoDocumentStart" in latex_support
    assert "standard" in latex_support
    assert "cheatsheet" in latex_support
    assert "\\HypoMakeCover" in latex_support
    assert "\\tableofcontents" in latex_support


def test_convert_rejects_unmarked_manual_heading_number(
    runner,
    cli_app,
    tmp_path,
):
    input_path = tmp_path / "bad-heading.md"
    input_path.write_text(
        """---
title: Bad Heading
---

# 1. Introduction
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "bad-heading.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code != 0
    assert not output_path.exists()
    diagnostic = f"{result.output}\n{result.exception or ''}"
    assert "manual number" in diagnostic
    assert ".manual-number" in diagnostic
    assert ".unnumbered" in diagnostic


def test_convert_allows_explicit_manual_number_heading(
    runner,
    cli_app,
    tmp_path,
):
    input_path = tmp_path / "manual-heading.md"
    input_path.write_text(
        """---
title: Manual Heading
document_type: article
---

# 1. Introduction {.manual-number}
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "manual-heading.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\section*{1. Introduction}" in tex
    assert "\\section{1. Introduction}" not in tex


def test_convert_allows_explicit_unnumbered_heading(
    runner,
    cli_app,
    tmp_path,
):
    input_path = tmp_path / "unnumbered-heading.md"
    input_path.write_text(
        """---
title: Unnumbered Heading
document_type: article
---

# Preface {.unnumbered}
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "unnumbered-heading.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\section*{Preface}" in tex
    assert "\\section{Preface}" not in tex


def test_convert_single_line_fenced_code_block_uses_command_box(
    runner,
    cli_app,
    tmp_path,
):
    input_path = tmp_path / "command-block.md"
    input_path.write_text(
        """---
title: Command Block
document_type: article
---

# Build

```bash
hypolatex build input.md --output build/output.pdf
```
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "command-block.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\begin{HypoCodeCommand}" in tex
    assert "hypolatex build input.md --output build/output.pdf" in tex
    assert "\\begin{HypoCodeBlock}" not in tex
    assert "\\begin{verbatim}" not in tex
    assert "\\begin{Shaded}" not in tex
    assert "\\KeywordTok" not in tex


def test_convert_multi_line_fenced_code_block_uses_full_width_code_box(
    runner,
    cli_app,
    tmp_path,
):
    input_path = tmp_path / "multi-line-block.md"
    input_path.write_text(
        """---
title: Multi Line Block
document_type: article
---

# Build

```bash
hypolatex doctor
hypolatex build input.md --output build/output.pdf
```
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "multi-line-block.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\begin{HypoCodeBlock}" in tex
    assert "hypolatex doctor" in tex
    assert "hypolatex build input.md --output build/output.pdf" in tex
    assert "\\begin{HypoCodeCommand}" not in tex
    assert "\\begin{verbatim}" not in tex
    assert "\\begin{Shaded}" not in tex


def test_convert_frontmatter_answer_mode_emits_review_selection(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "frontmatter-review.tex"

    result = _invoke_convert(runner, cli_app, ANSWER_MODE_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\HypoSetAnswerMode{review}" in tex
    assert "Teacher-only answer text" in tex


def test_convert_cli_answer_mode_overrides_frontmatter_selection(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "override-teacher.tex"

    result = _invoke_convert(
        runner,
        cli_app,
        ANSWER_MODE_FIXTURE,
        output_path,
        answer_mode="teacher",
    )

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "\\HypoSetAnswerMode{teacher}" in tex
    assert "\\HypoSetAnswerMode{review}" not in tex


def test_convert_rejects_invalid_cli_answer_mode_with_supported_modes(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "longform" / "tutorial.md"
    output_path = tmp_path / "invalid-answer-mode.tex"

    result = _invoke_convert(
        runner,
        cli_app,
        input_path,
        output_path,
        answer_mode="secret",
    )

    assert result.exit_code != 0
    assert not output_path.exists()
    diagnostic = f"{result.output}\n{result.exception or ''}".lower()
    assert "answer" in diagnostic
    assert "secret" in diagnostic
    for supported_mode in ("student", "review", "teacher"):
        assert supported_mode in diagnostic


def test_figure_directive_supports_fixed_placement_and_width(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "figures" / "figure-ref.md"
    output_path = tmp_path / "figure-ref.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert (
        "\\HypoFigureEx{fig:conversion-flow}{assets/conversion-flow.png}"
        "{Hypo-LaTeX conversion flow}{0.92\\linewidth}{H}"
    ) in tex

    core = _read_text(CORE_FILE)
    assert "\\RequirePackage{float}" in core
    assert "\\newcommand{\\HypoFigureEx}[5]" in core
    assert "\\HypoFigureEx{#1}{#2}{#3}{0.86\\linewidth}{htbp}" in core


def test_convert_rejects_unknown_directive_with_actionable_error(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "callouts" / "unknown-directive.md"
    output_path = tmp_path / "unknown.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code != 0
    assert not output_path.exists()

    diagnostic = f"{result.output}\n{result.exception or ''}".lower()
    assert "unknown directive" in diagnostic or "unsupported directive" in diagnostic
    assert "experiment" in diagnostic
    for supported_directive in ("note", "tip", "warning", "summary", "figure", "ref"):
        assert supported_directive in diagnostic
