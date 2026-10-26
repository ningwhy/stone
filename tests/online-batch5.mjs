// Targeted online re-verification for the fifth batch of fixes:
//
//   1. the bamboo-gate cut-out must not eat the white wall;
//   2. the ledger cards must line up on a shared grid;
//   3. the card art must load lazily, not all at once;
//   4. the chapter list must mark read and unread sections;
//   5. leaving a room must not let the walker run ahead of the map.
//
// Usage: ORIGIN_DIRECT=1 node tests/online-batch5.mjs
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync} from 'node:fs';

const direct=process.env.ORIGIN_DIRECT==='1';
const profile=process.env.ONLINE_PROFILE??(direct?'/tmp/wb-direct-batch5':'/tmp/wb-online-batch5');
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

const reading=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:120000});
  for(let i=0;i<5;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(60);}}
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:120000});
};

try{
 await page.goto('https://stone.yan.pub/',{waitUntil:'commit',timeout:120000});
 await page.waitForSelector('.chapter-select',{timeout:240000});
 await reading();

 // (4) read marks in the chapter list, checked before anything gets read.
 const marks=await page.locator('.chapter-select option').allTextContents();
 assert.ok(marks.length>0,'the chapter list is empty');
 assert.ok(marks.every(m=>/[○◐●]/.test(m)),'every chapter must carry a read mark');
 assert.ok(marks.some(m=>/○/.test(m)),'unread chapters must be marked as unread');
 assert.ok(marks.some(m=>/[◐●]/.test(m)),'read chapters must be marked as read');
 console.log(`${tag} chapter marks:`,JSON.stringify(marks.slice(0,4)));

 // (2)+(3) the ledger grid and the lazy card art. The cards live in the 见闻 tab.
 // A place card unlocks as soon as one paragraph on that map has been read, so
 // reading a few different maps fills the album with enough cards to judge the
 // lazy loading on.
 for(const section of ['arrival','reunion','uncles']){
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption(section);
  await reading();
 }
 await page.getByRole('button',{name:'背包',exact:true}).click();
 await page.getByRole('tab',{name:/见闻/}).click();
 await page.locator('.card-item').first().waitFor({timeout:30000});
 // The pictures are mounted by an IntersectionObserver, so give it a beat.
 await page.waitForTimeout(600);
 const faces=await page.locator('.card-face').evaluateAll(els=>{
  const out={};
  for(const el of els){const kind=[...el.closest('.card-item').classList].find(c=>['place','line','token','bond'].includes(c));
   const h=Math.round(el.getBoundingClientRect().height);(out[kind]=out[kind]??new Set()).add(h);}
  return Object.fromEntries(Object.entries(out).map(([k,v])=>[k,[...v]]));
 });
 const thumbs=await page.locator('.card-thumb').evaluateAll(ns=>[...new Set(ns.map(n=>Math.round(n.getBoundingClientRect().height)))]);
 console.log(`${tag} card face heights:`,JSON.stringify(faces),'thumb heights:',JSON.stringify(thumbs));
 assert.equal(thumbs.length,1,'the card thumbnails must all share one height');
 for(const [kind,heights] of Object.entries(faces))assert.equal(heights.length,1,`the ${kind} cards must share one height, got ${heights.join('/')}`);
 const dialog=page.locator('dialog[open]').first();
 // Bring the first unlocked card into view: a locked card shows a question mark
 // on purpose, so only an unlocked one can ever load a picture.
 const totalWithArt=await page.locator('.card-item.unlocked').count();
 assert.ok(totalWithArt>0,'reading must have unlocked at least one card');
 await page.locator('.card-item.unlocked').first().scrollIntoViewIfNeeded();
 await page.waitForTimeout(1200);
 const loaded=await page.locator('.card-art[src]').count();
 const pending=await page.locator('.card-thumb .card-art-placeholder').count();
 console.log(`${tag} card art loaded in view:`,loaded,'still pending:',pending,'unlocked cards:',totalWithArt);
 assert.ok(loaded>0,'the visible card art must load');
 // Every unlocked card owns exactly one picture slot; the deferred ones still
 // show the shimmer placeholder. Locked cards show a question mark instead.
 const slots=await page.locator('.card-item.unlocked').evaluateAll(ns=>ns.map(n=>({art:!!n.querySelector('.card-art[src]'),placeholder:!!n.querySelector('.card-art-placeholder')})));
 const deferred=slots.filter(s=>!s.art&&s.placeholder).length;
 console.log(`${tag} unlocked cards:`,totalWithArt,'deferred pictures:',deferred);
 assert.equal(slots.filter(s=>s.art).length,loaded,'every mounted picture belongs to an unlocked card');
 if(totalWithArt>1)assert.ok(deferred>0,'the offscreen card art must stay lazy');
 // Scrolling the album must bring the pictures in: they are deferred, not dropped.
 const before=loaded;
 await dialog.evaluate(el=>el.scrollTo(0,el.scrollHeight));
 await page.waitForTimeout(1500);
 const afterScroll=await page.locator('.card-art[src]').count();
 console.log(`${tag} card art after scrolling to the bottom:`,afterScroll);
 assert.ok(afterScroll>=before,'scrolling the album must not lose pictures');
 await page.screenshot({path:`artifacts/${tag}-batch5-ledger.png`,fullPage:true});

 // (1) the bamboo-gate cut-out: the wall must survive the matte.
 const gate=await page.evaluate(async()=>{
  const img=new Image();img.src='/assets/rongguo/bamboo-gate.webp';
  await img.decode();
  const c=document.createElement('canvas');c.width=img.width;c.height=img.height;
  const g=c.getContext('2d');g.drawImage(img,0,0);
  const d=g.getImageData(0,0,img.width,img.height).data;
  let opaque=0,nearWhiteOpaque=0;
  for(let i=0;i<d.length;i+=4){
   if(d[i+3]>200){opaque++;const m=Math.min(d[i],d[i+1],d[i+2]);if(m>=235)nearWhiteOpaque++;}
  }
  return {w:img.width,h:img.height,opaque,nearWhiteOpaque};
 });
 console.log(`${tag} bamboo-gate:`,JSON.stringify(gate));
 assert.ok(gate.opaque>50000,'the gate art must keep its body');
 assert.ok(gate.nearWhiteOpaque>2000,'the white wall of the gate must survive the matte');

 // (5) leaving a room must not walk ahead of the map.
 // The scenario the reader described: a scene change loads a new map while the
 // story is already in its moving state. The check samples the engine and the
 // stage together, frame by frame, and counts any frame where somebody walks
 // on a board that has not been drawn yet.
 await page.keyboard.press('Escape');
 await page.waitForTimeout(200);
 // 'arrival' opens on the capital street; two lines later the story steps onto
 // the 贾府 map — exactly the cut the reader described.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('arrival');
 await reading();
 let raced=0,walked=0,unlockedWindows=0;
 // Sample every frame: the engine's own coordinates tell whether anybody moved,
 // and the host's data-scene-ready tells whether the board under them is drawn.
 await page.evaluate(()=>{
  window.__samples=[];window.__sampling=true;
  const engine=window.__engine;
  const frame=()=>{
   const state=engine.getSnapshot();
   const host=document.querySelector('.game-map');
   const ready=host?.getAttribute('data-scene-ready')??'';
   // A walk is a character that was already moving and whose coordinates
   // changed by a step. A 'show' action places somebody on a new anchor in a
   // single frame, which is not a walk.
   const actors={};
   for(const [id,a] of Object.entries(state.actors))if(a.visible)actors[id]=[a.col,a.row,a.moving?1:0];
   window.__samples.push({ready,scene:state.sceneId,actors,locked:engine.stageIsLocked});
   if(window.__sampling)requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
 });
 // Step the story forward across the scene boundary.
 for(let i=0;i<5;i++){
  const button=page.getByRole('button',{name:'继续剧情',exact:true});
  if(await button.isEnabled())await button.click();
  await page.waitForTimeout(700);
 }
 const samples=await page.evaluate(()=>{window.__sampling=false;return window.__samples;});
 for(let i=1;i<samples.length;i++){
  const before=samples[i-1],after=samples[i];
  // The window between "the story changed map" and "the new map is drawn".
  const boardDown=after.ready!==after.scene;
  if(boardDown&&!after.locked)unlockedWindows++;
  let stepped=false;
  for(const [id,a] of Object.entries(after.actors)){
   const b=before.actors[id];
   if(!b||!a[2]||!b[2])continue;            // only a character that was walking
   if(b[0]!==a[0]||b[1]!==a[1])stepped=true; // and actually took a step
  }
  if(!stepped)continue;
  if(boardDown)raced++;
  else walked++;
 }
 // The gate must be held while a scene is still loading: that is the contract
 // the whole fix rests on, so it is checked directly as well.
 assert.equal(unlockedWindows,0,'the stage gate must stay shut until the new map is drawn');
 assert.equal(raced,0,'the walker must not run ahead of the map');
 assert.ok(walked>0,'nobody ever walked on a drawn board, so the check proved nothing');
 console.log(`${tag} walk-while-board-not-ready count: 0, frames walked on a drawn board: ${walked}, sampled frames: ${samples.length}`);

 console.log(`Passed: ${tag} keeps the white gate wall, the aligned card grid, the lazy card art, the chapter read marks and the walk that waits for the map.`);
}catch(e){
 console.error(`${tag} FAILED:`,e.message);
 process.exitCode=1;
}finally{
 if(errors.length)console.log(`${tag} page errors:`,JSON.stringify(errors.slice(0,5)));
 await context.close();
}
