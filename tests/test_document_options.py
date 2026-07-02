from __future__ import annotations

import importlib
from collections.abc import Mapping
from pathlib import Path

import pytest


def _document_options_module():
    try:
        return importlib.import_module("hypolatex.document_options")
    except ModuleNotFoundError as exc:
        if exc.name != "hypolatex.document_options":
            raise
        pytest.fail(
            "Expected src/hypolatex/document_options.py with "
            "resolve_document_options() for M2 document option handling.",
            pytrace=False,
        )


def _write_markdown(path: Path, frontmatter: str = "") -> Path:
    if frontmatter:
        path.write_text(f"---\n{frontmatter.strip()}\n---\n\n# Title\n", encoding="utf-8")
    else:
        path.write_text("# Title\n\nPlain body.\n", encoding="utf-8")
    return path


def _resolve(module, input_path: Path, answer_mode: str | None = None):
    resolver = getattr(module, "resolve_document_options", None)
    assert resolver is not None, (
        "document_options must expose resolve_document_options(input_path, "
        "answer_mode=None)."
    )
    if answer_mode is None:
        return resolver(input_path)
    return resolver(input_path, answer_mode=answer_mode)


def _option_value(options, name: str):
    if isinstance(options, Mapping):
        return options[name]
    return getattr(options, name)


def test_document_options_defaults_answer_mode_to_student(tmp_path):
    module = _document_options_module()
    input_path = _write_markdown(tmp_path / "default.md")

    options = _resolve(module, input_path)

    assert _option_value(options, "answer_mode") == "student"
    assert _option_value(options, "document_type") == "book"
    assert _option_value(options, "layout") == "standard"
    if isinstance(options, Mapping):
        assert dict(options)["layout"] == "standard"


def test_document_options_reads_frontmatter_answer_mode(tmp_path):
    module = _document_options_module()
    input_path = _write_markdown(
        tmp_path / "frontmatter.md",
        """
        answer_mode: review
        """,
    )

    options = _resolve(module, input_path)

    assert _option_value(options, "answer_mode") == "review"


def test_document_options_reads_frontmatter_document_type(tmp_path):
    module = _document_options_module()
    input_path = _write_markdown(
        tmp_path / "article.md",
        """
        document_type: article
        """,
    )

    options = _resolve(module, input_path)

    assert _option_value(options, "document_type") == "article"


def test_document_options_reads_frontmatter_layout_without_changing_document_type(
    tmp_path,
):
    module = _document_options_module()
    input_path = _write_markdown(
        tmp_path / "cheatsheet-article.md",
        """
        document_type: article
        layout: cheatsheet
        """,
    )

    options = _resolve(module, input_path)

    assert _option_value(options, "document_type") == "article"
    assert _option_value(options, "layout") == "cheatsheet"
    if isinstance(options, Mapping):
        assert dict(options) == {
            "answer_mode": "student",
            "document_type": "article",
            "layout": "cheatsheet",
        }


def test_document_options_accepts_documentclass_alias(tmp_path):
    module = _document_options_module()
    input_path = _write_markdown(
        tmp_path / "manual.md",
        """
        documentclass: handbook
        """,
    )

    options = _resolve(module, input_path)

    assert _option_value(options, "document_type") == "article"


def test_document_options_cli_answer_mode_override_wins(tmp_path):
    module = _document_options_module()
    input_path = _write_markdown(
        tmp_path / "override.md",
        """
        answer_mode: teacher
        """,
    )

    options = _resolve(module, input_path, answer_mode="student")

    assert _option_value(options, "answer_mode") == "student"
    assert _option_value(options, "document_type") == "book"


def test_document_options_rejects_invalid_answer_mode_with_supported_values(tmp_path):
    module = _document_options_module()
    error_type = getattr(module, "DocumentOptionsError", ValueError)
    input_path = _write_markdown(
        tmp_path / "invalid.md",
        """
        answer_mode: secret
        """,
    )

    with pytest.raises(error_type) as excinfo:
        _resolve(module, input_path)

    diagnostic = str(excinfo.value).lower()
    assert "answer" in diagnostic
    assert "secret" in diagnostic
    for supported_mode in ("student", "review", "teacher"):
        assert supported_mode in diagnostic


def test_document_options_rejects_invalid_document_type_with_supported_values(tmp_path):
    module = _document_options_module()
    error_type = getattr(module, "DocumentOptionsError", ValueError)
    input_path = _write_markdown(
        tmp_path / "invalid-document-type.md",
        """
        document_type: poster
        """,
    )

    with pytest.raises(error_type) as excinfo:
        _resolve(module, input_path)

    diagnostic = str(excinfo.value).lower()
    assert "document_type" in diagnostic
    assert "poster" in diagnostic
    for supported_type in ("book", "article"):
        assert supported_type in diagnostic


def test_document_options_rejects_invalid_layout_with_supported_values(tmp_path):
    module = _document_options_module()
    error_type = getattr(module, "DocumentOptionsError", ValueError)
    input_path = _write_markdown(
        tmp_path / "invalid-layout.md",
        """
        layout: slide-deck
        """,
    )

    with pytest.raises(error_type) as excinfo:
        _resolve(module, input_path)

    diagnostic = str(excinfo.value).lower()
    assert "layout" in diagnostic
    assert "slide-deck" in diagnostic
    for supported_layout in ("standard", "cheatsheet"):
        assert supported_layout in diagnostic
