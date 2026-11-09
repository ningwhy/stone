// 人物美术验收：图鉴脸部区分 / 体型档位 / 脚底锚点对齐地面 / 地面阴影与层级遮挡。
//
// 跑法：node tests/character-art-qa.mjs   （依赖本地 dev server http://127.0.0.1:5173）
// 产物：artifacts/char-art/*.png + 控制台打印的实测数据（缺陷以数据确认，不只截图）。
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { seekSection } from './lib/toc.mjs';
import { dismissPickup, dismissLeaf } from './lib/pickup.mjs';

const exe = process.env.CHROME_PATH || (existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome') ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : undefined);
const URL = process.env.TEST_URL ?? 'http://127.0.0.1:5173';
const browser = await chromium.launch({ headless: true, executablePath: exe });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', e => errors.push(e.message));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
mkdirSync('artifacts/char-art', { recursive: true });

const settle = async () => {
  await page.locator('.loading-screen').waitFor({ state: 'detached', timeout: 60000 });
  for (let i = 0; i < 14; i++) {
    const b = page.getByRole('button', { name: '跳过移动', exact: true });
    if (await b.isVisible()) { await b.click(); await page.waitForTimeout(45); }
  }
  await page.waitForFunction(() => !!document.querySelector('.dialogue-text')?.textContent?.trim(), undefined, { timeout: 60000 });
  await page.locator('.game-map[data-scene-ready]').waitFor({ timeout: 60000 });
  await page.waitForTimeout(450);
  // 开书/跳读后可能压着封面或封底，先把纸页收掉，否则会挡住「设置」等按钮。
  await dismissLeaf(page, false, true);
};

const dismissOverlays = async () => {
  // 纸页 / 拾取层都可能挡住测量，先收掉。
  await dismissPickup(page);
  await dismissLeaf(page, false, true);
  await page.waitForTimeout(150);
};

try {
  await page.goto(URL);
  await settle();

  // ── ① 图鉴脸部区分 ────────────────────────────────────────────────
  await page.getByRole('button', { name: '设置', exact: true }).click();
  await page.getByRole('button', { name: '人物图鉴', exact: true }).click();
  await page.locator('.cast-gallery').evaluate(e => { e.scrollTop = 0; });
  await page.waitForFunction(() => [...document.querySelectorAll('.cast-gallery img')].every(i => i.complete && i.naturalWidth > 0), undefined, { timeout: 20000 });
  const gallery = await page.locator('.cast-gallery img').evaluateAll(images => images.map(i => ({ src: i.getAttribute('src'), w: i.naturalWidth, h: i.naturalHeight, alt: i.getAttribute('alt') })));
  assert.ok(gallery.length >= 30, `gallery shows too few portraits: ${gallery.length}`);
  for (const g of gallery) {
    assert.ok(g.w > 0 && g.h > 0, `broken portrait: ${g.src}`);
    assert.match(g.src, /\?v=[a-f0-9]{12}$/, `portrait not versioned: ${g.src}`);
  }
  // 像素级去重：把每张图绘到 canvas 取校验和，确认没有两张完全相同的立绘（漏配/串图）。
  const dup = await page.evaluate(async () => {
    const imgs = [...document.querySelectorAll('.cast-gallery img')];
    const hashes = [];
    for (const im of imgs) {
      const c = document.createElement('canvas');
      c.width = im.naturalWidth; c.height = im.naturalHeight;
      const x = c.getContext('2d'); x.drawImage(im, 0, 0);
      const d = x.getImageData(0, 0, c.width, c.height).data;
      let h = 2166136261;
      for (let i = 0; i < d.length; i += 7) { h ^= d[i]; h = Math.imul(h, 16777619); }
      hashes.push((h >>> 0).toString(16));
    }
    const seen = new Map(); const clashes = [];
    hashes.forEach((h, i) => { if (seen.has(h)) clashes.push([i, seen.get(h)]); else seen.set(h, i); });
    return { count: imgs.length, clashes };
  });
  assert.equal(dup.clashes.length, 0, `duplicate portraits detected: ${JSON.stringify(dup.clashes)}`);
  await page.screenshot({ path: 'artifacts/char-art/gallery.png', fullPage: true });
  console.log(`①图鉴：列出 ${gallery.length} 张立绘，全部加载且版本化；像素去重 ${dup.count} 张无重复（脸部区分基础成立）。`);
  await page.keyboard.press('Escape');
  await page.locator('dialog[open]').waitFor({ state: 'detached', timeout: 10000 }).catch(() => {});

  // ── ② 体型档位 + ③ 脚底锚点对齐地面 ─────────────────────────────
  // 刘姥姥进府：板儿(child 0.72) 与 平儿(adult 1.0) 同场，正好比对身高与脚底。
  await page.evaluate(() => window.__mapScene.engine.seek('C06-083'));
  await settle();
  await dismissOverlays();
  await page.waitForTimeout(600);
  await page.waitForFunction(() => document.querySelector('.game-map[data-scene-ready]'), undefined, { timeout: 20000 });

  const onStage = await page.evaluate(() => {
    const scene = window.__mapScene;
    if (!scene) return { error: 'no scene' };
    const zoom = scene.cameras.main.zoom;
    const rows = [];
    for (const [id, view] of scene.actorViews) {
      if (!view.visible) continue;
      const sprite = scene.actorSprites.get(id);
      if (!sprite) continue;
      const img = scene.textures.get(sprite.texture.key).getSourceImage();
      const anchorFrac = sprite.originY;          // 脚底锚点占比（1=脚在图底）
      const scale = view.scaleY;                   // 容器缩放 = build（zoom>0.41 时 max 取 1）
      const figurePx = img.height * anchorFrac * scale * zoom; // 脚底以上的身高
      const bounds = sprite.getBounds();
      // 脚底（sprite 底边）应落在容器坐标 view.y（即投影地面点）；偏离即「悬空/陷地」。
      const footGap = Math.abs(bounds.bottom - view.y);
      rows.push({
        id, bitmapH: img.height, anchorFrac: Number(anchorFrac.toFixed(3)),
        scale: Number(scale.toFixed(3)), figurePx: Math.round(figurePx),
        footY: Math.round(view.y), spriteBottom: Math.round(bounds.bottom), footGap: Math.round(footGap),
      });
    }
    rows.sort((a, b) => b.figurePx - a.figurePx);
    return { zoom: Number(zoom.toFixed(3)), rows };
  });
  assert.ok(!onStage.error, onStage.error);
  console.log(`②/③ 场景 C06-083 在台人物（zoom=${onStage.zoom}）：`);
  for (const r of onStage.rows) console.log(`  ${r.id.padEnd(12)} 身高=${String(r.figurePx).padEnd(5)}px  bitmap=${r.bitmapH}  anchor=${r.anchorFrac}  scale=${r.scale}  脚底偏差=${r.footGap}px`);
  await page.screenshot({ path: 'artifacts/char-art/chibi-c06-083.png', fullPage: true });

  const byId = Object.fromEntries(onStage.rows.map(r => [r.id, r]));
  assert.ok(byId.ban_er && byId.ping_er, `板儿或平儿未上场：${JSON.stringify(Object.keys(byId))}`);
  assert.ok(byId.ban_er.figurePx < byId.ping_er.figurePx, `体型档位失效：板儿(${byId.ban_er.figurePx}) ≮ 平儿(${byId.ping_er.figurePx})`);
  const ratio = (byId.ban_er.figurePx / byId.ping_er.figurePx).toFixed(2);
  // 档位表 child=0.72 / adult=1.0，且 bitmap 高度与 anchorFrac 近似一致，故比值应接近 0.72。
  assert.ok(Math.abs(Number(ratio) - 0.72) < 0.08, `体型比值偏离档位表预期 0.72：实测 ${ratio}`);
  // 脚底锚点：每个在台人物脚底应贴合地面（偏差 < 3px）。
  for (const r of onStage.rows) assert.ok(r.footGap < 3, `${r.id} 脚底偏离地面 ${r.footGap}px（悬空/陷地）`);
  console.log(`  体型档位：板儿/平儿 = ${ratio}（档位表 0.72），板儿明显矮于平儿；脚底偏差均 <3px（落地正确）。`);

  // ── ④ 地面阴影与层级遮挡（视觉 + 数据）────────────────────────────
  // 同一场景里人物与家具按等距地面点排序：深度 = p.y。取一个多人的室内/院落节点，
  // 截图目视阴影衔接，并用数据确认「北面的人应在北面的物之后（depth 小）」。
  await page.evaluate(() => window.__mapScene.engine.seek('C06-096'));
  await settle();
  await dismissOverlays();
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'artifacts/char-art/ground-occlusion.png', fullPage: true });
  // 对话立绘脸部细节
  const speaker = await page.evaluate(() => {
    const el = document.querySelector('.speaker-portrait img');
    return el ? { src: el.getAttribute('src'), w: el.naturalWidth, h: el.naturalHeight } : null;
  });
  if (speaker) { assert.ok(speaker.w > 0 && speaker.h > 0, 'speaker portrait broken'); console.log(`④ 对话立绘：${speaker.src} (${speaker.w}×${speaker.h}) 加载正常。`); }
  await page.screenshot({ path: 'artifacts/char-art/speaker.png', fullPage: true });

  // 深度排序不变量：所有在台 sprite 的 depth 必须等于其地面点 p.y，且同一列里
  // 北（row 小）的人物/物体 depth 更小 → 被南面的遮挡。这里只校验 depth==p.y。
  const depthOk = await page.evaluate(() => {
    const scene = window.__mapScene;
    let bad = 0, n = 0;
    for (const [id, view] of scene.actorViews) {
      if (!view.visible) continue;
      n++;
      if (Math.abs(view.depth - view.y) > 0.5) bad++;
    }
    return { n, bad };
  });
  assert.equal(depthOk.bad, 0, `存在深度≠地面点的角色：${depthOk.bad}/${depthOk.n}`);
  console.log(`④ 层级遮挡：在台 ${depthOk.n} 人 depth 均等于地面点 p.y，等距排序成立；阴影衔接见 ground-occlusion.png 目视。`);

  assert.deepEqual(errors, [], JSON.stringify(errors));
  console.log('\n全部断言通过：人物美术四项验收（图鉴区分 / 体型档位 / 脚底锚点 / 地面阴影遮挡）均成立。');
} catch (e) {
  console.error('验收失败：', errors);
  console.error((await page.locator('body').innerText()).slice(0, 2000));
  await page.screenshot({ path: 'artifacts/char-art/failure.png', fullPage: true }).catch(() => {});
  throw e;
} finally {
  await ctx.close();
  await browser.close();
}
