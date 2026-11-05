"""Standalone runner: blockout + pantry props -> public/models/props_pantry.glb (pantry props only).
Run: Blender -b --python-exit-code 1 -P blender/props/run_pantry.py"""
import os, runpy, sys
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
runpy.run_path(os.path.join(ROOT, "blender", "build_blockout.py"), run_name="blockout")
sys.path.insert(0, HERE)
import pantry

objs = pantry.build(bpy.context)
OUT = os.path.join(ROOT, "public", "models", "props_pantry.glb")
if os.environ.get("PANTRY_NO_EXPORT"):
    sys.exit(0)
bpy.ops.object.select_all(action="DESELECT")
for o in bpy.data.collections["Pantry"].objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_yup=True, use_selection=True,
                          export_extras=True, export_apply=True, export_texcoords=True)
print("exported", OUT, len(objs), "objects")
