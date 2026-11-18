#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补上项目一直缺的两张大舞台：大观园全景（daguanyuan）与省亲正殿（shengqin）。

为什么这两张图一直缺、现在为什么必须补
------------------------------------
第 17 回「大观园试才题对额」35 个节点全挤在 `dinner`（贾母院后房与晚膳），
第 18 回元妃省亲的「正殿换匾受礼」又借 `central`（荣禧堂）。两回的制作记录都写明
这是同一处缺口：「大观园正殿/行宫仍无专图，用 dinner 占位（与第 17 回同一缺口，
daguanyuan 图待补）」。读者因此看见贾政带着宝玉在一间晚膳屋里游园、元妃在荣禧堂
受礼——方位全乱。这两张图就是补这个缺口。

范围边界（**只建图 + 改 scene 字段，不动剧情文案与锚点名**）
--------------------------------------------------------
第 17 回 35 节点虽然 place 分了 10 处景点，但 actions 里的 at 只用了 8 个锚点名
（都是 dinner 图的名字：grandmother_place / feng_place / grandmother_greet /
baoyu_greet / tea_place / wang_place / daiyu_place / liwan_place）。
第 18 回受礼段 8 节点（C18-063~070）用 central 的 6 个锚点名
（ceremonial_gate / rongxi_steps / rongxi_center / rongxi_door / east_door / east_court）。
所以新图**沿用这些锚点名**，剧情只把 `scene` 从 dinner/central 改成新场景 id，
`focus` / `actions[].at` / 中文文案一律不动。这样零锚点重映射风险，存档按 node id
定位也不受影响。

形制依据（第十七、十八回底本）
------------------------------
第十七回写大观园：「崇阁巍峨，层楼高起……一带清流，从花木深处泻于石隙之下」；
「迎面一带翠嶂挡在前面，白石崚嶒」；「若干亭榭，无字标题，任是花柳山水，也断不能生色」；
「有凤来仪」（潇湘馆，千竿翠竹）、「稻香村」（田舍）、「沁芳亭」诸景。
→ 图上：北面一道翠嶂（湖石成片），一条清流从石隙泻出横贯园子，园门内一座牌坊，
  亭榭分散在两岸，竹丛与田舍各占一角。原书未给精确尺寸方位，摆位属改编，
  在 scene-places 的 note 里标明。

第十八回写省亲：「贾妃在轿内看此园内外如此豪华，因默默叹息奢华过费」；
「元妃下了轿……至行宫，即有太监跪请升座受礼」；「（正殿）此系正殿，外臣未敢擅拟」；
「荣国太君及女眷等自东阶升月台上排班」。
→ 图上一条南北中轴：南端牌坊（行宫外）→ 石阶 → 正殿门 → 殿中御座，
  东侧另设东阶与女眷立处。正殿**故意不题匾**（原文情节，不可补匾）。

资产取舍（不生新图，复用既有素材）
----------------------------------
- 大观园：`main-hall`/`rongxi-hall` 作亭榭正厅，`flower-gate` 作园门，
  `taixu-gate` 作园内牌坊，`garden-tree`/`garden-rock` 成片作翠嶂与花木，
  `reeds` 点水岸，`bamboo-gate` 点潇湘馆。
- 省亲正殿：`taixu-hall`（仙宫规格，1100×784，此前未上过图）作行宫正殿，
  `taixu-gate`（560×530）作牌坊/仪门，`screen-wall` 作影壁，`main-hall` 作配殿。
  theme 用 `formal`（板地，庄重），与园子的 `garden`（石地）区分。

坐标坑（写图前必须记住，都是踩过的）
------------------------------------
- Tiled 128×64 菱形，unit = tileheight = 64（不是 128）；
  锚点 col = x/64 - 0.5、row = y/64 - 0.5（落格心）。
- 引擎路线走廊是 L 形，且在删 blocker 之前生成 → 摆石头/家具前先确认走廊不经过它。
- 要站人的锚点必须在某条 route 的 anchor_ids 里；名字存在 ≠ 可通行。
- 建筑（*-hall / is_shell）的脚线由 eave() 钉在地坪南沿，列号才管屏幕高度。
- 写完必须跑 npm run check:anchors。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

MAP_DIR = ROOT / 'maps'


def at(c, r, dx=0.0, dy=0.0):
    """屏幕像素偏移 → 等距格坐标（同 stage_defs.at）。"""
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {
    # ==================================================================
    # 大观园全景：第 17 回游园题匾的舞台
    #
    # 8 个锚点沿用 dinner 图，按游览动线自南（园门）向北（正殿）铺开：
    #   grandmother_place  园门内・翠嶂前（起点，贾珍/贾政入园）
    #   wang_place         园门内・贾政立处（题额发问）
    #   feng_place         游廊・清客立处
    #   tea_place          沁芳亭・茶座（众清客围随）
    #   daiyu_place        有凤来仪（潇湘馆，宝玉题「有凤来仪」）
    #   liwan_place        稻香村（李纨处）
    #   baoyu_greet        沁芳闸桥边（宝玉随行）
    #   grandmother_greet  正殿前月台（题额收束）
    #
    # 分区（zones 用 A0..A4，都进可走集合）：
    #   A0 前园（园门→翠嶂）  col 8-32,  row 26-37
    #   A1 中轴甬路          col 18-22, row 14-30
    #   A2 沁芳亭（西）      col 6-17,  row 18-27
    #   A3 有凤来仪/稻香村（东） col 23-35, row 16-28
    #   A4 正殿前月台（北）  col 14-28, row 8-16
    # 一条清流自西北石隙斜贯到东南（water），桥（terraces path）跨在中轴。
    # ==================================================================
    'daguanyuan': {
        'name': '大观园 · 全景',
        'theme': 'garden',
        'zones': [
            [8, 26, 24, 12],     # A0 前园
            [18, 14, 5, 16],     # A1 中轴甬路
            [6, 18, 12, 10],     # A2 沁芳亭（西岸）
            [23, 16, 13, 12],    # A3 东岸庭院
            [14, 8, 15, 8],      # A4 正殿前月台
        ],
        'anchors': {
            'grandmother_place': [20, 29],   # 园门内・翠嶂前
            'wang_place': [21, 26],          # 贾政立处
            'feng_place': [20, 23],          # 游廊・清客
            'tea_place': [12, 23],           # 沁芳亭・茶座（西）
            'daiyu_place': [29, 21],         # 有凤来仪（东）
            'liwan_place': [32, 26],         # 稻香村（东）
            'baoyu_greet': [20, 18],         # 沁芳闸桥边
            'grandmother_greet': [20, 12],   # 正殿前月台
        },
        'routes': {
            # 中轴：园门 → 翠嶂 → 游廊 → 桥 → 月台（一条主动线串起全程）
            'axis': ['grandmother_place', 'wang_place', 'feng_place', 'baoyu_greet', 'grandmother_greet'],
            # 西支路：沁芳亭茶座
            'west': ['feng_place', 'tea_place'],
            # 东支路：有凤来仪、稻香村
            'east': ['feng_place', 'daiyu_place', 'liwan_place'],
        },
        'labels': [
            ['大观园', 20, 35], ['翠嶂', 20, 30], ['沁芳亭', 10, 21],
            ['有凤来仪', 30, 19], ['稻香村', 33, 27], ['正殿', 20, 9],
        ],
        'props': [
            # 园门：南侧粉墙留洞（walls  south 段不封），门内一座牌坊
            ('taixu-gate', *at(20, 34), .92),
            # 翠嶂：园门迎面的白石崚嶒，成片（避开中轴走廊 col 20-22）
            ('garden-rock', *at(17, 30), .90),
            ('garden-rock', *at(15, 28), .84),
            ('garden-rock', *at(24, 29), .78),
            ('garden-rock', *at(26, 31), .72),
            # 沁芳亭（西岸）：一座厅榭 + 竹丛 + 花树
            ('main-hall', *at(10, 25), .70, 'A2'),
            ('bamboo-gate', *at(11, 21), .88),
            ('garden-tree', *at(10, 27), .92),
            ('garden-tree', *at(14, 26), .86),
            ('garden-tree', *at(12, 19), .80),
            # 有凤来仪（东岸）：千竿翠竹 —— 以竹门点题
            ('bamboo-gate', *at(29, 18), .96),
            ('garden-tree', *at(32, 20), .84),
            ('garden-tree', *at(35, 24), .80),
            # 稻香村（东岸）：田舍用 rongxi-hall 的小比例代（无专用农舍图在此）
            ('rongxi-hall', *at(30, 28), .58, 'A3'),
            ('reeds', *at(34, 28), .70),
            # 正殿前月台（北）：园内正厅，配两株花树
            ('rongxi-hall', *at(20, 10), .78, 'A4'),
            ('garden-tree', *at(15, 11), .82),
            ('garden-tree', *at(27, 12), .80),
            # 水边芦苇（西北石隙泻出处，收在沁芳亭锚点一屏内）
            ('reeds', *at(14, 21), .66),
        ],
        # 清流：自西北石隙斜向东南。两段矩形近似斜带，压过中轴处由桥面盖住。
        'water': [[8, 21, 12, 2], [20, 24, 12, 2]],
        # 桥：中轴上一段石板，跨过水带（col 20-22, row 23-25）
        'terraces': [[19, 22, 4, 4, 'path'], [18, 29, 6, 2, 'path']],
        # 园墙：北、东、西三面；南面只在园门两侧留墙（中段 col 18-22 留洞作门）
        'walls': [[8, 26, 8, 38], [32, 26, 32, 38], [8, 26, 32, 26],
                  [8, 38, 18, 38], [22, 38, 32, 38]],
        'flowerbeds': True,
    },

    # ==================================================================
    # 省亲正殿（行宫）：第 18 回元妃换匾受礼的舞台
    #
    # 6 个锚点沿用 central 图，按南北中轴 + 东阶排布：
    #   ceremonial_gate  南端牌坊（行宫外，元春下轿看匾）
    #   rongxi_steps     正殿石阶（贾政等迎候）
    #   rongxi_door      殿门（太监跪请）
    #   rongxi_center    殿中御座（元妃升座受礼）—— 正殿故意不题匾
    #   east_door        东阶（荣国太君升月台）
    #   east_court       东阶女眷立处
    #
    # 分区：
    #   A0 行宫外广场  col 12-28, row 26-38（牌坊、下轿）
    #   A1 中轴丹陛    col 18-22, row 14-28（石阶、殿门）
    #   A2 正殿        col 14-26, row 7-15（御座）
    #   A3 东阶女眷处  col 27-34, row 16-26
    # ==================================================================
    'shengqin': {
        'name': '省亲别墅 · 正殿',
        'theme': 'formal',
        'zones': [
            [12, 26, 16, 12],    # A0 行宫外广场
            [18, 14, 5, 14],     # A1 中轴丹陛
            [14, 7, 13, 8],      # A2 正殿
            [27, 16, 8, 11],     # A3 东阶女眷处
        ],
        'anchors': {
            'ceremonial_gate': [20, 32],
            'rongxi_steps': [20, 24],
            'rongxi_door': [20, 17],
            'rongxi_center': [20, 11],
            'east_door': [29, 20],
            'east_court': [31, 23],
        },
        'routes': {
            'axis': ['ceremonial_gate', 'rongxi_steps', 'rongxi_door', 'rongxi_center'],
            'east': ['rongxi_steps', 'east_door', 'east_court'],
        },
        'labels': [
            ['省亲别墅', 20, 36], ['牌坊', 20, 33], ['丹陛', 20, 22],
            ['正殿', 20, 8], ['东阶', 31, 19],
        ],
        'props': [
            # 行宫外牌坊：元妃下轿处
            ('taixu-gate', *at(20, 35), 1.0),
            # 影壁： entrance 内，遮住直视正殿（皇家仪制）
            ('screen-wall', *at(20, 29), .72),
            # 正殿：仙宫规格的行宫正殿，殿脚钉在 A2 地坪南沿
            ('taixu-hall', *at(20, 9), .92, 'A2'),
            # 配殿两座（东西）
            ('main-hall', *at(13, 14), .58),
            ('main-hall', *at(28, 13), .58),
            # 丹陛两侧花树，庄重对称（原文「两边」排班，对称是明写）
            ('garden-tree', *at(16, 21), .80),
            ('garden-tree', *at(25, 21), .80),
            # 东阶：女眷立处
            ('flower-gate', *at(29, 24), .82),
        ],
        'terraces': [[19, 14, 3, 14, 'court'], [18, 32, 5, 2, 'path']],
        # 宫墙：北、东、西三面，南面牌坊处留洞
        'walls': [[12, 26, 12, 38], [28, 26, 28, 38], [12, 26, 28, 26],
                  [12, 38, 18, 38], [22, 38, 28, 38]],
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
                     'writing-desk', 'screen-wall') and [c, r] not in anchor_cells:
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
