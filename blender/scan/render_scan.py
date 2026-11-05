"""Render the aligned photogrammetry mesh headless.
blender -b --python-exit-code 1 -P render_scan.py -- <out.png> <mode> [args]
 mode plan : ortho top-down, cut at z=<zcut> (default 2.0), scan frame
 mode cam  : x y z yaw pitch hfov [W H]  (aligned frame, z up, yaw deg CCW from +x)
Aligned frame = scan rotated -29.58 deg about z, floor at z=0 (see references/photogrammetry/align.json).
"""
import bpy, sys, math, mathutils
argv = sys.argv[sys.argv.index('--')+1:]
out, mode = argv[0], argv[1]
OBJ = '/Users/prath/projects/prath_personal/cctech_game/references/photogrammetry/obj/pantry-obj.obj'
ANG = math.radians(-29.58); FLOOR = 1.29
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=OBJ, forward_axis='Y', up_axis='Z')
ob = bpy.context.selected_objects[0]
ob.rotation_euler = (0, 0, ANG); ob.location = mathutils.Vector((0, 0, FLOOR))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('w'); sc.world.color = (1, 1, 1)
sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = out
cam = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
if mode == 'plan':
    zc = float(argv[2]) if len(argv) > 2 else 2.0
    W, H = 1600, 1400
    cam.type = 'ORTHO'; cam.ortho_scale = 16.0 * 1  # width in m
    cam.clip_start = 0.01; cam.clip_end = 50
    co.location = (-1.0, 4.0, zc); co.rotation_euler = (0, 0, 0)
    print('PLAN px/m', W / cam.ortho_scale, 'centre', co.location[:2])
elif mode == 'ortho':
    # ortho x y z yaw pitch scale W H [clip_end]: camera at (x,y,z) looking yaw/pitch, scale = view width in m
    x, y, z, yaw, pitch, scl, W, H = map(float, argv[2:10]); W, H = int(W), int(H)
    cam.type = 'ORTHO'; cam.ortho_scale = scl; cam.clip_start = 0.01
    cam.clip_end = float(argv[10]) if len(argv) > 10 else 50
    co.location = (x, y, z); co.rotation_euler = (math.radians(90 + pitch), 0, math.radians(yaw - 90))
else:
    x, y, z, yaw, pitch, hfov = map(float, argv[2:8])
    W, H = (int(argv[8]), int(argv[9])) if len(argv) > 9 else (1200, 900)
    cam.sensor_fit = 'HORIZONTAL'; cam.angle = math.radians(hfov); cam.clip_start = 0.05
    co.location = (x, y, z)
    # camera looks along -Z local; yaw=0 -> look +x
    co.rotation_euler = (math.radians(90 + pitch), 0, math.radians(yaw - 90))
sc.render.resolution_x, sc.render.resolution_y = W, H
bpy.ops.render.render(write_still=True)
