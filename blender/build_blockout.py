"""Headless room blockout. Run: Blender -b --python-exit-code 1 -P blender/build_blockout.py
Coordinates below are GAME coords in metres (x east, y up, z south), see
docs/reference/pantry-reference-sheet.md. Blender is z-up, so we map
game (x, y, z) -> blender (x, -z, y); the glTF exporter's +Y up then restores game coords.
"""
import bpy, bmesh, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "models", "room_blockout.glb")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layout

bpy.ops.wm.read_factory_settings(use_empty=True)
mats = {}

def mat(name, color, alpha=1.0):
    if name in mats:
        return mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 0.8
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    mats[name] = m
    return m

GREY = lambda v: (v, v, v)
M_WALL, M_FLOOR, M_DARK = mat("grey_wall", GREY(0.6)), mat("grey_floor", GREY(0.45)), mat("grey_dark", GREY(0.15))
M_LIGHT, M_GLASS = mat("grey_light", GREY(0.8)), mat("glass", (0.6, 0.7, 0.8), 0.25)

def box(name, x0, x1, y0, y1, z0, z1, m=M_WALL, static=1, collider=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = o.data.name = name
    o.scale = (x1 - x0, z1 - z0, y1 - y0)
    o.location = ((x0 + x1) / 2, -(z0 + z1) / 2, (y0 + y1) / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    o["static"] = static
    if collider:
        o["collider"] = collider
    if static:
        add_lightmap_uv(o)
    return o

def add_lightmap_uv(o):
    me = o.data
    me.uv_layers[0].name = "UVMap"
    lm = me.uv_layers.new(name="lightmap")
    me.uv_layers.active = lm
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    me.uv_layers.active = me.uv_layers["UVMap"]

L = layout
W, D, H, T = L.ROOM_W, L.ROOM_D, L.ROOM_H, L.WALL_T
# shell
box("floor", 0, W, -0.1, 0, 0, D, M_FLOOR)
box("ceiling", 0, W, H, H + 0.1, 0, D, M_LIGHT, collider="none")
box("wall_west", -T, 0, 0, H, -T, D + T)
box("wall_east", W, W + T, 0, H, -T, D + T)
box("wall_south", 0, W, 0, H, D, D + T)

# window wall (north, z=0): black mullions + glass
mull, fh, N = L.MULLION_W, L.WINDOW_FRAME_H, L.WINDOW_PANELS
bay = (W - mull) / N
box("window_frame_bottom", 0, W, 0, fh, -0.1, 0.1, M_DARK)
box("window_frame_top", 0, W, H - fh, H, -0.1, 0.1, M_DARK)
for i in range(N + 1):
    x = i * bay
    box(f"window_mullion_{i:02d}", x, x + mull, 0, H, -0.1, 0.1, M_DARK)
for i in range(N):
    x0 = i * bay + mull
    box(f"window_glass_{i:02d}", x0, x0 + bay - mull, fh, H - fh, -0.02, 0.02, M_GLASS)
box("window_sill", L.SILL_X0, W, 0, L.SILL_H, 0.1, 0.1 + L.SILL_D, M_DARK)

# west wall: orange chevron wall + double door
box("chevron_wall", 0, 0.12, 0, H, L.CHEVRON_Z0, L.CHEVRON_Z1, M_LIGHT)
M_CHEV = mat("grey_chev", GREY(0.35))
box("chevron_01", 0.12, 0.13, 0.95, H - 0.7, L.CHEVRON_Z0 + 0.1, L.CHEVRON_Z1 - 0.1, M_CHEV, collider="none")
box("chevron_02", 0.12, 0.13, 0.4, 0.9, L.CHEVRON_Z0 + 0.1, L.CHEVRON_Z1 - 0.1, M_CHEV, collider="none")
dz0, dz1, pad = L.DOOR_Z0, L.DOOR_Z0 + L.DOOR_W, L.DOOR_FRAME_PAD
box("door_frame", 0, 0.1, 0, L.DOOR_H + 0.1, dz0 - pad, dz1 + pad, M_DARK, collider="none")
box("door_leaf_a", 0.1, 0.15, 0, L.DOOR_H, dz0, (dz0 + dz1) / 2, M_GLASS, collider="none")
box("door_leaf_b", 0.1, 0.15, 0, L.DOOR_H, (dz0 + dz1) / 2, dz1, M_GLASS, collider="none")

# pillar, counter, fridge
ps, px, pz = L.PILLAR_SIZE / 2, L.PILLAR_CX, L.PILLAR_CZ
box("pillar_01", px - ps, px + ps, 0, H, pz - ps, pz + ps, M_LIGHT)
c = L.COUNTER
box("counter", c["x0"], W, 0, c["height"], c["z0"], c["z0"] + c["length"], M_DARK)
wc = L.WALL_CAB
box("wall_cabinets", W - wc["depth"], W, wc["y0"], wc["y1"], wc["z0"], wc["z1"], M_LIGHT)
f = L.FRIDGE
box("fridge_niche", f["x0"] - 0.05, f["x0"] + f["w"] + 0.05, 0, H, 0.0, L.FRIDGE_NICHE_D, M_WALL, collider="none")  # visual back panel
box("fridge", f["x0"], f["x0"] + f["w"], 0, f["h"], f["z0"], f["z0"] + f["d"], M_LIGHT)

# west-wall props
v = L.VENDING
box("vending_machine", 0, v["d"], 0, v["h"], v["z0"], v["z0"] + v["w"], M_DARK)
k = L.COOLERS
for i in range(k["n"]):
    z = k["z0"] + i * k["each_w"]
    box(f"cooler_{i + 1:02d}", 0, k["d"], 0, k["h"], z, z + k["each_w"], M_LIGHT)

# tables (top at TABLE_H)
TL, TW, TH = L.TABLE_L, L.TABLE_W, L.TABLE_H
for n, (x0, zc) in enumerate(L.table_positions(), 1):
    t = f"table_{n:02d}"
    box(t, x0, x0 + TL, TH - 0.05, TH, zc - TW / 2, zc + TW / 2, M_LIGHT)
    for lx in (x0 + 0.05, x0 + TL - 0.07):
        for lz in (zc - TW / 2 + 0.04, zc + TW / 2 - 0.07):
            box(f"{t}_leg_{'a' if lx < x0 + TL / 2 else 'b'}{'1' if lz < zc else '2'}", lx, lx + 0.02, 0, TH - 0.05, lz, lz + 0.03, M_DARK, collider="none")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_yup=True,
                          export_extras=True, export_apply=True, export_texcoords=True)
print("exported", OUT, len(bpy.data.objects), "objects")
