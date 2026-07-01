---
title: C3 Review Question Template
subtitle: Answer Visibility For Student, Review, And Teacher Builds
author: Example Author
organization: Hypo Research Lab
course: Review Packet Studio
date: 2026-06-29
theme: warm-handbook
answer_mode: student
cover_layout: info-panel
---

# Review Setup

This template demonstrates the C3 review question vocabulary: `question`, `hint`, `answer`, and `solution`.

`answer_mode` controls answer visibility. In `student`, Hypo-LaTeX hides answer and solution content. In `review` and `teacher`, Hypo-LaTeX shows/includes answer and solution content. The CLI `--answer-mode review` overrides the frontmatter default, so this file can be built as a reviewer copy with `hypolatex build skill/templates/review.md --answer-mode review --output build/c3-skill-review.pdf`.

## Review Item

::: {.question label="q:c3-validation" title="题目 1" style="card"}
How should a C3 author separate public validation from private corpus validation in a handoff note?
:::

::: {.hint title="提示"}
Identify which evidence can be committed and which evidence must remain local.
:::

::: {.answer title="参考答案"}
Public validation uses committed tests, fixtures, docs, and templates. Private corpus validation uses real local material and reports only sanitized pass/fail results.
:::

::: {.solution title="解析"}
A good handoff names the public commands that anyone can rerun, then separately records that a private smoke pass was run against `HYPOLATEX_TEST_CORPUS` or `tests/private/corpus`. The real inputs, generated PDFs, TeX, logs, JSON summaries, screenshots, and extracted text stay in ignored local paths and are not committed.
:::

::: {.question numbered="false" title="开放讨论"}
Which semantic module should be redesigned before accepting the document?
:::

:::summary
Use `student` for learner-facing copies, `review` for reviewer builds that need answers, and `teacher` for instructor or maintainer copies that include the same answer-bearing material.
:::
