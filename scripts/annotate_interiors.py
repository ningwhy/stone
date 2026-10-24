#!/usr/bin/env python3
"""Annotate the committed Tiled maps with interior ownership.

Two Tiled custom properties drive the "walk in and the roof comes off" behaviour:

  PlanZones object  `indoor`      (bool)   this floor is inside a building
  Art object        `interiorZone` (string) the zone this `exterior` building roofs over

The script is idempotent: re-running rewrites the same properties, and it never
touches anything else in the file, so the maps stay diff-friendly.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS = os.path.join(ROOT, 'maps')

# map -> { zone id: is indoor }
INDOOR_ZONES = {
    'central':      {'A1', 'A2'},
    'rongguo-entry':{'F'},
    'c4_yamen':     {'A1'},
    'wang':         {'A1'},
    'yucun':        {'A0'},
    'lin':          {'A0'},
    'east':         {'A2'},
    'c4_lixiang':   {'A1'},
}

# map -> { exterior art object name: interior zone id }
INTERIOR_OF = {
    'central':       {'rongxi-hall': 'A1', 'main-hall': 'A2'},
    'rongguo-entry': {'贾母正房外观': 'F'},
    'c4_yamen':      {'main-hall': 'A1'},
    'wang':          {'main-hall': 'A1'},
    'yucun':         {'main-hall': 'A0'},
    'lin':           {'main-hall': 'A0'},
    'east':          {'main-hall': 'A2'},
    'c4_lixiang':    {'main-hall': 'A1'},
}


def prop(props, name):
    for p in props:
        if p.get('name') == name:
            return p
    return None


def set_prop(obj, name, value, kind):
    p = prop(obj.get('properties') or [], name)
    if p is None:
        obj.setdefault('properties', []).append({'name': name, 'value': value, 'type': kind})
        return True
    if p.get('value') == value and p.get('type') == kind:
        return False
    p['value'], p['type'] = value, kind
    return True


def annotate(map_id):
    path = os.path.join(MAPS, map_id + '.tmj')
    with open(path, encoding='utf-8') as fh:
        data = json.load(fh)
    changed = False
    for layer in data['layers']:
        if layer['name'] == 'PlanZones':
            for obj in layer.get('objects') or []:
                zid = obj['name'].split(' ')[0]
                want = zid in INDOOR_ZONES[map_id]
                if set_prop(obj, 'indoor', want, 'bool'):
                    changed = True
                    print(f'  {map_id}: zone {zid} indoor={want}')
        elif layer['name'] == 'Art':
            for obj in layer.get('objects') or []:
                zone = INTERIOR_OF[map_id].get(obj['name'])
                if zone is None:
                    continue
                if set_prop(obj, 'interiorZone', zone, 'string'):
                    changed = True
                    print(f'  {map_id}: art {obj["name"]} interiorZone={zone}')
    if changed:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write('\n')
    else:
        print(f'  {map_id}: already annotated')
    return changed


if __name__ == '__main__':
    todo = sys.argv[1:] or sorted(INDOOR_ZONES)
    touched = 0
    for m in todo:
        if annotate(m):
            touched += 1
    print(f'{len(todo)} map(s) checked, {touched} rewritten')
