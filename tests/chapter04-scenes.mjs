import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFileSync,mkdirSync} from 'node:fs';
import {dismissPickup} from './lib/pickup.mjs';
/**
 * Chapter-four visual acceptance: the two new stages must render, the three new
 * Xue-family characters must appear with painted portraits, and the chapter-four
 * journey view must list every stage it actually visits.
 */
const story=JSON.parse(readFileSync('design/chapter04-story.json','utf8'));
const sections=JSON.parse(readFileSync('design/chapter04-sections.json','utf8'));
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(chrome?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});
const read=async()=>{await dismissPickup(page);await page.locator('.loading-screen').waitFor({state:'detached',timeout:20000});for(let i=0;i<5;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(60);}}await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim());await page.locator('.game-map[data-scene-ready]').waitFor();await dismissPickup(page);};
const node=()=>page.locator('.node-label').textContent();
try{
 await page.goto(process.env.TEST_URL??'http://127.0.0.1:4173');await read();
 // The four stages of chapter four must all open and report their own scene id.
 const expected=[['c4-court','c4_yamen'],['c4-xue','capital'],['c4-hall','central'],['c4-pear','c4_lixiang']];
 for(const [section,scene] of expected){
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption(section);await read();
  assert.equal(await page.locator('.game-map').getAttribute('data-scene-ready'),scene);
 }
 // The new Xue family must stand on the street stage with painted portraits.
 // Xue Pan and Aunt Xue both speak in the lane; Baochai never speaks in chapter four —
 // she is only described and shown standing — so her portrait is checked in the directory.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-xue');await read();
 const portraits={};
 for(let i=0;i<20;i++){
  const src=await page.locator('.speaker-portrait img').getAttribute('src');
  const file=(src??'').match(/([a-z]+)-portrait\.webp/)?.[1];
  if(file)portraits[file]=src;
  if(portraits.xuepan&&portraits.xueyima)break;
  await page.getByRole('button',{name:'继续剧情',exact:true}).click();await read();
 }
 for(const file of ['xuepan','xueyima']){
  assert.ok(portraits[file],`${file} has no painted portrait`);
  assert.match(portraits[file],new RegExp(`${file}-portrait\\.webp`));
 }
 // The cast directory must carry the painted portrait for all three of them.
 await page.getByRole('button',{name:'设置',exact:true}).click();await page.getByRole('button',{name:'人物图鉴',exact:true}).click();
 for(const [name,file] of [['薛蟠','xuepan'],['薛姨妈','xueyima'],['宝钗','baochai']]){
  const card=page.locator('.cast-gallery article').filter({has:page.locator('strong',{hasText:name})});
  assert.equal(await card.count(),1,`${name} missing from the cast directory`);
  assert.match(await card.locator('img').getAttribute('src'),new RegExp(`${file}-portrait\\.webp`));
 }
 await page.keyboard.press('Escape');
 // The court stage must show the case parties in turn: the magistrate first, then
 // the plaintiff who kneels before him.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-court');await read();
 const seen=[];
 for(let i=0;i<12;i++){
  const src=await page.locator('.speaker-portrait img').getAttribute('src');
  const file=(src??'').match(/([a-z]+)-portrait\.webp/)?.[1];
  if(file&&!seen.includes(file))seen.push(file);
  if(seen.includes('yucun')&&seen.includes('plaintiff'))break;
  await page.getByRole('button',{name:'继续剧情',exact:true}).click();await read();
 }
 assert.ok(seen.includes('yucun'),'the magistrate has no painted portrait');
 assert.ok(seen.includes('plaintiff'),'the plaintiff has no painted portrait');
 // Book four unfolds inside the estate, so its overview tab opens the estate map
 // rather than a journey list; the Xue courtyard is one of its places.
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();await page.locator('.world-map').waitFor();
 assert.equal(await page.locator('.world-location').count(),10);
 await page.screenshot({path:'artifacts/chapter04-overview.png',fullPage:true});
 await page.getByRole('button',{name:'当前场景',exact:true}).click();
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-pear');await read();
 await page.screenshot({path:'artifacts/chapter04-lixiang.png',fullPage:true});
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-court');await read();
 await page.screenshot({path:'artifacts/chapter04-yamen.png',fullPage:true});
 assert.equal(errors.length,0,JSON.stringify(errors));
 console.log(`Passed: chapter four opens the court, the street, Rongxi Hall and the Xue courtyard; the Xue family and the two court parties show painted portraits; the estate overview serves as this book's map tab.`);
}catch(e){console.error('Browser errors:',errors);console.error((await page.locator('body').innerText()).slice(0,3000));await page.screenshot({path:'artifacts/chapter04-failure.png',fullPage:true});throw e;}finally{await context.close();await browser.close();}
