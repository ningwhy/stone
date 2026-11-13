import {chromium} from 'playwright';

// Does a character's feet land on the cell the engine says they stand on?
// The sprite is drawn with its origin at the calibrated anchor
// (setOrigin(anchor[0]/w, anchor[1]/h)), so the drawn feet sit at
// origin + (0.5 - originX) * displayWidth. If the anchor is wrong, the feet
// and the engine's cell disagree and the walk looks broken even though every
// movement resolves.
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
  const rows = await page.evaluate(() => {
    const s = window.__mapScene;
    const st = s.engine.getSnapshot();
    const map = s.mapData;
    const project = (col, row) => ({
      x: (col - row) * map.tilewidth / 2,
      y: (col + row + 1) * map.tileheight / 2,
    });
    const out = [];
    for (const [actor, a] of Object.entries(st.actors)) {
      if (!a.visible) continue;
      const sprite = s.actorSprites?.get?.(actor);
      if (!sprite) { out.push({actor, note: 'no sprite'}); continue; }
      const p = project(a.col, a.row);
      const dw = sprite.displayWidth ?? 0;
      const originX = sprite.originX ?? 0;
      // Where the sprite's bottom-centre lands, relative to the container origin.
      const feetOffset = (0.5 - originX) * dw;
      out.push({
        actor,
        cell: `${a.col},${a.row}`,
        engineX: Math.round(p.x),
        engineY: Math.round(p.y),
        originX: Number(originX.toFixed(3)),
        originY: Number((sprite.originY ?? 0).toFixed(3)),
        displayW: Math.round(dw),
        displayH: Math.round(sprite.displayHeight ?? 0),
        feetOffsetPx: Math.round(feetOffset),
        spriteWorldX: Math.round(sprite.worldView ? sprite.x : sprite.x),
      });
    }
    return {step: s.engine.steps[st.index].id, scene: s.mapData.id, rows: out};
  });
  console.log(JSON.stringify(rows, null, 1));
  console.log('errors:', errors);
} finally {
  await browser.close();
}
