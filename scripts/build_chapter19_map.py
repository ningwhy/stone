#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十九回的新舞台：袭人家（xiren_home）。

第十九回宝玉撞破宁府小书房的事之后，茗烟引他出城逛，路过袭人家：
「袭人之母也早迎了出来。袭人拉了宝玉进去。宝玉见房中三五个女孩儿，
见他进来，都低了头，羞惭惭的。花自芳母子两个百般怕宝玉冷，又让他上炕，
又忙另摆果桌，又忙倒好茶。」

这是一户京城市井人家：母子两个待客的客舍，屋舍简朴、待客殷勤。
屋舍用最朴素的 farm-house 壳表现，家具用 plain-kang / square-table / round-stool /
cabinet / lamp-stand 一路——这些是设计取舍，不是原文写明的形制。

格局照第十回「金荣家」那一套：里屋与院子必须贴邻，中间只空一行，
否则 A* 找不到从院门进屋的路，人物会卡在院里走不进去。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

MAP_DIR = ROOT / 'maps'


def at(c, r, dx=0.0, dy=0.0):
    """把屏幕像素偏移换成等距格坐标（同 stage_defs.at）。"""
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {
    'xiren_home': {
        'name': '袭人家 · 院与里屋',
        'theme': 'interior',
        # 里屋（ROOM，行 10-19）与小院（A0，行 20-29）必须贴邻。
        'zones': [[12, 20, 16, 10], [13, 10, 14, 10, True, 'ROOM']],
        'anchors': {
            'gate': [22, 28],
            'yard': [17, 25],
            'room_door': [16, 19],
            'room': [18, 13],
            'kang': [15, 12],
            'table': [21, 14],
            'host': [19, 12],
        },
        'routes': {
            # 可通行的格子来自两处：zone id 匹配 ^(A\d*|B|C|D|E|F)$ 的地板，
            # 以及路线沿途铺出来的走廊。所以**每一个要站人的锚点都得在路线上**——
            # 只列 main/inner 两段的话，kang / table / host 就不通，
            # 引擎 show 时会抛「显示地点不可通行」。
            'main': ['gate', 'yard', 'room_door', 'room'],
            'inner': ['yard', 'room_door', 'room', 'kang'],
            'seats': ['room', 'table', 'host'],
        },
        'labels': [['花家', 16, 22], ['里屋', 18, 11], ['小院', 22, 26]],
        'props': [
            ('farm-house', *at(18, 13), .78, 'ROOM'),
            ('plain-kang', *at(15, 12, -20, 10), .68, 'ROOM'),
            ('square-table', *at(21, 14, 0, 0), .62, 'ROOM'),
            ('round-stool', *at(21, 14, 70, 20), .58, 'ROOM'),
            ('cabinet', *at(22, 12, 0, 0), .60, 'ROOM'),
            ('lamp-stand', *at(19, 16, 0, 0), .66, 'ROOM'),
            ('flower-gate', *at(22, 28), .50),
            ('garden-tree', *at(14, 24), .96),
            ('courtyard-wall', *at(25, 22), .62),
        ],
        'walls': [[12, 20, 28, 20], [12, 20, 12, 30], [28, 20, 28, 30],
                  [12, 30, 20, 30], [24, 30, 28, 30]],
        'terraces': [[20, 24, 4, 6, 'path']],
    },
}

manifest_path = ROOT / 'public/assets/rongguo/manifest.json'
assets = json.loads(manifest_path.read_text())['assets']
ts = json.loads((ROOT / 'maps/rongguo-art.tsj').read_text())
gids = {next(p['value'] for p in t['properties'] if p['name'] == 'asset'): t['id'] + 1 for t in ts['tiles']}


def make_obj(name, c, r, **kwargs):
    obj = {'id': 0, 'name': name, 'x': c * 64, 'y': r * 64, 'width': 0, 'height': 0,
           'rotation': 0, 'visible': True}
    obj.update(kwargs)
    return obj


def build_map(key, scene):
    counter = [1]

    def obj(name, c, r, **kwargs):
        o = make_obj(name, c, r, **kwargs)
        o['id'] = counter[0]
        counter[0] += 1
        return o

    zones = []
    rects = {}
    for i, z in enumerate(scene['zones']):
        c, r, w, h = z[:4]
        zid = z[5] if len(z) > 5 else f'A{i}'
        props = []
        if len(z) > 4 and z[4]:
            props.append({'name': 'indoor', 'value': True, 'type': 'bool'})
        zone = obj(f'{zid} {scene["name"]}', c, r, width=w * 64, height=h * 64)
        if props:
            zone['properties'] = props
        zones.append(zone)
        rects[zid] = tuple(z[:4])
    # 每个锚点都得站在一块地板上，否则走路会断。
    for name, (c, r) in scene['anchors'].items():
        assert any(z['x'] / 64 <= c < (z['x'] + z['width']) / 64
                   and z['y'] / 64 <= r < (z['y'] + z['height']) / 64 for z in zones), \
            f'{key}: anchor {name} ({c},{r}) stands outside every floor'
    anchors = [obj(n, c + .5, r + .5, point=True) for n, (c, r) in scene['anchors'].items()]
    paths = [obj('动线 %s' % rid, 0, 0, properties=[
        {'name': 'route_id', 'value': rid, 'type': 'string'},
        {'name': 'anchor_ids', 'value': ','.join(names), 'type': 'string'},
    ]) for rid, names in scene['routes'].items()]

    art = []
    footprints = []
    anchor_cells = list(scene['anchors'].values())
    for prop in scene['props']:
        asset, c, r, scale = prop[0], prop[1], prop[2], fit(prop[0], prop[3])
        interior_zone = prop[4] if len(prop) > 4 else None
        if is_shell(asset):
            c, r = eave(c, r, interior_zone, rects)
        if asset not in assets:
            print(f'  跳过缺失资产 {asset}')
            continue
        a = assets[asset]
        x = (c - r) * 64 + (a['width'] / 2 - a['anchor'][0]) * scale
        y = (c + r + 1) * 32 + (a['height'] - a['anchor'][1]) * scale
        art_props = [
            {'name': 'asset', 'value': asset, 'type': 'string'},
            {'name': 'visibility',
             'value': 'interior' if interior_zone else ('exterior' if is_shell(asset) else 'always'),
             'type': 'string'}]
        if interior_zone:
            art_props.append({'name': 'interiorZone', 'value': interior_zone, 'type': 'string'})
        art.append(obj(asset, 0, 0, x=y + x / 2, y=y - x / 2, gid=gids[asset],
                       width=a['width'] * scale, height=a['height'] * scale, type='art',
                       properties=art_props))
        if asset in ('wood-screen', 'tea-table', 'garden-rock', 'altar-table', 'square-table',
                     'writing-desk') and [c, r] not in anchor_cells:
            footprints.append(obj(asset, c, r, width=64, height=64, type='collision'))

    layers = []
    for name, entries in [('PlanZones', zones), ('PlanBlockers', []), ('Anchors', anchors),
                          ('Routes', paths), ('Art', art), ('ArtFootprints', footprints)]:
        layers.append({'id': len(layers) + 1, 'name': name, 'type': 'objectgroup', 'x': 0, 'y': 0,
                       'opacity': 1, 'visible': name == 'Art', 'draworder': 'topdown',
                       'objects': entries})
    labels = [obj(label, c + .5, r + .5, point=True) for label, c, r in scene['labels']]
    layers.append({'id': len(layers) + 1, 'name': 'Labels', 'type': 'objectgroup', 'x': 0, 'y': 0,
                   'opacity': 1, 'visible': False, 'objects': labels})

    tmj = {
        'type': 'map', 'version': '1.10', 'orientation': 'isometric', 'renderorder': 'right-down',
        'width': 40, 'height': 40, 'tilewidth': 128, 'tileheight': 64, 'infinite': False,
        'layers': layers, 'tilesets': [{'firstgid': 1, 'source': 'rongguo-art.tsj'}],
        'nextlayerid': len(layers) + 1, 'nextobjectid': counter[0],
        'properties': [{'name': 'sceneId', 'type': 'string', 'value': key},
                       {'name': 'title', 'type': 'string', 'value': scene['name']},
                       {'name': 'theme', 'type': 'string', 'value': scene['theme']}]
                      + ([{'name': 'terraces', 'type': 'string',
                           'value': ';'.join(','.join(str(v) for v in t) for t in scene['terraces'])}]
                         if scene.get('terraces') else [])
                      + ([{'name': 'walls', 'type': 'string',
                           'value': ';'.join(','.join(str(v) for v in w) for w in scene['walls'])}]
                         if scene.get('walls') else []),
    }
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    (MAP_DIR / f'{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')
    return len(scene['anchors'])


if __name__ == '__main__':
    for key, scene in scenes.items():
        n = build_map(key, scene)
        print(f'maps/{key}.tmj 已写出（{n} 个锚点）')
