import re
from pathlib import Path


TEST_ROOT = Path(__file__).parent
FIXTURE_ROOT = TEST_ROOT / "fixtures"
THEME_FIXTURE_ROOT = FIXTURE_ROOT / "themes"
THEME_FIRST_FIXTURE = THEME_FIXTURE_ROOT / "theme-first-classic.md"
INVALID_THEME_FIXTURE = THEME_FIXTURE_ROOT / "invalid-theme.md"
PLAIN_COMPAT_FIXTURE = FIXTURE_ROOT / "longform" / "tutorial.md"
TEX_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "tex" / "latex" / "hypolatex"
HYPOLATEX_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex.sty"
LAYOUT_FILE = TEX_PACKAGE_ROOT / "hypolatex-layout.sty"
CLASSIC_THEME_FILE = TEX_PACKAGE_ROOT / "hypolatex-theme-classic-readable.sty"
TECH_THEME_FILE = TEX_PACKAGE_ROOT / "hypolatex-theme-tech-minimal.sty"
WARM_THEME_FILE = TEX_PACKAGE_ROOT / "hypolatex-theme-warm-handbook.sty"
ACADEMIC_THEME_FILE = TEX_PACKAGE_ROOT / "hypolatex-theme-academic-clean.sty"
MIN_PDF_BYTES = 1024

ADVANCED_FRONTMATTER_FIELDS = (
    "font",
    "fonts",
    "mainfont",
    "sansfont",
    "monofont",
    "cjkfont",
    "paper",
    "paper_size",
    "accent",
    "accent_color",
    "spacing",
    "cover_layout",
    "cover_image",
)


def _read_text(path):
    return path.read_text(encoding="utf-8")


def _frontmatter_block(path):
    text = _read_text(path)
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter."
    end = text.index("\n---", 4)
    return text[4:end].strip()


def _invoke_convert(runner, cli_app, input_path, output_path, theme=None):
    args = ["convert", str(input_path), "--output", str(output_path)]
    if theme is not None:
        args.extend(["--theme", theme])
    return runner.invoke(cli_app, args)


def _invoke_build(runner, cli_app, input_path, output_path, theme=None, env=None):
    args = ["build", str(input_path), "--output", str(output_path)]
    if theme is not None:
        args.extend(["--theme", theme])
    return runner.invoke(cli_app, args, env=env)


def _theme_selection_markers(theme_id):
    return (
        f"theme={theme_id}",
        f"[{theme_id}]{{hypolatex}}",
        f"\\HypoUseTheme{{{theme_id}}}",
        f"\\HypoSelectTheme{{{theme_id}}}",
        f"\\HypoSetTheme{{{theme_id}}}",
        f"hypolatex-theme-{theme_id}",
    )


def _has_theme_selection(tex, theme_id):
    compact_tex = re.sub(r"\s+", "", tex)
    return any(
        marker in tex or marker in compact_tex
        for marker in _theme_selection_markers(theme_id)
    )


def _assert_theme_selected(tex, theme_id):
    assert _has_theme_selection(tex, theme_id), (
        f"Expected generated LaTeX to load or select theme {theme_id!r}. "
        "Recording the theme only as \\HypoSetMetadata{theme}{...} is not enough "
        "for the M3 preset plumbing contract."
    )


def test_theme_first_ai_frontmatter_only_requires_theme(runner, cli_app, tmp_path):
    frontmatter = _frontmatter_block(THEME_FIRST_FIXTURE)
    frontmatter_lines = tuple(
        line.strip() for line in frontmatter.splitlines() if line.strip()
    )
    assert frontmatter_lines == ("theme: classic-readable",)
    for field in ADVANCED_FRONTMATTER_FIELDS:
        assert re.search(rf"^{re.escape(field)}\s*:", frontmatter, re.MULTILINE) is None

    output_path = tmp_path / "theme-first.tex"
    result = _invoke_convert(runner, cli_app, THEME_FIRST_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    for field in ADVANCED_FRONTMATTER_FIELDS:
        assert f"\\HypoSetMetadata{{{field}}}" not in tex


def test_frontmatter_theme_selects_classic_readable_in_generated_latex(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "classic-readable.tex"

    result = _invoke_convert(runner, cli_app, THEME_FIRST_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    _assert_theme_selected(_read_text(output_path), "classic-readable")


def test_cli_theme_overrides_frontmatter_theme_in_generated_latex(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "override.tex"

    result = _invoke_convert(
        runner,
        cli_app,
        THEME_FIRST_FIXTURE,
        output_path,
        theme="plain",
    )

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    _assert_theme_selected(tex, "plain")
    assert not _has_theme_selection(tex, "classic-readable")


def test_invalid_theme_fails_before_toolchain_and_lists_valid_theme_ids(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "invalid-theme.pdf"

    result = _invoke_build(
        runner,
        cli_app,
        INVALID_THEME_FIXTURE,
        output_path,
        env={"PATH": ""},
    )

    assert result.exit_code != 0
    assert not output_path.exists()
    diagnostic = f"{result.output}\n{result.exception or ''}".lower()
    assert "theme" in diagnostic
    assert any(marker in diagnostic for marker in ("invalid", "unknown", "unsupported"))
    assert "vaporwave-debug" in diagnostic
    for valid_theme in ("classic-readable", "plain"):
        assert valid_theme in diagnostic
    for late_failure in ("latexmk", "xelatex", "pandoc"):
        assert late_failure not in diagnostic


def test_existing_plain_theme_document_remains_convertible(runner, cli_app, tmp_path):
    output_path = tmp_path / "plain-compat.tex"

    result = _invoke_convert(runner, cli_app, PLAIN_COMPAT_FIXTURE, output_path)

    assert result.exit_code == 0, result.output
    tex = _read_text(output_path)
    assert "{hypolatex}" in tex
    assert "\\HypoSetMetadata{theme}{plain}" in tex or _has_theme_selection(tex, "plain")
    assert "\\begin{HypoNote}" in tex
    assert "Building Reliable AI Tutorials" in tex


def test_build_accepts_small_cli_selected_theme_fixture(runner, cli_app, tmp_path):
    output_path = tmp_path / "theme-selected.pdf"

    result = _invoke_build(
        runner,
        cli_app,
        THEME_FIRST_FIXTURE,
        output_path,
        theme="classic-readable",
    )

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES


def test_theme_font_sets_record_preferred_chinese_font_roles():
    package_source = _read_text(HYPOLATEX_PACKAGE_FILE)
    layout_source = _read_text(LAYOUT_FILE)

    for expected in (
        "HypoUseReadableFonts",
        "HypoUseTechFonts",
        "HypoUseWarmFonts",
        "HypoUseAcademicFonts",
        "HypoSemanticTitleFont",
        "HypoQuestionTitleFont",
        "HypoAnswerTitleFont",
        "HypoRubricTitleFont",
        "HypoSerifModuleFont",
        "Noto Serif CJK SC Black",
        "Noto Serif CJK SC Bold",
        "Sarasa Gothic SC",
        "LXGW WenKai",
        "LXGW WenKai Mono",
        "Noto Serif CJK SC",
    ):
        assert expected in package_source

    assert "MiSans" not in package_source

    assert "HypoChapterTitleFont" in layout_source
    assert "HypoCoverTitleFont" in layout_source

    assert "HypoUseReadableFonts" in _read_text(CLASSIC_THEME_FILE)
    assert "HypoUseTechFonts" in _read_text(TECH_THEME_FILE)
    assert "HypoUseWarmFonts" in _read_text(WARM_THEME_FILE)
    assert "HypoUseAcademicFonts" in _read_text(ACADEMIC_THEME_FILE)
