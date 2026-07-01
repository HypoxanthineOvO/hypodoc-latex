# Hypo-LaTeX Figures

Hypo-LaTeX figure directives are designed for AI-maintained Markdown sources that need predictable PDF output.

## Recommended Longform Form

```markdown
::: {.figure label="fig:workflow" src="assets/workflow.png" caption="Workflow overview" width="0.92" placement="H"}
:::
```

- `label`: optional LaTeX label target.
- `src`: local image path, normally rooted at the project-level `assets/` directory.
- `caption`: visible caption.
- `width`: optional figure width. A plain number such as `0.92` becomes `0.92\linewidth`.
- `placement`: optional LaTeX placement. Use `H` to pin the image where it appears in Markdown.

## Placement Policy

- `placement="H"`: fixed position. Best for AI-authored books, tutorials, and source-order-sensitive explanations.
- omitted `placement`: defaults to `htbp`, allowing LaTeX to float the image near the source location.
- `placement="float"`: explicit alias for default `htbp`.

Use fixed placement for ordinary tutorial figures. Use floating placement only when page breaks matter more than strict source order.

## Width Policy

Use simple numeric widths in Markdown:

```markdown
width="0.92"
```

This is safer for AI authors than writing raw TeX dimensions. The Lua filter also accepts safe TeX dimensions such as `0.9\linewidth`, `0.8\textwidth`, `12cm`, or `320pt`.

## Resource Roots

During `hypolatex build`, local resources are copied into the temporary LaTeX build directory. Relative paths are resolved from:

1. Explicit resource roots supplied by the build pipeline.
2. The Markdown file directory.
3. The Markdown file directory's parent.

The input Markdown path is resolved to an absolute path before these roots are computed. This means both of these invocations can resolve `assets/...` when the Markdown file lives in `article/` and assets live in the project root:

```bash
hypolatex build article/book-hypolatex.md --output out.pdf
cd article && hypolatex build book-hypolatex.md --output ../out.pdf
```

## Compatibility

The legacy LaTeX macro remains available:

```tex
\HypoFigure{label}{src}{caption}
```

It now delegates to:

```tex
\HypoFigureEx{label}{src}{caption}{0.86\linewidth}{htbp}
```
