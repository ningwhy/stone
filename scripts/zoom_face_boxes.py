#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render enlarged, grid-annotated head crops so face boxes can be read by eye.

`scripts/inspect_face_boxes.py` only *proposes* a box: the skin-tone mask
latches onto hair, a collar or a scarf often enough that the proposal has to
be checked by eye before it is trusted. This script renders the top of each
asset at magnification with a pixel grid drawn on it, so the exact box that
sits on the face can be read off the picture instead of guessed at.

Usage:
  python3 scripts/zoom_face_boxes.py <asset-key> [<asset-key> ...]
  python3 scripts/zoom_face_boxes.py --ch24
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'public', 'assets', 'rongguo', 'manifest.json')
BOXES = os.path.join(ROOT, 'art', 'identity', 'auto-face-boxes.json')
OUT = os.path.join(ROOT, 'art', 'identity', 'face-box-zoom.png')

CELL = 460
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


def head_window(im):
    """The band of the picture that can hold a head, in source pixels.

    A portrait is 600 tall and the head sits in the top fifth; a chibi is 116
    tall and the head is roughly half of it. The window is generous enough to
    hold the head whatever the painting did, but never reaches the hands.
    """
    h = im.height
    return (0, 0, im.width, max(1, int(h * 0.34)))


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
    cols = 2
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * CELL, rows * (CELL + 40)), '#e6dfd0')
    draw = ImageDraw.Draw(sheet)

    for i, key in enumerate(keys):
        asset = assets.get(key)
        if not asset:
            draw.text((i * CELL + 10, 20), f'{key}: not in manifest', fill='red', font=font)
            continue
        im = Image.open(os.path.join(ROOT, 'public', asset['image'].lstrip('/'))).convert('RGBA')
        flat = Image.new('RGBA', im.size, (236, 230, 215, 255))
        flat.alpha_composite(im)
        flat = flat.convert('RGB')
        window = head_window(im)
        crop = flat.crop(window)
        scale = max(1, min(6, (CELL - 60) // max(1, crop.width)))
        crop = crop.resize((crop.width * scale, crop.height * scale),
                           Image.Resampling.LANCZOS)
        col = i % cols
        row = i // cols
        ox = col * CELL + 10
        oy = row * (CELL + 40) + 34
        sheet.paste(crop, (ox, oy))
        # Grid every 10 source pixels, with the coordinates written along the
        # top edge, so a box can be read off in source pixels.
        for gx in range(0, im.width + 1, 10):
            px = ox + gx * scale
            draw.line((px, oy, px, oy + crop.height), fill=(120, 150, 190), width=1)
            if gx % 20 == 0:
                draw.text((px + 1, oy - 16), str(gx), fill=(40, 70, 110), font=font)
        for gy in range(0, window[3] + 1, 10):
            py = oy + gy * scale
            draw.line((ox, py, ox + crop.width, py), fill=(120, 150, 190), width=1)
            if gy % 20 == 0:
                draw.text((ox - 34, py - 8), str(gy), fill=(40, 70, 110), font=font)
        box = boxes.get(key)
        if box:
            draw.rectangle((ox + box[0] * scale, oy + box[1] * scale,
                            ox + box[2] * scale, oy + box[3] * scale),
                           outline=(220, 40, 40), width=2)
        draw.text((col * CELL + 10, row * (CELL + 40) + 8),
                  f'{key}  {im.width}x{im.height}', fill='black', font=font)

    sheet.save(OUT)
    print(f'wrote {os.path.relpath(OUT, ROOT)}  ({sheet.size[0]}x{sheet.size[1]})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
