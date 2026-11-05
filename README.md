# cctech_game

Vite + TypeScript + Three.js (WebGPURenderer, auto WebGL2 fallback) + Rapier.

```sh
pnpm install
pnpm dev         # http://localhost:5173
pnpm build
pnpm typecheck
```

- `?webgl=1` forces the WebGL2 backend.
- The top-left overlay shows median fps, frame time and the active backend.

## Checks

- Camera poses live in `src/data/camera-poses.json` (position m, yaw/pitch deg, horizontal fov deg). `?pose=<name>` pins the camera.
- `pnpm check:shot <pose> [--webgl] [--headed] [--size 1600x1200] [--out path]` saves a PNG (default `.team/work/shots/<pose>-<backend>.png`).
- `pnpm check:fps [--webgl] [--headed] [--seconds 10] [--pose overview]` prints median fps, 1% low fps, max frame ms and backend.
- Headless fps is not representative of a real Mac; use `--headed` for real numbers.
- Page hooks: `window.__game` has `ready`, `backend`, `setPose(name)`, `fpsSamples`.
