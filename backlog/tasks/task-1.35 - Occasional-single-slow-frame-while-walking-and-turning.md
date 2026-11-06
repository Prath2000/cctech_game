---
id: TASK-1.35
title: Occasional single slow frame while walking and turning
status: To Do
assignee: []
created_date: '2026-11-06T10:48:00Z'
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
- [ ] #1 fps run reports the time and player position of any frame over 25 ms
- [ ] #2 Cause named from at least 10 runs on each backend, or stated as outside the game
- [ ] #3 If the game is the cause: fixed, and 10 further runs on each backend have no frame over 33 ms
<!-- AC:END -->
