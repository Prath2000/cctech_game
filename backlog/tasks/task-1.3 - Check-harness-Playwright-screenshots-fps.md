---
id: TASK-1.3
title: Check harness (Playwright screenshots + fps)
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T10:26:00Z'
labels:
  - effort:M
dependencies:
  - TASK-1.1
parent_task_id: TASK-1
priority: high
type: chore
ordinal: 1300
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Headless Playwright script: load scene at a named camera pose (position, yaw/pitch, lens) and save a PNG; sample fps for N s and print median/p1. Works for both backends. Spec §6 check loop, §8.

Parallel-safe: no. Plan: .team/changes/0001-pantry-poc/plan.md (T2).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `pnpm check:shot <pose>` writes a PNG.
- [x] #2 `pnpm check:fps` prints median fps and 1% low.
- [x] #3 Backend flag selectable.
- [x] #4 Camera poses live in one JSON file.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Use: pnpm check:shot <pose> [--webgl] [--headed] [--size WxH] [--out p]; pnpm check:fps [--webgl] [--headed] [--seconds N] [--pose p]. Poses in src/data/camera-poses.json. See README Checks.
<!-- SECTION:NOTES:END -->
