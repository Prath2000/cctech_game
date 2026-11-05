---
id: TASK-1.11
title: Pantry Use items
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T11:08:00Z'
labels:
  - effort:L
dependencies:
  - TASK-1.7
  - TASK-1.8
  - TASK-1.9
parent_task_id: TASK-1
priority: medium
type: feature
ordinal: 2100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Coffee machine pour with steam and sound; microwave door plus countdown and ding; fridge door; kettle; sink; cabinet doors to reach mugs. Spec §9 Use.

Parallel-safe: yes (with T12). Plan: .team/changes/0001-pantry-poc/plan.md (T11).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each listed item reacts as specified.
- [x] #2 Cabinet opens and mugs can be grabbed.
- [x] #3 No frame hitch when using each item (harness).
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Pantry module src/pantry (index, hinge, fx); handlers registered by use_kind. Doors = kinematic Rapier bodies that reverse if the player is in the swept volume. Hollow props (wall cabinet, coffee machine) use collider=boxes + collider_boxes JSON (pantry.py, room.ts); 6 mugs now stored inside wall cabinets (asleep until door opens). check:pantry: all items max frame ~19 ms (limit 50).
<!-- SECTION:NOTES:END -->
