import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
const reading=async()=>{for(let i=0;i<5;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(60);}}await page.locator('.dialogue-text').waitFor();await page.locator('.game-map[data-scene-ready]').waitFor();};
try{
 await page.goto(process.env.TEST_URL??'http://127.0.0.1:4173');await reading();
 await page.getByRole('button',{name:'设置',exact:true}).click();await page.getByRole('button',{name:'人物图鉴',exact:true}).click();
 await page.locator('.cast-gallery').evaluate(e=>{e.scrollTop=0;});
 await page.waitForFunction(()=>[...document.querySelectorAll('.cast-gallery img')].every(i=>i.complete&&i.naturalWidth>0));
 const images=await page.locator('.cast-gallery img').evaluateAll(images=>images.map(i=>({src:i.getAttribute('src'),closeup:!!i.closest('.portrait-closeup'),height:i.getBoundingClientRect().height,frame:i.closest('.gallery-portrait').getBoundingClientRect().height})));
 assert.equal(images.length,38);for(const i of images){assert.match(i.src,/\?v=[a-f0-9]{12}$/);assert.ok(i.closeup);assert.ok(i.height>i.frame*.9);}
 assert.ok(images.filter(i=>i.height>i.frame*1.3).length>=35);
 await page.screenshot({path:'artifacts/character-identities-gallery.png'});
 await page.getByRole('button',{name:'查看林黛玉资料',exact:true}).click();assert.equal(await page.locator('.character-detail .portrait-closeup').count(),1);await page.screenshot({path:'artifacts/character-identity-daiyu.png'});await page.keyboard.press('Escape');
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('feng');await reading();
 for(let i=0;i<8&&(await page.locator('.node-label').textContent())!=='F006';i++){await page.getByRole('button',{name:'继续剧情',exact:true}).click();await reading();}
 assert.equal(await page.locator('.node-label').textContent(),'F006');assert.match(await page.locator('.speaker-portrait img').getAttribute('src'),/feng-portrait\.webp\?v=/);await page.screenshot({path:'artifacts/character-identity-feng.png'});
 const manifest=JSON.parse(readFileSync('public/assets/rongguo/manifest.json'));assert.equal(Object.values(manifest.assets).filter(a=>a.identity).length,76);assert.deepEqual(errors,[]);
 console.log('Passed: 38 versioned close-up portraits, face detail, paired 76-asset manifest, fixed dialogue frame and new Feng portrait in live scene.');
}finally{await browser.close();}
