# Photogrammetry scan measurements (TASK-1.29)

Status: done. All values are in the layout frame (metres): x along the window wall from the chevron wall, y up, z out from the window wall. Measured on the 1.8M-point cloud; the scan has holes (ceiling centre, bay, floor patches), so every number is +-0.1 m unless marked.

## Method
- Source: `references/photogrammetry/ply/pantry.ply` (1.8M pts, ~1 cm spacing) and the OBJ mesh (same frame). Scripts: `blender/scan/load.py`, `blender/scan/render_scan.py`.
- Raw frame is z-up. Floor sits at z=-1.29. Walls are rotated 29.58 degrees about z (normal-angle histogram peak).
- Transform: `references/photogrammetry/align.json` (4x4 raw to layout frame: x along window wall from the chevron wall, y up, z out from the window wall).

## Scale check (metric, factor 1.0)
- Table tops 0.79-0.81 m (expected ~0.75), counter top 0.79-0.81, window sill 0.59-0.65, floor to ceiling ~2.7 m. All plausible for metric.
- Door: opening header at y=2.1 (standard 2.0-2.1), so scale is metric. Door width 1.55 (two ~0.78 leaves, plausible).
- Fridge: dense top at ~1.35 (see table), a small under-counter/mid-size unit; no real-world model number known, so it is a weak check only.
- Floor tile: not measurable. No repeating seam in the floor colour (autocorrelation shows no peak, 28% of floor cells empty, lighting dominates the texture).
- Verdict: scale 1.0 confirmed by door header + tables + sill + ceiling. Orientation: window wall z=-0.05..0, chevron wall x=-0.05..0, handedness matches `layout.py`.

## Room (layout frame)
| feature | scan | layout.py (guess) |
|---|---|---|
| main hall | 8.7 (x) by 7.35 (z) | 12.0 by 7.5 |
| kitchenette bay (SE) | x 6.3-8.7, z 7.35-9.95 | none |
| ceiling | ~2.7 m (2.4-2.7 spread, no clean plane) | 3.2 |
| window wall | at x_s=-5.85, the full 8.7 m, sill 0.61, glass head ~2.1-2.4 | 12 m, sill 0.9 |
| chevron "INNOVATION" wall | on x=0 (window-wall end), with a glass door at x_l ~0.3-1.3 (a gap in the wall) | west wall, z 1.5-3.5 |
| tables | 2 white tables (top 0.79-0.80) along the window wall, ~3.2 by 1.2 m: z 0.5-3.7 at x 0-1.5, and z 0.4-3.7 at x 5.7-6.9. The middle of the hall is empty floor. | 3x3 grid |
| counter | x 6.6-7.3, z 7.95-9.8 (1.85 m long, ~0.7 deep), top 0.80, plus a 0.5 m return along the east end (x_l 6.3-8.3, z 9.4-9.95) | east wall, 3.2 long |
| vending, coolers, circuit mural | on the partition at z=7.35, x 0.5-1.5 | west wall |
| fridge | grey, ~1.6 m tall, x ~7.0-7.7 near z 7.35 | x 10.95-11.65 |

## Features filled in this pass (layout frame)
| item | scan result | layout.py now |
|---|---|---|
| chevron graphic | orange on the x=0 wall, z 2.5-4.7, y 1.0-2.35 (2.2 wide) | z 1.5-3.5 |
| glass door | in the x=0 wall at z 4.8-6.4 (1.55 wide), head y=2.1, bright frame at both jambs; wall above up to 2.4 | z0 4.1, w 1.3, h 2.1 |
| window mullions | 10 dark vertical lines at x = 0.35 + 0.9k (k=0..9; x 3.05 hidden by a hole but fits the pitch), each ~0.1 wide, so **9 panels** of ~0.8 clear | 12 panels |
| pillar | full-height column, floor to ceiling, x 6.25-6.70 (0.45) by z 3.25-4.15 (0.9), beige, in the hall (not on the window strip) | 0.6 square at (9.9, 2.35) |
| hall/strip | no separate "window strip": tables start at z 0.4 right behind the glass | STRIP_W 2.75 |
| ceiling | 2.4 at x<2, 2.5-2.7 over x 4.5-7; no clean plane. Use 2.65. | 3.2 |
| east wall | x 8.55-8.7; a low dark unit (0.4 high, 0.3 deep) along it at z 7.06-9.27 | none |
| bay back wall | solid wall to the ceiling at x=6.7, z 8.0-10.0 (counter against it, facing +x) | none |
| fridge | x 6.9-7.35, z 7.0-7.44, grey, top ~1.35 (front face partly missing, height uncertain) | 0.7x0.7x1.7 at window-strip end |
| sink | not measurable (bay interior has no usable points; no basin visible) | on counter |
| wall cabinets | not measurable (no protruding box at y 1.0-2.4 beyond the x=6.7 wall; holes in that zone) | z 2.6-4.4 |
| ceiling fixtures | not measurable (ceiling centre is not scanned; only edge cells at x<2 and x 4.5-7 exist, no lights seen) | none |
| floor tile | not measurable (see Scale check) | none |

The earlier table (above) wrote the door as "x_l 0.3-1.3"; the re-measurement above in the layout frame supersedes it. Counter: re-check puts the back wall at x=6.7, front at x~7.4, z 7.4-9.5; the earlier z 7.95-9.8 is kept in the diff since the bay is full of holes (treat +-0.3).

## ASCII plan (layout frame, not to scale vertically; 1 char ~ 0.35 m)
```
 x=0                                                       x=8.7
 z=0  +=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=+  window wall (9 panels, sill 0.61)
      |###                                      ####     |
      |CHV  [table 0-1.5 x z0.5-3.7]  (empty   |table|   |  table 5.7-6.9 x z0.4-3.7
      |###                             floor)   |PIL |   |  PIL = pillar 6.25-6.7 x z3.25-4.15
 z=3.5|chevron wall z2.5-4.7                     ####     |
      |                                                   |
 z=4.8|DOOR (glass, to 6.4)                               |
 z=6.4|                                                   |
      |    open hall x0-8.7 by z0-7.35                    |
 z=7.35 +VEND+COOL=== partition (x -0.2-2.5, 4.3-7.4; scan hole 2.5-4.3 closed; bay opening 7.4-8.2) +
      (bay) x6.7-8.7, z7.35-10.0:                    |FR| |
                              wall x=6.7 |counter x6.7-7.4,z7.4-9.5|  low unit at east wall
 z=10 ------------------------ ----------------------------
```

## Proposed `layout.py` diff (NOT applied; the bake reads layout at start of each state)
```diff
-ROOM_W = 12.0
-ROOM_D = 7.5
-ROOM_H = 3.2
+ROOM_W = 8.7    # scan: window wall length [measured]
+ROOM_D = 7.35   # hall depth to partition [measured]
+ROOM_H = 2.65   # ceiling 2.4-2.7 [measured, uneven]
+BAY = dict(x0=6.7, x1=8.7, z0=ROOM_D, z1=10.0)  # kitchenette bay, new [measured, holes]
-WINDOW_PANELS = 12
-MULLION_W = 0.12
+WINDOW_PANELS = 9       # mullion lines at x = 0.35 + 0.9k [measured]
+MULLION_W = 0.10
+MULLION_X0, MULLION_PITCH = 0.35, 0.9
-SILL_H, SILL_D = 0.9, 0.45
+SILL_H, SILL_D = 0.61, 0.45   # depth unchanged, not measured
-STRIP_W = 2.75
+STRIP_W = 0.0           # no strip: tables sit behind the glass
-PILLAR_SIZE = 0.6
-PILLAR_CX = 9.9
-PILLAR_CZ = STRIP_W - 0.4
+PILLAR = dict(x0=6.25, z0=3.25, w=0.45, d=0.9)  # full height [measured]
-CHEVRON_Z0, CHEVRON_Z1 = 1.5, 3.5
-DOOR_Z0, DOOR_W, DOOR_H = 4.1, 1.3, 2.1
+CHEVRON_Z0, CHEVRON_Z1 = 2.5, 4.7
+DOOR_Z0, DOOR_W, DOOR_H = 4.8, 1.55, 2.1
-COUNTER = dict(x0=11.4, z0=2.0, length=3.2, depth=0.6, height=0.9)
-WALL_CAB = dict(depth=0.35, y0=1.45, y1=2.15, z0=2.6, z1=4.4)
-FRIDGE = dict(x0=ROOM_W - 1.05, z0=0.05, w=0.7, d=0.7, h=1.7)
+COUNTER = dict(x0=6.7, z0=7.95, length=1.85, depth=0.7, height=0.8)  # against wall x=6.7 [medium]
+WALL_CAB = None   # not measurable: keep removed or guess from photos
+FRIDGE = dict(x0=6.9, z0=7.0, w=0.45, d=0.45, h=1.35)  # [low: top only]
-VENDING = dict(z0=5.6, ...)
+VENDING = dict(x0=0.5, z0=ROOM_D - 0.8, ...)  # on the partition, x 0.5-1.5 [medium]
-SEAT_ROWS, SEAT_COLS = 3, 3
-SEAT_ORIGIN, SEAT_SPACING, TABLE_L, TABLE_W = ..., 1.8, 0.8
+TABLES = [dict(x0=0.0, z0=0.5), dict(x0=5.7, z0=0.4)]  # 2 tables, long axis along z
+TABLE_L, TABLE_W, TABLE_H = 3.2, 1.2, 0.80
-SPAWN = (1.0, 0.0, 3.3, -90)
+SPAWN = (3.5, 0.0, 5.0, -90)   # old spot is now inside a table
```
`table_positions()` and the builders that read SEAT_* / PILLAR_SIZE / STRIP_W must change with it (follow-up task). Chair count per table is not measurable (chairs are scarce/ghosted in the scan).

## Scan-as-visual: NO-GO
Previews: `docs/reference/scan/persp-window-wall.png` (from layout x=5.6 z=4.7, eye 1.6, looking at the windows) and `docs/reference/scan/persp-chevron-door.png` (from x=5.6 z=5.35 looking at the chevron wall and door). Also `plan-topdown-grid.png`, `eye-window-wall.png`.
- Verdict: do not use the raw scan mesh as the visual base. Use it as a measurement reference only.
- Why: large holes (rough view check: ~35-60% of frame, mostly ceiling and upper walls, plus ragged floor edges); the window glass is ghosted (outdoor facades bleed together); floor is smeared by baked shadows; the baked texture also fights our lightmap/on-off lighting states; 306k verts and a 4096 texture add load for a mostly empty room.
- Partial use that is fine: crop the chevron wall + door texture (sharp, recognisable) as a decal/texture on a modelled wall.
- Re-evaluate only if a cleaned, hole-filled mesh is produced (retopo + texture de-lighting), which is out of scope for the POC.

Renders: `docs/reference/scan/plan-topdown-grid.png` (1 m grid, raw scan x/y, floor-cut at z=2 m), `docs/reference/scan/eye-window-wall.png`.
