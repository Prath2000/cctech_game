// Seating checks via window.__game: (1) sit/stand on a chair (+ push-to-roll), (2) vending drops a grabbable snack,
// (3) a cooler fills a glass that can be carried; plus a frame-time guard while all of that runs.
import { startServer, launch, openGame } from './lib';

const { server, url } = await startServer();
const browser = await launch(false);
let failed = false;
const report = (ok: boolean, msg: string) => { if (!ok) failed = true; console.log(`${ok ? 'PASS' : 'FAIL'} ${msg}`); };
try {
  const { page } = await openGame(browser, url, 'webgl=1', 1280, 720);
  await page.waitForTimeout(500);

  // AC1: chairs
  const c1 = await page.evaluate(async () => {
    const g = (window as any).__game;
    const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
    const s = g.seating, pl = g.player;
    const ch = s.chairs[0];
    const o = ch.obj;
    // Stand behind the chair (away from its facing) and look at it.
    const f = s.forwardOf(o, pl.feet.clone());
    const fl = Math.hypot(f.x, f.z); f.x /= fl; f.z /= fl;
    pl.teleport(o.position.x - f.x * 1.6, 0, o.position.z - f.z * 1.6, 0);
    pl.yaw = Math.atan2(f.x, f.z);
    const out: any = {};
    s.sit(o);
    await wait(700);
    out.sitting = !!s.sitting;
    out.eye = g.camera.position.y;
    s.look(5, 0); // way past the limit
    await wait(50);
    out.yawOff = s.yaw - s.baseYaw;
    s.look(-12, 5);
    out.yawOff2 = s.yaw - s.baseYaw;
    out.pitch = s.pitch;
    await wait(50);
    out.stood = s.stand();
    out.sittingAfter = !!s.sitting;
    const d = Math.hypot(pl.feet.x - o.position.x, pl.feet.z - o.position.z);
    out.dist = d;
    out.clear = s.isClear(pl.feet.x, pl.feet.z);
    // Push: walk into another chair.
    const c2 = s.chairs[1].obj;
    const p0 = { x: c2.position.x, z: c2.position.z };
    pl.teleport(p0.x - 0.9, 0, p0.z, -90);
    pl.press('KeyW');
    await wait(900);
    pl.press('KeyW', false);
    await wait(400);
    out.pushed = Math.hypot(c2.position.x - p0.x, c2.position.z - p0.z);
    return out;
  });
  report(c1.eye > 1.0 && c1.eye < 1.3, `seated eye height ${c1.eye?.toFixed(2)}`);
  report(c1.sitting && c1.stood && !c1.sittingAfter, `sit then stand (sitting=${c1.sitting}, stood=${c1.stood})`);
  report(Math.abs(c1.yawOff) <= 1.75 && Math.abs(c1.yawOff2) <= 1.75 && c1.pitch <= 0.81, `mouse-look limited (yaw off ${c1.yawOff.toFixed(2)}/${c1.yawOff2.toFixed(2)}, pitch ${c1.pitch.toFixed(2)})`);
  report(c1.clear && c1.dist > 0.5, `stood up in free space (dist ${c1.dist.toFixed(2)}, clear=${c1.clear})`);
  report(c1.pushed > 0.15, `walking into a chair rolls it (${c1.pushed.toFixed(2)} m)`);

  // AC2: vending
  const v = await page.evaluate(async () => {
    const g = (window as any).__game;
    const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
    const m = g.scene.getObjectByName('vending_machine');
    const pl = g.player;
    pl.teleport(m.position.x + 1.4, 0, m.position.z, 90);
    const n0 = g.grab.items.length;
    const hum0 = g.audio.count.vending_hum ?? 0;
    g.seating.useVending(m);
    await wait(2600);
    const it = g.grab.items[g.grab.items.length - 1];
    const t = it.body.translation();
    const out: any = { added: g.grab.items.length - n0, name: it.obj.name, y: t.y, x: t.x, hum: (g.audio.count.vending_hum ?? 0) - hum0, drop: g.audio.count.vending_drop ?? 0 };
    pl.teleport(t.x + 0.9, 0, t.z, 90);
    pl.pitch = -0.5;
    await wait(200);
    out.picked = g.grab.pickItem(it) && g.grab.held === it;
    g.grab.drop();
    return out;
  });
  report(v.added === 1 && v.y > -0.05 && v.y < 0.4 && v.x > 0.3 && v.picked, `vending drops a grabbable snack (${v.name} at x=${v.x.toFixed(2)} y=${v.y.toFixed(2)}, picked=${v.picked})`);
  report(v.hum >= 1 && v.drop >= 1, `vending sounds triggered (motor ${v.hum}, drop ${v.drop})`);

  // AC3: cooler
  const w = await page.evaluate(async () => {
    const g = (window as any).__game;
    const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
    const c = g.scene.getObjectByName('cooler_01');
    const pl = g.player;
    pl.teleport(c.position.x + 1.0, 0, c.position.z, 90);
    g.grab.drop();
    const glug0 = g.audio.count.water_cooler_glug ?? 0;
    g.seating.useCooler(c);
    await wait(500);
    const mid = g.grab.items[g.grab.items.length - 1].obj;
    const midLevel = mid.userData.water_level;
    await wait(2800);
    const it = g.grab.items[g.grab.items.length - 1];
    const water = it.obj.children.find((x: any) => x.name === 'water');
    const out: any = { level: it.obj.userData.water_level, midLevel, scale: water?.scale.y, held: g.grab.held === it, glug: (g.audio.count.water_cooler_glug ?? 0) - glug0 };
    // carry it away
    pl.press('KeyS'); await wait(1700); pl.press('KeyS', false);
    await wait(300);
    const cam = g.player.feet;
    out.carryDist = Math.hypot(it.obj.position.x - cam.x, it.obj.position.z - cam.z);
    out.farFromCooler = Math.hypot(it.obj.position.x - c.position.x, it.obj.position.z - c.position.z);
    out.waterVisible = water?.visible;
    // Empty glass held + E near the cooler
    g.grab.drop();
    const glass = g.scene.getObjectByName('glass_05');
    const gi = g.grab.items.find((i: any) => i.obj === glass);
    pl.teleport(c.position.x + 1.0, 0, c.position.z, 90);
    pl.pitch = 0;
    pl.update(0.016);
    g.grab.pickItem(gi);
    out.heldFill = g.seating.fillHeld();
    await wait(2800);
    out.heldLevel = glass.userData.water_level;
    return out;
  });
  report(w.level === 1 && w.scale > 0.05 && w.midLevel > 0 && w.midLevel < 1, `cooler fills spawned glass (mid ${w.midLevel?.toFixed(2)}, final ${w.level}, scale ${w.scale?.toFixed(3)}, glug ${w.glug})`);
  report(w.held && w.carryDist < 1.6 && w.farFromCooler > 2.5 && w.waterVisible, `filled glass carried (${w.carryDist.toFixed(2)} m from player, ${w.farFromCooler.toFixed(1)} m from cooler)`);
  report(w.heldFill && w.heldLevel === 1, `E with held glass fills it (level ${w.heldLevel})`);

  // Frame times during a vend + fill + sit cycle
  const maxFrame = await page.evaluate(async () => {
    const g = (window as any).__game;
    const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
    const start = g.fpsSamples.length;
    const m = g.scene.getObjectByName('vending_machine');
    g.player.teleport(m.position.x + 1.4, 0, m.position.z, 90);
    g.seating.useVending(m);
    await wait(2500);
    g.seating.sit(g.seating.chairs[2].obj);
    await wait(1000);
    g.seating.stand();
    await wait(500);
    return Math.max(...g.fpsSamples.slice(start + 5));
  });
  report(maxFrame <= 50, `max frame ${maxFrame.toFixed(1)} ms during vend/sit (headless, includes one-off body creation)`);
} finally {
  await browser.close();
  await server.close();
}
process.exit(failed ? 1 : 0);
