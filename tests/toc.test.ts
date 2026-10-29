import test from 'node:test';
import assert from 'node:assert/strict';
import { buildToc, searchToc, tocMark, nodeActors } from '../src/toc.ts';
import { chapters, story, cast } from '../src/story.ts';

const { books } = buildToc([]);
const flat = books.flatMap(book => book.sections);
const ids = (needle: string) => searchToc(books, needle).flatMap(group => group.entries.map(entry => entry.id));

test('目录按回分组，六回齐全，每段都归到正确的回', () => {
  assert.deepEqual(books.map(book => book.name), ['第一回','第二回','第三回','第四回','第五回','第六回']);
  assert.equal(flat.length, chapters.length, 'every section must appear in the index');
  assert.equal(new Set(flat.map(entry => entry.id)).size, chapters.length, 'no section may appear twice');
  for (const entry of flat) {
    const section = chapters.find(candidate => candidate.id === entry.id)!;
    assert.equal(entry.book, section.book, `${entry.id} sits in the wrong book`);
    assert.equal(entry.total, story.filter(node => node.chapter === entry.id).length, `${entry.id} counts the wrong nodes`);
  }
});

test('已读进度按节点算，未读 ○、读完 ●、读一半 ◐', () => {
  const all = buildToc(story.map(node => node.id)).books;
  const every = all.flatMap(book => book.sections);
  assert.ok(every.every(entry => entry.read === entry.total), 'everything read means every section is finished');
  assert.ok(every.every(entry => entry.mark === '●'), 'a finished section is marked ●');
  const none = flat;
  assert.ok(none.every(entry => entry.mark === '○'), 'nothing read means every section is ○');
  assert.equal(tocMark(0, 5), '○');
  assert.equal(tocMark(2, 5), '◐');
  assert.equal(tocMark(5, 5), '●');
});

test('搜索能命中人物：placeholder 承诺「搜人物」，人物就必须搜得到', () => {
  // 这些名字不出现在任何段落标题里，只能靠在场人物命中。
  for (const person of ['宝钗', '刘姥姥', '甄士隐', '薛蟠', '警幻', '门子', '板儿']) {
    const hits = ids(person);
    assert.ok(hits.length > 0, `searching 「${person}」 finds nothing`);
  }
  // 宝钗本人在第四回出场；第五回的对白提到她，所以命中不止第四回。
  // 要判的是「她在哪一回真的在台上」，不是「哪一回提到她」。
  const onStage = flat.filter(entry => entry.actors.includes('宝钗')).map(entry => entry.id);
  assert.ok(onStage.length > 0, '宝钗 must be on stage somewhere');
  assert.ok(onStage.every(id => id.startsWith('c4-') || id.startsWith('c5-')), '宝钗 belongs to the fourth and fifth books');
  assert.ok(onStage.some(id => id.startsWith('c4-')), 'she is on stage in the fourth book');
  // 刘姥姥只出现在第六回。
  const onStageLiu = flat.filter(entry => entry.actors.includes('刘姥姥')).map(entry => entry.id);
  assert.ok(onStageLiu.length > 0, '刘姥姥 must be on stage somewhere');
  assert.ok(onStageLiu.every(id => id.startsWith('c6-')), '刘姥姥 belongs to the sixth book');
});

test('搜索能命中全名，也能命中短名', () => {
  assert.ok(ids('林黛玉').length > 0, 'a full name must find its section');
  assert.ok(ids('贾雨村').length > 0, 'a full name must find its section');
  assert.ok(ids('雨村').length > 0, 'the short name must find it too');
});

test('搜索能命中段内的全部地点，不只是第一个', () => {
  // prologue 跨扬州雨村客寓、林府书斋、运河舟行、贾政书房。
  const entry = flat.find(candidate => candidate.id === 'prologue')!;
  assert.ok(entry.places.length >= 4, `prologue crosses several places, got ${entry.places.length}`);
  assert.ok(entry.places.some(place => place.includes('林府')), 'the second place must be searchable');
  assert.ok(ids('林府').length > 0, 'searching a later place must find the section');
  assert.ok(ids('运河').length > 0, 'searching a later place must find the section');
  // place 仍然是第一个地点，卡片上的主标签不变。
  assert.equal(entry.place, entry.places[0]);
});

test('搜索能命中只有对白里才有的词', () => {
  assert.ok(ids('好了歌').length > 0, 'a word spoken in the scene must be searchable');
  assert.ok(ids('荣禧堂').length > 0, 'a place from the scene must be searchable');
});

test('搜索找不到的必须是原著里根本没有的词，不能是索引漏了', () => {
  // 妙玉、紫鹃、沁芳桥在本书前六回里一次也没出现，搜不到是对的；
  // 搜索不能凭空造出原著没有的段落。
  for (const absent of ['妙玉', '紫鹃', '晴雯']) {
    assert.equal(ids(absent).length, 0, `${absent} does not appear in the first six books`);
    assert.equal(story.filter(node => (node.title + node.text + node.place).includes(absent)).length, 0,
      `${absent} really is absent from the story`);
  }
});

test('搜索命中的是段而不是人：被提到但不在场的人不算出场', () => {
  const entry = flat.find(candidate => candidate.id === 'c6-gift')!;
  assert.ok(entry.actors.includes('刘姥姥'), 'she is on stage');
  assert.ok(entry.actors.includes('凤姐'), 'she is on stage');
  // 甄士隐在第六回只被提到，不在场。
  assert.ok(!entry.actors.includes('甄士隐'), 'a person only talked about is not on stage');
});

test('在场人物取自动作与说话人，而不是作者全集', () => {
  const actors = nodeActors({ actions: [{ type: 'show', actor: 'daiyu' }], speaker: 'narrator' });
  assert.deepEqual(actors, ['daiyu']);
  const parallel = nodeActors({ actions: [{ type: 'parallel', moves: [{ actor: 'daiyu' }, { actor: 'baoyu' }] }], speaker: 'narrator' });
  assert.deepEqual(parallel, ['daiyu', 'baoyu']);
  const speaking = nodeActors({ actions: [], speaker: 'xiren' });
  assert.deepEqual(speaking, ['xiren']);
});

test('搜索跨回：搜到的结果按回分组，顺序仍是书序', () => {
  const hits = searchToc(books, '黛玉');
  assert.ok(hits.length >= 2, '黛玉 must be found in more than one book');
  const numbers = hits.map(group => group.book);
  assert.deepEqual(numbers, [...numbers].sort((a, b) => a - b), 'the books stay in reading order');
});

test('空查询返回空结果，不是全部', () => {
  assert.deepEqual(searchToc(books, ''), []);
  assert.deepEqual(searchToc(books, '   '), []);
});

test('搜索文本包含标题、地点、人物名与人物全名', () => {
  const entry = flat.find(candidate => candidate.id === 'c4-pear')!;
  assert.ok(entry.haystack.includes('梨香院'), 'the place is searchable');
  assert.ok(entry.haystack.includes('薛宝钗') || entry.haystack.includes('宝钗'), 'the person is searchable');
  assert.ok(entry.haystack.includes(entry.title), 'the title is searchable');
  assert.ok(entry.haystack.includes('c4-pear'), 'the id is searchable');
  assert.ok(entry.haystack.includes('第四回'), 'the book is searchable');
});

test('人物名取自 cast 表，读起来是读者认得的名字', () => {
  for (const entry of flat) {
    for (const name of entry.actors) {
      assert.ok(Object.values(cast).some(actor => actor.name === name), `${name} is not a cast name`);
    }
  }
});
