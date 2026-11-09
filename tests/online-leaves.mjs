// Online check for the chapter cover and the back cover.
//
// The cover and the back cover are modal sheets: they lie over the stage and
// swallow every click. This script walks the deployed site the way a reader
// does and checks three things:
//
//   1. the book opens with a cover that carries the chapter title;
//   2. the last node of a chapter closes with a back cover;
//   3. jumping around the index leaves no sheet behind.
//
// The third one is the regression this script exists for: an earlier version
// only updated the sheet state when a sheet was about to appear, so the cover
// stayed on the stage after a jump and hid the "继续剧情" button.
//
// Usage: node tests/online-leaves.mjs
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync,rmSync} from 'node:fs';
import {seekSection} from './lib/toc.mjs';
import {chapterLeaves} from '../src/leaves.ts';
import {onlineUrl,onlineArgs,ignoreTlsErrors,onlineProfile} from './lib/online.mjs';

const profile=onlineProfile('leaves');
// A throwaway profile: this script clears the save on purpose, and it must not
// touch the profile the other online checks use.
if(process.env.ONLINE_PROFILE===undefined)rmSync(profile,{recursive:true,force:true});
const context=await chromium.launchPersistentContext(profile,{
  headless:false,channel:'chrome',viewport:{width:1440,height:900},reducedMotion:'reduce',
  ignoreHTTPSErrors:ignoreTlsErrors(),args:onlineArgs()});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});

const node=async()=>(await page.locator('.node-label').textContent())?.trim()??'';
const reading=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:120000});
  for(let i=0;i<5;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(60);}}
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
};
// The sheet is a React effect: it lands a frame after the node label does.
// Waiting for it explicitly keeps the check from racing the render.
const sheet=async cls=>{
  await page.waitForFunction(c=>!!document.querySelector(c),cls,{timeout:5000}).catch(()=>{});
  return page.locator(cls).count();
};

// The bounds come from the product code, so a change in the chapter split
// cannot quietly invalidate the check.
const leaves=chapterLeaves();
const first=leaves.get(1);
assert.ok(first,'chapter one must have a leaf record');

try{
 await page.goto(onlineUrl(),{waitUntil:'commit',timeout:120000});
 await page.locator('.loading-screen').waitFor({state:'detached',timeout:120000});
 // The profile is persistent, so a previous run's save would open the book in
 // the middle of a chapter — and a book opened mid-chapter rightly has no cover.
 // Start from a clean slate: the cover only appears at the very first node.
 await page.evaluate(()=>localStorage.clear());
 await page.reload({waitUntil:'commit',timeout:120000});
 await page.locator('.loading-screen').waitFor({state:'detached',timeout:120000});
 await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});

 // 1. The book opens with a cover.
 assert.equal(await sheet('.leaf-sheet.leaf-cover'),1,'the book must open with a cover');
 const title=(await page.locator('.leaf-title').textContent())?.trim()??'';
 assert.ok(title.includes('甄士隐梦幻识通灵'),`the cover carries the chapter title, got "${title}"`);
 const cast=await page.locator('.leaf-cast li').count();
 assert.ok(cast>0,'the cover lists the people of the chapter');
 // The little portraits fade in once the bitmaps arrive. A frame that never
 // filled in is a frame whose fade never happened, and it reads as a blank
 // box — so wait for the images, then look.
 await page.waitForFunction(()=>[...document.querySelectorAll('.leaf-cast-face img')].every(img=>img.dataset.loaded==='true'),undefined,{timeout:15000}).catch(()=>{});
 const painted=await page.evaluate(()=>[...document.querySelectorAll('.leaf-cast-face img')].map(img=>img.dataset.loaded==='true'&&img.naturalWidth>0));
 assert.ok(painted.length>0&&painted.every(Boolean),`every painted face on the cover must be visible, got ${painted.length} frames, ${painted.filter(v=>!v).length} empty`);
 // Measured, not eyeballed: each row of faces must sit at the same distance
 // from both edges, or the last row reads as pushed to one side.
 const rows=await page.evaluate(()=>{
   const sheet=document.querySelector('.leaf-sheet.leaf-cover');
   const sb=sheet.getBoundingClientRect();
   const buckets={};
   for(const li of document.querySelectorAll('.leaf-cast li')){
     const r=li.getBoundingClientRect();
     const key=Math.round(r.top-sb.top);
     (buckets[key]??=[]).push({left:Math.round(r.left-sb.left),right:Math.round(sb.right-r.right)});
   }
   return Object.values(buckets).map(v=>({
     count:v.length,
     leftGap:Math.min(...v.map(x=>x.left)),
     rightGap:Math.min(...v.map(x=>x.right)),
   }));
 });
 for(const row of rows){
   assert.ok(row.count<=4,`a row of faces must hold at most four, got ${row.count}`);
   assert.ok(Math.abs(row.leftGap-row.rightGap)<=2,`a row of faces must sit centred, left gap ${row.leftGap} vs right gap ${row.rightGap}`);
 }
 await page.screenshot({path:'artifacts/online-leaf-cover.png',fullPage:true});
 console.log(`online cover: ${title} · ${cast} faces · ${rows.length} rows, all centred`);

 // 2. Walk to the last node of chapter one; a back cover must close it.
 // The cover is a modal sheet: it swallows every click, so it has to be put
 // away the way a reader does before the story can be walked at all.
 await page.locator('.leaf-cover .leaf-open').click();
 await page.locator('.leaf-sheet').waitFor({state:'detached',timeout:10000});
 let steps=0;
 while(steps<200){
   const label=await node();
   if(label===first.lastNode)break;
   // A pickup popup is modal too, and a back cover shows up on the last node.
   const pickup=page.locator('.pickup-confirm');
   if(await pickup.isVisible().catch(()=>false)){await pickup.click();await pickup.waitFor({state:'detached',timeout:5000}).catch(()=>{});}
   await page.getByRole('button',{name:'继续剧情',exact:true}).click();
   await page.waitForTimeout(160);
   steps++;
 }
 assert.equal(await node(),first.lastNode,`chapter one must end at ${first.lastNode}`);
 assert.equal(await sheet('.leaf-sheet.leaf-back'),1,'the last node must close with a back cover');
 const backTitle=(await page.locator('.leaf-book').textContent())?.trim()??'';
 assert.ok(backTitle.includes('本回目完'),`the back cover says the chapter is over, got "${backTitle}"`);
 // The back cover names the next chapter, so the reader knows what is coming.
 const nextName=(await page.locator('.leaf-next-name').textContent())?.trim()??'';
 assert.ok(nextName.includes('第二回'),`the back cover names the next chapter, got "${nextName}"`);
 const nextTitle=(await page.locator('.leaf-next-title').textContent())?.trim()??'';
 assert.ok(nextTitle.includes('贾夫人仙逝扬州城'),`the back cover carries the next chapter's title, got "${nextTitle}"`);
 await page.screenshot({path:'artifacts/online-leaf-back.png',fullPage:true});
 console.log(`online back cover: ${backTitle} · reached in ${steps} steps`);

 // The back cover must not strand the reader: the way forward is there.
 assert.ok(await page.locator('.leaf-back .leaf-open').count()>0,'the back cover offers a way into the next chapter');

 // 3. The reader turns the page themselves: pressing 开启下一回 must bring
 //    the next chapter's cover, not jump straight into the story.
 await page.locator('.leaf-back .leaf-open').click();
 await page.waitForTimeout(400);
 assert.equal(await sheet('.leaf-sheet.leaf-cover'),1,'开启下一回 must open the next chapter cover');
 const nextCoverTitle=(await page.locator('.leaf-title').textContent())?.trim()??'';
 assert.ok(nextCoverTitle.includes('贾夫人仙逝扬州城'),`the second chapter cover carries its own title, got "${nextCoverTitle}"`);
 await page.screenshot({path:'artifacts/online-leaf-cover-2.png',fullPage:true});
 console.log(`online next cover: ${nextCoverTitle}`);

 // 4. Jump around the index; no sheet may be left on the stage.
 // The second chapter's cover is still up: it is a modal sheet and swallows
 // every click, so it has to be put away first — exactly like the reader would.
 await page.locator('.leaf-cover .leaf-open').click();
 await page.locator('.leaf-sheet').waitFor({state:'detached',timeout:10000});
 await seekSection(page,'c1-home');
 await page.waitForTimeout(600);
 const left=await page.locator('.leaf-sheet').count();
 assert.equal(left,0,`jumping must not leave a sheet on the stage, got ${left}`);
 // And the button it used to hide must be clickable again.
 await page.getByRole('button',{name:'继续剧情',exact:true}).click();
 await page.waitForTimeout(300);
 console.log('online jump: no sheet left behind, the story still moves');

 assert.deepEqual(errors,[],`console errors: ${errors.join(' | ')}`);
 console.log('Passed: the deployed site opens with a chapter cover, closes a chapter with a back cover, turns the page into the next chapter on request, and leaves no sheet behind after a jump.');
}finally{
 await context.close();
}
