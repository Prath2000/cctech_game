---
id: TASK-1.29
title: >-
  Analyse photogrammetry scan: true room measurements + scan-as-visual
  evaluation
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T11:44:00Z'
updated_date: '2026-11-05T11:49:00Z'
labels:
  - effort:M
dependencies: []
parent_task_id: TASK-1
priority: high
type: spike
ordinal: 2050
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
User supplied references/photogrammetry/pantry-obj.zip (textured mesh: 306k verts, 435k faces, 4096² texture) and pantry.zip (coloured point cloud, 1.8M points, PCL PLY). Extracted to references/photogrammetry/obj and ply (gitignored). Use it to replace guessed dimensions (room size, counter position, fridge, pillar, windows, door, chevron wall, table grid) and evaluate using the scan directly for realism.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Scale and orientation verified (known-size checks) and documented
- [ ] #2 docs/reference/scan-measurements.md with all key dimensions/positions vs current blender/layout.py and a proposed layout diff
- [ ] #3 Go/no-go on using the scan mesh/points as visual base, with preview renders
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
WIP: alignment, room size, counter done. Left: full feature table, layout diff, perspective renders, ASCII plan, scan-as-visual go/no-go, tick ACs.
<!-- SECTION:NOTES:END -->
