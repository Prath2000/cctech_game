---
id: TASK-1.16
title: Audio
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-05T11:14:00Z'
labels:
  - effort:S
dependencies:
  - TASK-1.11
  - TASK-1.12
parent_task_id: TASK-1
priority: low
type: feature
ordinal: 2600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CC0 sounds: coffee pour, microwave ding, fridge, vending drop, footsteps, ambience. Minimal mute/pause setting. Spec §3, §11.

Parallel-safe: yes (with T14, T15). Plan: .team/changes/0001-pantry-poc/plan.md (T16).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each Use item with a sound spec plays it.
- [x] #2 Mute toggle works.
- [x] #3 Licences recorded.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Sound library prepared in public/audio (manifest.json)

Audio engine extended in src/audio/audio.ts (master gain, mute/volume persisted, HRTF positional, ambience, footsteps, set-down clinks); settings overlay src/audio/settings.ts (Esc, M mutes); wiring in src/audio/extras.ts. Fridge hum added in pantry. playSound('switch_on') exported for TASK-1.13. Verified with pnpm check:audio.
<!-- SECTION:NOTES:END -->
