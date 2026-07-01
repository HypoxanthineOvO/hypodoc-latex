from __future__ import annotations

from pathlib import Path
import re

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_FILE = PROJECT_ROOT / "skill" / "SKILL.md"
TEMPLATE_FILE = PROJECT_ROOT / "skill" / "templates" / "longform.md"
MIN_PDF_BYTES = 1024

ADVANCED_STYLE_FIELDS = frozenset(
    {
        "font",
        "fonts",
        "mainfont",
        "sansfont",
        "monofont",
        "cjkfont",
        "paper",
        "paper_size",
        "accent",
        "accent_color",
        "resource_root",
        "resource-root",
        "cover_layout",
        "cover_image",
    }
)

ADVANCED_OVERRIDE_GROUPS = {
    "font": (
        "font",
        "fonts",
        "mainfont",
        "sansfont",
        "monofont",
        "cjkfont",
    ),
    "paper": ("paper", "paper_size", "paper size"),
    "accent": ("accent", "accent_color", "accent color"),
    "resource-root": ("resource-root", "resource_root", "resource root"),
    "cover": ("cover_layout", "cover_image", "cover layout", "cover image"),
}

OPTIONAL_ADVANCED_WORDS = (
    "optional",
    "advanced",
    "override",
    "overrides",
    "tuning",
    "only when",
)

PDF_EVIDENCE_TERMS = (
    "pdf evidence",
    "poppler",
    "pdfinfo",
    "pdftotext",
    "pdftoppm",
)


def _read_required_file(path: Path) -> str:
    assert path.is_file(), f"Expected required M6 contract file to exist: {path}"
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


def _has_theme_only_authoring_guidance(text: str) -> bool:
    theme_token = r"`?theme:?\s*`?"
    patterns = (
        rf"(ordinary|normal|default|typical|ai authoring|ai authors?).{{0,120}}"
        rf"(only|just|single|minimal|required).{{0,80}}{theme_token}",
        rf"{theme_token}.{{0,80}}(only|just).{{0,120}}"
        rf"(ordinary|normal|default|typical|ai authoring|ai authors?)",
        rf"(minimal|theme-first|theme first).{{0,120}}{theme_token}",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def test_skill_docs_publish_complete_five_theme_matrix():
    from hypolatex import themes

    text = _normalized(_read_required_file(SKILL_FILE))
    theme_ids = themes.valid_theme_ids()

    assert len(theme_ids) == 5, "M6 expects the C2 five-theme registry."
    missing_theme_ids = [theme_id for theme_id in theme_ids if theme_id not in text]
    assert not missing_theme_ids, (
        "Skill docs must list or explicitly reference the complete C2 theme "
        f"matrix. Missing theme IDs: {missing_theme_ids}"
    )


def test_skill_docs_make_theme_the_only_normal_ai_authoring_field():
    text = _normalized(_read_required_file(SKILL_FILE))

    assert "theme-first" in text or "theme first" in text, (
        "Skill docs should name the theme-first authoring contract."
    )
    _assert_near_any(
        text,
        ("theme",),
        ("choose", "select", "pick", "preset"),
        "Skill docs should tell AI authors to choose a theme preset first.",
    )
    assert _has_theme_only_authoring_guidance(text), (
        "Skill docs should state that ordinary AI authoring only needs `theme`, "
        "with other style knobs outside the normal default path."
    )


@pytest.mark.parametrize(
    ("group_name", "field_terms"),
    tuple(ADVANCED_OVERRIDE_GROUPS.items()),
)
def test_skill_docs_classify_style_knobs_as_optional_advanced_overrides(
    group_name: str,
    field_terms: tuple[str, ...],
):
    text = _normalized(_read_required_file(SKILL_FILE))

    assert any(term in text for term in field_terms), (
        f"Skill docs should mention {group_name} fields as available advanced "
        "style controls."
    )
    _assert_near_any(
        text,
        field_terms,
        OPTIONAL_ADVANCED_WORDS,
        f"Skill docs should classify {group_name} fields as optional advanced "
        "overrides, not normal AI authoring defaults.",
    )


def test_skill_docs_require_doctor_build_then_poppler_pdf_evidence():
    text = _normalized(_read_required_file(SKILL_FILE))

    doctor_index = text.find("hypolatex doctor")
    build_index = text.find("hypolatex build")
    assert doctor_index >= 0, "Skill docs must instruct AI to run `hypolatex doctor`."
    assert build_index >= 0, "Skill docs must instruct AI to run `hypolatex build`."
    assert doctor_index < build_index, (
        "Skill docs should put `hypolatex doctor` before the first build command."
    )

    assert any(term in text for term in PDF_EVIDENCE_TERMS), (
        "Skill docs must require Poppler/PDF evidence checks after PDF builds; "
        "stopping at MVP convert/build is not enough for M6."
    )
    _assert_near_any(
        text,
        PDF_EVIDENCE_TERMS,
        ("check", "verify", "inspect", "extract", "render", "evidence"),
        "Skill docs should tell AI agents how to inspect the PDF with evidence "
        "tools such as Poppler, pdfinfo, or pdftotext.",
    )


def test_longform_template_frontmatter_is_minimal_theme_first():
    from hypolatex import themes

    frontmatter = _frontmatter(_read_required_file(TEMPLATE_FILE))

    assert frontmatter.get("theme"), (
        "Skill template frontmatter should include a theme field for theme-first "
        "authoring."
    )
    assert frontmatter["theme"] in themes.valid_theme_ids(), (
        "Skill template should select a public theme ID from the C2 registry."
    )

    present_advanced_fields = sorted(
        field for field in ADVANCED_STYLE_FIELDS if field in frontmatter
    )
    assert not present_advanced_fields, (
        "Skill template frontmatter should stay minimal and must not default "
        f"advanced style fields: {present_advanced_fields}"
    )


@pytest.mark.slow
def test_longform_template_builds_with_classic_readable_theme(
    runner,
    cli_app,
    tmp_path,
):
    output_path = tmp_path / "skill-longform-c2.pdf"

    result = runner.invoke(
        cli_app,
        [
            "build",
            str(TEMPLATE_FILE),
            "--theme",
            "classic-readable",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.stat().st_size > MIN_PDF_BYTES
