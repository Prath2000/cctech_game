---
id: TASK-1.7
title: Branded props and furniture
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T10:42:00Z'
labels:
  - effort:L
dependencies:
  - TASK-1.5
  - TASK-1.2
parent_task_id: TASK-1
priority: high
type: feature
ordinal: 1700
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Model Tata Bistro machine, LG fridge, LG microwave, kettle, sink, vending "PUSH" machine, water coolers, chairs, tables, mugs, flasks, purple jug, glasses, using public product shapes for unseen sides and photo decals. Each as a named object. Spec §4, §10b.7.

Parallel-safe: yes (with T6). Plan: .team/changes/0001-pantry-poc/plan.md (T7).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All listed props exist in the scene with unique names.
- [ ] #2 Branded items side by side with photos have no major brand differences.
- [ ] #3 Repeated items (mugs, chairs) are instanced.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Seating half: blender/props/seating.py (+ run_seating.py, preview_seating.py; pnpm build:props:seating -> public/models/props_seating.glb). Layout read from blender/layout.py (tables, vending, coolers, room size) so a resize is one edit. Contains vending_machine (PUSH, 6 spiral rows, glass, keypad, tablet, flap), cooler_01/02 + steel_tumbler, 6+ tables, chairs (2 shared meshes), glasses, snack packets, ketchup/salt, 2 bins, 6 fans, circuit mural (decal cropped from photo 08). Skipped: INNOVATION chevrons (blockout/materials), LED panels (off in photos). ~113k tris counted per instance. Previews vs photos 08/08(1)/08(3) checked; coolers lack the photo gap between units (0.3 pitch).
<!-- SECTION:NOTES:END -->
