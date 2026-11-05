// TASK-1.13 check: toggles the light switch and measures fade duration + frame-time hitches around it.
import { parseArgs, startServer, launch, openGame } from './lib';

const { flags, opts } = parseArgs(process.argv.slice(2));
const pose = opts.pose ?? 'overview';
const { server, url } = await startServer();
const browser = await launch(flags.has('headed'));
try {
  const q = `pose=${encodeURIComponent(pose)}${flags.has('webgl') ? '&webgl=1' : ''}`;
  const { page, backend } = await openGame(browser, url, q, 1280, 720, opts.page ?? '');
  await page.waitForTimeout(3000);
  const r: any = await page.evaluate(`new Promise((res) => {
    const g = window.__game, sw = g.lightSwitch, u = g.baked.uLights;
    const frames = [];   // { t, dt, phase }
    let phase = 'idle', last = performance.now(), t0 = 0, fadeMs = {};
    const trace = [];
    const wait = (ms) => new Promise((r) => setTimeout(r, ms));
    const f = (t) => { frames.push({ dt: t - last, phase }); last = t; if (phase.startsWith('fade') && fadeMs[phase] === undefined && Math.abs(u.value - sw.target) < 1e-4) fadeMs[phase] = t - t0; requestAnimationFrame(f); };
    requestAnimationFrame(f);
    (async () => {
      await wait(1500);
      for (const [name, on] of [['fade-on', true], ['fade-off', false], ['fade-on2', true]]) {
        phase = 'before-' + name; await wait(1000);
        phase = name; t0 = performance.now(); sw.toggle(on); await wait(900);
        phase = 'after-' + name; await wait(1500);   // includes the post-fade reflection recapture
      }
      phase = 'done'; res({ frames, fadeMs, final: u.value });
    })();
  })`);
  const stat = (p: string) => {
    const d = r.frames.filter((f: any) => f.phase === p).map((f: any) => f.dt as number).sort((a: number, b: number) => a - b);
    return { n: d.length, median: d[Math.floor(d.length / 2)] ?? 0, max: d[d.length - 1] ?? 0 };
  };
  console.log(`backend: ${backend}  hasOn: ${await page.evaluate('window.__game.baked.hasOn')}  final uLights: ${r.final.toFixed(3)}`);
  let worst = 0;
  for (const n of ['fade-on', 'fade-off', 'fade-on2']) {
    const b = stat('before-' + n), f = stat(n), a = stat('after-' + n);
    worst = Math.max(worst, f.max, a.max);
    console.log(`${n}: fade ${r.fadeMs[n]?.toFixed(0)} ms | frame ms median/max  before ${b.median.toFixed(1)}/${b.max.toFixed(1)}  during ${f.median.toFixed(1)}/${f.max.toFixed(1)}  after(+recapture) ${a.median.toFixed(1)}/${a.max.toFixed(1)}`);
  }
  const base = stat('before-fade-on');
  const ok = worst < Math.max(60, base.max * 2.5) && Object.values(r.fadeMs).every((v: any) => v > 400 && v < 700);
  console.log(`worst frame near toggle: ${worst.toFixed(1)} ms  => ${ok ? 'PASS' : 'FAIL'}`);
  if (!ok) process.exitCode = 1;
} finally {
  await browser.close();
  await server.close();
}
