"""PDF build orchestration for Hypo-LaTeX."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from hypolatex import convert as convert_module
from hypolatex import document_options
from hypolatex import resource_files
from hypolatex import themes as themes_module


class BuildError(RuntimeError):
    """Raised when a converted LaTeX document cannot be built into a PDF."""


DEFAULT_PAPER = "a4paper"
SUPPORTED_PAPERS = frozenset({"a4paper", "letterpaper"})


@dataclass(frozen=True)
class BuildResult:
    """Result of a completed PDF build."""

    input_path: Path
    output_path: Path


def build_pdf(
    input_path: Path | str,
    output_path: Path | str,
    paper: str = DEFAULT_PAPER,
    theme: str | None = None,
    answer_mode: str | None = None,
) -> BuildResult:
    """Convert a HypoDoc Markdown file and compile it with latexmk/XeLaTeX."""

    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    paper = _normalize_paper(paper)

    if not source.is_file():
        raise BuildError(f"Input Markdown file does not exist: {source}")
    if target.exists() and target.is_dir():
        raise BuildError(f"Output path is a directory: {target}")

    try:
        themes_module.resolve_theme(source, override=theme)
    except themes_module.ThemeError as exc:
        raise BuildError(str(exc)) from exc

    try:
        options = document_options.resolve_document_options(
            source, answer_mode=answer_mode
        )
    except document_options.DocumentOptionsError as exc:
        raise BuildError(str(exc)) from exc

    latexmk = shutil.which("latexmk")
    if latexmk is None:
        raise BuildError(
            "latexmk executable was not found on PATH. Install latexmk and retry "
            "`hypolatex build`."
        )

    xelatex = shutil.which("xelatex")
    if xelatex is None:
        raise BuildError(
            "xelatex executable was not found on PATH. Install XeLaTeX and retry "
            "`hypolatex build`."
        )

    target_parent = target.parent if target.parent != Path("") else Path(".")
    target_parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="hypolatex-build-") as work_name:
        work_dir = Path(work_name)
        tex_path = work_dir / "document.tex"
        pdf_path = work_dir / "document.pdf"

        convert_module.convert_markdown(
            source, tex_path, theme=theme, answer_mode=options.answer_mode
        )
        _apply_paper_override(tex_path, paper)
        try:
            resource_files.prepare_markdown_resources(source, work_dir)
        except resource_files.ResourceError as exc:
            raise BuildError(f"Resource preparation failed.\n{exc}") from exc

        result = subprocess.run(
            [
                latexmk,
                "-xelatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                "-outdir=.",
                tex_path.name,
            ],
            cwd=work_dir,
            env=_latex_environment(),
            capture_output=True,
            check=False,
            text=True,
        )

        if result.returncode != 0:
            raise BuildError(_latexmk_failure_detail(result, work_dir))

        if not pdf_path.is_file():
            raise BuildError(
                "latexmk finished without creating document.pdf. Re-run with the "
                "same input and inspect latexmk output for missing TeX diagnostics."
            )

        _replace_pdf(pdf_path, target)

    return BuildResult(input_path=source, output_path=target)


def _normalize_paper(paper: str) -> str:
    normalized = paper.strip().lower()
    aliases = {
        "a4": "a4paper",
        "letter": "letterpaper",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in SUPPORTED_PAPERS:
        supported = ", ".join(sorted(SUPPORTED_PAPERS))
        raise BuildError(
            f"Unsupported paper size: {paper!r}. Use one of: {supported}."
        )
    return normalized


def _apply_paper_override(tex_path: Path, paper: str) -> None:
    if paper == DEFAULT_PAPER:
        return

    text = tex_path.read_text(encoding="utf-8")
    needle = "\\usepackage{hypolatex}"
    if needle not in text:
        raise BuildError(
            "Generated LaTeX did not load hypolatex, so paper size could not "
            "be applied."
        )

    replacement = f"\\providecommand{{\\HypoPaperSize}}{{{paper}}}\n{needle}"
    tex_path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")


def _replace_pdf(source: Path, target: Path) -> None:
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    os.close(descriptor)
    temp_path = Path(temp_name)
    try:
        shutil.copy2(source, temp_path)
        os.replace(temp_path, target)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _latex_environment() -> dict[str, str]:
    env = os.environ.copy()
    texinputs = [f"{path}//" for path in _texinputs_paths()]
    existing_texinputs = env.get("TEXINPUTS")
    texinputs.append(existing_texinputs if existing_texinputs is not None else "")
    env["TEXINPUTS"] = os.pathsep.join(texinputs)
    return env


def _texinputs_paths() -> tuple[Path, ...]:
    package_root = Path(__file__).resolve().parent
    project_root = package_root.parents[1]

    candidates = (
        project_root / "tex" / "latex" / "hypolatex",
        package_root / "tex" / "latex" / "hypolatex",
    )
    return tuple(path for path in candidates if path.is_dir())


def _latexmk_failure_detail(
    result: subprocess.CompletedProcess[str], work_dir: Path
) -> str:
    parts = [
        "LaTeX build failed while running `latexmk -xelatex`.",
        "Action: inspect the diagnostics below, fix the generated LaTeX or "
        "install the missing TeX package, then retry `hypolatex build`.",
    ]

    log_summary = _log_summary(work_dir / "document.log")
    if log_summary:
        parts.extend(("", "document.log summary:", log_summary))

    stdout = _tail_text(result.stdout)
    if stdout:
        parts.extend(("", "latexmk stdout:", stdout))

    stderr = _tail_text(result.stderr)
    if stderr:
        parts.extend(("", "latexmk stderr:", stderr))

    if not stdout and not stderr and not log_summary:
        parts.append(f"latexmk exited with code {result.returncode}.")

    return "\n".join(parts)


def _log_summary(log_path: Path) -> str:
    if not log_path.is_file():
        return ""

    lines = log_path.read_text(errors="replace").splitlines()
    interesting: list[str] = []
    for index, line in enumerate(lines):
        normalized = line.lower()
        is_error = (
            line.startswith("!")
            or "latex error" in normalized
            or "package " in normalized
            and " error" in normalized
            or "fatal error" in normalized
            or "undefined control sequence" in normalized
        )
        if is_error:
            start = max(0, index - 2)
            end = min(len(lines), index + 8)
            interesting.extend(lines[start:end])

    if interesting:
        return _tail_lines(interesting, max_lines=80)

    return _tail_lines(lines, max_lines=60)


def _tail_text(text: str, max_lines: int = 80) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return _tail_lines(lines, max_lines=max_lines)


def _tail_lines(lines: list[str], max_lines: int) -> str:
    if not lines:
        return ""
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(
        [f"... showing last {max_lines} of {len(lines)} lines", *lines[-max_lines:]]
    )
