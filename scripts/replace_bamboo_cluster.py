#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace the broken `bamboo-cluster` with a repainted, cleanly cut one.

The old bamboo (seed 10400055) was painted on a sheet of beige paper: the
source's own prompt had asked for a plain white backdrop, and the model gave
the prop a paper ground instead. SAM then read the bamboo as the subject and
kept the paper, so the runtime bitmap shipped as a cream slab with a few green
strokes in it — invisible as bamboo, and present in thirteen maps since it
was first committed on 2026-10-29.

The replacement (seed 10400571) was painted with the ground ruled out, and is
cut with `scripts/cutout_white_backdrop.py` instead of SAM (the server's
BiRefNet node is currently broken: `'Config' object has no attribute
'is_encoder_decoder'`).

The old seed stays in the generation plan and its source is kept on disk, so
this is a replacement, not a deletion: `art/source/bamboo-cluster_s10400055-01.png`
and its matte are still there for anyone who wants to compare.

Usage: repair_bamboo_cluster.py
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from cutout_white_backdrop import cutout  # noqa: E402

OLD_SEED = 10400055
NEW_SEED = 10400571
KEY = 'bamboo-cluster'

source = ROOT / f'art/source/{KEY}_s{NEW_SEED}-01.png'
matte = ROOT / f'art/matted/{KEY}_s{NEW_SEED}-white.png'
runtime = ROOT / f'public/assets/rongguo/{KEY}.png'

# --- 1. cut the prop out of the white backdrop -----------------------------
rgba, report = cutout(source, threshold=244)
Image.fromarray(rgba, 'RGBA').save(matte)
print('cutout:', json.dumps(report, ensure_ascii=False))

# --- 2. re-point the calibration at the new seed ---------------------------
config_path = ROOT / 'art/calibration.json'
config = json.loads(config_path.read_text())
entry = next((a for a in config['assets'] if a['id'] == KEY), None)
if entry is None:
    raise SystemExit(f'{KEY} is not in art/calibration.json')
entry['seed'] = NEW_SEED
entry['matteKind'] = 'white'
# The matte is the cropped prop, so the anchor is the bottom centre of what is
# actually there: the bamboo root, not the paper it used to stand on.
alpha = np.asarray(Image.open(matte).convert('RGBA').getchannel('A'))
ys, xs = np.nonzero(alpha > 8)
entry['anchor'] = [round((int(xs.min()) + int(xs.max())) / 2, 1), int(ys.max()) + 1]
entry['width'] = int(xs.max() - xs.min() + 1)
config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
print(f'calibration: seed={NEW_SEED} anchor={entry["anchor"]} width={entry["width"]}')

# --- 3. rebuild the runtime bitmaps ---------------------------------------
subprocess.run([sys.executable, str(ROOT / 'scripts/build_art_assets.py')], check=True,
               cwd=ROOT)
subprocess.run(['node', str(ROOT / 'scripts/build_webp.mjs')], check=True, cwd=ROOT)

# --- 4. prove the green is actually there ----------------------------------
for path in (runtime, runtime.with_suffix('.webp')):
    im = Image.open(path).convert('RGBA')
    px = list(im.getdata())
    op = [p for p in px if p[3] > 20]
    green = sum(1 for p in op if p[1] > p[0] + 8 and p[1] > p[2] + 8)
    print(f'{path.name}: {im.size[0]}x{im.size[1]} opaque={len(op)} green%={green / len(op) * 100:.2f}')

manifest = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())
entry = manifest['assets'][KEY]
print('manifest:', json.dumps({k: entry[k] for k in ('image', 'width', 'height', 'anchor', 'source')},
                               ensure_ascii=False))
