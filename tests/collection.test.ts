import assert from 'node:assert/strict';
import { test } from 'node:test';
import { cards, loadStored, saveStored, sceneIndex, unlockedCards } from '../src/collection.ts';

const steps = [
  { id: 'C1-002', scene: 'myth' },
  { id: 'C1-045', scene: 'farm' },
  { id: 'C2-030', scene: 'tavern' },
  { id: 'C04-033', scene: 'c4_yamen' },
];
const index = sceneIndex(steps);

test('卡片数据自洽：解锁节点与场景真实存在', () => {
  assert.equal(cards.length, 28, '首期 22 地志卡 + 6 金句卡');
  const scenes = new Set(steps.map(s => s.scene));
  for (const card of cards) {
    if (card.unlock.type === 'read') assert.equal(typeof card.unlock.node, 'string');
    else scenes.add(card.unlock.scene);
  }
});

test('读到某场景任意节点即解锁该地志卡', () => {
  const got = unlockedCards(['C1-045'], index);
  assert.ok(got.has('place.farm'), 'farm 地志卡解锁');
  assert.ok(!got.has('place.myth'), '未读 myth 则不解锁');
  assert.ok(got.has('line.haoliao'), '好了歌金句卡随 C1-045 解锁');
  assert.ok(!got.has('line.stone'), '未读 C1-002 金句卡不解锁');
});

test('解锁是持久集合与 readLog 推导的并集', () => {
  const got = unlockedCards(['C1-002'], index, ['line.huguanfu']);
  assert.ok(got.has('place.myth'));
  assert.ok(got.has('line.stone'));
  assert.ok(got.has('line.huguanfu'), '历史收集保留');
  assert.equal(got.size, 3);
});

test('同一场景多节点只解锁一次，幂等', () => {
  const once = unlockedCards(['C1-045'], index);
  const twice = unlockedCards(['C1-045', 'C1-046'], index);
  assert.deepEqual([...once].sort(), [...once].sort());
  assert.ok(twice.has('place.farm'));
});

test('localStorage 存取容错：坏数据不致命', () => {
  const sandbox = { store: {} as Record<string, string> };
  const fake = {
    getItem: (k: string) => sandbox.store[k] ?? null,
    setItem: (k: string, v: string) => { sandbox.store[k] = v; },
  };
  (globalThis as Record<string, unknown>).localStorage = fake;
  saveStored(['place.farm', 'line.haoliao']);
  assert.deepEqual(loadStored().sort(), ['line.haoliao', 'place.farm']);
  sandbox.store['honglou.collection.v1'] = '{broken json';
  assert.deepEqual(loadStored(), [], '坏 JSON 返回空集');
  sandbox.store['honglou.collection.v1'] = JSON.stringify([1, 'ok', null]);
  assert.deepEqual(loadStored(), ['ok'], '非字符串项过滤');
  delete (globalThis as Record<string, unknown>).localStorage;
  assert.deepEqual(loadStored(), [], '无 localStorage 环境不抛错');
});
