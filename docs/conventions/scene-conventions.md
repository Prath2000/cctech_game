# Scene conventions (shared by all builders)

- Units metres, Blender Z-up → glTF +Y up. Room axes per docs/reference/pantry-reference-sheet.md §1.
- Raw downloads (textures, HDRIs, models) go to `assets/raw/<source>/<id>/` — gitignored. Fetch scripts are committed and idempotent (skip if present).
- Licences: every third-party asset listed in `docs/licenses.md` (source, id, licence, URL). Each builder appends its own section.
- Blender build is modular. `blender/build_room.py` is the orchestrator: blockout → materials → props → export `public/models/room.glb`. Modules expose `build(context)`:
  - `blender/build_blockout.py` (shell, exists)
  - `blender/materials.py` (TASK-1.6)
  - `blender/props/pantry.py`, `blender/props/seating.py` (TASK-1.7)
  The orchestrator imports props modules only if present. Each props module also has a standalone runner exporting `public/models/props_<name>.glb` for review.
- Every object gets a unique, meaningful name. Custom properties (exported as glTF extras → three `userData`):
  - `static`: 1 = baked into lightmap, never moves; 0 = movable.
  - `interact`: `look` | `use` | `grab` (absent = not interactive; every modelled prop should at least be `look`).
  - `caption_id`: key into `src/data/captions.json` (defaults to object name).
  - `use_kind`: for `use` items, e.g. `coffee_machine`, `microwave`, `fridge_door`, `kettle`, `sink`, `cabinet_door`, `vending`, `cooler`, `chair`, `light_switch`.
  - `collider`: `box` (default) | `none` | `convex`; movable `grab` items get dynamic rigid bodies in the game.
  - `mass` (kg) for grab items.
- Static meshes need UV map `lightmap` (2nd UV). Movable meshes don't.
- Hinged parts (doors) are separate objects parented to the body, with the pivot at the hinge and custom prop `hinge_axis` (`x|y|z`) and `hinge_max_deg`.
- Instancing: repeated items (mugs, chairs) share one mesh datablock so they export as instances.
- Respect rule: the Ganesha idol (reception, not in POC 1) is look-only.

## Layout source
- All room dimensions and anchors (room size, windows, pillar, door, counter, fridge, coolers, vending, seating grid, spawn) live in `blender/layout.py`. Do not hardcode them; import it.
- Example, works under `blender -b -P blender/...` (also from `blender/props/`):
```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))        # file in blender/
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # file in blender/props/
import layout
x0 = layout.COUNTER["x0"]; tables = layout.table_positions()
```
- TS side: the spawn and `scripts/walk.ts` cases use numbers copied from `layout.py`; update them when layout changes.
