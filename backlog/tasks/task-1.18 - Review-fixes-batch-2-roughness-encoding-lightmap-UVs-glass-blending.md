---
id: TASK-1.18
title: 'Review fixes batch 2: roughness encoding, lightmap UVs, glass blending'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:48:00Z'
updated_date: '2026-11-05T10:51:00Z'
labels:
  - effort:S
dependencies: []
parent_task_id: TASK-1
priority: high
type: task
ordinal: 1850
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From batch-2 review. Must land before the full bake (TASK-1.10). 1) blender/materials.py:101-125 computed roughness maps written sRGB-tagged -> wrong curve; encode properly or Non-Color. 2) 75 static meshes in room.glb lack TEXCOORD_1 (vend_bottle_*, vend_can_*, vend_snack_* etc.): add lightmap UV or mark static=0/non-baked. 3) blender/materials.py:178-180 glass BLENDED -> sorting/overdraw; use alpha hash or render glass last with depthWrite off.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Roughness maps sample with the intended curve (verified numerically)
- [x] #2 Every static=1 mesh in room.glb has TEXCOORD_1; check script added
- [x] #3 Glass renders without sorting artifacts on WebGPU and WebGL2
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Roughness: root cause was data maps loaded/saved as sRGB (decode on load, encode on save). Now loaded and written Non-Color (set before filling pixels); exporter output is not black. Verified exported G mean vs raw rough.jpg*rs+ro within 0.5/255; normals ~(128,128,252). Lightmap: 74 vend_* clutter meshes get bake=0 (documented), socket_double gets lightmap UV; scripts/check_glb.py + pnpm check:glb pass. Glass: kept BLEND, room.ts sets depthWrite=false and renderOrder after load; shots OK on WebGPU and WebGL2.
<!-- SECTION:NOTES:END -->
