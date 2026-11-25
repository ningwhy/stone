#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十八回的新舞台：冯紫英家家宴厅。

第二十八回《蒋玉菡情赠茜香罗　薛宝钗羞笼红麝串》只有一处**必须新开**的景：

  冯紫英家 —— 家宴、唱曲、行令、赠茜香罗的地方。
     底本段 12：「一径到了冯紫英家门口，有人报与了冯紫英，出来迎接进去。
     只见薛蟠早已在那里久候，还有许多唱曲儿的小厮并唱小旦的蒋玉菡，
     锦香院的妓女云儿。大家都见过了，然后吃茶……然后摆上酒来，依次坐定。」
     段 30：「宝玉出席解手，蒋玉菡便随了出来。二人站在廊檐下……」
     这是全回家宴的重心：一处门、一间厅、一张酒桌、几张座、一段廊檐。
     不新开就会被塞进 `dinner`（贾母院晚膳）或 `tavern`（村肆），语义冲突。

**不用新图的场景**：
  - 沁芳闸（黛玉葬花、山坡诉肺腑）：复用 `qinfang`（花冢 tomb / 山子石 stone_seat）。
  - 王夫人上房（问药、配药方、凤姐作证）：复用 `wang`。
  - 凤姐院（写礼单、讨红玉）：复用 `c6_wangchui`（hall / platform / feng_room）。
  - 贾母院（黛玉裁剪、金玉红麝串）：复用 `rongguo-entry`（sceneId=`entry`）。
  - 怡红院（汗巾、节礼）：复用 `yihong`（baoyu_kang / xiren_kang）。

坐标纪律同第 24/25 回：
  - 网格 128×64 菱形，unit = tileheight = 64（不是 tilewidth）。
  - 锚点 col = x/64 - 0.5、row = y/64 - 0.5；footprint 不带 -0.5。
  - 路线走廊 L 形（先收敛 col 再收敛 row），且在删 blocker 之前生成；
    家具 footprint 压在廊上会断路。酒桌放 table 锚点北一格（col 15、row 16），
    不在竖廊 col 15 / row 17-28 上；屏风、柜、茶几同理避开各条路线。
  - 写完必须跑 npm run check:anchors 与 npm run map:framing。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import fit, is_shell  # noqa: E402

MAP_DIR = ROOT / 'maps'


def at(c, r, dx=0.0, dy=0.0):
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {
    # ------------------------------------------------------------------
    # 冯紫英家 · 家宴厅：进门过道 → 厅门 → 酒桌前，主客分坐两侧，
    # 唱曲小厮与云儿在西侧，蒋玉菡在主人一侧；东侧廊檐是宝玉与琪官
    # 解手出来、互赠汗巾之处。家具 footprint 全部避开 L 形路线走廊。
    # ------------------------------------------------------------------
    'fengziying_home': {
        'name': '冯紫英家 · 家宴厅',
        'theme': 'interior',
        'zones': [
            # 厅堂主体（室内）：col 8-26、row 12-23
            [8, 12, 18, 11, True, 'HALL'],
            # 进门过道（与厅相接，站人）：col 8-26、row 24-30
            [8, 24, 18, 6, False],
        ],
        'anchors': {
            'gate': [15, 28],          # 大门：冯紫英出来迎接
            'court': [15, 24],         # 院中/甬路
            'hall': [15, 20],          # 厅门：众人依次坐定
            'table': [15, 17],         # 酒桌前：行令、罚酒
            'host_seat': [12, 17],     # 主人冯紫英
            'baoyu_seat': [18, 17],    # 宝玉
            'xuepan_seat': [20, 16],   # 薛蟠
            'jiang_seat': [11, 16],    # 蒋玉菡（琪官）
            'yun_seat': [19, 19],      # 云儿（锦香院妓女，抱琵琶）
            'singer_place': [9, 19],   # 唱曲儿的小厮
            'corridor': [23, 22],      # 廊檐下：宝玉与琪官赠茜香罗
        },
        'routes': {
            'enter': ['gate', 'court', 'hall', 'table'],
            'host': ['table', 'host_seat', 'jiang_seat', 'singer_place'],
            'guests': ['table', 'baoyu_seat', 'xuepan_seat', 'yun_seat'],
            'to_corridor': ['table', 'corridor'],
        },
        'labels': [
            ['冯紫英家', 17, 11],
            ['家宴厅', 15, 14],
            ['廊檐', 24, 20],
            ['大门', 16, 29],
        ],
        'props': [
            # 酒桌在 table 锚点北一格，避开 col 15 的竖廊与各行横廊。
            ('square-table', *at(15, 16), 0.86),
            ('round-stool', *at(12, 17, 0, -18), 0.58),
            ('round-stool', *at(18, 17, 0, -18), 0.58),
            ('round-stool', *at(20, 16, -18, -16), 0.58),
            ('round-stool', *at(11, 16, 26, -14), 0.58),
            ('round-stool', *at(19, 19, 0, -14), 0.58),
            ('round-stool', *at(9, 19, 12, -12), 0.56),
            # 酒坛、屏风、柜与灯：屏风/柜是 footprint，避开所有路线走廊。
            ('wine-jars', *at(23, 14), 0.56),
            ('wood-screen', *at(22, 13), 0.72),
            ('wang-cabinet', *at(24, 16), 0.74),
            ('lamp-stand', *at(10, 13), 0.64),
            ('lamp-stand', *at(26, 20), 0.58),
            ('tea-table', *at(26, 24), 0.55),
            # 院中两株树，给「门口迎接」一段外场。
            ('garden-tree', *at(11, 27), 1.02),
            ('garden-tree', *at(24, 28), 0.98),
        ],
        'walls': [
            [8, 12, 26, 12],
            [8, 12, 8, 30],
            [26, 12, 26, 30],
            [8, 30, 14, 30],
            [19, 30, 26, 30],
        ],
        'terraces': [[14, 25, 4, 5, 'path']],
        'flowerbeds': False,
    },
}


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
            from stage_defs import eave
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
                     'writing-desk', 'plain-kang', 'wang-cabinet') and [c, r] not in anchor_cells:
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
                         if scene.get('walls') else [])
                      + ([{'name': 'flowerbeds', 'type': 'bool', 'value': False}]
                         if scene.get('flowerbeds') is False else []),
    }
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    (MAP_DIR / f'{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')
    return len(scene['anchors'])


manifest_path = ROOT / 'public/assets/rongguo/manifest.json'
assets = json.loads(manifest_path.read_text())['assets']
ts = json.loads((ROOT / 'maps/rongguo-art.tsj').read_text())
gids = {next(p['value'] for p in t['properties'] if p['name'] == 'asset'): t['id'] + 1 for t in ts['tiles']}


if __name__ == '__main__':
    for key, scene in scenes.items():
        n = build_map(key, scene)
        print(f'maps/{key}.tmj 已写出（{n} 个锚点）')
