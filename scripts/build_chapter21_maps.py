#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十一回的两张新舞台：怡红院（yihong）与贾琏院（jialian_home）。

第二十一回有两条彼此不相干的戏，各要各的屋：

  一、怡红院 —— 袭人娇嗔箴宝玉。湘云黛玉在门口拉扯、宝钗来劝，是站在院门里；
     梳洗、画眉、拈胭脂、摔胭脂，是外间的梳妆台前；宝玉闷坐续《庄子》「焚花散麝」、
     掷笔就寝、次日一早「从今咱们两个丢开手」，是里间的炕上与书案前。
     原文写明这一路在「宝玉房中」「外间」「里间」三处，所以图上分外间与里间两进，
     中间以软帘（屏风）相隔——「揭起软帘自往里间来」是这一幕的转折点。

  二、贾琏院 —— 俏平儿软语救贾琏。平儿抖出枕套里的一绺青丝，「便走至这边房内来」，
     在屋里与贾琏周旋；随后「平儿在窗外笑道」，两人隔着窗子说话，凤姐进门时
     又是在院中。所以图上分正房与窗外（窗下一处说话位）两处，窗外必须能站人。

形制依据（第十七回底本写明大观园诸处格局，第二十一回底本写明屋里的陈设）：

  第十七回：「忽抬头看见前面一带粉垣，里面数楹修舍……入门便是曲折游廊，阶下石子
  漫成甬路。」——粉墙、游廊、石子甬路，是大观园诸处的共同形制。
  第十七回：「粉墙环护，绿柳周垂……一入门，两边都是游廊相接。院中点衬几块山石，
  一边种著数本芭蕉，那一边乃是一棵西府海棠，其势若伞」——这一段正是**怡红院**
  （第十八回：「『红香绿玉』改作『怡红快绿』，即名曰『怡红院』」，同处有蕉有棠）。
  所以怡红院的院里：一棵海棠（garden-tree 就是西府海棠）、一片蕉（无蕉叶素材，
  以 taixu-tree 替代并在证据表标注改编）、几块山石、粉墙一圈、院门一座。

  第二十一回写明的屋内陈设，一一落到图上：
  「床几椅案」「妆奁等物」「镜台」「砚」「笔」「书」「剪灯烹茶」「斗蓬」
  「玉簪」「胭脂」——图上给：妆镜（qin-mirror）、书案（writing-desk）、书架
  （bookshelf）、灯架（lamp-stand）、炕（plain-kang）、床（canopy-bed）、屏风
  （wood-screen，兼作软帘）、茶几（tea-table）、圆凳（round-stool）、衣架（cabinet）。

  第十七回：「上面小小两三间房舍，一明两暗，里面都是合著地步打就的床几椅案。
  从里间房内又得一小门，出去则是后院。」——两三间房、明暗相间，最是怡红院的格局。

  第二十一回写明贾琏「搬出外书房来斋戒」，十二日后「仍复搬进卧室」；平儿
  「收拾贾琏在外的衣服舖盖」，抖出枕套里的青丝。凤姐院与贾琏的住处相邻，
  这一回写的是「凤姐往上屋去后」平儿收拾铺盖，地点在凤姐院一带。
  贾琏院形制：正房一间带耳房、院中一棵垂柳（willow→taixu-tree 替代，标注改编）、
  粉墙、院门，正房窗外有一处说话位。

设计取舍（原文未写、由改编推定的，在证据表 design 条目里逐条标注）：
  - 怡红院的院门开在东南，与外间朝南的窗相对，便于湘云黛玉在门口拉扯这一段。
  - 院中芭蕉无对应素材，用白花树（taixu-tree）代替，记为改编。
  - 贾琏院与凤姐院（wang 图里的 feng_room）相邻，但本图只画贾琏这一跨院。
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
    # ------------------------------------------------------------------
    # 怡红院：外间（梳妆、镜台、摔胭脂）与里间（炕、书案、续庄子）
    # ------------------------------------------------------------------
    'yihong': {
        'name': '大观园 · 怡红院',
        'theme': 'interior',
        # 外间（OUTER，行 20-29）与里间（INNER，行 10-19）贴邻：
        # 两进之间不留空隙——中间空一行，掀帘这一步就断了路。
        'zones': [[14, 20, 12, 10, False, 'OUTER'], [16, 10, 11, 10, True, 'INNER']],
        'anchors': {
            # 院门与院中：湘云黛玉在门口拉扯的一段
            'gate': [24, 28],
            'yard': [21, 26],
            'gate_step': [23, 27],
            # 外间：梳妆台前，湘云梳头、宝玉抢水洗脸、拈胭脂被拍落
            'outer_room': [18, 25],
            'mirror_place': [17, 24],
            'cui_lv_place': [20, 24],
            'zijun_place': [16, 24],
            'baochai_place': [22, 24],
            'baoyu_outer': [19, 26],
            # 软帘：宝玉「揭起软帘自往里间来」
            'curtain': [19, 19],
            # 里间：续《庄子》、掷笔、娇嗔
            'inner_room': [20, 15],
            'kang': [18, 14],
            'baoyu_kang': [19, 15],
            'xiren_kang': [21, 15],
            'desk_place': [22, 12],
            'book_place': [23, 13],
            'window_place': [24, 16],
        },
        'routes': {
            # 每一处要站人的地方都得在某条动线上：名字存在不等于可通行，
            # 引擎 show 时会抛「显示地点不可通行」。
            'gate_in': ['gate', 'gate_step', 'yard'],
            'to_outer': ['yard', 'outer_room', 'mirror_place', 'zijun_place',
                         'cui_lv_place', 'baochai_place', 'baoyu_outer'],
            'to_inner': ['baoyu_outer', 'curtain', 'inner_room', 'kang',
                         'baoyu_kang', 'xiren_kang', 'desk_place', 'book_place'],
            'window': ['inner_room', 'window_place'],
        },
        'labels': [['怡红院', 21, 29], ['外间', 19, 29], ['里间', 20, 10],
                   ['软帘', 19, 19], ['院中海棠', 22, 27]],
        'props': [
            # 屋壳：粉墙环护的一带修舍，屋里两进。
            ('main-hall', *at(20, 13), .90, 'INNER'),
            ('qin-room', *at(19, 22), .62, 'OUTER'),
            # 外间：镜台、妆奁、书案、灯
            ('qin-mirror', *at(17, 24, -40, 6), .58, 'OUTER'),
            ('writing-desk', *at(22, 25, 30, 12), .66, 'OUTER'),
            ('bookshelf', *at(25, 23, 0, 0), .64, 'OUTER'),
            ('lamp-stand', *at(16, 26, 0, 0), .62, 'OUTER'),
            ('tea-table', *at(20, 26, 0, 0), .56, 'OUTER'),
            ('round-stool', *at(20, 26, 66, 14), .54, 'OUTER'),
            # 软帘（屏风）：隔开外间与里间
            ('wood-screen', *at(19, 19, 0, 0), .66, 'INNER'),
            # 里间：炕、书案、书架、衣架
            ('plain-kang', *at(19, 14, 0, 10), .74, 'INNER'),
            ('writing-desk', *at(22, 12, 0, 0), .74, 'INNER'),
            ('bookshelf', *at(24, 12, 0, 0), .70, 'INNER'),
            ('cabinet', *at(25, 15, 0, 0), .58, 'INNER'),
            ('vase-stand', *at(17, 12, 0, 0), .54, 'INNER'),
            ('brazier', *at(25, 18, 0, 0), .56, 'INNER'),
            # 院中：粉墙、院门、海棠、山石
            ('screen-wall', *at(25, 26, 0, 0), .58),
            ('flower-gate', *at(24, 28), .48),
            ('garden-tree', *at(22, 27), .98),
            ('garden-rock', *at(26, 24), .84),
            ('reeds', *at(15, 27), .72),
        ],
        'walls': [[14, 19, 26, 19], [14, 19, 14, 30], [26, 19, 26, 30],
                  [14, 30, 21, 30], [24, 30, 26, 30]],
        'terraces': [[20, 20, 4, 9, 'path']],
    },

    # ------------------------------------------------------------------
    # 贾琏院：正房（平儿抖出青丝）与窗外（隔窗说话）
    # ------------------------------------------------------------------
    'jialian_home': {
        'name': '荣国府 · 贾琏院',
        'theme': 'interior',
        # 正房（ROOM，行 12-19）与院中（A0，行 20-29）贴邻，中间只空一行。
        'zones': [[15, 12, 10, 8, True, 'ROOM'], [13, 20, 14, 10]],
        'anchors': {
            'gate': [24, 28],
            'yard': [20, 25],
            'room_door': [19, 19],
            'room': [19, 15],
            'bed': [18, 14],
            'jia_lian_bed': [19, 14],
            'pinger_window': [22, 17],
            'window_place': [23, 17],
            'table_place': [22, 15],
            'trunk_place': [20, 16],
        },
        'routes': {
            'main': ['gate', 'yard', 'room_door', 'room'],
            'inside': ['room', 'bed', 'jia_lian_bed', 'trunk_place', 'table_place'],
            'window': ['room', 'pinger_window', 'window_place'],
        },
        'labels': [['贾琏院', 21, 29], ['正房', 19, 12], ['窗外', 23, 18]],
        'props': [
            ('main-hall', *at(20, 15), .86, 'ROOM'),
            # 枕套在炕上，抖出的青丝就在这里。
            ('plain-kang', *at(19, 14, -20, 8), .74, 'ROOM'),
            ('canopy-bed', *at(17, 13, 0, 0), .58, 'ROOM'),
            ('official-desk', *at(23, 14, 0, 0), .70, 'ROOM'),
            ('tea-table', *at(21, 16, 0, 0), .56, 'ROOM'),
            ('round-stool', *at(21, 16, 62, 12), .54, 'ROOM'),
            ('cabinet', *at(16, 16, 0, 0), .58, 'ROOM'),
            ('lamp-stand', *at(17, 17, 0, 0), .60, 'ROOM'),
            ('vase-stand', *at(24, 12, 0, 0), .52, 'ROOM'),
            # 院中：粉墙、院门、垂柳
            ('courtyard-wall', *at(24, 24, 0, 0), .58),
            ('flower-gate', *at(24, 28), .48),
            ('taixu-tree', *at(17, 24), .92),
            ('garden-rock', *at(25, 22), .80),
        ],
        'walls': [[13, 19, 27, 19], [13, 19, 13, 30], [27, 19, 27, 30],
                  [13, 30, 21, 30], [24, 30, 27, 30]],
        'terraces': [[19, 21, 4, 8, 'path']],
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
                         if scene.get('walls') else [])
                      + ([{'name': 'flowerbeds', 'type': 'bool', 'value': False}]
                         if scene.get('flowerbeds') is False else []),
    }
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    (MAP_DIR / f'{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')
    return len(scene['anchors'])


if __name__ == '__main__':
    for key, scene in scenes.items():
        n = build_map(key, scene)
        print(f'maps/{key}.tmj 已写出（{n} 个锚点）')
