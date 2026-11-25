/** 线上复验：第二十四回是否真的上线了。
 *
 *  走 stone-direct.yan.pub（DNS-only，不过 Cloudflare 托管挑战）。
 *  验的是「这一回特有的东西」，不是把全链路再跑一遍：
 *  - 目录里有没有第二十四回、十六段；
 *  - 十六段能否逐段推进、场景是否与设计一致（含本回新建的四张图
 *    spice_shop / ni_er_lane / qiranzhai / jia_yun_home —— 其余六张
 *    qinfang / yihong / capital / east / jialian_home / c6_wangchui
 *    都是第 16-23 回建好的）；
 *  - 封底与「下一回有没有上线」相称：第二十五回上线后，第二十四回封底
 *    应当显示「开启下一回 · 第二十五回」，而不再是「全书至此」；
 *  - 图鉴里这一回新出场八人（贾芸、小红、倪二、卜世仁、香菱、秋纹、
 *    碧痕、鸳鸯）的立绘是否画得出来。
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

const sections=JSON.parse(readFileSync('design/chapter24-sections.json','utf8'));
// 第二十四回新出场八人，都有戏份。
const NEW_CAST=['jia_yun','xiaohong','ni_er','bu_shi_ren','xiangling','qiuwen','bihen','yuan_yang'];
const tag=onlineTag();
// 一次性 profile：持久化 profile 里存着读过的档，开书会落在回中间。
const profile=onlineProfile('c24');
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

  // ---- 一、目录里有第二十四回，且列出十六段 ----
  const toc=await openToc(page);
  const groups=await toc.locator('.toc-book-name').allTextContents();
  console.log(`${tag} chapter groups:`,JSON.stringify(groups));
  assert.ok(groups.some(g=>g.includes('第二十四回')),'chapter 24 missing from the online index');
  // 目录左侧的回目名是中文数字。
  const bookName=groups.find(g=>g.includes('第二十四回'));
  await toc.locator('.toc-book-name').filter({hasText:bookName}).click();
  await page.waitForTimeout(300);
  const cards=await toc.locator('.toc-card').count();
  console.log(`${tag} chapter-24 sections:`,cards);
  assert.equal(cards,sections.length,`chapter 24 must list ${sections.length} sections, got ${cards}`);
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
  console.log(`${tag} chapter-24 stages walked:`,[...scenes].sort().join(' / '));
  // 本回用到的十张图都要走到——包括本回新建的四张。
  for(const stage of ['qinfang','yihong','capital','east','jialian_home','spice_shop','ni_er_lane','jia_yun_home','c6_wangchui','qiranzhai']){
    assert.ok(scenes.has(stage),`the ${stage} stage must be reachable online`);
  }
  assert.equal(scenes.size,10,'all ten chapter-24 stages must be reachable online');

  // ---- 三、封底与下一回相称 ----
  const {lastNode,beforeLast}=bookEnds(24);
  await seekSection(page,'c24-yipa');
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
  // 第二十五回上线后，第二十四回只是「某一回的末回」，标签是 C24-369。
  // 用共享判定读产品代码的 story 来分这两种情况。
  const endLabel=isBookFinalNode(lastNode)?'终幕':lastNode;
  await page.waitForFunction(label=>document.querySelector('.node-label')?.textContent===label,endLabel,{timeout:30000});
  const {backText}=await assertBackCover(page,24);
  console.log(`${tag} back cover:`,backText.replace(/\n+/g,' | ').slice(0,120));
  await page.screenshot({path:`artifacts/${tag}-c24-back-cover.png`,fullPage:true});

  // ---- 四、图鉴里的立绘都画得出来 ----
  // 封底是模态纸页，盖在舞台上会把顶栏的「设置」也一起挡住——先把它收起来。
  // 用它自己的「收起封底」按钮：通用的"关掉任何弹层"会点到别的按钮上。
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
  // 第二十四回新出场八人的立绘必须真的在图鉴里，而且画得出来。
  for(const actor of NEW_CAST){
    const hit=gallery.filter(i=>i.src.includes(`${actor}-portrait`));
    assert.equal(hit.length,1,`the new chapter-24 portrait ${actor}-portrait must be in the online album`);
    assert.ok(hit[0].w>0,`the new chapter-24 portrait ${actor}-portrait must render`);
  }
  console.log(`${tag} new cast portraits online:`,NEW_CAST.join(', '));
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  const realFailures=failed.filter(f=>!f.startsWith('403 '));
  console.log(`${tag} non-403 failed requests:`,realFailures.length);
  for(const f of realFailures.slice(0,10))console.log('  ',f);
  assert.deepEqual(errors,[],JSON.stringify(errors));
  console.log(`Passed (${tag}): chapter 24 is live — ${sections.length} sections, ${scenes.size} stages (incl. 4 new maps), TOC lists 第二十四回, back cover opens 第二十五回, ${gallery.length} portraits render (incl. ${NEW_CAST.length} new).`);
}catch(e){
  console.error('Browser errors:',errors);
  console.error((await page.locator('body').innerText()).slice(0,3000));
  await page.screenshot({path:`artifacts/${tag}-c24-failure.png`,fullPage:true});
  throw e;
}finally{
  await context.close();
  rmSync(profile,{recursive:true,force:true});
}
