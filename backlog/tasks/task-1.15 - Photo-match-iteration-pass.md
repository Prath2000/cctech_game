---
id: TASK-1.15
title: Photo-match iteration pass
status: In Progress
assignee: []
created_date: '2026-11-05T10:22:00Z'
updated_date: '2026-11-06T09:50:00Z'
labels:
  - effort:L
dependencies:
  - TASK-1.10
  - TASK-1.14
parent_task_id: TASK-1
priority: medium
type: task
ordinal: 2500
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Screenshot from each photo's camera spot, helper compares to photo against the fixed checklist and lists major/minor differences. Fix majors and repeat. Spec §10b.6, §10.1.

Parallel-safe: no. Plan: .team/changes/0001-pantry-poc/plan.md (T15).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Comparison report for every photo spot.
- [ ] #2 No major differences remain.
- [ ] #3 User gives the final verdict.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Pass 3 report for all 8 spots in .team/changes/0001-pantry-poc/verify.md. Majors remain, so AC #2 and #3 stay open.
<!-- SECTION:NOTES:END -->
