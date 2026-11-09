import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import { seekSection } from './lib/toc.mjs';
import { dismissLeaf } from './lib/pickup.mjs';
// 图鉴列出的是 cast 里除 sedan 外的每个人（App.tsx 遍历 Object.keys(cast)）。
// 人数从 manifest 的 -portrait 资源实读，写死 38 的话每加一批角色就要改一次断言，
// 改漏了会把「新人物没进图鉴」掩盖过去——这正是之前 38 与实际 68 脱节的原因。
const manifestAssets=JSON.parse(readFileSync('public/assets/rongguo/manifest.json')).assets;
const castCount=Object.keys(manifestAssets).filter(k=>k.endsWith('-portrait')).length;
// 只有带 identity.faceBox 的立绘才会被 Portrait.tsx 裁成脸部特写，其余以全身像呈现。
// 这是脸部设计元数据（art/identity）的缺口，不是渲染 bug——特写数应等于带 faceBox 的立绘数。
const portraitWithFaceBox=Object.entries(manifestAssets).filter(([k,v])=>k.endsWith('-portrait')&&v.identity?.faceBox).length;
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
const reading=async()=>{for(let i=0;i<5;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(60);}}await page.locator('.dialogue-text').waitFor();await page.locator('.game-map[data-scene-ready]').waitFor();};
try{
 await page.goto(process.env.TEST_URL??'http://127.0.0.1:4173');await reading();
 // 开书第一格压着封面，会挡住「设置」按钮——先收掉再点。
 await dismissLeaf(page,false,true);
 await page.getByRole('button',{name:'设置',exact:true}).click();await page.getByRole('button',{name:'人物图鉴',exact:true}).click();
 await page.locator('.cast-gallery').evaluate(e=>{e.scrollTop=0;});
 await page.waitForFunction(()=>[...document.querySelectorAll('.cast-gallery img')].every(i=>i.complete&&i.naturalWidth>0));
 const images=await page.locator('.cast-gallery img').evaluateAll(images=>images.map(i=>({src:i.getAttribute('src'),closeup:!!i.closest('.portrait-closeup'),height:i.getBoundingClientRect().height,frame:i.closest('.gallery-portrait').getBoundingClientRect().height})));
 assert.equal(images.length,castCount);
 const closeups=images.filter(i=>i.closeup).length;
 // 特写数必须等于带 faceBox 的立绘数：有 faceBox 就必须裁成特写（守渲染不变）；
 // 其余 castCount-portraitWithFaceBox 张是缺 faceBox 元数据、以全身像呈现的数据缺口。
 assert.equal(closeups,portraitWithFaceBox,`脸部特写 ${closeups} 张须等于带 faceBox 的立绘 ${portraitWithFaceBox} 张（另有 ${castCount-portraitWithFaceBox} 张缺 faceBox 元数据，以全身像呈现）`);
 for(const i of images){assert.match(i.src,/\?v=[a-f0-9]{12}$/);assert.ok(i.height>i.frame*.9);}
 assert.ok(images.filter(i=>i.height>i.frame*1.3).length>=35);
 await page.screenshot({path:'artifacts/character-identities-gallery.png'});
 await page.getByRole('button',{name:'查看林黛玉资料',exact:true}).click();assert.equal(await page.locator('.character-detail .portrait-closeup').count(),1);await page.screenshot({path:'artifacts/character-identity-daiyu.png'});await page.keyboard.press('Escape');
 await seekSection(page, 'feng');await reading();
 for(let i=0;i<8&&(await page.locator('.node-label').textContent())!=='F006';i++){await page.getByRole('button',{name:'继续剧情',exact:true}).click();await reading();}
 assert.equal(await page.locator('.node-label').textContent(),'F006');assert.match(await page.locator('.speaker-portrait img').getAttribute('src'),/feng-portrait\.webp\?v=/);await page.screenshot({path:'artifacts/character-identity-feng.png'});
const manifest=JSON.parse(readFileSync('public/assets/rongguo/manifest.json'));assert.equal(Object.values(manifest.assets).filter(a=>a.identity).length,92);assert.deepEqual(errors,[]);
console.log(`Passed: ${castCount} versioned portraits (${portraitWithFaceBox} face close-ups; ${castCount-portraitWithFaceBox} 缺 faceBox 以全身像呈现), paired 92-asset manifest (76 cast bitmaps plus the 16 portrait emotion variants), fixed dialogue frame and new Feng portrait in live scene.`);
}finally{await browser.close();}
