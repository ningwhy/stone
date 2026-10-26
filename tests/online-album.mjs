// Online-only check for the album tab: the 36 cards must render on the deployed
// site, and the four bond cards must show a direction tag and a from -> to row.
// The local smoke test covers the same DOM, but only this one runs against
// stone.yan.pub, where a stale bundle or a pruned asset would show up.
//
// The Cloudflare edge applies a bot challenge to automated clients, so the run
// resolves stone.yan.pub straight to the origin IP, exactly as online-verify
// does, and checks the deployed bytes themselves.
//
// Usage: node tests/online-album.mjs
//        ORIGIN_DIRECT=1 node tests/online-album.mjs
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync} from 'node:fs';

const direct=process.env.ORIGIN_DIRECT==='1';
const url=process.env.TEST_URL??'https://stone.yan.pub/';
const profile=process.env.ONLINE_PROFILE??(direct?'/tmp/wb-direct-album-profile':'/tmp/wb-online-album-profile');
const args=['--disable-blink-features=AutomationControlled'];
if(direct)args.push('--host-resolver-rules=MAP stone.yan.pub 154.8.237.35');
const context=await chromium.launchPersistentContext(profile,{
  headless:false,channel:'chrome',viewport:{width:1440,height:900},reducedMotion:'reduce',
  ignoreHTTPSErrors:direct,args});
const page=await context.newPage();
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});

try{
  await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
  // The profile is persistent, so a previous run may have left cards unlocked.
  await page.evaluate(()=>localStorage.removeItem('honglou.collection.v1'));
  await page.reload();
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
  await page.getByRole('button',{name:'设置',exact:true}).click();
  await page.getByRole('button',{name:'册页',exact:true}).click();
  assert.equal(await page.locator('.atlas-body article').count(),22,'the map tab must keep its 22 scenes');

  await page.getByRole('tab',{name:/见闻/}).click();
  assert.equal(await page.locator('.card-gallery .card-item').count(),36,'the album must list every card online');
  assert.equal(await page.locator('.card-item.token').count(),4,'the four tokens must be listed once each');
  assert.equal(await page.locator('.card-item.bond').count(),4,'the four bonds must be listed once each');

  // Reading nothing means every bond stays sealed, so only the sealed mark shows.
  assert.equal(await page.locator('.card-item.bond .card-mark').count(),4,'bonds must stay sealed until the owning node is read');

  // Unlock the four bonds by reading their nodes, then confirm each direction
  // tag and from -> to row renders with the right wording.
  const cases=[
    {id:'bond.xiren',name:'袭人',from:'贾母',to:'宝玉',mode:'赏给'},
    {id:'bond.yingge',name:'鹦哥',from:'贾母',to:'黛玉',mode:'赏给'},
    {id:'bond.jiaoxing',name:'娇杏',from:'封肃',to:'贾雨村',mode:'买卖'},
    {id:'bond.yinglian',name:'甄英莲',from:'甄士隐',to:'薛蟠',mode:'被夺'},
  ];
  const seen=[];
  for(const c of cases){
    await page.evaluate(id=>{
      const raw=JSON.parse(localStorage.getItem('honglou.collection.v1')??'[]');
      localStorage.setItem('honglou.collection.v1',JSON.stringify([...new Set([...raw,id])]));
    },c.id);
    await page.reload();
    await page.locator('.loading-screen').waitFor({state:'detached',timeout:30000});
    await page.getByRole('button',{name:'设置',exact:true}).click();
    await page.getByRole('button',{name:'册页',exact:true}).click();
    await page.getByRole('tab',{name:/见闻/}).click();
    // Two bonds share the 赏给 tag, so locate the card by its own name.
    const face=page.locator('.card-item.bond.unlocked').filter({hasText:c.name}).first();
    assert.equal(await face.count(),1,`${c.id} must render exactly one unlocked bond card`);
    const tag=(await face.locator('.bond-mode').textContent()).trim();
    const row=(await face.locator('.bond-row').textContent()).replace(/\s+/g,'');
    // 归属卡的附注本批挪到了卡框外的落款（.card-note），画上只留「谁 → 谁」。
    const note=(await face.locator('.card-note').textContent()).trim();
    assert.equal(tag,c.mode,'a bond must name its direction');
    assert.ok(row.includes(c.from)&&row.includes(c.to)&&row.includes('→'),`a bond must show ${c.from} -> ${c.to}`);
    assert.ok(note.length>4,'a bond must carry its note');
    seen.push(`${c.from}→${c.to}(${tag})`);
  }
  await page.screenshot({path:'artifacts/online-album.png',fullPage:true});
  // Scroll the panel down so the bond group is in frame for the record shot.
  await page.locator('.card-item.bond.unlocked').first().scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  await page.screenshot({path:'artifacts/online-album-bonds.png',fullPage:true});
  assert.deepEqual(errors,[],'the online page must run without console errors');
  console.log(`Passed: ${url} serves the 36-card album with four token cards and four bond cards.`);
  console.log(`online bonds: ${seen.join(', ')}`);
}finally{
  await context.close();
}
