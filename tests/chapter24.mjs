/** 第二十四回的定向验收：醉金刚轻财尚义侠，痴女儿遗帕惹相思。
 *
 *  与 tests/chapter23.mjs 同一模式，守住四件事：
 *  1. 十六段全部能推进到，且每段的落点节点与设计数据一致；
 *  2. 每一段的场景都在声明的场景表内（本回**四张新图**：卜家香料铺
 *     spice_shop、三街六巷 ni_er_lane、绮霰斋 qiranzhai、贾芸家
 *     jia_yun_home；其余六张 qinfang / yihong / capital / east /
 *     jialian_home / c6_wangchui 都是第 16-23 回已经建好的）；
 *  3. 封底与「下一回有没有上线」相称——第 25 回上线后，第 24 回的封底
 *     自动从「全书至此」变成「开启下一回 · 第二十五回」。用共享断言
 *     （tests/lib/backcover.mjs），它和产品代码看的是同一份数据；
 *  4. 369 个节点的正文逐字出自底本。
 *
 *  第 24 回新出场八人：贾芸、小红、倪二（醉金刚）、卜世仁、香菱、秋纹、
 *  碧痕、鸳鸯。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,readFileSync,mkdirSync} from 'node:fs';
import {dismissPickup, dismissLeaf, clickSkipIfShown, clickForwardIfShown} from './lib/pickup.mjs';
import {seekSection} from './lib/toc.mjs';
import {assertBackCover, assertNodeLabel, assertFoldedBackIsNotAPassThrough, bookEnds} from './lib/backcover.mjs';

const story=JSON.parse(readFileSync('design/chapter24-story.json','utf8'));
const sections=JSON.parse(readFileSync('design/chapter24-sections.json','utf8'));
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
    await page.screenshot({path:`artifacts/c24-${section.id}.png`,fullPage:true});
  }
  console.log('stages:',[...scenes].sort().join(' / '));
  // 本回用到的十张图都要走到——包括本回新建的四张。
  for(const stage of ['qinfang','yihong','capital','east','jialian_home','spice_shop','ni_er_lane','jia_yun_home','c6_wangchui','qiranzhai']){
    assert.ok(scenes.has(stage),`the ${stage} stage must be reachable`);
  }

  // ---- 二、段内连贯 ----
  const STAGES=['qinfang','yihong','capital','east','jialian_home','spice_shop','ni_er_lane','jia_yun_home','c6_wangchui','qiranzhai'];
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
  // 「醉金刚」是第 24 回独有的词（倪二自道「有人得罪了我醉金刚倪二的街坊」），
  // 原著其余二十三回一次也没出现过，命中的必须都是二十四回的段落。
  await page.getByRole('button',{name:'打开目录'}).click();
  await page.locator('.toc-body').waitFor({timeout:20000});
  await page.getByRole('searchbox',{name:'搜索剧情段落'}).fill('醉金刚');
  await page.waitForTimeout(200);
  const hitIds=await page.locator('.toc-card').evaluateAll(cards=>cards.map(c=>c.getAttribute('data-section')));
  assert.ok(hitIds.length>0&&hitIds.every(id=>String(id).startsWith('c24-')),`searching a chapter-24 phrase must land inside c24-*, got ${hitIds.join(',')}`);
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  // ---- 四、封底与下一回相称 ----
  // 末节点取**本回**的末节点，不是全书的末节点——见 bookEnds 的说明。
  const {lastNode,beforeLast}=bookEnds(24);
  await seekSection(page,'c24-yipa');
  await reading();
  await dismissLeaf(page,false,true);
  await page.evaluate(id=>window.__mapScene.engine.seek(id),beforeLast);
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent===id,beforeLast,{timeout:20000});
  await page.waitForTimeout(300);
  const arrived=await step(true);
  // 「终幕」只标在**全书**末节点上（src/App.tsx 的 state.index===story.length-1），
  // 不是标在「某一回的末节点」上。第 25 回上线后，第 24 回末节点的标签是
  // C24-369 而不是「终幕」—— 那是产品行为，不是缺陷。
  assert.ok(arrived===lastNode||arrived==='终幕',`book 24 must end on ${lastNode}, got ${arrived}`);
  await assertNodeLabel(page,lastNode);
  await assertBackCover(page,24);
  // 收起封底不能变成绕过封底的后门（详见 tests/lib/backcover.mjs）。
  await assertFoldedBackIsNotAPassThrough(page,24);
  await dismissLeaf(page,false,true);
  await page.screenshot({path:'artifacts/c24-back-cover.png',fullPage:true});

  // ---- 五、正文逐字出自底本 ----
  const source=readFileSync('docs/chapter24-source.txt','utf8');
  const strip=s=>s.replace(/[\s　]/g,'');
  const stripMarks=s=>s.replace(/[「」『』“”‘’"'《》〈〉（）()·．.，,。：:；;！!？?、—…～~]/g,'');
  const hay=stripMarks(strip(source));
  let mismatched=0;
  for(const n of story){
    const needle=stripMarks(strip(n.text));
    if(!hay.includes(needle))mismatched++;
  }
  assert.equal(mismatched,0,`${mismatched} nodes carry text not in the source`);

  assert.equal(errors.length,0,JSON.stringify(errors));
  console.log(`Passed: chapter 24 — ${sections.length} sections walked, ${story.length} nodes, ${scenes.size} stages, TOC search, back cover correct, all node text verbatim.`);
}catch(e){
  console.error('Browser errors:',errors);
  console.error((await page.locator('body').innerText()).slice(0,3000));
  await page.screenshot({path:'artifacts/c24-failure.png',fullPage:true});
  throw e;
}finally{
  await context.close();
  await browser.close();
}
