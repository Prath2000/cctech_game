"""Lightmap atlas packing (TASK-1.10). Called from build_room.py after props, before export.
Every static mesh without bake=0 gets its 2nd UV layer `lightmap` repacked into a shared atlas and a custom
prop `lm_atlas` (name, exported as userData). Faces that can never be seen (outer wall faces, ceiling top, floor
bottom, box undersides on the floor) are collapsed to UV (0,0) so they cost no texels.
"""
import math
import bpy
from mathutils import Vector
import layout

# name -> (px size, name prefixes). Everything else static goes to 'props'.
ATLAS_PX = {"shell": 2048, "props": 2048}
SHELL_PREFIX = ("floor", "ceiling", "wall_", "window_", "pillar", "chevron_wall", "fridge_niche")
PACK_MARGIN_PX = 8


def atlas_of(o):
    return "shell" if o.name.startswith(SHELL_PREFIX) and not o.name.startswith("ceiling_fan") else "props"


def baked_objects(scn):
    out = []
    for o in scn.objects:
        if o.type != "MESH" or o.get("static") != 1 or o.get("bake") == 0:
            continue
        if "lightmap" not in o.data.uv_layers:
            continue
        out.append(o)
    return out


def _visible_faces(o, room):
    """Return list of bool per polygon: could this face ever be lit and seen from inside the room?"""
    W, H, D = room
    mw = o.matrix_world
    nm = mw.to_3x3().inverted_safe().transposed()
    keep = []
    for p in o.data.polygons:
        c = mw @ p.center
        n = (nm @ p.normal).normalized()
        q = c + n * 0.02
        # blender coords: x east, y = -game z, z up
        gz = -q.y
        in_hall = -0.2 <= gz <= D
        in_bay = layout.BAY["x0"] <= q.x <= layout.BAY["x1"] and D <= gz <= layout.BAY["z1"]
        ok = (0.0 <= q.x <= W) and (0.0 <= q.z <= H) and (in_hall or in_bay)
        if ok and c.z < 0.005 and n.z < -0.5:  # underside resting on the floor
            ok = False
        keep.append(ok)
    return keep


def assign(ctx, W, H, D):
    scn = ctx.scene
    objs = baked_objects(scn)
    for o in objs:  # shared mesh datablocks would share UVs
        if o.data.users > 1:
            o.data = o.data.copy()
    groups = {k: [] for k in ATLAS_PX}
    for o in objs:
        groups[atlas_of(o)].append(o)
    stats = {}
    for atlas, lst in groups.items():
        if not lst:
            continue
        for o in lst:
            me = o.data
            lay = me.uv_layers["lightmap"]
            lay.data.foreach_set("uv", [0.0] * (2 * len(me.loops)))
            keep = _visible_faces(o, (W, H, D))
            me.polygons.foreach_set("select", keep)
            vsel = [False] * len(me.vertices)
            esel = [False] * len(me.edges)
            for p, k in zip(me.polygons, keep):
                if k:
                    for vi in p.vertices:
                        vsel[vi] = True
            for e in me.edges:
                esel[e.index] = vsel[e.vertices[0]] and vsel[e.vertices[1]]
            me.vertices.foreach_set("select", vsel)
            me.edges.foreach_set("select", esel)
            me.uv_layers.active = lay
            o["lm_atlas"] = atlas
            o["lm_px"] = ATLAS_PX[atlas]
        bpy.ops.object.mode_set(mode="OBJECT") if ctx.object and ctx.object.mode != "OBJECT" else None
        bpy.ops.object.select_all(action="DESELECT")
        for o in lst:
            o.select_set(True)
        ctx.view_layer.objects.active = lst[0]
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, scale_to_bounds=False)
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.average_islands_scale()
        bpy.ops.uv.pack_islands(rotate=True, margin_method="FRACTION", margin=PACK_MARGIN_PX / ATLAS_PX[atlas])
        bpy.ops.object.mode_set(mode="OBJECT")
        # texel density report (cm per texel)
        dens = []
        N = ATLAS_PX[atlas]
        for o in lst:
            me = o.data
            lay = me.uv_layers["lightmap"].data
            sx = o.matrix_world.to_scale()
            warea = uvarea = 0.0
            for p in me.polygons:
                uvs = [lay[l].uv for l in p.loop_indices]
                a = 0.0
                for i in range(len(uvs)):
                    u0, u1 = uvs[i], uvs[(i + 1) % len(uvs)]
                    a += u0.x * u1.y - u1.x * u0.y
                a = abs(a) / 2
                if a > 1e-9:
                    warea += p.area * abs(sx.x * sx.y * sx.z) ** (2 / 3)
                    uvarea += a
            if uvarea > 0:
                dens.append((math.sqrt(warea / (uvarea * N * N)) * 100, o.name, warea, uvarea))
        tot_uv = sum(d[3] for d in dens)
        dens.sort()
        med = dens[len(dens) // 2][0] if dens else 0
        stats[atlas] = {"objects": len(lst), "px": N, "uv_fill": round(tot_uv, 3), "cm_per_texel_median": round(med, 2),
                        "cm_per_texel_min": round(dens[0][0], 2), "cm_per_texel_max": round(dens[-1][0], 2),
                        "worst": [(d[1], round(d[0], 2)) for d in dens[-3:]]}
        print("[lightmap_uv]", atlas, stats[atlas], flush=True)
    return stats
