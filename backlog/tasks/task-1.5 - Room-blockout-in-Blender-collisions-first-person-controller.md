---
id: TASK-1.5
title: Room blockout in Blender + collisions + first-person controller
status: To Do
assignee: []
created_date: '2026-11-05T10:22:00Z'
labels:
  - effort:L
dependencies:
  - TASK-1.1
  - TASK-1.2
parent_task_id: TASK-1
priority: high
type: feature
ordinal: 1400
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Python-scripted Blender blockout from the reference sheet: room shell, windows, pillar, chevron wall and door, counter spot, fridge niche. Export glTF; Rapier colliders; walk and sprint, mouse look. Spec §5b, §9 controls, §11.

Parallel-safe: yes (with T4). Plan: .team/changes/0001-pantry-poc/plan.md (T5).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One Blender script rebuilds the blockout headless.
- [ ] #2 Walk and sprint around the room, no walking through walls or counters.
- [ ] #3 Blockout loads in game at 60 fps in the harness.
<!-- AC:END -->
