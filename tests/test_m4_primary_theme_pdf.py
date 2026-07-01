from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import importlib
import re
import shutil
import subprocess

import pytest
from typer.testing import CliRunner


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(__file__).parent
THEME_FIXTURE_ROOT = TEST_ROOT / "fixtures" / "themes"
THEME_FIRST_FIXTURE = THEME_FIXTURE_ROOT / "theme-first-classic.md"
TEX_PACKAGE_ROOT = REPO_ROOT / "tex" / "latex" / "hypolatex"
PLAIN_THEME_FILE = TEX_PACKAGE_ROOT / "hypolatex-theme-plain.sty"
CLASSIC_READABLE_THEME_FILE = (
    TEX_PACKAGE_ROOT / "hypolatex-theme-classic-readable.sty"
)
HYPOLATEX_PACKAGE_FILE = TEX_PACKAGE_ROOT / "hypolatex.sty"
CALLOUTS_FILE = TEX_PACKAGE_ROOT / "hypolatex-callouts.sty"
LAYOUT_FILE = TEX_PACKAGE_ROOT / "hypolatex-layout.sty"
CLASSIC_READABLE_COVER_ASSET = (
    TEX_PACKAGE_ROOT / "hypolatex-cover-classic-readable-integrated.png"
)
REAL_BOOK_SOURCE_ENV = "HYPOLATEX_REAL_BOOK_SOURCE"
MIN_FULL_BOOK_PDF_BYTES = 50_000
MIN_SCREENSHOT_BYTES = 1_000
CALLOUT_KINDS = ("Note", "Tip", "Warning", "Summary")
REPRESENTATIVE_SCREENSHOT_CATEGORIES = (
    "cover",
    "toc",
    "chapter-opener",
    "callout",
    "figure",
    "table-appendix",
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter_block(path: Path) -> str:
    text = _read_text(path)
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter."
    end = text.index("\n---", 4)
    return text[4:end].strip()


def _defined_html_colors(path: Path) -> dict[str, str]:
    text = _read_text(path)
    return {
        name: value.upper()
        for name, value in re.findall(
            r"\\definecolor\{([^}]+)\}\{HTML\}\{([0-9A-Fa-f]{6})\}",
            text,
        )
    }


def _relative_luminance(hex_color: str) -> float:
    channels = tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def linearize(channel: float) -> float:
        if channel <= 0.03928:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linearize(channel) for channel in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast_ratio(foreground: str, background: str) -> float:
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    lighter = max(first, second)
    darker = min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def _pdf_evidence_module():
    try:
        return importlib.import_module("hypolatex.pdf_evidence")
    except ModuleNotFoundError as exc:
        if exc.name != "hypolatex.pdf_evidence":
            raise
        pytest.fail(
            "Expected hypolatex.pdf_evidence with read_pdf_info(), "
            "extract_text(), and render_page_png() helpers.",
            pytrace=False,
        )


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


def _extract_page_text(pdf_path: Path, page: int) -> str:
    executable = shutil.which("pdftotext")
    assert executable is not None, (
        "pdftotext is required to verify M4 screenshot page categories."
    )

    result = subprocess.run(
        [
            executable,
            "-f",
            str(page),
            "-l",
            str(page),
            str(pdf_path),
            "-",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _page_has_markers(page_text: str, markers: tuple[str, ...]) -> bool:
    return all(_contains_text(page_text, marker) for marker in markers)


def _page_has_any_marker(page_text: str, markers: tuple[str, ...]) -> bool:
    return any(_contains_text(page_text, marker) for marker in markers)


def _page_has_figure_caption(page_text: str) -> bool:
    return re.search(r"图\s+\d+(?:\.\d+)?:", page_text) is not None


def _find_representative_page(
    page_texts: Mapping[int, str],
    category: str,
    candidates: range,
    excluded_pages: set[int],
    predicate,
) -> int:
    for page in candidates:
        if page in excluded_pages:
            continue
        if predicate(page_texts[page]):
            return page

    pytest.fail(
        f"Expected a distinct {category} screenshot page with stable page-text "
        "markers. If real-book pagination changes, update this evidence mapping "
        "or expose equivalent named page metadata; do not fall back to an "
        "arbitrary middle page.",
        pytrace=False,
    )


def _representative_pages(pdf_path: Path, total_pages: int) -> Mapping[str, int]:
    assert total_pages >= 8, (
        "The full real-book inspection PDF should have enough pages to render "
        "cover, front matter, body, and back matter evidence."
    )
    page_texts = {
        page: _extract_page_text(pdf_path, page)
        for page in range(1, total_pages + 1)
    }
    selected: dict[str, int] = {}
    excluded: set[int] = set()

    selected["cover"] = _find_representative_page(
        page_texts,
        "cover",
        range(1, 2),
        excluded,
        lambda text: _page_has_markers(
            text,
            ("AI 入门教程", "实用指南"),
        ),
    )
    excluded.add(selected["cover"])

    selected["toc"] = _find_representative_page(
        page_texts,
        "toc",
        range(2, min(total_pages, 8) + 1),
        excluded,
        lambda text: _page_has_markers(text, ("目录", "第一章")),
    )
    excluded.add(selected["toc"])

    selected["chapter-opener"] = _find_representative_page(
        page_texts,
        "chapter opener",
        range(2, min(total_pages, 24) + 1),
        excluded,
        lambda text: _page_has_markers(
            text,
            ("第一章：AI 能做什么", "1.1 AI 现在到底能干什么"),
        ),
    )
    excluded.add(selected["chapter-opener"])

    selected["callout"] = _find_representative_page(
        page_texts,
        "callout",
        range(1, total_pages + 1),
        excluded,
        lambda text: _page_has_any_marker(text, CALLOUT_KINDS),
    )
    excluded.add(selected["callout"])

    selected["figure"] = _find_representative_page(
        page_texts,
        "figure",
        range(1, total_pages + 1),
        excluded,
        _page_has_figure_caption,
    )
    excluded.add(selected["figure"])

    selected["table-appendix"] = _find_representative_page(
        page_texts,
        "table/appendix",
        range(max(1, total_pages - 20), total_pages + 1),
        excluded,
        lambda text: _page_has_markers(
            text,
            ("附录", "国内主流 AI 平台速查表", "豆包"),
        ),
    )

    assert tuple(selected) == REPRESENTATIVE_SCREENSHOT_CATEGORIES
    assert len(set(selected.values())) == len(selected), selected
    return selected


@pytest.fixture(scope="module")
def m4_final_real_book_pdf(tmp_path_factory):
    source = _real_book_source()
    output_path = tmp_path_factory.mktemp("real-book") / "real-book-primary-theme.pdf"

    from hypolatex.cli import app

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "build",
            str(source),
            "--theme",
            "classic-readable",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_FULL_BOOK_PDF_BYTES
    return output_path


def test_m4_keeps_m3_theme_first_contract(runner, cli_app, tmp_path):
    frontmatter = _frontmatter_block(THEME_FIRST_FIXTURE)
    frontmatter_lines = tuple(
        line.strip() for line in frontmatter.splitlines() if line.strip()
    )
    assert frontmatter_lines == ("theme: classic-readable",)

    output_path = tmp_path / "theme-first-classic.tex"
    result = runner.invoke(
        cli_app,
        ["convert", str(THEME_FIRST_FIXTURE), "--output", str(output_path)],
    )

    assert result.exit_code == 0, result.output
    assert "\\HypoUseTheme{classic-readable}" in _read_text(output_path)


def test_classic_readable_registry_is_not_plain_alias():
    from hypolatex import themes

    classic = themes.THEME_REGISTRY["classic-readable"]
    plain = themes.THEME_REGISTRY["plain"]

    assert classic.get("alias_of") != "plain", (
        "M4 must replace the M3 alias-level preset with real classic-readable "
        "theme behavior."
    )
    assert classic.get("latex_theme") == "classic-readable"
    assert classic != plain


def test_classic_readable_theme_file_defines_distinct_book_tokens():
    assert CLASSIC_READABLE_THEME_FILE.is_file(), (
        "M4 should add a LaTeX theme file for the public classic-readable theme "
        "instead of reusing hypolatex-theme-plain.sty."
    )

    plain_colors = _defined_html_colors(PLAIN_THEME_FILE)
    classic_colors = _defined_html_colors(CLASSIC_READABLE_THEME_FILE)
    required_tokens = {
        "HypoInk",
        "HypoMuted",
        "HypoAccent",
        "HypoNoteBack",
        "HypoTipBack",
        "HypoWarningBack",
        "HypoSummaryBack",
    }

    missing = sorted(required_tokens.difference(classic_colors))
    assert not missing, f"classic-readable is missing theme tokens: {missing}"

    changed_tokens = [
        token
        for token in required_tokens
        if classic_colors[token] != plain_colors.get(token)
    ]
    assert len(changed_tokens) >= 4, (
        "classic-readable should have observable token choices for a Chinese "
        "longform book, not only the same colors as plain."
    )

    classic_source = _read_text(CLASSIC_READABLE_THEME_FILE)
    assert "hypolatex-theme-classic-readable" in classic_source
    assert "classic-readable" in classic_source


def test_hypolatex_package_can_select_classic_readable_theme_file():
    package_source = _read_text(HYPOLATEX_PACKAGE_FILE)

    assert "hypolatex-theme-classic-readable" in package_source, (
        "\\HypoUseTheme{classic-readable} must load/select the real "
        "classic-readable theme file, not only rename \\HypoThemeName."
    )


def test_classic_readable_cover_uses_packaged_background_asset():
    assert CLASSIC_READABLE_COVER_ASSET.is_file(), (
        "classic-readable should ship a reusable cover image asset instead of "
        "requiring each Markdown source tree to carry the same generated file."
    )
    assert CLASSIC_READABLE_COVER_ASSET.stat().st_size > MIN_SCREENSHOT_BYTES
    assert CLASSIC_READABLE_COVER_ASSET.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    layout_source = _read_text(LAYOUT_FILE)
    assert "hypolatex-cover-classic-readable-integrated.png" in layout_source
    assert "integrated-art" in layout_source
    assert "\\ifdefstring{\\HypoThemeName}{classic-readable}" in layout_source
    assert "AddToShipoutPictureBG" in layout_source
    assert "\\HypoIfMetadataTF{version}" not in layout_source


def test_callout_boxes_use_title_contrast_tokens():
    callout_source = _read_text(CALLOUTS_FILE)

    assert "coltitle=HypoInk" not in callout_source, (
        "Callout titles should not keep using body ink on every title strip; "
        "M4 needs dedicated title text/background tokens to avoid the C1 "
        "dark-title-bar-with-black-text contrast failure."
    )

    for kind in CALLOUT_KINDS:
        assert f"colbacktitle=Hypo{kind}TitleBack" in callout_source
        assert f"coltitle=Hypo{kind}TitleText" in callout_source


def test_classic_readable_callout_title_tokens_have_safe_contrast():
    assert CLASSIC_READABLE_THEME_FILE.is_file(), (
        "classic-readable must define callout title colors for contrast checks."
    )
    colors = _defined_html_colors(CLASSIC_READABLE_THEME_FILE)

    for kind in CALLOUT_KINDS:
        background_token = f"Hypo{kind}TitleBack"
        text_token = f"Hypo{kind}TitleText"
        assert background_token in colors
        assert text_token in colors

        background = colors[background_token]
        text = colors[text_token]
        ratio = _contrast_ratio(text, background)
        assert ratio >= 4.5, (
            f"{kind} callout title contrast is {ratio:.2f}:1; expected at "
            "least 4.5:1."
        )
        if _relative_luminance(background) < 0.30:
            assert _relative_luminance(text) > 0.70, (
                f"{kind} uses a dark title background, so the title text token "
                "must be light rather than black/dark ink."
            )


@pytest.mark.slow
def test_full_real_book_builds_classic_readable_to_tmp_path(
    m4_final_real_book_pdf,
):
    assert m4_final_real_book_pdf.is_file()
    assert m4_final_real_book_pdf.stat().st_size > MIN_FULL_BOOK_PDF_BYTES


@pytest.mark.slow
def test_final_real_book_pdf_text_contains_expected_chinese_sections(
    m4_final_real_book_pdf,
):
    pdf_evidence = _pdf_evidence_module()

    pdf_text = pdf_evidence.extract_text(m4_final_real_book_pdf)

    assert any(
        _contains_text(pdf_text, expected)
        for expected in ("前言", "AI 入门教程")
    )
    for expected in ("第一章", "附录"):
        assert _contains_text(pdf_text, expected)
    assert not _contains_text(pdf_text, "v1.0-draft")


@pytest.mark.slow
def test_final_real_book_representative_screenshots_are_rendered(
    m4_final_real_book_pdf,
    tmp_path,
):
    pdf_evidence = _pdf_evidence_module()

    info = pdf_evidence.read_pdf_info(m4_final_real_book_pdf)
    total_pages = int(info["pages"])
    pages = _representative_pages(m4_final_real_book_pdf, total_pages)

    screenshot_dir = tmp_path / "m4-primary-theme-screenshots"
    for category, page in pages.items():
        screenshot_path = pdf_evidence.render_page_png(
            m4_final_real_book_pdf,
            output_dir=screenshot_dir,
            page=page,
            stem=f"real-book-{category}-page-{page}",
        )

        assert screenshot_path.suffix == ".png"
        assert screenshot_path.is_file()
        assert screenshot_path.stat().st_size > MIN_SCREENSHOT_BYTES
        assert screenshot_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
