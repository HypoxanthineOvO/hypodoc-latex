from __future__ import annotations

import importlib
import re
import textwrap
from collections.abc import Mapping
from pathlib import Path

import pytest


def _slides_module():
    try:
        return importlib.import_module("hypolatex.slides")
    except ModuleNotFoundError as exc:
        if exc.name != "hypolatex.slides":
            raise
        pytest.fail(
            "Expected src/hypolatex/slides.py with SlideOptions, SlidesError, "
            "resolve_slide_options(), and normalize_slides_markdown().",
            pytrace=False,
        )


def _write_deck(path: Path, markdown: str) -> Path:
    path.write_text(textwrap.dedent(markdown).lstrip(), encoding="utf-8")
    return path


def _option_value(options, name: str):
    if isinstance(options, Mapping):
        return options[name]
    return getattr(options, name)


def _resolve_slide_options(module, input_path: Path):
    resolver = getattr(module, "resolve_slide_options", None)
    assert resolver is not None, "slides must expose resolve_slide_options(input_path)."
    return resolver(input_path)


def _normalize_deck(module, input_path: Path, options=None) -> str:
    normalizer = getattr(module, "normalize_slides_markdown", None)
    assert normalizer is not None, (
        "slides must expose normalize_slides_markdown(input_path_or_text, options=...)."
    )
    if options is None:
        options = _resolve_slide_options(module, input_path)
    result = normalizer(input_path, options=options)
    return _normalized_markdown(result)


def _normalized_markdown(result) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, tuple) and result and isinstance(result[0], str):
        return result[0]
    markdown = getattr(result, "markdown", None)
    if isinstance(markdown, str):
        return markdown
    normalized = getattr(result, "normalized_markdown", None)
    if isinstance(normalized, str):
        return normalized
    pytest.fail(
        "normalize_slides_markdown must return Markdown as a string, tuple first "
        "item, .markdown, or .normalized_markdown.",
        pytrace=False,
    )


def _slides_error_type(module):
    error_type = getattr(module, "SlidesError", None)
    assert error_type is not None, "slides must expose SlidesError for lint diagnostics."
    return error_type


def _assert_lint_error(module, input_path: Path, fragments: tuple[str, ...]) -> str:
    with pytest.raises(_slides_error_type(module)) as excinfo:
        _normalize_deck(module, input_path)

    diagnostic = str(excinfo.value).lower()
    for fragment in fragments:
        assert fragment in diagnostic
    return diagnostic


def _heading_lines_outside_fences(markdown: str, level: int) -> list[str]:
    fence_re = re.compile(r"^\s*(```|~~~)")
    heading_re = re.compile(rf"^ {{0,3}}#{{{level}}}\s+")
    in_fence = False
    headings: list[str] = []

    for line in markdown.splitlines():
        if fence_re.match(line):
            in_fence = not in_fence
            continue
        if not in_fence and heading_re.match(line):
            headings.append(line.strip())

    return headings


def test_slide_options_default_contract(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "defaults.md",
        """
        ---
        document_type: beamer
        ---

        ### Opening

        Body.
        """,
    )

    options = _resolve_slide_options(module, input_path)

    assert _option_value(options, "section_dividers") is True
    assert _option_value(options, "subsection_dividers") is False
    assert _option_value(options, "frame_title_inheritance_limit") == 3
    assert _option_value(options, "continued_title_style") == "subtle"
    assert _option_value(options, "strict_structure") is True


def test_slide_options_frontmatter_overrides_are_parsed(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "overrides.md",
        """
        ---
        document_type: beamer
        section_dividers: false
        subsection_dividers: true
        frame_title_inheritance_limit: 1
        continued_title_style: suffix
        strict_structure: false
        ---

        ### Opening

        Body.
        """,
    )

    options = _resolve_slide_options(module, input_path)

    assert _option_value(options, "section_dividers") is False
    assert _option_value(options, "subsection_dividers") is True
    assert _option_value(options, "frame_title_inheritance_limit") == 1
    assert _option_value(options, "continued_title_style") == "suffix"
    assert _option_value(options, "strict_structure") is False


@pytest.mark.parametrize(
    ("deck_name", "markdown", "expected_headings"),
    [
        (
            "full-hierarchy",
            """
            # Section

            ## Subsection

            ### Frame

            Body.
            """,
            ("# Section", "## Subsection", "### Frame"),
        ),
        (
            "section-to-frame",
            """
            # Section

            ### Frame Without Subsection

            Body.
            """,
            ("# Section", "### Frame Without Subsection"),
        ),
        (
            "h3-only",
            """
            ### Standalone Frame

            Body.
            """,
            ("### Standalone Frame",),
        ),
    ],
)
def test_slides_valid_heading_structures_normalize_without_lint_error(
    tmp_path,
    deck_name,
    markdown,
    expected_headings,
):
    module = _slides_module()
    input_path = _write_deck(tmp_path / f"{deck_name}.md", markdown)

    normalized = _normalize_deck(module, input_path)

    for heading in expected_headings:
        assert heading in normalized
    assert "Body." in normalized


def test_slides_separator_opens_frame_with_explicit_inherited_title(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "inherit-title.md",
        """
        # Analysis

        ### Result

        First point.

        ---

        Second point.
        """,
    )

    normalized = _normalize_deck(module, input_path)
    frame_headings = _heading_lines_outside_fences(normalized, 3)

    assert frame_headings[0] == "### Result"
    assert len(frame_headings) == 2
    assert frame_headings[1].startswith("### Result")
    assert re.search(
        r"\b(continued|cont\.|part\s+2|2\s*/|2\s+of)\b",
        frame_headings[1],
        flags=re.IGNORECASE,
    ), "inherited frame title must carry a visible continuation marker"
    assert normalized.index(frame_headings[1]) > normalized.index("---")


def test_slides_lints_h2_without_preceding_h1(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "orphan-subsection.md",
        """
        ## Orphan Subsection

        ### Frame

        Body.
        """,
    )

    _assert_lint_error(module, input_path, ("h2", "h1", "subsection"))


def test_slides_lints_empty_frame(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "empty-frame.md",
        """
        ### First

        Has content.

        ---

        ---

        ### Next

        Has content.
        """,
    )

    _assert_lint_error(module, input_path, ("empty", "frame"))


def test_slides_lints_missing_noninferable_title_after_context_change(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "missing-title-after-section.md",
        """
        # Background

        ### Motivation

        Context.

        ---

        More motivation.

        # Results

        ---

        Results content lacks a frame title after the section changed.
        """,
    )

    _assert_lint_error(module, input_path, ("frame title", "section", "results"))


def test_slides_lints_inherited_title_beyond_configured_limit(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "inheritance-limit.md",
        """
        ---
        document_type: beamer
        frame_title_inheritance_limit: 1
        ---

        ### Repeated Topic

        First frame.

        ---

        Second frame may inherit.

        ---

        Third frame exceeds the configured inheritance limit.
        """,
    )

    _assert_lint_error(module, input_path, ("inherit", "limit", "repeated topic"))


def test_slides_lints_obvious_overfull_frame(tmp_path):
    module = _slides_module()
    dense_items = "\n".join(
        f"- Dense bullet {index}: " + ("this sentence is intentionally long. " * 4)
        for index in range(1, 81)
    )
    input_path = _write_deck(
        tmp_path / "overfull.md",
        f"""
        ### Dense Frame

        {dense_items}
        """,
    )

    _assert_lint_error(module, input_path, ("overfull", "frame"))


def test_slides_rewrites_stretch_true_image_to_raw_latex_without_keepaspectratio(
    tmp_path,
):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "stretch-image.md",
        """
        ### Image Frame

        ![Architecture](assets/architecture.png){width=50% stretch=true}
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert r"\includegraphics" in normalized
    assert "{assets/architecture.png}" in normalized
    assert "keepaspectratio" not in normalized
    assert "stretch=true" not in normalized
    assert "![Architecture]" not in normalized


def test_slides_stretch_true_raw_latex_carries_width_and_height_attributes(
    tmp_path,
):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "stretch-image-size.md",
        """
        ### Image Frame

        ![Result](assets/result.png){width=50% height=40% stretch=true}
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert r"\includegraphics[width=0.50\textwidth,height=0.40\textheight]" in normalized
    assert "{assets/result.png}" in normalized


def test_slides_stretch_true_image_is_wrapped_in_center_environment(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "stretch-centered.md",
        """
        ### Image Frame

        ![Result](assets/result.png){width=50% stretch=true}
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert "\\begin{center}\n\\includegraphics[width=0.50\\textwidth]{assets/result.png}\n\\end{center}" in normalized


def test_slides_captioned_lone_image_is_left_to_pandoc_figure(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "ordinary-image.md",
        """
        ### Image Frame

        ![Chart](assets/chart.png){width=50%}
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert "![Chart](assets/chart.png){width=50%}" in normalized
    assert r"\includegraphics" not in normalized


def test_slides_centers_captionless_image_with_fit_box_defaults(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "captionless-image.md",
        """
        ### Image Frame

        ![](assets/chart.png){width=62%}
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert (
        "\\begin{center}\n"
        "\\includegraphics[width=0.62\\linewidth,height=0.75\\textheight,keepaspectratio]"
        "{assets/chart.png}\n"
        "\\end{center}"
    ) in normalized
    assert "![](assets/chart.png)" not in normalized


def test_slides_centers_unsized_captionless_image_with_linewidth_and_height_cap(
    tmp_path,
):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "unsized-image.md",
        """
        ### Image Frame

        ![](assets/chart.png)
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert (
        "\\includegraphics[width=\\linewidth,height=0.75\\textheight,keepaspectratio]"
        "{assets/chart.png}"
    ) in normalized
    assert "\\begin{center}" in normalized


def test_slides_centers_multi_image_row_in_single_center_environment(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "image-row.md",
        """
        ### Image Frame

        ![](assets/left.png){width=62%} ![](assets/right.png){width=30%}
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert normalized.count("\\begin{center}") == 1
    assert (
        "\\includegraphics[width=0.62\\linewidth,height=0.75\\textheight,keepaspectratio]"
        "{assets/left.png}"
    ) in normalized
    assert (
        "\\includegraphics[width=0.30\\linewidth,height=0.75\\textheight,keepaspectratio]"
        "{assets/right.png}"
    ) in normalized


def test_slides_leaves_indented_captionless_image_untouched(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "indented-image.md",
        """
        ### Image Frame

        - Bullet with illustration:
          ![](assets/chart.png){width=40%}
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert "  ![](assets/chart.png){width=40%}" in normalized
    assert r"\includegraphics" not in normalized


def test_slides_leaves_image_with_trailing_text_untouched(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "inline-image.md",
        """
        ### Image Frame

        ![](assets/icon.png){width=5%} inline icon usage stays markdown.
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert "![](assets/icon.png){width=5%} inline icon usage stays markdown." in normalized
    assert r"\includegraphics" not in normalized


def test_slides_does_not_rewrite_image_like_line_inside_fenced_code_block(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "fenced-stretch-image.md",
        """
        ### Code Sample

        ```markdown
        ![Chart](assets/chart.png){width=50% stretch=true}
        ```

        The fenced example must stay literal.
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert "![Chart](assets/chart.png){width=50% stretch=true}" in normalized
    assert r"\includegraphics" not in normalized


def test_slides_ignores_separators_and_headings_inside_fenced_code_blocks(tmp_path):
    module = _slides_module()
    input_path = _write_deck(
        tmp_path / "fenced-code.md",
        """
        # Demo

        ### Code Sample

        ```markdown
        # Not A Section
        ## Not A Subsection
        ### Not A Frame
        ---
        ```

        Explanation after the code block.
        """,
    )

    normalized = _normalize_deck(module, input_path)

    assert _heading_lines_outside_fences(normalized, 1) == ["# Demo"]
    assert _heading_lines_outside_fences(normalized, 2) == []
    assert _heading_lines_outside_fences(normalized, 3) == ["### Code Sample"]
    assert "### Not A Frame" in normalized
    assert "Explanation after the code block." in normalized
