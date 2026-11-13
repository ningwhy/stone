/** 验收：构建产物里的图鉴标题与贾兰在册。
 *
 *  跑在 preview（dist 产物）上，不是 dev server —— 要验的是**部署出去的那份字节**。
 *  两件事：
 *  1. 面板标题写「前二十二回 · 人物图鉴」，不是「前22回」；
 *  2. 贾兰在册，且两张立绘/立绘特写都真的画出来了（naturalWidth>0）。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,mkdirSync} from 'node:fs';

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
  assert.ok(title.includes('前二十二回'),`the album title must read 「前二十二回」, got ${title}`);
  assert.ok(!/\d/.test(title.split('·')[0]),`the book scope must not contain arabic digits, got ${title}`);
  console.log('面板标题:',title);

  const names=await page.locator('.cast-gallery article strong').allTextContents();
  assert.ok(names.includes('贾兰'),`贾兰 must be in the album, got ${names.length} names`);
  console.log('图鉴人数:',names.length,'（含贾兰）');

  // 贾兰的两张图都要真的画出来。
  // 图鉴是长列表，图片带 loading="lazy"：不滚到视口里它压根不会加载，
  // naturalWidth 自然是 0——那是懒加载，不是图没画出来。
  await page.evaluate(()=>{
    const card=[...document.querySelectorAll('.cast-gallery article')]
      .find(a=>a.querySelector('strong')?.textContent==='贾兰');
    card?.scrollIntoView({block:'center'});
  });
  await page.waitForFunction(()=>{
    const card=[...document.querySelectorAll('.cast-gallery article')]
      .find(a=>a.querySelector('strong')?.textContent==='贾兰');
    const img=card?.querySelector('img');
    return !!img&&img.complete&&img.naturalWidth>0;
  },undefined,{timeout:20000});
  const imgs=await page.evaluate(()=>{
    const card=[...document.querySelectorAll('.cast-gallery article')]
      .find(a=>a.querySelector('strong')?.textContent==='贾兰');
    return [...card.querySelectorAll('img')].map(i=>({src:i.getAttribute('src'),w:i.naturalWidth,h:i.naturalHeight}));
  });
  assert.ok(imgs.length>=1,`贾兰 must have a portrait in the album`);
  for(const i of imgs)assert.ok(i.w>0&&i.h>0,`贾兰's portrait must be painted, got ${i.src} ${i.w}x${i.h}`);
  console.log('贾兰立绘:',imgs.map(i=>`${i.src} ${i.w}x${i.h}`).join(' | '));

  await page.screenshot({path:'artifacts/album-title-verify.png',fullPage:true});
  assert.equal(errors.length,0,JSON.stringify(errors));
  console.log('Passed: 面板标题「前二十二回 · 人物图鉴」，贾兰在册且立绘已绘出。');
}finally{
  await context.close();
  await browser.close();
}
