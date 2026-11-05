# CCTech 4th Floor Game: User Stories (DRAFT for discussion)

Status: draft. No backlog, no code, no tech choices.

## 1. Vision

- 1. A 3D, fully interactive, lore-accurate copy of the CCTech 4th floor that you can explore freely.
- 2. v1 is free roaming only: walk around and poke at things. No goals, no score.
- 3. Audience (GUESS): CCTech colleagues who enjoy spotting real details.
- 4. Success (GUESS): a colleague says "that's our pantry!" within a minute of starting.
- 5. Playable characters come later (see "Later").

## 1b. Decided so far (by the user)

- 1. Platform: **browser game**, played from a shared link. Confirmed after weighing desktop: browser (WebGPU) with baked lighting is enough for one office floor; the real limit is model/texture accuracy, not the browser.
- 1a. Audience: **CCTech people only**, just for fun. Real logo, names and inside jokes are fine.
- 1b. **Top priority: realistic visual fidelity, true to the real office.** When trade-offs come up, looking like the real place wins.
- 1d. Laptops: a mix (Windows without gaming GPUs + MacBooks). User doesn't see it as a blocker. Target is **fully detailed realistic**; a quality setting (e.g. High / Low) keeps weaker laptops playable without lowering the default look.
- 1e. Who builds: **Claude builds everything** (code, models, materials). No human 3D artist.
- 1f. Realism path: true realism comes from **capture** — phone-video walkthrough → Gaussian splat room shell, touchable objects cut out and replaced with photo-based 3D models, lit from a 360° office photo, invisible collision layer, side-by-side screenshot-vs-photo check loop. Limits: unfilmed spots blur, glass is hard, light switches need lights-on/off captures, files must be compressed/streamed.
- 1g. **First pass (POC 1) uses only the 15 reference photos.** No video capture yet. So POC 1 is hand-built models + photo-matched textures + baked lighting; scanning comes in a later pass once the user is happy.
- 1h. **POC 1 scope: the pantry only, no people.**
- 1i. **Performance is equal to visual fidelity: "creamy smooth".** Proposed targets (Claude's call, to confirm): steady 60 fps with no stutter on a typical office laptop at the default look; no hitch when grabbing/tossing or opening things; pantry loads in under ~10 s. Means: baked lighting (cheap to draw), compressed models/textures, few draw calls, instancing, auto-lower render resolution if frame rate dips, fps counter + budget checked every pass.
- 1k. **Lighting is the game changer — top of the fidelity list.** Approach (Claude's call): match the real fixtures (LED panel colour temperature, brightness) and real window daylight (physical sky, time of day matched to the photos); bake full bounce light in Blender Cycles at high quality, denoised, stored as HDR lightmaps; directional lightmaps so surface detail still catches light; light probes so moving objects (a grabbed mug) darken under cabinets and pick up room colour; baked reflection probes for granite/steel/fridge, sharper reflections on High; small live contact shadows + ambient occlusion for movable items; same tone mapping (AgX) in Blender and in the game so the bake looks identical in-browser; bright window with subtle glow; lights-on/off bakes blended smoothly for switches. Lighting gets its own photo-match check (brightness, colour warmth, shadow softness).
- 1j. Tech stack (Claude's call, user OK'd): Three.js (WebGPU, WebGL2 fallback) + TypeScript + Vite + pnpm; Rapier physics; Blender driven by scripts for modelling and Cycles light baking; CC0 PBR textures (Poly Haven / ambientCG) colour-matched to photos; photo-cut decals for labels; glTF + KTX2 + meshopt compression; Playwright screenshots vs reference photos for the check loop.
- 1c. To try in an early POC: compare "hand-made models only" vs "phone-video 3D scan (Gaussian splat) for the room + models for touchable objects" in one area (e.g. pantry). Light switches need on/off baked lighting.
- 2. "Fully interactive" means three levels (agreed as the right level):
  - Look: every visible object can be pointed at and shows its name plus a one-line lore caption.
  - Use: things you'd touch in real life work like real life (doors, appliances, chairs, lift button, light switches).
  - Grab: small loose things can be picked up, carried, dropped and tossed (mugs, flasks, magazines, bins, jug).
- 3. Not in v1: breaking things, other people walking around, riding the lift to other floors.
- 4. Respect rule: the Ganesha idol is Look-only. No grabbing or tossing it.
- 5. Photos: v1 POCs use only the 15 existing photos. The user shares more (desk area, meeting rooms, etc.) once the first few POC passes feel right.

## 2. v1 stories (free roam)

### Moving around

- 1. As a player, I want to walk around the floor in first person so that it feels like being there.
  - Done when: I can move and look with keyboard and mouse.
  - Done when: I can't walk through walls, furniture or closed glass.
- 2. As a player, I want to start at the building entrance so that the tour follows the real arrival path.
  - Done when: a new game begins at the entrance door.
  - Done when: from there I can reach lobby, reception, corridor, pantry, cafeteria and balcony on foot.
- 3. As a player, I want doors to open and close so that I can enter the rooms like in real life.
  - Done when: the wooden and glass entrance doors and the frosted office doors open when I interact.
  - Done when: the face reader beeps before the "Digital Transformation Unit" door opens.
  - Done when: doors don't trap or block me.
- 4. As a player, I want to use the lift and stairs so that the lobby feels real. (Decided: no riding to other floors in v1.)
  - Done when: I can press the lift button, it lights up, and the doors open.
  - Done when: the stairs beside the lift can be walked up to a landing (or are clearly blocked).
- 5. As a player, I want a sprint and a way to see where I am so that I don't get lost.
  - Done when: I can hold a key to move faster.
  - Done when: a simple map or area name (e.g. "Pantry") shows where I am.

### Interacting with objects (Look / Use / Grab)

- 6a. As a player, I want to point at any visible object and see its name and a one-line lore caption so that every corner has something to discover. (Look level)
  - Done when: every modelled object shows a name and caption when I aim at it.
  - Done when: captions live in one editable list so the user can add inside jokes later.
  - Done when: the Ganesha idol shows a caption but cannot be grabbed (respect rule).
- 6. As a player, I want to use the pantry appliances so that the pantry feels alive. (Use level)
  - Done when: the coffee machine pours with steam and sound; the microwave counts down and dings; the fridge opens; the kettle and sink respond.
  - Done when: a highlight or prompt shows what I can interact with, and which level (look, use or grab).
- 7. As a player, I want to pick up, carry, drop and toss small items (mugs, flasks, jug, magazines, bins, sticky note) so that "fully interactive" is real. (Grab level)
  - Done when: I can pick up, carry, drop and toss them.
  - Done when: dropped or tossed items land on surfaces and don't fall through the floor.
  - Done when: nothing breaks (decided: no breaking in v1).
- 8. As a player, I want to use the vending machine and water coolers so that the cafeteria feels lived in. (Use level)
  - Done when: "PUSH" drops a snack I can grab, and the coolers fill a glass.
- 9. As a player, I want chairs to roll, swivel and let me sit so that the room feels real. (Use level)
  - Done when: I can push a chair, swivel it, sit, and stand up again without getting stuck.
- 9b. As a player, I want light switches to work so that I can play with the lighting. (Use level)
  - Done when: switches turn their area's lights on and off.
- 10. As a player, I want to read the sticky note, plaque and signs up close so that the text details pay off.
  - Done when: signs and notes are readable when I walk up to them.

### Lore and easter eggs

- 11. As a colleague, I want signs, logos and quotes to match the real floor so that I trust it as a true replica.
  - Done when: the plaque, RECEPTION sign, "Digital Transformation Unit" door, B'ONE sign, INNOVATION sign and wall quote use the exact real text.
  - Done when: someone from CCTech checks them against the photos.
- 12. As a colleague, I want the real brand items (Tata Bistro, LG, the Ganesha idol, framed certificate) in the right places so that I can spot them.
  - Done when: each appears where the photos show it.
- 13. As a colleague, I want small hidden details (e.g. the face-reader beeping, a fun line on the certificate) so that exploring is rewarded. (GUESS: needs the user's picks)
  - Done when: at least 5 discoverable details exist and are listed in a checklist for testers.

### Look and feel

- 14. As a player, I want the floor to look like the real one (white walls, wood-look floors, frosted glass, granite, orange and blue) so that it feels right.
  - Done when: side-by-side with the photos, a colleague agrees each area looks the same.
- 15. As a player, I want ambient sound (AC hum, distant chatter, coffee machine) so that it feels like an office.
  - Done when: sounds change by area and can be turned off.
- 16. As a player, I want the room layout and sizes to be accurate so that walking distances feel real.
  - Done when: a floor plan is agreed and the model matches it (needs measurements, see questions).

### Settings and basics

- 17. As a player, I want to pause, adjust volume and mouse sensitivity, and quit so that I'm comfortable.
  - Done when: a pause menu offers these and saves them.
- 18. As a player, I want it to run smoothly on a normal office laptop so that colleagues can actually try it.
  - Done when: it holds a steady, smooth frame rate on a typical CCTech laptop (target to agree).

## 3. Later (not v1)

- 1. Playable characters (choose or customise, maybe colleague look-alikes).
- 2. Missing areas once photographed: main desk area, meeting rooms, cabins, washrooms.
- 3. NPC colleagues walking around, goals or mini-games, multiplayer, riding the lift to other floors.
- 3b. Breaking things (glass, mugs).
- 4. Seasonal or event decorations (e.g. festival, party).

## 4. Open questions (most important first)

- ~~Platform~~ decided: browser.
- ~~How "fully interactive"~~ decided: Look / Use / Grab (see 1b).
- ~~Missing areas~~ decided: photos come after the first POC passes.
- 4. Is the audience only CCTech staff? Is sharing outside the company OK (logos, brand, real names)?
- 5. Is real people's data (names, faces, desk labels) allowed, or keep it anonymous?
- 6. Any real-life measurements or a floor plan available?
- 7. Which inside jokes or hidden details do you want?
- 8. Does the company need to approve use of the logo and the "Digital Transformation Unit" name?

## 5. Proposed order (rough)

- 1. Walk around plus collisions in a simple version of the layout (stories 1, 2, 16).
- 2. Photographed areas looking right: lobby, reception, corridor, pantry, cafeteria, balcony (14, 11, 12).
- 3. Doors, lift, readable signs (3, 4, 10).
- 4. Look captions everywhere, then pantry and cafeteria interactions (6a, 6, 7, 8, 9, 9b).
- 5. Sound, map, settings (5, 15, 17).
- 6. Easter eggs and polish and performance (13, 18).
- Order is a proposal; you decide.
