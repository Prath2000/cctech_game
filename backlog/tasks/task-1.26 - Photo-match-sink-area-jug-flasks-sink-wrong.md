---
id: TASK-1.26
title: 'Photo-match: sink area jug/flasks/sink wrong'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T11:36:00Z'
updated_date: '2026-11-06T10:10:00Z'
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
Photo 07: jug narrower, translucent, near wall; steel flasks; stainless sink basin, soap dispenser, cloths. Shot has oversized jug in front, blocky cylinders, flat grey panels. Fix props + materials.py steel + layout.py sink. See verify.md.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done: jug slimmer/translucent, flasks reordered, soap dispenser cylinder, red cloth, yellow cloth, soap tray + sponge. Left: nudge jug z to ~2.9, flask positions vs socket plate, compare sink shot.

Pass 3 (119434b), one scout look; see verify.md. Sink basin matte despite the probe change. Pink bottle moved in room.glb but not visually confirmed; soap bottles could not be judged. Ratio 0.83.

Pass 4 (12ca175): sink steel brighter and shinier, mats darkened, sink ratio 0.81. Basin still not confirmed as reading as steel; see verify.md.
<!-- SECTION:NOTES:END -->
