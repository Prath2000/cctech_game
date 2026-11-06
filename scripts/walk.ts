// Drives the first-person controller into walls/counter/glass/table and asserts it never passes.
import { startServer, launch, openGame } from './lib';

const { server, url } = await startServer();
const browser = await launch(false);
let failed = false;
try {
  const { page } = await openGame(browser, url, 'webgl=1', 1280, 720);
  // [name, start x, z, yaw deg, max allowed coordinate check]
  const cases: [string, number, number, number, (p: { x: number; z: number }) => boolean][] = [
    ['west wall (sprint)', 2.0, 4.0, 90, (p) => p.x >= 0.29],
    ['south wall (partition)', 2.2, 5.0, 180, (p) => p.z <= 7.35 - 0.29],
    ['window glass', 3.0, 1.0, 0, (p) => p.z >= 0.29],
    ['east wall', 5.0, 5.0, -90, (p) => p.x <= 8.7 - 0.29],
    ['table', 3.0, 2.0, 90, (p) => p.x >= 1.5 + 0.29],
    ['pillar', 6.45, 5.5, 0, (p) => p.z >= 4.15 + 0.29],
  ];
  for (const [name, x, z, yaw, ok] of cases) {
    const p = await page.evaluate(
      ([x, z, yaw]) => new Promise<{ x: number; y: number; z: number }>((res) => {
        const pl = (window as any).__game.player;
        pl.enabled = true;
        pl.teleport(x, 0, z, yaw);
        pl.press('KeyW'); pl.press('ShiftLeft');
        setTimeout(() => {
          pl.press('KeyW', false); pl.press('ShiftLeft', false);
          res({ x: pl.feet.x, y: pl.feet.y, z: pl.feet.z });
        }, 2500);
      }),
      [x, z, yaw] as const,
    );
    // enabled is reset by the loop only when a pose is set; none here.
    const pass = ok(p) && Math.abs(p.y) < 0.05;
    if (!pass) failed = true;
    console.log(`${pass ? 'PASS' : 'FAIL'} ${name}: x=${p.x.toFixed(2)} y=${p.y.toFixed(2)} z=${p.z.toFixed(2)}`);
  }
  // walking moves freely in open space
  const moved = await page.evaluate(() => new Promise<number>((res) => {
    const pl = (window as any).__game.player;
    pl.teleport(3.0, 0, 5.0, -90);
    pl.press('KeyW');
    setTimeout(() => { pl.press('KeyW', false); res(pl.feet.x - 3.0); }, 500);
  }));
  const free = moved > 0.5;
  if (!free) failed = true;
  console.log(`${free ? 'PASS' : 'FAIL'} free walk: moved ${moved.toFixed(2)} m in 0.5 s`);
} finally {
  await browser.close();
  await server.close();
}
process.exit(failed ? 1 : 0);
