---
id: TASK-1.23
title: 'Photo-match: coffee station props wrong (Tata Bistro, LG, B''ONE)'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T11:36:00Z'
updated_date: '2026-11-05T11:54:00Z'
labels:
  - effort:S
dependencies: []
parent_task_id: TASK-1
priority: high
type: bug
ordinal: 2550
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Photo 06 (1): Tata Bistro machine should have a sloped front, large angled TATA BISTRO touchscreen, drip tray; LG microwave sits on left shelf; B'ONE panel and notice sheet missing. Shot is a plain black box. Fix blender/props/*.py and layout.py. See verify.md.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done: Tata Bistro rebuilt (brew deck, tall right block, angled steel-rimmed screen, drip tray grille), microwave moved left, B'ONE board + notice sheet decals, granite side panel. Left: label plate overlaps screen, window view above microwave, steel ribbed sheet, re-verify with shot.

Label plate moved off screen. Verification blocked: game fails to load in check:shot/check:pantry (page error Event, 30s timeout) after concurrent rebuilds; not diagnosed. Still: re-run shot + check:pantry, window view, steel sheet.
<!-- SECTION:NOTES:END -->
