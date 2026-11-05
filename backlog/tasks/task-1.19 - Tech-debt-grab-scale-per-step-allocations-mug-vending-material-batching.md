---
id: TASK-1.19
title: 'Tech debt: grab scale + per-step allocations; mug/vending material batching'
status: To Do
assignee: []
created_date: '2026-11-05T10:48:00Z'
updated_date: '2026-11-05T10:48:00Z'
labels:
  - effort:S
dependencies:
  - TASK-1.11
  - TASK-1.12
  - TASK-1.18
parent_task_id: TASK-1
priority: medium
type: chore
ordinal: 2350
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From batch-2 review. grab.ts:63/93 ignores object scale for colliders; grab.ts:148-152 allocates Ray/hit per step; pantry.py:532/548 one material per mug colour (92 materials, 208 primitives in room.glb) -> fold into perf pass: shared material with per-instance colour or atlas, merge static meshes by material.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Grab colliders respect object scale
- [ ] #2 No per-step allocations in grab
- [ ] #3 Mugs/vending items share materials; draw calls reduced (number recorded)
<!-- AC:END -->
