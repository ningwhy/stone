#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十四回的新舞台：香料铺、醉金刚巷口、绮霰斋外书房。

第二十四回《醉金刚轻财尚义侠　痴女儿遗帕惹相思》有三处**必须新开**的景，
底本都写明了地方的样子：

  一、香料铺 —— 贾芸的母舅卜世仁家。
     底本：「便一径往他母舅卜世仁家来。原来卜世仁现开香料舖。」
     这一段是全回的第一处转折：贾芸开口赊账，卜世仁拿「立了合同」「罚他二十两」
     的铺规把外甥顶回去。铺子必须有自己的门面、柜台、货��——不然「开香料舖」
     只是叙述里的一句词，图上无处可指。
     卜世仁的娘子与银姐只在旁白里说话（「你又糊涂了」「银姐，往对门王奶奶家去问」），
     **不安排她们登台**，图上不具象化。

  二、醉金刚巷口 —— 贾芸赌气出门，一头撞在醉汉身上，那人是倪二。
     底本：「这三街六巷，凭他是谁，有人得罪了我醉金刚倪二的街坊，管叫他人离家散！」
     「三街六巷」是市井街坊，不是荒野；倪二是「专放重利债，在赌博场吃闲钱」的泼皮。
     所以要一条**街**：街面、临街的门脸、一处酒肆（他刚从欠钱人家索了利钱吃醉回来）。
     底本明写他从「欠钱人家」索了利钱——所以街上要有第二处门脸。

  三、绮霰斋外书房 —— 贾芸等了宝玉一整日的地方。
     底本：「到贾母那边仪门外绮霰斋书房里来。」
     这**不是**怡红院：怡红院是宝玉的住处（`yihong`），绮霰斋在贾母院仪门之外，
     是外书房。底本写「只见焙茗，锄药两个小厮下象棋，为夺『车』正拌嘴，
     还有引泉、扫花、挑云、伴鹤四五个，又在房檐上掏小雀儿玩」——
     所以要一处**院子加一间书房**，院子里有小厮顽耍，房檐下能掏雀儿。
     小红就是在这道门前拦下贾芸的（见第 24 回第 16-17 段），门前要有站人的地方。

**不用新图的三处**：
  - 潇湘馆（黛玉与香菱）：第 23 回末尾黛玉已在潇湘馆，第 24 回开头香菱拍她一下、
    两人说些「绣的好，刺的精」，用 `night`（贾母院碧纱橱）不贴切，
    但本项目**没有潇湘馆专图**；第 23 回的黛玉戏用的就是 `qinfang`（沁芳闸桃花下）。
    本回开篇一段对话，复用 `qinfang`，不新开图。
  - 贾母院请安、贾琏院、怡红院、贾赦院：分别用 `rongguo-entry`（贾母院）、
    `jialian_home`、`yihong`、`east`。
  - 凤姐院外（贾芸献香）：用 `c6_wangchui`（荣府后门 · 周瑞家与凤姐院）——
    底本「到贾琏院门前，只见几个小厮拿着大高笤帚在那里扫院子呢。
    忽见周瑞家的从门里出来」，这正是周瑞家与凤姐院那一张图。

坐标坑（**写图前必须记住**）：
  - Tiled 网格是 128×64 菱形，`unit = tileheight = 64`（**不是 tilewidth**）。
  - 锚点 `col = x/64 - 0.5`、`row = y/64 - 0.5`（要落在格心）；
    footprint `col = x/64`、`row = y/64`（不带 -0.5）。
  - 引擎的路线走廊是 **L 形**（先收敛 col，再收敛 row），且**在删 blocker 之后**
    才生效——删 blocker 会切断刚画好的走廊。摆家具前先确认路线经过的格子。
  - 道具的 footprint 会把格子从可走集合里删掉；**压在路线上就会断路**。
    脚本会自动跳过锚点格，但路线走廊上的非锚点格仍要避开。
  - 写完必须跑 `npm run check:anchors`。
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
    # 卜世仁香料铺：临街的铺面，柜台在里，货架空着。
    #
    # 通行关系：
    #   街口（贾芸进来）→ 铺面前堂（与卜世仁对答）→ 铺面深处（辞别出门）
    # 「一半米都没」的赊账推托发生在柜台上，所以柜台前要能站两个人。
    # ------------------------------------------------------------------
    'spice_shop': {
        'name': '京城 · 卜世仁香料铺',
        'theme': 'street',
        'zones': [
            # 街面（南）
            [6, 23, 24, 8, False],
            # 铺面前堂（北）
            [9, 14, 14, 9, False],
            # 铺面里间（货架）
            [24, 15, 7, 8, True, 'BACK'],
        ],
        'anchors': {
            'street': [17, 28],
            'shop_door': [16, 22],
            'counter': [15, 19],
            'uncle': [18, 18],
            'nephew': [14, 20],
            'back': [26, 18],
            'exit': [26, 27],
        },
        'routes': {
            'in': ['street', 'shop_door', 'counter'],
            'talk': ['counter', 'uncle', 'nephew'],
            'out': ['nephew', 'shop_door', 'street', 'exit'],
        },
        'labels': [
            ['卜家香料铺', 16, 13],
            ['铺面', 16, 22],
            ['街口', 27, 29],
        ],
        'props': [
            # 铺面：柜台横在堂中，货架在后间。
            # 柜台是 footprint 资产（square-table），**要避开路线走廊**——
            # 路线在 counter / uncle / nephew 一带，柜台放在它们北侧。
            ('square-table', *at(16, 17), .74),
            ('official-chair', *at(15, 19), .70),
            ('round-stool', *at(19, 20), .62),
            # 货架空着：底本说「就拿现银子到我们这不三不四的铺子里来买，也还没有这些」
            ('bookshelf', *at(26, 17), .60, 'BACK'),
            ('vase-stand', *at(28, 19), .54, 'BACK'),
            ('wine-jars', *at(25, 20), .48, 'BACK'),
            # 街面：隔壁门脸与一棵歪树
            # ★ 树的位置是被取景门禁逼出来的：原来这株在 (9,26)，离所有锚点太远，
            #   树冠整体顶出画面上方余量（never in frame）。挪到街面中段 (8,24)，
            #   与 shop_door 同一带，从街口与铺门都看得到。
            ('garden-tree', *at(8, 24), 1.02),
            ('garden-tree', *at(27, 24), .96),
            ('garden-rock', *at(22, 29), .74),
            ('stone-lion', *at(11, 22), .50),
        ],
        'walls': [
            [9, 14, 23, 14], [9, 14, 9, 23], [23, 14, 23, 23],
            [9, 23, 13, 23], [19, 23, 23, 23],
        ],
        'terraces': [[14, 22, 4, 6, 'path']],
        'flowerbeds': False,
    },

    # ------------------------------------------------------------------
    # 醉金刚巷口：三街六巷里的一条街。
    #
    # 通行关系：
    #   巷口（贾芸低头走，撞上醉汉）→ 街心 → 倪二所欠钱人家的门脸 → 酒肆
    # 倪二「正从欠钱人家索了利钱，吃醉回来」，所以他是从北面门脸出来的。
    # ------------------------------------------------------------------
    'ni_er_lane': {
        'name': '京城 · 三街六巷（醉金刚巷口）',
        'theme': 'street',
        'zones': [
            # 街面（东西向，南侧）
            [5, 21, 26, 9, False],
            # 北侧门脸一：欠钱人家
            [10, 14, 8, 7, False],
            # 北侧门脸二：酒肆（室内）
            # ★ 这间必须是 indoor zone：`tavern-house` 是 shell（屋顶），只有在
            #   它自己的 zone 里才按「外壳」判定——从 zone 外的锚点看它整栋在画里，
            #   走进 zone 才掀顶露出酒坛与凳子。不配 zone 的话它会被当成普通道具
            #   按 640px 宽严格判取景，从东侧锚点直接判「never in frame」。
            [22, 13, 9, 8, True, 'TAVERN'],
        ],
        'anchors': {
            'lane': [8, 27],
            'street_center': [18, 25],
            'bully': [17, 23],
            'debtor_door': [13, 20],
            'tavern_door': [26, 21],
            'drunk': [21, 24],
        },
        'routes': {
            'lane': ['lane', 'street_center', 'bully'],
            'north': ['street_center', 'drunk', 'debtor_door'],
            'tavern': ['street_center', 'drunk', 'tavern_door'],
        },
        'labels': [
            ['三街六巷', 16, 29],
            ['酒肆', 27, 12],
            ['欠钱人家', 13, 13],
        ],
        'props': [
            # 酒肆：屋顶罩住 TAVERN 整间，屋里的酒坛与凳子掀顶才看得见。
            ('tavern-house', *at(26, 16), .88, 'TAVERN'),
            ('wine-jars', *at(28, 19), .56, 'TAVERN'),
            ('round-stool', *at(29, 21), .58, 'TAVERN'),
            # 欠钱人家的门脸（一堵照壁、一块园石）
            ('screen-wall', *at(13, 19), .58),
            ('garden-rock', *at(11, 20), .70),
            # 街面的杂物与树
            ('garden-tree', *at(6, 25), .98),
            ('garden-tree', *at(28, 26), 1.04),
            ('stone-lion', *at(31, 23), .48),
            ('garden-rock', *at(14, 28), .66),
        ],
        'walls': [
            [10, 14, 18, 14], [10, 14, 10, 21], [18, 14, 18, 21],
            [22, 13, 31, 13], [22, 13, 22, 21], [31, 13, 31, 21],
        ],
        'terraces': [[12, 24, 14, 4, 'path']],
        'flowerbeds': False,
    },

    # ------------------------------------------------------------------
    # 绮霰斋外书房：贾母院仪门之外的一处小院。
    #
    # 底本：「到贾母那边仪门外绮霰斋书房里来。只见焙茗，锄药两个小厮下象棋，
    # 为夺『车』正拌嘴，还有引泉、扫花、挑云、伴鹤四五个，又在房檐上掏小雀儿玩。」
    #
    # 通行关系：
    #   院门（贾芸跺脚进来）→ 院心（小厮下棋）→ 书房门前（焙茗迎出来）
    #   → 书房内（贾芸坐着等）
    # 小红在**书房门前**拦住贾芸（他说「廊上的二爷来了」），门前要能站人。
    # ------------------------------------------------------------------
    'qiranzhai': {
        'name': '荣国府 · 绮霰斋外书房',
        'theme': 'garden',
        'zones': [
            # 院子
            [8, 15, 20, 12, False],
            # 书房（北）
            [12, 7, 12, 7, True, 'STUDY'],
        ],
        'anchors': {
            'gate': [18, 26],
            'yard': [17, 20],
            'chess': [15, 19],
            'door': [17, 15],
            'study': [17, 11],
            'eave': [22, 15],
            'wait': [20, 12],
        },
        'routes': {
            'in': ['gate', 'yard', 'door'],
            'wait': ['door', 'study', 'wait'],
            'play': ['yard', 'chess', 'eave'],
        },
        'labels': [
            ['绮霰斋', 18, 6],
            ['外书房', 18, 10],
            ['仪门', 18, 28],
        ],
        'props': [
            # 书房
            ('main-hall', *at(17, 10), .78, 'STUDY'),
            ('writing-desk', *at(17, 11, 30, 14), .68, 'STUDY'),
            ('bookshelf', *at(14, 10, -20, 0), .58, 'STUDY'),
            ('round-stool', *at(20, 12), .58, 'STUDY'),
            # 院中：棋摊（两个小厮下象棋）
            ('square-table', *at(14, 18), .60),
            ('round-stool', *at(15, 20), .52),
            # 房檐下掏雀儿的地方——檐下要有东西可掏
            ('bamboo-cluster', *at(24, 15), .92),
            ('garden-tree', *at(26, 20), 1.06),
            ('garden-tree', *at(11, 22), 1.02),
            ('garden-rock', *at(23, 24), .70),
            ('flower-gate', *at(18, 26), .70),
        ],
        'walls': [
            [12, 7, 24, 7], [12, 7, 12, 15], [24, 7, 24, 15],
            [8, 15, 8, 27], [28, 15, 28, 27], [8, 27, 15, 27], [21, 27, 28, 27],
        ],
        'terraces': [[16, 17, 4, 10, 'path']],
        'flowerbeds': False,
    },

    # ------------------------------------------------------------------
    # 贾芸家：底本第 12 段「来至家门」「见他母亲自在炕上拈线」。
    #
    # 底本明写：
    #   「收了银子，来至家门，先到隔壁将倪二的信捎了与他娘子知道，方回家来。
    #     见他母亲自在炕上拈线，见他进来，便问那去了一日。」
    # 所以要一处**小屋**：一间屋、一个炕（母亲拈线的位置），
    # 街面上要有两处门脸——贾芸自家与隔壁倪二家（「先到隔壁」）。
    # 隔壁是倪二**他娘子**的家，倪二自己「我不回家去了」，所以只有门脸没人。
    # ------------------------------------------------------------------
    'jia_yun_home': {
        'name': '京城 · 贾芸家',
        'theme': 'street',
        'zones': [
            # 街面（南）
            [6, 23, 24, 8, False],
            # 贾芸家屋（北）
            [9, 14, 11, 9, False],
            # 隔壁倪二家（北）
            [22, 14, 8, 9, False],
        ],
        'anchors': {
            'street': [17, 28],
            'home_door': [13, 22],
            'room': [12, 19],
            'mother': [15, 18],
            'jia_yun': [11, 20],
            'neighbor_door': [24, 22],
            'neighbor_room': [26, 19],
        },
        'routes': {
            'in': ['street', 'home_door', 'room'],
            'talk': ['room', 'mother', 'jia_yun'],
            'next': ['jia_yun', 'neighbor_door', 'neighbor_room'],
            'out': ['jia_yun', 'home_door', 'street'],
        },
        'labels': [
            ['贾芸家', 13, 13],
            ['里屋', 13, 22],
            ['隔壁倪家', 25, 13],
            ['街口', 27, 29],
        ],
        'props': [
            # 屋里：炕（母亲拈线）、桌、凳
            ('plain-kang', *at(14, 17), .74),
            ('tea-table', *at(11, 18), .60),
            ('round-stool', *at(17, 20), .52),
            ('official-desk', *at(25, 17), .62),
            ('cabinet', *at(27, 20), .56),
            ('lamp-stand', *at(19, 18), .54),
            # 街面：两棵歪树与一块园石
            ('garden-tree', *at(9, 25), 1.00),
            ('garden-tree', *at(28, 25), .96),
            ('garden-rock', *at(21, 28), .68),
            ('stone-lion', *at(10, 22), .48),
        ],
        'walls': [
            [9, 14, 20, 14], [9, 14, 9, 23], [20, 14, 20, 23],
            [22, 14, 30, 14], [22, 14, 22, 23], [30, 14, 30, 23],
            [9, 23, 12, 23], [16, 23, 20, 23],
            [22, 23, 24, 23], [28, 23, 30, 23],
        ],
        'terraces': [[12, 23, 8, 4, 'path']],
        'flowerbeds': False,
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
