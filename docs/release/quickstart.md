---
title: Hypo-LaTeX Quickstart
author: Hypo-LaTeX Maintainers
theme: tech-minimal
document_type: article
---

# 检查环境

先在仓库根目录运行：

```bash
hypolatex doctor
```

如果输出提示缺少 Pandoc、XeLaTeX、latexmk 或 LaTeX package，先补齐依赖再继续。

# 写最小文档

新建一个 Markdown 文件，并写入 frontmatter。`theme` 必须使用已注册主题。最小字段可以是 `title: My First Hypo-LaTeX PDF`、`author: Your Name` 和 `theme: classic-readable`。

正文可以从普通标题、段落、列表、代码块和表格开始。中文文档保持中文主体，命令、路径和字段名保留英文。

# 构建 PDF

运行：

```bash
hypolatex build input.md --output build/output.pdf
```

如果需要临时换主题，运行：

```bash
hypolatex build input.md --theme warm-handbook --output build/output.pdf
```

# 需要审阅中间结果

只生成 TeX 时运行：

```bash
hypolatex convert input.md --output build/output.tex
```

复习题文档需要显示答案时运行：

```bash
hypolatex build input.md --answer-mode review --output build/review.pdf
```

# 发布前确认

- 源文件有 YAML frontmatter。
- `theme` 是公开注册主题。
- `hypolatex doctor` 没有阻塞项。
- `hypolatex build` 生成的 PDF 可以打开。
- 公开文档不写入本机私有路径或不可提交素材。
