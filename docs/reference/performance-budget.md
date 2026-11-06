# Performance budget (Safari not measured)

Measured on the user's Mac, production build, Chrome only. Update when the model or lightmaps change.
Re-measure with `pnpm run check:budget --url http://localhost:4173 [--mbps N]` and `scripts/fps.ts --url ... --headed --no-pose [--walk] [--webgl]`, against a running `vite preview`.

## Targets
- Frame rate: median 60 fps, no stutter, Safari and Chrome, both backends.
- Load: under about 10 s.

## Frame rate (Chrome, headed, player view, 1280x720, 15 s)
| Run | Median fps | 1% low | Max frame | Notes |
|---|---|---|---|---|
| WebGPU, standing | 59.9 | 53.5 | 18.7 ms | current lightmaps |
| WebGPU, walking (32 m) | 59.9 | 53.5 | 18.7 ms | current lightmaps |
| WebGL, walking (32 m) | 59.9 | 53.6 | 18.7 ms | current lightmaps |
| WebGL, standing | 59.9 | 56.6 | 17.8 ms | one run, before the WebP change |
| WebGPU, standing, 4 earlier runs | 59.9 | 56.5 in three, 29.4 in one | 17.8 ms in three, 100 ms in one | before the WebP change |

- The one 100 ms frame is unexplained and did not repeat in 3 further runs. Treat "no stutter" as likely, not proven.
- The light-switch fade stays at 16.8 ms worst frame (`check:switch`).
- Safari, either backend: not measured (needs "Allow remote automation" or a reading from the user).

## Load (cold, nothing cached, Chrome, throttled)
| Network | Time | Over the wire |
|---|---|---|
| 50 Mbps | 4.9 s | 20.7 MB |
| 20 Mbps | 10.0 s | 20.8 MB |

- Before lightmaps moved to lossless WebP: 6.6 s and 14.0 s, 30.7 MB. Pixels are identical, so the look did not change.
- Below 20 Mbps the target is missed. The next saving would be lossy lightmaps or KTX2; both change pixels, so they would need a new photo-match check.
- The bake now needs `cwebp` (`brew install webp`) and stops at once if it is missing.

## Download size
| Asset | Size |
|---|---|
| `public/lightmaps` | 11 MB of maps used by the game (20.5 MB as PNG), plus `sky.exr` and two `lighting.json` |
| `public/models` | 10 MB (`room.glb` 7.0 MB) |
| `public/audio` | 2.3 MB |

## Draw calls and triangles per pose (WebGPU, 1280x720)
Measured on model 5bddb05, unchanged since.

| Pose | Draw calls | Triangles |
|---|---|---|
| overview | 198 | 29139 |
| spike | 120 | 15881 |
| coffee-06-1 | 310 | 67781 |
| cabinets-07-1 | 247 | 51553 |
| fridge-07-2 | 77 | 6205 |
| sink-07 | 157 | 36069 |
| coolers-08 | 195 | 42391 |
| vending-08-1 | 200 | 42463 |
| cafeteria-08-3 | 297 | 58327 |
| strip-08-2 | 133 | 16621 |
| video-start | 119 | 15313 |
| video-end | 178 | 30327 |
| tata-close | 240 | 50047 |

## Not done
- Low graphics setting: deferred by the user for the first pass.
- The production build also carries 61 MB of unused test files (`dist/spike`); the game does not download them. See TASK-1.33.
