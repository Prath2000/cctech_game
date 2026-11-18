---
id: TASK-1.17
title: >-
  Resize room to the point-cloud scan layout (8.7 x 7.35 m hall + bay, 2.65 m
  ceiling)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:34:00Z'
updated_date: '2026-11-18T05:52:00Z'
labels:
  - effort:M
dependencies:
  - TASK-1.5
parent_task_id: TASK-1
priority: high
type: enhancement
ordinal: 1450
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User: the pantry looks too small. Re-measure from video gave window wall ~11-13 m, depth ~7-8 m, ceiling ~3.2 m, window strip ~2.5-3 m wide with one pillar, ~9-12 window panels of ~1 m, ~3 rows of 2-3 long tables (low-confidence guesses). Move all room dimensions into one shared blender/layout.py and rebuild.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All room dims and anchors live in blender/layout.py; blockout, materials and props read from it
- [x] #2 Room rebuilt at the new size; reference sheet and camera poses updated
- [x] #3 check:walk passes; user agrees proportions look right
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Room rebuilt at the scan layout (8.7 x 7.35 m hall + bay, 2.65 m ceiling), all sizes in blender/layout.py. check:walk passes (walls, glass, table, pillar block; free walk moves). User approved the proportions from overview, cafeteria and strip screenshots on 2026-11-18.
<!-- SECTION:FINAL_SUMMARY:END -->
