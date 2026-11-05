---
id: TASK-1.7
title: Branded props and furniture
status: To Do
assignee: []
created_date: '2026-11-05T10:22:00Z'
labels:
  - effort:L
dependencies:
  - TASK-1.5
  - TASK-1.2
parent_task_id: TASK-1
priority: high
type: feature
ordinal: 1700
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Model Tata Bistro machine, LG fridge, LG microwave, kettle, sink, vending "PUSH" machine, water coolers, chairs, tables, mugs, flasks, purple jug, glasses, using public product shapes for unseen sides and photo decals. Each as a named object. Spec §4, §10b.7.

Parallel-safe: yes (with T6). Plan: .team/changes/0001-pantry-poc/plan.md (T7).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All listed props exist in the scene with unique names.
- [ ] #2 Branded items side by side with photos have no major brand differences.
- [ ] #3 Repeated items (mugs, chairs) are instanced.
<!-- AC:END -->
