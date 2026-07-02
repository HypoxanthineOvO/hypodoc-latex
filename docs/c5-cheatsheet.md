# C5 Cheatsheet Layout

C5 增加的是面向紧凑速查表的 layout API。作者在 Markdown frontmatter 中写
`document_type: article` 与 `layout: cheatsheet`，即可让同一篇 `article`
进入 cheatsheet 版式路径。这里的 API 是文档版式约定，不是新的命令行入口；
构建 PDF 仍使用已有 build 流程。

## layout API

`layout api` 只负责声明文档布局。当前 cheatsheet 公共契约的核心字段是：

```yaml
---
document_type: article
layout: cheatsheet
---
```

`layout: cheatsheet` 会启用紧凑页面节奏、较密的模块间距，以及适合速查表的
grid/cell 渲染。它仍然属于 `article` 文档类型，因此正文、标题、受控表格和
C3 语义块保持兼容。

## grid/cell syntax

速查表内容建议放在 `cheatsheet-grid` 中，再用 `cheatsheet-cell` 表示每个知识
单元。grid 控制列数和间距，cell 记录类型、标题、优先级、跨度和是否必须保留。

```markdown
:::: {.cheatsheet-grid columns="3" gap="compact"}
::: {.cheatsheet-cell type="formula" title="Derivative Rules" priority="high" span="1" keep="true"}
- Power rule: $d(x^n)/dx = nx^{n-1}$
- Chain rule: $d(f(g(x)))/dx = f'(g(x))g'(x)$
:::

::: {.cheatsheet-cell type="concept" title="Review Checks" priority="medium" span="1" keep="false"}
- State assumptions.
- Keep formulas exact.
- Drop examples before formulas.
:::
::::
```

`cheatsheet-cell` 的 `priority="high"` 和 `keep="true"` 会影响 AI 工作流里的压缩
判断：这些单元应优先保留，除非用户明确放宽约束。

## article fallback

当文档是 `document_type: article` 但没有设置 `layout: cheatsheet` 时，系统走
普通 article fallback 行为，也就是标准文章布局。换句话说，`article` 是稳定的
基础文档类型，`layout: cheatsheet` 是在这个基础上打开紧凑速查表布局；没有该
layout 时不会破坏原有 article 渲染。

## target pages

`target pages` 是 hard constraint。AI 在执行 `hd:make-cheatsheet` Skill workflow
时，应把目标页数视为不可静默突破的约束：如果公式、关键点和示例无法压缩到目标
页数内，应返回 conflict report，而不是自动增加页数。压缩优先级为
`formulas > keypoints > examples`，所以示例最先删减，公式最后删减。

## compact table

速查表也可以使用受控表格 DSL。对高密度对照表，使用 `.table` 并声明
`type="cheatsheet"` 与 `density="compact"`。

```markdown
::: {.table type="cheatsheet" density="compact" width="0.92" caption="Sample quick reference" label="tab:sample-quick-reference"}
| Signal | Action | Evidence |
| --- | --- | --- |
| Formula | Keep exact | Equation visible |
| Keypoint | Merge when needed | One-line summary |
| Example | Omit first | Optional sample |
:::
```
