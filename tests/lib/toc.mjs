/** Jump to a section (段落) through the table of contents.
 *
 *  The header used to carry a native <select> with all 51 sections in it; the tests
 *  reached it with `getByRole('combobox',{name:'选择剧情段落'}).selectOption(id)`.
 *  The index is now a panel: open the 目录 button, pick the book, click the card.
 *  Every test that wants to jump somewhere goes through here, so the panel's
 *  navigation is exercised on every jump rather than in one place only. */
export async function seekSection(page, id) {
  const trigger = page.getByRole('button', { name: '打开目录' });
  await trigger.click();
  await page.locator('.toc-body').waitFor({ timeout: 20000 });

  // The card carries its book in the aria-label, so search by section id in the label
  // is not possible — the panel exposes the section title instead. Find the card by
  // the section id the panel keeps on the element.
  const card = page.locator(`.toc-card[data-section='${id}']`);
  if (await card.count()) {
    await card.first().click();
  } else {
    // Fall back to the search box: type the section id, which the panel matches
    // against the id as well as the title and the place.
    const search = page.getByRole('searchbox', { name: '搜索剧情段落' });
    await search.fill(id);
    await page.waitForTimeout(120);
    await page.locator(`.toc-card[data-section='${id}']`).first().click();
  }
  await page.locator('dialog[open]').waitFor({ state: 'detached', timeout: 20000 });
}

/** Open the table of contents and leave it open; returns the panel. */
export async function openToc(page) {
  await page.getByRole('button', { name: '打开目录' }).click();
  await page.locator('.toc-body').waitFor({ timeout: 20000 });
  return page.locator('.toc-body');
}
