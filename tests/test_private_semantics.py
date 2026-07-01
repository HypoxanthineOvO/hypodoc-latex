import re
from pathlib import Path

import pytest


MIN_PDF_BYTES = 1024
SEMANTIC_DIRECTIVE_RE = re.compile(
    r":::\s*(?:\{[^}]*\.)?"
    r"(?:objective|info|task|requirement|deliverable|checklist|rubric)\b"
)


def _markdown_samples(root):
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def _semantic_markdown_samples(root):
    samples = []
    for path in _markdown_samples(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if SEMANTIC_DIRECTIVE_RE.search(text):
            samples.append(path)
    return samples


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
def test_private_semantic_markdown_sample_converts_and_builds(
    private_corpus_root,
    runner,
    cli_app,
    tmp_path,
):
    corpus_root = Path(private_corpus_root)
    samples = _semantic_markdown_samples(corpus_root)
    if not samples:
        pytest.skip(
            "No Markdown samples with M3 semantic fenced directives found in "
            f"prepared corpus: {corpus_root}"
        )

    sample = samples[0]
    tex_path = tmp_path / "private-semantic-smoke.tex"
    pdf_path = tmp_path / "private-semantic-smoke.pdf"

    convert_result = _invoke_convert(runner, cli_app, sample, tex_path)
    assert convert_result.exit_code == 0, convert_result.output
    assert tex_path.is_file()

    build_result = _invoke_build(runner, cli_app, sample, pdf_path)
    assert build_result.exit_code == 0, build_result.output
    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > MIN_PDF_BYTES
