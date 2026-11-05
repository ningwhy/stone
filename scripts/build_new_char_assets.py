#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibrate the 6 new chapter-8/9 character assets into the runtime manifest.

For each character/kind it:
  - reads art/matted/{id}_s{seed}-sam.png, auto-detects the feet anchor
    (bottommost opaque pixel, x = centre of that row)
  - appends a calibration.json['assets'] entry (id, seed, anchor, width)
  - runs build_art_assets.py to emit public/assets/rongguo/{id}.png + manifest
  - protects maps/rongguo-entry.tmj (portraits are not placed on any map, so the
    rebuilt Art layer must be restored from the committed version)

Idempotent: calibration entries already present are skipped.
"""
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / '.local-tools/local-image-studio/scripts/image_studio.py'
MAT = ROOT / 'art/matted'
CAL = ROOT / 'art/calibration.json'
ENTRY = ROOT / 'maps/rongguo-entry.tmj'

# character id -> seed (portrait seed; chibi seed = +1, matching gen_new_characters.py)
CHARS = {
    'ying_er': 10232066,
    'qin_zhong': 10232068,
    'jia_rui': 10232070,
    'jin_rong': 10232072,
    'ming_yan': 10232074,
    'li_gui': 10232076,
}
PORTRAIT_W = 300
CHIBI_W = 50


def feet_anchor(stem):
    p = MAT / f'{stem}-sam.png'
    if not p.exists():
        raise FileNotFoundError(p)
    im = Image.open(p).convert('RGBA')
    a = np.asarray(im)[..., 3]
    # hard threshold like build_art_assets
    a = np.where(a >= 110, 255, 0).astype(np.uint8)
    rows = np.where(a.max(axis=1) > 0)[0]
    if len(rows) == 0:
        raise ValueError(f'{stem}: no opaque pixels')
    feet_y = int(rows.max())
    row = a[feet_y]
    xs = np.where(row > 0)[0]
    cx = int((xs.min() + xs.max()) / 2) if len(xs) else im.width // 2
    return [cx, feet_y]


def main():
    cal = json.loads(CAL.read_text())
    existing = {a['id'] for a in cal['assets']}
    added = 0
    for cid, seed in CHARS.items():
        for kind, width in (('portrait', PORTRAIT_W), ('chibi', CHIBI_W)):
            sid = f'{cid}-{kind}'
            if sid in existing:
                print('skip (calibrated)', sid); continue
            s = seed + (1 if kind == 'chibi' else 0)
            stem = f'{sid}_s{s}'
            anchor = feet_anchor(stem)
            cal['assets'].append({'id': sid, 'seed': s, 'anchor': anchor, 'width': width})
            print(f'add {sid} anchor={anchor} width={width}')
            added += 1
    if added:
        CAL.write_text(json.dumps(cal, ensure_ascii=False, indent=1) + '\n')
        print(f'calibration updated (+{added})')
    else:
        print('calibration already up to date')

    # protect entry map, run build, restore
    backup = ROOT / '/tmp/rongguo-entry-backup.tmj'
    if ENTRY.exists():
        shutil.copy2(ENTRY, backup)
    print('running build_art_assets.py ...')
    r = subprocess.run([sys.executable, str(ROOT / 'scripts/build_art_assets.py')], cwd=ROOT)
    if ENTRY.exists() and backup.exists():
        shutil.copy2(backup, ENTRY)
        print('restored maps/rongguo-entry.tmj (portraits are not map props)')
    r.check_returncode()
    # report
    man = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())['assets']
    for cid in CHARS:
        for kind in ('portrait', 'chibi'):
            key = f'{cid}-{kind}'
            a = man.get(key)
            print(f'  {key}:', f"{a['width']}x{a['height']} anchor={a['anchor']}" if a else 'MISSING')


if __name__ == '__main__':
    main()
