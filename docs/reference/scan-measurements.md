# Photogrammetry scan measurements (TASK-1.29) - WIP

Status: partial. Method, alignment, room size and counter are done. Full feature table, layout diff and scan-as-visual verdict are still to do.

## Method
- Source: `references/photogrammetry/ply/pantry.ply` (1.8M pts, ~1 cm spacing) and the OBJ mesh (same frame). Scripts: `blender/scan/load.py`, `blender/scan/render_scan.py`.
- Raw frame is z-up. Floor sits at z=-1.29. Walls are rotated 29.58 degrees about z (normal-angle histogram peak).
- Transform: `references/photogrammetry/align.json` (4x4 raw to layout frame: x along window wall from the chevron wall, y up, z out from the window wall).

## Scale check (metric, factor 1.0)
- Table tops 0.79-0.81 m (expected ~0.75), counter top 0.79-0.81, window sill 0.59-0.65, floor to ceiling ~2.7 m. All plausible for metric. Door, fridge and tile checks still to do.

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

## Open items
- Door, pillar, mullion count, sink, cabinets, ceiling fixtures, floor tile.
- Perspective renders near the photo poses, layout.py diff, ASCII plan.
- Scan-as-visual verdict. Early view: coverage has holes and the interior is mostly empty floor.

Renders: `docs/reference/scan/plan-topdown-grid.png` (1 m grid, raw scan x/y, floor-cut at z=2 m), `docs/reference/scan/eye-window-wall.png`.
