# Performance budget (draft: Safari not measured)

Measured on the user's Mac, production build, as of commit 119434b. Update when the model or lightmaps change.

## Targets
- Frame rate: median 60 fps, no stutter, Safari and Chrome, both backends.
- Load: under about 10 s.

## Measured
| Item | Result | Status |
|---|---|---|
| Chrome, standing still, 25 s, 1280x720 and 1920x1080, both backends | median 59.9 fps, 1% low 53.7, max frame 18.7-18.8 ms | meets target when still |
| Automatic resolution drop during those runs | never triggered | |
| Chrome, walking | not measured | open |
| Safari, either backend | not measured (needs "Allow remote automation" or a reading from the user) | open |
| Load, localhost | 2.1-3.9 s, one cold outlier 9.1 s | no network delay, so not a real-network figure |

## Download size
| Asset | Size |
|---|---|
| `public/lightmaps` | 33 MB |
| `public/models` | 9.6 MB (`room.glb` 6.8 MB) |
| `public/audio` | 2.3 MB |

## Not measured
- Draw calls and triangle counts: no script reports them yet.
- The production build also carries 61 MB of unused test files (`dist/spike`); the game does not download them. See TASK-1.33.
