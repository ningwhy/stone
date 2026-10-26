import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,mkdirSync} from 'node:fs';
/**
 * Outdoor travel stages: the two stretches the reader noticed were missing —
 * the canal run from Yangzhou to the capital (chapter three) and the out-of-town
 * walk to Zhitong temple plus the dusk return (chapter two) — must open as real
 * stages. Every walker has to land on the anchor the script named, the canal
 * stage has to carry its water band from map data (otherwise the river would
 * silently fall back to the old fixed pond), and the section dropdown, the
 * journey view and the atlas have to know the two new scenes.
 */
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const candidates=[process.env.TEST_URL,'http://127.0.0.1:4173','http://127.0.0.1:5173'].filter(Boolean);
let base=candidates.at(-1);
for(const url of candidates){try{if((await fetch(url)).ok){base=url;break;}}catch{}}
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(existsSync(chrome)?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts/travel-stages',{recursive:true});
// node -> scene, and the anchor cell every visible actor must end the walk on.
const stages=[
 ['C2-013a','guowai',{yucun:[15,33]}],
 ['C2-013b','guowai',{yucun:[21,28]}],
 ['C2-013c','guowai',{yucun:[21,12]}],
 ['C2-053a','guowai',{yucun:[24,31]}],
 ['C2-053b','guowai',{yucun:[15,33]}],
 ['P011a','canal',{daiyu:[6,27],xueyan:[6,28],nurse_wang:[6,29]}],
 ['P011b','canal',{daiyu:[20,25],xueyan:[20,26],nurse_wang:[20,27]}],
 ['P011c','canal',{daiyu:[33,25],xueyan:[33,26],nurse_wang:[33,27]}],
];
try{
 await page.goto(base);
 await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
 await page.waitForFunction(()=>!!document.querySelector('.game-map[data-scene-ready]'),undefined,{timeout:30000});
 for(const [id,scene,actors] of stages){
  await page.waitForFunction(()=>!!window.__mapScene,undefined,{timeout:30000});
  // seek applies the whole node instantly, so a settled read proves the walk
  // resolves to the authored anchor rather than a mid-stride position.
  await page.evaluate(n=>window.__mapScene.engine.seek(n),id);
  await page.waitForFunction(s=>window.__mapScene&&window.__mapScene.mapData.id===s,scene,{timeout:30000});
  await page.waitForTimeout(500);
  const snap=await page.evaluate(()=>{
   const s=window.__mapScene,st=s.engine.getSnapshot();
   return {step:s.engine.steps[st.index].id,scene:s.mapData.id,theme:s.mapData.theme,
    water:s.mapData.water,flowerbeds:s.mapData.flowerbeds,status:st.status,
    visible:Object.entries(st.actors).filter(([,a])=>a.visible).map(([k,a])=>[k,a.col,a.row,a.moving])};
  });
  assert.equal(snap.step,id,`seek landed on ${snap.step}`);
  assert.equal(snap.scene,scene);
  assert.equal(snap.status,'reading',`${id} left a walk unfinished`);
  assert.deepEqual(snap.visible.map(v=>v[0]).sort(),Object.keys(actors).sort(),`${id} shows the wrong cast`);
  for(const [k,col,row,moving] of snap.visible){
   assert.equal(moving,false,`${id} left ${k} mid-stride`);
   assert.deepEqual([col,row],actors[k],`${id} left ${k} off the authored anchor`);
  }
  if(scene==='canal'){
   assert.equal(snap.theme,'river');
   assert.deepEqual(snap.water,[[3,14,34,11]],'the canal stage lost its water band');
   assert.equal(snap.flowerbeds,false,'the canal stage must not grow garden flowerbeds');
  }else{
   assert.equal(snap.theme,'garden');
   assert.equal(snap.water.length,0,'the country walk has no water band');
   assert.equal(snap.flowerbeds,true,'the country walk keeps the garden flowerbeds');
  }
  await page.screenshot({path:`artifacts/travel-stages/${id}.png`});
 }
 // The new section has to appear in the dropdown and open at the out-of-town gate.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c2-guowai');
 await page.waitForFunction(()=>window.__mapScene&&window.__mapScene.mapData.id==='guowai',undefined,{timeout:30000});
 assert.equal(await page.evaluate(()=>window.__mapScene.engine.steps[window.__mapScene.engine.getSnapshot().index].id),'C2-013a');
 // The journey view lists the country walk as its own stage and can reopen it.
 await page.getByRole('button',{name:'本回行迹',exact:true}).click();
 await page.locator('.journey-sites').waitFor();
 assert.equal(await page.locator('.journey-site strong').filter({hasText:'扬州郭外 · 出城山道'}).count(),1,'the journey view omits the country walk');
 await page.locator('.journey-site').filter({has:page.locator('strong',{hasText:'扬州郭外 · 出城山道'})}).click();
 await page.waitForFunction(()=>window.__mapScene&&window.__mapScene.mapData.id==='guowai',undefined,{timeout:30000});
 assert.equal(await page.evaluate(()=>window.__mapScene.engine.steps[window.__mapScene.engine.getSnapshot().index].id),'C2-013a');
 // The atlas knows both new scenes, on the 40x40 stage contract.
 await page.getByRole('button',{name:'设置',exact:true}).click();
 await page.getByRole('button',{name:'册页',exact:true}).click();
 await page.locator('.atlas-body').waitFor();
 assert.equal(await page.locator('.atlas-body article').count(),22,'the atlas must list every scene');
 for(const [title,anchors] of [['运河 · 舟行北上',12],['扬州郭外 · 出城山道',10]]){
  const card=page.locator('.atlas-body article').filter({has:page.locator('h3',{hasText:title})});
  assert.equal(await card.count(),1,`the atlas omits ${title}`);
  assert.match(await card.locator('small').textContent(),new RegExp(`40×40 格 · ${anchors} 个剧情地点`));
 }
 await page.getByRole('button',{name:'返回故事',exact:true}).click();
 assert.equal(errors.length,0,JSON.stringify(errors));
 console.log(`Passed: ${stages.length} travel stages open on their own scene, every walk lands on the authored anchor, the canal carries its water band, and the dropdown, journey view and atlas know both new scenes.`);
}catch(e){console.error('Browser errors:',errors);console.error((await page.locator('body').innerText()).slice(0,3000));await page.screenshot({path:'artifacts/travel-stages-failure.png',fullPage:true});throw e;}finally{await context.close();await browser.close();}
