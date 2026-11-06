"""Low-sample preview renders of the seating props from sheet section 5 poses.
Run: Blender -b -P blender/props/preview_seating.py -- <outdir>"""
import bpy, os, sys, math, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "/tmp"
runpy.run_path(os.path.join(HERE, "run_seating.py"), run_name="runner")
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.samples = 16; sc.cycles.device = "CPU"
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[1].default_value = 1.6
sc.world = w
sc.view_settings.view_transform = "Standard"
# ceiling is a solid box: hide so light comes in; fill light
for n in ("ceiling",):
    bpy.data.objects[n].hide_render = True
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sun.data.energy = 2.5
sun.rotation_euler = (math.radians(50), 0, math.radians(30)); sc.collection.objects.link(sun)
sys.path.insert(0, os.path.join(os.path.dirname(HERE)))
import layout as L
vx = L.VENDING["x0"] + L.VENDING["w"] / 2   # vending + coolers sit on the partition at z=ROOM_D, facing -z
cx = L.COOLERS["x0"] + L.COOLERS["each_w"]
poses = {"cafeteria": (3.2, 1.3, 2.0, -90, -3, 78, 800, 600), "vending": (vx + 0.2, 1.3, L.ROOM_D - 2.3, 180, 0, 54, 600, 800),
         "coolers": (cx, 1.2, L.ROOM_D - 2.2, 180, 0, 54, 600, 800)}
for k, (x, y, z, yaw, pitch, hf, rx, ry) in poses.items():
    if os.environ.get("ONLY") and k != os.environ["ONLY"]:
        continue
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
    cam.data.sensor_fit = "HORIZONTAL"; cam.data.angle_x = math.radians(hf)
    cam.location = (x, -z, y); cam.rotation_euler = (math.radians(90 + pitch), 0, math.radians(yaw))
    sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.filepath = os.path.join(out, f"prev_{k}.png"); bpy.ops.render.render(write_still=True)
