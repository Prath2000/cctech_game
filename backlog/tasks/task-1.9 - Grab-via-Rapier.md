---
id: TASK-1.9
title: Grab via Rapier
status: To Do
assignee: []
created_date: '2026-11-05T10:22:00Z'
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
- [ ] #1 Test cube can be picked up, carried, dropped and tossed.
- [ ] #2 200 drops/tosses in a script: zero fall-throughs.
- [ ] #3 No frame over 33 ms during grab in the harness.
<!-- AC:END -->
