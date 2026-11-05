"""Headless room blockout. Run: Blender -b --python-exit-code 1 -P blender/build_blockout.py
Coordinates below are GAME coords in metres (x east, y up, z south), see
docs/reference/pantry-reference-sheet.md. Blender is z-up, so we map
game (x, y, z) -> blender (x, -z, y); the glTF exporter's +Y up then restores game coords.
"""
import bpy, bmesh, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "models", "room_blockout.glb")
W, D, H = 8.0, 6.0, 3.0

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

T = 0.2  # wall thickness (outside the 8x6 interior)
# shell
box("floor", 0, W, -0.1, 0, 0, D, M_FLOOR)
box("ceiling", 0, W, H, H + 0.1, 0, D, M_LIGHT, collider="none")
box("wall_west", -T, 0, 0, H, -T, D + T)
box("wall_east", W, W + T, 0, H, -T, D + T)
box("wall_south", 0, W, 0, H, D, D + T)

# window wall (north, z=0): 9 bays, black mullions + glass
mull = 0.12
bay = (W - mull) / 9
box("window_frame_bottom", 0, W, 0, 0.08, -0.1, 0.1, M_DARK)
box("window_frame_top", 0, W, H - 0.08, H, -0.1, 0.1, M_DARK)
for i in range(10):
    x = i * bay
    box(f"window_mullion_{i:02d}", x, x + mull, 0, H, -0.1, 0.1, M_DARK)
for i in range(9):
    x0 = i * bay + mull
    box(f"window_glass_{i:02d}", x0, x0 + bay - mull, 0.08, H - 0.08, -0.02, 0.02, M_GLASS)
box("window_sill", 4.5, W, 0, 0.9, 0.1, 0.55, M_DARK)

# west wall: orange chevron wall + double door (z 3.2-4.4)
box("chevron_wall", 0, 0.12, 0, H, 1.2, 2.8, M_LIGHT)
box("chevron_01", 0.12, 0.13, 0.95, 3.0 - 0.7, 1.3, 2.7, mat("grey_chev", GREY(0.35)), collider="none")
box("chevron_02", 0.12, 0.13, 0.4, 0.9, 1.3, 2.7, mat("grey_chev", GREY(0.35)), collider="none")
box("door_frame", 0, 0.1, 0, 2.2, 3.15, 4.45, M_DARK, collider="none")
box("door_leaf_a", 0.1, 0.15, 0, 2.1, 3.2, 3.8, M_GLASS, collider="none")
box("door_leaf_b", 0.1, 0.15, 0, 2.1, 3.8, 4.4, M_GLASS, collider="none")

# pillar, counter, fridge
box("pillar_01", 5.6, 6.2, 0, H, 1.9, 2.5, M_LIGHT)
box("counter", 7.4, 8.0, 0, 0.9, 1.4, 4.4, M_DARK)
box("wall_cabinets", 7.65, 8.0, 1.45, 2.15, 2.0, 3.8, M_LIGHT)
box("fridge_niche", 6.9, 7.7, 0, H, 0.0, 0.8, M_WALL, collider="none")  # visual back panel
box("fridge", 6.95, 7.65, 0, 1.7, 0.05, 0.75, M_LIGHT)

# west-wall props
box("vending_machine", 0, 0.8, 0, 1.85, 4.55, 5.4, M_DARK)
box("cooler_01", 0, 0.35, 0, 1.45, 5.42, 5.71, M_LIGHT)
box("cooler_02", 0, 0.35, 0, 1.45, 5.71, 6.0, M_LIGHT)

# tables: 3 rows x 2 tables (1.5 x 0.75, top 0.75 m)
n = 1
for zc in (1.5, 3.5, 5.0):
    for x0 in (2.5, 4.0):
        t = f"table_{n:02d}"
        box(t, x0, x0 + 1.5, 0.7, 0.75, zc - 0.375, zc + 0.375, M_LIGHT)
        for lx in (x0 + 0.05, x0 + 1.43):
            for lz in (zc - 0.33, zc + 0.3):
                box(f"{t}_leg_{'a' if lx < x0 + 1 else 'b'}{'1' if lz < zc else '2'}", lx, lx + 0.02, 0, 0.7, lz, lz + 0.03, M_DARK, collider="none")
        n += 1

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_yup=True,
                          export_extras=True, export_apply=True, export_texcoords=True)
print("exported", OUT, len(bpy.data.objects), "objects")
