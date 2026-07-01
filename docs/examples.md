# HypoDoc Markdown 示例

这个页面集中放 Hypo-LaTeX 常用的 HypoDoc Markdown 片段。README 只保留最短的代表性例子；实际写文档、维护模板或更新 AI Skill 时，可以参考这里。

## 最小长文文档

```markdown
---
title: Example Longform Document
author: Example Author
theme: classic-readable
---

# 第一章

这里写正文。普通 Markdown 段落、列表、数学公式和图片仍然走 Pandoc 的常规路径。
```

## 项目或作业模块

语义模块用于标记文档意图。它们不是只给课程作业用，也可以用于科研组项目、实现 Brief、实验任务和交接文档。

```markdown
::: {.objective title="目标"}
完成一个可复现的 PDF 构建，并保留验证证据。
:::

::: {.info title="背景"}
输入源文件由 AI 维护，人工只审批 Markdown 和最终 PDF。
:::

::: {.task title="任务"}
- 运行环境检查。
- 构建 PDF。
- 记录输出文件和验证命令。
:::

::: {.requirement title="要求"}
- 不提交 private corpus 的真实输入和生成物。
- 所有公开测试必须能在干净环境中运行。
:::

::: {.deliverable title="交付物"}
提交 Markdown 源文件、生成的 PDF 路径和测试摘要。
:::

::: {.checklist title="检查清单"}
- `hypolatex doctor` 通过。
- `hypolatex build` 通过。
- PDF 页数和文本抽取结果符合预期。
:::

::: {.rubric title="验收标准"}
- 源文件结构清晰。
- PDF 可读。
- 私有测试结果不进入仓库。
:::
```

## 复习题

复习题文档使用 `question`、`hint`、`answer` 和 `solution`。

```markdown
---
title: Review Packet
theme: classic-readable
answer_mode: student
---

::: {.question title="题目 1" style="outline"}
为什么构建 PDF 前需要先运行 `hypolatex doctor`？
:::

::: {.hint title="提示" style="plain"}
从外部命令和 LaTeX package 依赖入手。
:::

::: {.answer title="参考答案" style="plain"}
因为 PDF 构建依赖 Pandoc、XeLaTeX、latexmk 和必要的 LaTeX package。
:::

::: {.solution title="解析" style="plain"}
如果依赖缺失，转换可能成功但编译失败；先做环境检查可以把失败前移到更明确的阶段。
:::
```

用 CLI 构建不同答案版本：

```bash
uv run hypolatex build review.md --answer-mode student --output build/student.pdf
uv run hypolatex build review.md --answer-mode review --output build/review.pdf
uv run hypolatex build review.md --answer-mode teacher --output build/teacher.pdf
```

## 组合式复习题卡片

当一个复习题需要把题干、提示、答案和解析放在同一个大卡片里时，使用 `qa`。

```markdown
::: {.qa title="复习题：构建证据"}
::: {.question title="题目" numbered="false"}
哪些构建证据可以进入公开仓库，哪些应该留在本机？
:::

:::hint
区分 synthetic/public fixtures 和真实 private corpus。
:::

:::answer
公开 fixtures 的测试结果可以提交；真实 private corpus 的输入、PDF 和抽取文本都应留在 ignored 路径。
:::

:::solution
公开测试用于回归，private corpus 只用于本机 smoke validation。两类结果应在报告中分开记录。
:::
:::
```

## 图片

教程或书籍里如果希望图片接近源码位置，可以显式设置宽度和固定 placement。

```markdown
::: {.figure label="fig:workflow" src="assets/workflow.png" caption="Workflow overview" width="0.92" placement="H"}
:::
```

`src` 会相对 Markdown 源文件目录和配置的资源目录解析。更多细节见 `docs/figures.md`。

## 受控表格

只有在表格版式需要稳定控制时才使用 `.table`。普通 Markdown 表格不需要包在 `.table` 中，它们会继续走 Pandoc 的默认表格路径。

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
| Review | PDF text and page evidence | Reviewer |

:::
````

当前表格类型包括 `default`、`comparison`、`checklist`、`rubric`、`cheatsheet`、`compact` 和 `long`。当前密度包括 `compact`、`normal` 和 `comfortable`。
