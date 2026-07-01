"""Poppler-backed PDF evidence helpers for Hypo-LaTeX."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import re
import shutil
import subprocess


class PdfEvidenceError(RuntimeError):
    """Raised when Poppler cannot inspect or render a PDF."""


def read_pdf_info(pdf_path: Path | str) -> Mapping[str, str]:
    """Return normalized metadata from `pdfinfo` for a PDF."""

    pdf = _require_pdf_path(pdf_path)
    result = _run_poppler_tool("pdfinfo", [str(pdf)])
    info: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized_key = _normalize_pdfinfo_key(key)
        info[normalized_key] = value.strip()
    return info


def extract_text(pdf_path: Path | str) -> str:
    """Extract searchable text from a PDF with `pdftotext`."""

    pdf = _require_pdf_path(pdf_path)
    result = _run_poppler_tool("pdftotext", [str(pdf), "-"])
    return result.stdout


def render_page_png(
    pdf_path: Path | str,
    output_dir: Path | str,
    page: int = 1,
    stem: str | None = None,
) -> Path:
    """Render one PDF page as a PNG using `pdftoppm`."""

    if page < 1:
        raise PdfEvidenceError(f"PDF page numbers start at 1; got {page}.")

    pdf = _require_pdf_path(pdf_path)
    destination = Path(output_dir).expanduser()
    destination.mkdir(parents=True, exist_ok=True)

    output_stem = stem or f"{pdf.stem}-page-{page}"
    output_base = destination / output_stem
    output_png = output_base.with_suffix(".png")
    output_png.unlink(missing_ok=True)

    _run_poppler_tool(
        "pdftoppm",
        [
            "-f",
            str(page),
            "-singlefile",
            "-png",
            str(pdf),
            str(output_base),
        ],
    )

    if not output_png.is_file() or output_png.stat().st_size == 0:
        raise PdfEvidenceError(
            "`pdftoppm` finished without creating a non-empty PNG at "
            f"{output_png}."
        )
    return output_png


def _require_pdf_path(pdf_path: Path | str) -> Path:
    pdf = Path(pdf_path).expanduser()
    if not pdf.is_file():
        raise PdfEvidenceError(f"PDF file does not exist: {pdf}")
    return pdf


def _run_poppler_tool(
    tool: str, args: list[str]
) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(tool)
    if executable is None:
        raise PdfEvidenceError(
            f"{tool} executable was not found on PATH. Install Poppler PDF "
            "tools and retry the PDF evidence command."
        )

    result = subprocess.run(
        [executable, *args],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        if not detail:
            detail = f"{tool} exited with code {result.returncode}."
        raise PdfEvidenceError(f"Poppler tool `{tool}` failed.\n{detail}")
    return result


def _normalize_pdfinfo_key(key: str) -> str:
    normalized = key.strip().casefold()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized


__all__ = [
    "PdfEvidenceError",
    "extract_text",
    "read_pdf_info",
    "render_page_png",
]
