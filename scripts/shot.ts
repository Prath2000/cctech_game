import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { parseArgs, startServer, launch, openGame } from './lib';

const { flags, opts, pos } = parseArgs(process.argv.slice(2));
const pose = pos[0] ?? 'overview';
const [w, h] = (opts.size ?? '1600x1200').split('x').map(Number);
const { server, url } = await startServer();
const browser = await launch(flags.has('headed'));
try {
  const q = `pose=${encodeURIComponent(pose)}${flags.has('webgl') ? '&webgl=1' : ''}`;
  const { page, backend } = await openGame(browser, url, q, w, h);
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
