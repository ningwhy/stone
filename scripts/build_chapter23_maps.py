#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十三回的新舞台：沁芳闸桃花下（qinfang）。

第二十三回有两条彼此不相干的戏，各要各的景：

  一、沁芳闸桃花下 —— 宝玉携《会真记》到「沁芳闸桥边桃花底下一块石上坐著」，
     看到「落红成阵」，风把桃花吹落满身满书满地；黛玉担着花锄花帚来，
     说「撂在水里不好」，要扫进「畸角上」的花冢；二人共读《会真记》，
     宝玉说「多愁多病身」、黛玉说「倾国倾城貌」，闹到「苗而不秀」。

     这一段底本写明了三样东西，缺一样这段戏就散架：
       「沁芳闸桥边」——桥与闸，
       「桃花底下」——桃林，
       「一块石上」——供他坐的石头；
     还有一句「那畸角上我有一个花冢」，所以图上要有一处**角落**能埋花。

  二、梨香院墙角 —— 黛玉「刚走到梨香院墙角上，只听墙内笛韵悠扬，歌声婉转」，
     唱的是《牡丹亭》里「原来姹紫嫣红开遍」「良辰美景奈何天」
     「则为你如花美眷，似水流年」。她「便一蹲身坐在一块山子石上」，
     「细嚼『如花美眷，似水流年』八个字的滋味」，最后「不觉心痛神痴，眼中落泪」。

     这一段**不另开新图**：梨香院已经有专图 `c4_lixiang`
     （第四回为香菱入府而建），本回从院墙外听声，用它的一角即可。

形制依据（第十七回底本写大观园诸处格局，第二十三回底本写这一段的具体位置）：

  第十七回：「只见水如晶帘一般奔入。原来这桥便是通外河之闸，引泉而入者。」
    ——沁芳闸是**园中水系的一座桥兼闸**，水从桥下穿过、往外河去。
    所以图上：一条水面横贯，水的北端有一道闸口，桥跨在水上。
  第二十三回：「宝玉携了一套《会真记》，走到沁芳闸桥边桃花底下一块石上坐著」
    ——桃花在**桥边**，不在水里；石头供坐。
  第二十三回：「那花瓣浮在水面，飘飘荡荡，竟流出沁芳闸去了」
    ——水面要能**流出去**，所以水不是死水塘，要通向闸口。
  第二十三回：「那畸角上我有一个花冢」
    ——花冢在**角落里**，图上要有一处两面围合的凹角。

设计取舍（原文未写、由改编推定的，在证据表 design 条目里逐条标注）：
  - 桃树用 `garden-tree`（西府海棠的同一棵素材）。本项目无桃花素材，
    记为改编；树的摆位成片而非单株，因为「桃花底下一块石」要成荫。
  - 闸墩、坐石与山子石都用 `garden-rock`（园石）承担，共五块：闸口东西两侧
    各立一块作闸墩，宝玉坐的「一块石」在桃林下，另有两块散石分置花冢旁
    与东岸。真正的桥在底本里是「沁芳闸桥边」——图上以 `terraces` 铺的石板
    桥面代木石桥，记为改编。
    （早期草稿曾打算拿 `stage-platform`／`canal-quay` 兼充闸台与石岸，
    但那两张素材的形制与这座园内的水闸不合，最终全部换成 `garden-rock`。）
  - 水边的芦苇用 `reeds`，点出这是水岸而不是旱地。
  - 落花不单独做素材：桃树脚下与池边由 `garden-rock`、地面贴花承担，
    「落红成阵」靠底本正文表现，不做成贴图（避免贴纸感）。
  - 墙用 `walls` 参数（北、东、南三面粉墙，西面敞开向园子），它们落进
    `PlanBlockers` 层，是**阻挡**而不是贴图：围出「畸角」——花冢所在的凹角。

坐标坑（**第 22 回挖出来的，写图前必须记住**）：
  - Tiled 网格是 128×64 菱形，`unit = tileheight = 64`（**不是 tilewidth**）。
  - 锚点 `col = x/64 - 0.5`、`row = y/64 - 0.5`（要落在格心）；
    footprint `col = x/64`、`row = y/64`（不带 -0.5）。
  - 引擎的路线走廊是 **L 形**（先收敛 col，再收敛 row），且**在删 blocker 之后**
    才生效——删 blocker 会切断刚画好的走廊。
    所以**摆家具前先确认路线走廊经过的格子**，否则会出现「路线声明了但走不通」。
    写完必须跑 `npm run check:anchors`。
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
    # 沁芳闸桃花下：桥边桃花、落花、花冢
    #
    # 布局按底本的三句话排：
    #   「沁芳闸桥边」  → 闸口在北，桥跨在水上，水往闸口流出去
    #   「桃花底下一块石」→ 桃林在桥西（西=屏幕左上），石在桃下
    #   「那畸角上我有一个花冢」→ 花冢在东墙与南墙围出的凹角
    #
    # 通行关系：
    #   西岸桃林（宝玉坐石、黛玉担锄来）→ 桥面 → 东岸（花冢凹角）
    #   水面本身不可走，落花是从桥西抖进水里、飘向闸口。
    # ------------------------------------------------------------------
    'qinfang': {
        'name': '大观园 · 沁芳闸桃花下',
        'theme': 'garden',
        # 两岸的地 + 中间的水 + 一座桥。
        # ★ 三条硬约束（都是踩过坑才知道的）：
        #   1) zone 的 id 必须匹配 ^(A\d*|B|C|D|E|F)$ 才会纳入可走集合；
        #   2) **走廊是 L 形**（先收敛 col，再收敛 row），且在删 blocker **之后**
        #      才生效 —— 所以路线经过的格子不能压着石头；
        #   3) 走廊会**无条件**把中间格加成可走。所以闸台必须**一直连到桥**，
        #      否则「桥→闸」那一段会变成一条走在水面上的路。
        #
        # 布局按底本的三句话排：
        #   「沁芳闸桥边」      → 闸在北，桥东西横跨，水从桥下往南流
        #   「桃花底下一块石」 → 桃林在桥西（西=屏幕左上），石在桃下
        #   「那畸角上我有一个花冢」→ 花冢在东墙围出的凹角
        #
        # 可走面：
        #   A 西岸桃林  col 3-18
        #   C 闸台（北） col 19-21，row 8-14 —— 从北岸伸出的石台
        #   D 桥面      col 12-29，row 15-16 —— 东西横跨，压住水带的北端
        #   B 东岸      col 22-37 —— 花冢凹角在这一岸
        'zones': [
            [3, 7, 16, 22],
            [19, 8, 3, 7],
            [12, 15, 18, 2],
            [22, 7, 16, 22],
        ],
        'anchors': {
            # 西岸：桃花底下
            'bank_west': [10, 20],
            'peach_grove': [7, 12],
            'stone_seat': [13, 17],
            # 桥：西头、中段
            'bridge_head': [14, 15],
            'bridge_mid': [20, 15],
            # 东岸：花冢凹角
            'bank_east': [26, 20],
            'corner': [34, 12],
            'tomb': [32, 15],
            # 闸口北端的石台
            'sluice': [20, 8],
        },
        'routes': {
            # 每一处要站人的地方都得在某条动线上：名字存在不等于可通行，
            # 引擎 show 时会抛「显示地点不可通行」。
            'west_bank': ['bank_west', 'stone_seat', 'peach_grove'],
            'cross': ['bank_west', 'bridge_head', 'bridge_mid', 'sluice'],
            'to_tomb': ['bridge_mid', 'bank_east', 'tomb', 'corner'],
        },
        'labels': [
            ['沁芳闸', 20, 5],
            ['桃花坡', 6, 14],
            ['桥', 24, 14],
            ['花冢', 33, 17],
        ],
        'props': [
            # 闸口两侧的石头（闸墩）。**放在走廊之外**——石头会生成 footprint，
            # footprint 会在走廊生成之后把格子删掉，压在路线上就会断路。
            ('garden-rock', *at(18, 9), .80),
            ('garden-rock', *at(22, 9), .78),
            # 桃林：成片，不是一株（底本「桃花底下」要成荫）
            ('garden-tree', *at(5, 13), .96),
            ('garden-tree', *at(4, 21), .86),
            ('garden-tree', *at(11, 24), .92),
            # 这株原在 (3,26)：西岸最西南角，离 peach_grove / stone_seat / bank_west
            # 都远到取景门禁判「never in frame」——树冠整体在画面之外，读者看不到
            # 桃林是成片的。挪到 (6,18)，与另外几株一起成荫。
            ('garden-tree', *at(6, 18), .84),
            ('garden-tree', *at(16, 23), .88),
            ('garden-tree', *at(25, 13), .90),
            ('garden-tree', *at(28, 10), .84),
            ('garden-tree', *at(35, 22), .88),
            # 宝玉坐的「一块石」。落在 stone_seat 那一格，脚本会自动跳过
            # footprint（锚点格不能被道具的碰撞删掉）。
            ('garden-rock', *at(13, 17), .78),
            # 花冢旁的山子石（避开走廊）
            ('garden-rock', *at(33, 13), .72),
            ('garden-rock', *at(29, 23), .66),
            # 水边芦苇
            ('reeds', *at(18, 25), .70),
            ('reeds', *at(22, 26), .66),
        ],
        # 水面：南北向的一带，从桥下往南流（底本「竟流出沁芳闸去了」）。
        # 与 zone D 有一格重叠 —— 那正是**桥面压住水面**，水从桥下穿过去。
        'water': [[19, 15, 3, 14]],
        # 甬路：西岸到桥头的一段石板路；桥面本身也铺石板。
        'terraces': [[9, 20, 6, 2, 'path'], [18, 15, 4, 2, 'path']],
        # 粉墙：北、东、南三面围合，西面敞开向园子。
        'walls': [[17, 6, 37, 6], [37, 6, 37, 29], [17, 29, 37, 29]],
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
                      + ([{'name': 'water', 'type': 'string',
                           'value': ';'.join(','.join(str(v) for v in w) for w in scene['water'])}]
                         if scene.get('water') else [])
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
