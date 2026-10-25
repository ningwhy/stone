#!/usr/bin/env python3
"""Write the authoritative facing table for the painted cast, keyed by asset.

The facing decides whether a portrait or a chibi sprite is mirrored when it
is shown, so it has to come from somewhere that can be defended, and it has to
be known for every painted bitmap — not for a character as a whole.

Why the table is keyed by asset and not by character
----------------------------------------------------

A character is not one picture. It is a portrait, a chibi sprite, and now a
set of portrait emotion variants, each a separate bitmap that was painted
separately. The emotion variants were repainted by an image model, and they do
not all come out facing the same way: the same grandmother faces one way in
the neutral portrait and another in the sad variant. The chibi sprites were
painted as their own set and are not simply the portrait at a smaller size.
So one reading per character was never enough, and the earlier table — which
gave the chibi the same facing as the portrait by assumption — was wrong
wherever the two disagree.

How the facing is read
----------------------

The geometry of Apple Vision's semantic landmarks, the reading this cast has
used since the first pass:

  * the nose tip's horizontal offset from the midpoint of the two eyes
  * the centre of the mouth's offset from the same midpoint

Both are reported in units of the eye span. A positive offset means the
feature sits on the image's right, so the face points to the image's right.
The sign follows from construction, not from a hand-made label: the region
Vision calls leftEye really does sit to the left of rightEye, and that is
checked on every face (the naming check). The landmarks land where they
claim — scripts/facing_audit.swift draws the fit back onto the picture.

scripts/facing_assets.py does the measuring and writes
art/identity/facing-assets.json. Each asset is measured through several
crops, because a chibi sprite is fifty pixels wide and which crop lets the
detector find the face depends on the sprite. A crop that yields no face, or
whose two features disagree, or whose naming check fails, is not a vote.

What the eye settled
---------------------

Some heads the detector could not read in any crop, and some it read from a
single crop — one reading is a thin basis for a decision that decides
whether a sprite gets mirrored. Those were read by eye from the review sheet
art/identity/facing-review-sheet.png and are recorded in REVIEWED below with
the reason, so the table stays reproducible and the hand-made readings stay
visible.

Usage: python3 scripts/build_facing.py
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'public', 'assets', 'rongguo', 'manifest.json')
MEASURED = os.path.join(ROOT, 'art', 'identity', 'facing-assets.json')
OUT = os.path.join(ROOT, 'design', 'character-facing.json')

# Heads the detector could not settle, read by eye from the review sheet.
# Every entry names the reason it was read by hand, so a later measurement
# that disagrees with the eye can be investigated rather than silently
# overwritten.
REVIEWED = {
    # The neutral grandmother portrait: the detector fits the face but puts
    # the nose and the mouth on opposite sides of the eye midpoint in every
    # crop. The painted head turns to the image's left.
    'grandmother-portrait': ('left', 'nose and mouth disagree in every crop; '
                                     'painted head read by eye, it turns left'),
    'grandmother-portrait-angry': ('right', 'detector reads no face in any crop; '
                                          'painted head read by eye, it turns right'),
    'grandmother-portrait-sad': ('left', 'detector reads no face in any crop; '
                                       'painted head read by eye, it turns left'),
    'grandmother-portrait-surprise': ('right', 'detector reads no face in any crop; '
                                             'painted head read by eye, it turns right'),
    'grandmother-portrait-joy': ('right', 'the only crop that yields a face has '
                                        'its nose and mouth disagree; the painted '
                                        'head read by eye, it turns right'),
    'leng-portrait': ('right', 'detector reads no face in any crop; painted head '
                               'read by eye, it turns right'),
    'nurse_li-portrait': ('left', 'detector reads no face in any crop; painted head '
                                  'read by eye, it turns left'),
    'xuepan-portrait': ('right', 'detector reads no face in any crop; painted head '
                                'read by eye, it turns right'),
    'zheng-portrait': ('left', 'detector reads no face in any crop; painted head '
                              'read by eye, it turns left'),
    'liwan-chibi': ('right', 'detector reads no face in any crop; painted head '
                             'read by eye, it turns right'),
    'nurse_wang-chibi': ('right', 'detector reads no face in any crop; painted head '
                                 'read by eye, it turns right'),
    'plaintiff-chibi': ('right', 'detector reads no face in any crop; painted head '
                                 'read by eye, the lowered head still turns right'),
    'yinglian-chibi': ('right', 'detector reads no face in any crop; painted head '
                                'read by eye, it turns right'),
    'zhang-chibi': ('right', 'detector reads no face in any crop; painted head '
                             'read by eye, it turns right'),
    'xiren-chibi': ('right', 'the only crop that yielded a reading failed the '
                             'naming check, so its sign means nothing; the painted '
                             'head read by eye, it turns right'),
    # Heads read from a single crop. The eye confirms each one, and the
    # confirmation is what makes one measurement enough here.
    'baoyu-chibi': ('right', 'single crop read; confirmed by eye'),
    'feng-chibi': ('right', 'single crop read; confirmed by eye'),
    'kongkong-chibi': ('right', 'single crop read; confirmed by eye'),
    'maid-chibi': ('right', 'single crop read; confirmed by eye'),
    'messenger-chibi': ('right', 'single crop read; confirmed by eye'),
    'ruhai-chibi': ('right', 'single crop read; confirmed by eye'),
    'xichun-chibi': ('right', 'single crop read; confirmed by eye'),
    'yucun-chibi': ('right', 'single crop read; confirmed by eye'),
    'zheng-chibi': ('right', 'single crop read; confirmed by eye'),
}

# Vehicles are cast members but not a face: the sedan is carried by four bearers
# whose heads turn inward towards the chair, so the group has no single painted
# side. It keeps the left default and the runtime flips it with the direction of
# travel, which is what a symmetric load should do.
VEHICLE = {'sedan'}


def main():
    with open(MANIFEST, encoding='utf-8') as fh:
        assets = json.load(fh)['assets']
    measured = {}
    if os.path.exists(MEASURED):
        with open(MEASURED, encoding='utf-8') as fh:
            for row in json.load(fh):
                measured[row['asset']] = row

    # Every painted character, from the cast the runtime knows about.
    story = open(os.path.join(ROOT, 'src', 'story.ts'), encoding='utf-8').read()
    cast_ids = re.findall(r'^\s{2}(\w+):\{', story, re.M)

    entries = {}
    missing = []
    for actor in cast_ids:
        if actor in VEHICLE:
            entries[actor] = {'portrait': 'left', 'chibi': 'left',
                              'evidence': {'method': 'default-vehicle-group'}}
            missing.append(actor)
            continue
        for kind in ('portrait', 'chibi'):
            key = f'{actor}-{kind}'
            review = REVIEWED.get(key)
            row = measured.get(key)
            if review:
                entries.setdefault(actor, {})[kind] = review[0]
                entries[actor].setdefault('evidence', {})[kind] = {
                    'method': 'visual-review',
                    'reason': review[1],
                }
            elif row:
                entries.setdefault(actor, {})[kind] = row['facing']
                entries[actor].setdefault('evidence', {})[kind] = {
                    'noseOffset': row.get('noseOffset'),
                    'mouthOffset': row.get('mouthOffset'),
                    'votes': row.get('votes'),
                    'method': row.get('method'),
                }
            else:
                entries.setdefault(actor, {})[kind] = 'left'
                entries[actor].setdefault('evidence', {})[kind] = {
                    'method': 'default-unmeasured',
                }
                missing.append(key)

    # The emotion variants are a separate bitmap per emotion, and they get
    # their own entries, because they are repainted and do not all face the
    # same way.
    variants = {}
    for key in sorted(assets):
        if '-portrait-' not in key or key.endswith('-portrait'):
            continue
        review = REVIEWED.get(key)
        row = measured.get(key)
        if review:
            variants[key] = {'facing': review[0],
                             'evidence': {'method': 'visual-review',
                                          'reason': review[1]}}
        elif row:
            variants[key] = {'facing': row['facing'],
                             'evidence': {k: row.get(k) for k in
                                          ('noseOffset', 'mouthOffset', 'votes', 'method')}}
        else:
            variants[key] = {'facing': 'left',
                             'evidence': {'method': 'default-unmeasured'}}
            missing.append(key)

    if missing:
        print('no single painted side, defaulted to left:', ', '.join(missing),
              file=sys.stderr)

    out = {
        'version': 2,
        'note': ('Facing of every painted head, as painted, keyed by the asset that '
                 'carries it. A portrait or chibi is mirrored when the side it is '
                 'shown on disagrees with this. Read from the geometry of Apple '
                 'Vision semantic landmarks: the nose tip and the mouth centre are '
                 'measured against the midpoint of the two eyes, and the sign follows '
                 'from the naming check rather than from any hand-made label. Each '
                 'asset is measured through several crops and voted on; a crop that '
                 'yields no face, whose two features disagree, or whose naming check '
                 'fails is not a vote. Entries the detector could not settle carry '
                 '"method": "visual-review" and the reason instead. The emotion '
                 'variants live under "variants": they are repainted bitmaps and do '
                 'not all face the same way as their base portrait.'),
        'actors': entries,
        'variants': variants,
    }
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write('\n')

    portrait_right = sum(1 for v in entries.values() if v.get('portrait') == 'right')
    chibi_right = sum(1 for v in entries.values() if v.get('chibi') == 'right')
    variant_right = sum(1 for v in variants.values() if v['facing'] == 'right')
    print(f'wrote {os.path.relpath(OUT, ROOT)}: {len(entries)} actors '
          f'({portrait_right} portraits right, {chibi_right} chibis right), '
          f'{len(variants)} variants ({variant_right} right)')


if __name__ == '__main__':
    main()
