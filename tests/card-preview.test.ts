import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ledgerCards, ledgerActorOf, flowLine, cardsForEntry } from '../src/cardPreview.ts';
import { ledgerEntries, unlockedLedger } from '../src/ledger.ts';
import { artAssets } from '../src/art.ts';

const all=new Set(ledgerEntries.map(e=>e.id));
const cards=ledgerCards(all);

test('别名归一：账上的写法能落到同一个 cast 角色上', () => {
  // 账上写简称、图上写全名
  assert.equal(ledgerActorOf('熙凤'),'feng');
  assert.equal(ledgerActorOf('王熙凤'),'feng');
  assert.equal(ledgerActorOf('宝玉'),'baoyu');
  assert.equal(ledgerActorOf('贾宝玉'),'baoyu');
  assert.equal(ledgerActorOf('黛玉'),'daiyu');
  assert.equal(ledgerActorOf('林黛玉'),'daiyu');
  // 账上带地名或职衔前缀
  assert.equal(ledgerActorOf('来升（宁国府总管）'),'lai_sheng');
  assert.equal(ledgerActorOf('水月庵净虚'),'jing_xu');
  assert.equal(ledgerActorOf('北静郡王'),'shui_rong');
  // 「甄家娘子」即士隐之妻封氏（第一回：「嫡妻封氏」）
  assert.equal(ledgerActorOf('甄家娘子'),'fengshi');
});

test('别名归一不靠模糊匹配：名字对不上就是真的对不上', () => {
  // 「冯家」是一族人家，不是冯家老仆（cast 里的 plaintiff）。
  assert.equal(ledgerActorOf('冯家'),undefined);
  // 「张（金哥之父）」是金哥的父亲，不是张如圭、也不是张友士。
  assert.equal(ledgerActorOf('张（金哥之父）'),undefined);
  assert.notEqual(ledgerActorOf('张（金哥之父）'),'zhang');
  assert.notEqual(ledgerActorOf('张（金哥之父）'),'zhang_youshi');
  // 机构不是人。
  assert.equal(ledgerActorOf('宁国府'),undefined);
});

test('每个账上的人与物都有一张卡，笔数对得上', () => {
  const people=cards.people;
  assert.ok(people.length>=50,`the ledger must have a card for everyone on it, got ${people.length}`);
  for(const card of people){
    assert.ok(card.total>0,`${card.title} must have transfers`);
    assert.equal(card.flows.length,card.total,`${card.title}: the card must list every transfer`);
    assert.equal(card.got,card.flows.filter(f=>f.unlocked).length,`${card.title}: the unlocked count must match the flows`);
    assert.equal(card.category,'person',`${card.title}: a person card is a person card`);
  }
  for(const card of cards.items){
    assert.ok(card.total>0,`${card.title} must have transfers`);
    assert.equal(card.flows.length,card.total);
    assert.ok(card.flows.every(f=>f.mode),`${card.title}: every flow must have a mode`);
  }
});

test('卡片上的大图都指向真实存在的资产', () => {
  for(const card of [...cards.people,...cards.items]){
    if(card.art==='portrait'){
      assert.ok(card.artKey,`${card.title}: a portrait card needs an asset key`);
      assert.ok(artAssets[card.artKey],`${card.title}: ${card.artKey} must exist in the manifest`);
    } else if(card.art==='goods'){
      assert.ok(card.artSrc,`${card.title}: a goods card needs a path`);
      assert.match(card.artSrc!,/^\/assets\/cards\/.+\.webp$/,`${card.title}: ${card.artSrc} must be a shipped card picture`);
    } else {
      assert.equal(card.art,'seal',`${card.title}: an unknown art kind`);
      assert.ok(card.seal,`${card.title}: a seal card needs a character to stamp`);
    }
  }
});

test('人被转手也算一件物：英莲这张卡挂的是她自己的立绘', () => {
  const yinglian=cards.items.find(c=>c.title==='英莲');
  assert.ok(yinglian,'英莲 must have a card');
  assert.equal(yinglian.total,3,'卖冯渊、偷卖薛家、被夺走，三笔同链');
  assert.equal(yinglian.art,'portrait');
  assert.equal(yinglian.artKey,'yinglian-portrait');
  assert.deepEqual(yinglian.flows.map(f=>f.mode),['sold','sold','taken']);
});

test('没画出像的人落一方花押，不硬凑一张画', () => {
  // 宁国府是机构、贾赦不曾登场、王子腾只在信里被提到——都没有像。
  for(const name of ['宁国府','贾赦','王子腾','冯家']){
    const card=cards.people.find(c=>c.title===name);
    assert.ok(card,`${name} must have a card`);
    assert.equal(card.art,'seal',`${name} has no portrait, so the card falls back to the seal`);
    assert.equal(card.seal,name[0]);
  }
});

test('落花押的名单是固定的：归一之后仍然没有像的，就这十二个', () => {
  // 钉死这份名单，是为了有人往 cast 里补人、或改别名表时立刻能看出来：
  // 谁该有像而没有、谁不该有像而硬凑了一张。文档写什么不算数，这里才算数。
  const sealed=cards.people.filter(c=>c.art==='seal').map(c=>c.title).sort();
  assert.deepEqual(sealed,[
    '东平郡王','南安郡王','冯家','冯渊','宁国府','张（金哥之父）',
    '王子腾','拐子','胡老爷家太太','贾敬','贾赦','西宁郡王',
  ].sort());
  // 这两个看着像「没登场的人」，其实有像——别再让它们落花押。
  for(const name of ['北静郡王','甄家娘子']){
    const card=cards.people.find(c=>c.title===name);
    assert.ok(card,`${name} must have a card`);
    assert.equal(card.art,'portrait',`${name} does have a portrait`);
  }
});

test('未入账的账不泄露：只留一个「？」', () => {
  const locked=ledgerCards(new Set());
  for(const card of [...locked.people,...locked.items]){
    assert.equal(card.got,0,`${card.title}: nothing is unlocked yet`);
    for(const flow of card.flows){
      assert.equal(flow.unlocked,false);
      assert.equal(flow.source,'',`${card.title}: a locked transfer must not quote the original`);
      assert.equal(flow.circumstance,'',`${card.title}: a locked transfer must not state the circumstance`);
    }
  }
});

test('没读到的回不当剧透：出场回目只算已入账的那些回', () => {
  // 贾雨村在账上有四回的账。只读到第一回时，卡片顶部不能说
  // 「出场于 第一回、第二回、第三回、第四回」——那三回读者还没读到。
  // 口径与账簿一致：`LedgerRow` 未入账时连回目印都不露。
  const early=ledgerCards(unlockedLedger(['C1-033']));
  const yuncun=early.people.find(c=>c.title==='贾雨村')!;
  assert.ok(yuncun.total>yuncun.got,'贾雨村 must have transfers the reader has not reached');
  assert.deepEqual(yuncun.books,[1],`only the books already on the books may be named, got ${JSON.stringify(yuncun.books)}`);
  // 一笔都没入账时，出场回数是空的——不该报一个「第一回」。
  const empty=ledgerCards(new Set());
  const yuncun0=empty.people.find(c=>c.title==='贾雨村')!;
  assert.deepEqual(yuncun0.books,[],'an unread person must not name any chapter');
});

test('入账之后原文与情形才露出来', () => {
  const got=unlockedLedger(['C1-033']);
  const card=cards.people.find(c=>c.title==='贾雨村');
  const flow=card!.flows.find(f=>f.id==='ledger.yucun-silver-50');
  assert.ok(flow,'the fifty taels must be on 贾雨村\'s card');
  assert.equal(flow.unlocked,true);
  assert.ok(flow.source.length>0,'an unlocked transfer must quote the original');
  assert.ok(flow.circumstance.length>0);
  assert.equal(flow.amount,50);
  assert.ok(got.has(flow.id));
});

test('流转一行说得清：谁 → 谁、什么方式、多少钱', () => {
  const card=cards.people.find(c=>c.title==='贾雨村');
  const flow=card!.flows.find(f=>f.id==='ledger.yucun-silver-50')!;
  const line=flowLine(flow);
  assert.match(line,/甄士隐 → 贾雨村/);
  assert.match(line,/赠与/);
  assert.match(line,/50 两/);
});

test('按一笔账能找回它两头的卡片', () => {
  // 一笔账有两头：给出的人和得到的人，各有一张卡。
  const cards=cardsForEntry('ledger.yucun-silver-50',all);
  assert.equal(cards.length,2,'the fifty taels link 甄士隐 and 贾雨村');
  // 不按汉字码位排序——那会把「甄」排在「贾」前面，只按名字集合比。
  assert.deepEqual(new Set(cards.map(c=>c.name)),new Set(['甄士隐','贾雨村']));
  assert.equal(cards.find(c=>c.side==='from')!.name,'甄士隐');
  assert.equal(cards.find(c=>c.side==='to')!.name,'贾雨村');
  // 被转手的人也有卡：英莲在账上是「物」，但她本人也有立绘。
  const yinglian=cardsForEntry('ledger.yinglian-taken',all);
  assert.ok(yinglian.length>=1);
  assert.ok(yinglian.some(c=>c.name==='英莲'||c.name==='薛蟠'));
});
