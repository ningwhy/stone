/** 旧存档兼容：加了新回目之后，老读者读到的进度还得能读回来。
 *
 *  存档是 append 型的：`engine.restore` 按**节点 id** 定位，不是按序号，
 *  新加的回目只是往数组后面追加，所以老档的序号虽然整体后移，节点 id 还在，
 *  读回来落点不变。
 *
 *  这一份测试造两类老档：
 *  1. 第 17 回时期存下的档（停在大观园那一段）——老档里没有第 18 回的角色；
 *  2. 老档里 `actors` 缺了几个后来才出场的角色——读档时应当被补成不可见的占位。
 *
 *  两者都不该报错，更不该把读者丢到别的段落去。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {dismissPickup, dismissLeaf} from './lib/pickup.mjs';

const story16=JSON.parse(readFileSync('design/chapter16-story.json','utf8'));
const story17=JSON.parse(readFileSync('design/chapter17-story.json','utf8'));
const story18=JSON.parse(readFileSync('design/chapter18-story.json','utf8'));
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(existsSync(chrome)?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});

const node=()=>page.locator('.node-label').textContent();
async function reading(){
  await dismissPickup(page);
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
  for(let i=0;i<4;i++){
    const b=page.getByRole('button',{name:'跳过移动',exact:true});
    if(await b.isVisible().catch(()=>false)){await b.click();await page.waitForTimeout(80);}
  }
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:30000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:30000});
  await dismissLeaf(page,false);
}

try{
  await page.goto(process.env.TEST_URL??'http://127.0.0.1:5173');
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});

  // 走到第 17 回的某一段，存一个档——这就是「第 18 回上线之前」的存档形状。
  await page.evaluate(id=>window.__mapScene.engine.seek(id),story17[story17.length-5].id);
  await page.waitForTimeout(600);
  await reading();
  const savedNode=await node();
  const oldSave=await page.evaluate(()=>{
    const data=window.__mapScene.engine.serialize();
    return data;
  });
  assert.ok(oldSave&&oldSave.node,'the engine must be able to serialize a save');
  // 模拟老档：把第 18 回才出现的角色从 actors 里删掉。
  const oldActors=Object.keys(oldSave.state.actors);
  const newIn18=[...new Set(story18.flatMap(n=>(n.actions??[]).filter(a=>a.actor).map(a=>a.actor)))].filter(a=>!oldActors.includes(a));
  console.log('第18回新增角色（老档里没有）:',newIn18.join(', ')||'（无）');
  const trimmed=structuredClone(oldSave);
  for(const a of newIn18)delete trimmed.state.actors[a];
  // 再删一个第 16 回就有的角色，模拟更老的档。
  trimmed.state.actors.xiren=undefined;
  delete trimmed.state.actors.xiren;
  await page.evaluate(save=>localStorage.setItem('honglou-five-six-chapters:v5',JSON.stringify(save)),trimmed);
  console.log('造好的老档停在:',trimmed.node,'（读档前页面在',savedNode,'）');

  // 刷新读档。
  await page.reload();
  await reading();
  const landed=await node();
  console.log('读档后落在:',landed);
  // 末节点标签是「终幕」，这里不是末节点，所以应当是节点 id。
  assert.equal(landed,trimmed.node,`the old save must reopen where it was saved, got ${landed}`);
  // 老档里没有的角色，读档后应当被补成不可见的占位，不能报错也不能乱出现在场上。
  const restored=await page.evaluate(()=>window.__mapScene.engine.getSnapshot().actors);
  for(const a of newIn18){
    assert.ok(restored[a],`${a} must be seeded by the restore`);
    assert.equal(restored[a].visible,false,`${a} must be seeded invisible, not on stage`);
  }
  assert.ok(restored.xiren,`xiren must be seeded by the restore`);
  assert.equal(restored.xiren.visible,false,'xiren must be seeded invisible');
  console.log('读档后 actors 数:',Object.keys(restored).length,'（老档只有',Object.keys(trimmed.state.actors).length,'个）');

  // 读档之后还能继续往下读——读档不是死的存档。
  const before=await node();
  await page.getByRole('button',{name:'继续剧情',exact:true}).click();
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent!==id,before,{timeout:20000});
  assert.notEqual(await node(),before,'the story must continue after loading an old save');
  console.log('读档后继续读到:',await node());

  assert.equal(errors.length,0,JSON.stringify(errors));
  console.log('Passed: an old save from before chapter 18 reopens at the same line, missing actors are seeded invisible, and the story continues.');
}catch(e){
  console.error('Browser errors:',errors);
  console.error((await page.locator('body').innerText()).slice(0,2500));
  await page.screenshot({path:'artifacts/save-compat-failure.png',fullPage:true});
  throw e;
}finally{
  await context.close();
  await browser.close();
}
