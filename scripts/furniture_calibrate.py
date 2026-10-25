#!/usr/bin/env python3
"""Append the new indoor furniture to art/calibration.json.

Anchors follow the shipped convention (same as tea-table / dining-table):
[bbox center x, bbox bottom - 2] measured on the thresholded matte
(alpha >= 110, exactly the threshold build_art_assets.py applies), in the
matte's own pixel space. New entries are appended at the END of the assets
list so existing tileset gids never shift.

Idempotent: an entry whose id already exists is left untouched.
Run:  python3 scripts/furniture_calibrate.py
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

# (id, seed, design output width in px). Widths keep each piece proportional
# to the shipped tea-table (130) / dining-table (230) and to 116px chibi cast.
# `alphaFloor` lifts the soft-edge floor for thin-structure pieces (chair
# spindles, stool legs, flower-stand posts): at 70-110px wide a 1px antialias
# halo is a large share of the silhouette, which would drop the shipped
# solid-alpha guard below its .9 line. 128 keeps one antialiased edge pixel.
FURNITURE = [
    ('square-table', 10224101, 165, None),
    ('altar-table', 10224102, 195, None),
    ('writing-desk', 10224103, 180, None),
    ('official-chair', 10224104, 100, 128),
    ('round-stool', 10224105, 70, 128),
    ('square-stool', 10224106, 70, 128),
    ('cabinet', 10224107, 130, None),
    ('brazier', 10224118, 90, None),
    ('vase-stand', 10224109, 110, 128),
]


def main() -> int:
    cfg = json.loads((ROOT / 'art/calibration.json').read_text())
    assets = cfg['assets']
    known = {a['id'] for a in assets}
    added = []
    fixed = 0
    for key, seed, width, alpha_floor in FURNITURE:
        if key in known:
            existing = next(a for a in assets if a['id'] == key)
            if alpha_floor and 'alphaFloor' not in existing:
                existing['alphaFloor'] = alpha_floor
                fixed += 1
                print(f'fix  {key}: alphaFloor {alpha_floor}')
            else:
                print(f'skip {key}: already calibrated')
            continue
        matte = ROOT / f'art/matted/{key}_s{seed}-sam.png'
        if not matte.exists():
            print(f'skip {key}: matte missing ({matte.name})')
            continue
        a = np.asarray(Image.open(matte).convert('RGBA').getchannel('A'))
        m = a >= 110
        ys, xs = np.where(m)
        if not len(xs):
            print(f'skip {key}: matte is empty')
            continue
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        cx = (bbox[0] + bbox[2]) / 2
        anchor = [round(cx, 1), bbox[3] - 2]
        entry = {'id': key, 'seed': seed, 'anchor': anchor, 'width': width}
        if alpha_floor:
            entry['alphaFloor'] = alpha_floor
        assets.append(entry)
        added.append((key, entry))
        print(f'add  {key}: bbox {bbox} anchor {anchor} width {width}'
              + (f' alphaFloor {alpha_floor}' if alpha_floor else ''))
    if added or fixed:
        (ROOT / 'art/calibration.json').write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2) + '\n')
        print(f'wrote art/calibration.json ({len(assets)} assets, +{len(added)}, {fixed} fixed)')
    else:
        print('nothing to add')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
