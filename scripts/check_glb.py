#!/usr/bin/env python3
"""Fail if any static=1 (and bake!=0) mesh node in a glb lacks TEXCOORD_1, or has too little of its surface with
lightmap space (the mesh renders one flat colour, often black). Usage: check_glb.py [file.glb]"""
import json, struct, sys

path = sys.argv[1] if len(sys.argv) > 1 else "public/models/room.glb"
with open(path, "rb") as f:
    _, _, _ = struct.unpack("<III", f.read(12))
    n, _ = struct.unpack("<II", f.read(8))
    g = json.loads(f.read(n))
    n, _ = struct.unpack("<II", f.read(8))
    blob = f.read(n)

def read_vec(accessor_index, fmt):
    a = g["accessors"][accessor_index]
    bv = g["bufferViews"][a["bufferView"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", struct.calcsize("<" + fmt))
    return [struct.unpack_from("<" + fmt, blob, off + stride * i) for i in range(a["count"])]

# lightmap_uv.py squashes never-seen faces (outer wall faces, undersides) to one point on purpose, so a plain box keeps
# only 43-51% of its surface. Below this share, faces the player can see have lost their lightmap space.
MIN_KEPT_AREA = 0.3

def kept_area_share(prim):
    """Share of this primitive's surface area that has real lightmap space."""
    uv = read_vec(prim["attributes"]["TEXCOORD_1"], "ff")
    pos = read_vec(prim["attributes"]["POSITION"], "fff")
    fmt = {5121: "B", 5123: "H", 5125: "I"}[g["accessors"][prim["indices"]]["componentType"]]
    idx = [i[0] for i in read_vec(prim["indices"], fmt)]
    total = kept = 0.0
    for t in range(0, len(idx), 3):
        i, j, k = idx[t:t + 3]
        e1 = [pos[j][m] - pos[i][m] for m in range(3)]
        e2 = [pos[k][m] - pos[i][m] for m in range(3)]
        cross = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        area = 0.5 * sum(c * c for c in cross) ** 0.5
        uv_area = abs((uv[j][0] - uv[i][0]) * (uv[k][1] - uv[i][1]) - (uv[k][0] - uv[i][0]) * (uv[j][1] - uv[i][1])) / 2
        total += area
        if uv_area > 1e-10:
            kept += area
    return kept / total if total else 1.0

def uv_collapsed(prim):
    return kept_area_share(prim) < MIN_KEPT_AREA

def flag(extras, key, default):
    v = (extras or {}).get(key, default)
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

bad, flat, baked, skipped = [], [], 0, 0
for node in g["nodes"]:
    if "mesh" not in node:
        continue
    ex = node.get("extras")
    if flag(ex, "static", 0) != 1:
        continue
    if flag(ex, "bake", 1) == 0:
        skipped += 1
        continue
    baked += 1
    if any("TEXCOORD_1" not in p["attributes"] for p in g["meshes"][node["mesh"]]["primitives"]):
        bad.append(node.get("name", "?"))
    elif any(uv_collapsed(p) for p in g["meshes"][node["mesh"]]["primitives"]):
        flat.append(node.get("name", "?"))
print(f"{path}: {baked} baked static meshes, {skipped} bake=0, {len(bad)} missing TEXCOORD_1, {len(flat)} with no lightmap space")
if bad:
    print("missing:", ", ".join(sorted(bad)))
if flat:
    print("no lightmap space:", ", ".join(sorted(flat)))
if bad or flat:
    sys.exit(1)
