/** 「原文与改编」弹窗的覆盖度验收。
 *
 *  这段说明是给读者看的「这本书改了什么」：从前十九回写到前三十回，
 *  第 20-30 回的十一段是 2026-11-25 才补上的。补写时凭记忆写的一版里，
 *  有好几处引文在底本里查不到（黛玉的灯谜其实不是「更香」，「青埂峰下，
 *  别来无恙」也不是底本原话）。所以这条测试把说明里的每一处引文
 *  都拿到底本里逐字核一遍 —— 写错一个就红。
 *
 *  另外钉住两件事：说明里不许出现「前十九回」这种过期口径；
 *  第 20 至 30 回每一回都要有自己的段落。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync, readFileSync} from 'node:fs';
import {dismissPickup, dismissLeaf} from './lib/pickup.mjs';

const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROME_PATH || (existsSync(chrome) ? chrome : undefined),
});
const page = await browser.newPage({viewport: {width: 1440, height: 900}});
const errors = [];
page.on('pageerror', e => errors.push(e.message));

const BASE = process.env.TEST_URL || 'http://127.0.0.1:5173/';
await page.goto(BASE, {waitUntil: 'load'});
await dismissPickup(page);
await page.locator('.loading-screen').waitFor({state: 'detached', timeout: 30000});
// 封面是压住全屏的弹层，不先翻开它，顶栏的设置按钮点不动
await dismissLeaf(page, false, true);
await page.waitForFunction(() => !!document.querySelector('.dialogue-text')?.textContent?.trim(),
  undefined, {timeout: 30000});
await dismissLeaf(page, false, true);

// 打开设置 → 原文与改编
await page.getByRole('button', {name: '设置', exact: true}).click();
await page.getByRole('button', {name: '原文与改编'}).click();
await page.locator('.source-body').waitFor({timeout: 20000});

const body = (await page.locator('.source-body').textContent()) || '';
assert.ok(body.length > 3000, `来源说明应有实质内容，实际长度 ${body.length}`);

// 口径不许停留在十九回
assert.ok(!body.includes('前十九回'), '来源说明仍写着「前十九回」，口径未更新');
assert.ok(body.includes('前三十回'), '来源说明未声明覆盖前三十回');

// 第 20 至 30 回每一回都要有自己的段落
const CN = ['二十', '二十一', '二十二', '二十三', '二十四', '二十五', '二十六', '二十七', '二十八', '二十九', '三十'];
for (const cn of CN) {
  assert.ok(body.includes(`第${cn}回`), `来源说明缺少第${cn}回的段落`);
}

// 每一处引号里的引文都要在对应底本里逐字可查
const quotes = [...body.matchAll(/「([^」]{2,60})」/g)].map(m => m[1]);
assert.ok(quotes.length >= 20, `引文太少（${quotes.length}），说明被削掉了`);

const normalize = (s) => s.replace(/\s+/g, '')
  .replace(/[“”]/g, '「').replace(/[‘’]/g, '「')
  .replace(/『/g, '「').replace(/』/g, '」');

const sources = [];
for (let n = 20; n <= 30; n++) {
  sources.push(normalize(readFileSync(`docs/chapter${String(n).padStart(2, '0')}-source.txt`, 'utf8')));
}
const all = sources.join('');

// 前十九回的引文在更早的底本里，也要能查到
const early = [];
for (let n = 1; n <= 19; n++) {
  try {
    early.push(normalize(readFileSync(`docs/chapter${String(n).padStart(2, '0')}-source.txt`, 'utf8')));
  } catch { /* 早期底本文件名可能不同 */ }
}
const haystack = all + early.join('');

// 「原文段落起句」是界面自带的标签，不是引文
const LABEL = '原文段落起句';
const missing = quotes.filter(q => q !== LABEL && !haystack.includes(normalize(q)));
assert.deepEqual(missing, [],
  `以下引文在底本里查不到（可能是凭记忆写的转述）：${missing.join(' | ')}`);

// 底本版本说明也要跟上
assert.ok(body.includes('第二十五至三十回'), '来源说明未交代第 25-30 回的底本版本');

assert.deepEqual(errors, [], `浏览器不应报错：${errors.join(' | ')}`);
console.log(`OK 来源说明：${body.length} 字，覆盖第 20-30 回全部段落；`
  + `${quotes.length} 处引文全部在底本中逐字可查`);
await browser.close();
