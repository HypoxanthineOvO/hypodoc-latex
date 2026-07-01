from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = PROJECT_ROOT / "skill" / "SKILL.md"
DOCS_C3_GUIDANCE = PROJECT_ROOT / "docs" / "c3-authoring.md"
PROJECT_TEMPLATE = PROJECT_ROOT / "skill" / "templates" / "project.md"
REVIEW_TEMPLATE = PROJECT_ROOT / "skill" / "templates" / "review.md"
PRIVATE_ROOT = PROJECT_ROOT / "tests" / "private"
PRIVATE_CORPUS_ENV = "HYPOLATEX_TEST_CORPUS"
MIN_PDF_BYTES = 1024

SEMANTIC_DIRECTIVES = (
    "objective",
    "info",
    "task",
    "requirement",
    "deliverable",
    "checklist",
    "rubric",
)
REVIEW_DIRECTIVES = ("question", "hint", "answer", "solution")
ANSWER_MODES = ("student", "review", "teacher")
QUESTION_STYLES = ("outline", "plain", "card")
TABLE_TYPES = (
    "default",
    "comparison",
    "checklist",
    "rubric",
    "cheatsheet",
    "compact",
    "long",
)
TABLE_DENSITIES = ("compact", "normal", "comfortable")


def _read_required_file(path: Path) -> str:
    assert path.is_file(), f"Expected required M6 skill/docs file to exist: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def _has_directive(text: str, directive: str) -> bool:
    return f":::{directive}" in text or bool(
        re.search(rf":::\s*\{{[^}}]*\.{re.escape(directive)}\b", text)
    )


def _assert_contains_all(text: str, terms: tuple[str, ...], label: str) -> None:
    missing = [term for term in terms if term not in text]
    assert not missing, f"{label} missing required terms: {missing}"


def _assert_near_any(
    text: str,
    anchors: tuple[str, ...],
    neighbors: tuple[str, ...],
    message: str,
    *,
    window: int = 180,
) -> None:
    for anchor in anchors:
        for match in re.finditer(re.escape(anchor), text):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            context = text[start:end]
            if any(neighbor in context for neighbor in neighbors):
                return

    assert False, message


def _invoke_build(runner, cli_app, input_path: Path, output_path: Path, *extra_args):
    return runner.invoke(
        cli_app,
        ["build", str(input_path), "--output", str(output_path), *extra_args],
    )


def _assert_non_empty_pdf(output_path: Path) -> None:
    assert output_path.suffix == ".pdf"
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES


def test_skill_docs_contract_explains_c3_authoring_surface():
    text = _normalized(_read_required_file(SKILL_FILE))

    _assert_contains_all(
        text,
        ("semantic", "vocabulary", "project", "assignment"),
        "Skill docs semantic vocabulary contract",
    )
    _assert_contains_all(
        text,
        SEMANTIC_DIRECTIVES,
        "Skill docs project/assignment semantic block vocabulary",
    )
    _assert_contains_all(
        text,
        REVIEW_DIRECTIVES,
        "Skill docs review question vocabulary",
    )
    _assert_near_any(
        text,
        ("review question", "question"),
        ("hint", "answer", "solution"),
        "Skill docs should teach the review-question block family together.",
    )


def test_skill_docs_contract_explains_answer_mode_precedence():
    text = _normalized(_read_required_file(SKILL_FILE))

    _assert_contains_all(
        text,
        ("answer_mode", "--answer-mode", "frontmatter"),
        "Skill docs answer_mode contract",
    )
    _assert_contains_all(text, ANSWER_MODES, "Skill docs supported answer modes")
    _assert_near_any(
        text,
        ("--answer-mode",),
        ("override", "overrides", "wins", "precedence", "frontmatter"),
        "Skill docs must state that CLI `--answer-mode` overrides frontmatter.",
    )
    _assert_near_any(
        text,
        ("frontmatter",),
        ("default", "student", "answer_mode", "precedence"),
        "Skill docs must explain the frontmatter/default answer_mode path.",
    )


def test_skill_docs_contract_explains_question_styles_and_plain_aliases():
    text = _normalized(_read_required_file(SKILL_FILE))

    _assert_contains_all(
        text,
        QUESTION_STYLES,
        "Skill docs question style contract",
    )
    _assert_near_any(
        text,
        ("plain",),
        ("text", "inline", "alias", "aliases"),
        "Skill docs should say text/inline are aliases for plain, while plain "
        "is the canonical non-card spelling.",
    )
    _assert_near_any(
        text,
        ("plain",),
        ("non-card", "text-first", "ordinary text flow", "no surrounding box"),
        "Skill docs should explain that plain is true non-card text flow.",
    )


def test_skill_docs_contract_explains_table_dsl_and_longtable_fallback():
    text = _normalized(_read_required_file(SKILL_FILE))

    _assert_contains_all(
        text,
        (".table", "controlled table", "yaml", "columns", "longtable"),
        "Skill docs controlled table DSL contract",
    )
    _assert_near_any(
        text,
        ("yaml",),
        ("columns", "align", "width", "weight"),
        "Skill docs must show YAML `columns` configuration for controlled tables.",
    )
    _assert_near_any(
        text,
        ("longtable",),
        ("fallback", "falls back", "long", "multi-page"),
        "Skill docs must explain the longtable fallback for long controlled tables.",
    )
    _assert_contains_all(
        text,
        TABLE_TYPES,
        "Skill docs controlled table type contract",
    )
    _assert_contains_all(
        text,
        TABLE_DENSITIES,
        "Skill docs controlled table density contract",
    )
    _assert_near_any(
        text,
        ("ordinary markdown", "outside `.table`", "outside .table"),
        ("pandoc", "ordinary", "do not wrap", "reserve"),
        "Skill docs should clarify ordinary Markdown tables remain ordinary.",
    )
    _assert_near_any(
        text,
        ("row spans", "column spans"),
        ("do not support", "unsupported", "does not support"),
        "Skill docs must document that controlled tables do not support row or column spans.",
    )
    _assert_near_any(
        text,
        ("exactly one markdown table",),
        ("yaml", "optional yaml", "after"),
        "Skill docs must state that `.table` contains exactly one Markdown table after optional YAML.",
    )


def test_skill_docs_contract_explains_public_private_validation_and_artifacts():
    text = _normalized(_read_required_file(SKILL_FILE))

    _assert_contains_all(
        text,
        (
            "public",
            "private",
            "private corpus",
            "hypolatex_test_corpus",
            "tests/private/corpus",
        ),
        "Skill docs public/private validation contract",
    )
    _assert_near_any(
        text,
        ("private corpus", "tests/private/corpus", "hypolatex_test_corpus"),
        ("prepare", "manifest", "workflow", "smoke", "pytest"),
        "Skill docs must document the private corpus workflow, not only name it.",
    )
    _assert_near_any(
        text,
        ("artifact", "artifacts", "results", "pdf"),
        ("do not commit", "don't commit", "not commit", "never commit"),
        "Skill docs must state that real corpus artifacts/results are not committed.",
    )


def test_docs_c3_authoring_guidance_exists_and_summarizes_public_contract():
    text = _normalized(_read_required_file(DOCS_C3_GUIDANCE))

    _assert_contains_all(
        text,
        (
            "c3",
            "semantic",
            "block",
            "answer_mode",
            "--answer-mode",
            "frontmatter",
            ".table",
            "yaml",
            "columns",
            "longtable",
            "public",
            "private",
            "private corpus",
        ),
        "Docs-side C3 authoring guidance",
    )
    _assert_contains_all(
        text,
        SEMANTIC_DIRECTIVES,
        "Docs-side C3 semantic block vocabulary",
    )
    _assert_contains_all(
        text,
        REVIEW_DIRECTIVES,
        "Docs-side C3 review block vocabulary",
    )
    _assert_near_any(
        text,
        ("--answer-mode",),
        ("override", "overrides", "wins", "precedence", "frontmatter"),
        "Docs-side C3 guidance must explain CLI/frontmatter answer_mode precedence.",
    )
    _assert_near_any(
        text,
        ("longtable",),
        ("fallback", "falls back", "long", "multi-page"),
        "Docs-side C3 guidance must explain the longtable fallback.",
    )
    _assert_contains_all(
        text,
        QUESTION_STYLES,
        "Docs-side C3 question style contract",
    )
    _assert_contains_all(
        text,
        TABLE_TYPES,
        "Docs-side C3 controlled table type contract",
    )
    _assert_contains_all(
        text,
        TABLE_DENSITIES,
        "Docs-side C3 controlled table density contract",
    )
    _assert_near_any(
        text,
        ("ordinary markdown", "outside `.table`", "outside .table"),
        ("pandoc", "ordinary", "reserve"),
        "Docs-side C3 guidance should clarify ordinary Markdown tables remain ordinary.",
    )
    _assert_near_any(
        text,
        ("row spans", "column spans"),
        ("do not support", "unsupported", "does not support"),
        "Docs-side C3 guidance must document controlled table span limits.",
    )
    _assert_near_any(
        text,
        ("private corpus", "hypolatex_test_corpus", "tests/private/corpus"),
        ("workflow", "prepare", "manifest", "smoke", "pytest"),
        "Docs-side C3 guidance must summarize the private corpus workflow.",
    )
    _assert_near_any(
        text,
        ("artifact", "artifacts", "results", "pdf"),
        ("do not commit", "don't commit", "not commit", "never commit"),
        "Docs-side C3 guidance must state real artifacts/results are not committed.",
    )


def test_project_template_demonstrates_project_assignment_blocks_and_controlled_table():
    text = _read_required_file(PROJECT_TEMPLATE)
    normalized = _normalized(text)

    assert "project" in normalized
    assert "assignment" in normalized
    for directive in SEMANTIC_DIRECTIVES:
        assert _has_directive(text, directive), (
            "Project template should demonstrate the project/assignment "
            f"semantic block `:::{directive}`."
        )

    assert _has_directive(text, "table"), (
        "Project template should demonstrate the controlled `.table` DSL."
    )
    _assert_contains_all(
        normalized,
        (".table", "columns:", "caption", "label"),
        "Project template controlled table example",
    )


def test_review_template_demonstrates_review_blocks_and_answer_mode_behavior():
    text = _read_required_file(REVIEW_TEMPLATE)
    normalized = _normalized(text)

    for directive in REVIEW_DIRECTIVES:
        assert _has_directive(text, directive), (
            f"Review template should demonstrate `:::{directive}`."
        )

    _assert_contains_all(
        normalized,
        ("answer_mode", "--answer-mode", *ANSWER_MODES),
        "Review template answer-mode guidance",
    )
    _assert_near_any(
        normalized,
        ("student",),
        ("hide", "hides", "omit", "omits", "without"),
        "Review template should say student mode hides answer/solution content.",
    )
    _assert_near_any(
        normalized,
        ("review", "teacher"),
        ("show", "shows", "include", "includes", "answer", "solution"),
        "Review template should say review/teacher modes show answer/solution content.",
    )


@pytest.mark.parametrize(
    ("template_path", "build_args", "output_name"),
    (
        pytest.param(PROJECT_TEMPLATE, (), "skill-project-template.pdf", id="project"),
        pytest.param(
            REVIEW_TEMPLATE,
            ("--answer-mode", "review"),
            "skill-review-template.pdf",
            id="review-answer-mode",
        ),
    ),
)
def test_skill_c3_templates_build_to_non_empty_pdf(
    runner,
    cli_app,
    tmp_path,
    template_path,
    build_args,
    output_name,
):
    _read_required_file(template_path)
    output_path = tmp_path / output_name

    result = _invoke_build(runner, cli_app, template_path, output_path, *build_args)

    assert result.exit_code == 0, result.output
    _assert_non_empty_pdf(output_path)


def test_private_validation_paths_are_gitignored_for_real_corpus_artifacts():
    ignored_paths = (
        "tests/private/corpus/real-corpus-sample.md",
        "tests/private/results/m6-private-smoke.pdf",
        "tests/private/results/m6-private-smoke.tex",
        "tests/private/results/m6-private-smoke.log",
        "tests/private/results/m6-private-smoke.json",
    )
    for ignored_path in ignored_paths:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", ignored_path],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0, (
            f"{ignored_path} must be ignored so real corpus artifacts are not "
            "accidentally committed."
        )


@pytest.mark.private_corpus
def test_private_corpus_marker_uses_env_root_and_keeps_outputs_in_tmp_path(
    private_corpus_root,
    tmp_path,
):
    assert PRIVATE_CORPUS_ENV in os.environ

    configured_root = Path(os.environ[PRIVATE_CORPUS_ENV]).expanduser()
    if not configured_root.is_absolute():
        configured_root = (PROJECT_ROOT / configured_root).resolve(strict=False)

    assert Path(private_corpus_root) == configured_root
    assert tmp_path.exists()
    assert not tmp_path.is_relative_to(PRIVATE_ROOT)
