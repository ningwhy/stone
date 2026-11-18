#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibrate the eight chapter-24 characters to the project's asset contract.

Chapter 24 puts eight new faces on stage (贾芸 / 小红 / 倪二 / 卜世仁 /
香菱 / 秋纹 / 碧痕 / 鸳鸯), so they need the same treatment as everybody else
in the cast album. The bitmaps were painted by `scripts/gen_ch24_characters.py`
(qwen21 t2i -> bg-removal) and arrive as raw mattes, so the steps the painting
pipeline does not cover are carried out here:

  * measures the feet anchor from the matted bitmap (same threshold as
    `build_art_assets.py`: alpha >= 110),
  * scales by **height** (portrait 600, chibi 116) so the figure stands the
    same height as everybody else in the cast,
  * gives the chibi a `bodyCompress` (split = 0.42 x feet row, factor 0.64),
    the median contract of the compressed old chibis,
  * writes the sixteen entries into `art/calibration.json`.

It does NOT touch `maps/rongguo-entry.tmj` and does NOT rebuild the whole
manifest: `build_art_assets.py` rewrites `manifest.json` from the calibration
table and has silently dropped the identity blocks of characters that were
painted outside that pipeline before. The manifest entries are registered
afterwards by `scripts/rebuild_new_character_manifest.py`, which only rewrites
its own blocks.

Usage:
  python3 scripts/calibrate_ch24_chars.py
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT / 'art/matted'
CAL = ROOT / 'art/calibration.json'

# The seed of each character in art/identity/character-designs.json; the chibi
# is the portrait's seed + 1, same as every other character in the cast.
CHARS = {
    'jia_yun': 10234120,
    'xiaohong': 10234130,
    'ni_er': 10234140,
    'bu_shi_ren': 10234150,
    'xiangling': 10234160,
    'qiuwen': 10234170,
    'bihen': 10234180,
    'yuan_yang': 10234190,
}
PORTRAIT_H = 600
CHIBI_H = 116
CHIBI_SPLIT_RATIO = 0.42
CHIBI_FACTOR = 0.64


def feet_anchor(stem: str):
    """Bottom-most opaque row, x = centre of that row.

    Same threshold as `build_art_assets.py` (alpha >= 110) so the anchor the
    map uses lands exactly on the feet, not on the last anti-aliased pixel.
    """
    p = MAT / f'{stem}-sam.png'
    if not p.exists():
        raise FileNotFoundError(p)
    a = np.asarray(Image.open(p).convert('RGBA'))[..., 3]
    a = np.where(a >= 110, 255, 0).astype(np.uint8)
    rows = np.where(a.max(axis=1) > 0)[0]
    if len(rows) == 0:
        raise ValueError(f'{stem}: no opaque pixels (blank matte?)')
    feet_y = int(rows.max())
    xs = np.where(a[feet_y] > 0)[0]
    cx = int((xs.min() + xs.max()) / 2)
    return [cx, feet_y], (int(rows.min()), feet_y)


def main() -> int:
    cal = json.loads(CAL.read_text())
    by_id = {a['id']: a for a in cal['assets']}

    for cid, seed_base in CHARS.items():
        for kind, height in (('portrait', PORTRAIT_H), ('chibi', CHIBI_H)):
            sid = f'{cid}-{kind}'
            seed = seed_base + (1 if kind == 'chibi' else 0)
            anchor, (top, bottom) = feet_anchor(f'{sid}_s{seed}')
            item = by_id.get(sid)
            if item is None:
                item = {'id': sid, 'seed': seed}
                cal['assets'].append(item)
            item.pop('width', None)
            item['seed'] = seed
            item['height'] = height
            item['anchor'] = anchor
            if kind == 'chibi':
                item['bodyCompress'] = {'split': round(bottom * CHIBI_SPLIT_RATIO),
                                        'factor': CHIBI_FACTOR}
            print(f'{sid}: anchor={anchor} height={height}'
                  + (f' compress={item["bodyCompress"]}' if kind == 'chibi' else '')
                  + f'  (content rows {top}-{bottom})')

    shutil.copy2(CAL, Path('/tmp/calibration-backup-before-ch24.json'))
    CAL.write_text(json.dumps(cal, ensure_ascii=False, indent=1) + '\n')
    print(f'calibration rewritten ({len(cal["assets"])} entries)')
    by_id = {a['id']: a for a in cal['assets']}

    # Report what the final bitmap will look like once the calibration is
    # applied, so the anchor can be sanity-checked against the bitmap bounds.
    for cid, seed_base in CHARS.items():
        for kind, height in (('portrait', PORTRAIT_H), ('chibi', CHIBI_H)):
            sid = f'{cid}-{kind}'
            seed = seed_base + (1 if kind == 'chibi' else 0)
            src = MAT / f'{sid}_s{seed}-sam.png'
            im = Image.open(src)
            ratio = height / im.height
            w = round(im.width * ratio)
            item = by_id[sid]
            ax, ay = item['anchor']
            ax_scaled, ay_scaled = ax * ratio, ay * ratio
            ok = 0 <= ax_scaled <= w and 0 <= ay_scaled <= height + 1
            print(f'  {sid}: scaled {w}x{height} anchor=({ax_scaled:.0f},{ay_scaled:.0f})'
                  + ('' if ok else '  <== ANCHOR OUT OF BITMAP'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
