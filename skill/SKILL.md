---
name: hypolatex
description: Use this skill for Hypo-LaTeX authoring, conversion, build, compile, and PDF evidence workflows with `hypolatex` when the user wants to write Markdown, convert to TeX, or produce/check PDFs.
---

# Hypo-LaTeX Theme-first Workflow

Use Hypo-LaTeX for longform Markdown documents that need a reviewable TeX file or a compiled PDF.

## Workflow

1. Choose a theme preset first. For ordinary AI authoring, set only `theme:` in frontmatter or use `--theme` on build commands; do not invent font, paper, accent, cover, or resource-root fields by default.
2. Run `hypolatex doctor` before conversion or build work. Treat it as the environment and dependency check for Pandoc, latexmk, XeLaTeX, and required TeX packages.
3. If `hypolatex doctor` reports missing dependencies, stop and ask the user to install the missing items. Do not pretend dependencies are installed.
4. Copy, create, or edit a Markdown template before building. Use `skill/templates/longform.md` as the longform starting point, or make a similar `.md` template with minimal frontmatter and supported fenced directives.
5. Generate reviewable TeX with:

```bash
hypolatex convert INPUT.md --output OUTPUT.tex
```

6. Compile the PDF with:

```bash
hypolatex build INPUT.md --theme THEME_ID --output OUTPUT.pdf
```
7. After a successful build, collect PDF evidence with Poppler tools or the project's PDF evidence helpers. At minimum, check page size/page count and text extraction markers; render a page screenshot when visual layout matters.
8. Use bare `hypolatex` or `hypolatex --help` only when you need command help.

## Theme Matrix

- `plain`: use for baseline compatibility, debugging, or minimal documents.
- `classic-readable`: use as the default for readable longform books, tutorials, and general PDF output. It uses Noto Serif CJK SC for body text, Noto Serif CJK SC Black for major titles, and Noto Serif CJK SC Bold for module/Q-A titles when available.
- `tech-minimal`: use for technical guides, model reviews, rankings, tables, and modern engineering-style documents when the user wants restrained paper-like typography. It keeps Noto Serif CJK SC as the body font and uses Sarasa Gothic SC only as an explicit sans fallback/accent font.
- `warm-handbook`: use for approachable handbooks, course notes, explanation-heavy writing, and learning material. It keeps Noto Serif CJK SC for body text and uses warmer colors/spacing; LXGW is reserved for mono/code when available.
- `academic-clean`: use for academic notes, research-style reports, and formal study material. It keeps a restrained Noto Serif CJK SC style.

## Minimal Frontmatter

Use a theme-first default like this:

```yaml
---
title: Example Longform Document
author: Example Author
theme: classic-readable
---
```

Do not add advanced style fields to ordinary AI-authored drafts unless the user asks for them or the source project already requires them.

## Optional Advanced Overrides

Use these only when the user explicitly asks for them or the project already has fixed constraints:

- Fonts: `font`, `fonts`, `mainfont`, `sansfont`, `monofont`, `cjkfont`.
- Paper: `paper`, `paper_size`.
- Accent color: `accent`, `accent_color`.
- Cover layout: `cover_layout`, `cover_image`.
- Asset/resource root: `resource-root`, `resource_root`.

Prefer theme presets for normal work. Advanced overrides should tune a selected theme, not replace the theme-first choice.

See `docs/fonts.md` for the current Chinese font role mapping. Do not add `mainfont`, `sansfont`, `monofont`, or `cjkfont` to ordinary AI-authored Markdown just because preferred fonts are installed; themes already choose Noto Serif CJK SC, Sarasa Gothic SC accents, and LXGW WenKai Mono where appropriate.

## Heading Numbering Discipline

Do not write manual numbers in ordinary headings. Let LaTeX generate heading
numbers by default:

```markdown
# 项目定位
## 构建流程
```

If the user explicitly wants to preserve a hand-written heading number, mark the
heading with `.manual-number`:

```markdown
# 1. 项目定位 {.manual-number}
```

If the user wants an unnumbered heading without a manual number, mark it with
`.unnumbered`:

```markdown
# 致读者 {.unnumbered}
```

Before writing `1.`, `2.`, `A.`, or `第一章` at the start of a heading, verify
whether this is truly a manual number or just accidental numbering. Unmarked
manual-looking heading numbers are rejected by the converter so the mistake is
caught before PDF generation.

## Inline Code And Commands

Use inline code only for short tokens such as `theme`, `answer_mode`,
`hypolatex`, `docs/release/quickstart.md`, or a compact option name. Full
commands should be fenced code blocks, because styled inline code is not a
reliable line-breaking container.

Good:

```bash
hypolatex build input.md --theme warm-handbook --output build/output.pdf
```

Avoid:

```markdown
Run `hypolatex build input.md --theme warm-handbook --output build/output.pdf`.
```

## Cover Layouts

Cover layouts are structural templates; themes provide colors and tone. For ordinary drafts, omit `cover_layout`. When the user asks for a specific cover treatment, use the documented layout names in `docs/cover-layouts.md`:

- `full-bleed-card`: image cover with readable title, abstract, and author cards. Use this when a good image exists but title/background overlap is risky.
- `integrated-art`: complete cover artwork with coordinated blank text zones. Use this for final longform books when external white cards look disconnected from the image.
- `top-title-image`: clean title area with image below. Use this for longform books where title clarity is more important than immersion.
- `info-panel`: structured exam, assignment, project, or guide cover.
- `paper-ink`: quiet formal book cover without a strong image.
- `plain`: minimal baseline cover.

Do not invent new `cover_layout` values. If no layout fits, leave the field out and explain the mismatch.

## C3 Semantic Authoring

C3 adds a semantic block vocabulary for project, assignment, course, and research-group documents. Use the blocks to mark intent, not to force a rigid course schema. The same vocabulary can describe a class project, a lab onboarding task, a reading assignment, a research sprint, or an operational handoff.

Project and assignment semantic block vocabulary:

```markdown
::: {.objective title="目标"}
State the outcome the reader should be able to produce.
:::

::: {.info title="背景"}
Give context, assumptions, dates, inputs, or constraints.
:::

::: {.task title="任务"}
Describe the work unit the reader should perform.
:::

::: {.requirement title="要求"}
List mandatory constraints or acceptance rules.
:::

::: {.deliverable title="交付物"}
Name the artifact, evidence, or handoff the reader must provide.
:::

::: {.checklist title="检查清单"}
- Convert the source.
- Build the PDF.
- Record validation evidence.
:::

::: {.rubric title="验收标准"}
- The result is reviewable from source and PDF.
- Private material stays outside committed artifacts.
:::
```

Use `objective` for the goal, `info` for background, `task` for actions, `requirement` for non-negotiable constraints, `deliverable` for outputs, `checklist` for completion checks, and `rubric` for grading, review criteria, or non-course acceptance standards. Keep prose domain-specific; C3 blocks provide structure without replacing the author's voice.

All semantic blocks support `title="..."`. Prefer explicit Chinese titles in Chinese documents, for example `title="目标"` or `title="验收标准"`. Hypo-LaTeX renders these modules through reusable `HypoBox` presets with borders, title bands, and role-specific visual tokens; do not simulate module styling with Markdown tables or manual separators.

## C3 Review Questions And Answer Modes

The review question vocabulary is `question`, `hint`, `answer`, and `solution`.

```markdown
::: {.question label="q:handoff-risk" title="题目 1" style="card"}
Which validation evidence should be kept public, and which evidence should remain local?
:::

:::hint
Separate synthetic/public checks from real-corpus checks.
:::

:::answer
Public checks can be committed; real-corpus artifacts and results stay local.
:::

:::solution
Use public fixtures for regression tests, then run a private corpus smoke pass with local files under ignored paths.
:::
```

Questions are numbered by default. Use canonical styles rather than inventing
visual names:

- `style="outline"`: default light framed prompt.
- `style="card"`: strong review-card question.
- `style="plain"`: true text-first non-card question/follow-up with colored
  labels and no surrounding box.

The converter also accepts `style="text"` and `style="inline"` as aliases for
`plain`, but AI-authored Markdown should prefer the canonical `plain` spelling.
Use `numbered="false"` only for an unnumbered discussion prompt:

```markdown
::: {.question numbered="false" title="开放讨论"}
Which module style should be revised before acceptance?
:::
```

Text-first non-card review item:

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

Use `qa` when a review item should keep the prompt, hint, answer, and solution inside one outer card:

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

`answer_mode` controls whether answer-bearing material is visible. Supported modes are `student`, `review`, and `teacher`.

Precedence:

1. CLI `--answer-mode` overrides the Markdown frontmatter `answer_mode`.
2. Frontmatter `answer_mode` is used when no CLI override is supplied.
3. The default is `student`.

Behavior:

- `student` hides `answer` and `solution` content while keeping questions and hints visible.
- `review` shows answer and solution content for review builds.
- `teacher` also includes answer and solution content for instructor or maintainer builds.

Examples:

```yaml
---
title: Review Packet
answer_mode: student
---
```

```bash
hypolatex build skill/templates/review.md --answer-mode review --output build/review.pdf
```

## C3 Controlled Table DSL

Use the controlled `.table` DSL when table layout matters. Ordinary Markdown
tables outside `.table` remain ordinary Pandoc tables; do not wrap every table
by default. A controlled table is a fenced div that contains optional YAML
configuration followed by exactly one Markdown table. The YAML `columns` list
lets authors set per-column `align`, `width`, and `weight` without writing raw
LaTeX column specifications.

````markdown
::: {.table}
```yaml
type: checklist
density: compact
caption: Project checkpoint map
label: tab:checkpoint-map
columns:
  - align: left
    width: 0.22
  - align: left
    width: 0.42
  - align: left
    width: 0.28
```

| Checkpoint | Evidence | Owner |
|---|---|---|
| Scope | Approved objective and requirements | Lead author |
| Build | PDF generated from Markdown | Implement worker |
| Review | Notes recorded without private data | Reviewer |

:::
````

Table configuration supports `type`, `long`, `density`, `width`, `caption`,
`label`, `header`, `striped`, and YAML `columns`.

Use these table `type` values:

- `default`: general controlled table.
- `comparison`: option/model/capability comparison.
- `checklist`: status, evidence, or handoff checks.
- `rubric`: grading, review, acceptance, or evaluation criteria.
- `cheatsheet`: dense quick-reference table.
- `compact`: generic dense table when no more specific pattern fits.
- `long`: multi-page table.

Use `density: compact`, `density: normal`, or `density: comfortable`. `width:
0.9` means `0.9\linewidth`; per-column widths also accept fractions such as
`0.25` or percentages such as `25%`. Labels must be simple TeX-safe identifiers
without spaces.

Use `type: long` or `long: true` for long or multi-page tables. Hypo-LaTeX then
uses the `longtable` fallback instead of a short floating `tblr` table, keeping
captions and labels while allowing the table to break across pages. Current
controlled tables do not support row spans or column spans, and `.table` content
must be exactly one Markdown table after the optional YAML block.

## C3 Public And Private Validation

C3 validation has a public/private split.

Public validation uses committed templates, public fixtures, and docs tests. It is safe to run in CI and safe to quote in reports:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/test_skill_docs.py -q
uv run hypolatex build skill/templates/project.md --theme tech-minimal --output build/c3-skill-project.pdf
uv run hypolatex build skill/templates/review.md --answer-mode review --output build/c3-skill-review.pdf
```

The private corpus workflow is for real course, project, or research documents. Keep real source files under ignored local paths such as `tests/private/corpus`, or point `HYPOLATEX_TEST_CORPUS` at another local directory. Prepare samples from a manifest with `scripts/prepare_private_corpus.py`, run a small private smoke pytest selection, and write outputs under ignored result locations or pytest `tmp_path`. Do not read, print, commit, or paste private corpus contents into public artifacts.

Real artifacts and results are local only: do not commit real source excerpts, generated private PDFs, private TeX, logs, JSON summaries, screenshots, or copied text. Public reports may say that the private smoke passed or failed, but they should not include private corpus content.

For a docs-side version of this contract, see `docs/c3-authoring.md`.

## PDF Evidence

After `hypolatex build`, verify the produced PDF rather than assuming success from the exit code alone.

```bash
pdfinfo OUTPUT.pdf
pdftotext OUTPUT.pdf -
pdftoppm -png -f 1 -singlefile OUTPUT.pdf /tmp/hypolatex-page-1
```

Use `pdfinfo` to confirm page count and page size. Use `pdftotext` to confirm expected title, section, and Chinese text markers. Use `pdftoppm` or Hypo-LaTeX PDF evidence helpers when a rendered page screenshot is needed.

## Figures

For AI-authored longform books, prefer fixed figure placement and explicit width:

```markdown
::: {.figure label="fig:example" src="assets/example.png" caption="Example figure" width="0.92" placement="H"}
:::
```

- `width` is a fraction of `\linewidth`; `width="0.92"` becomes `0.92\linewidth`.
- `placement="H"` pins the figure where it appears in the Markdown source.
- Omit `placement` only when LaTeX should naturally float the image near the source location.
- Keep project assets under `assets/` at the project root. `hypolatex build` resolves resources from the Markdown file directory and its parent project directory.

## Error Handling

When convert or build fails, read the exit code, stderr, and diagnostics before advising the user. Explain the error and give one actionable fix.

- Pandoc errors usually mean Pandoc is missing, Markdown syntax is invalid, or an unsupported fenced directive was used.
- latexmk errors usually mean XeLaTeX failed, a TeX package is missing, or generated LaTeX needs review.
- Dependency diagnostics from `hypolatex doctor` are authoritative for missing tools and packages.
- If `hypolatex convert` fails, inspect the Pandoc stderr and fix the Markdown template or dependency issue.
- If `hypolatex build` fails, inspect the latexmk diagnostics and any document log summary, then fix the input or ask the user to install the missing dependency.

## MVP Limits

- XeLaTeX is the first and default PDF engine path in the MVP.
- Pandoc is required and must be installed.
- Beamer is not supported and is out of scope for this MVP.
- Textual and TUI interfaces are not supported and are deferred outside the MVP.
