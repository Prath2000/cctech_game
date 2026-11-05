---
id: TASK-1.25
title: 'Photo-match: LG fridge too small and view blocked'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T11:36:00Z'
updated_date: '2026-11-05T11:49:00Z'
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
Photo 07 (2): large silver LG fridge close-up with glazed wall left; shot has small distant fridge and a big grey slab blocking view. Fix props/fridge.py scale, layout.py slab, pose. See verify.md.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
WIP: fridge moved to world z 0.2-0.755 beside windows, top 1.6m; niche depth 0.8->0.05 (it walled off windows); window_sill now stops at fridge. Left: rebake lightmaps (layout changed), verify pose framing, final check:pantry.
<!-- SECTION:NOTES:END -->
