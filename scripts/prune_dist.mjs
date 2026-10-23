#!/usr/bin/env node
/** After vite copies public/ into dist/, drop the PNG originals: the runtime
 * requests WebP exclusively (see src/art.ts), so PNGs in dist are dead weight. */
import {readdirSync, statSync, rmSync, existsSync} from 'node:fs';
import {join, resolve} from 'node:path';

const dir = resolve(import.meta.dirname, '..', 'dist/assets/rongguo');
if (!existsSync(dir)) process.exit(0);

let removed = 0, bytes = 0, missingWebp = 0;
for (const file of readdirSync(dir)) {
  if (!file.endsWith('.png')) continue;
  const webp = join(dir, file.replace(/\.png$/, '.webp'));
  if (!existsSync(webp)) { missingWebp++; continue; } // keep PNG when no WebP exists
  bytes += statSync(join(dir, file)).size;
  rmSync(join(dir, file)); removed++;
}
console.log(`prune_dist: removed ${removed} PNG files (${(bytes / 1024 / 1024).toFixed(1)} MB), ${missingWebp} kept without WebP`);
