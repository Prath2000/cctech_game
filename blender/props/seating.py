"""Seating-zone props (TASK-1.7, seating half). Module API: build(context) -> list of root objects.

Authoring coords are GAME metres (x east, y up, z south, see docs/reference/pantry-reference-sheet.md);
mapped to Blender (x, -z, y) so the glTF exporter's +Y up restores game coords.
Every prop mesh is authored in a local frame: origin = floor centre, FRONT = +x, viewer-right = -z.
Repeated items (chairs, tables, glasses, spirals, bottles, fans) share mesh datablocks -> glTF instances.
"""
import bpy, bmesh, os, sys, math, random
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "blender"))
import layout as L
DECAL = os.path.join(ROOT, "assets", "decals", "seating")
SERIF = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
SANS = "/System/Library/Fonts/Supplemental/Arial.ttf"

# ---------------------------------------------------------------- materials
def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

_mats = {}
def mat(name, hexcol, rough=0.5, metal=0.0, alpha=1.0, emit=None, spec=0.5):
    name = "sx_" + name
    if name in _mats and name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hexcol), 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    if emit:
        b.inputs["Emission Color"].default_value = (*lin(emit[0]), 1)
        b.inputs["Emission Strength"].default_value = emit[1]
    _mats[name] = True
    return m

def M():
    return dict(
        black=mat("vend_black", "#15171a", 0.45), black_gl=mat("black_gloss", "#0c0d0f", 0.2),
        glass=mat("vend_glass", "#dfeaf0", 0.03, alpha=0.1), clear=mat("glass_clear", "#e8f2f4", 0.03, alpha=0.2),
        green=mat("flap_green", "#5db83a", 0.4), led=mat("led_white", "#e6f2ff", 0.3, emit=("#dcecff", 6.0)),
        screen=mat("screen", "#e8f0f5", 0.2, emit=("#e8f0f5", 1.2)), grey=mat("int_grey", "#cfd3d6", 0.6),
        steel=mat("steel", "#b9bbbd", 0.3, metal=1.0), coil=mat("coil_steel", "#8e9296", 0.35, metal=1.0),
        white=mat("white_plastic", "#f3f5f6", 0.22), blue=mat("blue_plastic", "#1f9ad6", 0.3),
        blue_dk=mat("blue_dark", "#14709f", 0.4), fabric=mat("blue_fabric", "#1c6ec0", 0.92),
        yellow=mat("yellow_trim", "#e8c53a", 0.8), vinyl=mat("clear_vinyl", "#cfe6f2", 0.15, alpha=0.45),
        red=mat("red_plastic", "#d4252b", 0.4), taphot=mat("tap_red", "#d6201f", 0.4),
        chair_g=mat("chair_green", "#8a9a35", 0.45), chair_b=mat("chair_blue", "#3a98dc", 0.45),
        foot=mat("foot_black", "#17181a", 0.7), lam=mat("table_laminate", "#f2f3f4", 0.3),
        edge=mat("table_edge", "#dfe1e2", 0.4), bin_green=mat("bin_green", "#2c8c5a", 0.5),
        text_w=mat("text_white", "#f4f4f2", 0.5), text_k=mat("text_black", "#0a0a0a", 0.5),
        fan_w=mat("fan_white", "#f1f1ef", 0.5), glassw=mat("tumbler_glass", "#dfeaee", 0.04, alpha=0.3),
        ketchup=mat("ketchup_red", "#b3201f", 0.35), cap_w=mat("cap_white", "#eeeeee", 0.5),
        wall=mat("mural_vinyl", "#ffffff", 0.55),
        b1=mat("bottle_pink", "#e24f8a", 0.25), b2=mat("bottle_orange", "#f08a1c", 0.25),
        b3=mat("bottle_green", "#6cc04a", 0.25), b4=mat("bottle_blue", "#2a62c9", 0.25),
        can=mat("can_silver", "#c8ccd0", 0.25, metal=1.0), can_r=mat("can_red", "#c0262a", 0.3, metal=0.6),
        sn1=mat("snack_red", "#cc2a2b", 0.35), sn2=mat("snack_orange", "#ee7a1e", 0.35),
        sn3=mat("snack_blue", "#2b5fb8", 0.35), sn_label=mat("snack_label", "#f2d34a", 0.4),
    )

# ---------------------------------------------------------------- mesh builder
def gv(x, y, z):
    return Vector((x, -z, y))

class MB:
    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _add(self, tmp, m):
        bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces[:])
        i, vm = self.mi(m), {}
        for v in tmp.verts:
            vm[v] = self.bm.verts.new(v.co)
        for f in tmp.faces:
            try:
                nf = self.bm.faces.new([vm[v] for v in f.verts])
            except ValueError:
                continue
            nf.material_index = i
            nf.smooth = True
        tmp.free()

    def box(self, c, s, m, bevel=0.004, rot=None):
        t = bmesh.new()
        r = bmesh.ops.create_cube(t, size=1.0)
        bmesh.ops.scale(t, vec=(s[0], s[2], s[1]), verts=t.verts[:])
        b = min(bevel, min(s) * 0.4)
        if b > 5e-4:
            bmesh.ops.bevel(t, geom=t.verts[:] + t.edges[:], offset=b, segments=2, affect="EDGES")
        if rot:  # rotation about game y (vertical) in radians
            bmesh.ops.rotate(t, verts=t.verts[:], cent=(0, 0, 0), matrix=Matrix.Rotation(rot, 3, "Z"))
        bmesh.ops.translate(t, vec=gv(*c), verts=t.verts[:])
        self._add(t, m)

    def tube(self, p0, p1, r, m, seg=8, r1=None):
        a, b = gv(*p0), gv(*p1)
        d = b - a
        t = bmesh.new()
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        bmesh.ops.create_cone(t, cap_ends=True, segments=seg, radius1=r if r1 is None else r1, radius2=r,
                              depth=d.length, matrix=Matrix.Translation((a + b) / 2) @ rot)
        self._add(t, m)

    def cyl(self, c, r, h, m, axis="y", seg=16, r2=None, bevel=0.0):
        a = {"y": (0, 0, 1), "x": (1, 0, 0), "z": (0, 1, 0)}[axis]  # blender axis of game axis
        h2 = h / 2
        p0 = [c[0], c[1], c[2]]
        p1 = list(p0)
        i = {"x": 0, "y": 1, "z": 2}[axis]
        p0[i] -= h2
        p1[i] += h2
        self.tube(p0, p1, r if r2 is None else r2, m, seg, r1=r)

    def lathe(self, c, prof, m, seg=14):
        """prof: [(radius, y)] bottom->top about the game y axis."""
        t = bmesh.new()
        rings = []
        for rr, y in prof:
            rings.append([t.verts.new(gv(c[0] + rr * math.cos(2 * math.pi * k / seg), c[1] + y,
                                         c[2] + rr * math.sin(2 * math.pi * k / seg))) for k in range(seg)])
        for a, b in zip(rings, rings[1:]):
            for k in range(seg):
                q = [a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]]
                if len(set(q)) == 4:
                    try:
                        t.faces.new(q)
                    except ValueError:
                        pass
        for rg, rr in ((rings[0], prof[0][0]), (rings[-1], prof[-1][0])):
            if rr > 1e-5:
                t.faces.new(rg)
        bmesh.ops.remove_doubles(t, verts=t.verts[:], dist=1e-6)
        self._add(t, m)

    def panel(self, fn, nu, nv, thick, m):
        t = bmesh.new()
        g = [[t.verts.new(gv(*fn(-1 + 2 * i / nu, -1 + 2 * j / nv))) for j in range(nv + 1)] for i in range(nu + 1)]
        for i in range(nu):
            for j in range(nv):
                t.faces.new([g[i][j], g[i + 1][j], g[i + 1][j + 1], g[i][j + 1]])
        bmesh.ops.solidify(t, geom=t.faces[:], thickness=thick)
        self._add(t, m)

    def text(self, body, pos, size, m, font=SANS, extrude=0.0015, align="CENTER"):
        cu = bpy.data.curves.new("tmp_text", "FONT")
        cu.body, cu.size, cu.extrude, cu.align_x, cu.align_y = body, size, extrude, align, "CENTER"
        if os.path.exists(font):
            cu.font = bpy.data.fonts.load(font)
        o = bpy.data.objects.new("tmp_text", cu)
        bpy.context.scene.collection.objects.link(o)
        me = bpy.data.meshes.new_from_object(o)
        bpy.data.objects.remove(o)
        bpy.data.curves.remove(cu)
        # text X -> viewer right (blender +y), text Y -> up (+z), text normal -> front (+x)
        mx = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0))).to_4x4()
        mx = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        me.transform(Matrix.Translation(gv(*pos)) @ mx)
        t = bmesh.new()
        t.from_mesh(me)
        bpy.data.meshes.remove(me)
        self._add(t, m)

    def finish(self, name, lightmap=False):
        bm = self.bm
        for e in bm.edges:
            if len(e.link_faces) == 2:
                n0, n1 = e.link_faces[0].normal, e.link_faces[1].normal
                e.smooth = n0.length < 1e-6 or n1.length < 1e-6 or n0.angle(n1) < math.radians(35)
        me = bpy.data.meshes.new(name)
        bm.loops.layers.uv.new("UVMap")
        bm.to_mesh(me)
        bm.free()
        for m in self.mats:
            me.materials.append(m)
        if lightmap:
            add_lightmap_uv(me)
        return me

def add_lightmap_uv(me):
    lm = me.uv_layers.new(name="lightmap")
    me.uv_layers.active = lm
    o = bpy.data.objects.new("tmp_uv", me)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.objects.remove(o)
    me.uv_layers.active = me.uv_layers["UVMap"]

# ---------------------------------------------------------------- object helpers
_col = None
def put(name, me, loc, rot=(0, 0, 0), parent=None, props=None):
    o = bpy.data.objects.new(name, me)
    _col.objects.link(o)
    o.location = gv(*loc)
    o.rotation_euler = rot
    if parent:
        o.parent = parent
    for k, v in (props or {}).items():
        o[k] = v
    return o

def face_rot(dx, dz):  # blender z rotation so local +x faces game direction (dx, dz)
    return (0, 0, math.atan2(-dz, dx))

def P(static, interact="look", **kw):
    d = {"static": static, "interact": interact}
    d.update(kw)
    return d

def empty_prop(d):  # children of a prop: no own collider, same static flag
    return {"static": d["static"], "collider": "none"}

# ---------------------------------------------------------------- prop meshes
def mesh_spiral(ms):
    b = MB()
    turns, seg, R, L = 8, 6, 0.04, 0.48
    n = turns * seg
    ring = []
    for i in range(n + 1):
        a = 2 * math.pi * i / seg
        x = L * i / n
        c = Vector((x, math.cos(a) * R, math.sin(a) * R))
        row = []
        for k in range(4):
            ph = math.pi / 2 * k
            row.append(b.bm.verts.new(gv(x + 0.004 * math.sin(ph), math.cos(a) * (R + 0.004 * math.cos(ph)), math.sin(a) * (R + 0.004 * math.cos(ph)))))
        ring.append(row)
    for i in range(n):
        for k in range(4):
            b.bm.faces.new([ring[i][k], ring[i][(k + 1) % 4], ring[i + 1][(k + 1) % 4], ring[i + 1][k]]).material_index = b.mi(ms["coil"])
    bmesh.ops.recalc_face_normals(b.bm, faces=b.bm.faces[:])
    return b.finish("mesh_vend_spiral")

def mesh_bottle(ms, col, name, h=0.19, r=0.032):
    b = MB()
    prof = [(0, 0), (r * 0.8, 0), (r, 0.01), (r, h * 0.58), (r * 0.9, h * 0.68), (r * 0.42, h * 0.8), (r * 0.36, h * 0.86), (0, h * 0.86)]
    b.lathe((0, 0, 0), prof, ms[col], 12)
    b.cyl((0, h * 0.9, 0), r * 0.4, h * 0.08, ms["cap_w"], seg=10)
    b.cyl((0, h * 0.34, 0), r * 1.01, h * 0.28, ms["text_w"], seg=12)  # label band
    return b.finish(name)

def mesh_can(ms, col, name):
    b = MB()
    b.cyl((0, 0.065, 0), 0.033, 0.13, ms[col], seg=12)
    b.cyl((0, 0.131, 0), 0.027, 0.005, ms["can"], seg=12)
    return b.finish(name)

def mesh_snack(ms, col, name):
    """Foil packet standing, facing +x: 0.16 wide (z) x 0.22 high x 0.03 thick."""
    b = MB()
    def fn(u, v):
        bulge = 0.016 * (1 - u * u) * (1 - 0.6 * abs(v)) ** 0.5
        return (bulge, 0.11 + 0.11 * v, 0.08 * u)
    b.panel(fn, 6, 8, 0.004, ms[col])
    b.box((0.017, 0.11, 0), (0.002, 0.07, 0.11), ms["sn_label"], 0.0005)
    b.box((0.0, 0.215, 0), (0.012, 0.012, 0.16), ms[col], 0.002)
    b.box((0.0, 0.005, 0), (0.012, 0.012, 0.16), ms[col], 0.002)
    return b.finish(name)

def mesh_glass(ms):
    b = MB()
    b.lathe((0, 0, 0), [(0, 0), (0.026, 0), (0.028, 0.004), (0.036, 0.11), (0.0335, 0.11), (0.025, 0.012), (0, 0.012)], ms["glassw"], 16)
    return b.finish("mesh_glass_tumbler")

def mesh_tumbler_steel(ms):
    b = MB()
    b.lathe((0, 0, 0), [(0, 0), (0.03, 0), (0.036, 0.1), (0.034, 0.1), (0.0, 0.01)], ms["steel"], 16)
    return b.finish("mesh_steel_tumbler")

def mesh_chair(ms, shell, name):
    b = MB()
    def sq(u, v, n=4):
        d = (abs(u) ** n + abs(v) ** n) ** (1 / n)
        k = max(abs(u), abs(v)) / d if d > 1e-9 else 0
        return u * k, v * k
    def seat(u, v):
        pu, pv = sq(u, v)
        return (pu * 0.215, 0.436 + 0.02 * (pu * pu + pv * pv) / 2, pv * 0.215)
    def back(u, v):
        pu, pv = sq(u, v)
        s = (pv + 1) / 2
        return (-0.2 - 0.056 * s + 0.04 * pu * pu, 0.575 + 0.28 * s, pu * 0.205)
    b.panel(seat, 12, 12, 0.014, ms[shell])
    b.panel(back, 12, 10, 0.012, ms[shell])
    st = ms["steel"]
    for sz in (-1, 1):
        b.tube((0.215, 0.012, sz * 0.2), (0.175, 0.43, sz * 0.18), 0.0105, st)
        b.tube((-0.225, 0.012, sz * 0.2), (-0.185, 0.43, sz * 0.18), 0.0105, st)
        b.tube((-0.185, 0.43, sz * 0.18), (-0.225, 0.64, sz * 0.17), 0.0105, st)
        b.cyl((0.215 + 0.0, 0.007, sz * 0.2), 0.015, 0.016, ms["foot"], seg=8)
        b.cyl((-0.225, 0.007, sz * 0.2), 0.015, 0.016, ms["foot"], seg=8)
        b.tube((0.175, 0.415, sz * 0.18), (-0.185, 0.415, sz * 0.18), 0.008, st, 6)
    b.tube((0.175, 0.415, -0.18), (0.175, 0.415, 0.18), 0.008, st, 6)
    b.tube((-0.185, 0.415, -0.18), (-0.185, 0.415, 0.18), 0.008, st, 6)
    b.tube((-0.225, 0.64, -0.17), (-0.225, 0.64, 0.17), 0.009, st, 6)
    return b.finish(name)

def mesh_table(ms):
    b = MB()
    b.box((0, 0.735, 0), (L.TABLE_L, 0.03, L.TABLE_W), ms["lam"], 0.006)
    b.box((0, 0.718, 0), (L.TABLE_L, 0.004, L.TABLE_W), ms["edge"], 0.001)
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.box((sx * (L.TABLE_L / 2 - 0.07), 0.36, sz * (L.TABLE_W / 2 - 0.065)), (0.035, 0.72, 0.035), ms["steel"], 0.004)
            b.box((sx * (L.TABLE_L / 2 - 0.07), 0.01, sz * (L.TABLE_W / 2 - 0.065)), (0.05, 0.02, 0.05), ms["foot"], 0.004)
    for sz in (-1, 1):
        b.box((0, 0.68, sz * (L.TABLE_W / 2 - 0.065)), (L.TABLE_L - 0.14, 0.035, 0.03), ms["steel"], 0.003)
    for sx in (-1, 1):
        b.box((sx * (L.TABLE_L / 2 - 0.07), 0.68, 0), (0.03, 0.035, L.TABLE_W - 0.13), ms["steel"], 0.003)
    return b.finish("mesh_cafeteria_table", lightmap=True)

def mesh_fan(ms, H=3.0):
    b = MB()
    b.cyl((0, H - 0.03, 0), 0.06, 0.06, ms["fan_w"], seg=14)           # canopy (ceiling 3.0)
    b.cyl((0, H - 0.18, 0), 0.012, 0.3, ms["fan_w"], seg=8)             # downrod
    b.cyl((0, H - 0.34, 0), 0.1, 0.1, ms["fan_w"], seg=18, r2=0.09)     # motor
    for i in range(3):
        a = i * 2 * math.pi / 3
        ca, sa = math.cos(a), math.sin(a)
        b.box((ca * 0.36, H - 0.4, sa * 0.36), (0.5, 0.01, 0.12), ms["fan_w"], 0.004, rot=-a)
        b.box((ca * 0.14, H - 0.4, sa * 0.14), (0.1, 0.012, 0.03), ms["steel"], 0.003, rot=-a)
    return b.finish("mesh_ceiling_fan", lightmap=True)

# ---------------------------------------------------------------- composite props
def build_vending(ms, shared, zc):
    """PUSH snack vending machine. 0.85 W (z) x 0.8 D (x) x 1.85 H; front +x."""
    D2, W2, H = 0.4, 0.425, 1.85
    b = MB()
    k, bl = ms["black"], ms["black_gl"]
    gx0, gx1, gy0, gy1 = -0.36, 0.36, 0.42, 1.75  # glass opening (z, y)
    cy = (gy0 + gy1) / 2
    gh = gy1 - gy0
    # carcass: posts, top block, bottom block, sides, back, top, with the glass opening left clear
    for sz in (-1, 1):
        b.box((0, 0.03 + (H - 0.03) / 2, sz * 0.396), (0.8, H - 0.03, 0.058), k, 0.012)          # front posts (z beyond glass)
        b.box((0, cy, sz * 0.4235), (0.8, gh, 0.003), k, 0.0)                                      # side skin
    b.box((0, (gy1 + H) / 2, 0), (0.8, H - gy1, 0.85), k, 0.012)                                   # top block
    b.box((0, (0.03 + gy0) / 2, 0), (0.8, gy0 - 0.03, 0.85), k, 0.012)                             # bottom block (PUSH, flap)
    b.box((-0.395, cy, 0), (0.01, gh, 0.8), k, 0.0)                                                # back
    b.box((0, 0.015, 0), (0.72, 0.03, 0.78), bl, 0.003)
    b.box((-0.385, cy, 0), (0.008, gh, gx1 * 2), ms["grey"], 0.0)                                  # lit interior back
    for sz in (-1, 1):
        b.box((0, cy, sz * (gx1 - 0.002)), (0.77, gh, 0.004), ms["grey"], 0.0)
    b.box((0, gy1 - 0.003, 0), (0.77, 0.004, gx1 * 2), ms["grey"], 0.0)
    b.box((0, gy0 + 0.003, 0), (0.77, 0.004, gx1 * 2), ms["grey"], 0.0)
    b.box((0.05, gy1 - 0.02, 0.0), (0.04, 0.012, gx1 * 2 - 0.1), ms["led"], 0.0)   # top LED strips
    b.box((0.25, gy1 - 0.02, 0.0), (0.04, 0.012, gx1 * 2 - 0.1), ms["led"], 0.0)
    for sz in (-1, 1):
        b.box((0.37, 1.05, sz * 0.347), (0.015, 1.25, 0.012), ms["led"], 0.0)
    # glass front + frame lips
    b.box((D2 + 0.004, (gy0 + gy1) / 2, 0), (0.006, gy1 - gy0, gx1 * 2), ms["glass"], 0.0)
    b.box((D2 + 0.006, gy1 + 0.015, 0), (0.014, 0.03, 0.78), bl, 0.003)
    b.box((D2 + 0.006, gy0 - 0.015, 0), (0.014, 0.03, 0.78), bl, 0.003)
    for sz in (-1, 1):
        b.box((D2 + 0.006, (gy0 + gy1) / 2, sz * 0.375), (0.014, gy1 - gy0, 0.025), bl, 0.003)
    # shelves + labels
    rows = [0.53, 0.69, 0.87, 1.04, 1.23, 1.43]
    for y in rows:
        b.box((0.03, y - 0.006, 0), (0.72, 0.012, 0.7), ms["steel"], 0.002)
        b.box((D2 - 0.03, y + 0.002, 0), (0.012, 0.018, 0.68), ms["text_w"], 0.001)
    # lower panel: PUSH text, delivery flap, keypad, card plate
    b.text("PUSH", (D2 + 0.0035, 0.355, 0.0), 0.07, ms["text_w"], SERIF, 0.003)
    b.box((D2 + 0.004, 0.17, 0.013), (0.012, 0.19, 0.37), ms["green"], 0.006)
    b.box((D2 + 0.012, 0.17, 0.013), (0.012, 0.16, 0.33), ms["green"], 0.004)
    b.box((D2 + 0.016, 0.26, 0.013), (0.02, 0.012, 0.16), k, 0.004)  # pull
    b.box((D2 + 0.01, 0.255, 0.013), (0.002, 0.012, 0.13), ms["led"], 0.0)
    b.box((D2 + 0.006, 0.14, -0.315), (0.012, 0.15, 0.16), bl, 0.004)  # keypad housing
    for r_ in range(4):
        for c_ in range(3):
            b.box((D2 + 0.0135, 0.19 - r_ * 0.03, -0.315 + (c_ - 1) * 0.04), (0.006, 0.02, 0.028), ms["grey"], 0.002)
    b.box((D2 + 0.006, 0.9, 0.395), (0.012, 0.06, 0.03), ms["steel"], 0.004)  # lock plate
    # payment tablet on bracket (viewer-right = -z)
    b.box((D2 + 0.02, 1.36, -0.27), (0.016, 0.32, 0.2), ms["black"], 0.01)
    b.box((D2 + 0.0295, 1.36, -0.27), (0.002, 0.29, 0.175), ms["screen"], 0.003)
    b.box((D2 + 0.01, 1.36, -0.27), (0.02, 0.1, 0.04), k, 0.004)
    # glass-side faces of frame at corners
    me = b.finish("mesh_vending_body", lightmap=True)
    root = put("vending_machine", me, (0.405, 0.0, zc), face_rot(1, 0), props=P(1, "use", use_kind="vending", collider="box", caption_id="vending_machine"))
    # spirals + products (shared meshes)
    rng = random.Random(3)
    cols = [0.30 - i * 0.1 for i in range(7)]
    content = {1.43: None, 1.23: "snack", 1.04: "snack", 0.87: "bottle", 0.69: "can", 0.53: "can"}
    n_s = n_i = 0
    for y in rows:
        for z in cols:
            n_s += 1
            put(f"vend_spiral_{n_s:02d}", shared["spiral"], (-0.1, y + 0.05, z), parent=root, props=empty_prop(root))
            kind = content[y]
            if kind is None or rng.random() < 0.2:
                continue
            n_i += 1
            if kind == "snack":
                put(f"vend_snack_{n_i:02d}", shared["sn"][rng.randrange(3)], (0.22, y + 0.008, z), parent=root, props=empty_prop(root))
            elif kind == "bottle":
                put(f"vend_bottle_{n_i:02d}", shared["bt"][rng.randrange(4)], (0.2, y, z), parent=root, props=empty_prop(root))
            else:
                put(f"vend_can_{n_i:02d}", shared["can"][rng.randrange(2)], (0.2, y, z), parent=root, props=empty_prop(root))
    return root

def build_cooler(ms, idx, loc, tumbler):
    """Voltas floor-standing hot/cold dispenser with 19 L bottle in a blue cover; front +x."""
    b = MB()
    W, Dp = 0.30, 0.35
    b.box((0, 0.025, 0), (0.4, 0.05, 0.31), ms["blue"], 0.006)                      # base tray
    for sx in (-1, 1):
        b.box((sx * 0.19, 0.06, 0), (0.02, 0.04, 0.31), ms["blue"], 0.004)
    for sz in (-1, 1):
        b.box((0, 0.06, sz * 0.15), (0.4, 0.04, 0.02), ms["blue"], 0.004)
    b.box((0, 0.5, 0), (Dp, 0.9, W), ms["white"], 0.012)                           # body
    b.box((0.0, 0.93, 0), (Dp + 0.008, 0.03, W + 0.008), ms["white"], 0.01)          # top lip
    b.box((Dp / 2 + 0.002, 0.78, 0), (0.006, 0.17, W - 0.04), ms["white"], 0.004)     # tap panel
    b.box((Dp / 2 + 0.003, 0.44, 0), (0.004, 0.05, 0.001), ms["grey"], 0.0)
    b.box((Dp / 2 - 0.02, 0.52, 0), (0.06, 0.2, W - 0.1), ms["black_gl"], 0.004)     # recess behind drip tray
    b.box((Dp / 2 + 0.03, 0.4, 0), (0.1, 0.035, W - 0.06), ms["blue"], 0.006)         # drip tray
    b.box((Dp / 2 + 0.082, 0.4, 0), (0.002, 0.03, W - 0.1), ms["blue_dk"], 0.0)
    b.box((Dp / 2 + 0.05, 0.4175, 0), (0.07, 0.003, W - 0.09), ms["blue_dk"], 0.0)   # grill
    b.box((0.0, 0.24, Dp / 2 - 0.2), (0.0, 0.0, 0.0), ms["white"], 0.0) if False else None
    for sz, tm in ((-0.07, "blue"), (0.0, "white"), (0.07, "taphot")):
        b.box((Dp / 2 + 0.012, 0.74, sz), (0.02, 0.025, 0.025), ms[tm], 0.004)
        b.cyl((Dp / 2 + 0.03, 0.725, sz), 0.009, 0.035, ms["steel"], seg=8)
        b.box((Dp / 2 + 0.008, 0.768, sz), (0.004, 0.012, 0.02), ms["taphot"] if tm != "blue" else ms["blue"], 0.0)
    b.text("VOLTAS", (Dp / 2 + 0.0055, 0.86, 0.0), 0.022, ms["blue"], SANS, 0.001)
    b.box((Dp / 2 + 0.0055, 0.8, 0.075), (0.002, 0.04, 0.04), ms["text_w"], 0.0)     # REFILL QR sticker
    b.box((Dp / 2 + 0.0065, 0.8, 0.075), (0.002, 0.03, 0.03), ms["text_k"], 0.0)
    b.cyl((0, 0.96, 0), 0.115, 0.02, ms["white"], seg=24)                            # bottle neck seat
    # bottle in blue cover with clear vinyl window + yellow trim
    b.cyl((0, 0.97, 0), 0.138, 0.02, ms["yellow"], seg=28)
    b.cyl((0, 1.19, 0), 0.135, 0.42, ms["fabric"], seg=28)
    b.lathe((0, 0, 0), [(0.135, 1.4), (0.125, 1.43), (0.09, 1.455), (0.0, 1.465)], ms["fabric"], 28)
    b.box((0.131, 1.19, 0), (0.012, 0.36, 0.09), ms["vinyl"], 0.003)
    me = b.finish(f"mesh_cooler_{idx:02d}", lightmap=True)
    root = put(f"cooler_{idx:02d}", me, loc, face_rot(1, 0), props=P(1, "use", use_kind="cooler", collider="box", caption_id="water_cooler"))
    return root

def build_bin(ms, name, loc, face, front, label):
    b = MB()
    b.box((0, 0.33, 0), (0.35, 0.66, 0.35), ms["steel"], 0.02)
    b.box((0, 0.69, 0), (0.37, 0.05, 0.37), ms["steel"], 0.015)
    b.box((0.01, 0.725, 0), (0.2, 0.02, 0.2), ms["black"], 0.008)
    b.box((0.177, 0.33, 0), (0.004, 0.45, 0.29), ms[front], 0.003)
    b.text(label, (0.1805, 0.38, 0), 0.045, ms["text_w"], SANS, 0.001)
    b.box((0, 0.012, 0), (0.33, 0.024, 0.33), ms["foot"], 0.004)
    me = b.finish("mesh_" + name, lightmap=True)
    return put(name, me, loc, face_rot(*face), props=P(1, "look", collider="box", caption_id="waste_bin"))

def build_mural(D):
    me = bpy.data.meshes.new("mesh_mural_circuit_arrow")
    z0, z1, y0, y1 = D - 1.6, D, 1.2, 2.32
    vs = [gv(0.004, y0, z1), gv(0.004, y0, z0), gv(0.004, y1, z0), gv(0.004, y1, z1)]
    me.from_pydata(vs, [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for loop, p in zip(me.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[loop.index].uv = p
    m = bpy.data.materials.new("sx_mural_circuit_arrow")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    tx = m.node_tree.nodes.new("ShaderNodeTexImage")
    p = os.path.join(DECAL, "mural_circuit_arrow.jpg")
    if os.path.exists(p):
        tx.image = bpy.data.images.load(p)
    m.node_tree.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    me.materials.append(m)
    add_lightmap_uv(me)
    return put("mural_circuit_arrow", me, (0, 0, 0), props=P(1, "look", collider="none", caption_id="circuit_mural"))

# ---------------------------------------------------------------- entry
def build(context=None):
    global _col
    ms = M()
    _col = bpy.data.collections.get("seating") or bpy.data.collections.new("seating")
    if _col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(_col)
    # replace blockout placeholders
    for o in list(bpy.data.objects):
        if o.name in ("vending_machine", "cooler_01", "cooler_02") or o.name.startswith("table_"):
            bpy.data.objects.remove(o)
    shared = dict(
        spiral=mesh_spiral(ms),
        bt=[mesh_bottle(ms, c, f"mesh_bottle_{c}") for c in ("b1", "b2", "b3", "b4")],
        can=[mesh_can(ms, "can", "mesh_can_silver"), mesh_can(ms, "can_r", "mesh_can_red")],
        sn=[mesh_snack(ms, c, f"mesh_snack_{c}") for c in ("sn1", "sn2", "sn3")],
    )
    # layout comes from blender/layout.py (shared with the blockout): a resize there moves everything here
    W, D, H = L.ROOM_W, L.ROOM_D, L.ROOM_H
    V, C = L.VENDING, L.COOLERS
    out = []
    zcs = [C["z0"] + C["each_w"] * (i + 0.5) for i in range(C["n"])]
    out.append(build_vending(ms, shared, V["z0"] + V["w"] / 2))
    for i, zc_ in enumerate(zcs, 1):
        out.append(build_cooler(ms, i, (C["d"] / 2 + 0.03, 0, zc_), None))
    put("steel_tumbler_01", mesh_tumbler_steel(ms), (0.3, 0.405, zcs[0]), props=P(0, "grab", mass=0.2, collider="box", caption_id="steel_tumbler"))
    put("socket_double_01", _socket(ms), (0.0, 1.1, sum(zcs) / len(zcs)), props=P(1, "look", collider="none"))
    out.append(build_mural(D))
    me_t = mesh_table(ms)
    tables = []
    for n, (x0, zc) in enumerate(L.table_positions(), 1):
        o = put(f"table_{n:02d}", me_t, (x0 + L.TABLE_L / 2, 0, zc), props=P(1, "look", collider="box", caption_id="cafeteria_table"))
        tables.append((o, x0 + L.TABLE_L / 2, zc))
    cols = L.SEAT_COLS
    rows_z = sorted({t[2] for t in tables})
    col_x = [L.SEAT_ORIGIN[0] + c * L.SEAT_SPACING[0] for c in range(cols)]
    # chairs (two shared meshes: green / blue shells)
    ch = [mesh_chair(ms, "chair_g", "mesh_chair_green"), mesh_chair(ms, "chair_b", "mesh_chair_blue")]
    rng = random.Random(11)
    ci = 1
    for (o, xc, zc) in tables:
        for side in (-1, 1):
            for dx in (-L.TABLE_L / 4, L.TABLE_L / 4):
                x = xc + dx + rng.uniform(-0.06, 0.06)
                pull = rng.uniform(0.0, 0.06)
                z = zc + side * (L.TABLE_W / 2 + 0.08 + pull)
                yaw = rng.uniform(-0.15, 0.15)
                rot = (0, 0, face_rot(0, -side)[2] + yaw)
                put(f"chair_{ci:02d}", ch[rng.randrange(2) if ci % 3 else ci % 2], (x, 0, z), rot,
                    props=P(0, "use", use_kind="chair", collider="box", mass=3.5, caption_id="cafeteria_chair"))
                ci += 1
    # grab items, relative to tables (clamped to the tables that exist)
    def tb(i):
        return tables[min(i, len(tables) - 1)]
    gl = mesh_glass(ms)
    spots = [(tb(0), -0.4, 0.05), (tb(0), -0.25, -0.15), (tb(2 * cols - 1), 0.3, -0.15),
             (tb(2 * cols), 0.55, 0.2)]
    for i, ((_, tx, tz), dx, dz) in enumerate(spots, 1):
        put(f"glass_{i:02d}", gl, (tx + dx, 0.75, tz + dz), props=P(0, "grab", mass=0.25, collider="box", caption_id="glass"))
    put("glass_05", gl, (0.3, 0.405, zcs[-1]), props=P(0, "grab", mass=0.25, collider="box", caption_id="glass"))
    for i, (t_, dx, dz, r) in enumerate([(tb(cols), -0.4, 0.1, 0.3), (tb(2 * cols), 0.2, -0.1, 1.2), (tb(len(tables) - 1), -0.3, 0.1, 2.0)], 1):
        put(f"snack_packet_{i:02d}", shared["sn"][i - 1], (t_[1] + dx, 0.7525, t_[2] + dz), (0, -math.pi / 2, r), props=P(0, "grab", mass=0.06, collider="box", caption_id="snack_packet"))
    kt = tb(2 * cols)  # foreground table of the cafeteria photo
    kb = MB()
    kb.lathe((0, 0, 0), [(0, 0), (0.03, 0), (0.035, 0.01), (0.035, 0.14), (0.015, 0.17), (0.013, 0.21), (0, 0.21)], ms["ketchup"], 16)
    kb.cyl((0, 0.215, 0), 0.016, 0.02, ms["cap_w"], seg=10)
    put("ketchup_bottle_01", kb.finish("mesh_ketchup_bottle"), (kt[1] - 0.1, 0.75, kt[2] + 0.2), props=P(0, "grab", mass=0.45, collider="box", caption_id="ketchup_bottle"))
    sb = MB()
    sb.lathe((0, 0, 0), [(0, 0), (0.024, 0), (0.025, 0.09), (0.0, 0.1)], ms["steel"], 14)
    put("salt_shaker_01", sb.finish("mesh_salt_shaker"), (kt[1] + 0.15, 0.75, kt[2] + 0.15), props=P(0, "grab", mass=0.15, collider="box", caption_id="salt_shaker"))
    # bins (window strip, `08 (2)`), just west of the first table column
    out.append(build_bin(ms, "bin_plastic_01", (col_x[0] + 0.2, 0, 0.32), (0, 1), "bin_green", "PLASTIC"))
    out.append(build_bin(ms, "bin_nec_01", (col_x[0] + 0.65, 0, 0.32), (0, 1), "red", "NEC"))
    # ceiling fans (shared mesh): grid over the table block, 2.5 m pitch
    mf = mesh_fan(ms, H)
    i = 1
    for zc in rows_z[:-1]:
        for cx in col_x:
            put(f"ceiling_fan_{i:02d}", mf, (cx + L.TABLE_L / 2, 0, zc + L.SEAT_SPACING[1] / 2), (0, 0, i), props=P(1, "look", collider="none", caption_id="ceiling_fan"))
            i += 1
    return out

def _socket(ms):
    b = MB()
    b.box((0.008, 0, 0), (0.016, 0.08, 0.15), ms["white"], 0.004)
    for sz in (-0.03, 0.03):
        b.box((0.017, 0.0, sz), (0.004, 0.03, 0.03), ms["text_k"], 0.0)
    return b.finish("mesh_socket_double")
