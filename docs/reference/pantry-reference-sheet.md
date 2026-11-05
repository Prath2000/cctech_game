# CCTech pantry + seating: reference sheet (TASK-1.2)

Every number is an ESTIMATE from photos unless marked "seen". **[G]** = guess. Photos: WhatsApp Image 2026-11-05, stamped 15:18-15:20 (Pune, India, guess). Short names below drop the "WhatsApp Image 2026-11-05 at 15.25." prefix.

## 1. Conventions
- Units metres. Origin = floor corner where the window wall meets the west wall (top-left of plan). **x = right (east), z = toward the viewer (south, into the room), y = up.**
- Window wall = **north wall, z = 0**. Default three.js camera at yaw 0 looks along -z (at the windows).
- Yaw in degrees, counter-clockwise seen from above: 0 looks -z (windows), +90 looks -x (west wall), -90 looks +x (east wall), 180 looks +z. Pitch + = up. hfov = horizontal field of view.
- Scale anchors: door leaf 2.1 m [G, standard]; counter top 0.9 m [G, standard]; 600x600 mm floor tiles [G]; cooler body ~1.0-1.1 m + bottle ~0.45 m; fridge ~1.65-1.75 m (LG top-freezer 2-door class); vending machine ~1.8-1.9 m; chair seat 0.45 m; white table top 0.75 m.

## 2. Same room?
- `08 (2)` (long strip beside the windows, fridge at its far end, red/white/blue chevron wall, wooden desk) is the **same open space**. The video pan (f_01 to f_09) turns from that strip straight into the seating hall with the vending/cooler wall, so it is one L-shaped open area.
- For the POC it is simplified to one rectangle: the strip becomes the east end of the window wall (fridge corner), the hall is the rest.
- The red/white/blue chevron wall (east end) differs from the orange "INNOVATION" chevron wall (west wall).

## 3. Room (proposal, all [G])
| Item | Value | Estimated from |
|---|---|---|
| Footprint | **8.0 (x) x 6.0 (z) m** | prior read; hall ~3 table rows deep, strip ~2.5 m wide; could stretch to 9 m |
| Ceiling | 3.0 m [G] | door 2.1 m + header; tile grid 600 mm |
| Window wall | z=0, full length, floor-to-ceiling black-framed glass, ~9 panes ~0.9 m wide, 0.9 m granite sill inside the strip | `08 (2)`, `08 (3)`, video |
| Sill | granite, dark (#2a2b30), 0.9 m high, ~0.5 m deep, in the strip (x 4.5-8) | `08 (2)` |
| Floor | glossy cream-white tile #e6e2d8, 600 mm, skirting #cfc9bb | `08 (3)` |
| Ceiling | white 600x600 grid tiles #f1f1ef, 3-4 ceiling fans, CCTV domes | `08 (3)` |
| Pillar | white square column 0.6 x 0.6 m at about (5.9, 2.2) | `08 (2)` foreground right, video f_09 |

### Proposed counter position
- **Counter on the east wall (x = 7.4-8.0), z = 1.4 to 4.4 (3.0 m long, 0.6 deep, 0.9 high), front facing west (-x).** Window-side end is ~1.4 m from the window wall, so the sink/mug cabinets sit near the glass (windows seen right of the cabinets in `07 (1)`).
- Wall cabinets (3 doors, ~1.8 m wide) at y 1.45-2.15 above the sink; microwave on a bracket and a TV above the coffee end.
- Fridge in the window corner at (7.3, 0.4), facing -x/+z towards the room, as in `08 (2)`. Counter position relative to windows/fridge is NOT seen anywhere: guess.
- Water coolers and vending machine on the west wall near the door.

### Plan (top-down, metres)
```
 x=0                                          x=8
 z=0 +=====================WINDOWS (north wall)====================+
     |  chevrons(orange)            sill . . . . . [FR]            |
     |  z1.2-2.8          corridor strip      pillar#   |#COUNTER#  |
 z=2 |                                              ##  |# sink  #  |
     |  DOOR z3.2-4.4          tables (white)           |# TATA  #  |
 z=4 |  [VEND] z4.6-5.4   o o o o  x2.5-5.5             |#########  |
     |  [C1][C2] z5.5-5.9     green/blue chairs           (x7.4-8)  |
 z=6 +=============================================================+
        west wall (x=0)                                east wall (x=8)
 FR = LG fridge (7.3,0.4). C1/C2 = Voltas coolers. VEND = vending, on west wall.
 Table rows: 2 rows of 2 white tables (1.5x0.75) at x~2.5-5.5, z~1.5 and z~3.5, plus row near z~5.

```
- Table layout is a guess from `08 (3)` and video f_17: long white tables pushed together in rows parallel to the window wall.

## 4. Photo entries
Common: light state for all = **daylight only, hard low-ish afternoon sun (elev ~35-40°, Nov 15:20) coming through the window wall, throwing long shafts and window-frame shadows on the floor**. Ceiling panel lights: no visible lit fixtures [G: off, or too weak against the sun]; ceiling fans visible but still. Sun is from the window side (north wall, slightly west of the glass normal: patches fall toward +z/+x).

### 4.1 `06 (1)` Coffee station (Tata Bistro, LG microwave)
- **Camera:** at ~(6.7,1.4,3.6), 1.1 m in front of the counter, looking at the back wall (roughly -x/east wall side, yaw ~-85). Height ~1.4 m, pitch -5°.
- **Lens:** phone main, hfov 69° (landscape).
- **Light:** direct sun from the left/front-left, hard shadow of photographer on the counter; bright blown-out wall #f3efe6.
- **Materials/colours:** counter granite with white-grey speckle #3a3a3e (dark grey/black, polished); counter fascia white #ecebe8; wall plaster off-white #e8e4da; coffee machine matte black #1f2022 with a dark steel top; microwave black #17181a with glass door; TV black #101214; sheet on the wall white paper.
- **Objects:** Tata Bistro bean-to-cup machine ~0.45 W x 0.55 D x 0.65 H on the counter (the right half, sits on a granite return that has a raised edge); LG microwave ~0.5 x 0.3 x 0.3 m on a bracket at y~1.2-1.5; flat TV above (~1.0 m wide) at y~1.7-2.2; stainless flasks 0.08 dia x 0.25 H; white glass jar (storage canister) 0.1 dia x 0.18; steel tumbler 0.07 x 0.09; white rectangular tissue/paper dispenser box 0.3 x 0.12 x 0.2 [G]; grey rubber mat on the counter; white drain pipe vertical on wall 0.05 dia; "B'ONE" boxed item and a stainless panel (fridge side) at the far right.
- **Text/brands:** "TATA Bistro" on the screen and the front (white/blue letters, #ffffff on #3b4a6b screen); "LG" on the microwave; "B'ONE" printed on a carton at right; a laminated A4 notice (red/white table) on the wall; red date stamp (overlay, ignore).

### 4.2 `07 (1)` Cabinets of mugs
- **Camera:** ~(6.9,1.5,2.8), standing at the counter, looking up slightly at the wall cabinets, yaw ~-88, pitch +12°.
- **Lens:** phone main, hfov 69°, landscape.
- **Light:** sun glare from the window side (right), cabinet gloss reflects the window and photographer; no visible fixture lights.
- **Materials/colours:** high-gloss laminate doors light grey #cfcdca (very reflective, roughness ~0.1); open shelf below the doors, shelf interior #e4e2de; glass shelf at left; wall below plaster #ece8de; grey-blue window curtain/glass at far left #8aa0b3; black glossy panel (window/TV glass) on the right.
- **Objects:** wall unit ~1.9 m wide x 0.35 deep: three doors (each ~0.6 w x 0.7 h) at y~1.45-2.15; open shelf at y~1.2-1.45 under the doors holding ~14 mugs (0.08-0.1 dia x 0.095 H) in brown, navy, white, red, green, patterned; side open shelving at left with dish soap (yellow, 0.25 H), sponge tub; 6-way white switchboard with plugs at y~1.15 (0.12 x 0.2 [G]); purple kettle (jug) at the bottom; black microwave visible at the lower right.
- **Text/brands:** one white mug has a logo; no readable text otherwise.

### 4.3 `07 (2)` LG fridge by the windows
- **Camera:** ~(4.5,1.3,1.2) looking east at the fridge ~3 m away, yaw ~-85, pitch -5°. Portrait photo.
- **Lens:** phone main, portrait hfov ≈ 54° (vertical of landscape 69°).
- **Light:** strong sun from the left (window side) producing shadow diagonals across the fridge and floor; sill granite reflecting.
- **Materials/colours:** fridge brushed stainless/silver #b7b9bb, plastic handle and trim #8c8e90; sill granite black-speckled #25262a; sill wall white #efece4; window frames black #1a1c20, glass faint blue-grey; floor tile #e8e4da with beige grout; right of the fridge a white pillar/wall edge #f4f2ec with a blue/orange chevron mural slice (blue #1d8ed9, orange #e8602c); black mesh chair at the right (#1e1e20).
- **Objects:** LG top-freezer ~0.55 W x 0.65 D x 1.70 H; small white tray (tissue box) on the sill ~0.15 x 0.08; sill ~0.9 m high; a power cable to the wall.
- **Text/brands:** "LG" top-left; sticker "Take only what you have kept here. Respect others' belongings." (yellow/white round, 0.12 dia); "Smart Inverter 10 Year warranty" sticker; "Power Savings Guide" star-label (red/yellow, 0.1x0.14); QR code label.

### 4.4 `07` Sink + purple jug + flasks
- **Camera:** ~(6.9,1.6,3.2), 0.9 m from the counter, looking down, yaw ~-90, pitch -22°.
- **Lens:** phone main, hfov 69°, landscape.
- **Light:** raking sun from the left casting the photographer's long shadow on the counter; strong hot spots on the wall.
- **Materials/colours:** counter granite dark with silver flecks #2d2d31, thickness ~0.03; base cabinets white laminate #eeeeea with chrome bar pulls (~0.12 long) -- three 0.45-0.6 wide doors; wall plaster off-white #ece8de, mild stains; sink single steel bowl #a6a8aa (0.5 x 0.4, ~0.18 deep) cut into the granite; grey drying mats #8e9195 (two, ~0.4 x 0.3); upper shelf edge at the top.
- **Objects:** purple 20 L water jug (#b66ac8 translucent pink-purple, 0.27 dia x 0.48 H) upside-down with a hose to a pump; soap dispenser wall-mounted white/clear (0.07 x 0.07 x 0.2) at y~1.2; red towel over the corner; steel flasks (0.07 dia x 0.27 H) x3-4, glass bottle (0.07 x 0.25), olive green mug #6f7a3a; yellow sticky note #f2d94a (0.1 x 0.1) on the granite; sponge/soap holder caddy; 6-way switchboard at y~1.1 with grey cable; white tissue dispenser at right; LG microwave bottom-right on a bracket.
- **Text/brands:** "LG" on the microwave; label on the jug unreadable.

### 4.5 `08` Water coolers + circuit-arrow mural
- **Camera:** ~(1.2,1.3,3.2) camera ~2.2 m from the west wall at ~(2.2,1.2,5.4), yaw +90, pitch 0. Portrait.
- **Lens:** phone main, portrait hfov ≈ 54°.
- **Light:** soft, mostly bounced daylight (no direct patch on the wall), even and cool; vending glass reflecting.
- **Materials/colours:** wall plaster #ece9e0; skirting beige tile #c9c1ae; floor #dedad0; coolers glossy white #f3f5f6 with blue #1f9ad6 drip tray and blue basin; water bottle covers royal blue fabric #1c6ec0 with clear vinyl window strip; mural vinyl: light blue #3fb4e0 and navy #1a58a8 circuit lines with a pale-blue dot grid #7ec8ea; black vending machine #131518 to the right; black mesh chair (#202022) foreground left.
- **Objects:** two Voltas floor-standing hot/cold dispensers ~0.32 W x 0.35 D x 0.95 H (body) + 19 L bottle with cover ~0.27 dia x 0.5 H (total ~1.45 m); blue trays 0.4 x 0.4 x 0.05; steel tumbler in the left unit; a double socket at y~1.1 above/between coolers; mural arrow pointing left ~2.7 m wide x 1.8 m high, bottom edge ~0.9 m up.
- **Text/brands:** "VOLTAS" on each cooler; "REFILL" QR-code stickers; red/yellow hot-water tap tags.

### 4.6 `08 (1)` PUSH vending machine + cooler
- **Camera:** ~(2.3,1.3,5.1) facing the machine ~1.8 m away, yaw +95, pitch 0. Portrait.
- **Lens:** phone main, portrait hfov ≈ 54°.
- **Light:** even bounce light, interior LED strip lit inside the machine (white-blue); no direct sun.
- **Materials/colours:** cabinet matte black #15171a; glass front ~0.8 x 1.2; green delivery flap #6dbf4a with black pull; wall off-white #eeeae0; skirting tiles #c9c1ae; floor #ddd9ce; screen on the right of the glass (#e8f0f5, 0.2 x 0.3).
- **Objects:** vending machine ~0.85 W x 0.8 D x 1.85 H; 6 shelves of bottles/cans; payment tablet on a bracket 1.35 m high, 0.16 x 0.25; lock plate at the left of the glass; black cable to the floor; cooler to its left (see 4.5), with blue tray; mural fragment at the upper left.
- **Text/brands:** "PUSH" in white serif capital on the black lower panel (above the flap); small shelf labels; "VOLTAS" on the cooler.

### 4.7 `08 (3)` Cafeteria + INNOVATION chevron wall
- **Camera:** ~(6.5,1.3,3.6), at the east end of the hall, looking west, yaw ~+80, pitch -3°. Wider shot (possibly ultra-wide mode).
- **Lens:** hfov ~78° [G; ceiling-tile lines converge strongly]; if it looks too wide use 69°.
- **Light:** daylight; sun patch on the far window side and floor right; bright but without harsh interior shadow; ceiling lights not lit (the tiles are evenly white).
- **Materials/colours:** walls white #f3f1ec; chevrons orange-red #e8602c (vinyl, two stacked chevrons, each ~1.6 W x 2.3 H, bottom ~0.95 m up); text black; door black-glass double leaf with steel pull bars (0.02 dia x 1.0 long), frame #1b1c1f; tables white laminate #f2f3f4 with thin steel legs; plastic chairs olive-green #8a9a35 and sky-blue #3a98dc; floor tile #e4e0d6 with reflections; window mullions black #15171a; vertical curtains/blinds dark at the window side.
- **Objects:** white tables ~1.5 W x 0.75 D x 0.75 H (arranged in rows, pushed together); ~16 chairs (0.45 x 0.45 seat 0.45 H, back 0.85 H) green and blue, shell chairs on steel legs; black mesh chair foreground left; ketchup bottle (red, 0.07 x 0.22) and steel salt shaker (0.05 x 0.1) on the foreground table; wooden table at the left edge; vending machine + coolers at the far left; 3-4 white ceiling fans (blade 1.2 m span); CCTV domes; wall AC/air-con unit; people seated (ignore).
- **Text/brands:** "INNOVATION" black sans on the left chevron (0.4 W x 0.05 H, y~1.8, ~0.2 m cap height).

### 4.8 `08 (2)` Window-side strip with fridge (same room)
- **Camera:** ~(2.0,1.4,1.2) at the strip start, looking east along the windows, yaw ~-88, pitch -4°.
- **Lens:** hfov ~75° [G, near ultra-wide look].
- **Light:** hard direct sun through the glass, giving oblique stripes on the floor between mullion shadows; bright blown highlights; ceiling not lit.
- **Materials/colours:** glass blue-grey #9fb4c4; window frames black #17181b with 0.12 m mullions; sill granite #26272b; cream tile floor #ebe5d6; fridge steel #b9bbbd; red/white/blue chevron mural (red #ea5a3a, blue #1e8bd5, white); pillar white #f3f1ec; bins stainless with printed fronts (red "NEC" bin front #d4252b; green "PLASTIC" front #2c8c5a).
- **Objects:** corridor ~2.5 m wide; ~9 window bays; two waste bins ~0.35 W x 0.35 D x 0.7 H in the foreground; fridge at the far end ~1.7 H; red water bottle on the sill; desk (wood #8b5a2b, 1.2 x 0.6 x 0.75) and mesh chairs at the right; black cabinet by the fridge.
- **Text/brands:** "PLASTIC" (white sans on green bin), partial "NEC"/"N.E.C" on the red bin; LG on the fridge.

## 5. Camera poses (for the Playwright harness)
Positions are in plan coordinates (section 1). Screenshot after any fix; keep aspect 4:3 (landscape) or 3:4 (portrait).

| name | x | y | z | yaw | pitch | hfov | aspect |
|---|---|---|---|---|---|---|---|
| coffee-06-1 | 6.7 | 1.40 | 3.6 | -85 | -5 | 69 | 4:3 |
| cabinets-07-1 | 6.9 | 1.50 | 2.8 | -88 | 12 | 69 | 4:3 |
| fridge-07-2 | 4.5 | 1.30 | 1.2 | -85 | -5 | 54 | 3:4 |
| sink-07 | 6.9 | 1.60 | 3.2 | -90 | -22 | 69 | 4:3 |
| coolers-08 | 2.2 | 1.20 | 5.4 | 90 | 0 | 54 | 3:4 |
| vending-08-1 | 2.3 | 1.30 | 5.1 | 95 | 0 | 54 | 3:4 |
| cafeteria-08-3 | 6.5 | 1.30 | 3.6 | 80 | -3 | 78 | 4:3 |
| strip-08-2 | 2.0 | 1.40 | 1.2 | -88 | -4 | 75 | 4:3 |
| video-start (f_01) | 2.0 | 1.4 | 1.2 | -88 | -4 | 69 | 16:9 |
| video-end (f_17) | 5.0 | 1.4 | 5.4 | 135 | -3 | 69 | 16:9 |

Notes: portrait hfov = 2*atan(tan(34.5°)*3/4) ≈ 54°. Chevron wall and the coolers are on the **west** wall (x=0). The coffee station camera is within the counter plan x 7.4-8 so keep ≥0.9 m from the counter.

## 6. Ceiling fixture observations
- Grid ceiling 600x600 mm tiles, white, T-bar #e8e8e6; ceiling height guess 3.0 m (tile count and door scale).
- 3-4 white ceiling fans, 3 blades, hung on ~0.3 m downrods, each ~1.2 m span, spaced ~2.5 m (seen in `08 (3)`, video f_09).
- CCTV domes (small white) on the wall/ceiling at the corners; wall AC split unit near the window wall.
- No lit panel lights are visible: the room is day-lit. Panel lights (600x600 LED) probably exist but off; model them as present-but-off, with an optional "on" state.
- Window-side blinds: dark vertical curtains partly drawn at the far end.

## 7. Gaps to invent
1. Exact room dimensions and the east/south wall details (never seen); counter relative position.
2. Back (south) wall; door positions other than the dark double door (z~3.2-4.4 west wall).
3. Table count/layout: I assumed rows; the real count unknown.
4. Counter underside: only white doors seen; the dishwasher/bins are invented.
5. Wall-mounted TV size and cabinet depth.
6. Mugs: any 10-14 coloured mugs; the exact bottle contents in the vending machine.
7. Light fixtures when switched on (type, intensity).
8. City view outside: simple low-poly buildings and a car park (visible: car park far below, towers, red billboard in the distance); window glass tint.
9. Exact sun azimuth (assume elevation ~38°, from the window side, slight +x shift).
10. People: none modelled.
