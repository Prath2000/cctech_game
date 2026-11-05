# NNNN-slug: verify
## Tests
- **Tests:** 
- **E2E:** 
## Review
- **Review:** 
- **Security:** 
- **Perf:** 
- **Bugs / tech debt filed:** 
## Result
- **Verdict:** pass | fail

## Photo-match pass 1

Shots: `.team/work/shots/<pose>-webgpu.png` (WebGPU, 1600x1200). Side-by-sides (photo left, shot right): `.team/work/shots/match-<pose>.png`. Raw logs: `.team/work/scratch/shot-<pose>.log`.
Poses: coffee-06-1, cabinets-07-1, fridge-07-2, sink-07, coolers-08, vending-08-1, cafeteria-08-3, strip-08-2. Not compared (no photo): overview, spike, video-start/end.

### Cross-cutting
- MAJOR Pose/harness: portrait poses (fridge-07-2, coolers-08, vending-08-1) render 4:3 landscape, not 3:4. Fix: scripts/shot.ts viewport from pose aspect + camera-poses.json aspect field.
- MAJOR Lighting: no hard sun patches or window light pools on floor/walls; whole room is flat, cool-white, evenly lit and soft-shadowed. Photos show warm, hard-edged sun (photographer shadow, diagonal window patches on floor). Fix: blender/bake_room.py sun lamp (low angle, strong, warm ~5000K, small angle for hard shadow).
- MAJOR Brightness/warmth: photos warm (cream #f3efe6 walls, beige floor tiles); shots are grey/cool and floor is bright white-blue. Fix: bake_room.py world/sun colour, blender/materials.py wall/floor albedo.
- MINOR Wall/ceiling: wall is a rough grey concrete texture; photos show smooth off-white paint. Fix: materials.py wall material (lower roughness texture, warm white).

### coffee-06-1
- MAJOR Brand/shape: Tata Bistro machine is a plain black box with a small screen inset; photo has a sloped front, tall wide body, big TATA BISTRO touchscreen angled out, drip tray. LG microwave is too small/placed wrong (photo: left, on a shelf above counter at the left). Fix: blender/props/coffee_machine.py (or equivalent), microwave placement in layout.py.
- MAJOR Missing: B'ONE panel/door on right wall, notice sheet by microwave, window view above microwave (photo shows city through window, top-left). Fix: layout.py + props.
- MINOR Counter: granite top okay but photo has curved front/side panel; thermos/jar small items differ. Fix: props.
- MINOR Pose: shot is further/right and sees more bare wall; photo is closer to the counter, machine fills the right half. Fix: camera-poses.json move x down ~0.5, yaw a few degrees left.

### cabinets-07-1
- MAJOR Layout: photo has 3 tall glossy doors, shelf row of colourful mugs (red, blue, black, grey, white, pink) and a dark window/city on right. Shot has 2 doors and a uniform grey mug row; no coloured mugs. Fix: blender/props/cabinet*.py door count, mug colour list in props.
- MAJOR Pose: shot looks up and sees counter items in foreground (purple jug); photo has the cabinet bottom at 3/4 height and a socket plate below. Fix: camera-poses.json lower pitch (~12 to 0..5), move back.
- MINOR Window view on right missing (photo: dark glass + skyline). Fix: layout.py window/glazing and the HDRI.

### fridge-07-2
- MAJOR Object: fridge is small, far, and set against a wall; photo is a close-up of a large silver LG double-door fridge (freezer top, curved handle) with window wall on left. Fix: pose (move closer, x ~6.2?) and fridge size in blender/props/fridge.py (scale up to 1.5-1.7 m high x 0.6 m wide).
- MAJOR Window: photo shows a full glazed wall left with city view; shot has windows partly occluded by a large grey slab (counter, ~half frame) in foreground. Fix: layout.py (slab blocks view; likely counter/ledge mis-sized) or camera-poses.json.
- MINOR Stickers on fridge present but differ (LG/10-year badge shapes). Fix: props/fridge.py decals.

### sink-07
- MAJOR Shapes: purple jug is huge and sits in front of sink; photo jug is narrower, translucent pink-purple, sitting back near the wall. Flasks/jars are blocky white/black cylinders; photo has steel flasks. Soap dispenser, red cloth, yellow cloth, stainless sink basin missing/wrong (shot has two flat grey panels). Fix: props/jug.py scale+position; layout.py sink basin; props small items; materials.py steel.
- MINOR Socket plate present; microwave top-right matches roughly; mug shelf shown as plain white mugs. Fix: mug colours.
- MINOR Pose: shot ~0.5 m too close and shifted; photo frames jug mid-frame.

### coolers-08
- MAJOR Layout: photo shows two white/blue water coolers with blue covered bottles at 1.0 m height, mural arrow above pointing left, vending machine dark at right edge. Shot has right object correct but is too zoomed: vending machine occupies right third and coolers' bottles are large. Fix: camera-poses.json (back up ~1 m; aspect 3:4).
- MINOR Mural: circuit arrow pattern present and good; photo arrow is lighter and ends further right. Fix: materials.py mural decal scale.
- MINOR Chair in photo foreground missing. Fix: layout.py add dark mesh chair.

### vending-08-1
- MAJOR Brand: PUSH vending machine has no PUSH text, no green lower dispense flap/bay, and the touch panel is a blank white rectangle (photo: small tablet with keypad grid). Machine is too wide/box-like with chunky frame; shelf products are muted. Fix: blender/props/vending.py (add PUSH label, green flap, keypad texture).
- MAJOR Pose: shot centres machine and sees the side coolers behind it; photo has full machine in view at 3/4 height with the coolers left. Fix: camera-poses.json back up ~1 m, yaw ~90, aspect 3:4.
- MINOR Light strip inside machine overexposed; photo has bright inner light but softer.

### cafeteria-08-3
- MAJOR Brand: INNOVATION chevrons are red-orange and present but smaller and farther than the photo and text is hardly legible; in photo they are the dominant feature (large orange chevrons, ~25% of wall width). Fix: layout.py/materials.py chevron size (x1.3) and colour #e5663a.
- MAJOR Furniture: photo has dense mixed olive-green and blue chairs closely around white tables in front of the camera; shot has sparse chairs of the same palette, tables too long and floor is bright white. Fix: layout.py chair count/spacing, table sizes.
- MINOR Pose: camera is a bit high; photo is at table level with floor visible. Fix: camera-poses.json y 1.3->1.15, pitch -5.
- MINOR Ceiling: photo has fans, grid panels; shot has perforated white. Fix: layout.py ceiling props.
- MINOR Dark-glass windows on right in shot show a bright sky; photo has dim skyline with buildings. Fix: window view HDRI/backdrop.

### strip-08-2
- MAJOR Layout: photo is a narrow window-side strip with a dark low ledge on the window side (granite), 2 bins (red and green) in foreground, a silver fridge and a person at a desk with a red/orange/blue chevron at the far end. Shot shows the strip as a wide hall: cafeteria is in view at right, far end has coffee counter; fridge missing at the end; ledge not visible as granite. Fix: layout.py (strip must be walled by a partition at its east side), pose pitch/yaw, add bins in props.
- MAJOR Pose: shot is ~2 m back and yawed so window wall dominates left; the photo is a corridor view along the glass. Fix: camera-poses.json yaw to -90 and x ~3.
- MAJOR Window view: photo has parked cars and city; shot is blank blue/white. Fix: window backdrop plate in layout.py / bake_room.py.
- MINOR Floor: beige tile with strong sun patches in photo; shot nearly white with no patches (see lighting).
