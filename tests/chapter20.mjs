/** 第二十回的定向验收：王熙凤正言弹妒意、林黛玉俏语谑娇音。
 *
 *  与 tests/chapter19.mjs 同一模式，守住四件事：
 *  1. 七段全部能推进到，且每段的落点节点与设计数据一致；
 *  2. 每一段的场景都在声明的场景表内（night / c7_lixiang / wang / dinner）；
 *  3. 封底与「下一回有没有上线」相称——第 20 回刚上线时是「全书至此」，
 *     第 21 回上线后是「开启下一回」。用共享断言（tests/lib/backcover.mjs），
 *     它和产品代码看的是同一份数据；
 *  4. 39 个节点的正文逐字出自底本。
 *
 *  第 20 回新出场四人：贾环、赵姨娘、史湘云、麝月。前三人有戏份，
 *  麝月只守着篦头，所以本回另外要验一次「查无此人」的样本已随之改变：
 *  browser-smoke 里那个样本必须换成一个第 20 回之前没有出现过的名字。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,readFileSync,mkdirSync} from 'node:fs';
import {dismissPickup, dismissLeaf, clickSkipIfShown, clickForwardIfShown} from './lib/pickup.mjs';
import {seekSection} from './lib/toc.mjs';
import {assertBackCover, assertFoldedBackIsNotAPassThrough} from './lib/backcover.mjs';
import {chapterLeaves} from '../src/leaves.ts';

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
    // 「跳过移动」是一次演出按钮，可能在 isVisible() 与 click() 之间自己消失
    // （走完了就该变回「继续剧情」）。给 click 一个短超时并吞掉超时：跳过是
    // 可选的加速手段，不该因为按钮恰好收起而让整条回归挂 30 秒。
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
  // 「咬舌」是第 20 回独有的词（C20-039 的正文），命中的必须都是二十回的段落。
  await page.getByRole('button',{name:'打开目录'}).click();
  await page.locator('.toc-body').waitFor({timeout:20000});
  await page.getByRole('searchbox',{name:'搜索剧情段落'}).fill('咬舌');
  await page.waitForTimeout(200);
  const hitIds=await page.locator('.toc-card').evaluateAll(cards=>cards.map(c=>c.getAttribute('data-section')));
  assert.ok(hitIds.length>0&&hitIds.every(id=>String(id).startsWith('c20-')),`searching a chapter-20 phrase must land inside c20-*, got ${hitIds.join(',')}`);
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  // ---- 四、封底与下一回相称 ----
  //
  // ★ 末节点要取**本回**的末节点，不是全书的末节点。
  //   写 `story[story.length-1]` 的时候，第 20 回恰是全书末回，那是对的；
  //   第 21 回上线之后，全书末节点变成 C21-139，而这里要验的是**第 20 回**
  //   的封底——断言对象错位，封底根本不会出现（它翻在第 21 回末节点上）。
  //   判据与产品代码看同一份数据：`chapterLeaves()` 与 `src/App.tsx` 的
  //   leafData、`src/leaves.ts` 的 chapterLeaf 是同一份。
  const leaves=chapterLeaves();
  const firstIdx=story.findIndex(n=>n.id===leaves.get(20).firstNode);
  const lastIdx=story.findIndex(n=>n.id===leaves.get(20).lastNode);
  assert.ok(firstIdx>=0&&lastIdx>firstIdx,`book 20 must own a run of nodes, got ${firstIdx}..${lastIdx}`);
  const lastNode=story[lastIdx].id;
  const beforeLast=story[lastIdx-1].id;
  await seekSection(page,'c20-qiaoyu');
  await reading();
  await dismissLeaf(page,false,true);
  await page.evaluate(id=>window.__mapScene.engine.seek(id),beforeLast);
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent===id,beforeLast,{timeout:20000});
  await page.waitForTimeout(300);
  const arrived=await step(true);
  assert.ok(arrived===lastNode,`book 20 must end on ${lastNode}, got ${arrived}`);
  await assertBackCover(page,20);
  await page.screenshot({path:'artifacts/c20-back-cover.png',fullPage:true});

  // ---- 四之二、收起封底既不偷偷前进，也不把读者堵死 ----
  // 早先这里断言的是「收起封底后『继续剧情』必须消失」，理由是「读者再点
  // 一下就会跨进下一回，还跳过了下一回的封面」。那条理由经实测不成立：下一回
  // 的封面是到达那一回首个节点时自己翻出来的（src/leaves.ts 的 leafTrigger），
  // 与封底收没收起无关；而那个断言反倒把顶栏锁死，让回末节点上的读者再也
  // 推不动。现在这条断言守的是真正的不变量（详见 tests/lib/backcover.mjs）。
  await assertFoldedBackIsNotAPassThrough(page,20);
  // 断言最后把读者推进了下一回并翻出了它的封面，接着把它收掉，别挡住后面的检查。
  await dismissLeaf(page,false,true);

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
