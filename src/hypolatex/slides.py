"""Slides DSL option resolution and normalization."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import os
import re
from typing import Any


class SlidesError(ValueError):
    """Raised when slide options or slide structure are invalid."""


_OPTION_NAMES = (
    "section_dividers",
    "subsection_dividers",
    "frame_title_inheritance_limit",
    "continued_title_style",
    "strict_structure",
)
_CONTINUED_TITLE_STYLES = ("subtle", "suffix", "none")
_HEADING_RE = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.*?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
_BULLET_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
_IMAGE_ATTR_LINE_RE = re.compile(
    r"^(?P<indent>\s*)!\[(?P<alt>(?:\\.|[^\]])*)\]"
    r"\((?P<target>[^)]+)\)\{(?P<attrs>[^}]*)\}(?P<trailing>\s*)$"
)
_IMAGE_TOKEN_RE = re.compile(
    r"!\[(?P<alt>(?:\\.|[^\]])*)\]\((?P<target>[^)]+)\)(?:\{(?P<attrs>[^}]*)\})?"
)
_ATTR_RE = re.compile(
    r"""(?P<name>[A-Za-z_:-][\w:-]*)=(?P<quote>["']?)(?P<value>[^\s"']+)(?P=quote)"""
)
_DEFAULT_IMAGE_HEIGHT_CAP = r"0.75\textheight"


@dataclass(frozen=True)
class SlideOptions(Mapping[str, object]):
    """Resolved options for the AI-friendly slides Markdown contract."""

    section_dividers: bool = True
    subsection_dividers: bool = False
    frame_title_inheritance_limit: int = 3
    continued_title_style: str = "subtle"
    strict_structure: bool = True

    def __post_init__(self) -> None:
        if self.frame_title_inheritance_limit < 1:
            raise SlidesError("frame_title_inheritance_limit must be a positive int.")
        if self.continued_title_style not in _CONTINUED_TITLE_STYLES:
            supported = ", ".join(_CONTINUED_TITLE_STYLES)
            raise SlidesError(
                "continued_title_style must be one of: " f"{supported}."
            )

    def __getitem__(self, key: str) -> object:
        if key not in _OPTION_NAMES:
            raise KeyError(key)
        return getattr(self, key)

    def __iter__(self) -> Iterator[str]:
        return iter(_OPTION_NAMES)

    def __len__(self) -> int:
        return len(_OPTION_NAMES)


class NormalizedSlides(str):
    """String result with attribute access for callers that prefer objects."""

    @property
    def markdown(self) -> str:
        return str(self)

    @property
    def normalized_markdown(self) -> str:
        return str(self)


@dataclass
class _Frame:
    title: str
    lines: list[str]


@dataclass(frozen=True)
class _Heading:
    level: int
    title: str


def resolve_slide_options(input_path: Path | str | os.PathLike[str]) -> SlideOptions:
    """Resolve slide options from flat YAML frontmatter scalar values."""

    text = Path(input_path).expanduser().resolve().read_text(encoding="utf-8")
    frontmatter, _ = _split_frontmatter(text)
    return _options_from_mapping(frontmatter)


def normalize_slides_markdown(
    input_path_or_text: Path | str | os.PathLike[str],
    options: SlideOptions | Mapping[str, Any] | None = None,
) -> NormalizedSlides:
    """Normalize slides Markdown and fail fast on unsafe slide structure."""

    text = _read_input_text(input_path_or_text)
    frontmatter, body = _split_frontmatter(text)
    resolved_options = (
        _coerce_options(options) if options is not None else _options_from_mapping(frontmatter)
    )
    events = _parse_body(body, resolved_options)
    normalized = _render_events(events)
    return NormalizedSlides(normalized)


def _read_input_text(input_path_or_text: Path | str | os.PathLike[str]) -> str:
    if isinstance(input_path_or_text, os.PathLike):
        return Path(input_path_or_text).expanduser().resolve().read_text(encoding="utf-8")

    candidate = Path(input_path_or_text).expanduser()
    if "\n" not in input_path_or_text and candidate.exists():
        return candidate.resolve().read_text(encoding="utf-8")

    return input_path_or_text


def _options_from_mapping(values: Mapping[str, str]) -> SlideOptions:
    kwargs: dict[str, object] = {}
    if "section_dividers" in values:
        kwargs["section_dividers"] = _parse_bool(
            "section_dividers", values["section_dividers"]
        )
    if "subsection_dividers" in values:
        kwargs["subsection_dividers"] = _parse_bool(
            "subsection_dividers", values["subsection_dividers"]
        )
    if "frame_title_inheritance_limit" in values:
        kwargs["frame_title_inheritance_limit"] = _parse_positive_int(
            "frame_title_inheritance_limit", values["frame_title_inheritance_limit"]
        )
    if "continued_title_style" in values:
        kwargs["continued_title_style"] = _parse_choice(
            "continued_title_style",
            values["continued_title_style"],
            _CONTINUED_TITLE_STYLES,
        )
    if "strict_structure" in values:
        kwargs["strict_structure"] = _parse_bool(
            "strict_structure", values["strict_structure"]
        )
    return SlideOptions(**kwargs)


def _coerce_options(options: SlideOptions | Mapping[str, Any]) -> SlideOptions:
    if isinstance(options, SlideOptions):
        return options
    return SlideOptions(
        section_dividers=bool(options.get("section_dividers", True)),
        subsection_dividers=bool(options.get("subsection_dividers", False)),
        frame_title_inheritance_limit=int(
            options.get("frame_title_inheritance_limit", 3)
        ),
        continued_title_style=str(options.get("continued_title_style", "subtle")),
        strict_structure=bool(options.get("strict_structure", True)),
    )


def _parse_body(
    body: str, options: SlideOptions
) -> list[_Frame | _Heading]:
    events: list[_Frame | _Heading] = []
    current_frame: _Frame | None = None
    section: str | None = None
    last_title: str | None = None
    title_run_count = 0
    context_changed = False
    pending_new_frame = False
    in_fence = False

    def finish_current_frame() -> None:
        nonlocal current_frame
        if current_frame is None:
            return
        _validate_frame(current_frame)
        events.append(current_frame)
        current_frame = None

    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        fence_match = _FENCE_RE.match(line)
        if fence_match is not None:
            if current_frame is None and line.strip():
                if last_title is None or context_changed:
                    _raise_missing_frame_title(section)
                current_frame = _inherit_frame(
                    last_title, title_run_count, options
                )
                title_run_count += 1
                pending_new_frame = False
            if current_frame is not None:
                current_frame.lines.append(line)
            in_fence = not in_fence
            continue

        if not in_fence:
            heading_match = _HEADING_RE.match(line)
            if heading_match is not None:
                level = len(heading_match.group("level"))
                title = heading_match.group("title").strip()
                if level == 1:
                    finish_current_frame()
                    section = title
                    last_title = None
                    title_run_count = 0
                    context_changed = True
                    pending_new_frame = False
                    if options.section_dividers:
                        events.append(_Heading(level=1, title=title))
                    continue
                if level == 2:
                    if section is None and options.strict_structure:
                        raise SlidesError(
                            f"H2 subsection {title!r} requires a preceding H1 section."
                        )
                    finish_current_frame()
                    last_title = None
                    title_run_count = 0
                    context_changed = True
                    pending_new_frame = False
                    events.append(_Heading(level=2, title=title))
                    continue
                if level == 3:
                    finish_current_frame()
                    current_frame = _Frame(title=title, lines=[])
                    last_title = title
                    title_run_count = 1
                    context_changed = False
                    pending_new_frame = False
                    continue

            if line.strip() == "---":
                if pending_new_frame and current_frame is None:
                    raise SlidesError(
                        f"Empty frame after separator near title {last_title!r}."
                    )
                finish_current_frame()
                pending_new_frame = True
                continue

        if not line.strip() and current_frame is None:
            continue

        if current_frame is None:
            if last_title is None or context_changed:
                _raise_missing_frame_title(section)
            current_frame = _inherit_frame(last_title, title_run_count, options)
            title_run_count += 1
            pending_new_frame = False

        current_frame.lines.append(line if in_fence else _rewrite_image_line(line))

    if pending_new_frame and current_frame is None:
        if last_title is None or context_changed:
            _raise_missing_frame_title(section)
        current_frame = _inherit_frame(last_title, title_run_count, options)

    finish_current_frame()
    return events


def _inherit_frame(
    title: str,
    title_run_count: int,
    options: SlideOptions,
) -> _Frame:
    next_count = title_run_count + 1
    if next_count > options.frame_title_inheritance_limit:
        raise SlidesError(
            f"Cannot inherit frame title {title!r} beyond "
            f"limit {options.frame_title_inheritance_limit}."
        )
    return _Frame(
        title=_continued_title(title, next_count, options),
        lines=[],
    )


def _continued_title(title: str, count: int, options: SlideOptions) -> str:
    if options.continued_title_style == "suffix":
        return f"{title} {count}/{options.frame_title_inheritance_limit}"
    if options.continued_title_style == "none":
        return title
    return f"{title} (continued {count}/{options.frame_title_inheritance_limit})"


def _validate_frame(frame: _Frame) -> None:
    nonblank = [line for line in frame.lines if line.strip()]
    if not nonblank:
        raise SlidesError(f"Empty frame {frame.title!r} is not allowed.")

    bullet_count = sum(1 for line in nonblank if _BULLET_RE.match(line))
    char_count = sum(len(line) for line in nonblank)
    if bullet_count > 60 or len(nonblank) > 180 or char_count > 12000:
        raise SlidesError(f"Overfull frame {frame.title!r} is too large.")


def _rewrite_image_line(line: str) -> str:
    stretch_rewrite = _rewrite_stretch_image_line(line)
    if stretch_rewrite != line:
        if stretch_rewrite == stretch_rewrite.lstrip():
            return f"\\begin{{center}}\n{stretch_rewrite}\n\\end{{center}}"
        return stretch_rewrite
    return _rewrite_centered_image_line(line)


def _rewrite_stretch_image_line(line: str) -> str:
    match = _IMAGE_ATTR_LINE_RE.match(line)
    if match is None:
        return line

    attrs = _parse_image_attrs(match.group("attrs"))
    if attrs.get("stretch", "").lower() != "true":
        return line

    options: list[str] = []
    width = _percent_graphics_option(attrs.get("width"), r"\textwidth")
    height = _percent_graphics_option(attrs.get("height"), r"\textheight")
    if width is not None:
        options.append(f"width={width}")
    if height is not None:
        options.append(f"height={height}")

    option_text = f"[{','.join(options)}]" if options else ""
    return (
        f"{match.group('indent')}\\includegraphics{option_text}"
        f"{{{match.group('target')}}}{match.group('trailing')}"
    )


def _rewrite_centered_image_line(line: str) -> str:
    if line != line.lstrip():
        return line
    tokens = _match_image_only_tokens(line)
    if tokens is None:
        return line
    if len(tokens) == 1 and tokens[0].group("alt").strip():
        # Captioned lone image: pandoc renders a centered figure with caption.
        return line
    graphics = "\n".join(_fit_includegraphics(token) for token in tokens)
    return f"\\begin{{center}}\n{graphics}\n\\end{{center}}"


def _match_image_only_tokens(line: str) -> list[re.Match[str]] | None:
    if not line.startswith("!["):
        return None
    tokens = list(_IMAGE_TOKEN_RE.finditer(line))
    if not tokens:
        return None
    position = 0
    for token in tokens:
        if line[position : token.start()].strip():
            return None
        position = token.end()
    if line[position:].strip():
        return None
    return tokens


def _fit_includegraphics(token: re.Match[str]) -> str:
    attrs = _parse_image_attrs(token.group("attrs") or "")
    width = attrs.get("width")
    height = attrs.get("height")
    width_option = _percent_graphics_option(width, r"\linewidth") or width or r"\linewidth"
    height_option = (
        _percent_graphics_option(height, r"\textheight")
        or height
        or _DEFAULT_IMAGE_HEIGHT_CAP
    )
    return (
        f"\\includegraphics[width={width_option},height={height_option},keepaspectratio]"
        f"{{{token.group('target')}}}"
    )


def _parse_image_attrs(text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in _ATTR_RE.finditer(text):
        attrs[match.group("name").lower()] = match.group("value")
    return attrs


def _percent_graphics_option(value: str | None, unit: str) -> str | None:
    if value is None or not value.endswith("%"):
        return None
    try:
        fraction = Decimal(value[:-1]) / Decimal(100)
    except InvalidOperation:
        return None
    return f"{fraction:.2f}{unit}"


def _raise_missing_frame_title(section: str | None) -> None:
    if section is None:
        raise SlidesError("Missing non-inferable frame title before frame content.")
    raise SlidesError(
        f"Missing non-inferable frame title after section {section!r} context change."
    )


def _render_events(events: list[_Frame | _Heading]) -> str:
    output: list[str] = []
    seen_frame = False

    for event in events:
        if isinstance(event, _Heading):
            _append_block(output, f"{'#' * event.level} {event.title}")
            continue

        if seen_frame:
            _append_block(output, "---")
        _append_block(output, f"### {event.title}")
        _append_block(output, "\n".join(_trim_blank_lines(event.lines)))
        seen_frame = True

    if not output:
        return ""
    return "\n".join(output).strip() + "\n"


def _append_block(output: list[str], block: str) -> None:
    block = block.strip("\n")
    if not block:
        return
    if output and output[-1] != "":
        output.append("")
    output.extend(block.splitlines())


def _trim_blank_lines(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    frontmatter_lines: list[str] = []
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() in {"---", "..."}:
            body = "\n".join(lines[index + 1 :])
            if text.endswith("\n"):
                body += "\n"
            return _parse_flat_frontmatter(frontmatter_lines), body
        frontmatter_lines.append(line)

    return {}, text


def _parse_flat_frontmatter(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        if key in _OPTION_NAMES:
            values[key] = _clean_scalar(value)
    return values


def _clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1].strip()
    if "#" in value:
        value = value.split("#", 1)[0].strip()
    return value


def _parse_bool(name: str, value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "on", "1"}:
        return True
    if normalized in {"false", "no", "off", "0"}:
        return False
    raise SlidesError(f"{name} must be a bool scalar.")


def _parse_positive_int(name: str, value: str) -> int:
    try:
        parsed = int(value.strip())
    except ValueError as exc:
        raise SlidesError(f"{name} must be a positive int.") from exc
    if parsed < 1:
        raise SlidesError(f"{name} must be a positive int.")
    return parsed


def _parse_choice(name: str, value: str, choices: tuple[str, ...]) -> str:
    normalized = value.strip().lower()
    if normalized in choices:
        return normalized
    supported = ", ".join(choices)
    raise SlidesError(f"{name} must be one of: {supported}.")
