import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { chapterLeaf, chapterLeaves, chapterTitle, leafTrigger } from '../src/leaves.ts';
import { cast, chapters, story, bookNames } from '../src/story.ts';

// 每一回都是一本小书：前面有封面，后面有封底。这一组断言把封面的两样
// 东西钉住——原著回目联与本回出场人物——并且保证它们永远跟着剧情走，
// 不会因为改了某个节点而悄悄失真。

const titles = JSON.parse(readFileSync(new URL('../design/chapter-titles.json', import.meta.url), 'utf8'));
const variants = JSON.parse(readFileSync(new URL('../design/simplified-traditional.json', import.meta.url), 'utf8'));
const books = [...chapterLeaves().keys()].sort((a, b) => a - b);
// 剧情在全书里是连着的一条线，每一回占据其中连续的一段。
const order = new Map(story.map((node, index) => [node.id, index]));

// 底本里带回目联的那些回，封面上的回目联必须与原文一致。底本是节选、
// 根本没有回目联的（第三、十、十一、十二回），列在这里是为了让清单写全
// ——新补一回底本时，这条清单要么多一项，要么明确说明它没有回目联。
const sourcesWithCouplet = [1, 2, 4, 5, 6, 7, 8, 9, 13, 14, 15];
const sourcesWithoutCouplet = [3, 10, 11, 12];

const toTraditional = (text: string) =>
  [...text].map(char => (variants.map as Record<string, string>)[char] ?? char).join('');

test('每一回都有回目联，上下句都在', () => {
  assert.ok(books.length >= 15, `只有 ${books.length} 回有封面封底`);
  for (const book of books) {
    const title = chapterTitle(book);
    assert.ok(title, `第 ${book} 回没有回目联`);
    assert.ok(title.first.length >= 5, `第 ${book} 回上句太短：${title.first}`);
    assert.ok(title.second.length >= 5, `第 ${book} 回下句太短：${title.second}`);
    // 上句与下句是并排的一联，不能写成同一句。
    assert.notEqual(title.first, title.second, `第 ${book} 回上下句重复`);
  }
});

test('底本清单写全了：每一回要么有回目联，要么说明是节选', () => {
  const listed = [...sourcesWithCouplet, ...sourcesWithoutCouplet].sort((a, b) => a - b);
  assert.deepEqual(listed, Array.from({ length: 15 }, (_, i) => i + 1));
  assert.equal(new Set([...sourcesWithCouplet, ...sourcesWithoutCouplet]).size, 15, '有一回列了两次');
});

test('回目联与底本原文一致，不是自己编的', () => {
  // 底本繁简混用：有的回目是简体，有的底本通篇繁体，有的还是节选。
  // 所以两种形态都试一遍，两种都对不上才算抄错了。
  for (const book of sourcesWithCouplet) {
    const source = readFileSync(new URL(`../docs/chapter${String(book).padStart(2, '0')}-source.txt`, import.meta.url), 'utf8');
    const title = chapterTitle(book)!;
    for (const line of [title.first, title.second]) {
      const found = source.includes(line) || source.includes(toTraditional(line));
      assert.ok(found, `第 ${book} 回的回目联在底本里找不到：${line}`);
    }
  }
});

test('节选底本确实不含回目联，免得清单写错了还照样通过', () => {
  for (const book of sourcesWithoutCouplet) {
    const source = readFileSync(new URL(`../docs/chapter${String(book).padStart(2, '0')}-source.txt`, import.meta.url), 'utf8');
    const title = chapterTitle(book)!;
    for (const line of [title.first, title.second]) {
      const found = source.includes(line) || source.includes(toTraditional(line));
      assert.equal(found, false, `第 ${book} 回的底本其实有回目联，清单该把它算进带回目联的那一列`);
    }
  }
});

test('每一回的首尾节点确实属于这一回', () => {
  for (const book of books) {
    const leaf = chapterLeaf(book)!;
    const first = story.find(node => node.id === leaf.firstNode);
    const last = story.find(node => node.id === leaf.lastNode);
    assert.ok(first, `第 ${book} 回的首节点 ${leaf.firstNode} 不在剧情里`);
    assert.ok(last, `第 ${book} 回的末节点 ${leaf.lastNode} 不在剧情里`);
    for (const [label, node] of [['首', first], ['末', last]] as const) {
      const owner = chapters.find(section => section.id === node.chapter)?.book;
      assert.equal(owner, book, `第 ${book} 回的${label}节点落在第 ${owner} 回`);
    }
  }
});

test('每一回在剧情里占据连续的一段，且全书没有漏掉的节点', () => {
  let covered = 0;
  for (const book of books) {
    const leaf = chapterLeaf(book)!;
    const from = order.get(leaf.firstNode)!;
    const to = order.get(leaf.lastNode)!;
    const span = story.filter(node => (order.get(node.id) ?? -1) >= from && (order.get(node.id) ?? -1) <= to);
    assert.equal(span.length, leaf.nodes, `第 ${book} 回的节点数与剧情对不上`);
    assert.equal(span[0].id, leaf.firstNode);
    assert.equal(span[span.length - 1].id, leaf.lastNode);
    covered += span.length;
  }
  assert.equal(covered, story.length, '有几回没有把剧情全包住');
});

test('封面列出的人物都在名册里，且不重复', () => {
  const names = new Set(Object.values(cast).map(person => person.name));
  for (const book of books) {
    const leaf = chapterLeaf(book)!;
    assert.ok(leaf.actors.length > 0, `第 ${book} 回的封面没有人物`);
    for (const actor of leaf.actors) {
      assert.ok(names.has(actor), `第 ${book} 回的封面写了名册里没有的人：${actor}`);
    }
    // 人物不重复：封面上的两个同名立绘是同一张脸。
    assert.equal(new Set(leaf.actors).size, leaf.actors.length, `第 ${book} 回的封面人物重复`);
  }
});

test('相邻两回首尾相接：上一回读完就是下一回翻开', () => {
  for (let i = 1; i < books.length; i++) {
    const previous = chapterLeaf(books[i - 1])!;
    const current = chapterLeaf(books[i])!;
    const from = order.get(previous.lastNode)!;
    const to = order.get(current.firstNode)!;
    assert.equal(to, from + 1, `第 ${books[i - 1]} 回与第 ${books[i]} 回之间断了`);
  }
});

test('翻开封面与合上封底只在自然推进时发生', () => {
  for (const book of books) {
    const leaf = chapterLeaf(book)!;
    // 走到本回开头：自然推进时出封面，开书第一格时也出封面。
    assert.equal(leafTrigger({ nodeId: leaf.firstNode, leaf, advanced: true, atStart: false }), 'cover');
    assert.equal(leafTrigger({ nodeId: leaf.firstNode, leaf, advanced: false, atStart: true }), 'cover');
    // 跳读落到同一节点时不翻页——读者是去找一段戏，不是去翻书。
    assert.equal(leafTrigger({ nodeId: leaf.firstNode, leaf, advanced: false, atStart: false }), null);
    // 读完本回：自然推进时出封底，跳读时不弹封底把读者拽走。
    assert.equal(leafTrigger({ nodeId: leaf.lastNode, leaf, advanced: true, atStart: false }), 'back');
    assert.equal(leafTrigger({ nodeId: leaf.lastNode, leaf, advanced: false, atStart: false }), null);
    // 回中间的节点什么都不翻。
    const middle = story[order.get(leaf.firstNode)! + Math.floor(leaf.nodes / 2)];
    assert.equal(leafTrigger({ nodeId: middle.id, leaf, advanced: true, atStart: false }), null);
  }
});

test('没有封面数据时不翻页', () => {
  assert.equal(leafTrigger({ nodeId: 'C1-001', leaf: null, advanced: true, atStart: false }), null);
});

test('回目名与回次对得上', () => {
  for (const book of books) {
    assert.ok(bookNames[book], `第 ${book} 回没有回目名`);
    assert.ok(chapterTitle(book), `第 ${book} 回没有回目联`);
  }
  assert.equal(titles.books['1'].first, '甄士隐梦幻识通灵');
  assert.equal(titles.books['15'].second, '秦鲸卿得趣馒头庵');
});
