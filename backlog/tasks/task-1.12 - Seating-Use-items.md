---
id: TASK-1.12
title: Seating Use items
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T10:56:00Z'
labels:
  - effort:M
dependencies:
  - TASK-1.7
  - TASK-1.8
  - TASK-1.9
parent_task_id: TASK-1
priority: medium
type: feature
ordinal: 2200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Chairs roll, swivel, can be sat in; vending machine drops a snack that can be grabbed; water coolers fill a glass. Spec §9 seating.

Parallel-safe: yes (with T11). Plan: .team/changes/0001-pantry-poc/plan.md (T12).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Sit and stand on a chair works.
- [x] #2 Vending drops a grabbable snack.
- [x] #3 Cooler fills a glass that can be carried.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
src/seating.ts (chairs/vending/coolers), src/audio/audio.ts, scripts/seating.ts (pnpm check:seating). Chairs: dynamic Y-locked bodies, player passes through and pushes by proximity; room.ts skips static colliders for chairs. check:grab fails on stale bounds (room now extends past z 7), not from this change.
<!-- SECTION:NOTES:END -->
