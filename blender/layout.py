"""Single source of truth for room dimensions and anchors (TASK-1.17).
GAME coords in metres: x east, y up, z south. Window wall is z=0 (north); the
interior spans x 0..ROOM_W, z 0..ROOM_D. Every blender builder must import this.
All measurements come from video, so confidence is LOW: tweak here, then run
`pnpm build:blockout` and re-check poses in src/data/camera-poses.json.
"""

# --- shell ---------------------------------------------------------------
ROOM_W = 12.0   # window-wall length. Video estimate 11-13 m [low]
ROOM_D = 7.5    # window -> back wall. Video estimate 6.5-9 m [low]
ROOM_H = 3.2    # ceiling. Video estimate ~3.2 m (door 2.1 m + header) [medium]
WALL_T = 0.2    # wall thickness, built outside the interior [assumed]

# --- window wall (z=0) -----------------------------------------------------
WINDOW_PANELS = 12    # video shows ~9-12 panels [low]
MULLION_W = 0.12      # black mullion width [assumed from photos]
WINDOW_FRAME_H = 0.08  # top/bottom black frame height [assumed]
SILL_X0 = 8.0         # granite sill runs from here to the east wall [reference sheet 08 (2)]
SILL_H, SILL_D = 0.9, 0.45  # sill height/depth [sheet]

# --- window strip + pillar -------------------------------------------------
STRIP_W = 2.75        # strip between windows and seating hall, 2.5-3 m [low]
PILLAR_SIZE = 0.6     # white square column [photo 08 (2), medium]
PILLAR_CX = 9.9       # near the fridge end of the strip [low]
PILLAR_CZ = STRIP_W - 0.4  # on the strip/hall boundary

# --- west wall: chevron wall + black glass double door --------------------
CHEVRON_Z0, CHEVRON_Z1 = 1.5, 3.5   # orange chevron graphics span [photo 08 (3), low position]
DOOR_Z0, DOOR_W, DOOR_H = 4.1, 1.3, 2.1   # black glass double door [low position]
DOOR_FRAME_PAD = 0.05

# --- east wall: kitchenette counter (position NOT seen anywhere: guess) ----
COUNTER = dict(x0=11.4, z0=2.0, length=3.2, depth=0.6, height=0.9)  # sheet proposal scaled; x1=ROOM_W
WALL_CAB = dict(depth=0.35, y0=1.45, y1=2.15, z0=2.6, z1=4.4)       # above sink, sheet [low]
FRIDGE = dict(x0=ROOM_W - 1.05, z0=0.05, w=0.7, d=0.7, h=1.7)       # LG fridge, window-strip east end [photo 08 (2), medium]
FRIDGE_NICHE_D = 0.8  # visual back panel depth

# --- west wall: vending + coolers (sheet: near the door) -------------------
VENDING = dict(z0=5.6, w=0.85, d=0.8, h=1.85)  # photo 08 (1) [low position]
COOLERS = dict(z0=6.5, each_w=0.3, n=2, d=0.35, h=1.45)  # photo 08 [low position]

# --- seating hall: long white tables ---------------------------------------
SEAT_ROWS, SEAT_COLS = 3, 3   # video: ~3 rows of 2-3 long tables [low]
SEAT_ORIGIN = (2.2, 3.3)      # (x0 of first table, z centre of first row)
SEAT_SPACING = (2.3, 1.6)     # (x pitch between tables, z pitch between rows)
TABLE_L, TABLE_W, TABLE_H = 1.8, 0.8, 0.75  # table top size/height [assumed]
CHAIRS_PER_TABLE = 4          # video [low]

# --- player ------------------------------------------------------------------
SPAWN = (1.0, 0.0, 3.3, -90)  # feet x,y,z, yaw deg (-90 faces +x, into the hall)


def table_positions():
    """[(x0, zc)] for every table, row-major."""
    return [(SEAT_ORIGIN[0] + c * SEAT_SPACING[0], SEAT_ORIGIN[1] + r * SEAT_SPACING[1])
            for r in range(SEAT_ROWS) for c in range(SEAT_COLS)]
