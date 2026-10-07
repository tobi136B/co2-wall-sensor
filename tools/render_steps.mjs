// Pictures of the assembly steps for docs/assembly.md, taken from the 3D assembly guide.
//
// Every step is shown in its finished state, without the panel, so the picture works in both languages.
//
// Usage:   python tools/build_site.py --version dev --out _site
//          npm install --no-save playwright-core three@0.170.0
//          node tools/render_steps.mjs _site docs/images/steps
// Needs Chromium (PLAYWRIGHT_CHROMIUM or /opt/pw-browsers/chromium).

import { chromium } from 'playwright-core';
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, resolve } from 'node:path';

const [site, outDir] = process.argv.slice(2);
if (!site || !outDir) {
  console.error('usage: node tools/render_steps.mjs SITE_DIR OUT_DIR');
  process.exit(2);
}
const THREE = resolve('node_modules/three');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png',
  '.stl': 'application/octet-stream', '.svg': 'image/svg+xml' };

const server = createServer(async (req, res) => {
  try {
    const path = decodeURIComponent(req.url.split('?')[0]);
    const file = join(resolve(site), path.endsWith('/') ? path + 'index.html' : path);
    res.writeHead(200, { 'content-type': TYPES[extname(file)] || 'application/octet-stream' });
    res.end(await readFile(file));
  } catch {
    res.writeHead(404);
    res.end();
  }
}).listen(0);
const base = `http://127.0.0.1:${server.address().port}/`;

const browser = await chromium.launch({
  executablePath: process.env.PLAYWRIGHT_CHROMIUM || '/opt/pw-browsers/chromium',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await (await browser.newContext({ viewport: { width: 1300, height: 820 } })).newPage();
page.on('pageerror', (e) => console.error('page error:', e.message));
// three.js from node_modules instead of the CDN, fonts are not needed for the canvas
await page.route(/cdn\.jsdelivr\.net\/npm\/three@[^/]+\/(.*)/, (r) =>
  r.fulfill({ path: join(THREE, r.request().url().replace(/.*three@[^/]+\//, '')), contentType: 'text/javascript' }));
await page.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.abort());
await page.goto(base + 'assembly.html');
await page.waitForFunction(() => window.assemblyGuide, null, { timeout: 60000 });
await page.addStyleTag({ content: '#hint, #badge, #progress, .tip { display: none !important; }' });

await mkdir(outDir, { recursive: true });
const count = await page.evaluate(() => window.assemblyGuide.data.steps.length);
for (let i = 0; i < count; i++) {
  await page.evaluate((k) => window.assemblyGuide.goTo(k, { instant: true }), i);
  await page.waitForTimeout(4500); // the new parts light up shortly, wait until they show their true colours
  const file = join(outDir, `step_${String(i + 1).padStart(2, '0')}.png`);
  await page.locator('#stage canvas').screenshot({ path: file });
  console.log('written:', file);
}
await browser.close();
server.close();
