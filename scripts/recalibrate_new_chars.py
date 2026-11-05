#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-calibrate the 6 chapter-8/9 characters to the same contract as the old 45.

Why this exists
---------------
The 12 assets (ying_er / qin_zhong / jia_rui / jin_rong / ming_yan / li_gui,
portrait + chibi) were first calibrated against the **Qwen Image 2.1** renders,
which are a larger canvas than the **Z-Image** renders the characters were
finally painted with. When the art was repainted on the Z-Image canvas the
calibration was left untouched, so every anchor was still expressed in the old
canvas coordinates and landed *outside* the new bitmap
(ying_er-portrait anchor y=878 on a 779px tall asset, jia_rui-portrait anchor
x=57 on a 300px wide asset). On the map that reads as a figure hovering above
or sinking into the ground, or standing off to one side of its own tile.

The old 45 also scale by **height** (portrait 600, chibi 116) so everybody
stands the same height and only their build changes the width, and their chibis
carry a `bodyCompress` (split/factor) that produces the big-head-small-body
proportion. The new six were written with `width` and no compression, which is
why they came out at 561-779 tall and read less like chibis.

What it does
------------
  - re-measures the feet anchor from the *current* matted bitmap
  - switches width -> height (portrait 600, chibi 116)
  - adds bodyCompress to chibis, split = 0.42 of the measured feet row
    (median of the 38 compressed old chibis), factor 0.64 (their majority value)
  - backs up calibration.json, rebuilds, and restores maps/rongguo-entry.tmj

Idempotent: re-running re-measures again and converges.
"""
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT / 'art/matted'
CAL = ROOT / 'art/calibration.json'
ENTRY = ROOT / 'maps/rongguo-entry.tmj'
BACKUP = Path('/tmp/rongguo-entry-backup.tmj')

CHARS = {
    'ying_er': 10232066,
    'qin_zhong': 10232068,
    'jia_rui': 10232070,
    'jin_rong': 10232072,
    'ming_yan': 10232074,
    'li_gui': 10232076,
}
PORTRAIT_H = 600   # old-cast majority (44 of 51 portraits)
CHIBI_H = 116      # old-cast majority (42 of 51 chibis)
CHIBI_SPLIT_RATIO = 0.42   # median split/anchorY of the 38 compressed old chibis
CHIBI_FACTOR = 0.64        # their majority factor


def feet_anchor(stem):
    """Bottom-most opaque row, x = centre of that row. Same threshold as build_art_assets."""
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


def main():
    cal = json.loads(CAL.read_text())
    shutil.copy2(CAL, Path('/tmp/calibration-backup-before-recalib.json'))
    by_id = {a['id']: a for a in cal['assets']}
    changed = 0
    for cid, seed in CHARS.items():
        for kind, height in (('portrait', PORTRAIT_H), ('chibi', CHIBI_H)):
            sid = f'{cid}-{kind}'
            s = seed + (1 if kind == 'chibi' else 0)
            anchor, (top, bottom) = feet_anchor(f'{sid}_s{s}')
            item = by_id.get(sid)
            if item is None:
                print('MISSING calibration entry', sid); continue
            item.pop('width', None)
            item['height'] = height
            item['anchor'] = anchor
            if kind == 'chibi':
                item['bodyCompress'] = {'split': round(bottom * CHIBI_SPLIT_RATIO),
                                        'factor': CHIBI_FACTOR}
            print(f'{sid}: anchor={anchor} height={height}'
                  + (f' compress={item["bodyCompress"]}' if kind == 'chibi' else '')
                  + f'  (content rows {top}-{bottom})')
            changed += 1
    CAL.write_text(json.dumps(cal, ensure_ascii=False, indent=1) + '\n')
    print(f'calibration rewritten ({changed} entries)')

    if ENTRY.exists():
        shutil.copy2(ENTRY, BACKUP)
    print('running build_art_assets.py ...')
    r = subprocess.run([sys.executable, str(ROOT / 'scripts/build_art_assets.py')], cwd=ROOT)
    if ENTRY.exists() and BACKUP.exists():
        shutil.copy2(BACKUP, ENTRY)
        print('restored maps/rongguo-entry.tmj (portraits are not map props)')
    r.check_returncode()

    man = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())['assets']
    print('--- rebuilt ---')
    bad = 0
    for cid in CHARS:
        for kind in ('portrait', 'chibi'):
            key = f'{cid}-{kind}'
            a = man.get(key)
            if not a:
                print('  MISSING', key); bad += 1; continue
            ax, ay = a['anchor']
            ok = 0 <= ax <= a['width'] and 0 <= ay <= a['height'] + 1
            if not ok:
                bad += 1
            print(f"  {key}: {a['width']}x{a['height']} anchor={a['anchor']}"
                  + ('' if ok else '  <== ANCHOR OUT OF BITMAP'))
    print('anchor problems:', bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
