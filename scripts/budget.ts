// Numbers for docs/reference/performance-budget.md: draw calls and triangles per pose, plus cold load on a throttled
// network. Usage: pnpm run check:budget --url http://localhost:4173 [--mbps 50] [--headed]. Needs a production preview running for a fair load time.
import { parseArgs, startServer, launch, openGame } from './lib';

const { flags, opts } = parseArgs(process.argv.slice(2));
const mbps = Number(opts.mbps ?? 50);
const dev = opts.url ? null : await startServer();
const url = opts.url ?? dev!.url;
const browser = await launch(flags.has('headed'));
try {
  const { page, backend } = await openGame(browser, url, 'pose=overview', 1280, 720);
  console.log(`backend: ${backend}`);
  console.log('pose  drawCalls  triangles');
  const poses: string[] = await page.evaluate(() => (window as any).__game.poses);
  for (const name of poses) {
    const moved = await page.evaluate((n) => (window as any).__game.setPose(n), name);
    if (!moved) throw new Error(`unknown pose ${name}`);
    await page.waitForTimeout(300);
    const { drawCalls, triangles } = await page.evaluate(() => (window as any).__game.renderer.info.render);
    console.log(`${name}  ${drawCalls}  ${triangles}`);
  }
  await page.close();

  // Cold load: new context, so nothing is cached.
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const cold = await ctx.newPage();
  const cdp = await ctx.newCDPSession(cold);
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  await cdp.send('Network.emulateNetworkConditions', {
    offline: false, latency: 20, downloadThroughput: (mbps * 1e6) / 8, uploadThroughput: (mbps * 1e6) / 8,
  });
  let bytes = 0;
  cdp.on('Network.loadingFinished', (e: { encodedDataLength: number }) => { bytes += e.encodedDataLength; });
  await cold.addInitScript('window.__name = (f) => f');
  const t0 = Date.now();
  await cold.goto(url);
  await cold.waitForFunction(() => (window as any).__game, null, { timeout: 180000 });
  await cold.evaluate(() => (window as any).__game.ready);
  console.log(`cold load at ${mbps} Mbps: ${((Date.now() - t0) / 1000).toFixed(1)} s, ${(bytes / 1e6).toFixed(1)} MB over the wire`);
} finally {
  await browser.close();
  await dev?.server.close();
}
