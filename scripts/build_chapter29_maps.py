#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十九回的新舞台：清虚观。

第二十九回《享福人福深还祷福　痴情女情重愈斟情》的**主场景**是清虚观打醮：

  底本段 4：「将至观前，只听钟鸣鼓响，早有张法官执香披衣，带领众道士在路旁迎接。
  贾母的轿刚至山门以内……便命住轿。」又「进入二层山门」。
  段 6：「只见贾蓉从钟楼里跑了出来。」「贾珍站在阶矶上，因问：管家在那里？」
  段 10：「说著跑到大殿上去」，张道士从大殿取寄名符。
  段 13：「贾母与众人上了楼，在正面楼上归坐。凤姐等占了东楼。众丫头等在西楼」，
  贾珍「神前拈了戏……开戏」。

  这是一座**道观**（张道士、道录司、寄名符、传道法器），与现有 `c15_tiejian`
  （铁槛寺）、`c15_shuiyue`（水月庵）、`zhitong`（智通寺）三张**佛寺**图语义冲突，
  且那三张都没有「钟楼／阶矶／正面楼·东楼·西楼／戏台」这组打醮看戏所需的地点，
  故新建一张，而不是把它们改叫清虚观。

**不用新图的场景**：
  - 怡红院（开篇甩手帕、结尾宝黛大闹、薛蟠生日推病、袭人劝宝玉）：复用 `yihong`
    （开篇甩手帕、结尾袭人劝宝玉均在怡红院；宝黛大闹一场复用第 26 回新建的 `xiaoxiang` 潇湘馆）。
  - 贾母院（凤姐约看戏、请薛姨妈、贾母抱怨「不是冤家不聚头」）：复用 `entry`。
  - 宁荣街（初一出门、车辆纷纷、周瑞家的喝止）：复用 `capital`。

坐标纪律同第 24、25 回（详见 build_chapter24_maps.py / build_chapter25_maps.py 文件头）：
  - 网格 128×64 菱形，unit = tileheight = 64（不是 tilewidth）。
  - 锚点 col = x/64 - 0.5、row = y/64 - 0.5；footprint 不带 -0.5。
  - 路线走廊是 L 形（先收敛 col，再收敛 row），且在删 blocker 之前生成：
    `altar-table`/`garden-rock`/`tea-table`/`wood-screen` 的 footprint 一律避开
    row 18、row 21 的横向走廊与 col 12/16/20/24/25 的纵向走廊。
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
    # 清虚观：观前街 → 山门（住轿看泥胎圣像）→ 二层山门（小道士撞凤姐）
    #   → 院中（瞻拜观玩、张道士陪笑、取符、送玉）→ 正面楼/东楼/西楼（看戏）
    #   西偏钟楼（贾蓉乘凉）、阶矶（贾珍问管家）、大殿（张道士取寄名符）。
    #
    # 通行关系：
    #   enter  street → shanmen → ermen → court
    #   view   court → main_tower → east_tower / west_tower
    #   stage  main_tower → stage
    #   zhang  court → zhang_seat
    #   hall   court → steps → hall_door → hall
    #   bell   court → bell_tower
    # 所有锚点都落在某条 route 的 anchor_ids 里 → check:anchors 会验证两两连通。
    # ------------------------------------------------------------------
    'qingxu_guan': {
        'name': '清虚观 · 打醮与看戏',
        'theme': 'garden',
        'zones': [
            # 大殿室内（掀顶：张道士进去取寄名符）
            [16, 8, 10, 5, True, 'A0'],
            # 观院主体：山门到二层山门到院中、看楼、戏台、钟楼、阶矶
            [10, 13, 24, 15, False, 'A1'],
            # 观前街：轿马、执事、张法官带道士迎接
            [10, 28, 24, 6, False, 'A2'],
        ],
        'anchors': {
            'street': [20, 31],      # 观前街：张法官带众道士路旁迎接
            'shanmen': [20, 27],     # 山门以内：贾母住轿看泥胎圣像
            'ermen': [20, 24],       # 二层山门：小道士撞凤姐、贾珍领出去
            'court': [20, 21],       # 院中：一层一层瞻拜观玩、张道士进见
            'main_tower': [20, 18],  # 正面楼：贾母归坐、宝玉坐旁边
            'east_tower': [27, 18],  # 东楼：凤姐等占了东楼
            'west_tower': [13, 18],  # 西楼：众丫头等轮流伺候
            'stage': [16, 15],       # 戏台：神前拈戏、开戏
            'zhang_seat': [25, 22],  # 张道士陪笑站处
            'bell_tower': [12, 16],  # 钟楼：贾蓉躲进来乘凉
            'steps': [24, 14],       # 阶矶：贾珍问管家、喝命啐贾蓉
            'hall_door': [20, 12],   # 大殿门
            'hall': [20, 9],         # 大殿：张道士取寄名符
        },
        'routes': {
            'enter': ['street', 'shanmen', 'ermen', 'court'],
            'view': ['court', 'main_tower', 'east_tower', 'west_tower'],
            'stage_route': ['main_tower', 'stage'],
            'zhang': ['court', 'zhang_seat'],
            'hall_route': ['court', 'steps', 'hall_door', 'hall'],
            'bell': ['court', 'bell_tower'],
        },
        'labels': [
            ['清虚观', 20, 8],
            ['大殿', 20, 9],
            ['钟楼', 12, 15],
            ['戏台', 16, 14],
            ['正面楼', 20, 17],
            ['东楼', 27, 17],
            ['西楼', 13, 17],
            ['二层山门', 20, 23],
            ['山门', 20, 27],
            ['观前街', 26, 30],
        ],
        'props': [
            # 大殿：屋顶是 shell，随「走到 hall」掀开；香案在殿内偏东，避开 col 20 走廊。
            ('main-hall', *at(20, 11), 0.86, 'A0'),
            ('altar-shrine', *at(23, 10), 0.54),
            ('altar-table', *at(24, 9), 0.62),
            ('taixu-vase', *at(16, 10), 0.46),
            ('taixu-vase', *at(25, 10), 0.46),
            # 戏台在院北，三座看楼在南面对着戏台。椅子不带 footprint，不压走位。
            ('stage-platform', *at(16, 14), 0.72),
            ('official-chair', *at(19, 17), 0.56),
            ('official-chair', *at(26, 17), 0.56),
            ('official-chair', *at(12, 17), 0.56),
            # 二层山门与山门：道观的门楼，不带 footprint。
            ('flower-gate', *at(20, 23), 0.66),
            ('taixu-gate', *at(20, 26), 0.72),
            ('stone-lion', *at(17, 27), 0.52),
            ('stone-lion', *at(23, 27), 0.52),
            # 观前街：轿子、灯笼、树。
            ('sedan-chair', *at(24, 30), 0.74),
            ('estate-lantern', *at(18, 25), 0.58),
            ('estate-lantern', *at(22, 25), 0.58),
            ('garden-tree', *at(31, 26), 1.02),
            # 西边那株原放 (9,25)，屏幕 x=-1026，离所有锚点都超出取景框——
            # 挪到 (15,26)，从 street/shanmen 都看得见，且不在任何 L 形走廊上。
            ('garden-tree', *at(15, 26), 1.06),
            ('bamboo-cluster', *at(32, 16), 0.92),
            ('bamboo-cluster', *at(9, 18), 0.92),
            # 四件带 footprint 的家具都放在横向走廊（row 18/21）与纵向走廊之外。
            ('garden-rock', *at(30, 18), 0.82),
            ('garden-rock', *at(10, 20), 0.78),
            ('tea-table', *at(30, 24), 0.52),
            ('wood-screen', *at(11, 23), 0.68),
        ],
        'walls': [
            [10, 8, 34, 8],
            [10, 8, 10, 28],
            [34, 8, 34, 28],
            [10, 28, 18, 28],
            [22, 28, 34, 28],
        ],
        'terraces': [[20, 14, 2, 14, 'path']],
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
