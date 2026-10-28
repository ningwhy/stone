#!/usr/bin/env python3
"""Furnish the hand-authored entry stage (荣国府 · 贾母院) the same way the generated
stages are furnished: an enclosure, a 甬路 on the axis, and a room that has something
in it once the roof comes off.

`maps/rongguo-entry.tmj` is authored by hand and is not rebuilt by any generator, so
this script patches it in place. Every insert is idempotent: an object with the same
name is updated, not duplicated.

What the novel gives for 贾母正房 (第三回): 贾母 坐在榻上, 黛玉 挨着坐下, 邢夫人王夫人
在地下椅子上坐了, 地下两溜椅子, 几上茗碗瓶花. So: a 榻 at the head of the room, two
chairs for the two 舅母, a screen behind, vase stands and a tea table. Nothing in the
middle, because that is where the greeting happens.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / 'maps/rongguo-entry.tmj'
assets = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())['assets']
ts = json.loads((ROOT / 'maps/rongguo-art.tsj').read_text())
gids = {next(p['value'] for p in t['properties'] if p['name'] == 'asset'): t['id'] + 1 for t in ts['tiles']}


def at(c, r, dx=0.0, dy=0.0):
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


def art_xy(asset, c, r, scale):
    """The same screen→tile conversion every builder uses, so the object lands like one."""
    a = assets[asset]
    x = (c - r) * 64 + (a['width'] / 2 - a['anchor'][0]) * scale
    y = (c + r + 1) * 32 + (a['height'] - a['anchor'][1]) * scale
    return y + x / 2, y - x / 2


# (name, asset, col, row, scale, interiorZone)
FURNITURE = [
    ('贾母榻', 'daybed', *at(19, 5.4), .74, 'F'),
    ('榻后屏风', 'wood-screen', *at(19, 4.2), .62, 'F'),
    ('邢夫人椅', 'official-chair', *at(17, 4.5), .68, 'F'),
    ('王夫人椅', 'official-chair', *at(23, 4.5), .68, 'F'),
    ('瓶花东', 'taixu-vase', *at(21, 4.3), .52, 'F'),
    ('瓶花西', 'taixu-vase', *at(16, 4.3), .52, 'F'),
    ('茗碗案', 'tea-table', *at(26, 5.2), .56, 'F'),
    ('落地灯', 'lamp-stand', *at(16, 8.4), .62, 'F'),
]

# The west wall of the compound, with the 西角门 left open between the two runs.
WALLS = '3.5,27,3.5,31;3.5,33,3.5,36'
# 甬路 from the 穿堂 mouth to the hall steps, laid over the courtyard tiles.
TERRACES = '18,11,2,8,path'


def main():
    data = json.loads(MAP.read_text())
    props = data.setdefault('properties', [])
    for name, value in (('walls', WALLS), ('terraces', TERRACES)):
        entry = next((p for p in props if p['name'] == name), None)
        if entry is None:
            props.append({'name': name, 'type': 'string', 'value': value})
        else:
            entry['value'] = value

    art = next(l for l in data['layers'] if l['name'] == 'Art')
    by_name = {o['name']: o for o in art['objects']}
    next_id = max(o['id'] for l in data['layers'] for o in l.get('objects', [])) + 1
    for name, asset, c, r, scale, zone in FURNITURE:
        if asset not in assets:
            print(f'  skip {name}: {asset} not built yet')
            continue
        a = assets[asset]
        x, y = art_xy(asset, c, r, scale)
        obj = by_name.get(name)
        if obj is None:
            obj = {'id': next_id, 'name': name, 'rotation': 0, 'visible': True, 'type': 'art'}
            next_id += 1
            art['objects'].append(obj)
        obj.update({'x': x, 'y': y, 'width': a['width'] * scale, 'height': a['height'] * scale,
                    'gid': gids[asset],
                    'properties': [{'name': 'asset', 'type': 'string', 'value': asset},
                                   {'name': 'visibility', 'type': 'string', 'value': 'interior'},
                                   {'name': 'interiorZone', 'type': 'string', 'value': zone},
                                   {'name': 'depthOffset', 'type': 'float', 'value': 0}]})
        print(f'  {name} {asset} at ({c:.2f},{r:.2f})')
    MAP.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(f'Furnished {MAP.name}: {len(FURNITURE)} pieces, walls and 甬路.')


if __name__ == '__main__':
    main()
