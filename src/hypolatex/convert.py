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
from hypolatex import slides
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
    normalized_source: Path | None = None
    try:
        pandoc_source = source
        if options.document_type == "beamer":
            try:
                normalized_markdown = slides.normalize_slides_markdown(source)
            except slides.SlidesError as exc:
                raise ConversionError(str(exc)) from exc

            normalized_source = _make_temp_markdown(target_parent, source.name)
            normalized_source.write_text(
                _prepend_frontmatter(source, str(normalized_markdown)),
                encoding="utf-8",
            )
            pandoc_source = normalized_source

        with (
            resources.as_file(
                resources.files("hypolatex").joinpath(
                    "resources", "filters", "hypolatex.lua"
                )
            ) as lua_filter,
            resources.as_file(
                resources.files("hypolatex").joinpath(
                    "resources",
                    "templates",
                    _template_name(options.document_type),
                )
            ) as template,
        ):
            command = [
                pandoc,
                str(pandoc_source),
                "--from=markdown+yaml_metadata_block+fenced_divs+header_attributes",
                f"--to={_pandoc_writer(options.document_type)}",
                "--standalone",
                "--wrap=none",
                "--no-highlight",
                f"--template={template}",
                f"--lua-filter={lua_filter}",
                f"--metadata=documentclass:{options.document_type}",
                f"--metadata=layout:{options.layout}",
                f"--output={temp_path}",
            ]
            if options.document_type == "beamer":
                command.extend(
                    [
                        "--slide-level=3",
                        f"--metadata=palette:{options.palette}",
                        f"--metadata=aspectratio:{options.aspectratio}",
                        f"--metadata=footline:{options.footline}",
                    ]
                )
                if options.logo is not None:
                    command.append(f"--metadata=logo:{options.logo}")
            else:
                command.append(
                    f"--top-level-division={_top_level_division(options.document_type)}"
                )

            result = subprocess.run(
                command,
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
        _insert_preamble_commands(
            temp_path,
            preamble_commands,
            package_name=_package_name(options.document_type),
        )

        os.replace(temp_path, target)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        if normalized_source is not None:
            normalized_source.unlink(missing_ok=True)

    return ConversionResult(input_path=source, output_path=target)


def _make_temp_output(parent: Path, output_name: str) -> Path:
    suffix = ".tmp.tex"
    prefix = f".{output_name}."
    descriptor, name = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=parent)
    os.close(descriptor)
    return Path(name)


def _make_temp_markdown(parent: Path, input_name: str) -> Path:
    prefix = f".{input_name}."
    descriptor, name = tempfile.mkstemp(prefix=prefix, suffix=".tmp.md", dir=parent)
    os.close(descriptor)
    return Path(name)


def _should_emit_theme_selection(effective_theme: str, override: str | None) -> bool:
    return override is not None or effective_theme != themes_module.DEFAULT_THEME


def _template_name(document_type: str) -> str:
    if document_type == "beamer":
        return "hypolatex-beamer.tex"
    return "hypolatex.tex"


def _pandoc_writer(document_type: str) -> str:
    if document_type == "beamer":
        return "beamer"
    return "latex"


def _package_name(document_type: str) -> str:
    if document_type == "beamer":
        return "hypolatex-beamer"
    return "hypolatex"


def _top_level_division(document_type: str) -> str:
    if document_type == "article":
        return "section"
    return "chapter"


def _insert_preamble_commands(
    tex_path: Path, commands: list[str], package_name: str
) -> None:
    text = tex_path.read_text(encoding="utf-8")
    needle = f"\\usepackage{{{package_name}}}"
    if needle not in text:
        raise ConversionError(
            f"Generated LaTeX did not load {package_name}, so document options "
            "could not be applied."
        )

    replacement = "\n".join([needle, *commands])
    tex_path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")


def _prepend_frontmatter(source: Path, body: str) -> str:
    frontmatter = _frontmatter_block(source.read_text(encoding="utf-8"))
    if not frontmatter:
        return body
    return f"{frontmatter.rstrip()}\n\n{body.lstrip()}"


def _frontmatter_block(text: str) -> str:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return ""

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() in {"---", "..."}:
            return "".join(lines[: index + 1])
    return ""


def _pandoc_error_detail(result: subprocess.CompletedProcess[str]) -> str:
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    if stderr and stdout:
        return f"{stderr}\n{stdout}"
    return stderr or stdout or f"pandoc exited with code {result.returncode}"
