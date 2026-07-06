# Beamer Slides DSL

Hypo-LaTeX treats Beamer as a first-class document type for the current Slides DSL. It does not provide an automatic Marp-to-LaTeX or arbitrary LaTeX-deck converter; authors write the supported Markdown structure directly.

## Frontmatter

Use `document_type: beamer`. The aliases `slides` and `presentation` resolve to the same Beamer branch.

```yaml
---
title: Function Matrix
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
```

Slides options:

- `palette`: deck color system, one of `red`, `blue`, `yellow`, `gray`, or `mono`; default `red`.
- `aspectratio`: Beamer slide geometry, one of `43`, `54`, `149`, `1610`, `169`, or `32`; default `169`.
- `footline`: footer style, one of `full`, `page`, or `none`; default `full`.
- `logo`: optional local image path shown on the title page.
- `section_dividers`: whether H1 sections create divider slides; default `true`.
- `subsection_dividers`: whether H2 subsections create divider slides; default `false`.
- `frame_title_inheritance_limit`: how many separator-created frames may inherit the previous H3 frame title; default `3`.
- `continued_title_style`: continuation title behavior, one of `subtle`, `suffix`, or `none`.
- `strict_structure`: reject unsafe heading order; default `true`.

## Heading Contract

- H1 (`#`) is a Beamer section.
- H2 (`##`) is a Beamer subsection.
- H3 (`###`) is a frame title.
- `---` is a frame separator that starts a new frame. When allowed by `frame_title_inheritance_limit`, it can inherit the previous H3 frame title and apply `continued_title_style`.
- With `strict_structure: true`, H2 without a preceding H1 is invalid.

## Content Contract

The existing semantic blocks are supported on slides and frames: `objective`, `info`, `task`, `requirement`, `deliverable`, `checklist`, `rubric`, `question`, `hint`, `answer`, and `solution`.

Controlled `.table` blocks are supported for slide tables, but dense tables still need author judgment. Density and overfull lint checks are heuristics for likely crowded frames; they are limited lint signals, not a layout guarantee.

Slide assets must be local assets. Use relative paths or a local `resource-root`/`resource_root`; remote URLs are not fetched, and public examples must not depend on private or remote files.

Image sizing defaults to an aspect-ratio-preserving fit box. Width/height Markdown image attributes are allowed, but Beamer keeps the original image proportions by default.

A standalone image line (one or more caption-less images, nothing else on the line) is horizontally centered and rewritten to a fit box: the given `width` percent maps to `\linewidth`, and the image height is capped at `0.75\textheight` with `keepaspectratio` so tall figures cannot overflow the frame. Several images on the same line become one centered row and share the same per-image fit-box rules:

```markdown
![](assets/left.png){width=62%} ![](assets/right.png){width=30%}
```

A lone image with a non-empty caption stays in Markdown, so pandoc renders it as a centered figure with the caption; indented images (for example inside a list item) and images mixed with text on the same line are left untouched.

To intentionally stretch an image to both dimensions, opt in with `stretch=true`, for example:

```markdown
![Result](assets/result.png){width=50% height=40% stretch=true}
```

`stretch=true` disables the aspect-ratio guarantee for that image; the stretched image is still centered.
