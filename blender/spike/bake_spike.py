"""TASK-1.4 lighting spike: build test room, bake ambient-cube lightmaps (6 axes) + probes, render reference.
Run: Blender -b --python-exit-code 1 -P blender/spike/bake_spike.py -- [--lm 2048] [--samples 128] [--ref-samples 512]
Outputs to public/spike/ and .team/work/shots/spike-blender.png
"""
import bpy, bmesh, math, json, os, sys, time
import numpy as np
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'public', 'spike')
SHOTS = os.path.join(ROOT, '.team', 'work', 'shots')
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default):
    return type(default)(argv[argv.index(name) + 1]) if name in argv else default
LM = arg('--lm', 2048); SAMPLES = arg('--samples', 128); REF_SAMPLES = arg('--ref-samples', 512)
RANGE = 8.0   # lightmap encoding: sRGB8(c / RANGE); baked value = radiance of a white surface (Cycles DIFFUSE no-colour = E/pi in W/m2 units); game multiplies albedo only
SUN_STRENGTH = 4.0; SUN_ELEV = 38.0
os.makedirs(OUT, exist_ok=True); os.makedirs(SHOTS, exist_ok=True)
T0 = time.time(); timings = {}
def lap(name):
    timings[name] = round(time.time() - T0 - sum(timings.values()), 1); print('[time]', name, timings[name], flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = d.type != 'CPU'
scn.cycles.device = 'GPU'
scn.cycles.use_denoising = True
scn.cycles.max_bounces = 6; scn.cycles.diffuse_bounces = 4
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'None'
scn.view_settings.exposure = 0.0

# ---------------- world: Nishita sky (sun disc off; sun is a Sun lamp) ----------------
w = bpy.data.worlds.new('sky'); scn.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
sky.sun_disc = False; sky.sun_elevation = math.radians(SUN_ELEV); sky.sun_rotation = 0
bg = nt.nodes.new('ShaderNodeBackground'); out = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(sky.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0])

# sun travels toward -Y (into room) and +X a bit, descending
h = Vector((0.3, -1.0, 0)).normalized(); el = math.radians(SUN_ELEV)
sun_dir = Vector((h.x * math.cos(el), h.y * math.cos(el), -math.sin(el)))
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = SUN_STRENGTH; sun.angle = math.radians(0.53)
sun_o = bpy.data.objects.new('sun', sun); scn.collection.objects.link(sun_o)
sun_o.rotation_euler = sun_dir.to_track_quat('-Z', 'Y').to_euler()
# keep Nishita sky sun position consistent with the lamp (sky glow around sun)
sky.sun_rotation = math.atan2(-sun_dir.x, sun_dir.y) + math.pi  # tuned: verified visually

# ---------------- materials ----------------
ALBEDO = {'floor': (0.30, 0.18, 0.10), 'wall': (0.72, 0.70, 0.64), 'ceiling': (0.80, 0.80, 0.80),
          'counter': (0.45, 0.50, 0.55), 'panel': (0.60, 0.40, 0.30), 'sphere': (0.60, 0.60, 0.60)}
bake_nodes = []  # (axis vector node, flag node)
BAKE_IMG = bpy.data.images.new('lm', LM, LM, alpha=False, float_buffer=True)
BAKE_IMG.colorspace_settings.name = 'Non-Color'

def make_mat(name, normal_img=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree; n.nodes.clear()
    d = n.nodes.new('ShaderNodeBsdfDiffuse'); d.inputs['Color'].default_value = (*ALBEDO[name], 1)
    o = n.nodes.new('ShaderNodeOutputMaterial'); n.links.new(d.outputs[0], o.inputs[0])
    geo = n.nodes.new('ShaderNodeNewGeometry')
    base_n = geo.outputs['Normal']
    if normal_img:
        tex = n.nodes.new('ShaderNodeTexImage'); tex.image = normal_img; tex.interpolation = 'Linear'
        uvn = n.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'uv0'
        n.links.new(uvn.outputs[0], tex.inputs[0])
        nm = n.nodes.new('ShaderNodeNormalMap'); nm.uv_map = 'uv0'; nm.inputs['Strength'].default_value = 1.0
        n.links.new(tex.outputs['Color'], nm.inputs['Color']); base_n = nm.outputs[0]
    # bake override: camera-ray (depth 0) shading normal := fixed world axis (ambient cube bake)
    lp = n.nodes.new('ShaderNodeLightPath')
    less = n.nodes.new('ShaderNodeMath'); less.operation = 'LESS_THAN'; less.inputs[1].default_value = 0.5
    n.links.new(lp.outputs['Ray Depth'], less.inputs[0])
    flag = n.nodes.new('ShaderNodeValue'); flag.outputs[0].default_value = 0.0
    both = n.nodes.new('ShaderNodeMath'); both.operation = 'MULTIPLY'
    n.links.new(less.outputs[0], both.inputs[0]); n.links.new(flag.outputs[0], both.inputs[1])
    axis = n.nodes.new('ShaderNodeCombineXYZ')
    mix = n.nodes.new('ShaderNodeMix'); mix.data_type = 'VECTOR'
    n.links.new(both.outputs[0], mix.inputs['Factor'])
    n.links.new(base_n, mix.inputs[4]); n.links.new(axis.outputs[0], mix.inputs[5])
    n.links.new(mix.outputs[1], d.inputs['Normal'])
    img = n.nodes.new('ShaderNodeTexImage'); img.image = BAKE_IMG; img.select = True; n.nodes.active = img
    bake_nodes.append((axis, flag))
    return m

# normal map (procedural tiles with bevel), saved as PNG, same file used by game
def make_normal_map(res=512, tiles=(8, 6), bevel=0.22, strength=3.0):
    u = (np.arange(res) + 0.5) / res
    X, Y = np.meshgrid(u, u)
    fx = (X * tiles[0]) % 1.0; fy = (Y * tiles[1]) % 1.0
    ex = np.minimum(fx, 1 - fx); ey = np.minimum(fy, 1 - fy)
    e = np.minimum(ex, ey)
    hgt = np.clip(e / bevel, 0, 1); hgt = hgt * hgt * (3 - 2 * hgt)
    hgt = hgt + 0.03 * np.sin(X * 90) * np.sin(Y * 70)
    gy, gx = np.gradient(hgt)
    gx *= res * strength / 40; gy *= res * strength / 40   # image rows go top->bottom
    nx, ny, nz = -gx, +gy, np.ones_like(gx)                # +Y up in tangent space (rows downward)
    L = np.sqrt(nx * nx + ny * ny + nz * nz)
    rgb = np.stack([nx / L, ny / L, nz / L], -1) * 0.5 + 0.5
    rgba = np.concatenate([rgb, np.ones((res, res, 1))], -1)
    img = bpy.data.images.new('panel_normal', res, res, alpha=False)
    img.colorspace_settings.name = 'Non-Color'; img.alpha_mode = 'CHANNEL_PACKED'
    img.pixels.foreach_set(np.flipud(rgba).astype(np.float32).ravel())  # blender row0 = bottom
    img.filepath_raw = os.path.join(OUT, 'panel_normal.png'); img.file_format = 'PNG'; img.save()
    return img
nmap = make_normal_map()
mats = {k: make_mat(k, nmap if k == 'panel' else None) for k in ['floor', 'wall', 'ceiling', 'counter', 'panel']}

# ---------------- geometry ----------------
RX, RY, RZ = 8.0, 6.0, 3.0
WIN = (1.5, 6.5, 0.4, 2.6)  # x0 x1 z0 z1 on y=RY wall
quads = []  # (mat, verts, normal)
def Q(mat, vs, nrm): quads.append((mat, [Vector(v) for v in vs], Vector(nrm)))
Q('floor', [(0,0,0),(RX,0,0),(RX,RY,0),(0,RY,0)], (0,0,1))
Q('ceiling', [(0,0,RZ),(RX,0,RZ),(RX,RY,RZ),(0,RY,RZ)], (0,0,-1))
Q('wall', [(0,0,0),(RX,0,0),(RX,0,RZ),(0,0,RZ)], (0,1,0))
Q('wall', [(0,0,0),(0,RY,0),(0,RY,RZ),(0,0,RZ)], (1,0,0))
Q('wall', [(RX,0,0),(RX,RY,0),(RX,RY,RZ),(RX,0,RZ)], (-1,0,0))
x0, x1, z0, z1 = WIN
for a in [(0,0,x0,RZ), (x1,0,RX,RZ), (x0,0,x1,z0), (x0,z1,x1,RZ)]:
    ax0, az0, ax1, az1 = a
    Q('wall', [(ax0,RY,az0),(ax1,RY,az0),(ax1,RY,az1),(ax0,RY,az1)], (0,-1,0))
# counter box (south wall), 5 faces
cx0, cx1, cy0, cy1, ch = 5.0, 7.0, 0.0, 0.7, 0.9
Q('counter', [(cx0,cy0,ch),(cx1,cy0,ch),(cx1,cy1,ch),(cx0,cy1,ch)], (0,0,1))
Q('counter', [(cx0,cy1,0),(cx1,cy1,0),(cx1,cy1,ch),(cx0,cy1,ch)], (0,1,0))
Q('counter', [(cx0,cy0,0),(cx0,cy1,0),(cx0,cy1,ch),(cx0,cy0,ch)], (-1,0,0))
Q('counter', [(cx1,cy0,0),(cx1,cy1,0),(cx1,cy1,ch),(cx1,cy0,ch)], (1,0,0))
# normal-mapped panel on east wall
PY0, PY1, PZ0, PZ1, PX = 2.0, 4.6, 0.6, 2.4, RX - 0.02
PANEL_Q = len(quads)
Q('panel', [(PX,PY0,PZ0),(PX,PY1,PZ0),(PX,PY1,PZ1),(PX,PY0,PZ1)], (-1,0,0))

me = bpy.data.meshes.new('static'); ob = bpy.data.objects.new('static', me); scn.collection.objects.link(ob)
mat_names = list(mats.keys())
for k in mat_names: me.materials.append(mats[k])
bm = bmesh.new(); uv0 = bm.loops.layers.uv.new('uv0'); lm = bm.loops.layers.uv.new('lm')
for qi, (mn, vs, nrm) in enumerate(quads):
    if (vs[1] - vs[0]).cross(vs[2] - vs[1]).dot(nrm) < 0: vs = vs[::-1]; flip = True
    else: flip = False
    f = bm.faces.new([bm.verts.new(v) for v in vs]); f.material_index = mat_names.index(mn)
    if qi == PANEL_Q:
        for l in f.loops:
            v = l.vert.co; l[uv0].uv = ((v.y - PY0) / (PY1 - PY0), (v.z - PZ0) / (PZ1 - PZ0))
bm.to_mesh(me); bm.free()
me.uv_layers.active = me.uv_layers['lm']
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')
me.uv_layers.active = me.uv_layers['lm']; me.uv_layers['lm'].active_render = True
lap('build+uv')

# sphere (for reference render only)
sph_mat = bpy.data.materials.new('sphere'); sph_mat.use_nodes = True
sph_mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*ALBEDO['sphere'], 1)
sph_mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1.0
sph_mat.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.0
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(3.2, 3.6, 0.3), segments=64, ring_count=32)
sphere = bpy.context.active_object; sphere.name = 'sphere'; sphere.data.materials.append(sph_mat)
bpy.ops.object.shade_smooth()
sphere.hide_render = True; sphere.select_set(False)

# ---------------- bake ambient cube ----------------
AXES = {'px': (1,0,0), 'nx': (-1,0,0), 'py': (0,1,0), 'ny': (0,-1,0), 'pz': (0,0,1), 'nz': (0,0,-1)}
scn.cycles.samples = SAMPLES
scn.render.bake.margin = 8; scn.render.bake.margin_type = 'EXTEND'
scn.render.bake.use_pass_direct = True; scn.render.bake.use_pass_indirect = True; scn.render.bake.use_pass_color = False
for ax, flag in bake_nodes: flag.outputs[0].default_value = 1.0
ob.select_set(True); bpy.context.view_layer.objects.active = ob
sizes = {}; raw = {}
def denoise(a):
    H, W = a.shape[:2]
    sc = bpy.data.scenes.new('dn'); sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.resolution_percentage = 100
    img = bpy.data.images.new('dn_in', W, H, alpha=False, float_buffer=True); img.colorspace_settings.name = 'Non-Color'
    rgba = np.concatenate([np.flipud(a), np.ones((H, W, 1), np.float32)], -1).astype(np.float32)
    img.pixels.foreach_set(rgba.ravel())
    g = bpy.data.node_groups.new('dng', 'CompositorNodeTree')
    g.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    ni = g.nodes.new('CompositorNodeImage'); ni.image = img
    nd = g.nodes.new('CompositorNodeDenoise')
    go = g.nodes.new('NodeGroupOutput')
    g.links.new(ni.outputs[0], nd.inputs[0]); g.links.new(nd.outputs[0], go.inputs[0])
    sc.compositing_node_group = g
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
    sc.render.filepath = os.path.join(OUT, '_dn.exr')
    bpy.ops.render.render(write_still=True, scene=sc.name)
    r = bpy.data.images.load(sc.render.filepath); r.colorspace_settings.name = 'Non-Color'
    o = np.empty(W * H * 4, np.float32); r.pixels.foreach_get(o)
    res = np.flipud(o.reshape(H, W, 4)[..., :3]).copy()
    bpy.data.images.remove(r); bpy.data.images.remove(img); bpy.data.scenes.remove(sc); os.remove(sc.render.filepath if False else os.path.join(OUT, '_dn.exr'))
    return res

def lin2srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 1e-9), 1 / 2.4) - 0.055)
for name, v in AXES.items():
    for ax, flag in bake_nodes:
        for i in range(3): ax.inputs[i].default_value = v[i]
    BAKE_IMG.pixels.foreach_set(np.zeros(LM * LM * 4, np.float32))
    t = time.time()
    bpy.ops.object.bake(type='DIFFUSE')
    px = np.empty(LM * LM * 4, np.float32); BAKE_IMG.pixels.foreach_get(px)
    a = np.flipud(px.reshape(LM, LM, 4)[..., :3].copy())   # top row first (glTF/flipY=false)
    a = denoise(a.astype(np.float32)) if name != 'x' else a  # OIDN via compositor
    raw[name] = None
    # full-float EXR (for size comparison / reference)
    BAKE_IMG.pixels.foreach_set(np.concatenate([np.flipud(a), np.ones((LM, LM, 1), np.float32)], -1).astype(np.float32).ravel())
    ims = scn.render.image_settings; ims.file_format = 'OPEN_EXR'; ims.color_depth = '16'; ims.color_mode = 'RGB'; ims.exr_codec = 'ZIP'
    epath = os.path.join(OUT, f'lm_{name}.exr'); BAKE_IMG.save_render(epath)
    sizes[f'exr_{name}'] = os.path.getsize(epath)
    # sRGB8 PNG, range-scaled
    enc = (np.clip(lin2srgb(np.clip(a / RANGE, 0, 1)), 0, 1) * 255 + 0.5).astype(np.uint8)
    pim = bpy.data.images.new(f'png_{name}', LM, LM, alpha=False); pim.colorspace_settings.name = 'Non-Color'
    rgba = np.concatenate([np.flipud(enc).astype(np.float32) / 255.0, np.ones((LM, LM, 1), np.float32)], -1)
    pim.pixels.foreach_set(rgba.ravel()); pim.filepath_raw = os.path.join(OUT, f'lm_{name}.png')
    pim.file_format = 'PNG'; pim.save_render(pim.filepath_raw) if False else pim.save()
    bpy.data.images.remove(pim)
    sizes[f'png_{name}'] = os.path.getsize(os.path.join(OUT, f'lm_{name}.png'))
    print('[bake]', name, round(time.time() - t, 1), 's', 'max', float(a.max()), 'mean', float(a.mean()), flush=True)
lap('bake_lightmaps')
for ax, flag in bake_nodes: flag.outputs[0].default_value = 0.0

# ---------------- probes (ambient cube from baked white mini-cubes) ----------------
PX_ = [1.0, 3.0, 5.0, 7.0]; PY_ = [1.2, 2.6, 4.0, 5.4]; PZ_ = [0.4, 1.4, 2.4]
CELL = 16; PER_ROW = 20
pme = bpy.data.meshes.new('probes'); pob = bpy.data.objects.new('probes', pme); scn.collection.objects.link(pob)
white = bpy.data.materials.new('white'); white.use_nodes = True; wn = white.node_tree; wn.nodes.clear()
wd = wn.nodes.new('ShaderNodeBsdfDiffuse'); wd.inputs['Color'].default_value = (1, 1, 1, 1)
wo = wn.nodes.new('ShaderNodeOutputMaterial'); wn.links.new(wd.outputs[0], wo.inputs[0])
pimg = bpy.data.images.new('probe_bake', CELL * PER_ROW, CELL * PER_ROW, alpha=False, float_buffer=True)
pimg.colorspace_settings.name = 'Non-Color'
wi = wn.nodes.new('ShaderNodeTexImage'); wi.image = pimg; wi.select = True; wn.nodes.active = wi
pme.materials.append(white)
pbm = bmesh.new(); puv = pbm.loops.layers.uv.new('lm')
probe_list = []; cell = 0; hs = 0.06
FACES = [('px',(1,0,0)),('nx',(-1,0,0)),('py',(0,1,0)),('ny',(0,-1,0)),('pz',(0,0,1)),('nz',(0,0,-1))]
for x in PX_:
    for y in PY_:
        for z in PZ_:
            probe_list.append((x, y, z)); c = Vector((x, y, z))
            for fname, n in FACES:
                n = Vector(n); t1 = n.cross(Vector((0,0,1)) if abs(n.z) < 0.9 else Vector((1,0,0))).normalized(); t2 = n.cross(t1)
                vs = [c + n*hs + t1*s1*hs + t2*s2*hs for s1, s2 in [(-1,-1),(1,-1),(1,1),(-1,1)]]
                f = pbm.faces.new([pbm.verts.new(v) for v in vs]); f.material_index = 0
                f.normal_update()
                cx_, cy_ = cell % PER_ROW, cell // PER_ROW; cell += 1
                for l, (u, v) in zip(f.loops, [(0,0),(1,0),(1,1),(0,1)]):
                    l[puv].uv = ((cx_ + 0.1 + 0.8 * u) / PER_ROW, (cy_ + 0.1 + 0.8 * v) / PER_ROW)
pbm.to_mesh(pme); pbm.free()
# ensure each probe face points along its intended axis
for i, p in enumerate(pme.polygons):
    want = Vector(FACES[i % 6][1])
    if p.normal.dot(want) < 0: print('[warn] probe face flipped', i)
# hide room from selection, bake probes
for o in bpy.context.selected_objects: o.select_set(False)
pob.select_set(True); bpy.context.view_layer.objects.active = pob
ob.hide_render = False
pme.uv_layers.active = pme.uv_layers['lm']
scn.cycles.samples = 256; scn.render.bake.margin = 0
for n_ in bake_nodes: pass
bpy.ops.object.bake(type='DIFFUSE')
parr = np.empty(CELL * PER_ROW * CELL * PER_ROW * 4, np.float32); pimg.pixels.foreach_get(parr)
parr = parr.reshape(CELL * PER_ROW, CELL * PER_ROW, 4)[..., :3]   # row0 = bottom (v=0)
probes = []; cell = 0
for pos in probe_list:
    cube = []
    for fname, n in FACES:
        cx_, cy_ = cell % PER_ROW, cell // PER_ROW; cell += 1
        blk = parr[cy_ * CELL + 4: cy_ * CELL + CELL - 4, cx_ * CELL + 4: cx_ * CELL + CELL - 4]
        cube.append([round(float(x), 5) for x in blk.reshape(-1, 3).mean(0)])
    probes.append({'pos': pos, 'cube': cube})
bpy.data.objects.remove(pob)
lap('probes')

# ---------------- export glb (static only) ----------------
for o in bpy.context.selected_objects: o.select_set(False)
ob.select_set(True); bpy.context.view_layer.objects.active = ob
poses = json.load(open(os.path.join(ROOT, 'src/data/camera-poses.json')))
meta = {'range': RANGE, 'albedo': {k: ALBEDO[k] for k in ['floor','wall','ceiling','counter','panel','sphere']},
        'sun': {'dir_blender': list(sun_dir), 'strength': SUN_STRENGTH, 'elevation': SUN_ELEV},
        'probes': {'grid': {'x': PX_, 'y': PY_, 'z': PZ_}, 'order': ['px','nx','py','ny','pz','nz'], 'blender_axes': True, 'items': probes},
        'sphere': {'radius': 0.3, 'albedo': ALBEDO['sphere']}, 'lm': LM, 'sizes': sizes, 'timings': timings}
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'))

# ---------------- reference render ----------------
sphere.hide_render = False
cam_d = bpy.data.cameras.new('cam'); cam_o = bpy.data.objects.new('cam', cam_d); scn.collection.objects.link(cam_o); scn.camera = cam_o
P = poses['spike']; yaw = math.radians(P['yaw']); pit = math.radians(P['pitch'])
fwd3 = Vector((-math.sin(yaw) * math.cos(pit), math.sin(pit), -math.cos(yaw) * math.cos(pit)))
pos3 = P['position']
cam_o.location = (pos3[0], -pos3[2], pos3[1])
fwdB = Vector((fwd3.x, -fwd3.z, fwd3.y))
cam_o.rotation_euler = fwdB.to_track_quat('-Z', 'Y').to_euler()
cam_d.sensor_fit = 'HORIZONTAL'; cam_d.angle = math.radians(P['hfov'])
scn.render.resolution_x, scn.render.resolution_y = 1600, 1200; scn.render.resolution_percentage = 100
scn.cycles.samples = REF_SAMPLES; scn.cycles.use_denoising = True
for ax, flag in bake_nodes: flag.outputs[0].default_value = 0.0
scn.render.filepath = os.path.join(SHOTS, 'spike-blender.png'); scn.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
lap('reference_render')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, '.team', 'work', 'spike.blend'), copy=True)
# equirect sky for the window (for the game background)
cam_d.type = 'PANO'
try: cam_d.panorama_type = 'EQUIRECTANGULAR'
except Exception: cam_d.cycles.panorama_type = 'EQUIRECTANGULAR'
cam_o.location = (4, 3, 1.5); cam_o.rotation_euler = (math.radians(90), 0, 0)  # looks +Y, up=+Z
scn.render.resolution_x, scn.render.resolution_y = 1024, 512
scn.cycles.samples = 32
for o in [ob, sphere]: o.hide_render = True   # sky only
scn.render.image_settings.file_format = 'OPEN_EXR'; scn.render.filepath = os.path.join(OUT, 'sky')
scn.render.use_file_extension = True
bpy.ops.render.render(write_still=True)
lap('sky')
# exporter drops TEXCOORD_1 unless a material texture reads it: give export-only Principled mats a tiny texture on 'lm'
dummy = bpy.data.images.new('dummy', 2, 2); dummy.pixels.foreach_set([1.0] * 16)
for i, m in enumerate(me.materials):
    nn = m.node_tree; nn.nodes.clear()
    pb = nn.nodes.new('ShaderNodeBsdfPrincipled'); po = nn.nodes.new('ShaderNodeOutputMaterial')
    nn.links.new(pb.outputs[0], po.inputs[0])
    uvn = nn.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'lm'
    tx = nn.nodes.new('ShaderNodeTexImage'); tx.image = dummy
    nn.links.new(uvn.outputs[0], tx.inputs[0]); nn.links.new(tx.outputs[0], pb.inputs['Base Color'])
glb = os.path.join(OUT, 'room.glb')
bpy.ops.export_scene.gltf(filepath=glb, use_selection=True, export_format='GLB', export_yup=True,
                          export_apply=True, export_materials='EXPORT', export_image_format='JPEG')
lap('export')
json.dump(timings, open(os.path.join(OUT, 'timings.json'), 'w'))
print('[done]', timings)
