# Hypo-LaTeX Semantic Module Design

This note records the C3 revision contract for teaching, project, review, and reusable document modules.

## Current Model

Semantic modules use two independent layers:

1. `HypoBox` primitives and presets wrap `tcolorbox` capabilities.
2. Author-facing Markdown directives map to those presets.

Question/answer material is intentionally separate from ordinary document boxes. A question can be a text-flow prompt, a light outline prompt, a card-style review item, or part of a larger `qa` group container.

## HypoBox Primitive Layer

The LaTeX layer exposes `\HypoBox{family}{icon}{title}{options}{content}` as the common primitive. It owns:

- themed color family lookup, such as `HypoSemantic*`, `HypoQuestion*`, and `HypoRubric*`
- title band rendering
- left rail / frame density
- optional title icon in a fixed-width slot, so Chinese and English titles start
  from the same text column across icon shapes
- list-friendly padding and breakable behavior

Current presets:

| Preset | Purpose |
|---|---|
| `hypobox/subtle` | ordinary teaching/project modules |
| `hypobox/card` | strong card blocks, mainly explicit review questions |
| `hypobox/answer` | answer-bearing blocks controlled by `answer_mode` |
| `hypobox/rubric` | evaluation, grading, or acceptance criteria |
| `hypobox/question-plain` | light outline question prompt |
| `hypobox/qa` | grouped Q-A container that can hold question, hint, answer, and solution together |

Semantic roles should not hard-code their own visual structures. They should choose a preset and theme token family.

The default question style is `outline`: it is intentionally not a strong review
card, but it still has a light outer frame and title area. Use `style="plain"`
for a true text-flow question without an outer box. `style="text"` and
`style="inline"` are accepted aliases for `plain`; new authoring guidance should
prefer the canonical `plain` spelling.

## List Behavior

Semantic boxes must remain friendly to Markdown lists. The core package loads
`enumitem`, keeps list spacing compact, and extends `itemize`/`enumerate` to
five levels.

Unordered list labels are fixed as:

| Level | Label |
|---|---|
| 1 | solid bullet |
| 2 | hollow circle |
| 3 | solid square |
| 4 | hollow square |
| 5 | triangle |

Ordered lists use conservative nested numbering and smaller indentation than
the default LaTeX list layout.

## Ordinary Semantic Roles

| Directive | Preset | Default title |
|---|---|---|
| `objective` | `hypobox/subtle` | `Objective` |
| `info` | `hypobox/subtle` | `Info` |
| `task` | `hypobox/subtle` | `Task` |
| `requirement` | `hypobox/subtle` with requirement colors | `Requirement` |
| `deliverable` | `hypobox/subtle` | `Deliverable` |
| `checklist` | `hypobox/subtle` | `Checklist` |
| `rubric` | `hypobox/rubric` | `Rubric` |

All ordinary semantic roles support an optional `title` attribute.

```markdown
::: {.task title="实施任务"}
Build the PDF and record validation commands.
:::
```

## Q-A Roles

| Directive | Default structure | Notes |
|---|---|---|
| `question` | light outline prompt | numbered by default; use `style="plain"` for text flow and `style="card"` for strong review cards |
| `hint` | ordinary semantic box | visible in all answer modes; use `style="plain"` for non-card follow-up formatting |
| `answer` | answer box | hidden in `student`, visible in `review` and `teacher`; use `style="plain"` to match a text-flow question |
| `solution` | answer box | hidden in `student`, visible in `review` and `teacher`; use `style="plain"` to match a text-flow question |
| `qa` | grouped outer card | can contain question, hint, answer, and solution together |

Question attributes:

```markdown
::: {.question label="q:privacy" title="题目 1" style="card"}
Which evidence must remain local?
:::

::: {.question numbered="false" title="开放讨论"}
What should be improved before acceptance?
:::

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

Grouped Q-A example:

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

Inside `qa`, nested question/hint/answer/solution blocks render as section
headers plus thin rules inside one outer card. Their icons use the same fixed
slot as ordinary boxes, and section body text is aligned to the title text
column.

## Theme Tokens

Themes own colors and title fonts. Semantic roles should not encode visual decisions in Markdown.

Core token families:

- `HypoSemantic*`
- `HypoRequirement*`
- `HypoQuestion*`
- `HypoHint*`
- `HypoAnswer*`
- `HypoSolution*`
- `HypoRubric*`

Each family provides `Back`, `Frame`, `TitleBack`, and `TitleText` colors.

Current font decision:

- Body: `Noto Serif CJK SC`
- Display title: `Noto Serif CJK SC Black`
- Module / Q-A title: `Noto Serif CJK SC Bold`
- Mono/code: `LXGW WenKai Mono`
