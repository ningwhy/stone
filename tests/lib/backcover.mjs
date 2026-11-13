/** 封底的两种形态：全书终幕，或通往下一回。
 *
 *  封底长什么样，取决于**下一回有没有上线**——不是取决于「这一回是不是
 *  末回」。`src/App.tsx` 的 `nextBook` 是按 `bookNames` 往后找第一回有剧情的：
 *  第 20 回上线时它的封底是「全书至此，砖石犹温。」；第 21 回上线之后，
 *  第 20 回的封底就改成了「开启下一回 → 第二十一回」。
 *
 *  所以每一回的定向测试都不能把「全书至此」写死——那不是这一回的属性，
 *  是「后面还有没有回」的属性。写死的话，加一回就会把前面每一回的测试
 *  全部弄红，而红的原因跟被测的那一回毫无关系。
 *
 *  这里把两种形态都表达出来：断言的是「封底与下一回的有无相称」，
 *  而不是「封底长什么样」。判定用的 `chapterLeaves` 与产品代码
 *  （`src/App.tsx` 的 nextBook、`src/leaves.ts` 的 chapterLeaf）是同一份
 *  数据，不另立一份口径。 */
import assert from 'node:assert/strict';
import { chapterLeaves } from '../../src/leaves.ts';
import { story } from '../../src/story.ts';

/** 下一回是哪一回：与 `src/App.tsx` 的 nextBook 同一套判据。 */
export function nextBookOf(book) {
  const leaves = chapterLeaves();
  const last = Math.max(...[...leaves.keys()]);
  for (let b = book + 1; b <= last; b++) if (leaves.has(b)) return b;
  return null;
}

/** 某个节点是不是**全书**的末节点。
 *
 *  「终幕」这个标签只标在全书末节点上（`src/App.tsx` 的
 *  `state.index===story.length-1`），不是标在「某一回的末节点」上。
 *  所以第 18 回的末节点在第 21 回上线之后，标签是 `C18-135` 而不是
 *  「终幕」——那是产品行为，不是缺陷。写死「末回末节点一定显示终幕」
 *  的断言，每加一回就会把前面每一回都弄红。
 *
 *  判据与产品代码看的是同一份 `story` 数组，不另立口径。 */
export function isBookFinalNode(nodeId) {
  return story.length > 0 && story[story.length - 1].id === nodeId;
}

/** 断言节点标签：全书末节点显示「终幕」，其余显示节点 id。 */
export async function assertNodeLabel(page, nodeId) {
  const label = await page.locator('.node-label').textContent();
  if (isBookFinalNode(nodeId)) {
    assert.equal(label, '终幕', `the last node of the whole book is labelled 终幕, got ${label}`);
  } else {
    assert.equal(label, nodeId, `the node label must be the node id, got ${label}`);
  }
  return label;
}

/** 某一回自己的首末节点。
 *
 *  ★ 不要用 `story[story.length-1]` 取末节点——那是**全书**的末节点。
 *    第 18 回刚上线时它恰是全书末回，那时的写法是对的；第 21 回上线之后，
 *    全书末节点变成 C21-139，而第 18/19/20 回要验的是**自己那一回**的封底。
 *    断言对象一旦错位，那一回的封底根本不会出现在它该出现的地方
 *    （封底翻在全书末节点上），测试却「通过」了——什么都没验到。
 *
 *  这里按 `chapterLeaves()` 定位，与产品代码（`src/App.tsx` 的 leafData、
 *  `src/leaves.ts` 的 chapterLeaf）看同一份数据，不另立口径。 */
export function bookEnds(book) {
  const leaf = chapterLeaves().get(book);
  if (!leaf) throw new Error(`第 ${book} 回没有封底数据`);
  const first = story.findIndex(n => n.id === leaf.firstNode);
  const last = story.findIndex(n => n.id === leaf.lastNode);
  if (first < 0 || last <= first) throw new Error(`第 ${book} 回的节点区间不对：${first}..${last}`);
  return {
    firstNode: leaf.firstNode,
    lastNode: leaf.lastNode,
    beforeLast: story[last - 1].id,
  };
}

/** 断言封底与「下一回有没有上线」相称。
 *
 *  @param page  Playwright page（此刻封底应当已经翻出来）
 *  @param book  当前这一回的回次（1 起）
 */
export async function assertBackCover(page, book) {
  await page.waitForFunction(() => !!document.querySelector('.leaf-sheet.leaf-back'), undefined, { timeout: 10000 });
  const backText = await page.locator('.leaf-sheet.leaf-back').innerText();
  const flat = backText.replace(/\n+/g, ' | ');
  const next = nextBookOf(book);
  const openCount = await page.locator('.leaf-back .leaf-open').count();
  const foldCount = await page.locator('.leaf-back .leaf-fold').count();

  if (next != null) {
    assert.ok(backText.includes('开启下一回'),
      `the back cover of book ${book} must offer the next book, got: ${flat.slice(0, 100)}`);
    assert.equal(openCount, 1, `the back cover of book ${book} must carry exactly one 「开启下一回」 button`);
    // 下一回的回目名要写在封底上，读者才知道自己要去哪里。
    const { bookNames } = await import('../../src/story.ts');
    assert.ok(backText.includes(bookNames[next]),
      `the back cover must name the next book ${bookNames[next]}, got: ${flat.slice(0, 140)}`);
  } else {
    assert.ok(backText.includes('全书至此'),
      `the back cover of book ${book} must say the book ends here, got: ${flat.slice(0, 100)}`);
    assert.equal(openCount, 0, `the final back cover must not offer to open a next book`);
  }
  // 两种形态都还得能收起来——封底是盖在舞台上的纸页。
  assert.equal(foldCount, 1, `the back cover of book ${book} can still be folded away`);
  return { backText, next };
}

/** 断言「收起封底」既不偷偷前进，也不把读者堵死。
 *
 *  这条断言的判据改过一次，理由记在这里：
 *
 *  早先的版本断言「收起封底后『继续剧情』必须消失」，理由是「读者再点一下
 *  就会跨进下一回，并且跳过下一回的封面」。那条理由**经实测不成立**：下一回
 *  的封面是到达那一回首个节点时自己翻出来的（`src/leaves.ts` 的
 *  `leafTrigger`：`nodeId === leaf.firstNode` 时返回 'cover'），与封底收没收
 *  起无关。浏览器实测（收起封底 → 推进）确实翻出了下一回的封面。
 *
 *  那个版本反而制造了一个真缺陷：顶栏被锁成「回到封底」，读者收起封底之后
 *  就**再也推不动了**——点「回到封底」把纸页翻回来，再收起，又是「回到封底」。
 *  回末节点上除了封底自己的「开启下一回」，没有一条前进的路。
 *
 *  现在守的是两条真正的不变量：
 *  1. 收起封底不前进节点——读者还停在本回的最后一句；
 *  2. 收起封底之后读者仍能前进——推进按钮还在，按下去会走进下一回，
 *     且下一回的封面照常翻出来。
 *
 *  末回例外：那里没有下一回可进，「继续剧情」按下去只会重走已读完的戏，
 *  所以折叠后的按钮改成「回到封底」（`src/App.tsx` 的 `foldedBack&&ended`）。
 *
 *  这条断言不写死第几回：任何一回的末节点都该守同一条规矩。 */
export async function assertFoldedBackIsNotAPassThrough(page, book) {
  // 先确认封底确实在场上（调用方应当在末节点上）。
  await page.waitForFunction(() => !!document.querySelector('.leaf-sheet.leaf-back'), undefined, { timeout: 10000 });
  const fold = page.locator('.leaf-sheet.leaf-back .leaf-fold');
  assert.ok(await fold.count(), `the back cover of book ${book} must offer a way to fold it away`);
  await fold.click();
  // 末节点往往还带着一段演出（效果或走动）。演出没结束之前，顶栏是
  // 「跳过移动」——推进按钮根本不该出现，这是对的。所以这里要等演出收工，
  // 再检查收起封底之后顶栏给的是什么。
  await page.waitForFunction(() => {
    const e = window.__mapScene?.engine;
    const s = e?.getSnapshot?.();
    return !!s && s.status !== 'moving';
  }, undefined, { timeout: 15000 });
  await page.waitForTimeout(300);

  // 收起封底时，本回的末节点仍然是当前节点——没有偷偷往前走。
  const node = await page.locator('.node-label').textContent();
  const last = chapterLeaves().get(book)?.lastNode;
  assert.ok(last == null || node === last || node === '终幕',
    `folding the back cover must leave the reader on ${last}, got ${node}`);

  const forward = page.getByRole('button', { name: '继续剧情', exact: true });
  const back = page.getByRole('button', { name: '回到封底', exact: true });
  const next = nextBookOf(book);

  if (next == null) {
    // 末回：没有下一回可进，按钮要把封底重新翻出来，而不是给一条走不通的路。
    assert.ok(await back.isVisible().catch(() => false),
      `after folding the back cover of the last book the reader must be offered a way back to it ` +
      `(node=${node}, leaf=${await page.locator('.leaf-sheet').count()})`);
    await back.click();
    await page.waitForTimeout(300);
    assert.ok(await page.locator('.leaf-sheet.leaf-back').count(),
      `「回到封底」 must bring the back cover of book ${book} back`);
    return;
  }

  // 非末回：收起封底之后读者仍要能往前走，不能被堵死。
  assert.ok(await forward.isVisible().catch(() => false),
    `folding the back cover of book ${book} must leave the reader a way forward ` +
    `(node=${node}, leaf=${await page.locator('.leaf-sheet').count()})`);

  // 往前走一步：应当走进下一回的第一个节点，**并且下一回的封面照常翻出来**。
  //
  // `waitForFunction` 的回调在**浏览器**里跑，Node 侧的变量必须作为参数传进去
  // （直接闭包引用会报 `node is not defined`）。
  await forward.click();
  await page.waitForFunction(before => {
    const label = document.querySelector('.node-label')?.textContent ?? '';
    return !!label && label !== before;
  }, node, { timeout: 15000 });
  await page.waitForTimeout(600);
  const movedTo = await page.locator('.node-label').textContent();
  assert.ok(movedTo !== node,
    `the reader must actually advance after folding the back cover, still on ${node}`);
  assert.ok(await page.locator('.leaf-sheet.leaf-cover').count(),
    `the next book must open with its cover even when the previous back cover was folded away ` +
    `(book ${book} -> ${movedTo})`);
}
