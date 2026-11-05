import { mkdirSync, readFileSync } from 'node:fs';
import { chromium } from 'playwright';
import { parseArgs, startServer } from './lib';

// pnpm render:pt [pose ...] [--spp 700] [--cap 170] [--headed] [--q "sun=12&exp=1"]
const { flags, opts, pos } = parseArgs(process.argv.slice(2));
const all = Object.keys(JSON.parse(readFileSync('src/pathtrace/poses.json', 'utf8')));
const names = pos.length ? pos : all;
const spp = Number(opts.spp ?? 64);
const capMs = Number(opts.cap ?? 170) * 1000;
const [W, H] = [1600, 1000];
const { server, url } = await startServer();
const browser = await chromium.launch({
  headless: !flags.has('headed'),
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-unsafe-webgpu'],
});
try {
  mkdirSync('renders/pathtrace', { recursive: true });
  for (const name of names) {
    const page = await browser.newPage({ viewport: { width: W, height: H } });
    page.on('pageerror', (e) => console.error('[page error]', e.message));
    page.on('console', (m) => { if (m.type() === 'error') console.error('[console]', m.text()); });
    await page.goto(`${url}pathtrace.html?pose=${name}&spp=${spp}&w=${W}&h=${H}${opts.q ? '&' + opts.q : ''}`);
    await page.waitForFunction(() => (window as any).__pt, null, { timeout: 120000 });
    const t0 = Date.now();
    while (Date.now() - t0 < capMs && !(await page.evaluate(() => (window as any).__pt.done))) await page.waitForTimeout(1000);
    const n = await page.evaluate(() => (window as any).__pt.samples);
    const out = `renders/pathtrace/${name}.png`;
    await page.locator('canvas').screenshot({ path: out });
    console.log(`${name}: ${Math.round(n)} spp in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${out}`);
    await page.close();
  }
} finally {
  await browser.close();
  await server.close();
}
