"""Theme preset resolution for Hypo-LaTeX documents."""

from __future__ import annotations

from pathlib import Path
import re


class ThemeError(ValueError):
    """Raised when a document or CLI option selects an unsupported theme."""


DEFAULT_THEME = "plain"
THEME_REGISTRY = {
    "plain": {
        "latex_theme": "plain",
    },
    "classic-readable": {
        "latex_theme": "classic-readable",
    },
    "tech-minimal": {
        "latex_theme": "tech-minimal",
    },
    "warm-handbook": {
        "latex_theme": "warm-handbook",
    },
    "academic-clean": {
        "latex_theme": "academic-clean",
    },
}

_THEME_LINE_RE = re.compile(r"^theme\s*:\s*(?P<value>.*?)\s*$")


def valid_theme_ids() -> tuple[str, ...]:
    """Return all supported public theme IDs."""

    return tuple(sorted(THEME_REGISTRY))


def validate_theme_id(theme_id: str) -> str:
    """Normalize and validate a public theme ID."""

    normalized = theme_id.strip()
    if normalized in THEME_REGISTRY:
        return normalized

    supported = ", ".join(valid_theme_ids())
    raise ThemeError(
        f"Unsupported theme: {theme_id!r}. Use one of: {supported}."
    )


def resolve_theme(input_path: Path | str, override: str | None = None) -> str:
    """Resolve the effective theme from CLI override or YAML frontmatter."""

    if override is not None:
        return validate_theme_id(override)

    source = Path(input_path).expanduser().resolve()
    theme_id = _read_frontmatter_theme(source)
    if theme_id is None:
        return DEFAULT_THEME
    return validate_theme_id(theme_id)


def _read_frontmatter_theme(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    frontmatter_lines: list[str] = []
    for line in lines[1:]:
        if line.strip() in {"---", "..."}:
            break
        frontmatter_lines.append(line)
    else:
        return None

    for line in frontmatter_lines:
        match = _THEME_LINE_RE.match(line.strip())
        if match is None:
            continue
        return _clean_scalar(match.group("value"))

    return None


def _clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()

    if "#" in value:
        value = value.split("#", 1)[0].strip()
    return value
