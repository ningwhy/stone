import {chromium} from 'playwright';
import {readFileSync} from 'node:fs';

// The anchor is the sprite's origin: setOrigin(anchor[0]/width, anchor[1]/height).
// If the anchor is outside the bitmap, the sprite is drawn off its own texture
// and its feet never land on the cell it stands on. This measures, on screen,
// where each character's feet actually are versus where the engine says they are.
const manifest = JSON.parse(readFileSync('public/assets/rongguo/manifest.json')).assets;
const suspects = Object.entries(manifest)
  .filter(([k, v]) => k.endsWith('-chibi') || k.endsWith('-portrait'))
  .filter(([, v]) => v.anchor[0] > v.width || v.anchor[1] > v.height);

console.log('suspects (anchor outside bitmap):');
for (const [k, v] of suspects) {
  console.log(`  ${k.padEnd(24)} anchor=${JSON.stringify(v.anchor)} size=${v.width}x${v.height}`);
}

const browser = await chromium.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
});
const page = await browser.newPage({viewport: {width: 1440, height: 900}, reducedMotion: 'reduce'});
const errors = [];
page.on('pageerror', e => errors.push(e.message));
try {
  await page.goto(process.env.TEST_URL ?? 'http://127.0.0.1:5173');
  await page.locator('.loading-screen').waitFor({state: 'detached', timeout: 30000});
  await page.waitForFunction(() => !!window.__mapScene, undefined, {timeout: 30000});
  const info = await page.evaluate(() => {
    const s = window.__mapScene;
    const st = s.engine.getSnapshot();
    const out = [];
    for (const [actor, a] of Object.entries(st.actors)) {
      if (!a.visible) continue;
      const sprite = s.actors?.[actor]?.sprite ?? null;
      out.push({actor, col: a.col, row: a.row, moving: !!a.moving});
    }
    return {step: s.engine.steps[st.index].id, scene: s.mapData.id, actors: out};
  });
  console.log('\nvisible actors on screen:', JSON.stringify(info, null, 1));
  await page.screenshot({path: 'artifacts/probe-anchor.png'});
  console.log('page errors:', errors);
} finally {
  await browser.close();
}
