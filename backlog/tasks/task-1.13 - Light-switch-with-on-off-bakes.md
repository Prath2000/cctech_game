---
id: TASK-1.13
title: Light switch with on/off bakes
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T11:50:00Z'
labels:
  - effort:M
dependencies:
  - TASK-1.10
  - TASK-1.8
parent_task_id: TASK-1
priority: medium
type: feature
ordinal: 2300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Second bake (lights off) and smooth blend in the TSL material; switch is a Use item. Spec §7 light switch.

Parallel-safe: yes (with T11, T12). Plan: .team/changes/0001-pantry-poc/plan.md (T13).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Using the switch fades lights on/off in about 0.5 s.
- [ ] #2 Both states are baked by the same command.
- [ ] #3 No hitch measured at the switch.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
WIP: done = bake_room.py both-states (on = lights-only delta, LED 8.5 radiance, 16 panels in pantry.py), baked.ts uLights blend (static+probes), lightswitch.ts (E toggle, 0.5s fade, recapture reflections in place), scripts/switch.ts (pnpm check:switch), package.json. Left = full bake running (log: $TMPDIR/full.log, output public/lightmaps/{off,on}/, ~40 min); check:switch showed WebGPU validation error 'Invalid RenderPipeline aluminium_black' + 283ms frame at first toggle (stale off bake, investigate); then check:shot ?lights=1 views, texture MB, tick ACs, Done. Quick on bake: ~97 lux at LED 2.0 so 8.5 chosen (~410 lux).

On-state lightmaps are now luminance-only, 3 axes per RGB texture (<atlas>_on_p.png = px,py,pz; <atlas>_on_n.png = nx,ny,nz), tinted in shader by the LED colour. Reason: off(6)+on(6)+PBR maps hit 17 sampled textures, over the WebGPU 16 limit (pipeline creation failed). Probes stay full RGB. Full bake (both states) restarted, log in session TMPDIR full.log, output public/lightmaps/{off,on}/. Still to do: check:switch rerun, ?lights=1 shots on both backends, texture MB, tick ACs, Done.
<!-- SECTION:NOTES:END -->
