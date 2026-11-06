"""Full-room lighting bake (TASK-1.10). One command: pnpm bake:room [-- --quick] [-- --state on]
Run: Blender -b --python-exit-code 1 -P blender/bake_room.py -- [--state off|on] [--quick] [--samples N] [--ref-samples N]
  1. builds the room (build_room.py: blockout + materials + props + lightmap atlas UVs -> public/models/room.glb)
  2. sets up daylight (Multiple-Scattering sky + sun matching the photos, window portal), LED panels off/on
  3. bakes an ambient cube (6 axis maps, Cycles Metal) per atlas, OIDN-denoises explicitly, encodes sRGB8 with
     a measured per-atlas HDR range, bakes a cube-probe grid, renders the sky backdrop + Blender reference shots
Outputs: public/lightmaps/<state>/{<atlas>_<axis>.png, lighting.json}, public/lightmaps/sky.exr, .team/work/shots/ref-*.png
Axes in file names are GAME axes (x east, y up, z south). Blender (x, y, z) = game (x, -z, y).
"""
import bpy, bmesh, math, json, os, sys, time
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default):
    return type(default)(argv[argv.index(name) + 1]) if name in argv else default
STATE = arg('--state', 'both'); QUICK = '--quick' in argv
if STATE == 'both':  # one command bakes both states (separate Blender processes: clean scene each)
    import subprocess
    rest = list(argv)
    if '--state' in rest: i = rest.index('--state'); del rest[i:i + 2]
    for st in ('off', 'on'):
        subprocess.run([bpy.app.binary_path, '-b', '--python-exit-code', '1', '-P', os.path.abspath(__file__), '--', *rest, '--state', st], check=True)
    sys.exit(0)
SAMPLES = arg('--samples', 24 if QUICK else 384)
PROBE_SAMPLES = arg('--probe-samples', 64 if QUICK else 512)
REF_SAMPLES = arg('--ref-samples', 48 if QUICK else 256)
REF_POSES = arg('--ref-poses', 'coffee-06-1,cafeteria-08-3,overview').split(',')
SUN_ELEV = arg('--sun-elev', 38.0); SUN_STRENGTH = arg('--sun', 6.0); SKY_STRENGTH = arg('--sky', 1.0)
OUT = os.path.join(ROOT, 'public', 'lightmaps', STATE); SHOTS = os.path.join(ROOT, '.team', 'work', 'shots')
os.makedirs(OUT, exist_ok=True); os.makedirs(SHOTS, exist_ok=True)
T0 = time.time(); timings = {}
def lap(name):
    timings[name] = round(time.time() - T0 - sum(timings.values()), 1); print('[time]', name, timings[name], flush=True)

sys.path[:0] = [HERE, ROOT]
import build_room  # noqa: F401  (rebuilds room + atlas UVs + exports room.glb)
import layout, lightmap_uv
lap('build_room')
scn = bpy.context.scene; ctx = bpy.context

# ---------------- cycles ----------------
scn.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = d.type != 'CPU'
scn.cycles.device = 'GPU'
scn.cycles.max_bounces = 8; scn.cycles.diffuse_bounces = 5; scn.cycles.glossy_bounces = 2
scn.cycles.transmission_bounces = 4; scn.cycles.sample_clamp_indirect = 12.0
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'None'; scn.view_settings.exposure = 0.0

# ---------------- daylight ----------------
# Sun travels from the window wall (north, blender +y) into the room (-y), slightly toward +x (game +z, +x patches).
h = Vector((0.3, -1.0, 0)).normalized(); el = math.radians(SUN_ELEV)
sun_dir = Vector((h.x * math.cos(el), h.y * math.cos(el), -math.sin(el)))
w = bpy.data.worlds.new('sky'); scn.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
sky.sun_disc = False; sky.sun_elevation = el; sky.sun_rotation = math.atan2(-sun_dir.x, sun_dir.y) + math.pi
bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = SKY_STRENGTH
wo = nt.nodes.new('ShaderNodeOutputWorld')
nt.links.new(sky.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], wo.inputs[0])
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = SUN_STRENGTH; sun.color = (1.0, 0.86, 0.68); sun.angle = math.radians(0.53)
sun_o = bpy.data.objects.new('sun', sun); scn.collection.objects.link(sun_o)
sun_o.rotation_euler = sun_dir.to_track_quat('-Z', 'Y').to_euler()
# light portal over the window wall (blender y = 0 plane, faces into the room = -y): less noise from the world light
por = bpy.data.lights.new('portal', 'AREA'); por.shape = 'RECTANGLE'; por.size = layout.ROOM_W; por.size_y = layout.ROOM_H
try: por.cycles.is_portal = True
except Exception as e: print('[warn] portal', e)
por_o = bpy.data.objects.new('portal', por); scn.collection.objects.link(por_o)
por_o.location = (layout.ROOM_W / 2, 0.05, layout.ROOM_H / 2); por_o.rotation_euler = (math.radians(90), 0, 0)
# window glass: invisible to light rays (kept for camera / game); frame + mullions stay solid
for o in scn.objects:
    if o.type == 'MESH' and o.name.startswith('window_glass'):
        o.visible_diffuse = o.visible_glossy = o.visible_transmission = o.visible_shadow = False
# 'on' state = LIGHTS-ONLY delta: daylight (sky, sun, portal) is switched off so the game blends
# final = off + uLights * on, which keeps the daylight bake exact. Panels are 0.6 m emissive area lights.
# Scale: 1 unit of irradiance ~ 1000 lux (the daylit shade of the room is ~0.5-1 unit); LED_ON_STRENGTH is panel radiance
# (8.5 -> ~2700 nit-equivalent; real panels 2500-4000), measured so the measured desk-height illuminance lands at 300-500 lux (printed as [lux]).
LUX_PER_UNIT = 1000.0
LED_ON_STRENGTH = arg('--led', 8.5)
if STATE == 'on':
    bg.inputs['Strength'].default_value = 0.0; sun.energy = 0.0; por_o.hide_render = True
for o in scn.objects:
    if o.type == 'MESH' and o.name.startswith('led_panel'):
        m = o.active_material
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Emission Color'].default_value = (1.0, 0.96, 0.90, 1)  # ~4500-5000 K neutral white
                    n.inputs['Emission Strength'].default_value = LED_ON_STRENGTH if STATE == 'on' else 0.0
lap('lighting_setup')

# ---------------- bake materials: atlas target + ambient-cube normal override ----------------
objs = lightmap_uv.baked_objects(scn)
atlases = {}
for o in objs: atlases.setdefault(o['lm_atlas'], []).append(o)
IMGS = {a: bpy.data.images.new(f'lm_{a}', lightmap_uv.ATLAS_PX[a], lightmap_uv.ATLAS_PX[a], alpha=False, float_buffer=True) for a in atlases}
for i in IMGS.values(): i.colorspace_settings.name = 'Non-Color'
patched = {}   # material -> (image node, axis node, flag node)
def patch(m):
    if m in patched: return
    n = m.node_tree
    axis = n.nodes.new('ShaderNodeCombineXYZ')
    flag = n.nodes.new('ShaderNodeValue'); flag.outputs[0].default_value = 0.0
    lp = n.nodes.new('ShaderNodeLightPath')
    less = n.nodes.new('ShaderNodeMath'); less.operation = 'LESS_THAN'; less.inputs[1].default_value = 0.5
    n.links.new(lp.outputs['Ray Depth'], less.inputs[0])
    both = n.nodes.new('ShaderNodeMath'); both.operation = 'MULTIPLY'
    n.links.new(less.outputs[0], both.inputs[0]); n.links.new(flag.outputs[0], both.inputs[1])
    geo = n.nodes.new('ShaderNodeNewGeometry')
    mix = n.nodes.new('ShaderNodeMix'); mix.data_type = 'VECTOR'
    n.links.new(both.outputs[0], mix.inputs['Factor'])
    n.links.new(geo.outputs['Normal'], mix.inputs[4]); n.links.new(axis.outputs[0], mix.inputs[5])
    for b in [x for x in n.nodes if x.type == 'BSDF_PRINCIPLED']:
        for l in list(b.inputs['Normal'].links): n.links.remove(l)
        n.links.new(mix.outputs[1], b.inputs['Normal'])
    img = n.nodes.new('ShaderNodeTexImage'); img.select = True; n.nodes.active = img
    patched[m] = (img, axis, flag)
for o in objs:
    if not o.material_slots: print('[warn] no material', o.name)
    for s in o.material_slots:
        if s.material and not s.material.use_nodes: s.material.use_nodes = True
        if s.material: patch(s.material)
print('[bake] patched', len(patched), 'materials,', len(objs), 'objects, atlases', {a: len(v) for a, v in atlases.items()})

# game axes -> blender vectors
AXES = {'px': (1, 0, 0), 'nx': (-1, 0, 0), 'py': (0, 0, 1), 'ny': (0, 0, -1), 'pz': (0, -1, 0), 'nz': (0, 1, 0)}
scn.cycles.samples = SAMPLES
scn.render.bake.margin = 8; scn.render.bake.margin_type = 'EXTEND'
scn.render.bake.use_pass_direct = True; scn.render.bake.use_pass_indirect = True; scn.render.bake.use_pass_color = False

def denoise(a):
    H, W = a.shape[:2]
    sc = bpy.data.scenes.new('dn'); sc.render.resolution_x = W; sc.render.resolution_y = H; sc.render.resolution_percentage = 100
    img = bpy.data.images.new('dn_in', W, H, alpha=False, float_buffer=True); img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(np.concatenate([a, np.ones((H, W, 1), np.float32)], -1).astype(np.float32).ravel())
    g = bpy.data.node_groups.new('dng', 'CompositorNodeTree')
    g.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    ni = g.nodes.new('CompositorNodeImage'); ni.image = img
    nd = g.nodes.new('CompositorNodeDenoise'); go = g.nodes.new('NodeGroupOutput')
    g.links.new(ni.outputs[0], nd.inputs[0]); g.links.new(nd.outputs[0], go.inputs[0])
    sc.compositing_node_group = g
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
    tmp = os.path.join(OUT, '_dn.exr'); sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True, scene=sc.name)
    r = bpy.data.images.load(tmp); r.colorspace_settings.name = 'Non-Color'
    o = np.empty(W * H * 4, np.float32); r.pixels.foreach_get(o)
    res = o.reshape(H, W, 4)[..., :3].copy()
    bpy.data.images.remove(r); bpy.data.images.remove(img); bpy.data.scenes.remove(sc); bpy.data.node_groups.remove(g); os.remove(tmp)
    return res

def lin2srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 1e-9), 1 / 2.4) - 0.055)

def save_png(arr8, path):
    H, W = arr8.shape[:2]
    pim = bpy.data.images.new('png', W, H, alpha=False); pim.colorspace_settings.name = 'Non-Color'
    pim.pixels.foreach_set(np.concatenate([arr8.astype(np.float32) / 255.0, np.ones((H, W, 1), np.float32)], -1).ravel())
    pim.filepath_raw = path; pim.file_format = 'PNG'; pim.save(); bpy.data.images.remove(pim)

meta_atlas = {}
for a, lst in atlases.items():
    N = lightmap_uv.ATLAS_PX[a]; img = IMGS[a]
    for m, (tex, axis, flag) in patched.items(): tex.image = img; flag.outputs[0].default_value = 1.0
    maps = {}
    for name, v in AXES.items():
        for m, (tex, axis, flag) in patched.items():
            for i in range(3): axis.inputs[i].default_value = v[i]
        img.pixels.foreach_set(np.zeros(N * N * 4, np.float32))
        t = time.time()
        bpy.ops.object.select_all(action='DESELECT')
        for o in lst: o.select_set(True)
        ctx.view_layer.objects.active = lst[0]
        bpy.ops.object.bake(type='DIFFUSE')
        tb = time.time() - t
        px = np.empty(N * N * 4, np.float32); img.pixels.foreach_get(px)
        raw = px.reshape(N, N, 4)[..., :3].copy()
        t = time.time(); den = np.maximum(denoise(raw), 0.0); td = time.time() - t
        maps[name] = den
        print(f'[bake] {a}/{name} bake {tb:.1f}s denoise {td:.1f}s raw max {raw.max():.3f} den max {den.max():.3f} mean {den.mean():.4f}', flush=True)
    for m, (tex, axis, flag) in patched.items(): flag.outputs[0].default_value = 0.0
    vmax = max(float(m_.max()) for m_ in maps.values())
    p9999 = max(float(np.percentile(m_, 99.99)) for m_ in maps.values())
    # measured HDR headroom: encode sRGB8(c / RANGE); the range covers p99.99 x1.25 (a few outlier texels/fireflies clip)
    RANGE = max(1.0 if STATE == 'off' else 1 / 32, math.ceil(p9999 * 1.25 * 32) / 32)
    sizes = {}
    if STATE == 'on':
        # lights-only maps are one colour (neutral-white LED): store LUMINANCE only, 3 axes per RGB texture ->
        # 2 textures per atlas instead of 6 (WebGPU/WebGL2 allow ~16 samplers per material; off 6 + on 6 + PBR maps overflowed it)
        lum = {n: d @ np.array([0.2126, 0.7152, 0.0722], np.float32) for n, d in maps.items()}
        RANGE = max(1 / 32, math.ceil(max(float(np.percentile(l, 99.99)) for l in lum.values()) * 1.25 * 32) / 32)
        for tag, trio in (('p', ('px', 'py', 'pz')), ('n', ('nx', 'ny', 'nz'))):
            arr = np.stack([lum[k] for k in trio], -1)
            enc = (np.clip(lin2srgb(np.clip(arr / RANGE, 0, 1)), 0, 1) * 255 + 0.5).astype(np.uint8)
            p = os.path.join(OUT, f'{a}_on_{tag}.png'); save_png(enc, p); sizes[tag] = os.path.getsize(p)
        maps = {}
    for name, den in maps.items():
        enc = (np.clip(lin2srgb(np.clip(den / RANGE, 0, 1)), 0, 1) * 255 + 0.5).astype(np.uint8)
        p = os.path.join(OUT, f'{a}_{name}.png'); save_png(enc, p); sizes[name] = os.path.getsize(p)
    meta_atlas[a] = {'px': N, 'range': RANGE, 'max': round(vmax, 3), 'p99_99': round(p9999, 3), 'objects': len(lst), 'png_bytes': sizes, 'packed': 'lum3' if STATE == 'on' else None}
    print('[atlas]', a, meta_atlas[a], flush=True)
    lap(f'bake_{a}')
# restore for reference renders
for m, (tex, axis, flag) in patched.items(): flag.outputs[0].default_value = 0.0

# ---------------- probe grid ----------------
GX = [0.4, 1.2, 2.2, 3.2, 4.2, 5.2, 6.2, 7.2, 8.2, 9.2, 10.0, 10.8, 11.4, 11.75]
GY = [0.3, 1.05, 1.7, 2.4, 3.0]
GZ = [0.25, 0.75, 1.4, 2.2, 3.1, 4.0, 4.9, 5.8, 6.6, 7.2]
CELL = 16; probes_pos = [(x, y, z) for x in GX for y in GY for z in GZ]
nface = len(probes_pos) * 6; PER_ROW = int(math.ceil(math.sqrt(nface)))
FACES = ['px', 'nx', 'py', 'ny', 'pz', 'nz']
dg = ctx.evaluated_depsgraph_get()
def inside_solid(p):
    o = Vector((p[0], -p[2], p[1])); back = 0
    for d in [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]:
        hit, loc, nrm, idx, ob, mw = scn.ray_cast(dg, o, Vector(d), distance=30.0)
        if hit and nrm.dot(Vector(d)) > 0: back += 1
    return back >= 3
valid = [not inside_solid(p) for p in probes_pos]
print('[probes]', len(probes_pos), 'total', sum(valid), 'valid')
pme = bpy.data.meshes.new('probes'); pob = bpy.data.objects.new('probes', pme); scn.collection.objects.link(pob)
white = bpy.data.materials.new('white'); white.use_nodes = True; wn = white.node_tree; wn.nodes.clear()
wd = wn.nodes.new('ShaderNodeBsdfDiffuse'); wd.inputs['Color'].default_value = (1, 1, 1, 1)
wout = wn.nodes.new('ShaderNodeOutputMaterial'); wn.links.new(wd.outputs[0], wout.inputs[0])
pimg = bpy.data.images.new('probe_bake', CELL * PER_ROW, CELL * PER_ROW, alpha=False, float_buffer=True); pimg.colorspace_settings.name = 'Non-Color'
wi = wn.nodes.new('ShaderNodeTexImage'); wi.image = pimg; wi.select = True; wn.nodes.active = wi
pme.materials.append(white)
pbm = bmesh.new(); puv = pbm.loops.layers.uv.new('lm'); hs = 0.05; cell = 0
for (gx, gy, gz), ok in zip(probes_pos, valid):
    c = Vector((gx, -gz, gy))
    for fname in FACES:
        n = Vector(AXES[fname]); t1 = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))).normalized(); t2 = n.cross(t1)
        vs = [c + n * hs + t1 * s1 * hs + t2 * s2 * hs for s1, s2 in [(-1, -1), (1, -1), (1, 1), (-1, 1)]]
        f = pbm.faces.new([pbm.verts.new(v) for v in vs]); f.material_index = 0
        cx_, cy_ = cell % PER_ROW, cell // PER_ROW; cell += 1
        for l, (u, v) in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            l[puv].uv = ((cx_ + 0.1 + 0.8 * u) / PER_ROW, (cy_ + 0.1 + 0.8 * v) / PER_ROW)
pbm.to_mesh(pme); pbm.free()
for i, p in enumerate(pme.polygons):  # make sure every face points along its axis
    if p.normal.dot(Vector(AXES[FACES[i % 6]])) < 0: print('[warn] probe face flipped', i)
pob.visible_diffuse = pob.visible_glossy = pob.visible_shadow = pob.visible_transmission = False  # probes don't shade each other
bpy.ops.object.select_all(action='DESELECT'); pob.select_set(True); ctx.view_layer.objects.active = pob
pme.uv_layers.active = pme.uv_layers['lm']
scn.cycles.samples = PROBE_SAMPLES; scn.render.bake.margin = 0
bpy.ops.object.bake(type='DIFFUSE')
parr = np.empty(pimg.size[0] * pimg.size[1] * 4, np.float32); pimg.pixels.foreach_get(parr)
parr = parr.reshape(pimg.size[1], pimg.size[0], 4)[..., :3]
cube = np.zeros((len(probes_pos), 6, 3), np.float32); cell = 0
for i in range(len(probes_pos)):
    for f in range(6):
        cx_, cy_ = cell % PER_ROW, cell // PER_ROW; cell += 1
        blk = parr[cy_ * CELL + 4: cy_ * CELL + CELL - 4, cx_ * CELL + 4: cx_ * CELL + CELL - 4]
        cube[i, f] = blk.reshape(-1, 3).mean(0)
# invalid probes: fill from valid neighbours (runtime also ignores them in the interpolation weights)
ny_, nz_ = len(GY), len(GZ)
def idx(ix, iy, iz): return (ix * ny_ + iy) * nz_ + iz
for _ in range(3):
    for ix in range(len(GX)):
        for iy in range(ny_):
            for iz in range(nz_):
                i = idx(ix, iy, iz)
                if valid[i]: continue
                acc = []; 
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            jx, jy, jz = ix + dx, iy + dy, iz + dz
                            if 0 <= jx < len(GX) and 0 <= jy < ny_ and 0 <= jz < nz_ and valid[idx(jx, jy, jz)]: acc.append(cube[idx(jx, jy, jz)])
                if acc: cube[i] = np.mean(acc, 0)
bpy.data.objects.remove(pob)
# desk-height illuminance estimate: E = pi * (white-diffuse radiance of the up-facing probe face), x LUX_PER_UNIT
pyi = FACES.index('py'); dsk = [idx(ix, GY.index(1.05), iz) for ix in range(len(GX)) for iz in range(nz_) if valid[idx(ix, GY.index(1.05), iz)] and 1.0 < GX[ix] < 10.5 and 1.0 < GZ[iz] < 6.6]
print('[lux]', STATE, 'mean desk-height (y=1.05) up-facing illuminance', round(float(np.pi * cube[dsk, pyi].mean() * LUX_PER_UNIT)), 'lux over', len(dsk), 'probes', flush=True)
probe_meta = {'x': GX, 'y': GY, 'z': GZ, 'order': FACES, 'valid': [int(v) for v in valid],
              'cube': [[[round(float(c), 5) for c in f] for f in p] for p in cube]}
lap('probes')

# ---------------- reference renders + sky ----------------
poses = json.load(open(os.path.join(ROOT, 'src/data/camera-poses.json')))
cam_d = bpy.data.cameras.new('cam'); cam_o = bpy.data.objects.new('cam', cam_d); scn.collection.objects.link(cam_o); scn.camera = cam_o
def point_camera(P):
    yaw = math.radians(P['yaw']); pit = math.radians(P['pitch'])
    fwd3 = Vector((-math.sin(yaw) * math.cos(pit), math.sin(pit), -math.cos(yaw) * math.cos(pit)))
    cam_o.location = (P['position'][0], -P['position'][2], P['position'][1])
    cam_o.rotation_euler = Vector((fwd3.x, -fwd3.z, fwd3.y)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.sensor_fit = 'HORIZONTAL'; cam_d.angle = math.radians(P['hfov'])
scn.render.resolution_x, scn.render.resolution_y = 1280, 720
scn.cycles.samples = REF_SAMPLES; scn.cycles.use_denoising = True
scn.render.image_settings.file_format = 'PNG'
if '--no-ref' not in argv and STATE == 'off':
    for pn in REF_POSES:
        point_camera(poses[pn]); scn.render.filepath = os.path.join(SHOTS, f'ref-{STATE}-{pn}.png')
        bpy.ops.render.render(write_still=True)
    lap('reference_renders')
if STATE == 'on': bpy.data.objects.remove(cam_o); print('[done] on state'); json.dump({'state': STATE, 'quick': QUICK, 'samples': SAMPLES, 'axes': list(AXES), 'atlases': meta_atlas, 'probes': probe_meta, 'led_strength': LED_ON_STRENGTH, 'lux_per_unit': LUX_PER_UNIT, 'timings': timings}, open(os.path.join(OUT, 'lighting.json'), 'w')); sys.exit(0)
cam_d.type = 'PANO'
try: cam_d.panorama_type = 'EQUIRECTANGULAR'
except Exception: cam_d.cycles.panorama_type = 'EQUIRECTANGULAR'
cam_o.location = (6, -3, 1.6); cam_o.rotation_euler = (math.radians(90), 0, 0)
scn.render.resolution_x, scn.render.resolution_y = 1024, 512; scn.cycles.samples = 32
for o in scn.objects:
    if o.type == 'MESH': o.hide_render = True
sky_path = os.path.join(ROOT, 'public', 'lightmaps', 'sky')
scn.render.image_settings.file_format = 'OPEN_EXR'; scn.render.image_settings.color_depth = '16'; scn.render.filepath = sky_path; scn.render.use_file_extension = True
bpy.ops.render.render(write_still=True)
lap('sky')

meta = {'state': STATE, 'quick': QUICK, 'samples': SAMPLES, 'axes': list(AXES), 'atlases': meta_atlas, 'probes': probe_meta,
        'sun': {'dir_blender': list(sun_dir), 'strength': SUN_STRENGTH, 'elevation': SUN_ELEV, 'sky_strength': SKY_STRENGTH},
        'lightmap_uv': getattr(build_room, 'LM_STATS', None), 'timings': timings}
json.dump(meta, open(os.path.join(OUT, 'lighting.json'), 'w'))
print('[done]', timings, flush=True)
