import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { readFileSync } from 'node:fs';
import { parseArgs, startServer, launch, openGame } from './lib';

const { flags, opts, pos } = parseArgs(process.argv.slice(2));
const pose = pos[0] ?? 'overview';
const poses = JSON.parse(readFileSync('src/data/camera-poses.json', 'utf8')) as Record<string, { aspect?: number }>;
const aspect = poses[pose]?.aspect ?? 4 / 3; // width / height; portrait photos are 0.75
const long = Number(opts.long ?? 1600);
const [w, h] = opts.size
  ? opts.size.split('x').map(Number)
  : aspect >= 1 ? [long, Math.round(long / aspect)] : [Math.round(long * aspect), long];
const { server, url } = await startServer();
const browser = await launch(flags.has('headed'));
try {
  const q = `${opts.q ? opts.q + '&' : ''}pose=${encodeURIComponent(pose)}${flags.has('webgl') ? '&webgl=1' : ''}`;
  const { page, backend } = await openGame(browser, url, q, w, h, opts.page ?? '');
  if (flags.has('webgl') && backend !== 'WebGL2') console.warn(`warning: asked for WebGL2, got ${backend}`);
  if (!flags.has('webgl') && backend !== 'WebGPU') console.warn('warning: WebGPU unavailable here; rendered with WebGL2 fallback');
  await page.waitForTimeout(500);
  const out = opts.out ?? `.team/work/shots/${pose}-${backend.toLowerCase()}.png`;
  mkdirSync(dirname(out), { recursive: true });
  await page.screenshot({ path: out });
  console.log(`saved ${out} (backend: ${backend}, ${w}x${h})`);
} finally {
  await browser.close();
  await server.close();
}
