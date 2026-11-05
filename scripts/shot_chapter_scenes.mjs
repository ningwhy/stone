/** Screenshot every section of a chapter for 目检.
 *
 *  The browser smoke test only walks chapters 1–4, so a new chapter's stages were never
 *  looked at. This jumps through the table of contents — the same path a reader takes —
 *  and writes one screenshot per section into artifacts/ch<from><to>/.
 *
 *  Usage: node scripts/shot_chapter_scenes.mjs 10 11 12
 */
import {chromium} from 'playwright';
import {readFileSync,mkdirSync} from 'node:fs';
import {dismissPickup} from '../tests/lib/pickup.mjs';
import {seekSection} from '../tests/lib/toc.mjs';
const books=process.argv.slice(2).map(Number);
if(!books.length)throw new Error('pass the chapter numbers, e.g. 10 11 12');
const sections=books.flatMap(n=>JSON.parse(readFileSync(`design/chapter${String(n).padStart(2,'0')}-sections.json`,'utf8')));
const out=`artifacts/ch${books.join('')}`;
const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||chrome});
const page=await (await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'})).newPage();
const errs=[];page.on('pageerror',e=>errs.push(e.message));page.on('console',m=>{if(m.type()==='error')errs.push(m.text());});
mkdirSync(out,{recursive:true});
await page.goto(process.env.TEST_URL??'http://127.0.0.1:5173');
for(const s of sections){
 await seekSection(page,s.id);
 await page.locator('.loading-screen').waitFor({state:'detached',timeout:20000});
 await dismissPickup(page);
 for(let i=0;i<4;i++){const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible()){await b.click();await page.waitForTimeout(80);}}
 await page.waitForFunction(()=>!!document.querySelector('.dialogue-text')?.textContent?.trim());
 await page.locator('.game-map[data-scene-ready]').waitFor();
 await page.waitForTimeout(500);
 await page.screenshot({path:`${out}/${s.id}-${s.scene}.png`});
 console.log(s.id, s.title, s.scene, await page.locator('.node-label').textContent());
}
console.log(`console errors: ${errs.length}`, errs.slice(0,5));
await browser.close();
