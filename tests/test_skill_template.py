from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = PROJECT_ROOT / "skill" / "SKILL.md"
TEMPLATE_FILE = PROJECT_ROOT / "skill" / "templates" / "longform.md"
MIN_PDF_BYTES = 1024

REQUIRED_TEMPLATE_METADATA = (
    "title",
    "subtitle",
    "author",
    "organization",
    "course",
    "date",
    "version",
    "logo",
    "icon",
    "abstract",
    "theme",
)

SUPPORTED_HYPOLATEX_SUBCOMMANDS = frozenset({"doctor", "convert", "build"})
ALLOWED_HYPOLATEX_FLAGS = frozenset({"--help"})
HYPOLATEX_REFERENCE_RE = re.compile(
    r"(?<![\w./-])hypolatex(?![\w./-])",
    re.IGNORECASE,
)
ARG_TERMINATORS = frozenset("`'\"()[]{}<>.,;:!?")
NEGATIVE_MVP_LIMIT_PHRASES = (
    "not supported",
    "unsupported",
    "out of scope",
    "deferred",
    "not in the mvp",
    "not in mvp",
    "outside the mvp",
    "outside mvp",
    "no beamer",
    "no textual",
    "no tui",
    "no textual/tui",
    "no textual or tui",
    "不支持",
    "不在 mvp",
    "暂不",
    "延期",
    "范围外",
    "不包含",
)
ERROR_INTERPRETATION_WORDS = (
    "interpret",
    "explain",
    "diagnose",
    "triage",
    "read the error",
    "read errors",
    "exit code",
    "stderr",
    "解释",
    "诊断",
    "定位",
)
ERROR_CONTEXT_WORDS = (
    "error",
    "errors",
    "failure",
    "failed",
    "diagnostic",
    "diagnostics",
    "exit code",
    "stderr",
    "错误",
    "失败",
    "诊断",
)


def _read_required_file(path: Path) -> str:
    assert path.is_file(), f"Expected required M4 file to exist: {path}"
    return path.read_text(encoding="utf-8")


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


def _normalized(text: str) -> str:
    return text.lower()


def _assert_contains_any(text: str, options: tuple[str, ...], message: str) -> None:
    assert any(option in text for option in options), message


def _assert_near_any(
    text: str,
    anchors: tuple[str, ...],
    neighbors: tuple[str, ...],
    message: str,
    *,
    window: int = 140,
) -> None:
    for anchor in anchors:
        for match in re.finditer(re.escape(anchor), text):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            context = text[start:end]
            if any(neighbor in context for neighbor in neighbors):
                return

    assert False, message


def _assert_has_negative_limit_context(
    text: str, term: str, feature_label: str
) -> None:
    matches = list(re.finditer(re.escape(term), text))
    assert matches, f"Skill should mention {feature_label}."

    for match in matches:
        start = max(0, match.start() - 140)
        end = min(len(text), match.end() + 140)
        context = text[start:end]
        if any(phrase in context for phrase in NEGATIVE_MVP_LIMIT_PHRASES):
            return

    assert False, (
        f"Skill should pair {feature_label} with negative or deferred MVP wording."
    )


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


def test_unsupported_hypolatex_reference_helper_scans_full_text():
    assert _unsupported_hypolatex_references(
        "Prefer hypolatex publish for release handoff."
    )
    assert _unsupported_hypolatex_references("Run `hypolatex --version`.")
    assert _unsupported_hypolatex_references("Run `hypolatex --config`.")

    allowed_references = "\n".join(
        (
            "Run hypolatex doctor before conversion.",
            "Use uv run hypolatex build examples/longform.md.",
            "Check hypolatex --help when unsure.",
            "The public CLI is hypolatex.",
            "Use hypolatex\nbefore choosing a supported subcommand.",
        )
    )
    assert _unsupported_hypolatex_references(allowed_references) == []


def test_skill_markdown_has_ai_readable_frontmatter_for_hypolatex_workflows():
    frontmatter = _frontmatter(_read_required_file(SKILL_FILE))

    assert frontmatter.get("name"), "Skill frontmatter must include name."
    description = _normalized(frontmatter.get("description", ""))
    assert description, "Skill frontmatter must include description."
    _assert_contains_any(
        description,
        ("hypo-latex", "hypolatex"),
        "Description should identify the Hypo-LaTeX workflow.",
    )
    _assert_contains_any(
        description,
        ("create", "author", "write", "draft", "创建", "撰写", "写作"),
        "Description should trigger document creation or authoring use cases.",
    )
    _assert_contains_any(
        description,
        ("convert", "conversion", "转换"),
        "Description should trigger document conversion use cases.",
    )
    _assert_contains_any(
        description,
        ("build", "compile", "pdf", "构建", "编译"),
        "Description should trigger PDF build use cases.",
    )


def test_skill_markdown_guides_real_cli_commands_and_dependency_honesty():
    text = _read_required_file(SKILL_FILE)
    normalized = _normalized(text)

    for command in ("hypolatex doctor", "hypolatex convert", "hypolatex build"):
        assert command in normalized, (
            f"Skill must instruct AI agents to run `{command}`."
        )

    unsupported_references = _unsupported_hypolatex_references(text)
    assert not unsupported_references, (
        "Skill should only reference MVP CLI subcommands "
        "`doctor`, `convert`, and `build`; `hypolatex --help` and bare "
        "`hypolatex` are also allowed. Unsupported references: "
        + ", ".join(unsupported_references)
    )

    _assert_near_any(
        normalized,
        ("hypolatex doctor",),
        (
            "environment",
            "dependency",
            "dependencies",
            "diagnostic",
            "check",
            "检查环境",
            "环境",
            "依赖",
            "诊断",
        ),
        "Skill should guide AI agents to run `hypolatex doctor` for "
        "environment checks.",
    )
    _assert_near_any(
        normalized,
        (
            "skill/templates/longform.md",
            ".md template",
            "markdown template",
            ".md 模板",
            "模板",
        ),
        (
            "copy",
            "create",
            "edit",
            "duplicate",
            "复制",
            "创建",
            "新建",
            "编辑",
        ),
        "Skill should guide template creation or editing with the Markdown template.",
    )
    _assert_contains_any(
        normalized,
        ERROR_INTERPRETATION_WORDS,
        "Skill should tell AI agents to interpret or explain errors.",
    )
    for anchors, label in (
        (("convert", "转换"), "convert"),
        (("build", "构建", "编译"), "build"),
        (("latexmk",), "latexmk"),
        (("pandoc",), "Pandoc"),
        (("dependency", "dependencies", "依赖"), "dependency"),
    ):
        _assert_near_any(
            normalized,
            anchors,
            ERROR_CONTEXT_WORDS,
            f"Skill should explain how to interpret {label} errors.",
        )

    _assert_contains_any(
        normalized,
        ("missing", "not found", "dependency", "dependencies", "缺依赖", "缺少依赖"),
        "Skill should explain how to handle missing dependency diagnostics.",
    )
    _assert_contains_any(
        normalized,
        ("ask the user", "tell the user", "let the user", "请用户", "让用户"),
        "Skill should tell the AI to ask the user to install missing dependencies.",
    )
    _assert_contains_any(
        normalized,
        ("do not fake", "don't fake", "do not pretend", "不要伪造", "不要假装"),
        "Skill should explicitly prohibit pretending that dependencies were installed.",
    )


def test_skill_markdown_names_mvp_limits():
    normalized = _normalized(_read_required_file(SKILL_FILE))

    assert "xelatex" in normalized
    _assert_contains_any(
        normalized,
        ("first", "primary", "preferred", "default", "优先", "默认"),
        "Skill should state the XeLaTeX-first MVP build direction.",
    )

    assert "pandoc" in normalized
    _assert_contains_any(
        normalized,
        ("required", "must be installed", "must exist", "必需", "必须", "必要"),
        "Skill should state that Pandoc is required.",
    )

    _assert_has_negative_limit_context(normalized, "beamer", "Beamer")

    _assert_has_negative_limit_context(normalized, "textual", "Textual")
    _assert_has_negative_limit_context(normalized, "tui", "TUI")


def test_longform_template_covers_confirmed_metadata_and_directives():
    text = _read_required_file(TEMPLATE_FILE)
    frontmatter = _frontmatter(text)

    for field in REQUIRED_TEMPLATE_METADATA:
        assert frontmatter.get(field), (
            f"Skill longform template must include frontmatter field `{field}`."
        )

    for directive in ("note", "tip", "warning", "summary"):
        assert _has_callout_directive(text, directive), (
            f"Skill longform template must include `{directive}` directive syntax."
        )

    assert re.search(r":::\s*\{[^}]*\.figure\b[^}]*\blabel=", text), (
        "Skill longform template must include a figure directive with label."
    )
    assert re.search(r":::\s*\{[^}]*\.figure\b[^}]*\bsrc=", text), (
        "Skill longform template must include a figure directive with src."
    )
    assert re.search(r":::\s*\{[^}]*\.figure\b[^}]*\bcaption=", text), (
        "Skill longform template must include a figure directive with caption."
    )
    assert re.search(r":::\s*\{[^}]*\.ref\b[^}]*\btarget=", text), (
        "Skill longform template must include a ref directive with target."
    )


def _has_callout_directive(text: str, directive: str) -> bool:
    return f":::{directive}" in text or bool(
        re.search(rf":::\s*\{{[^}}]*\.{re.escape(directive)}\b", text)
    )


def test_skill_longform_template_builds_to_non_empty_pdf(runner, cli_app, tmp_path):
    _read_required_file(TEMPLATE_FILE)
    output_path = tmp_path / "skill-longform.pdf"

    result = runner.invoke(
        cli_app,
        ["build", str(TEMPLATE_FILE), "--output", str(output_path)],
    )

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES
