// Side-by-side photo | shot for every pose with a `photo` field -> .team/work/shots/match-<pose>.png
// Usage: pnpm check:match [pose ...]
import { readFileSync, mkdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { parseArgs, startServer, launch, openGame } from './lib';

const { pos } = parseArgs(process.argv.slice(2));
const poses = JSON.parse(readFileSync('src/data/camera-poses.json', 'utf8')) as Record<string, { aspect?: number; photo?: string }>;
const names = Object.keys(poses).filter((n) => poses[n].photo && (!pos.length || pos.includes(n)));
const dir = '.team/work/shots';
mkdirSync(dir, { recursive: true });
const { server, url } = await startServer();
const browser = await launch(false);
try {
  for (const n of names) {
    const aspect = poses[n].aspect ?? 4 / 3;
    const [w, h] = aspect >= 1 ? [1600, Math.round(1600 / aspect)] : [Math.round(1600 * aspect), 1600];
    const { page } = await openGame(browser, url, `pose=${encodeURIComponent(n)}`, w, h);
    await page.waitForTimeout(500);
    const shot = `${dir}/${n}-shot.png`;
    await page.screenshot({ path: shot });
    await page.close();
    const out = `${dir}/match-${n}.png`;
    const py = `import sys\nfrom PIL import Image\na=Image.open(sys.argv[1]).convert('RGB');b=Image.open(sys.argv[2]).convert('RGB')\nH=800;a=a.resize((round(a.width*H/a.height),H));b=b.resize((round(b.width*H/b.height),H))\no=Image.new('RGB',(a.width+b.width,H));o.paste(a,(0,0));o.paste(b,(a.width,0));o.save(sys.argv[3])`;
    execFileSync('python3', ['-c', py, `references/img/photos/${poses[n].photo}`, shot, out]);
    console.log(`saved ${out}`);
  }
} finally {
  await browser.close();
  await server.close();
}
