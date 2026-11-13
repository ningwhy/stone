/** 校验每张图的**路线锚点可通行 + 同 route 内两两连通**。
 *
 *  记忆里的硬约束：名字存在 ≠ 可通行。可通行格只来自两处——
 *  `src/model.ts` 的 `parseTiledMap`：zone id 匹配 `^(A\d*|B|C|D|E|F)$` 的地板，
 *  以及 Routes 层路线沿途的走廊。要站人的锚点必须在某条 route 的 `anchor_ids` 里。
 *
 *  两类锚点必须分开看：
 *  - **路线锚点**（出现在某条 route 的 anchor_ids 里）：必须可通行，且同 route
 *    内两两在可通行格上连通。否则引擎寻路会抛「没有可行走路线」，读者点到
 *    那一步就走不动。这是**硬门禁**。
 *  - **装饰锚点**（不在任何 route 里）：只是道具位（挂画、戏台、桌案），
 *    设计上就不可站人，比如 `c11_tianxiang:stage`、`c5_ningfu:portrait_wall`。
 *    这些不可通行是正常的，不算问题。
 *
 *  连通性直接用引擎自己的 `findPath` 判定，别自己重写一套 BFS：
 *  引擎的走廊生成是 **L 形（先走列、再走行）**，再扣掉 blocker，
 *  自己写的 BFS 与引擎的实际可达性可能不一致（血泪教训，见下）。
 *
 *  血泪教训：`yihong` 的 `to_outer` 路线曾经断在 (20,26)——那是 `tea-table`
 *  的 ArtFootprints。路线走廊在 blocker 之前生成、之后被删，于是 yard 出发的
 *  任何横向走廊都被茶几切断（引擎的 L 形走廊第一步必然经过它）。
 *  剧情当时没走这条路线，所以浏览器回归是绿的，但这条路是**定时炸弹**。
 *  这就是为什么要把「每条 route 内两两连通」做成独立门禁，而不是靠剧情覆盖。
 *
 *  用法：node --experimental-strip-types scripts/check_anchors_walkable.mjs maps/*.tmj
 *  退出码非 0 表示有 route 锚点不可通行或断连。
 */
import {readFileSync} from 'node:fs';
import {parseTiledMap, findPath, cellKey} from '../src/model.ts';

const files = process.argv.slice(2);
if (!files.length) {
  console.error('用法：node --experimental-strip-types scripts/check_anchors_walkable.mjs maps/*.tmj');
  process.exit(2);
}

let problems = 0;
let routeAnchors = 0;
let decorative = 0;

for (const f of files) {
  const map = parseTiledMap(JSON.parse(readFileSync(f, 'utf8')));

  // 路线锚点 = 出现在任意 route 的 anchor_ids 里的那些。
  const inRoute = new Set();
  for (const names of Object.values(map.routes)) for (const n of names) inRoute.add(n);

  const bad = [];
  for (const [name, p] of Object.entries(map.anchors)) {
    const ok = map.walkable.has(cellKey(p.col, p.row));
    if (inRoute.has(name)) {
      routeAnchors++;
      if (!ok) bad.push(`路线锚点不可通行：${map.id}:${name} (${p.col},${p.row})`);
    } else {
      decorative++;
    }
  }

  // 同 route 内两两连通：用引擎自己的 findPath 判定。
  for (const [rid, names] of Object.entries(map.routes)) {
    for (let i = 1; i < names.length; i++) {
      const a = map.anchors[names[i - 1]], b = map.anchors[names[i]];
      try {
        findPath(map, a, b);
      } catch (err) {
        bad.push(`路线断连：${map.id}:${rid} ${names[i - 1]} → ${names[i]}（${err.message}）`);
      }
    }
  }

  if (bad.length) {
    problems += bad.length;
    console.log(`\n=== ${map.id} (${map.title}) ===`);
    for (const b of bad) console.log('  ✗ ' + b);
  }
}

console.log(
  problems
    ? `\n${problems} problem(s)`
    : `\nall route anchors walkable and connected — ${routeAnchors} route anchors, ${decorative} decorative anchors`
);
process.exitCode = problems ? 1 : 0;
