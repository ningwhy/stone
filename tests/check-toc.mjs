import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });

// Collect JS errors
const jsErrors = [];
page.on('pageerror', err => jsErrors.push(err.message));

await page.goto('https://stone.yan.pub/');
await page.waitForTimeout(5000);

console.log('JS errors:', jsErrors.length);
for (const e of jsErrors) console.log('  ', e);

// Check if toc-trigger exists
const tocTrigger = await page.locator('.toc-trigger').first();
const exists = await tocTrigger.count() > 0;
console.log('toc-trigger exists:', exists);

if (exists) {
  await tocTrigger.click();
  await page.waitForTimeout(1000);
  
  const books = await page.locator('.toc-book').all();
  console.log('Book buttons:', books.length);
  for (let i = 0; i < books.length; i++) {
    const text = await books[i].textContent();
    const isActive = await books[i].hasClass('active');
    console.log(`  Book ${i+1}: "${text.trim().substring(0,30)}" active=${isActive}`);
  }
  
  // Click chapter 15
  await page.locator('.toc-book').nth(14).click();
  await page.waitForTimeout(1000);
  
  const sections = await page.locator('.toc-card').all();
  console.log('Sections visible for ch15:', sections.length);
  for (const s of sections) {
    const title = await s.locator('strong').textContent();
    console.log('  Section:', title);
  }
  
  const emptyMsg = await page.locator('.toc-empty').all();
  console.log('Empty msg:', emptyMsg.length > 0);
  if (emptyMsg.length > 0) {
    console.log('  Text:', await emptyMsg[0].textContent());
  }
  
  await page.screenshot({ path: '/tmp/online-toc.png' });
} else {
  await page.screenshot({ path: '/tmp/online-error.png' });
}

await browser.close();
console.log('Done');
