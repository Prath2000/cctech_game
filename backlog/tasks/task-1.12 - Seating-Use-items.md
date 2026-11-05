---
id: TASK-1.12
title: Seating Use items
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T10:43:00Z'
labels:
  - effort:M
dependencies:
  - TASK-1.7
  - TASK-1.8
  - TASK-1.9
parent_task_id: TASK-1
priority: medium
type: feature
ordinal: 2200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Chairs roll, swivel, can be sat in; vending machine drops a snack that can be grabbed; water coolers fill a glass. Spec §9 seating.

Parallel-safe: yes (with T11). Plan: .team/changes/0001-pantry-poc/plan.md (T12).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sit and stand on a chair works.
- [ ] #2 Vending drops a grabbable snack.
- [ ] #3 Cooler fills a glass that can be carried.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Started early: seating half of TASK-1.7 is done (props_seating via blender/props/seating.py); pantry half still in progress.
<!-- SECTION:NOTES:END -->
