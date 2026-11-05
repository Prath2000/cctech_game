---
id: TASK-1.6
title: Materials, textures and decals
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T10:47:00Z'
labels:
  - effort:M
dependencies:
  - TASK-1.5
parent_task_id: TASK-1
priority: high
type: feature
ordinal: 1600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CC0 PBR textures (Poly Haven/ambientCG) colour-matched to photos for floor, walls, granite, cabinets, windows; decals for the sticky note, B'ONE sign, INNOVATION sign, mural, chevrons. Spec §6.

Parallel-safe: yes (with T7). Plan: .team/changes/0001-pantry-poc/plan.md (T6).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each surface in the reference sheet has a material.
- [x] #2 Decals placed from photo crops.
- [x] #3 Texture licences recorded in one file.
- [x] #4 Screenshot from one photo spot shows matching surfaces.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Materials via blender/materials.py (recoloured CC0 PBR, world-size UVs, decals placed from named object bounds); build_room.py orchestrates to public/models/room.glb (WebP textures, 6 MB); src/room.ts loads room.glb. Checked cafeteria-08-3 vs photo: colours/chevrons match; lighting pending TASK-1.10.
<!-- SECTION:NOTES:END -->
