import cardData from '../design/collection-cards.json' with { type: 'json' };

export type CardKind = 'place' | 'line' | 'token' | 'bond';
/** 归属的三种方向：granted 赏给（恩主分派）/ sold 买卖（聘娶为妾）/ taken 掠夺（拐卖） */
export type BondMode = 'granted' | 'sold' | 'taken';
export interface CardDef {
  id: string;
  kind: CardKind;
  book: number;
  /** place 卡所属场景；line / token / bond 卡没有 */
  scene?: string;
  name: string;
  subtitle: string;
  quote?: string;
  attribution?: string;
  node?: string;
  /** 信物卡与归属卡的原文依据（繁体引文），用于卡面落款 */
  source?: string;
  /** 归属卡：谁的归属、到谁那里去、以什么方式 */
  bond?: { from: string; to: string; mode: BondMode; note: string };
  /** 归属卡：对应的 cast 人物 id，用于取立绘 */
  actor?: string;
  unlock: { type: 'read_scene'; scene: string } | { type: 'read'; node: string };
}

export const cards: CardDef[] = cardData.cards as CardDef[];

/**
 * 卡片解锁判定是引擎的旁挂：只读两样现成事实——
 * 引擎的 readLog（已读节点）与读者自己的寻访/收集记录。
 * 引擎不感知卡片，存档格式也不因此升级。
 */
export function unlockedCards(
  readLog: Iterable<string>,
  sceneByNode: ReadonlyMap<string, string>,
  stored: Iterable<string> = [],
): Set<string> {
  const read = new Set(readLog);
  const result = new Set(stored);
  for (const card of cards) {
    if (card.unlock.type === 'read') {
      if (read.has(card.unlock.node)) result.add(card.id);
    } else {
      // read_scene：读过该地图上的任何一段剧情即解锁
      for (const id of read) {
        if (sceneByNode.get(id) === card.unlock.scene) {
          result.add(card.id);
          break;
        }
      }
    }
  }
  return result;
}

/** 节点 → 场景 映射，从引擎 steps 建一次即可。 */
export function sceneIndex(steps: ReadonlyArray<{ id: string; scene: string }>): Map<string, string> {
  const index = new Map<string, string>();
  for (const step of steps) if (!index.has(step.id)) index.set(step.id, step.scene);
  return index;
}

const STORE_KEY = 'honglou.collection.v1';

export function loadStored(): string[] {
  try {
    const raw = globalThis.localStorage?.getItem(STORE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === 'string') : [];
  } catch {
    return [];
  }
}

export function saveStored(ids: Iterable<string>): void {
  try {
    globalThis.localStorage?.setItem(STORE_KEY, JSON.stringify([...ids].sort()));
  } catch {
    // 隐私浏览或存储限制：收集进度退化为仅本次会话，不打扰阅读
  }
}

/** 按回目分组（册页面板的展示顺序）。信物卡与归属卡单列一组，不进回目分组。 */
export function cardsByBook(): Map<number, CardDef[]> {
  const groups = new Map<number, CardDef[]>();
  for (const card of cards) {
    if (card.kind === 'token' || card.kind === 'bond') continue;
    const list = groups.get(card.book) ?? [];
    list.push(card);
    groups.set(card.book, list);
  }
  return groups;
}

/** 信物卡：原文写明「交到手上」的东西，单列一组。 */
export function tokenCards(): CardDef[] {
  return cards.filter(card => card.kind === 'token');
}

/** 归属卡：原文写明「这个人归了谁」，单列一组。 */
export function bondCards(): CardDef[] {
  return cards.filter(card => card.kind === 'bond');
}
