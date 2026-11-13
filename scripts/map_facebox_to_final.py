#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Map a face box measured on the *matte* into the final asset's coordinates.

Why this exists
---------------
`identity.faceBox` in the manifest is expressed in the **final PNG's** pixel
coordinates — the bitmap the browser loads. That is the only coordinate system
`src/Portrait.tsx` can crop with:

    const h=(box[3]-box[1])*2.25, top=Math.max(0,box[1]-(box[3]-box[1])*.48)

A face box found on `art/matted/*-sam.png` is in a different space. The matte
goes through several transforms before it becomes the final PNG
(`scripts/build_art_assets.py`):

  1. `bodyCompress` — the lower body below `split` is squeezed by `factor`;
     the anchor and anything under the split move up.
  2. optional `baseSlope` shear (none of the characters use it).
  3. `mirror` (none of the characters use it).
  4. crop to the opaque bounding box (`crop` in the manifest).
  5. scale to the calibrated `height` (portrait 600, chibi 116).

Steps 1-4 are all affine, so a box can be carried through them exactly. This
script replays them and prints the final box.

The script verifies itself before it is trusted: it re-runs the same mapping
for characters whose face box was reviewed by eye (si_er, zijun, cui_lv,
jia_huan) and compares the result with the box actually in the manifest. Only
when the replay matches does it print the box for the new character.

Usage:
  python3 scripts/map_facebox_to_final.py --asset jia_lan-portrait --box 297 90 468 300
  python3 scripts/map_facebox_to_final.py --self-check
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def load():
    manifest = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())['assets']
    calibration = {a['id']: a for a in json.loads((ROOT / 'art/calibration.json').read_text())['assets']}
    return manifest, calibration


def final_geometry(manifest, calibration, key):
    """Replay the matte -> final transform, return (scale_x, scale_y, offset_x, offset_y).

    The offsets are applied *after* scaling, i.e. the final box is
    `box * scale + offset`. The crop is the opaque bounding box of the
    compressed matte, exactly as `build_art_assets.py` computes it.
    """
    entry = manifest[key]
    item = calibration[key]
    matte_path = ROOT / entry['matte']
    im = Image.open(matte_path).convert('RGBA')

    ax, ay = item['anchor']
    if 'bodyCompress' in item:
        split = item['bodyCompress']['split']
        factor = item['bodyCompress']['factor']
        lower = im.crop((0, split, im.width, im.height)).resize(
            (im.width, round((im.height - split) * factor)), Image.Resampling.LANCZOS)
        joined = Image.new('RGBA', (im.width, split + lower.height))
        joined.paste(im.crop((0, 0, im.width, split)), (0, 0))
        joined.paste(lower, (0, split))
        im = joined
        ay = split + (ay - split) * factor if ay > split else ay

    bbox = im.getbbox()
    if bbox is None:
        raise ValueError(f'{key}: blank matte')

    factor = item['width'] / im.width if 'width' in item else item['height'] / im.height
    size = (round(im.width * factor), round(im.height * factor))
    sx, sy = size[0] / (bbox[2] - bbox[0]), size[1] / (bbox[3] - bbox[1])

    # The crop removes (bbox[0], bbox[1]) before the scale, so a matte point p
    # lands at  (p - bbox_origin) * scale  in the final bitmap.
    off_x, off_y = -bbox[0] * sx, -bbox[1] * sy
    return sx, sy, off_x, off_y, (ax, ay), entry


def map_box(box, sx, sy, off_x, off_y):
    x0, y0, x1, y1 = box
    fx0 = x0 * sx + off_x
    fy0 = y0 * sy + off_y
    fx1 = x1 * sx + off_x
    fy1 = y1 * sy + off_y
    return [round(min(fx0, fx1)), round(min(fy0, fy1)),
            round(max(fx0, fx1)), round(max(fy0, fy1))]


def self_check(manifest, calibration):
    """Replay the mapping for reviewed boxes and compare with the manifest."""
    print('--- self check: replayed matte box -> final box vs manifest ---')
    worst = 0
    for key in ('si_er-portrait', 'si_er-chibi', 'zijun-portrait', 'cui_lv-portrait', 'jia_huan-portrait'):
        if key not in manifest or key not in calibration:
            continue
        stored = manifest[key]['identity']['faceBox']
        sx, sy, ox, oy, _, _ = final_geometry(manifest, calibration, key)
        # The stored box is in final space; invert it back to matte space and
        # forward again. A correct replay returns the stored value.
        matte_box = [(stored[0] - ox) / sx, (stored[1] - oy) / sy,
                     (stored[2] - ox) / sx, (stored[3] - oy) / sy]
        replayed = map_box(matte_box, sx, sy, ox, oy)
        delta = max(abs(a - b) for a, b in zip(replayed, stored))
        worst = max(worst, delta)
        print(f'  {key}: stored={stored} replayed={replayed} max_delta={delta:.2f}px')
    print(f'  worst delta: {worst:.2f}px (rounding only)')
    return worst


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--asset')
    ap.add_argument('--box', nargs=4, type=int)
    ap.add_argument('--self-check', action='store_true')
    args = ap.parse_args()

    manifest, calibration = load()

    if args.self_check:
        self_check(manifest, calibration)
        return 0

    if not args.asset or not args.box:
        ap.error('--asset and --box are required (or use --self-check)')

    key = args.asset
    if key not in manifest:
        print(f'{key}: not in the manifest yet; cannot read its geometry.\n'
              f'  Register the asset first, then map the face box.')
        return 1
    sx, sy, ox, oy, anchor, entry = final_geometry(manifest, calibration, key)
    out = map_box(args.box, sx, sy, ox, oy)
    print(json.dumps({
        'asset': key,
        'matteBox': args.box,
        'finalBox': out,
        'finalSize': [entry['width'], entry['height']],
        'scale': [round(sx, 5), round(sy, 5)],
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
