---
id: TASK-1.8
title: Look data and Look highlight
status: To Do
assignee: []
created_date: '2026-11-05T10:22:00Z'
labels:
  - effort:S
dependencies:
  - TASK-1.5
parent_task_id: TASK-1
priority: high
type: feature
ordinal: 1800
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Interaction framework core: raycast from the crosshair, highlight and prompt showing interaction level, name plus one-line caption from one editable data file (`captions.json`). Spec §9 Look and highlight.

Parallel-safe: yes (with T6, T7). Plan: .team/changes/0001-pantry-poc/plan.md (T8).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Looking at any named object shows name and caption.
- [ ] #2 Editing the JSON changes the text on reload.
- [ ] #3 Highlight shows the level (Look/Use/Grab).
<!-- AC:END -->
