import {readFileSync} from 'node:fs';
// 账簿节点集：读到这些节点时必弹获得弹窗（设计数据里挂了 ledger 条目的节点）。
let LEDGER_NODES = null;
function ledgerNodes() {
  if (!LEDGER_NODES) {
    const data = JSON.parse(readFileSync(new URL('../../design/ledger.json', import.meta.url), 'utf8'));
    LEDGER_NODES = new Set(data.entries.map(e => e.node));
  }
  return LEDGER_NODES;
}
// 获得弹窗是模态的：会挡住「继续剧情/跳过移动」等一切点击。所有要推进剧情的
// 浏览器测试都通过这里把它收下。当前节点是账簿节点时主动等它出现（避免与
// React 渲染竞态）；否则只做零开销的可见性检查。
export async function dismissPickup(page, expect = false) {
  let expectLedger = expect;
  if (!expectLedger) {
    const label = await page.locator('.node-label').textContent().catch(() => null);
    expectLedger = label != null && ledgerNodes().has(label);
  }
  const button = page.locator('.pickup-confirm');
  if (expectLedger) await button.waitFor({state:'visible',timeout:8000}).catch(() => {});
  if (await button.isVisible().catch(() => false)) {
    await button.click();
    await button.waitFor({state:'detached',timeout:5000}).catch(() => {});
  }
}

/** The cover and the back cover of a chapter are modal sheets too.
 *
 *  They lie over the stage and swallow every click, so a test that walks the
 *  story has to put them away the way a reader does: press the button on the
 *  page.
 *
 *  `advance` decides what a back cover does. With it, the back cover's button
 *  is pressed and the story moves on into the next chapter. Without it, the
 *  sheet is only cleared from the way — a cover is closed, and a back cover
 *  that has no way forward is folded away.
 *
 *  `wait` makes it wait for the sheet to show up. The sheet is a React effect,
 *  so it lands a frame after the node label does; a test that has just moved
 *  to a node has to give it that frame, while a test that is only clearing
 *  the way should not wait at all. */
export async function dismissLeaf(page, advance = false, wait = false) {
  for (let i = 0; i < 4; i++) {
    const sheet = page.locator('.leaf-sheet');
    const shown = await sheet.count() > 0 || (wait && await sheet.waitFor({ state: 'visible', timeout: 600 }).then(() => true).catch(() => false));
    if (!shown) return;
    const isBack = await page.locator('.leaf-sheet.leaf-back').count() > 0;
    if (isBack) {
      // The back cover either carries the story into the next chapter, or it is
      // folded away so the reader can look back at the lines just read.
      if (advance) {
        const forward = page.locator('.leaf-back .leaf-open');
        if (await forward.count() && await forward.isVisible().catch(() => false)) {
          await forward.click();
          await page.waitForTimeout(200);
          continue;
        }
      }
      const fold = page.locator('.leaf-fold');
      if (await fold.count() && await fold.isVisible().catch(() => false)) {
        await fold.click();
        await page.waitForTimeout(200);
        continue;
      }
      return;
    }
    const button = page.locator('.leaf-cover .leaf-open');
    if (await button.count() && await button.isVisible().catch(() => false)) {
      await button.click();
      await page.waitForTimeout(200);
      continue;
    }
    return;
  }
}
