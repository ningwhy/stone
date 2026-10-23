import { artAssets, artImage } from './art.ts';
import type { MapData } from './model.ts';
import type { StoryEngine } from './engine.ts';
import type { ActorId } from './story.ts';

/** Scene changes rebuild the Phaser stage, so every asset has to be fetched again before the map appears.
 * Warming the HTTP cache while the reader is still busy with dialogue removes most of that wait.
 * Nothing here is required for correctness: it only pays forward what the next scene will ask for. */
const warmed = new Set<string>();
const pending: string[] = [];
let scheduled = false;
const THROTTLE = 2;
const GAP_MS = 400;

function idle(run: () => void) {
  const request = (globalThis as {requestIdleCallback?: (cb: () => void, opt?: {timeout: number}) => number}).requestIdleCallback;
  if (typeof request === 'function') request(run, {timeout: 1500});
  else setTimeout(run, 220);
}

function drain() {
  for (let i = 0; i < THROTTLE && pending.length; i++) {
    const key = pending.shift()!;
    if (!artAssets[key] || warmed.has(key)) continue;
    warmed.add(key);
    const image = new Image();
    image.decoding = 'async';
    image.src = artImage(key);
  }
  if (pending.length) setTimeout(drain, GAP_MS);
  else scheduled = false;
}

/** Data-saver motifs and very slow links are better off paying per scene. */
export function prefetchEnabled() {
  const connection = (navigator as {connection?: {saveData?: boolean; effectiveType?: string}}).connection;
  if (!connection) return true;
  return !connection.saveData && !/^(slow-2g|2g)$/.test(connection.effectiveType ?? '');
}

export function queuePrefetch(keys: Iterable<string>) {
  if (!prefetchEnabled()) return;
  for (const key of keys) if (artAssets[key] && !warmed.has(key) && !pending.includes(key)) pending.push(key);
  if (scheduled || !pending.length) return;
  scheduled = true;
  idle(drain);
}

function chibi(actor: ActorId) { return actor === 'sedan' ? 'sedan-chair' : `${actor}-chibi`; }

/** Everything a scene needs the moment it becomes the current stage. */
export function sceneAssets(engine: StoryEngine, scene: string) {
  const keys = new Set<string>();
  const map = engine.maps[scene] as MapData | undefined;
  if (!map) return keys;
  for (const object of map.art) keys.add(object.asset);
  for (const step of engine.steps) {
    if (step.scene !== scene) continue;
    for (const action of step.actions) {
      if (action.type === 'show' || action.type === 'move') keys.add(chibi(action.actor));
      else if (action.type === 'parallel') for (const move of action.moves) keys.add(chibi(move.actor));
    }
  }
  return keys;
}

/** The next few scenes in reading order — enough to cover a reading session without flooding the link. */
export function prefetchUpcoming(engine: StoryEngine, index: number, lookahead = 2) {
  const needed = new Set<string>();
  const scenes: string[] = [];
  for (let i = index; i < engine.steps.length && scenes.length <= lookahead; i++) {
    const scene = engine.steps[i].scene;
    if (scenes.includes(scene)) continue;
    scenes.push(scene);
    for (const key of sceneAssets(engine, scene)) needed.add(key);
  }
  queuePrefetch(needed);
}

/** Portraits and tokens for the scene on stage now: dialogue audiences never wait on the speaker's face. */
export function prefetchCast(engine: StoryEngine, index: number) {
  const step = engine.steps[index];
  if (!step) return;
  const needed = sceneAssets(engine, step.scene);
  for (let i = index; i < engine.steps.length && engine.steps[i].scene === step.scene; i++) {
    for (const action of engine.steps[i].actions) {
      if (action.type === 'show' || action.type === 'effect') needed.add(`${action.actor}-portrait`);
    }
  }
  queuePrefetch(needed);
}
