#!/usr/bin/env python3
"""Fail if any static=1 (and bake!=0) mesh node in a glb lacks TEXCOORD_1, or has all of it collapsed to one
point (no lightmap space: the mesh renders one flat colour, often black). Usage: check_glb.py [file.glb]"""
import json, struct, sys

path = sys.argv[1] if len(sys.argv) > 1 else "public/models/room.glb"
with open(path, "rb") as f:
    _, _, _ = struct.unpack("<III", f.read(12))
    n, _ = struct.unpack("<II", f.read(8))
    g = json.loads(f.read(n))
    n, _ = struct.unpack("<II", f.read(8))
    blob = f.read(n)

def uv_collapsed(prim):
    a = g["accessors"][prim["attributes"]["TEXCOORD_1"]]
    bv = g["bufferViews"][a["bufferView"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", 8)
    uvs = {struct.unpack_from("<ff", blob, off + stride * i) for i in range(a["count"])}
    return len(uvs) <= 1

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
    elif all(uv_collapsed(p) for p in g["meshes"][node["mesh"]]["primitives"]):
        flat.append(node.get("name", "?"))
print(f"{path}: {baked} baked static meshes, {skipped} bake=0, {len(bad)} missing TEXCOORD_1, {len(flat)} with no lightmap space")
if bad:
    print("missing:", ", ".join(sorted(bad)))
if flat:
    print("no lightmap space:", ", ".join(sorted(flat)))
if bad or flat:
    sys.exit(1)
