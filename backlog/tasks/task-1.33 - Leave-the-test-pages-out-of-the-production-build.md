---
id: TASK-1.33
title: Leave the test pages out of the production build
status: To Do
assignee: []
created_date: '2026-11-06T09:50:00Z'
labels:
  - effort:S
dependencies: []
parent_task_id: TASK-1
priority: low
type: chore
ordinal: 6600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
dist contains 61 MB of dist/spike plus spike.html and pathtrace.html, none of which the game page needs. The game does not download them, so this affects hosting size, not load time. In scope: production build only. Out of scope: removing them from local development; render:pt must keep working.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Production build contains no spike or pathtrace pages or spike assets
- [ ] #2 render:pt and the dev-server spike page still work
<!-- AC:END -->
