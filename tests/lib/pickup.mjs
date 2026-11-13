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

/** 点一下顶栏的「跳过移动」——**如果它此刻真的是那个按钮**。
 *
 *  ★ 这里有一个必须绕开的坑。
 *
 *  顶栏那一个按钮在「跳过移动」和「继续剧情」之间来回换身份，而它**占的是
 *  同一个位置**。原来各测试的写法是：
 *
 *      const skip=page.getByRole('button',{name:'跳过移动',exact:true});
 *      if(await skip.isVisible())await skip.click({timeout:1500}).catch(()=>{});
 *
 *  `isVisible()` 判到「跳过移动」，可等 `click()` 真正落手时，React 早已把
 *  那个按钮换成了「继续剧情」。Playwright 的 `click()` 会**重新解析** locator，
 *  于是那一下点中的是「继续剧情」——剧情于是多走一步。
 *
 *  后果不是「多读一句」这么轻：一步多走会让读者跨过本回的末节点，
 *  末节点的封底还没翻出来就被跨过去，下一回的封面也来不及翻。第 20 回的
 *  「段内连贯」断言就是这么挂的——它一路多走，走到第 21 回的 `yihong`
 *  场景上，断言「不该走到这张图」就红了。追出来的现场（探针七）：
 *
 *      19.212 MARK step1:skipVisible#0     ← 判的是「跳过移动」
 *      19.255 ★    click "继续剧情"          ← 点的其实是「继续剧情」
 *      19.257 ★    advance 1324->1325
 *
 *  所以这里不按「角色+名字」找按钮，而是**按按钮当下真实的文案**取元素，
 *  再用 `dispatchEvent` 直接派发 click：元素一旦取到就是那个元素，
 *  React 中途把它换掉也换不掉这一下已经派发出去的 click。
 *
 *  @param page     Playwright page
 *  @param limit    最多尝试几次（演出里会连续出现「跳过移动」）
 *  @param settle   每次点完等多久（毫秒）
 *  @returns 点了几次
 */
export async function clickSkipIfShown(page, limit = 3, settle = 120) {
  let clicked = 0;
  for (let i = 0; i < limit; i++) {
    // 按**当下真实的文案**取元素：按钮换了身份，这里就取不到，不会误点。
    const handle = await page.evaluateHandle(() => {
      const btn = [...document.querySelectorAll('nav button')]
        .find(b => b.textContent?.trim() === '跳过移动');
      return btn ?? null;
    });
    const element = handle.asElement();
    if (!element) {
      await handle.dispose();
      break;
    }
    // 按钮此刻确实是「跳过移动」，点它。
    await element.dispatchEvent('click');
    await handle.dispose();
    clicked++;
    await page.waitForTimeout(settle);
  }
  return clicked;
}

/** 点一下顶栏的「继续剧情」——**如果它此刻真的是那个按钮**。
 *
 *  与 `clickSkipIfShown` 同一个坑：那个按钮的位置上坐的可能是「跳过移动」，
 *  用 `getByRole(...).click()` 会因为重新解析 locator 而点到另一个身份上，
 *  剧情就多走一步。这里按**当下真实的文案**取元素再派发 click。
 *
 *  @returns 点到了就返回 true，没点到返回 false
 */
export async function clickForwardIfShown(page) {
  const handle = await page.evaluateHandle(() => {
    const btn = [...document.querySelectorAll('nav button')]
      .find(b => b.textContent?.trim() === '继续剧情');
    return btn ?? null;
  });
  const element = handle.asElement();
  if (!element) {
    await handle.dispose();
    return false;
  }
  await element.dispatchEvent('click');
  await handle.dispose();
  return true;
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
