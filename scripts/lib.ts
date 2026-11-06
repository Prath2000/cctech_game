import { createServer, type ViteDevServer } from 'vite';
import { chromium, type Browser, type Page } from 'playwright';

export function parseArgs(argv: string[]) {
  const flags = new Set<string>();
  const opts: Record<string, string> = {};
  const pos: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const k = a.slice(2);
      if (['webgl', 'headed', 'no-pose'].includes(k)) flags.add(k);
      else opts[k] = argv[++i];
    } else pos.push(a);
  }
  return { flags, opts, pos };
}

export async function startServer(): Promise<{ server: ViteDevServer; url: string }> {
  const server = await createServer({ server: { port: 5199, strictPort: false }, logLevel: 'error' });
  await server.listen();
  const url = server.resolvedUrls?.local[0] ?? 'http://localhost:5199/';
  return { server, url };
}

export async function launch(headed: boolean): Promise<Browser> {
  const args = ['--enable-unsafe-webgpu', '--enable-features=Vulkan', '--use-angle=metal', '--ignore-gpu-blocklist'];
  for (const channel of ['chrome', undefined]) {
    try {
      return await chromium.launch({ headless: !headed, channel, args });
    } catch {
      /* try next */
    }
  }
  throw new Error('No Chromium available; run `pnpm exec playwright install chromium`');
}

export async function openGame(
  browser: Browser, url: string, query: string, width: number, height: number, pagePath = '',
): Promise<{ page: Page; backend: string }> {
  const page = await browser.newPage({ viewport: { width, height } });
  await page.addInitScript('window.__name = (f) => f'); // tsx/esbuild helper used inside page.evaluate callbacks
  page.on('pageerror', (e) => console.error('[page error]', e.message));
  await page.goto(`${url}${pagePath}?${query}`);
  await page.waitForFunction(() => (window as any).__game, null, { timeout: 30000 });
  // vite may full-reload once (dep optimisation / file changes); retry across navigations
  for (let i = 0; ; i++) {
    try {
      await page.waitForFunction(() => (window as any).__game, null, { timeout: 30000 });
      await page.evaluate(() => (window as any).__game.ready);
      const backend: string = await page.evaluate(() => (window as any).__game.backend);
      return { page, backend };
    } catch (e) {
      if (i >= 3 || !String(e).includes('navigation')) throw e;
    }
  }
}
