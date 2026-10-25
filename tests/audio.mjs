// The soundtrack has to survive a real browser: files decode, the context unlocks on a
// gesture, the piece follows the stage theme, and the settings sliders do what they say.
// Run against the dev server (npm run dev) like the other browser suites.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';

const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(existsSync(chrome)?chrome:undefined),
  args:['--autoplay-policy=no-user-gesture-required']});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});

const audioRequests=[];
page.on('request',r=>{if(r.url().includes('/assets/audio/'))audioRequests.push(r.url());});

const debug=()=>page.evaluate(()=>{
  const a=window.__audio;
  if(!a)return null;
  const ctx=a.ctx;
  return {
    ready:a.ready,
    state:ctx?ctx.state:'none',
    prefs:a.getPrefs(),
    current:a.current?a.current.name:null,
  };
});
const currentPiece=()=>page.evaluate(()=>window.__audio&&window.__audio.current?window.__audio.current.name:null);

const reading=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:20000});
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim());
  await page.locator('.game-map[data-scene-ready]').waitFor();
};

try{
  await page.goto(process.env.TEST_URL??'http://127.0.0.1:5173');
  await reading();

  // The context stays suspended until a gesture, so a click is what starts the music --
  // exactly as it does for a reader. Click the map navigation bar, never a walker: an
  // actor would open its profile dialog and cover the controls the test needs next.
  const beforeGesture=await debug();
  assert.ok(beforeGesture,'the audio engine exposes its QA handle');
  assert.equal(beforeGesture.ready,false,'nothing plays before the first gesture');
  await page.locator('.dialogue-text').click();
  await page.waitForFunction(()=>window.__audio&&window.__audio.ready===true,null,{timeout:8000});
  // the story opens on the mythic rock of the first chapter, so the bowls play first
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-myth',null,{timeout:10000});
  const afterGesture=await debug();
  assert.equal(afterGesture.state,'running','the context runs after the first gesture');
  assert.equal(afterGesture.current,'bgm-myth','the opening stage gets the mythic piece');

  // Every effect file and the current piece were actually fetched and decoded.
  await page.waitForFunction(()=>window.__audio&&window.__audio.buffers.size>=8,null,{timeout:15000});
  for(const name of ['sfx-step-a','sfx-step-b','sfx-tap','sfx-page','sfx-door','sfx-bell','sfx-chair','bgm-myth']){
    assert.ok(audioRequests.some(u=>u.includes(`/${name}.ogg`)),`${name}.ogg was never requested`);
  }

  // The sliders in the settings panel move the real gains and persist.
  await page.getByRole('button',{name:'设置'}).click();
  await page.locator('.audio-settings input[type=range]').first().fill('20');
  await page.locator('.audio-settings input[type=range]').nth(1).fill('40');
  await page.waitForTimeout(150);
  const moved=await debug();
  assert.ok(Math.abs(moved.prefs.bgm-0.2)<0.02&&Math.abs(moved.prefs.sfx-0.4)<0.02,'the sliders wrote the prefs');
  assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('honglou.audio.v1')||'{}').bgm),0.2,'prefs persisted');
  // music at zero fades the piece out instead of muting a running source
  await page.locator('.audio-settings input[type=range]').first().fill('0');
  await page.waitForTimeout(700);
  assert.equal(await currentPiece(),null,'music off stops the piece');
  await page.locator('.audio-settings input[type=range]').first().fill('60');
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-myth',null,{timeout:8000});
  await page.getByRole('button',{name:'关闭弹窗'}).click();

  // The piece follows the stage: a garden courtyard, then the formal yamen (quieter,
  // guqin), then a night scene. Each swap fetches its own file.
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c1-home');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-garden',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-garden.ogg')),'the garden piece was fetched');
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c2-dismissal');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-interior',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-interior.ogg')),'the interior piece was fetched');
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('night');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-night',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-night.ogg')),'the night piece was fetched');
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c1-home');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-garden',null,{timeout:10000});

  // A dialogue advance plays the page effect; the engine keeps working regardless.
  const node=await page.locator('.node-label').textContent();
  await page.getByRole('button',{name:'继续剧情',exact:true}).click();
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent!==id,node,{timeout:8000});

  assert.deepEqual(errors,[],`console/page errors: ${errors.join(' | ')}`);
  console.log('audio: context unlocked, 8 files fetched, theme swaps, sliders and persistence all pass');
}finally{
  await browser.close();
}
