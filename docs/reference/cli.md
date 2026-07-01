# Hypo-LaTeX CLI Reference

The CLI entry point is `hypolatex`.

## Commands

```text
hypolatex doctor
hypolatex convert INPUT_PATH --output OUTPUT.tex
hypolatex build INPUT_PATH --output OUTPUT.pdf
```

## `hypolatex doctor`

Checks required local executables and TeX packages.

```bash
uv run hypolatex doctor
```

Use this before conversion or PDF builds. Dependency diagnostics from `doctor`
are authoritative for missing tools and packages.

## `hypolatex convert`

Converts HypoDoc Markdown to a standalone LaTeX document.

```bash
uv run hypolatex convert INPUT.md --output OUTPUT.tex
```

Options:

| Option | Meaning |
|---|---|
| `--output`, `-o` | required LaTeX output file |
| `--theme` | theme preset ID; overrides Markdown frontmatter `theme` |
| `--answer-mode` | `student`, `review`, or `teacher`; overrides frontmatter `answer_mode` |

## `hypolatex build`

Converts HypoDoc Markdown and compiles a PDF with XeLaTeX.

```bash
uv run hypolatex build INPUT.md --output OUTPUT.pdf
```

Options:

| Option | Meaning |
|---|---|
| `--output`, `-o` | required PDF output file |
| `--paper` | paper size, currently `a4paper` or `letterpaper`; default `a4paper` |
| `--theme` | theme preset ID; overrides Markdown frontmatter `theme` |
| `--answer-mode` | `student`, `review`, or `teacher`; overrides frontmatter `answer_mode` |

## Common Examples

Build a classic-readable longform PDF:

```bash
uv run hypolatex build skill/templates/longform.md \
  --theme classic-readable \
  --output build/longform.pdf
```

Build a review copy with answers visible:

```bash
uv run hypolatex build skill/templates/review.md \
  --answer-mode review \
  --output build/review.pdf
```

Generate TeX for review:

```bash
uv run hypolatex convert skill/templates/project.md \
  --output build/project.tex
```
