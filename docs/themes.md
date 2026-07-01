# Hypo-LaTeX 主题

Hypo-LaTeX 采用以主题为中心的写作方式。普通 AI 生成或维护的文档，frontmatter 里通常只需要写 `theme:`，字体、颜色、封面和语义块样式由主题负责。

## 最小主题配置

```yaml
---
title: Example Document
author: Example Author
theme: classic-readable
---
```

只有当文档有明确的成品约束时，才应该使用字体、纸张、强调色、封面或资源目录等额外字段。不要因为字段存在，就在普通草稿里默认写一堆样式覆盖项。

## 公开主题预设

### `plain`

基础兼容主题，适合调试、最小文档和渲染器测试。需要尽量排除视觉样式干扰时使用它。

### `classic-readable`

长文默认选择，适合教程、书籍感资料和一般 PDF 输出。它优先保证中文排版稳定、正文可读和纸面阅读舒适度。

适合：

- 长文教程
- 解释型书稿
- 文章合集
- 需要人工审阅的正文草稿

### `tech-minimal`

克制的技术主题，适合模型评测、工程指南、榜单、表格和技术报告。它会保持页面安静，同时给密集信息更清晰的结构。

适合：

- 模型评测笔记
- 技术教程
- 对比表格
- 榜单式资料

### `warm-handbook`

更亲和的手册主题，适合课程笔记、解释型材料和不希望过于正式的学习资料。

适合：

- 学习手册
- 课程讲义
- 复习资料
- 分步骤讲解

### `academic-clean`

正式、克制的学术主题，适合研究风格报告、正式笔记和考试复习资料。

适合：

- 研究笔记
- 正式阅读材料
- 学术风格报告
- 考试复习文档

## 高级覆盖项

高级覆盖项用于微调一个已经选好的主题，不应该替代以 `theme:` 为核心的普通写作方式。

字体字段示例：

```yaml
mainfont: Sarasa Gothic SC
sansfont: MiSans
monofont: LXGW WenKai Mono
cjkfont: Sarasa Gothic SC
```

纸张和强调色字段示例：

```yaml
paper: a4
accent: "#2F5F8F"
```

封面字段示例：

```yaml
cover_layout: full-bleed-card
cover_image: assets/cover.png
```

资源目录字段示例：

```yaml
resource-root: assets
```

当前中文字体的角色分配见 `docs/fonts.md`。封面布局的可用值见 `docs/cover-layouts.md`。

## CLI 覆盖主题

构建时可以用 CLI 临时覆盖 frontmatter 里的主题：

```bash
uv run hypolatex build input.md --theme tech-minimal --output build/output.pdf
```

提交到仓库的正式文档源文件，建议优先在 frontmatter 里写 `theme:`。这样源文件本身就能说明自己的渲染意图。
