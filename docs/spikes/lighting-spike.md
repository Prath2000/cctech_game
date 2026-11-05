# Lighting spike (TASK-1.4, risk #1)

Verdict: GO for the pipeline (Blender Cycles bake -> ambient-cube lightmaps -> TSL, WebGPU + WebGL2, AgX).
Probes: GO. Directional lightmap: GO (ambient cube), with a quality caveat (see below).

## Pipeline as built
- `blender/spike/bake_spike.py` (Blender 5.1.2, headless, Cycles Metal GPU): builds 8x6x3 m room (window wall with 5x2.2 m opening, counter, normal-mapped panel, sphere), Multiple-Scattering sky + Sun lamp (38 deg, strength 4, 0.53 deg), lightmap UV = 2nd UV layer `lm` (smart_project + pack). Run: `Blender -b --python-exit-code 1 -P blender/spike/bake_spike.py -- --lm 2048 --samples 128 --ref-samples 512`.
- Directional lightmap = **ambient cube (6 bakes)**: bake DIFFUSE direct+indirect, colour off, six times. For each axis the shader's shading normal is overridden to that world axis on the camera ray only (Light Path Ray Depth == 0, Mix node), so bounces still use true normals. Six maps (+-X, +-Y, +-Z) = irradiance-like value for a normal along each axis. Runtime: `E(n) = n.x^2*E(+-X) + n.y^2*E(+-Y) + n.z^2*E(+-Z)` (Valve ambient cube). For un-perturbed axis-aligned surfaces this is exactly the baked value; for the normal-mapped panel it reacts to the perturbed normal.
- Denoise: Cycles bake ignores `use_denoising`. Each bake is denoised afterwards with the compositor Denoise node (OIDN) in a throwaway scene (`compositing_node_group`, Blender 5.x API), ~1.6 s per 2048^2 map. Without it PNGs were 7-8 MB each (noise); with it 1.5 MB.
- Probes: 4x4x3 grid (48 points, 1.0-2.0 m spacing). Each probe is a 0.12 m white cube whose 6 faces are baked in one Cycles bake (16 px cell per face, 256 spp); face value = ambient-cube coefficient. Stored in `meta.json` (864 RGB triples). Runtime trilinear interpolation in JS into 6 vec3 uniforms, same `ambientCube()` function as the lightmap. (Research suggested LightProbeGrid / L1 SH volume; the ambient cube reuses one code path and bakes via Cycles. L1/L2 SH is an upgrade, not needed for the spike.)
- Reference: Cycles 512 spp denoised, camera from pose `spike` in `src/data/camera-poses.json` (same file read by Blender and the game), AgX, exposure 0.
- Export: GLB with TEXCOORD_0 (panel normal map UV) and TEXCOORD_1 (lightmap UV). The glTF exporter drops the 2nd UV unless a material texture reads it, so export-only Principled materials with a dummy texture on `lm` are created at the very end (this wipes the render materials, so export runs last). Albedos come from `meta.json`, not the GLB.
- Sky through the window: Blender equirect render of the sky (`sky.exr`, 0.4 MB) set as `scene.background`; orientation matched on first try (no rotation needed).
- Game: `spike.html` + `src/spike/main.ts` (three/webgpu, TSL `MeshBasicNodeMaterial`, no scene lights). `vite.config.ts` aliases `three` -> `three/webgpu` (so GLTFLoader/EXRLoader share one class set) and adds `spike.html` as a second page. Harness: `--page spike.html` (and `--q "a=b"` extra query) added to `scripts/lib.ts`, `shot.ts`, `fps.ts`; pose `spike` appended to camera-poses.json.
- Query params: `?webgl=1`, `?sphere=x,y,z` (Blender coords), `?anim=1` (sphere sweeps sun patch -> shadow), `?nomap=1`, `?exposure=`, `?tm=none`.

## Units and encoding (gotchas)
- Cycles DIFFUSE bake without colour = radiance of a white surface (already E/pi). Game multiplies by albedo only. No extra 1/pi (found by comparing against Blender "Standard" render: with /pi it was 0.30x too dark; without, within 1-5 of 255).
- Lightmap encoding shipped: **8-bit sRGB PNG, value = L/8** (hardware sRGB decode, bilinear works, no shader decode). Range 8 is generous (max baked 4.0); RANGE 4 would double precision. Measure vs half-float EXR (ZIP, RGB16): 2048^2 PNG ~1.5 MB each (8.96 MB for 6) vs EXR 7.2-10.4 MB each (49 MB for 6). A banded-looking result was not seen. Real HDR (sun >8x) would need RGBM/BC6H (KTX2) - see follow-ups.
- Axis map: Blender (x,y,z) -> three (x,z,-y): three +Y uses Blender +Z bake, three +Z uses Blender -Y bake, three -Z uses Blender +Y.

## Timings (Apple M5, Metal GPU, 2048^2, 128 spp)
- 6 lightmap bakes + 6 denoises + saves: 180 s (about 15 s bake + 1.6 s denoise + save each; one earlier run took 123 s; machine load varies).
- 48 probes (288 faces): 2-8 s. Reference render 1600x1200 512 spp denoised: 75-82 s. Sky: 7-14 s. Total about 4.5 min.
- Cost scales with 6x per light state: TASK-1.13 on/off = 2 states = 12 bakes (about 6 min for this room; the real room is bigger).

## Results vs acceptance
1. Close to Blender: yes. `.team/work/shots/spike-compare-blender-vs-game.png` (left Blender, right game, WebGPU). Layout, sun patch shape and colour, window, panel, wall/ceiling gradients match. With Blender view = Standard and game tone mapping off the mean abs diff is 3.9/255 (points within 1-5). With AgX in both, three's AgX renders ~8-12 levels brighter in mid-tones; `toneMappingExposure = 0.85` brings sampled points to within ~1-7 (mean abs diff 5.5/255). Remaining differences: sphere has no contact shadow/GI feedback in game; Blender window sky is slightly brighter near the horizon; game sun-patch edge is slightly softer (2048 map over 48 m^2, about 1.7 cm texels).
2. Normal map reacts: yes (`spike-panel-strip.png`: Blender | game | game with `nomap=1`). Tile bevels light according to the baked directional light. Weaker contrast than the path-traced panel (ambient cube is a 6-lobe approximation of the real incident distribution; no specular).
3. Probe sphere: yes. Interpolated top-face value at (3.2, 4.6, 0.3) in sun 3.3/2.5/1.9 (b/g/r) vs (3.2, 1.2, 0.3) in shade 0.67/0.57/0.47; mean 1.82 -> 0.63 (sphere darkens to about 35%). Sphere shading was checked via numbers and sun-position screenshots (`spike-sphere-sun.png`, `spike-sphere-shadow.png`; shadow position is near the camera and mostly out of frame in pose `spike`).
4. WebGPU vs WebGL2: identical (mean abs diff 0.01/255 between screenshots). fps (check:fps, 1280x720, 8 s): WebGPU headless 59.9 median / 59.5 1% low; headed 59.9 / 53.5 (max frame 18.7 ms); WebGL2 headless 59.9 / 59.5; headed 59.9 / 53.7. Capped at vsync 60; scene is trivial (3 draw calls + sphere), so these show correctness and no per-frame cost problems, not a performance budget for the real room.
5. Go/no-go below.

## What worked / what failed
- Worked: ambient-cube trick for directional bakes in plain Cycles; compositor denoise; probes via baked cubes; one code path (`ambientCube`) for static and dynamic; both backends identical; AgX near-match with exposure.
- Cycles bake `use_denoising` is ignored (needs the separate denoise step). Blender 5.1: sky type enum is `MULTIPLE_SCATTERING` (no `NISHITA`); glTF exporter drops UV1 unless read by a material texture (as the research doc predicted); no PIL inside Blender (write PNGs through `bpy.data.images`).
- Not done: L1/L2 SH, KTX2/BC6H compression, specular/reflection probes, LightProbeGrid, light-switch blend, sphere-vs-static shadowing.

## Recommended pipeline for TASK-1.10 / 1.13
1. Keep the ambient-cube lightmap as the baseline: 6 bakes per light state at 2048 (floor/walls) with extra per-object atlases if needed. Evaluate whether a cheaper HL2-basis (3 maps) or L1 SH (4 maps) matches the panel look; test on real normal-mapped props before changing.
2. Encode: sRGB8 PNG with range 4-8 for the POC; move to KTX2 (BC6H or ASTC HDR) in TASK-1.14 if memory/transfer matters. Use RGBM/BC6H if lights get stronger than the range.
3. Probes: reuse the baked cube probe method on a grid at 1 m spacing (0.5 m near light changes); 4x4x3 took 2-8 s. Move to a `Data3DTexture` + `texture3D` lookup when probe count grows.
4. TASK-1.13 on/off blend: bake the ambient cube (and probes) for `lights_off` (sky only) and `lights_on` (sky + lights, or lights-only delta); blend in shader `mix(offMap, onMap, uSwitch)` per axis, or store the lights-only contribution so day light stays independent. Memory doubles (6 -> 12 textures); consider packing axes into fewer textures (e.g. PX/NX in RGB+RGB of one 16-bit/BC6H pair).
5. Tone mapping: AgX in both; set exposure from a Blender render of the same pose (0.85 here); re-calibrate when the real room is lit. Do not expect an exact match (Blender AgX is the OCIO LUT version).
6. Pipeline hygiene: always bake from the same pose JSON; export last; keep denoise as an explicit step.

## Follow-ups (not in backlog)
- Texel-density / UV packing for the real room's lightmap atlases (single 2048 atlas gives about 1.7 cm in this room only because it is empty).
- KTX2/BC6H (or ASTC HDR) transcoding step for lightmaps.
- Specular/reflection probe (box-projected cubemap) validation in TSL - not exercised here.
- Sphere/dynamic-object contact shadow (AO or a simple blob shadow) and probe validity near walls/counters (probes inside geometry).
- Make `vite.config.ts` and the `three` alias the project standard (TASK-1.5 may add its own config; merge, keep the alias and the second page).
- Optional script to regenerate side-by-side compare images.
