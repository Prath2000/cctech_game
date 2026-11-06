import { parseArgs, startServer, launch, openGame } from './lib';

const { flags, opts } = parseArgs(process.argv.slice(2));
const seconds = Number(opts.seconds ?? 10);
const pose = opts.pose ?? 'overview';
const headed = flags.has('headed');
if (!headed) console.warn('WARNING: headless run; fps is not representative of a real Mac GPU/display. Use --headed.');
// --url http://...: measure a server that is already running (a production preview) instead of the dev server.
const dev = opts.url ? null : await startServer();
const url = opts.url ?? dev!.url;
const browser = await launch(headed);
try {
  // --no-pose: the real player view, with auto resolution active (a pose switches it off).
  const q = `${flags.has('no-pose') ? '' : `pose=${encodeURIComponent(pose)}`}${flags.has('webgl') ? '&webgl=1' : ''}`;
  const started = Date.now();
  const { page, backend } = await openGame(browser, url, q, Number(opts.width ?? 1280), Number(opts.height ?? 720), opts.page ?? '');
  console.log(`load ms (page open to game ready): ${Date.now() - started}`);
  page.on('console', (m) => { if (m.text().startsWith('[autores]')) console.log(m.text()); });
  await page.waitForTimeout(2000); // warm-up
  // --walk: the player walks back and forth (and turns) while frames are sampled. Needs --no-pose.
  // --turn N: radians per 50 ms (default 0.01). --delay N: extra seconds before the walk starts.
  if (opts.delay) await page.waitForTimeout(Number(opts.delay) * 1000);
  if (flags.has('walk')) await page.evaluate((turn) => {
    const g = (window as any).__game, pl = g.player;
    let key = 'KeyW', dist = 0, prev = pl.feet.clone();
    pl.press(key);
    setInterval(() => { pl.press(key, false); key = key === 'KeyW' ? 'KeyS' : 'KeyW'; pl.press(key); }, 2000);
    setInterval(() => { dist += pl.feet.distanceTo(prev); prev.copy(pl.feet); (window as any).__walked = dist; pl.yaw += turn; }, 50);
  }, Number(opts.turn ?? 0.01));
  // Also note every frame over 25 ms: when it happened, where the player was, and what the browser says took the time.
  const { frames, slow, loaf }: { frames: number[]; slow: string[]; loaf: string[] } = await page.evaluate(`new Promise((res) => {
    const out = [], slow = [], loaf = [];
    const start = performance.now();
    let last = start;
    const end = last + ${seconds} * 1000;
    try {
      new PerformanceObserver((l) => { for (const e of l.getEntries()) loaf.push(
        (e.startTime - start).toFixed(0) + ' ms in: ' + e.duration.toFixed(0) + ' ms, blocking ' + e.blockingDuration.toFixed(0) + ', scripts ' +
        (e.scripts.map((x) => (x.sourceFunctionName || x.invoker || '?') + ' ' + x.duration.toFixed(0)).join('; ') || 'none')
      ); }).observe({ type: 'long-animation-frame' });
    } catch {}
    // What the renderer has created so far; a jump on a slow frame points at first-time GPU work.
    const r = window.__game && window.__game.renderer;
    const gpu = () => r ? 'textures ' + r.info.memory.textures + ', geometries ' + r.info.memory.geometries + ', pipelines ' + (r._pipelines ? r._pipelines.caches.size : '?') : '';
    let prevGpu = gpu();
    const f = (t) => {
      out.push(t - last);
      const nowGpu = gpu();
      if (nowGpu !== prevGpu) { slow.push('renderer grew, ' + ((t - start) / 1000).toFixed(1) + ' s in, ' + (t - last).toFixed(1) + ' ms: ' + prevGpu + ' -> ' + nowGpu); prevGpu = nowGpu; }
      if (out.length > 1 && t - last > 25) {
        const p = window.__game && window.__game.player;
        slow.push((t - last).toFixed(1) + ' ms, ' + ((t - start) / 1000).toFixed(1) + ' s in' + (p ? ', at ' + p.feet.x.toFixed(1) + ',' + p.feet.z.toFixed(1) + ' yaw ' + p.yaw.toFixed(2) : ''));
      }
      last = t;
      if (t < end) requestAnimationFrame(f);
      else res({ frames: out.slice(1), slow, loaf });
    };
    requestAnimationFrame(f);
  })`);
  const sorted = [...frames].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const worst = sorted.slice(Math.floor(sorted.length * 0.99));
  const avgWorst = worst.reduce((a, b) => a + b, 0) / worst.length;
  console.log(`backend: ${backend}  frames: ${frames.length}  seconds: ${seconds}`);
  console.log(`median fps: ${(1000 / median).toFixed(1)}`);
  console.log(`1% low fps: ${(1000 / avgWorst).toFixed(1)}`);
  console.log(`max frame ms: ${sorted[sorted.length - 1].toFixed(1)}`);
  for (const x of slow) console.log(`slow frame: ${x}`);
  for (const x of loaf) console.log(`long frame: ${x}`);
  if (flags.has('walk')) console.log(`walked m: ${(await page.evaluate(() => (window as any).__walked)).toFixed(1)}`);
} finally {
  await browser.close();
  await dev?.server.close();
}
