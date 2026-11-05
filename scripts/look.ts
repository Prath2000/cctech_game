// Aims at the ?debug=1 panel/box/cube and asserts the prompt shows name + caption + level.
import { startServer, launch, openGame } from './lib';

const { server, url } = await startServer();
const browser = await launch(false);
let failed = false;
try {
  const { page } = await openGame(browser, url, 'webgl=1&debug=1', 1280, 720);
  const cases: [string, number, number, number, number, string[]][] = [
    ['panel', 1.0, 3.0, -90, -0.38, ['Look', 'Test Panel', 'Just look at it.']],
    ['cube', 1.0, 3.8, -90, -0.5, ['Grab', 'Test Cube']],
    ['box', 1.4, 4.6, -90, -0.5, ['Use [E]', 'Test Box']],
  ];
  for (const [name, x, z, yaw, pitch, want] of cases) {
    const text = await page.evaluate(async ([x, z, yaw, pitch, nm]) => {
      const pl = (window as any).__game.player;
      const g = (window as any).__game;
      pl.teleport(x, 0, z, yaw);
      const o = g.scene.getObjectByName(nm);
      if (o) {
        const p = o.getWorldPosition(new o.position.constructor());
        pl.yaw = Math.atan2(-(p.x - x), -(p.z - z));
        pl.pitch = Math.atan2(p.y - 1.6, Math.hypot(p.x - x, p.z - z));
      } else pl.pitch = pitch;
      await new Promise((r) => setTimeout(r, 400));
      return document.getElementById('hud-prompt')!.textContent;
    }, [x, z, yaw, pitch, 'debug_' + name] as const);
    const pass = want.every((w) => text.includes(w));
    if (!pass) failed = true;
    console.log(`${pass ? 'PASS' : 'FAIL'} ${name}: ${JSON.stringify(text)}`);
  }
  if (process.env.SHOT) await page.screenshot({ path: process.env.SHOT });
} finally {
  await browser.close();
  await server.close();
}
process.exit(failed ? 1 : 0);
