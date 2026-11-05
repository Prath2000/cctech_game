---
id: TASK-1.27
title: 'Photo-match: PUSH vending machine missing brand details'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T11:36:00Z'
updated_date: '2026-11-05T12:02:00Z'
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
Photo 08 (1): PUSH text, green dispense flap, keypad tablet; shot has none. Fix blender/props/vending.py. Pose should back up ~1 m. See verify.md.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
WIP: tablet now has red header + 3x4 thumbnail grid, overlaps glass edge. PUSH/flap already in code. Left: verify shot (pose too close, pose worker), check:seating.

Build OK. Visual verify BLOCKED: game page fails to load (lightmap file names in public/lightmaps/on do not match src/lighting/baked.ts, other workers mid-change). Needs shot of vending-08-1 once lighting is stable.
<!-- SECTION:NOTES:END -->
