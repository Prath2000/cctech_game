---
id: TASK-1.13
title: Light switch with on/off bakes
status: To Do
assignee: []
created_date: '2026-11-05T10:22:00Z'
labels:
  - effort:M
dependencies:
  - TASK-1.10
  - TASK-1.8
parent_task_id: TASK-1
priority: medium
type: feature
ordinal: 2300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Second bake (lights off) and smooth blend in the TSL material; switch is a Use item. Spec §7 light switch.

Parallel-safe: yes (with T11, T12). Plan: .team/changes/0001-pantry-poc/plan.md (T13).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Using the switch fades lights on/off in about 0.5 s.
- [ ] #2 Both states are baked by the same command.
- [ ] #3 No hitch measured at the switch.
<!-- AC:END -->
