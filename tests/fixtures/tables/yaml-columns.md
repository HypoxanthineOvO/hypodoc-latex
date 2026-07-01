---
title: Controlled Table YAML Column Config
author: M5 Test Worker
theme: plain
---

# YAML Column Config

The first fenced `yaml` block inside `.table` is table configuration, not table
content.

::: {.table}
```yaml
type: rubric
density: normal
width: 0.9
caption: YAML configured rubric
label: tab:yaml-columns
header: true
striped: false
columns:
  - align: left
    width: 0.34
    weight: 2
  - align: center
    width: 0.18
    weight: 1
  - align: right
    width: 0.28
    weight: 3
```

| Criterion | Score | Comment |
| --- | --- | --- |
| Accuracy | 4 | Evidence is grounded |
| Clarity | 3 | Needs one example |
| Safety | 5 | No raw LaTeX escape hatch |
:::
