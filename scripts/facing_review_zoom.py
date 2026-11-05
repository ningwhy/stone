#!/usr/bin/env python3
"""Render enlarged head crops for the assets whose facing is still undecided.

The detector reads most of the cast on its own. The heads it cannot read are
settled by eye, and the eye is only trustworthy if the picture it looks at is
the same picture the detector read: the final asset in the manifest, not the
raw generation, and the same crop box the detector was pointed at.

So this script takes the head box that scripts/inspect_face_boxes.py proposed,
crops it out of the manifest asset, blows it up, and draws a vertical line
through the box's horizontal centre. A face that points to the image's right
has its nose and mouth to the right of that line.

Usage: python3 scripts/facing_review_zoom.py <asset-key> [<asset-key> ...]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'public', 'assets', 'rongguo', 'manifest.json')
BOXES = os.path.join(ROOT, 'art', 'identity', 'auto-face-boxes.json')
OUT = os.path.join(ROOT, 'art', 'identity', 'facing-review-zoom.png')

CELL = 400
PAD = 8


def load_font(size):
    for path in ('/System/Library/Fonts/STHeiti Light.ttc',
                 '/System/Library/Fonts/PingFang.ttc'):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def main():
    keys = sys.argv[1:]
    if not keys:
        print('give at least one asset key', file=sys.stderr)
        return 1
    with open(MANIFEST, encoding='utf-8') as fh:
        assets = json.load(fh)['assets']
    with open(BOXES, encoding='utf-8') as fh:
        boxes = json.load(fh)

    font = load_font(19)
    cols = len(keys)
    sheet = Image.new('RGB', (cols * CELL, CELL + 54), '#e6dfd0')
    draw = ImageDraw.Draw(sheet)

    for i, key in enumerate(keys):
        asset = assets.get(key)
        if not asset:
            draw.text((i * CELL + 10, 20), f'{key}: not in manifest', fill='red', font=font)
            continue
        # The manifest stores a site-absolute path, e.g. /assets/rongguo/x.png;
        # it is served out of public/.
        image = Image.open(os.path.join(ROOT, 'public', asset['image'].lstrip('/'))).convert('RGBA')
        flat = Image.new('RGBA', image.size, '#f2ead9')
        flat.alpha_composite(image)
        flat = flat.convert('RGB')

        bx, by, bw, bh = boxes[key]
        x0 = max(0, bx - PAD)
        y0 = max(0, by - PAD)
        x1 = min(flat.width, bx + bw + PAD)
        y1 = min(flat.height, by + bh + PAD)
        crop = flat.crop((x0, y0, x1, y1))

        scale = min((CELL - 20) / crop.width, (CELL - 20) / crop.height)
        crop = crop.resize((max(1, int(crop.width * scale)),
                            max(1, int(crop.height * scale))), Image.LANCZOS)
        px = i * CELL + (CELL - crop.width) // 2
        py = 10
        sheet.paste(crop, (px, py))

        centre = px + int(((bx + bw / 2) - x0) * scale)
        draw.line([(centre, py), (centre, py + crop.height)], fill=(220, 0, 0), width=2)
        draw.rectangle([px, py, px + crop.width - 1, py + crop.height - 1],
                       outline=(120, 120, 140))
        draw.text((i * CELL + 10, CELL + 12), key, fill='black', font=font)
        draw.text((i * CELL + 10, CELL + 36), 'red line = head centre',
                  fill=(180, 0, 0), font=font)

    sheet.save(OUT)
    print(f'wrote {OUT} ({sheet.size[0]}x{sheet.size[1]})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
