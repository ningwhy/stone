#!/usr/bin/env python3
"""Build the two outdoor travel stages from design/travel-maps.json.

These stages walk between the location maps instead of cutting to them: the canal
carries Daiyu from Yangzhou to the capital, the country road carries Yucun out of
the city to Zhitong temple (and back at dusk). They follow the same TMJ contract as
every other stage in maps/, so the runtime and Tiled read them unchanged.

Unlike build_chapter_maps.py this generator only writes its own two files; it never
touches the hand-furnished estate stages.

Usage: python3 scripts/build_travel_maps.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / 'public/assets/rongguo/manifest.json'
assets = json.loads(manifest_path.read_text())['assets']
ts = json.loads((ROOT / 'maps/rongguo-art.tsj').read_text())
gids = {next(p['value'] for p in t['properties'] if p['name'] == 'asset'): t['id'] + 1 for t in ts['tiles']}

design = json.loads((ROOT / 'design/travel-maps.json').read_text())
FOOTPRINTED = ('wood-screen', 'dining-table', 'tea-table', 'canopy-bed', 'garden-rock')

for key, s in design.items():
    counter = 1

    def obj(name, c, r, **kwargs):
        global counter
        o = {'id': counter, 'name': name, 'x': c * 64, 'y': r * 64, 'width': 0, 'height': 0, 'rotation': 0, 'visible': True}
        counter += 1
        o.update(kwargs)
        return o

    zones = [obj(f'A{i} {s["name"]}', c, r, width=w * 64, height=h * 64) for i, (c, r, w, h) in enumerate(s['zones'])]
    anchors = [obj(n, c + .5, r + .5, point=True) for n, (c, r) in s['anchors'].items()]
    # Route corridors are what the walkable set is built from; each route is listed
    # separately so the return road does not drag a phantom corridor across the stage.
    route_specs = s.get('routes') or [{'id': 'main', 'anchors': list(s['anchors'])}]
    for route in route_specs:
        for name in route['anchors']:
            assert name in s['anchors'], f'{key}: route {route["id"]} references unknown anchor {name}'
    paths = [obj('场景动线', 0, 0, properties=[
        {'name': 'route_id', 'value': route['id'], 'type': 'string'},
        {'name': 'anchor_ids', 'value': ','.join(route['anchors']), 'type': 'string'}]) for route in route_specs]
    art = []
    for asset, c, r, scale in s['props']:
        if asset not in assets:
            continue
        a = assets[asset]
        x = (c - r) * 64 + (a['width'] / 2 - a['anchor'][0]) * scale
        y = (c + r + 1) * 32 + (a['height'] - a['anchor'][1]) * scale
        art.append(obj(asset, 0, 0, x=y + x / 2, y=y - x / 2, gid=gids[asset], width=a['width'] * scale,
                       height=a['height'] * scale, type='art', properties=[
                           {'name': 'asset', 'value': asset, 'type': 'string'},
                           {'name': 'visibility', 'value': 'always', 'type': 'string'},
                           {'name': 'depthOffset', 'value': 0, 'type': 'float'}]))
    footprints = []
    for asset, c, r, scale in s['props']:
        if asset in FOOTPRINTED and [c, r] not in list(s['anchors'].values()):
            footprints.append(obj(asset, c, r, width=64, height=64, type='collision'))
    layers = []
    for n, entries in [('PlanZones', zones), ('PlanBlockers', []), ('Anchors', anchors), ('Routes', paths), ('Art', art), ('ArtFootprints', footprints)]:
        layers.append({'id': len(layers) + 1, 'name': n, 'type': 'objectgroup', 'x': 0, 'y': 0, 'opacity': 1,
                       'visible': n == 'Art', 'draworder': 'topdown', 'objects': entries})
    labels = [obj(label, c + .5, r + .5, point=True) for label, c, r in s['labels']]
    layers.append({'id': len(layers) + 1, 'name': 'Labels', 'type': 'objectgroup', 'x': 0, 'y': 0, 'opacity': 1,
                   'visible': False, 'draworder': 'topdown', 'objects': labels})
    props = [{'name': 'sceneId', 'type': 'string', 'value': key},
             {'name': 'title', 'type': 'string', 'value': s['name']},
             {'name': 'theme', 'type': 'string', 'value': s['theme']}]
    if s.get('water'):
        props.append({'name': 'water', 'type': 'string', 'value': s['water']})
    if s.get('flowerbeds') is False:
        props.append({'name': 'flowerbeds', 'type': 'bool', 'value': False})
    tmj = {'type': 'map', 'version': '1.10', 'orientation': 'isometric', 'renderorder': 'right-down', 'width': 40,
           'height': 40, 'tilewidth': 128, 'tileheight': 64, 'infinite': False, 'layers': layers,
           'tilesets': [{'firstgid': 1, 'source': 'rongguo-art.tsj'}], 'nextlayerid': len(layers) + 1,
           'nextobjectid': counter, 'properties': props}
    (ROOT / f'maps/{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')
    print(f'Built maps/{key}.tmj: {len(zones)} zones, {len(anchors)} anchors, {len(art)} art, '
          f'{len(footprints)} footprints, routes {[r["id"] for r in route_specs]}')
