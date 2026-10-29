import { chromium } from 'playwright';
import { existsSync, mkdirSync } from 'node:fs';
import { seekSection } from './lib/toc.mjs';
const exe = process.env.CHROME_PATH || (existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome') ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : undefined);
const browser = await chromium.launch({ headless: true, executablePath: exe });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
mkdirSync('artifacts', { recursive: true });
const read = async () => {
  await page.locator('.loading-screen').waitFor({ state: 'detached', timeout: 60000 });
  for (let i = 0; i < 12; i++) { const b = page.getByRole('button', { name: '跳过移动', exact: true }); if (await b.isVisible()) { await b.click(); await page.waitForTimeout(50); } }
  await page.waitForFunction(() => !!document.querySelector('.dialogue-text')?.textContent?.trim(), undefined, { timeout: 60000 });
  await page.locator('.game-map[data-scene-ready]').waitFor({ timeout: 60000 });
  await page.waitForTimeout(450);
};
await page.goto(process.env.TEST_URL ?? 'http://127.0.0.1:5173');
await read();
const sections = ['c6-qin', 'c6-grandmother', 'c6-village', 'c6-dawn', 'c6-capital', 'c6-backgate', 'c6-zhourui', 'c6-feng', 'c6-audience', 'c6-gift'];
const report = [];
for (const s of sections) {
  try {
    await seekSection(page, s);
    await read();
    const txt = (await page.locator('.dialogue-text').textContent())?.trim().slice(0, 40) ?? '';
    const spk = (await page.locator('.dialogue-speaker, .speaker').first().textContent().catch(() => '')) ?? '';
    await page.screenshot({ path: `artifacts/sweep-${s}.png`, fullPage: true });
    report.push(`OK  ${s.padEnd(15)} speaker="${spk}" text="${txt}"`);
  } catch (e) {
    report.push(`ERR ${s.padEnd(15)} ${e.message.split('\n')[0]}`);
  }
}
console.log(report.join('\n'));
console.log('TOTAL ERRORS:', errors.length);
if (errors.length) console.log(errors.slice(0, 10).join('\n'));
await ctx.close();
await browser.close();
