---
title: Function Matrix
subtitle: Public Beamer Slides DSL Template
author: Hypo-LaTeX
theme: plain
document_type: beamer
palette: red
aspectratio: "169"
footline: full
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
Connect a function's domain, codomain, kernel, image, and rank to the matrix
used to represent a linear map.
:::

- A function matrix records how input coordinates determine output coordinates.
- The public template is synthetic and contains no private course or corpus text.

---

- Separator-driven frames inherit the previous H3 frame title while the
  inheritance limit allows it.
- Use this pattern only when a topic needs one short continuation frame.

### Domain And Codomain

::: {.info title="Notation"}
For a linear map $T: V \to W$, the domain is $V$ and the codomain is $W$.
:::

- Matrix columns correspond to basis vectors from the domain.
- Matrix rows correspond to output coordinates in the codomain.

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
| Kernel | Solutions of $Ax=0$ | Detect null vectors |
| Image | Span of columns of $A$ | Count pivot columns |
| Rank | Dimension of image | Compare with target dimension |

:::

### Local Asset Rule

::: {.requirement title="Asset Discipline"}
Slide decks may reference local assets with relative paths, but public templates
must not fetch remote or private files during builds.
:::

- Keep public examples self-contained unless a local fixture asset is committed.
- Use `resource-root` only for local project assets that belong with the deck.
- Image dimensions preserve aspect ratio by default; add `stretch=true` only
  when an image should deliberately fill both width and height.
- Standalone caption-less image lines are centered automatically with a
  `0.75\textheight` height cap; place side-by-side figures on one line and
  give each a `width=NN%` that sums below 100%.
