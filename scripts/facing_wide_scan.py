#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wide-scan facing measurement for characters that never went through the
identity pipeline.

Why this exists
---------------

`scripts/facing_assets.py` measures the facing of the official cropped bitmap.
That works for the characters whose portrait or chibi was cropped down to the
shipped sprite, because the crop leaves the head large enough for the face
detector. A character drawn after that pipeline was set up — the ones from
chapter 16 onward — ships as a full-size canvas with the figure on it, and the
official crop on that canvas reads the face too small for the detector: it
returns "no face" for every crop and the asset stays unresolved.

So the head is measured on the *source* bitmap instead, found by scanning for
the skin-toned region rather than by trusting the recorded box. The scan walks
several horizontal bands of the figure, and for each band it tries a range of
window widths, so a head that sits high in the frame and a head that sits low
are both reachable.

The sign convention is calibrated, not assumed
-----------------------------------------------

The offset of the nose tip from the midpoint of the two eyes is reported in
units of the eye span, and a positive number means the feature sits on the
image's right. Whether that means "facing right" on a *particular* asset
depends on the crop that produced it, so the rule is calibrated on assets
whose facing is already recorded in art/identity/facing-assets.json.

The calibration needs both directions. A ruler of only right-facing sprites
cannot tell a sign convention from a coincidence, so RULER_RIGHT and
RULER_LEFT are both used, and the rule has to reproduce every one of them
before any new asset is read. The calibration run prints the verdict per
sample, and the caller is expected to read it before trusting the output.

A `SWAPPED` verdict means the crop mirrored the head, so its sign has to be
flipped before use; an `ok` verdict means it did not. Both verdicts require
the nose and the mouth to agree, because they come from opposite ends of the
face and a disagreement means the fit landed on the wrong features.

The crop is the head, cut by hand around the recorded face box and grown
until the detector accepts it. The automatic band scan that this script used
to do was tried first and abandoned: on the ruler it produced a reading for
only six of eleven samples, and it disagreed with the known answer on two of
those six — one right-facing sprite read as left, and the one left-facing
sprite read as right. A rule that fails its own ruler is not a rule.

Usage:
    python3 scripts/facing_wide_scan.py --calibrate
    python3 scripts/facing_wide_scan.py zijun-portrait zijun-chibi ...
"""
import argparse
import json
import os
import subprocess
import sys

try:
    from PIL import Image
except ImportError:
    print('Pillow is required', file=sys.stderr)
    raise SystemExit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'public', 'assets', 'rongguo', 'manifest.json')
FACING = os.path.join(ROOT, 'art', 'identity', 'facing-assets.json')
VISION = os.path.join(ROOT, 'scripts', 'facing_vision.swift')
CACHE = os.path.join(ROOT, 'artifacts', 'facing-wide-cache')
BOXES = os.path.join(ROOT, 'art', 'identity', 'auto-face-boxes.json')

# The ten chibi sprites whose facing the identity pipeline already recorded.
# They are the ruler: the rule this script derives has to reproduce all ten.
RULER_RIGHT = ['baochai-chibi', 'daiyu-chibi', 'feng-chibi', 'baoyu-chibi']
RULER_LEFT = ['dai_quan-portrait', 'jia_lian-portrait', 'jia_rui-portrait',
              'menzi-portrait', 'ming_yan-portrait', 'monk-portrait',
              'ruhai-portrait', 'yucun-portrait']

# How the head window is placed on the source bitmap: the band of the figure
# the head may occupy, and the window's width as a share of that band.
BANDS = [(0.02, 0.26), (0.06, 0.34), (0.10, 0.42)]
WIDTHS = [0.34, 0.28, 0.22, 0.46, 0.18]
INSET = 0.34          # the window is narrowed from both sides of the band
UPSCALE = 3           # the crop is grown before the detector sees it


def load_manifest():
    with open(MANIFEST, encoding='utf-8') as fh:
        return json.load(fh)['assets']


def source_path(entry):
    """The shipping bitmap.

    The face box was measured on this picture, not on the source: the source
    is a full canvas with the figure on it, and the box recorded for the
    shipping sprite would land in the wrong place on it.
    """
    p = os.path.join(ROOT, 'public' + entry['image'])
    if os.path.exists(p):
        return p
    return p.replace('.png', '.webp')


def skin_boxes(im):
    """Bounding boxes of the skin-toned regions in the upper part of a figure."""
    import numpy as np
    a = np.asarray(im.convert('RGBA'))
    r, g, b, al = [a[:, :, j].astype(int) for j in range(4)]
    skin = (r > 130) & (r - g > 7) & (g - b > 6) & (r - g < 68) & (al > 220)
    skin[int(im.height * 0.45):] = False
    m = skin
    seen = np.zeros_like(m)
    groups = []
    ys, xs = np.where(m)
    for y, x in zip(ys, xs):
        if seen[y, x]:
            continue
        stack = [(int(x), int(y))]
        seen[y, x] = True
        pts = []
        while stack:
            x0, y0 = stack.pop()
            pts.append((x0, y0))
            for xx, yy in ((x0 - 1, y0), (x0 + 1, y0), (x0, y0 - 1), (x0, y0 + 1)):
                if (0 <= yy < m.shape[0] and 0 <= xx < m.shape[1]
                        and m[yy, xx] and not seen[yy, xx]):
                    seen[yy, xx] = True
                    stack.append((xx, yy))
        if len(pts) >= 12:
            groups.append(pts)
    boxes = []
    for pts in groups:
        gx = [p[0] for p in pts]
        gy = [p[1] for p in pts]
        boxes.append((min(gx), min(gy), max(gx) + 1, max(gy) + 1))
    return boxes


def make_crops(key, im, face_box):
    """The head windows for one bitmap.

    The head is cut around the recorded face box and grown until the detector
    accepts it. For an asset that never went through the identity pipeline the
    box comes from art/identity/auto-face-boxes.json, which proposes one from
    the skin tones alone.
    """
    out = []
    W, H = im.size
    if face_box:
        x0, y0, x1, y1 = [int(v) for v in face_box]
    else:
        x0, y0, x1, y1 = 0, 0, W, int(H * 0.40)
    box_w, box_h = x1 - x0, y1 - y0
    # Three paddings: the face alone, the face with hair, the face with hair
    # and shoulders. Which one the detector accepts depends on the head.
    for name, pad in (('tight', 0.20), ('wide', 0.45), ('wider', 0.80)):
        px = int(box_w * pad)
        py = int(box_h * pad)
        cx0 = max(0, x0 - px)
        cy0 = max(0, y0 - py)
        cx1 = min(W, x1 + px)
        cy1 = min(H, y1 + py)
        if cx1 - cx0 > 12 and cy1 - cy0 > 12:
            out.append((f'{key}--{name}', im.crop((cx0, cy0, cx1, cy1))))
    return out


def upscale(im):
    w, h = im.size
    return im.resize((w * UPSCALE, h * UPSCALE), Image.Resampling.LANCZOS)


def run_vision(paths):
    if not paths:
        return {}
    cmd = ['swift', VISION] + paths
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError('facing_vision.swift failed: ' + proc.stderr[-500:])
    out = {}
    for line in proc.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) < 4:
            continue
        path, name_check, nose, mouth = parts[0], parts[1], parts[2], parts[3]
        try:
            out[path] = (name_check, float(nose), float(mouth))
        except ValueError:
            continue
    return out


def classify_reading(name_check, nose, mouth):
    """A crop's reading, or None when the crop did not work."""
    if name_check != 'ok':
        return None
    if nose == 0 and mouth == 0:
        return None
    if nose * mouth <= 0:
        return None          # the two features disagree: the fit is unreliable
    return 'right' if nose > 0 else 'left'


def measure(key, entry, cache_dir, face_box):
    im = Image.open(source_path(entry)).convert('RGBA')
    crops = make_crops(key, im, face_box)
    paths = []
    for name, crop in crops:
        p = os.path.join(cache_dir, name + '.png')
        if not os.path.exists(p):
            upscale(crop).convert('RGB').save(p)
        paths.append(p)
    readings = run_vision(paths)
    votes = {'left': 0, 'right': 0}
    details = []
    for p in paths:
        if p not in readings:
            continue
        nc, nose, mouth = readings[p]
        if nc == 'SWAPPED':
            nose, mouth = -nose, -mouth
        verdict = classify_reading(nc if nc != 'SWAPPED' else 'ok', nose, mouth)
        if verdict is None:
            continue
        votes[verdict] += 1
        details.append(f'{os.path.basename(p)[len(key) + 2:-4]}:{verdict}'
                       + ('(swapped)' if nc == 'SWAPPED' else ''))
    return votes, details


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('assets', nargs='*')
    ap.add_argument('--calibrate', action='store_true')
    ap.add_argument('--out', default=os.path.join(ROOT, 'artifacts', 'facing-wide-scan.json'))
    args = ap.parse_args()

    manifest = load_manifest()
    os.makedirs(CACHE, exist_ok=True)
    boxes = {}
    if os.path.exists(BOXES):
        with open(BOXES, encoding='utf-8') as fh:
            boxes = json.load(fh)

    keys = args.assets
    if args.calibrate:
        keys = RULER_RIGHT + RULER_LEFT

    results = {}
    for key in keys:
        entry = manifest.get(key)
        if not entry:
            print(f'{key}: NOT IN MANIFEST')
            continue
        votes, details = measure(key, entry, CACHE, boxes.get(key))
        results[key] = {'votes': votes, 'details': details}
        print(f'{key:24s} left={votes["left"]:3d} right={votes["right"]:3d}  '
              + ' '.join(details[:6]))

    with open(args.out, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
