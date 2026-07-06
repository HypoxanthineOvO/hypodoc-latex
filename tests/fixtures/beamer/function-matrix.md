---
title: Function Matrix Beamer Fixture
subtitle: Public slides DSL regression deck
author: Hypo-LaTeX
theme: plain
document_type: beamer
section_dividers: true
subsection_dividers: false
frame_title_inheritance_limit: 3
continued_title_style: subtle
strict_structure: true
---

# Function Matrix

## Mapping Contract

### Function Matrix Overview

::: {.objective title="Slide Goal"}
Connect a function's domain, codomain, rule, kernel, image, and rank to the
matrix representation used for linear maps.
:::

- A function matrix records how input coordinates determine output coordinates.
- The public fixture is synthetic and contains no private course or corpus text.

---

- Separator-driven continuation should inherit the previous frame title.
- The continuation title must make the repeated topic visible in the PDF.

### Domain And Codomain

::: {.info title="Notation"}
For a linear map $T: V \to W$, the domain is $V$ and the codomain is $W$.
:::

> A function assigns to every element of the domain exactly one element of the
> codomain.

- The matrix columns describe how basis vectors from the domain move.
- The row count is controlled by the chosen basis for the codomain.

## Matrix Evidence

### Kernel, Image, Rank

::: {.task title="Reader Check"}
Use the matrix to locate the kernel, image, and rank before drawing conclusions
about injectivity or surjectivity.
:::

- Kernel: all input vectors mapped to zero.
- Image: all reachable output vectors.
- Rank: the dimension of the image.

### Function Matrix Table

::: {.table}
```yaml
type: comparison
density: compact
caption: Function matrix evidence
label: tab:function-matrix-evidence
columns:
  - align: left
    width: 0.24
  - align: left
    width: 0.34
  - align: left
    width: 0.28
```

| Object | Matrix evidence | Slide check |
|---|---|---|
| Domain | Number of input coordinates | Match column count |
| Codomain | Number of output coordinates | Match row count |
| Kernel | Solutions of $Ax=0$ | Detect nonzero null vectors |
| Image | Span of columns of $A$ | Count pivot columns |
| Rank | Dimension of image | Compare with target dimension |

:::

### Local Asset Rule

::: {.requirement title="Asset Discipline"}
Slide decks may reference local assets with relative paths, but public fixtures
must not fetch remote or private files during tests.
:::

- Keep public examples self-contained unless a local fixture asset is committed.
- Use `resource-root` only for local project assets that belong with the deck.
