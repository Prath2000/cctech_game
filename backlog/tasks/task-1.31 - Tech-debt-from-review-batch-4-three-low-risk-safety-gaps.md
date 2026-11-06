---
id: TASK-1.31
title: 'Tech debt from review batch 4: three low-risk safety gaps'
status: To Do
assignee: []
created_date: '2026-11-06T08:41:00Z'
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
