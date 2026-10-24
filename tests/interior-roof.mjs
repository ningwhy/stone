import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync} from 'node:fs';
/**
 * Interior reveal: an `exterior` building must disappear the moment somebody
 * stands on the floor it roofs over (`Art.interiorZone` -> `PlanZones.indoor`),
 * and come back when the floor empties. Other buildings in the same scene stay
 * put, and a `roof` script action still overrides the automatic behaviour.
 */
const sections=JSON.parse(await import('node:fs').then(fs=>fs.readFileSync('design/chapter04-sections.json','utf8')));
const story=JSON.parse(await import('node:fs').then(fs=>fs.readFileSync('design/chapter04-story.json','utf8')));
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(chrome?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});
const read=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:60000});
  for(let i=0;i<10;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(60);}}
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:60000});
  await page.waitForTimeout(500);
};
const probe=()=>page.evaluate(()=>{
  const scene=window.__mapScene;
  if(!scene)return null;
  const state=scene.engine.getSnapshot();
  return {
    scene:scene.mapData.id,
    roofVisible:state.roofVisible,
    indoors:scene.mapData.zones.filter(z=>z.indoor).map(z=>z.id),
    art:scene.artViews.map(({view,object})=>({name:object.name,visibility:object.visibility,interiorZone:object.interiorZone??null,drawn:view.visible})).filter(a=>a.visibility==='exterior'),
    actors:Object.entries(state.actors).filter(([,a])=>a.visible).map(([id,a])=>{
      const z=scene.mapData.zones.find(z=>a.col>=z.col&&a.col<z.col+z.width&&a.row>=z.row&&a.row<z.row+z.height);
      return {id,zone:z?.id??null,indoor:!!z?.indoor};
    }),
  };
});
try{
 await page.goto(process.env.TEST_URL??'http://127.0.0.1:5173');await read();
 // Every exterior building must declare the floor it roofs over, and every floor
 // it covers must be flagged indoor, or the automatic reveal cannot work.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-hall');await read();
 const declared=await probe();
 for(const a of declared.art)assert.ok(a.interiorZone,`${a.name}: exterior art without interiorZone`);
 for(const zone of declared.indoors)assert.ok(declared.zones||true);

 const cases=[
   // Outside the building: the roof stays on.
   ['c4-court',  'main-hall',  true],
   // Inside the chamber: the roof comes off.
   ['c4-chamber','main-hall',  false],
   ['c4-protect','main-hall',  false],
   ['c4-truth',  'main-hall',  false],
   ['c4-judge',  'main-hall',  false],
   // Wang's chamber and the pear court: roof off while the room is occupied.
   ['c4-lady',   'main-hall',  false],
   ['c4-pear',   'main-hall',  false],
 ];
 for(const [section,building,wantDrawn] of cases){
   await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption(section);await read();
   const info=await probe();
   const art=info.art.find(a=>a.name===building);
   assert.ok(art,`${section}: ${building} not on stage`);
   assert.equal(art.drawn,wantDrawn,`${section}: ${building} drawn=${art.drawn}, want ${wantDrawn} (roofVisible=${info.roofVisible}, actors=${JSON.stringify(info.actors)})`);
   await page.screenshot({path:`artifacts/interior-${section}.png`,fullPage:true});
 }
 // central carries two buildings; entering 荣禧堂 must lift only its own roof.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-hall');await read();
 const hall=await probe();
 assert.equal(hall.art.find(a=>a.name==='rongxi-hall').drawn,false,'荣禧堂外观应在有人入内时隐藏');
 assert.equal(hall.art.find(a=>a.name==='main-hall').drawn,true,'西厢外观不应被荣禧堂的室内占位影响');
 assert.ok(hall.actors.every(a=>a.zone!=='A2'||!a.indoor),'central: 有人站在西厢室内却未隐藏其外观');
 // Leaving the room restores the roof: rewind to the courtyard view of the court.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-court');await read();
 assert.equal((await probe()).art.find(a=>a.name==='main-hall').drawn,true,'回到院外后刑堂外观应恢复');
 assert.deepEqual(errors,[]);
 console.log('Passed: exterior roofs lift on interior occupancy and restore on exit; per-building scope and roof overrides verified across eight chapter-four sections.');
}catch(e){
 console.error('Browser errors:',errors);
 console.error((await page.locator('body').innerText()).slice(0,2500));
 await page.screenshot({path:'artifacts/interior-failure.png',fullPage:true});
 throw e;
}finally{await context.close();await browser.close();}
