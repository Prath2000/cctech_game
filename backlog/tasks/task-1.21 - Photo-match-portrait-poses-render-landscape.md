---
id: TASK-1.21
title: 'Photo-match: portrait poses render landscape'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T11:36:00Z'
updated_date: '2026-11-05T11:47:00Z'
labels:
  - effort:S
dependencies: []
parent_task_id: TASK-1
priority: high
type: bug
ordinal: 2550
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Poses fridge-07-2, coolers-08, vending-08-1 are 3:4 in reference sheet sec 5 but check:shot outputs 1600x1200. Fix scripts/shot.ts viewport from pose aspect. See verify.md Photo-match pass 1.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
check:shot now sizes viewport from pose aspect (long side 1600; --long/--size override); camera-poses.json gained aspect + photo fields; new pnpm check:match writes .team/work/shots/match-<pose>.png (photo|shot). lib.openGame retries on vite reload. Poses retuned vs photos: coffee, cabinets, fridge, sink, coolers, vending, cafeteria, strip-08-2 (fridge/sink/strip pending prop+lighting work from others).
<!-- SECTION:NOTES:END -->
