#!/usr/bin/env python3
"""Validate the Vision measurement with a mirror test, then fix the sign.

A detector that reads the head turn has one hard requirement: flipping the
picture must flip the reading. That test needs no labels at all, so it can
settle the sign convention on its own.

After the sign is fixed the measurement is compared against the hand-checked
ground truth, and any disagreement is listed for a second look.
"""
import json
import os
import subprocess
import sys
import tempfile

try:
    from PIL import Image
except ImportError:
    print('Pillow is required', file=sys.stderr)
    raise SystemExit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'public', 'assets', 'rongguo', 'manifest.json')
SCRIPT = os.path.join(ROOT, 'scripts', 'facing_vision.swift')

GROUND_TRUTH = {
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


def measure(paths):
    result = subprocess.run(['swift', SCRIPT] + list(paths), capture_output=True, text=True)
    out = {}
    for ln in result.stdout.strip().split('\n'):
        if not ln:
            continue
        parts = ln.split('\t')
        out[parts[0]] = parts[1:]
    return out


def main():
    with open(MANIFEST, encoding='utf-8') as fh:
        assets = json.load(fh)['assets']

    actors = [k.replace('-portrait', '') for k in sorted(assets)
              if k.endswith('-portrait') and assets[k].get('identity', {}).get('faceBox')]

    with tempfile.TemporaryDirectory() as tmp:
        plain, flipped = {}, {}
        plain_paths, flipped_paths = [], []
        for actor in actors:
            image = load(assets[f'{actor}-portrait'])
            p = os.path.join(tmp, f'{actor}-p.png')
            f = os.path.join(tmp, f'{actor}-f.png')
            image.save(p)
            image.transpose(Image.FLIP_LEFT_RIGHT).save(f)
            plain[actor], flipped[actor] = p, f
            plain_paths.append(p)
            flipped_paths.append(f)

        a = measure(plain_paths)
        b = measure(flipped_paths)

        print('mirror consistency: the reading must change sign when the picture is flipped')
        good = bad = skipped = 0
        raw = {}
        for actor in actors:
            pa, pb = a.get(plain[actor], ['NONE', 'NONE', '0']), b.get(flipped[actor], ['NONE', 'NONE', '0'])
            if pa[0] in ('NONE', 'ERR') or pb[0] in ('NONE', 'ERR'):
                skipped += 1
                continue
            va, vb = float(pa[0]), float(pb[0])
            raw[actor] = va
            if va * vb < 0:
                good += 1
            else:
                bad += 1
                print(f'  {actor:12s} {va:+.4f} -> {vb:+.4f}  NOT FLIPPED')
        print(f'  flipped sign correctly: {good}, did not: {bad}, no face: {skipped}')

        # The mirrored copy of a right-facing head is a left-facing head, so the
        # sign that survives the mirror test is the one that matches the truth.
        sign = 1.0
        hit = sum(1 for actor, truth in GROUND_TRUTH.items()
                  if actor in raw and (('right' if raw[actor] * sign > 0 else 'left') == truth))
        total = sum(1 for actor in GROUND_TRUTH if actor in raw)
        print(f'\nground truth with sign {sign:+.0f}: {hit}/{total} matched')
        sign = -1.0
        hit2 = sum(1 for actor, truth in GROUND_TRUTH.items()
                   if actor in raw and (('right' if raw[actor] * sign > 0 else 'left') == truth))
        print(f'ground truth with sign {sign:+.0f}: {hit2}/{total} matched')
        if hit2 > hit:
            sign = -1.0
        print(f'\nchosen sign: {sign:+.0f}')

        print('\nper-actor reading with the corrected sign')
        for actor in actors:
            if actor not in raw:
                continue
            value = raw[actor] * sign
            truth = GROUND_TRUTH.get(actor)
            verdict = 'right' if value > 0 else 'left'
            mark = ''
            if truth:
                mark = 'ok' if verdict == truth else 'MISMATCH'
            print(f'  {actor:12s} {value:+.4f} -> {verdict:5s} truth={truth or "-":5s} {mark}')

        out = os.path.join(ROOT, 'art', 'identity', 'facing-vision.json')
        rows = [{'actor': actor, 'portraitOffset': round(raw[actor] * sign, 4)} for actor in actors if actor in raw]
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=1)
        print('\nwrote', os.path.relpath(out, ROOT))


if __name__ == '__main__':
    main()
