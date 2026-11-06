#!/usr/bin/env python3
"""Measure the head-to-body proportion of every chibi bitmap.

The chibis are drawn on canvas that is cropped to the figure, so the canvas
height says nothing about the person: a figure with a small head on a long
body and a figure with a huge head on a short body both fill their canvas.
What the eye reads as "tall" is exactly this ratio, and the map renders every
chibi at the same scale, so the difference is visible on stage.

The head is the widest part of a chibi. The neck is the narrowest point
between the head and the body, so the head bottom is the first row after the
top whose width drops well below the head's own width.

Usage:
    python3 scripts/measure_chibi_proportion.py            # every chibi
    python3 scripts/measure_chibi_proportion.py liu_lao ban_er
"""
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = json.load(open(os.path.join(ROOT, 'public/assets/rongguo/manifest.json'), encoding='utf-8'))['assets']

# The head is a chibi's widest part. The neck sits well below it, but the
# hem of a robe can be as wide as the head, so the neck is found as the
# narrowest row inside the upper half rather than the first row that is
# merely narrower than the head.
NECK_SEARCH_BOTTOM = 0.72
NECK_WIDTH_RATIO = 0.62


def profile(path):
    """Per-row opaque pixel counts, top to bottom."""
    im = Image.open(path).convert('RGBA')
    alpha = np.asarray(im.getchannel('A'))
    mask = alpha >= 128
    widths = mask.sum(axis=1)
    ys = np.where(mask)[0]
    top, bottom = int(ys[0]), int(ys[-1])
    return widths, top, bottom


def head_ratio(path):
    widths, top, bottom = profile(path)
    full = bottom - top + 1
    head_width = int(widths[top:bottom + 1].max())
    limit = int(bottom - (bottom - top) * NECK_SEARCH_BOTTOM)
    neck = None
    for y in range(top, limit):
        if int(widths[y]) <= head_width * NECK_WIDTH_RATIO:
            neck = y
            break
    if neck is None or neck <= top:
        return None
    head = neck - top
    return dict(head=head, full=full, ratio=head / full, neck=neck - top)


def main():
    wanted = set(sys.argv[1:])
    rows = []
    for key, entry in MANIFEST.items():
        if not key.endswith('-chibi'):
            continue
        if wanted and key not in wanted:
            continue
        path = os.path.join(ROOT, 'public', entry['image'].lstrip('/'))
        if not os.path.exists(path):
            continue
        measured = head_ratio(path)
        if not measured:
            continue
        rows.append((key, measured))

    rows.sort(key=lambda r: r[1]['ratio'])
    print(f'{"asset":28} {"头高":>5} {"全高":>5} {"头占比":>7}  头身比')
    for key, m in rows:
        ratio = m['ratio']
        heads = f'≈{1 / ratio:.1f}头身' if ratio > 0 else 'n/a'
        print(f'{key:28} {m["head"]:>5} {m["full"]:>5} {ratio:>7.3f}  {heads}')

    if rows:
        ratios = [r[1]['ratio'] for r in rows]
        print()
        print(f'头占比范围 {min(ratios):.3f} ~ {max(ratios):.3f}，'
              f'极差 {max(ratios) - min(ratios):.3f}（{max(ratios) / min(ratios):.2f} 倍）')


if __name__ == '__main__':
    main()
