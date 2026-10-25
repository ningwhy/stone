#!/usr/bin/env node
/** Convert the painted PNG assets to WebP beside their sources.
 * The manifest keeps pointing at the PNG originals (single source of truth for
 * calibration and content checks); the runtime prefers WebP via src/art.ts.
 * Incremental: a WebP is rebuilt only when its PNG is newer. */
import {execFileSync} from 'node:child_process';
import {readdirSync, statSync, existsSync, rmSync, readFileSync, writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
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

// Stamp every manifest entry with its WebP's content digest. The runtime appends it as a
// query string, so a rebuilt asset gets a fresh URL and browsers stop serving the previous
// bitmap from cache. Before this existed only identity portraits carried a version, and a
// redrawn prop (the sedan growing four bearers) kept its old URL forever.
const manifestPath = join(dir, 'manifest.json');
if (existsSync(manifestPath)) {
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  let hashed = 0;
  for (const [key, entry] of Object.entries(manifest.assets)) {
    const webp = join(dir, String(entry.image ?? '').split('/').pop()?.replace(/\.png$/, '.webp') ?? '');
    if (!existsSync(webp)) continue;
    const hash = createHash('md5').update(readFileSync(webp)).digest("hex").slice(0, 12);
    if (entry.hash !== hash) { manifest.assets[key].hash = hash; hashed++; }
  }
  if (hashed) writeFileSync(manifestPath, JSON.stringify(manifest, null, 1) + '\n');
  console.log(`build_webp: ${hashed} manifest entries stamped with a content hash`);
}
