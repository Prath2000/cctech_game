"""Room orchestrator. Run: pnpm build:room
blockout (build_blockout.py, also writes room_blockout.glb) -> materials -> props modules (if present) -> public/models/room.glb
Each module exposes build(context).
"""
import importlib, os, sys
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "public", "models", "room.glb")
for p in (HERE, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import build_blockout  # noqa: F401  (runs at import: resets the scene and builds the shell)
import materials

ctx = bpy.context
materials.build(ctx)

for name in (() if os.environ.get("ROOM_PROPS") == "0" else ("pantry", "seating")):
    if os.path.exists(os.path.join(HERE, "props", f"{name}.py")):
        try:
            importlib.import_module(f"props.{name}").build(ctx)
            print("props module built:", name)
        except Exception as e:  # a broken props module must not block the room
            import traceback; traceback.print_exc()
            print("WARNING: props module failed:", name, e)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_yup=True, export_extras=True,
                          export_apply=True, export_texcoords=True, export_image_format="WEBP",
                          export_image_quality=85)
print("exported", OUT, len(bpy.data.objects), "objects")
