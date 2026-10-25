import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,mkdirSync,readFileSync} from 'node:fs';
const story=[1,2,3,4].flatMap(n=>JSON.parse(readFileSync(`design/chapter0${n}-story.json`,'utf8')));
const chapters=[...JSON.parse(readFileSync('design/chapter03-sections.json','utf8')),...JSON.parse(readFileSync('design/chapter04-sections.json','utf8'))];
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(existsSync(chrome)?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});mkdirSync('artifacts',{recursive:true});
const saved=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('honglou-four-chapters:v4')));
const node=()=>page.locator('.node-label').textContent();
// A paused stage must hold still. Read the canvas pixels inside the page instead of
// comparing Playwright element screenshots: the element screenshot path re-rasterises
// the canvas layer, and that re-rasterisation shows GPU rounding noise even when the
// painted frame is byte-identical, so it would report a false difference.
const canvasPixels=()=>page.evaluate(()=>{const canvas=document.querySelector('canvas');const data=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;let hash=2166136261;for(let i=0;i<data.length;i++){hash^=data[i];hash=Math.imul(hash,16777619);}return hash>>>0;});
const reading=async()=>{await page.locator('.loading-screen').waitFor({state:'detached',timeout:20000});for(let i=0;i<4;i++){const skip=page.getByRole('button',{name:'跳过移动',exact:true});if(await skip.isVisible()){await skip.click();await page.waitForTimeout(60);}}await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim());await page.locator('.game-map[data-scene-ready]').waitFor();};
async function fit(){const control=await page.getByRole('button',{name:'继续剧情',exact:true}).boundingBox();assert.ok(control);const viewport=page.viewportSize();assert.ok(control.y+control.height<=viewport.height,`controls below screen: ${control.y+control.height}>${viewport.height}`);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
async function next(skip=true){const before=await node();await page.getByRole('button',{name:'继续剧情',exact:true}).click();await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent!==id,before);const b=page.getByRole('button',{name:'跳过移动',exact:true});if(skip&&await b.isVisible())await b.click();await reading();}
try{
 await page.goto(process.env.TEST_URL??'http://127.0.0.1:5173');await reading();assert.equal(await node(),'C1-001');await fit();await page.screenshot({path:'artifacts/chapter-opening.png',fullPage:true});
 const visited=new Set();
 for(let i=0;i<story.length;i++){
  assert.equal(await node(),i===story.length-1?'终幕':story[i].id);const data=await saved();assert.equal(data.node,story[i].id);visited.add(data.state.sceneId);assert.equal(Math.round((await page.locator('.dialogue-panel').boundingBox()).height),206);
  if(story[i].id==='F001'){assert.equal(data.state.actors.feng.visible,false);assert.equal(await page.locator('.dialogue-type').textContent(),'画外');}
  if(['C1-012','C1-025','C1-039','C2-018','C2-023'].includes(story[i].id))await page.screenshot({path:`artifacts/prequel-${story[i].id}.png`,fullPage:true});
  if(story[i].id==='B010')await page.screenshot({path:'artifacts/chapter-first-meeting.png',fullPage:true});
  if(story[i].id==='F006')await page.screenshot({path:'artifacts/chapter-feng.png',fullPage:true});
  if(story[i].id==='U009')await page.screenshot({path:'artifacts/chapter-rongxi.png',fullPage:true});
  if(story[i].id==='T012')await page.screenshot({path:'artifacts/chapter-night.png',fullPage:true});
  if(i<story.length-1)await next();
 }
 // The prequel gets its own scene atlas and every section can be selected.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c1-home');await reading();await page.getByRole('button',{name:'本回行迹',exact:true}).click();await page.locator('.journey-sites').waitFor();assert.equal(await page.locator('.journey-site').count(),6);await page.screenshot({path:'artifacts/prequel-journey.png',fullPage:true});await page.getByRole('button',{name:'当前场景',exact:true}).click();
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('letter');await reading();while(await node()!=='END')await next();
 // The walk stops at the old chapter-three finale, so its history stops there too.
 // That finale is no longer the end of the book: reloading offers to continue, not restart.
 assert.equal(visited.size,22);assert.equal((await saved()).state.history.length,242);await page.reload();await reading();assert.equal(await node(),'END');await page.getByRole('button',{name:'继续剧情',exact:true}).waitFor();
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption(chapters[2].id);await reading();assert.equal(await node(),'N005');const height=(await page.locator('.map-panel').boundingBox()).height;
 await page.getByRole('button',{name:'继续剧情',exact:true}).click();await page.getByRole('button',{name:'跳过移动',exact:true}).waitFor();assert.equal((await page.locator('.map-panel').boundingBox()).height,height);await page.locator('.map-action-cue').waitFor();await page.screenshot({path:'artifacts/chapter-action.png',fullPage:true});
 await page.getByRole('button',{name:'暂停',exact:true}).click();await page.waitForTimeout(120);const paused=await canvasPixels();await page.waitForTimeout(200);assert.equal(await canvasPixels(),paused);await page.getByRole('button',{name:'继续演出',exact:true}).click();await reading();assert.equal(await node(),'N006');

 // Map dominates the viewport; toolbar stays clickable with both portrait groups present.
 const mapBox=await page.locator('.map-panel').boundingBox();assert.ok(mapBox.height>780&&mapBox.width>1380);
 const zoomBefore=Number(await page.locator('.game-map').getAttribute('data-zoom'));
 await page.getByRole('button',{name:'放大地图',exact:true}).click();assert.ok(Number(await page.locator('.game-map').getAttribute('data-zoom'))>zoomBefore);
 await page.getByRole('button',{name:'缩小地图',exact:true}).click();assert.equal(await page.locator('dialog[open]').count(),0);
 for(let i=0;i<8;i++)await page.getByRole('button',{name:'缩小地图',exact:true}).click();
 assert.ok(Number(await page.locator('.game-map').getAttribute('data-min-actor-pixels'))>=47.9);assert.ok(Number(await page.locator('.game-map').getAttribute('data-label-pixels'))>=11.9);
 await page.screenshot({path:'artifacts/map-min-zoom.png',fullPage:true});
 await page.getByRole('button',{name:'回到剧情镜头'}).click();
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();await page.locator('.world-map').waitFor();await page.waitForFunction(()=>document.querySelectorAll('.world-location image[data-loaded=true]').length===9);
 assert.equal(await page.locator('.world-location').count(),9);
 await page.getByRole('button',{name:'查看贾赦东院地点',exact:true}).click();assert.ok((await page.locator('.world-detail').textContent()).includes('黑油大门'));
 assert.equal(await node(),'N006');await page.getByRole('button',{name:'关闭地点详情'}).click();
 await page.screenshot({path:'artifacts/rongguo-overview.png',fullPage:true});
 await page.getByRole('button',{name:'当前场景',exact:true}).click();
 // A real sequential boundary must animate along the estate roads; pause freezes the token.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption(chapters[3].id);await reading();
 while(await node()!=='F015')await next();
 await page.getByRole('button',{name:'继续剧情',exact:true}).click();await page.locator('[data-testid=world-travel-route]').waitFor();
 await page.getByRole('button',{name:'暂停',exact:true}).click();const travelPosition=await page.locator('.world-traveler').getAttribute('transform');await page.waitForTimeout(200);assert.equal(await page.locator('.world-traveler').getAttribute('transform'),travelPosition);
 await page.screenshot({path:'artifacts/rongguo-travel.png',fullPage:true});
 await page.getByRole('button',{name:'继续演出',exact:true}).click();await page.waitForFunction(()=>!document.querySelector('[data-testid=world-travel-route]'));await reading();assert.equal(await node(),'U001');
 await page.getByRole('button',{name:'设置',exact:true}).click();await page.getByRole('checkbox').check();assert.equal(await page.locator('dialog h2').textContent(),'阅读设置');await page.locator('dialog').getByRole('combobox').selectOption('2');await page.getByRole('checkbox').uncheck();await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'设置',exact:true}).click();await page.getByRole('button',{name:'地图地点',exact:true}).click();assert.equal(await page.locator('.atlas-body article').count(),22);await page.keyboard.press('Escape');

 // A complete painted cast directory makes early characters discoverable after resuming.
 await page.getByRole('button',{name:'设置',exact:true}).click();await page.getByRole('button',{name:'人物图鉴',exact:true}).click();
 assert.equal(await page.locator('.cast-gallery article').count(),38);
 assert.equal(await page.locator('.cast-gallery img').count(),38);
 await page.screenshot({path:'artifacts/cast-directory.png',fullPage:true});
 await page.locator('.cast-gallery article').filter({has:page.locator('strong',{hasText:'冷子兴'})}).getByRole('button',{name:'定位出场 →',exact:true}).click();await reading();assert.equal((await saved()).state.actors.leng.visible,true);assert.ok((await node()).startsWith('C2-'));await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('prologue');await reading();await next();await next();await next();assert.equal(await node(),'P004');
 assert.match(await page.locator('.speaker-portrait img').getAttribute('src'),/^\/assets\/rongguo\/leng-portrait\.webp\?v=[a-f0-9]+$/);
 await page.screenshot({path:'artifacts/leng-zixing.png',fullPage:true});
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();await page.getByRole('button',{name:'查看王熙凤院地点',exact:true}).click();
 assert.ok((await page.locator('.world-detail').textContent()).includes('粉油大影壁'));
 await page.getByRole('button',{name:'从此处剧情开始 →',exact:true}).click();await reading();assert.equal(await node(),'U019');
 await page.screenshot({path:'artifacts/feng-courtyard-gate.png',fullPage:true});
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();
 assert.equal(await page.getByRole('button',{name:'查看王熙凤院地点',exact:true}).getAttribute('data-asset'),'estate-feng');
 assert.equal(await page.getByRole('button',{name:'查看贾政书房地点',exact:true}).getAttribute('data-asset'),'estate-study');
 await page.waitForFunction(()=>document.querySelectorAll('.world-location image[data-loaded=true]').length===9);await page.screenshot({path:'artifacts/rongguo-estate-rebuilt.png',fullPage:true});
 await page.getByRole('button',{name:'当前场景',exact:true}).click();
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption(chapters[6].id);await reading();await page.setViewportSize({width:1280,height:720});await page.waitForTimeout(120);await fit();await page.screenshot({path:'artifacts/chapter-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(120);
// Portrait phones get a rotate invitation; dismiss it to verify the compact layout beneath.
await page.locator('.rotate-hint').waitFor({timeout:4000}).catch(()=>{});
const rotateDismiss=page.getByRole('button',{name:'仍要竖屏浏览'});
if(await rotateDismiss.isVisible())await rotateDismiss.click();
await fit();assert.equal(Math.round((await page.locator('.dialogue-panel').boundingBox()).height),246);await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('night');await reading();assert.equal(await node(),'T001');await fit();await page.screenshot({path:'artifacts/chapter-mobile.png',fullPage:true});
 await page.reload();await reading();assert.equal(await node(),'T001');await page.evaluate(()=>localStorage.setItem('honglou-four-chapters:v4','{bad'));await page.reload();await reading();assert.equal(await node(),'C1-001');
 assert.equal(errors.length,0,JSON.stringify(errors));console.log('Passed: all 354 nodes, twenty-two maps, complete history, chapter 1–4 selection, cross-scene save/reload, offscreen reveal, natural movement, pause, settings, atlas, stable map area, minimum readable sprites/labels, zoom hit targets, overview browsing, paused estate travel, controls visible at 1440×900 / 1280×720 / 390×844, corrupt-save recovery.');
}catch(e){console.error('Browser errors:',errors);console.error((await page.locator('body').innerText()).slice(0,3500));await page.screenshot({path:'artifacts/browser-failure.png',fullPage:true});throw e;}finally{await context.close();await browser.close();}
