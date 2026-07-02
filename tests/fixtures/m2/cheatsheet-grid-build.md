---
title: Cheatsheet Grid Build Smoke
author: C5 M2 Test Worker
theme: plain
document_type: article
layout: cheatsheet
---

# Cheatsheet Grid Build Smoke

:::: {.cheatsheet-grid columns="3" gap="compact"}
::: {.cheatsheet-cell type="formula" title="Derivative Rules" priority="high" span="2" keep="true"}
Remember the essentials:

- Power rule for quick differentiation.
- Chain rule for nested functions.

$$
\frac{d}{dx}x^2 = 2x
$$

Use `sympy.diff()` to verify examples.
:::

::: {.cheatsheet-cell type="workflow" title="Build Loop" priority="medium" span="1" keep="false"}
Run the public build path:

1. Write the fixture.
2. Run `hypolatex build`.
3. Check the PDF text.
:::
::::
