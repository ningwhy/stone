#!/usr/bin/env python3
"""Measure the painted facing of every character asset, keyed by asset id.

The runtime mirrors a portrait or a chibi sprite when the side it is shown on
disagrees with the side the head is painted facing, so the facing has to be
known for *every* painted head — not for a character as a whole. A portrait and
its emotion variants are separate bitmaps: the variants were repainted by an
image model, and the variants of one character do not all come out facing the
same way. The chibi sprites are separate bitmaps again, and they were measured
rather than assumed this time.

The measurement is the geometry of Apple Vision's semantic landmarks, the
reading that scripts/build_facing.py already established for this cast:

  * the nose tip's horizontal offset from the midpoint of the two eyes
  * the centre of the mouth's offset from the same midpoint

Both are reported in units of the eye span. A positive offset means the
feature sits on the image's right, so the face points to the image's right.
The sign needs no reference label: the region Vision calls leftEye really does
sit to the left of rightEye, and that is checked on every face here
(nameCheck). The two features come from opposite ends of the face, so when
they agree the reading is a measurement rather than a guess.

Why several crops per asset
---------------------------

A chibi sprite is about fifty pixels wide and its head is a small part of
that, which is below what the face detector accepts. Cropping the head so it
fills the frame fixes that — but a too-tight crop drops the hair and the
outline the detector needs, and a too-wide crop puts the body back into the
frame and the detector may pick a face off the collar instead. The three
crops below trade those failures against each other, and which one succeeds
depends on the sprite: a bald old man and a girl with a flowery headdress do
not fail in the same way.

So every asset is measured through several crops and the readings are voted
on. A crop that yields no face is not a disagreement, it is a crop that did
not work. Two features that disagree inside one crop (the nose says right,
the mouth says left) mark that crop as unreliable rather than as a reading.

Why the source bitmap is not the answer
---------------------------------------

art/identity/<actor>-chibi/edit-01.png is a 512px bitmap, and Vision reads a
face on most of them — but that is the wrong picture. Every chibi in this
cast had its face replaced by the identity system, and the replacement face
can face a different way from the body it was pasted onto. The painted
sprite that ships is the one the audience sees, so that is what is measured.
The source bitmap is only consulted as a last resort, and a reading taken
from it is recorded as such, because a face that was pasted on is exactly the
case where the source and the shipping sprite can differ.

Usage: python3 scripts/facing_assets.py [--refresh] [--only key ...]
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
SCRIPT = os.path.join(ROOT, 'scripts', 'facing_vision.swift')
OUT = os.path.join(ROOT, 'art', 'identity', 'facing-assets.json')
CACHE = os.path.join(ROOT, 'artifacts', 'facing-asset-cache')

# The face has to fill enough of the frame for the landmarks to land on the
# features they claim to.
MIN_FACE_SPAN = 900

# How far the head window is widened around the recorded face box, per crop.
# 'tight' is the recorded face box, 'wide' adds the hair and the outline,
# 'whole' is the entire sprite.
CROP_SHAPES = {
    'tight': (0.0, 0.0, 0.0, 0.0),
    'wide': (0.6, 0.5, 0.6, 0.7),
    'wider': (1.0, 0.8, 1.0, 1.0),
}


def classify(key: str) -> str:
    """portrait | chibi | emotion-variant, from the asset id."""
    if key.endswith('-chibi'):
        return 'chibi'
    if '-portrait-' in key:
        return 'emotion'
    return 'portrait'


def load(entry):
    path = os.path.join(ROOT, 'public', entry['image'].lstrip('/'))
    if not os.path.exists(path):
        path = path.replace('.png', '.webp')
    return Image.open(path).convert('RGBA')


def crop_variants(key: str, entry, image):
    """The bitmaps the face is measured on, as (name, image) pairs."""
    kind = classify(key)
    box = (entry.get('identity') or {}).get('faceBox')
    if not box:
        # A portrait with no recorded face box is measured whole.
        return [('whole', image)]

    x0, y0, x1, y1 = [int(v) for v in box]
    width, height = x1 - x0, y1 - y0
    variants = []
    if kind == 'chibi':
        # A chibi sprite is fifty pixels wide and its head is a small part of
        # that, below what the detector accepts. Cropping the head so it
        # fills the frame is what makes it measurable at all.
        for name, (lx, ly, rx, by) in CROP_SHAPES.items():
            cx0 = max(0, x0 - int(width * lx))
            cy0 = max(0, y0 - int(height * ly))
            cx1 = min(image.width, x1 + int(width * rx))
            cy1 = min(image.height, y1 + int(height * by))
            if cx1 <= cx0 or cy1 <= cy0:
                continue
            variants.append((name, image.crop((cx0, cy0, cx1, cy1))))
        variants.append(('whole', image))
        return variants

    # A portrait is measured whole first: the painted body tells the detector
    # what it is looking at. The face box is the fallback for the portraits
    # where the whole figure hides the face — a turned head on a dark robe,
    # or a head that is small in the frame.
    variants.append(('whole', image))
    for name, (lx, ly, rx, by) in (('tight', CROP_SHAPES['tight']),
                                   ('wide', CROP_SHAPES['wide'])):
        cx0 = max(0, x0 - int(width * lx))
        cy0 = max(0, y0 - int(height * ly))
        cx1 = min(image.width, x1 + int(width * rx))
        cy1 = min(image.height, y1 + int(height * by))
        if cx1 <= cx0 or cy1 <= cy0:
            continue
        variants.append((name, image.crop((cx0, cy0, cx1, cy1))))
    return variants


def source_bitmap(key: str):
    """The 512px source the sprite was painted from, when it exists."""
    if not key.endswith('-chibi'):
        return None
    path = os.path.join(ROOT, 'art', 'identity', key, 'edit-01.png')
    return path if os.path.exists(path) else None


def upscale(image):
    scale = MIN_FACE_SPAN / max(image.size)
    if scale <= 1:
        return image
    return image.resize((max(1, int(image.width * scale)),
                         max(1, int(image.height * scale))), Image.LANCZOS)


def run_vision(paths):
    if not paths:
        return {}
    result = subprocess.run(['swift', SCRIPT] + list(paths),
                            capture_output=True, text=True)
    readings = {}
    for ln in result.stdout.strip().split('\n'):
        if not ln:
            continue
        parts = ln.split('\t')
        if len(parts) < 4:
            continue
        readings[parts[0].split('/')[-1].replace('.png', '')] = {
            'nameCheck': parts[1],
            'nose': None if parts[2] in ('NONE', 'ERR') else float(parts[2]),
            'mouth': None if parts[3] in ('NONE', 'ERR') else float(parts[3]),
        }
    return readings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true',
                        help='re-measure even when a cached reading exists')
    parser.add_argument('--only', nargs='*', default=None,
                        help='measure only these asset keys')
    args = parser.parse_args()

    with open(MANIFEST, encoding='utf-8') as fh:
        assets = json.load(fh)['assets']

    keys = [k for k in sorted(assets)
            if k.endswith('-portrait') or k.endswith('-chibi') or '-portrait-' in k]
    if args.only:
        wanted = set(args.only)
        keys = [k for k in keys if k in wanted]

    os.makedirs(CACHE, exist_ok=True)

    # Prepare every crop of every asset.
    jobs = []       # (cache_key, path)
    asset_jobs = {}  # asset key -> [(crop name, cache key, path)]
    for key in keys:
        entry = assets[key]
        image = load(entry)
        prepared = []
        for name, crop in crop_variants(key, entry, image):
            cache_key = f'{key}--{name}'
            path = os.path.join(CACHE, cache_key + '.png')
            upscale(crop).save(path)
            prepared.append((name, cache_key, path))
            jobs.append((cache_key, path))
        src = source_bitmap(key)
        if src:
            prepared.append(('source', 'source:' + key, src))
            jobs.append(('source:' + key, src))
        asset_jobs[key] = prepared

    # Every crop of every asset is measured in one Vision pass.
    fresh = run_vision([path for _, path in jobs])

    rows = []
    summary = {'measured': 0, 'voted': 0, 'single': 0, 'unresolved': 0,
               'conflict': 0, 'fromSource': 0}
    print(f'{"asset":30s} {"kind":8s} {"votes":16s} {"facing":7s} evidence')
    for key in keys:
        votes = []
        detail = []
        for name, cache_key, path in asset_jobs[key]:
            m = fresh.get(cache_key)
            if not m or m.get('nose') is None or m.get('mouth') is None:
                continue
            if m.get('nameCheck') != 'ok':
                # The region Vision calls leftEye did not sit left of
                # rightEye, so the fit landed on something that is not a
                # face and the sign of its offsets means nothing. This crop
                # is not a vote.
                detail.append(f'{name}:misidentified')
                continue
            by_nose = 'right' if m['nose'] > 0 else 'left'
            by_mouth = 'right' if m['mouth'] > 0 else 'left'
            if by_nose != by_mouth:
                # The two features disagree inside this crop, so the crop's
                # fit is not on the features it claims. It is not a vote.
                detail.append(f'{name}:conflict')
                continue
            votes.append(by_nose)
            detail.append(f'{name}:{by_nose}')

        # The source bitmap is a last resort: the shipping sprite had its
        # face replaced, so a reading taken from the source can disagree
        # with the sprite that ships.
        source_vote = None
        if not votes:
            m = fresh.get('source:' + key)
            if m and m.get('nose') is not None and m.get('mouth') is not None \
                    and m.get('nameCheck') == 'ok':
                by_nose = 'right' if m['nose'] > 0 else 'left'
                by_mouth = 'right' if m['mouth'] > 0 else 'left'
                if by_nose == by_mouth:
                    source_vote = by_nose
                    detail.append(f'source:{by_nose}')

        if votes:
            right = votes.count('right')
            left = votes.count('left')
            facing = 'right' if right >= left else 'left'
            method = 'vision-landmark-geometry'
            summary['voted' if len(votes) > 1 else 'single'] += 1
        elif source_vote:
            facing = source_vote
            method = 'vision-landmark-geometry-on-source-bitmap'
            summary['fromSource'] += 1
        else:
            summary['unresolved'] += 1
            print(f'{key:30s} {classify(key):8s} {"-":16s} {"?":7s} no face measured')
            continue

        if len(set(votes)) > 1:
            summary['conflict'] += 1

        nose = []
        mouth = []
        for name, cache_key, path in asset_jobs[key]:
            m = fresh.get(cache_key)
            if m and m.get('nose') is not None and m.get('mouth') is not None \
                    and m.get('nameCheck') == 'ok':
                by_nose = 'right' if m['nose'] > 0 else 'left'
                by_mouth = 'right' if m['mouth'] > 0 else 'left'
                if by_nose == by_mouth:
                    nose.append(round(m['nose'], 4))
                    mouth.append(round(m['mouth'], 4))

        rows.append({
            'asset': key,
            'kind': classify(key),
            'facing': facing,
            'votes': len(votes),
            'voteDetail': detail,
            'noseOffset': max(nose, key=abs) if nose else None,
            'mouthOffset': max(mouth, key=abs) if mouth else None,
            'method': method,
        })
        summary['measured'] += 1
        print(f'{key:30s} {classify(key):8s} {str(votes):16s} {facing:7s} {method}')

    print(f'\nmeasured {summary["measured"]}, unresolved {summary["unresolved"]}, '
          f'crop-conflict {summary["conflict"]}, from source {summary["fromSource"]}')

    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)
    print('wrote', os.path.relpath(OUT, ROOT))


if __name__ == '__main__':
    main()
