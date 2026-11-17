import { ledgerEntries, ledgerActors, ledgerItemTraces, ledgerPortrait, ledgerEntryArt, modeNames, categoryNames } from './ledger.ts';
import type { LedgerEntry, LedgerCategory, LedgerMode, PersonLedger, ItemTrace } from './ledger.ts';
import { cast } from './story.ts';
import type { ActorId } from './story.ts';
import { artAssets } from './art.ts';

/** 背包卡片预览：把账上的人与物摊成一张可读的卡。
 *
 *  账簿原本只是索引——一列名字、一列小图，看得出有谁有物，却看不出这个人
 *  在书里是什么来历、那样东西又怎么转了几道手。卡片补的就是这一层：
 *  大图卡面、原文引文、情节说明、出场回目、流转时间线。
 *
 *  全部字段来自已有底本与账簿数据，不新造数值、不臆造身世。 */

/** 卡面上那张大图的来路。 */
export type CardArtKind =
  /** 人物卡：整幅立绘（不裁切），由卡面的竖版画框配 `object-fit:contain` 收下。 */
  | 'portrait'
  /** 器物卡：方形货品图。 */
  | 'goods'
  /** 账上只有名字、没画出像的：落一方朱印式花押。 */
  | 'seal';

/** 一张卡上的一笔流转。 */
export interface CardFlow {
  /** 账目 id，用于 key 与定位。 */
  id: string;
  /** 原文写明的品名。 */
  what: string;
  category: LedgerCategory;
  mode: LedgerMode;
  /** 转手双方：from → to。 */
  from: string;
  to: string;
  /** 原文明确写出的价钱；未写价则为 null。 */
  amount: number | null;
  /** 出场回目。 */
  book: number;
  /** 这一笔发生在哪个剧情节点。 */
  node: string;
  /** 情节说明。 */
  circumstance: string;
  /** 原文引文。 */
  source: string;
  /** 是否已入账（读到那一回才入账）。未入账时不显示详情。 */
  unlocked: boolean;
}

/** 卡片主体。 */
export interface CardPreview {
  /** 卡片主标题：人名或品名。 */
  title: string;
  /** 副标题：人物的身份/关系，或物品的类别与笔数。 */
  subtitle: string;
  /** 种类徽章：人物为「人」，物品按账上类别。 */
  badge: string;
  /** 账上类别：人物恒为 person，物品按账上类别（决定卡面配色）。 */
  category: LedgerCategory;
  /** 大图来源。 */
  art: CardArtKind;
  /** 立绘资产名（art==='portrait' 时有值）。 */
  artKey?: string;
  /** 货品图的绝对路径（art==='goods' 时有值）。 */
  artSrc?: string;
  /** 立绘对应的 cast 角色（有则点开可看图鉴资料）。 */
  actor?: ActorId;
  /** 花押用的首字（art==='seal' 时有值）。 */
  seal?: string;
  /** 出场回目（人物卡：他在账上出现过的回数）。 */
  books: number[];
  /** 这一笔/这些笔的流转时间线，按剧情先后。 */
  flows: CardFlow[];
  /** 已入账的笔数 / 总笔数。 */
  got: number;
  total: number;
}

/** 账上人名 → cast 角色的显式别名表。
 *
 *  这里只收**逐条核对过底本**的写法，不做自动模糊匹配：账上「冯家」是
 *  一族人家，模糊匹配会撞上冯家老仆；「张（金哥之父）」是金哥的父亲，
 *  模糊匹配会撞上张如圭或张友士——那三个人与账上这两个人毫无关系。
 *  名字对不上就是真的对不上，宁可留白，不可张冠李戴。 */
const PERSON_ALIAS: Record<string, ActorId> = {
  // 账上写简称、图上写全名
  '熙凤': 'feng',
  '王熙凤': 'feng',
  '林黛玉': 'daiyu',
  '黛玉': 'daiyu',
  '宝玉': 'baoyu',
  '贾宝玉': 'baoyu',
  '林如海': 'ruhai',
  '贾雨村': 'yucun',
  '秦可卿': 'qin_ke',
  '薛宝钗': 'baochai',
  '警幻仙姑': 'jinghuan',
  // 账上带地名或职衔前缀
  '来升（宁国府总管）': 'lai_sheng',
  '水月庵净虚': 'jing_xu',
  '北静郡王': 'shui_rong',
  // 「甄家娘子」即士隐之妻封氏（第一回：「嫡妻封氏」）
  '甄家娘子': 'fengshi',
};

/** 账上人名 → cast 角色。先查显式别名表，再按 cast 的 name / fullName 精确匹配。 */
export function ledgerActorOf(name: string): ActorId | undefined {
  if (PERSON_ALIAS[name]) return PERSON_ALIAS[name];
  for (const id of Object.keys(cast) as ActorId[]) {
    const entry = cast[id];
    if (entry.name === name || entry.fullName === name) return id;
  }
  return undefined;
}

/** 一个人的大图：cast 立绘优先，其次账簿专属立绘，都没有就落花押。
 *
 *  ★ 别再加「账簿专属立绘」表：账上那 8 个没进过场的人（贾雨村、甄士隐、
 *  封肃、林如海、贾政、贾母、门子、薛蟠）如今都在 cast 表里，且名字能精确
 *  命中，所以上面第一路就会取到他们的立绘。曾经有一张重复的表挂在 cast
 *  之后，实测 0 次触发——已删。`ledgerPortrait()` 是账簿自己的表，是这里的
 *  第二路兜底。 */
function personArt(name: string): {kind: CardArtKind; artKey?: string; actor?: ActorId} {
  const actor = ledgerActorOf(name);
  if (actor && artAssets[`${actor}-portrait`]) return {kind: 'portrait', artKey: `${actor}-portrait`, actor};
  const only = ledgerPortrait(name);
  if (only && artAssets[only]) return {kind: 'portrait', artKey: only};
  return {kind: 'seal'};
}

/** 物品的大图：取这条流转链上已入账那一笔的货品图；未入账时不提前泄露。 */
function itemArt(trace: ItemTrace, unlocked: Set<string>): {kind: CardArtKind; artSrc?: string; artKey?: string; actor?: ActorId} {
  const hit = trace.entries.find(e => unlocked.has(e.id) && ledgerEntryArt(e));
  if (!hit) return {kind: 'seal'};
  const art = ledgerEntryArt(hit)!;
  if (hit.art) return {kind: 'goods', artSrc: hit.art};
  // 人物类的账目挂的是那个被转手的人自己的立绘（账簿专属资产，未必在 cast 表里）。
  if (hit.category === 'person') return {kind: 'portrait', artKey: art};
  // 其余情况拿到的是货品图的资产名（不是路径），按方形器物图处理。
  const owner = ledgerActorOf(hit.to);
  if (owner && artAssets[`${owner}-portrait`]) return {kind: 'portrait', artKey: `${owner}-portrait`, actor: owner};
  return {kind: 'goods', artSrc: art};
}

/** 一笔账翻成卡片上的一行。
 *
 *  ★ 未入账的一笔**不带原文与情形**：账上写明了什么，得等读者读到那一回
 *  才算数。未入账时这两栏留空，界面上只留一个「？」——不提前泄露。 */
function toFlow(entry: LedgerEntry, unlocked: Set<string>): CardFlow {
  const got=unlocked.has(entry.id);
  return {
    id: entry.id,
    what: got?entry.what:'',
    category: entry.category,
    mode: entry.mode,
    from: got?entry.from:'',
    to: got?entry.to:'',
    amount: got?entry.amount:null,
    book: entry.book,
    node: entry.node,
    circumstance: got?entry.circumstance:'',
    source: got?(entry.source??''):'',
    unlocked: got,
  };
}

/** 一个人的副题：只补卡名没说的那部分。
 *
 *  账上写「宝玉」，图上是「贾宝玉」——副题补上全名与关系；
 *  账上已经写「贾雨村」，再补一遍「贾雨村」就是重复，读着别扭。
 *  副题存在的意义是补信息，不是重复卡名。 */
function personSubtitle(name: string, actor?: ActorId): string {
  if (!actor) return '账上有名，书中未曾登场';
  const entry = cast[actor];
  const parts: string[] = [];
  if (entry.fullName && entry.fullName !== name) parts.push(entry.fullName);
  if (entry.relation) parts.push(entry.relation);
  return parts.length ? parts.join(' · ') : '账上有名，书中未曾登场';
}

/** 一个人的卡片：从账上这个人的全部往来里整理出来。 */
export function personCard(person: PersonLedger, unlocked: Set<string>): CardPreview {
  const art = personArt(person.name);
  const entries = [...person.got.map(s => s.entry), ...person.given.map(s => s.entry)]
    .sort((a, b) => a.book - b.book || a.node.localeCompare(b.node));
  const flows = entries.map(e => toFlow(e, unlocked));
  const actor = art.actor;
  return {
    title: person.name,
    subtitle: personSubtitle(person.name, actor),
    badge: '人',
    category: 'person',
    art: art.kind,
    artKey: art.artKey,
    actor,
    seal: person.name[0],
    books: unlockedBooks(flows),
    flows,
    got: flows.filter(f => f.unlocked).length,
    total: flows.length,
  };
}

/** 出场回目：**只算已入账的那些回**。
 *
 *  ★ 账簿里未入账的一笔连回目印都不露（见 `LedgerRow`），卡片顶部的
 *  「出场于 第N回」是同一口径——读者还没读到第三回，卡片就不该告诉他
 *  「他在第三回有账」。早先这里统计全部 entries，等于提前剧透。 */
function unlockedBooks(flows: CardFlow[]): number[] {
  return [...new Set(flows.filter(f => f.unlocked).map(f => f.book))].sort((a, b) => a - b);
}

/** 物品的副题：这东西在谁手里转过。
 *
 *  不重复卡名与徽章（类别已经写在徽章上了），只说流转链的首尾：
 *  「甄士隐 → 贾雨村」。未入账的那一笔不露名字——账还没上册，
 *  说得出从谁到谁就是剧透。 */
function itemSubtitle(trace: ItemTrace, flows: CardFlow[]): string {
  const got = flows.filter(f => f.unlocked);
  if (got.length === 0) return '尚未入账';
  const first = got[0].from;
  const last = got[got.length - 1].to;
  if (!first || !last) return categoryNames[trace.category];
  return first === last ? `一直在 ${first} 手里` : `${first} → ${last}`;
}

/** 一件东西的卡片：从它的流转链里整理出来。 */
export function itemCard(trace: ItemTrace, unlocked: Set<string>): CardPreview {
  const art = itemArt(trace, unlocked);
  // 按剧情先后排，别依赖账簿里的隐含顺序——副题要说「从谁到谁」，
  // 首尾排错了就说反了。
  const ordered = [...trace.entries].sort((a, b) => a.book - b.book || a.node.localeCompare(b.node));
  const flows = ordered.map(e => toFlow(e, unlocked));
  const got = flows.filter(f => f.unlocked).length;
  return {
    title: trace.label,
    subtitle: itemSubtitle(trace, flows),
    badge: categoryNames[trace.category],
    category: trace.category,
    art: art.kind,
    artKey: art.artKey,
    artSrc: art.artSrc,
    actor: art.actor,
    seal: trace.label[0],
    books: unlockedBooks(flows),
    flows,
    got,
    total: trace.entries.length,
  };
}

/** 背包里的全部卡片：账上的人 + 账上的物。 */
export function ledgerCards(unlocked: Set<string>): {people: CardPreview[]; items: CardPreview[]} {
  return {
    people: ledgerActors().map(p => personCard(p, unlocked)),
    items: ledgerItemTraces().map(t => itemCard(t, unlocked)),
  };
}

/** 卡片上的流转文字：「谁 → 谁 · 什么方式 · 多少钱」。 */
export function flowLine(flow: CardFlow): string {
  const price = flow.amount != null ? ` · ${flow.amount} 两` : '';
  return `${flow.from} → ${flow.to} · ${modeNames[flow.mode]}${price}`;
}

/** 一张卡上出现过的人名（用于「此人还与谁有过往来」这类交叉引用）。 */
export function cardNames(card: CardPreview): string[] {
  const names = new Set<string>();
  for (const flow of card.flows) {
    names.add(flow.from);
    for (const n of flow.to.split('、')) names.add(n);
  }
  return [...names];
}

/** 账簿里某一笔对应的卡片（用于从流水直接跳到卡片）。
 *
 *  一笔账有两头（谁给谁），所以它对应的不止一张卡：
 *  给出的人和得到的人都各有一张。这一笔若涉及多人（顿号分隔），每人一卡。 */
export interface EntryCard {
  /** 'from' 是给出的一方，'to' 是得到的一方。 */
  side: 'from'|'to';
  /** 这一头的名字。 */
  name: string;
  card: CardPreview;
}
export function cardsForEntry(entryId: string, unlocked: Set<string>): EntryCard[] {
  const entry = ledgerEntries.find(e => e.id === entryId);
  if (!entry) return [];
  const out: EntryCard[] = [];
  for(const name of entry.from.split('、')){
    const person=ledgerActors().find(p=>p.name===name);
    if(person) out.push({side:'from',name,card:personCard(person,unlocked)});
  }
  for(const name of entry.to.split('、')){
    const person=ledgerActors().find(p=>p.name===name);
    if(person) out.push({side:'to',name,card:personCard(person,unlocked)});
  }
  if(out.length===0){
    const trace=ledgerItemTraces().find(t=>t.entries.some(e=>e.id===entryId));
    if(trace) out.push({side:'from',name:trace.label,card:itemCard(trace,unlocked)});
  }
  return out;
}
