/** 列出某张图上**可通行**的锚点（可站人）。
 *
 *  记忆里的硬约束：名字存在 ≠ 可通行。可通行格只来自两处——
 *  `src/model.ts` 的 `parseTiledMap`：zone id 匹配 `^(A\d*|B|C|D|E|F)$` 的地板，
 *  以及 Routes 层路线沿途的走廊。要站人的锚点必须在某条 route 的 `anchor_ids` 里。
 *
 *  用法：node --experimental-strip-types scripts/anchors_of.mjs dinner central ...
 */
import {readFileSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseTiledMap,cellKey} from '../src/model.ts';

const root = resolve(dirname(fileURLToPath(import.meta.url)),'..');
const maps = new Map();
for (const file of readdirSync(resolve(root,'maps')).filter(f=>f.endsWith('.tmj'))){
  const map = parseTiledMap(JSON.parse(readFileSync(resolve(root,'maps',file),'utf8')));
  maps.set(map.id, map);
}

const want = process.argv.slice(2);
for (const id of (want.length?want:[...maps.keys()])){
  const map = maps.get(id);
  if (!map) { console.log(`!! 未知场景 ${id}`); continue; }
  const onRoute = new Set();
  for (const names of Object.values(map.routes)) for (const n of names) onRoute.add(n);
  const ok = [], bad = [];
  for (const [name, a] of Object.entries(map.anchors)){
    // 锚点自己所在的格必须可通行（parseTiledMap 里就是 (col,row)）
    (map.walkable.has(cellKey(a.col, a.row)) ? ok : bad).push(name);
  }
  console.log(`\n== ${id}  (${map.title})`);
  console.log(`   可通行(${ok.length}):`, ok.join(', '));
  console.log(`   不可通行(${bad.length}):`, bad.join(', '));
}
