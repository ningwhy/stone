/** 司棋的定向视觉验收。
 *
 *  司棋的首版立绘被渲染成男性青年，2026-11-25 重做。这条测试守住的不是
 *  「有一张叫司棋的图」，而是「游戏里站在迎春房位置上的那个身影确实是女的、
 *  而且穿的正是第七十一回写明的红裙」。
 *
 *  两条证据链：
 *  1. DOM 里立绘是一个 <img class="portrait-painted">，它的 src 带 manifest 的 hash。
 *     断言这个 src 的 hash 等于 manifest 里司棋立绘当前的 hash —— 这条钉死了
 *     「浏览器拿到的是重做后的字节」，而不是同名旧图被缓存。
 *  2. 把这张运行时图片解码进 canvas，按红裙阈值统计裙摆像素 —— 这条钉死了
 *     「字节确实是红裙」，而不是「图存在但画的不是」。
 *  首版错图下身是灰裙（冷灰，R-B 很小），新版是红裙（暖红，R-B > 40）。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync, mkdirSync, writeFileSync} from 'node:fs';
import {dismissPickup, dismissLeaf, clickSkipIfShown} from './lib/pickup.mjs';
import {seekSection} from './lib/toc.mjs';
import manifest from '../public/assets/rongguo/manifest.json' with {type: 'json'};

const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROME_PATH || (existsSync(chrome) ? chrome : undefined),
});
const context = await browser.newContext({viewport: {width: 1440, height: 900}, reducedMotion: 'reduce'});
const page = await context.newPage();
const errors = [];
page.on('pageerror', e => errors.push(e.message));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
mkdirSync('artifacts', {recursive: true});

const BASE = process.env.TEST_URL || 'http://127.0.0.1:5173/';

await page.goto(BASE, {waitUntil: 'load'});
await dismissPickup(page);
await page.locator('.loading-screen').waitFor({state: 'detached', timeout: 30000});
// 封面是压住全屏的弹层，不先翻开它，后面的目录按钮点不动
await dismissLeaf(page, false, true);
for (let i = 0; i < 4; i++) await clickSkipIfShown(page);
await page.waitForFunction(() => !!document.querySelector('.dialogue-text')?.textContent?.trim(),
  undefined, {timeout: 30000});
await dismissLeaf(page, false, true);

// 跳到司棋说话的那一段（第27回「红玉打听凤姐」）
await seekSection(page, 'c27-wen');
await page.locator('.game-map[data-scene-ready]').waitFor({timeout: 30000});
await dismissLeaf(page, false, true);

// 推进到司棋的台词节点：说话人变成「司棋」为止
const speaker = () => page.locator('.speaker-line h2').textContent().catch(() => '');
let found = false;
for (let i = 0; i < 60; i++) {
  const s = (await speaker()) || '';
  if (s.includes('司棋')) { found = true; break; }
  await page.keyboard.press('Space');
  await page.waitForTimeout(200);
}
assert.ok(found, '第27回应能推进到司棋的台词节点');

const text = (await page.locator('.dialogue-text').textContent()) || '';
assert.ok(text.includes('没理论'), `司棋的台词应为底本原文「没理论」，实际为「${text}」`);

await page.waitForTimeout(800);

// 抓运行时真正加载的立绘 <img>
const painted = await page.evaluate(() => {
  const imgs = [...document.querySelectorAll('img.portrait-painted')];
  return imgs.map(i => ({
    src: i.currentSrc || i.src,
    alt: i.alt,
    naturalWidth: i.naturalWidth,
    naturalHeight: i.naturalHeight,
    complete: i.complete,
  }));
});
assert.ok(painted.length > 0, '对话面板里应有立绘 <img>');
const siqiImg = painted.find(p => p.alt.includes('司棋')) ?? painted[0];
assert.ok(siqiImg.alt.includes('司棋') || painted.length === 1,
  `应能找到司棋的立绘，实际 alt 为 ${JSON.stringify(painted.map(p => p.alt))}`);

// 证据 1：src 的 hash 必须等于 manifest 里司棋立绘当前的 hash
const manifestHash = manifest.assets['siqi-portrait'].hash;
assert.ok(siqiImg.src.includes(manifestHash),
  `运行时加载的司棋立绘 hash 应为 ${manifestHash}，实际 src=${siqiImg.src}`);
assert.ok(siqiImg.complete && siqiImg.naturalWidth > 0,
  `司棋立绘应真的加载完成，实际 complete=${siqiImg.complete} w=${siqiImg.naturalWidth}`);

// 证据 2：把这张运行时图片解码进 canvas，统计裙摆的暖红像素
const sample = await page.evaluate(async (url) => {
  const img = new Image();
  img.crossOrigin = 'anonymous';
  await new Promise((ok, no) => { img.onload = ok; img.onerror = () => no(new Error('decode failed')); img.src = url; });
  const w = img.naturalWidth, h = img.naturalHeight;
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d', {willReadFrequently: true});
  ctx.drawImage(img, 0, 0);
  const d = ctx.getImageData(0, 0, w, h).data;
  let reds = 0, rs = 0, gs = 0, bs = 0;
  let minX = w, maxX = -1, minY = h, maxY = -1;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      if (d[i + 3] < 100) continue;
      const r = d[i], g = d[i + 1], b = d[i + 2];
      // 红裙的暗红：R 远高于 G 与 B。阈值必须同时压住 G，
      // 否则肤色（R 165 G 116 B 93）也会混进来，把 bbox 拉到头部。
      if (r > 60 && r < 200 && r - b > 55 && r - g > 40) {
        reds++; rs += r; gs += g; bs += b;
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
      }
    }
  }
  if (!reds) return {error: 'no red pixels', w, h};
  // 按行统计红像素落在哪一段：裙摆应占住下半身
  const bands = [];
  for (let y0 = 0; y0 < h; y0 += h / 4) {
    const y1 = Math.min(h, Math.round(y0 + h / 4));
    let n = 0;
    for (let y = y0; y < y1; y++) for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 4;
      if (d[i + 3] < 100) continue;
      const r = d[i], g = d[i + 1], b = d[i + 2];
      if (r > 60 && r < 200 && r - b > 55 && r - g > 40) n++;
    }
    bands.push(n);
  }
  return {
    w, h, reds,
    avg: [rs / reds, gs / reds, bs / reds],
    bbox: [minX, minY, maxX, maxY],
    bands,
  };
}, siqiImg.src);

assert.ok(!sample.error, `应能从运行时立绘上取到裙摆颜色：${sample.error}`);
assert.ok(sample.reds > 10000, `运行时立绘上的红裙像素太少（${sample.reds}），可能不是新图`);
const [r, g, b] = sample.avg;
assert.ok(r - b > 55 && r - g > 40,
  `司棋裙摆应为暖红（R-B>55, R-G>40），实际均色 ${sample.avg.map(v => v.toFixed(1))}`);
// 红裙要占住立绘的下半身，而不是只有头上一点红
assert.ok(sample.bands[2] > 2000 && sample.bands[3] > 2000,
  `红裙应铺满立绘下半部（四段分布 ${sample.bands}），实际只在头部有点红`);
assert.ok(sample.bands[1] < sample.bands[2] / 4,
  `红裙重心应在下半身，四段分布 ${sample.bands}`);

writeFileSync('artifacts/ch27-siqi-portrait-runtime.json',
  JSON.stringify({src: siqiImg.src, manifestHash, sample}, null, 1));
await page.locator('.game-map').screenshot({path: 'artifacts/ch27-siqi-portrait.png'});

assert.deepEqual(errors, [], `浏览器不应报错：${errors.join(' | ')}`);
console.log(`OK 司棋：台词「${text.trim()}」；运行时立绘 ${sample.w}x${sample.h}（hash ${manifestHash}）；`
  + `裙摆均色 ${sample.avg.map(v => v.toFixed(1))}，红像素 ${sample.reds}，bbox ${sample.bbox}`);
await browser.close();
