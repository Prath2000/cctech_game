# POC 1 task plan (parent TASK-1)
Spec: docs/superpowers/specs/2026-11-05-pantry-poc-design.md. Deps use list numbers. P = priority (P0 highest). Effort XS-XL.

## T1. Project scaffold
- Type: task | P0 | S | deps: none | parallel: yes (with T3)
- Vite + TS + Three.js WebGPU (WebGL2 fallback) + Rapier, pnpm, fps counter, empty scene. `pnpm dev` is the one local command. Spec §6, §10.4.
- Done when: 1. `pnpm dev` serves a page that opens in Safari. 2. fps counter visible. 3. Renderer logs which backend (WebGPU/WebGL2) is active; a `?webgl=1` flag forces WebGL2.

## T2. Check harness (Playwright screenshots + fps)
- Type: chore | P0 | M | deps: T1 | parallel: no
- Headless Playwright script: load scene at a named camera pose (position, yaw/pitch, lens) and save a PNG; sample fps for N s and print median/p1. Works for both backends. Spec §6 check loop, §8.
- Done when: 1. `pnpm check:shot <pose>` writes a PNG. 2. `pnpm check:fps` prints median fps and 1% low. 3. Backend flag selectable. 4. Camera poses live in one JSON file.

## T3. Reference survey and sheet
- Type: task | P0 | M | deps: none | parallel: yes
- Helper reads each pantry/seating photo and video frames: camera spot, lens estimate, size estimates, light state (on/off, sun), materials, brand details. Writes one reference sheet doc. Spec §5, §5b, §10b.5, §10c.
- Done when: 1. Sheet has an entry for every pantry and seating photo listed in §5/§5b. 2. Each entry has camera spot, lens, light state, materials. 3. Room size and counter position proposal listed.

## T4. Lighting spike (risk #1)
- Type: spike | P0 | L | deps: T1, T2 | parallel: no
- On a simple box room with one window: Blender Cycles bake (denoised HDR, plus directional lightmap), AgX in both, a probe sample, and a TSL material in Three.js that shows it. Must run on WebGPU and WebGL2. Spec §7, §10b.1-2.
- Done when: 1. Box-room screenshot from game is visibly close to Blender render (same AgX). 2. Normal-mapped surface reacts to directional lightmap. 3. A movable test sphere picks up probe light. 4. Same result on WebGPU and WebGL2, fps measured with T2. 5. Short written go/no-go plus fallback if any piece fails.

## T5. Room blockout in Blender + collisions + first-person controller
- Type: feature | P0 | L | deps: T1, T3 | parallel: yes (with T4)
- Python-scripted Blender blockout from the reference sheet: room shell, windows, pillar, chevron wall and door, counter spot, fridge niche. Export glTF; Rapier colliders; walk and sprint, mouse look. Spec §5b, §9 controls, §11.
- Done when: 1. One Blender script rebuilds the blockout headless. 2. Walk and sprint around the room, no walking through walls or counters. 3. Blockout loads in game at 60 fps in the harness.

## T6. Materials, textures and decals
- Type: feature | P1 | M | deps: T5 | parallel: yes (with T7)
- CC0 PBR textures (Poly Haven/ambientCG) colour-matched to photos for floor, walls, granite, cabinets, windows; decals for the sticky note, B'ONE sign, INNOVATION sign, mural, chevrons. Spec §6.
- Done when: 1. Each surface in the reference sheet has a material. 2. Decals placed from photo crops. 3. Texture licences recorded in one file. 4. Screenshot from one photo spot shows matching surfaces.

## T7. Branded props and furniture
- Type: feature | P1 | L | deps: T5, T3 | parallel: yes (with T6)
- Model Tata Bistro machine, LG fridge, LG microwave, kettle, sink, vending "PUSH" machine, water coolers, chairs, tables, mugs, flasks, purple jug, glasses, using public product shapes for unseen sides and photo decals. Each as a named object. Spec §4, §10b.7.
- Done when: 1. All listed props exist in the scene with unique names. 2. Branded items side by side with photos have no major brand differences. 3. Repeated items (mugs, chairs) are instanced.

## T8. Look data and Look highlight
- Type: feature | P1 | S | deps: T5 | parallel: yes (with T6, T7)
- Interaction framework core: raycast from the crosshair, highlight and prompt showing interaction level, name plus one-line caption from one editable data file (`captions.json`). Spec §9 Look and highlight.
- Done when: 1. Looking at any named object shows name and caption. 2. Editing the JSON changes the text on reload. 3. Highlight shows the level (Look/Use/Grab).

## T9. Grab via Rapier
- Type: feature | P1 | M | deps: T8, T5 | parallel: yes (with T6, T7)
- Pick up, carry, drop, toss small rigid bodies. Items settle on surfaces and never fall through. Spec §9 Grab, §8 no hitch.
- Done when: 1. Test cube can be picked up, carried, dropped and tossed. 2. 200 drops/tosses in a script: zero fall-throughs. 3. No frame over 33 ms during grab in the harness.

## T10. Full lighting bake, probes, reflections, tone mapping
- Type: feature | P1 | XL | deps: T4, T6, T7 | parallel: no
- Apply the spike pipeline to the full room: matched fixtures and daylight, high-quality Cycles bake (hours OK), directional lightmaps, light probes, baked reflection probes (granite, steel, fridge), window glow, contact shadows and AO for movable items. Spec §7, §10b.4-5.
- Done when: 1. One command re-bakes the room. 2. Movable mugs pick up room light and darken under cabinets. 3. Reflections visible on granite and fridge. 4. Runs on both backends. 5. fps recorded with T2.

## T11. Pantry Use items
- Type: feature | P2 | L | deps: T7, T8, T9 | parallel: yes (with T12)
- Coffee machine pour with steam and sound; microwave door plus countdown and ding; fridge door; kettle; sink; cabinet doors to reach mugs. Spec §9 Use.
- Done when: 1. Each listed item reacts as specified. 2. Cabinet opens and mugs can be grabbed. 3. No frame hitch when using each item (harness).

## T12. Seating Use items
- Type: feature | P2 | M | deps: T7, T8, T9 | parallel: yes (with T11)
- Chairs roll, swivel, can be sat in; vending machine drops a snack that can be grabbed; water coolers fill a glass. Spec §9 seating.
- Done when: 1. Sit and stand on a chair works. 2. Vending drops a grabbable snack. 3. Cooler fills a glass that can be carried.

## T13. Light switch with on/off bakes
- Type: feature | P2 | M | deps: T10, T8 | parallel: yes (with T11, T12)
- Second bake (lights off) and smooth blend in the TSL material; switch is a Use item. Spec §7 light switch.
- Done when: 1. Using the switch fades lights on/off in about 0.5 s. 2. Both states are baked by the same command. 3. No hitch measured at the switch.

## T14. Performance pass
- Type: task | P2 | L | deps: T10, T11, T12, T13 | parallel: no
- KTX2 textures, meshopt, instancing and draw-call budget, automatic resolution drop, High/Low setting, load time. Spec §8, §10b.2-3.
- Done when: 1. Median 60 fps and no stutter on the user's Mac, Safari and Chrome, both backends. 2. Load under about 10 s. 3. Low setting measurably faster, same default look. 4. Budget numbers in a short doc.

## T15. Photo-match iteration pass
- Type: task | P2 | L | deps: T10, T14 | parallel: no
- Screenshot from each photo's camera spot, helper compares to photo against the fixed checklist and lists major/minor differences. Fix majors and repeat. Spec §10b.6, §10.1.
- Done when: 1. Comparison report for every photo spot. 2. No major differences remain. 3. User gives the final verdict.

## T16. Audio
- Type: feature | P3 | S | deps: T11, T12 | parallel: yes (with T14, T15)
- CC0 sounds: coffee pour, microwave ding, fridge, vending drop, footsteps, ambience. Minimal mute/pause setting. Spec §3, §11.
- Done when: 1. Each Use item with a sound spec plays it. 2. Mute toggle works. 3. Licences recorded.

## Critical path
T1 -> T2 -> T4 -> T10 -> T13 -> T14 -> T15 (T6 and T7 also feed T10 via T5; T3 -> T5 -> T6/T7).

## Proposed order (user decides)
T1, T3 (parallel) -> T2, T5 -> T4 -> T6, T7, T8, T9 (parallel) -> T10 -> T11, T12, T13 -> T14 -> T15, T16.

Backlog ids: T1=TASK-1.1, T3=TASK-1.2, T2=TASK-1.3, T(n)=TASK-1.n for n>=4.
