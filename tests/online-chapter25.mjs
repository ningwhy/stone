/** 线上复验：第二十五回是否真的上线了。
 *
 *  走 stone-direct.yan.pub（DNS-only，不过 Cloudflare 托管挑战）。
 *  验的是「这一回特有的东西」，不是把全链路再跑一遍：
 *  - 目录里有没有第二十五回、十三段；
 *  - 十三段能否逐段推进、场景是否与设计一致（含本回新建的赵姨娘房
 *    zhao_room —— 其余四张 yihong / qinfang / wang / entry 都是前面
 *    各回建好的）；
 *  - 封底与「下一回有没有上线」相称：第二十五回现在是全书末回，封底
 *    应当显示「全书至此」，且没有「开启下一回」按钮；
 *  - 图鉴里这一回新出场两人（马道婆 ma_dao_po、彩霞 cai_xia）的立绘
 *    是否画得出来。
 *
 *  存档用一次性 profile：持久化 profile 里存着读过的档，开书会落在回中间。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFileSync, mkdirSync, rmSync} from 'node:fs';
import {dismissPickup, dismissLeaf, clickSkipIfShown, clickForwardIfShown} from './lib/pickup.mjs';
import {seekSection, openToc} from './lib/toc.mjs';
import {assertBackCover, isBookFinalNode, bookEnds} from './lib/backcover.mjs';
import {onlineUrl, onlineTag, onlineArgs, ignoreTlsErrors, onlineProfile} from './lib/online.mjs';

const sections=JSON.parse(readFileSync('design/chapter25-sections.json','utf8'));
// 第二十五回新出场两人，都有戏份。
const NEW_CAST=['ma_dao_po','cai_xia'];
const tag=onlineTag();
// 一次性 profile：持久化 profile 里存着读过的档，开书会落在回中间。
const profile=onlineProfile('c25');
rmSync(profile,{recursive:true,force:true});
const context=await chromium.launchPersistentContext(profile,{
  headless:!process.env.ONLINE_HEADED,channel:'chrome',viewport:{width:1440,height:900},reducedMotion:'reduce',
  ignoreHTTPSErrors:ignoreTlsErrors(),args:onlineArgs()});
const page=await context.newPage(),errors=[],failed=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
page.on('response',r=>{if(r.status()>=400)failed.push(`${r.status()} ${r.url().slice(0,110)}`);});
mkdirSync('artifacts',{recursive:true});

const node=()=>page.locator('.node-label').textContent();
const currentScene=()=>page.locator('.game-map').getAttribute('data-scene-ready');

async function reading(){
  await dismissPickup(page);
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:120000});
  for(let i=0;i<5;i++){
    await clickSkipIfShown(page);
  }
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:120000});
  await dismissLeaf(page,false);
}

try{
  await page.goto(onlineUrl(),{waitUntil:'commit',timeout:120000});
  await page.waitForSelector('.toc-trigger',{timeout:240000});
  await reading();
  await dismissLeaf(page,false,true);
  console.log(`${tag} node:`,await node());

  // ---- 一、目录里有第二十五回，且列出十三段 ----
  const toc=await openToc(page);
  const groups=await toc.locator('.toc-book-name').allTextContents();
  console.log(`${tag} chapter groups:`,JSON.stringify(groups));
  assert.ok(groups.some(g=>g.includes('第二十五回')),'chapter 25 missing from the online index');
  // 目录左侧的回目名是中文数字。
  const bookName=groups.find(g=>g.includes('第二十五回'));
  await toc.locator('.toc-book-name').filter({hasText:bookName}).click();
  await page.waitForTimeout(300);
  const cards=await toc.locator('.toc-card').count();
  console.log(`${tag} chapter-25 sections:`,cards);
  assert.equal(cards,sections.length,`chapter 25 must list ${sections.length} sections, got ${cards}`);
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  // ---- 二、逐段推进：落点与场景都要对 ----
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
  }
  console.log(`${tag} chapter-25 stages walked:`,[...scenes].sort().join(' / '));
  for(const stage of ['yihong','qinfang','wang','entry','zhao_room']){
    assert.ok(scenes.has(stage),`the ${stage} stage must be reachable online`);
  }
  assert.equal(scenes.size,5,'all five chapter-25 stages must be reachable online');

  // ---- 三、封底与下一回相称 ----
  const {lastNode,beforeLast}=bookEnds(25);
  await seekSection(page,'c25-jie');
  await reading();
  await dismissLeaf(page,false,true);
  await page.evaluate(id=>window.__mapScene.engine.seek(id),beforeLast);
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent===id,beforeLast,{timeout:30000});
  await page.waitForTimeout(300);
  await dismissLeaf(page,false,true);
  await clickSkipIfShown(page);
  const moved=await clickForwardIfShown(page);
  assert.ok(moved,'the reader must be able to walk into the last node');
  // 「终幕」只标在**全书**末节点上（src/App.tsx 的 state.index===story.length-1）。
  // 第二十五回现在是全书末回，所以标签恰好就是「终幕」。用共享判定读产品
  // 代码的 story 来分「全书末回」与「某一回的末回」这两种情况。
  const endLabel=isBookFinalNode(lastNode)?'终幕':lastNode;
  await page.waitForFunction(label=>document.querySelector('.node-label')?.textContent===label,endLabel,{timeout:30000});
  const {backText}=await assertBackCover(page,25);
  console.log(`${tag} back cover:`,backText.replace(/\n+/g,' | ').slice(0,120));
  await page.screenshot({path:`artifacts/${tag}-c25-back-cover.png`,fullPage:true});

  // ---- 四、图鉴里的立绘都画得出来 ----
  // 封底是模态纸页，盖在舞台上会把顶栏的「设置」也一起挡住——先把它收起来。
  const fold=page.locator('.leaf-back .leaf-fold');
  if(await fold.count()&&await fold.isVisible().catch(()=>false))await fold.click();
  await page.locator('.leaf-sheet.leaf-back').waitFor({state:'detached',timeout:10000}).catch(()=>{});
  await page.getByRole('button',{name:'设置',exact:true}).click();
  await page.getByRole('button',{name:'人物图鉴',exact:true}).click();
  await page.locator('.cast-gallery').waitFor({timeout:30000});
  await page.locator('.cast-gallery').evaluate(e=>{e.scrollTop=0;});
  await page.waitForFunction(()=>[...document.querySelectorAll('.cast-gallery img')].every(i=>i.complete&&i.naturalWidth>0),undefined,{timeout:60000});
  const gallery=await page.locator('.cast-gallery img').evaluateAll(imgs=>imgs.map(i=>({src:i.getAttribute('src'),w:i.naturalWidth})));
  const broken=gallery.filter(i=>i.w===0);
  console.log(`${tag} cast album: ${gallery.length} portraits, ${broken.length} broken`);
  assert.equal(broken.length,0,'every portrait in the online cast album must render');
  for(const actor of NEW_CAST){
    const hit=gallery.filter(i=>i.src.includes(`${actor}-portrait`));
    assert.equal(hit.length,1,`the new chapter-25 portrait ${actor}-portrait must be in the online album`);
    assert.ok(hit[0].w>0,`the new chapter-25 portrait ${actor}-portrait must render`);
  }
  console.log(`${tag} new cast portraits online:`,NEW_CAST.join(', '));
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  const realFailures=failed.filter(f=>!f.startsWith('403 '));
  console.log(`${tag} non-403 failed requests:`,realFailures.length);
  for(const f of realFailures.slice(0,10))console.log('  ',f);
  assert.deepEqual(errors,[],JSON.stringify(errors));
  console.log(`Passed (${tag}): chapter 25 is live — ${sections.length} sections, ${scenes.size} stages (incl. 1 new map), TOC lists 第二十五回, back cover ends the book, ${gallery.length} portraits render (incl. ${NEW_CAST.length} new).`);
}catch(e){
  console.error('Browser errors:',errors);
  console.error((await page.locator('body').innerText()).slice(0,3000));
  await page.screenshot({path:`artifacts/${tag}-c25-failure.png`,fullPage:true});
  throw e;
}finally{
  await context.close();
  rmSync(profile,{recursive:true,force:true});
}
