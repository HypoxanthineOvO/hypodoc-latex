from __future__ import annotations

import base64
import os
from pathlib import Path
import shutil
import subprocess

import pytest


TEST_ROOT = Path(__file__).parent
FIXTURE_ROOT = TEST_ROOT / "fixtures" / "m1"
REAL_BOOK_SOURCE_ENV = "HYPOLATEX_REAL_BOOK_SOURCE"
MIN_PDF_BYTES = 1024
FIGURE_PLACEHOLDER_TEXT = "Figure asset unavailable"
TINY_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1Pe"
    "AAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def _invoke_build(runner, cli_app, input_path, output_path):
    return runner.invoke(
        cli_app,
        ["build", str(input_path), "--output", str(output_path)],
    )


def _assert_non_empty_pdf(output_path):
    assert output_path.suffix == ".pdf"
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES


def _extract_pdf_text(pdf_path):
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext is required for PDF text assertions.")

    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


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


def _assert_pdf_text_contains(pdf_text, expected_fragments):
    for expected in expected_fragments:
        assert expected in pdf_text


def test_build_compiles_pandoc_tightlist_fixture(runner, cli_app, tmp_path):
    input_path = FIXTURE_ROOT / "pandoc-tightlist.md"
    output_path = tmp_path / "pandoc-tightlist.pdf"

    result = _invoke_build(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdf_text = _extract_pdf_text(output_path)
    _assert_pdf_text_contains(
        pdf_text,
        (
            "Checklist",
            "Keep metadata stable.",
            "Compile compact lists.",
            "Preserve later prose.",
            "The build should reach the PDF stage without a missing macro error.",
        ),
    )


def test_build_compiles_minimal_markdown_table_fixture(runner, cli_app, tmp_path):
    input_path = FIXTURE_ROOT / "basic-table.md"
    output_path = tmp_path / "basic-table.pdf"

    result = _invoke_build(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdf_text = _extract_pdf_text(output_path)
    _assert_pdf_text_contains(
        pdf_text,
        (
            "Basic Table",
            "Concept",
            "Status",
            "Lists",
            "Tables",
            "The document should continue after the table.",
        ),
    )
    assert pdf_text.count("Required") >= 2


def test_build_resolves_project_root_relative_figure_without_placeholder(
    runner,
    cli_app,
    tmp_path,
):
    project_root = tmp_path / "source-book"
    article_dir = project_root / "article"
    asset_dir = project_root / "assets"
    article_dir.mkdir(parents=True)
    asset_dir.mkdir()

    input_path = article_dir / "book-hypolatex.md"
    image_path = asset_dir / "source-root-diagram.png"
    output_path = tmp_path / "source-root-resources.pdf"

    image_path.write_bytes(base64.b64decode(TINY_PNG))
    input_path.write_text(
        """---
title: Source Root Resource Fixture
author: M1 Test Worker
theme: plain
---

# Source Root Figure

This fixture mirrors a source-root book shape: the Markdown file lives under
`article/`, while figure assets are addressed from the project root.

::: {.figure label="fig:source-root" src="assets/source-root-diagram.png" caption="Source root diagram"}
:::
""",
        encoding="utf-8",
    )

    result = _invoke_build(runner, cli_app, input_path, output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdf_text = _extract_pdf_text(output_path)
    assert "Source root diagram" in pdf_text
    assert FIGURE_PLACEHOLDER_TEXT not in pdf_text
    assert "source-root-diagram.png" not in pdf_text


def test_build_resolves_project_root_figure_when_invoked_from_article_dir(
    runner,
    cli_app,
    tmp_path,
    monkeypatch,
):
    project_root = tmp_path / "source-book"
    article_dir = project_root / "article"
    asset_dir = project_root / "assets"
    article_dir.mkdir(parents=True)
    asset_dir.mkdir()

    input_path = article_dir / "book-hypolatex.md"
    image_path = asset_dir / "source-root-diagram.png"
    output_path = tmp_path / "source-root-resources-from-article.pdf"

    image_path.write_bytes(base64.b64decode(TINY_PNG))
    input_path.write_text(
        """---
title: Source Root Resource Fixture
author: M1 Test Worker
theme: plain
---

# Source Root Figure

This fixture mirrors running `hypolatex build book-hypolatex.md` from the
article directory while the assets live in the project root.

::: {.figure label="fig:source-root" src="assets/source-root-diagram.png" caption="Source root diagram" width="0.92" placement="H"}
:::
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(article_dir)
    result = _invoke_build(runner, cli_app, Path("book-hypolatex.md"), output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdf_text = _extract_pdf_text(output_path)
    assert "Source root diagram" in pdf_text
    assert FIGURE_PLACEHOLDER_TEXT not in pdf_text
    assert "source-root-diagram.png" not in pdf_text


@pytest.mark.slow
def test_slow_real_book_build_writes_only_to_tmp_path(runner, cli_app, tmp_path):
    source = _real_book_source()
    output_path = tmp_path / "real-book-baseline.pdf"

    result = _invoke_build(runner, cli_app, source, output_path)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)
    pdf_text = _extract_pdf_text(output_path)
    assert FIGURE_PLACEHOLDER_TEXT not in pdf_text
    for expected in (
        "AI \u5165\u95e8\u6559\u7a0b",
        "\u7b2c\u4e00\u7ae0",
        "\u9644\u5f55",
    ):
        assert expected in pdf_text
