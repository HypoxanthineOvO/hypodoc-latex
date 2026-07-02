---
title: Hypo-LaTeX Release Handbook
author: Hypo-LaTeX Maintainers
theme: warm-handbook
answer_mode: review
document_type: article
---

# 项目定位

Hypo-LaTeX 是面向长文、课程资料、项目说明和 AI 协作写作的 PDF 构建工具。它把 HypoDoc Markdown 源文件转换成可审阅的 TeX，再通过 LaTeX 后端生成 PDF。项目目标不是替代所有 Markdown 或 LaTeX 写法，而是在中文长文、教学模块、复习题、受控表格和主题化 PDF 输出之间提供一条稳定路径。

典型使用方式是：作者维护 Markdown，Hypo-LaTeX 负责主题、语义模块和构建流程。这样同一份源文件既能被人类快速审阅，也能被 AI Skill 安全地继续维护。

# 规范来源和手册边界

`hypodoc-spec` 是 HypoDoc Markdown 草案的权威来源。本仓库中的 `spec/hypodoc` 是同步进入项目的规范草案来源。本手册是解释性和发布同步章节，用来说明 Hypo-LaTeX 当前支持的公开写作方式；它不是规范真相源。

当手册说明和 `hypodoc-spec` 或 `spec/hypodoc` 发生差异时，应以规范草案为准，并把本手册更新为同步解释，而不是在手册中另建一套规范。

# 快速开始和构建流程

先检查本机环境：

```bash
hypolatex doctor
```

然后构建 Markdown 到 PDF：

```bash
hypolatex build docs/release/quickstart.md --output build/release/hypolatex-quickstart.pdf
```

如果只想生成可审阅的 TeX，可以先运行：

```bash
hypolatex convert docs/release/quickstart.md --output build/release/hypolatex-quickstart.tex
```

发布文档推荐流程是：

1. 为源文件写 YAML frontmatter。
2. 选择已注册 `theme`。
3. 运行 `hypolatex doctor`。
4. 运行 `hypolatex build`。
5. 用 `pdftotext` 或人工检查确认标题、命令和关键章节可读。

# CLI

Hypo-LaTeX 的公开命令行以小而清晰为原则。

| 命令 | 用途 |
|---|---|
| `hypolatex doctor` | 检查 Pandoc、XeLaTeX、latexmk 和必要 LaTeX package。 |
| `hypolatex convert` | 把 HypoDoc Markdown 转成 TeX，适合审阅中间结果。 |
| `hypolatex build` | 转换并编译 PDF，是发布文档的主路径。 |

常用示例：

```bash
hypolatex build input.md --theme classic-readable --output build/output.pdf
hypolatex build review.md --answer-mode review --output build/review.pdf
```

CLI 参数会覆盖源文件中同名的构建意图。例如 `--theme` 会覆盖 frontmatter 的 `theme`，`--answer-mode review` 会覆盖 frontmatter 的 `answer_mode`。

# 主题和 theme-first 写作

Hypo-LaTeX 推荐 theme-first 写作：源文件优先声明一个已注册主题，让主题负责字体、颜色、封面和语义模块样式。

最小 frontmatter 包含 `title: Example Document`、`author: Example Author` 和 `theme: classic-readable`。

当前公开主题包括 `plain`、`classic-readable`、`tech-minimal`、`warm-handbook` 和 `academic-clean`。除非成品有明确版式约束，不建议在普通文档里手写大量字体、纸张、颜色和封面覆盖项。

# HypoDoc Markdown 子集

HypoDoc Markdown 子集面向可构建、可审阅、可同步的长文资料。推荐使用：

- YAML frontmatter 描述标题、作者、主题和答案模式。
- 普通标题、段落、列表、代码块和 Markdown 表格。
- fenced div 表达语义模块、复习题、受控表格和图片。
- 简单路径和字段名，避免把私有路径写进公开文档。

标题默认交给 LaTeX 自动编号，不要在普通标题文本里顺手写 `1.`、`2.` 或 `第一章`。如果确实要保留手写编号，必须写成 `# 1. 标题 {.manual-number}`；如果标题本身不要编号，必须写成 `# 致读者 {.unnumbered}`。未标记但疑似手写编号的标题会被转换器拒绝，这样 AI 写作中的顺手编号会在构建前暴露出来。

不建议在发布文档中直接写复杂 LaTeX 宏、不可移植字体路径或依赖本机私有素材的图片引用。需要表达复杂版式时，优先查 `hypodoc-spec` 和 `spec/hypodoc`，再同步到 Hypo-LaTeX 已支持的子集。

# 语义模块

语义模块用来说明一段内容的目的，而不是让作者手写视觉样式。常用模块包括 `objective`、`info`、`task`、`requirement`、`deliverable`、`checklist` 和 `rubric`。

示例写法可以使用 `::: {.objective title="目标"}` 表达目标，使用 `::: {.task title="任务"}` 表达工作，使用 `::: {.deliverable title="交付物"}` 表达交付物。指令块结束时用 `:::` 收束。

实际写作时，模块标题应该使用中文，指令名保持英文，便于转换层稳定识别。

# 复习题和 Q-A

复习题使用 `question`、`hint`、`answer`、`solution`，也可以用 `qa` 把一组问答放进同一个模块。`answer_mode` 控制答案是否出现在 PDF 中。

| answer_mode | 行为 |
|---|---|
| `student` | 隐藏 `answer` 和 `solution`。 |
| `review` | 显示答案和解析，适合审阅版。 |
| `teacher` | 显示答案和解析，适合教师或维护者版本。 |

示例写法可以使用 `::: {.question title="复习题" style="plain"}` 提出问题，再使用 `::: {.answer title="参考答案" style="plain"}` 写参考答案。发布前运行 `hypolatex doctor` 的原因是 PDF 构建依赖 Pandoc、LaTeX 工具链和本地 package，提前检查能避免构建中途失败。

::: {.qa title="复习题：构建路径"}
::: {.question title="题目" numbered="false"}
发布文档的最小构建路径应该先运行哪个命令？
:::

::: {.answer title="参考答案"}
先运行 `hypolatex doctor`，再运行 `hypolatex build`。
:::
:::

# 受控表格

普通 Markdown 表格适合简单内容。需要稳定列宽、密度、caption、label 或多页表格时，使用 `.table` 受控表格。

受控表格通常从 `::: {.table}` 开始，配置 `type: checklist`、`density: compact`、`caption: Release evidence map`、`label: tab:release-evidence`，然后跟一个 Markdown 表格。表格列可以是 `Checkpoint`、`Evidence` 和 `Owner`，行可以记录 `Source`、`Build` 和 `Review`。

受控表格的目标是让 AI 和人类都能维护表格意图，不需要把 LaTeX 列格式直接塞进 Markdown。

# Cheatsheet 紧凑布局

需要一页或两页的紧凑速查表时，在 frontmatter 中声明 `document_type: article` 加 `layout: cheatsheet`。cheatsheet 是 `article` 之上的布局模式，不是新的文档类型：正文、标题、语义模块和受控表格保持兼容；不写该 layout 时文档仍走标准 article 版式。

写作约定是：

- 多栏内容放在 `cheatsheet-grid` 中（如 `columns="4"`、`gap="compact"`），正文按语义顺序自然顺排，multicols 自动换列，不手写 `\columnbreak`。
- 正文章节保持普通标题加列表的流式写法；只有“别忘了”“重点”“补充”这类提示才使用 `cheatsheet-cell` 小盒子。盒子是强调手段，不是结构单位。
- 窄栏中较长公式写成行间数学，过宽的等式链用 `aligned` 拆行；短字段可以用行内代码，过长的行内代码会自动降级为可折行文本。
- 高密度对照表使用 `.table` 配 `type: cheatsheet` 与 `density: compact`。

`hd:make-cheatsheet` 是 AI 面向的 Skill workflow：从既有资料整理速查表时，目标页数是硬约束，压缩优先级为公式高于关键点高于示例；无法压进目标页数时应返回冲突报告，而不是静默加页。内置示例模板是 `skill/templates/cheatsheet.md`，完整说明见 `docs/c5-cheatsheet.md`。

# 图片

图片推荐用 `.figure` 指令，而不是在正文中混合裸 LaTeX。发布文档中只有在图片资源可公开、可提交、可通过相对路径解析时才引用图片。

推荐写法是 `::: {.figure label="fig:workflow" src="assets/workflow.png" caption="Workflow overview" width="0.92" placement="H"}`，再用 `:::` 结束。

`src` 应该指向仓库内公开资源，`caption` 写可读说明，`width` 用简单比例，例如 `0.92`。当教程需要图片接近源码位置时，可以使用 `placement="H"`。

# AI 写作和 Skill

Hypo-LaTeX 面向 AI 协作写作，但公开文档仍应保持人类可读。AI 写作建议遵循三条规则：

1. 先写结构，再补正文。
2. 优先使用已支持的 HypoDoc Markdown 子集。
3. 构建前运行 `hypolatex doctor`，构建后保留可复现命令。

完整命令应该使用 fenced code block，不要塞进行内代码。行内代码适合 `theme`、`answer_mode`、`hypolatex` 这类短字段；只要命令包含多个参数或接近一整行，就写成 `bash` 代码块，避免行内盒子过长导致排版溢出。

`hypolatex skill` 代表面向 agent 的使用习惯：AI 在维护本仓库文档或模板时，应读取项目 Skill，优先选择 theme-first frontmatter、语义模块、复习题、受控表格和公开资源路径。Skill 不是私有语料入口，也不应该把本机素材路径写进发布文档。

# 发布前检查清单

- 文档有 YAML frontmatter，并设置已注册 `theme`。
- 中文为主体，英文只用于术语、命令、路径和字段名。
- `hypolatex doctor` 通过或缺失项已记录。
- `hypolatex build` 能生成 PDF。
- PDF 文本中能抽取标题、`hypolatex build`、`theme` 等证据。
- 手册只解释当前实现和同步章节，不取代 `hypodoc-spec` 或 `spec/hypodoc`。
