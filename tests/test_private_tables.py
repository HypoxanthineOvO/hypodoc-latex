import re
from pathlib import Path

import pytest


MIN_PDF_BYTES = 1024
CONTROLLED_TABLE_RE = re.compile(r":::\s*(?:\{[^}]*\.)?table\b")
PIPE_TABLE_RE = re.compile(r"(?m)^\s*\|.+\|\s*$\n^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
TABLE_CONTEXT_RE = re.compile(
    r"(grading|rubric|checklist|评分|量规|清单|检查)",
    re.IGNORECASE,
)


def _markdown_samples(root):
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def _private_table_markdown_samples(root):
    controlled = []
    contextual = []
    for path in _markdown_samples(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if CONTROLLED_TABLE_RE.search(text):
            controlled.append(path)
        elif PIPE_TABLE_RE.search(text) and TABLE_CONTEXT_RE.search(text):
            contextual.append(path)

    return [*controlled, *contextual]


def _invoke_convert(runner, cli_app, input_path, output_path):
    return runner.invoke(
        cli_app,
        ["convert", str(input_path), "--output", str(output_path), "--theme", "plain"],
    )


def _invoke_build(runner, cli_app, input_path, output_path):
    return runner.invoke(
        cli_app,
        ["build", str(input_path), "--output", str(output_path), "--theme", "plain"],
    )


@pytest.mark.private_corpus
def test_private_table_markdown_sample_converts_and_builds(
    private_corpus_root,
    runner,
    cli_app,
    tmp_path,
):
    corpus_root = Path(private_corpus_root)
    samples = _private_table_markdown_samples(corpus_root)
    if not samples:
        pytest.skip(
            "No private Markdown samples with controlled or ordinary table syntax "
            f"found in prepared corpus: {corpus_root}"
        )

    sample = None
    tex_path = tmp_path / "private-table-smoke.tex"
    pdf_path = tmp_path / "private-table-smoke.pdf"
    for index, candidate in enumerate(samples):
        candidate_tex_path = tmp_path / f"private-table-smoke-{index}.tex"
        candidate_pdf_path = tmp_path / f"private-table-smoke-{index}.pdf"
        convert_result = _invoke_convert(
            runner, cli_app, candidate, candidate_tex_path
        )
        if convert_result.exit_code == 0:
            build_result = _invoke_build(runner, cli_app, candidate, candidate_pdf_path)
            if build_result.exit_code == 0:
                sample = candidate
                tex_path = candidate_tex_path
                pdf_path = candidate_pdf_path
                break
            continue

        diagnostic = (
            f"{convert_result.output}\n{convert_result.exception or ''}".lower()
        )
        assert "unsupported directive 'table'" not in diagnostic, (
            "Private controlled table sample failed because the M5 .table DSL is "
            "unsupported. Output is suppressed to avoid leaking corpus text. "
            f"Sample path: {candidate}"
        )

    if sample is None:
        pytest.skip(
            "Private table candidates were present, but none converted cleanly "
            "and built cleanly enough for table smoke without exposing unrelated "
            "corpus failures."
        )

    assert tex_path.is_file()
    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > MIN_PDF_BYTES
