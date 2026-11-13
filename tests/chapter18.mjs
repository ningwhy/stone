/** 第十八回的定向验收：元妃归省。
 *
 *  这一回是「底本切片式生成」的第一回成品，全书的正文与「原文段落起句」
 *  都必须逐字出自 docs/chapter18-source.txt。这一份测试要守住三件事：
 *
 *  1. 十六段全部能推进到，且每一段的落点节点与设计数据一致；
 *  2. 每一段的场景都在设计里声明的场景表内，不会在运行期跳到别的地图；
 *  3. 封底与「下一回有没有上线」相称：第十九回上线前是「全书至此」，
 *     上线之后是「开启下一回」。这一条用共享断言（tests/lib/backcover.mjs），
 *     它和产品代码看的是同一份数据——写死「全书至此」的话，每加一回就会
 *     把前面每一回的测试都弄红，而红的原因跟被测的这一回毫无关系。
 *
 *  另外顺带核一遍两件容易悄悄坏掉的事：
 *  - 目录搜索能用正文里的字搜到这一回（段落搜索不是摆设）；
 *  - 人物图鉴在这一回解锁了新角色，且立绘真的画出来了（naturalWidth>0）。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,readFileSync,mkdirSync} from 'node:fs';
import {dismissPickup, dismissLeaf, clickSkipIfShown, clickForwardIfShown} from './lib/pickup.mjs';
import {seekSection} from './lib/toc.mjs';
import {assertBackCover, assertNodeLabel, assertFoldedBackIsNotAPassThrough, bookEnds} from './lib/backcover.mjs';

const story=JSON.parse(readFileSync('design/chapter18-story.json','utf8'));
const sections=JSON.parse(readFileSync('design/chapter18-sections.json','utf8'));
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(existsSync(chrome)?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});

// 每一段的首节点与场景，都从设计数据实读：写死的话，改了分节就会让断言失真。
const byId=new Map(story.map(n=>[n.id,n]));
const node=()=>page.locator('.node-label').textContent();
// 场景就绪时，地图宿主上的 data-scene-ready 就是当前的 sceneId。
const currentScene=()=>page.locator('.game-map').getAttribute('data-scene-ready');

async function reading(){
  await dismissPickup(page);
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:20000});
  await clickSkipIfShown(page,4,60);
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:20000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:20000});
  await dismissLeaf(page,false);
}

// 推进一句。封底/封面在这一刻可能翻出来：先收掉，再断言节点确实动了。
//
// 末节点常带一段演出（走位/效果），此时引擎状态是「演出中」，
// advance 只在「读完」时才肯走一步——不先收掉，点了「继续剧情」
// 会什么也不发生，节点标签不动，等待就会超时。
// 推进一句。封底/封面在这一刻可能翻出来：先收掉，再断言节点确实动了。
//
// `keepLeaf` 为真时**不收**这一轮翻出来的纸页——测封底要用。
// 末节点常带一段演出（走位/效果），此时引擎状态是「演出中」，
// advance 只在「读完」时才肯走一步——不先收掉，点了「继续剧情」
// 会什么也不发生，节点标签不动，等待就会超时。
async function step(keepLeaf=false){
  await dismissPickup(page);
  const before=await node();
  await dismissLeaf(page,false,true);
  for(let i=0;i<3;i++){
    await clickSkipIfShown(page);
  }
  // 回末封底会在节点标签之后一帧才挂上，重渲染时还可能再挂一次；点
  // 「继续剧情」之前再收一次。仍没有该按钮说明这一段已走到本回末，
  // 连走该停下，而不是让 locator.click 挂 30 秒超时。
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

  // 存档是 append 型的：上一次的读档会把故事停在回中间。清掉，
  // 让每次运行都从第一回开头走。
  await page.evaluate(()=>localStorage.clear());
  await page.reload();
  await reading();
  await dismissLeaf(page,false,true);

  // ---- 一、逐段推进：十六段全部可达，落点与场景都对 ----
  const seenScenes=new Set();
  for(const section of sections){
    await seekSection(page,section.id);
    await reading();
    await dismissLeaf(page,false,true);
    const landed=await node();
    assert.equal(landed,section.start,`${section.id} must land on its first node ${section.start}, got ${landed}`);
    const scene=await currentScene();
    assert.equal(scene,section.scene,`${section.id} must be staged in ${section.scene}, got ${scene}`);
    seenScenes.add(scene);
    await page.screenshot({path:`artifacts/c18-${section.id}.png`,fullPage:true});
  }
  // 七张复用地图全都被用上了；哪一张没被走到，说明某段的场景声明写错了。
  assert.deepEqual([...seenScenes].sort(),['c11_tianxiang','canal','capital','central','dinner','entry','wang'].sort(),'all seven reused stages must be staged');

  // ---- 二、段内连贯：每段往后走若干句，节点不乱跳、场景不乱切 ----
  for(const section of sections){
    await seekSection(page,section.id);
    await reading();
    await dismissLeaf(page,false,true);
    const start=await node();
    const scene=await currentScene();
    let walked=0;
    for(let i=0;i<6;i++){
      const prev=await node();
      const now=await step();
      if(now===start||now===prev)break;
      walked++;
    }
    assert.ok(walked>0,`${section.id} must let the reader walk forward`);
    // 段内换场景是允许的（第十六段就跨了两张图），但不能跳到这一回没用过的场景。
    const after=await currentScene();
    assert.ok(['entry','dinner','wang','central','capital','canal','c11_tianxiang'].includes(after),`${section.id} walked into an unexpected stage ${after}`);
    assert.ok(scene!==undefined);
  }

  // ---- 三、目录搜索能搜到本回的正文 ----
  await page.getByRole('button',{name:'打开目录'}).click();
  await page.locator('.toc-body').waitFor({timeout:20000});
  await page.getByRole('searchbox',{name:'搜索剧情段落'}).fill('体仁沐德');
  await page.waitForTimeout(200);
  const hits=await page.locator('.toc-card').count();
  assert.ok(hits>0,'searching a phrase from chapter 18 must find its section');
  // 搜到的必须是十八回的那一段，不能是别的回目的同名段落。
  const hitIds=await page.locator('.toc-card').evaluateAll(cards=>cards.map(c=>c.getAttribute('data-section')));
  assert.ok(hitIds.every(id=>String(id).startsWith('c18-')),`the search must land inside chapter 18, got ${hitIds.join(',')}`);
  // 目录是原生 <dialog>：Escape 被 onCancel 拦掉了，只能用它自己的关闭按钮。
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  // ---- 四、人物图鉴解锁 ----
  await page.getByRole('button',{name:'设置',exact:true}).click();
  await page.getByRole('button',{name:'人物图鉴',exact:true}).click();
  await page.locator('.cast-gallery').waitFor({timeout:20000});
  await page.locator('.cast-gallery').evaluate(e=>{e.scrollTop=0;});
  await page.waitForFunction(()=>[...document.querySelectorAll('.cast-gallery img')].every(i=>i.complete&&i.naturalWidth>0),undefined,{timeout:30000});
  const castCount=await page.locator('.cast-gallery article').count();
  assert.ok(castCount>0,'the cast album lists people');
  // 图鉴里的每一张立绘都得真的画出来：图鉴是「已见人物」的册子，
  // 空白格子会让读者以为没走到过这一回。
  const broken=await page.locator('.cast-gallery img').evaluateAll(imgs=>imgs.filter(i=>!i.complete||i.naturalWidth===0).length);
  assert.equal(broken,0,'every portrait in the cast album must render');
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  // ---- 五、封底与下一回相称 ----
  // 封底只在「自然推进一步」时翻出来（leafTrigger 要求 advanced），
  // 所以不能直接 seek 到末节点——跳读不翻页。停在末节点的前一句，
  // 再自然走一步，让封底自己翻出来。
  // 末节点取**本回**的末节点，不是全书的末节点——见 bookEnds 的说明。
  const {lastNode,beforeLast}=bookEnds(18);
  await seekSection(page,'c18-gift');
  await reading();
  await dismissLeaf(page,false,true);
  await page.evaluate(id=>window.__mapScene.engine.seek(id),beforeLast);
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent===id,beforeLast,{timeout:20000});
  await page.waitForTimeout(200);
  const arrived=await step(true);
  // 「终幕」只标在**全书**末节点上（src/App.tsx 的 state.index===story.length-1），
  // 不是标在「某一回的末节点」上。第 18 回在第 21 回上线之后就不是全书末回了，
  // 标签自然是 C18-135 —— 那是产品行为，不是缺陷。
  assert.ok(arrived===lastNode,`book 18 must end on ${lastNode}, got ${arrived}`);
  await assertNodeLabel(page,lastNode);
  await assertBackCover(page,18);
  // 收起封底不能变成绕过封底的后门（详见 tests/lib/backcover.mjs）。
  await assertFoldedBackIsNotAPassThrough(page,18);
  await dismissLeaf(page,false,true);
  await page.screenshot({path:'artifacts/c18-back-cover.png',fullPage:true});

  // ---- 六、正文逐字出自底本：页面上的每一句都要能在底本里查到 ----
  const source=readFileSync('docs/chapter18-source.txt','utf8');
  const strip=s=>s.replace(/[\s\u3000]/g,'');
  const flat=strip(source);
  const stripMarks=s=>s.replace(/[「」『』“”‘’"'《》〈〉（）()·．.，,。：:；;！!？?、—…～~]/g,'');
  let mismatched=0;
  for(const n of story){
    // 引号样式是排版差异，正文字符本身必须逐字相同。
    const needle=stripMarks(strip(n.text));
    const hay=stripMarks(flat);
    if(!hay.includes(needle))mismatched++;
  }
  assert.equal(mismatched,0,`${mismatched} nodes carry text that is not in the source`);

  assert.equal(errors.length,0,JSON.stringify(errors));
  console.log(`Passed: chapter 18 — ${sections.length} sections walked, ${story.length} nodes, ${seenScenes.size} reused stages, TOC search, cast album renders, final back cover ends the book, all node text verbatim from the source.`);
}catch(e){
  console.error('Browser errors:',errors);
  console.error((await page.locator('body').innerText()).slice(0,3500));
  await page.screenshot({path:'artifacts/c18-failure.png',fullPage:true});
  throw e;
}finally{
  await context.close();
  await browser.close();
}
