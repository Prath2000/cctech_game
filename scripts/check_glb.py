#!/usr/bin/env python3
"""Fail if any static=1 (and bake!=0) mesh node in a glb lacks TEXCOORD_1. Usage: check_glb.py [file.glb]"""
import json, struct, sys

path = sys.argv[1] if len(sys.argv) > 1 else "public/models/room.glb"
with open(path, "rb") as f:
    _, _, _ = struct.unpack("<III", f.read(12))
    n, _ = struct.unpack("<II", f.read(8))
    g = json.loads(f.read(n))

def flag(extras, key, default):
    v = (extras or {}).get(key, default)
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

bad, baked, skipped = [], 0, 0
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
print(f"{path}: {baked} baked static meshes, {skipped} bake=0, {len(bad)} missing TEXCOORD_1")
if bad:
    print("missing:", ", ".join(sorted(bad)))
    sys.exit(1)
