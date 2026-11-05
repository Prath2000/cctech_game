---
id: TASK-1.9
title: Grab via Rapier
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T10:39:00Z'
labels:
  - effort:M
dependencies:
  - TASK-1.8
  - TASK-1.5
parent_task_id: TASK-1
priority: high
type: feature
ordinal: 1900
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Pick up, carry, drop, toss small rigid bodies. Items settle on surfaces and never fall through. Spec §9 Grab, §8 no hitch.

Parallel-safe: yes (with T6, T7). Plan: .team/changes/0001-pantry-poc/plan.md (T9).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Test cube can be picked up, carried, dropped and tossed.
- [x] #2 200 drops/tosses in a script: zero fall-throughs.
- [x] #3 No frame over 33 ms during grab in the harness.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
src/interact/grab.ts: grab items -> dynamic Rapier bodies (cuboid/convex from geometry, mass from userData, CCD), velocity-follow hold point with wall ray clamp, click/drop, Q/right-click toss, sleeping bodies skipped in mesh sync, respawn safety net. Collision groups: held items ignore player. pnpm check:grab: 200 cycles 0 fall-throughs, max frame ~21ms. Also review fixes: fixed-step physics, cached pickable meshes, highlight cache, room colliders oriented.
<!-- SECTION:NOTES:END -->
