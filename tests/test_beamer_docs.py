from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = PROJECT_ROOT / "skill" / "SKILL.md"
PUBLIC_DOC_FILES = (
    PROJECT_ROOT / "docs" / "user-guide.md",
    PROJECT_ROOT / "docs" / "examples.md",
    PROJECT_ROOT / "docs" / "themes.md",
    PROJECT_ROOT / "docs" / "reference" / "cli.md",
    PROJECT_ROOT / "docs" / "c3-authoring.md",
)
PLAIN_BEAMER_THEME = PROJECT_ROOT / "themes" / "plain" / "beamer.sty"

SEMANTIC_SLIDE_BLOCKS = (
    "objective",
    "info",
    "task",
    "requirement",
    "deliverable",
    "checklist",
    "rubric",
    "question",
    "hint",
    "answer",
    "solution",
)


def _read_required_file(path: Path) -> str:
    assert path.is_file(), f"Expected required public Beamer artifact: {path}"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def _public_docs_text() -> str:
    return "\n\n".join(_read_required_file(path) for path in PUBLIC_DOC_FILES)


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


def _assert_beamer_dsl_contract_documented(text: str, label: str) -> None:
    _assert_contains_all(
        text,
        (
            "document_type: beamer",
            "presentation",
            "slides",
            "h1",
            "h2",
            "h3",
            "frame_title_inheritance_limit",
            "continued_title_style",
            "section_dividers",
            "subsection_dividers",
            "strict_structure",
            "overfull",
            "density",
            "local asset",
        ),
        label,
    )

    _assert_near_any(
        text,
        ("document_type: beamer",),
        ("presentation", "slides", "alias", "aliases"),
        f"{label} should name relevant Beamer document_type aliases.",
    )
    _assert_near_any(
        text,
        ("h1", "# "),
        ("section",),
        f"{label} should map H1 headings to Beamer sections.",
    )
    _assert_near_any(
        text,
        ("h2", "## "),
        ("subsection",),
        f"{label} should map H2 headings to Beamer subsections.",
    )
    _assert_near_any(
        text,
        ("h3", "### "),
        ("frame title", "frame titles"),
        f"{label} should map H3 headings to frame titles.",
    )
    _assert_near_any(
        text,
        ("---",),
        ("frame separator", "new frame", "split"),
        f"{label} should document `---` as the frame separator.",
    )
    _assert_near_any(
        text,
        ("frame_title_inheritance_limit",),
        ("default", "3", "limit"),
        f"{label} should document the title inheritance limit/default.",
    )
    _assert_near_any(
        text,
        ("continued_title_style", "continuation"),
        ("continued", "suffix", "subtle", "none"),
        f"{label} should document continuation title behavior.",
    )
    _assert_near_any(
        text,
        ("h2", "subsection"),
        ("h1", "invalid", "reject", "error"),
        f"{label} should state that H2 without H1 is invalid.",
    )
    _assert_near_any(
        text,
        ("overfull", "density"),
        ("heuristic", "limited", "lint", "not a layout guarantee"),
        f"{label} should document density/overfull lint limitations.",
    )
    _assert_near_any(
        text,
        ("local asset", "asset", "resource-root", "resource_root"),
        ("relative", "local", "remote", "do not fetch", "no remote"),
        f"{label} should document local asset rules for slide decks.",
    )
    _assert_near_any(
        text,
        ("semantic block", "semantic blocks", "objective", "question"),
        ("slide", "slides", "beamer", "frame"),
        f"{label} should state semantic blocks are supported on slides.",
    )
    _assert_contains_all(
        text,
        SEMANTIC_SLIDE_BLOCKS,
        f"{label} semantic slide block vocabulary",
    )


def test_public_docs_document_beamer_slides_dsl_contract():
    _assert_beamer_dsl_contract_documented(
        _normalized(_public_docs_text()),
        "Public Beamer docs",
    )


def test_skill_guidance_documents_beamer_slides_dsl_contract():
    _assert_beamer_dsl_contract_documented(
        _normalized(_read_required_file(SKILL_FILE)),
        "Skill Beamer guidance",
    )


def test_plain_beamer_theme_does_not_shadow_upstream_beamer_package_identity():
    text = _read_required_file(PLAIN_BEAMER_THEME)

    assert not re.search(r"\\ProvidesPackage\s*\{\s*beamer\s*\}", text), (
        "themes/plain/beamer.sty must not declare itself as the upstream "
        "`beamer` package before public theme loading."
    )
    provides_match = re.search(
        r"\\Provides(?:Package|File|Class|ExplPackage)\s*\{(?P<name>[^}]*)\}"
        r"(?P<description>[^\n]*)",
        text,
    )
    assert provides_match is not None, (
        "Plain Beamer theme should declare a Hypo-specific package/file identity."
    )
    identity = f"{provides_match.group('name')} {provides_match.group('description')}"
    assert re.search(r"hypo.*beamer|beamer.*hypo", identity, re.IGNORECASE), (
        "Plain Beamer theme identity should use a Hypo-specific or "
        "Beamer-theme-specific naming convention."
    )
