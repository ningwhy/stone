import {chromium} from 'playwright';
import {existsSync,mkdirSync} from 'node:fs';
import { seekSection } from './lib/toc.mjs';
/**
 * Layout probe for the chapter-six 凤姐院 stage (c6_wangchui).
 *
 * It reports, in Phaser screen coordinates, where each art sprite and each
 * walker actually lands, so the "building sits on top of the people" complaint
 * can be checked against real numbers instead of eyeballed screenshots.
 */
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||(existsSync(chrome)?chrome:undefined)});
const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
mkdirSync('artifacts',{recursive:true});
const read=async()=>{
  await page.locator('.loading-screen').waitFor({state:'detached',timeout:60000});
  for(let i=0;i<10;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(60);}}
  await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim(),undefined,{timeout:60000});
  await page.locator('.game-map[data-scene-ready]').waitFor({timeout:60000});
  await page.waitForTimeout(400);
};
const probe=()=>page.evaluate(()=>{
  const scene=window.__mapScene;
  if(!scene)return null;
  const map=scene.mapData;
  const cam=scene.cameras.main;
  const state=scene.engine.getSnapshot();
  const art=scene.artViews.map(({view,object})=>({
    name:object.name,asset:object.asset,visibility:object.visibility,interiorZone:object.interiorZone??null,
    visible:view.visible,alpha:view.alpha,depth:view.depth,
    // Phaser screen rectangle of the drawn image (origin 0.5,1 => bottom-centre anchor)
    screen:{x:Math.round(view.x-cam.worldView.x),y:Math.round(view.y-cam.worldView.y),
            w:Math.round(view.displayWidth),h:Math.round(view.displayHeight)},
    world:{x:Math.round(object.x),y:Math.round(object.y)},
    cell:(()=>{const c=(object.x-object.y)/64+0.5,r=(object.x+object.y)/128+0.5;return {c:+c.toFixed(1),r:+r.toFixed(1)};})(),
  }));
  const actors=Object.entries(state.actors).filter(([,a])=>a.visible).map(([id,a])=>{
    const v=scene.actorViews.get(id);
    return {id,col:a.col,row:a.row,
      screen:{x:Math.round(v.x-cam.worldView.x),y:Math.round(v.y-cam.worldView.y)},
      zone:map.zones.find(z=>a.col>=z.col&&a.col<z.col+z.width&&a.row>=z.row&&a.row<z.row+z.height)?.id??null};
  });
  const labels=map.labels.map(l=>({text:l.text,col:l.point.col,row:l.point.row}));
  return {scene:map.id,zoom:cam.zoom,canvas:{w:cam.width,h:cam.height},art,actors,labels,
    zones:map.zones.map(z=>({id:z.id,col:z.col,row:z.row,w:z.width,h:z.height,indoor:!!z.indoor})),
    anchors:Object.entries(map.anchors).map(([n,p])=>({name:n,col:p.col,row:p.row}))};
});
try{
  await page.goto(process.env.TEST_URL??'http://127.0.0.1:5173');await read();
  for(const section of ['c6-backgate','c6-zhourui','c6-feng','c6-audience','c6-gift']){
    await seekSection(page, section);await read();
    const info=await probe();
    console.log(`\n=== ${section} (${info.scene}) zoom=${info.zoom.toFixed(2)} canvas=${info.canvas.w}x${info.canvas.h} ===`);
    console.log('actors(screen):',info.actors.map(a=>`${a.id}@(${a.col},${a.row}) z=${a.zone} s=(${a.screen.x},${a.screen.y})`).join(' | '));
    console.log('art(screen):');
    for(const a of info.art)console.log(`   ${a.asset.padEnd(15)} vis=${String(a.visible).padEnd(5)} a=${a.alpha.toFixed(2)} cell=(${a.cell.c},${a.cell.r}) screen=(${a.screen.x},${a.screen.y}) ${a.screen.w}x${a.screen.h}`);
    console.log('labels:',info.labels.map(l=>`${l.text}@(${l.col},${l.row})`).join(' '));
    await page.screenshot({path:`artifacts/probe-${section}.png`,fullPage:true});
  }
  console.log('\nerrors:',JSON.stringify(errors));
}finally{await context.close();await browser.close();}
