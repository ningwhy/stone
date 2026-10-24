import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync, readFileSync} from 'node:fs';
/**
 * Character facing: painted portraits and chibi sprites are not mirrored by a
 * global rule. `design/character-facing.json` records the measured side each
 * picture was painted facing, and `paintedFacing(actor, kind)` drives every
 * mirror decision. This walks the whole story once and checks that
 *   - a walking chibi is flipped exactly when its painted side disagrees with
 *     the isometric walking direction, and
 *   - the dialogue speaker portrait faces the text while listeners face the
 *     speaker.
 */
const facing=JSON.parse(readFileSync('design/character-facing.json','utf8')).actors;
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(chrome?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});
const read=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:60000});
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:60000});
  await page.waitForTimeout(400);
};
try{
 await page.goto(process.env.TEST_URL??'http://127.0.0.1:5173');await read();
 // Sample the live stage every frame while the story is played through.
 await page.evaluate(()=>{
   window.__chibi=[];window.__seen=new Set();
   const tick=()=>{
     const scene=window.__mapScene;
     if(scene){
       const state=scene.engine.getSnapshot();
       for(const [id,a] of Object.entries(state.actors)){
         if(!a.visible||!a.moving)continue;
         const sprite=scene.actorSprites.get(id);
         if(!sprite)continue;
         const key=`${id}:${a.direction}:${sprite.flipX}`;
         if(window.__seen.has(key))continue;
         window.__seen.add(key);
         window.__chibi.push({id,direction:a.direction,flipX:sprite.flipX});
       }
     }
     requestAnimationFrame(tick);
   };
   requestAnimationFrame(tick);
 });
 const portraits=[];
 for(let i=0;i<420;i++){
   const speaker=await page.locator('.dialogue-line h2, .speaker-line h2').first().textContent().catch(()=>null);
   const node=await page.locator('.node-label').textContent().catch(()=>null);
   const row=await page.evaluate(()=>{
     const pick=sel=>{const img=document.querySelector(sel);if(!img)return null;return {src:img.getAttribute('src'),mirrored:getComputedStyle(img).transform.includes('matrix(-1')};};
     return {speaker:pick('.speaker-portrait img'),listener:pick('.listener-feature img')};
   });
   portraits.push({node,speaker,...row});
   const next=page.getByRole('button',{name:'继续剧情',exact:true});
   if(await next.isVisible().catch(()=>false)){
     await next.click().catch(()=>{});
     const skip=page.getByRole('button',{name:'跳过移动',exact:true});
     if(await skip.isVisible().catch(()=>false))await skip.click().catch(()=>{});
     await page.waitForTimeout(220);
   } else await page.waitForTimeout(150);
 }
 const chibi=await page.evaluate(()=>window.__chibi);
 assert.ok(chibi.length>=20,`只采样到 ${chibi.length} 个行走帧，无法覆盖朝向表`);
 let mismatch=0;
 for(const r of chibi){
   const painted=facing[r.id]?.chibi;
   assert.ok(painted,`朝向表缺少 ${r.id} 的 chibi 记录`);
   // Iso walking right (direction 1) means the sprite must end up facing right,
   // so flip only when the painted chibi already faces the other way.
   const want=(r.direction===1)!==(painted==='right');
   if(want!==r.flipX){mismatch++;console.error('chibi mismatch',JSON.stringify(r),'painted',painted);}
 }
 assert.equal(mismatch,0,`${mismatch}/${chibi.length} 个行走帧镜像方向与朝向表不一致`);
 // Speaker portrait must face the text (right); listeners must face the speaker (left).
 let portraitRows=0;
 for(const row of portraits){
   const actor=(src)=>src && /rongguo\/([a-z_]+)-portrait/.exec(src)?.[1];
   const sp=actor(row.speaker?.src), ls=actor(row.listener?.src);
   if(sp){
     portraitRows++;
     const want=facing[sp]?.portrait!=='right';
     assert.equal(row.speaker.mirrored,want,`${row.node} 讲话人 ${sp} 立绘镜像=${row.speaker.mirrored}，期望 ${want}`);
   }
   if(ls){
     const want=facing[ls]?.portrait==='right';
     assert.equal(row.listener.mirrored,want,`${row.node} 听众 ${ls} 立绘镜像=${row.listener.mirrored}，期望 ${want}`);
   }
 }
 assert.ok(portraitRows>=30,`只采样到 ${portraitRows} 行讲话人立绘`);
 assert.deepEqual(errors,[]);
 console.log(`Passed: ${chibi.length} walking frames and ${portraitRows} speaker portraits agree with design/character-facing.json (${new Set(chibi.map(r=>r.id)).size} actors).`);
}catch(e){
 console.error('Browser errors:',errors);
 await page.screenshot({path:'artifacts/facing-failure.png',fullPage:true});
 throw e;
}finally{await context.close();await browser.close();}
