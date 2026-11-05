# POC 1 — CCTech Pantry + Seating (one open room): Design

Status: draft for approval. Date: 2026-11-05.
Related: `docs/product/user-stories-draft.md` (full v1 stories and all decisions so far).

## 1. Intent and why

- The long-term game: a 3D, free-roam, lore-accurate replica of the CCTech 4th floor, played in a browser, just for CCTech people to have fun. Playable characters come later.
- What matters most to the user: **real realism** — visual fidelity true to the real office — with **lighting as the game changer**, and **"creamy smooth" performance** treated as equally important.
- POC 1 exists to prove that a browser can deliver that look and smoothness, using the pantry as the test room, and to let the user judge lighting, materials and the Look / Use / Grab feel before more areas (and more photos / video scans) come in.

## 2. Goals

- 1. A walkable, first-person 3D pantry + seating room that a CCTech colleague recognises instantly from the reference photos.
- 2. Lighting that reads as real: true-to-fixture colour and brightness, real window daylight, soft bounce light, believable shadows and reflections.
- 3. Steady, stutter-free performance on typical office laptops (mix of Windows laptops without gaming GPUs and MacBooks).
- 4. The three interaction levels working in the pantry:
  - Look: every modelled object shows its name + a one-line lore caption.
  - Use: real-life behaviour for things you'd touch.
  - Grab: small loose items can be picked up, carried, dropped, tossed.
- 5. A repeatable photo-match check (game screenshot vs reference photo from the same spot).

## 3. Non-goals (POC 1)

- Any area outside the open pantry + seating room (lobby, reception, corridor, balcony come later).
- People / NPCs / playable characters.
- Breaking things.
- Video/Gaussian-splat capture (later pass, once the user is happy with POC passes).
- Map, menus beyond a minimal settings/pause, sound mixing polish, deployment to a public host. POC is run locally.

## 4. Anti-goals (a failure even if it "works")

- Looks like a generic video game or a stock asset pack rather than *our* pantry.
- Flat, uniform, "gamey" lighting; objects that glow or float because they don't sit in the room's light.
- Stutter, frame drops, or hitches when grabbing or using things.
- Wrong brand details (the Tata Bistro machine, LG fridge/microwave, B'ONE sign must be right).

## 5. Constraints

- Platform: browser (WebGPU, WebGL2 fallback). Runs locally.
- Source material: **only the existing reference photos** in `references/img/photos/`. Pantry photos (per the image survey):
  - `WhatsApp Image 2026-11-05 at 15.25.06 (1).jpeg` — Tata Bistro coffee machine, LG microwave, flasks, "B'ONE" sign.
  - `WhatsApp Image 2026-11-05 at 15.25.07 (1).jpeg` — cabinets full of mugs, kettle.
  - `WhatsApp Image 2026-11-05 at 15.25.07 (2).jpeg` — silver LG fridge by the windows.
  - `WhatsApp Image 2026-11-05 at 15.25.07.jpeg` — sink, purple water jug, flasks, yellow sticky note.
  - The other photos can be used for overall style (white walls, wood-look floor, granite, CCTech orange/blue).
- Sizes and unseen sides must be estimated from the photos; there are no measurements or floor plan.
- Claude builds everything (code, models, materials, lighting). No human 3D artist.
- Free tools / CC0 assets only. Package manager: pnpm.
- Audience is internal: real logo, brand names and inside jokes are fine.

## 5b. Scope (user-decided)

- The pantry and the cafeteria seating are **one open room**; POC 1 includes the whole room: kitchenette counter, fridge, seating (white tables, green / light-blue chairs), the orange/red chevron wall with its dark door, the vending ("PUSH") machine and water coolers under the circuit-arrow mural, the "INNOVATION" sign, and the floor-to-ceiling windows.
- Extra reference photos for the seating side: `WhatsApp Image 2026-11-05 at 15.25.08.jpeg` (water coolers + mural), `...15.25.08 (1).jpeg` (vending machine + cooler), `...15.25.08 (3).jpeg` (cafeteria chairs, INNOVATION sign).
- **Counter position is not shown anywhere** (Claude's call): place the kitchenette counter in a plausible spot consistent with the photos and video; the user corrects it after the first pass.

## 6. Decided "how" (user-approved)

- Engine: **Three.js** (WebGPU renderer, WebGL2 fallback), **TypeScript**, **Vite**, **pnpm**.
- Physics and collisions: **Rapier**.
- Modelling: **Blender, driven by Python scripts**; scene built to sizes estimated from the photos.
- Materials: CC0 PBR textures (Poly Haven / ambientCG) colour-matched to the photos; brand labels and the sticky note as decals cut from the photos.
- Assets shipped as glTF with compressed textures (KTX2) and compressed meshes (meshopt).
- Check loop: Playwright screenshots from camera positions matching each pantry photo (same lens width), compared side by side by a helper; iterate.

## 7. Lighting (the game changer)

- Match the real fixtures (LED colour temperature and brightness) and the real window daylight (physical sky, time of day matched to the photos).
- Bake full bounce lighting in Blender Cycles at high quality, denoised, stored as HDR lightmaps.
- Directional lightmaps (or equivalent) so normal-mapped detail (wood grain, granite) still reacts to light.
- Light probes so moving/grabbed objects pick up the room's light and darken under cabinets.
- Baked reflection probes for granite, steel and fridge; sharper reflections on the High setting.
- Small live contact shadows and ambient occlusion for movable objects.
- Same tone mapping (AgX) in Blender and in the game so the bake looks identical in the browser.
- Bright window with subtle glow.
- Light switch: lights-on and lights-off bakes, blended smoothly.
- Lighting has its own photo-match check: brightness, colour warmth, shadow softness.

## 8. Performance ("creamy smooth")

- Targets (proposed, Claude's call): steady **60 fps** with no stutter on a typical office laptop at the default look; no hitch when grabbing, tossing or using things; pantry loads in **under ~10 s** locally.
- Means: baked lighting, compressed assets, few draw calls, instancing for repeated items (mugs), automatic render-resolution drop if frame rate dips, on-screen fps counter, budget checked every pass.
- A High / Low quality setting; Low keeps weaker laptops smooth without changing the default look.

## 9. Interactions in the pantry

- Look (all modelled objects): name + one-line lore caption; captions in one editable data file so the user can add inside jokes.
- Use:
  - Coffee machine: pour with steam and sound.
  - Microwave: door opens; countdown and ding.
  - Fridge: door opens.
  - Kettle and sink: respond (animation and/or sound).
  - Cabinet doors open (to reach mugs).
  - Light switch: lights on/off (see lighting).
- Use (seating side): chairs roll, swivel and let you sit; "PUSH" vending machine drops a snack you can grab; water coolers fill a glass.
- Grab: mugs, flasks, purple jug, sticky note, dropped snack, glasses (and any other small loose items visible in the photos). Pick up, carry, drop, toss; items land and settle on surfaces and never fall through.
- A highlight/prompt shows what can be interacted with and at which level.
- Controls: first-person, keyboard + mouse, walk and sprint; collisions with walls, counters and fridge.

## 10. Done when

- 1. From each pantry photo's camera spot, the game screenshot is judged a close match (layout, materials, brand details, lighting) by side-by-side review; the user agrees it looks like our pantry.
- 2. The fps counter shows a steady ~60 fps on the user's laptop at the default look, with no visible stutter during interactions.
- 3. Every Look / Use / Grab item listed above works.
- 4. Runs locally with one command and opens in Safari.

## 10b. Calls made after the builder check (Claude's calls, user to review)

- 1. **Custom shader work is expected.** Directional lightmaps, light probes, reflection probes and the lights-on/off blend are not built into Three.js; the builder writes them (prefer TSL node materials so they compile to both WebGPU and WebGL2). A plain lightmap + ambient term is only a fallback if a piece proves impossible, and must be reported.
- 2. **60 fps must hold on both WebGPU and the WebGL2 fallback.** No WebGPU-only features in the default look. Test in Safari (the user's browser) and Chrome.
- 3. **Reference machine:** the user's own Mac for the 60 fps check; the Low setting is the safety net for weaker Windows laptops.
- 4. **Bake time:** Blender Cycles bakes may run long (hours is fine) on the user's Mac; quality over speed for the bake.
- 5. **Light state:** photos were taken around 15:20 on 5 Nov 2026 (Pune afternoon, guess). A helper reads each pantry photo for lights on/off, sun vs overcast and fixture type before the bake; bake an afternoon daylight state to match.
- 6. **"Close match" judging:** a helper compares each screenshot with its photo against a fixed checklist (layout, object placement, materials, brand details, brightness, colour warmth, shadow softness) and lists differences as major/minor. Iterate until no major differences remain; the user then gives the final verdict. No numeric score in POC 1.
- 7. **Unseen sides of branded objects** (Tata Bistro machine, LG fridge/microwave): modelled from the real product's known shape (public product images as reference), with decals from the photos.

## 10c. What the pantry video shows (`references/video/WhatsApp Video 2026-11-05 at 15.47.51.mp4`, 8.7 s, 480p; frames in `references/video/frames/`)

- Panning view (turning right, uncertain): floor-to-ceiling windows with a city view along one side; a stainless single-door fridge beside a pillar near the start; an orange/red chevron graphic wall with a dark door and a vending/water unit; open seating with white tables and green / light-blue chairs.
- Lighting: daylight dominates; hard sunlight from the window side with bright patches on pillars and floor; ceiling lights look off or are not visible; neutral to cool white.
- Materials (estimates): light grey/beige floor, white walls with orange/red chevron graphics, dark speckled granite counter, white high-gloss wall cabinets.
- Size (guess): roughly 8 x 6 m, ceiling about 3 m.
- Not seen: the kitchenette counter (sink, coffee machine, microwave) in relation to the windows/fridge, ceiling fixtures, door location, the back wall.

## 11. Left to the builder

- Exact project structure, file layout, and how Blender scripts are organised.
- Specific CC0 textures/models chosen, and lightmap resolution/format details, as long as the lighting and performance goals hold.
- How the auto-resolution and quality settings are implemented.
- Exact sounds (CC0) and caption wording (placeholder captions are fine; the user adds inside jokes later).
- Which parts of the pantry beyond the photos to invent (keep it plausible and consistent with the photos).
