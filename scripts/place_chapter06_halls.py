#!/usr/bin/env python3
"""Search the isometric placement of the two halls on the chapter-six 凤姐院 stage.

A hall sprite is anchored at its ground line and drawn upward from it, so it roofs
over the ground cells whose projected points fall inside the sprite rectangle. A
hall is placed well when it roofs over the room anchors it is supposed to cover,
does not swallow a cell somebody stands on, and leaves the second hall room to
look after itself instead of stacking on top of it.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
assets = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())['assets']
TILE_W, TILE_H = 128, 64


def project(col, row):
    return ((col - row) * TILE_W / 2, (col + row + 1) * TILE_H / 2)


def rect(asset, scale, c, r):
    """Screen rectangle of the hall dropped at (c, r)."""
    a = assets[asset]
    x = (c - r) * TILE_W / 2
    y = (c + r + 1) * TILE_H / 2
    return x - a['width'] * scale / 2, y - a['height'] * scale, x + a['width'] * scale / 2, y


def covers(asset, scale, c, r, anchor):
    left, top, right, bottom = rect(asset, scale, c, r)
    ax, ay = project(anchor[0], anchor[1])
    return left <= ax <= right and top <= ay <= bottom


def overlap(a, b):
    """Fraction of the smaller sprite's width that the two sprites share."""
    left = max(a[0], b[0]); right = min(a[2], b[2])
    if right <= left:
        return 0.0
    span = min(a[2] - a[0], b[2] - b[0])
    return (right - left) / span


wangchui = json.loads((ROOT / 'maps/c6_wangchui.tmj').read_text())
zones = {}
for o in [l for l in wangchui['layers'] if l['name'] == 'PlanZones'][0]['objects']:
    zones[o['name'].split()[0]] = (int(o['x'] / 64), int(o['y'] / 64),
                                  int(o['width'] / 64), int(o['height'] / 64))
all_anchors = {(int(o['x'] / 64 - .5), int(o['y'] / 64 - .5))
               for o in [l for l in wangchui['layers'] if l['name'] == 'Anchors'][0]['objects']}

A2 = zones['A2']
zc, zr, zw, zh = A2
print('A2 室内地坪: col %d..%d  row %d..%d' % (zc, zc + zw, zr, zr + zh))
print('锚点:', sorted(all_anchors))
print()

# The rooms the two halls are responsible for. main-hall roofs the hall and the
# 凤姐上房 (the room the audience happens in), rongxi-hall roofs the east room.
SCALES = [0.62, 0.66, 0.7, 0.74, 0.78, 0.82]

main_opts = []
for scale in SCALES:
    for r in range(zr, zr + zh):
        for c in range(zc, zc + zw):
            if (c, r) in all_anchors:
                continue
            if not (covers('main-hall', scale, c, r, (21, 6)) and covers('main-hall', scale, c, r, (20, 3))):
                continue
            main_opts.append((scale, c, r))
rongxi_opts = []
for scale in SCALES:
    for r in range(zr, zr + zh):
        for c in range(zc, zc + zw):
            if (c, r) in all_anchors:
                continue
            if not covers('rongxi-hall', scale, c, r, (26, 6)):
                continue
            rongxi_opts.append((scale, c, r))

print(f'main-hall 候选 {len(main_opts)}，rongxi-hall 候选 {len(rongxi_opts)}')
print()

# Pick the pair that sits closest to the rooms it roofs while barely touching.
pairs = []
for ms, mc, mr in main_opts:
    mrect = rect('main-hall', ms, mc, mr)
    for rs, rc, rr in rongxi_opts:
        rrect = rect('rongxi-hall', rs, rc, rr)
        ov = overlap(mrect, rrect)
        if ov > 0.45:
            continue
        # distance from each hall's ground point to the room it must look like
        dm = max(abs(mc - 21), abs(mr - 6)) + max(abs(mc - 20), abs(mr - 3))
        dr = max(abs(rc - 26), abs(rr - 6))
        pairs.append((ov * 4 + dm * 0.5 + dr * 0.5, ov, ms, mc, mr, rs, rc, rr))

pairs.sort()
print('最优配对（低重叠 + 紧贴各自房间）:')
for p in pairs[:10]:
    _, ov, ms, mc, mr, rs, rc, rr = p
    print(f'   main-hall scale={ms} @({mc},{mr})   rongxi-hall scale={rs} @({rc},{rr})   重叠={ov:.0%}')
