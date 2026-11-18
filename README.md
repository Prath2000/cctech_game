# CCTech Office Game

> **🚧 Work in progress.** This is an unfinished side project. Things will change, some parts look rough, and help is very welcome.

A 3D copy of the CCTech 4th-floor pantry and seating area that you can walk around in, right in your web browser. The goal is for it to look and feel like the real place, so a colleague says "hey, that's our pantry!" within a minute.

There is no score and no mission. You just explore and play with things.

## What works today

- Walk around the pantry and seating area.
- Pick things up, carry them, drop them or throw them (mugs, bottles and so on).
- Flip the light switches.
- Get a snack from the vending machine and fill a glass at the water cooler.
- Sit on chairs.
- Point at things to see their name and a short note.
- Sounds, with a mute key.

## Still being worked on

- Making each corner match the real photos more closely (coffee machine, sink, cabinets, signs).
- Smoothness: walking is mostly a steady 60 frames per second, with a rare short hitch.
- Not yet tested properly in Safari.
- Only the pantry and seating area exist. Desks, meeting rooms and the rest of the floor come later.

The full to-do list lives in the `backlog/` folder.

## Controls

| Key | What it does |
|---|---|
| W A S D | Walk |
| Mouse | Look around (click the game first) |
| Shift | Walk faster |
| E | Use something (switch, vending machine, cooler, chair) |
| Left click | Pick up / drop |
| Right click or Q | Throw what you're holding |
| M | Sound on / off |
| Esc | Settings |

## Run it on your computer

You need [Node.js](https://nodejs.org) and [pnpm](https://pnpm.io).

```sh
pnpm install
pnpm dev
```

Then open http://localhost:5173 in Chrome.

- Chrome works best. Add `?webgl=1` to the address if the game won't start on an older computer.
- The small box in the top-left corner shows how smoothly it runs.

## Want to help?

You're welcome to join in, whether you code, make 3D models, take photos of the office, or just spot what looks wrong.

1. Have a look at the open tasks in `backlog/tasks/`.
2. Pick one, or suggest your own idea.
3. Work on your own branch and open a pull request (a request to add your changes).

**Office photos are especially useful.** Pictures of corners that aren't built yet, or close-ups of labels and signs, help the game look real.

## How it's put together (for developers)

- `src/`: the game itself (TypeScript, Three.js for 3D, Rapier for physics).
- `blender/`: scripts that build the 3D models and work out the lighting in Blender.
- `public/`: the finished models, lighting, textures and sounds the game loads.
- `references/`: real office photos and video used to match the look.
- `scripts/`: automatic checks (screenshots next to the real photos, smoothness tests, walking tests).
- `docs/`: notes, decisions and research.

Handy check commands:

```sh
pnpm typecheck          # check the code for mistakes
pnpm check:match        # game screenshots next to the real photos
pnpm check:walk         # walls and furniture block you correctly
pnpm check:fps --headed # how smoothly it runs
```
