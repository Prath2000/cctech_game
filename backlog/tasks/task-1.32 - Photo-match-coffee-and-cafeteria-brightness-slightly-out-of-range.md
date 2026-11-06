---
id: TASK-1.32
title: 'Photo-match: coffee and cafeteria brightness slightly out of range'
status: To Do
assignee: []
created_date: '2026-11-06T09:50:00Z'
labels:
  - effort:S
dependencies: []
parent_task_id: TASK-1
priority: low
type: bug
ordinal: 5600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
On 119434b check:match gives coffee 0.78 (target >= 0.8) and cafeteria 1.16 (over by 0.01). Bring both into range with local changes only. Out of scope: global exposure change; avoid a full bake (about 45 min).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 check:match reports coffee and cafeteria in range
- [ ] #2 All other check:match ratios stay in range
<!-- AC:END -->
