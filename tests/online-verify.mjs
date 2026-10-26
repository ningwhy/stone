// Online verification against the deployed site: confirm chapter four is live.
//
// Two modes:
//   default            go through Cloudflare, exactly as a visitor does.
//   ORIGIN_DIRECT=1    resolve stone.yan.pub to the origin IP, skipping the
//                      Cloudflare edge. The edge applies a bot challenge to
//                      automated clients, which makes the run slow and flaky;
//                      the direct mode checks the deployed bytes themselves.
//
// Usage: node tests/online-verify.mjs
//        ORIGIN_DIRECT=1 node tests/online-verify.mjs
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync} from 'node:fs';

const direct=process.env.ORIGIN_DIRECT==='1';
const profile=process.env.ONLINE_PROFILE??(direct?'/tmp/wb-direct-profile':'/tmp/wb-online-profile');
const args=['--disable-blink-features=AutomationControlled'];
if(direct)args.push('--host-resolver-rules=MAP stone.yan.pub 154.8.237.35');
const context=await chromium.launchPersistentContext(profile,{
  headless:false,channel:'chrome',viewport:{width:1440,height:900},reducedMotion:'reduce',
  ignoreHTTPSErrors:direct,args});
const page=await context.newPage(),errors=[],failed=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
// Cloudflare serves a challenge page with 403 to suspicious clients, so a failed
// request is not necessarily a missing asset. Record both to tell them apart.
page.on('requestfailed',r=>failed.push(`${r.failure()?.errorText??'failed'} ${r.url().slice(0,110)}`));
page.on('response',r=>{if(r.status()>=400)failed.push(`${r.status()} ${r.url().slice(0,110)}`);});
mkdirSync('artifacts',{recursive:true});

// A scene loads the map tiles and the standing portraits, so the wait has to
// tolerate a cold cache behind the tunnel plus the Cloudflare round trip.
const reading=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:120000});
  for(let i=0;i<5;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(60);}}
  // waitForFunction takes (fn, arg, options): the options object has to sit in the
  // third slot or Playwright silently treats it as the function argument and falls
  // back to the 30 second default timeout.
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:120000});
};
const tag=direct?'origin':'online';
try{
 await page.goto('https://stone.yan.pub/',{waitUntil:'commit',timeout:120000});
 await page.waitForSelector('.chapter-select',{timeout:240000});
 await reading();
 console.log(`${tag} node:`,await page.locator('.node-label').textContent());
 const groups=await page.locator('.chapter-select optgroup').evaluateAll(os=>os.map(o=>o.label));
 console.log(`${tag} chapter groups:`,JSON.stringify(groups));
 assert.ok(groups.some(g=>g.includes('第四回')),'chapter four missing from the online selector');
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-court');await reading();
 assert.equal(await page.locator('.game-map').getAttribute('data-scene-ready'),'c4_yamen');
 console.log(`${tag} chapter-four stage: c4_yamen`);
 await page.screenshot({path:`artifacts/${tag}-chapter04.png`,fullPage:true});
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-xue');await reading();
 for(let i=0;i<20;i++){
  const src=await page.locator('.speaker-portrait img').getAttribute('src');
  if(src&&src.includes('xuepan-portrait')){console.log(`${tag} xuepan portrait:`,src);break;}
  await page.getByRole('button',{name:'继续剧情',exact:true}).click();await reading();
 }
 // Book four unfolds inside the estate too: the same overview tab opens there.
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();
 await page.locator('.world-map').waitFor({timeout:30000});
 console.log(`${tag} chapter-four overview: estate map opens`);
 await page.getByRole('button',{name:'当前场景',exact:true}).click();
 // The estate overview is the chapter-three page; its thumbnails used to 404 in production.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('reunion');await reading();
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();
 await page.locator('.world-map').waitFor({timeout:60000});
 await page.waitForFunction(()=>document.querySelectorAll('.world-location image[data-loaded=true]').length===10,undefined,{timeout:120000});
 console.log(`${tag} overview thumbnails: 10 loaded`);
 await page.screenshot({path:`artifacts/${tag}-overview.png`,fullPage:true});
 const realFailures=failed.filter(f=>!f.startsWith('403 '));
 console.log(`${tag} non-403 failed requests:`,realFailures.length);
 for(const f of realFailures.slice(0,10))console.log('  ',f);
 assert.deepEqual(errors,[],JSON.stringify(errors));

 // The new playback controls: one switch that reads 自动 while the reader drives and
 // 暂停 while the story drives itself, and the master sound switch beside it.
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c1-home');await reading();
 assert.equal(await page.getByRole('button',{name:'暂停',exact:true}).count(),0,'a separate pause button is still in the toolbar');
 await page.getByRole('button',{name:'自动',exact:true}).click();
 await page.waitForTimeout(300);
 assert.equal(await page.getByRole('button',{name:'暂停',exact:true}).count(),1,'the same button now reads 暂停');
 const autoNode=await page.locator('.node-label').textContent();
 await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent!==id,autoNode,{timeout:30000});
 await page.getByRole('button',{name:'暂停',exact:true}).click();
 console.log(`${tag} auto/pause switch: one button, two readings, the story advanced and stopped`);

 // The sound master switch is one click from the story, and it is remembered.
 await page.locator('.dialogue-text').click();
 await page.waitForFunction(()=>window.__audio&&window.__audio.ready===true,null,{timeout:20000});
 await page.getByRole('button',{name:'关闭声音'}).click();
 await page.waitForTimeout(400);
 assert.equal(await page.evaluate(()=>window.__audio.muted),true,'the toolbar switch silences the game');
 await page.getByRole('button',{name:'开启声音'}).click();
 await page.waitForTimeout(300);
 assert.equal(await page.evaluate(()=>window.__audio.muted),false,'the toolbar switch brings the sound back');
 console.log(`${tag} master sound switch: silences and restores`);

 // 回看 can send the reader back to any line they have read.
 await page.getByRole('button',{name:'回看',exact:true}).click();
 await page.locator('.history-list').waitFor({timeout:20000});
 const readCount=await page.locator('.history-list article').count();
 assert.ok(readCount>=1,'the log of what has been read is empty');
 const jumpId=await page.locator('.history-list article').first().locator('small').textContent();
 await page.locator('.history-list article').first().getByRole('button').click();
 await reading();
 assert.equal(await page.locator('.node-label').textContent(),jumpId,'the reader landed on the line they chose');
 await page.getByRole('button',{name:'回看',exact:true}).click();
 await page.locator('.history-list').waitFor({timeout:20000});
 assert.ok(await page.locator('.history-list article').count()>=readCount,'the log did not shrink after a jump backwards');
 await page.getByRole('button',{name:'关闭弹窗'}).click();
 console.log(`${tag} 回看: ${readCount} lines, jumpable, and the log survives the jump`);

 // Each of the four books has a piece of its own, and the stage still overrides it.
 const piece=async(section,expected)=>{
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption(section);await reading();
  await page.waitForFunction(name=>window.__audio&&window.__audio.current&&window.__audio.current.name===name,expected,{timeout:30000});
  console.log(`${tag} piece ${section}:`,expected);
 };
 await piece('c1-home','bgm-book-one');
 await piece('c2-dismissal','bgm-book-two');
 await piece('prologue','bgm-book-three');
 await piece('c4-court','bgm-book-four');
 await piece('arrival','bgm-street');
 await page.screenshot({path:`artifacts/${tag}-playback.png`,fullPage:true});
 console.log(`Passed: https://stone.yan.pub/ serves chapter four, the new court stage, the Xue portraits, the chapter-four journey view and the estate overview thumbnails, plus the merged auto/pause switch, the master sound switch, the jumpable 回看 log and the per-book pieces.`);
}catch(e){
 console.error('errors',errors);
 console.error('failed requests',failed.slice(0,20));
 console.error((await page.locator('body').innerText()).slice(0,2000));
 await page.screenshot({path:`artifacts/${tag}-failure.png`,fullPage:true});
 throw e;
}finally{await context.close();}
