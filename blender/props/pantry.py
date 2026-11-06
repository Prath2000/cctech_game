"""Pantry props (TASK-1.7, pantry half). Module API: build(context) -> list of created objects.

All coordinates in this file are GAME coords in metres (x east, y up, z south); G() maps to
Blender z-up (x, -z, y). The counter (blockout) is x 7.4-8.0, z 1.4-4.4, top at y 0.9 and
everything faces -x (west), see docs/reference/pantry-reference-sheet.md section 3/4.
Procedural models from product dims + photo decals (assets/decals/pantry/); no downloaded assets.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DECALS = os.path.join(ROOT, "assets", "decals", "pantry")
CT = 0.8  # counter top height [scan: counter top 0.79-0.81]
# TASK-1.17: props are authored in an OLD frame (counter x 7.4-8.0 facing -x, run z 1.4-3.25) then build() maps the
# counter group onto the scan layout (x'=14.7-x, z'=11.2-z, i.e. wall x=6.7, facing +x, run z 9.8..7.95) and warps the
# fridge to the scan footprint. Old anchors: the 8 x 6 x 3 m blockout (counter x 7.4-8.0, z from 1.4, ceiling 3.0).
# Everything is shifted by (DX, DZ) / CEIL so a room resize is a one-line change here
# (build() also reads the blockout 'counter' / 'ceiling' objects when present).
ROOM_W, ROOM_H, COUNTER_Z0 = 8.0, 3.0, 1.4
DX, DZ = 0.0, 0.0

_mats = {}
_col = None


def G(x, y, z):
    return Vector((x + DX, -(z + DZ), y))


# ---------------------------------------------------------------- materials
def M(name, base, rough=0.5, metal=0.0, trans=0.0, ior=1.45, emit=None, emit_k=0.0, coat=0.0, alpha=None):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base[:3], 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["IOR"].default_value = ior
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.05
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[:3], 1)
        b.inputs["Emission Strength"].default_value = emit_k
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    _mats[name] = m
    return m


def tex_mat(name, fname, rough=0.35, emit_k=0.0):
    """Image-textured material from assets/decals/pantry (None if the file is missing)."""
    if name in _mats:
        return _mats[name]
    path = os.path.join(DECALS, fname)
    if not os.path.exists(path):
        print("pantry: missing decal", path)
        return None
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    if emit_k:
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit_k
    _mats[name] = m
    return m


def materials():
    return dict(
        fridge=M("pantry_fridge_steel", (0.62, 0.63, 0.64), 0.42, 1.0),
        steel=M("pantry_steel", (0.72, 0.73, 0.74), 0.3, 1.0),
        chrome=M("pantry_chrome", (0.9, 0.9, 0.9), 0.08, 1.0),
        dark_steel=M("pantry_dark_steel", (0.2, 0.2, 0.22), 0.35, 1.0),
        blk=M("pantry_black_plastic", (0.025, 0.026, 0.028), 0.38),
        blk_gloss=M("pantry_black_gloss", (0.012, 0.012, 0.014), 0.12, coat=0.6),
        glass_dark=M("pantry_glass_dark", (0.01, 0.012, 0.015), 0.04, coat=1.0),
        white=M("pantry_white_plastic", (0.86, 0.86, 0.84), 0.35),
        lam_grey=M("pantry_gloss_laminate_grey", (0.86, 0.86, 0.84), 0.1, coat=0.8),
        lam_white=M("pantry_white_laminate", (0.82, 0.82, 0.8), 0.22, coat=0.4),
        carcass=M("pantry_carcass", (0.86, 0.85, 0.83), 0.45),
        purple=M("pantry_purple_pet", (0.78, 0.3, 0.84), 0.1, trans=0.92, ior=1.5),
        purple_cap=M("pantry_purple_cap", (0.12, 0.05, 0.4), 0.35),
        glass=M("pantry_clear_glass", (0.9, 0.95, 0.95), 0.03, trans=1.0, ior=1.5),
        frost=M("pantry_frosted_glass", (0.85, 0.87, 0.86), 0.25, trans=0.6, ior=1.5),
        rubber=M("pantry_grey_rubber", (0.26, 0.27, 0.29), 0.85),
        hose=M("pantry_grey_hose", (0.2, 0.21, 0.22), 0.6),
        note=M("pantry_sticky_note", (0.88, 0.68, 0.06), 0.85),
        olive=M("pantry_mug_olive", (0.18, 0.2, 0.05), 0.2, coat=0.5),
        led_off=M("pantry_led_panel", (0.82, 0.84, 0.86), 0.5, emit=(1, 1, 0.95), emit_k=0.0),
        fan_white=M("pantry_fan_white", (0.85, 0.85, 0.83), 0.45),
        green_led=M("pantry_mw_display", (0.02, 0.05, 0.02), 0.3, emit=(0.2, 1.0, 0.3), emit_k=0.6),
        red_cloth=M("pantry_red_cloth", (0.5, 0.03, 0.04), 0.9),
        granite=M("pantry_granite_dark", (0.07, 0.072, 0.08), 0.22, coat=0.4),
        sink_steel=M("pantry_sink_steel", (0.8, 0.81, 0.82), 0.12, 1.0),
        soap_yel=M("pantry_soap_yellow", (0.82, 0.68, 0.06), 0.3),
        soap_grn=M("pantry_soap_green", (0.12, 0.5, 0.18), 0.3),
        pink=M("pantry_pink_bottle", (0.85, 0.2, 0.45), 0.25),
        yellow=M("pantry_dish_yellow", (0.8, 0.65, 0.05), 0.3, trans=0.3),
    )


MUG_COLORS = {
    "brown": (0.07, 0.025, 0.015), "navy": (0.01, 0.06, 0.14), "white": (0.8, 0.8, 0.78),
    "red": (0.5, 0.03, 0.03), "green": (0.18, 0.5, 0.2), "black": (0.015, 0.015, 0.017),
    "teal": (0.01, 0.2, 0.3), "cream": (0.6, 0.5, 0.35), "sage": (0.55, 0.65, 0.5),
}


# ---------------------------------------------------------------- bmesh helpers
def _finalize(bm, flip_check=()):
    bm.normal_update()
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(38):
            e.smooth = False


def bm_box(bm, x0, x1, y0, y1, z0, z1, bevel=0.003, mi=0):
    before = set(bm.verts)
    vs = bmesh.ops.create_cube(bm, size=1)["verts"]
    for v in vs:
        px, py, pz = v.co.x + 0.5, v.co.y + 0.5, v.co.z + 0.5  # 0..1 in blender axes
        v.co = G(x0 + (x1 - x0) * px, y0 + (y1 - y0) * pz, z1 - (z1 - z0) * py)
    edges = list({e for v in vs for e in v.link_edges})
    faces = list({f for v in vs for f in v.link_faces})
    b = min(bevel, (x1 - x0) / 2.2, (y1 - y0) / 2.2, (z1 - z0) / 2.2)
    if b > 1e-5:
        r = bmesh.ops.bevel(bm, geom=edges, offset=b, offset_type="OFFSET", segments=2, profile=0.6, affect="EDGES")
        faces = list(r["faces"]) + faces
    bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.is_valid])
    return [v for v in bm.verts if v not in before]


def bm_box_mi(bm, mi, *a, **k):
    before = set(bm.faces)
    r = bm_box(bm, *a, **k)
    for f in bm.faces:
        if f not in before:
            f.material_index = mi
    return r


def bm_lathe(bm, profile, cx=0.0, cz=0.0, y0=0.0, segs=32, mi=0):
    """Closed (r, y) profile (start and end at r=0) spun around the vertical axis at (cx, cz)."""
    rings = []
    apex = {}
    for (r, y) in profile:
        ring = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            if r < 1e-7:
                key = round(y, 6)
                if key not in apex:
                    apex[key] = bm.verts.new(G(cx, y0 + y, cz))
                ring.append(apex[key])
            else:
                ring.append(bm.verts.new(G(cx + r * math.cos(a), y0 + y, cz + r * math.sin(a))))
        rings.append(ring)
    faces = []
    for i in range(len(rings) - 1):
        for j in range(segs):
            k = (j + 1) % segs
            vs = [rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]]
            uniq = []
            for v in vs:
                if v not in uniq:
                    uniq.append(v)
            if len(uniq) >= 3:
                try:
                    f = bm.faces.new(uniq)
                    f.material_index = mi
                    faces.append(f)
                except ValueError:
                    pass
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    return faces


def bm_tube(bm, pts, r, segs=8, closed=False, mi=0, caps=True):
    pts = [G(*p) for p in pts]
    n = len(pts)
    tans = []
    for i in range(n):
        a = pts[(i + 1) % n] if (closed or i < n - 1) else pts[i]
        b = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        tans.append((a - b).normalized())
    ref = Vector((1, 0, 0)) if abs(tans[0].x) < 0.9 else Vector((0, 1, 0))
    nrm = tans[0].cross(ref).normalized()
    rings = []
    for i in range(n):
        t = tans[i]
        nrm = (nrm - t * nrm.dot(t)).normalized()
        bn = t.cross(nrm)
        rings.append([bm.verts.new(pts[i] + (nrm * math.cos(2 * math.pi * j / segs) + bn * math.sin(2 * math.pi * j / segs)) * r) for j in range(segs)])
    faces = []
    for i in range(n if closed else n - 1):
        i2 = (i + 1) % n
        for j in range(segs):
            k = (j + 1) % segs
            f = bm.faces.new([rings[i][j], rings[i][k], rings[i2][k], rings[i2][j]])
            f.material_index = mi
            faces.append(f)
    if caps and not closed:
        for ring in (rings[0], rings[-1]):
            f = bm.faces.new(ring)
            f.material_index = mi
            faces.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    return faces


def bm_open_box(bm, x0, x1, y0, y1, z0, z1, wall=0.002, bevel=0.012, mi=0):
    """Open-top tray with thickness (sink bowl)."""
    vs = bm_box(bm, x0, x1, y0, y1, z0, z1, bevel)
    top = [f for f in bm.faces if f.is_valid and all(abs(v.co.z - y1) < 1e-6 for v in f.verts)]
    bmesh.ops.delete(bm, geom=top, context="FACES_ONLY")
    # solidify by offsetting inward copy
    faces = [f for f in bm.faces]
    r = bmesh.ops.solidify(bm, geom=faces, thickness=-wall)
    for f in bm.faces:
        f.material_index = mi
    return vs


def bm_quad_front(bm, x, zc, yc, w, h):
    """Vertical quad facing -x with UVs 0..1 (u to +z, v up)."""
    uv = bm.loops.layers.uv.verify()
    vs = [bm.verts.new(G(x, yc - h / 2, zc - w / 2)), bm.verts.new(G(x, yc - h / 2, zc + w / 2)),
          bm.verts.new(G(x, yc + h / 2, zc + w / 2)), bm.verts.new(G(x, yc + h / 2, zc - w / 2))]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.x > 0:
        f.normal_flip()
    for l, (u, v) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        l[uv].uv = (u, v)
    return f


def rotate_bm(bm, verts, angle, axis, pivot):
    bmesh.ops.rotate(bm, verts=verts, cent=pivot, matrix=Matrix.Rotation(angle, 3, axis))


# ---------------------------------------------------------------- object helpers
def collection():
    global _col
    if _col is None:
        _col = bpy.data.collections.get("Pantry") or bpy.data.collections.new("Pantry")
        if _col.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(_col)
    return _col


def add_lightmap_uv(o):
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
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


def finish(name, bm, mats, origin=(0, 0, 0), parent=None, static=0, extras=None, mesh=None):
    """bm holds coords in game space; shifted so the object origin sits at `origin` (game coords)."""
    _finalize(bm)
    o0 = G(*origin)
    bmesh.ops.translate(bm, verts=bm.verts, vec=-o0)
    me = mesh or bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in (mats if isinstance(mats, (list, tuple)) else [mats]):
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    collection().objects.link(o)
    o.location = o0
    if parent is not None:
        o.parent = parent
        o.matrix_parent_inverse = Matrix.Translation(-parent.location)
    o["static"] = 1 if static else 0
    for k, v in (extras or {}).items():
        o[k] = v
    if static:
        add_lightmap_uv(o)
    return o


def decal(name, parent, fname, x, zc, yc, w, h, tilt=0.0, tilt_pivot=None, extras=None):
    m = tex_mat("pantry_decal_" + os.path.splitext(fname)[0], fname)
    if m is None:
        return None
    bm = bmesh.new()
    bm_quad_front(bm, x, zc, yc, w, h)
    if tilt:
        rotate_bm(bm, bm.verts, tilt, "Y", G(*tilt_pivot))
    o = finish(name, bm, m, origin=(x, yc, zc), parent=parent, static=0, extras={"interact": "look", "collider": "none", **(extras or {})})
    return o


def collider_boxes(origin, boxes):
    """Hollow-prop collision: custom prop `collider_boxes` = JSON [[cx, cy, cz, hx, hy, hz], ...] in game axes relative to the
    object origin (room.ts builds one cuboid per entry; used with collider=boxes)."""
    out = []
    for (x0, x1, y0, y1, z0, z1) in boxes:
        out.append([round((x0 + x1) / 2 - origin[0], 4), round((y0 + y1) / 2 - origin[1], 4), round((z0 + z1) / 2 - origin[2], 4),
                    round((x1 - x0) / 2, 4), round((y1 - y0) / 2, 4), round((z1 - z0) / 2, 4)])
    return json.dumps(out)


def hinge(o, axis, max_deg, sign):
    o["hinge_axis"] = axis
    o["hinge_max_deg"] = max_deg
    o["hinge_open_sign"] = sign


# ---------------------------------------------------------------- props
def fridge(mt):
    out = []
    x0, x1 = 6.98, 7.62
    z0, z1 = 0.2 - DZ, 0.755 - DZ  # world z 0.2-0.755: beside the glazed wall, not in front of a niche (TASK-1.25)
    zc = (z0 + z1) / 2
    top = 1.6
    bm = bmesh.new()
    bm_box(bm, x0 + 0.04, x1, 0.04, top, z0, z1, 0.008)
    for fx in (x0 + 0.08, x1 - 0.06):
        for fz in (z0 + 0.04, z1 - 0.04):
            bm_box(bm, fx - 0.025, fx + 0.025, 0.0, 0.04, fz - 0.025, fz + 0.025, 0.004)
    body = finish("lg_fridge", bm, mt["fridge"], (zc * 0 + (x0 + x1) / 2, 0, zc), static=1,
                  extras={"interact": "look", "caption_id": "lg_fridge", "collider": "box"})
    out.append(body)
    # freezer door (top) and fridge door (bottom): hinged on the +z side (viewer's right)
    specs = [("lg_fridge_door_freezer", 0.975, top, "fridge_door"), ("lg_fridge_door_main", 0.065, 0.965, "fridge_door")]
    for nm, ya, yb, uk in specs:
        bm = bmesh.new()
        bm_box(bm, x0, x0 + 0.045, ya, yb, z0, z1, 0.006)
        d = finish(nm, bm, mt["fridge"], (x0 + 0.02, (ya + yb) / 2, z1), parent=body, static=0,
                   extras={"interact": "use", "use_kind": uk, "caption_id": nm, "collider": "box"})
        hinge(d, "y", 110, 1)
        out.append(d)
        if nm.endswith("freezer"):
            fz = d
        else:
            mdoor = d
    # recessed scoop handle at top of the main door: dark slot + steel lip
    bm = bmesh.new()
    bm_box(bm, x0 - 0.004, x0 + 0.002, 0.915, 0.96, z0 + 0.03, z1 - 0.03, 0.002)
    out.append(finish("lg_fridge_handle_slot", bm, mt["blk"], (x0, 0.94, zc), parent=mdoor, extras={"interact": "look", "collider": "none"}))
    bm = bmesh.new()
    bm_box(bm, x0 - 0.016, x0 + 0.0, 0.945, 0.962, z0 + 0.05, z1 - 0.05, 0.006)
    out.append(finish("lg_fridge_handle_lip", bm, mt["steel"], (x0, 0.95, zc), parent=mdoor, extras={"interact": "look", "collider": "none"}))
    # photo decals on the freezer door (front plane x0)
    fx = x0 - 0.0006
    for nm, f, dz, dy, w, h in [
        ("lg_fridge_logo", "lg_fridge_logo.png", -0.2, 1.505, 0.05, 0.03),
        ("fridge_sticker_respect", "fridge_sticker_respect.png", 0.165, 1.465, 0.115, 0.112),
        ("fridge_sticker_10year", "fridge_sticker_10year.png", 0.165, 1.325, 0.068, 0.094),
        ("fridge_sticker_power_guide", "fridge_sticker_power_guide.png", 0.165, 1.17, 0.075, 0.122),
        ("fridge_sticker_qr", "fridge_sticker_qr.png", 0.165, 1.025, 0.07, 0.095),
    ]:
        o = decal(nm, fz, f, fx, zc + dz, dy, w, h)
        if o:
            out.append(o)
    return out


def microwave(mt):
    out = []
    x0, x1 = 7.68, 8.0
    z0, z1 = 3.40, 3.855
    y0, y1 = 1.25, 1.502
    bm = bmesh.new()
    bm_box(bm, x0 + 0.02, x1, y0, y1, z0, z1, 0.006)
    bm_box(bm, x0, x0 + 0.03, y0, y1, z1 - 0.15, z1, 0.005)  # control panel block
    # side brackets
    for bz in (z0 + 0.06, z1 - 0.06):
        bm_box(bm, x0 + 0.1, x1, y0 - 0.014, y0, bz - 0.02, bz + 0.02, 0.002)
    # display + buttons
    bm_box_mi(bm, 1, x0 - 0.002, x0 + 0.002, 1.44, 1.47, z1 - 0.125, z1 - 0.055, 0.001)
    for i in range(3):
        for j in range(2):
            bm_box_mi(bm, 2, x0 - 0.003, x0 + 0.002, 1.31 + j * 0.045, 1.345 + j * 0.045, z1 - 0.13 + i * 0.044, z1 - 0.1 + i * 0.044, 0.001)
    mw = finish("lg_microwave", bm, [mt["blk_gloss"], mt["green_led"], mt["dark_steel"]], (x1 - 0.16, (y0 + y1) / 2, (z0 + z1) / 2), static=1,
                extras={"interact": "use", "use_kind": "microwave", "caption_id": "lg_microwave", "collider": "box"})
    out.append(mw)
    # door: hinged on the low-z side (viewer's left)
    dz1 = z1 - 0.15
    bm = bmesh.new()
    bm_box(bm, x0, x0 + 0.03, y0 + 0.035, y1 - 0.012, z0 + 0.004, dz1 - 0.003, 0.005)
    bm_box_mi(bm, 1, x0 - 0.002, x0 + 0.004, y0 + 0.05, y1 - 0.03, z0 + 0.025, dz1 - 0.02, 0.002)
    d = finish("lg_microwave_door", bm, [mt["blk_gloss"], mt["glass_dark"]], (x0 + 0.015, (y0 + y1) / 2, z0), parent=mw, static=0,
               extras={"interact": "use", "use_kind": "microwave", "caption_id": "lg_microwave_door", "collider": "box"})
    hinge(d, "y", 105, -1)
    out.append(d)
    o = decal("lg_microwave_logo", mw, "lg_microwave_logo.png", x0 - 0.0006, z0 + 0.05, y0 + 0.018, 0.05, 0.0286)
    if o:
        out.append(o)
    return out


def coffee_machine(mt):
    out = []
    # Tata My Bistro (photo 06): left brew unit (deck + recessed bay + drip tray) with an angled touchscreen, taller plain right block.
    cx0, cx1 = 7.50, 7.97
    z0, z1 = 3.93, 4.47
    zm = 4.19  # split between brew unit (low z) and right block
    by = CT
    bm = bmesh.new()
    bm_box(bm, cx0 + 0.02, cx1, by, by + 0.04, z0, z1, 0.006)                        # base plate
    bm_box(bm, cx0 + 0.07, cx1, by + 0.04, by + 0.55, zm, z1, 0.01)                  # right block (tall, plain)
    bm_box(bm, cx0 + 0.05, cx1, by + 0.30, by + 0.50, z0, zm, 0.01)                  # brew-unit deck
    bm_box(bm, cx0 + 0.23, cx1, by + 0.04, by + 0.30, z0, zm, 0.008)                 # bay back block
    bm_box(bm, cx0 + 0.05, cx1, by + 0.04, by + 0.30, z0, z0 + 0.012, 0.004)         # bay side wall
    bm_box(bm, cx0 + 0.07, cx0 + 0.075, by + 0.04, by + 0.30, zm - 0.012, zm, 0.001)  # bay right wall (thin)
    # brewing spout and nozzles
    bm_box(bm, cx0 + 0.15, cx0 + 0.25, by + 0.235, by + 0.30, z0 + 0.1, z0 + 0.21, 0.01)
    for dz in (0.135, 0.175):
        for v in bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.006, radius2=0.006, depth=0.04)["verts"]:
            v.co = G(cx0 + 0.2 + v.co.x, by + 0.215 + v.co.z, z0 + dz + v.co.y)
    # top vent rings (grey fans, mi=1) on deck and right block, plus the handle slot
    for hx, hz, ty in ((cx0 + 0.14, z0 + 0.07, by + 0.50), (cx0 + 0.14, z0 + 0.20, by + 0.50), (cx0 + 0.34, z0 + 0.13, by + 0.50),
                       (cx0 + 0.36, zm + 0.08, by + 0.55), (cx0 + 0.36, zm + 0.22, by + 0.55), (cx0 + 0.20, zm + 0.15, by + 0.55)):
        bm_lathe(bm, [(0, 0), (0.026, 0), (0.026, 0.003), (0.0, 0.003)], hx, hz, ty, 20, mi=1)
    bm_box_mi(bm, 1, cx0 + 0.14, cx0 + 0.18, by + 0.55, by + 0.553, zm + 0.1, zm + 0.17, 0.001)
    # silver label plate on the right block front
    bm_box_mi(bm, 2, cx0 + 0.066, cx0 + 0.072, by + 0.44, by + 0.5, zm + 0.2, zm + 0.31, 0.001)
    body = finish("tata_bistro_machine", bm, [mt["blk"], mt["dark_steel"], mt["steel"]], (7.735, by, 4.355), static=0,
                  extras={"interact": "use", "use_kind": "coffee_machine", "caption_id": "tata_bistro", "collider": "boxes", "mass": 18.0,
                          "collider_boxes": collider_boxes((7.735, by, 4.355), [
                              (cx0 + 0.07, cx1, by + 0.04, by + 0.55, zm, z1), (cx0 + 0.05, cx1, by + 0.30, by + 0.50, z0, zm),
                              (cx0 + 0.23, cx1, by + 0.04, by + 0.30, z0, zm), (cx0 + 0.05, cx1, by + 0.04, by + 0.30, z0, z0 + 0.012),
                              (cx0 + 0.02, cx1, by, by + 0.04, z0, z1)])})
    # a coffee machine is heavy furniture: not grabbed
    body["static"] = 1
    add_lightmap_uv(body)
    del body["mass"]
    out.append(body)
    # drip tray: dark pan + steel grille bars, protruding in front of the base
    bm = bmesh.new()
    bm_box_mi(bm, 1, cx0 - 0.02, cx0 + 0.24, by + 0.04, by + 0.058, z0 + 0.02, zm - 0.02, 0.004)
    for i in range(16):
        bm_box(bm, cx0 - 0.015, cx0 + 0.235, by + 0.058, by + 0.066, z0 + 0.026 + i * 0.0093, z0 + 0.031 + i * 0.0093, 0.0008)
    bm_box(bm, cx0 - 0.02, cx0 - 0.012, by + 0.058, by + 0.07, z0 + 0.02, zm - 0.02, 0.002)  # front rim
    out.append(finish("tata_bistro_drip_tray", bm, [mt["steel"], mt["blk"]], (cx0 + 0.15, by + 0.05, z0 + 0.1), parent=body, extras={"interact": "look", "collider": "none"}))
    # angled touchscreen (steel rim + black glass), leaning back from the deck front
    sc = (cx0 + 0.035, by + 0.395, (z0 + zm) / 2 + 0.07)
    ang = math.radians(22)
    bm = bmesh.new()
    bm_box_mi(bm, 1, sc[0] - 0.012, sc[0] + 0.012, sc[1] - 0.11, sc[1] + 0.11, sc[2] - 0.17, sc[2] + 0.17, 0.008)
    bm_box_mi(bm, 0, sc[0] - 0.006, sc[0] + 0.006, sc[1] - 0.102, sc[1] + 0.102, sc[2] - 0.162, sc[2] + 0.162, 0.006)
    rotate_bm(bm, bm.verts, ang, "Y", G(*sc))
    scr = finish("tata_bistro_screen_bezel", bm, [mt["blk_gloss"], mt["steel"]], (sc[0], sc[1], sc[2]), parent=body, extras={"interact": "use", "use_kind": "coffee_machine", "caption_id": "tata_bistro_screen", "collider": "none"})
    out.append(scr)
    d = decal("tata_bistro_screen", scr, "tata_bistro_screen.png", sc[0] - 0.0135, sc[2], sc[1], 0.31, 0.19,
              tilt=ang, tilt_pivot=sc, extras={"caption_id": "tata_bistro_screen"})
    if d:
        out.append(d)
    # granite curved side panel left of the machine (photo 06)
    bm = bmesh.new()
    bm_box(bm, cx0 - 0.04, cx1 + 0.03, by, by + 0.5, z0 - 0.032, z0 - 0.008, 0.01)
    out.append(finish("coffee_side_panel", bm, mt["granite"], (7.735, by, z0 - 0.02), static=1, extras={"interact": "look", "collider": "none", "caption_id": "counter"}))
    # B'ONE board + notice sheet
    bm = bmesh.new()
    # photo 06: white board with red lettering on the x=6.7 wall just right of the machine, top above the machine (old frame: x 7.94-8.0, z 3.38-3.58, y 1.4-1.8)
    bm = bmesh.new()
    bm_box(bm, 7.94, 7.995, 1.4, 1.8, 3.38, 3.58, 0.004)
    out.append(finish("bone_board", bm, mt["white"], (7.97, 1.6, 3.48), static=1, extras={"interact": "look", "collider": "none", "caption_id": "bone_board"}))
    d = decal("bone_board_label", out[-1], "bone_panel.png", 7.935, 3.48, 1.6, 0.15, 0.34)
    if d:
        out.append(d)
    d = decal("coffee_notice_sheet", body, "coffee_notice_sheet.png", 7.994, 4.05, 1.62, 0.2, 0.185)
    if d:
        out.append(d)
    return out


def counter_items(mt):
    out = []
    # --- sink (cut into the blockout counter if present) + bowl + faucet
    sx0, sx1, sz0, sz1 = 7.5, 7.9, 1.85, 2.35
    cut = bmesh.new()
    bm_box(cut, 14.7 - sx1 + 0.01, 14.7 - sx0 - 0.01, CT - 0.19, CT + 0.05, 11.2 - 0.45 - sz1 + 0.01, 11.2 - 0.45 - sz0 - 0.01, 0.0)  # old sink box -> new frame (dz -0.45)
    cm = bpy.data.meshes.new("sink_cutter")
    cut.to_mesh(cm)
    cut.free()
    co = bpy.data.objects.new("sink_cutter", cm)
    collection().objects.link(co)
    counter = bpy.data.objects.get("counter")
    if counter is not None and not counter.get("pantry_sink_cut"):
        mod = counter.modifiers.new("sink_cut", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = co
        bpy.context.view_layer.objects.active = counter
        bpy.ops.object.modifier_apply(modifier=mod.name)
        counter["pantry_sink_cut"] = 1
        for l in list(counter.data.uv_layers):
            if l.name == "lightmap":
                counter.data.uv_layers.remove(l)
        add_lightmap_uv(counter)
    bpy.data.objects.remove(co)
    # opaque inset steel basin: solid 15 mm walls and floor (the old 2 mm open shell read as a translucent box)
    bm = bmesh.new()
    bx0, bx1, bz0, bz1, wt = sx0 + 0.012, sx1 - 0.012, sz0 + 0.012, sz1 - 0.012, 0.015
    by0 = CT - 0.18
    bm_box(bm, bx0, bx1, by0, by0 + wt, bz0, bz1, 0.002)                     # floor
    bm_box(bm, bx0, bx0 + wt, by0, CT - 0.004, bz0, bz1, 0.002)              # walls
    bm_box(bm, bx1 - wt, bx1, by0, CT - 0.004, bz0, bz1, 0.002)
    bm_box(bm, bx0, bx1, by0, CT - 0.004, bz0, bz0 + wt, 0.002)
    bm_box(bm, bx0, bx1, by0, CT - 0.004, bz1 - wt, bz1, 0.002)
    # rim flange (frame) around the opening
    for (a, b, c, d) in [(sx0, sx1, sz0, sz0 + 0.025), (sx0, sx1, sz1 - 0.025, sz1), (sx0, sx0 + 0.025, sz0, sz1), (sx1 - 0.025, sx1, sz0, sz1)]:
        bm_box(bm, a, b, CT - 0.004, CT + 0.004, c, d, 0.001)
    # drain
    bm_lathe(bm, [(0, 0), (0.03, 0), (0.03, 0.003), (0, 0.003)], (sx0 + sx1) / 2, (sz0 + sz1) / 2, by0 + wt, 24)
    bowl = finish("sink_bowl", bm, mt["sink_steel"], ((sx0 + sx1) / 2, CT, (sz0 + sz1) / 2), static=1,
                  extras={"interact": "look", "caption_id": "sink", "collider": "none"})
    out.append(bowl)
    fx, fz = 7.93, (sz0 + sz1) / 2
    bm = bmesh.new()
    bm_lathe(bm, [(0, 0), (0.028, 0), (0.028, 0.012), (0.018, 0.016), (0.0, 0.016)], fx, fz, CT, 24)
    bm_lathe(bm, [(0, 0.016), (0.012, 0.016), (0.012, 0.2), (0.0, 0.2)], fx, fz, CT, 20)
    arc = [(fx, CT + 0.2, fz)] + [(fx - 0.2 * (1 - math.cos(a)) * 1.0 - 0.0, CT + 0.2 + 0.1 * math.sin(a) * (1 - a / 3.2), fz) for a in [i * math.pi / 2 / 8 for i in range(1, 9)]]
    pts = [(fx - 0.17 * math.sin(a), CT + 0.2 + 0.12 * math.sin(a * 1.0) - 0.0 * a - 0.07 * (a / (math.pi * 0.6)) ** 2 * 0, fz) for a in [i * math.pi * 0.6 / 14 for i in range(15)]]
    pts = [(fx - 0.19 * (1 - math.cos(t)), CT + 0.2 + 0.085 * math.sin(t) - 0.085 * (t / 1.9) ** 2 * 0.0, fz) for t in [i * 1.9 / 14 for i in range(15)]]
    pts = [(fx - 0.2 * math.sin(t), CT + 0.2 + 0.07 * (1 - math.cos(t * 1.5)) * 0.0 + 0.1 * math.sin(min(t, 1.3)) - 0.12 * max(0, t - 1.3) ** 1.0, fz) for t in [i * 1.57 / 12 for i in range(13)]]
    pts = []
    for i in range(14):
        t = i / 13
        ang = t * math.pi * 0.62
        pts.append((fx - 0.2 * (1 - math.cos(ang)) / (1 - math.cos(math.pi * 0.62)) * 0.0 - 0.17 * math.sin(ang * 1.3) * 1.0, CT + 0.2 + 0.09 * math.sin(ang) - 0.03 * t * t, fz))
    bm_tube(bm, [(fx, CT + 0.19, fz)] + pts, 0.0095, 12)
    bm_box(bm, fx - 0.012, fx + 0.012, CT + 0.04, CT + 0.05, fz + 0.02, fz + 0.1, 0.003)  # side lever
    out.append(finish("sink_faucet", bm, mt["chrome"], (fx, CT, fz), static=1,
                      extras={"interact": "use", "use_kind": "sink", "caption_id": "sink_faucet", "collider": "none"}))
    return out


def lathe_obj(name, profile, mats, at, segs=32, extras=None, mesh=None, parts=None, static=0, parent=None):
    bm = bmesh.new()
    bm_lathe(bm, profile, at[0], at[2], at[1], segs)
    return finish(name, bm, mats, at, static=static, extras=extras, mesh=mesh, parent=parent)


def mugs(mt):
    out = []
    prof = [(0, 0), (0.034, 0), (0.038, 0.006), (0.041, 0.09), (0.042, 0.095), (0.038, 0.095), (0.0365, 0.09), (0.034, 0.008), (0, 0.006)]
    bm = bmesh.new()
    bm_lathe(bm, prof, 0, 0, 0, 24)
    pts = [(0.0, 0.07 + 0.032 * math.cos(a), 0.041 + 0.028 * math.sin(a) + 0.0) for a in [i * 2 * math.pi / 14 for i in range(14)]]
    pts = [(0, 0.052 + 0.034 * math.cos(a), 0.036 + 0.03 * math.sin(a)) for a in [i * 2 * math.pi / 14 for i in range(14)]]
    bm_tube(bm, pts, 0.0055, 8, closed=True)
    _finalize(bm)
    bmesh.ops.translate(bm, verts=bm.verts, vec=-G(0, 0, 0))
    mesh = bpy.data.meshes.new("mug_shared")
    bm.to_mesh(mesh)
    bm.free()
    # one shared material; per-colour meshes carry a uniform COLOR_0 (vertex colour) that multiplies base colour
    mug_mat = M("pantry_mug", (1, 1, 1), 0.18, coat=0.6)
    if not mug_mat.node_tree.nodes.get("mug_vcol"):
        nt = mug_mat.node_tree
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.name = "mug_vcol"
        vc.layer_name = "Col"
        nt.links.new(vc.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    meshes = {}

    def mug_mesh(k, c):
        if k not in meshes:
            me = mesh.copy()
            me.name = "mug_" + k
            me.materials.clear()
            me.materials.append(mug_mat)
            ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
            for i in range(len(ca.data)):
                ca.data[i].color = (*c, 1.0)
            meshes[k] = me
        return meshes[k]
    # ~15 mugs on the open shelf under the wall cabinet (shelf board top y 1.468; old frame x 7.65-8.0, z 1.9-3.25)
    cols = ["white", "brown", "navy", "red", "cream", "teal", "green", "black", "sage"]
    layout = []
    for k in range(13):  # z 2.6-3.23 only: the z 1.98-2.55 end of the shelf holds the kettle and bottles (photo 07-1)
        row, col = (0, k) if k < 7 else (1, k - 7)
        n_row = 7 if row == 0 else 6
        layout.append((cols[(k * 4) % len(cols)], 7.78 + 0.1 * row, 2.6 + (col + 0.5) * (0.63 / n_row), 0.35 * k, 1.45 + 0.018))
    for i, (c, x, z, rot, my) in enumerate(layout):
        o = bpy.data.objects.new(f"mug_{i + 1:02d}", mug_mesh(c, MUG_COLORS[c]))
        collection().objects.link(o)
        o.location = G(x, my, z)
        o.rotation_euler[2] = rot
        for k, v in {"static": 0, "interact": "grab", "caption_id": "mug", "mass": 0.3, "collider": "convex"}.items():
            o[k] = v
        out.append(o)
    # olive mug on the drying mat (counter)
    o = bpy.data.objects.new("mug_olive_counter", mug_mesh("olive", (0.18, 0.2, 0.05)))
    collection().objects.link(o)
    o.location = G(7.6, CT + 0.004, 3.0)
    o.rotation_euler[2] = 2.4
    for k, v in {"static": 0, "interact": "grab", "caption_id": "mug", "mass": 0.3, "collider": "convex"}.items():
        o[k] = v
    out.append(o)
    return out


def wall_cabinets(mt):
    out = []
    # old frame (see header): z 1.9-3.25 -> scan z 9.3-7.95 (three doors over the open mug shelf); z 1.4-1.9 is the microwave shelf
    x0, x1 = 7.65, 8.0
    z0, z1 = 1.9, 3.25
    t = 0.018
    bm = bmesh.new()
    bm_box(bm, x0, x1, 1.45, 1.45 + t, z0, z1, 0.002)       # open-shelf board
    bm_box(bm, x0, x1, 1.68, 1.7, z0, z1, 0.002)         # cabinet floor
    bm_box(bm, x0, x1, 2.38 - t, 2.38, z0, z1, 0.002)     # top
    bm_box(bm, x1 - 0.012, x1, 1.45, 2.38, z0, z1, 0.0)    # back
    bm_box(bm, x0, x1, 1.45, 2.38, z0, z0 + t, 0.002)
    bm_box(bm, x0, x1, 1.45, 2.38, z1 - t, z1, 0.002)
    body = finish("wall_cabinet_body", bm, mt["carcass"], ((x0 + x1) / 2, 1.915, (z0 + z1) / 2), static=1,
                  extras={"interact": "look", "caption_id": "wall_cabinet", "collider": "boxes",
                          "collider_boxes": collider_boxes(((x0 + x1) / 2, 1.915, (z0 + z1) / 2), [
                              (x0, x1, 1.45, 1.45 + t, z0, z1), (x0, x1, 1.68, 1.70, z0, z1), (x0, x1, 2.38 - t, 2.38, z0, z1),
                              (x1 - 0.012, x1, 1.45, 2.38, z0, z1), (x0, x1, 1.45, 2.38, z0, z0 + t), (x0, x1, 1.45, 2.38, z1 - t, z1)])})
    out.append(body)
    pitch = (z1 - z0 - 2 * t) / 3
    for i in range(3):
        za = z0 + t + i * pitch + 0.002
        zb = za + pitch - 0.004
        bm = bmesh.new()
        bm_box(bm, x0 - 0.018, x0, 1.682, 2.382, za, zb, 0.003)
        left = i < 2
        hz = za if left else zb
        d = finish(f"wall_cabinet_door_{i + 1:02d}", bm, mt["lam_grey"], (x0 - 0.009, 2.032, hz), parent=body, static=0,
                   extras={"interact": "use", "use_kind": "cabinet_door", "caption_id": "wall_cabinet_door", "collider": "box"})
        hinge(d, "y", 100, -1 if left else 1)
        out.append(d)
    # shelf for the microwave over the sink end (microwave sits at y 1.25, see SHIFT)
    bm = bmesh.new()
    bm_box(bm, x0 + 0.01, x1, 1.22, 1.236, 1.4, z0, 0.002)
    out.append(finish("microwave_shelf", bm, mt["carcass"], ((x0 + x1) / 2, 1.228, (1.4 + z0) / 2), static=1,
                      extras={"interact": "look", "caption_id": "wall_cabinet", "collider": "box"}))
    return out


def base_cabinets(mt):
    out = []
    n = 3
    w = 1.85 / n   # counter run 1.85 m [scan]
    xo = 0.1       # counter is 0.7 deep [scan]: doors sit 0.1 proud of the old 0.6 front
    for i in range(n):
        za = 1.405 + i * w + 0.002
        zb = 1.405 + (i + 1) * w - 0.002
        left = i % 2 == 0
        bm = bmesh.new()
        bm_box(bm, 7.378 - xo, 7.4 - xo, 0.06, CT - 0.03, za, zb, 0.003)
        hz = za if left else zb
        d = finish(f"base_cabinet_door_{i + 1:02d}", bm, mt["lam_white"], (7.389 - xo, (0.06 + CT - 0.03) / 2, hz), static=0,
                   extras={"interact": "use", "use_kind": "cabinet_door", "caption_id": "base_cabinet_door", "collider": "box"})
        hinge(d, "y", 100, -1 if left else 1)
        out.append(d)
        pz = zb - 0.04 if left else za + 0.04
        bm = bmesh.new()
        bm_box(bm, 7.362 - xo, 7.378 - xo, CT - 0.18, CT - 0.06, pz - 0.006, pz + 0.006, 0.004)
        for py in (CT - 0.17, CT - 0.07):
            bm_box(bm, 7.376 - xo, 7.38 - xo, py - 0.006, py + 0.006, pz - 0.004, pz + 0.004, 0.001)
        out.append(finish(f"base_cabinet_pull_{i + 1:02d}", bm, mt["chrome"], (7.37 - xo, CT - 0.12, pz), parent=d, extras={"interact": "look", "collider": "none"}))
    return out


def small_props(mt):
    out = []
    grab = lambda mass, cap: {"interact": "grab", "mass": mass, "caption_id": cap, "collider": "convex"}
    # purple 20 L water jug (upright, neck up, per photo 07) with pump hose to the wall socket
    jx, jz = 7.87, 2.9
    jr = 0.9  # radial scale: photo 07 jug is slimmer than first pass
    prof = [(0, 0), (0.1, 0), (0.125, 0.012), (0.135, 0.04), (0.135, 0.11), (0.131, 0.12), (0.135, 0.13), (0.135, 0.27), (0.131, 0.28), (0.135, 0.29),
            (0.135, 0.33), (0.12, 0.375), (0.085, 0.415), (0.048, 0.435), (0.034, 0.44), (0.034, 0.448), (0.0, 0.448)]
    bm = bmesh.new()
    prof = [(r * jr, h) for r, h in prof]
    bm_lathe(bm, prof, jx, jz, CT, 40)
    bm_lathe(bm, [(0, 0.44), (0.04, 0.44), (0.04, 0.49), (0.0, 0.49)], jx, jz, CT, 28, mi=1)
    jug = finish("water_jug_20l", bm, [mt["purple"], mt["purple_cap"]], (jx, CT, jz), extras=grab(1.2, "water_jug"))
    out.append(jug)
    pts = [(jx, CT + 0.49, jz), (jx, CT + 0.56, jz), (jx + 0.05, CT + 0.55, jz + 0.07), (7.97, CT + 0.45, jz + 0.15), (7.99, CT + 0.3, jz + 0.19)]
    sm = []
    for i in range(len(pts) - 1):
        for k in range(8):
            f = k / 8
            sm.append(tuple(pts[i][c] + (pts[i + 1][c] - pts[i][c]) * f for c in range(3)))
    sm.append(pts[-1])
    bm = bmesh.new()
    bm_tube(bm, sm, 0.006, 8)
    out.append(finish("water_jug_hose", bm, mt["hose"], pts[-1], static=1, extras={"interact": "look", "collider": "none"}))

    # small steel kettle + two soap bottles at the sink end of the open shelf (photo cabinets-07-1)
    sy = 1.45 + 0.018
    bm = bmesh.new()
    bm_lathe(bm, [(0, 0), (0.06, 0), (0.06, 0.02), (0, 0.02)], 7.82, 2.2, sy, 28, mi=1)
    bm_lathe(bm, [(0, 0.02), (0.058, 0.02), (0.07, 0.04), (0.068, 0.12), (0.05, 0.155), (0.04, 0.16), (0, 0.16)], 7.82, 2.2, sy, 28, mi=0)
    bm_lathe(bm, [(0, 0.16), (0.038, 0.16), (0.036, 0.175), (0.012, 0.185), (0, 0.185)], 7.82, 2.2, sy, 20, mi=1)
    bm_tube(bm, [(7.82 + 0.07 + 0.03 * math.sin(math.pi * (0.1 + 0.8 * i / 9)), sy + 0.09 + 0.055 * math.cos(math.pi * (0.1 + 0.8 * i / 9)), 2.2) for i in range(10)], 0.007, 8, mi=1)
    out.append(finish("shelf_kettle_01", bm, [mt["steel"], mt["blk"]], (7.82, sy, 2.2), extras={"interact": "grab", "mass": 0.8, "caption_id": "kettle", "collider": "convex"}))
    for i, (bz, col, h) in enumerate(((2.04, "soap_yel", 0.17), (2.4, "soap_grn", 0.15))):
        bm = bmesh.new()
        bm_lathe(bm, [(0, 0), (0.03, 0), (0.033, 0.006), (0.033, h - 0.04), (0.02, h - 0.015), (0.01, h - 0.01), (0, h - 0.01)], 7.9, bz, sy, 20)
        out.append(finish(f"shelf_bottle_{i + 1:02d}", bm, mt[col], (7.9, sy, bz), extras={"interact": "grab", "mass": 0.3, "caption_id": "bottle", "collider": "convex"}))
    # steel / black / glass flasks along the back edge
    def flask(name, r, h, body, cap, at, share=None, mass=0.3):
        prof = [(0, 0), (r - 0.006, 0), (r, 0.008), (r, h - 0.045), (r - 0.006, h - 0.038), (r - 0.0065, h - 0.034), (0, h - 0.034)]
        bm = bmesh.new()
        bm_lathe(bm, prof, 0, 0, 0, 28)
        bm_lathe(bm, [(0, h - 0.034), (r - 0.002, h - 0.034), (r, h - 0.03), (r, h - 0.004), (r - 0.003, h), (0, h)], 0, 0, 0, 28, mi=1)
        o = finish(name, bm, [body, cap], (0, 0, 0), extras=grab(mass, "flask"), mesh=share)
        o.location = G(*at)
        return o

    f1 = flask("steel_flask_01", 0.033, 0.27, mt["steel"], mt["steel"], (7.9, CT, 3.4))
    out.append(f1)
    o = bpy.data.objects.new("steel_flask_02", f1.data)
    collection().objects.link(o)
    o.location = G(7.93, CT, 3.3 + 0.0)
    o.location = G(7.78, CT, 3.33)
    for k, v in grab(0.3, "flask").items():
        o[k] = v
    o["static"] = 0
    out.append(o)
    out.append(flask("steel_tumbler_black", 0.037, 0.2, mt["blk"], mt["blk"], (7.9, CT, 3.18)))
    out.append(flask("steel_tumbler_01", 0.035, 0.15, mt["steel"], mt["blk"], (7.93, CT, 3.05)))
    out.append(flask("glass_bottle_01", 0.035, 0.25, mt["glass"], mt["steel"], (7.92, CT, 3.26 - 0.0 + 0.0)))
    out[-1].location = G(7.92, CT, 3.29)
    out[-3].location = G(7.9, CT, 3.18)
    out[-2].location = G(7.9, CT, 3.08)
    # small steel tumbler near the coffee machine
    bm = bmesh.new()
    bm_lathe(bm, [(0, 0), (0.032, 0), (0.035, 0.004), (0.036, 0.09), (0.033, 0.09), (0.032, 0.006), (0, 0.006)], 7.62, 3.86, CT, 28)
    t = finish("steel_cup_01", bm, mt["steel"], (7.62, CT, 3.86), extras=grab(0.12, "steel_cup"))
    out.append(t)
    # white glass storage jar with steel lid
    bm = bmesh.new()
    bm_lathe(bm, [(0, 0), (0.047, 0), (0.05, 0.006), (0.05, 0.165), (0.0, 0.165)], 7.72, 3.76, CT, 28)
    bm_lathe(bm, [(0, 0.165), (0.052, 0.165), (0.052, 0.182), (0.0, 0.182)], 7.72, 3.76, CT, 28, mi=1)
    out.append(finish("glass_jar_01", bm, [mt["frost"], mt["steel"]], (7.72, CT, 3.76), extras=grab(0.6, "glass_jar")))
    # pink hand-wash bottle beside the sink (scan x 7.32 z 9.4, on the counter strip beside the sink (x 7.2-7.4), clear of the drying mats (x <= 7.15): solid counter, it sat over the sink basin x 6.8-7.2 and rested on the mats)
    PBX, PBZ = 7.38, 1.8  # old frame; scan x = 14.7 - x, scan z = 11.2 - z (see main below)
    bm = bmesh.new()
    pk = 1.9  # photo-07: a large pink bottle (~0.4 m), not a hand-wash pump
    bm_lathe(bm, [(r * pk, h * pk) for r, h in [(0, 0), (0.032, 0), (0.036, 0.006), (0.036, 0.15), (0.03, 0.18), (0.014, 0.195), (0.012, 0.205), (0, 0.205)]], PBX, PBZ, CT, 24)
    bm_lathe(bm, [(r * pk, h * pk) for r, h in [(0, 0.2), (0.016, 0.2), (0.016, 0.235), (0.0, 0.235)]], PBX, PBZ, CT, 16, mi=1)
    out.append(finish("pink_bottle_01", bm, [mt["pink"], mt["white"]], (PBX, CT, PBZ), extras=grab(0.35, "bottle")))
    # tissue / paper dispenser
    bm = bmesh.new()
    bm_box(bm, 7.86, 7.98, CT, CT + 0.2, 3.44, 3.74, 0.008)
    bm_box_mi(bm, 1, 7.858, 7.862, CT + 0.14, CT + 0.15, 3.48, 3.70, 0.0005)
    out.append(finish("tissue_dispenser_01", bm, [mt["white"], mt["blk"]], (7.92, CT, 3.59), extras=grab(0.5, "tissue_dispenser")))
    # grey drying mats
    for i, mz in enumerate((2.85, 3.34)):
        bm = bmesh.new()
        bm_box(bm, 7.45, 7.70, CT, CT + 0.006, mz - 0.21, mz + 0.21, 0.002)
        out.append(finish(f"drying_mat_{i + 1:02d}", bm, mt["rubber"], (7.575, CT, mz), extras=grab(0.2, "drying_mat")))
    # sticky note (thin object, not a decal)
    bm = bmesh.new()
    bm_box(bm, -0.1, 0.1, 0.0, 0.0012, -0.09, 0.09, 0.0002)
    sn = finish("sticky_note_01", bm, mt["note"], (0, 0, 0), extras=grab(0.01, "sticky_note"))
    sn.location = G(7.8, CT + 0.0066, 2.36)
    sn.rotation_euler[2] = math.radians(-14)
    out.append(sn)
    # wall soap dispenser left of the sink: slim white cylinder, clear level window, steel pump at the bottom
    sxc, szc = 7.955, 1.755
    bm = bmesh.new()
    bm_box(bm, 7.985, 8.0, 1.19, 1.43, szc - 0.03, szc + 0.03, 0.003)
    bm_lathe(bm, [(0, 0), (0.033, 0), (0.035, 0.004), (0.035, 0.22), (0.032, 0.226), (0, 0.226)], sxc, szc, 1.2, 28)
    bm_box_mi(bm, 1, sxc - 0.0365, sxc - 0.03, 1.27, 1.37, szc - 0.011, szc + 0.011, 0.001)
    bm_lathe(bm, [(0, 0), (0.02, 0), (0.02, 0.025), (0.0, 0.025)], sxc, szc, 1.175, 20, mi=2)
    bm_box_mi(bm, 2, sxc - 0.05, sxc - 0.01, 1.178, 1.187, szc - 0.008, szc + 0.008, 0.002)
    out.append(finish("soap_dispenser_01", bm, [mt["white"], mt["frost"], mt["chrome"]], (sxc, 1.3, szc), static=1, extras={"interact": "look", "caption_id": "soap_dispenser", "collider": "none"}))
    # red dish cloth hung on the wall beside the dispenser
    bm = bmesh.new()
    bm_box(bm, 7.984, 7.992, 1.1, 1.42, 1.5, 1.68, 0.002)
    bm_lathe(bm, [(0, 0), (0.006, 0), (0.006, 0.02), (0, 0.02)], 7.975, 1.59, 1.42, 12, mi=1)
    out.append(finish("red_cloth_01", bm, [mt["red_cloth"], mt["chrome"]], (7.988, 1.26, 1.59), static=1, extras={"interact": "look", "caption_id": "cloth", "collider": "none"}))
    # soap tray with a yellow sponge beside the faucet
    bm = bmesh.new()
    bm_open_box(bm, 7.83, 7.95, 0.9, 0.93, 1.73, 1.84, 0.003, 0.004)
    bm_box_mi(bm, 1, 7.85, 7.93, 0.918, 0.945, 1.745, 1.825, 0.004)
    out.append(finish("sink_soap_tray", bm, [mt["white"], mt["yellow"]], (7.89, CT, 1.785), static=1, extras={"interact": "look", "caption_id": "sponge", "collider": "none"}))
    return out


def kettle(mt):
    px, py, pz = 7.8, CT, 1.62
    bm = bmesh.new()
    bm_lathe(bm, [(0, 0), (0.088, 0), (0.09, 0.004), (0.09, 0.034), (0, 0.034)], px, pz, py, 36, mi=1)
    bm_lathe(bm, [(0, 0.034), (0.074, 0.034), (0.088, 0.06), (0.086, 0.17), (0.064, 0.21), (0.054, 0.218), (0.0, 0.218)], px, pz, py, 36, mi=0)
    bm_lathe(bm, [(0, 0.218), (0.05, 0.218), (0.048, 0.232), (0.02, 0.24), (0.0, 0.242)], px, pz, py, 24, mi=1)
    sp = bmesh.ops.create_cube(bm, size=1)["verts"]
    for v in sp:  # spout wedge toward -x (front)
        top = v.co.z > 0
        v.co = G(px - 0.085 - 0.04 * (0.5 - v.co.x), py + 0.14 + v.co.z * 0.14, pz - v.co.y * (0.04 if top else 0.05))
    bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.is_valid])
    hp = []
    for i in range(14):
        a = math.pi * (0.1 + 0.8 * i / 13)
        hp.append((px + 0.09 + 0.045 * math.sin(a), py + 0.12 + 0.075 * math.cos(a), pz))
    bm_tube(bm, hp, 0.0085, 8, mi=1)
    return finish("kettle_01", bm, [mt["steel"], mt["blk"]], (px, py, pz),
                  extras={"interact": "use", "use_kind": "kettle", "caption_id": "kettle", "collider": "convex", "mass": 0.9})


def switch_plate(mt):
    x = 8.0
    z, y = 3.05, 1.1
    bm = bmesh.new()
    bm_box(bm, x - 0.012, x, y - 0.075, y + 0.075, z - 0.12, z + 0.12, 0.003)
    for r in range(2):
        for c in range(4):
            cz = z - 0.09 + c * 0.06
            cy = y - 0.035 + r * 0.07
            bm_box_mi(bm, 1, x - 0.02, x - 0.012, cy - 0.022, cy + 0.022, cz - 0.014, cz + 0.014, 0.002)
    return finish("light_switch_plate_01", bm, [mt["white"], mt["lam_white"]], (x - 0.006, y, z), static=1,
                  extras={"interact": "use", "use_kind": "light_switch", "caption_id": "light_switch", "collider": "none"})


def ceiling(mt):
    out = []
    cy = ROOM_H
    # 3 x 3 grid of 0.6 m LED panels over the 8.7 x 7.35 hall, plus 2 over the kitchen bay, which daylight barely reaches (ceiling fixtures are not measurable in the scan)
    for i, (x, z) in enumerate([(x, z) for x in (1.5, 4.35, 7.2) for z in (1.2, 3.7, 6.2)] + [(7.7, 8.0), (7.7, 9.3), (7.1, 8.65)]):  # [not measured] 3 x 3 grid + bay (last 3 = bay, boosted in bake_room.py)
        bm = bmesh.new()
        bm_box(bm, x - 0.3, x + 0.3, cy - 0.015, cy, z - 0.3, z + 0.3, 0.002)
        bm_box_mi(bm, 1, x - 0.285, x + 0.285, cy - 0.019, cy - 0.014, z - 0.285, z + 0.285, 0.001)
        out.append(finish(f"led_panel_{i + 1:02d}", bm, [mt["fan_white"], mt["led_off"]], (x, cy - 0.01, z), static=1,
                          extras={"interact": "look", "caption_id": "led_panel", "collider": "none", "emissive_on_strength": 6.0}))
    # ceiling fans: built by props/seating.py, one over each table
    return out


# ---------------------------------------------------------------- entry point
SHIFT = [  # old-frame (dx, dy, dz) for top-level objects, by name prefix: squeeze the 3.2 m run into the scan's 1.85 m counter
    (("sink_bowl", "sink_faucet"), (0, 0, -0.45)),
    (("soap_dispenser",), (0, 0, -0.25)), (("red_cloth",), (0, 0, 0.05)), (("sink_soap_tray",), (0, 0, -0.3)),
    (("kettle",), (0, 0, 0.40)),
    (("lg_microwave",), (0, 0, -1.985)),   # on the left (high-z) wall shelf above the sink, y 1.25 (wall_cabinets)
    (("tata_bistro", "coffee_"), (0, 0, -1.25)),    # was -1.37: sat inside the coffee machine block and was hidden
    (("steel_flask", "steel_tumbler", "glass_bottle", "glass_jar"), (0, 0.25, -0.9)),
    (("tissue_dispenser",), (0, 0.25, -1.1)),
    (("steel_cup",), (0, 0, -1.25)),
    (("water_jug_20l",), (-0.27, -CT, 0.5)),
    (("drying_mat_01",), (0.1, 0, -1.25)), (("drying_mat_02",), (0.1, 0, -0.95)),   # dx 0.1 = scan x -0.1: frees the counter strip x 7.2-7.4 for the pink bottle
    (("mug_olive",), (0, 0, -0.75)),
    (("light_switch",), (0, 0, 0.4)),
]
FRIDGE_NEW = dict(x0=6.9, z0=6.9, w=0.45, d=0.44, h=1.35)   # layout.FRIDGE [scan]


def _place():
    """Map the old-frame props onto the scan layout (see header)."""
    from mathutils import Matrix
    bpy.context.view_layer.update()
    objs = list(collection().objects)
    fr = [o for o in objs if o.name.startswith(("lg_fridge", "fridge_sticker"))]
    # 1) counter group: per-object shift, then 180 deg turn about the vertical onto the x=6.7 wall
    A = Matrix.Translation((14.7, -11.2, 0)) @ Matrix.Rotation(math.pi, 4, "Z")
    for o in objs:
        if o.parent is not None or o in fr or o.name.startswith("led_panel"):
            continue
        for names, (dx, dy, dz) in SHIFT:
            if o.name.startswith(names):
                o.location += Vector((dx, -dz, dy))
                bpy.context.view_layer.update()
        o.matrix_world = A @ o.matrix_world
        bpy.context.view_layer.update()
    # 2) fridge: warp meshes + origins to the scan footprint/height (no rotation: door faces -x into the hall)
    F = FRIDGE_NEW
    sx, sz, sy = F["w"] / 0.64, F["d"] / 0.555, F["h"] / 1.6

    def warp(p):
        return Vector((F["x0"] + sx * (p.x - 6.98), -(F["z0"] + sz * (-p.y - 0.2)), sy * p.z))
    data = []
    for o in fr:
        mw = o.matrix_world.copy()
        data.append((o, warp(mw.translation), [warp(mw @ v.co) for v in o.data.vertices]))
    for o, nw, vw in data:
        for v, w in zip(o.data.vertices, vw):
            v.co = w - nw
        o.data.update()
    def depth(o):
        d = 0
        while o.parent:
            o, d = o.parent, d + 1
        return d
    for o, nw, _ in sorted(data, key=lambda t: depth(t[0])):
        o.matrix_world = Matrix.Translation(nw)
        bpy.context.view_layer.update()


def build(context=None):
    global ROOM_W, ROOM_H, COUNTER_Z0, DX, DZ
    DX = DZ = 0.0   # props are authored in the old frame; _place() maps them (TASK-1.17)
    ce = bpy.data.objects.get("ceiling")
    if ce is not None:
        ROOM_H = min((ce.matrix_world @ Vector(v)).z for v in ce.bound_box)
    for n in ("fridge",):  # blockout stand-ins replaced by the detailed props
        o = bpy.data.objects.get(n)
        if o is not None:
            bpy.data.objects.remove(o)
    mt = materials()
    objs = []
    for fn in (fridge, microwave, coffee_machine, counter_items, mugs, wall_cabinets, base_cabinets, small_props, ceiling):
        r = fn(mt)
        objs += r
    objs += [kettle(mt), switch_plate(mt)]
    for o in list(objs):   # not in the scan / no room on the 1.85 m counter
        if o.name in ("sticky_note_01", "water_jug_hose", "sink_soap_tray"):
            objs.remove(o)
            bpy.data.objects.remove(o)
    _place()
    names = [o.name for o in objs]
    assert len(names) == len(set(names)), "duplicate names"
    tris = 0
    for o in objs:
        me = o.data
        if hasattr(me, "polygons"):
            tris += sum(len(p.vertices) - 2 for p in me.polygons)
    print(f"pantry: {len(objs)} objects, ~{tris} tris (mug instances counted per object)")
    return objs
