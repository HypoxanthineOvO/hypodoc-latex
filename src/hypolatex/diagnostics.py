"""Reusable local environment diagnostics for Hypo-LaTeX."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys


REQUIRED_EXECUTABLES = (
    "pandoc",
    "python3",
    "uv",
    "xelatex",
    "latexmk",
    "kpsewhich",
    "fc-match",
)

PDF_EVIDENCE_TOOLS = (
    "pdfinfo",
    "pdftotext",
    "pdftoppm",
)

REQUIRED_TEX_PACKAGES = (
    "ctex",
    "fontspec",
    "fontawesome5",
    "tcolorbox",
    "fancyhdr",
    "geometry",
    "titlesec",
    "eso-pic",
)

REQUIRED_NOTO_CJK_FONTS = (
    "Noto Serif CJK SC",
    "Noto Sans CJK SC",
    "Noto Sans Mono CJK SC",
)

RECOMMENDED_CHINESE_FONTS = (
    "MiSans",
    "Sarasa Gothic SC",
    "LXGW WenKai",
    "LXGW WenKai Mono",
    "Smiley Sans",
    "Alibaba PuHuiTi 3.0",
    "DingTalk JinBuTi",
)


@dataclass(frozen=True)
class CheckResult:
    """Result for one required executable or TeX package."""

    name: str
    ok: bool
    detail: str
    remediation: str = ""


@dataclass(frozen=True)
class DoctorReport:
    """Collected doctor results."""

    executables: tuple[CheckResult, ...]
    tex_packages: tuple[CheckResult, ...]
    noto_cjk_fonts: tuple[CheckResult, ...]
    recommended_chinese_fonts: tuple[CheckResult, ...]
    pdf_evidence_tools: tuple[CheckResult, ...]

    @property
    def ok(self) -> bool:
        return all(
            result.ok
            for result in (
                *self.executables,
                *self.tex_packages,
                *self.noto_cjk_fonts,
                *self.pdf_evidence_tools,
            )
        )


def collect_doctor_report() -> DoctorReport:
    """Check every dependency needed by the Hypo-LaTeX toolchain."""

    return DoctorReport(
        executables=tuple(check_executable(name) for name in REQUIRED_EXECUTABLES),
        tex_packages=tuple(check_tex_package(name) for name in REQUIRED_TEX_PACKAGES),
        noto_cjk_fonts=tuple(
            check_font_family(name) for name in REQUIRED_NOTO_CJK_FONTS
        ),
        recommended_chinese_fonts=tuple(
            check_font_family(name) for name in RECOMMENDED_CHINESE_FONTS
        ),
        pdf_evidence_tools=tuple(
            check_pdf_evidence_tool(name) for name in PDF_EVIDENCE_TOOLS
        ),
    )


def check_executable(name: str) -> CheckResult:
    """Return whether an executable can be found on PATH.

    The Python runtime may satisfy the python3 requirement even when the exact
    command is not available, which keeps embedded or virtualenv executions
    truthful.
    """

    found = shutil.which(name)
    if found:
        return CheckResult(name=name, ok=True, detail=found)

    if name == "python3":
        current_python = Path(sys.executable)
        if current_python.is_file():
            return CheckResult(
                name=name,
                ok=True,
                detail=f"current Python runtime: {current_python}",
            )

    return CheckResult(
        name=name,
        ok=False,
        detail=f"{name} was not found on PATH.",
        remediation=f"Install {name} and ensure it is available on PATH.",
    )


def check_pdf_evidence_tool(name: str) -> CheckResult:
    """Return whether a required Poppler evidence executable is available."""

    found = shutil.which(name)
    if found:
        return CheckResult(name=name, ok=True, detail=found)

    return CheckResult(
        name=name,
        ok=False,
        detail=f"{name} was not found on PATH.",
        remediation=(
            "Install Poppler PDF tools and ensure "
            f"`{name}` is available on PATH."
        ),
    )


def check_tex_package(name: str) -> CheckResult:
    """Return whether kpsewhich can resolve a required LaTeX package."""

    kpsewhich = shutil.which("kpsewhich")
    if not kpsewhich:
        return CheckResult(
            name=name,
            ok=False,
            detail="kpsewhich was not found, so TeX packages cannot be checked.",
            remediation=(
                "Install a TeX distribution with kpsewhich, then install "
                f"the {name} package."
            ),
        )

    target = f"{name}.sty"
    result = subprocess.run(
        [kpsewhich, target],
        capture_output=True,
        check=False,
        text=True,
    )
    output = (result.stdout or result.stderr).strip()
    if result.returncode == 0 and result.stdout.strip():
        return CheckResult(name=name, ok=True, detail=result.stdout.strip())

    detail = output or f"kpsewhich could not locate {target}."
    return CheckResult(
        name=name,
        ok=False,
        detail=detail,
        remediation=(
            f"Install the TeX package {name} in your TeX distribution; "
            f"`kpsewhich {target}` must return a .sty path."
        ),
    )


def check_font_family(family: str) -> CheckResult:
    """Return whether fontconfig resolves a requested font family exactly."""

    fc_match = shutil.which("fc-match")
    if not fc_match:
        return CheckResult(
            name=family,
            ok=False,
            detail="fc-match was not found, so font families cannot be checked.",
            remediation=(
                "Install fontconfig and the required Chinese fonts, then "
                "ensure `fc-match` is available on PATH."
            ),
        )

    result = subprocess.run(
        [fc_match, "--format=%{family}\n", family],
        capture_output=True,
        check=False,
        text=True,
    )
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        detail = output or f"fc-match exited with code {result.returncode}."
        return CheckResult(
            name=family,
            ok=False,
            detail=detail,
            remediation=(
                f"Install the `{family}` font family and verify it with "
                f"`fc-match \"{family}\"`."
            ),
        )

    if _font_match_contains_family(output, family):
        return CheckResult(name=family, ok=True, detail=output or family)

    resolved = output or "<no font family returned>"
    return CheckResult(
        name=family,
        ok=False,
        detail=f"fc-match resolved to {resolved!r}, not {family!r}.",
        remediation=(
            f"Install the `{family}` font family and refresh fontconfig "
            "so `fc-match` resolves to the requested family."
        ),
    )


def _font_match_contains_family(output: str, family: str) -> bool:
    expected = family.casefold()
    candidates: list[str] = []
    for line in output.splitlines():
        candidates.extend(part.strip().casefold() for part in line.split(","))
    return expected in candidates
