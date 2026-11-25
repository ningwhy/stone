#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十六回的新舞台：潇湘馆。

第二十六回《蜂腰桥设言传心事　潇湘馆春困发幽情》只有一处**必须新开**的景：

  潇湘馆 —— 回目明写，宝玉在此听黛玉「每日家情思睡昏昏」的长叹，
     掀帘进去，紫鹃倒茶，一句「若共你多情小姐同鸳帐」惹哭黛玉。
     底本段 12「匾上写著『潇湘馆』三字」「湘帘垂地」「一缕幽香从碧纱窗中暗暗透出」，
     段 13 黛玉在床上装睡，段 15 紫鹃倒茶——有窗、有床、有茶几的内室。
     现有 `daguanyuan` 只是大观园全景俯瞰、`night` 是贾母院碧纱橱，都不是大观园里的潇湘馆，
     语义冲突，所以新开一张室内图。

**不用新图的场景**：
  - 怡红院（红玉佳蕙、贾芸见宝玉、坠儿传帕、宝玉出逛、宝钗、晴雯不开门）：复用 `yihong`（17 锚点）。
  - 沁芳亭 / 蜂腰桥（李嬷嬷、坠儿引贾芸、四目相对）：复用 `qinfang`（桥/水岸/山子石）。
  - 荣府二门（老爷叫宝玉、焙茗等候）：复用 `entry`（hall_door / passage_entry）。
  - 薛蟠书房（寿礼、唐寅、冯紫英）：复用 `c4_lixiang`（梨香院前厅，street_gate / front_hall）。

坐标纪律同第 24/25 回（详见 build_chapter25_maps.py 文件头）：
  - 网格 128×64 菱形，unit = tileheight = 64（不是 tilewidth）。
  - 锚点 col = x/64 - 0.5、row = y/64 - 0.5；footprint 不带 -0.5。
  - 路线走廊 L 形且在删 blocker 之后才生效；家具 footprint 压在路线上会断路，
    脚本跳过锚点格，但路线走廊上的非锚点格仍要避开。
  - 写完必须跑 npm run check:anchors 与 npm run map:framing。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

MAP_DIR = ROOT / 'maps'


def at(c, r, dx=0.0, dy=0.0):
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {
    # ------------------------------------------------------------------
    # 潇湘馆：竹影掩映的院门在外，房内湘帘垂地。宝玉先在碧纱窗外贴脸听叹，
    # 再掀帘进屋；黛玉在床上，紫鹃在茶几边倒茶，奶娘婆子立在一旁。
    #
    # 通行关系：
    #   院门 → 窗外（贴纱窗听）→ 房门（掀帘）→ 床（黛玉）；
    #   床 → 坐椅 → 茶几 → 紫鹃 → 奶娘（房内走动）。
    # 家具 footprint（床、桌、柜、案、屏）都要避开 L 形路线走廊；锚点格脚本会自动跳过。
    # ------------------------------------------------------------------
    'xiaoxiang': {
        'name': '大观园 · 潇湘馆',
        'theme': 'garden',
        'zones': [
            # 内室（室内）：床、坐椅、茶几、紫鹃与奶娘都在此。
            [8, 14, 16, 11, True, 'ROOM'],
            # 院中过道（室外）：院门与碧纱窗下，宝玉在此站人。
            [8, 25, 16, 5, False],
        ],
        'anchors': {
            'gate': [15, 27],          # 院门：宝玉信步走入
            'window_out': [12, 26],    # 碧纱窗外：贴脸听「每日家情思睡昏昏」
            'door': [16, 23],          # 房门湘帘：掀帘进来
            'bed': [13, 19],           # 床：黛玉伸懒腰、装睡、下床
            'chair': [18, 18],         # 坐椅：宝玉一歪身坐下
            'desk_place': [19, 20],    # 茶几：紫鹃倒茶
            'zijun_place': [20, 22],   # 紫鹃立处
            'nurse_place': [22, 19],   # 奶娘并两个婆子
        },
        'routes': {
            'in': ['gate', 'window_out', 'door', 'bed'],
            'inside': ['bed', 'chair', 'desk_place', 'zijun_place', 'nurse_place'],
        },
        'labels': [
            ['潇湘馆', 15, 13],
            ['碧纱窗', 12, 25],
            ['床', 12, 17],
            ['茶几', 21, 21],
        ],
        'props': [
            # 床靠西墙，黛玉在床上；footprint 避开床锚点 (13,19) 与动线。
            ('plain-kang', *at(11, 19), 0.92),
            ('wang-kang-table', *at(11, 21), 0.62),
            # 宝玉坐的椅子旁一张小几；避开 chair(18,18) 与茶几动线。
            ('square-table', *at(19, 17), 0.72),
            ('round-stool', *at(17, 17), 0.55),
            # 紫鹃倒茶的茶几在东侧，避开 desk(19,20)/zijun(20,22) 动线。
            ('tea-table', *at(21, 18), 0.55),
            ('round-stool', *at(21, 21), 0.55),
            # 案与灯，靠墙陈设，不压路线。
            ('writing-desk', *at(10, 17), 0.70),
            ('lamp-stand', *at(9, 20), 0.62),
            # 门外竹丛与屏风扇，给「凤尾森森、湘帘垂地」一个遮挡。
            ('bamboo-cluster', *at(14, 29), 0.80),
            ('wood-screen', *at(10, 25), 0.78),
        ],
        'walls': [
            [8, 14, 23, 14],
            [8, 14, 8, 30],
            [23, 14, 23, 30],
            [9, 30, 14, 30],
            [19, 30, 23, 30],
        ],
        'terraces': [[13, 27, 6, 4, 'path']],
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
