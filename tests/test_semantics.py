from pathlib import Path
import re

import pytest


TEST_ROOT = Path(__file__).parent
FIXTURE_ROOT = TEST_ROOT / "fixtures" / "semantics"
SNAPSHOT_ROOT = TEST_ROOT / "snapshots" / "semantics"
TEX_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "tex" / "latex" / "hypolatex"
HYPOLATEX_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex.sty"
CORE_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex-core.sty"
ICONS_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex-icons.sty"
CALLOUTS_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex-callouts.sty"
SEMANTICS_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex-semantics.sty"

SEMANTIC_ENVIRONMENTS = (
    ("objective", "HypoObjective", "Objective"),
    ("info", "HypoInfo", "Info"),
    ("task", "HypoTask", "Task"),
    ("requirement", "HypoRequirement", "Requirement"),
    ("deliverable", "HypoDeliverable", "Deliverable"),
    ("checklist", "HypoChecklist", "Checklist"),
    ("rubric", "HypoRubric", "Rubric"),
)


def _read_text(path):
    return path.read_text(encoding="utf-8")


def _invoke_convert(runner, cli_app, input_path, output_path):
    return runner.invoke(
        cli_app, ["convert", str(input_path), "--output", str(output_path)]
    )


@pytest.mark.parametrize(
    ("fixture_name", "snapshot_name"),
    (
        pytest.param("project-brief.md", "project-brief.tex", id="project-brief"),
        pytest.param(
            "assignment-brief.md", "assignment-brief.tex", id="assignment-brief"
        ),
    ),
)
def test_semantic_directives_convert_to_stable_snapshot(
    runner,
    cli_app,
    tmp_path,
    fixture_name,
    snapshot_name,
):
    input_path = FIXTURE_ROOT / fixture_name
    output_path = tmp_path / snapshot_name
    expected_path = SNAPSHOT_ROOT / snapshot_name

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert _read_text(output_path) == _read_text(expected_path)


def test_semantic_directives_preserve_nested_markdown_inside_blocks(
    runner,
    cli_app,
    tmp_path,
):
    input_path = FIXTURE_ROOT / "assignment-brief.md"
    output_path = tmp_path / "assignment-brief.tex"

    result = _invoke_convert(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    for _, environment, _ in SEMANTIC_ENVIRONMENTS:
        assert f"\\begin{{{environment}}}" in tex
        assert f"\\end{{{environment}}}" in tex
    assert "\\textbf{nested emphasis}" in tex
    assert "\\texttt{inline\\_code}" in tex
    assert "\\begin{itemize}" in tex
    assert "\\begin{enumerate}" in tex
    assert "Draft a response with \\textbf{evidence}" in tex


def test_core_styles_pandoc_inline_code_without_changing_markdown_contract():
    core_source = _read_text(CORE_PACKAGE_FILE)

    assert "\\RequirePackage{tcolorbox}" in core_source
    assert "\\newtcbox{\\HypoInlineCode}" in core_source
    assert "\\RenewDocumentCommand{\\texttt}{m}" in core_source
    assert "colback=HypoNoteBack" in core_source
    assert "colframe=HypoSemanticFrame" in core_source
    assert "coltext=HypoAccent" in core_source


def test_core_styles_fenced_code_blocks_with_theme_tokens():
    core_source = _read_text(CORE_PACKAGE_FILE)

    assert "\\RequirePackage{listings}" in core_source
    assert "\\tcbuselibrary{listings,breakable,skins}" in core_source
    assert "\\lstdefinestyle{HypoListingStyle}" in core_source
    assert "\\newtcblisting{HypoCodeCommand}" in core_source
    assert "\\newtcblisting{HypoCodeBlock}" in core_source
    assert "colback=HypoNoteBack" in core_source
    assert "colframe=HypoSemanticFrame" in core_source
    assert "breaklines=true" in core_source
    assert "width=0.88\\linewidth" in core_source


def test_semantic_package_is_loaded_and_defines_public_environments():
    assert SEMANTICS_PACKAGE_FILE.is_file(), (
        "M3 must add hypolatex-semantics.sty for reusable assignment/project "
        "semantic blocks."
    )

    package_source = _read_text(HYPOLATEX_PACKAGE_FILE)
    assert "\\RequirePackage{hypolatex-semantics}" in package_source

    semantics_source = _read_text(SEMANTICS_PACKAGE_FILE)
    for _, environment, title in SEMANTIC_ENVIRONMENTS:
        assert environment in semantics_source
        assert title in semantics_source


def test_semantic_package_uses_reusable_box_archetypes_and_theme_tokens():
    semantics_source = _read_text(SEMANTICS_PACKAGE_FILE)

    assert "\\RequirePackage{tcolorbox}" in semantics_source
    for archetype in (
        "HypoBox",
        "HypoBoxTitle",
        "HypoSemanticStandardBox",
        "HypoSemanticNumberedBox",
        "HypoSemanticAnswerBox",
        "HypoSemanticRubricBox",
        "hypobox/subtle",
        "hypobox/card",
    ):
        assert archetype in semantics_source

    for token in (
        "HypoSemanticBack",
        "HypoQuestionBack",
        "HypoAnswerBack",
        "HypoRubricBack",
        "HypoSemanticTitleFont",
        "HypoQuestionTitleFont",
        "HypoRubricTitleFont",
    ):
        assert token in semantics_source

    assert "Latin Modern Roman" not in semantics_source


def test_semantic_titles_use_fixed_width_icon_slot():
    icons_source = _read_text(ICONS_PACKAGE_FILE)
    semantics_source = _read_text(SEMANTICS_PACKAGE_FILE)
    callouts_source = _read_text(CALLOUTS_PACKAGE_FILE)

    for expected in (
        "\\newlength{\\HypoIconSlotWidth}",
        "\\makebox[\\HypoIconSlotWidth][c]{\\HypoIcon{#1}}",
        "\\NewDocumentCommand{\\HypoIconTitle}",
        "\\newlength{\\HypoIconTitleIndent}",
    ):
        assert expected in icons_source

    assert "\\HypoIconTitle{#1}{#2}" in semantics_source
    assert "\\leftskip=\\HypoIconTitleIndent" in semantics_source

    for expected in (
        "title={\\HypoIconTitle{note}{Note}}",
        "title={\\HypoIconTitle{tip}{Tip}}",
        "title={\\HypoIconTitle{warning}{Warning}}",
        "title={\\HypoIconTitle{summary}{Summary}}",
    ):
        assert expected in callouts_source


def test_question_styles_separate_outline_frame_from_plain_text_flow():
    semantics_source = _read_text(SEMANTICS_PACKAGE_FILE)

    assert "\\NewDocumentCommand{\\HypoQuestionOutlineBox}" in semantics_source
    assert "\\NewDocumentCommand{\\HypoQuestionTextBox}" in semantics_source
    assert "\\NewDocumentCommand{\\HypoTextQASection}" in semantics_source
    assert "\\NewDocumentCommand{\\Hypo@ResolvePrefixedTitle}" in semantics_source
    assert "hypobox/question-plain" in semantics_source
    assert "boxrule=0.35pt" in semantics_source
    assert "leftrule=2pt" in semantics_source
    assert "colbacktitle=HypoQuestionBack" in semantics_source
    assert "O{outline} +b" in semantics_source
    assert "\\ifstrequal{#2}{plain}" in semantics_source
    assert "\\HypoQuestionTextBox{#1}{#3}" in semantics_source
    text_section = re.search(
        r"\\NewDocumentCommand\{\\HypoTextQASection\}\{m m m \+m\}\{%(.+?)\n\}",
        semantics_source,
        re.DOTALL,
    )
    assert text_section is not None
    assert "\\leftskip" not in text_section.group(1)
    assert "\\setlength{\\parindent}{0pt}" in text_section.group(1)
    assert "\\begin{tcolorbox}[hypobox/question-plain]" not in semantics_source


def test_core_package_defines_compact_five_level_list_contract():
    core_source = _read_text(CORE_PACKAGE_FILE)

    assert "\\RequirePackage{enumitem}" in core_source
    assert "\\setlistdepth{5}" in core_source
    assert "\\renewlist{itemize}{itemize}{5}" in core_source
    assert "\\renewlist{enumerate}{enumerate}{5}" in core_source
    for command in (
        "HypoItemBulletSolid",
        "HypoItemBulletHollow",
        "HypoItemBulletSquare",
        "HypoItemBulletHollowSquare",
        "HypoItemBulletTriangle",
    ):
        assert command in core_source

    for expected in (
        "\\setlist[itemize,1]{label=\\HypoItemBulletSolid}",
        "\\setlist[itemize,2]{label=\\HypoItemBulletHollow,leftmargin=1.25em}",
        "\\setlist[itemize,3]{label=\\HypoItemBulletSquare,leftmargin=1.2em}",
        "\\setlist[itemize,4]{label=\\HypoItemBulletHollowSquare,leftmargin=1.2em}",
        "\\setlist[itemize,5]{label=\\HypoItemBulletTriangle,leftmargin=1.2em}",
        "\\setlist[enumerate]",
    ):
        assert expected in core_source
