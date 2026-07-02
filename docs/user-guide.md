# Hypo-LaTeX 用户指南

Hypo-LaTeX 从 HypoDoc Markdown 构建 PDF。推荐工作流是：人类或 AI 维护结构化 Markdown，Hypo-LaTeX 将源文件转换成可审阅 TeX，并通过 LaTeX 后端编译 PDF。

## 当前状态

Hypo-LaTeX 目前处于早期预览阶段。它已经适合本地实验和内部文档生产，但 HypoDoc Markdown 0.1 草案和 CLI 接口仍可能变化。

## 环境要求

本地开发推荐使用 `uv` 安装依赖：

```bash
uv sync
```

PDF 构建路径需要：

- Pandoc
- XeLaTeX
- latexmk
- `hypolatex doctor` 报告中列出的必要 LaTeX package

先运行：

```bash
uv run hypolatex doctor
```

如果 `doctor` 报告缺少工具或 LaTeX package，应先安装缺失依赖，再继续构建。

## 构建 PDF

使用内置长文模板：

```bash
uv run hypolatex build skill/templates/longform.md \
  --theme classic-readable \
  --output build/longform.pdf
```

只生成可审阅 TeX，不编译 PDF：

```bash
uv run hypolatex convert skill/templates/longform.md \
  --output build/longform.tex
```

## 以主题为中心的 frontmatter

普通文档优先使用最小 frontmatter：

```yaml
---
title: Example Document
author: Example Author
theme: classic-readable
---
```

除非文档有明确成品约束，否则优先选择主题预设，不要手动覆盖字体、纸张、强调色和封面配置。

## 语义模块

语义模块用于表达内容意图：

```markdown
::: {.objective title="目标"}
说明读者最终应该达成的结果。
:::

::: {.task title="任务"}
描述需要完成的工作。
:::

::: {.deliverable title="交付物"}
说明需要提交或交接的产物。
:::
```

当前项目/文档类模块包括 `objective`、`info`、`task`、`requirement`、`deliverable`、`checklist` 和 `rubric`。

## 复习题

复习题文档使用 `question`、`hint`、`answer`、`solution`，也可以用 `qa` 把一组题目内容放进同一个大卡片。

```markdown
::: {.question title="开放推理题" style="plain"}
解释为什么构建前需要先运行环境检查。
:::

::: {.hint title="提示" style="plain"}
从外部命令和 LaTeX package 依赖入手。
:::

::: {.answer title="参考答案" style="plain"}
答案在 review 和 teacher 构建中显示。
:::
```

题目样式：

- `outline`：默认的轻边框题目。
- `card`：更强的复习卡片题目。
- `plain`：没有外框的正文流题目。

答案模式：

- `student`：隐藏 `answer` 和 `solution`。
- `review`：显示答案和解析。
- `teacher`：显示答案和解析，用于教师或维护者版本。

CLI 的 `--answer-mode` 会覆盖 frontmatter 中的 `answer_mode`。

## 图片

教程类图片如果需要保持接近源码位置，可以显式设置宽度和 placement：

```markdown
::: {.figure label="fig:workflow" src="assets/workflow.png" caption="Workflow overview" width="0.92" placement="H"}
:::
```

更多细节见 `docs/figures.md`。

## 受控表格

只有在表格版式需要稳定控制时才使用 `.table`。普通 Markdown 表格不需要包在 `.table` 中。

````markdown
::: {.table}
```yaml
type: checklist
density: compact
caption: Checkpoint map
label: tab:checkpoint-map
columns:
  - align: left
    width: 0.24
  - align: left
    width: 0.46
  - align: left
    width: 0.22
```

| Checkpoint | Evidence | Owner |
|---|---|---|
| Scope | Objective and requirements | Lead |
| Build | Generated PDF | Implementer |

:::
````

当前表格类型包括 `default`、`comparison`、`checklist`、`rubric`、`cheatsheet`、`compact` 和 `long`。

## Cheatsheet 布局

需要紧凑速查表时，在 frontmatter 中声明 `layout: cheatsheet`：

```yaml
---
title: Midterm Cheatsheet
theme: tech-minimal
document_type: article
layout: cheatsheet
---
```

`layout: cheatsheet` 仍属于 `article` 文档类型：正文、标题、语义模块和受控表格保持兼容，但页面进入紧凑节奏（小字号、密间距、轻量标题标记）。

多栏内容放在 `cheatsheet-grid` 中自然顺排，multicols 自动换列；只有“别忘了”“补充”这类提示才用 `cheatsheet-cell` 小盒子，正文章节不要装进盒子：

```markdown
:::: {.cheatsheet-grid columns="4" gap="compact"}

# 一、复数与三角函数 {.manual-number}

- $e^{j\theta}=\cos\theta+j\sin\theta$.

::: {.cheatsheet-cell type="keypoint" title="别忘了！" priority="high"}
$\sin\theta$ 的逆欧拉公式系数是 $1/(2j)$.
:::
::::
```

窄栏排版建议：较长公式写成行间数学（`$$...$$`），过宽的等式链用 `aligned` 拆行；过长的行内代码会自动降级为可折行文本，不会溢出栏宽。内置模板见 `skill/templates/cheatsheet.md`，AI 工作流见 Skill 中的 `hd:make-cheatsheet`，完整说明见 `docs/c5-cheatsheet.md`。

## AI Skill

AI Skill 位于 `skill/SKILL.md`。当 agent 需要维护 HypoDoc Markdown 并通过 Hypo-LaTeX 构建 PDF 时，应使用这个 Skill。

## 更多文档

- HypoDoc Markdown 规范：`spec/hypodoc/spec/hypodoc-markdown.md`
- 示例集合：`docs/examples.md`
- 主题说明：`docs/themes.md`
- C3 写作指南：`docs/c3-authoring.md`
- 语义模块设计：`docs/semantic-modules.md`
- Cheatsheet 布局：`docs/c5-cheatsheet.md`
- CLI 参考：`docs/reference/cli.md`
