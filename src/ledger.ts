import ledgerData from '../design/ledger.json' with { type:'json' };

/** 流转账簿：前四回里每一样「给」出去的东西——银两、衣物、物件、人、人情——
 *  在谁与谁之间、以何种方式、什么情形下转手，价钱几何。与册页卡片同源同解锁：
 *  读到对应剧情节点，这一笔才入账。 */
export type LedgerMode = 'granted' | 'sold' | 'taken' | 'paid';
export type LedgerCategory = 'money' | 'clothing' | 'item' | 'person' | 'favor';
export interface LedgerEntry {
  id: string;
  book: number;
  node: string;
  what: string;
  category: LedgerCategory;
  from: string;
  to: string;
  mode: LedgerMode;
  /** 明确写出的银两数；原文只说「许多」「两封」的记 null，不计入净额。 */
  amount: number | null;
  circumstance: string;
  source?: string;
  /** 货品图（与信物卡共用美术）；大多数账没有，展示时退回字面。 */
  art?: string;
}

export const ledgerEntries: LedgerEntry[] = (ledgerData as {entries: LedgerEntry[]}).entries;
export const LEDGER_STORE_KEY = 'honglou.ledger.v1';
export const modeNames: Record<LedgerMode, string> = {granted:'赠与', sold:'买卖', taken:'强夺', paid:'赔付'};
export const categoryNames: Record<LedgerCategory, string> = {money:'银两', clothing:'衣物', item:'物件', person:'人', favor:'人情'};

/** 读到即入账：推导（阅读记录）∪ 历史存储（localStorage），与卡片解锁同一规则。 */
export function unlockedLedger(readLog: string[], stored: string[] = []): Set<string> {
  const read = new Set(readLog);
  const ids = new Set<string>();
  for (const entry of ledgerEntries) if (read.has(entry.node) || stored.includes(entry.id)) ids.add(entry.id);
  return ids;
}

export function loadStoredLedger(): string[] {
  try {
    if (typeof localStorage === 'undefined') return [];
    const raw = localStorage.getItem(LEDGER_STORE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string') : [];
  } catch { return []; }
}

export function saveStoredLedger(ids: Set<string>): void {
  try {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem(LEDGER_STORE_KEY, JSON.stringify([...ids]));
  } catch { /* 私密模式等场景下静默放弃 */ }
}

/** 一个人的账本：他得到的与给出的，按剧情顺序。 */
export interface LedgerSide { entry: LedgerEntry; counterparty: string }
export interface PersonLedger {
  name: string;
  got: LedgerSide[];
  given: LedgerSide[];
  /** 有明确银两数的净流：正为进，负为出。原文未写价的（「许多」「两封」）不计入。 */
  net: number;
  pricedIn: number;
  pricedOut: number;
}
export function ledgerFor(name: string): PersonLedger {
  const got: LedgerSide[] = [], given: LedgerSide[] = [];
  let net = 0, pricedIn = 0, pricedOut = 0;
  for (const entry of ledgerEntries) {
    if (entry.to.split('、').includes(name)) {
      got.push({entry, counterparty: entry.from});
      if (entry.amount != null) { net += entry.amount; pricedIn += entry.amount; }
    }
    if (entry.from === name || entry.from.split('、').includes(name)) {
      given.push({entry, counterparty: entry.to});
      if (entry.amount != null) { net -= entry.amount; pricedOut += entry.amount; }
    }
  }
  return {name, got, given, net, pricedIn, pricedOut};
}

/** 有账目的人物，按净额从大到小。 */
export function ledgerActors(): PersonLedger[] {
  const names = new Set<string>();
  for (const e of ledgerEntries) {
    for (const n of e.to.split('、')) names.add(n);
    for (const n of e.from.split('、')) names.add(n);
  }
  return [...names].map(ledgerFor).sort((a, b) => b.net - a.net || (b.got.length + b.given.length) - (a.got.length + a.given.length));
}

/** 一件东西（或一个人）的转手链：它在各回、各角色之间的完整流转史。 */
export interface ItemTrace {
  /** 分组键：品名去掉括注后的本体（「英莲（偷卖薛家）」与「英莲」同链）。 */
  key: string;
  label: string;
  category: LedgerCategory;
  entries: LedgerEntry[];
}
export function ledgerItemTraces(): ItemTrace[] {
  const order: string[] = [];
  const byKey = new Map<string, ItemTrace>();
  for (const entry of ledgerEntries) {
    const key = entry.what.split('（')[0];
    let trace = byKey.get(key);
    if (!trace) { trace = {key, label: key, category: entry.category, entries: []}; byKey.set(key, trace); order.push(key); }
    trace.entries.push(entry);
  }
  return order.map(key => byKey.get(key)!);
}

/** 账上人物的手绘立绘：账簿里的人也要有脸。
 *  键是 art 资产名（`<actor>-portrait`）；只有画过立绘的人才有，
 *  甄家娘子、拐子、冯渊、冯家、王子腾等未出场者留空。 */
const LEDGER_PORTRAITS: Record<string, string> = {
  '贾雨村': 'yucun-portrait', '甄士隐': 'shiyin-portrait', '封肃': 'fengsu-portrait',
  '林如海': 'ruhai-portrait', '贾政': 'zheng-portrait', '黛玉': 'daiyu-portrait',
  '熙凤': 'feng-portrait', '贾母': 'grandmother-portrait', '宝玉': 'baoyu-portrait',
  '门子': 'menzi-portrait', '薛蟠': 'xuepan-portrait',
};

/** 一个人在账上有没有立绘；没有就返回 undefined，界面上只留空位。 */
export function ledgerPortrait(name: string): string | undefined {
  return LEDGER_PORTRAITS[name];
}

/** 人物类的账目挂谁的脸。
 *  账上的人也是被转手的一方：英莲被卖、娇杏被送、鹦哥与袭人被给了出去，
 *  所以这类账目的货品图就是那个人本身的立绘——账簿里人也得有脸。 */
const LEDGER_PERSON_ART: Record<string, string> = {
  'ledger.jiaoxing-sale': 'jiaoxing-portrait',
  'ledger.grandmother-yingge': 'yingge-portrait',
  'ledger.grandmother-xiren': 'xiren-portrait',
  'ledger.yinglian-first-sale': 'yinglian-portrait',
  'ledger.yinglian-second-sale': 'yinglian-portrait',
  'ledger.yinglian-taken': 'yinglian-portrait',
};

/** 一笔账的货品图：器物走 entry.art，人物走被转手那个人的立绘。 */
export function ledgerEntryArt(entry: LedgerEntry): string | undefined {
  return entry.art ?? (entry.category === 'person'
    ? LEDGER_PERSON_ART[entry.id]
    : undefined);
}
