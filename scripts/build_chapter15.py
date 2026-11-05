#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-fifteen's stages, script and section table.

第十五回 · 王凤姐弄权铁槛寺 · 秦鲸卿得趣馒头庵

Chapter fifteen owns this generator; nothing here touches an earlier chapter.

Outputs:
  maps/c15_road.tmj          新舞台：出城大路 · 铁槛寺道
  maps/c15_tiejian.tmj        新舞台：铁槛寺 · 寺门与停灵内殿
  maps/c15_shuiyue.tmj        新舞台：水月庵（馒头庵）· 净室与殿上
  maps/c15_village.tmj        新舞台：铁槛寺下村庄 · 庄院与纺车
  design/chapter15-story.json   节点 C15-001..
  design/chapter15-sections.json

本回用：maps/c14_funeral.tmj（宁府会芳园灵前）、maps/c13_funeral.tmj（宁府上房与停灵）。

四张地图的分工：
  c15_road     出城大路：宁府送殡出城，一路祭棚、鼓乐、幢幡宝盖；凤姐的车在此
                邀宝玉同车，两骑马压地飞来报「这里有下处」。
  c15_tiejian  铁槛寺：宁荣二公当日修造，阴阳两宅俱已预备妥贴，为送灵人口寄居。
                原文写「寺门」与「内殿偏室」（安灵之处），还有外面款待亲友的场面。
  c15_shuiyue  水月庵（馒头庵）：离铁槛寺不远，凤姐嫌铁槛寺不方便，早遣人来
                腾出两间房子作下处。净虚求情、秦钟与智能儿相会都在此处。
  c15_village  铁槛寺下村庄：凤姐打尖、宝玉玩纺车、二丫头纺线的地方。
                原文写「庄农人家无多房舍」「一间房前，炕上有个纺车」。

人物：水溶、净虚、智能儿、二丫头、旺儿为本回新立绘；凤姐、宝玉、秦钟、
贾珍、贾蓉、平儿、宝珠复用既有资产。智善（净虚徒弟）在原著中只列名一次，
不另造人出场；秦业年迈多病不能在此，只命秦钟等待安灵，作转述。

Usage: python3 scripts/build_chapter15.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

BACKUP = ROOT / 'artifacts/backups/2026-11-03-chapter15'
PUBLISH_MAP = True
MAP_DIR = ROOT / 'maps' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter15'
STAGE_DIR = ROOT / 'design' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter15'


def at(c, r, dx=0.0, dy=0.0):
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {
    # 出城大路：宁府送殡出城，一路热闹非常。凤姐的车在此邀宝玉同车。
    'c15_road': {
        'name': '出城大路 · 铁槛寺道',
        'theme': 'street',
        # A0（行 12–25）是大路本体；A1（行 8–11）北侧的祭棚区。
        'zones': [[11, 12, 20, 14, True, 'A0'], [13, 8, 12, 4, False]],
        'anchors': {
            'street': [20, 25],
            'gate': [20, 22],
            'road': [20, 19],
            'carriage': [22, 17],
            'horse': [17, 17],
            'tent': [18, 10],
            'field': [26, 15],
        },
        'routes': {
            'main': ['street', 'gate', 'road', 'carriage'],
            'to_horse': ['road', 'horse'],
            'to_tent': ['road', 'tent'],
            'to_field': ['road', 'field'],
        },
        'labels': [['出城大路', 20, 14], ['祭棚', 19, 9]],
        'props': [
            # 送殡的仪仗：幢幡宝盖、执事、鼓乐厅。
            ('sedan-chair', *at(24, 18, 0, 0), .72, 'A0'),
            ('canopy-bed', *at(19, 15, 0, 0), .60, 'A0'),
            ('stage-platform', *at(16, 14, 0, 0), .58, 'A0'),
            ('official-desk', *at(25, 13, 0, 0), .60, 'A0'),
            ('round-stool', *at(14, 13, 0, 0), .56, 'A0'),
            # 城门外各家的祭棚。
            ('square-table', *at(17, 10, 0, 0), .54),
            ('tea-table', *at(20, 10, 0, 0), .50),
            ('lamp-stand', *at(15, 11, 0, 0), .56),
            ('wine-jars', *at(22, 10, 0, 0), .52),
            # 路边：田野、树木、竹丛、拴马石。
            ('garden-tree', *at(13, 20, 0, 0), .94),
            ('garden-tree', *at(28, 18, 0, 0), .92),
            ('bamboo-cluster', *at(29, 23, 0, 0), .90),
            ('garden-rock', *at(13, 24, 0, 0), .76),
            ('stone-lion', *at(26, 21, 0, 0), .52),
        ],
        'walls': [[11, 12, 31, 12], [11, 12, 11, 26], [31, 12, 31, 26],
                  [11, 26, 31, 26]],
        'terraces': [[18, 18, 5, 5, 'path']],
    },
    # 铁槛寺：寺门、停灵的内殿偏室、外面对亲友的款待。
    'c15_tiejian': {
        'name': '铁槛寺 · 寺门与停灵',
        'theme': 'garden',
        # A0 覆盖行 9–19：内殿偏室在前，寺门前的院子在后，中间由 court 相连。
        # 行 18 必须在地板内，否则 court 锚点落在地板外，人物走不进去。
        'zones': [[13, 9, 16, 11, True, 'A0'], [11, 20, 20, 10, False]],
        'anchors': {
            'street': [21, 27],
            'gate': [20, 21],
            'court': [20, 18],
            'hall_door': [20, 16],
            'hall': [20, 12],
            'side': [16, 12],
            'east': [25, 13],
        },
        'routes': {
            'main': ['street', 'gate', 'court', 'hall_door', 'hall'],
            'to_side': ['hall', 'side'],
            'to_east': ['hall', 'east'],
        },
        'labels': [['铁槛寺', 20, 10], ['寺门', 20, 22], ['停灵内殿', 19, 16]],
        'props': [
            ('zhitong-temple', *at(20, 12), .74, 'A0'),
            ('altar-shrine', *at(23, 11, 0, 0), .50, 'A0'),
            ('brazier', *at(17, 13, 0, 0), .56, 'A0'),
            ('lamp-stand', *at(15, 15, 0, 0), .58, 'A0'),
            ('official-chair', *at(20, 13, 0, 0), .64, 'A0'),
            # 寺门外：款待亲友的棚子与人群。
            ('square-table', *at(24, 24, 0, 0), .58),
            ('round-stool', *at(17, 24, 0, 0), .58),
            ('tea-table', *at(26, 22, 0, 0), .52),
            # 原 at(14,22) 偏西偏北、取景框够不到；北移到寺门外西侧 at(14,19)，
            # 避开 lamp-stand 与 stone-lion，由 hall_door / side 锚点取景到。
            ('bamboo-cluster', *at(14, 19, 0, 0), .96),
            ('bamboo-cluster', *at(28, 25, 0, 0), .90),
            # 原 at(13,27) 偏西偏北、取景框够不到；东移到寺门外南侧 at(19,27)，
            # 与竹丛（at(14,19)）相隔约 9.6 格不重叠，由 street / gate / court 取景到。
            ('garden-tree', *at(19, 27, 0, 0), .98),
            ('garden-tree', *at(29, 19, 0, 0), .92),
            ('garden-rock', *at(16, 28, 0, 0), .78),
            ('stone-lion', *at(18, 22, 0, 0), .54),
            ('stone-lion', *at(23, 22, 0, 0), .54),
        ],
        'walls': [[11, 20, 31, 20], [11, 20, 11, 30], [31, 20, 31, 30],
                  [11, 30, 31, 30]],
        'terraces': [[19, 21, 4, 7, 'path']],
    },
    # 水月庵（馒头庵）：凤姐的下处。殿上顽耍、净室歇息、后面房中智能儿洗茶碗。
    'c15_shuiyue': {
        'name': '水月庵（馒头庵）',
        'theme': 'interior',
        'zones': [[12, 9, 18, 11, True, 'A0'], [14, 21, 12, 7, True, 'B']],
        'anchors': {
            'gate': [20, 22],
            'court': [20, 19],
            'hall_door': [20, 16],
            'hall': [20, 13],
            'nun_seat': [16, 12],
            'back_room': [18, 24],
            'side': [25, 13],
        },
        'routes': {
            'main': ['gate', 'court', 'hall_door', 'hall'],
            'to_nun': ['hall', 'nun_seat'],
            'to_back': ['gate', 'back_room'],
            'to_side': ['hall', 'side'],
        },
        'labels': [['水月庵', 20, 10], ['殿上', 20, 14], ['净室', 17, 23]],
        'props': [
            ('zhitong-temple', *at(20, 12), .70, 'A0'),
            ('altar-shrine', *at(23, 11, 0, 0), .48, 'A0'),
            ('brazier', *at(17, 14, 0, 0), .54, 'A0'),
            ('official-chair', *at(16, 12, 0, 0), .62, 'A0'),
            ('round-stool', *at(24, 14, 0, 0), .58, 'A0'),
            ('tea-table', *at(20, 16, 0, 0), .52, 'A0'),
            # 后面房中：智能儿洗茶碗的地方。
            ('plain-kang', *at(18, 24, 0, 0), .58, 'B'),
            ('tea-table', *at(22, 24, 0, 0), .50, 'B'),
            ('wood-screen', *at(15, 24, 0, 0), .58, 'B'),
            ('bamboo-cluster', *at(26, 26, 0, 0), .88),
            # 原 at(12,24) 偏西偏北、取景框够不到；北移到院西缘 at(13,19)，
            # 避开正殿与后房，由 hall_door / nun_seat 锚点取景到。
            ('garden-tree', *at(13, 19, 0, 0), .94),
        ],
        'walls': [[14, 21, 26, 21], [14, 21, 14, 28], [26, 21, 26, 28]],
        'terraces': [[19, 21, 3, 5, 'path']],
    },
    # 铁槛寺下村庄：凤姐打尖、宝玉玩纺车的地方。
    'c15_village': {
        'name': '铁槛寺下 · 村庄',
        'theme': 'garden',
        'zones': [[12, 20, 18, 10, False], [14, 10, 8, 8, True, 'B']],
        'anchors': {
            'road': [20, 28],
            'yard': [20, 25],
            'door': [18, 20],
            'room': [17, 14],
            'spindle': [20, 13],
            'field': [26, 24],
        },
        'routes': {
            'main': ['road', 'yard', 'door', 'room'],
            'to_spindle': ['room', 'spindle'],
            'to_field': ['yard', 'field'],
        },
        'labels': [['村庄', 20, 27], ['庄屋', 17, 11], ['田亩', 26, 25]],
        'props': [
            ('farm-house', *at(17, 13), .70, 'B'),
            ('plain-kang', *at(16, 13, 0, 0), .58, 'B'),
            ('farm-stove', *at(20, 14, 0, 0), .54, 'B'),
            # 纺车：宝玉见了不知何物，上来拧转作耍。用既有 square-stool 的意象不对，
            # 这里用 writing-desk 摆成案上的纺车，位置在炕边。
            ('writing-desk', *at(20, 13, 0, 0), .52, 'B'),
            ('round-stool', *at(22, 15, 0, 0), .54, 'B'),
            ('tea-table', *at(15, 15, 0, 0), .48, 'B'),
            # 庄农的田亩与农具：宝玉见了锹、橛、锄、犁皆以为奇。
            ('garden-rock', *at(27, 23, 0, 0), .72),
            ('bamboo-cluster', *at(14, 24, 0, 0), .90),
            ('garden-tree', *at(25, 28, 0, 0), .96),
            ('garden-tree', *at(13, 27, 0, 0), .90),
        ],
        'walls': [[12, 20, 30, 20], [12, 20, 12, 30], [30, 20, 30, 30]],
        'terraces': [[18, 24, 5, 5, 'path']],
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

    indoor = scene.get('indoor_zones', {})
    zones = []
    rects = {}
    for i, z in enumerate(scene['zones']):
        c, r, w, h = z[:4]
        zid = z[5] if len(z) > 5 else f'A{i}'
        props = []
        if (len(z) > 4 and z[4]) or indoor.get(zid):
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
        indoor_zone = prop[5] if len(prop) > 5 else None
        if asset not in assets:
            continue
        a = assets[asset]
        x = (c - r) * 64 + (a['width'] / 2 - a['anchor'][0]) * scale
        y = (c + r + 1) * 32 + (a['height'] - a['anchor'][1]) * scale
        art_props = [
            {'name': 'asset', 'value': asset, 'type': 'string'},
            {'name': 'visibility',
             'value': 'interior' if indoor_zone else ('exterior' if is_shell(asset) else 'always'),
             'type': 'string'}]
        if interior_zone or indoor_zone:
            art_props.append({'name': 'interiorZone', 'value': interior_zone or indoor_zone,
                              'type': 'string'})
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
                      + ([{'name': 'flowerbeds', 'type': 'bool', 'value': False}]),
    }
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    (MAP_DIR / f'{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')
    return len(scene['anchors'])


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

SECTIONS = [
    ('c15-prince', '宁国府 · 北静王赠念珠', 'c14_funeral'),
    ('c15-road', '出城大路 · 凤姐邀宝玉同车', 'c15_road'),
    ('c15-village', '铁槛寺下 · 村庄打尖', 'c15_village'),
    ('c15-spinning', '村庄 · 纺车与二丫头', 'c15_village'),
    ('c15-temple', '铁槛寺 · 安灵', 'c15_tiejian'),
    ('c15-shuiyue', '水月庵 · 智能儿倒茶', 'c15_shuiyue'),
    ('c15-petition', '水月庵 · 净虚求情', 'c15_shuiyue'),
    ('c15-night', '水月庵 · 秦钟智能', 'c15_shuiyue'),
    ('c15-letter', '水月庵 · 旺儿修书', 'c15_shuiyue'),
    ('c15-farewell', '铁槛寺 · 照望告别', 'c15_tiejian'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 15, 'paragraphLead': lead, 'textKind': 'adaptation',
                          'layer': layer}}


def say(id, speaker, text, title=None, actions=None, focus=None, layer=None, offscreen=False):
    step = {**current, 'id': id, 'speaker': speaker, 'text': text,
            'title': title or section_titles[current['chapter']],
            'actions': actions or []}
    if focus:
        step['focus'] = focus
    if layer:
        step['source'] = {**current['source'], 'layer': layer}
    if offscreen:
        step['offscreen'] = True
    steps.append(step)


def show(a, p):
    return {'type': 'show', 'actor': a, 'at': p}


def hide(a):
    return {'type': 'hide', 'actor': a}


def move(a, *p):
    return {'type': 'move', 'actor': a, 'via': list(p)}


def parallel(*m):
    return {'type': 'parallel', 'moves': list(m)}


def effect(a, kind):
    return {'type': 'effect', 'actor': a, 'kind': kind, 'duration': 1.8}


# ===== c15-prince : 北静王赠念珠 =========================
# 原文位置：水溶「名不虚传，果然如宝似玉」，又问「衔的那宝贝在那里」，
# 看了又念了那上头的字，问「果灵验否」，并解下腕上的鹡鸰香念珠相赠。
section('c15-prince', 'c14_funeral', '会芳园 · 灵前', 'garden',
        '话说宝玉举目见北静王水溶头上戴著洁白簪缨银翅王帽')
say('C15-001', 'narrator',
    '话说宝玉举目见北静王水溶头上戴著洁白簪缨银翅王帽，'
    '穿著江牙海水五爪坐龙白蟒袍，系著碧玉红鞓带，面如美玉，目似明星，'
    '真好秀丽人物。宝玉忙抢上来参见，水溶连忙从轿内伸出手来挽住。',
    '面如美玉，目似明星',
    [show('baoyu', 'side'), show('shui_rong', 'garden')])
say('C15-002', 'narrator',
    '见宝玉戴著束发银冠，勒著双龙出海抹额，穿著白蟒箭袖，围著攒珠银带，'
    '面若春花，目如点漆。水溶笑道：「名不虚传，果然如宝似玉。」'
    '因问：「衔的那宝贝在那里？」宝玉见问，连忙从衣内取了递与过去。',
    '名不虚传，果然如宝似玉', [move('baoyu', 'side', 'garden')])
say('C15-003', 'shui_rong',
    '水溶细细的看了，又念了那上头的字，因问：「果灵验否？」'
    '贾政忙道：「虽如此说，只是未曾试过。」'
    '水溶一面极口称奇道异，一面理好彩绦，亲自与宝玉带上，'
    '又携手问宝玉几岁，读何书。宝玉一一的答应。', '亲自与宝玉带上',
    [effect('shui_rong', 'greet')])
say('C15-004', 'shui_rong',
    '水溶见他语言清楚，谈吐有致，一面又向贾政笑道：「令郎真乃龙驹凤雏，'
    '非小王在世翁前唐突，将来雏凤清于老凤声，未可量也。」'
    '贾政忙陪笑道：「犬子岂敢谬承金奖。赖蕃郡余祯，果如是言，'
    '亦荫生辈之幸矣。」', '令郎真乃龙驹凤雏',
    [effect('shui_rong', 'greet')])
say('C15-005', 'shui_rong',
    '水溶又道：「只是一件，令郎如是资质，想老太夫人，夫人辈自然钟爱极矣，'
    '但吾辈后生，甚不宜钟溺，钟溺则未免荒失学业。'
    '昔小王曾蹈此辙，想令郎亦未必不如是也。'
    '若令郎在家难以用功，不妨常到寒第。小王虽不才，却多蒙海上众名士'
    '凡至都者，未有不另垂青目。是以寒第高人颇聚。'
    '令郎常去谈会谈会，则学问可以日进矣。」贾政忙躬身答应。',
    '不妨常到寒第', [effect('shui_rong', 'idle')])
say('C15-006', 'narrator',
    '水溶又将腕上一串念珠卸了下来，递与宝玉道：「今日初会，仓促竟无敬贺之物，'
    '此是前日圣上亲赐鹡鸰香念珠一串，权为贺敬之礼。」'
    '宝玉连忙接了，回身奉与贾政。贾政与宝玉一齐谢过。',
    '圣上亲赐鹡鸰香念珠一串', [effect('shui_rong', 'greet'), effect('baoyu', 'greet')])
say('C15-007', 'shui_rong',
    '于是贾赦、贾珍等一齐上来请回舆，水溶道：「逝者已登仙界，'
    '非碌碌你我尘寰中之人也。小王虽上叨天恩，虚邀郡袭，'
    '岂可越仙輀而进也？」贾赦等见执意不从，只得告辞谢恩回来，'
    '命手下掩乐停音，滔滔然将殡过完，方让水溶回舆去了。',
    '岂可越仙輀而进也', [effect('shui_rong', 'greet')])

# ===== c15-road : 出城大路，凤姐邀宝玉同车 ================
# 原文位置：「刚至城门前，又有贾赦、贾政、贾珍等诸同僚属下各家祭棚接祭，
# 一一的谢过，然后出城，竟奔铁槛寺大路行来」，接着是凤姐唤宝玉同车，
# 两骑马压地飞来报「这里有下处」。
section('c15-road', 'c15_road', '出城大路', 'road',
        '且说宁府送殡，一路热闹非常')
say('C15-010', 'narrator',
    '且说宁府送殡，一路热闹非常。刚至城门前，又有贾赦、贾政、贾珍等'
    '诸同僚属下各家祭棚接祭，一一的谢过，然后出城，'
    '竟奔铁槛寺大路行来。', '竟奔铁槛寺大路行来',
    [show('jia_zhen', 'road'), show('feng', 'carriage'),
     show('baoyu', 'horse'), show('qin_zhong', 'road')])
say('C15-011', 'narrator',
    '彼时贾珍带贾蓉来到诸长辈前，让坐轿上马，因而贾赦一辈的各自上了车轿，'
    '贾珍一辈的也将要上马。凤姐儿因记挂著宝玉，怕他在郊外纵性逞强，'
    '不服家人的话，贾政管不著这些小事，惟恐有个失闪，难见贾母，'
    '因此便命小厮来唤他。宝玉只得来到他车前。', '宝玉只得来到他车前',
    [move('baoyu', 'horse', 'road', 'carriage')])
say('C15-012', 'feng',
    '凤姐笑道：「好兄弟，你是个尊贵人，女孩儿一样的人品，'
    '别学他们猴在马上。下来，咱们姐儿两个坐车，岂不好？」'
    '宝玉听说，忙下了马，爬入凤姐车上，二人说笑前来。',
    '咱们姐儿两个坐车', [effect('feng', 'greet')])
say('C15-013', 'narrator',
    '不一时，只见从那边两骑马压地飞来，离凤姐车不远，一齐蹿下来，'
    '扶车回说：「这里有下处，奶奶请歇更衣。」'
    '凤姐急命请邢夫人王夫人的示下，那人回来说：「太太们说不用歇了，'
    '叫奶奶自便罢。」凤姐听了，便命歇了再走。',
    '这里有下处，奶奶请歇更衣',
    [move('feng', 'carriage', 'road'), show('messenger', 'road')])
say('C15-014', 'narrator',
    '宝玉在车内急命请秦相公。那时秦钟正骑马随著他父亲的轿，'
    '忽见宝玉的小厮跑来，请他去打尖。秦钟看时，只见凤姐儿的车往北而去，'
    '后面拉著宝玉的马，搭著鞍笼，便知宝玉同凤姐坐车，'
    '自己也便带马赶上去，同入一庄门内。', '自己也便带马赶上去',
    [move('qin_zhong', 'road', 'gate'), move('feng', 'road', 'gate'),
     move('baoyu', 'carriage', 'road')])

# ===== c15-village : 村庄打尖 ===========================
section('c15-village', 'c15_village', '铁槛寺下 · 村庄', 'yard',
        '早有家人将众庄汉撵尽')
say('C15-020', 'narrator',
    '早有家人将众庄汉撵尽。那庄农人家无多房舍，婆娘们无处回避，'
    '只得由他们去了。那些村姑庄妇见了凤姐、宝玉、秦钟的人品衣服，'
    '礼数款段，岂有不爱看的？', '岂有不爱看的',
    [show('feng', 'yard'), show('baoyu', 'yard'), show('qin_zhong', 'yard')])
say('C15-021', 'narrator',
    '一时凤姐进入茅堂，因命宝玉等先出去顽顽。'
    '宝玉等会意，因同秦钟出来，带著小厮们各处游顽。'
    '凡庄农动用之物，皆不曾见过。', '因命宝玉等先出去顽顽',
    [move('feng', 'yard', 'door', 'room'),
     parallel(move('baoyu', 'yard', 'field'), move('qin_zhong', 'yard', 'field'))])
say('C15-022', 'baoyu',
    '宝玉一见了锹、橛、锄、犁等物，皆以为奇，不知何项所使，其名为何。'
    '小厮在旁一一的告诉了名色，说明原委。'
    '宝玉听了，因点头叹道：「怪道古人诗上说，谁知盘中餐，粒粒皆辛苦，'
    '正为此也。」', '粒粒皆辛苦', [effect('baoyu', 'greet')])

# ===== c15-spinning : 纺车与二丫头 ======================
section('c15-spinning', 'c15_village', '村庄 · 庄屋', 'spindle',
        '一面说，一面又至一间房前')
say('C15-030', 'narrator',
    '一面说，一面又至一间房前，只见炕上有个纺车，'
    '宝玉又问小厮们：「这又是什么？」小厮们又告诉他原委。'
    '宝玉听说，便上来拧转作耍，自为有趣。', '炕上有个纺车',
    [move('baoyu', 'field', 'door', 'room'), move('qin_zhong', 'field', 'yard')])
say('C15-031', 'narrator',
    '只见一个约有十七八岁的村庄丫头跑了来乱嚷：「别动坏了！」'
    '众小厮忙断喝拦阻。宝玉忙丢开手，陪笑说道：'
    '「我因为没见过这个，所以试他一试。」', '别动坏了',
    [show('er_ya_tou', 'room'), move('er_ya_tou', 'room', 'spindle'),
     effect('baoyu', 'anger')])
say('C15-032', 'er_ya_tou',
    '那丫头道：「你们那里会弄这个，站开了，我纺与你瞧。」'
    '秦钟暗拉宝玉笑道：「此卿大有意趣。」宝玉一把推开，笑道：'
    '「该死的！再胡说，我就打了。」说著，只见那丫头纺起线来。'
    '宝玉正要说话时，只听那边老婆子叫道：「二丫头，快过来！」'
    '那丫头听见，丢下纺车，一径去了。', '我纺与你瞧',
    [effect('er_ya_tou', 'idle')])
say('C15-033', 'narrator',
    '宝玉怅然无趣。只见凤姐儿打发人来叫他两个进去。'
    '凤姐洗了手，换衣服抖灰，问他们换不换。宝玉不换，只得罢了。'
    '家下仆妇们将带著行路的茶壶茶杯、十锦屉盒，各样小食端来，'
    '凤姐等吃过茶，待他们收拾完毕，便起身上车。',
    '宝玉怅然无趣', [move('feng', 'room', 'yard'), effect('baoyu', 'rest')])
say('C15-034', 'narrator',
    '外面旺儿预备下赏封，赏了本村主人。庄妇等来叩赏。'
    '凤姐并不在意，宝玉却留心看时，内中并无二丫头。'
    '一时上了车，出来走不多远，只见迎头二丫头怀里抱著他小兄弟，'
    '同著几个小女孩子说笑而来。宝玉恨不得下车跟了他去，'
    '料是众人不依的，少不得以目相送，争奈车轻马快，一时展眼无踪。',
    '一时展眼无踪', [show('er_ya_tou', 'yard'), move('er_ya_tou', 'yard', 'field')])

# ===== c15-temple : 铁槛寺安灵 =========================
section('c15-temple', 'c15_tiejian', '铁槛寺 · 停灵内殿', 'hall',
        '走不多时，仍又跟上大殡了')
say('C15-040', 'narrator',
    '走不多时，仍又跟上大殡了。早有前面法鼓金铙，幢幡宝盖：'
    '铁槛寺接灵众僧齐至。少时到入寺中，另演佛事，重设香坛。'
    '安灵于内殿偏室之中，宝珠安于里寝室相伴。', '安灵于内殿偏室之中',
    [show('feng', 'gate'), show('bao_zhu', 'hall'),
     move('feng', 'gate', 'court', 'hall_door', 'hall')])
say('C15-041', 'narrator',
    '外面贾珍款待一应亲友，也有扰饭的，也有不吃饭而辞的，'
    '一应谢过乏，从公侯伯子男一起一起的散去，至未末时分方才散尽了。'
    '里面的堂客皆是凤姐张罗接待，先从显官诰命散起，也到晌午大错时方散尽了。',
    '从公侯伯子男一起一起的散去', [effect('jia_zhen', 'idle')])
say('C15-042', 'narrator',
    '只有几个亲戚是至近的，等做过三日安灵道场方去。'
    '那时邢、王二夫人知凤姐必不能来家，也便就要进城。'
    '王夫人要带宝玉去，宝玉乍到郊外，那里肯回去，只要跟凤姐住著。'
    '王夫人无法，只得交与凤姐便回来了。',
    '只要跟凤姐住著', [show('baoyu', 'hall'), effect('baoyu', 'rest')])

# ===== c15-shuiyue : 智能儿倒茶 ========================
# 原文位置：原来这馒头庵就是水月庵，离铁槛寺不远；凤姐嫌铁槛寺不方便，
# 早遣人来和馒头庵的姑子净虚说了，腾出两间房子来作下处。
section('c15-shuiyue', 'c15_shuiyue', '水月庵 · 殿上', 'hall',
        '原来这铁槛寺原是宁荣二公当日修造')
say('C15-050', 'narrator',
    '原来这铁槛寺原是宁荣二公当日修造，现今还是有香火地亩布施，'
    '以备京中老了人口，在此便宜寄放。其中阴阳两宅俱已预备妥贴，'
    '好为送灵人口寄居。不想如今后辈人口繁盛，其中贫富不一，或性情参商。',
    '阴阳两宅俱已预备妥贴', [show('feng', 'court'), show('baoyu', 'hall')])
say('C15-051', 'narrator',
    '即今秦氏之丧，族中诸人皆权在铁槛寺下榻，独有凤姐嫌不方便，'
    '因而早遣人来和馒头庵的姑子净虚说了，腾出两间房子来作下处。'
    '原来这馒头庵就是水月庵，因他庙里做的馒头好，就起了这个浑号，'
    '离铁槛寺不远。', '腾出两间房子来作下处',
    [move('feng', 'hall', 'court'), show('jing_xu', 'gate')])
say('C15-052', 'narrator',
    '当下和尚工课已完，奠过茶饭，贾珍便命贾蓉请凤姐歇息。'
    '凤姐见还有几个妯娌陪著女亲，自己便辞了众人，'
    '带了宝玉、秦钟往水月庵来。原来秦业年迈多病，不能在此，'
    '只命秦钟等待安灵罢了。', '带了宝玉、秦钟往水月庵来',
    [move('feng', 'court', 'gate'), show('jia_rong', 'gate')])
say('C15-053', 'narrator',
    '那秦钟便只跟著凤姐、宝玉，一时到了水月庵，'
    '净虚带领智善、智能两个徒弟出来迎接，大家见过。'
    '凤姐等来至净室更衣净手毕，因见智能儿越发长高了，'
    '模样儿越发出息了，因说道：「你们师徒怎么这些日子也不往我们那里去？」',
    '模样儿越发出息了',
    [show('qin_zhong', 'gate'), show('zhi_neng', 'gate'),
     move('feng', 'gate', 'court', 'hall_door', 'hall'),
     move('baoyu', 'hall', 'gate'), move('qin_zhong', 'gate', 'court')])
say('C15-054', 'jing_xu',
    '净虚道：「可是这几天都没工夫，因胡老爷府里产了公子，'
    '太太送了十两银子来这里，叫请几位师父念三日血盆经，'
    '忙的没个空儿，就没来请奶奶的安。」',
    '念三日血盆经', [effect('jing_xu', 'greet')])
say('C15-055', 'baoyu',
    '且说秦钟、宝玉二人正在殿上顽耍，因见智能过来，宝玉笑道：「能儿来了。」'
    '秦钟道：「理那东西作什么？」宝玉笑道：「你别弄鬼，'
    '那一日在老太太屋里，一个人没有，你搂着他作什么？这会子还哄我。」'
    '秦钟笑道：「这可是没有的话。」',
    '能儿来了', [show('zhi_neng', 'hall'), move('zhi_neng', 'gate', 'hall'),
                  effect('baoyu', 'greet')])
say('C15-056', 'baoyu',
    '宝玉笑道：「有没有也不管你，你只叫住他倒碗茶来我吃，就丢开手。」'
    '秦钟笑道：「这又奇了，你叫他倒去，还怕他不倒？何必要我说呢。」'
    '宝玉道：「我叫他倒的是无情意的，不及你叫他倒的是有情意的。」'
    '秦钟只得说道：「能儿，倒碗茶来给我。」',
    '不及你叫他倒的是有情意的',
    [effect('qin_zhong', 'greet')])
say('C15-057', 'narrator',
    '那智能儿自幼在荣府走动，无人不识，因常与宝玉秦钟顽笑。'
    '他如今大了，渐知风月，便看上了秦钟人物风流，那秦钟也极爱他妍媚，'
    '二人虽未上手，却已情投意合了。今智能见了秦钟，心眼俱开，'
    '走去倒了茶来。秦钟笑道：「给我。」宝玉叫：「给我！」'
    '智能儿抿嘴笑道：「一碗茶也争，我难道手里有蜜！」'
    '宝玉先抢得了，吃著，方要问话，只见智善来叫智能去摆茶碟子，'
    '一时来请他两个去吃茶果点心。他两个那里吃这些东西，坐一坐仍出来顽耍。',
    '一碗茶也争', [effect('zhi_neng', 'greet')])

# ===== c15-petition : 净虚求情 =========================
# 原文位置：净虚求凤姐替长安县张家退亲事；凤姐说「你叫他拿三千银子来，
# 我就替他出这口气」，又声明「我一个钱也不要他的」。
section('c15-petition', 'c15_shuiyue', '水月庵 · 净室', 'nun_seat',
        '凤姐也略坐片时，便回至净室歇息')
say('C15-060', 'narrator',
    '凤姐也略坐片时，便回至净室歇息，老尼相送。'
    '此时众婆娘媳妇见无事，都陆续散了，自去歇息，'
    '跟前不过几个心腹常侍小婢，老尼便趁机说道：'
    '「我正有一事，要到府里求太太，先请奶奶一个示下。」',
    '我正有一事，要到府里求太太', [move('feng', 'hall', 'court', 'gate', 'back_room'),
                                     show('jing_xu', 'back_room')])
say('C15-061', 'jing_xu',
    '老尼道：「阿弥陀佛！只因当日我先在长安县内善才庵内出家的时节，'
    '那时有个施主姓张，是大财主。他有个女儿小名金哥，'
    '那年都往我庙里来进香，不想遇见了长安府府太爷的小舅子李衙内。'
    '那李衙内一心看上，要娶金哥，打发人来求亲，'
    '不想金哥已受了原任长安守备的公子的聘定。',
    '他有个女儿小名金哥', [effect('jing_xu', 'greet')])
say('C15-062', 'jing_xu',
    '张家若退亲，又怕守备不依，因此说已有了人家。'
    '谁知李公子执意不依，定要娶他女儿，张家正无计策，两处为难。'
    '不想守备家听了此言，也不管青红皂白，便来作践辱骂，'
    '说一个女儿许几家，偏不许退定礼，就打官司告状起来。'
    '那张家急了，只得著人上京来寻门路，赌气偏要退定礼。',
    '赌气偏要退定礼', [effect('jing_xu', 'idle')])
say('C15-063', 'jing_xu',
    '老尼道：「我想如今长安节度云老爷与府上最契，可以求太太与老爷说声，'
    '打发一封书去，求云老爷和那守备说一声，不怕那守备不依。'
    '若是肯行，张家连倾家孝顺也都情愿。」', '求云老爷和那守备说一声',
    [effect('jing_xu', 'greet')])
say('C15-064', 'feng',
    '凤姐听了笑道：「这事倒不大，只是太太再不管这样的事。」'
    '老尼道：「太太不管，奶奶也可以主张了。」'
    '凤姐听说笑道：「我也不等银子使，也不做这样的事。」'
    '净虚听了，打去妄想，半晌叹道：「虽如此说，张家已知我来求府里，'
    '如今不管这事，张家不知道没工夫管这事，不希罕他的谢礼，'
    '倒象府里连这点子手段也没有的一般。」', '我也不等银子使，也不做这样的事',
    [effect('feng', 'anger')])
say('C15-065', 'feng',
    '凤姐听了这话，便发了兴头，说道：「你是素日知道我的，'
    '从来不信什么是阴司地狱报应的，凭是什么事，我说要行就行。'
    '你叫他拿三千银子来，我就替他出这口气。」'
    '老尼听说，喜不自禁，忙说：「有，有！这个不难。」',
    '你叫他拿三千银子来', [effect('feng', 'greet')])
say('C15-066', 'feng',
    '凤姐又道：「我比不得他们扯篷拉牵的图银子。这三千银子，'
    '不过是给打发说去的小厮作盘缠，使他赚几个辛苦钱，我一个钱也不要他的。'
    '便是三万两，我此刻也拿的出来。」老尼连忙答应，'
    '又说道：「既如此，奶奶明日就开恩也罢了。」'
    '凤姐道：「你瞧瞧我忙的，那一处少了我？既应了你，'
    '自然快快的了结。」', '我一个钱也不要他的',
    [effect('feng', 'idle')])

# ===== c15-night : 秦钟智能 ============================
section('c15-night', 'c15_shuiyue', '水月庵 · 后面房中', 'back_room',
        '谁想秦钟趁黑无人，来寻智能')
say('C15-070', 'narrator',
    '谁想秦钟趁黑无人，来寻智能。刚至后面房中，只见智能独在房中洗茶碗，'
    '秦钟跑来便搂著亲嘴。智能急的跺脚说：「这算什么！'
    '再这么我就叫唤。」', '再这么我就叫唤',
    [show('qin_zhong', 'back_room'), show('zhi_neng', 'back_room'),
     effect('zhi_neng', 'anger')])
say('C15-071', 'narrator',
    '秦钟求道：「好人，我已急死了。你今儿再不依，我就死在这里。」'
    '智能道：「你想怎样？除非等我出了这牢坑，离了这些人，才依你。」'
    '秦钟道：「这也容易，只是远水救不得近渴。」'
    '说著，一口吹了灯，满屋漆黑，将智能抱到炕上，就云雨起来。',
    '除非等我出了这牢坑', layer='reported')
say('C15-072', 'narrator',
    '那智能百般的挣挫不起，又不好叫的，少不得依他了。'
    '正在得趣，只见一人进来，将他二人按住，也不则声。'
    '二人不知是谁，唬的不敢动一动。只听那人嗤的一声，掌不住笑了，'
    '二人听声方知是宝玉。秦钟连忙起来，抱怨道：「这算什么？」'
    '宝玉笑道：「你倒不依，咱们就叫喊起来。」羞的智能趁黑地跑了。',
    '只听那人嗤的一声', [show('baoyu', 'back_room'), effect('baoyu', 'greet')])
say('C15-073', 'baoyu',
    '宝玉拉了秦钟出来道：「你可还和我强？」秦钟笑道：'
    '「好人，你只别嚷的众人知道，你要怎样我都依你。」'
    '宝玉笑道：「这会子也不用说，等一会睡下，再细细的算帐。」',
    '再细细的算帐', [move('baoyu', 'back_room', 'gate'), effect('qin_zhong', 'idle')])
say('C15-074', 'narrator',
    '一时宽衣安歇的时节，凤姐在里间，秦钟、宝玉在外间，'
    '满地下皆是家下婆子，打舖坐更。'
    '凤姐因怕通灵玉失落，便等宝玉睡下，命人拿来塞在自己枕边。'
    '宝玉不知与秦钟算何帐目，未见真切，未曾记得，此是疑案，不敢纂创。',
    '此是疑案，不敢纂创', [hide('qin_zhong'), hide('baoyu')])

# ===== c15-letter : 旺儿修书 ===========================
section('c15-letter', 'c15_shuiyue', '水月庵 · 净室', 'back_room',
        '一宿无话。至次日一早')
say('C15-080', 'narrator',
    '一宿无话。至次日一早，便有贾母王夫人打发了人来看宝玉，'
    '又命多穿两件衣服，无事宁可回去。宝玉那里肯回去，'
    '又有秦钟恋著智能，调唆宝玉求凤姐再住一天。',
    '又有秦钟恋著智能，调唆宝玉求凤姐再住一天',
    [show('baoyu', 'back_room'), show('qin_zhong', 'back_room')])
say('C15-081', 'feng',
    '凤姐想了一想：凡丧仪大事虽妥，还有一半点小事未曾安插，'
    '可以指此再住一日，岂不又在贾珍跟前送了满情，'
    '二则又可以完净虚那事，三则顺了宝玉的心，贾母听见，岂不欢喜？'
    '因有此三益，便向宝玉道：「我的事都完了，你要在这里逛，'
    '少不得越性辛苦一日罢了，明儿可是定要走的了。」',
    '因有此三益', [show('feng', 'back_room'), effect('feng', 'greet')])
say('C15-082', 'baoyu',
    '宝玉听说，千姐姐万姐姐的央求：「只住一日，明儿必回去的。」'
    '于是又住了一夜。', '只住一日，明儿必回去的',
    [effect('baoyu', 'greet')])
say('C15-083', 'narrator',
    '凤姐便命悄悄将昨日老尼之事，说与来旺儿。来旺儿心中俱已明白，'
    '急忙进城找著主文的相公，假托贾琏所嘱，修书一封，连夜往长安县来，'
    '不过百里路程，两日工夫俱已妥协。'
    '那节度使名唤云光，久见贾府之情，这点小事，岂有不允之理，给了回书，'
    '旺儿回来。', '假托贾琏所嘱，修书一封',
    [show('wang_er', 'gate'), move('wang_er', 'gate', 'court')])

# ===== c15-farewell : 铁槛寺照望 =======================
section('c15-farewell', 'c15_tiejian', '铁槛寺 · 停灵内殿', 'hall',
        '却说凤姐等又过一日')
say('C15-090', 'narrator',
    '却说凤姐等又过一日，次日方别了老尼，著他三日后往府里去讨信。'
    '那秦钟与智能百般不忍分离，背地里多少幽期密约，俱不用细述，'
    '只得含恨而别。', '只得含恨而别',
    [show('feng', 'gate'), move('feng', 'gate', 'court', 'hall_door', 'hall')])
say('C15-091', 'narrator',
    '凤姐又到铁槛寺中照望一番。宝珠执意不肯回家，'
    '贾珍只得派妇女相伴。后回再见。', '宝珠执意不肯回家',
    [show('bao_zhu', 'hall'), effect('bao_zhu', 'rest')])


def verify_sources():
    import re
    base = re.sub(r'\s+', '', Path('docs/chapter15-source.txt').read_text())
    leads = {}
    for s in steps:
        leads.setdefault(s['source']['paragraphLead'], []).append(s['id'])
    bad = 0
    for lead, ids in leads.items():
        if re.sub(r'\s+', '', lead) not in base:
            bad += 1
            print('  LEAD NOT IN SOURCE:', lead, '->', ids)
    print(f'paragraphLead 校验: {len(leads)} 条, 不匹配 {bad} 条')
    return bad == 0


def build_story():
    ids = [s['id'] for s in steps]
    assert len(ids) == len(set(ids)), 'duplicate node id'
    for s in steps:
        assert s['chapter'] in section_titles, f"{s['id']}: unknown section"
    if not verify_sources():
        raise SystemExit('source leads do not match docs/chapter15-source.txt')
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_DIR / 'chapter15-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 15}
                for sid, title, scene in SECTIONS]
    (STAGE_DIR / 'chapter15-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter15-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter15-sections.json  %d sections' % n_sections)
