import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'}),errors=[];
page.on('pageerror',e=>errors.push(e.message));
const read=async()=>{for(let i=0;i<5;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(60);}}await page.locator('.dialogue-text').waitFor();await page.locator('.game-map[data-scene-ready]').waitFor();};
try{
 await page.goto('http://127.0.0.1:5173');await read();
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('c1-disaster');await read();
 for(let i=0;i<8&&await page.locator('.game-map').getAttribute('data-scene-ready')!=='ruins';i++){await page.getByRole('button',{name:'继续剧情',exact:true}).click();await read();}
 assert.equal(await page.locator('.game-map').getAttribute('data-scene-ready'),'ruins');await page.screenshot({path:'artifacts/prequel-fire-ruins.png'});
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('arrival');await read();await page.screenshot({path:'artifacts/ning-rong-street.png'});
 await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption('uncles');await read();await page.screenshot({path:'artifacts/black-oil-gate.png'});
 await page.getByRole('button',{name:'荣国府总览',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.world-location image[data-loaded=true]').length===10);
 await page.waitForFunction(()=>[...document.querySelectorAll('image[href*="manor-main-gate"]')].some(n=>n.dataset.loaded==='true'));
 await page.getByRole('button',{name:'查看王熙凤院地点',exact:true}).click();assert.ok((await page.locator('.world-detail').textContent()).includes('粉油'));await page.getByRole('button',{name:'关闭地点详情'}).click();
 await page.screenshot({path:'artifacts/rongguo-geography-corrected.png'});
assert.deepEqual(errors,[]);const manifest=JSON.parse(readFileSync('public/assets/rongguo/manifest.json'));assert.equal(Object.keys(manifest.assets).length,134);
console.log('Passed: final main-gate, west-gate, black-oil-gate and fire-ruins artwork; accessible estate labels; 134 runtime assets.');
}finally{await browser.close();}
