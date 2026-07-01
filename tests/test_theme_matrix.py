from __future__ import annotations

from itertools import combinations
import os
from pathlib import Path
import re

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(__file__).parent
FIXTURE_ROOT = TEST_ROOT / "fixtures"
TEX_PACKAGE_ROOT = REPO_ROOT / "tex" / "latex" / "hypolatex"
HYPOLATEX_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex.sty"
CLASSIC_READABLE_THEME_FILE = (
    TEX_PACKAGE_ROOT / "hypolatex-theme-classic-readable.sty"
)
M5_LONGFORM_FIXTURE = FIXTURE_ROOT / "longform" / "m5-theme-matrix.md"
REAL_BOOK_SOURCE_ENV = "HYPOLATEX_REAL_BOOK_SOURCE"

EXPECTED_THEME_IDS = (
    "academic-clean",
    "classic-readable",
    "plain",
    "tech-minimal",
    "warm-handbook",
)
NEW_THEME_IDS = ("tech-minimal", "warm-handbook", "academic-clean")
FIXTURE_THEME_IDS = ("warm-handbook", "academic-clean")
REQUIRED_COLOR_TOKENS = (
    "HypoInk",
    "HypoMuted",
    "HypoAccent",
    "HypoNoteBack",
    "HypoNoteFrame",
    "HypoNoteTitleBack",
    "HypoNoteTitleText",
    "HypoTipBack",
    "HypoTipFrame",
    "HypoTipTitleBack",
    "HypoTipTitleText",
    "HypoWarningBack",
    "HypoWarningFrame",
    "HypoWarningTitleBack",
    "HypoWarningTitleText",
    "HypoSummaryBack",
    "HypoSummaryFrame",
    "HypoSummaryTitleBack",
    "HypoSummaryTitleText",
    "HypoSemanticBack",
    "HypoSemanticFrame",
    "HypoSemanticTitleBack",
    "HypoSemanticTitleText",
    "HypoRequirementBack",
    "HypoRequirementFrame",
    "HypoRequirementTitleBack",
    "HypoRequirementTitleText",
    "HypoQuestionBack",
    "HypoQuestionFrame",
    "HypoQuestionTitleBack",
    "HypoQuestionTitleText",
    "HypoHintBack",
    "HypoHintFrame",
    "HypoHintTitleBack",
    "HypoHintTitleText",
    "HypoAnswerBack",
    "HypoAnswerFrame",
    "HypoAnswerTitleBack",
    "HypoAnswerTitleText",
    "HypoSolutionBack",
    "HypoSolutionFrame",
    "HypoSolutionTitleBack",
    "HypoSolutionTitleText",
    "HypoRubricBack",
    "HypoRubricFrame",
    "HypoRubricTitleBack",
    "HypoRubricTitleText",
)
MIN_FULL_BOOK_PDF_BYTES = 50_000
MIN_FIXTURE_PDF_BYTES = 1_024


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _theme_file(theme_id: str) -> Path:
    return TEX_PACKAGE_ROOT / f"hypolatex-theme-{theme_id}.sty"


def _defined_html_colors(path: Path) -> dict[str, str]:
    text = _read_text(path)
    return {
        name: value.upper()
        for name, value in re.findall(
            r"\\definecolor\{([^}]+)\}\{HTML\}\{([0-9A-Fa-f]{6})\}",
            text,
        )
    }


def _extract_pdf_text(pdf_path: Path) -> str:
    from hypolatex import pdf_evidence

    return pdf_evidence.extract_text(pdf_path)


def _real_book_source() -> Path:
    configured = os.environ.get(REAL_BOOK_SOURCE_ENV)
    if not configured:
        pytest.skip(f"{REAL_BOOK_SOURCE_ENV} is not set")

    source = Path(configured).expanduser()
    if not source.is_absolute():
        source = (Path.cwd() / source).resolve(strict=False)
    if not source.is_file():
        pytest.skip(f"{REAL_BOOK_SOURCE_ENV} does not point to a file: {source}")
    return source


def _contains_text(pdf_text: str, expected: str) -> bool:
    compact_text = re.sub(r"\s+", "", pdf_text)
    compact_expected = re.sub(r"\s+", "", expected)
    return expected in pdf_text or compact_expected in compact_text


def _invoke_build(runner, cli_app, input_path: Path, output_path: Path, theme: str):
    return runner.invoke(
        cli_app,
        [
            "build",
            str(input_path),
            "--theme",
            theme,
            "--output",
            str(output_path),
        ],
    )


def _assert_pdf_contains_markers(pdf_path: Path, markers: tuple[str, ...]) -> None:
    pdf_text = _extract_pdf_text(pdf_path)
    missing = [marker for marker in markers if not _contains_text(pdf_text, marker)]
    assert not missing, f"{pdf_path} is missing extracted text markers: {missing}"


def test_m5_registry_contains_complete_book_theme_matrix():
    from hypolatex import themes

    assert themes.valid_theme_ids() == EXPECTED_THEME_IDS

    for theme_id in NEW_THEME_IDS:
        theme_config = themes.THEME_REGISTRY[theme_id]
        assert theme_config.get("latex_theme") == theme_id
        assert theme_config.get("alias_of") not in {"plain", "classic-readable"}


@pytest.mark.parametrize("theme_id", NEW_THEME_IDS)
def test_m5_new_themes_have_real_latex_theme_files(theme_id):
    theme_file = _theme_file(theme_id)

    assert theme_file.is_file(), (
        f"M5 must add a real LaTeX package for {theme_id!r}; registry-only "
        "theme IDs do not satisfy the validation matrix."
    )

    source = _read_text(theme_file)
    assert f"hypolatex-theme-{theme_id}" in source
    assert theme_id in source


@pytest.mark.parametrize("theme_id", NEW_THEME_IDS)
def test_m5_new_themes_define_token_sets_distinct_from_classic_readable(theme_id):
    theme_file = _theme_file(theme_id)
    assert theme_file.is_file(), f"Missing M5 theme file: {theme_file}"

    classic_colors = _defined_html_colors(CLASSIC_READABLE_THEME_FILE)
    theme_colors = _defined_html_colors(theme_file)

    missing = sorted(set(REQUIRED_COLOR_TOKENS).difference(theme_colors))
    assert not missing, f"{theme_id} is missing required theme tokens: {missing}"

    changed_from_classic = [
        token
        for token in REQUIRED_COLOR_TOKENS
        if theme_colors[token] != classic_colors.get(token)
    ]
    assert len(changed_from_classic) >= 6, (
        f"{theme_id} should have observable token/style differences from "
        "classic-readable, not a copied palette."
    )


def test_m5_new_theme_token_sets_are_pairwise_distinct():
    token_sets = {}
    for theme_id in NEW_THEME_IDS:
        theme_file = _theme_file(theme_id)
        assert theme_file.is_file(), f"Missing M5 theme file: {theme_file}"
        token_sets[theme_id] = _defined_html_colors(theme_file)

    for left, right in combinations(NEW_THEME_IDS, 2):
        changed_tokens = [
            token
            for token in REQUIRED_COLOR_TOKENS
            if token_sets[left].get(token) != token_sets[right].get(token)
        ]
        assert len(changed_tokens) >= 4, (
            f"{left} and {right} should not share the same visible token set."
        )


def test_hypolatex_package_can_select_each_m5_theme_file():
    package_source = _read_text(HYPOLATEX_PACKAGE_FILE)

    for theme_id in NEW_THEME_IDS:
        assert f"hypolatex-theme-{theme_id}" in package_source
        assert theme_id in package_source


@pytest.mark.slow
def test_tech_minimal_builds_full_real_book_to_tmp_path(runner, cli_app, tmp_path):
    source = _real_book_source()
    output_path = tmp_path / "real-book-tech-minimal.pdf"

    result = _invoke_build(
        runner,
        cli_app,
        source,
        output_path,
        "tech-minimal",
    )

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_FULL_BOOK_PDF_BYTES

    pdf_text = _extract_pdf_text(output_path)
    expected_markers = ("AI 入门教程", "前言", "第一章", "附录")
    found = [
        marker
        for marker in expected_markers
        if _contains_text(pdf_text, marker)
    ]
    assert len(found) >= 3, (
        "tech-minimal real-book PDF should retain several expected Chinese "
        f"book markers; found only {found}."
    )


@pytest.mark.slow
@pytest.mark.parametrize("theme_id", FIXTURE_THEME_IDS)
def test_remaining_m5_themes_build_longform_fixture_with_required_content(
    runner,
    cli_app,
    tmp_path,
    theme_id,
):
    output_path = tmp_path / f"m5-longform-{theme_id}.pdf"

    result = _invoke_build(
        runner,
        cli_app,
        M5_LONGFORM_FIXTURE,
        output_path,
        theme_id,
    )

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_FIXTURE_PDF_BYTES
    _assert_pdf_contains_markers(
        output_path,
        (
            "主题矩阵验证",
            "中文证据文本",
            "Note",
            "Theme matrix validation flow",
            "覆盖点",
        ),
    )
