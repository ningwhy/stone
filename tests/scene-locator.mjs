/** 大地图定位转场的定向验收（换场景 + 每回开篇）。
 *
 *  守住八件事：
 *  1. 剧情用到的每一个 scene 都有方位；天下层 / 府内层的面包屑结构正确；
 *  2. 回目开篇：封面盖着时不白播，收起封面才出现，且 reason=chapter；
 *  3. 两种第二拍：府内层下钻到点阵图，天下层留在舆图上推镜（不切空白图）；
 *  4. 可跳过（按钮 / 自动收起）、设置可关、重开时当场补一次；
 *  5. 不吞指针、不改引擎状态：顶栏按钮仍可点，.game-map 仍算可见；
 *  6. 普通动效下 progress 真的从 0 走到 1，天下层的 detail 层全程不出现；
 *  7. ★ 转场必须等**这个场景**的图画完才播：转场每一帧，舞台上的
 *    data-scene-ready 都得等于转场目标场景（旧图还亮着、或底下空白都不行）；
 *  8. ★ 两拍**不交叠**：天下层与府内层不能同时半透明——那等于两张地图
 *    压在一起，地名互相干扰，读者两头都看不清。
 *
 *  与 check_content.mjs 的分工：那道门禁保证「不漏配场景」，这里保证
 *  「配了之后画得对」。两道都要过才能构建上线。
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { story, chapters } from '../src/story.ts';
import {
  scenePlaces, placeOf, regionPoint, detailPoint, breadcrumbs,
  levelDots, regionDots, sceneLevels,
} from '../src/scenePlaces.ts';
import { dismissLeaf, dismissPickup } from './lib/pickup.mjs';
import { seekSection } from './lib/toc.mjs';

const URL = process.env.TEST_URL ?? 'http://127.0.0.1:5173';
const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

// ---- 一、静态数据 ----
const used = new Set([...story.map(s => s.scene), ...chapters.map(c => c.scene)]);
for (const scene of used) {
  const place = placeOf(scene);
  assert.ok(place, `${scene} has no entry in design/scene-places.json`);
  assert.ok(sceneLevels[place.level], `${scene} points at an unknown level ${place.level}`);
  assert.ok(place.name?.trim(), `${scene} has no place name`);
  const rp = regionPoint(scene), dp = detailPoint(scene);
  for (const [label, pt] of [['region', rp], ['detail', dp]]) {
    assert.ok(Number.isFinite(pt.x) && Number.isFinite(pt.y), `${scene} has a non-finite ${label} point`);
  }
  const crumbs = breadcrumbs(scene);
  if (place.level === 'realm') assert.equal(crumbs.length, 1, `${scene} is a realm scene and must not drill down`);
  else assert.ok(crumbs.length >= 2, `${scene} in ${place.level} needs a breadcrumb trail`);
}
assert.equal(Object.keys(scenePlaces).length, used.size, 'the place table must have no orphan scenes');
for (const level of Object.keys(sceneLevels)) {
  assert.ok(levelDots(level).length > 0, `level ${level} has no dots to draw`);
}
assert.equal(regionDots().length, 10, 'the realm map draws all ten regions');
console.log(`places: ${used.size} scenes, ${Object.keys(sceneLevels).length} levels, ${regionDots().length} regions`);

// ---- 二、浏览器 ----
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROME_PATH ?? (existsSync(chrome) ? chrome : undefined),
});

/** 一次性把转场 DOM 读成普通对象。waitForFunction 在条件成立的那一帧返回，
 *  避免「等到了又自己收起来」造成的竞态。 */
async function capture(page, scene, timeout = 15000) {
  const handle = await page.waitForFunction(want => {
    const e = document.querySelector('[data-testid=scene-locator]');
    if (!e || e.dataset.scene !== want) return false;
    const realm = e.querySelector('g[data-layer=realm]');
    const detail = e.querySelector('g[data-layer=detail]');
    return {
      dataset: { ...e.dataset },
      realmOpacity: Number(realm?.getAttribute('opacity')),
      realmZoom: Number(realm?.getAttribute('data-zoom')),
      detailOpacity: Number(detail?.getAttribute('opacity')),
      detailDots: detail?.querySelectorAll('.locator-dot').length ?? 0,
      detailLabels: detail ? [...detail.querySelectorAll('.locator-dot-label')].map(t => t.textContent?.trim()) : [],
      texts: [...e.querySelectorAll('text')].map(t => t.textContent?.trim()),
      crumbs: [...e.querySelectorAll('.locator-crumbs span')].map(s => s.textContent?.trim()),
      lit: e.querySelectorAll('.locator-crumbs span.lit').length,
      hasSkip: !!e.querySelector('.locator-skip'),
    };
  }, scene, { timeout, polling: 40 });
  return handle.jsonValue();
}

async function boot(reducedMotion) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE ' + m.text()); });
  await page.goto(URL);
  await page.locator('.loading-screen').waitFor({ state: 'detached', timeout: 30000 });
  await page.waitForFunction(() => !!document.querySelector('.dialogue-text')?.textContent?.trim(), undefined, { timeout: 60000 });
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.locator('.loading-screen').waitFor({ state: 'detached', timeout: 30000 });
  await page.waitForFunction(() => !!document.querySelector('.dialogue-text')?.textContent?.trim(), undefined, { timeout: 60000 });
  await page.locator('.game-map[data-scene-ready]').waitFor({ timeout: 30000 });
  return { context, page, errors };
}

async function toggleSetting(page, on) {
  await page.getByRole('button', { name: '设置' }).click();
  const box = page.getByRole('checkbox', { name: '换场景时显示大地图定位' });
  await box.waitFor({ timeout: 8000 });
  if (await box.isChecked() !== on) await box.click();
  await page.getByRole('button', { name: '关闭弹窗' }).click();
  await page.locator('dialog[open]').waitFor({ state: 'detached', timeout: 8000 });
}

let context;
try {
  // ---- reduced-motion：静态终点，断言不依赖时间 ----
  const booted = await boot('reduce');
  context = booted.context;
  const { page, errors } = booted;
  const loc = page.locator('[data-testid=scene-locator]');

  // 封面还盖着时不该白播一次（封面 z-index 58 会把它压住）。
  await page.locator('.leaf-sheet.leaf-cover').waitFor({ timeout: 10000 });
  assert.equal(await loc.count(), 0, 'the locator must wait until the chapter cover is folded away');
  await page.locator('.leaf-cover .leaf-open').click();
  await dismissPickup(page);

  // 第一回开篇：myth 是天下层场景，只能推镜、不能下钻。
  const opening = await capture(page, 'myth');
  assert.equal(opening.dataset.reason, 'chapter');
  assert.equal(opening.dataset.level, 'realm');
  assert.equal(opening.dataset.drill, 'no');
  assert.equal(opening.dataset.reduced, 'yes');
  assert.equal(opening.dataset.progress, '1.000', 'reduced-motion renders the static endpoint');
  assert.equal(opening.crumbs.length, 2, 'realm scenes get a region crumb so the second beat still lights up');
  assert.ok(opening.crumbs[1].includes('大荒山'));
  assert.ok(opening.texts.includes('大荒山 · 青埂峰'), 'the arrival label must name the place');
  assert.equal(opening.realmOpacity, 1);
  assert.ok(opening.realmZoom > 1.15, `realm scenes must push the camera in, got zoom ${opening.realmZoom}`);
  assert.equal(opening.detailOpacity, 0, 'a realm scene must never switch to the empty detail dot field');
  assert.equal(opening.hasSkip, true);
  console.log('opening: chapter / realm / push-in, no empty drill-down');

  // 不吞指针、不改引擎：顶栏按钮仍可点，小场景图仍算可见（用 opacity 而非 visibility）。
  const hit = await page.evaluate(() => {
    const b = [...document.querySelectorAll('nav button')].find(x => x.textContent?.trim().includes('继续剧情'));
    if (!b) return { same: false, reason: 'no continue button' };
    const r = b.getBoundingClientRect();
    const el = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
    return { same: el === b || b.contains(el), tag: el?.tagName, cls: el?.getAttribute('class') ?? '' };
  });
  assert.ok(hit.same, `the locator must not swallow clicks on the header: ${JSON.stringify(hit)}`);
  assert.equal(await page.locator('.game-map[data-scene-ready]').isVisible(), true,
    'the underlying stage stays visible (opacity only) so existing tests keep passing');

  // 跳过按钮与自动收起。
  await page.locator('.locator-skip').click();
  await loc.waitFor({ state: 'detached', timeout: 5000 });
  await seekSection(page, 'c1-dream');
  await dismissPickup(page);
  await capture(page, 'dream');
  await loc.waitFor({ state: 'detached', timeout: 8000 });
  console.log('skip button and auto-dismiss both work');

  // 府内层下钻：第 3 回 reunion 的 entry 在荣国府总览。
  await seekSection(page, 'reunion');
  await dismissLeaf(page, false, true);
  await dismissPickup(page);
  const drill = await capture(page, 'entry');
  assert.equal(drill.dataset.level, 'rongguo');
  assert.equal(drill.dataset.drill, 'yes');
  assert.equal(drill.detailOpacity, 1, 'the detail layer is fully shown at the endpoint');
  assert.equal(drill.realmOpacity, 0, 'the realm layer fades out on a real drill-down');
  assert.ok(drill.detailDots >= 10, `rongguo should draw its whole dot field, got ${drill.detailDots}`);
  assert.ok(drill.detailLabels.length >= 5, `the dot field needs readable place labels, got ${drill.detailLabels.length}`);
  assert.ok(drill.detailLabels.some(t => t && t.includes('贾母院')), 'the target dot must carry its own label');
  assert.ok(drill.detailLabels.every(t => t && t.length <= 9), 'labels are short enough to read without overlap');
  assert.ok(drill.crumbs.length >= 3, 'a drill-down shows the full breadcrumb trail');
  console.log(`drill-down: ${drill.dataset.level} / ${drill.detailDots} dots / ${drill.crumbs.length} crumbs`);

  // 同一回里换场景：reason 必须是 scene，不是 chapter。
  await page.locator('.locator-skip').click();
  await loc.waitFor({ state: 'detached', timeout: 5000 });
  await seekSection(page, 'dinner');
  await dismissPickup(page);
  const sameBook = await capture(page, 'dinner');
  assert.equal(sameBook.dataset.reason, 'scene', 'a scene change inside one book is not a chapter opening');
  assert.equal(sameBook.dataset.drill, 'yes');
  assert.ok(sameBook.dataset.fromScene.length > 0, 'the flying token needs its origin scene');
  await loc.waitFor({ state: 'detached', timeout: 8000 });

  // 设置可关：关掉后换场景不再弹；重新打开时立刻补一次。
  await toggleSetting(page, false);
  assert.equal(await page.evaluate(() => localStorage.getItem('honglou.scene-locator')), 'off');
  await loc.waitFor({ state: 'detached', timeout: 5000 });
  assert.equal(await loc.count(), 0, 'turning the setting off clears an in-flight locator');
  await seekSection(page, 'uncles');
  await dismissPickup(page);
  await page.waitForTimeout(1400);
  assert.equal(await loc.count(), 0, 'no locator while the setting is off');
  await toggleSetting(page, true);
  assert.equal(await page.evaluate(() => localStorage.getItem('honglou.scene-locator')), 'on');
  const reenabled = await capture(page, 'east');
  assert.ok(reenabled.dataset.scene === 'east', 're-enabling shows the current place at once');
  console.log('settings: off suppresses the transition, on replays the current place');
  assert.deepEqual(errors, [], JSON.stringify(errors));
  await context.close();

  // ---- 普通动效：逐帧确认天下层全程不切空图、推镜单调放大 ----
  const animated = await boot('no-preference');
  context = animated.context;
  const p2 = animated.page;
  const loc2 = p2.locator('[data-testid=scene-locator]');
  await p2.locator('.leaf-sheet.leaf-cover').waitFor({ timeout: 10000 });
  await p2.locator('.leaf-cover .leaf-open').click();
  await loc2.waitFor({ timeout: 8000 });
  const frames = await p2.evaluate(async () => {
    const out = [];
    // 转场约 2.1s 推进到终点 + 900ms 停留；采样窗口要盖住整段，
    // 否则最后一帧还没到 p=1 就退出，下面的 「reaches its endpoint」 会假红。
    const end = performance.now() + 3600;
    while (performance.now() < end) {
      const e = document.querySelector('[data-testid=scene-locator]');
      if (e) {
        const realm = e.querySelector('g[data-layer=realm]');
        const detail = e.querySelector('g[data-layer=detail]');
        out.push({
          p: Number(e.dataset.progress),
          zoom: Number(realm?.getAttribute('data-zoom')),
          realm: Number(realm?.getAttribute('opacity')),
          detail: Number(detail?.getAttribute('opacity')),
        });
      }
      await new Promise(r => requestAnimationFrame(r));
    }
    return out;
  });
  assert.ok(frames.length > 12, `expected a real animation, got ${frames.length} frames`);
  assert.ok(frames[0].p < .4, `the first sampled frame should be in beat one, got ${frames[0].p}`);
  assert.ok(Math.max(...frames.map(f => f.p)) > .9, 'the animation must reach its endpoint');
  assert.ok(frames.every(f => f.detail === 0), 'a realm scene must never fade in the empty detail layer');
  assert.ok(frames.every(f => f.realm === 1), 'a realm scene keeps the labelled realm map on screen');
  assert.equal(frames[0].zoom, 1, 'beat one is an unzoomed realm map');
  assert.ok(Math.max(...frames.map(f => f.zoom)) > 1.15, 'beat two pushes the camera in');
  for (let i = 1; i < frames.length; i++) {
    assert.ok(frames[i].zoom + 1e-6 >= frames[i - 1].zoom, 'the push-in must be monotonic');
  }
  assert.equal(await loc2.count(), 0, 'the locator is gone after the animation finishes');
  assert.deepEqual(animated.errors, [], JSON.stringify(animated.errors));
  console.log(`animation: ${frames.length} frames, ${frames[0].p.toFixed(2)} → ${Math.max(...frames.map(f => f.p)).toFixed(2)}, zoom ${frames[0].zoom} → ${Math.max(...frames.map(f => f.zoom)).toFixed(3)}`);

  // ---- ★ 不变量 9：「没加载完就一闪而过」的两道回归锁 ----
  // 上次修复只保证了「等场景图 ready 再播」，但读者仍反馈大地图一闪而过。
  // 两个真因：(1) progress 乘了人物行走速度，2 倍速时整段砍半；
  // (2) 整层 CSS 淡入 .28s，首帧地图是空白的，看着像还没加载。
  // 这里量「挂载 → 卸载」的墙钟时长：无论速度几档都不得低于 2.6s，
  // 且首帧 computed opacity 必须为 1（有内容，不在淡入）。
  for (const speed of [1, 2]) {
    const s = await boot('no-preference');
    await s.page.locator('.leaf-sheet.leaf-cover').waitFor({ timeout: 10000 });
    await s.page.locator('.leaf-cover .leaf-open').click();
    await s.page.waitForFunction(() => !!window.__mapScene, undefined, { timeout: 30000 });
    await s.page.evaluate(v => window.__mapScene.engine.setSpeed(v), speed);
    await s.page.evaluate(() => {
      // 只量新场景 dream 的转场：换场景瞬间旧转场会被 stageReady 收掉，
      // 那几毫秒不是「一闪而过」的对象（见 App 的 stageReady 注释）。
      window.__life = { firstOpacity: null, mount: 0, unmount: 0 };
      const mo = new MutationObserver(() => {
        const e = document.querySelector('[data-testid=scene-locator]');
        if (e && e.dataset.scene === 'dream' && !window.__life.mount) {
          window.__life.mount = performance.now();
          window.__life.firstOpacity = Number(getComputedStyle(e).opacity);
        }
        if (!e && window.__life.mount && !window.__life.unmount) window.__life.unmount = performance.now();
      });
      mo.observe(document.body, { childList: true, subtree: true });
      window.__moLife = mo;
    });
    await seekSection(s.page, 'c1-dream');
    await dismissPickup(s.page);
    await s.page.waitForTimeout(5000);
    const life = await s.page.evaluate(() => { window.__moLife.disconnect(); return window.__life; });
    const shown = Math.round(life.unmount - life.mount);
    assert.ok(shown >= 2600, `locator must stay legible ≥2.6s at speed ${speed}, got ${shown}ms`);
    assert.equal(life.firstOpacity, 1, `the first frame must show the map, not fade in from blank (speed ${speed})`);
    console.log(`legibility: speed ${speed} → ${shown}ms visible, first-frame opacity ${life.firstOpacity}`);
    await s.context.close();
  }

  // ---- ★ 不变量 8：两拍不交叠 ----
  // 天下层与府内层同时半透明 = 两张地图压在一起，地名互相干扰，
  // 读者既看不清天下、也看不清府内，等于两拍都没交代到。
  // 换成府内层场景再逐帧量一遍：两层可见区间不得有交叠。
  await p2.evaluate(() => window.scrollTo(0, 0));
  await seekSection(p2, 'reunion');
  await dismissLeaf(p2, false, true);
  await dismissPickup(p2);
  const drillFrames = await p2.evaluate(async () => {
    const out = [];
    const end = performance.now() + 3200;
    while (performance.now() < end) {
      const e = document.querySelector('[data-testid=scene-locator]');
      if (e && e.dataset.scene === 'entry') {
        const realm = e.querySelector('g[data-layer=realm]');
        const detail = e.querySelector('g[data-layer=detail]');
        out.push({
          p: Number(e.dataset.progress),
          realm: Number(realm?.getAttribute('opacity')),
          detail: Number(detail?.getAttribute('opacity')),
        });
      }
      await new Promise(r => requestAnimationFrame(r));
    }
    return out;
  });
  assert.ok(drillFrames.length > 12, `expected a real drill-down animation, got ${drillFrames.length} frames`);
  const overlapped = drillFrames.filter(f => f.realm > 0.05 && f.detail > 0.05);
  assert.equal(overlapped.length, 0,
    `the two beats must not cross-fade on top of each other, but ${overlapped.length} frames had both layers visible`);
  assert.ok(drillFrames.some(f => f.realm > 0.9), 'beat one must show the realm map');
  assert.ok(drillFrames.some(f => f.detail > 0.9), 'beat two must show the estate dot field');
  assert.ok(drillFrames.some(f => f.realm <= 0.05 && f.detail <= 0.05),
    'there must be a clean gap between the two beats');
  console.log(`non-overlap: ${drillFrames.length} frames, realm-only ${drillFrames.filter(f => f.realm > .05 && f.detail <= .05).length}, detail-only ${drillFrames.filter(f => f.detail > .05 && f.realm <= .05).length}, gap ${drillFrames.filter(f => f.realm <= .05 && f.detail <= .05).length}, overlap ${overlapped.length}`);

  // ---- ★ 不变量 7：转场必须等这个场景的图画完 ----
  // 用户反馈：「现在大地图还没加载出来的时候，就开始播放动画了。然后直接进入
  // 场景图。到时大地图都看不到。」——转场一开始就把小场景图藏掉，
  // 底下若还没画完，读者从头到尾没看清一张大地图。
  //
  // ★ 这里必须用 MutationObserver 量「转场元素**挂载的那一刻**」，不能用定时采样。
  // 定时采样（哪怕 30ms 一帧）会漏掉一个几毫秒的窗口：旧图刚卸、新图未画时，
  // 布尔判据 sceneReady 会短暂为 false，而那恰恰是转场错误地抢跑的那一瞬。
  // 实测回退布尔判据后，转场在 t=152ms 挂载，而舞台此时 data-scene-ready
  // 还是「无」——底下是空白。9ms 后转场被收掉又重放。
  await p2.waitForTimeout(1500);
  await p2.evaluate(() => {
    window.__mounts = [];
    const mo = new MutationObserver(muts => {
      for (const m of muts) {
        for (const n of m.addedNodes) {
          if (n.nodeType !== 1) continue;
          const loc = n.matches?.('[data-testid=scene-locator]')
            ? n : n.querySelector?.('[data-testid=scene-locator]');
          if (!loc) continue;
          const map = document.querySelector('.game-map');
          window.__mounts.push({
            scene: loc.dataset.scene,
            ready: map?.getAttribute('data-scene-ready') ?? null,
            hasAttr: map?.hasAttribute('data-scene-ready') ? 1 : 0,
          });
        }
      }
    });
    mo.observe(document.body, { childList: true, subtree: true });
    window.__stopMounts = () => mo.disconnect();
  });
  await seekSection(p2, 'dinner');
  await dismissLeaf(p2, false, true);
  await dismissPickup(p2);
  await p2.waitForTimeout(5500);
  const mounts = await p2.evaluate(() => { window.__stopMounts(); return window.__mounts; });
  const dinnerMounts = mounts.filter(m => m.scene === 'dinner');
  assert.ok(dinnerMounts.length >= 1, `expected the transition to mount, got ${JSON.stringify(mounts)}`);
  const staleMounts = dinnerMounts.filter(m => m.hasAttr !== 1 || m.ready !== m.scene);
  assert.equal(staleMounts.length, 0,
    `the transition must mount only after its own scene's map is ready, but ${staleMounts.length} mount(s) showed another scene (or none): ${JSON.stringify(staleMounts)}`);
  console.log(`timing: the transition mounted ${dinnerMounts.length} time(s), always with its own scene ready`);

  console.log('Passed: scene locator — 45 scenes mapped, chapter + scene triggers, realm push-in vs estate drill-down, skip/auto-dismiss/settings, no swallowed clicks, animated frames verified, beats never overlap, transition waits for its own map.');
} catch (e) {
  console.error('scene-locator failed:', e.message);
  throw e;
} finally {
  await context?.close().catch(() => {});
  await browser.close();
}
