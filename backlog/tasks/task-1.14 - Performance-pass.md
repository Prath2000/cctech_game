---
id: TASK-1.14
title: Performance pass
status: To Do
assignee: []
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T11:22:00Z'
labels:
  - effort:L
dependencies:
  - TASK-1.10
  - TASK-1.11
  - TASK-1.12
  - TASK-1.13
  - TASK-1.19
  - TASK-1.20
parent_task_id: TASK-1
priority: medium
type: task
ordinal: 2400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
KTX2 textures, meshopt, instancing and draw-call budget, automatic resolution drop, High/Low setting, load time. Spec §8, §10b.2-3.

Parallel-safe: no. Plan: .team/changes/0001-pantry-poc/plan.md (T14).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Median 60 fps and no stutter on the user's Mac, Safari and Chrome, both backends.
- [ ] #2 Load under about 10 s.
- [ ] #3 Low setting measurably faster, same default look.
- [ ] #4 Budget numbers in a short doc.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
From spike: KTX2 BC6H/ASTC HDR transcoding for lightmaps; pack ambient-cube axes into fewer textures.
<!-- SECTION:NOTES:END -->
