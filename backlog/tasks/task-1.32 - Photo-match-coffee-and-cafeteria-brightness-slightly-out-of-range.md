---
id: TASK-1.32
title: 'Photo-match: coffee and cafeteria brightness slightly out of range'
status: In Progress
assignee: []
created_date: '2026-11-06T09:50:00Z'
updated_date: '2026-11-06T10:28:00Z'
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
- [x] #2 All other check:match ratios stay in range
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Pass 4 (12ca175): coffee 0.77, cafeteria 1.16. Fridge 1.18 is also over range, tracked in TASK-1.25.

ec25efa: coffee shows 0.80 but is 101/127 = 0.795, under the 0.8 target, so reopened (a2e7d0d marked it Done on the rounded number). Cafeteria 1.14. granite_black tint went from #2d2d31 to #85858b, a large change: needs an independent look at the counter against the photo. Full checks not re-run on this model yet.

2026-11-06: counter and sill now share one texture, tint #2d2d31, contrast 1.8 (room.glb 8.2 -> 7.0 MB). Checks pass. Scout: at this tint the coffee-shot counter still reads too light, the sink one slightly too dark, flecks fainter than the photo; so the coffee-shot gap is not the tint (possibly glare or baked light, not confirmed). check:match coffee 0.77 (miss), sink 0.81, cafeteria 1.14. AC #1 left unchecked: coffee needs a bake or the user's call.
<!-- SECTION:NOTES:END -->
