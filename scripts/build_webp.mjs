#!/usr/bin/env node
/** Convert the painted PNG assets to WebP beside their sources.
 * The manifest keeps pointing at the PNG originals (single source of truth for
 * calibration and content checks); the runtime prefers WebP via src/art.ts.
 * Incremental: a WebP is rebuilt only when its PNG is newer. */
import {execFileSync} from 'node:child_process';
import {readdirSync, statSync, existsSync, rmSync} from 'node:fs';
import {join, resolve} from 'node:path';

const root = resolve(import.meta.dirname, '..');
const dir = join(root, 'public/assets/rongguo');
const QUALITY = 84;

function cwebp() {
  for (const candidate of ['/opt/homebrew/bin/cwebp', '/usr/local/bin/cwebp']) {
    if (existsSync(candidate)) return candidate;
  }
  try { execFileSync('cwebp', ['-version'], {stdio: 'ignore'}); return 'cwebp'; }
  catch { return null; }
}

const bin = cwebp();
if (!bin) {
  console.error('build_webp: cwebp not found. Install with `brew install webp` (assets stay PNG and keep working).');
  process.exit(0); // non-fatal: the app falls back to PNG URLs only if WebP is absent
}

const pngs = readdirSync(dir).filter((f) => f.endsWith('.png'));
let made = 0, skipped = 0, before = 0, after = 0;
for (const file of pngs) {
  const src = join(dir, file);
  const out = join(dir, file.replace(/\.png$/, '.webp'));
  before += statSync(src).size;
  if (existsSync(out) && statSync(out).mtimeMs >= statSync(src).mtimeMs) {
    skipped++; after += statSync(out).size; continue;
  }
  execFileSync(bin, ['-quiet', '-mt', '-sharp_yuv', '-q', String(QUALITY), src, '-o', out], {stdio: 'pipe'});
  after += statSync(out).size; made++;
}

// Sources without a manifest entry would ship dead weight.
for (const file of readdirSync(dir)) {
  if (file.endsWith('.webp') && !existsSync(join(dir, file.replace(/\.webp$/, '.png')))) {
    rmSync(join(dir, file)); console.warn(`build_webp: removed orphan ${file}`);
  }
}

const mb = (n) => (n / 1024 / 1024).toFixed(1);
console.log(`build_webp: ${made} converted, ${skipped} up-to-date; PNG ${mb(before)}MB -> WebP ${mb(after)}MB (${Math.round(after / before * 100)}%)`);
