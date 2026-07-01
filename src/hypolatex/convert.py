"""Markdown-to-LaTeX conversion pipeline for Hypo-LaTeX."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from hypolatex import document_options
from hypolatex import themes as themes_module


class ConversionError(RuntimeError):
    """Raised when HypoDoc Markdown cannot be converted to LaTeX."""


@dataclass(frozen=True)
class ConversionResult:
    """Result of a completed conversion."""

    input_path: Path
    output_path: Path


def convert_markdown(
    input_path: Path | str,
    output_path: Path | str,
    theme: str | None = None,
    answer_mode: str | None = None,
) -> ConversionResult:
    """Convert a HypoDoc Markdown document to LaTeX using Pandoc."""

    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()

    if not source.is_file():
        raise ConversionError(f"Input Markdown file does not exist: {source}")
    if target.exists() and target.is_dir():
        raise ConversionError(f"Output path is a directory: {target}")

    try:
        effective_theme = themes_module.resolve_theme(source, override=theme)
    except themes_module.ThemeError as exc:
        raise ConversionError(str(exc)) from exc

    try:
        options = document_options.resolve_document_options(
            source, answer_mode=answer_mode
        )
    except document_options.DocumentOptionsError as exc:
        raise ConversionError(str(exc)) from exc

    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise ConversionError(
            "Pandoc executable was not found on PATH. Install Pandoc and retry "
            "`hypolatex convert`."
        )

    target_parent = target.parent if target.parent != Path("") else Path(".")
    target_parent.mkdir(parents=True, exist_ok=True)

    temp_path = _make_temp_output(target_parent, target.name)
    try:
        with (
            resources.as_file(
                resources.files("hypolatex").joinpath(
                    "resources", "filters", "hypolatex.lua"
                )
            ) as lua_filter,
            resources.as_file(
                resources.files("hypolatex").joinpath(
                    "resources", "templates", "hypolatex.tex"
                )
            ) as template,
        ):
            result = subprocess.run(
                [
                    pandoc,
                    str(source),
                    "--from=markdown+yaml_metadata_block+fenced_divs+header_attributes",
                    "--to=latex",
                    "--standalone",
                    "--wrap=none",
                    "--no-highlight",
                    f"--template={template}",
                    f"--lua-filter={lua_filter}",
                    f"--top-level-division={_top_level_division(options.document_type)}",
                    f"--metadata=documentclass:{options.document_type}",
                    f"--output={temp_path}",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

        if result.returncode != 0:
            detail = _pandoc_error_detail(result)
            raise ConversionError(f"HypoDoc Markdown conversion failed.\n{detail}")

        preamble_commands = [f"\\HypoSetAnswerMode{{{options.answer_mode}}}"]
        if _should_emit_theme_selection(effective_theme, theme):
            preamble_commands.append(f"\\HypoUseTheme{{{effective_theme}}}")
        _insert_preamble_commands(temp_path, preamble_commands)

        os.replace(temp_path, target)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return ConversionResult(input_path=source, output_path=target)


def _make_temp_output(parent: Path, output_name: str) -> Path:
    suffix = ".tmp.tex"
    prefix = f".{output_name}."
    descriptor, name = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=parent)
    os.close(descriptor)
    return Path(name)


def _should_emit_theme_selection(effective_theme: str, override: str | None) -> bool:
    return override is not None or effective_theme != themes_module.DEFAULT_THEME


def _top_level_division(document_type: str) -> str:
    if document_type == "article":
        return "section"
    return "chapter"


def _insert_preamble_commands(tex_path: Path, commands: list[str]) -> None:
    text = tex_path.read_text(encoding="utf-8")
    needle = "\\usepackage{hypolatex}"
    if needle not in text:
        raise ConversionError(
            "Generated LaTeX did not load hypolatex, so document options could "
            "not be applied."
        )

    replacement = "\n".join([needle, *commands])
    tex_path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")


def _pandoc_error_detail(result: subprocess.CompletedProcess[str]) -> str:
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    if stderr and stdout:
        return f"{stderr}\n{stdout}"
    return stderr or stdout or f"pandoc exited with code {result.returncode}"
