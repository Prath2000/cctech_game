---
id: TASK-1.1
title: Project scaffold
status: To Do
assignee: []
created_date: '2026-11-05T10:22:00Z'
labels:
  - effort:S
dependencies: []
parent_task_id: TASK-1
priority: high
type: task
ordinal: 1100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Vite + TS + Three.js WebGPU (WebGL2 fallback) + Rapier, pnpm, fps counter, empty scene. `pnpm dev` is the one local command. Spec §6, §10.4.

Parallel-safe: yes (with T3). Parent: TASK-1. Plan: .team/changes/0001-pantry-poc/plan.md (T1).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `pnpm dev` serves a page that opens in Safari.
- [ ] #2 fps counter visible.
- [ ] #3 Renderer logs which backend (WebGPU/WebGL2) is active; a `?webgl=1` flag forces WebGL2.
<!-- AC:END -->
