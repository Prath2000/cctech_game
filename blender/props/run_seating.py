"""Runner: blockout + seating props -> public/models/props_seating.glb.
Run: Blender -b --python-exit-code 1 -P blender/props/run_seating.py [-- --preview-only]
"""
import bpy, os, sys, runpy, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
OUT = os.path.join(ROOT, "public", "models", "props_seating.glb")

# blockout script resets the scene and exports room_blockout.glb (same content as before), then we add props.
runpy.run_path(os.path.join(ROOT, "blender", "build_blockout.py"), run_name="blockout")
import seating
importlib.reload(seating)
objs = seating.build(None)
tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == "MESH" and o.name in ())  # placeholder
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_yup=True,
                          export_extras=True, export_apply=True, export_texcoords=True)
dg = bpy.context.evaluated_depsgraph_get()
t = 0
for o in bpy.data.objects:
    if o.type == "MESH" and not o.name.startswith(("window", "wall", "floor", "ceiling", "chevron", "door", "pillar", "counter", "fridge")):
        me = o.data
        me.calc_loop_triangles()
        t += len(me.loop_triangles)
print("exported", OUT, len(bpy.data.objects), "objects; seating tris counted per instance:", t)
