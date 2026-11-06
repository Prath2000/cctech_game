---
id: TASK-1.24
title: 'Photo-match: cabinets and mugs differ'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T11:36:00Z'
updated_date: '2026-11-06T09:50:00Z'
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
Photo 07 (1): 3 tall glossy doors, shelf of colourful mugs; shot has 2 doors and uniform grey mugs. Fix blender/props cabinet door count + mug colours; pose pitch in camera-poses.json. See verify.md.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
WIP: 3 wall doors exist (shot crops to 2 by pose). Grey mugs root cause: src/lighting/baked.ts lit() emissive uses materialColor.rgb (white on shared pantry_mug), ignores COLOR_0 vertex colour; GLB export is fine. Fix in lighting: multiply by vertexColor() when geometry has color attr. Not edited (lighting-owned).

Pass 3 (119434b), one scout look; see verify.md. Cabinets and mugs passed, ratio 0.92. Open only for a confirming look and the user verdict.
<!-- SECTION:NOTES:END -->
