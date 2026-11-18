---
id: TASK-1.14
title: Performance pass
status: To Do
assignee: []
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-18T06:20:00Z'
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
- [x] #2 Load under about 10 s.
- [ ] #3 Low setting measurably faster, same default look.
- [x] #4 Budget numbers in a short doc.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
From spike: KTX2 BC6H/ASTC HDR transcoding for lightmaps; pack ambient-cube axes into fewer textures.

User 2026-11-06: Low setting (AC #3) does not matter for the first pass; defer it.

Load: 4.9 s at 50 Mbps, 10.0 s at 20 Mbps after lossless WebP lightmaps (20.8 MB). Walking measured at 60 fps both backends in Chrome. Numbers in docs/reference/performance-budget.md. AC #1 needs Safari; AC #3 deferred by the user.

2026-11-18: user accepted 10.6 s cold load at 20 Mbps (5.6 s at 50 Mbps) after the warm-up fix.
<!-- SECTION:NOTES:END -->
