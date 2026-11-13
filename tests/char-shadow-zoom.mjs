// 放大相机到角色脚部，判人物接触阴影在原生分辨率下是否接得上地面、深浅是否自然。
import { chromium } from 'playwright';
import { existsSync, mkdirSync } from 'node:fs';
import { dismissPickup, dismissLeaf, clickSkipIfShown} from './lib/pickup.mjs';
const exe = process.env.CHROME_PATH || (existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome') ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : undefined);
const URL = process.env.TEST_URL ?? 'http://127.0.0.1:5173';
const browser = await chromium.launch({ headless: true, executablePath: exe });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
const page = await ctx.newPage();
mkdirSync('artifacts/char-art', { recursive: true });
const settle = async () => {
  await page.locator('.loading-screen').waitFor({ state: 'detached', timeout: 60000 });
  await clickSkipIfShown(page,14,45);
  await page.waitForFunction(() => !!document.querySelector('.dialogue-text')?.textContent?.trim(), undefined, { timeout: 60000 });
  await page.locator('.game-map[data-scene-ready]').waitFor({ timeout: 60000 });
  await page.waitForTimeout(450);
  await dismissLeaf(page, false, true);
};
await page.goto(URL);
await settle();
await page.evaluate(() => window.__mapScene.engine.seek('C06-083'));
await settle();
await dismissPickup(page); await dismissLeaf(page, false, true);
await page.waitForTimeout(500);

// 取板儿世界坐标，放大相机对准其脚部。
const focus = await page.evaluate(() => {
  const scene = window.__mapScene;
  const v = scene.actorViews.get('ban_er');
  const cam = scene.cameras.main;
  cam.setZoom(2.8);
  cam.centerOn(v.x, v.y - 10);
  return { x: v.x, y: v.y, zoom: cam.zoom };
});
await page.waitForTimeout(400);
await page.screenshot({ path: 'artifacts/char-art/shadow-baner-zoom.png' });

// 同样对准平儿，看成人阴影。
await page.evaluate(() => {
  const scene = window.__mapScene;
  const v = scene.actorViews.get('ping_er');
  scene.cameras.main.centerOn(v.x, v.y - 10);
});
await page.waitForTimeout(400);
await page.screenshot({ path: 'artifacts/char-art/shadow-pinger-zoom.png' });

// 数据：人物阴影椭圆（alpha .16）vs 家具阴影（alpha .07/.09）的“落地感”量化。
// 采样板儿脚底中心点上下各 3px 的明度，看阴影是否让脚底比周围地面暗。
const sample = await page.evaluate(() => {
  const scene = window.__mapScene;
  const canvas = scene.game.canvas;
  const cctx = canvas.getContext('2d');
  const cam = scene.cameras.main;
  const v = scene.actorViews.get('ban_er');
  // 世界→屏幕
  const sx = (v.x - cam.worldView.x) * cam.zoom;
  const sy = (v.y - cam.worldView.y) * cam.zoom;
  const px = Math.round(sx), py = Math.round(sy);
  const lum = (x, y) => {
    if (x < 0 || y < 0 || x >= canvas.width || y >= canvas.height) return null;
    const d = cctx.getImageData(x, y, 1, 1).data;
    return Math.round(0.299 * d[0] + 0.587 * d[1] + 0.114 * d[2]);
  };
  return {
    footCenter: lum(px, py),
    justAboveFoot: lum(px, py - 4),
    justBelowFoot: lum(px, py + 6),
    leftOfFoot: lum(px - 14, py + 2),
    rightOfFoot: lum(px + 14, py + 2),
  };
});
console.log('板儿脚底明度采样(0黑~255白)：', JSON.stringify(sample));
console.log('脚底中心 vs 左右两侧（阴影应使中心更暗）：', sample.footCenter, 'vs', sample.leftOfFoot, '/', sample.rightOfFoot);
await ctx.close(); await browser.close();
