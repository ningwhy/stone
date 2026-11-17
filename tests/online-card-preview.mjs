// Targeted online re-verification for the backpack card page:
//
//   1. clicking a person in the ledger opens a card on top of the ledger;
//   2. the card carries a big picture, the name, the transfer timeline and the
//      quoted original text;
//   3. the picture really loads from the origin, not a broken image;
//   4. closing the card leaves the reader back in the backpack list.
//
// Usage: node tests/online-card-preview.mjs
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdirSync,readFileSync} from 'node:fs';
import {dismissPickup,dismissLeaf} from './lib/pickup.mjs';
import {seekSection} from './lib/toc.mjs';
import {onlineUrl, onlineTag, onlineArgs, ignoreTlsErrors, onlineProfile} from './lib/online.mjs';
import {decodePng,luminance} from './lib/png.mjs';

const profile=onlineProfile('card-preview');
const context=await chromium.launchPersistentContext(profile,{
  headless:false,channel:'chrome',viewport:{width:1440,height:900},reducedMotion:'reduce',
  ignoreHTTPSErrors:ignoreTlsErrors(),args:onlineArgs()});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});
const tag=onlineTag();

const ledger=JSON.parse(readFileSync('design/ledger.json','utf8'));
const ledgerTotal=ledger.entries.length;

const dismiss=async()=>{await dismissPickup(page);await page.waitForTimeout(120);};
const reading=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:120000});
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:120000});
};

try{
  await page.goto(onlineUrl(),{waitUntil:'commit',timeout:120000});
  await page.waitForSelector('.toc-trigger',{timeout:240000});
  await reading();

  // Read enough of the book to unlock a good share of the ledger, so the card
  // has something to show. (A fresh profile starts at the beginning.)
  for(const section of ['arrival','reunion','uncles','c4-court','c4-truth']){
    await dismissLeaf(page,false,true);
    await seekSection(page, section);
    await reading();
    for(let i=0;i<12;i++){
      await dismiss();
      await dismissLeaf(page,false,true);
      const b=page.getByRole('button',{name:'继续剧情',exact:true});
      if(await b.isEnabled())await b.click();
      await page.waitForTimeout(280);
    }
  }
  await dismiss();
  await dismissLeaf(page,false,true);

  await page.getByRole('button',{name:'背包',exact:true}).click();
  await page.getByRole('tab',{name:/账簿/}).click();
  await page.locator('.ledger-row').first().waitFor({timeout:30000});
  await page.waitForTimeout(1200);

  // (1) clicking a person opens a card on top of the ledger.
  await page.locator('.ledger-people button').filter({hasText:'贾雨村'}).first().click();
  const dialog=page.locator('dialog.preview-dialog');
  await dialog.waitFor({state:'visible',timeout:15000});
  const title=await page.locator('.preview-card-foot strong').first().textContent();
  assert.equal(title.trim(),'贾雨村','the card must be the person that was clicked');
  console.log(`${tag} card title:`,title.trim());

  // (2) the card carries a picture, the timeline and the quoted original.
  const face=await page.evaluate(()=>{
    const dlg=document.querySelector('dialog.preview-dialog');
    if(!dlg)return null;
    const img=dlg.querySelector('.preview-face img');
    const box=e=>{if(!e)return null;const r=e.getBoundingClientRect();
      return {w:Math.round(r.width),h:Math.round(r.height),x:Math.round(r.x),y:Math.round(r.y)};};
    return {
      hasFace:!!dlg.querySelector('.preview-face'),
      kind:dlg.querySelector('.preview-kind')?.textContent?.trim(),
      kicker:dlg.querySelector('.preview-kicker')?.textContent?.trim(),
      flows:dlg.querySelectorAll('.preview-flow').length,
      quoted:dlg.querySelectorAll('.preview-flow-source').length,
      sealed:dlg.querySelectorAll('.card-seal').length,
      ledgerLine:dlg.querySelector('.preview-ledger')?.textContent?.trim(),
      imgSrc:img?.getAttribute('src')??null,
      imgW:img?.naturalWidth??0,
      imgH:img?.naturalHeight??0,
      imgFit:img?getComputedStyle(img).objectFit:null,
      dialog:box(dlg),
      card:box(dlg.querySelector('.preview-card')),
      art:box(dlg.querySelector('.preview-card-art')),
      viewport:{w:innerWidth,h:innerHeight},
    };
  });
  console.log(`${tag} card face:`,JSON.stringify(face));
  assert.ok(face.hasFace,'the card must have a face');
  assert.ok(face.flows>0,'the card must list the transfers');
  assert.ok(face.quoted>0,'the card must quote the original text');
  assert.ok(face.sealed>0,'the card must stamp the chapter');
  assert.match(face.ledgerLine,/\d+\/\d+ 笔入账/,'the card must say how much is on the books');

  // (2b) the chapters named on the card must be the chapters already on the
  // books. A chapter the reader has not reached yet must not be named —
  // that would be telling them the story before they read it.
  const named=await page.evaluate(()=>{
    const dlg=document.querySelector('dialog.preview-dialog');
    const line=dlg.querySelector('.preview-ledger')?.textContent??'';
    const m=line.match(/出场于\s*(.+)$/);
    const names=m?m[1].split('、').map(s=>s.trim()).filter(Boolean):[];
    const unlocked=dlg.querySelectorAll('.preview-flow:not(.locked)').length;
    const locked=dlg.querySelectorAll('.preview-flow.locked').length;
    const books=[...new Set([...dlg.querySelectorAll('.preview-flow:not(.locked) .card-seal')]
      .map(s=>s.textContent.trim()))];
    return {names,unlocked,locked,books};
  });
  console.log(`${tag} card chapters:`,JSON.stringify(named));
  assert.ok(named.unlocked>0,'some transfers must be on the books');
  assert.equal(named.names.length,named.books.length,
    `the card names ${named.names.length} chapters but only ${named.books.length} are on the books — it must not spoil unread chapters`);

  // (3) the picture really comes back from the origin with real pixels.
  await page.waitForTimeout(1200);
  const pic=await page.evaluate(()=>{
    const img=document.querySelector('dialog.preview-dialog .preview-face img');
    return img?{src:img.getAttribute('src'),w:img.naturalWidth,h:img.naturalHeight}:null;
  });
  console.log(`${tag} card picture:`,JSON.stringify(pic));
  assert.ok(pic,'the card must show a picture');
  assert.ok(pic.w>0&&pic.h>0,'the card picture must have real pixels');

  await page.locator('dialog.preview-dialog .preview-card').screenshot({path:`artifacts/card-preview-online-face-${tag}.png`});
  await page.locator('dialog.preview-dialog').screenshot({path:`artifacts/card-preview-online-${tag}.png`});

  // The card must be a card on the live site too: centred, portrait, whole
  // picture. A `dialog` with `width:auto` spans the viewport and sits in the
  // top-left corner — its centre would still be the middle of the screen, so
  // the size has to be checked as well.
  const cx=face.dialog.x+face.dialog.w/2, cy=face.dialog.y+face.dialog.h/2;
  const offX=Math.abs(cx-face.viewport.w/2), offY=Math.abs(cy-face.viewport.h/2);
  console.log(`${tag} card box:`,JSON.stringify({dialog:face.dialog,card:face.card,art:face.art,
    offX:Math.round(offX),offY:Math.round(offY),fit:face.imgFit}));
  assert.ok(face.dialog.w<=face.viewport.w*0.92,
    `the card must be a card-sized box, but it spans ${face.dialog.w}px of ${face.viewport.w}`);
  assert.ok(offX<12,`the card must be centred horizontally, it is ${Math.round(offX)}px off`);
  assert.ok(offY<12,`the card must be centred vertically, it is ${Math.round(offY)}px off`);
  assert.ok(face.card.h>face.card.w,`the card must be taller than wide, got ${face.card.w}x${face.card.h}`);
  assert.ok(face.art.h>face.art.w,`the picture frame must be taller than wide, got ${face.art.w}x${face.art.h}`);
  assert.equal(face.imgFit,'contain',`the picture must fit whole in the frame, got object-fit:${face.imgFit}`);

  // The name sits on the card paper below the frame: dark ink on pale paper.
  // Only the pixels can say for sure.
  const nameBox=await page.locator('dialog.preview-dialog .preview-card-foot strong').boundingBox();
  const paperBox=await page.locator('dialog.preview-dialog .preview-card-foot').boundingBox();
  const png=decodePng(await page.screenshot({clip:paperBox}));
  const nameRow=Math.round(nameBox.y+nameBox.height/2-paperBox.y);
  const lum=[];
  for(let x=0;x<png.width;x++)lum.push(luminance(png,x,nameRow));
  const dark=lum.map((l,x)=>l<140?x:-1).filter(x=>x>=0);
  assert.ok(dark.length>0,'the card name must show dark ink, but the row has none');
  const from=dark[0],to=dark[dark.length-1]+1;
  let sum=0;
  for(let x=from;x<to;x++)sum+=lum[x];
  const mean=sum/(to-from),inkRatio=dark.length/(to-from);
  console.log(`${tag} card name pixels:`,JSON.stringify({paperMean:Math.round(mean),inkRatio:+inkRatio.toFixed(3)}));
  assert.ok(inkRatio>0.15,
    `the card name must show dark ink, but only ${(inkRatio*100).toFixed(1)}% of its lettering is dark`);
  assert.ok(mean>150,
    `the card name must sit on pale paper, but the paper averages ${Math.round(mean)}`);

  // (4) closing the card leaves the reader back in the backpack. The card sits
  // on top of the ledger rather than replacing it, so the column behind it
  // stays on that person; clicking the same person again folds that column
  // away and the running total is back.
  await page.getByRole('button',{name:'关闭卡片'}).click();
  await dialog.waitFor({state:'hidden',timeout:10000});
  assert.ok(await page.locator('dialog.is-ledger').isVisible(),'the ledger must still be open behind the card');
  assert.ok(await page.locator('.ledger-people button').count()>0,'the backpack list must still be there');
  await page.locator('.ledger-people button').filter({hasText:'贾雨村'}).first().click();
  await page.waitForTimeout(400);
  assert.equal(await page.locator('.ledger-book .ledger-row').count(),ledgerTotal,
    'the ledger must list every transfer once the column is folded away');

  assert.equal(errors.length,0,`the page must be free of errors, got ${JSON.stringify(errors)}`);
  console.log(`${tag} card preview: a person opens a card with a real picture, the timeline and the quoted text; closing it returns to the backpack.`);
}finally{
  await context.close();
}
