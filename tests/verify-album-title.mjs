/** 验收：构建产物里的图鉴标题与末回新角色在册。
 *
 *  跑在 preview（dist 产物）上，不是 dev server —— 要验的是**部署出去的那份字节**。
 *  两件事：
 *  1. 面板标题写「前N回 · 人物图鉴」（中文数字，不是「前N回」）；
 *  2. 末回的新角色在册，且两张立绘/立绘特写都真的画出来了（naturalWidth>0）。
 *
 *  ★ 标题里的回次**不写死**：`src/App.tsx` 的 `bookScope` 是按 `bookNames`
 *    派生、再由 `src/cnNumber.ts` 转成中文数字的，所以断言也从同一份数据
 *    算出该显示什么。写死「第22回」的话，每加一回这个脚本就会红一次，
 *    而红的原因跟被测的东西毫无关系。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,mkdirSync} from 'node:fs';
import {bookNames} from '../src/story.ts';
import {cnNumber} from '../src/cnNumber.ts';

const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(existsSync(chrome)?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage();
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
mkdirSync('artifacts',{recursive:true});

try{
  await page.goto(process.env.TEST_URL??'http://127.0.0.1:4173');
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.evaluate(()=>localStorage.clear());
  await page.reload();
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});

  // 收掉封面，露出设置。
  await page.locator('.leaf-cover .leaf-open').click().catch(()=>{});
  await page.waitForTimeout(300);
  await page.getByRole('button',{name:'设置'}).click();
  await page.locator('dialog[open]').waitFor({timeout:20000});
  await page.getByRole('button',{name:'人物图鉴'}).click();
  await page.locator('.cast-gallery').waitFor({timeout:20000});

  const title=await page.locator('dialog h2').textContent();
  // 标题里的回次按数据算：末回 = bookNames 里最大的那个回次。
  const lastBook=Math.max(...Object.keys(bookNames).map(Number));
  const expectedScope=`前${cnNumber(lastBook)}回`;
  assert.ok(title.includes(expectedScope),`the album title must read 「${expectedScope}」, got ${title}`);
  assert.ok(!/\d/.test(title.split('·')[0]),`the book scope must not contain arabic digits, got ${title}`);
  console.log('面板标题:',title);

  const names=await page.locator('.cast-gallery article strong').allTextContents();
  // 末回的新角色必须在册。第 30 回新登场：龄官。
  // 这里跟着末回走：再加回时把这里换成那一回的新角色。
  const NEW_OF_LAST_BOOK=['龄官'];
  for(const name of NEW_OF_LAST_BOOK){
    assert.ok(names.includes(name),`${name} must be in the album, got ${names.length} names`);
  }
  console.log('图鉴人数:',names.length,`（含${NEW_OF_LAST_BOOK.join('、')}）`);

  // 末回新角色的立绘要真的画出来。
  // 图鉴是长列表，图片带 loading="lazy"：不滚到视口里它压根不会加载，
  // naturalWidth 自然是 0——那是懒加载，不是图没画出来。
  const sample=NEW_OF_LAST_BOOK[0];
  await page.evaluate(name=>{
    const card=[...document.querySelectorAll('.cast-gallery article')]
      .find(a=>a.querySelector('strong')?.textContent===name);
    card?.scrollIntoView({block:'center'});
  },sample);
  await page.waitForFunction(name=>{
    const card=[...document.querySelectorAll('.cast-gallery article')]
      .find(a=>a.querySelector('strong')?.textContent===name);
    const img=card?.querySelector('img');
    return !!img&&img.complete&&img.naturalWidth>0;
  },sample,{timeout:20000});
  const imgs=await page.evaluate(name=>{
    const card=[...document.querySelectorAll('.cast-gallery article')]
      .find(a=>a.querySelector('strong')?.textContent===name);
    return [...card.querySelectorAll('img')].map(i=>({src:i.getAttribute('src'),w:i.naturalWidth,h:i.naturalHeight}));
  },sample);
  assert.ok(imgs.length>=1,`${sample} must have a portrait in the album`);
  for(const i of imgs)assert.ok(i.w>0&&i.h>0,`${sample}'s portrait must be painted, got ${i.src} ${i.w}x${i.h}`);
  console.log(`${sample}立绘:`,imgs.map(i=>`${i.src} ${i.w}x${i.h}`).join(' | '));

  await page.screenshot({path:'artifacts/album-title-verify.png',fullPage:true});
  assert.equal(errors.length,0,JSON.stringify(errors));
  console.log(`Passed: 面板标题「${expectedScope} · 人物图鉴」，${NEW_OF_LAST_BOOK.join('、')}在册且立绘已绘出。`);
}finally{
  await context.close();
  await browser.close();
}
