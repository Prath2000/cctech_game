---
id: TASK-1.31
title: 'Tech debt from review batch 4: three low-risk safety gaps'
status: Done
assignee: []
created_date: '2026-11-06T08:41:00Z'
updated_date: '2026-11-06T09:20:00Z'
labels:
  - effort:S
dependencies: []
parent_task_id: TASK-1
priority: low
ordinal: 4600
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
All low severity, no player-visible effect today. (1) src/lighting/baked.ts ~148: LED panels glow even if the on/ bake is missing; tie the panel term to hasOn. (2) scripts/check_glb.py uv_collapsed: only flags a mesh when every primitive collapses, so a partly collapsed mesh passes; add a share threshold. (3) blender/bake_room.py:84: bay boost matches led_panel_10/11/12 by name; assert exactly 3 matched or use an extras flag.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done: check_glb area check (fails under 30% lightmap area), baked.ts panels dark with no on-bake, exactly-3 bay panels assert in bake_room.py (runs on next bake).
<!-- SECTION:NOTES:END -->
