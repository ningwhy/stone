#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-fourteen's stages, script and section table.

第十四回 · 林如海捐馆扬州城 · 贾宝玉路谒北静王

Chapter fourteen owns this generator; nothing here touches an earlier chapter.

Outputs:
  maps/c14_office.tmj        新舞台：宁国府 · 门房与领牌处
  maps/c14_funeral.tmj       新舞台：宁国府 · 会芳园灵前（哭灵）
  design/chapter14-story.json   节点 C14-001..
  design/chapter14-sections.json

本回用：maps/c13_funeral.tmj（宁府上房与停灵）、maps/c13_baosha.tmj（三间抱厦）、
maps/c6_wangchui.tmj（凤姐院）、maps/night.tmj（贾母院）、maps/c5_ningfu.tmj（宁府会芳园）。

三张地图的分工：
  c14_office   门房与领牌处：凤姐坐堂理事、彩明念花名册、媳妇们领牌支取。
                原文把这一段写成一整套行政动作（点卯、分班、定则例），
                需要一块能同时容纳凤姐、彩明与等候办事的人的场地。
  c14_funeral  会芳园灵前：五七正五日上，凤姐「一手扶着丰儿，两个媳妇执着手把灯罩」，
                簇拥进来，一见了棺材眼泪便滚下来。灵前要能放一张大圈椅。
  c13_funeral  上房与停灵（第十三回已建）：贾珍、宝玉、凤姐议定协理的地方。

人物：来升、昭儿为本回新立绘；凤姐、平儿、宝玉、秦钟、贾珍、尤氏、贾琏、
王夫人、邢夫人、贾蓉、贾赦、贾政、北静王水溶复用既有资产。宝珠（第十三回
已立绘）在此继续摔丧驾灵。来旺媳妇、张材家的、王兴媳妇在原著中只列名，
不另造人出场。

Usage: python3 scripts/build_chapter14.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

BACKUP = ROOT / 'artifacts/backups/2026-11-03-chapter14'
PUBLISH_MAP = True
MAP_DIR = ROOT / 'maps' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter14'
STAGE_DIR = ROOT / 'design' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter14'


def at(c, r, dx=0.0, dy=0.0):
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {
    # 门房与领牌处：凤姐坐堂，彩明在侧，媳妇们排队领牌。
    'c14_office': {
        'name': '宁国府 · 门房领牌处',
        'theme': 'interior',
        # 大堂（A0，行 12-20）为主，门外（OUT，行 21-27）供办事的人在廊下候着。
        'zones': [[12, 12, 18, 9, True, 'A0'], [14, 21, 16, 7, False]],
        'anchors': {
            'door': [21, 21],
            'wait': [18, 24],
            'queue': [24, 24],
            'hall_door': [20, 20],
            'seat': [20, 15],
            'clerk': [24, 16],
            'counter': [17, 17],
        },
        'routes': {
            'main': ['door', 'hall_door', 'seat'],
            'to_counter': ['seat', 'counter'],
            'to_clerk': ['seat', 'clerk'],
        },
        'labels': [['门房', 21, 23], ['理事堂', 20, 13], ['领牌处', 17, 18]],
        'props': [
            ('ning-hall', *at(20, 15), .70, 'A0'),
            ('official-chair', *at(20, 15, 0, 0), .66, 'A0'),
            ('square-table', *at(24, 16, 0, 0), .56, 'A0'),
            ('writing-desk', *at(17, 17, 0, 0), .62, 'A0'),
            ('lamp-stand', *at(16, 13, 0, 0), .60, 'A0'),
            ('brazier', *at(26, 18, 0, 0), .56, 'A0'),
            ('bamboo-gate', *at(20, 20, 0, 0), .54, 'A0'),
            ('flower-gate', *at(15, 25, 0, 0), .46),
            ('garden-tree', *at(27, 25, 0, 0), .92),
            ('stone-lion', *at(17, 26, 0, 0), .52),
        ],
        'walls': [[14, 21, 30, 21], [14, 21, 14, 28], [30, 21, 30, 28],
                  [14, 28, 30, 28]],
        'terraces': [[19, 21, 4, 6, 'path'], [19, 20, 3, 3, 'path']],
    },
    # 会芳园灵前：五七正五日，凤姐放声大哭，里外男女上下接声嚎哭。
    'c14_funeral': {
        'name': '宁国府 · 会芳园灵前',
        'theme': 'interior',
        'zones': [[11, 10, 20, 12, True, 'A0'], [24, 8, 8, 6, True, 'B']],
        'anchors': {
            'garden': [20, 18],
            'altar': [26, 12],
            'chair': [22, 15],
            # 宁府大门：凤姐与平儿从荣府来，在门内下车处站定，再往园中。
            'door': [13, 21],
            'gate': [15, 20],
            'side': [17, 13],
            'far': [28, 16],
        },
        'routes': {
            'main': ['door', 'gate', 'garden', 'chair'],
            'to_altar': ['garden', 'altar'],
            'to_side': ['garden', 'side'],
        },
        'labels': [['会芳园', 20, 11], ['灵前', 26, 9], ['灵棚', 21, 19]],
        'props': [
            ('altar-table', *at(26, 12, 0, 0), .72, 'B'),
            ('wood-screen', *at(29, 11, 0, -60), .70, 'B'),
            ('brazier', *at(24, 12, 0, 0), .58, 'B'),
            # 灵前的大圈椅：凤姐「放声大哭」的地方。
            ('official-chair', *at(22, 15, 0, 0), .70, 'A0'),
            ('square-table', *at(17, 14, 0, 0), .56, 'A0'),
            ('lamp-stand', *at(14, 12, 0, 0), .60, 'A0'),
            ('bamboo-cluster', *at(13, 17, 0, 0), .92),
            ('garden-tree', *at(29, 19, 0, 0), .96),
            ('garden-rock', *at(14, 20, 0, 0), .80),
        ],
        'terraces': [[19, 18, 4, 3, 'path']],
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
    ('c14-warn', '宁国府 · 传话立威', 'c13_funeral'),
    ('c14-duties', '宁国府 · 点卯分派', 'c14_office'),
    ('c14-rules', '宁国府 · 定则例', 'c14_office'),
    ('c14-cry', '会芳园 · 灵前大哭', 'c14_funeral'),
    ('c14-beating', '宁国府 · 打二十板子', 'c14_office'),
    ('c14-baoyu', '宁国府 · 宝玉秦钟来扰', 'c14_office'),
    ('c14-zhao', '宁国府 · 昭儿报信', 'c14_office'),
    ('c14-prepare', '宁国府 · 发送殡筹备', 'c13_funeral'),
    ('c14-procession', '宁国府 · 六十四名青衣请灵', 'c14_funeral'),
    ('c14-prince', '宁国府 · 北静王路奠', 'c14_funeral'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 14, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c14-warn : 传话立威 ==============================
# 原文位置：宁国府中都总管来升听得里面委请了凤姐，传齐同事人等说
# 「那是个有名的烈货，脸酸心硬，一时恼了，不认人的」。
section('c14-warn', 'c13_funeral', '宁国府 · 上房', 'room',
        '话说宁国府中都总管来升闻得里面委请了凤姐')
say('C14-001', 'narrator',
    '话说宁国府中都总管来升闻得里面委请了凤姐，因传齐同事人等说道：'
    '「如今请了西府里琏二奶奶管理内事，倘或他来支取东西，或是说话，'
    '我们须要比往日小心些。每日大家早来晚散，宁可辛苦这一个月，'
    '过后再歇着，不要把老脸丢了。', '不要把老脸丢了',
    [show('lai_sheng', 'room'), show('jia_zhen', 'room')])
say('C14-002', 'lai_sheng',
    '来升又道：「那是个有名的烈货，脸酸心硬，一时恼了，不认人的。」'
    '众人都道：「有理。」又有一个笑道：「论理，我们里面也须得他来整治整治，'
    '都忒不像了。」', '脸酸心硬',
    [effect('lai_sheng', 'anger')])
say('C14-003', 'narrator',
    '正说着，只见来旺媳妇拿了对牌来领取呈文京榜纸札，票上批著数目。'
    '众人连忙让坐倒茶，一面命人按数取纸来抱著，'
    '同来旺媳妇一路来至仪门口，方交与来旺媳妇自己抱进去了。',
    '来旺媳妇拿了对牌来领取', [move('lai_sheng', 'room', 'hall_door', 'hall')])

# ===== c14-duties : 点卯分派 =============================
section('c14-duties', 'c14_office', '宁国府 · 理事堂', 'seat',
        '凤姐即命彩明钉造簿册')
say('C14-010', 'narrator',
    '凤姐即命彩明钉造簿册。即时传来升媳妇，兼要家口花名册来查看，'
    '又限于明日一早传齐家人媳妇进来听差等语。'
    '大概点了一点数目单册，问了来升媳妇几句话，便坐车回家。一宿无话。',
    '凤姐即命彩明钉造簿册',
    [show('feng', 'seat'), show('lai_sheng', 'clerk'), effect('feng', 'greet')])
say('C14-011', 'narrator',
    '至次日，卯正二刻便过来了。那宁国府中婆娘媳妇闻得到齐，'
    '只见凤姐正与来升媳妇分派，众人不敢擅入，只在窗外听觑。',
    '卯正二刻便过来了',
    [move('feng', 'door', 'hall_door', 'seat'), hide('lai_sheng')])
say('C14-012', 'feng',
    '只听凤姐与来升媳妇道：「既托了我，我就说不得要讨你们嫌了。'
    '我可比不得你们奶奶好性儿，由著你们去。再不要说你们'
    '『这府里原是这样』的话，如今可要依著我行，'
    '错我半点儿，管不得谁是有脸的，谁是没脸的，一律现清白处理。」',
    '一律现清白处理', [effect('feng', 'anger')])
say('C14-013', 'narrator',
    '说著，便吩咐彩明念花名册，按名一个一个的唤进来看视。',
    '按名一个一个的唤进来看视', [effect('feng', 'greet')])

# ===== c14-rules : 定则例 ==============================
# 原文位置：凤姐分派人客、亲眷、灵前、内茶房、酒饭器皿、祭礼、灯油、上夜，
# 共分八班；再定「卯正二刻点卯，巳正吃早饭，午初刻领牌回事，戌初烧过黄昏纸」。
section('c14-rules', 'c14_office', '宁国府 · 理事堂', 'seat',
        '一时看完，便又吩咐道')
say('C14-020', 'narrator',
    '一时看完，便又吩咐道：「这二十个分作两班，一班十个，'
    '每日在里头单管人客来往倒茶，别的事不用他们管。'
    '这二十个也分作两班，每日单管本家亲戚茶饭，别的事也不用他们管。'
    '这四十个人也分作两班，单在灵前上香添油，挂幔守灵，供饭供茶，'
    '随起举哀，别的事也不与他们相干。', '这二十个分作两班',
    [effect('feng', 'greet')])
say('C14-021', 'narrator',
    '「这四个人单在内茶房收管杯碟茶器，若少一件，便叫他四个描赔。'
    '这四个人单管酒饭器皿，少一件，也是他四个描赔。'
    '这八个单管监收祭礼。这八个单管各处灯油、蜡烛、纸札，'
    '我总支了来，交与你八个，然后按我的定数再往各处去分派。'
    '这三十个每日轮流各处上夜，照管门户，监察火烛，打扫地方。',
    '若少一件，便叫他四个描赔', [effect('feng', 'greet')])
say('C14-022', 'narrator',
    '「这下剩的按著房屋分开，某人守某处，某处所有桌椅古董起，'
    '至于痰盒掸帚，一草一苗，或丢或坏，就和守这处的人算帐描赔。'
    '来升家的每日揽总查看，或有偷懒的，赌钱吃酒的，打架拌嘴的，立刻来回我。'
    '你有徇情，经我查出，三四辈子的老脸就顾不成了。'
    '如今都有定规，以后那一行乱了，只和那一行说话。', '如今都有定规',
    [effect('feng', 'anger')])
say('C14-023', 'narrator',
    '「素日跟我的人，随身自有钟表，不论大小事，我是皆有一定的时辰。'
    '横竖你们上房里也有时辰钟。卯正二刻我来点卯，巳正吃早饭，'
    '凡有领牌回事的，只在午初刻。戌初烧过黄昏纸，我亲到各处查一遍，'
    '回来上夜的交明钥匙。第二日仍是卯正二刻过来。'
    '说不得咱们大家辛苦这几日罢，事完了，你们家大爷自然赏你们。」',
    '卯正二刻我来点卯', [effect('feng', 'greet')])
say('C14-024', 'narrator',
    '说罢，又吩咐按数发与茶叶、油烛、鸡毛掸子、笤帚等物。'
    '一面又搬取家伙：桌围、椅搭、坐褥、毡席、痰盒、脚踏之类。'
    '一面交发，一面提笔登记，某人管某处，某人领某物，开得十分清楚。',
    '开得十分清楚', [effect('feng', 'idle')])
say('C14-025', 'narrator',
    '众人领了去，也都有了投奔，不似先时只拣便宜的做，剩下的苦差没个招揽。'
    '各房中也不能趁乱失迷东西。便是人来客往，也都安静了，'
    '不比先前一个正摆茶，又去端饭，正陪举哀，又顾接客。'
    '如这些无头绪，荒乱，推托，偷闲，窃取等弊，次日一概都蠲了。',
    '次日一概都蠲了', offscreen=True)

# ===== c14-cry : 灵前大哭 ==============================
# 原文位置：五七正五日上，寅正起身，卯正二刻到宁府，
# 一见了棺材眼泪恰似断线之珠；凤姐放声大哭，里外男女上下接声嚎哭。
section('c14-cry', 'c14_funeral', '会芳园 · 灵前', 'chair',
        '这日乃五七正五日上')
say('C14-030', 'narrator',
    '这日乃五七正五日上，那应佛僧正开方破狱，传灯照亡，参阎君，拘都鬼，'
    '筵请地藏王，开金桥，引幢幡，那道士们正伏章申表，朝三清，叩玉帝，'
    '禅僧们行香，放焰口，拜水忏，又有十三众尼僧，搭绣衣，靸红鞋，'
    '在灵前默诵接引诸咒，十分热闹。', '五七正五日上',
    [show('bao_zhu', 'altar'), show('jia_zhen', 'garden')])
say('C14-031', 'narrator',
    '那凤姐必知今日人客不少，在家中歇宿一夜，至寅正，平儿便请起来梳洗。'
    '及收拾完备，更衣盥手，吃了两口奶子糖粳米粥，漱口已毕，'
    '已是卯正二刻了。', '至寅正，平儿便请起来梳洗',
    [show('feng', 'door'), show('ping_er', 'garden')])
say('C14-032', 'narrator',
    '凤姐出至厅前，上了车，前面打了一对明角灯，大书「荣国府」三个大字，'
    '款款来至宁府。大门上门灯朗挂，两边一色戳灯，照如白昼，'
    '白汪汪穿孝仆从两边侍立。', '大书「荣国府」三个大字',
    [move('feng', 'door', 'garden'), move('ping_er', 'door', 'garden')])
say('C14-033', 'narrator',
    '请车至正门上，小厮等退去，众媳妇上来揭起车帘。'
    '凤姐下了车，一手扶著丰儿，两个媳妇执著手把灯罩，簇拥著凤姐进来。'
    '宁府诸媳妇迎来请安接待。', '簇拥著凤姐进来',
    [move('feng', 'garden', 'chair')])
say('C14-034', 'narrator',
    '凤姐缓缓走入会芳园中登仙阁灵前，一见了棺材，那眼泪恰似断线之珠，'
    '滚将下来。院中许多小厮垂手伺候烧纸。'
    '凤姐吩咐得一声：「供茶烧纸。」只听一棒锣鸣，诸乐齐奏，'
    '早有人端过一张大圈椅来，放在灵前，凤姐坐了，放声大哭。',
    '眼泪恰似断线之珠', [effect('feng', 'anger')])
say('C14-035', 'narrator',
    '于是里外男女上下，见凤姐出声，都忙忙接声嚎哭。'
    '一时贾珍尤氏遣人来劝，凤姐方才止住。', '都忙忙接声嚎哭',
    [effect('feng', 'anger')])

# ===== c14-beating : 打二十板子 =========================
# 原文位置：按名查点，各项人数都已到齐，只有迎送亲客上的一人未到；
# 凤姐冷笑，命「带出去，打二十板子」，并革来升一月银米。
section('c14-beating', 'c14_office', '宁国府 · 理事堂', 'seat',
        '按名查点，各项人数都已到齐')
# 这是本段切换到 c14_office 的第一个节点。engine 切场景时会把所有人置为
# 不可见，所以在这里先 show 再 move —— 直接 move 会撞上「移动角色未显示」。
say('C14-040', 'narrator',
    '来旺媳妇献茶漱口毕，凤姐方起身，别过族中诸人，自入抱厦内来。'
    '按名查点，各项人数都已到齐，只有迎送亲客上的一人未到。'
    '即命传到，那人已张惶愧惧。',     '只有迎送亲客上的一人未到',
    [show('feng', 'door'), move('feng', 'door', 'hall_door', 'seat')])
say('C14-041', 'feng',
    '凤姐冷笑道：「我说是谁误了，原来是你！你原比他们有体面，'
    '所以才不听我的话。」那人道：「小的天天都来的早，'
    '只有今儿，醒了觉得早些，因又睡迷了，来迟了一步，求奶奶饶过这次。」',
    '原来是你', [effect('feng', 'anger')])
say('C14-042', 'narrator',
    '正说着，只见荣国府中的王兴媳妇来了，在前探头。'
    '凤姐且不发放这人，却先问：「王兴媳妇作什么？」'
    '王兴媳妇巴不得先问他完了事，连忙进去说：'
    '「领牌取线，打车轿网络。」', '领牌取线，打车轿网络',
    [show('wang', 'counter')])
say('C14-043', 'feng',
    '说著，将个帖儿递上去。凤姐命彩明念道：「大轿两顶，小轿四顶，'
    '车四辆，共用大小络子若干根，用珠儿线若干斤。」'
    '凤姐听了，数目相合，便命彩明登记，取荣国府对牌掷下。'
    '王兴家的去了。', '数目相合', [effect('feng', 'greet')])
say('C14-044', 'narrator',
    '凤姐方欲说话时，见荣国府的四个执事人进来，都是要支取东西领牌来的。'
    '凤姐命彩明要了帖念过，听了一共四件，指两件说道：'
    '「这两件开销错了，再算清了来取。」说著掷下帖子来。那二人扫兴而去。',
    '这两件开销错了', [effect('feng', 'anger')])
say('C14-045', 'narrator',
    '凤姐因见张材家的在旁，因问：「你有什么事？」'
    '张材家的忙取帖儿回说：「就是方才车轿围作成，领取裁缝工银若干两。」'
    '凤姐听了，便收了帖子，命彩明登记。', '领取裁缝工银若干两',
    [effect('feng', 'idle')])
say('C14-046', 'feng',
    '凤姐便说道：「明儿他也睡迷了，后儿我也睡迷了，将来都没了人了。'
    '本来要饶你，只是我头一次宽了，下次人就难管，不如现开发的好。」'
    '登时放下脸来，喝命：「带出去，打二十板子！」', '打二十板子',
    [effect('feng', 'anger')])
say('C14-047', 'narrator',
    '一面又掷下宁国府对牌：「出去说与来升，革他一月银米！」'
    '众人听说，又见凤姐眉立，知是恼了，不敢怠慢，'
    '拖人的出去拖人，执牌传谕的忙去传谕。'
    '那人身不由己，已拖出去挨了二十大板，还要进来叩谢。',
    '革他一月银米', [effect('feng', 'anger')])
say('C14-048', 'feng',
    '凤姐道：「明日再有误的，打四十，后日的六十，有要挨打的，只管误！」'
    '说著，吩咐：「散了罢。」窗外众人听说，方各自执事去了。'
    '彼时宁府荣府两处执事领牌交牌的，人来人往不绝，'
    '那抱愧被打之人含羞去了，这才知道凤姐利害。众人不敢偷闲，自此兢兢业业。',
    '明日再有误的，打四十', [effect('feng', 'greet')])

# ===== c14-baoyu : 宝玉秦钟来扰 =======================
section('c14-baoyu', 'c14_office', '宁国府 · 理事堂', 'seat',
        '如今且说宝玉因见今日人众')
say('C14-050', 'narrator',
    '如今且说宝玉因见今日人众，恐秦钟受了委曲，因默与他商议，'
    '要同他往凤姐处来坐。秦钟道：“他的事多，况且不喜人去，'
    '咱们去了，他岂不烦腻。”宝玉道：“他怎好腻我们，不相干，'
    '只管跟我来。”', '只管跟我来',
    [show('baoyu', 'wait'), show('qin_zhong', 'queue')])
say('C14-051', 'narrator',
    '说著，便拉了秦钟，直至抱厦。凤姐才吃饭，见他们来了，便笑道：'
    '“好长腿子，快上来罢。”宝玉道：“我们偏了。”'
    '凤姐道：“在这边外头吃的，还是那边吃的？”'
    '宝玉道：“这边同那些浑人吃什么！原是那边，'
    '我们两个同老太太吃了来的。”一面归坐。', '好长腿子，快上来罢',
    [parallel(move('baoyu', 'wait', 'door', 'hall_door', 'seat'),
              move('qin_zhong', 'queue', 'door', 'hall_door', 'seat'))])
say('C14-052', 'narrator',
    '凤姐吃毕饭，就有宁国府中的一个媳妇来领牌，为支取香灯事。'
    '凤姐笑道：“我算著你们今儿该来支取，总不见来，想是忘了。'
    '这会子到底来取，要忘了，自然是你们包出来，都便宜了我。”'
    '那媳妇笑道：“何尝不是忘了，方才想起来，再迟一步，也领不成了。”'
    '说罢，领牌而去。', '总不见来，想是忘了',
    [effect('feng', 'greet')])
say('C14-053', 'narrator',
    '一时登记交牌。秦钟因笑道：“你们两府里都是这牌，'
    '倘或别人私弄一个，支了银子跑了，怎样？”'
    '凤姐笑道：“依你说，都没王法了。”', '倘或别人私弄一个',
    [effect('qin_zhong', 'greet')])
say('C14-054', 'baoyu',
    '宝玉因道：“怎么咱们家没人领牌子做东西？”'
    '凤姐道：“人家来领的时候，你还做梦呢。我且问你，'
    '你们这夜书多早晚才念呢？”宝玉道：“巴不得这如今就念才好，'
    '他们只是不快收拾出书房来，这也无法。”'
    '凤姐笑道：“你请我一请，包管就快了。”', '怎么咱们家没人领牌子做东西',
    [effect('baoyu', 'greet')])
say('C14-055', 'feng',
    '宝玉道：“你要快也不中用，他们该作到那里的，自然就有了。”'
    '凤姐笑道：“便是他们作，也得要东西，搁不住我不给对牌是难的。”'
    '宝玉听说，便猴向凤姐身上立刻要牌，说：“好姐姐，给出牌子来，'
    '叫他们要东西去。”凤姐道：“我乏的身子上生疼，还搁的住揉搓。'
    '你放心罢，今儿才领了纸裱糊去了，他们该要的还等叫去呢，可不傻了？”'
    '宝玉不信，凤姐便叫彩明查册子与宝玉看了。', '给出牌子来',
    [effect('feng', 'idle')])

# ===== c14-zhao : 昭儿报信 =============================
section('c14-zhao', 'c14_office', '宁国府 · 理事堂', 'seat',
        '正闹著，人回：「苏州去的人昭儿来了。」')
say('C14-060', 'narrator',
    '正闹著，人回：“苏州去的人昭儿来了。”凤姐急命唤进来。'
    '昭儿打千儿请安。凤姐便问：“回来做什么的？”'
    '昭儿道：“二爷打发回来的。林姑老爷是九月初三日巳时没的。”',
    '林姑老爷是九月初三日巳时没的',
    [show('zhao_er', 'door'), move('zhao_er', 'door', 'hall_door', 'counter')])
say('C14-061', 'narrator',
    '昭儿道：“二爷带了林姑娘同送林姑老爷灵到苏州，大约赶年底就回来。'
    '二爷打发小的来报个信请安，讨老太太示下，还瞧瞧奶奶家里好，'
    '叫把大毛衣服带几件去。”凤姐道：“你见过别人了没有？”'
    '昭儿道：“都见过了。”说毕，连忙退去。', '大约赶年底就回来',
    [effect('zhao_er', 'greet')])
say('C14-062', 'feng',
    '凤姐向宝玉笑道：“你林妹妹可在咱们家住长了。”'
    '宝玉道：“了不得，想来这几日他不知哭的怎样呢。”'
    '说著，蹙眉长叹。', '你林妹妹可在咱们家住长了',
    [effect('feng', 'idle')])
say('C14-063', 'narrator',
    '凤姐见昭儿回来，因当著人未及细问贾琏，心中自是记挂，'
    '待要回去，争奈事情繁杂，一时去了，恐有延迟失误，惹人笑话。'
    '少不得耐到晚上回来，复令昭儿进来，细问一路平安信息。',
    '复令昭儿进来，细问一路平安信息', offscreen=True)
say('C14-064', 'narrator',
    '连夜打点大毛衣服，和平儿亲自检点包裹，再细细追想所需何物，'
    '一并包藏交付昭儿。又细细吩咐昭儿：「在外好生小心伏侍，'
    '不要惹你二爷生气，时时劝他少吃酒，别勾引他认得混帐老婆，回来打折你的腿」等语。'
    '赶乱完了，天已四更将尽，总睡下又走了困，不觉天明鸡唱，'
    '忙梳洗过宁府中来。', '时时劝他少吃酒', offscreen=True)

# ===== c14-prepare : 发送殡筹备 =========================
# 原文位置：贾珍因见发引日近，亲自坐车带阴阳司吏往铁槛寺踏看寄灵所在；
# 凤姐也预先逐细分派料理，忙得茶饭也没工夫吃。
section('c14-prepare', 'c13_funeral', '宁国府 · 上房', 'room',
        '那贾珍因见发引日近')
say('C14-070', 'narrator',
    '那贾珍因见发引日近，亲自坐车，带了阴阳司吏，往铁槛寺来踏看寄灵所在。'
    '又一一嘱咐住持色空，好生预备新鲜陈设，多请名僧，以备接灵使用。'
    '色空忙看晚斋。贾珍也无心茶饭，因天晚不得进城，就在净室胡乱歇了一夜。'
    '次日早，便进城来料理出殡之事。', '往铁槛寺来踏看寄灵所在',
    [show('jia_zhen', 'room'), move('jia_zhen', 'room', 'hall_door', 'hall')])
say('C14-071', 'narrator',
    '里面凤姐见日期有限，也预先逐细分派料理，'
    '一面又派荣府中车轿人从跟王夫人送殡，又顾自己送殡去占下处。'
    '目今正值缮国公诰命亡故，王邢二夫人又去打祭送殡，'
    '西安郡王妃华诞，送寿礼，镇国公诰命生了长男，预备贺礼，'
    '又有胞兄王仁连家眷回南，一面写家信禀叩父母并带往之物，'
    '又有迎春染病，每日请医服药。', '也预先逐细分派料理',
    [show('feng', 'room'), effect('feng', 'idle')])
say('C14-072', 'narrator',
    '又兼发引在迩，因此忙的凤姐茶饭也没工夫吃得，坐卧不能清净。'
    '刚到了宁府，荣府的人又跟到宁府，既回到荣府，宁府的人又找到荣府。'
    '凤姐见如此，心中倒十分欢喜，并不偷安推托，恐落人褒贬，'
    '因此日夜不暇，筹划得十分的整肃。于是合族上下无不称叹者。',
    '合族上下无不称叹者', [move('feng', 'room', 'hall_door', 'hall')])

# ===== c14-procession : 六十四名青衣请灵 =================
section('c14-procession', 'c14_funeral', '会芳园 · 灵前', 'garden',
        '这日伴宿之夕')
say('C14-080', 'narrator',
    '这日伴宿之夕，里面两班小戏并耍百戏的与亲朋堂客伴宿，'
    '尤氏犹卧于内室，一应张罗款待，独是凤姐一人周全承应。'
    '合族中虽有许多妯娌，但或有羞口的，或有羞脚的，或有不惯见人的，'
    '或有惧贵怯官的，种种之类，俱不及凤姐举止舒徐，言语慷慨，珍贵宽大，'
    '因此也不把众人放在眼里，挥霍指示，任其所为，目若无人。',
    '独是凤姐一人周全承应', [show('feng', 'garden'), show('you_shi', 'side')])
say('C14-081', 'narrator',
    '一夜中灯明火彩，客送官迎，那百般热闹，自不用说的。'
    '至天明，吉时已到，一般六十四名青衣请灵，'
    '前面铭旌上大书：奉天洪建兆年不易之朝诰封一等宁国公冢孙妇'
    '防护内廷紫禁道御前侍卫龙禁尉享强寿贾门秦氏恭人之灵柩。',
    '六十四名青衣请灵', [show('bao_zhu', 'altar'), move('bao_zhu', 'altar', 'garden')])
say('C14-082', 'narrator',
    '宝珠自行未嫁女之礼外，摔丧驾灵，十分哀苦。', '摔丧驾灵',
    [effect('bao_zhu', 'anger')])

# ===== c14-prince : 北静王路奠 =========================
# 原文位置：路上四座祭棚，第四座是北静郡王的；水溶五更入朝，公事一毕，
# 便换了素服，坐大轿鸣锣张伞而来；问贾政「那一位是衔宝而诞者」。
section('c14-prince', 'c14_funeral', '会芳园 · 灵前', 'garden',
        '走不多时，路旁彩棚高搭')
say('C14-090', 'narrator',
    '走不多时，路旁彩棚高搭。设席张筵，和音奏乐，俱是各家路祭：'
    '第一座是东平王府祭棚，第二座是南安郡王祭棚，第三座是西宁郡王，'
    '第四座是北静郡王的。原来这四王，当日惟北静王功高，'
    '及今子孙犹袭王爵。', '第四座是北静郡王的',
    [show('jia_zhen', 'garden'), show('xing', 'side')])
say('C14-091', 'narrator',
    '现今北静王水溶年未弱冠，生得形容秀美，情性谦和。'
    '近闻宁国公冢孙妇告殂，因想当日彼此祖父相与之情，同难同荣，'
    '未以异姓相视，因此不以王位自居，上日也曾探丧上祭，'
    '如今又设路奠，命麾下各官在此伺候。', '生得形容秀美，情性谦和',
    [show('shui_rong', 'gate'), move('shui_rong', 'gate', 'garden')])
say('C14-092', 'narrator',
    '自己五更入朝，公事一毕，便换了素服，坐大轿鸣锣张伞而来，至棚前落轿。'
    '手下各官两旁拥侍，军民人众不得往还。', '坐大轿鸣锣张伞而来',
    [move('shui_rong', 'garden', 'side')])
say('C14-093', 'narrator',
    '一时只见宁府大殡浩浩荡荡，压地银山一般从北而至。'
    '早有宁府开路传事人看见，连忙回去报与贾珍。'
    '贾珍急命前面驻扎，同贾赦贾政三人连忙迎来，以国礼相见。'
    '水溶在轿内欠身含笑答礼，仍以世交称呼接待，并不妄自尊大。',
    '仍以世交称呼接待',
    [show('jia_zhen', 'gate'), show('xing', 'far')])
say('C14-094', 'jia_zhen',
    '贾珍道：「犬妇之丧，累蒙郡驾下临，荫生辈何以克当。」'
    '水溶笑道：「世交之谊，何出此言。」遂回头命长府官主祭代奠。'
    '贾赦等一旁还礼毕，复身又来谢恩。', '世交之谊，何出此言',
    [effect('shui_rong', 'greet')])
say('C14-095', 'narrator',
    '水溶十分谦逊，因问贾政道：「那一位是衔宝而诞者？'
    '几次要见一见，都为杂冗所阻，想今日是来的，何不请来一会。」'
    '贾政听说，忙回去，急命宝玉脱去孝服，领他前来。',
    '那一位是衔宝而诞者', [effect('shui_rong', 'idle')])
say('C14-096', 'baoyu',
    '那宝玉素日就曾听得父兄亲友人等说闲话时，赞水溶是个贤王，'
    '且生得才貌双全，风流潇洒，每不以官俗国体所缚。'
    '每思相会，只是父亲拘束严密，无由得会，今见反来叫他，自是欢喜。'
    '一面走，一面早瞥见那水溶坐在轿内，好个仪表人材。'
    '不知近看时又是怎样，且听下回分解。', '好个仪表人材',
    [show('baoyu', 'side'), move('baoyu', 'side', 'far')])


def verify_sources():
    import re
    base = re.sub(r'\s+', '', Path('docs/chapter14-source.txt').read_text())
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
        raise SystemExit('source leads do not match docs/chapter14-source.txt')
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_DIR / 'chapter14-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 14}
                for sid, title, scene in SECTIONS]
    (STAGE_DIR / 'chapter14-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter14-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter14-sections.json  %d sections' % n_sections)
