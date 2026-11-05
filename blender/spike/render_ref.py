"""Re-render the spike reference from .team/work/spike.blend with another view transform (debug AgX/exposure).
Blender -b -P blender/spike/render_ref.py -- <view_transform> <out.png> [samples]"""
import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath='.team/work/spike.blend')
s = bpy.context.scene
cam = bpy.data.objects['cam']; pass
import math
s.camera = cam
s.view_settings.view_transform = a[0]
s.render.resolution_x, s.render.resolution_y = 1600, 1200
s.cycles.samples = int(a[2]) if len(a) > 2 else 128
s.render.filepath = a[1]; s.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
