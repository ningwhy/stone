/** Every walk the story authors must actually resolve on the map.
 *
 * `verify_map_paths.mjs` proves that every anchor reaches every other anchor.
 * That is a property of the map alone, and a stricter one than the story needs:
 * a map may keep a decorative anchor (a window, a far bank) that nothing walks
 * to, and the map is still fine.
 *
 * This gate checks the property the reader actually experiences: replay the
 * story's `move` and `parallel` actions against the real A* and confirm every
 * leg has a route. It also honours the engine's visibility rule — a scene
 * change hides everybody, so a walk whose actor was never re-shown in the new
 * scene would throw `移动角色未显示` in the middle of a read.
 *
 * Usage: node --experimental-strip-types scripts/verify_story_walks.mjs
 */
import {readFileSync,readdirSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseTiledMap,findPath,cellKey} from '../src/model.ts';
import {story} from '../src/story.ts';

const root = resolve(dirname(fileURLToPath(import.meta.url)),'..');
const maps = new Map();
for (const file of readdirSync(resolve(root,'maps')).filter(f=>f.endsWith('.tmj'))){
  const map = parseTiledMap(JSON.parse(readFileSync(resolve(root,'maps',file),'utf8')));
  maps.set(map.id, map);
}

const errors = [];
let legs = 0;
let moves = 0;

// Replay the story the way the engine does: a scene change hides everybody.
const visible = new Set();
let sceneId = null;

for (const step of story) {
  if (step.scene !== sceneId) {
    sceneId = step.scene;
    visible.clear();
  }
  for (const action of step.actions ?? []) {
    if (action.type === 'show') {
      visible.add(action.actor);
    } else if (action.type === 'hide') {
      visible.delete(action.actor);
    } else if (action.type === 'move' || action.type === 'parallel') {
      moves++;
      const list = action.type === 'parallel' ? action.moves : [action];
      for (const move of list) {
        if (!visible.has(move.actor)) {
          errors.push(`${step.id}: ${move.actor} walks without being shown in this scene`);
          continue;
        }
        const map = maps.get(step.scene);
        if (!map) { errors.push(`${step.id}: unknown scene ${step.scene}`); continue; }
        let from = null;
        for (const name of move.via) {
          const to = map.anchors[name];
          if (!to) { errors.push(`${step.id}: unknown anchor ${name}`); from = null; break; }
          if (from) {
            legs++;
            try {
              findPath(map, from, to);
            } catch (e) {
              errors.push(`${step.id}: ${move.actor} ${e.message}`);
            }
          }
          from = to;
        }
      }
    }
  }
}

if (errors.length) {
  for (const error of errors) console.error(`ERROR ${error}`);
  console.error(`\n${errors.length} broken walk(s) in ${moves} move action(s)`);
  process.exitCode = 1;
} else {
  console.log(`All ${moves} move action(s) resolve: ${legs} walked leg(s), every one has a route.`);
}
