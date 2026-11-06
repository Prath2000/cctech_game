---
id: TASK-1.28
title: 'Photo-match: INNOVATION chevrons, chairs, strip view'
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-05T11:36:00Z'
updated_date: '2026-11-06T09:50:00Z'
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
Photos 08 (3) and 08 (2): chevrons too small, chairs sparse, window-side strip layout and window view (cars/city) wrong. Fix layout.py, materials.py, window backdrop, camera-poses.json strip-08-2. See verify.md.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
WIP: clean orange chevron PNGs (scripts/make_chevrons.py), window_backdrop plane (scripts/make_backdrop.py, materials.py), 6 chairs/table, sill full length. Left: rebuild verify, shots, check:seating, no strip partition added.

Build OK (room.glb 302 objects). Visual verify BLOCKED by same lighting load failure; re-run check:shot cafeteria-08-3 / strip-08-2 and check:seating after lighting settles. Strip partition not added.

Pass 3 (119434b), one scout look; see verify.md. The old load-failure block is gone. Chairs passed. INNOVATION text and chevrons could not be judged because strip framing differs from the photo. check:seating passed earlier but was not rerun on 119434b. Cafeteria ratio 1.16 misses by 0.01; about 2 tables vs about 4 in the photo.
<!-- SECTION:NOTES:END -->
