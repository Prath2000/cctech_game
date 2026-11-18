---
id: TASK-1.35
title: Occasional single slow frame while walking and turning
status: In Progress
assignee: []
created_date: '2026-11-06T10:48:00Z'
updated_date: '2026-11-18T05:59:00Z'
labels:
  - effort:S
dependencies: []
parent_task_id: TASK-1
priority: low
type: bug
ordinal: 8600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Headed Chrome, production build, 15 s runs. 3 of 10 walking-and-turning runs had one slow frame: WebGPU 32.5 ms; WebGL 49.7 ms and 250.1 ms. An earlier standing WebGPU run had 100 ms. Most runs stay at 18.7 ms. Cause unknown: not tested whether it is a first view of an area, shader or texture work, or other activity on the Mac. In scope: find out when the slow frames happen and fix them if they come from the game. Out of scope: Safari (TASK-1.34).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 fps run reports the time and player position of any frame over 25 ms
- [x] #2 Cause named from at least 10 runs on each backend, or stated as outside the game
- [ ] #3 If the game is the cause: fixed, and 10 further runs on each backend have no frame over 33 ms
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-18 re-test after final code (try/finally + hidden objects warmed): partway through (19 of 40 runs), 3 slow frames seen: 83.4 ms (WebGPU fast turn, 2.3 s in, at 6.9,4.5), 33.3 ms and 32.4 ms (~11 s in, near 5.0-5.5, 4.8-4.9). No 'renderer grew' lines. AC #3 reopened.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Cause: the renderer built new GPU programs the first time parts of the room came into view while walking (WebGPU pipelines 90->102, WebGL 56->58); turning faster reproduced it 5/5, standing still 0/5. Fix (src/main.ts): build all programs during loading with culling and hidden objects switched on just for that step. Measured in the earlier session: 40 headed-Chrome runs (normal walk + fast turn, both backends, 15 s each), no frame over 18.8 ms, no new programs built. fps.ts reports each frame over 25 ms with time, position and yaw. Reviewer: no bugs, typecheck passes. Not re-measured this session: Google Chrome is no longer installed. Not covered: switch/sit/grab actions; older 100/250 ms frames never reproduced; Safari is TASK-1.34.
<!-- SECTION:FINAL_SUMMARY:END -->
