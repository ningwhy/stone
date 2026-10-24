#!/usr/bin/env python3
"""Measure the painted facing of every head and cross-check the two features.

Vision's semantic landmarks give two independent readings of the head turn:
where the nose tip sits relative to the eyes, and where the centre of the
mouth sits. They come from opposite ends of the face, so if they agree the
reading is a measurement rather than a guess.

The sign needs no reference image. Two things have to hold: the region called
leftEye really does sit left of rightEye, and the landmarks land on the
features they claim to. The first is checked on every face here; the second
is checked by drawing the fit back onto the picture with
scripts/facing_overlay.swift, and by scripts/facing_lines.swift, which puts
a vertical rule through the nose tip and through the eye midpoint so the
offset can be read straight off the image.

The chibi sprites are about fifty pixels wide, below what the detector
accepts, so they are upscaled before they are measured.
"""
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
SCRIPT = os.path.join(ROOT, 'scripts', 'facing_vision.swift')
OUT = os.path.join(ROOT, 'art', 'identity', 'facing-measured.json')
CACHE = os.path.join(ROOT, 'artifacts', 'facing-measure-cache')

# Facing read by eye from the review sheets, kept only as a third opinion.
# Several of these turned out to be wrong when the geometric measurement was
# checked against a rule drawn on the picture, which is exactly why the
# measurement does not take its sign from them.
BY_EYE = {
    'feng': 'right', 'jiaoxing': 'left', 'tanchun': 'right', 'menzi': 'right',
    'wang': 'right', 'nurse_wang': 'right', 'grandmother': 'right', 'xueyima': 'right',
    'maid': 'right', 'xichun': 'right', 'xiren': 'right', 'guide': 'right',
    'yingchun': 'right', 'huoqi': 'right', 'messenger': 'right', 'yingge': 'right',
    'xing': 'right',
}


def load(entry):
    path = os.path.join(ROOT, 'public', entry['image'].lstrip('/'))
    if not os.path.exists(path):
        path = path.replace('.png', '.webp')
    return Image.open(path).convert('RGBA')


def main():
    with open(MANIFEST, encoding='utf-8') as fh:
        assets = json.load(fh)['assets']

    keys = [k for k in sorted(assets)
            if (k.endswith('-portrait') or k.endswith('-chibi')) and '-portrait-' not in k]

    os.makedirs(CACHE, exist_ok=True)
    prepared = []
    for key in keys:
        image = load(assets[key])
        # The detector needs a face large enough to fit a model. The chibi
        # sprites are about fifty pixels wide, so they are scaled well past
        # their natural size; the measurement only needs the shape.
        if max(image.size) < 900:
            scale = 900 / max(image.size)
            image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))),
                                 Image.LANCZOS)
        path = os.path.join(CACHE, key + '.png')
        image.save(path)
        prepared.append((key, path))

    result = subprocess.run(['swift', SCRIPT] + [p for _, p in prepared],
                            capture_output=True, text=True)
    measured = {}
    for ln in result.stdout.strip().split('\n'):
        if not ln:
            continue
        parts = ln.split('\t')
        if len(parts) < 4:
            continue
        measured[parts[0].split('/')[-1].replace('.png', '')] = {
            'nameCheck': parts[1],
            'nose': None if parts[2] in ('NONE', 'ERR') else float(parts[2]),
            'mouth': None if parts[3] in ('NONE', 'ERR') else float(parts[3]),
        }

    swapped = [k for k, v in measured.items() if v['nameCheck'] == 'SWAPPED']
    print(f'naming check: leftEye left of rightEye on {len(measured) - len(swapped)}/{len(measured)}'
          + (f', SWAPPED on {swapped}' if swapped else ''))

    rows = []
    agree = conflict = unresolved = 0
    print('\nfeature   nose  mouth  verdict  by-eye')
    for key in keys:
        m = measured.get(key)
        if not m or m['nose'] is None or m['mouth'] is None:
            unresolved += 1
            print(f'{key:26s} no face measured')
            continue
        by_nose = 'right' if m['nose'] > 0 else 'left'
        by_mouth = 'right' if m['mouth'] > 0 else 'left'
        ok = by_nose == by_mouth
        agree += ok
        conflict += not ok
        actor = key.replace('-portrait', '').replace('-chibi', '')
        kind = 'portrait' if key.endswith('-portrait') else 'chibi'
        eye = BY_EYE.get(actor, '-')
        mark = ''
        if eye != '-':
            mark = '  same' if eye == by_nose else '  DIFFERENT'
        rows.append({'actor': actor, 'kind': kind, 'facing': by_nose,
                     'noseOffset': round(m['nose'], 4), 'mouthOffset': round(m['mouth'], 4),
                     'confidence': round(min(abs(m['nose']), abs(m['mouth'])), 4)})
        print(f'{key:26s} {by_nose:5s} {by_mouth:6s} {"ok" if ok else "CONFLICT"}   {eye}{mark}')
    print(f'\nfeatures agree on {agree}, conflict on {conflict}, unmeasured on {unresolved}')

    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
    print('wrote', os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
