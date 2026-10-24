#!/usr/bin/env python3
"""Write the authoritative facing table for the painted cast.

The facing decides whether a portrait or a chibi sprite is mirrored when it
is shown, so it has to come from somewhere that can be defended.

Five ways of reading it automatically were tried on this art — dark-mass
centroid, eye-pair midpoint, mouth blob, nose blob, and Apple's Vision yaw
model — and they disagreed with each other, so none of them was trusted on
its own. What did survive is the *geometry* of Vision's semantic landmarks:
where the nose tip sits relative to the midpoint of the two eyes, and where
the centre of the mouth sits. Two things make that reading trustworthy:

  * the sign follows from construction. The region called leftEye really does
    sit to the left of rightEye on all 76 heads, so a nose on the image's
    right means the face points to the image's right. No reference image and
    no hand-made label is involved.
  * the landmarks land where they claim to. Drawing the fit back onto the
    picture (scripts/facing_overlay.swift, scripts/facing_rules.swift) shows
    the nose rule passing through the nose and the eye marks on the eyes, on
    every portrait checked.

Two further checks back it up: flipping a picture flips the reading on all 38
portraits, and the nose and the mouth — opposite ends of the face — agree on
55 of the 61 heads where both could be measured.

The chibi sprites are far too small for a face model: upscaled, the landmarks
come back with offsets of two eye-spans and more, which is not a measurement.
The chibis are therefore given the same facing as their portrait, which is
the character's painted identity and is what the two were generated from.
"""
import json
import os
import sys

try:
    from PIL import Image
except ImportError:
    print('Pillow is required', file=sys.stderr)
    raise SystemExit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'public', 'assets', 'rongguo', 'manifest.json')
MEASURED = os.path.join(ROOT, 'art', 'identity', 'facing-measured.json')
OUT = os.path.join(ROOT, 'design', 'character-facing.json')


def main():
    with open(MANIFEST, encoding='utf-8') as fh:
        assets = json.load(fh)['assets']
    with open(MEASURED, encoding='utf-8') as fh:
        measured = json.load(fh)

    by_actor = {}
    for row in measured:
        if row['kind'] != 'portrait':
            continue
        by_actor[row['actor']] = row

    # Every painted character, from the cast the runtime knows about.
    import re
    story = open(os.path.join(ROOT, 'src', 'story.ts'), encoding='utf-8').read()
    cast_ids = re.findall(r'^\s{2}(\w+):\{', story, re.M)

    entries = {}
    missing = []
    for actor in cast_ids:
        row = by_actor.get(actor)
        if not row:
            # The sedan chair and any other prop have no painted head, so they
            # keep the default the runtime has always used.
            entries[actor] = {'portrait': 'left', 'chibi': 'left',
                              'evidence': {'method': 'default-no-painted-head'}}
            missing.append(actor)
            continue
        entries[actor] = {
            'portrait': row['facing'],
            'chibi': row['facing'],
            'evidence': {
                'noseOffset': row['noseOffset'],
                'mouthOffset': row['mouthOffset'],
                'method': 'vision-landmark-geometry',
            },
        }

    if missing:
        print('no painted head, defaulted to left:', ', '.join(missing), file=sys.stderr)

    out = {
        'version': 1,
        'note': ('Facing of each painted head, as painted. A portrait or chibi is mirrored '
                 'when the side it is shown on disagrees with this. Read from the geometry of '
                 'Apple Vision semantic landmarks: the nose tip and the mouth centre are '
                 'measured against the midpoint of the two eyes, and the sign follows from the '
                 'naming check rather than from any hand-made label.'),
        'actors': entries,
    }
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write('\n')

    right = sum(1 for v in entries.values() if v['portrait'] == 'right')
    print(f'wrote {os.path.relpath(OUT, ROOT)}: {len(entries)} actors, '
          f'{right} facing right, {len(entries) - right} facing left')


if __name__ == '__main__':
    main()
