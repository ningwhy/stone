#!/usr/bin/env python3
"""Furnish the interior floors that the roof reveal exposes.

`central.tmj` (荣禧堂) roofs a large floor with no furnishings at all, so once
the exterior comes off the hall reads as an empty box. This adds a screen and
two tea tables on cells the story never walks over, following the exact object
convention already used by `dinner.tmj`:

  Art object      x = (col + 0.5) * 64, y = (row + 0.5) * 64, anchored bottom-centre
  ArtFootprints   x = col * 64, y = row * 64, 64 x 64 (one tile of collision)

Idempotent: an object that already exists with the same geometry is left alone.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIT = 64

# map -> [(asset, col, row, width, height)]
ADDITIONS = {
    'central': [
        ('wood-screen', 22, 11, 171, 155),
        ('tea-table',   25, 20, 104, 85),
        ('tea-table',   16, 20, 104, 85),
    ],
}


def annotate(map_id, additions):
    path = os.path.join(ROOT, 'maps', map_id + '.tmj')
    with open(path, encoding='utf-8') as fh:
        data = json.load(fh)
    art = next(l for l in data['layers'] if l['name'] == 'Art')
    foot = next(l for l in data['layers'] if l['name'] == 'ArtFootprints')
    gid_pool = max([o.get('gid', 0) for o in art['objects']] + [o.get('gid', 0) for o in foot['objects']] + [1])
    next_id = max([o.get('id', 0) for o in art['objects']] + [o.get('id', 0) for o in foot['objects']]) + 1
    changed = False
    for asset, col, row, w, h in additions:
        if any(o['name'] == asset and abs(o['x'] - (col + .5) * UNIT) < 1 and abs(o['y'] - (row + .5) * UNIT) < 1 for o in art['objects']):
            print(f'  {map_id}: {asset} at ({col},{row}) already present')
            continue
        gid_pool += 1
        art['objects'].append({
            'id': next_id, 'name': asset, 'x': (col + .5) * UNIT, 'y': (row + .5) * UNIT,
            'width': float(w), 'height': float(h), 'rotation': 0, 'visible': True,
            'gid': gid_pool, 'type': 'art',
            'properties': [
                {'name': 'asset', 'value': asset, 'type': 'string'},
                {'name': 'visibility', 'value': 'always', 'type': 'string'},
                {'name': 'depthOffset', 'value': 0, 'type': 'float'},
            ],
        })
        next_id += 1
        if not any(o['name'] == asset and abs(o['x'] - col * UNIT) < 1 and abs(o['y'] - row * UNIT) < 1 for o in foot['objects']):
            foot['objects'].append({
                'id': next_id, 'name': asset, 'x': col * UNIT, 'y': row * UNIT,
                'width': float(UNIT), 'height': float(UNIT), 'rotation': 0, 'visible': True, 'type': '',
            })
            next_id += 1
        changed = True
        print(f'  {map_id}: added {asset} at ({col},{row})')
    if changed:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write('\n')
    return changed


if __name__ == '__main__':
    todo = sys.argv[1:] or sorted(ADDITIONS)
    n = 0
    for m in todo:
        if annotate(m, ADDITIONS[m]):
            n += 1
    print(f'{len(todo)} map(s) checked, {n} rewritten')
