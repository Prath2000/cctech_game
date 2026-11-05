---
id: TASK-1.10
title: Full lighting bake, probes, reflections, tone mapping
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T10:58:00Z'
labels:
  - effort:XL
dependencies:
  - TASK-1.4
  - TASK-1.6
  - TASK-1.7
  - TASK-1.18
parent_task_id: TASK-1
priority: high
type: feature
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Apply the spike pipeline to the full room: matched fixtures and daylight, high-quality Cycles bake (hours OK), directional lightmaps, light probes, baked reflection probes (granite, steel, fridge), window glow, contact shadows and AO for movable items. Spec §7, §10b.4-5.

Parallel-safe: no. Plan: .team/changes/0001-pantry-poc/plan.md (T10).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One command re-bakes the room.
- [ ] #2 Movable mugs pick up room light and darken under cabinets.
- [x] #3 Reflections visible on granite and fridge.
- [ ] #4 Runs on both backends.
- [ ] #5 fps recorded with T2.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
From spike (docs/spikes/lighting-spike.md): use ambient-cube lightmaps (6 bakes) + cube probes grid; must also cover texel density/UV packing for the full room atlases, box-projected reflection probe validation in TSL, contact shadow/AO for dynamic items, probe validity near geometry. Sun patches need HDR headroom: consider RGBM or 16-bit instead of sRGB8 range 4-8.

Reflections+contact: src/lighting/{reflections,contact,index}.ts. 3 box-projected CubeCamera probes (pantry/window/hall; 256px High, 64 Low via ?quality=low) -> PMREM (roughness blur) + TSL getParallaxCorrectNormal on granite/steel/chrome/gloss/glass/floor (30 material variants). Contact blobs: 99 radial quads via Rapier down-ray, height-scaled, 0 extra passes. GTAO skipped. fps --headed: WebGPU 59.9 med/54.0 1%low; WebGL2 59.9/53.7. Caveat: reflections are subtle until baked lightmaps/emissive lights exist; call captureReflections() after them (main.ts currently captures after hemi+sun).
<!-- SECTION:NOTES:END -->
