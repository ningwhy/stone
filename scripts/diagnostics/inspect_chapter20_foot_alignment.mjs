import {chromium} from 'playwright';
import {seekSection} from '../../tests/lib/toc.mjs';
import {dismissLeaf} from '../../tests/lib/pickup.mjs';

// Walk the chapter-20 cast on screen and measure where each sprite's feet land
// versus the cell the engine says they stand on. The chapter-20 characters
// (jia_huan, jia_lian, yuanchun, zhao_yiniang, she_yue, shi_xiangyun) had
// their anchors rebuilt when the bamboo asset was replaced, so this is the
// check that the rebuild did not move anybody off their cell.
const browser = await chromium.launch({
  headless: true,
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
});
const page = await browser.newPage({viewport: {width: 1440, height: 900}, reducedMotion: 'reduce'});
const errors = [];
page.on('pageerror', e => errors.push(e.message));
const reading = async () => {
  for (let i = 0; i < 6; i++) {
    const b = page.getByRole('button', {name: '跳过移动', exact: true});
    if (await b.isVisible()) { await b.click(); await page.waitForTimeout(60); }
  }
  await page.locator('.dialogue-text').waitFor();
  await page.locator('.game-map[data-scene-ready]').waitFor();
};
try {
  await page.goto(process.env.TEST_URL ?? 'http://127.0.0.1:5173');
  await reading();
  await dismissLeaf(page, false, true);

  const seen = new Map();
  const sections = ['c20-tanyi', 'c20-xiangyun', 'c20-momo', 'c20-fengjie', 'c20-shuyao'];
  for (const sec of sections) {
    await seekSection(page, sec);
    await reading();
    // Walk a few nodes so different actors take the stage.
    for (let step = 0; step < 6; step++) {
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
          if (!sprite) continue;
          const p = project(a.col, a.row);
          const dw = sprite.displayWidth ?? 0;
          out.push({
            actor,
            cell: `${a.col},${a.row}`,
            engineX: Math.round(p.x),
            engineY: Math.round(p.y),
            originX: Number((sprite.originX ?? 0).toFixed(3)),
            originY: Number((sprite.originY ?? 0).toFixed(3)),
            displayW: Math.round(dw),
            feetOffsetPx: Math.round((0.5 - (sprite.originX ?? 0)) * dw),
            feetDyPx: Math.round((1 - (sprite.originY ?? 0)) * (sprite.displayHeight ?? 0)),
          });
        }
        return {step: s.engine.steps[st.index].id, scene: s.mapData.id, rows: out};
      });
      for (const r of rows.rows) {
        const key = `${r.actor}@${r.cell}`;
        if (!seen.has(key)) seen.set(key, {...r, node: rows.step, scene: rows.scene});
      }
      const next = page.getByRole('button', {name: '继续剧情', exact: true});
      if (!(await next.isVisible())) break;
      await next.click();
      await reading();
    }
  }
  console.log(JSON.stringify([...seen.values()], null, 1));
  console.log('page errors:', errors);
} finally {
  await browser.close();
}
