---
id: TASK-1.4
title: 'Lighting spike (risk #1)'
status: To Do
assignee: []
created_date: '2026-11-05T10:22:00Z'
labels:
  - effort:L
dependencies:
  - TASK-1.1
  - TASK-1.3
parent_task_id: TASK-1
priority: high
type: spike
ordinal: 1500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On a simple box room with one window: Blender Cycles bake (denoised HDR, plus directional lightmap), AgX in both, a probe sample, and a TSL material in Three.js that shows it. Must run on WebGPU and WebGL2. Spec §7, §10b.1-2.

Parallel-safe: no. Plan: .team/changes/0001-pantry-poc/plan.md (T4).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Box-room screenshot from game is visibly close to Blender render (same AgX).
- [ ] #2 Normal-mapped surface reacts to directional lightmap.
- [ ] #3 A movable test sphere picks up probe light.
- [ ] #4 Same result on WebGPU and WebGL2, fps measured with T
- [ ] #5 Short written go/no-go plus fallback if any piece fails.
<!-- AC:END -->
