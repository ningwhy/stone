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
import {decodePng,luminance,rowMaxLuminance} from './lib/png.mjs';

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
  const title=await page.locator('.preview-title strong').first().textContent();
  assert.equal(title.trim(),'贾雨村','the card must be the person that was clicked');
  console.log(`${tag} card title:`,title.trim());

  // (2) the card carries a picture, the timeline and the quoted original.
  const face=await page.evaluate(()=>{
    const dlg=document.querySelector('dialog.preview-dialog');
    if(!dlg)return null;
    const img=dlg.querySelector('.preview-face img');
    return {
      hasFace:!!dlg.querySelector('.preview-face'),
      badge:dlg.querySelector('.preview-badge')?.textContent?.trim(),
      kicker:dlg.querySelector('.preview-kicker')?.textContent?.trim(),
      flows:dlg.querySelectorAll('.preview-flow').length,
      quoted:dlg.querySelectorAll('.preview-flow-source').length,
      sealed:dlg.querySelectorAll('.card-seal').length,
      ledgerLine:dlg.querySelector('.preview-ledger')?.textContent?.trim(),
      imgSrc:img?.getAttribute('src')??null,
      imgW:img?.naturalWidth??0,
      imgH:img?.naturalHeight??0,
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

  await page.locator('dialog.preview-dialog .preview-face').screenshot({path:`artifacts/card-preview-online-face-${tag}.png`});
  await page.locator('dialog.preview-dialog').screenshot({path:`artifacts/card-preview-online-${tag}.png`});

  // The name must be legible ON the card face, and only the pixels can say.
  // A missing dark bed leaves cream lettering on a pale robe: the DOM looks
  // perfect (the image is there, the gradient exists), the reader sees
  // nothing. So read the picture that was just taken.
  const faceBox=await page.locator('dialog.preview-dialog .preview-face').boundingBox();
  const titleBox=await page.locator('dialog.preview-dialog .preview-title strong').boundingBox();
  const png=decodePng(await page.screenshot({clip:faceBox}));
  const scan=Math.floor(png.width*0.45);
  const nameRow=Math.round(titleBox.y+titleBox.height/2-faceBox.y);
  let sum=0,ink=0;
  for(let x=0;x<scan;x++){
    const l=luminance(png,x,nameRow);
    sum+=l;
    if(l>170)ink++;
  }
  const mean=sum/scan,peak=rowMaxLuminance(png,nameRow,0,scan),inkRatio=ink/scan;
  const bottomMax=rowMaxLuminance(png,png.height-2,0,Math.floor(png.width*0.6));
  console.log(`${tag} card name pixels:`,JSON.stringify({bottomMax:Math.round(bottomMax),
    nameMean:Math.round(mean),namePeak:Math.round(peak),inkRatio:+inkRatio.toFixed(3)}));
  assert.ok(bottomMax<110,
    `the dark bed under the card name must cover the picture, but the bottom row is still bright (${Math.round(bottomMax)})`);
  assert.ok(inkRatio>0.02,
    `the card name must show cream lettering, but only ${(inkRatio*100).toFixed(1)}% of its row is bright`);
  assert.ok(peak-mean>50,
    `the card name must stand out from its bed, peak ${Math.round(peak)} vs mean ${Math.round(mean)}`);

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
