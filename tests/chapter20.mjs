/** 第二十回的定向验收：王熙凤正言弹妒意、林黛玉俏语谑娇音。
 *
 *  与 tests/chapter19.mjs 同一模式，守住四件事：
 *  1. 七段全部能推进到，且每段的落点节点与设计数据一致；
 *  2. 每一段的场景都在声明的场景表内（night / c7_lixiang / wang / dinner）；
 *  3. 封底不再是全书终幕——第 20 回是当前末回，封底应显示
 *     「全书至此，砖石犹温。」；
 *  4. 39 个节点的正文逐字出自底本。
 *
 *  第 20 回新出场四人：贾环、赵姨娘、史湘云、麝月。前三人有戏份，
 *  麝月只守着篦头，所以本回另外要验一次「查无此人」的样本已随之改变：
 *  browser-smoke 里那个样本必须换成一个第 20 回之前没有出现过的名字。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,readFileSync,mkdirSync} from 'node:fs';
import {dismissPickup, dismissLeaf} from './lib/pickup.mjs';
import {seekSection} from './lib/toc.mjs';

const story=JSON.parse(readFileSync('design/chapter20-story.json','utf8'));
const sections=JSON.parse(readFileSync('design/chapter20-sections.json','utf8'));
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(existsSync(chrome)?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});

const node=()=>page.locator('.node-label').textContent();
const currentScene=()=>page.locator('.game-map').getAttribute('data-scene-ready');

async function reading(){
  await dismissPickup(page);
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
  for(let i=0;i<4;i++){
    const skip=page.getByRole('button',{name:'跳过移动',exact:true});
    if(await skip.isVisible().catch(()=>false)){await skip.click();await page.waitForTimeout(60);}
  }
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:30000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:30000});
  await dismissLeaf(page,false);
}

async function step(keepLeaf=false){
  await dismissPickup(page);
  const before=await node();
  await dismissLeaf(page,false,true);
  for(let i=0;i<3;i++){
    const skip=page.getByRole('button',{name:'跳过移动',exact:true});
    if(await skip.isVisible().catch(()=>false)){await skip.click();await page.waitForTimeout(120);}
  }
  await page.getByRole('button',{name:'继续剧情',exact:true}).click();
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent!==id,before,{timeout:20000});
  await page.waitForTimeout(150);
  if(!keepLeaf)await dismissLeaf(page,false,true);
  await dismissPickup(page);
  return await node();
}

try{
  await page.goto(process.env.TEST_URL??'http://127.0.0.1:5173');
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.evaluate(()=>localStorage.clear());
  await page.reload();
  await reading();
  await dismissLeaf(page,false,true);

  // ---- 一、逐段推进 ----
  const scenes=new Set();
  for(const section of sections){
    await seekSection(page,section.id);
    await reading();
    await dismissLeaf(page,false,true);
    const landed=await node();
    assert.equal(landed,section.start,`${section.id} must land on ${section.start}, got ${landed}`);
    const scene=await currentScene();
    assert.equal(scene,section.scene,`${section.id} must be staged in ${section.scene}, got ${scene}`);
    scenes.add(scene);
    await page.screenshot({path:`artifacts/c20-${section.id}.png`,fullPage:true});
  }
  console.log('stages:',[...scenes].sort().join(' / '));
  // 本回用到的四张图都要走到。
  for(const stage of ['night','c7_lixiang','wang','dinner']){
    assert.ok(scenes.has(stage),`the ${stage} stage must be reachable`);
  }

  // ---- 二、段内连贯 ----
  const STAGES=['night','c7_lixiang','wang','dinner'];
  for(const section of sections){
    await seekSection(page,section.id);
    await reading();
    await dismissLeaf(page,false,true);
    const start=await node();
    let walked=0;
    for(let i=0;i<6;i++){
      const now=await step();
      if(now===start)break;
      walked++;
    }
    assert.ok(walked>0,`${section.id} must let the reader walk forward`);
    const after=await currentScene();
    assert.ok(STAGES.includes(after),`${section.id} walked into an unexpected stage ${after}`);
  }

  // ---- 三、目录搜索 ----
  // 搜索覆盖段落标题与正文（toc.ts 的 haystack 把 node.title 与 node.text 都编进去了），
  // 「咬舌」是第 20 回独有的词（C20-039 的正文），命中的必须都是二十回的段落。
  await page.getByRole('button',{name:'打开目录'}).click();
  await page.locator('.toc-body').waitFor({timeout:20000});
  await page.getByRole('searchbox',{name:'搜索剧情段落'}).fill('咬舌');
  await page.waitForTimeout(200);
  const hitIds=await page.locator('.toc-card').evaluateAll(cards=>cards.map(c=>c.getAttribute('data-section')));
  assert.ok(hitIds.length>0&&hitIds.every(id=>String(id).startsWith('c20-')),`searching a chapter-20 phrase must land inside c20-*, got ${hitIds.join(',')}`);
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  // ---- 四、封底（第 20 回是当前末回 → 全书至此）----
  const lastNode=story[story.length-1].id, beforeLast=story[story.length-2].id;
  await seekSection(page,'c20-qiaoyu');
  await reading();
  await dismissLeaf(page,false,true);
  await page.evaluate(id=>window.__mapScene.engine.seek(id),beforeLast);
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent===id,beforeLast,{timeout:20000});
  await page.waitForTimeout(300);
  const arrived=await step(true);
  assert.ok(arrived==='终幕'||arrived===lastNode,`the book must end on ${lastNode}, got ${arrived}`);
  await page.waitForFunction(()=>!!document.querySelector('.leaf-sheet.leaf-back'),undefined,{timeout:8000});
  const backText=await page.locator('.leaf-sheet.leaf-back').innerText();
  assert.ok(backText.includes('全书至此'),`the back cover must say the book ends here until book 21 exists, got: ${backText.slice(0,80)}`);
  await page.screenshot({path:'artifacts/c20-back-cover.png',fullPage:true});

  // ---- 五、正文逐字出自底本 ----
  const source=readFileSync('docs/chapter20-source.txt','utf8');
  const strip=s=>s.replace(/[\s\u3000]/g,'');
  const stripMarks=s=>s.replace(/[「」『』“”‘’"'《》〈〉（）()·．.，,。：:；;！!？?、—…～~]/g,'');
  const hay=stripMarks(strip(source));
  let mismatched=0;
  for(const n of story){
    const needle=stripMarks(strip(n.text));
    if(!hay.includes(needle))mismatched++;
  }
  assert.equal(mismatched,0,`${mismatched} nodes carry text not in the source`);

  assert.equal(errors.length,0,JSON.stringify(errors));
  console.log(`Passed: chapter 20 — ${sections.length} sections walked, ${story.length} nodes, ${scenes.size} stages, TOC search, back cover correct, all node text verbatim.`);
}catch(e){
  console.error('Browser errors:',errors);
  console.error((await page.locator('body').innerText()).slice(0,3000));
  await page.screenshot({path:'artifacts/c20-failure.png',fullPage:true});
  throw e;
}finally{
  await context.close();
  await browser.close();
}
