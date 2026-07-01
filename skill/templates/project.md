---
title: C3 Project Brief Template
subtitle: Semantic Blocks For Assignments, Projects, And Research Tasks
author: Example Author
organization: Hypo Research Lab
course: Flexible Project Studio
date: 2026-06-29
theme: tech-minimal
cover_layout: info-panel
---

# Project Orientation

This project assignment template demonstrates the C3 semantic block vocabulary without turning the document into a fixed course schema. Adapt the labels and prose for a course exercise, research-group sprint, lab task, or operations handoff.

::: {.objective title="目标"}
Produce a reviewable PDF brief from Markdown that names the work, the constraints, the expected artifact, and the validation evidence.
:::

::: {.info title="背景信息"}
The project team starts from a short Markdown source. The final handoff should be understandable to a reviewer who only sees the source file, generated TeX, public build result, and implementation notes.
:::

::: {.task title="实施任务"}
Draft the brief, add the controlled table below, build the PDF, and record the exact validation commands that were run.
:::

::: {.requirement title="硬性要求"}
Keep the document source portable: use supported C3 blocks, supported theme metadata, and project-local assets only when they are already part of the repository.
:::

::: {.deliverable title="交付物"}
Submit the Markdown source, the generated public PDF, and a short note explaining what was validated and what remains out of scope.
:::

::: {.checklist title="交接检查"}
- The objective is stated in reader-facing language.
- Each requirement can be checked by a reviewer.
- Deliverables name concrete artifacts or evidence.
- Public outputs do not include private corpus content.
:::

::: {.rubric title="验收标准"}
- The source uses semantic modules instead of manual visual separators.
- The generated PDF makes each module visually identifiable.
- The validation note separates public evidence from local private-corpus evidence.
:::

## Checkpoint Table

The controlled `.table` example uses YAML `columns`, plus a caption and label, so the layout is stable in the generated PDF.

::: {.table}
```yaml
type: checklist
density: compact
caption: Project assignment checkpoint map
label: tab:c3-project-checkpoints
columns:
  - align: left
    width: 0.22
  - align: left
    width: 0.42
  - align: left
    width: 0.28
```

| Checkpoint | Evidence | Reviewer Signal |
|---|---|---|
| Scope | Objective, task, and requirement blocks | The work is bounded |
| Build | PDF produced from this Markdown source | The template is buildable |
| Handoff | Deliverable and checklist blocks | The next reader knows what to inspect |
| Privacy | Public/private validation note | Real artifacts stay local |

:::

:::summary
C3 blocks help authors communicate intent while leaving room for many document types: course assignments, project briefs, lab workflows, research tasks, and review packets.
:::
