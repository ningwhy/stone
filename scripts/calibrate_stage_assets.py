#!/usr/bin/env python3
"""Give every matted stage asset a calibration entry: bottom-centre anchor, on-screen width.

The props are already drawn as isometric objects, so there is no skew to fit — the only
calibration that matters is where the object touches the ground and how wide it lands on
screen. Both come straight from the alpha bounding box of the matte:

  anchor = (bbox centre x, bbox bottom y)   — the ground line the depth sort uses
  width  = bbox width                       — the sprite's on-screen footprint

Existing entries are left untouched, so hand-tuned anchors survive a re-run.

Usage: python3 scripts/calibrate_stage_assets.py [--width id=px ...]
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
plan = json.loads((ROOT / 'art/generation-plan.json').read_text())
config_path = ROOT / 'art/calibration.json'
config = json.loads(config_path.read_text())

# Buildings read a little small at full cell width; furniture reads best at ~0.35 of the
# cell so a chair is a chair next to a 1100 px hall. Overridable per id from the CLI.
DEFAULT_WIDTH = {'*': None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--width', nargs='*', default=[], help='id=px overrides')
    parser.add_argument('--only', nargs='*', help='restrict to these ids')
    args = parser.parse_args()
    overrides = dict(item.split('=') for item in args.width)

    have = {a['id'] for a in config['assets']}
    added = 0
    for job in plan['jobs']:
        key = job['id']
        if args.only and key not in args.only:
            continue
        if key in have:
            continue
        stem = f"{key}_s{job['seed']}"
        matte = ROOT / f'art/matted/{stem}-sam.png'
        if not matte.is_file():
            continue
        im = Image.open(matte).convert('RGBA')
        alpha = np.asarray(im.getchannel('A'))
        ys, xs = np.nonzero(alpha > 8)
        if not len(xs):
            print(f'  skip {key}: empty matte')
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        width = int(overrides.get(key, min(x1 - x0 + 1, 900)))
        config['assets'].append({'id': key, 'seed': job['seed'],
                                 'anchor': [round((x0 + x1) / 2, 1), y1 + 1],
                                 'width': width})
        added += 1
        print(f'  {key:16s} bbox {x1 - x0 + 1}x{y1 - y0 + 1}  width {width}')
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    print(f'calibration.json: {added} new entr{"y" if added == 1 else "ies"}')


if __name__ == '__main__':
    main()
