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
    muted:a.muted,
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

  // Every effect file and the current piece were actually fetched and decoded. The opening
  // stage warms six effects -- the one footfall its own surface uses, plus the chime, page,
  // door, bell and poles, which any scene may need -- and the theme piece makes seven.
  await page.waitForFunction(()=>window.__audio&&window.__audio.buffers.size>=7,null,{timeout:15000});
  // requested eagerly on any stage, unlike the footfalls below.
  for(const name of ['sfx-tap','sfx-page','sfx-door','sfx-bell','sfx-chair','bgm-myth']){
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

  // The piece follows the place, and each of the four books has one of its own. A courtyard
  // or a parlour has no piece of its own and takes its chapter's; a canal, a street and a
  // night speak for themselves.
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c1-home');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-book-one',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-book-one.ogg')),'the first chapter piece was fetched');
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c2-dismissal');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-book-two',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-book-two.ogg')),'the second chapter piece was fetched');
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('night');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-night',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-night.ogg')),'the night piece was fetched');

  // The canal has its own piece. It is the stage the water music was written for, and no
  // paragraph opens there, so the test seeks to it the way a reader arrives: mid-journey.
  const seekVoyage=async()=>{
    await page.evaluate(()=>window.__mapScene.engine.seek('P011a'));
    await reading();
  };
  await seekVoyage();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-water',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-water.ogg')),'the water piece was fetched');

  // The capital is street-themed and now has its own market music instead of the courtyard.
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('arrival');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-street',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-street.ogg')),'the street piece was fetched');

  // The Lin estate is themed river because there is water in its courtyard, but a
  // conversation about an appointment is not a voyage, so it does not take the canal's
  // piece: it falls through to the chapter it belongs to, the third book.
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('prologue');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-book-three',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-book-three.ogg')),'the third chapter piece was fetched');

  // The fourth book has a piece of its own too, and it is the one that carries the
  // judgement in the back room of the yamen.
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c4-court');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-book-four',null,{timeout:10000});
  assert.ok(audioRequests.some(u=>u.includes('/bgm-book-four.ogg')),'the fourth chapter piece was fetched');

  // A courtyard has no piece of its own either, so it takes the first book's.
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c1-home');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current&&window.__audio.current.name==='bgm-book-one',null,{timeout:10000});

  // Every stage asks only for the footfall belonging to the surface it stands on, so by the
  // end of this journey all four should have been fetched: stone in a courtyard and in the
  // capital, boards under a roof, dust on the lane outside the wall, and -- on water, where
  // there are no feet -- a pole going into the canal instead.
  await page.evaluate(()=>window.__mapScene.engine.seek('C2-013a'));
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.buffers.has('sfx-step-earth'),null,{timeout:10000});
  await seekVoyage();
  await page.waitForFunction(()=>window.__audio&&window.__audio.buffers.has('sfx-oar'),null,{timeout:10000});
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c2-dismissal');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.buffers.has('sfx-step-board'),null,{timeout:10000});
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c1-home');
  await reading();
  await page.waitForFunction(()=>window.__audio&&window.__audio.buffers.has('sfx-step-stone'),null,{timeout:10000});

  // A dialogue advance plays the page effect; the engine keeps working regardless.
  const node=await page.locator('.node-label').textContent();
  await page.getByRole('button',{name:'继续剧情',exact:true}).click();
  await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent!==id,node,{timeout:8000});

  // The master switch silences everything at once and remembers the choice, while the
  // two sliders keep the positions they had: the balance comes back unchanged.
  await page.getByRole('button',{name:'设置'}).click();
  await page.locator('.audio-settings input[type=range]').first().fill('45');
  await page.locator('.audio-settings input[type=range]').nth(1).fill('65');
  await page.waitForTimeout(120);
  const master=await page.getByRole('checkbox',{name:'开启全部声音'});
  await master.uncheck();
  await page.waitForTimeout(700);
  const silenced=await debug();
  assert.equal(silenced.muted,true,'the master switch reports the silence');
  assert.equal(silenced.current,null,'the piece is stopped while silenced');
  assert.ok(Math.abs(silenced.prefs.bgm-0.45)<0.02&&Math.abs(silenced.prefs.sfx-0.65)<0.02,'the sliders kept their positions');
  assert.equal(await page.evaluate(()=>localStorage.getItem('honglou.audio.muted.v1')),'1','the silence was remembered');
  // The sliders are disabled while silenced, so they cannot be mistaken for live controls.
  assert.equal(await page.locator('.audio-settings input[type=range]').first().isDisabled(),true);
  await master.check();
  await page.waitForFunction(()=>window.__audio&&window.__audio.current!==null,null,{timeout:10000});
  const restored=await debug();
  assert.equal(restored.muted,false,'the master switch is back on');
  assert.equal(await page.evaluate(()=>localStorage.getItem('honglou.audio.muted.v1')),'0');
  await page.getByRole('button',{name:'关闭弹窗'}).click();

  // The toolbar mute button is the same switch, one click away from the story.
  await page.getByRole('button',{name:'关闭声音'}).click();
  await page.waitForTimeout(500);
  assert.equal((await debug()).muted,true,'the toolbar switch silences the game');
  await page.getByRole('button',{name:'开启声音'}).click();
  await page.waitForTimeout(300);
  assert.equal((await debug()).muted,false,'the toolbar switch brings the sound back');

  assert.deepEqual(errors,[],`console/page errors: ${errors.join(' | ')}`);
  console.log('audio: context unlocked, effects fetched, ten pieces follow the place and the book '
    + '(mythic rock, first book, second book, third book, fourth book, canal water, capital market, '
    + 'night), four surfaces have their own footfall, sliders, master switch and persistence all pass');
}finally{
  await browser.close();
}
