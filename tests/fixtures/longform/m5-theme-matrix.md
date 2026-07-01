---
title: M5 Theme Matrix Longform
subtitle: Additional theme validation fixture
author: Test Worker
date: 2026-06-29
theme: plain
abstract: Covers Chinese text, callouts, figures, references, and tables for theme builds.
---

# 主题矩阵验证

这是一段中文证据文本，用来确认新增书籍主题可以处理中文正文、目录和章节标题。

:::note
主题矩阵应保持真实内容可读，而不是只生成一个空白 PDF。
:::

## Figure And Reference

The figure directive may render a placeholder when the asset is absent, but the
theme build must still preserve captions and references.

::: {.figure label="fig:theme-flow" src="assets/theme-flow.png" caption="Theme matrix validation flow"}
:::

See the validation flow:

::: {.ref target="fig:theme-flow"}
:::

## Table Evidence

| 覆盖点 | Expected evidence |
| --- | --- |
| 中文 | 中文证据文本 |
| Callout | Note box content |
| Figure | Theme matrix validation flow |
| Table | This table compiles |

The document continues after the table so theme-specific spacing and table
handling must leave the body intact.
