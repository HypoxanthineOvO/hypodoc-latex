"""Typer command line interface for Hypo-LaTeX."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from hypolatex import build as build_module
from hypolatex import convert as convert_module
from hypolatex import doctor as doctor_module


app = typer.Typer(
    help="Hypo-LaTeX command line tools for conversion, builds, and diagnostics.",
    no_args_is_help=True,
)


@app.command("doctor")
def doctor() -> None:
    """Check required local executables and TeX packages."""

    doctor_module.run()


@app.command("convert")
def convert(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="HypoDoc Markdown input file.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="LaTeX output file.",
        ),
    ],
    theme: Annotated[
        str | None,
        typer.Option(
            "--theme",
            help="Theme preset ID. Overrides the Markdown frontmatter theme.",
        ),
    ] = None,
    answer_mode: Annotated[
        str | None,
        typer.Option(
            "--answer-mode",
            help=(
                "Answer visibility mode: student, review, or teacher. "
                "Overrides the Markdown frontmatter answer_mode."
            ),
        ),
    ] = None,
) -> None:
    """Convert HypoDoc Markdown to a standalone LaTeX document."""

    try:
        convert_module.convert_markdown(
            input_path, output, theme=theme, answer_mode=answer_mode
        )
    except convert_module.ConversionError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@app.command("build")
def build(
    input_path: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="HypoDoc Markdown input file.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=True,
            dir_okay=False,
            writable=True,
            help="PDF output file.",
        ),
    ],
    paper: Annotated[
        str,
        typer.Option(
            "--paper",
            help="Paper size for the generated PDF: a4paper or letterpaper.",
        ),
    ] = build_module.DEFAULT_PAPER,
    theme: Annotated[
        str | None,
        typer.Option(
            "--theme",
            help="Theme preset ID. Overrides the Markdown frontmatter theme.",
        ),
    ] = None,
    answer_mode: Annotated[
        str | None,
        typer.Option(
            "--answer-mode",
            help=(
                "Answer visibility mode: student, review, or teacher. "
                "Overrides the Markdown frontmatter answer_mode."
            ),
        ),
    ] = None,
) -> None:
    """Convert HypoDoc Markdown and compile a PDF with XeLaTeX."""

    try:
        build_module.build_pdf(
            input_path,
            output,
            paper=paper,
            theme=theme,
            answer_mode=answer_mode,
        )
    except (build_module.BuildError, convert_module.ConversionError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
