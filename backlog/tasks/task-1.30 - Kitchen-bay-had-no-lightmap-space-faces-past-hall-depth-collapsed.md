---
id: TASK-1.30
title: Kitchen bay had no lightmap space (faces past hall depth collapsed)
status: Done
assignee: []
created_date: '2026-11-06T06:36:00Z'
labels:
  - bug
dependencies: []
parent_task_id: TASK-1
priority: high
ordinal: 3600
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
lightmap_uv._visible_faces only allowed z <= ROOM_D, so 10 meshes (bay walls, floor, ceiling, counter...) were flat and read black. Fixed; check_glb fails on it.
<!-- SECTION:NOTES:END -->
