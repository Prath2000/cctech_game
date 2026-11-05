import { parseArgs, startServer, launch, openGame } from './lib';

const { flags, opts } = parseArgs(process.argv.slice(2));
const seconds = Number(opts.seconds ?? 10);
const pose = opts.pose ?? 'overview';
const headed = flags.has('headed');
if (!headed) console.warn('WARNING: headless run; fps is not representative of a real Mac GPU/display. Use --headed.');
const { server, url } = await startServer();
const browser = await launch(headed);
try {
  const q = `pose=${encodeURIComponent(pose)}${flags.has('webgl') ? '&webgl=1' : ''}`;
  const { page, backend } = await openGame(browser, url, q, 1280, 720);
  await page.waitForTimeout(2000); // warm-up
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
  await server.close();
}
