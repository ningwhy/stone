#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibrate and build the ten chapter-13/14/15 characters.

The contract is the same one the tenth-to-twelfth chapters used
(see docs/production/art.md, and scripts/build_ch1012_assets.py):

  - portrait is scaled by `height: 600`, chibi by `height: 116`.
    Scaling old portraits by height keeps everybody the same size on the board
    and lets only girth change the width; scaling by width would make them
    stand at different heights.
  - chibi carries `bodyCompress` (split = feet anchor x 0.42, factor = 0.64).
    The big-head small-body proportion comes from it; without it the sprite is
    not a chibi at all.
  - the anchor is measured from the current matted bitmap: the bottom-most
    opaque row, and the centre of that row. A new canvas means a new
    measurement — reusing the old coordinates leaves people floating or sunk.

Why not build_new_char_assets.py: that script skips an entry whose
calibration already exists, and what is needed here is precisely to re-measure
against the bitmaps that were just painted.

Idempotent: re-running re-measures and converges.

Usage: python3 scripts/build_ch1315_assets.py
"""
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT / 'art/matted'
CAL = ROOT / 'art/calibration.json'
ENTRY = ROOT / 'maps/rongguo-entry.tmj'
BACKUP = Path('/tmp/rongguo-entry-backup-ch1315.tmj')

_SEEDS = {c['id']: c['seed'] for c in
          json.loads((ROOT / 'art/identity/character-designs.json').read_text())['characters']}
CHARS = {k: _SEEDS[k] for k in
         ('dai_quan', 'bao_zhu', 'lai_sheng', 'zhao_er', 'shui_rong',
          'jing_xu', 'zhi_neng', 'er_ya_tou', 'wang_er', 'qin_ye')}

PORTRAIT_H = 600
CHIBI_H = 116
CHIBI_SPLIT_RATIO = 0.42
CHIBI_FACTOR = 0.64


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
    shutil.copy2(CAL, Path('/tmp/calibration-backup-before-ch1315.json'))
    by_id = {a['id']: a for a in cal['assets']}
    changed = 0
    for cid, seed in CHARS.items():
        for kind, height in (('portrait', PORTRAIT_H), ('chibi', CHIBI_H)):
            sid = f'{cid}-{kind}'
            s = seed + (1 if kind == 'chibi' else 0)
            anchor, (top, bottom) = feet_anchor(f'{sid}_s{s}')
            item = by_id.get(sid)
            if item is None:
                # A new character entering the book. The fields must match the
                # old ones: build_art_assets.py derives the source name from
                # `seed` (`{id}_s{seed}-sam.png`), and a missing seed is a KeyError.
                item = {'id': sid, 'seed': s}
                cal['assets'].append(item)
                by_id[sid] = item
                print('NEW calibration entry', sid)
            item['seed'] = s
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
