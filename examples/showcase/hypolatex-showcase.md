---
title: Hypo-LaTeX Showcase
subtitle: 真实 PDF 渲染展示
author: Hypo-LaTeX Team
date: 2026-07-01
theme: classic-readable
abstract: 展示封面、主题视觉、长文、语义块、Q-A、受控表格、图片和 theme contact sheet。
---

# 封面与 Theme Visual System

Hypo-LaTeX 把 HypoDoc Markdown 渲染为可审阅的 PDF。这个 showcase
是 README banner 的来源：它不是手工绘制的 mock image，而是由
`hypolatex build` 构建 PDF 后再 screenshot 截图得到。

本页覆盖 cover、封面、theme、主题视觉和 visual system。当前源文件选择
`classic-readable`，用于展示长文阅读时的标题层级、正文灰度、语义块和表格节奏。

\special{pdf:literal direct /Span << /ActualText (hypo-latex classic-readable) >> BDC}PDF text evidence marker\special{pdf:literal direct EMC}

:::note
Semantic callout：主题应负责视觉风格，作者只需要在 frontmatter 中选择
公开注册的 `theme`。
:::

## Longform Narrative 长文教程片段

Longform prose 长文应该像教程一样可以连续阅读。作者先写出稳定的结构：
主题选择、章节标题、解释段落、任务块、复习题、受控表格和图片引用。渲染器再把这些
Markdown 结构交给 LaTeX 后端处理，使 PDF 保留清晰的目录、段落间距和中文字体配置。

这一段故意保持多句 narrative，以检查长文页面在真实 PDF 中不会只出现标题或短列表。
它还说明 README banner 的目的：给第一次进入仓库的读者一个快速、可信的视觉证据，
说明 Hypo-LaTeX 已经能从公开 Markdown 自托管生成展示 PDF。

::: {.task title="实现任务：Self-hosted showcase"}
构建 `examples/showcase/hypolatex-showcase.md`，输出
`build/showcase/hypolatex-showcase.pdf`，再用 `pdftoppm` 和 ImageMagick
生成 `assets/readme/showcase-banner.png`。
:::

::: {.requirement title="语义块：公开渲染契约"}
语义块 semantic blocks 应表达文档意图，而不是让作者直接维护复杂 LaTeX。
这里的 task、assignment、note 和 question 会被转换为主题可控制的 PDF 结构。
:::

# Q-A Review Questions 问答

::: {.question label="q:theme-first" title="Question: 为什么优先选择 theme？" style="card"}
解释为什么 HypoDoc Markdown 的普通作者只需要声明 `theme`，而不是手写版式命令。
:::

::: {.answer title="Answer: 参考答案" style="card"}
因为主题封装了封面、字体、颜色、标题、表格和语义块视觉；Markdown 源文件只表达内容和结构。
:::

::: {.question label="q:banner" title="Question: README banner 的证据链是什么？" style="plain"}
说明 banner 为什么应来自真实 PDF render / screenshot。
:::

::: {.answer title="Answer: 参考答案" style="plain"}
真实截图可以同时验证 CLI 构建、PDF 页面、主题视觉、图片、表格和文本抽取，而不是只验证一张静态设计图。
:::

# Controlled Tables 受控表格

下面的 controlled table 使用 `.table` 语义块和 YAML `columns:` 配置。它展示
table、受控表格、密度、列宽和 caption 的公开写法。

::: {.table}
```yaml
type: comparison
density: normal
width: 0.92
caption: Showcase controlled table
label: tab:showcase-controlled
header: true
striped: true
columns:
  - align: left
    width: 0.24
    weight: 2
  - align: left
    width: 0.36
    weight: 3
  - align: center
    width: 0.18
    weight: 1
```

| Feature | Evidence in this showcase | Status |
| --- | --- | --- |
| Cover and theme visual | Frontmatter plus first page prose | shown |
| Semantic blocks | task, assignment, note, question, answer | shown |
| Figure image | figure directive with caption and reference | shown |
| Controlled table | YAML columns and Markdown rows | shown |
:::

# Figures Images 图片

Figure / image support should keep captions and labels even when a public
example image is represented by the renderer's placeholder path.

::: {.figure label="fig:showcase-flow" src="assets/showcase-flow.png" caption="Showcase PDF render and README banner screenshot flow" width="0.86" placement="H"}
:::

The banner script renders pages from this PDF:

::: {.ref target="fig:showcase-flow"}
:::

# Theme Contact Sheet 主题总览

The theme contact sheet / theme matrix lists all public theme IDs that are
available for AI authors and human maintainers:

| Theme ID | 用途 | Visual cue |
| --- | --- | --- |
| `plain` | 基础兼容和调试 | minimal baseline |
| `classic-readable` | 长文、教程、书籍 | readable classic |
| `tech-minimal` | 技术指南和表格密集资料 | compact technical |
| `warm-handbook` | 手册、课程笔记、解释型材料 | warm handbook |
| `academic-clean` | 正式笔记和研究风格报告 | academic clean |

这张 contact sheet 让 README banner 在一张图中同时展示主题矩阵、正文、语义块、
question / answer、table 和 figure 证据。
