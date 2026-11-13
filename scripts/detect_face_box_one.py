#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Propose a face box for ONE bitmap that is not in the manifest yet.

Why this exists
---------------
`scripts/inspect_face_boxes.py` reads the asset list straight out of
`public/assets/rongguo/manifest.json`, so it cannot be used for a character
whose bitmaps are not registered yet — but the face box has to exist *before*
the manifest entry can be written (`rebuild_new_character_manifest.py` reads
it from `art/identity/auto-face-boxes.json`). Chicken and egg.

So this script runs the identical detection on a single file: the same skin
mask, the same lower-half cut, the same connected-component pass, the same
"the face has to sit in the upper part of the picture" rule. It differs only
in that it takes a path on the command line instead of walking the manifest.

That upper-region rule is the whole point. The skin-tone mask happily latches
onto a pale beige apron (second chapter-21, Cui Lv) and reports a box across
the waist; requiring the component to live in the top third of the bitmap
rejects that and keeps the real face. The result still has to be checked by
eye afterwards — the automatic detector is a proposal, not a verdict.

Usage:
  python3 scripts/detect_face_box_one.py art/matted/jia_lan-portrait_s10234080-sam.png
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def detect(path: Path):
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im)
    r, g, b, al = [a[:, :, j].astype(int) for j in range(4)]
    skin = (r > 130) & (r - g > 7) & (g - b > 6) & (r - g < 68) & (al > 220)
    skin[int(im.height * .52):] = False

    scale = 1 if im.height < 200 else 3
    m = np.asarray(Image.fromarray(skin.astype('uint8') * 255)
                   .resize((im.width // scale, im.height // scale))) > 100
    seen = np.zeros_like(m)
    groups = []
    for y, x in zip(*np.where(m)):
        if seen[y, x]:
            continue
        q = [(int(x), int(y))]
        seen[y, x] = True
        pts = []
        while q:
            x0, y0 = q.pop()
            pts.append((x0, y0))
            for xx, yy in ((x0 - 1, y0), (x0 + 1, y0), (x0, y0 - 1), (x0, y0 + 1)):
                if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    q.append((xx, yy))
        if (len(pts) > max(6, im.width * im.height / scale ** 2 * .0009)
                and min(p[1] for p in pts) * scale < im.height * (.34 if scale == 1 else .20)):
            groups.append(pts)

    if not groups:
        raise ValueError(f'{path.name}: no face candidate found')
    group = max(groups, key=len)
    xs = [p[0] * scale for p in group]
    ys = [p[1] * scale for p in group]
    return [min(xs), min(ys), max(xs) + scale, max(ys) + scale], im


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    if not path.is_absolute():
        path = ROOT / path
    box, im = detect(path)
    print(json.dumps({'file': path.name, 'size': list(im.size), 'faceBox': box}))

    shown = im.copy()
    ImageDraw.Draw(shown).rectangle(box, outline='red', width=2)
    out = ROOT / 'art/identity' / f'face-box-{path.stem}.png'
    out.parent.mkdir(exist_ok=True)
    shown.thumbnail((300, 300))
    shown.save(out)
    print(f'wrote {out.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
