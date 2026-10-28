#!/usr/bin/env python3
"""Will the camera actually show what the beat is about?

The stage is drawn in world pixels and the camera does not centre the anchor: `MapScene.target()`
sets the player about 65 px above the middle of the viewport, and `fit()` clamps the zoom at
0.9, so a 1440×900 canvas shows roughly 1600×1000 world pixels — less the section bar at the
top and the dialogue box at the bottom. A 15×11 courtyard fits; a temple eleven rows away
does not, and that beat plays out over empty paving.

Each piece of art is judged only from the anchors it is actually visible from:

  shell (`exterior`)  hides once the walk is inside its floor, so it must be framed from the
                      anchors that are *outside* that floor — if every anchor is indoors it is
                      never shown, and is skipped
  furnishing          shows only with the roof off, so it must be framed from the anchors
                      *inside* its floor — the 榻 and the four chairs have to be in shot from
                      the seats that are about to use them
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZOOM = .9
HALF_W = 720 / ZOOM                      # 800 px either side of the camera
UP, DOWN = 450 / ZOOM - 70, 450 / ZOOM - 160   # 430 px above the anchor, 340 below
LIFT = -45 + 105 / ZOOM                  # target() sits this far below the anchor's feet
CROP = .18                               # a prop may hang a little out of frame
# A roof may leave frame; standing two rows from a 應天府 you see the eave and the door, and
# that is the shot the beat wants. What may never happen is the building's own foot being
# out of frame — that is the bug this checks — or its top third alone filling the screen.
ROOF_CROP = .55

problems = 0


def in_frame(ax, ay, w, h, anchor, crop=0.0):
    """Is an art object whose foot is at (ax,ay) visible from `anchor`?"""
    cx, cy = anchor[0], anchor[1] + LIFT
    dw, dh = ax - cx, ay - cy
    half = w / 2 * ZOOM * (1 - crop)
    if abs(dw) + half > HALF_W:
        return False
    top = dh - h * ZOOM * (1 - crop)
    return dh <= DOWN + h * ZOOM * crop and top >= -UP


for path in sorted((ROOT / 'maps').glob('*.tmj')):
    d = json.loads(path.read_text())
    layers = {l['name']: l.get('objects') or [] for l in d['layers']}
    # Object x/y are grid coordinates (centre of the cell), so the screen pair is
    # ((c-r)*64, (c+r+1)*32) — the +1 is the bottom edge of the cell, where feet stand.
    anchors = {o['name']: ((o['x'] / 64 - .5 - (o['y'] / 64 - .5)) * 64,
                           (o['x'] / 64 - .5 + o['y'] / 64 - .5) * 32 + 32)
               for o in layers.get('Anchors', [])}
    cells = {o['name']: (o['x'] / 64 - .5, o['y'] / 64 - .5) for o in layers.get('Anchors', [])}
    zones = {}
    for o in layers.get('PlanZones', []):
        props = {p['name']: p['value'] for p in o.get('properties') or []}
        zones[o['name'].split(' ')[0]] = (props.get('indoor') is True,
                                          (o['x'] / 64, o['y'] / 64,
                                           o['width'] / 64, o['height'] / 64))
    if not anchors or not zones:
        continue

    def inside(zone, name):
        zc, zr, zw, zh = zones[zone][1]
        c, r = cells[name]
        return zc <= c < zc + zw and zr <= r < zr + zh

    for o in layers.get('Art', []):
        props = {p['name']: p['value'] for p in o.get('properties') or []}
        name, vis, zone = o['name'], props.get('visibility'), props.get('interiorZone')
        # Tiled stores the pair inverted as `X = sy + sx/2, Y = sy - sx/2`; undo it.
        ax, ay = o['x'] - o['y'], (o['x'] + o['y']) / 2
        if vis == 'interior':
            seen_from = [n for n in anchors if zone and inside(zone, n)] if zone else list(anchors)
            kind = 'furnishing'
        elif vis == 'exterior' and zone:
            seen_from = [n for n in anchors if not inside(zone, n)]
            kind = 'shell'
        else:
            seen_from = list(anchors)
            kind = 'prop'
        if not seen_from:
            continue  # a roof that is always lifted, or a room nobody walks into: no frame to judge
        crop = CROP if kind == 'prop' else ROOF_CROP
        if any(in_frame(ax, ay, o['width'], o['height'], anchors[n], crop) for n in seen_from):
            continue
        print(f'{path.stem:14s} {kind:10s} {name} never in frame '
              f'({" / ".join(seen_from[:4])}{"…" if len(seen_from) > 4 else ""})')
        problems += 1

print(f'\n{problems} framing problem(s)')
sys.exit(1 if problems else 0)
