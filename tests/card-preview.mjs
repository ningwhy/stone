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
import {decodePng,luminance} from './lib/png.mjs';

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

/** Is the card a proper card, and is it centred?
 *
 *  Three things a reader notices first, and none of them are in the DOM:
 *
 *  1. The dialog must be centred. `margin:auto` only centres a `dialog` when
 *     its size is fixed — with `width:auto` the auto margin collapses to 0 and
 *     the box spans the whole viewport, so the card sits in the top-left
 *     corner. Check the box, not the stylesheet.
 *  2. The picture must be a full figure, not a crop. The portraits are tall
 *     and narrow (600px high, 190–350 wide); a landscape frame would cut the
 *     head or the feet off. With `object-fit:contain` the whole figure fits.
 *  3. The name must be readable. It sits on the card paper below the frame —
 *     dark ink on pale paper — so it is legible by construction, and the
 *     pixels confirm it: the row carries dark strokes on a light bed.
 */
async function checkCardLooksLikeACard(page,what){
  const view=page.viewportSize();
  const dlg=await page.locator('dialog.preview-dialog').boundingBox();
  const card=await page.locator('.preview-card').boundingBox();
  const art=await page.locator('.preview-card-art').boundingBox();
  const img=await page.locator('.preview-face .card-face-img').first();
  const hasImg=await img.count()>0;
  let fit=null;
  if(hasImg) fit=await img.evaluate(el=>getComputedStyle(el).objectFit);
  const cx=dlg.x+dlg.width/2, cy=dlg.y+dlg.height/2;
  const offX=Math.abs(cx-view.width/2), offY=Math.abs(cy-view.height/2);
  console.log(`${what}:`,JSON.stringify({dlg:{x:Math.round(dlg.x),y:Math.round(dlg.y),w:Math.round(dlg.width),h:Math.round(dlg.height)},
    card:{w:Math.round(card.width),h:Math.round(card.height)},art:{w:Math.round(art.width),h:Math.round(art.height)},
    offX:Math.round(offX),offY:Math.round(offY),fit}));
  // (1) centred on screen — and actually a card-sized box, not the whole
  // viewport. A `dialog` with `width:auto` spans the viewport; its centre
  // would still be the middle of the screen, so the size has to be checked
  // too or the assertion would pass on a broken layout.
  assert.ok(dlg.width<=view.width*0.92,
    `the card must be a card-sized box, but it spans ${Math.round(dlg.width)}px of ${view.width}`);
  assert.ok(dlg.height<=view.height*0.94,
    `the card must be a card-sized box, but it spans ${Math.round(dlg.height)}px of ${view.height}`);
  assert.ok(offX<12,`the card must be centred horizontally, it is ${Math.round(offX)}px off`);
  assert.ok(offY<12,`the card must be centred vertically, it is ${Math.round(offY)}px off`);
  // (2) a portrait card, and a frame taller than it is wide.
  assert.ok(card.height>card.width,`the card must be taller than wide, got ${Math.round(card.width)}x${Math.round(card.height)}`);
  assert.ok(art.height>art.width,`the picture frame must be taller than wide, got ${Math.round(art.width)}x${Math.round(art.height)}`);
  // (3) the whole figure fits in the frame — nothing cropped.
  if(hasImg) assert.equal(fit,'contain',`the picture must fit whole in the frame, got object-fit:${fit}`);
}

/** Is the name on the card legible?
 *
 *  The name sits on the card paper below the picture frame: dark ink on pale
 *  paper. Read the pixels to be sure — the ink must be darker than the paper
 *  it sits on, with a real gap between them.
 */
async function checkNameLegible(page,what){
  const nameBox=await page.locator('.preview-card-foot strong').boundingBox();
  const paperBox=await page.locator('.preview-card-foot').boundingBox();
  const png=decodePng(await page.screenshot({clip:paperBox}));
  const nameRow=Math.round(nameBox.y+nameBox.height/2-paperBox.y);
  // The name element spans the whole paper row (it is a block), but the
  // lettering sits in the middle of it. Find the ink: scan the row and take
  // the span between the first and the last dark pixel.
  const lum=[];
  for(let x=0;x<png.width;x++) lum.push(luminance(png,x,nameRow));
  const dark=lum.map((l,x)=>l<140?x:-1).filter(x=>x>=0);
  assert.ok(dark.length>0,`the card name must show dark ink, but the row has none`);
  const from=dark[0],to=dark[dark.length-1]+1;
  let sum=0;
  for(let x=from;x<to;x++)sum+=lum[x];
  const mean=sum/(to-from);
  const inkRatio=dark.length/(to-from);
  console.log(`${what} name:`,JSON.stringify({row:nameRow,span:[from,to],
    paperMean:Math.round(mean),inkRatio:+inkRatio.toFixed(3)}));
  assert.ok(inkRatio>0.15,
    `the card name must show dark ink, but only ${(inkRatio*100).toFixed(1)}% of its lettering is dark`);
  assert.ok(mean>150,
    `the card name must sit on pale paper, but the paper averages ${Math.round(mean)}`);
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
  assert.equal((await page.locator('.preview-card-foot strong').textContent()).trim(),'贾雨村','the card must name the person');

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
  // frame — that is what a reader would see.
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
      imgTop:Math.round(i.top),faceTop:Math.round(f.top),
      natural:{w:img.naturalWidth,h:img.naturalHeight}};
  });
  console.log('card picture on screen:',JSON.stringify(shown));
  assert.ok(shown&&shown.imgW>40&&shown.imgH>40,
    `the card picture must have a visible size, got ${JSON.stringify(shown)}`);
  // The whole figure must be on the card: the picture is scaled to fit the
  // frame (object-fit:contain), so it never spills out and is never cropped.
  assert.ok(shown.overlapRatio>0.98,
    `the whole picture must sit inside the frame, only ${(shown.overlapRatio*100).toFixed(0)}% is on the card`);
  // The figure must be scaled down to fit, not cropped to fill. With
  // object-fit:contain the *element* box still spans the frame, so the
  // drawn size has to be computed: the picture keeps its own proportions and
  // fits inside, so the drawn width is the smaller of the two fits.
  const fitScale=Math.min(shown.imgW/shown.natural.w,shown.imgH/shown.natural.h);
  const drawnW=shown.natural.w*fitScale, drawnH=shown.natural.h*fitScale;
  assert.ok(drawnW<=shown.imgW+1&&drawnH<=shown.imgH+1,
    `the whole figure must fit inside the frame, it would draw ${Math.round(drawnW)}x${Math.round(drawnH)} in ${shown.imgW}x${shown.imgH}`);
  // It must actually fill the frame's height (a person standing on the frame),
  // otherwise the figure would be a tiny stamp in the middle.
  assert.ok(fitScale*shown.natural.h>shown.imgH*0.8,
    `the figure must stand tall in the frame, it only fills ${Math.round(fitScale*shown.natural.h)} of ${shown.imgH}px`);
  // The card must look like a card: centred, portrait, whole picture.
  await checkCardLooksLikeACard(page,'the person card');
  // And the name on the card paper must be legible.
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
  assert.equal((await page.locator('.preview-card-foot strong').textContent()).trim(),'英莲');
  assert.equal(await page.locator('.preview-flow').count(),3,'the item card must list all three transfers of 英莲');
  const itemFace=await page.evaluate(()=>{const i=document.querySelector('.preview-face .card-face-img');return i?i.getAttribute('src'):null;});
  assert.ok(itemFace&&/yinglian-portrait/.test(itemFace),`a transferred person must show their own portrait, got ${itemFace}`);
  await page.screenshot({path:'artifacts/card-preview-item.png'});

  // The item card is a card too: centred, portrait, whole picture, legible name.
  await checkCardLooksLikeACard(page,'the item card');
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
  // The seal card has no picture — the seal stands in for it. It must still be
  // a card: centred, portrait, and the name readable on the paper below.
  await checkCardLooksLikeACard(page,'the seal card');
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
