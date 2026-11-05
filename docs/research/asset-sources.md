# Asset sources (research, 2026-11-05)

Prefer scripted downloads: Poly Haven (`https://api.polyhaven.com/files/<id>`) and ambientCG (`https://ambientcg.com/get?file=<Id>_2K-JPG.zip`), both CC0.

## Textures
- Floor tile / laminate (Poly Haven): `floor_tiles_06`, `large_grey_tiles`, `interior_tiles`, `laminate_floor_02`
- Wall plaster (Poly Haven): `plastered_wall_04`, `white_plaster_02`
- Granite (ambientCG): `Granite003A`, `Granite005A` — no true black granite; darken in Blender
- Brushed steel (ambientCG): `Metal009`, `Metal011`, `Metal012`; aluminium frames: `Metal050A`
- Ceiling (ambientCG): `OfficeCeiling001`–`OfficeCeiling006`
- Plastic (ambientCG): `Plastic013A`, `Plastic010` — also basis for white gloss laminate (roughness tweak); frosted glass = procedural transmission + roughness

## Models
- Poly Haven CC0: `plastic_monobloc_chair_01`, `plastic_thermos`, `metal_jug`, `jug_01`, `vintage_microwave`, `vintage_electric_kettle`, `modern_ceiling_lamp_01`
- Kenney Furniture Kit (CC0) — likely kitchen items; list unconfirmed
- Sketchfab CC-BY fallback (attribution required, API token for download): water dispenser `457cd4e5…`, vending machine `d62a741a…`, kettle `11cbe604…`, microwave `5af99db1…`, plastic chair `be3d5131…`, sink `504248ed…`, thermos `db12f86e…`, snack pack `213071ad…` (ids truncated in research; re-search by name)
- No CC0 found: single-door fridge, water cooler, LED panel, Tata Bistro machine → model procedurally in Blender from product dimensions + photo decals.

## HDRIs
- Sky: `kloofendal_48d_partly_cloudy_puresky`, `qwantani_noon_puresky` (Poly Haven)
- Interior: `newman_cafeteria`, `small_empty_room_2`
- No Indian-city HDRI found; window city view = photo-based backdrop from video frames, or generic.

## Product dimensions (W x H x D)
- LG 185 L single-door fridge: 534 x 1172 x 650 mm
- LG MS2043DB 20 L microwave: 455 x 252 x 320 mm
- Tata MyBistro (closest: "Dr. Coffee M12", 10" touchscreen): no published dims; use ~330 x 530 x 710 mm (W x D x H guess)

## Not yet researched
- CC0 sounds (freesound.org CC0, Pixabay) — do in TASK-1.16.
