#!/usr/bin/env python3
"""Export a review sheet of the heads whose facing could not be settled.

The measurement in scripts/facing_assets.py settles most of the cast on its
own. What is left are two groups:

  * heads the face detector could not read at all, in any crop
  * heads read from a single crop, where one reading is a thin basis for a
    decision that decides whether a sprite gets mirrored

Both are shown here, large, with the measured reading printed beside each
one, so the eye can settle what the detector could not. The result is written
to art/identity/facing-review.json and is merged into the facing table by
scripts/build_facing.py, where every hand-made reading is recorded with the
reason it was made.

Usage: python3 scripts/facing_review_sheet.py [--write]
"""
import argparse
import json
import os

try:
    from PIL import Image, ImageDraw
except ImportError:
    print('Pillow is required', file=sys.stderr)
    raise SystemExit(1)

import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'public', 'assets', 'rongguo', 'manifest.json')
MEASURED = os.path.join(ROOT, 'art', 'identity', 'facing-assets.json')
SHEET = os.path.join(ROOT, 'art', 'identity', 'facing-review-sheet.png')
OUT = os.path.join(ROOT, 'art', 'identity', 'facing-review.json')

CELL = 260
COLUMNS = 4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true',
                        help='also write the review file')
    args = parser.parse_args()

    with open(MANIFEST, encoding='utf-8') as fh:
        assets = json.load(fh)['assets']
    rows = {}
    if os.path.exists(MEASURED):
        with open(MEASURED, encoding='utf-8') as fh:
            for row in json.load(fh):
                rows[row['asset']] = row

    keys = [k for k in sorted(assets)
            if k.endswith('-portrait') or k.endswith('-chibi') or '-portrait-' in k]
    need = [k for k in keys if k not in rows or rows[k].get('votes', 0) <= 1]

    rows_out = max(1, (len(need) + COLUMNS - 1) // COLUMNS)
    sheet = Image.new('RGB', (COLUMNS * CELL, rows_out * (CELL + 40)), '#e6dfd0')
    draw = ImageDraw.Draw(sheet)

    for index, key in enumerate(need):
        entry = assets[key]
        path = os.path.join(ROOT, 'public', entry['image'].lstrip('/'))
        if not os.path.exists(path):
            path = path.replace('.png', '.webp')
        image = Image.open(path).convert('RGBA')
        box = (entry.get('identity') or {}).get('faceBox')
        if box:
            x0, y0, x1, y1 = [int(v) for v in box]
            width, height = x1 - x0, y1 - y0
            crop = image.crop((max(0, x0 - int(width * 0.7)),
                               max(0, y0 - int(height * 0.6)),
                               min(image.width, x1 + int(width * 0.7)),
                               min(image.height, y1 + int(height * 0.9))))
        else:
            crop = image.copy()
        crop.thumbnail((CELL - 20, CELL - 20), Image.LANCZOS)
        cell_x = (index % COLUMNS) * CELL
        cell_y = (index // COLUMNS) * (CELL + 40)
        backdrop = Image.new('RGB', crop.size, (243, 239, 231))
        backdrop.paste(crop, (0, 0), crop)
        sheet.paste(backdrop, (cell_x + (CELL - backdrop.width) // 2,
                               cell_y + (CELL - backdrop.height) // 2))
        reading = rows.get(key)
        if reading:
            label = f"{reading['facing']} ({reading['votes']} vote)"
        else:
            label = 'not measured'
        draw.text((cell_x + 8, cell_y + CELL + 6), key, fill='#2f3f38')
        draw.text((cell_x + 8, cell_y + CELL + 22), label, fill='#7a4a32')

    sheet.save(SHEET)
    print(f'wrote {os.path.relpath(SHEET, ROOT)} with {len(need)} heads:',
          ', '.join(need))

    if args.write:
        with open(OUT, 'w', encoding='utf-8') as fh:
            json.dump({'assets': need}, fh, ensure_ascii=False, indent=1)
        print('wrote', os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
