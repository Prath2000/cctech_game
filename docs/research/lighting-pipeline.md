# Lighting pipeline research (pantry spike)

Scope: Blender 5.1 Cycles headless bake -> glTF + HDR lightmaps -> three.js `three/webgpu` (WebGPURenderer, WebGL2 fallback), AgX in both.
Verified against: Blender 5.1.2 (local, headless probes run) and three.js dev 0.187.0 source (shallow clone, 2026-11-05). Items marked UNVERIFIED are from web snippets only.

## 1. Recommended pipeline (step by step)

1. Model the pantry in metres. Apply all transforms. Keep static lit meshes in one "Static" collection; dynamic props (characters, movables) are excluded from the bake.
2. UV0 = material/texture UVs. UV1 (named `Lightmap`) = lightmap UVs, one non-overlapping atlas for the whole room (or one per big surface group). `smart_project` (angle 66 deg, island_margin 0.003-0.01) is fine for box-like furniture; walls/floor/ceiling are planar so keep them as few, large islands.
3. Bake `DIFFUSE` with direct+indirect, colour OFF (irradiance-like, albedo-free). Runtime multiplies by albedo. Do NOT bake COMBINED (bakes albedo + specular in; double-lit, can't be re-tinted, and specular is view dependent).
4. Denoise (OIDN) the baked EXR as a separate step (see 2.4), save 32-bit EXR master.
5. Convert master -> runtime encoding (spike A: half-float EXR via `EXRLoader`; spike B: KTX2 UASTC HDR 4x4 -> BC6H). Also a LDR fallback is NOT needed: WebGL2 fallback supports half-float textures.
6. Export glTF (geometry + UV0 + UV1 + materials, no baked textures in it). Lightmap EXR is loaded separately and assigned at runtime (`material.lightMap`, `texture.channel = 1`, `lightMapIntensity = Math.PI`).
7. Reflection: bake one cubemap at room centre, box-project in TSL (section 5). Dynamic objects: three.js `LightProbeGrid` (runtime baked) or custom baked SH volume (section 4).
8. Tone mapping: `renderer.toneMapping = THREE.AgXToneMapping`; calibrate exposure against a Blender Standard-viewed render of the same camera (section 6).

## 2. Blender 5.1 baking via Python

### 2.1 Facts verified on 5.1.2 (headless, `Blender -b --factory-startup`)
- `scene.cycles.bake_type` enum: COMBINED AO SHADOW POSITION NORMAL UV ROUGHNESS EMIT ENVIRONMENT DIFFUSE GLOSSY TRANSMISSION.
- `scene.render.bake` (BakeSettings): `margin`, `margin_type` (`ADJACENT_FACES` | `EXTEND`), `use_pass_direct/indirect/color`, `use_clear`, `target` (`IMAGE_TEXTURES`|`VERTEX_COLORS`), `view_from`, `max_ray_distance`, `cage_*`.
- `bpy.ops.object.bake(type=..., pass_filter={'DIRECT','INDIRECT'}, margin, margin_type, uv_layer="Lightmap", use_clear, target, ...)` has a `uv_layer` arg: bakes into that UV map without changing the active one. Exclude `COLOR` from `pass_filter` for albedo-free output.
- Operator poll fails ("context is incorrect") unless the object is selected AND `view_layer.objects.active` is set. Target Image Texture node must exist in each material and be the ACTIVE node (`nodes.active = node`).
- Denoise settings: `scene.cycles.use_denoising`, `denoiser` ('OPENIMAGEDENOISE'), `denoising_prefilter`, `denoising_quality`, `denoising_input_passes` ('RGB','RGB_ALBEDO','RGB_ALBEDO_NORMAL'), `denoising_use_gpu`. These are NOT bake-specific; whether bake honours them is UNVERIFIED (3.x had a seam bug with denoise on bake: projects.blender.org/blender/blender/issues/97808; a later commit skips denoising for non-colour passes). Do not rely on it, denoise afterwards (2.4).
- Image save: `img.filepath_raw = abs_path; img.file_format = 'OPEN_EXR'; img.save()` worked (float image `bpy.data.images.new(name, w, h, float_buffer=True, alpha=False)`). Use ABSOLUTE paths (`//` failed headless with unsaved .blend). Image colorspace is "Linear Rec.709" for float images; keep it.
- File formats available include `OPEN_EXR`, `HDR`, `AVIF`, `WEBP`, `PNG`, `TIFF`.

### 2.2 Blender 5.x API changes that bite scripts
- Python 3.13 (5.1). `bpy.app.handler.exit_pre` new.
- `scene.use_nodes` deprecated (always True, removed in 6.0); `scene.node_tree` removed -> `scene.compositing_node_group`. `Material.use_nodes` prints a DeprecationWarning (removal in 6.0) but still works in 5.1.2.
- `ImageFormatSettings.media_type` ('IMAGE', ...) must be set BEFORE `file_format` when configuring `scene.render.image_settings`. (Not needed for `Image.save()`.)
- EEVEE id is now `BLENDER_EEVEE` (was `BLENDER_EEVEE_NEXT`). Pass names renamed ("Diffuse Color" etc.).
- Default view transform for a new scene is AgX (`scene.view_settings.view_transform == 'AgX'`, look 'None'). Enum introspection of view_transform/look returned only 'NONE' in background, so set by string, read back to verify.
- Sources: developer.blender.org/docs/release_notes/5.0/python_api/ , .../5.1/python_api/ , docs.blender.org/api/current/

### 2.3 Bake script skeleton
```python
import bpy
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.device = 'GPU'            # or CPU; set preferences first for Metal/CUDA
cy.samples = 1024; cy.use_denoising = False   # denoise afterwards for control
cy.sample_clamp_indirect = 10.0               # kills fireflies; keep >> 1
sc.view_settings.view_transform = 'AgX'       # irrelevant for linear bake data

# lightmap UV: second layer, unwrap, pack
me = obj.data
uv = me.uv_layers.get("Lightmap") or me.uv_layers.new(name="Lightmap")
me.uv_layers.active = uv
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, correct_aspect=True,
                         scale_to_bounds=False)
# for one shared atlas: select ALL static meshes in multi-object edit mode, then
# bpy.ops.uv.pack_islands(margin=0.004) (rotate=False keeps texel grids axis aligned)
bpy.ops.object.mode_set(mode='OBJECT')

img = bpy.data.images.new("pantry_LM", 2048, 2048, float_buffer=True, alpha=False)
for mat in used_materials:               # add active Image Texture node to every material
    n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img
    mat.node_tree.nodes.active = n       # (no UVMap node needed: bake uses uv_layer arg)
# select static meshes, set active
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT','INDIRECT'},
                    margin=8, margin_type='EXTEND', uv_layer="Lightmap",
                    use_clear=True, target='IMAGE_TEXTURES')
img.filepath_raw = "/abs/path/pantry_LM.exr"; img.file_format = 'OPEN_EXR'
img.save()
```
- `lightmap_pack` (bpy.ops.uv.lightmap_pack) exists but gives uniform quads per face (wasteful, more seams). Prefer smart_project + pack_islands. Margin: bake `margin` px >= 2x the bleed you need; with BC6H 4x4 blocks and mips use margin 8 at 2048.
- Many meshes sharing one image: one bake call with all selected writes into the one image (each object's own UV1). Unlinked/duplicate-UV overlapping islands will corrupt each other, check no overlap.
- Light units: Blender sun strength is W/m2 irradiance; point/area W are NOT lux. Use matching sun/area emission only for calibration (section 6).

### 2.4 Denoising baked data (OIDN)
- Option A (simplest, in Blender): load EXR into compositor (`sc.compositing_node_group` in 5.x; create with `bpy.data.node_groups.new(..., 'CompositorNodeTree')`) with a Denoise node (OIDN), then File Output EXR. Costs: no albedo/normal aux, may blur at island edges.
- Option B (preferred if available): Intel `oidnDenoise` CLI / `oidn` pip wheel on the EXR (HDR mode, `--hdr`), with `--clean_aux`. UNVERIFIED availability on this machine (`which oidnDenoise`).
- Denoise BEFORE the margin dilation concerns: bake with `margin_type='EXTEND'`, then denoise, so edge texels are real colour not black.
- Keep samples high-ish (512-2048 for a 8x6 m room, indirect clamp 10); a noisy bake + heavy denoise looks smeared on walls.
- The Lightmapper (github.com/Naxela/The_Lightmapper): Blender add-on, Cycles + bundled OIDN/OptiX, 8-bit RGBM/LogLuv PNG and 32-bit HDR output, "directional from normal maps". Docs are thin, unmaintained-looking (Lightmapper-One branch WIP). Treat as reference, do not depend on it.

### 2.5 glTF export with TEXCOORD_1 (verified gotcha)
- The Blender glTF exporter ONLY writes `TEXCOORD_1` if some material texture reads that UV map. A mesh with a `Lightmap` UV layer but no material using it exported only `TEXCOORD_0` (tested 5.1.2).
- Verified fix: Image Texture -> UV Map node (`uv_map = "Lightmap"`) -> linked into Principled input exports `texCoord: 1` and `TEXCOORD_1`. Cleanest for the spike: in the export-only material add a UV Map("Lightmap") -> Image Texture (tiny 4x4 white png) -> glTF Material Output group "Occlusion" (exports occlusionTexture texCoord 1). Ignore that texture at runtime.
- Alternative that avoids the hack: bake script also writes UV1 to a side `.bin`/JSON and the app sets `geometry.setAttribute('uv1', ...)`. More code, rather use the hack.
- Exporter options of interest (5.1): `export_texcoords`, `export_tangents`, `export_unused_textures`, `export_extras`, `export_lights`, `export_attributes`. Export with `export_format='GLB'`, `export_apply=True`; consider Draco/meshopt separately (quantization of UV1 hurts lightmap seams, use 16-bit min).
- three.js side: GLTFLoader gives `geometry.attributes.uv1`. Note three.js attribute names: `uv`, `uv1`, `uv2`, `uv3` = TEXCOORD_0..3.

## 3. three.js lightmap loading (r187 / dev, WebGPU node path)
- `MeshStandardNodeMaterial` (and `MeshStandardMaterial` auto-converted by WebGPURenderer): set `material.lightMap = tex; material.lightMapIntensity = k;`. Node path (src/nodes/accessors/MaterialNode.js): `LIGHT_MAP = texture(lightMap).rgb * lightMapIntensity`, texture node UV = `uv(texture.channel)`, so set `tex.channel = 1` for UV1. (Same forum pitfall as `lightMap` seeming ignored: wrong/missing channel.)
- Unit convention: node lightmap adds to `context.irradiance`, diffuse BRDF then applies `albedo/PI`. Blender DIFFUSE-without-colour is radiance of a white Lambertian = E/PI. So texel*PI is irradiance: `material.lightMapIntensity = Math.PI` (verify empirically with a grey-card patch). The in-browser `LightMapper` example doc states its output is "irradiance in lux".
- `lightMap` does not need `aoMap`; no AO is baked into DIFFUSE (use `AO` bake type -> `aoMap` on UV1 if contact shadows wanted, mind that DIFFUSE indirect already has them).
- Direct lights still add on top: for a fully baked scene REMOVE the lights baked in. Keep only dynamic ones. Bake and runtime must not both contain the same light.
- Colour space: `tex.colorSpace = THREE.LinearSRGBColorSpace` (NoColorSpace for data) for EXR/HDR/KTX2 HDR. `tex.flipY` is false for EXRLoader results; check orientation (Blender image origin is bottom-left; EXRLoader yields matching glTF UVs in tests only after verifying with a UV test grid).
- Built-in in-browser baker exists in dev: `examples/jsm/lighting/LightMapper.js`, `RayTracedRadiosity.js`, `utils/unwrapUVs.js`, example `webgpu_lightmap_baking.html` (half-float accumulation, max 256 samples; irradiance in lux). Useful as a no-Blender fallback/benchmark; quality vs Cycles untested.

### 3.1 HDR encodings that work in browsers
| Option | Format at runtime | Size (2048^2) | Notes |
|---|---|---|---|
| EXR half (PIZ/ZIP) via `EXRLoader` (`type: HalfFloatType`) | RGBA16F | ~16 MB GPU, 5-12 MB file | simplest, exact, WebGL2+WebGPU OK. Spike baseline |
| `.hdr` RGBE via `HDRLoader`/`RGBELoader` | HalfFloat after decode | ~4-8 MB file | RGBE shared exponent artefacts on saturated colours; fine for greyish indirect |
| RGBM/RGBD in PNG | RGBA8, decode in TSL | 4 MB GPU | needs custom TSL decode `rgb*a*maxRange`; do NOT mipmap/filter naively (filtering encoded values is wrong at edges); banding in dark areas |
| KTX2 UASTC HDR 4x4 (basisu) | BC6H (desktop/WebGPU) or RGBA16F fallback | 4 MB GPU (BC6H 8bpp) | `KTX2Loader` in dev supports it: transcodes to BC6H if BPTC supported, else `RGBA_HALF`; native ASTC HDR only on WebGL path (WebGPU hardcodes `astcHDRSupported:false`). 6x6 detection NOT matched (4x4 only). Check device feature `texture-compression-bc`; Apple Silicon Safari/Chrome exposes BC? use fallback path and measure |
| Ultra HDR JPEG (`UltraHDRLoader`) | HalfFloat | small | designed for env maps/photos, gain map quantisation; not for lightmaps |
- Recommendation: baseline EXR half; if the page is >10 MB, spike B with `basisu -hdr_4x4 -ktx2 -mipmap`. Always keep mips (`texture.generateMipmaps=true` for uncompressed half-float works on WebGPU; for KTX2 mips come from file). Lightmaps are low-frequency: 1024^2 can be enough (see 6.3).
- Filtering: half-float linear filtering is core in WebGL2 (EXT_color_buffer_half_float not required for sampling) and WebGPU (`float16` filterable). Full 32-bit float filtering needs `float32-filterable`, avoid FloatType.

## 4. Directional lightmaps and probes
### 4.1 Directional lightmaps (no ready-made three.js implementation found)
- Nothing in three.js core/addons or forum (searched 2025-26) gives dominant-direction or SH L1 lightmaps. Write own TSL (small).
- Cheap, robust option: Valve "ambient cube" / Radiosity-normal-map idea: bake 6 irradiance maps with fixed world-space cosine directions (+-X, +-Y, +-Z) and at runtime `E(n) = n.x^2*E(sign(nx)X) + n.y^2*E(sign(ny)Y) + n.z^2*E(sign(nz)Z)`. Can also be fitted to SH L1 (4 coeffs/channel).
- Blender has no SH/directional bake. Technique (UNVERIFIED in 5.1, needs a spike check): per direction d, replace the material with an emission-free Diffuse BSDF whose Normal input = constant vector d (Vector Transform world->object if needed) and bake `DIFFUSE` direct+indirect. Cycles evaluates the diffuse lobe around the custom normal, so output approximates E(d). Check that surfaces facing away still receive light correctly (shading normal vs geometric normal clamps) by comparing sum of weights against the plain bake.
- Alternative (Bakery style): dominant direction map = direction of brightest incoming light, from 3 HL2-basis tangent-space bakes (normal-map node with the three basis vectors), needs tangents on UV1, more fiddly in glTF.
- TSL sketch (ambient cube, world normals, 6 textures packed as 2 atlases or 6 `texture()` nodes):
```js
import { Fn, normalWorld, texture, uv, vec3, float } from 'three/tsl';
const uv1 = uv(1);
const E = Fn(() => {
  const n = normalWorld, n2 = n.mul(n);
  const cx = n.x.greaterThan(0).select(texture(pX, uv1).rgb, texture(nX, uv1).rgb);
  // same for y, z
  return cx.mul(n2.x).add(cy.mul(n2.y)).add(cz.mul(n2.z));
});
material.lightMapNode ... // not an API: use material.irradianceNode? see below
```
  Hook: MeshStandardNodeMaterial has no `lightMapNode` slot. Options: (a) `class DirLightMapNode extends LightingNode` with `setup(builder){ builder.context.irradiance.addAssign(E()); }` and push via `material.lightsNode`/subclass `setupLightMap` (see `IrradianceNode.js` ~ line 36 for the exact pattern); (b) `material.envNode`-free: override `NodeMaterial.setupLightMap()` in a subclass returning `new IrradianceNode(E())`. (b) is smallest. Cost: 6 taps + 6 textures per fragment, ok for a static room.

### 4.2 Light probes for dynamic objects
- three.js dev ships `examples/jsm/lighting/LightProbeGrid.js` (WebGPURenderer) and `LightProbeGridWebGL.js` (WebGLRenderer). Docs: threejs.org/docs/pages/LightProbeGrid.html. It is a `Light`: add to the scene, all lit node materials sample position-dependent L2 SH irradiance (9 coeffs packed in a 7-slice RGBA `Data3DTexture`, `grid.texture`).
- Constructor `new LightProbeGrid(w, h, d, nx, ny, nz)` (volume centred on object position, probes at cell centres). `grid.bake(renderer, scene, {cubemapSize, near, far, bounces, start, count, pass})` is GPU-resident, bakes AT RUNTIME from the live scene (not from Blender). For an 8x6x3 m room: `new LightProbeGrid(8,3,6, 8,3,6)` (~1 probe/m), `cubemapSize:16`, `bounces:2`.
- Forum thread (discourse.threejs.org/t/global-illumination/91243) calls it experimental, "WebGPU support later"; the current dev source has the WebGPU class, so supported in r187 dev. Check which released tag (r18x) includes it before pinning `three` in package.json (UNVERIFIED which tag).
- Caveats: run-time bake of static scene = it re-lights from three's own lights/materials (not Cycles GI). To get Cycles-quality probes, bake from Blender: place a grid of Empties, per probe render a 6-face or equirect Cycles image (or bake with `bpy.ops.render.render` + Panoramic camera) -> project to L1/L2 SH in Python (numpy) -> store RGBA16F 3D texture (`Data3DTexture`, 4 slices for L1x3 channels) -> sample in TSL with `texture3D(tex, (positionWorld - origin)/size)` trilinear and evaluate `E(n)` (L1: `a0 + a1*n`, clamp >= 0). Hook as in 4.1(b) but with `builder.context.irradiance`. Effort ~1 day; defer until LightProbeGrid proves insufficient.
- Dynamic objects must skip `lightMap` (no UV1) and ONLY use probes + direct dynamic lights. Static meshes get lightMap; they also receive the probe grid, so disable the grid on them or you double count indirect diffuse (three has no per-material probe opt-out; use layers/ separate grid ... UNVERIFIED, test).

## 5. Reflection probes
- three.js ships box projection in TSL: `getParallaxCorrectNormal(reflectVector, cubeSize:vec3, cubePos:vec3)` (src/nodes/functions/material/getParallaxCorrectNormal.js, example `examples/webgpu_materials_envmaps_bpcem.html`):
```js
import { getParallaxCorrectNormal, pmremTexture, reflectVector, vec3 } from 'three/tsl';
const pm = pmremGen.fromCubemap?.(cubeTex)  // or load via PMREMGenerator
material.envNode = pmremTexture(pmRT.texture, getParallaxCorrectNormal(reflectVector, vec3(8, 3, 6), vec3(0, 1.5, 0)));
```
  Uses `positionWorld` so it is exact only for box-shaped rooms: pantry fits. `cubeSize` = room AABB, `cubePos` = room centre (NOT probe capture point; the algorithm intersects the box from the fragment, capture point should equal cubePos).
- Roughness: `pmremTexture` provides roughness-prefiltered mips; build via `PMREMGenerator.fromCubemap` (WebGPU: `await renderer.init()` first) once at load.
- Bake cubemap in Blender: Panoramic camera (Equirectangular) at room centre (z~1.4 m), Cycles, 1024x512 EXR (render, not bake), load via `EXRLoader` -> `PMREMGenerator.fromEquirectangular`; for box projection with equirect, convert via `fromEquirectangular` then pass the resulting PMREM RT texture to `pmremTexture` as above. Mirror is a risk (no front-face seams) if capture camera is near walls. Exclude emissive "fake" lights if lightmap already counts them.
- Alternative: capture cube in-browser with `CubeCamera` after the lightmap is applied (matches the runtime look, includes baked GI via the lightmap). Recommended for the spike: cheap, no Blender round trip.
- Specular of metal/glossy surfaces is the main visible beneft; keep `envMapIntensity` ~1 and reduce lightMap contribution on shiny surfaces if double counted.

## 6. Pitfalls
### 6.1 AgX parity
- three.js `AgXToneMapping` (src/nodes/display/ToneMappingFunctions.js `agxToneMapping`) is Troy Sobotka's AgX base + three's own matrices/polynomial, applied to linear Rec.709/sRGB then sRGB OETF. Blender's AgX view transform is the OCIO LUT version; they are "close, not identical" (github.com/mrdoob/three.js/issues/27362, discourse "Is AGX tonemapping implemented correctly?").
- Blender Looks (Punchy, Golden, ...) have no three.js equivalent: keep Look = None in Blender. Blender 5.1 default view transform = AgX, look None -> compare against that.
- Match method: render a Macbeth/grey-ramp in Blender (Cycles, AgX) and in three with the same exposure; tune `renderer.toneMappingExposure` ~ 2^(Blender exposure). Don't expect pixel parity; do ratio checks on 18% grey (target sRGB ~ 118 in AgX output), and white/colour patches.
- Blender's "Standard" transform is the right one for comparing raw linear data; AgX is applied ONLY at display, never in the bake data (bake outputs scene-linear, view transform not baked).
### 6.2 Colour management
- Everything in the pipeline is linear Rec.709 floats. Set `renderer.outputColorSpace = SRGBColorSpace`, albedo textures `SRGBColorSpace`, lightmap/EXR `LinearSRGBColorSpace`/NoColorSpace. Don't let Blender's Filmic/AgX influence saved EXR (view transform is not applied on `Image.save()` for float EXR, applied on PNG/JPG!). Never save lightmaps as 8-bit PNG via `save_render`.
- Emissive lamp panels: Blender emission strength vs three `emissiveIntensity` need manual match; with AgX bright emissives desaturate to white similarly in both.
- Colour-managed "scene-linear" in Blender 5.1 is Linear Rec.709 by default (matches three); if the file uses ACEScg/Rec.2020 working space convert before export.
### 6.3 Texel density for an 8 x 6 m room
- Floor+ceiling = 2x48 m2, walls (3 m high) = 84 m2, furniture ~30-60 m2 => ~200-250 m2 lit surface.
- Targets: 2 texels/10 cm (20 tex/m) -> 200 m2*400 = 80k texels = ~300x300 (!). Real-world budget with padding/packing losses (50% utilisation, ~8 px margins): 1024^2 gives ~13 tex/m on average, 2048^2 gives ~26 tex/m. Recommend: 2048^2 atlas at ~20-30 tex/m for the whole room; spike up to 4096^2 only to show seam improvements. Soft shadows from windows/lights are the limiting detail: ~3-5 cm penumbra wants 30+ tex/m near contact areas.
- Weight texel density: floor/ceiling/walls 10-15 tex/m (smooth), furniture 30-50 tex/m (contact shadows). Use per-object UV scale before `pack_islands`.
- Memory: 2048^2 RGBA16F = 32 MB with mips (45 MB w/ mips ~1.33x), BC6H = 5.6 MB. Mobile: prefer KTX2/BC6H(ASTC HDR on iOS not exposed in WebGPU path, see 3.1) or 1024^2 half-float.
### 6.4 Seams, leaks
- Island margin (UV space) >= 2-3 texels, bake margin `EXTEND` >= 8px; denoise leaks colour across islands unless islands have padding; BC6H 4x4 blocks bleed -> margin >= 4px mandatory.
- Linear filtering at island borders shows seams on lit/dark transitions: keep islands edges where geometry is a hard crease or hidden; weld shared edges in smart_project (`bpy.ops.uv.smart_project` splits at angle limit; lower it to 45 deg).
- Light leaks at wall/floor corners from bilinear: add 1-2 texel gap, `mipmap` bias: sample `lightMap` with `minFilter = LinearMipmapLinear` ok; mips mix island borders, prefer `LinearFilter` without mips at distance < 15 m OR pad more.
- Double-sided geometry: backfaces bake as black on the inside; ensure normals face the room.
- Draco/meshopt quantisation of UV1: use >= 14 bits.
### 6.5 Other
- WebGL2 fallback: node materials run there; verify `LightProbeGrid` (WebGPU variant) works under `WebGPURenderer({ forceWebGL: true })` -- the doc says bake() "requires WebGPURenderer", which is OK because WebGPURenderer with WebGL backend is still a WebGPURenderer, BUT its Data3DTexture 7-slice atlas sampling is UNVERIFIED on the WebGL backend. Test in spike.
- `KTX2Loader.detectSupport(renderer)` required; `detectSupportAsync` deprecated r181 (target removal ~r190) -- `await renderer.init()` first.
- Dynamic shadows from the sun/spot plus baked indirect: keep shadow-casting lights for dynamic characters only; bake static lights' direct term in the map or you double-count.
- Blender "Point/Area" watt vs three candela/lux: calibrate with a grey card, don't convert by formula.
- Risks tracked below.

## 7. Risks (ranked)
1. glTF TEXCOORD_1 not exported without material reference (verified) -> need export hack or side-channel UV1 (2.5). Low effort, must automate.
2. Bake-vs-runtime light unit mismatch (`lightMapIntensity = PI`, exposure) -> needs a calibration grey-card test, otherwise "looks dark/too bright".
3. Double-counting indirect (lightMap + LightProbeGrid + env map + baked emissive) -> plan layers: static=lightMap only, dynamic=probes.
4. OIDN on baked EXR (bake-time denoising unreliable; seams) -> separate denoise step; confirm tool availability.
5. KTX2 HDR on WebGPU path: BC6H only if BPTC feature; native ASTC HDR disabled for WebGPU; fallback RGBA16F doubles size. Start with EXR half.
6. Directional lightmap bake technique (custom normal Diffuse BSDF, ambient cube) unverified in Blender 5.1; effort 1-2 days; only worth it if normal-mapped surfaces look flat. Defer.
7. Probe baking from Blender needs custom code (no loader/format for LightProbeGrid data; only runtime bake exists). Prefer runtime `LightProbeGrid.bake`.
8. AgX not pixel identical Blender vs three; no AgX Looks. Accept ~5% delta, document.
9. API churn: three.js dev 0.187 (LightProbeGrid, LightMapper are new addons, names may change); Blender 6.0 will remove `use_nodes`/`node_tree`. Pin versions, wrap in a script version check.
10. Seams/leaks at island edges with BC6H + mips -> padding rules in 6.4.

## 8. Suggested spike order
1. Cycles DIFFUSE bake of one room + EXR + glTF with UV1; load in three with `lightMapIntensity = PI`; compare to Cycles render (AgX both).
2. Add CubeCamera box-projected reflections (`getParallaxCorrectNormal`).
3. Add `LightProbeGrid` for a dynamic prop; verify no double count and WebGL fallback.
4. Optional: KTX2 UASTC HDR (BC6H) size/quality vs EXR; directional (ambient cube) bake.

## Links
- three.js LightProbeGrid docs: https://threejs.org/docs/pages/LightProbeGrid.html
- three.js GI thread: https://discourse.threejs.org/t/global-illumination/91243
- three.js source: https://github.com/mrdoob/three.js (examples/jsm/lighting/, examples/webgpu_lightmap_baking.html, examples/webgpu_materials_envmaps_bpcem.html, examples/jsm/loaders/KTX2Loader.js)
- three.js AgX: https://github.com/mrdoob/three.js/issues/27362 , https://discourse.threejs.org/t/is-agx-tonemapping-implemented-correctly/60609
- Blender 5.0/5.1 Python API notes: https://developer.blender.org/docs/release_notes/5.0/python_api/ , https://developer.blender.org/docs/release_notes/5.1/python_api/
- Blender API: https://docs.blender.org/api/current/ (bpy.types.BakeSettings, CyclesRenderSettings)
- Bake denoise seam issue: https://projects.blender.org/blender/blender/issues/97808
- The Lightmapper: https://github.com/Naxela/The_Lightmapper
