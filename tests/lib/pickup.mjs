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
