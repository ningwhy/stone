#!/usr/bin/env python3
"""Bring hand-authored maps up to the stage contract the generators already follow.

`c6_wangchui` and `rongguo-entry` were laid out by one-off scripts before the camera budget
existed: 王夫人院 stands 733 px tall, 贾母正房 888 px, so their ridges leave the frame before
their eaves ever enter it. The rule every other map obeys is simple — nothing painted may
stand taller than the stage can show — and this applies it in place, idempotently:

  * any Art taller than MAX stands scaled down about its own foot, so it keeps standing
    where it was placed and only gets shorter;
  * a shell (`visibility=exterior`) with an `interiorZone` has its foot moved to the south
    edge of the floor it roofs, so the roof lifts on the eave and not through the middle of
    the room.

Usage: python3 scripts/refit_stage_assets.py [--dry-run] [map ...]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX = 470  # a hall may stand this tall and still show eave, door and a slice of ridge
# A gate is meant to be the tallest thing in the courtyard — 垂花门 at 631 px is a doorway you
# look up at, not a mistake. Only the mass of a roof is capped.
UNCAPPED = ('门', '影壁', 'colonnade', 'arch')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    dry = '--dry-run' in sys.argv
    keys = args or ['c6_wangchui', 'rongguo-entry']

    for key in keys:
        path = ROOT / f'maps/{key}.tmj'
        if not path.exists():
            print(f'{key}: no such map')
            continue
        d = json.loads(path.read_text())
        layers = {l['name']: l for l in d['layers']}
        zones = {}
        for o in (layers.get('PlanZones') or {}).get('objects', []):
            zones[o['name'].split(' ')[0]] = (o['x'] / 64, o['y'] / 64,
                                             o['width'] / 64, o['height'] / 64)
        changed = []
        for o in (layers.get('Art') or {}).get('objects', []):
            props = {p['name']: p['value'] for p in o.get('properties') or []}
            h = o['height']
            if h > MAX and not any(word in o['name'] for word in UNCAPPED):
                k = MAX / h
                o['width'], o['height'] = o['width'] * k, h * k
                changed.append(f"{o['name']} {h:.0f}→{MAX}")
            elif h > MAX:
                changed.append(f"{o['name']} {h:.0f} kept (gate, not a roof)")
            zone = props.get('interiorZone')
            if props.get('visibility') == 'exterior' and zone in zones:
                zc, zr, zw, zh = zones[zone]
                # The stored pair is inverted (`X = sy + sx/2, Y = sy - sx/2`); rebuild it
                # from the cell the roof should stand on.
                sx, sy = o['x'] - o['y'], (o['x'] + o['y']) / 2
                col = sx / 64 + sy / 32 - 1  # invert x=(c-r)*64, y=(c+r+1)*32
                row = sy / 32 - 1 - col
                if zc <= col < zc + zw and zr <= row < zr + zh and row != zr + zh - .5:
                    row = zr + zh - .5
                    nx, ny = (col - row) * 64, (row + 1) * 32
                    o['x'], o['y'] = ny + nx / 2, ny - nx / 2
                    changed.append(f"{o['name']} foot→row {row:.1f}")
        if changed and not dry:
            path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
        print(f"{key}: {'; '.join(changed) if changed else 'already within budget'}")


if __name__ == '__main__':
    main()
