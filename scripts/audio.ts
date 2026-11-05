// Audio check: triggers each Use item via window.__game and asserts the engine recorded the expected play() calls
// (counts are recorded even when the AudioContext is suspended, so no real listening is needed).
import { startServer, launch, openGame } from './lib';

const { server, url } = await startServer();
const browser = await launch(false);
let failed = false;
const check = (ok: boolean, msg: string) => { console.log(`${ok ? 'PASS' : 'FAIL'} ${msg}`); if (!ok) failed = true; };
try {
  const { page } = await openGame(browser, url, 'webgl=1', 1280, 720);
  await page.evaluate(() => (window as any).__game.audio.whenReady());
  await page.waitForTimeout(500);
  const r = await page.evaluate(async () => {
    const g = (window as any).__game;
    const a = g.audio, pl = g.player;
    const wait = (ms: number) => new Promise((res) => setTimeout(res, ms));
    const out: Record<string, number> = {};
    const kinds: Record<string, THREE.Object3D> = {};
    g.scene.traverse((o: any) => { const k = o.userData?.use_kind; if (k && !kinds[k]) kinds[k] = o; });
    const names = (n: string[]) => Object.fromEntries(n.map((k) => [k, a.count[k] ?? 0]));
    const base = { ...a.count };
    const delta = (k: string) => (a.count[k] ?? 0) - (base[k] ?? 0);
    const use = async (kind: string, ms: number, again = 0) => {
      const o: any = kinds[kind];
      if (!o) return false;
      pl.teleport(o.getWorldPosition(new (o.position.constructor)()).x - 1.2, 0, o.getWorldPosition(new (o.position.constructor)()).z, 0);
      g.pantry.use(o.name);
      await wait(ms);
      for (let i = 0; i < again; i++) { g.pantry.use(o.name); await wait(1200); }
      return true;
    };
    const found: Record<string, boolean> = {};
    found.fridge = await use('fridge_door', 900, 1);
    found.microwave_door = true;
    pl.teleport(0, 0, 0, 0);
    g.pantry.use('lg_microwave_door'); await wait(900); // open it, then start cooking (closes door, hum, beep after 10 s)
    found.mwdoor = await use('microwave', 1500);
    found.coffee = await use('coffee_machine', 5500);
    found.kettle = await use('kettle', 500, 1);
    found.sink = await use('sink', 300, 1);
    found.cabinet = await use('cabinet_door', 900, 1);
    found.vending = await use('vending', 1500);
    found.cooler = await use('cooler', 500);
    found.chair = await use('chair', 1000);
    if (g.seating.sitting) g.seating.stand();
    // microwave runs 10 s: wait for the beep
    await wait(10500);
    // footsteps: walk ~6 m
    let walked = 0;
    for (const yaw of [-90, 0, 90, 180]) { // try each heading in case something blocks one of them
      pl.teleport(1.0, 0, 3.3, yaw);
      const p0 = pl.feet.clone();
      pl.press('KeyW'); await wait(1500); pl.press('KeyW', false);
      walked += Math.hypot(pl.feet.x - p0.x, pl.feet.z - p0.z);
      if (walked > 4) break;
    }
    out.sit = g.seating.sitting ? 1 : 0; out.fps = g.fpsSamples.slice(-20).reduce((a: number, b: number) => a + b, 0) / 20;
    out.walked = walked;
    out.steps = Object.keys(a.count).filter((k) => k.startsWith('footstep')).reduce((s, k) => s + delta(k), 0);
    // set-down: drop a mug from height
    const it = g.grab.items.find((i: any) => i.obj.name.startsWith('mug'));
    if (it) { it.body.sleep(); it.body.setTranslation({ x: 3, y: 1.6, z: 3.3 }, true); it.body.setLinvel({ x: 0, y: 0, z: 0 }, true); it.body.wakeUp(); await wait(1800); }
    out.setdown = ['glass_set_down', 'mug_set_down_1', 'mug_set_down_2', 'mug_clink'].reduce((s, k) => s + delta(k), 0);
    // mute
    const lvl = a.masterLevel;
    a.setMuted(true); const muted = a.masterLevel; a.setMuted(false);
    window.dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyM' }));
    const viaKey = a.muted && a.masterLevel === 0;
    window.dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyM' }));
    const stored = localStorage.getItem('cctech.audio');
    const counts: Record<string, number> = {};
    for (const k of Object.keys(a.count)) counts[k] = delta(k);
    return { found, counts, out, lvl, muted, viaKey, unmuted: a.masterLevel, stored, ambience: ['office_room_tone', 'ac_hum', 'city_distant'].map((k) => a.count[k] ?? 0) };
  });
  console.log(JSON.stringify(r.counts));
  const need: [string, string[]][] = [
    ['fridge', ['fridge_door_open', 'fridge_door_close', 'fridge_hum']],
    ['microwave_door', ['microwave_hum', 'microwave_door_open', 'microwave_door_close', 'microwave_beep']],
    ['coffee', ['coffee_grind', 'coffee_pour', 'steam_hiss']],
    ['kettle', ['kettle_boil', 'kettle_click']],
    ['sink', ['sink_tap']],
    ['cabinet', ['cabinet_open', 'cabinet_close']],
    ['vending', ['vending_hum', 'vending_drop']],
    ['cooler', ['water_cooler_glug']],
    ['chair', ['chair_creak']],
  ];
  for (const [item, snds] of need) {
    check(!!r.found[item], `${item} item exists`);
    for (const s of snds) check((r.counts[s] ?? 0) > 0, `${item} -> ${s}`);
  }
  check(r.out.steps >= 4, `footsteps played while walking (${r.out.steps}, walked ${r.out.walked.toFixed(1)} m, sit ${r.out.sit}, frame ${r.out.fps.toFixed(0)} ms)`);
  check(r.out.setdown >= 1, `set-down clink on mug impact (${r.out.setdown})`);
  check(r.ambience.every((n) => n > 0), `ambience loops started (${r.ambience})`);
  check(r.muted === 0 && r.lvl > 0 && r.viaKey && r.unmuted > 0, `mute works (level ${r.lvl} -> ${r.muted}, M key ${r.viaKey})`);
  check(!!r.stored, 'settings persisted to localStorage');
} finally {
  await browser.close();
  await server.close();
}
process.exit(failed ? 1 : 0);
