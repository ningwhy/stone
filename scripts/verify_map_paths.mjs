/** Every anchor on every map must be able to reach every other one.
 *
 * The engine walks people with a four-way A* over `walkable`, and a walk that
 * has no route throws at the moment it is authored — which in a long story is
 * a failure the reader meets several hours in. This gate catches it before the
 * story is built.
 *
 * Two things make a floor walkable, and both are easy to get wrong:
 *
 *  1. The zone id. `parseTiledMap` only adds a floor to `walkable` when its id
 *     matches /^(A\d*|B|C|D|E|F)$/. A zone called `YARD` or `SHrine` looks
 *     like a floor in Tiled and is invisible ground to the engine.
 *  2. The routes. The `Routes` layer carves the corridor between the anchors
 *     it names, axis by axis, and that is the only way two separate floor
 *     regions get joined.
 *
 * Furniture then punches holes again: `wood-screen`, `tea-table`,
 * `garden-rock`, `altar-table`, `square-table` and `writing-desk` write an
 * `ArtFootprints` cell, and a footprint on the corridor truncates it.
 *
 * Usage: node --experimental-strip-types scripts/verify_map_paths.mjs [mapId...]
 */
import {readFileSync,readdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseTiledMap,findPath} from '../src/model.ts';

const root = resolve(dirname(fileURLToPath(import.meta.url)),'..');
const wanted = process.argv.slice(2);
const files = readdirSync(resolve(root,'maps')).filter(f=>f.endsWith('.tmj')).sort();

let failed = 0;
let checked = 0;

for (const file of files) {
  const map = parseTiledMap(JSON.parse(readFileSync(resolve(root,'maps',file),'utf8')));
  if (wanted.length && !wanted.includes(map.id)) continue;
  const names = Object.keys(map.anchors);
  const broken = [];
  for (const from of names) {
    for (const to of names) {
      if (from === to) continue;
      try {
        findPath(map, map.anchors[from], map.anchors[to]);
      } catch (e) {
        broken.push(`${from} → ${to}: ${e.message}`);
      }
    }
  }
  checked++;
  if (broken.length) {
    failed++;
    console.error(`FAIL ${map.id} (${file}): ${broken.length} unreachable pair(s)`);
    for (const line of broken.slice(0,12)) console.error(`     ${line}`);
    if (broken.length > 12) console.error(`     ... and ${broken.length-12} more`);
  } else {
    console.log(`ok   ${map.id}: ${names.length} anchors, all pairs reachable`);
  }
}

if (!checked) {
  console.error('no map matched');
  process.exitCode = 1;
} else if (failed) {
  console.error(`${failed}/${checked} map(s) failed`);
  process.exitCode = 1;
} else {
  console.log(`All ${checked} map(s) pass: every anchor reaches every other anchor.`);
}
