// 定位到具体段落内的第 N 个节点截图：段落下拉只到段首，而台基与陈设的问题
// （配殿有没有东西、宴席是不是散着摆）常常出现在段中，必须真的走到那一步看。
// 用法：node tests/c5-node-shots.mjs c5-scroll:4 c5-banquet:6
import { chromium } from 'playwright';
import { existsSync, mkdirSync } from 'node:fs';
import { seekSection } from './lib/toc.mjs';
import { clickSkipIfShown } from './lib/pickup.mjs';
const exe = process.env.CHROME_PATH || (existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome') ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : undefined);
const browser = await chromium.launch({ headless: true, executablePath: exe });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
mkdirSync('artifacts', { recursive: true });
const settle = async () => {
  await page.locator('.loading-screen').waitFor({ state: 'detached', timeout: 60000 });
  await clickSkipIfShown(page,12,50);
  await page.waitForFunction(() => !!document.querySelector('.dialogue-text')?.textContent?.trim(), undefined, { timeout: 60000 });
  await page.locator('.game-map[data-scene-ready]').waitFor({ timeout: 60000 });
  // A node that hands out a collectible opens a modal over the whole stage; dismiss it or
  // every screenshot of that beat is a card instead of the room it is supposed to show.
  for (const name of ['收下', '收下并打开背包', '关闭']) {
    const b = page.getByRole('button', { name, exact: true });
    if (await b.count() && await b.first().isVisible().catch(() => false)) { await b.first().click(); await page.waitForTimeout(120); }
  }
  await page.waitForTimeout(450);
};
await page.goto(process.env.TEST_URL ?? 'http://127.0.0.1:5173');
await settle();
const jobs = process.argv.slice(2).map(a => { const [s, n] = a.split(':'); return { s, n: Number(n ?? 0) }; });
const report = [];
for (const { s, n } of jobs) {
  try {
    await seekSection(page, s);
    await settle();
    for (let i = 0; i < n; i++) {
      await page.getByRole('button', { name: /继续剧情/ }).click();
      await settle();
    }
    const id = (await page.locator('.dialogue-text').textContent())?.trim().slice(0, 34) ?? '';
    const node = await page.evaluate(() => document.querySelector('[data-step-id]')?.dataset.stepId ?? document.body.innerText.match(/C\d\d-\d\d\d/)?.[0] ?? '');
    await page.screenshot({ path: `artifacts/node-${s}-${n}.png`, fullPage: true });
    report.push(`OK  ${s}+${n}  ${node}  ${id}`);
  } catch (e) {
    report.push(`ERR ${s}+${n}  ${e.message.split('\n')[0]}`);
  }
}
console.log(report.join('\n'));
console.log('TOTAL ERRORS:', errors.length);
if (errors.length) console.log(errors.slice(0, 10).join('\n'));
await ctx.close();
await browser.close();
