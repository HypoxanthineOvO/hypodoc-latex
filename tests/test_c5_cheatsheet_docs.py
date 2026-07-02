from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = PROJECT_ROOT / "skill" / "SKILL.md"
DOCS_C5_CHEATSHEET = PROJECT_ROOT / "docs" / "c5-cheatsheet.md"
CHEATSHEET_TEMPLATE = PROJECT_ROOT / "skill" / "templates" / "cheatsheet.md"

SUPPORTED_HYPOLATEX_SUBCOMMANDS = frozenset({"doctor", "convert", "build"})
ALLOWED_HYPOLATEX_FLAGS = frozenset({"--help"})
HYPOLATEX_REFERENCE_RE = re.compile(
    r"(?<![\w./-])hypolatex(?![\w./-])",
    re.IGNORECASE,
)
ARG_TERMINATORS = frozenset("`'\"()[]{}<>.,;:!?")


def _read_required_file(path: Path) -> str:
    assert path.is_file(), f"Expected required C5 cheatsheet file to exist: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def _frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", text, re.DOTALL)
    assert match, "Expected YAML frontmatter delimited by leading --- blocks."
    return _parse_simple_yaml_mapping(match.group("body"))


def _parse_simple_yaml_mapping(frontmatter: str) -> dict[str, str]:
    data: dict[str, str] = {}
    current_block_key: str | None = None

    for line in frontmatter.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        key_match = re.match(r"^(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)$", line)
        if key_match:
            key = key_match.group("key")
            value = key_match.group("value").strip()
            current_block_key = key if value in {"|", ">"} else None
            data[key] = "" if current_block_key else value.strip("\"'")
            continue

        if current_block_key and line.startswith((" ", "\t")):
            data[current_block_key] = (
                f"{data[current_block_key]} {line.strip()}".strip()
            )

    return data


def _assert_contains_all(text: str, terms: tuple[str, ...], label: str) -> None:
    missing = [term for term in terms if term not in text]
    assert not missing, f"{label} missing required terms: {missing}"


def _assert_near_any(
    text: str,
    anchors: tuple[str, ...],
    neighbors: tuple[str, ...],
    message: str,
    *,
    window: int = 220,
) -> None:
    for anchor in anchors:
        for match in re.finditer(re.escape(anchor), text):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            context = text[start:end]
            if any(neighbor in context for neighbor in neighbors):
                return

    assert False, message


def _next_hypolatex_token(text: str, start: int) -> str | None:
    index = start
    while index < len(text) and text[index] in " \t":
        index += 1

    if index >= len(text) or text[index] in "\r\n" or text[index] in ARG_TERMINATORS:
        return None

    end = index
    while (
        end < len(text)
        and not text[end].isspace()
        and text[end] not in ARG_TERMINATORS
    ):
        end += 1

    return text[index:end].lower()


def _hypolatex_reference_context(text: str, start: int, end: int) -> str:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end].strip()


def _unsupported_hypolatex_references(text: str) -> list[str]:
    unsupported: list[str] = []

    for match in HYPOLATEX_REFERENCE_RE.finditer(text):
        token = _next_hypolatex_token(text, match.end())
        if not token or token in ALLOWED_HYPOLATEX_FLAGS:
            continue

        context = _hypolatex_reference_context(text, match.start(), match.end())
        if token.startswith("-"):
            unsupported.append(f"`hypolatex {token}` in {context!r}")
        elif token[0].isalpha():
            if token not in SUPPORTED_HYPOLATEX_SUBCOMMANDS:
                unsupported.append(f"`hypolatex {token}` in {context!r}")
        else:
            unsupported.append(f"`hypolatex {token}` in {context!r}")

    return unsupported


def _assert_priority_order(text: str) -> None:
    priority_patterns = (
        r"compression[^.]{0,240}formulas[^.]{0,120}keypoints[^.]{0,120}examples",
        r"priority[^.]{0,240}formulas[^.]{0,120}keypoints[^.]{0,120}examples",
        r"formulas\s*>\s*keypoints\s*>\s*examples",
    )
    assert any(re.search(pattern, text) for pattern in priority_patterns), (
        "Skill docs must state the compression priority order: "
        "formulas > keypoints > examples."
    )


def test_skill_command_names_hd_make_cheatsheet_and_ai_facing_boundary():
    text = _read_required_file(SKILL_FILE)
    normalized = _normalized(text)

    assert "hd:make-cheatsheet" in normalized, (
        "Skill docs must expose the AI-facing `hd:make-cheatsheet` command."
    )
    _assert_near_any(
        normalized,
        ("hd:make-cheatsheet",),
        ("ai-facing", "skill command", "skill workflow"),
        "`hd:make-cheatsheet` must be described as an AI-facing Skill Command "
        "or Skill workflow.",
    )
    _assert_near_any(
        normalized,
        ("hd:make-cheatsheet", "skill command", "skill workflow"),
        ("not a cli", "not a hypolatex cli", "not a subcommand", "not a cli subcommand"),
        "Skill docs must explicitly say this is not a `hypolatex` CLI subcommand.",
    )

    unsupported_references = _unsupported_hypolatex_references(text)
    hd_references = [ref for ref in unsupported_references if "hd:" in ref]
    assert not hd_references, (
        "The unsupported-command helper must not see `hd:make-cheatsheet` as "
        f"`hypolatex hd:...`: {hd_references}"
    )


def test_skill_command_keeps_deterministic_build_on_hypolatex_build():
    normalized = _normalized(_read_required_file(SKILL_FILE))

    _assert_near_any(
        normalized,
        ("deterministic",),
        ("hypolatex build",),
        "The deterministic build path must still call `hypolatex build`.",
    )
    _assert_near_any(
        normalized,
        ("distill",),
        ("no", "not", "do not", "without", "unsupported", "not add", "not create"),
        "Skill docs must say the workflow does not add a distill subcommand.",
    )
    _assert_near_any(
        normalized,
        ("extraction cli", "deterministic extraction"),
        ("no", "not", "do not", "without", "unsupported", "not add", "not create"),
        "Skill docs must say deterministic extraction is not a new CLI surface.",
    )
    assert "hypolatex distill" not in normalized, (
        "Mention distill as an unsupported concept without documenting a fake "
        "`hypolatex distill` command."
    )


def test_skill_command_preserves_sources_and_writes_new_cheatsheet_markdown():
    normalized = _normalized(_read_required_file(SKILL_FILE))

    _assert_near_any(
        normalized,
        ("source document", "source material", "input document"),
        ("not modify", "do not modify", "unchanged", "read-only", "preserve"),
        "Skill docs must say source documents are not modified.",
    )
    _assert_near_any(
        normalized,
        ("cheatsheet markdown", "cheatsheet .md", "new markdown"),
        ("generate", "create", "write", "new"),
        "Skill docs must say the workflow generates a new cheatsheet Markdown file.",
    )


def test_skill_command_output_choices_and_compression_contract():
    normalized = _normalized(_read_required_file(SKILL_FILE))

    _assert_contains_all(
        normalized,
        ("formulas", "keypoints", "examples"),
        "Skill command output choices",
    )
    _assert_near_any(
        normalized,
        ("output choices", "output_choices", "choice", "choices"),
        ("formulas", "keypoints", "examples"),
        "Skill docs must describe formulas/keypoints/examples as output choices.",
    )
    _assert_near_any(
        normalized,
        ("target pages", "target_pages"),
        ("hard constraint", "strict", "must fit", "blocking"),
        "Skill docs must state target pages are a hard constraint.",
    )
    _assert_priority_order(normalized)


def test_skill_command_conflict_report_and_private_data_policy():
    normalized = _normalized(_read_required_file(SKILL_FILE))

    _assert_contains_all(
        normalized,
        (
            "conflict report",
            "target pages",
            "actual pages",
            "omitted candidates",
            "suggested user action",
        ),
        "Skill command conflict report format",
    )
    _assert_contains_all(
        normalized,
        ("blocking",),
        "Skill command conflict report blocking-cell field",
    )
    assert (
        "keep" in normalized
        and ("high-priority" in normalized or "high priority" in normalized)
        and "cells" in normalized
    ), (
        "Conflict reports must include blocking keep/high-priority cells."
    )

    _assert_near_any(
        normalized,
        ("source material", "source materials"),
        ("local", "not committed", "do not commit", "never commit"),
        "Private-data policy must keep source material local and uncommitted.",
    )
    _assert_near_any(
        normalized,
        ("generated artifacts", "real generated artifacts"),
        ("local", "not committed", "do not commit", "never commit"),
        "Private-data policy must keep real generated artifacts local and uncommitted.",
    )


def test_c5_cheatsheet_docs_exist_and_cover_public_contract():
    normalized = _normalized(_read_required_file(DOCS_C5_CHEATSHEET))

    _assert_contains_all(
        normalized,
        (
            "layout api",
            "layout: cheatsheet",
            "cheatsheet-grid",
            "cheatsheet-cell",
            "article",
            "fallback",
            "target pages",
            "hard constraint",
        ),
        "C5 cheatsheet docs public contract",
    )
    _assert_near_any(
        normalized,
        ("article",),
        ("fallback", "falls back", "document_type"),
        "C5 docs must explain the article fallback behavior.",
    )


def test_cheatsheet_template_exists_with_article_frontmatter_and_public_safe_content():
    text = _read_required_file(CHEATSHEET_TEMPLATE)
    normalized = _normalized(text)
    frontmatter = _frontmatter(text)

    assert frontmatter.get("document_type") == "article"
    assert frontmatter.get("layout") == "cheatsheet"

    _assert_contains_all(
        normalized,
        ("cheatsheet-grid", "cheatsheet-cell"),
        "Cheatsheet template grid/cell syntax",
    )
    _assert_contains_all(
        normalized,
        (
            "signals",
            "systems",
            "ch1-ch4",
            "lti",
            "convolution",
            "fourier series",
            "ctft",
            "energy",
            "power",
            "parseval",
            "一、复数与三角函数",
            "模、共轭、复值、辐角",
            "欧拉公式",
            "别忘了",
            "1/(2j)",
            "补充",
        ),
        "Cheatsheet template dense signals-and-systems demo markers",
    )
    for top_level_heading in (
        "一、复数与三角函数",
        "二、ch1 基本信号",
        "三、lti systems & convolution",
        "四、ch3. fourier series",
        "五、ch4. c.t.f.t.",
    ):
        assert normalized.count(top_level_heading) == 1, (
            "Cheatsheet template should preserve each handwritten top-level "
            f"section exactly once; repeated heading: {top_level_heading!r}"
        )
        assert f"# {top_level_heading} {{.manual-number}}" in normalized, (
            "Each handwritten top-level section must be a plain flowing "
            "Markdown heading (not a boxed cell title): "
            f"{top_level_heading!r}"
        )

    cell_count = normalized.count("cheatsheet-cell")
    assert 2 <= cell_count <= 6, (
        "Cheatsheet cells are reserved for reminder/margin-note callouts "
        '(e.g. "别忘了", "补充"); body sections must flow as plain headings '
        f"and text, so only a few callout cells are expected, found: {cell_count}"
    )
    assert "\\columnbreak" not in text, (
        "Cheatsheet template must rely on natural multicols auto-flow instead "
        "of manual column breaks."
    )

    private_markers = (
        "confidential",
        "proprietary",
        "private corpus",
        "real generated artifact",
        "real source material",
        "customer",
        "internal-only",
    )
    leaked_markers = [marker for marker in private_markers if marker in normalized]
    assert not leaked_markers, (
        "Cheatsheet template must use public-safe sample content; found private "
        f"markers: {leaked_markers}"
    )
    assert any(
        marker in normalized for marker in ("public-safe", "public safe", "sample", "example", "synthetic")
    ), "Cheatsheet template should make its sample/public-safe nature clear."
