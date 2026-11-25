#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十回的新舞台：蔷薇花架。

第三十回《宝钗借扇机带双敲　龄官划蔷痴及局外》只有一处**必须新开**的景：

  蔷薇花架 —— 龄官蹲在花下、用绾头的簪子在泥地上画几千个「蔷」字，
     宝玉隔著篱笆洞儿偷看，看到看痴；阵雨落下，龄官误把他当丫头提醒避雨。
     底本段 12：「刚到了蔷薇花架，只听有人哽噎之声……如今五月之际，那蔷薇正是花叶
     茂盛之际，宝玉便悄悄的隔著篱笆洞儿一看，只见一个女孩子蹲在花下，手里拿著根
     绾头的簪子在地下抠土，一面悄悄的流泪。」
     段 13：「伏中阴晴不定，片云可以至雨，忽一阵凉风过了，唰唰的落下一阵雨来。」

     这一段的三样东西缺一不可，现有图都对不上：
       1) 蔷薇花叶茂盛 —— 一丛成荫的花木（不是桃林、不是水边）；
       2) 篱笆洞儿 —— 一道有洞口的篱笆，宝玉在洞外看，龄官在花下画；
       3) 积水的泥地 —— 龄官「在地下画字」，雨来了「头上滴下水来」。

     沁芳闸 `qinfang` 是水闸桥边桃林，语义是「水+桥+桃」；这里是「花架+篱笆+泥地」，
     把龄官划蔷塞进桃林会丢掉「隔篱笆洞儿看」这个关键动作，所以新开一张。

**不用新图的场景**：
  - 黛玉房（紫鹃劝、宝玉赔不是、戳额递帕、凤姐跳进来）：复用 `night`
    （daiyu_bed / bedside / night_talk / outer_door）。
  - 贾母院（凤姐说合、宝钗借扇机带双敲、负荆请罪、凤姐吃姜）：复用 `dinner`
    （grandmother_place / daiyu_place / feng_place / baoyu_greet / tea_place）。
  - 王夫人上房（金钏儿捶腿、调笑、被撵）：复用 `wang`
    （wang_host / kang_edge / guest_seat / hall_entry）。
  - 怡红院（宝官玉官玩耍、关门叫门、误踢袭人、夜间吐血）：复用 `yihong`
    （yard / gate_step / outer_room / xiren_kang / baoyu_kang）。

坐标纪律同第 23/24/25 回（详见 build_chapter23_maps.py 文件头）：
  - 网格 128×64 菱形，unit = tileheight = 64（不是 tilewidth）。
  - 锚点 col = x/64 - 0.5、row = y/64 - 0.5；footprint 不带 -0.5。
  - 路线走廊 L 形且在删 blocker 之后才生效；家具 footprint 别压在走廊上。
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
    # 蔷薇花架：花木成荫的园中一角，一道带洞的篱笆把里外分开。
    #   宝玉从园路来 → 篱笆洞儿外偷看 → 花架外痴看 → 花架下龄官画蔷 → 花丛
    #
    # 单个 zone（A0）铺满整块地面，一条 main 动线串起全部锚点：
    # 五个锚点都落在 route 的 anchor_ids 里，show 不会抛「不可通行」。
    # 家具 footprint（garden-rock / wood-screen）避开 L 形走廊与锚点格。
    # ------------------------------------------------------------------
    'qiangwei': {
        'name': '大观园 · 蔷薇花架',
        'theme': 'garden',
        'zones': [
            [4, 6, 30, 28],
        ],
        'anchors': {
            'garden_path': [10, 28],       # 园路：宝玉从王夫人房出来，忙进大观园
            'fence_hole': [16, 24],        # 篱笆洞儿：宝玉隔此偷看
            'outside_trellis': [19, 20],   # 花架外：宝玉看痴、淋雨处
            'under_trellis': [23, 18],     # 花架下：龄官蹲地画「蔷」
            'rose_bush': [27, 13],         # 蔷薇花叶茂盛处
        },
        'routes': {
            'main': ['garden_path', 'fence_hole', 'outside_trellis', 'under_trellis', 'rose_bush'],
        },
        'labels': [
            ['蔷薇花架', 24, 11],
            ['篱笆洞儿', 15, 25],
            ['园路', 9, 30],
        ],
        'props': [
            # 蔷薇花叶：用 garden-tree 成片 Rend 出花架的荫翳（本项目无蔷薇专素材，
            # 记为改编）。树不生成 footprint，可贴近锚点摆放以便镜头取到。
            ('garden-tree', *at(8, 27), .92),
            ('garden-tree', *at(13, 25), .86),
            ('garden-tree', *at(17, 22), .90),
            ('garden-tree', *at(21, 20), .94),
            ('garden-tree', *at(25, 15), .88),
            ('garden-tree', *at(29, 17), .84),
            # 篱笆：洞儿本身用 bamboo-gate 点出「隔著篱笆洞儿一看」。
            # gate 不生成 footprint，正好压在 fence_hole 锚点格。
            ('bamboo-gate', *at(16, 24), .78),
            # 两扇木屏作风篱笆的其余部分，摆在走廊之外（不压 L 形路线）。
            ('wood-screen', *at(12, 21), .72),
            ('wood-screen', *at(29, 10), .70),
            # 花架下的石头：避开走廊与锚点格（脚本自动跳过锚点格 footprint）。
            ('garden-rock', *at(14, 21), .74),
            ('garden-rock', *at(30, 24), .70),
        ],
        # 甬路：园路到篱笆洞的一段石板，点出「宝玉来到花架」的路线。
        'terraces': [[9, 28, 7, 2, 'path']],
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
