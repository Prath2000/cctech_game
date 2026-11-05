---
id: TASK-1.20
title: 'Review fixes batch 3: spawn caps, fill hitch, audio panners'
status: Done
assignee:
  - '@claude'
created_date: '2026-11-05T11:22:00Z'
updated_date: '2026-11-05T11:27:00Z'
labels:
  - effort:S
dependencies: []
parent_task_id: TASK-1
priority: high
type: task
ordinal: 2350
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
From batch-3 review: 1) pantry/index.ts:150-160 coffee mug spawn unbounded -> cap/reuse. 2) seating.ts:340 glass grab-able mid-fill -> interact look until filled. 3) seating.ts:384/54 water material compiles at first fill (hitch) -> warm up at init / compileAsync. 4) audio.ts:155-163 new HRTF panner per play -> equalpower or pool. 5) audio.ts:94-121 linvel alloc per item per frame, skip sleeping bodies. 6) audio.ts:134-138 retry other format on decode failure. 7) pantry/hinge.ts:60 overlap test uses previous pose; door flip-flop; sit() without door check.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Repeated coffee/vending/cooler use never grows bodies beyond a cap (check script)
- [x] #2 No new material/pipeline compiles at interaction time (first-use hitch gone)
- [x] #3 Audio one-shots reuse panners; decode falls back to the other format
- [x] #4 Hinge doors never flip-flop or clip the player
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Mug spawn capped at 6 (recycle oldest); glass non-grabbable until filled; water material warmed at init; audio equalpower panners, decode fallback, sleeping bodies skipped; hinge tests next pose, holds and reverses once; sit() blocked by kinematic door. All checks pass.
<!-- SECTION:NOTES:END -->
