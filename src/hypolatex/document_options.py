"""Document option resolution for Hypo-LaTeX documents."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
import re


class DocumentOptionsError(ValueError):
    """Raised when a document option is unsupported or malformed."""


DEFAULT_ANSWER_MODE = "student"
SUPPORTED_ANSWER_MODES = ("student", "review", "teacher")
DEFAULT_DOCUMENT_TYPE = "book"
SUPPORTED_DOCUMENT_TYPES = ("book", "article", "beamer")
DEFAULT_LAYOUT = "standard"
SUPPORTED_LAYOUTS = ("standard", "cheatsheet")
DEFAULT_BEAMER_PALETTE = "red"
SUPPORTED_BEAMER_PALETTES = ("red", "blue", "yellow", "gray", "mono")
DEFAULT_BEAMER_ASPECTRATIO = "169"
SUPPORTED_BEAMER_ASPECTRATIOS = ("43", "54", "149", "1610", "169", "32")
DEFAULT_BEAMER_FOOTLINE = "full"
SUPPORTED_BEAMER_FOOTLINES = ("full", "page", "none")

_ANSWER_MODE_LINE_RE = re.compile(r"^answer_mode\s*:\s*(?P<value>.*?)\s*$")
_DOCUMENT_TYPE_LINE_RE = re.compile(
    r"^(?:document_type|documentclass)\s*:\s*(?P<value>.*?)\s*$"
)
_LAYOUT_LINE_RE = re.compile(r"^layout\s*:\s*(?P<value>.*?)\s*$")
_BEAMER_PALETTE_LINE_RE = re.compile(r"^palette\s*:\s*(?P<value>.*?)\s*$")
_BEAMER_ASPECTRATIO_LINE_RE = re.compile(r"^aspectratio\s*:\s*(?P<value>.*?)\s*$")
_BEAMER_FOOTLINE_LINE_RE = re.compile(r"^footline\s*:\s*(?P<value>.*?)\s*$")
_BEAMER_LOGO_LINE_RE = re.compile(r"^logo\s*:\s*(?P<value>.*?)\s*$")


@dataclass(frozen=True)
class DocumentOptions(Mapping[str, str]):
    """Resolved document options.

    The mapping interface keeps this object convenient for tests and callers
    that prefer dictionary-like access while preserving named attributes for
    the public options. Beamer-only options are present in the mapping only
    when ``document_type`` resolves to ``beamer``.
    """

    answer_mode: str = DEFAULT_ANSWER_MODE
    document_type: str = DEFAULT_DOCUMENT_TYPE
    layout: str = DEFAULT_LAYOUT
    palette: str | None = None
    aspectratio: str | None = None
    footline: str | None = None
    logo: str | None = None

    def __getitem__(self, key: str) -> str | None:
        if key == "answer_mode":
            return self.answer_mode
        if key == "document_type":
            return self.document_type
        if key == "layout":
            return self.layout
        if self.document_type == "beamer":
            if key == "palette":
                return self.palette
            if key == "aspectratio":
                return self.aspectratio
            if key == "footline":
                return self.footline
            if key == "logo":
                return self.logo
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        yield "answer_mode"
        yield "document_type"
        yield "layout"
        if self.document_type == "beamer":
            yield "palette"
            yield "aspectratio"
            yield "footline"
            yield "logo"

    def __len__(self) -> int:
        if self.document_type == "beamer":
            return 7
        return 3


def valid_answer_modes() -> tuple[str, ...]:
    """Return all supported answer visibility modes."""

    return SUPPORTED_ANSWER_MODES


def valid_document_types() -> tuple[str, ...]:
    """Return supported document shape presets."""

    return SUPPORTED_DOCUMENT_TYPES


def valid_layouts() -> tuple[str, ...]:
    """Return supported document startup layouts."""

    return SUPPORTED_LAYOUTS


def valid_beamer_palettes() -> tuple[str, ...]:
    """Return supported Beamer palette presets."""

    return SUPPORTED_BEAMER_PALETTES


def valid_beamer_aspectratios() -> tuple[str, ...]:
    """Return supported Beamer aspect ratios."""

    return SUPPORTED_BEAMER_ASPECTRATIOS


def valid_beamer_footlines() -> tuple[str, ...]:
    """Return supported Beamer footline presets."""

    return SUPPORTED_BEAMER_FOOTLINES


def validate_answer_mode(answer_mode: str) -> str:
    """Normalize and validate an answer visibility mode."""

    normalized = answer_mode.strip()
    if normalized in SUPPORTED_ANSWER_MODES:
        return normalized

    supported = ", ".join(SUPPORTED_ANSWER_MODES)
    raise DocumentOptionsError(
        f"Unsupported answer_mode: {answer_mode!r}. Use one of: {supported}."
    )


def validate_document_type(document_type: str) -> str:
    """Normalize and validate the document shape preset."""

    normalized = document_type.strip().lower()
    aliases = {
        "longform": "book",
        "tutorial": "book",
        "manual": "article",
        "handbook": "article",
        "handout": "article",
        "short": "article",
        "presentation": "beamer",
        "slides": "beamer",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized in SUPPORTED_DOCUMENT_TYPES:
        return normalized

    supported = ", ".join(SUPPORTED_DOCUMENT_TYPES)
    raise DocumentOptionsError(
        f"Unsupported document_type: {document_type!r}. Use one of: {supported}."
    )


def validate_layout(layout: str) -> str:
    """Normalize and validate the document startup layout."""

    normalized = layout.strip().lower()
    if normalized in SUPPORTED_LAYOUTS:
        return normalized

    supported = ", ".join(SUPPORTED_LAYOUTS)
    raise DocumentOptionsError(
        f"Unsupported layout: {layout!r}. Use one of: {supported}."
    )


def validate_beamer_palette(palette: str) -> str:
    """Normalize and validate a Beamer palette preset."""

    normalized = palette.strip().lower()
    if normalized in SUPPORTED_BEAMER_PALETTES:
        return normalized

    supported = ", ".join(SUPPORTED_BEAMER_PALETTES)
    raise DocumentOptionsError(
        f"Unsupported palette: {palette!r}. Use one of: {supported}."
    )


def validate_beamer_aspectratio(aspectratio: str) -> str:
    """Normalize and validate a Beamer aspect ratio option."""

    normalized = aspectratio.strip()
    if normalized in SUPPORTED_BEAMER_ASPECTRATIOS:
        return normalized

    supported = ", ".join(SUPPORTED_BEAMER_ASPECTRATIOS)
    raise DocumentOptionsError(
        f"Unsupported aspectratio: {aspectratio!r}. Use one of: {supported}."
    )


def validate_beamer_footline(footline: str) -> str:
    """Normalize and validate a Beamer footline preset."""

    normalized = footline.strip().lower()
    if normalized in SUPPORTED_BEAMER_FOOTLINES:
        return normalized

    supported = ", ".join(SUPPORTED_BEAMER_FOOTLINES)
    raise DocumentOptionsError(
        f"Unsupported footline: {footline!r}. Use one of: {supported}."
    )


def resolve_document_options(
    input_path: Path | str,
    answer_mode: str | None = None,
) -> DocumentOptions:
    """Resolve document options from CLI overrides and YAML frontmatter."""

    source = Path(input_path).expanduser().resolve()
    frontmatter_document_type = _read_frontmatter_document_type(source)
    frontmatter_layout = _read_frontmatter_layout(source)
    document_type = (
        DEFAULT_DOCUMENT_TYPE
        if frontmatter_document_type is None
        else validate_document_type(frontmatter_document_type)
    )
    layout = (
        DEFAULT_LAYOUT
        if frontmatter_layout is None
        else validate_layout(frontmatter_layout)
    )

    if answer_mode is not None:
        return DocumentOptions(
            answer_mode=validate_answer_mode(answer_mode),
            document_type=document_type,
            layout=layout,
            **_resolve_beamer_options(source, document_type),
        )

    frontmatter_answer_mode = _read_frontmatter_answer_mode(source)

    return DocumentOptions(
        answer_mode=(
            DEFAULT_ANSWER_MODE
            if frontmatter_answer_mode is None
            else validate_answer_mode(frontmatter_answer_mode)
        ),
        document_type=document_type,
        layout=layout,
        **_resolve_beamer_options(source, document_type),
    )


def _read_frontmatter_answer_mode(path: Path) -> str | None:
    return _read_frontmatter_scalar(path, _ANSWER_MODE_LINE_RE)


def _read_frontmatter_document_type(path: Path) -> str | None:
    return _read_frontmatter_scalar(path, _DOCUMENT_TYPE_LINE_RE)


def _read_frontmatter_layout(path: Path) -> str | None:
    return _read_frontmatter_scalar(path, _LAYOUT_LINE_RE)


def _read_frontmatter_beamer_palette(path: Path) -> str | None:
    return _read_frontmatter_scalar(path, _BEAMER_PALETTE_LINE_RE)


def _read_frontmatter_beamer_aspectratio(path: Path) -> str | None:
    return _read_frontmatter_scalar(path, _BEAMER_ASPECTRATIO_LINE_RE)


def _read_frontmatter_beamer_footline(path: Path) -> str | None:
    return _read_frontmatter_scalar(path, _BEAMER_FOOTLINE_LINE_RE)


def _read_frontmatter_beamer_logo(path: Path) -> str | None:
    return _read_frontmatter_scalar(path, _BEAMER_LOGO_LINE_RE)


def _resolve_beamer_options(
    source: Path, document_type: str
) -> dict[str, str | None]:
    if document_type != "beamer":
        return {}

    frontmatter_palette = _read_frontmatter_beamer_palette(source)
    frontmatter_aspectratio = _read_frontmatter_beamer_aspectratio(source)
    frontmatter_footline = _read_frontmatter_beamer_footline(source)

    return {
        "palette": (
            DEFAULT_BEAMER_PALETTE
            if frontmatter_palette is None
            else validate_beamer_palette(frontmatter_palette)
        ),
        "aspectratio": (
            DEFAULT_BEAMER_ASPECTRATIO
            if frontmatter_aspectratio is None
            else validate_beamer_aspectratio(frontmatter_aspectratio)
        ),
        "footline": (
            DEFAULT_BEAMER_FOOTLINE
            if frontmatter_footline is None
            else validate_beamer_footline(frontmatter_footline)
        ),
        "logo": _read_frontmatter_beamer_logo(source),
    }


def _read_frontmatter_scalar(path: Path, pattern: re.Pattern[str]) -> str | None:
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
        match = pattern.match(line.strip())
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
