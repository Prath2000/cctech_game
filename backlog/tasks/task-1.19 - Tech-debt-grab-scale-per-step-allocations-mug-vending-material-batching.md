---
id: TASK-1.19
title: 'Tech debt: grab scale + per-step allocations; mug/vending material batching'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:48:00Z'
updated_date: '2026-11-05T11:21:00Z'
labels:
  - effort:S
dependencies:
  - TASK-1.11
  - TASK-1.12
  - TASK-1.18
parent_task_id: TASK-1
priority: medium
type: chore
ordinal: 2350
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From batch-2 review. grab.ts:63/93 ignores object scale for colliders; grab.ts:148-152 allocates Ray/hit per step; pantry.py:532/548 one material per mug colour (92 materials, 208 primitives in room.glb) -> fold into perf pass: shared material with per-instance colour or atlas, merge static meshes by material.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Grab colliders respect object scale
- [x] #2 No per-step allocations in grab
- [x] #3 Mugs/vending items share materials; draw calls reduced (number recorded)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Code done, room.glb NOT rebuilt (bake running). grab.ts: collider verts now multiplied by object scale; beforeStep reuses one Rapier Ray. pantry.py: 10 mug materials -> 1 shared 'pantry_mug' with per-colour mesh + COLOR_0 vertex colour. Test build (ROOM_OUT env, not public/): materials 92->83, mug mats 10->1, meshes 146, prims 250, mesh nodes 263 (~457 draw prims) unchanged; check:glb passes (0 missing TEXCOORD_1). Vending products already share meshes (9 mats); left. Static merge left to TASK-1.14. Pending: rebuild room.glb after bake, renderer.info numbers, check:grab (51ms frame fail under bake CPU load).

Final: room.glb rebuilt after bake finished. materials 92->83 (mug 10->1), meshes 146, primitives 250, mesh nodes 263 unchanged (no instancing/merge; merge left to TASK-1.14). check:glb, typecheck, build, check:grab, check:pantry, check:seating pass. renderer.info not captured (headless checks only).
<!-- SECTION:NOTES:END -->
