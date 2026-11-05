---
id: TASK-1.2
title: Reference survey and sheet
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T10:23:00Z'
labels:
  - effort:M
dependencies: []
parent_task_id: TASK-1
priority: high
type: task
ordinal: 1200
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Helper reads each pantry/seating photo and video frames: camera spot, lens estimate, size estimates, light state (on/off, sun), materials, brand details. Writes one reference sheet doc. Spec §5, §5b, §10b.5, §10c.

Parallel-safe: yes. Parent: TASK-1. Plan: .team/changes/0001-pantry-poc/plan.md (T3).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Sheet has an entry for every pantry and seating photo listed in §5/§5b.
- [ ] #2 Each entry has camera spot, lens, light state, materials.
- [ ] #3 Room size and counter position proposal listed.
<!-- AC:END -->
