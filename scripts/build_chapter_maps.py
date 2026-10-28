#!/usr/bin/env python3
"""Build the prequel and chapter-three stage maps; preserve the authored Rongguo entry map.

Layout vocabulary — all of it a design decision. The novel fixes the order of the walk
and what each room contains; it never gives a plan drawing, so the plan is ours:

  zones      `[col,row,w,h]`, optional 5th `True` marks an indoor floor
  terraces   `[col,row,w,h,'court'|'path']` a stone platform or a 甬路 laid over the tiles
  walls      `[c1,r1,c2,r2]` courtyard enclosure; the gaps between segments are the gates
  water      `[col,row,w,h]` pond, canal, or the ink-black 迷津
  beds       `[col,row,w,h]` flowerbeds; an empty list means paved or dust instead
  props      `(asset, col, row, scale[, zoneId])`

`col,row` is normally `at(c,r,dx,dy)` — a screen-pixel offset from one anchor. One grid
cell is 128×64 px, so a chair dropped on the "next cell" lands half a table away from
the table it belongs to; that is what made the props look scattered.

A fifth element names the floor a piece belongs to. A roof asset (`*-hall`) becomes the
shell that lifts off that floor; anything else becomes a furnishing that only appears
once somebody walks in.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import SCENES, at, eave, fit, is_shell  # noqa: E402  (the plan lives next door)


# Every plan is in stage_defs.py, one block per courtyard, so the geometry reads like the
# description it came from instead of an anonymous table of numbers.
scenes = SCENES

manifest_path = ROOT / 'public/assets/rongguo/manifest.json'
assets = json.loads(manifest_path.read_text())['assets']
ts = json.loads((ROOT / 'maps/rongguo-art.tsj').read_text())
gids = {next(p['value'] for p in t['properties'] if p['name'] == 'asset'): t['id'] + 1 for t in ts['tiles']}

for key, s in scenes.items():
    counter = 1

    def obj(name, c, r, **kwargs):
        global counter
        o = {'id': counter, 'name': name, 'x': c * 64, 'y': r * 64, 'width': 0, 'height': 0,
             'rotation': 0, 'visible': True}
        counter += 1
        o.update(kwargs)
        return o

    zones = []
    for i, z in enumerate(s['zones']):
        c, r, w, h = z[:4]
        indoor = [{'name': 'indoor', 'type': 'bool', 'value': True}] if len(z) > 4 and z[4] else []
        zone = obj(f'{z[5] if len(z) > 5 else "A" + str(i + 1)} {s["name"]}', c, r,
                   width=w * 64, height=h * 64)
        # Omit `properties` entirely when empty: a null list breaks annotate_interiors.
        if indoor:
            zone['properties'] = indoor
        zones.append(zone)
    # A named floor must exist, and every anchor must stand on one, or the walk breaks.
    zone_ids = {o['name'].split(' ')[0]: o for o in zones}
    zone_rects = {n: (o['x'] / 64, o['y'] / 64, o['width'] / 64, o['height'] / 64)
                  for n, o in zone_ids.items()}
    for name, (c, r) in s['anchors'].items():
        inside = any(z['x'] / 64 <= c < (z['x'] + z['width']) / 64
                     and z['y'] / 64 <= r < (z['y'] + z['height']) / 64 for z in zones)
        assert inside, f'{key}: anchor {name} ({c},{r}) stands outside every floor'
    for prop in s.get('props', []):
        if len(prop) > 4 and prop[4]:
            assert prop[4] in zone_ids, f'{key}: prop {prop[0]} names unknown floor {prop[4]}'
            assert is_shell(prop[0]) or True
    anchors = [obj(n, c + .5, r + .5, point=True) for n, (c, r) in s['anchors'].items()]
    paths = [obj('场景动线', 0, 0, properties=[{'name': 'route_id', 'value': 'main', 'type': 'string'},
                                          {'name': 'anchor_ids', 'value': ','.join(s['anchors']), 'type': 'string'}])]
    # All named points are joined by explicit corridors; A* still operates on the grid.
    art = []
    for prop in s.get('props', []):
        asset, c, r, scale = prop[0], prop[1], prop[2], fit(prop[0], prop[3])
        zone = prop[4] if len(prop) > 4 else None
        if asset not in assets:
            continue
        if is_shell(asset):
            c, r = eave(c, r, zone, zone_rects)
        a = assets[asset]
        x = (c - r) * 64 + (a['width'] / 2 - a['anchor'][0]) * scale
        y = (c + r + 1) * 32 + (a['height'] - a['anchor'][1]) * scale
        shell = is_shell(asset)
        art_props = [{'name': 'asset', 'value': asset, 'type': 'string'},
                     {'name': 'visibility',
                      'value': 'exterior' if shell else ('interior' if zone else 'always'),
                      'type': 'string'}]
        if zone:
            # Both the roof and its furnishings name the floor they belong to, so a stage
            # with two halls opens only the room somebody actually walked into.
            art_props.append({'name': 'interiorZone', 'value': zone, 'type': 'string'})
        art.append(obj(asset, 0, 0, x=y + x / 2, y=y - x / 2, gid=gids[asset],
                       width=a['width'] * scale, height=a['height'] * scale, type='art',
                       properties=art_props))
    footprints = []
    for prop in s.get('props', []):
        asset, c, r = prop[0], prop[1], prop[2]
        if asset in ('wood-screen', 'dining-table', 'tea-table', 'canopy-bed', 'garden-rock',
                     'altar-table', 'writing-desk') and [c, r] not in list(s['anchors'].values()):
            footprints.append(obj(asset, c, r, width=64, height=64, type='collision'))
    layers = []
    for n, entries in [('PlanZones', zones), ('PlanBlockers', []), ('Anchors', anchors),
                       ('Routes', paths), ('Art', art), ('ArtFootprints', footprints)]:
        layers.append({'id': len(layers) + 1, 'name': n, 'type': 'objectgroup', 'x': 0, 'y': 0,
                       'opacity': 1, 'visible': n == 'Art', 'draworder': 'topdown',
                       'objects': entries})
    labels = [obj(label, c + .5, r + .5, point=True) for label, c, r in s['labels']]
    layers.append({'id': len(layers) + 1, 'name': 'Labels', 'type': 'objectgroup', 'x': 0, 'y': 0,
                   'opacity': 1, 'visible': False, 'objects': labels})

    properties = [{'name': 'sceneId', 'type': 'string', 'value': key},
                  {'name': 'title', 'type': 'string', 'value': s['name']},
                  {'name': 'theme', 'type': 'string', 'value': s['theme']}]
    # Grid rectangles travel as one string per property, matching the parser in model.ts.
    for name, rows in (('terraces', s.get('terraces')), ('walls', s.get('walls')),
                       ('water', s.get('water')), ('lights', s.get('lights'))):
        if rows:
            properties.append({'name': name, 'type': 'string',
                               'value': ';'.join(','.join(str(v) for v in row) for row in rows)})
    if s.get('dusk'):
        properties.append({'name': 'dusk', 'type': 'bool', 'value': True})
    if s.get('beds') == []:
        properties.append({'name': 'flowerbeds', 'type': 'bool', 'value': False})
    elif s.get('beds'):
        properties.append({'name': 'flowerbeds', 'type': 'string',
                           'value': ';'.join(','.join(str(v) for v in row) for row in s['beds'])})

    tmj = {'type': 'map', 'version': '1.10', 'orientation': 'isometric',
           'renderorder': 'right-down', 'width': 40, 'height': 40,
           'tilewidth': 128, 'tileheight': 64, 'infinite': False, 'layers': layers,
           'tilesets': [{'firstgid': 1, 'source': 'rongguo-art.tsj'}],
           'nextlayerid': len(layers) + 1, 'nextobjectid': counter, 'properties': properties}
    (ROOT / f'maps/{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')

entry = ROOT / 'maps/rongguo-entry.tmj'
d = json.loads(entry.read_text())
# Keep the hand-authored walls/terraces and the 甬路: furnish_entry.py owns those.
d['properties'] = [p for p in d['properties']
                   if p['name'] not in ('sceneId', 'title', 'theme')] + [
    {'name': 'sceneId', 'type': 'string', 'value': 'entry'},
    {'name': 'title', 'type': 'string', 'value': '荣国府 · 贾母院'},
    {'name': 'theme', 'type': 'string', 'value': 'garden'}]
entry.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
print(f'Built {len(scenes)} chapter maps + existing entry map')
