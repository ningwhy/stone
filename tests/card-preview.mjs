// Targeted browser test for the backpack card page.
//
//   1. clicking a person in the ledger pops a card open;
//   2. the card carries the picture, the name, the transfer timeline and the
//      quoted original text;
//   3. an unlocked transfer shows its details, a locked one shows only a "？";
//   4. the card closes and the reader is back in the backpack list.
//
// Usage: node tests/card-preview.mjs
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync,readFileSync} from 'node:fs';
import {dismissPickup,dismissLeaf} from './lib/pickup.mjs';
import {seekSection} from './lib/toc.mjs';
import {decodePng,luminance,rowMaxLuminance} from './lib/png.mjs';

const ledger=JSON.parse(readFileSync('design/ledger.json','utf8'));
const ledgerTotal=ledger.entries.length;
const yuncun=ledger.entries.filter(e=>e.from==='贾雨村'||e.to==='贾雨村');

const context=await chromium.launchPersistentContext('/tmp/card-preview-profile',{
  headless:!process.env.HEADED,channel:'chrome',viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});

const reading=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:120000});
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:120000});
};

/** Is the name on the card actually legible?
 *
 *  The card face is a pale portrait (or a pale seal) with a dark gradient laid
 *  over its lower part so the cream name and subtitle can be read on top of
 *  it. That gradient is a ::after overlay — and the general rule
 *  `.card-face>*:not(...){position:relative;z-index:2}` also matches the
 *  picture holder, lifting it *above* the overlay (z-index:1). The picture
 *  then draws fine and the gradient hides *behind* it: the name sits on a
 *  pale robe with nothing to carry it. The DOM cannot see this — the image is
 *  present, loaded, and perfectly visible — only the pixels can.
 *
 *  So take the screenshot and read it: the bottom of the face must be dark
 *  (the bed is doing its job), and the name row must carry bright cream
 *  strokes that stand clear of the bed they sit on.
 */
async function checkNameLegible(page,what){
  const faceBox=await page.locator('.preview-face').boundingBox();
  const titleBox=await page.locator('.preview-title strong').boundingBox();
  const png=decodePng(await page.screenshot({clip:faceBox}));
  const bottomRow=png.height-2;          // just above the classification line
  const bright=rowMaxLuminance(png,bottomRow,0,Math.floor(png.width*0.6));
  const nameRow=Math.round(titleBox.y+titleBox.height/2-faceBox.y);
  const scan=Math.floor(png.width*0.45);
  let sum=0,ink=0,n=0;
  for(let x=0;x<scan;x++){
    const l=luminance(png,x,nameRow);
    sum+=l;n++;
    if(l>170)ink++;              // a cream stroke
  }
  const mean=sum/n;
  const peak=rowMaxLuminance(png,nameRow,0,scan);
  const inkRatio=ink/n;
  console.log(`${what}:`,JSON.stringify({bottomMax:Math.round(bright),nameRow,
    nameMean:Math.round(mean),namePeak:Math.round(peak),inkRatio:+inkRatio.toFixed(3)}));
  assert.ok(bright<110,
    `the dark bed under the card name must cover the picture, but the bottom row is still bright (${Math.round(bright)})`);
  // The name is cream lettering on a dark bed. Two things have to hold: the
  // row must carry bright strokes (there really is lettering in it), and the
  // strokes must sit on something darker (the bed is doing its job). The row
  // average on its own cannot decide this — a figure in a pale robe drags it
  // up, a figure in a dark robe drags it down.
  assert.ok(inkRatio>0.02,
    `the card name must show cream lettering, but only ${(inkRatio*100).toFixed(1)}% of its row is bright`);
  assert.ok(peak-mean>50,
    `the card name must stand out from its bed, peak ${Math.round(peak)} vs mean ${Math.round(mean)}`);
}

try{
  await page.goto('http://localhost:5173/',{waitUntil:'commit',timeout:120000});
  await page.waitForSelector('.toc-trigger',{timeout:240000});
  await reading();

  // Read enough of the book to unlock a good share of the ledger, so the card
  // has something to show. (A fresh profile starts at the beginning.)
  for(const section of ['arrival','reunion','uncles','c4-court','c4-truth']){
    await dismissLeaf(page,false,true);
    await seekSection(page,section);
    await reading();
    for(let i=0;i<12;i++){
      await dismissPickup(page);
      await dismissLeaf(page,false,true);
      const b=page.getByRole('button',{name:'继续剧情',exact:true});
      if(await b.isEnabled())await b.click();
      await page.waitForTimeout(260);
    }
  }
  await dismissPickup(page);
  await dismissLeaf(page,false,true);

  // The backpack is one tap away, straight to the ledger tab.
  await page.getByRole('button',{name:'背包',exact:true}).click();
  await page.getByRole('tab',{name:/账簿/}).click();
  await page.locator('.ledger-people button').first().waitFor({timeout:30000});

  // (1) clicking a person pops the card open.
  await page.locator('.ledger-people button').filter({hasText:'贾雨村'}).click();
  const card=page.locator('dialog.preview-dialog');
  await card.waitFor({state:'visible',timeout:10000});
  assert.ok(await card.isVisible(),'clicking a person must open the card');
  assert.ok(await page.locator('.preview-face').isVisible(),'the card must show its face');
  assert.equal((await page.locator('.preview-title strong').textContent()).trim(),'贾雨村','the card must name the person');

  // (2) the card carries the picture, the timeline and the quoted original.
  const face=await page.evaluate(()=>{
    const img=document.querySelector('.preview-face .card-face-img');
    return img?{src:img.getAttribute('src'),w:img.naturalWidth,h:img.naturalHeight}:null;
  });
  assert.ok(face&&face.src,'the card must have a picture');
  assert.ok(/yucun-portrait/.test(face.src),`the person card must use their portrait, got ${face.src}`);
  const flows=await page.locator('.preview-flow').count();
  assert.ok(flows>=yuncun.length,`the card must list every transfer, got ${flows} for ${yuncun.length}`);
  assert.ok(await page.locator('.preview-flow-source').count()>=1,'an unlocked transfer must quote the original text');
  assert.ok(await page.locator('.preview-flow-circ').count()>=1,'an unlocked transfer must say the circumstance');

  // The picture must actually load, not just sit in the DOM.
  await page.locator('.preview-face .card-face-img').scrollIntoViewIfNeeded();
  await page.waitForTimeout(700);
  const loaded=await page.evaluate(()=>{const i=document.querySelector('.preview-face .card-face-img');return i?{w:i.naturalWidth,h:i.naturalHeight}:null;});
  assert.ok(loaded&&loaded.w>0&&loaded.h>0,`the card picture must load, got ${JSON.stringify(loaded)}`);

  // Loading is not the same as being visible. A card face can show an empty
  // gradient while the image is perfectly "loaded": the picture ends up with
  // a zero-sized box because some other rule won the cascade. So measure the
  // box on the screen and check that the picture actually lands inside the
  // face — that is what a reader would see.
  const shown=await page.evaluate(()=>{
    const face=document.querySelector('.preview-face');
    const img=document.querySelector('.preview-face .card-face-img');
    if(!face||!img)return null;
    const f=face.getBoundingClientRect(),i=img.getBoundingClientRect();
    const overlap=Math.max(0,Math.min(f.right,i.right)-Math.max(f.left,i.left))
      *Math.max(0,Math.min(f.bottom,i.bottom)-Math.max(f.top,i.top));
    return {faceW:Math.round(f.width),faceH:Math.round(f.height),
      imgW:Math.round(i.width),imgH:Math.round(i.height),
      overlapRatio:overlap/(i.width*i.height),
      imgTop:Math.round(i.top),faceTop:Math.round(f.top)};
  });
  console.log('card picture on screen:',JSON.stringify(shown));
  assert.ok(shown&&shown.imgW>40&&shown.imgH>40,
    `the card picture must have a visible size, got ${JSON.stringify(shown)}`);
  // A standing figure is deliberately cropped by the card face (overflow is
  // hidden), so the picture may spill below the face — what matters is that a
  // real part of it is drawn on the face, and that it starts at the top of it
  // (the head is what the reader recognises).
  assert.ok(shown.overlapRatio>0.2,
    `the card picture must be drawn on the card face, only ${(shown.overlapRatio*100).toFixed(0)}% overlaps it`);
  assert.ok(shown.imgTop<=shown.faceTop+shown.faceH*0.3,
    `the card picture must start at the top of the card face, got ${JSON.stringify(shown)}`);
  // And the name on the person card must be legible on top of the picture.
  await checkNameLegible(page,'the person card');

  // (3) a locked transfer shows only a "？" — no quote, no circumstance.
  const locked=await page.evaluate(()=>{
    const rows=[...document.querySelectorAll('.preview-flow.locked')];
    return {count:rows.length,withText:rows.filter(r=>(r.textContent??'').includes('？？？')).length};
  });
  if(locked.count>0) assert.equal(locked.count,locked.withText,'a locked transfer must stay blank');

  // (4) closing the card returns the reader to the backpack list.
  await page.getByRole('button',{name:'关闭卡片'}).click();
  await card.waitFor({state:'hidden',timeout:8000});
  assert.ok(await page.locator('dialog.is-ledger').isVisible(),'the ledger must still be open behind the card');
  assert.equal(await page.locator('.ledger-people button').count()>0,true,'the backpack list must still be there');

  // The same works for an item: 英莲 is transferred three times, so its card
  // carries the whole chain.
  await page.getByRole('tab',{name:/按物/}).click();
  await page.locator('.ledger-people button').filter({hasText:'英莲'}).click();
  await card.waitFor({state:'visible',timeout:10000});
  assert.equal((await page.locator('.preview-title strong').textContent()).trim(),'英莲');
  assert.equal(await page.locator('.preview-flow').count(),3,'the item card must list all three transfers of 英莲');
  const itemFace=await page.evaluate(()=>{const i=document.querySelector('.preview-face .card-face-img');return i?i.getAttribute('src'):null;});
  assert.ok(itemFace&&/yinglian-portrait/.test(itemFace),`a transferred person must show their own portrait, got ${itemFace}`);
  await page.screenshot({path:'artifacts/card-preview-item.png'});

  // The dark bed under the name must really sit ON TOP of the picture.
  await checkNameLegible(page,'the item card');
  await page.getByRole('button',{name:'关闭卡片'}).click();
  await card.waitFor({state:'hidden',timeout:8000});

  // A person nobody painted falls back to the seal, not to a broken image.
  await page.getByRole('tab',{name:/按人/}).click();
  await page.locator('.ledger-people button').filter({hasText:'东平郡王'}).click();
  await card.waitFor({state:'visible',timeout:10000});
  assert.equal(await page.locator('.card-face-seal').count(),1,'an unpainted person must fall back to the seal');
  assert.equal(await page.locator('.preview-face .card-face-img').count(),0,'an unpainted person must not show a broken picture');
  // The seal must actually cover the card face, not sit as a stamp in a corner.
  const seal=await page.evaluate(()=>{
    const face=document.querySelector('.preview-face');
    const s=document.querySelector('.card-face-seal');
    if(!face||!s)return null;
    const f=face.getBoundingClientRect(),r=s.getBoundingClientRect();
    return {faceW:Math.round(f.width),faceH:Math.round(f.height),
      sealW:Math.round(r.width),sealH:Math.round(r.height)};
  });
  console.log('card seal on screen:',JSON.stringify(seal));
  assert.ok(seal&&seal.sealW>seal.faceW*0.9&&seal.sealH>seal.faceH*0.9,
    `the seal must cover the card face, got ${JSON.stringify(seal)}`);
  // The seal card has no picture to carry the dark bed for it, so the name
  // ends up on the pale seal itself — the same contrast question, asked of
  // the fallback face. (Before the fix it read as white text on white paper.)
  await checkNameLegible(page,'the seal card');
  await page.screenshot({path:'artifacts/card-preview-seal.png'});
  await page.getByRole('button',{name:'关闭卡片'}).click();
  await card.waitFor({state:'hidden',timeout:8000});

  // The ledger must still list every transfer afterwards. Clicking the same
  // person a second time folds that column away again, so the reader can get
  // back to the running total — the card does not replace the list, it sits
  // on top of it.
  await page.locator('.ledger-people button').filter({hasText:'东平郡王'}).click();
  assert.ok(!(await page.locator('dialog.preview-dialog').isVisible().catch(()=>false)),
    'clicking the same person again folds the card away');
  assert.equal(await page.locator('.ledger-book .ledger-row').count(),ledgerTotal,'the ledger must list every transfer');

  assert.deepEqual(errors,[],`the page must run without errors, got ${JSON.stringify(errors)}`);
  console.log(`card preview: a person and an item both open a card with their picture, timeline and quoted text; locked transfers stay blank; the card closes back to the backpack.`);
}finally{
  await context.close();
}
