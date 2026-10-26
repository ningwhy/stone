import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ledgerEntries, unlockedLedger, ledgerFor, ledgerActors, ledgerItemTraces, loadStoredLedger, saveStoredLedger, LEDGER_STORE_KEY } from '../src/ledger.ts';
import { story } from '../src/story.ts';

const nodeIds = new Set(story.map(s => s.id));

test('账簿数据自洽：节点真实存在，转手双方齐全，方向合法', () => {
  assert.ok(ledgerEntries.length >= 20, '前四回写明的「给」至少二十笔');
  for (const entry of ledgerEntries) {
    assert.ok(nodeIds.has(entry.node), `${entry.id} points at an unknown node ${entry.node}`);
    assert.ok(entry.from && entry.to, `${entry.id} has an incomplete transfer`);
    assert.ok(['granted', 'sold', 'taken', 'paid'].includes(entry.mode), `${entry.id} has an unknown mode`);
    assert.ok(['money', 'clothing', 'item', 'person', 'favor'].includes(entry.category));
    assert.ok(entry.circumstance.length > 6, `${entry.id} must say under what circumstance`);
    assert.ok(entry.source, `${entry.id} must cite the original text`);
    if (entry.amount != null) assert.ok(entry.amount > 0 && Number.isFinite(entry.amount));
  }
});

test('四种转手方式都有样本：同一个「给」字，原文里意思并不相同', () => {
  const modes = new Set(ledgerEntries.map(e => e.mode));
  assert.deepEqual([...modes].sort(), ['granted', 'paid', 'sold', 'taken'].sort());
});

test('读到节点即入账，与卡片同一解锁规则', () => {
  const got = unlockedLedger(['C1-033']);
  assert.ok(got.has('ledger.yucun-silver-50'), '士隐赠银五十两在 C1-033 入账');
  assert.ok(got.has('ledger.yucun-winter-clothes'), '两套冬衣同笔入账');
  assert.ok(!got.has('ledger.jiaoxing-sale'), '未读第二回则无娇杏之卖');
  const later = unlockedLedger(['C2-004']);
  assert.ok(later.has('ledger.jiaoxing-sale'));
  assert.ok(later.has('ledger.fengsu-baijin'), '百金聘资同节点入账');
  assert.ok(later.has('ledger.fengsu-secret-letter'), '密书同节点入账');
});

test('历史存储与阅读记录取并集', () => {
  const got = unlockedLedger(['C1-033'], ['ledger.menzi-huguanfu']);
  assert.ok(got.has('ledger.yucun-silver-50'));
  assert.ok(got.has('ledger.menzi-huguanfu'), '历史账目保留');
  assert.equal(got.size, 3);
});

test('雨村的账：进五十两，出二两并百金，净花五十二两', () => {
  const book = ledgerFor('贾雨村');
  assert.ok(book.got.some(({ entry }) => entry.id === 'ledger.yucun-silver-50'));
  assert.ok(book.given.some(({ entry }) => entry.id === 'ledger.yucun-fengsu-2liang'));
  assert.ok(book.given.some(({ entry }) => entry.id === 'ledger.fengsu-baijin'));
  assert.equal(book.pricedIn, 50);
  assert.equal(book.pricedOut, 102);
  assert.equal(book.net, -52);
});

test('封肃是前两回最赚的人：二两加百金，还半哄半赚了女婿的置办钱', () => {
  const book = ledgerFor('封肃');
  assert.equal(book.net, 102);
  assert.ok(book.got.some(({ entry }) => entry.id === 'ledger.fengsu-land-money'), '士隐的折变银子进了封肃的手');
  assert.ok(book.given.some(({ entry }) => entry.id === 'ledger.jiaoxing-sale'), '娇杏是封肃给出的');
  const top = ledgerActors()[0];
  assert.equal(top.name, '封肃');
  assert.ok(top.net > 0);
});

test('多人转手按顿号拆分：书信二封给贾政与王子腾，两人都算收到', () => {
  assert.ok(ledgerFor('贾政').got.some(({ entry }) => entry.id === 'ledger.yucun-letters'));
  assert.ok(ledgerFor('王子腾').got.some(({ entry }) => entry.id === 'ledger.yucun-letters'));
});

test('只有原文明确写出两数的账计净额：两封、许多不折算', () => {
  const priced = ledgerEntries.filter(e => e.amount != null).map(e => e.amount as number);
  assert.deepEqual(priced.sort((a, b) => a - b), [2, 50, 100], '五十两、二两、百金——其余原文未写价');
});

test('localStorage 存取容错：坏数据不致命', () => {
  const sandbox = { store: {} as Record<string, string> };
  (globalThis as Record<string, unknown>).localStorage = {
    getItem: (k: string) => sandbox.store[k] ?? null,
    setItem: (k: string, v: string) => { sandbox.store[k] = v; },
  };
  saveStoredLedger(new Set(['ledger.yucun-silver-50']));
  assert.deepEqual(loadStoredLedger(), ['ledger.yucun-silver-50']);
  sandbox.store[LEDGER_STORE_KEY] = '{broken';
  assert.deepEqual(loadStoredLedger(), [], '坏 JSON 返回空集');
  sandbox.store[LEDGER_STORE_KEY] = JSON.stringify([3, 'ok', null]);
  assert.deepEqual(loadStoredLedger(), ['ok'], '非字符串项过滤');
  delete (globalThis as Record<string, unknown>).localStorage;
  assert.deepEqual(loadStoredLedger(), [], '无 localStorage 环境不抛错');
});

test('按物追踪：英莲三笔同链，链序即剧情序', () => {
  const traces = ledgerItemTraces();
  const yinglian = traces.find(t => t.key === '英莲');
  assert.ok(yinglian, '英莲必须有流转链');
  assert.equal(yinglian!.entries.length, 3, '卖冯渊、偷卖薛家、被薛蟠夺走三笔同链');
  assert.deepEqual(yinglian!.entries.map(e => e.mode), ['sold', 'sold', 'taken']);
  assert.ok(yinglian!.entries[0].node !== yinglian!.entries[2].node, '链上节点按剧情先后');
});

test('按物追踪：括注不拆链，单笔物品也有完整去向', () => {
  const traces = ledgerItemTraces();
  assert.ok(traces.length < ledgerEntries.length, '分组必须真的合并了同名条目');
  const silver = traces.find(t => t.key === '白银五十两');
  assert.ok(silver && silver.entries.length === 1, '五十两自成一条链');
  assert.equal(silver!.entries[0].from, '甄士隐');
  assert.equal(silver!.entries[0].to, '贾雨村');
});

test('货品图只挂在有信物图的账上，路径指向已存在的卡图', () => {
  const withArt = ledgerEntries.filter(e => e.art);
  assert.equal(withArt.length, 4, '护官符、密书、花帐、银两四件挂图');
  for (const e of withArt) assert.match(e.art!, /^\/assets\/cards\/.+\.webp$/);
  for (const e of withArt) assert.ok(e.source, '挂图的账必须同时有原文引文');
});
