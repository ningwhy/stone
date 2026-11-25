#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十五回的新舞台：赵姨娘房。

第二十五回《魇魔法姊弟逢五鬼　红楼梦通灵遇双真》只有一处**必须新开**的景：

  赵姨娘房 —— 马道婆与赵姨娘定魇魔法之计的地方。
     底本段 8：「一时来至赵姨娘房内，二人见过，赵姨娘命小丫头倒了茶来与他吃。
     马道婆因见炕上堆著些零碎绸缎湾角，赵姨娘正粘鞋呢。」
     段 10：赵姨娘「走到橱柜里将梯己拿了出来」，写五百两欠契，
     马道婆「向裤腰里掏出十个纸铰的青面白发的鬼来，并两个纸人」。
     这是全回魇魔法的策源地：一间屋、一张炕（粘鞋）、一张柜（取银子）、
     一处能两人对坐说悄悄话的地方。不新开就会被塞进王夫人上房，
     而那正是被魇魔法的人养病之处，语义冲突。

**不用新图的场景**：
  - 怡红院（红玉梦/宝玉寻红玉/黛玉瞧伤/吃茶打趣/宝玉疯魔起）：复用 `yihong`（17 锚点）。
  - 沁芳闸（红玉过翠烟桥见贾芸种树）：复用 `qinfang`（桥/山子石/桃林俱在）。
  - 王夫人上房（贾环抄咒烫宝玉/抬二人养病/僧道解厄/宝钗打趣）：复用 `wang`
    （kang_edge / wang_host / guest_seat / hall_entry）。
  - 贾母院（马道婆劝贾母供海灯）：复用 `rongguo-entry`（grandmother_seat）。

坐标纪律同第 24 回（详见 build_chapter24_maps.py 文件头）：
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
    # 赵姨娘房：一间内室，炕上堆着零碎绸缎（赵姨娘粘鞋），角上一张柜（藏梯己银子），
    # 当中一张桌子可倒茶对坐。马道婆从门口进来，两人在炕边低声定计。
    #
    # 通行关系：
    #   门口（马道婆进来）→ 茶桌（倒茶）→ 炕边（粘鞋、对坐密谋）→ 柜前（取银子写契）
    # 家具 footprint（炕、桌、柜）都要避开 L 形路线走廊；锚点格脚本会自动跳过。
    # ------------------------------------------------------------------
    'zhao_room': {
        'name': '荣国府 · 赵姨娘房',
        'theme': 'interior',
        'zones': [
            # 内室主体（室内）
            [8, 14, 16, 11, True, 'ROOM'],
            # 门口过道（与内室相接，站人）
            [8, 25, 16, 5, False],
        ],
        'anchors': {
            'door': [15, 27],       # 门口过道：马道婆进来
            'table': [15, 23],      # 茶桌前：小丫头倒茶、二人对坐
            'zhao_seat': [13, 19],  # 炕边：赵姨娘粘鞋、坐处
            'madao_seat': [18, 19], # 炕对面：马道婆坐处
            'kang': [16, 17],       # 炕：堆零碎绸缎
            'cabinet': [21, 20],    # 柜前：赵姨娘取梯己银子
        },
        'routes': {
            'in': ['door', 'table', 'zhao_seat'],
            'talk': ['zhao_seat', 'kang', 'madao_seat'],
            'silver': ['madao_seat', 'cabinet'],
        },
        'labels': [
            ['赵姨娘房', 15, 13],
            ['炕', 16, 16],
            ['柜', 22, 19],
        ],
        'props': [
            # 炕靠北墙，赵姨娘坐炕边粘鞋；炕是 footprint 资产，放在 kang 锚点北一格。
            ('plain-kang', *at(16, 16), 0.92),
            ('wang-kang-table', *at(16, 18), 0.62),
            # 茶桌在房中，倒茶对坐；square-table 是 footprint，避开 zhao/madao 两锚点。
            ('square-table', *at(15, 22), 0.72),
            ('round-stool', *at(13, 22), 0.55),
            ('round-stool', *at(17, 22), 0.55),
            # 柜在东墙，赵姨娘从这里取梯己银子。
            ('wang-cabinet', *at(22, 20), 0.74),
            ('tea-table', *at(19, 23), 0.55),
            # 屏风扇挡门口视线，给「悄悄说道」一个遮挡。
            ('wood-screen', *at(11, 24), 0.78),
            ('lamp-stand', *at(10, 17), 0.62),
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
