# Changelog

## v0.2.0

本版本对应 Cycle C5「Cheatsheet Compact Layout and AI-Friendly Authoring」，仍为本地发布：release assets 只在本地生成和检查，尚未上传 CTAN 或 PyPI。

新增：

- `layout: cheatsheet`：`article` 之上的紧凑速查表布局模式（小字号、密间距、轻量标题标记、multicols 自然换列并带列级 needspace 标题保护），不设置时 article 行为不变。
- `cheatsheet-grid` / `cheatsheet-cell` 指令：多栏顺排容器与小 callout 提示盒（盒子作为强调手段，正文保持流式）。
- `hd:make-cheatsheet` Skill workflow 与内置模板 `skill/templates/cheatsheet.md`：目标页数为硬约束，压缩优先级 formulas > keypoints > examples。
- 受控表格新增 `type: cheatsheet` 的紧凑速查表尺度。

改进与修复：

- 行内代码（`\texttt` 盒）宽度感知：超过 0.6 行宽自动降级为可折行 accent 色文本，修复窄栏与 showcase 中的行内盒溢出。
- `hypolatex-core.sty` 引入 amsmath；cheatsheet 版式放宽换行容差并收紧 display skip，支持 `aligned` 拆分过宽等式链。
- 重建 `build/showcase/hypolatex-showcase.pdf` 与 `assets/readme/showcase-banner.png`（0 overfull）。
- 文档同步：`docs/c5-cheatsheet.md` 新增，`docs/user-guide.md`、`docs/release/handbook.md`、README 补充 cheatsheet 公开写法。

本次 release assets 范围与 v0.1.0 相同：wheel、sdist、release handbook PDF、quickstart PDF。

## v0.1.0

这是 Hypo-LaTeX 的首个本地发布卫生版本，重点是把 HypoDoc Markdown 到 LaTeX/PDF renderer 的公开包装信息、构建资产边界和发布前说明整理清楚。当前版本面向本地验证、内部试用和后续发布准备，不代表已经完成远端发布。

本次 release assets 范围包括：

- Python wheel (`.whl`)。
- Python sdist / source distribution (`.tar.gz`)。
- Hypo-LaTeX release handbook PDF（发布手册 PDF）。
- Hypo-LaTeX quickstart PDF（快速开始 PDF）。

目前这些资产仅作为本地 release artifacts 生成和检查使用，尚未发布或上传到 CTAN 或 PyPI。后续如果进行 CTAN/PyPI 发布，应在发布动作完成后再更新本 changelog 的状态说明。
