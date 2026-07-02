---
title: Cheatsheet Grid Contract
author: C5 M2 Test Worker
theme: plain
document_type: article
layout: cheatsheet
---

# Cheatsheet Grid Contract

:::: {.cheatsheet-grid columns="3" gap="compact"}
::: {.cheatsheet-cell type="formula" title="Derivative Rules" priority="high" span="2" keep="true"}
Remember:

- Power rule: $x^n \to n x^{n-1}$
- Chain rule keeps the **inner derivative**.

$$
\frac{d}{dx}\sin x = \cos x
$$

Use `sympy.diff()` for quick checks.
:::

::: {.cheatsheet-cell type="workflow" title="Build Loop" priority="medium" span="1" keep="false"}
Run the focused command:

1. Edit the Markdown.
2. Run `hypolatex build`.
3. Inspect the generated PDF.
:::
::::
