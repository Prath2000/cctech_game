"""TASK-1.6 materials, textures and decals for the room blockout.

`build(context=None)` assigns PBR materials to the blockout objects by name, rewrites the
render UV ("UVMap") as world-size UVs (1 unit = one texture repeat), and adds photo decals.
Textures come from assets/raw (scripts/fetch_textures.py); colours are matched to the hex values
in docs/reference/pantry-reference-sheet.md by re-colouring the albedo at build time.
Props modules can reuse materials via `get(name)`.
"""
import os, re
import bpy, bmesh
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "assets", "raw")
DECALS = os.path.join(ROOT, "assets", "decals")

def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

def srgb2lin(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

# name: textures from `src` (None = plain factors), `tile` metres per repeat, `tint` target mean sRGB hex,
# `mix` 0 keep photo colour .. 1 fully recolour keeping only the luminance pattern, `con` luminance contrast,
# `rs/ro` roughness scale/offset (texture) or `rough` constant, `metal` constant or "tex".
SPECS = {
    "floor_tile": dict(src="polyhaven/large_grey_tiles", px=2048, tile=1.2, tint="#d9cfbc", mix=0.85, con=0.6,
                       rs=0.35, ro=0.04, metal=0.0, coat=0.5),
    "wall_plaster": dict(src="polyhaven/white_plaster_02", px=1024, tile=1.5, tint="#f3efe6", mix=0.9, con=0.7,
                         rs=1.0, ro=0.0, metal=0.0),
    "ceiling_tile": dict(src="ambientcg/OfficeCeiling005", px=1024, tile=1.2, tint="#dcdcd9", mix=0.9, con=0.6,
                         rs=1.0, ro=0.0, metal=0.0),
    "granite_black": dict(src="ambientcg/Granite005A", px=2048, tile=1.0, tint="#2d2d31", mix=0.8, con=1.8,
                          rs=0.5, ro=0.05, metal=0.0, coat=0.6),
    "steel_brushed": dict(src="ambientcg/Metal012", px=1024, tile=0.5, tint="#b7b9bb", mix=0.6, con=0.8,
                          rs=1.0, ro=0.0, metal="tex"),
    "aluminium_black": dict(src="ambientcg/Metal050A", px=1024, tile=0.5, tint="#1a1c20", mix=1.0, con=1.0,
                            rs=1.0, ro=0.0, metal=0.7),
    "gloss_white": dict(color="#eeeeea", rough=0.1, metal=0.0, coat=0.8),       # base cabinets, laminate
    "gloss_grey": dict(color="#cfcdca", rough=0.1, metal=0.0, coat=0.8),        # wall cabinet doors (07 (1))
    "laminate_table": dict(color="#f2f3f4", rough=0.25, metal=0.0),
    "plastic_black": dict(color="#15171a", rough=0.5, metal=0.0),               # vending machine cabinet
    "plastic_white": dict(color="#f3f5f6", rough=0.2, metal=0.0, coat=0.5),     # coolers
    "paint_white": dict(color="#f3f1ec", rough=0.85, metal=0.0),                # pillar
    "paint_chevron_orange": dict(color="#e5663a", rough=0.6, metal=0.0),
    "glass_clear": dict(color="#9fb4c4", rough=0.02, metal=0.0, alpha=0.18, spec=0.9),
    "glass_black": dict(color="#101214", rough=0.03, metal=0.0, alpha=0.8, spec=0.9),
    "glass_frosted": dict(color="#e8eef2", rough=0.55, metal=0.0, alpha=0.6),
}

# object name regex -> material (first match wins)
ASSIGN = [
    (r"^floor(_bay)?$", "floor_tile"),
    (r"^ceiling(_bay)?$", "ceiling_tile"),
    (r"^wall_(west|east|south|bay_west|bay_south)$", "wall_plaster"),
    (r"^window_wall_", "wall_plaster"),
    (r"^low_unit$", "plastic_black"),
    (r"^(chevron_wall|fridge_niche)$", "wall_plaster"),
    (r"^window_(frame|mullion)", "aluminium_black"),
    (r"^window_glass", "glass_clear"),
    (r"^window_sill$", "granite_black"),
    (r"^door_frame$", "aluminium_black"),
    (r"^door_leaf", "glass_black"),
    (r"^door_pull", "steel_brushed"),
    (r"^pillar", "paint_white"),
    (r"^counter$", "granite_black"),      # top slab only, body below is gloss_white (see split_counter)
    (r"^wall_cabinets$", "gloss_grey"),
    (r"^fridge$", "steel_brushed"),
    (r"^vending_machine$", "plastic_black"),
    (r"^cooler_", "plastic_white"),
    (r"^table_\d+_leg", "steel_brushed"),
    (r"^table_\d+$", "laminate_table"),
]

_cache = {}

def get(name):
    """Return (building if needed) the named room material."""
    if name in _cache:
        return _cache[name]
    m = _make_material(name, SPECS[name])
    _cache[name] = m
    return m

# ---------------------------------------------------------------- images
def _load_arr(path, px, nc=False):
    im = bpy.data.images.load(path, check_existing=False)
    if nc:  # data map: read the stored bytes verbatim (no sRGB decode)
        im.colorspace_settings.name = "Non-Color"
    if px and im.size[0] != px:
        im.scale(px, px)
    w, h = im.size
    a = np.empty(w * h * 4, np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)

def _new_image(name, arr, nc=False, ext="JPEG"):
    h, w, _ = arr.shape
    im = bpy.data.images.new(name, w, h, alpha=arr.shape[2] == 4 and ext == "PNG")
    if nc:  # data map: tag Non-Color BEFORE filling so pixels are stored/saved verbatim
        im.colorspace_settings.name = "Non-Color"
    im.pixels.foreach_set(np.ascontiguousarray(arr, np.float32).ravel())
    im.file_format = ext
    im.pack()
    return im

def _tex_dir(src):
    return os.path.join(RAW, *src.split("/"))

def _colour_image(name, s):
    a = _load_arr(os.path.join(_tex_dir(s["src"]), "color.jpg"), s["px"])
    rgb = a[..., :3]
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mean = float(lum.mean())
    pat = np.clip((lum - mean) * s["con"] + mean, 0, 1) / max(mean, 1e-4)  # luminance pattern, mean 1
    target = hexrgb(s["tint"])
    recol = np.clip(pat[..., None] * target, 0, 1)
    orig = np.clip(rgb * (target.mean() / max(rgb.mean(), 1e-4)), 0, 1)  # keep hue, match brightness
    out = recol * s["mix"] + orig * (1 - s["mix"])
    a = np.concatenate([out, np.ones_like(out[..., :1])], -1)
    return _new_image(name + "_color", a)

def _orm_image(name, s):
    d = _tex_dir(s["src"])
    r = _load_arr(os.path.join(d, "rough.jpg"), s["px"], nc=True)[..., 0]
    r = np.clip(r * s["rs"] + s["ro"], 0.03, 1)
    mp = os.path.join(d, "metal.jpg")
    m = _load_arr(mp, s["px"], nc=True)[..., 0] if s["metal"] == "tex" and os.path.exists(mp) else np.full_like(r, s["metal"] if s["metal"] != "tex" else 0)
    a = np.stack([np.ones_like(r), r, m, np.ones_like(r)], -1)
    return _new_image(name + "_orm", a, nc=True)

def _normal_image(name, s):
    a = _load_arr(os.path.join(_tex_dir(s["src"]), "normal.jpg"), s["px"], nc=True)
    return _new_image(name + "_normal", a, nc=True)

# ---------------------------------------------------------------- materials
def _setup(m):
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs["BSDF"], nt.nodes["Material Output"].inputs["Surface"])
    return nt, b

def _make_material(name, s):
    m = bpy.data.materials.new(name)
    nt, b = _setup(m)
    m["tile_m"] = s.get("tile", 1.0)
    L = nt.links.new
    if "src" in s:
        uv = nt.nodes.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"
        def tex(img, y):
            t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.location = (-600, y)
            t.interpolation = "Linear"
            L(uv.outputs["UV"], t.inputs["Vector"])
            return t
        tc = tex(_colour_image(name, s), 300)
        L(tc.outputs["Color"], b.inputs["Base Color"])
        to = tex(_orm_image(name, s), 0)
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        L(to.outputs["Color"], sep.inputs["Color"])
        L(sep.outputs["Green"], b.inputs["Roughness"])
        L(sep.outputs["Blue"], b.inputs["Metallic"])
        if os.environ.get("NO_NORMALS"):
            return m
        tn = tex(_normal_image(name, s), -300)
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.0
        L(tn.outputs["Color"], nm.inputs["Color"])
        L(nm.outputs["Normal"], b.inputs["Normal"])
    else:
        b.inputs["Base Color"].default_value = (*srgb2lin(hexrgb(s["color"])), 1)
        b.inputs["Roughness"].default_value = s["rough"]
        b.inputs["Metallic"].default_value = s["metal"]
    if s.get("coat"):
        b.inputs["Coat Weight"].default_value = s["coat"]
        b.inputs["Coat Roughness"].default_value = 0.03
    if s.get("alpha") is not None:
        b.inputs["Alpha"].default_value = s["alpha"]
        m.surface_render_method = "BLENDED"
    if "spec" in s:
        b.inputs["Specular IOR Level"].default_value = s["spec"]
    return m

# ---------------------------------------------------------------- UV / geometry helpers
def world_uv(o, tile):
    """Box-project the render UV in world metres / tile (blender axes: z up)."""
    me = o.data
    uvl = me.uv_layers["UVMap"]
    mw = o.matrix_world
    for p in me.polygons:
        n = (mw.to_3x3() @ p.normal)
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            c = mw @ me.vertices[me.loops[li].vertex_index].co
            u, v = {0: (c.y, c.z), 1: (c.x, c.z), 2: (c.x, c.y)}[ax]
            uvl.data[li].uv = (u / tile, v / tile)

def bounds(name):
    """Game-space (x0,x1,y0,y1,z0,z1) of a named object (blender y = -game z)."""
    o = bpy.data.objects[name]
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    xs, ys, zs = [c.x for c in cs], [c.z for c in cs], [-c.y for c in cs]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

def split_counter(o, granite, laminate):
    """Granite slab on top (3 cm), white gloss laminate base cabinets below."""
    cut = bounds(o.name)[3] - 0.03 - o.location.z  # local z of the slab underside
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, cut), plane_no=(0, 0, 1))
    for f in bm.faces:
        f.material_index = 0 if f.calc_center_median().z > cut else 1
    bm.to_mesh(o.data); bm.free()
    o.data.materials.clear()
    o.data.materials.append(granite); o.data.materials.append(laminate)

def chevron_span():
    """Game z range (lo, hi) of the chevron panel: the scan's graphic span (layout.CHEVRON_Z0/Z1)."""
    return bounds("chevron_wall")[4], bounds("chevron_wall")[5]

def fit_chevron_wall():
    """Stretch the chevron panel to chevron_span() so both chevron decals sit on it."""
    o = bpy.data.objects.get("chevron_wall")
    if not o:
        return
    lo, hi = chevron_span()
    zmid = bounds("chevron_wall")[4:6]
    mid = sum(zmid) / 2
    for v in o.data.vertices:
        zg = -(o.matrix_world @ v.co).y
        v.co.y = -(lo if zg < mid else hi) - o.location.y

def add_mesh_object(name, verts_game, caption):
    gb = lambda p: (p[0], -p[2], p[1])
    me = bpy.data.meshes.new(name)
    me.from_pydata([gb(p) for p in verts_game], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = c
    lm = me.uv_layers.new(name="lightmap")
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        lm.data[i].uv = c
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o["static"] = 1; o["collider"] = "none"; o["interact"] = "look"; o["caption_id"] = caption
    return o

def decal(name, png, centre, right, up, w, h, caption, blend=False):
    """Textured plane `0.004 m` off a surface. centre/right/up in game coords (right x up = facing normal)."""
    c, r, u = Vector(centre), Vector(right).normalized(), Vector(up).normalized()
    pts = [c - r * w / 2 - u * h / 2, c + r * w / 2 - u * h / 2, c + r * w / 2 + u * h / 2, c - r * w / 2 + u * h / 2]
    o = add_mesh_object(name, [tuple(p) for p in pts], caption)
    m = bpy.data.materials.new("mat_" + name)
    nt, b = _setup(m)
    im = bpy.data.images.load(os.path.join(DECALS, png + ".png"))
    im.pack(); im.file_format = "PNG"
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = im
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    if blend:
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
        m.surface_render_method = "BLENDED"
    o.data.materials.append(m)
    # the glTF front face is the CCW face seen from outside: make sure the normal matches right x up
    want = r.cross(u)
    gn = Vector(o.data.polygons[0].normal)
    got = Vector((gn.x, gn.z, -gn.y))  # blender -> game
    if want.dot(got) < 0:
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o

def add_window_backdrop():
    """Hazy city plate (scripts/make_backdrop.py) 30 m outside the window wall (z<0): emissive, unlit, no shadow."""
    z = -30.0
    o = add_mesh_object("window_backdrop", [(-30, -14, z), (42, -14, z), (42, 31, z), (-30, 31, z)], "window_view")
    o["static"] = 0; o["bake"] = 0; o["lit"] = False
    o.visible_shadow = False
    m = bpy.data.materials.new("mat_window_backdrop")
    nt, b = _setup(m)
    im = bpy.data.images.load(os.path.join(DECALS, "window_backdrop.jpg"))
    im.pack(); im.file_format = "JPEG"
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = im
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Roughness"].default_value = 1.0
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 1.0
    o.data.materials.append(m)
    # face the room (+z): vertices go (0,1,2,3) left to right seen from inside, so flip if the normal points away
    gn = Vector(o.data.polygons[0].normal)
    if -gn.y < 0:
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o

def add_door_pulls(steel):
    x0, x1, y0, y1, za0, za1 = bounds("door_leaf_a")
    zm = za1  # meeting line of the two leaves
    for n, z in (("door_pull_a", zm - 0.1), ("door_pull_b", zm + 0.1)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=1.0, location=(x1 + 0.02, -z, y0 + 1.05))
        o = bpy.context.active_object
        o.name = o.data.name = n
        o.data.materials.append(steel)
        o["static"] = 1; o["collider"] = "none"; o["interact"] = "look"
        o.data.uv_layers.new(name="UVMap")
        o.data.uv_layers.new(name="lightmap")

def build(context=None):
    # 1. materials + geometry tweaks
    fit_chevron_wall()
    for n in ("chevron_01", "chevron_02"):  # grey placeholders, replaced by the chevron decals
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    add_door_pulls(get("steel_brushed"))
    for o in [o for o in bpy.data.objects if o.type == "MESH"]:
        for pat, mname in ASSIGN:
            if re.search(pat, o.name):
                m = get(mname)
                if o.name == "counter":
                    split_counter(o, m, get("gloss_white"))
                else:
                    o.data.materials.clear(); o.data.materials.append(m)
                if "UVMap" not in o.data.uv_layers:
                    o.data.uv_layers.new(name="UVMap")
                world_uv(o, m["tile_m"])
                break
    # 2. decals (game coords: x east, y up, z south); west wall decals face +x with image-right = -z
    D = 0.004
    x_w = bounds("floor")[0]                 # west wall plane
    x_e = bounds("wall_east")[0]             # east wall inner face
    z_s = bounds("wall_south")[4]            # south wall inner face
    cw = bounds("chevron_wall")[1] + D       # chevron panel face
    lo, hi = chevron_span()
    # INNOVATION chevron pair, orange, west wall only: as tall as the panel allows (1.5 m, y 0.9-2.4) and filling its
    # whole z span (2.5-4.7). Innovation chevron (520 x 720 px) nearest the door, large chevron (600 x 840 px) to its left.
    ch = 1.5
    wi, wl = ch * 520 / 720, ch * 600 / 840
    yc = 0.9 + ch / 2
    zi = hi - 0.02 - wi / 2
    zl = hi - 0.02 - wi - wl / 2
    decal("decal_chevron_innovation", "chevron_innovation", (cw, yc, zi), (0, 0, -1), (0, 1, 0), wi, ch, "innovation_sign", blend=True)
    decal("decal_chevron_large", "chevron_large", (cw, yc, zl), (0, 0, -1), (0, 1, 0), wl, ch, "chevron_wall", blend=True)
    # circuit mural: built by props/seating.py (build_mural) on the partition, x 0.5-1.5
    add_window_backdrop()
    cx0, cx1, cy0, cy1, cz0, cz1 = bounds("counter")
    decal("decal_sticky_note", "sticky_note", (cx0 + 0.3, cy1 + D, (cz0 + cz1) / 2), (0.966, 0, 0.259), (0.259, 0, -0.966), 0.1, 0.1, "sticky_note")
    decal("decal_bone_sign", "bone_sign", (x_e - D, cy1 + 0.15, cz1 - 0.3), (0, 0, 1), (0, 1, 0), 0.32, 0.1, "bone_sign")
