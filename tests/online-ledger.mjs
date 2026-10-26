// Targeted online re-verification for the ledger pictures:
//
//   1. every unlocked transfer must show a picture, not a blank slot;
//   2. the ledger rows must all share one height (no ragged list);
//   3. the pictures must actually load from the origin, not 404;
//   4. the people grid must show portraits, complete faces, one size for all.
//
// Usage: ORIGIN_DIRECT=1 node tests/online-ledger.mjs
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync,readFileSync} from 'node:fs';
import {dismissPickup} from './lib/pickup.mjs';

const direct=process.env.ORIGIN_DIRECT==='1';
const profile=process.env.ONLINE_PROFILE??(direct?'/tmp/wb-direct-ledger':'/tmp/wb-online-ledger');
const args=['--disable-blink-features=AutomationControlled'];
if(direct)args.push('--host-resolver-rules=MAP stone.yan.pub 154.8.237.35');
const context=await chromium.launchPersistentContext(profile,{
  headless:false,channel:'chrome',viewport:{width:1440,height:900},reducedMotion:'reduce',
  ignoreHTTPSErrors:direct,args});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});
const tag=direct?'origin':'online';

const ledger=JSON.parse(readFileSync('design/ledger.json','utf8'));
const ledgerArt=ledger.entries.filter(e=>e.art).map(e=>e.art.replace(/^\//,''));

// 获得弹窗是模态的：它会挡住「继续剧情」等一切点击，必须先收下。
const dismiss=async()=>{await dismissPickup(page);await page.waitForTimeout(120);};
const reading=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:120000});
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:120000});
};

try{
 await page.goto('https://stone.yan.pub/',{waitUntil:'commit',timeout:120000});
 await page.waitForSelector('.chapter-select',{timeout:240000});
 await reading();

 // Read enough of the book to unlock a good share of the ledger, including the
 // people entries (a person is transferred, so their row carries their portrait).
 for(const section of ['arrival','reunion','uncles','c4-court','c4-truth']){
   await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption(section);
   await reading();
   for(let i=0;i<12;i++){
     await dismiss();
     const b=page.getByRole('button',{name:'继续剧情',exact:true});
     if(await b.isEnabled())await b.click();
     await page.waitForTimeout(280);
   }
 }
 await dismiss();

 await page.getByRole('button',{name:'背包',exact:true}).click();
 await page.getByRole('tab',{name:/账簿/}).click();
 await page.locator('.ledger-row').first().waitFor({timeout:30000});
 await page.waitForTimeout(1200);

 // (1) every unlocked row carries a picture frame, and no row is a bare blank.
 const rows=await page.evaluate(()=>{
   const all=[...document.querySelectorAll('.ledger-row')];
   const unlocked=all.filter(r=>r.classList.contains('unlocked'));
   return {
     total:all.length, unlocked:unlocked.length,
     withFrame:unlocked.filter(r=>r.querySelector('.card-thumb,.ledger-thumb-empty')).length,
     withRealFrame:unlocked.filter(r=>r.querySelector('.card-thumb')).length,
     heights:[...new Set(unlocked.map(r=>Math.round(r.getBoundingClientRect().height)))],
     circHeights:[...new Set([...document.querySelectorAll('.ledger-circ')].map(c=>Math.round(c.getBoundingClientRect().height)))],
     lockedHeights:[...new Set(all.filter(r=>!r.classList.contains('unlocked')).map(r=>Math.round(r.getBoundingClientRect().height)))],
   };
 });
 console.log(`${tag} ledger rows:`,JSON.stringify(rows));
 assert.ok(rows.unlocked>=15,`expected most transfers to be unlocked, got ${rows.unlocked}`);
 assert.equal(rows.withRealFrame,rows.unlocked,
   `every unlocked transfer needs a picture, ${rows.unlocked-rows.withRealFrame} rows are blank`);
 // (2) one height for every unlocked row, and one for the circumstances.
 assert.equal(rows.heights.length,1,`the ledger rows must share one height, got ${rows.heights.join('/')}`);
 assert.equal(rows.circHeights.length,1,`the circumstances must share one height, got ${rows.circHeights.join('/')}`);

 // (3) the pictures must come back from the origin with real bytes.
 const fetched=[];
 page.on('response',r=>{if(/\/assets\/cards\/ledger_.*\.webp/.test(r.url()))fetched.push({url:r.url(),status:r.status()});});
 await page.locator('.ledger-row.unlocked').first().scrollIntoViewIfNeeded();
 await page.waitForTimeout(2000);
 const loaded=await page.evaluate(()=>[...document.querySelectorAll('.ledger-row .card-art[src]')]
   .map(i=>({src:i.getAttribute('src'),w:i.naturalWidth,h:i.naturalHeight})));
 console.log(`${tag} ledger pictures loaded:`,loaded.length,'| natural sizes:',
   JSON.stringify([...new Set(loaded.map(i=>`${i.w}x${i.h}`))]));
 assert.ok(loaded.length>=1,'the ledger pictures in view must load');
 assert.ok(loaded.every(i=>i.w>0&&i.h>0),'every loaded ledger picture must have real pixels');
 assert.ok(fetched.every(f=>f.status===200),`the ledger pictures must be served, got ${JSON.stringify(fetched.filter(f=>f.status!==200))}`);

 // (4) the people grid: portraits, one size, faces intact.
 const people=await page.evaluate(()=>{
   const btns=[...document.querySelectorAll('.ledger-people button')];
   return {
     count:btns.length,
     btnHeights:[...new Set(btns.map(b=>Math.round(b.getBoundingClientRect().height)))],
     thumbHeights:[...new Set([...document.querySelectorAll('.ledger-people .card-thumb,.ledger-people .ledger-thumb-empty')]
       .map(t=>Math.round(t.getBoundingClientRect().height)))],
     portraits:document.querySelectorAll('.ledger-people .card-thumb').length,
   };
 });
 console.log(`${tag} ledger people:`,JSON.stringify(people));
 assert.ok(people.portraits>=6,'the ledger must show portraits for the people who have one');
 assert.equal(people.thumbHeights.length,1,`the ledger thumbnails must share one height, got ${people.thumbHeights.join('/')}`);
 assert.equal(people.btnHeights.length,1,`the ledger buttons must share one height, got ${people.btnHeights.join('/')}`);

 // The portrait must fit inside its box: a tall standing figure cropped by
 // object-fit:cover would lose its head, so the box must not crop it.
 const fit=await page.evaluate(()=>{
   const imgs=[...document.querySelectorAll('.ledger-people .card-art')];
   return imgs.map(i=>({of:getComputedStyle(i).objectFit,cls:i.className,nw:i.naturalWidth,nh:i.naturalHeight}));
 });
 assert.ok(fit.length>0,'the people grid must show portraits');
 assert.ok(fit.every(i=>i.of==='contain'),`the portraits must fit whole, got ${JSON.stringify([...new Set(fit.map(i=>i.of))])}`);

 await page.locator('.ledger-people').screenshot({path:`artifacts/ledger-online-people-${tag}.png`});
 await page.locator('.ledger-book').screenshot({path:`artifacts/ledger-online-rows-${tag}.png`});

 console.log(`${tag} ledger pictures: every unlocked transfer shows a picture, the rows line up on one height, the people carry whole portraits, and the assets are served from the origin.`);
}finally{
 await context.close();
}
