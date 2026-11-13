/** 场景转场的方位数据。
 *
 *  `design/scene-places.json` 是唯一权威源；`design/atlas-maps.json` 是读者主动
 *  打开的交互式总览舆图，两者刻意分开——总览舆图只画了 28 个考据过的建筑，
 *  而剧情里 45 个 scene 有 18 个（怡红院、贾琏院、袭人家…）根本不在那张图上。
 *  把定位动画硬接到总览舆图上，那些场景就会「查无此地」。
 *
 *  这份表是**叙事方位示意**，不是考据地图：早期回目借图严重（`night` 既当
 *  碧纱橱又当黛玉房），一律按 Tiled 地图标题与主要 place 归类。
 */
import data from '../design/scene-places.json' with { type: 'json' };

export type ScenePlace = {
  level: string;
  region: string;
  col: number;
  row: number;
  name: string;
  note?: string;
};

export type Point = { x: number; y: number };

const table = data.scenes as Record<string, ScenePlace>;
const levels = data.levels as Record<string, { name: string; origin: number[]; scale: number }>;
const regions = data.regions as Record<string, { name: string; col: number; row: number; tone: string }>;
const crumbs = data.crumbs as Record<string, string[]>;

export const scenePlaces = table;
export const sceneRegions = regions;
export const sceneLevels = levels;
export const levelNames = Object.fromEntries(Object.entries(levels).map(([id, l]) => [id, l.name]));

/** 某一回的「天下」图投影。等距格：x = ox + (col-row)*s，y = oy + (col+row)*s/2。 */
export function isoOf(level: string) {
  const def = levels[level] ?? levels.realm;
  const [ox, oy] = def.origin, s = def.scale;
  return (col: number, row: number): Point => ({ x: ox + (col - row) * s, y: oy + (col + row) * s / 2 });
}

export function placeOf(scene: string): ScenePlace | null {
  return table[scene] ?? null;
}

/** 场景在「天下」图上的区域落点。第一拍的光点飞到这里。 */
export function regionPoint(scene: string): Point {
  const place = table[scene];
  const region = regions[place?.region ?? 'capital'] ?? regions.capital;
  return isoOf('realm')(region.col, region.row);
}

/** 场景在它自己那一层的等距格落点。第二拍下钻后光点飞到这里。 */
export function detailPoint(scene: string): Point {
  const place = table[scene];
  if (!place) return isoOf('realm')(regions.capital.col, regions.capital.row);
  return isoOf(place.level)(place.col, place.row);
}

/** 层级面包屑，如 ['天下舆图','京城总览','荣国府总览']。 */
export function breadcrumbs(scene: string): string[] {
  const place = table[scene];
  return crumbs[place?.level ?? 'realm'] ?? crumbs.realm;
}

export function regionName(scene: string): string {
  const place = table[scene];
  return regions[place?.region ?? 'capital']?.name ?? '京都 · 神京';
}

/** 同一层里的所有地点，用来画下钻后的点阵底图（不是只有当前一个孤点）。 */
export function levelDots(level: string) {
  const iso = isoOf(level);
  return Object.entries(table)
    .filter(([, p]) => p.level === level)
    .map(([scene, p]) => ({ scene, name: p.name, point: iso(p.col, p.row) }));
}

/** 天下图上的区域色块中心，用来画底图。 */
export function regionDots() {
  const iso = isoOf('realm');
  return Object.entries(regions).map(([key, r]) => ({ key, name: r.name, tone: r.tone, point: iso(r.col, r.row) }));
}

/** 二次贝塞尔上一点，供光点飞行用。控制点往上抬，读起来像「越过一段路」。 */
export function bezier(from: Point, to: Point, t: number, lift = 46): Point {
  const k = Math.max(0, Math.min(1, t));
  const cx = (from.x + to.x) / 2, cy = (from.y + to.y) / 2 - lift;
  const u = 1 - k;
  return {
    x: u * u * from.x + 2 * u * k * cx + k * k * to.x,
    y: u * u * from.y + 2 * u * k * cy + k * k * to.y,
  };
}

/** easeInOutCubic：光点起步与落点都慢，中途快，像真的赶路。 */
export function ease(t: number) {
  const k = Math.max(0, Math.min(1, t));
  return k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
}
