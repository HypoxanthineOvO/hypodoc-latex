# Hypo-LaTeX Developer Guide

Hypo-LaTeX is the LaTeX/PDF renderer implementation for HypoDoc Markdown. It
contains the CLI, Pandoc Lua filter, LaTeX package files, themes, templates,
tests, and AI Skill used to build PDF documents.

## Repository Layout

| Path | Purpose |
|---|---|
| `src/hypolatex` | Python CLI and bundled runtime resources |
| `src/hypolatex/resources/filters/hypolatex.lua` | Pandoc Lua filter for HypoDoc Markdown directives |
| `tex/latex/hypolatex` | LaTeX package implementation |
| `themes` | theme assets copied into builds |
| `skill` | AI-facing Skill and templates |
| `docs` | renderer docs and authoring guides |
| `tests` | public and private-lane tests |
| `spec/hypodoc` | HypoDoc Markdown spec submodule |

## Spec Submodule

`spec/hypodoc` points to the independent HypoDoc Spec repository. It is the
intended source of truth for shared HypoDoc Markdown syntax.

Clone with submodules when working on the format:

```bash
git clone --recurse-submodules <repo-url>
```

Initialize later if needed:

```bash
git submodule update --init --recursive
```

The submodule is not a runtime dependency for ordinary `hypolatex build`.

## Local Development

Install dependencies:

```bash
uv sync
```

Run environment diagnostics:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run hypolatex doctor
```

Run focused tests:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/test_skill_docs.py tests/test_table_dsl.py tests/test_review_questions.py tests/test_semantics.py -q
```

Run a broader public regression:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q
```

Private corpus tests are local-only and must not commit real inputs, generated
PDFs, logs, screenshots, summaries, or extracted text.

## Build Evidence

PDF builds should be verified with more than a zero exit code. Useful checks:

```bash
pdfinfo build/output.pdf
pdftotext build/output.pdf -
pdftoppm -png -f 1 -singlefile build/output.pdf /tmp/hypolatex-page-1
```

Use text markers and rendered page previews when validating visual behavior.

## Release Notes

Release work should keep these facts true:

- `README.md` is concise and user-facing.
- `docs/user-guide.md` contains the complete user path.
- `docs/developer.md` contains repo and testing guidance.
- `docs/reference/cli.md` mirrors the CLI surface.
- `CHANGELOG.md` records release-facing changes.
- `LICENSE` is the license authority.

Do not include private corpus content in release artifacts.
