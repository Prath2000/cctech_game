// 200 randomised pick/drop/toss cycles on the debug cube (deterministic physics stepping): zero fall-throughs,
// then a real-time grab/toss run asserting no frame over 33 ms.
import { startServer, launch, openGame } from './lib';

const { server, url } = await startServer();
const browser = await launch(false);
let failed = false;
try {
  const { page } = await openGame(browser, url, 'webgl=1&debug=1', 1280, 720);
  page.on('console', (m) => m.text().startsWith('BAD') && console.log(m.text()));
  const res = await page.evaluate(() => {
    const g = (window as any).__game;
    const cube = g.scene.getObjectByName('debug_cube');
    const item = g.grab.items.find((i: any) => i.obj === cube);
    const pl = g.player;
    let bad = 0, minY = 9, lo = [9, 9], hi = [-9, -9];
    const bounds = (x: number, y: number, z: number) => y > 0.05 && x > -1 && x < 9.7 && z > -1 && z < 11; // hall 8.7 x 7.35 + bay to z 10 (blender/layout.py)
    for (let i = 0; i < 200; i++) {
      pl.teleport(2.2 + Math.random() * 1.2, 0, 4.0 + Math.random() * 2.0, Math.random() * 360);
      pl.pitch = -1.3 + Math.random() * 1.6; // the blockout is open-topped: no upward tosses over the walls
      pl.update(0.016);
      item.body.setTranslation({ x: pl.feet.x, y: 1.2, z: pl.feet.z }, true);
      g.stepPhysics(2);
      g.grab.pickItem(item);
      g.stepPhysics(20);
      if (i % 2) g.grab.toss(); else g.grab.drop();
      g.stepPhysics(240);
      const t = item.body.translation();
      minY = Math.min(minY, t.y);
      if (!bounds(t.x, t.y, t.z) || ![t.x, t.y, t.z].every(Number.isFinite)) { bad++; if (bad < 6) console.log("BAD", i, i % 2 ? "toss" : "drop", JSON.stringify({ t, f: pl.feet, yaw: pl.yaw, pitch: pl.pitch })); }
    }
    return { bad, minY, respawns: g.grab.respawns };
  });
  const p1 = res.bad === 0 && res.respawns === 0;
  if (!p1) failed = true;
  console.log(`${p1 ? 'PASS' : 'FAIL'} 200 drops/tosses: ${res.bad} fall-throughs/escapes, ${res.respawns} respawns, min y ${res.minY.toFixed(3)}`);

  // Real-time: the actual click path (aim -> pick -> carry -> toss -> pick -> drop) with frame times recorded.
  const maxFrame = await page.evaluate(async () => {
    const g = (window as any).__game;
    const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
    const pl = g.player;
    pl.enabled = true;
    pl.teleport(2.0, 0, 5.0, -90);
    await wait(500);
    const start = g.fpsSamples.length;
    for (let k = 0; k < 6; k++) {
      const cube = g.scene.getObjectByName('debug_cube');
      const p = cube.position;
      pl.teleport(p.x - 0.8, 0, p.z, -90);
      pl.pitch = Math.atan2(p.y - 1.6, 0.8);
      await wait(150);
      g.grab.pickTarget();
      pl.press('KeyW'); await wait(300); pl.press('KeyW', false);
      pl.look(0.5, 0.2); await wait(300);
      k % 2 ? g.grab.drop() : g.grab.toss();
      await wait(800);
    }
    return { max: Math.max(...g.fpsSamples.slice(start)), n: g.fpsSamples.length - start };
  });
  const p2 = maxFrame.max <= 33;
  if (!p2) failed = true;
  console.log(`${p2 ? 'PASS' : 'FAIL'} real-time grab: max frame ${maxFrame.max.toFixed(1)} ms over ${maxFrame.n} frames`);
} finally {
  await browser.close();
  await server.close();
}
process.exit(failed ? 1 : 0);
