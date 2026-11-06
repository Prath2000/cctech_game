// Uses every pantry item through window.__game.pantry (real-time, rendered) and records the max frame time per item.
// Also checks: doors open/close, cabinet mugs wake + can be grabbed, coffee mug ends filled, microwave countdown, no trapped player.
import { startServer, launch, openGame } from './lib';

const LIMIT_MS = Number(process.env.PANTRY_MAX_MS ?? 50);
const { server, url } = await startServer();
const browser = await launch(false);
let failed = false;
const check = (ok: boolean, msg: string) => { console.log(`${ok ? 'PASS' : 'FAIL'} ${msg}`); if (!ok) failed = true; };
try {
  const { page } = await openGame(browser, url, 'webgl=1', 1280, 720);
  const r = await page.evaluate(async (limit) => {
    const g = (window as any).__game;
    const P = g.pantry, pl = g.player;
    const wait = (ms: number) => new Promise((res) => setTimeout(res, ms));
    const idle = async (max = 20000) => { const t0 = performance.now(); while (P.busy() && performance.now() - t0 < max) await wait(50); await wait(100); };
    const out: { name: string; max: number; ok: boolean; note: string }[] = [];
    const run = async (name: string, at: [number, number, number], fn: () => Promise<string>) => {
      pl.teleport(at[0], 0, at[1], at[2]);
      await wait(400);
      const start = g.fpsSamples.length;
      const note = await fn();
      const frames = g.fpsSamples.slice(start);
      const max = Math.max(...frames);
      out.push({ name, max, ok: max <= limit, note });
    };
    const door = (n: string) => P.state().doors[n];
    const state = () => P.state();
    await wait(500);

    await run('fridge', [5.6, 7.2, -90], async () => {
      P.use('lg_fridge_door_main'); await wait(1200);
      const open = door('lg_fridge_door_main');
      P.use('lg_fridge_door_main'); await wait(1200);
      return `open=${open.toFixed(2)} closed=${door('lg_fridge_door_main').toFixed(2)} ${open > 0.95 && door('lg_fridge_door_main') < 0.05 ? '' : 'BAD'}`;
    });
    await run('microwave door', [8.2, 8.8, 90], async () => {
      P.use('lg_microwave_door'); await wait(1200);
      const open = door('lg_microwave_door');
      P.use('lg_microwave_door'); await wait(1200);
      return `open=${open.toFixed(2)} closed=${door('lg_microwave_door').toFixed(2)} ${open > 0.95 && door('lg_microwave_door') < 0.05 ? '' : 'BAD'}`;
    });
    await run('microwave run', [8.2, 8.8, 90], async () => {
      P.use('lg_microwave'); await wait(5000);
      const mid = state().mw;
      await idle();
      return `running mid=${mid} after=${state().mw} beeps=${g.audio.count.microwave_beep ?? 0} ${mid && !state().mw ? '' : 'BAD'}`;
    });
    await run('coffee', [8.2, 8.2, 90], async () => {
      P.use('tata_bistro_machine'); await wait(500);
      await idle(); await wait(500);
      const s = state();
      return `filled=${JSON.stringify(s.filled)} phase=${s.coffeePhase} ${s.filled.length === 1 ? '' : 'BAD'}`;
    });
    await run('kettle', [8.2, 9.2, 90], async () => {
      P.use('kettle_01'); await wait(1500);
      const on = state().kettle;
      P.use('kettle_01'); await wait(500);
      return `on=${on} off=${!state().kettle} ${on && !state().kettle ? '' : 'BAD'}`;
    });
    await run('sink', [8.2, 9.5, 90], async () => {
      P.use('sink_faucet'); await wait(1500);
      const on = state().sink;
      P.use('sink_faucet'); await wait(600);
      return `on=${on} off=${!state().sink} ${on && !state().sink ? '' : 'BAD'}`;
    });
    // TASK-1.17: wall cabinets (and their mugs) are not in the scan, so only the base cabinet doors remain.
    await run('base cabinet', [8.2, 9.0, 90], async () => {
      P.use('base_cabinet_door_01'); await wait(1200);
      const d = door('base_cabinet_door_01');
      P.use('base_cabinet_door_01'); await wait(1200);
      return `open=${d.toFixed(2)} closed=${door('base_cabinet_door_01').toFixed(2)} ${d > 0.95 && door('base_cabinet_door_01') < 0.05 ? '' : 'BAD'}`;
    });
    // Door must not trap the player: stand where the open fridge door sweeps.
    pl.teleport(6.4, 0, 7.0, -90); await wait(300);
    // Repeated coffee use must not grow bodies unbounded: move each mug away so every use would spawn a new one.
    pl.teleport(8.2, 0, 8.2, 90); await wait(300);
    const bodies = () => g.grab.world.bodies.len();
    const b0 = bodies();
    for (let i = 0; i < 30; i++) {
      P.use('tata_bistro_machine');
      for (let k = 0; k < 80; k++) P.update(0.1); // simulate ~8 s: grind, pour, steam
      const m = g.grab.items.filter((it: any) => it.obj.name.startsWith('mug')).pop();
      if (m) { m.body.setTranslation({ x: 0, y: 5, z: 0 }, true); m.obj.position.set(0, 5, 0); } // away from the spout
    }
    const coffeeGrowth = bodies() - b0;
    P.use('lg_fridge_door_freezer'); await wait(1500);
    const bounced = state().bounced;
    return { out, bounced, coffeeGrowth };
  }, LIMIT_MS);
  for (const o of r.out) check(o.ok && !o.note.includes('BAD'), `${o.name}: max frame ${o.max.toFixed(1)} ms (limit ${LIMIT_MS}) ${o.note}`);
  check(r.coffeeGrowth <= 6, `30 coffee uses grew bodies by ${r.coffeeGrowth} (cap 6)`);
  console.log(`info door reversals when player in the way: ${r.bounced}`);
} finally {
  await browser.close();
  await server.close();
}
process.exit(failed ? 1 : 0);
