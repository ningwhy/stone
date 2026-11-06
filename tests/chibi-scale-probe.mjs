// Measure how tall the chibi figures actually stand on the map.
//
// The engine scales every chibi by `max(1, 48/(bitmapHeight*zoom))` and the
// bitmaps are ~116px tall, so that term is 0.41 and the max() pins the scale
// to 1: every chibi used to be drawn at its raw bitmap size, and the painted
// figure inside each bitmap decided how tall the person looked. A build scale
// now shortens the figures the way their age asks for.
//
// The probe reads the live scene instead of guessing from the bitmaps: the
// bitmap is ~116px for everybody, so only the on-stage size can answer the
// question the reader actually asks — is the child shorter than the grown woman?
//
// Usage: node tests/chibi-scale-probe.mjs [sectionId]
import { chromium } from 'playwright';
import { existsSync, mkdirSync } from 'node:fs';
const exe = process.env.CHROME_PATH || (existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome') ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : undefined);
const browser = await chromium.launch({ headless: true, executablePath: exe });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
const page = await ctx.newPage();
mkdirSync('artifacts', { recursive: true });

const settle = async () => {
  await page.locator('.loading-screen').waitFor({ state: 'detached', timeout: 60000 });
  for (let i = 0; i < 12; i++) {
    const b = page.getByRole('button', { name: '跳过移动', exact: true });
    if (await b.isVisible()) { await b.click(); await page.waitForTimeout(50); }
  }
  await page.waitForFunction(() => !!document.querySelector('.dialogue-text')?.textContent?.trim(), undefined, { timeout: 60000 });
  await page.locator('.game-map[data-scene-ready]').waitFor({ timeout: 60000 });
  await page.waitForTimeout(500);
};

await page.goto(process.env.TEST_URL ?? 'http://127.0.0.1:5173');
await settle();

const section = process.argv[2] ?? 'c6-village';
const steps = Number(process.argv[3] ?? 0);
const { seekSection } = await import('./lib/toc.mjs');
await seekSection(page, section);
await settle();
await page.waitForTimeout(600);

// Walk on to a later beat so a specific group of people can be photographed
// standing together.
for (let i = 0; i < steps; i++) {
  const next = page.getByRole('button', { name: '继续剧情' });
  if (await next.count()) {
    await next.click();
  } else {
    await page.keyboard.press('Space');
  }
  await page.waitForTimeout(260);
}
await settle();
await page.waitForTimeout(600);

// The actor container holds the sprite plus its contact shadow; the sprite's
// origin is its foot anchor, so the on-stage height of the figure is the
// distance from the sprite's top edge to the anchor.
const measured = await page.evaluate(() => {
  const scene = window.__mapScene;
  if (!scene) return { error: 'no scene' };
  const zoom = scene.cameras.main.zoom;
  const rows = [];
  for (const [id, view] of scene.actorViews) {
    const sprite = scene.actorSprites.get(id);
    if (!sprite) continue;
    const asset = scene.textures.get(sprite.texture.key).getSourceImage();
    const h = asset.height;
    const anchorFrac = sprite.originY;
    // Figure height = everything above the foot anchor, scaled.
    const figurePx = h * anchorFrac * view.scaleY * zoom;
    const totalPx = h * view.scaleY * zoom;
    rows.push({
      id,
      visible: view.visible,
      bitmap: h,
      scale: Number(view.scaleY.toFixed(3)),
      figurePx: Math.round(figurePx),
      totalPx: Math.round(totalPx),
    });
  }
  return { zoom: Number(zoom.toFixed(3)), rows };
});

if (measured.error) {
  console.log(JSON.stringify(measured));
} else {
  console.log(`zoom=${measured.zoom}`);
  console.log('id'.padEnd(14) + 'bitmap'.padEnd(8) + 'scale'.padEnd(8) + 'figure(px)'.padEnd(12) + 'full(px)');
  for (const r of measured.rows.filter(r => r.visible).sort((a, b) => b.figurePx - a.figurePx)) {
    console.log(
      r.id.padEnd(14) + String(r.bitmap).padEnd(8) + String(r.scale).padEnd(8) +
      String(r.figurePx).padEnd(12) + String(r.totalPx));
  }
}

const info = await page.evaluate(() => ({
  node: document.querySelector('.node-label')?.textContent ?? '',
  dialogue: document.querySelector('.dialogue-text')?.textContent?.trim().slice(0, 70) ?? '',
}));
console.log(JSON.stringify(info, null, 1));

await page.screenshot({ path: `artifacts/chibi-scale-${section}.png`, fullPage: true });
console.log('screenshot: artifacts/chibi-scale-' + section + '.png');
await browser.close();
