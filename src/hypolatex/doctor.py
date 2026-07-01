"""Implementation for the `hypolatex doctor` command."""

from __future__ import annotations

import typer

from hypolatex.diagnostics import CheckResult, collect_doctor_report


def run() -> None:
    """Run local toolchain checks and exit non-zero on missing requirements."""

    report = collect_doctor_report()

    typer.echo("Hypo-LaTeX doctor")
    typer.echo("")
    _print_section("Executables", report.executables)
    typer.echo("")
    _print_section("TeX packages", report.tex_packages)
    typer.echo("")
    _print_section("Noto CJK fonts", report.noto_cjk_fonts)
    typer.echo("")
    _print_section("Recommended Chinese fonts", report.recommended_chinese_fonts)
    typer.echo("")
    _print_section("Poppler PDF evidence tools", report.pdf_evidence_tools)

    if report.ok:
        typer.echo("")
        typer.echo("All required Hypo-LaTeX checks passed.")
        return

    typer.echo("")
    typer.echo("Missing requirements detected. Install the items above and retry.")
    raise typer.Exit(code=1)


def _print_section(title: str, results: tuple[CheckResult, ...]) -> None:
    typer.echo(f"{title}:")
    for result in results:
        status = "OK" if result.ok else "MISSING"
        typer.echo(f"  [{status}] {result.name}: {result.detail}")
        if result.remediation:
            typer.echo(f"        Action: {result.remediation}")
