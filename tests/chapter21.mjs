/** 第二十一回的定向验收：贤袭人娇嗔箴宝玉、俏平儿软语救贾琏。
 *
 *  与 tests/chapter20.mjs 同一模式，守住四件事：
 *  1. 十二段全部能推进到，且每段的落点节点与设计数据一致；
 *  2. 每一段的场景都在声明的场景表内（本回五张图：yihong / night / dinner /
 *     wang / jialian_home，其中 yihong 是本回新建的怡红院专属图）；
 *  3. 封底与「下一回有没有上线」相称——第 21 回是当前末回，封底显示
 *     「全书至此」；第 22 回上线后自动变成「开启下一回」。用共享断言
 *     （tests/lib/backcover.mjs），它和产品代码看的是同一份数据；
 *  4. 139 个节点的正文逐字出自底本。
 *
 *  第 21 回新出场三人：紫鹃、翠缕、四儿。三人都有戏份，所以本回另外要验
 *  一次「查无此人」的样本已随之改变：browser-smoke 里那个样本必须换成
 *  一个第 21 回之前没有出现过的名字。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,readFileSync,mkdirSync} from 'node:fs';
import {dismissPickup, dismissLeaf, clickSkipIfShown, clickForwardIfShown} from './lib/pickup.mjs';
import {seekSection} from './lib/toc.mjs';
import {assertBackCover, assertFoldedBackIsNotAPassThrough, bookEnds} from './lib/backcover.mjs';

const story=JSON.parse(readFileSync('design/chapter21-story.json','utf8'));
const sections=JSON.parse(readFileSync('design/chapter21-sections.json','utf8'));
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
    await clickSkipIfShown(page);
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
    await clickSkipIfShown(page);
  }
  // 回末封底会在节点标签之后一帧才挂上，点「继续剧情」之前再收一次；
  // 仍没有该按钮说明这一段已走到本回末，连走该停下而不是挂超时。
  await dismissLeaf(page,false,true);
  if(!await clickForwardIfShown(page))return before;
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
    await page.screenshot({path:`artifacts/c21-${section.id}.png`,fullPage:true});
  }
  console.log('stages:',[...scenes].sort().join(' / '));
  // 本回用到的五张图都要走到。
  for(const stage of ['yihong','night','dinner','wang','jialian_home']){
    assert.ok(scenes.has(stage),`the ${stage} stage must be reachable`);
  }

  // ---- 二、段内连贯 ----
  const STAGES=['yihong','night','dinner','wang','jialian_home'];
  for(const section of sections){
    await seekSection(page,section.id);
    await reading();
    await dismissLeaf(page,false,true);
    const start=await node();
    let walked=0;
    for(let i=0;i<6;i++){
      const prev=await node();
      const now=await step();
      if(now===start||now===prev)break;
      walked++;
    }
    assert.ok(walked>0,`${section.id} must let the reader walk forward`);
    const after=await currentScene();
    assert.ok(STAGES.includes(after),`${section.id} walked into an unexpected stage ${after}`);
  }

  // ---- 三、目录搜索 ----
  // 搜索覆盖段落标题与正文（toc.ts 的 haystack 把 node.title 与 node.text 都编进去了），
  // 「焚花」是第 21 回独有的词（C21-068 一段的正文），命中的必须都是二十一回的段落。
  await page.getByRole('button',{name:'打开目录'}).click();
  await page.locator('.toc-body').waitFor({timeout:20000});
  await page.getByRole('searchbox',{name:'搜索剧情段落'}).fill('焚花');
  await page.waitForTimeout(200);
  const hitIds=await page.locator('.toc-card').evaluateAll(cards=>cards.map(c=>c.getAttribute('data-section')));
  assert.ok(hitIds.length>0&&hitIds.every(id=>String(id).startsWith('c21-')),`searching a chapter-21 phrase must land inside c21-*, got ${hitIds.join(',')}`);
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  // ---- 四、封底与下一回相称 ----
  // 末节点取**本回**的末节点，不是全书的末节点——见 bookEnds 的说明。
  const {lastNode,beforeLast}=bookEnds(21);
  await seekSection(page,'c21-chuangwai');
  await reading();
  await dismissLeaf(page,false,true);
  await page.evaluate(id=>window.__mapScene.engine.seek(id),beforeLast);
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent===id,beforeLast,{timeout:20000});
  await page.waitForTimeout(300);
  const arrived=await step(true);
  assert.ok(arrived===lastNode,`book 21 must end on ${lastNode}, got ${arrived}`);
  await assertBackCover(page,21);
  // 收起封底不能变成绕过封底的后门（详见 tests/lib/backcover.mjs）。
  await assertFoldedBackIsNotAPassThrough(page,21);
  await dismissLeaf(page,false,true);
  await page.screenshot({path:'artifacts/c21-back-cover.png',fullPage:true});

  // ---- 五、正文逐字出自底本 ----
  const source=readFileSync('docs/chapter21-source.txt','utf8');
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
  console.log(`Passed: chapter 21 — ${sections.length} sections walked, ${story.length} nodes, ${scenes.size} stages, TOC search, back cover correct, all node text verbatim.`);
}catch(e){
  console.error('Browser errors:',errors);
  console.error((await page.locator('body').innerText()).slice(0,3000));
  await page.screenshot({path:'artifacts/c21-failure.png',fullPage:true});
  throw e;
}finally{
  await context.close();
  await browser.close();
}
