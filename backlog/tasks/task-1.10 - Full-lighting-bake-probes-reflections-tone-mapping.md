---
id: TASK-1.10
title: Full lighting bake, probes, reflections, tone mapping
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T11:34:00Z'
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
- [x] #1 One command re-bakes the room.
- [x] #2 Movable mugs pick up room light and darken under cabinets.
- [x] #3 Reflections visible on granite and fridge.
- [x] #4 Runs on both backends.
- [x] #5 fps recorded with T2.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
From spike (docs/spikes/lighting-spike.md): use ambient-cube lightmaps (6 bakes) + cube probes grid; must also cover texel density/UV packing for the full room atlases, box-projected reflection probe validation in TSL, contact shadow/AO for dynamic items, probe validity near geometry. Sun patches need HDR headroom: consider RGBM or 16-bit instead of sRGB8 range 4-8.

Reflections+contact: src/lighting/{reflections,contact,index}.ts. 3 box-projected CubeCamera probes (pantry/window/hall; 256px High, 64 Low via ?quality=low) -> PMREM (roughness blur) + TSL getParallaxCorrectNormal on granite/steel/chrome/gloss/glass/floor (30 material variants). Contact blobs: 99 radial quads via Rapier down-ray, height-scaled, 0 extra passes. GTAO skipped. fps --headed: WebGPU 59.9 med/54.0 1%low; WebGL2 59.9/53.7. Caveat: reflections are subtle until baked lightmaps/emissive lights exist; call captureReflections() after them (main.ts currently captures after hemi+sun).

Lighting core done. Bake: pnpm bake:room (full 128 spp ~18 min incl. room build + refs; --quick 24 spp ~9 min; --state off|on). Atlases: shell + props, 2048^2, 1.35 / 2.04 cm per texel, 6 ambient-cube maps each, OIDN denoised, sRGB8 with measured range 11.0 / 8.25 (max 12.8 / 18.9), PNG 1.6-2.1 MB / 0.8-1.0 MB per map (~23 MB total). 700 probes (670 valid, inside-solid ones ignored). Probe check: under wall cabinet 0.41 vs open counter 0.59 vs mid-room 1.48 (mean cube value). Both backends: max screenshot diff 1.2/255 mean over 4 poses. Game vs Blender ref: close in brightness/warmth; AgX exposure 0.9. fps headed 1280x720: WebGPU median 59.9, 1% low 56.9; WebGL2 59.9 / 57.0. Not done: window bloom, sun-patch tuning vs photos (TASK-1.15), on-state bake (TASK-1.13).
<!-- SECTION:NOTES:END -->
