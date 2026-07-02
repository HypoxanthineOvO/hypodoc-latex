---
title: Printable Cheatsheet
subtitle: C5 M3 compact layout evidence
author: Hypo-LaTeX public fixture
theme: tech-minimal
document_type: article
layout: cheatsheet
---

# Printable Cheatsheet

:::: {.cheatsheet-grid columns="3" gap="compact"}
::: {.cheatsheet-cell type="formula" title="Derivative Rules" priority="high" span="1" keep="true"}
Use the quick rules before expanding an expression:

- Power rule: $d(x^n)/dx = nx^{n-1}$.
- Chain rule: $d(f(g(x)))/dx = f'(g(x))g'(x)$.
- Product rule: $d(uv)/dx = u'v + uv'$.

$$
\frac{d}{dx}\sin(x^2)=2x\cos(x^2)
$$
:::

::: {.cheatsheet-cell type="workflow" title="Build Loop" priority="medium" span="1" keep="false"}
Keep the local loop short:

1. Edit Markdown.
2. Run `hypolatex build`.
3. Inspect the PDF evidence.
4. Commit only the intended files.

English marker: build path evidence.
:::

::: {.cheatsheet-cell type="concept" title="Model Checklist" priority="normal" span="1" keep="false"}
Review every generated model note for:

- Assumption stated.
- Constraint named.
- Failure mode listed.
- 中文 marker: 模型检查清单.
:::
::::

:::: {.cheatsheet-grid columns="4" gap="compact"}
::: {.cheatsheet-cell type="concept" title="Limits" priority="normal" span="1" keep="false"}
Use $\lim_{h\to 0}\frac{f(x+h)-f(x)}{h}$ when the symbolic rule is unclear.
:::

::: {.cheatsheet-cell type="formula" title="Series" priority="normal" span="1" keep="false"}
For small $x$, remember $e^x \approx 1+x+x^2/2$ and $\sin x \approx x$.
:::

::: {.cheatsheet-cell type="workflow" title="Debug" priority="medium" span="1" keep="false"}
When output shifts, compare generated `.tex`, PDF text, and screenshot evidence.
:::

::: {.cheatsheet-cell type="concept" title="Safety" priority="high" span="1" keep="true"}
Never accept raw attribute values as LaTeX keys without validation.
:::
::::

::: {.table type="cheatsheet" density="compact" width="0.92" caption="Dense Table Evidence" label="tab:dense-table-evidence" header="true" striped="true"}
| Signal | Action | Evidence |
| --- | --- | --- |
| Dense Table Evidence | Keep row rhythm tight | PDF text marker |
| Derivative Rules | Check formulas first | $\frac{d}{dx}x^3=3x^2$ |
| Model Checklist | Confirm assumptions | 中文/English marker |
| `hypolatex build` | Compile public sample | page count 2-4 |
| screenshot evidence | Render page 1 PNG | non-empty image |
| grid/cell | Preserve directive path | `cheatsheet-grid` |
:::

:::: {.cheatsheet-grid columns="3" gap="compact"}
::: {.cheatsheet-cell type="workflow" title="PDF Evidence" priority="medium" span="1" keep="false"}
Expected evidence:

- `pdfinfo` reports a bounded printable sample.
- `pdftotext` finds key markers.
- `pdftoppm` renders page 1 as PNG.
:::

::: {.cheatsheet-cell type="formula" title="Probability" priority="normal" span="1" keep="false"}
Bayes rule:

$$
P(A\mid B)=\frac{P(B\mid A)P(A)}{P(B)}
$$

Use it to update belief after evidence.
:::

::: {.cheatsheet-cell type="concept" title="Notation" priority="normal" span="1" keep="false"}
Keep notation local and visible:

- $\theta$: model parameters.
- $x$: observed input.
- $y$: target label.
:::
::::

:::: {.cheatsheet-grid columns="3" gap="compact"}
::: {.cheatsheet-cell type="concept" title="Compact Lists" priority="normal" span="1" keep="false"}
Lists should stay readable while using compact vertical spacing:

- Scan.
- Compare.
- Decide.
:::

::: {.cheatsheet-cell type="workflow" title="Review Order" priority="medium" span="1" keep="false"}
Suggested order:

1. Structure.
2. Evidence.
3. Typography.
4. Regression risk.
:::

::: {.cheatsheet-cell type="formula" title="Linear Algebra" priority="normal" span="1" keep="false"}
Matrix reminder:

$$
A^{-1}A=I
$$

Check dimensions before multiplying.
:::
::::

:::: {.cheatsheet-grid columns="4" gap="compact"}
::: {.cheatsheet-cell type="concept" title="Token Budget" priority="normal" span="1" keep="false"}
Prefer reusable snippets over repeated paragraphs when a page must print.
:::

::: {.cheatsheet-cell type="workflow" title="Fixture Rule" priority="normal" span="1" keep="false"}
A public fixture must avoid private paths and machine-specific data.
:::

::: {.cheatsheet-cell type="concept" title="Chinese Marker" priority="normal" span="1" keep="false"}
中文证据：紧凑速查表应保持可搜索文本。
:::

::: {.cheatsheet-cell type="formula" title="Integral" priority="normal" span="1" keep="false"}
$$
\int_0^1 x^2\,dx=\frac{1}{3}
$$
:::
::::
