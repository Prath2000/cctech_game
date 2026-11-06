"""Single source of truth for room dimensions and anchors (TASK-1.17).
GAME coords in metres: x along the window wall from the chevron wall (x=0), y up, z out from the
window wall (z=0). Every blender builder must import this.
ALL NUMBERS COME FROM THE POINT-CLOUD SCAN (references/photogrammetry/ply/pantry.ply, aligned with
references/photogrammetry/align.json; tables in docs/reference/scan-measurements.md). The scan is the
source of truth for layout; video and photos only decide how things look. Items the scan could not
measure are marked [not measured]. Tweak here, then run `pnpm build:blockout` and re-check poses
in src/data/camera-poses.json.
Outline (hall + kitchenette bay): (0,0) (8.7,0) (8.7,10) (6.7,10) (6.7,7.35) (0,7.35).
"""

# --- shell ---------------------------------------------------------------
ROOM_W = 8.7    # window-wall length [scan]
ROOM_D = 7.35   # hall depth, window wall -> partition [scan]
ROOM_H = 2.65   # ceiling, scan spread 2.4-2.7 [scan, uneven]
WALL_T = 0.2    # wall thickness, built outside the interior [assumed]
BAY = dict(x0=6.7, x1=8.7, z0=ROOM_D, z1=10.0)  # kitchenette bay behind the partition [scan, holes inside]
# partition at z=ROOM_D: scan wall points at x 0-2.5 and 4.3-7.4 (z 7.23-7.31). The middle (2.5-4.3) has 0 points
# at any height and no floor beyond (hall floor is also missing nearby), so it is a scan hole, closed with wall.
# The bay opens at x 7.4-8.7.
PARTITION_GAP = (2.5, 4.3)   # scan hole, closed with wall
BAY_OPEN_X0 = 7.4            # partition ends here, walkable opening up to the east wall [scan: wall ends ~7.4-7.6]

# --- window wall (z=0) -----------------------------------------------------
WINDOW_PANELS = 9     # mullion lines at x = 0.35 + 0.9k, k=0..9 [scan]
MULLION_W = 0.10
MULLION_X0, MULLION_PITCH = 0.35, 0.9
WINDOW_FRAME_H = 0.08  # top/bottom black frame height [assumed]
SILL_X0 = 0.0
SILL_H, SILL_D = 0.61, 0.30   # height [scan]; depth [not measured], 0.3 so it clears the tables at z 0.4

# --- pillar (full height, in the hall; no window strip) ---------------------
STRIP_W = 0.0
PILLAR = dict(x0=6.25, z0=3.25, w=0.45, d=0.9)   # [scan]

# --- west wall (x=0): chevron graphic + glass door -----------------------
CHEVRON_Z0, CHEVRON_Z1 = 2.5, 4.7   # y 1.0-2.35 [scan]
CHEVRON_Y0, CHEVRON_Y1 = 1.0, 2.35
DOOR_Z0, DOOR_W, DOOR_H = 4.8, 1.55, 2.1   # [scan]
DOOR_FRAME_PAD = 0.05

# --- kitchenette bay: counter against the wall at x=6.7, facing +x ---------
COUNTER = dict(x0=6.7, z0=7.95, length=1.85, depth=0.7, height=0.8)   # [scan, medium]
# wall cabinets (photo-match, [not measured] in the scan): 0.35 deep on the x=6.7 wall above the counter, y 1.45-2.38.
# Right of the microwave shelf: z 7.95-9.3 holds three grey doors over an open mug shelf; z 9.3-9.8 is the microwave shelf above the sink.
WALL_CAB = dict(x0=6.7, depth=0.35, z0=7.95, z1=9.3, y0=1.45, y1=2.38, mw_z0=9.3, mw_z1=9.8, mw_y=1.226)
FRIDGE = dict(x0=6.9, z0=6.9, w=0.45, d=0.44, h=1.35)   # footprint x 6.9-7.35, z 6.9-7.34 (scan said 7.0-7.44, overlapped the partition), top ~1.35 [scan, low: front face missing]; z0 moved 7.0 -> 6.9 so it clears the partition (z 7.35)
LOW_UNIT = dict(x0=8.4, x1=8.7, z0=7.06, z1=9.27, h=0.4)   # dark unit on the east wall [scan]

# --- partition (hall side): vending + coolers + circuit mural, x 0.5-1.5 --
VENDING = dict(x0=0.5, w=0.7, d=0.8, h=1.85)           # [scan x range; size assumed]
COOLERS = dict(x0=1.4, each_w=0.4, n=2, d=0.35, h=1.465)  # [scan x range 1.2-1.7; size assumed] two Voltas units at pitch 0.4 (x centres 1.6, 2.0), clear of the vending machine
MURAL = dict(x0=1.3, x1=2.5, y0=1.5, y1=2.36)  # circuit-board mural on the partition, above the coolers

# --- hall: 2 white tables, long axis along z --------------------------------
TABLE_H = 0.80   # [scan]
# footprints [scan]: x0, x1, z0, z1. Table 2 is cut at z 3.2 so it clears the pillar (x 6.25-6.70, z 3.25-4.15)
TABLES = [dict(x0=0.0, x1=1.5, z0=0.5, z1=3.7), dict(x0=5.7, x1=6.9, z0=0.4, z1=3.2)]

# --- player ------------------------------------------------------------------
SPAWN = (3.5, 0.0, 5.0, -90)  # feet x,y,z, yaw deg (-90 faces +x), clear floor


def table_footprints():
    """[(xc, zc, x_size, z_size)] per table."""
    return [((t["x0"] + t["x1"]) / 2, (t["z0"] + t["z1"]) / 2, t["x1"] - t["x0"], t["z1"] - t["z0"]) for t in TABLES]
