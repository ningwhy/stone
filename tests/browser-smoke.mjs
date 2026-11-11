import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync,mkdirSync,readFileSync,readdirSync} from 'node:fs';
import {dismissPickup, dismissLeaf} from './lib/pickup.mjs';
import { seekSection, openToc } from './lib/toc.mjs';
import { chapterLeaves } from '../src/leaves.ts';
const story=[1,2,3,4].flatMap(n=>JSON.parse(readFileSync(`design/chapter0${n}-story.json`,'utf8')));
// 每一回的首末节点：直接用产品代码算，改了分节也不会让断言失真。
const leafBounds={first:new Set(),last:new Set()};
for(const leaf of chapterLeaves().values()){leafBounds.first.add(leaf.firstNode);leafBounds.last.add(leaf.lastNode);}
const ledgerEntries=JSON.parse(readFileSync('design/ledger.json','utf8')).entries;
const ledgerNodes=new Set(ledgerEntries.map(e=>e.node));
// 同地图数一样：账簿笔数从数据实读，写死的话补回目会把「新账没收进背包」掩盖过去。
const ledgerTotal=ledgerEntries.length;
const chapters=[...JSON.parse(readFileSync('design/chapter03-sections.json','utf8')),...JSON.parse(readFileSync('design/chapter04-sections.json','utf8'))];
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
// 册页「地图」页逐张列出 maps/ 下的每一张舞台，数量得跟着地图走：写死数字的话，
// 每加一回就要改一次断言，改漏了就会把「新地图没进册页」这件事掩盖过去。
const mapCount=readdirSync('maps').filter(f=>f.endsWith('.tmj')).length;
// 人物图鉴列出的是每一个画了立绘的人：数字从 manifest 实读，写死 51 的话，
// 每新增一批人物就要改一次断言，改漏了就会把「新人物没进图鉴」这件事掩盖过去。
const castCount=Object.keys(JSON.parse(readFileSync('public/assets/rongguo/manifest.json')).assets).filter(k=>k.endsWith('-portrait')).length;
// 回目名也从数据实读：目录左侧那一列写死成九回的话，补一回就要改一次断言，
// 改漏了就会把「新的一回没列进目录」这件事掩盖过去。
const bookCount=readdirSync('design').filter(f=>/^chapter\d+-sections\.json$/.test(f)).length;
const CN=['零','一','二','三','四','五','六','七','八','九','十'];
// 回次名从产品代码实读（src/story.ts 的 bookNames）。这里原来自己拼中文数字，
// 拼到第二十回就断了——「第十${CN[11]}」拼出「第十undefined」，测试于是报
// 目录少了一回，其实目录是对的、测试的期望值是错的。实读之后就没有第二份
// 中文数字表可以漂移了。
const {bookNames}=await import('../src/story.ts');
const allBooks=Object.keys(bookNames).map(Number).sort((a,b)=>a-b).map(n=>bookNames[n]);
assert.equal(allBooks.length,bookCount,`bookNames must cover every chapter, got ${allBooks.length} of ${bookCount}`);
// 「查无此人」的那个样本名，必须在**全部**回目的正文里一个字都没出现过。
// 这个样本随回目推移而失效：妙玉被第十八回推翻、晴雯被第十九回推翻、
// 麝月被第二十回推翻。每加一回都要重挑一个，并在下面这条静态断言里
// 立刻发现「样本已经被某一回用掉了」——否则断言会误判成搜索功能坏了。
const absentSample='紫鹃';
{
  const all=readdirSync('design').filter(f=>/^chapter\d+-story\.json$/.test(f))
    .map(f=>readFileSync(`design/${f}`,'utf8')).join('');
  const hits=all.split(absentSample).length-1;
  assert.equal(hits,0,`the absent-name sample 「${absentSample}」 must not appear in any chapter, found ${hits}`);
}
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(existsSync(chrome)?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});mkdirSync('artifacts',{recursive:true});
const saved=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('honglou-five-six-chapters:v5')));
const node=()=>page.locator('.node-label').textContent();
// A paused stage must hold still. Read the canvas pixels inside the page instead of
// comparing Playwright element screenshots: the element screenshot path re-rasterises
// the canvas layer, and that re-rasterisation shows GPU rounding noise even when the
// painted frame is byte-identical, so it would report a false difference.
const canvasPixels=()=>page.evaluate(()=>{const canvas=document.querySelector('canvas');const data=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;let hash=2166136261;for(let i=0;i<data.length;i++){hash^=data[i];hash=Math.imul(hash,16777619);}return hash>>>0;});
const reading=async()=>{await dismissPickup(page);await page.locator('.loading-screen').waitFor({state:'detached',timeout:20000});for(let i=0;i<4;i++){const skip=page.getByRole('button',{name:'跳过移动',exact:true});if(await skip.isVisible()){await skip.click();await page.waitForTimeout(60);}}await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim());await page.locator('.game-map[data-scene-ready]').waitFor();await dismissLeaf(page,false);};
// 封底时顶栏那一格是提示而不是按钮，所以量按钮要能退回到提示行；否则一回读
// 完，布局检查会因为「找不到继续剧情」而误报成控件跑出屏幕。
async function fit(){const control=(await page.getByRole('button',{name:'继续剧情',exact:true}).boundingBox())??(await page.locator('.next-button-hint').boundingBox());assert.ok(control);const viewport=page.viewportSize();assert.ok(control.y+control.height<=viewport.height,`controls below screen: ${control.y+control.height}>${viewport.height}`);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
// 推进到下一个节点。
//
//  封底插在中间：读到某回的最后一个节点时，那一页会盖在舞台上，而它自己
// 的按钮才是通往下一回的路。所以推进分成两拍——先把剧情翻到下一句，
// 若是回末就多按一次封底上的按钮。封面只是把它收起来，不推进剧情。
async function next(skip=true){
  await dismissPickup(page);
  const before=await node();
  // 收掉可能还留在台上的纸页。等一等再收：纸页是 React 的 effect，比节点
  // 标签晚一帧才挂上来，急着收会收了个寂寞，纸页随后盖在舞台上把顶栏的
  // 「继续剧情」挡住，点击穿透之下剧情就多走了一步。
  await dismissLeaf(page,false,true);
  await page.getByRole('button',{name:'继续剧情',exact:true}).click();
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent!==id,before);
  // 走完一回的末节点，下一句就是下一回的开头：封底与封面都可能在这一刻
  // 翻出来（都是 React 的 effect，比节点标签晚一帧）。
  //
  // 收之前先等它真的挂上来，再看一眼该有的那页在不在：封面与封底是这页纸
  // 存在的理由，只查「不该出现时别出现」是查不出它被拆掉的。首末节点用产品
  // 代码算，改了分节也不会让断言失真。
  //
  // 这里必须等，不能收得太早：纸页是 React 的 effect，比节点标签晚一帧才
  // 挂上来。急着收会收了个寂寞——纸页随后才盖在舞台上，把顶栏的「继续剧
  // 情」一起挡住，测试点按钮时点击穿透，剧情就多走了一步（曾经一路错到
  // A003 才暴露）。
  //
  // 只在回首与回末等：其余节点本来就没有纸页，等下去是白等——三百多步
  // 各等三秒，一轮测试要多花十几分钟。
  const arrived=await node();
  const wantsCover=leafBounds.first.has(arrived);
  const wantsBack=leafBounds.last.has(arrived);
  // A walk that lands on the wrong line is a failure of the stage, not of the
  // assertion: the engine may have been mid-move when the button was pressed.
  // Record the landing so a drift can be traced to the step that caused it.
  if(process.env.SMOKE_TRACE)console.log(`TRACE ${before} -> ${arrived}`);
  if(wantsCover||wantsBack)await page.waitForFunction(()=>!!document.querySelector('.leaf-sheet'),undefined,{timeout:3000}).catch(()=>{});
  if(wantsCover)assert.equal(await page.locator('.leaf-sheet.leaf-cover').count(),1,`${arrived} must open with a cover`);
  if(wantsBack)assert.equal(await page.locator('.leaf-sheet.leaf-back').count(),1,`${arrived} must close with a back cover`);
  // 然后收起来，免得挡住下一步。封底不按「开启下一回」——那个按钮会把故事
  // 推到下一回的第一句，而这一步只该走一句；测试要走的路线由它自己控制。
  await dismissLeaf(page,false,true);
  await page.waitForTimeout(120);
  await dismissLeaf(page,false,true);
  await dismissPickup(page,ledgerNodes.has(arrived));
  const b=page.getByRole('button',{name:'跳过移动',exact:true});if(skip&&await b.isVisible())await b.click();
  await reading();
}
try{
 await page.goto(process.env.TEST_URL??'http://127.0.0.1:5173');
 // 开书第一格就该有封面：这一页是这一回的开场，读者得先看见它才进得去。
 // 断言放在 reading() 之前——reading() 收纸页，收完就看不见了。
 await page.locator('.loading-screen').waitFor({state:'detached',timeout:20000});
 await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
 await page.waitForFunction(()=>!!document.querySelector('.leaf-sheet.leaf-cover'),undefined,{timeout:5000});
 assert.equal(await page.locator('.leaf-sheet.leaf-cover').count(),1,'the book must open with the first cover');
 assert.ok((await page.locator('.leaf-title').textContent())?.includes('甄士隐梦幻识通灵'),'the cover carries the chapter title');
 await page.screenshot({path:'artifacts/chapter-cover.png',fullPage:true});
 await reading();assert.equal(await node(),'C1-001');await fit();await page.screenshot({path:'artifacts/chapter-opening.png',fullPage:true});
 // 目录标注已读：读过的那段带 ◐ 或 ●，没读过的带 ○。
 // 这条检查必须在读完之前——读完一部书之后所有段落都已读，就再也看不到未读标记了。
 const toc=await openToc(page);
 // 每一回都在左侧列出；右栏只摊开当前那一回——这是索引该有的样子，
 // 88 段一次铺开反而没人看得下去。
 assert.deepEqual(await toc.locator('.toc-book-name').allTextContents(),allBooks);
 const marks=await toc.locator('.toc-card-mark').allTextContents();
 assert.ok(marks.length>0,'the index lists no section');
 assert.ok(marks.every(m=>/[○◐●]/.test(m)),'every section must carry a read mark');
 assert.ok(marks.some(m=>/[◐●]/.test(m)),'the sections already read must be marked as read');
 assert.ok(marks.some(m=>/○/.test(m)),'the sections not read yet must be marked as unread');
 // 面板的滚动结构：dialog 不再滚动，左右两栏各自滚动。
 // 原来 dialog 只有 max-height，flex 链拿不到确定高度，两栏被撑到内容高度
 // （实测 1054px），overflow:auto 永远不触发——真正在滚的是 dialog 自己，
 // 于是左栏无法单独滑动。判据是：dialog 自身不可滚，左栏可滚。
 const scrollShape=await page.evaluate(()=>{
  const dlg=document.querySelector('dialog[open]'),books=document.querySelector('.toc-books'),secs=document.querySelector('.toc-sections');
  return {dialogScrolls:dlg.scrollHeight>dlg.clientHeight,booksScrolls:books.scrollHeight>books.clientHeight,secsScrolls:secs.scrollHeight>secs.clientHeight};
 });
 assert.ok(!scrollShape.dialogScrolls,'the dialog itself must not scroll — the two columns do');
 assert.ok(scrollShape.booksScrolls,'the book column must scroll on its own');
 // 左栏真的能滑：把鼠标放在左栏上滚滚轮，只有左栏的 scrollTop 变。
 const wheelBefore=await page.evaluate(()=>document.querySelector('.toc-books').scrollTop);
 const booksBox=await page.locator('.toc-books').boundingBox();
 await page.mouse.move(booksBox.x+booksBox.width/2,booksBox.y+booksBox.height/2);
 await page.mouse.wheel(0,300);await page.waitForTimeout(250);
 const wheelAfter=await page.evaluate(()=>({books:document.querySelector('.toc-books').scrollTop,dialog:document.querySelector('dialog[open]').scrollTop,sections:document.querySelector('.toc-sections').scrollTop}));
 assert.ok(wheelAfter.books>wheelBefore,`the book column must scroll by itself, got ${wheelAfter.books}`);
 assert.equal(wheelAfter.dialog,0,'the dialog must not scroll while the book column does');
 assert.equal(wheelAfter.sections,0,'the section column must not scroll while the book column does');
 await page.evaluate(()=>{document.querySelector('.toc-books').scrollTop=0;});
 // 吸底：面板最下面那一行常驻，写明所选回目。
 const foot=await page.locator('.toc-foot').textContent();
 assert.match(foot,/所选回目/,'the bottom bar must name the chosen book');
 assert.match(foot,new RegExp(allBooks[0]),'the bottom bar must name the chosen book by name');
 const footBox=await page.locator('.toc-foot').boundingBox(),dlgBox=await page.locator('dialog[open]').boundingBox();
 assert.ok(footBox.y+footBox.height<=dlgBox.y+dlgBox.height+1,'the bottom bar must sit inside the panel');
 // 吸顶：右栏的回目标题钉在栏顶，滚到哪儿都不离开。
 // 跨回搜索才会出现多组标题，交接也只在多组时才有意义。
 await toc.getByRole('searchbox',{name:'搜索剧情段落'}).fill('宝玉');
 await page.waitForTimeout(400);
 const sticky=await page.evaluate(async()=>{
  const secs=document.querySelector('.toc-sections');
  const samples=[];
  for(const frac of [0.35,0.5,0.65]){
   secs.scrollTop=Math.floor((secs.scrollHeight-secs.clientHeight)*frac);
   await new Promise(r=>setTimeout(r,350));
   const rail=secs.getBoundingClientRect().top+parseFloat(getComputedStyle(secs).paddingTop||'0');
   const heads=[...document.querySelectorAll('.toc-group-head')].map(h=>{const r=h.getBoundingClientRect();return {top:r.top,bottom:r.bottom,txt:h.textContent};});
   // 交接的不变量：栏顶那一行必须始终被标题占着（读者不会失去位置），
   // 且顶部区域不得有任何两个标题互相压住。交接途中活跃标题正让位上移、
   // 下一个正滚进来，两者边缘相接，所以判据是「栏顶被覆盖」而不是「顶边对齐」。
   const covering=heads.filter(h=>h.top<=rail&&h.bottom>rail);
   // 交接处不能叠成一摞：顶部区域里的标题必须边缘相接，不得互相压住。
   const near=heads.filter(h=>h.bottom>rail-2&&h.top<rail+80);
   let overlap=false;
   // 交接处允许 1px 的亚像素误差：判据是「不得互相压住」，
   // 而不是「不得有一像素的重合」。
   for(let i=0;i<near.length;i++)for(let j=i+1;j<near.length;j++)if(near[i].top<near[j].bottom-2&&near[j].top<near[i].bottom-2)overlap=true;
   samples.push({frac,coveringCount:covering.length,coveringText:covering.map(h=>h.txt),overlap,near:near.map(h=>`${h.txt} ${Math.round(h.top)}~${Math.round(h.bottom)}`)});
  }
  return samples;
 });
 for(const s of sticky){
  assert.equal(s.coveringCount,1,`exactly one heading must cover the rail at ${s.frac}, got ${s.coveringCount} (${s.coveringText})`);
  assert.ok(!s.overlap,`the headings must hand over, not pile up at ${s.frac}: ${s.near.join(' / ')}`);
 }
 await toc.getByRole('searchbox',{name:'搜索剧情段落'}).fill('');
 await page.waitForTimeout(300);
 // 单回模式下只有一个标题，它必须一直钉在栏顶。
 await toc.locator('.toc-book',{hasText:allBooks[14]}).click();
 await page.waitForTimeout(300);
 const single=await page.evaluate(async()=>{
  const secs=document.querySelector('.toc-sections');
  const head=document.querySelector('.toc-group-head');
  const rail=secs.getBoundingClientRect().top+parseFloat(getComputedStyle(secs).paddingTop||'0');
  const at=[];
  for(const frac of [0,0.5,1]){secs.scrollTop=Math.floor((secs.scrollHeight-secs.clientHeight)*frac);await new Promise(r=>setTimeout(r,250));at.push(Math.round(head.getBoundingClientRect().top-rail));}
  return at;
 });
 assert.ok(single.every(d=>Math.abs(d)<=2),`the heading must stay at the rail, offsets ${single.join('/')}`);
 // 逐回翻过去：每一回都摊得开，而且段落数与设计表一致。
 const expected=await page.evaluate(async()=>{const m=await import('/design/chapter01-sections.json');return m.default.length;});
 for(const book of allBooks.slice(1)){
  await toc.locator('.toc-book',{hasText:book}).click();
  await page.waitForTimeout(120);
  assert.ok(await toc.locator('.toc-card').count()>0,`${book} lists no section`);
 }
 assert.ok(expected>0,'the section sheet is empty');
 // 搜一个只属于某回的词：跨回命中，不再需要从头划到底。
 await toc.getByRole('searchbox',{name:'搜索剧情段落'}).fill('梨香院');
 await page.waitForTimeout(150);
 const hits=await toc.locator('.toc-card').count();
 assert.ok(hits>0,'searching a place must find its section');
 const books=await toc.locator('.toc-group h3').allTextContents();
 // 梨香院第四回（薛家迁入）、第七回（送宫花）与第八回（金莺微露意）都有，命中必须按回分组、按书序排。
 // 分组标题带着段数（"第四回2 段"），取回目名要用正则整段抠——原来按 slice(0,3) 取，
 // 遇上「第十一回」只会拿到「第十一」，命中回一多就对不上。
 const bookNames=(await toc.locator('.toc-group h3').allTextContents()).map(t=>t.match(/^第[一二三四五六七八九十]+回/)[0]);
 assert.ok(bookNames.includes('第四回'),`梨香院 must find the fourth book, got ${books}`);
 assert.ok(bookNames.includes('第七回'),`梨香院 must find the seventh book, got ${books}`);
 const order=bookNames.map(b=>allBooks.indexOf(b));
 assert.ok(order.every(i=>i>=0),`a matched book is not in the index: ${bookNames}`);
 assert.deepEqual(order,[...order].sort((a,b)=>a-b),'the matched books stay in reading order');
 // 搜人名：搜索框写着「搜段落、人物或地点」，人物就必须搜得到。
 // 「宝钗」不出现在任何段落标题里，只能靠在场人物命中——这条断言守的就是它。
 await toc.getByRole('searchbox',{name:'搜索剧情段落'}).fill('宝钗');
 await page.waitForTimeout(150);
 const people=await toc.locator('.toc-card').count();
 assert.ok(people>0,'searching a person must find their section');
 const personLabels=await toc.locator('.toc-card-actors').allTextContents();
 assert.ok(personLabels.some(t=>t.includes('宝钗')),'the found section must show who is on stage');
 // 搜一个只在段内后半段出现的地点：多地点的段落不能只按第一个地点建索引。
 await toc.getByRole('searchbox',{name:'搜索剧情段落'}).fill('林府');
 await page.waitForTimeout(150);
 assert.ok(await toc.locator('.toc-card').count()>0,'a place in the middle of a section must be searchable');
 // 搜一个剧情里根本没有的名字：必须找不到，不能凭空造出段落。
 // 这个名字必须在前二十回里从未出现——「妙玉」被第十八回推翻，
 // 「晴雯」被第十九回推翻（她恰在第十九回登场），「麝月」又被第二十回推翻
 // （她恰在第二十回登场，还守着篦头那一场）。这里改用「紫鹃」：
 // 她是黛玉的丫鬟，要到第二十一回以后才出场，前二十回一个字都没出现。
 await toc.getByRole('searchbox',{name:'搜索剧情段落'}).fill('紫鹃');
 await page.waitForTimeout(150);
 assert.equal(await toc.locator('.toc-card').count(),0,'a name absent from the story must find nothing');
 assert.ok(await toc.locator('.toc-empty').count()>0,'an empty result must say so');
 // 选了最后一回、搜一下再清空：书栏必须还在那一回，不能弹回当前所在的第一回。
 await toc.getByRole('searchbox',{name:'搜索剧情段落'}).fill('');
 await page.waitForTimeout(150);
 const kept=await toc.locator('.toc-book.active .toc-book-name').textContent();
 assert.equal(kept,allBooks.at(-1),`the chosen book must survive a search, got ${kept}`);
 // 搜索框有内容时 Esc 只清搜索，空的时候 Esc 关弹窗。
 await toc.getByRole('searchbox',{name:'搜索剧情段落'}).fill('太虚');
 await page.waitForTimeout(120);
 await page.keyboard.press('Escape');
 await page.waitForTimeout(120);
 assert.equal(await toc.getByRole('searchbox',{name:'搜索剧情段落'}).inputValue(),'','Escape must clear the search box');
 assert.equal(await page.locator('dialog[open]').count(),1,'Escape must not close the panel while the search has text');
 await page.keyboard.press('Escape');
 await page.locator('dialog[open]').waitFor({state:'detached',timeout:20000});
 const visited=new Set();
 for(let i=0;i<story.length;i++){
  // When the walk drifts off the script, the failure has to say where it was
  // and what the board looked like at that moment: a bare "expected C1-030,
  // got C1-029" does not tell the reader whether the stage was moving, whether
  // a sheet was covering it, or whether the engine sat on a different index.
  if(await node()!==story[i].id){
   const dump=await page.evaluate(()=>{
    const s=JSON.parse(localStorage.getItem('honglou-five-six-chapters:v5')??'null');
    const btn=[...document.querySelectorAll('nav button')].map(b=>b.textContent?.trim()).find(t=>t&&(t.includes('继续剧情')||t.includes('跳过移动')))??null;
    return {label:document.querySelector('.node-label')?.textContent??null,btn,savedNode:s?.node??null,savedIndex:s?.state?.index??null,savedStatus:s?.state?.status??null,savedScene:s?.state?.sceneId??null,sheets:[...document.querySelectorAll('.leaf-sheet')].map(e=>e.className),pickup:document.querySelectorAll('.pickup-overlay').length,bodyText:document.body.innerText.slice(0,400)};
   });
   console.error('DRIFT at step',i,JSON.stringify(dump,null,1));
  }
  assert.equal(await node(),story[i].id);const data=await saved();assert.equal(data.node,story[i].id);visited.add(data.state.sceneId);assert.equal(Math.round((await page.locator('.dialogue-panel').boundingBox()).height),206);
  if(story[i].id==='F001'){assert.equal(data.state.actors.feng.visible,false);assert.equal(await page.locator('.dialogue-type').textContent(),'画外');}
  if(['C1-012','C1-025','C1-039','C2-018','C2-023'].includes(story[i].id))await page.screenshot({path:`artifacts/prequel-${story[i].id}.png`,fullPage:true});
  if(story[i].id==='B010')await page.screenshot({path:'artifacts/chapter-first-meeting.png',fullPage:true});
  if(story[i].id==='F006')await page.screenshot({path:'artifacts/chapter-feng.png',fullPage:true});
  if(story[i].id==='U009')await page.screenshot({path:'artifacts/chapter-rongxi.png',fullPage:true});
  if(story[i].id==='T012')await page.screenshot({path:'artifacts/chapter-night.png',fullPage:true});
  if(i<story.length-1)await next();
 }
 // The prequel gets its own scene atlas and every section can be selected.
 await seekSection(page, 'c1-home');await reading();
 // 跳读之后不该留着封面或封底。翻页的规矩是「该有就有、该无就无」：
 // 上一版只在出现时才更新状态，纸页会赖在舞台上，连顶栏的「继续剧情」
 // 一起挡住——读下去像是按钮坏了。
 assert.equal(await page.locator('.leaf-sheet').count(),0,`jumping must not leave a cover or back cover on screen, got ${await page.locator('.leaf-sheet').count()}`);
 await page.getByRole('button',{name:'本回行迹',exact:true}).click();await page.locator('.journey-sites').waitFor();assert.equal(await page.locator('.journey-site').count(),6);await page.screenshot({path:'artifacts/prequel-journey.png',fullPage:true});await page.getByRole('button',{name:'当前场景',exact:true}).click(); await seekSection(page, 'letter');await reading();while(await node()!=='END')await next();
 // The walk stops at the old chapter-three finale, so its history stops there too.
 // That finale is no longer the end of the book: reloading offers to continue, not restart.
 assert.equal(visited.size,22);assert.equal((await saved()).state.history.length,242);await page.reload();await reading();assert.equal(await node(),'END');await page.getByRole('button',{name:'继续剧情',exact:true}).waitFor();
 await seekSection(page, chapters[2].id);await reading();assert.equal(await node(),'N005');const height=(await page.locator('.map-panel').boundingBox()).height;
 await page.getByRole('button',{name:'继续剧情',exact:true}).click();await page.getByRole('button',{name:'跳过移动',exact:true}).waitFor();assert.equal((await page.locator('.map-panel').boundingBox()).height,height);await page.locator('.map-action-cue').waitFor();await page.screenshot({path:'artifacts/chapter-action.png',fullPage:true});
 await page.getByRole('button',{name:'暂停演出',exact:true}).click();await page.waitForTimeout(120);const paused=await canvasPixels();await page.waitForTimeout(200);assert.equal(await canvasPixels(),paused);await page.getByRole('button',{name:'继续演出',exact:true}).click();await reading();assert.equal(await node(),'N006');

 // Map dominates the viewport; toolbar stays clickable with both portrait groups present.
 const mapBox=await page.locator('.map-panel').boundingBox();assert.ok(mapBox.height>780&&mapBox.width>1380);
 const zoomBefore=Number(await page.locator('.game-map').getAttribute('data-zoom'));
 await page.getByRole('button',{name:'放大地图',exact:true}).click();assert.ok(Number(await page.locator('.game-map').getAttribute('data-zoom'))>zoomBefore);
 await page.getByRole('button',{name:'缩小地图',exact:true}).click();assert.equal(await page.locator('dialog[open]').count(),0);
 for(let i=0;i<8;i++)await page.getByRole('button',{name:'缩小地图',exact:true}).click();
 assert.ok(Number(await page.locator('.game-map').getAttribute('data-min-actor-pixels'))>=47.9);assert.ok(Number(await page.locator('.game-map').getAttribute('data-label-pixels'))>=11.9);
 await page.screenshot({path:'artifacts/map-min-zoom.png',fullPage:true});
 await page.getByRole('button',{name:'回到剧情镜头'}).click();
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();await page.locator('.world-map').waitFor();await page.waitForFunction(()=>document.querySelectorAll('.world-location image[data-loaded=true]').length===10);
 assert.equal(await page.locator('.world-location').count(),10);
 await page.getByRole('button',{name:'查看贾赦东院地点',exact:true}).click();assert.ok((await page.locator('.world-detail').textContent()).includes('黑油大门'));
 assert.equal(await node(),'N006');await page.getByRole('button',{name:'关闭地点详情'}).click();
 await page.screenshot({path:'artifacts/rongguo-overview.png',fullPage:true});
 // 三级舆图：府内是第三级，可上溯京城再下钻宁国府；碧纱橱是房内空间，梨香院才是院落。
 assert.deepEqual(await page.locator('.world-crumbs button').allTextContents(),['天下舆图','京城总览','荣国府总览']);
 assert.equal(await page.getByRole('button',{name:'查看碧纱橱（贾母正房内）地点'}).getAttribute('data-kind'),'room');
 assert.equal(await page.getByRole('button',{name:'查看正室东耳房 · 东廊小正房地点'}).getAttribute('data-kind'),'room');
 assert.equal(await page.getByRole('button',{name:'查看梨香院地点'}).getAttribute('data-kind'),'court');
 await page.locator('.world-crumbs button',{hasText:'京城总览'}).click();
 assert.deepEqual(await page.locator('.world-crumbs button').allTextContents(),['天下舆图','京城总览']);
 await page.getByRole('button',{name:'查看宁国府地点'}).click();await page.getByRole('button',{name:'进入宁国府总览 →'}).click();
 assert.deepEqual(await page.locator('.world-crumbs button').allTextContents(),['天下舆图','京城总览','宁国府总览']);
 await page.waitForFunction(()=>document.querySelectorAll('.world-location image[data-loaded=true]').length===7);
 await page.screenshot({path:'artifacts/ningguo-overview.png',fullPage:true});
 await page.getByRole('button',{name:'当前场景',exact:true}).click();
 // A real sequential boundary must animate along the estate roads; pause freezes the token.
 await seekSection(page, chapters[3].id);await reading();
 while(await node()!=='F015')await next();
 await page.getByRole('button',{name:'继续剧情',exact:true}).click();await page.locator('[data-testid=world-travel-route]').waitFor();
 await page.getByRole('button',{name:'暂停演出',exact:true}).click();const travelPosition=await page.locator('.world-traveler').getAttribute('transform');await page.waitForTimeout(200);assert.equal(await page.locator('.world-traveler').getAttribute('transform'),travelPosition);
 await page.screenshot({path:'artifacts/rongguo-travel.png',fullPage:true});
 await page.getByRole('button',{name:'继续演出',exact:true}).click();await page.waitForFunction(()=>!document.querySelector('[data-testid=world-travel-route]'));await reading();assert.equal(await node(),'U001');
 await page.getByRole('button',{name:'设置',exact:true}).click();await page.getByRole('checkbox',{name:'显示地图上的引导路线'}).check();assert.equal(await page.locator('dialog h2').textContent(),'阅读设置');await page.locator('dialog').getByRole('combobox').selectOption('2');await page.getByRole('checkbox',{name:'显示地图上的引导路线'}).uncheck();await page.keyboard.press('Escape');

 // One switch, two readings: the button reads 自动 while the reader drives and 暂停 while
 // the story drives itself. There is no second button that looks live and does nothing.
 await seekSection(page, 'c1-home');await reading();
 const auto=page.getByRole('button',{name:'自动',exact:true});
 assert.equal(await page.getByRole('button',{name:'暂停',exact:true}).count(),0,'there is no separate pause button in the toolbar');
 await auto.click();
 await page.waitForTimeout(300);
 assert.equal(await page.getByRole('button',{name:'暂停',exact:true}).count(),1,'the same button now reads 暂停');
 const autoNode=await node();
 await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent!==id,autoNode,{timeout:12000});
 assert.notEqual(await node(),autoNode,'auto-play actually advanced the story');
 await page.getByRole('button',{name:'暂停',exact:true}).click();
 const stopped=await node();
 await page.waitForTimeout(1200);
 assert.equal(await node(),stopped,'pressing 暂停 stops the story');
 assert.equal(await page.getByRole('button',{name:'自动',exact:true}).count(),1,'the button reads 自动 again');

 // 回看 is a log of the whole reading, and every line in it can be jumped back to.
 await page.getByRole('button',{name:'回看',exact:true}).click();
 await page.locator('.history-list').waitFor();
 const readCount=await page.locator('.history-list article').count();
 assert.ok(readCount>=3,`only ${readCount} lines in the log`);
 const jumpTo=page.locator('.history-list article').first().locator('button');
 const jumpId=await page.locator('.history-list article').first().locator('small').textContent();
 await jumpTo.click();
 await reading();
 assert.equal(await node(),jumpId,'the reader landed on the line they chose');
 await page.getByRole('button',{name:'回看',exact:true}).click();
 await page.locator('.history-list').waitFor();
 assert.ok(await page.locator('.history-list article').count()>=readCount,'the log did not shrink after a jump backwards');
 await page.getByRole('button',{name:'关闭弹窗'}).click();

 // 背包直达：顶栏「背包」按钮一步打开账簿页签，不必再穿设置与册页三层。
 await page.getByRole('button',{name:'背包',exact:true}).click();
 await page.locator('.ledger-switch').waitFor();
 assert.equal(await page.getByRole('tab',{name:/账簿/}).getAttribute('aria-selected'),'true','the backpack button lands on the ledger tab');
 await page.getByRole('tab',{name:'地图'}).click(); // 复位页签，后面的册页断言默认从地图起
 await page.keyboard.press('Escape');

 await page.getByRole('button',{name:'设置',exact:true}).click();await page.getByRole('button',{name:'册页',exact:true}).click();assert.equal(await page.locator('.atlas-body article').count(),mapCount);
 // 见闻标签：32 张卡（22 地志 + 6 金句 + 4 信物），读过的部分已入册，收集数与页签一致。
 await page.getByRole('tab',{name:/见闻/}).click();
 assert.equal(await page.locator('.card-gallery .card-item').count(),36,'the album must list every card');
 // 信物与归属各自单列一组，不与回目分组重复。
 assert.equal(await page.locator('.card-item.token').count(),4,'the four tokens must be listed once each');
 assert.equal(await page.locator('.card-item.bond').count(),4,'the four bonds must be listed once each');
 const unlockedCount=await page.locator('.card-gallery .card-item.unlocked').count();
 assert.ok(unlockedCount>=1,'reading some nodes must already fill the album');
 assert.match(await page.getByRole('tab',{name:/见闻/}).textContent(),new RegExp(`${unlockedCount}/36`));
 // 卡格整齐：旧版四类卡各定一个高度（150/170/186px），看着大的大小的小。
 // 新版所有卡面写死同一高度，四列横向纵向都齐平——断言整个画廊只存在一种高度。
 const faceHeights=await page.locator('.card-gallery .card-face').evaluateAll(els=>[...new Set(els.map(e=>Math.round(e.getBoundingClientRect().height)))]);
 assert.equal(faceHeights.length,1,`every card face must share one height, got ${faceHeights.join('/')}`);
 // 贴图铺满卡面、不再套一层独立小图框：解锁卡里画框尺寸应与卡面一致（差只在 1px 边框内）。
 const fillRatios=await page.locator('.card-gallery .card-item.unlocked .card-thumb').evaluateAll(els=>els.map(e=>{
   const t=e.getBoundingClientRect(),f=e.closest('.card-face').getBoundingClientRect();
   return Math.max(Math.abs(t.width-f.width),Math.abs(t.height-f.height));
 }));
 assert.ok(fillRatios.every(d=>d<=2),`the art must fill the card face, max gap ${Math.max(...fillRatios)}px`);
 // 卡图按可见性才加载：册页一次 36 张大图同屏解码会卡死页面。
 // 断言口径是「已挂上 src 的图」——没进视口的卡只有占位，没有 src。
 // 卡图是异步挂 src 的：断言必须等第一张真的挂上，否则读到的是 0 而不是「在加载」。
 await page.waitForFunction(()=>document.querySelectorAll('.card-gallery .card-art[src]').length>0,undefined,{timeout:15000});
 const loadedPics=await page.locator('.card-gallery .card-art[src]').count();
 assert.ok(loadedPics>=1,'the pictures in view must still load');
 assert.ok(loadedPics<36,`the album must not load all 36 pictures at once, got ${loadedPics}`);
 const pendingPics=await page.locator('.card-gallery .card-thumb .card-art-placeholder').count();
 assert.ok(pendingPics>0,'the pictures outside the view must wait for their turn');
// 账簿标签：每一笔流转（银两、衣物、物件、人、人情），页签计数与实际入账一致。
await page.getByRole('tab',{name:/账簿/}).click();
assert.equal(await page.locator('.ledger-book .ledger-row').count(),ledgerTotal,'the ledger must list every transfer');
const ledgerShown=Number((await page.getByRole('tab',{name:/账簿/}).textContent()).match(/(\d+)\/(\d+)/)[1]);
assert.equal(Number((await page.getByRole('tab',{name:/账簿/}).textContent()).match(/(\d+)\/(\d+)/)[2]),ledgerTotal,'the tab total must match the ledger data');
 assert.equal(await page.locator('.ledger-book .ledger-row.unlocked').count(),ledgerShown,'the ledger tab count must equal its unlocked rows');
 assert.ok(await page.locator('.ledger-people button').count()>=8,'the ledger must name everyone with a balance');
 await page.locator('.ledger-people button').filter({hasText:'贾雨村'}).click();
 assert.match(await page.locator('.ledger-summary').textContent(),/贾雨村/);
 // 账簿也要有贴图：账上的人和物都得有脸，不能只是一行行字。
 // 人物按钮里画过立绘的人要挂上立绘，画框尺寸统一。
 const ledgerThumbs=await page.locator('.ledger-people .card-thumb').evaluateAll(els=>[...new Set(els.map(e=>Math.round(e.getBoundingClientRect().height)))]);
 assert.equal(ledgerThumbs.length,1,`the ledger thumbnails must share one height, got ${ledgerThumbs.join('/')}`);
 assert.ok(await page.locator('.ledger-people .card-thumb').count()>=6,'the ledger must show portraits for the people who have one');
 // 已入账的流水行要带货品图，尺寸同样统一。
 const rowThumbs=await page.locator('.ledger-row .card-thumb').evaluateAll(els=>[...new Set(els.map(e=>Math.round(e.getBoundingClientRect().height)))]);
 assert.equal(rowThumbs.length,1,`the ledger row thumbnails must share one height, got ${rowThumbs.join('/')}`);
 assert.ok(await page.locator('.ledger-row .card-thumb').count()>=1,'the unlocked ledger rows must show their goods');
 // 流水行要等高：情形文字从 16 字到 46 字不等，行高原本跟着字走
 // （实测过 70/95/117 三种高度），列表看上去参差不齐。
 const rowHeights=await page.locator('.ledger-row.unlocked').evaluateAll(els=>[...new Set(els.map(e=>Math.round(e.getBoundingClientRect().height)))]);
 assert.equal(rowHeights.length,1,`the unlocked ledger rows must share one height, got ${rowHeights.join('/')}`);
 const circHeights=await page.locator('.ledger-circ').evaluateAll(els=>[...new Set(els.map(e=>Math.round(e.getBoundingClientRect().height)))]);
 assert.equal(circHeights.length,1,`the circumstances must share one height, got ${circHeights.join('/')}`);
 // 每一笔已入账的账目都要有货品图，不能留空位。
 // 判据看行首有没有画框（有框即已配图），不看 img：贴图按可见性才加载，
 // 视口外的行只有占位符、还没有 img 节点，用 img 判会把懒加载误判成缺图。
 const unlockedRows=await page.locator('.ledger-row.unlocked').count();
 const rowsWithArt=await page.locator('.ledger-row.unlocked:has(.card-thumb)').count();
 assert.equal(rowsWithArt,unlockedRows,`every unlocked transfer needs its goods picture, ${unlockedRows-rowsWithArt} rows are blank`);
 // 贴图要真的能加载出来（不只是在 DOM 里挂了标签）。
 // 得先把流水行滚进视口：贴图按可见性才加载，视口外的行只有占位符。
 await page.locator('.ledger-row.unlocked').first().scrollIntoViewIfNeeded();
 await page.waitForTimeout(600);
 const loadedGoods=await page.locator('.ledger-row .card-art[src]').count();
 assert.ok(loadedGoods>=1,'the ledger pictures in view must load');
 // 按物视角：英莲的三笔（卖冯渊/偷卖薛家/被夺）合成一条流转链。
 await page.getByRole('tab',{name:/按物/}).click();
 await page.locator('.ledger-people button').filter({hasText:'英莲'}).click();
 assert.match(await page.locator('.ledger-book h3').textContent(),/英莲的流转链/);
 assert.equal(await page.locator('.ledger-book .ledger-row').count(),3,'the chain lists every transfer of one item');
 await page.getByRole('tab',{name:'地图'}).click();assert.equal(await page.locator('.atlas-body article').count(),mapCount);
 await page.keyboard.press('Escape');

 // A complete painted cast directory makes early characters discoverable after resuming.
 await page.getByRole('button',{name:'设置',exact:true}).click();await page.getByRole('button',{name:'人物图鉴',exact:true}).click();
 assert.equal(await page.locator('.cast-gallery article').count(),castCount);
 assert.equal(await page.locator('.cast-gallery img').count(),castCount);
 await page.screenshot({path:'artifacts/cast-directory.png',fullPage:true});
 await page.locator('.cast-gallery article').filter({has:page.locator('strong',{hasText:'冷子兴'})}).getByRole('button',{name:'定位出场 →',exact:true}).click();await reading();assert.equal((await saved()).state.actors.leng.visible,true);assert.ok((await node()).startsWith('C2-'));await seekSection(page, 'prologue');await reading();await next();await next();await next();assert.equal(await node(),'P004');
 assert.match(await page.locator('.speaker-portrait img').getAttribute('src'),/^\/assets\/rongguo\/leng-portrait\.webp\?v=[a-f0-9]+$/);
 await page.screenshot({path:'artifacts/leng-zixing.png',fullPage:true});
 // 扬州一节的「总览」落在第一级天下；下钻 京都 → 京城 → 荣国府 才到凤姐院门口。
 await page.getByRole('button',{name:'天下舆图',exact:true}).click();await page.locator('.world-map').waitFor();
 await page.getByRole('button',{name:'查看京都 · 神京地点'}).click();await page.getByRole('button',{name:'进入京城总览 →'}).click();
 await page.getByRole('button',{name:'查看荣国府地点'}).click();await page.getByRole('button',{name:'进入荣国府总览 →'}).click();
 assert.deepEqual(await page.locator('.world-crumbs button').allTextContents(),['天下舆图','京城总览','荣国府总览']);
 await page.getByRole('button',{name:'查看王熙凤院地点',exact:true}).click();
 assert.ok((await page.locator('.world-detail').textContent()).includes('粉油大影壁'));
 await page.getByRole('button',{name:'从此处剧情开始 →',exact:true}).click();await reading();assert.equal(await node(),'U019');
 await page.screenshot({path:'artifacts/feng-courtyard-gate.png',fullPage:true});
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();
 assert.equal(await page.getByRole('button',{name:'查看王熙凤院地点',exact:true}).getAttribute('data-asset'),'estate-feng');
 assert.equal(await page.getByRole('button',{name:'查看贾政书房地点',exact:true}).getAttribute('data-asset'),'estate-study');
 await page.waitForFunction(()=>document.querySelectorAll('.world-location image[data-loaded=true]').length===10);await page.screenshot({path:'artifacts/rongguo-estate-rebuilt.png',fullPage:true});
 await page.getByRole('button',{name:'当前场景',exact:true}).click();
 // Book four also unfolds inside the estate: the same overview tab opens there, and the
 // Xue family courtyard is a place on the map with its own path into the lane spine.
 await seekSection(page, 'c4-pear');await reading();
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();await page.locator('.world-map').waitFor();
 await page.waitForFunction(()=>document.querySelector('.world-location.current')?.getAttribute('data-asset')==='estate-lixiang',undefined,{timeout:30000});
 await page.getByRole('button',{name:'查看梨香院地点',exact:true}).click();
 assert.ok((await page.locator('.world-detail').textContent()).includes('薛姨妈'));
 await page.getByRole('button',{name:'从此处剧情开始 →',exact:true}).click();await reading();assert.equal(await node(),'C04-104');
 await page.screenshot({path:'artifacts/lixiang-overview.png',fullPage:true});
 await page.getByRole('button',{name:'当前场景',exact:true}).click();
 await seekSection(page, chapters[6].id);await reading();await page.setViewportSize({width:1280,height:720});await page.waitForTimeout(120);await fit();await page.screenshot({path:'artifacts/chapter-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(120);
// Portrait phones get a rotate invitation; dismiss it to verify the compact layout beneath.
await page.locator('.rotate-hint').waitFor({timeout:4000}).catch(()=>{});
const rotateDismiss=page.getByRole('button',{name:'仍要竖屏浏览'});
if(await rotateDismiss.isVisible())await rotateDismiss.click();
await fit();assert.equal(Math.round((await page.locator('.dialogue-panel').boundingBox()).height),246);await seekSection(page, 'night');await reading();assert.equal(await node(),'T001');await fit();await page.screenshot({path:'artifacts/chapter-mobile.png',fullPage:true});
 await page.reload();await reading();assert.equal(await node(),'T001');
// 获得弹窗：清掉账簿存档后重读「交到手上」的节点，货品卡像捡道具一样弹出；
// 收下后写入存档，回头再读同一段不再弹第二次。
await page.evaluate(()=>localStorage.removeItem('honglou.ledger.v1'));
await page.reload();await reading();
await page.evaluate(()=>window.__mapScene.engine.seek('C1-033'));
await page.locator('.pickup-overlay').waitFor({timeout:8000});
assert.equal(await page.locator('.pickup-item').count(),2,'C1-033 hands over silver and winter clothes');
assert.match(await page.locator('.pickup-item img').first().getAttribute('src'),/token_yinbi/,'the goods show their art');
await page.getByRole('button',{name:'收下',exact:true}).click();
await page.locator('.pickup-overlay').waitFor({state:'detached',timeout:5000});
assert.ok((await page.evaluate(()=>JSON.parse(localStorage.getItem('honglou.ledger.v1')??'[]'))).includes('ledger.yucun-silver-50'),'taking the goods stores them');
await page.evaluate(()=>window.__mapScene.engine.seek('C1-042'));
await dismissPickup(page,true);
await page.evaluate(()=>window.__mapScene.engine.seek('C1-033'));
await page.waitForTimeout(500);
assert.equal(await page.locator('.pickup-overlay').count(),0,'collected goods do not pop twice');
await page.evaluate(()=>localStorage.setItem('honglou-five-six-chapters:v5','{bad'));await page.reload();await reading();assert.equal(await node(),'C1-001');
 assert.equal(errors.length,0,JSON.stringify(errors));console.log(`Passed: all ${story.length} nodes, ${mapCount} maps, complete history, chapter 1–4 selection, cross-scene save/reload, offscreen reveal, natural movement, pause, settings, atlas, stable map area, minimum readable sprites/labels, zoom hit targets, overview browsing, paused estate travel, controls visible at 1440×900 / 1280×720 / 390×844, corrupt-save recovery.`);
}catch(e){console.error('Browser errors:',errors);console.error((await page.locator('body').innerText()).slice(0,3500));await page.screenshot({path:'artifacts/browser-failure.png',fullPage:true});throw e;}finally{await context.close();await browser.close();}
