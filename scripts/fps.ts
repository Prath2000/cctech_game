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
  if (flags.has('walk')) await page.evaluate(() => {
    const g = (window as any).__game, pl = g.player;
    let key = 'KeyW', dist = 0, prev = pl.feet.clone();
    pl.press(key);
    setInterval(() => { pl.press(key, false); key = key === 'KeyW' ? 'KeyS' : 'KeyW'; pl.press(key); }, 2000);
    setInterval(() => { dist += pl.feet.distanceTo(prev); prev.copy(pl.feet); (window as any).__walked = dist; g.camera.rotation.y += 0.01; }, 50);
  });
  const frames: number[] = await page.evaluate(`new Promise((res) => {
    const out = [];
    let last = performance.now();
    const end = last + ${seconds} * 1000;
    const f = (t) => {
      out.push(t - last);
      last = t;
      if (t < end) requestAnimationFrame(f);
      else res(out.slice(1));
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
} finally {
  await browser.close();
  await dev?.server.close();
}
