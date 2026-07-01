---
title: Hypo-LaTeX Longform Demo
subtitle: Markdown Source To Reviewable TeX And PDF
author: Example Author
organization: Hypo Research Lab
course: Reliable Document Workflows
date: 2026-06-28
version: v0.1
logo: assets/hypo-logo.pdf
icon: book-open
abstract: This demo shows the minimum longform structure for Hypo-LaTeX authoring, conversion, and PDF build review.
theme: classic-readable
---

# Orientation

Hypo-LaTeX keeps the source document in Markdown while producing a stable TeX surface for review.

:::note
Start with a short source file and confirm that the metadata, callouts, figures, and references convert as expected.
:::

## Authoring Flow

Draft the document in Markdown, review the generated TeX, then build the PDF when the structure is ready.

:::tip
Keep each section focused on one idea so later edits stay easy to review.
:::

## Figure Placeholder

The figure directive can point at an asset that is not present yet. The current MVP renders a fallback box so the PDF still builds.

::: {.figure label="fig:workflow-overview" src="assets/workflow-overview.png" caption="Hypo-LaTeX authoring and build overview" width="0.92" placement="H"}
:::

The previous placeholder is referenced below.

::: {.ref target="fig:workflow-overview"}
:::

:::warning
Check dependency diagnostics before assuming that a build failure is caused by document content.
:::

## Review Checklist

Use the generated TeX to inspect metadata, headings, callouts, figure labels, and references before sharing the PDF.

:::summary
A longform Hypo-LaTeX document starts with complete frontmatter, uses supported directives, and keeps conversion errors easy to diagnose.
:::
