import {chromium} from 'playwright';
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
const page=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
const reading=async()=>{await page.locator('.dialogue-text').waitFor();await page.locator('.game-map[data-scene-ready]').waitFor();};
const node=()=>page.locator('.node-label').textContent();
const next=async()=>{const before=await node();await page.getByRole('button',{name:'继续剧情',exact:true}).click();await page.waitForFunction(id=>document.querySelector('.node-label')?.textContent!==id,before);const b=page.getByRole('button',{name:'跳过移动',exact:true});if(await b.isVisible())await b.click();await reading();};
await page.goto('http://127.0.0.1:5173');await reading();
const shots=[
  ['dinner','dinner','D001'],
  ['dinner-late','dinner','D005'],
  ['night','night','T001'],
  ['tavern','c1-home','C1-030'],
  ['suzhou','c1-home','C1-019'],
  ['east','uncles','U014'],
  ['lin','c2-lin','P002'],
  ['yucun','c2-ningrong','C2-018'],
  ['wang','c4-lady','C04-001'],
  ['central','c4-hall','C04-094'],
  ['lixiang','c4-pear','C04-104'],
  ['yamen','c4-court','C04-007'],
];
for(const [name,section,target] of shots){
  await page.getByRole('combobox',{name:'选择剧情段落'}).selectOption(section);
  await reading();
  for(let i=0;i<160&&await node()!==target;i++)await next();
  await page.waitForTimeout(250);
  await page.locator('.game-map').screenshot({path:`artifacts/furn-${name}.png`});
  console.log('shot',name,await node());
}
console.log('errors',JSON.stringify(errors));
await browser.close();
