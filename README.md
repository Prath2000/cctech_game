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
