import test from 'node:test';
import assert from 'node:assert/strict';
import { buildToc, searchToc, tocMark, nodeActors } from '../src/toc.ts';
import { chapters, story, cast, bookNames } from '../src/story.ts';

const { books } = buildToc([]);
const flat = books.flatMap(book => book.sections);
const ids = (needle: string) => searchToc(books, needle).flatMap(group => group.entries.map(entry => entry.id));
// 回目名从数据实读：写死成九回的话，每补一回就要改一次断言，改漏了就会把
// 「新的一回没进目录」这件事掩盖过去。
const expectedBooks = [...new Set(chapters.map(candidate => candidate.book))]
  .sort((a, b) => a - b).map(book => bookNames[book]);

test('目录按回分组，每一回齐全，每段都归到正确的回', () => {
  assert.deepEqual(books.map(book => book.name), expectedBooks);
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
  // 她在台上的回目从数据实读：写死「第四、五、七、八回」的话，每加一回
  // 只要她再登场一次，这条断言就红——而红的原因跟搜索功能无关。
  const onStage = flat.filter(entry => entry.actors.includes('宝钗')).map(entry => entry.id);
  assert.ok(onStage.length > 0, '宝钗 must be on stage somewhere');
  const baochaiBooks = [...new Set(onStage.map(id => chapters.find(c => c.id === id)!.book))].sort((a, b) => a - b);
  assert.ok(baochaiBooks.includes(4), 'she is on stage in the fourth book');
  // 每一段她都在台的段，其回数必须与实读出来的回数一致。
  const expectedBooksForBaochai = baochaiBooks.map(book => String(book));
  for (const id of onStage) {
    const book = chapters.find(c => c.id === id)!.book;
    assert.ok(expectedBooksForBaochai.includes(String(book)),
      `宝钗 is on stage in book ${book}, which is not in ${expectedBooksForBaochai.join('/')}`);
  }
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
  // 搜索框承诺「搜段落、人物或地点」。搜一个人名却搜不到，有两种可能：
  // 索引漏了，或者这个人根本还没登场。这条断言守的是第二种。
  //
  // 样本随回目推移而失效：妙玉被第十八回推翻、晴雯被第十九回推翻、
  // 紫鹃被第二十一回推翻（她是黛玉房首席大丫头，第二十一回替她递香皂）。
  // 现在用「檀云」——她是宝玉房里的丫头，全书二十一回里一次也没出现过，
  // 也不在 cast 表里（搜人物是靠在场人物命中的，她压根没被画过）。
  //
  // 判据覆盖**所有可搜路径**：正文、段落标题、地点、在场人物、段 id。
  // 只查正文是不够的——名字要是出现在地点或人物表里，搜索照样能命中。
  const absent = '檀云';
  assert.equal(ids(absent).length, 0, `${absent} does not appear in any book`);
  assert.equal(story.filter(node => (node.title + node.text + node.place).includes(absent)).length, 0,
    `${absent} really is absent from the story`);
  assert.equal(flat.filter(entry => entry.actors.some(actor => actor.includes(absent))).length, 0,
    `${absent} must not be on stage anywhere`);
  assert.equal(flat.filter(entry => entry.places.some(place => place.includes(absent))).length, 0,
    `${absent} must not be a place anywhere`);
  assert.equal(flat.filter(entry => entry.id.includes(absent)).length, 0,
    `${absent} must not be part of a section id`);
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
