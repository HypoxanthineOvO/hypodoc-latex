---
title: Building Reliable AI Tutorials
subtitle: A Hypo-LaTeX Longform Fixture
author: Ada Chen
organization: Hypo Research Lab
course: AI Writing Systems
date: 2026-06-28
version: v0.2-red
logo: assets/hypo-logo.pdf
icon: book-open
abstract: This fixture covers every initial frontmatter slot and a small longform body.
theme: plain
---

# Orientation

Hypo-LaTeX keeps authoring in Markdown while preserving a reviewable LaTeX surface.

:::note
Keep the source document short enough for AI editing and explicit enough for deterministic conversion.
:::

## Conversion Contract

Every supported frontmatter field maps to a stable metadata macro before the document body.

:::summary
The generated TeX should be deterministic, semantic, and free of timestamps.
:::

### Review Loop

Snapshot diffs should make schema drift visible before PDF styling work begins.
