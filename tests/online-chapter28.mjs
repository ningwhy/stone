/** 线上复验：第28回是否真的上线了（stone-direct.yan.pub）。
 *
 *  - 目录里有第28回与全部段落；
 *  - 逐段落点与场景与设计一致；
 *  - 封底与「下一回有没有上线」相称（共享断言，随回次自动变化）；
 *  - 图鉴里本回新出场角色（jiang_yuhan、yun_er）的立绘画得出来。
 *  存档用一次性 profile。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFileSync, mkdirSync, rmSync} from 'node:fs';
import {dismissPickup, dismissLeaf, clickSkipIfShown, clickForwardIfShown} from './lib/pickup.mjs';
import {seekSection, openToc} from './lib/toc.mjs';
import {assertBackCover, isBookFinalNode, bookEnds} from './lib/backcover.mjs';
import {onlineUrl, onlineTag, onlineArgs, ignoreTlsErrors, onlineProfile} from './lib/online.mjs';

const sections=JSON.parse(readFileSync('design/chapter28-sections.json','utf8'));
const NEW_CAST=["jiang_yuhan", "yun_er"];
const tag=onlineTag();
const profile=onlineProfile('c28');
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

  // ---- 一、目录 ----
  const toc=await openToc(page);
  const groups=await toc.locator('.toc-book-name').allTextContents();
  console.log(`${tag} chapter groups:`,JSON.stringify(groups));
  assert.ok(groups.some(g=>g.includes('第二十八回')),'chapter 28 missing from the online index');
  const bookName=groups.find(g=>g.includes('第二十八回'));
  await toc.locator('.toc-book-name').filter({hasText:bookName}).click();
  await page.waitForTimeout(300);
  const cards=await toc.locator('.toc-card').count();
  assert.equal(cards,sections.length,`chapter 28 must list ${sections.length} sections, got ${cards}`);
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  // ---- 二、逐段推进 ----
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
  console.log(`${tag} chapter-28 stages:`,[...scenes].sort().join(' / '));
  for(const stage of ["c6_wangchui", "entry", "fengziying_home", "qinfang", "wang", "yihong"]){
    assert.ok(scenes.has(stage),`the ${stage} stage must be reachable online`);
  }
  assert.equal(scenes.size,6,'all chapter-28 stages must be reachable online');

  // ---- 三、封底 ----
  const {lastNode,beforeLast}=bookEnds(28);
  await seekSection(page,'c28-daiyan');
  await reading();
  await dismissLeaf(page,false,true);
  await page.evaluate(id=>window.__mapScene.engine.seek(id),beforeLast);
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent===id,beforeLast,{timeout:30000});
  await page.waitForTimeout(300);
  await dismissLeaf(page,false,true);
  await clickSkipIfShown(page);
  const moved=await clickForwardIfShown(page);
  assert.ok(moved,'the reader must be able to walk into the last node');
  const endLabel=isBookFinalNode(lastNode)?'终幕':lastNode;
  await page.waitForFunction(label=>document.querySelector('.node-label')?.textContent===label,endLabel,{timeout:30000});
  const {backText}=await assertBackCover(page,28);
  console.log(`${tag} back cover:`,backText.replace(/\n+/g,' | ').slice(0,120));
  await page.screenshot({path:`artifacts/${tag}-c28-back-cover.png`,fullPage:true});

  // ---- 四、图鉴 ----
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
  assert.equal(broken.length,0,'every portrait in the online cast album must render');
  for(const actor of NEW_CAST){
    const hit=gallery.filter(i=>i.src.includes(`${actor}-portrait`));
    assert.equal(hit.length,1,`the new chapter-28 portrait ${actor}-portrait must be in the online album`);
    assert.ok(hit[0].w>0,`the new chapter-28 portrait ${actor}-portrait must render`);
  }
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  const realFailures=failed.filter(f=>!f.startsWith('403 '));
  console.log(`${tag} non-403 failed requests:`,realFailures.length);
  assert.deepEqual(errors,[],JSON.stringify(errors));
  console.log(`Passed (${tag}): chapter 28 is live — ${sections.length} sections, ${scenes.size} stages, TOC lists 第二十八回, ${gallery.length} portraits render (incl. ${NEW_CAST.length} new).`);
}catch(e){
  console.error('Browser errors:',errors);
  console.error((await page.locator('body').innerText()).slice(0,3000));
  await page.screenshot({path:`artifacts/${tag}-c28-failure.png`,fullPage:true});
  throw e;
}finally{
  await context.close();
  rmSync(profile,{recursive:true,force:true});
}
