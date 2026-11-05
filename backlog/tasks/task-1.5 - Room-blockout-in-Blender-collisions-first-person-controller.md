---
id: TASK-1.5
title: Room blockout in Blender + collisions + first-person controller
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T10:28:00Z'
labels:
  - effort:L
dependencies:
  - TASK-1.1
  - TASK-1.2
parent_task_id: TASK-1
priority: high
type: feature
ordinal: 1400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Python-scripted Blender blockout from the reference sheet: room shell, windows, pillar, chevron wall and door, counter spot, fridge niche. Export glTF; Rapier colliders; walk and sprint, mouse look. Spec §5b, §9 controls, §11.

Parallel-safe: yes (with T4). Plan: .team/changes/0001-pantry-poc/plan.md (T5).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 One Blender script rebuilds the blockout headless.
- [x] #2 Walk and sprint around the room, no walking through walls or counters.
- [x] #3 Blockout loads in game at 60 fps in the harness.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Blender blockout (pnpm build:blockout -> public/models/room_blockout.glb, 71 objs, lightmap UV2, static=1, collider=none extras); src/room.ts cuboid colliders; src/controller.ts Rapier KCC FPS (WASD, mouse, Shift sprint, autostep); pnpm check:walk asserts wall/glass/counter/table/pillar blocking; headless fps 59.9 median (WebGPU, 1280x720) with ?pose=overview
<!-- SECTION:NOTES:END -->
