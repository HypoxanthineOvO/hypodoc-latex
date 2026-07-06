# C3 Authoring Guide

C3 is the Hypo-LaTeX authoring layer for structured project, assignment, review, and real-corpus validation documents. It gives authors semantic blocks, controlled review answers, and a table DSL while keeping the source in ordinary Markdown. This docs-side guide is self-contained; the runtime Skill contract in `../skill/SKILL.md` is the companion instruction for AI agents.

## Semantic Blocks

C3 semantic blocks name the purpose of a section without forcing a fixed course schema. Use them for courses, projects, research-group tasks, lab handoffs, or operational checklists.

Project and assignment semantic block vocabulary:

- `objective`: the outcome the reader should reach.
- `info`: context, assumptions, dates, materials, or constraints.
- `task`: the work unit the reader should perform.
- `requirement`: mandatory rules or acceptance constraints.
- `deliverable`: the artifact or evidence the reader must provide.
- `checklist`: completion checks before handoff or review.
- `rubric`: grading, review criteria, or non-course acceptance standards.

Example:

```markdown
::: {.objective title="目标"}
Produce a short PDF brief that can be reviewed from both Markdown and generated TeX.
:::

::: {.info title="背景"}
The source should stay small enough for a reviewer to inspect quickly.
:::

::: {.task title="任务"}
Draft the brief, build it, and record the commands used for validation.
:::

::: {.requirement title="要求"}
Use a supported theme and avoid project-specific implementation code.
:::

::: {.deliverable title="交付物"}
Submit the Markdown source and the public build evidence.
:::

::: {.checklist title="检查清单"}
- Source builds without conversion errors.
- Tables have captions and labels when they are referenced.
- Private material is not copied into public output.
:::

::: {.rubric title="验收标准"}
- The source is readable by humans and AI agents.
- The generated PDF preserves the intended module structure.
:::
```

All semantic blocks support `title="..."`. Use explicit Chinese titles in Chinese documents. The LaTeX layer renders semantic blocks as themed boxes through reusable `HypoBox` presets; authors should not fake module styling with Markdown separators.

## Review Questions

The review question vocabulary is `question`, `hint`, `answer`, and `solution`.

- `question`: prompt the reader or reviewer.
- `hint`: visible guidance that does not reveal the full response.
- `answer`: the concise expected answer.
- `solution`: a fuller explanation, rubric, or worked reasoning.

```markdown
::: {.question label="q:validation-split" title="题目 1" style="card"}
Why should public validation and private corpus validation be reported separately?
:::

:::hint
Think about what can be committed and quoted safely.
:::

:::answer
Public validation is reproducible from committed files; private validation uses real local material that must not be exposed.
:::

:::solution
Keep public tests and templates in the repository. Keep real-corpus inputs and generated results under ignored local paths, and report only pass/fail summaries or sanitized metadata.
:::
```

Questions are numbered by default. Add `numbered="false"` for an unnumbered
discussion item. Use canonical styles:

- `style="outline"`: default light framed prompt.
- `style="plain"`: true non-card text flow for the question and its
  hint/answer/solution.
- `style="card"`: strong review card.

`style="text"` and `style="inline"` are accepted aliases for `plain`, but new
sources should prefer `plain`.

```markdown
::: {.question title="非 Card 开放推理题" style="plain"}
Explain the reasoning in ordinary text flow.
:::

::: {.hint title="提示" style="plain"}
Use a short colored label rather than a card.
:::

::: {.answer title="参考答案" style="plain"}
Keep the answer in the same reading flow.
:::

::: {.solution title="解析" style="plain"}
Use the label to mark the semantic part without adding a surrounding box.
:::
```

Use `qa` when a review item should keep its question, hint, answer, and solution inside one outer card:

```markdown
::: {.qa title="复习题：导数与幂函数"}
::: {.question title="题目" numbered="false"}
求函数 $f(x)=x^3$ 的导数。
:::

:::hint
先确认幂函数求导规则。
:::

:::answer
$f'(x)=3x^2$。
:::

:::solution
根据幂函数求导规则，$\frac{d}{dx}x^n=nx^{n-1}$。
:::
:::
```

## Answer Mode Precedence

`answer_mode` controls answer visibility. The supported modes are `student`, `review`, and `teacher`.

Precedence:

1. CLI `--answer-mode` overrides frontmatter `answer_mode`.
2. Frontmatter `answer_mode` is used when no CLI override is supplied.
3. The default is `student`.

Behavior:

- `student` hides `answer` and `solution` content.
- `review` shows/includes answer and solution content for reviewer builds.
- `teacher` shows/includes answer and solution content for instructor or maintainer builds.

Use frontmatter for the document default:

```yaml
---
title: Review Packet
answer_mode: student
---
```

Use the CLI when the build needs a different view:

```bash
hypolatex build skill/templates/review.md --answer-mode review --output build/c3-skill-review.pdf
```

## Controlled Tables

Use the controlled `.table` DSL when table behavior should be predictable in
TeX and PDF output. Ordinary Markdown tables outside `.table` keep Pandoc's
normal table path, so reserve `.table` for cases where captioning, column
control, density, striping, or long-table behavior matters. A controlled table
is a fenced div with optional YAML configuration followed by exactly one
Markdown table.

````markdown
::: {.table}
```yaml
type: rubric
density: compact
caption: Review evidence map
label: tab:review-evidence
columns:
  - align: left
    width: 0.20
  - align: left
    width: 0.42
  - align: left
    width: 0.30
```

| Area | Evidence | Reviewer Check |
|---|---|---|
| Source | Markdown template | Semantic blocks are intentional |
| Build | Generated PDF | Captions and labels render |
| Privacy | Private lane notes | Real artifacts are not committed |

:::
````

YAML table configuration may set `type`, `long`, `density`, `width`, `caption`,
`label`, `header`, `striped`, and `columns`. In `columns`, use `align`, `width`,
and `weight` instead of raw LaTeX column specifications.

Supported table types are:

| Type | Use |
|---|---|
| `default` | general controlled table |
| `comparison` | comparing options, models, capabilities, or tradeoffs |
| `checklist` | status, evidence, handoff, or completion checks |
| `rubric` | grading, review, acceptance, or evaluation criteria |
| `cheatsheet` | dense quick-reference table |
| `compact` | generic dense table |
| `long` | multi-page table |

Supported densities are `compact`, `normal`, and `comfortable`. A numeric table
`width` such as `0.9` becomes `0.9\linewidth`; column widths may use fractions
or percentages such as `25%`. Labels should be simple TeX-safe identifiers
without spaces.

For long or multi-page tables, set `type: long` or `long: true`; Hypo-LaTeX uses
the `longtable` fallback so the table can break across pages while preserving
caption and label behavior. Current controlled tables do not support row spans
or column spans, and `.table` content must be exactly one Markdown table after
the optional YAML block.

## Public And Private Validation

C3 separates public validation from private corpus validation.

Public validation is committed and reproducible. It covers docs contracts, public fixtures, and buildable templates:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/test_skill_docs.py -q
uv run hypolatex build skill/templates/project.md --theme tech-minimal --output build/c3-skill-project.pdf
uv run hypolatex build skill/templates/review.md --answer-mode review --output build/c3-skill-review.pdf
```

The private corpus workflow uses real local documents. Keep real samples under `tests/private/corpus` or set `HYPOLATEX_TEST_CORPUS` to another local corpus root. Use the committed manifest and `scripts/prepare_private_corpus.py` to list, check, and prepare smoke samples, then run private smoke pytest selections with outputs in pytest `tmp_path` or ignored `tests/private/results` paths.

Real artifacts and results are local only. Do not commit real source files, private PDFs, generated private TeX, logs, JSON summaries, screenshots, or extracted text. Public reports may record that private corpus smoke validation passed or failed, but they must not include private corpus content.

## Beamer Note

C3 semantic blocks also work on Beamer slides. For `document_type: beamer`
(`slides`/`presentation` aliases), H1 maps to section, H2 maps to subsection,
H3 maps to frame title, and `---` is a frame separator/new frame. The same
semantic blocks are supported on slides: `objective`, `info`, `task`,
`requirement`, `deliverable`, `checklist`, `rubric`, `question`, `hint`,
`answer`, and `solution`. `strict_structure` makes H2 without H1 invalid;
`frame_title_inheritance_limit` default is `3`; `continued_title_style` values
are `subtle`, `suffix`, and `none`; `section_dividers` and
`subsection_dividers` control divider frames. Density/overfull lint is a
limited heuristic, not a layout guarantee. Slide local asset references must be
relative local files or a local `resource-root`/`resource_root`; remote files
are not fetched.
