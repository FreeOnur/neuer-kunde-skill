// Captures the README screenshots and GIF frames from real sites built with /neuer-kunde.
// Usage: node capture.mjs <base-url> <out-dir> [job ...]
//   base-url  a static build of the Löwen Webdesign site (it also serves the concept sites under /konzepte/)
//   jobs      hero3d | swipe | concepts | stills   (default: all)
// Frames land in <out-dir>/<job>/ and are turned into GIFs with ffmpeg (see make-gifs.sh).
// WebGL in a headless cloud browser runs on SwiftShader (software), so the 3D frames are taken with
// reduced motion: the world jumps straight to each scroll position and renders one clean frame.
import { mkdirSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(process.env.PLAYWRIGHT_FROM ?? import.meta.url);
const { chromium, devices } = require('playwright');

const [base = 'http://127.0.0.1:4555', out = './frames', ...wanted] = process.argv.slice(2);
const jobs = wanted.length ? wanted : ['hero3d', 'swipe', 'concepts', 'stills'];
const webgl = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const dir = (name) => { const d = `${out}/${name}`; mkdirSync(d, { recursive: true }); return d; };
const pad = (i) => String(i).padStart(3, '0');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function noSound(page) {
  const b = page.getByRole('button', { name: /^(No sound|Ohne Ton)$/ });
  if (await b.count()) await b.first().click().catch(() => {});
  await page.mouse.move(2, 2);
}

/** The 3D world: from the lion at the top through the tunnel to the ring around the work. */
async function hero3d(browser) {
  const d = dir('hero3d');
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  await page.goto(`${base}/en/?welt=immer`);
  await page.waitForFunction(() => performance.getEntriesByName('welt:erstes-bild').length > 0, null, { timeout: 120_000 });
  await noSound(page);
  await wait(1500);
  const end = await page.evaluate(() => { const s = document.querySelector('#arbeiten'); return s.getBoundingClientRect().top + scrollY + 60; });
  const n = 72;
  for (let i = 0; i < n; i++) {
    // ease in and out, so the start and the end hold for a moment
    const t = i / (n - 1), e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    await page.evaluate((y) => window.scrollTo(0, y), Math.round(e * end));
    await wait(450);
    await page.screenshot({ path: `${d}/${pad(i)}.png` });
  }
  await ctx.close();
}

/** Phone: swiping through the work with a finger. */
async function swipe(browser) {
  const d = dir('swipe');
  const ctx = await browser.newContext({ ...devices['Pixel 7'], viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  await page.goto(`${base}/en/`);
  await wait(1500);
  await noSound(page);
  await page.evaluate(() => { const s = document.querySelector('#arbeiten'); window.scrollTo(0, s.getBoundingClientRect().top + scrollY + 2); });
  await wait(2500);
  const cdp = await ctx.newCDPSession(page);
  let i = 0;
  const shot = async () => page.screenshot({ path: `${d}/${pad(i++)}.png` });
  for (let k = 0; k < 6; k++) { await shot(); await wait(80); }
  for (const [from, to] of [[330, 70], [330, 70], [330, 70], [60, 330]]) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: from, y: 430 }] });
    for (let k = 1; k <= 10; k++) {
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: from + ((to - from) * k) / 10, y: 432 }] });
      if (k % 2 === 0) await shot();
    }
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    for (let k = 0; k < 14; k++) { await shot(); await wait(60); }
  }
  await ctx.close();
}

/** The three concept sites: what their motion looks like right after loading, then a little scrolling. */
async function concepts(browser) {
  for (const k of ['tischlerei-frastanz', 'friseur-feldkirch', 'gasthaus-bludenz']) {
    const d = dir(`concept-${k}`);
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    const page = await ctx.newPage();
    await page.goto(`${base}/konzepte/${k}/`, { waitUntil: 'domcontentloaded' });
    let i = 0;
    const t0 = Date.now();
    while (Date.now() - t0 < 3200) { await page.screenshot({ path: `${d}/${pad(i++)}.png` }); await wait(40); }
    for (let s = 0; s < 34; s++) {
      await page.mouse.wheel(0, 70);
      await page.screenshot({ path: `${d}/${pad(i++)}.png` });
      await wait(30);
    }
    for (let s = 0; s < 12; s++) { await page.screenshot({ path: `${d}/${pad(i++)}.png` }); await wait(60); }
    await ctx.close();
  }
}

/** Still screenshots for the gallery. */
async function stills(browser) {
  const d = dir('stills');
  // Desktop with the 3D world
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
    const page = await ctx.newPage();
    await page.goto(`${base}/en/?welt=immer`);
    await page.waitForFunction(() => performance.getEntriesByName('welt:erstes-bild').length > 0, null, { timeout: 120_000 });
    await noSound(page);
    await wait(2000);
    await page.screenshot({ path: `${d}/loewen-hero.png` });
    for (const [name, sel, dy] of [['loewen-work', '#arbeiten', 0], ['loewen-tech', '#technik', 0], ['loewen-pricing', '#preise', -70]]) {
      await page.evaluate(([s, d]) => { const el = document.querySelector(s); window.scrollTo(0, el.getBoundingClientRect().top + scrollY + d); }, [sel, dy]);
      await wait(2500);
      await page.screenshot({ path: `${d}/${name}.png` });
    }
    await ctx.close();
  }
  // Phone with the 3D world
  {
    const ctx = await browser.newContext({ ...devices['Pixel 7'], viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    const page = await ctx.newPage();
    await page.goto(`${base}/en/?welt=immer`);
    await page.waitForFunction(() => performance.getEntriesByName('welt:erstes-bild').length > 0, null, { timeout: 120_000 });
    await noSound(page);
    await wait(2000);
    await page.screenshot({ path: `${d}/loewen-phone-hero.png` });
    await page.evaluate(() => { const el = document.querySelector('#preise'); window.scrollTo(0, el.getBoundingClientRect().top + scrollY + 330); });
    await wait(2500);
    await page.screenshot({ path: `${d}/loewen-phone-pricing.png` });
    await ctx.close();
  }
}

const browser = await chromium.launch({ args: webgl });
for (const j of jobs) {
  const t = Date.now();
  await ({ hero3d, swipe, concepts, stills })[j](browser);
  console.log(`${j}: ${Math.round((Date.now() - t) / 1000)} s`);
}
await browser.close();
