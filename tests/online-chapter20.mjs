/** 线上复验：第二十回是否真的上线了。
 *
 *  走 stone-direct.yan.pub（DNS-only，不过 Cloudflare 托管挑战）。
 *  验的是「这一回特有的东西」，不是把全链路再跑一遍：
 *  - 目录里有没有第二十回、七段；
 *  - 七段能否逐段推进、场景是否与设计一致；
 *  - 封底是不是全书终幕（第二十一回还不存在）；
 *  - 图鉴里这一回新出场四人（贾环、赵姨娘、史湘云、麝月）的立绘是否画得出来。
 *
 *  存档用一次性 profile：持久化 profile 里存着读过的档，开书会落在回中间。
 */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,readFileSync,mkdirSync,rmSync} from 'node:fs';
import {dismissPickup, dismissLeaf} from './lib/pickup.mjs';
import {seekSection, openToc} from './lib/toc.mjs';
import {onlineUrl, onlineTag, onlineArgs, ignoreTlsErrors} from './lib/online.mjs';

const sections=JSON.parse(readFileSync('design/chapter20-sections.json','utf8'));
const story=JSON.parse(readFileSync('design/chapter20-story.json','utf8'));
// 第二十回新出场四人。麝月只有一场戏（守着篦头），但立绘同样要画得出来。
const NEW_CAST=['jia_huan','zhao_yiniang','shi_xiangyun','she_yue'];
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const tag=onlineTag();
// 一次性 profile：持久化 profile 里存着读过的档，开书会落在回中间。
const profile=`/tmp/wb-${tag}-c20`;
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
    const b=page.getByRole('button',{name:'跳过移动',exact:true});
    if(await b.isVisible().catch(()=>false)){await b.click();await page.waitForTimeout(80);}
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

  // ---- 一、目录里有第二十回，且列出七段 ----
  const toc=await openToc(page);
  const groups=await toc.locator('.toc-book-name').allTextContents();
  console.log(`${tag} chapter groups:`,JSON.stringify(groups));
  assert.ok(groups.some(g=>g.includes('第二十回')),'chapter 20 missing from the online index');
  // 目录左侧的回目名是中文数字。
  const bookName=groups.find(g=>g.includes('第二十回'));
  await toc.locator('.toc-book-name').filter({hasText:bookName}).click();
  await page.waitForTimeout(300);
  const cards=await toc.locator('.toc-card').count();
  console.log(`${tag} chapter-20 sections:`,cards);
  assert.equal(cards,sections.length,`chapter 20 must list ${sections.length} sections, got ${cards}`);
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
  console.log(`${tag} chapter-20 stages walked:`,[...scenes].sort().join(' / '));
  assert.equal(scenes.size,4,'all four chapter-20 stages must be reachable online');

  // ---- 三、封底是全书终幕 ----
  const lastNode=story[story.length-1].id, beforeLast=story[story.length-2].id;
  await seekSection(page,'c20-qiaoyu');
  await reading();
  await dismissLeaf(page,false,true);
  await page.evaluate(id=>window.__mapScene.engine.seek(id),beforeLast);
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent===id,beforeLast,{timeout:30000});
  await page.waitForTimeout(300);
  await dismissLeaf(page,false,true);
  const skip=page.getByRole('button',{name:'跳过移动',exact:true});
  if(await skip.isVisible().catch(()=>false)){await skip.click();await page.waitForTimeout(200);}
  await page.getByRole('button',{name:'继续剧情',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.node-label')?.textContent==='终幕',undefined,{timeout:30000});
  await page.waitForFunction(()=>!!document.querySelector('.leaf-sheet.leaf-back'),undefined,{timeout:15000});
  const backText=await page.locator('.leaf-sheet.leaf-back').innerText();
  console.log(`${tag} back cover:`,backText.replace(/\n+/g,' | ').slice(0,120));
  assert.ok(backText.includes('全书至此'),'the online back cover must end the book');
  assert.equal(await page.locator('.leaf-back .leaf-open').count(),0,'the online back cover must not offer a next book');
  await page.screenshot({path:`artifacts/${tag}-c20-back-cover.png`,fullPage:true});

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
  // 第二十回新出场四人的立绘必须真的在图鉴里，而且画得出来。
  for(const actor of NEW_CAST){
    const hit=gallery.filter(i=>i.src.includes(`${actor}-portrait`));
    assert.equal(hit.length,1,`the new chapter-20 portrait ${actor}-portrait must be in the online album`);
    assert.ok(hit[0].w>0,`the new chapter-20 portrait ${actor}-portrait must render`);
  }
  console.log(`${tag} new cast portraits online:`,NEW_CAST.join(', '));
  await page.getByRole('button',{name:'关闭弹窗'}).click();
  await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});

  const realFailures=failed.filter(f=>!f.startsWith('403 '));
  console.log(`${tag} non-403 failed requests:`,realFailures.length);
  for(const f of realFailures.slice(0,10))console.log('  ',f);
  assert.deepEqual(errors,[],JSON.stringify(errors));
  console.log(`Passed (${tag}): chapter 20 is live — ${sections.length} sections, ${scenes.size} stages, TOC lists 第二十回, back cover ends the book, ${gallery.length} portraits render (incl. ${NEW_CAST.length} new).`);
}catch(e){
  console.error('Browser errors:',errors);
  console.error((await page.locator('body').innerText()).slice(0,3000));
  await page.screenshot({path:`artifacts/${tag}-c20-failure.png`,fullPage:true});
  throw e;
}finally{
  await context.close();
  rmSync(profile,{recursive:true,force:true});
}
