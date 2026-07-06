# Hypo-LaTeX CLI Reference

The CLI entry point is `hypolatex`.

## Commands

```text
hypolatex doctor
hypolatex convert INPUT_PATH --output OUTPUT.tex
hypolatex build INPUT_PATH --output OUTPUT.pdf
```

`hypolatex convert` and `hypolatex build` also accept `document_type: beamer`
sources. `slides` and `presentation` are aliases for Beamer document type.

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

Build a Beamer Slides DSL deck:

```bash
uv run hypolatex build skill/templates/beamer.md \
  --output build/skill-beamer.pdf
```

Beamer contract summary: `document_type: beamer`; aliases `slides` and
`presentation`; H1 is section, H2 is subsection, H3 is frame title; `---` is a
frame separator/new frame. `frame_title_inheritance_limit` default is `3`;
`continued_title_style` values are `subtle`, `suffix`, and `none`.
`section_dividers`, `subsection_dividers`, and `strict_structure` tune the deck
structure, and H2 without H1 is invalid when strict structure is on. Density and
overfull lint are heuristic and limited, not a layout guarantee. Slide local
asset references must use relative local files or local `resource-root` /
`resource_root`; remote files are not fetched. Supported semantic blocks on
slides are `objective`, `info`, `task`, `requirement`, `deliverable`,
`checklist`, `rubric`, `question`, `hint`, `answer`, and `solution`.
