import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });

// Load local dist
await page.goto('file:///Users/bot/WorkBuddy/tiledMap/dist/index.html');
await page.waitForTimeout(3000);

// Click the toc trigger
const tocTrigger = await page.locator('.toc-trigger').first();
await tocTrigger.click();
await page.waitForTimeout(1000);

await page.screenshot({ path: '/tmp/toc-debug-1.png', fullPage: false });

// Get toc books
const books = await page.locator('.toc-book').all();
console.log('Total book buttons:', books.length);
for (let i = 0; i < books.length; i++) {
  const text = await books[i].textContent();
  const isActive = await books[i].hasClass('active');
  console.log(`  Book ${i+1}: "${text.trim().substring(0,30)}" active=${isActive}`);
}

// Click chapter 15
const book15 = await page.locator('.toc-book').nth(14); // 0-indexed
await book15.click();
await page.waitForTimeout(1000);

await page.screenshot({ path: '/tmp/toc-debug-2.png', fullPage: false });

// Get toc sections visible
const sections = await page.locator('.toc-card').all();
console.log('Sections visible for chapter 15:', sections.length);
for (const s of sections) {
  const title = await s.locator('strong').textContent();
  console.log('  Section:', title);
}

// Check for empty message
const emptyMsg = await page.locator('.toc-empty').all();
console.log('Empty message visible:', emptyMsg.length > 0);
if (emptyMsg.length > 0) {
  const text = await emptyMsg[0].textContent();
  console.log('Empty message:', text);
}

// Check toc-sections container style
const tocSectionsContainer = await page.locator('.toc-sections').first();
const style = await tocSectionsContainer.evaluate(el => {
  const cs = window.getComputedStyle(el);
  return {
    display: cs.display,
    visibility: cs.visibility,
    opacity: cs.opacity,
    height: cs.height,
    width: cs.width
  };
});
console.log('toc-sections style:', JSON.stringify(style, null, 2));

// Check visible DOM for toc-sections
const visibleSections = await page.locator('.toc-sections').first().evaluate(el => {
  const cards = el.querySelectorAll('.toc-card');
  return {
    cardCount: cards.length,
    containerHeight: el.clientHeight,
    containerVisible: el.clientHeight > 0 && el.clientWidth > 0,
    childHtml: el.innerHTML.substring(0, 500)
  };
});
console.log('toc-sections DOM:', JSON.stringify(visibleSections, null, 2));

await browser.close();
console.log('Done');
