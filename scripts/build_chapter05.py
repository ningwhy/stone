#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-five maps, its playable script and its evidence table.

Chapter five owns this generator; nothing here touches build_chapter04.py or
write_prequel.py, so re-running it cannot overwrite an earlier chapter.

Outputs (printed at the end):
  maps/c5_ningfu.tmj        new stage: the ning-fu garden and Qin Keqing's room
  maps/c5_taixu.tmj         new stage: the great void illusion (Tai-xu)
  maps/c5_mijing.tmj        new stage: the Mijing ford at the end of the dream
  design/chapter05-story.json      nodes C05-001..C05-103
  design/chapter05-sections.json   eight sections: c5-niang .. c5-mijing
  design/chapter05-evidence.json   explicit / design evidence for every node

Usage: python3 scripts/build_chapter05.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402  (a roof lifts off the floor it covers)
BACKUP = ROOT / 'artifacts/backups/2026-10-27-chapter05'

# ---------------------------------------------------------------------------
# Maps
#
# The original names no direction, no distance and no building size for any of
# these places, so every layout below is a design decision, recorded as such in
# the evidence table. What the original does fix is the order of the walk:
# ning-fu garden -> Qin Keqing's room -> sleep -> Tai-xu -> the registry
# alcoves -> the banquet -> the boudoir -> Mijing -> back to reality.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 成套摆放：屏幕像素偏移
#
# 只按整数格坐标摆家具是「乱」的根源：等距下一格是 (±64, ±32) 像素，一张案宽
# 146px，把椅子放到「相邻一格」就等于把它甩到案外半张桌子的地方，看上去像随手
# 扔的。所以一处的家具先定一个落点（人站的地方或陈设中心），其余件按**屏幕像素**
# 相对它摆，椅子才真的贴住案沿、屏风才真的立在床后。
#
#   dx 右为正、dy 下为正（屏幕方向）
#   x=(c-r)*64, y=(c+r+1)*32  ⇒  dc = dx/128 + dy/64, dr = dy/64 - dx/128
# ---------------------------------------------------------------------------
def at(c, r, dx=0.0, dy=0.0):
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {    # Ning-fu house: the plum garden, the upper room Qin Keqing shows him, and
    # her own bedchamber where the dream starts.
    # 宁国府：会芳园赏梅 → 上房（挂《燃藜图》，宝玉不肯住）→ 秦氏卧房（海棠春睡图、
    # 武则天宝镜、赵飞燕金盘、安禄山木瓜、寿昌公主榻、同昌公主联珠帐，甜香袭人）。
    # 园与两进屋各有自己的屋顶：站进哪一间，哪一间的屋顶才掀开。
    'c5_ningfu': {
        'name': '宁国府 · 会芳园与秦氏卧房',
        'theme': 'garden',
        'zones': [[6, 20, 28, 14], [10, 10, 20, 10, True, 'UPPER'],
                  [12, 4, 16, 7, True, 'BED']],
        'anchors': {
            'garden_entry': [7, 28],
            'garden_center': [18, 27],
            'plum_grove': [27, 22],
            'upper_room_door': [19, 19],
            'upper_room': [19, 13],
            'portrait_wall': [22, 12],
            'bedchamber_door': [16, 10],
            'bedchamber': [17, 6],
            'screen_bed': [21, 6],
        },
        'routes': {
            'garden': ['garden_entry', 'garden_center', 'plum_grove'],
            'to_upper': ['garden_center', 'upper_room_door', 'upper_room'],
            'to_bed': ['upper_room', 'bedchamber_door', 'bedchamber'],
            'to_screen': ['bedchamber', 'screen_bed'],
        },
        'labels': [['会芳园', 18, 25], ['上房', 19, 11], ['秦氏卧房', 17, 4], ['梅花处', 27, 21]],
        'props': [
            # ── 会芳园：梅花、湖石、一段曲径，门在园南 ────────────────────────
            ('flower-gate', *at(7, 29), .62),
            ('garden-tree', *at(27, 21), .94),
            ('garden-tree', *at(24, 25), .84),
            ('garden-tree', *at(31, 25), .76),
            ('garden-tree', *at(10, 24), 1.06),
            # 进园这一段路上也得有东西可看：原来从园门到上房一路空着，第一眼像个后院。
            ('garden-tree', *at(12, 27), 1.02),
            ('garden-tree', *at(23, 28), .92),
            ('garden-rock', *at(15, 30), .82),
            ('garden-rock', *at(27, 31), .74),
            ('wang-rock', *at(29, 29), .82),
            ('garden-rock', *at(21, 30), .76),
            ('garden-rock', *at(13, 30), .68),
            # ── 上房：正面挂着《燃藜图》，一副对联，地下两溜椅子 ────────────
            ('ning-hall', *at(19, 12), .86, 'UPPER'),
            ('altar-table', *at(19, 13, 24, 34), .70, 'UPPER'),
            ('official-chair', *at(19, 13, -120, 40), .72, 'UPPER'),
            ('official-chair', *at(19, 13, 150, 40), .72, 'UPPER'),
            ('tea-table', *at(15, 13, 0, 10), .58, 'UPPER'),
            # ── 秦氏卧房：联珠帐的拔步床、宝镜金盘、寿昌公主的榻、甜香 ──────
            ('qin-room', *at(18, 6), .78, 'BED'),
            ('qin-bed', *at(17, 6, -70, 16), .80, 'BED'),
            ('qin-mirror', *at(21, 6, 40, 14), .70, 'BED'),
            ('daybed', *at(19, 7, 70, 40), .62, 'BED'),
            ('taixu-brazier', *at(15, 6, -30, 12), .54, 'BED'),
            ('wood-screen', *at(20, 5, 40, 0), .62, 'BED'),
        ],
        'water': [[22, 24, 6, 3]],
        'beds': [[10, 24, 3, 4], [16, 26, 3, 3]],
        'terraces': [[14, 22, 4, 9, 'path'], [17, 19, 4, 3, 'path']],
        # 上房墙上那幅《燃藜图》没有做成地图物件：等距俯视下屋壳一掀，连墙带顶整座消失，
        # 墙面根本不存在，画只会浮在地板上方半空。原文的描写交给对话文本（C05-013 起）。
        # 这里原来摆的是 wang-portrait —— 王夫人的**人物立绘**（248×600），竖着杵在屋里，
        # 比所有家具都高，看着就是一张立绘被丢进了地图。已删。
    },
    # 迷津：原著只给了四件事——荆榛遍地、迎面一道黑溪、并无桥梁、中无舟楫只有一个木筏。
    # 于是这一场没有屋、没有台基：南岸一片荆棘乱石，黑水横贯全屏，北岸是雾气里的崖壁，
    # 木筏孤零零停在岸边水上。水用 ruins 主题的墨黑水色画（见 MapScene.create）。
    'c5_mijing': {
        'name': '迷津 · 黑溪',
        'theme': 'ruins',
        # 黑水横在南北两岸之间：rows 18-22 全是水，两岸的地面不许压上去——原来北岸的
        # 地块一直铺到 row 21，水带上浮着几块浅色地砖，像黑河上漂着纸。
        'zones': [[6, 23, 28, 11], [10, 13, 20, 5]],
        'anchors': {
            'thicket': [8, 31],
            'bank': [15, 29],
            'stream_edge': [18, 24],
            'raft': [21, 24],
            'ferryman': [24, 25],
            'far_bank': [18, 15],
        },
        'routes': {
            'approach': ['thicket', 'bank', 'stream_edge'],
            'crossing': ['stream_edge', 'raft'],
            'ferry': ['stream_edge', 'ferryman'],
        },
        'labels': [['荆棘丛', 8, 31], ['黑溪', 18, 20], ['迷津', 18, 15]],
        'props': [
            # 南岸：荆棘成丛，愈近水愈密；乱石间杂，没有一处是整齐的。
            ('mijing-thorn', *at(8, 31), .96),
            ('mijing-thorn', *at(12, 30), 1.06),
            ('mijing-thorn', *at(24, 30), .88),
            ('mijing-thorn', *at(28, 26), .98),
            ('mijing-thorn', *at(6, 31), .82),
            ('mijing-thorn', *at(21, 27), .76),
            ('garden-rock', *at(14, 28), .88),
            ('garden-rock', *at(26, 28), 1.02),
            ('garden-rock', *at(9, 25), .74),
            # 木筏：唯一的渡具，停在水上，不靠任何岸。
            ('mijing-raft', *at(20, 21), .88),
            # 北岸：黑水那边的崖壁，只给轮廓，不给细节。崖石立在北岸的南沿（原本在
            # (13,13) 的崖顶，从对岸看只剩一片天）——「迷津」这三个字要压在崖上。
            ('wang-rock', *at(15, 17), 1.34),
            ('wang-rock', *at(24, 13), 1.18),
            ('garden-rock', *at(20, 12), .98),
        ],
        'water': [[4, 18, 32, 5]],
        'beds': [],
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
        zone = obj(f'{(z[5] if len(z) > 5 else "A" + str(i))} {scene["name"]}', z[0], z[1],
                   width=z[2] * 64, height=z[3] * 64)
        if len(z) > 4 and z[4]:
            zone['properties'] = [{'name': 'indoor', 'type': 'bool', 'value': True}]
        zones.append(zone)
        rects[z[5] if len(z) > 5 else f'A{i + 1}'] = tuple(z[:4])
    # Every anchor has to stand on a floor, or the walk has nowhere to resolve.
    for name, (c, r) in scene['anchors'].items():
        assert any(z[0] <= c < z[0] + z[2] and z[1] <= r < z[1] + z[3] for z in scene['zones']), \
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
        zone = prop[4] if len(prop) > 4 else None
        if asset not in assets:
            continue
        if is_shell(asset):
            c, r = eave(c, r, zone, rects)
        a = assets[asset]
        x = (c - r) * 64 + (a['width'] / 2 - a['anchor'][0]) * scale
        y = (c + r + 1) * 32 + (a['height'] - a['anchor'][1]) * scale
        shell = is_shell(asset)
        art_props = [{'name': 'asset', 'value': asset, 'type': 'string'},
                     {'name': 'visibility',
                      'value': 'exterior' if shell else ('interior' if zone else 'always'),
                      'type': 'string'}]
        if zone:
            art_props.append({'name': 'interiorZone', 'value': zone, 'type': 'string'})
        art.append(obj(asset, 0, 0, x=y + x / 2, y=y - x / 2, gid=gids[asset],
                       width=a['width'] * scale, height=a['height'] * scale, type='art',
                       properties=art_props))
        if asset in ('wood-screen', 'tea-table', 'garden-rock', 'altar-table', 'square-table') \
                and [c, r] not in anchor_cells:
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
                      + ([{'name': 'water', 'type': 'string',
                           'value': ';'.join(','.join(str(v) for v in w) for w in scene['water'])}]
                         if scene.get('water') else [])
                      + ([{'name': 'walls', 'type': 'string',
                           'value': ';'.join(','.join(str(v) for v in w) for w in scene['walls'])}]
                         if scene.get('walls') else [])
                      + ([{'name': 'flowerbeds', 'type': 'string',
                           'value': ';'.join(','.join(str(v) for v in b) for b in scene['beds'])}]
                         if scene.get('beds') else [])
                      + ([{'name': 'flowerbeds', 'type': 'bool', 'value': False}]
                         if scene.get('beds') == [] else [])

    }
    (ROOT / f'maps/{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')
    return len(scene['anchors'])


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

SECTIONS = [
    ('c5-niang', '宁府会芳园 · 宝黛生隙', 'c5_ningfu'),
    ('c5-sleep', '秦氏卧房 · 入梦', 'c5_ningfu'),
    ('c5-meet', '太虚幻境 · 遇警幻', 'c5_taixu'),
    ('c5-scroll', '薄命司 · 十二钗册页', 'c5_taixu'),
    ('c5-banquet', '警幻院 · 红楼梦十二支', 'c5_taixu'),
    ('c5-boudoir', '香闺绣阁 · 警幻设局', 'c5_taixu'),
    ('c5-mijing', '迷津 · 夜叉海鬼', 'c5_mijing'),
    ('c5-wake', '秦氏卧房 · 梦醒', 'c5_ningfu'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 5, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c5-niang : the ning-fu garden ==========================================
section('c5-niang', 'c5_ningfu', '宁国府 · 会芳园', 'garden_center',
        '如今且說林黛玉自在榮府以來', layer='reported')
say('C05-001', 'narrator',
    '第四回已把薛家母子寄居荣府的事略略说明，这一回暂且撂下不写。',
    '薛家寄居 · 撂笔不写')
say('C05-002', 'narrator',
    '林黛玉自进荣府以来，贾母万般怜爱，寝食起居一如宝玉；迎春、探春、惜春三个亲孙女倒且靠后。宝玉与黛玉更是日则同行同坐，夜则同息同止，言和意顺，略无参商。',
    '宝黛亲密')
say('C05-003', 'narrator',
    '忽然来了一个薛宝钗，年纪虽大不多，品格端方，容貌丰美，人多谓黛玉所不及。宝钗行为豁达，随分从时，比黛玉大得下人之心，连那些小丫头子也多喜与她去顽。',
    '宝钗入府')
say('C05-004', 'narrator',
    '因此黛玉心中便有些悒郁不忿之意，宝钗却浑然不觉。宝玉在孩提之间，一片愚拙偏僻，视姊妹弟兄皆出一意，并无亲疏远近之别。',
    '黛玉不忿')
say('C05-005', 'narrator',
    '这一日不知为何，他二人言语有些不合起来。黛玉又气得独在房中垂泪，宝玉又自悔言语冒撞，前去俯就，那黛玉方渐渐的回转来。',
    '一夕之隙')
say('C05-006', 'narrator',
    '这一节不过是一段回述，并未演在台上。此刻在场的，是东边宁国府的园子。',
    '转入宁府', [hide('baoyu'), hide('daiyu')])

section('c5-niang', 'c5_ningfu', '宁国府 · 会芳园', 'garden_center',
        '因東邊寧府中花園內梅花盛開，賈珍之妻尤氏乃治酒')
say('C05-007', 'narrator',
    '因东边宁府中花园内梅花盛开，贾珍之妻尤氏乃治酒，请贾母、邢夫人、王夫人等赏花。',
    '宁府赏花')
say('C05-008', 'narrator',
    '是日先携了贾蓉之妻秦氏，二人来面请。贾母等于早饭后过来，就在会芳园游顽，先茶后酒，不过是宁荣二府女眷家宴小集，并无别样新文趣事可记。',
    '会芳园小集')
say('C05-009', 'narrator',
    '宁荣二府的女眷在园中赏梅。宝钗、黛玉也在其中，只是原文说这一席「并无别样新文趣事可记」，本回便不为她们另设一场。',
    '园中女眷',
    [show('baoyu', 'garden_center'), show('baochai', 'plum_grove'),
     show('daiyu', 'garden_entry')])
say('C05-010', 'narrator',
    '一时宝玉倦怠，欲睡中觉，贾母命人好生哄着，歇一回再来。',
    '宝玉倦怠',
    [hide('daiyu'), hide('baochai')])
say('C05-011', 'qin_ke',
    '我们这里有给宝叔收拾下的屋子，老祖宗放心，只管交与我就是了。',
    '秦氏回话',
    [show('qin_ke', 'garden_center')])
say('C05-012', 'narrator',
    '秦氏又向宝玉的奶娘丫鬟等道：嬷嬷、姐姐们，请宝叔随我来。',
    '随秦氏去',
    [move('qin_ke', 'upper_room_door'), move('baoyu', 'garden_center', 'upper_room_door')])

# ===== c5-sleep : the upper room and the bedchamber ============================
section('c5-sleep', 'c5_ningfu', '宁国府 · 上房', 'upper_room',
        '當下秦氏引了一簇人來至上房內間')
say('C05-013', 'narrator',
    '当下秦氏引了一簇人来到上房内间。宝玉抬头看见一幅画贴在上面，画的人物固好，其故事乃是《燃藜图》，也不看系何人所画，心中便有些不快。',
    '燃藜图',
    [move('qin_ke', 'upper_room'), move('baoyu', 'upper_room')])
say('C05-014', 'narrator',
    '上房里陈设得十分精致。宝玉抬头便看见那幅《燃藜图》，看画中人物固好，却不问他画的是谁，心里先自不快起来。',
    '画中人')
say('C05-015', 'narrator',
    '壁上还有一副对联，写的是——',
    '燃藜图对联', focus='portrait_wall')
say('C05-016', 'narrator',
    '世事洞明皆学问，人情练达即文章。',
    '世事洞明皆学问')
say('C05-017', 'narrator',
    '及看了这两句，纵然室宇精美，铺陈华丽，也断断不肯在这里了。',
    '断断不肯在此')
say('C05-018', 'qin_ke',
    '这里还不好，可往那里去呢？不然往我屋里去吧。',
    '往我屋里去',
    [move('qin_ke', 'bedchamber_door'), move('baoyu', 'upper_room', 'bedchamber_door')])
say('C05-019', 'narrator',
    '宝玉点头微笑。有一个嬷嬷说道：「那里有个叔叔往侄儿房里睡觉的理？」',
    '秦氏卧房',
    [move('qin_ke', 'bedchamber'), move('baoyu', 'bedchamber')])
say('C05-020', 'narrator',
    '案上设着武则天当日镜室中设的宝镜，一边摆着飞燕立着舞过的金盘，盘内盛着安禄山掷过伤了太真乳的木瓜；上面设着寿昌公主于含章殿下卧的榻，悬的是同昌公主制的联珠帐。',
    '床上陈设', focus='screen_bed')
say('C05-021', 'baoyu',
    '这里好！',
    '这里好')
say('C05-022', 'narrator',
    '秦氏笑道：「我这屋子大约神仙也可以住得了。」说毕亲自展开了纱衾，移了鸳枕，服侍宝玉卧好。宝玉便合上眼，惚惚的睡去，犹似秦氏在前，遂悠悠荡荡，随了秦氏，至一所在。',
    '入梦', layer='dream')

# ===== c5-meet : the arch and the fairy =========================================
section('c5-meet', 'c5_taixu', '太虚幻境 · 石牌坊前', 'arch',
        '那寶玉剛合上眼，便惚惚的睡去', layer='dream')
say('C05-023', 'narrator',
    '但见朱栏白石，绿树清溪，真是人迹稀逢，飞尘不到。宝玉在梦中欢喜，想道：「这个去处有趣，我就在这里过一生，纵然失了家也愿意，强如天天被父母师傅打呢。」',
    '朱栏白石',
    [show('baoyu', 'arch'), hide('qin_ke')])
say('C05-024', 'narrator',
    '正走着，忽然听见一派的撫琴之声。',
    '远处琴声')
say('C05-025', 'narrator',
    '歌毕声未息，早见那边走出一个人来，蹁跚袅娜，端的与人不同。',
    '警幻现身',
    [show('jinghuan', 'arch'), move('jinghuan', 'arch', 'gate_outer'), effect('jinghuan', 'jade')])
say('C05-026', 'narrator',
    '那仙姑生得骨骼轻举，腰如约素，行动处如弱柳扶风。原文本有一段《燃藜图》赋铺陈其容貌，此处从略，只留其风神。',
    '警幻风神')
say('C05-027', 'baoyu',
    '神仙姐姐不知从哪里来，如今要往哪里去？也不知这是何处，望乞携带携带。',
    '宝玉问路')
say('C05-028', 'jinghuan',
    '吾居离恨天之上，灌愁海之中，乃放春山遣香洞太虚幻境警幻仙姑是也：司人伦风月之职。',
    '警幻自报家门')
say('C05-029', 'narrator',
    '宝玉忙毕身作揖，听了这番话，方知人间天上果有一处仙乡。壁上题着对联——',
    '牌坊对联')
say('C05-030', 'narrator',
    '假作真时真亦假，无为有处有还无。',
    '假作真时真亦假')

# ===== c5-scroll : the gate and the registry ====================================
section('c5-scroll', 'c5_taixu', '太虚幻境 · 孽海情天宫门', 'gate_outer',
        '轉過牌坊，便是一座宮門', layer='dream')
say('C05-031', 'narrator',
    '转过牌坊，便是一座宫门，上面横书四个大字，道是：「孽海情天」。',
    '孽海情天',
    [move('baoyu', 'arch', 'gate_outer'), move('jinghuan', 'gate_outer', 'gate_inner')])
say('C05-032', 'narrator',
    '宫门两旁还有一副对联，大书云——',
    '孽海情天对联')
say('C05-033', 'narrator',
    '厚地高天，堪叹古今情不尽。痴男怨女，可怜风月债难偿。',
    '堪叹古今情不尽')
say('C05-034', 'baoyu',
    '原来如此。但不知何为「古今之情」，何为「风月之债」？从今倒要领略领略。',
    '宝玉自省')
say('C05-035', 'narrator',
    '不料早把些邪魔招入膏肓。当下随了仙姑进入二层门内，至两边配殿，皆有匾额对联。',
    '两边配殿',
    [move('baoyu', 'gate_outer', 'gate_inner'), move('jinghuan', 'gate_inner', 'hall_left')])
say('C05-036', 'narrator',
    '左边配殿的对联是——',
    '配殿联语')
say('C05-037', 'narrator',
    '春恨秋悲皆自惹，花容月貌为谁妍。',
    '春恨秋悲皆自惹')
say('C05-038', 'narrator',
    '宝玉看了，便知感叹。进门来，只见有十数个大橱，皆用封条封着。',
    '十数个大橱',
    [move('baoyu', 'hall_left', 'registry'), move('jinghuan', 'hall_left', 'registry')])
say('C05-039', 'narrator',
    '看那封条上，皆是各省的地名。宝玉一心只拣自己的家乡封条看，遂无心看别省的了。',
    '各省封条')
say('C05-040', 'narrator',
    '只见那边橱上封条上大书七字云：「金陵十二钗正册」。',
    '金陵十二钗正册')
say('C05-041', 'narrator',
    '宝玉问道：「何为『金陵十二钗正册』？」',
    '请言薄命女')
say('C05-042', 'narrator',
    '警幻道：「即贵省中十二冠首女子之册，故为正册。」',
    '正册')
say('C05-043', 'narrator',
    '宝玉道：「常听人说，金陵极大，怎么只十二个女子？如今单我家里，上上下下，就有几百女孩子呢。」',
    '宝玉追问')
say('C05-044', 'narrator',
    '警幻冷笑道：「贵省女子固多，不过择其紧要者录之。下边二橱则又次之。余者庸常之辈，则无册可录矣。」',
    '在册者八人')
say('C05-045', 'narrator',
    '一面说，一面又翻出「副册」来。',
    '翻出副册')
say('C05-046', 'narrator',
    '宝玉看第一页上，便画着一株桂花，下面有一池沼，其中水涸泥干，莲枯藕败，后面写着——',
    '香菱册页')
say('C05-047', 'narrator',
    '根并荷花一茎香，平生遭际实堪伤。自从两地生孤木，致使香魂返故乡。',
    '根并荷花一茎香')
say('C05-048', 'narrator',
    '宝玉看了不解。便又掷了，再去取「正册」看，只见头一页上便画着两株枯木，木上悬着一围玉带，又有一堆雪，雪下一股金簪。也有四句言词，道是——',
    '钗黛合册')
say('C05-049', 'narrator',
    '可叹停机德，谁怜咏絮才。玉带林中挂，金簪雪里埋。',
    '玉带林中挂', [effect('baoyu', 'rest')])
say('C05-050', 'narrator',
    '宝玉看了仍不解。待要问时，情知他必不肯泄露，待要丢下，又不舍。遂又往后看时，只见画着一张弓，弓上挂着香橼。',
    '元春册页')
say('C05-051', 'narrator',
    '二十年来辨是非，榴花开处照宫闱。三春争及初春景，虎兔相逢大梦归。',
    '二十年来辨是非')
say('C05-052', 'narrator',
    '后面又画着两人放风筝，一片大海，一只大船，船中有一女子掩面泣涕之状。也有四句写云——',
    '探春册页')
say('C05-053', 'narrator',
    '才自精明志自高，生于末世运偏淆。清明涕送江边望，千里东风一梦遥。',
    '才自精明志自高')
say('C05-054', 'narrator',
    '后面又画几缕飞云，一湾逝水。',
    '迎春册页')
say('C05-055', 'narrator',
    '富贵又何为，襁褓之间父母违。展眼吊斜晖，湘江水逝楚云飞。',
    '富贵又何为')
say('C05-056', 'narrator',
    '后面又画着一块美玉，落在泥垢之中。其断语云——',
    '惜春册页')
say('C05-057', 'narrator',
    '欲洁何曾洁，云空未必空。可怜金玉质，终陷淖泥中。',
    '欲洁何曾洁')
say('C05-058', 'narrator',
    '后面忽见画着个恶狼，追扑一美女，欲啖之意。其书云——',
    '中山狼册页')
say('C05-059', 'narrator',
    '子系中山狼，得志便猖狂。金闺花柳质，一载赴黄粱。',
    '子系中山狼')
say('C05-060', 'narrator',
    '后面便是一所古庙，里面有一美人在内看经独坐。其判云——',
    '古庙美人册页')
say('C05-061', 'narrator',
    '勘破三春景不长，缁衣顿改昔年妆。可怜绣户侯门女，独卧青灯古佛旁。',
    '勘破三春景不长')
say('C05-062', 'narrator',
    '后面便是一片冰山，上面有一只雌凤。其判曰——',
    '冰山雌凤册页')
say('C05-063', 'narrator',
    '凡鸟偏从末世来，都知爱慕此生才。一从二令三人木，哭向金陵事更哀。',
    '凡鸟偏从末世来')
say('C05-064', 'narrator',
    '后面又是一座荒村野店，有一美人在那里纺绩。其判云——',
    '荒村野店册页')
say('C05-065', 'narrator',
    '势败休云贵，家亡莫论亲。偶因济村妇，巧得遇恩人。',
    '偶因济村妇')
say('C05-066', 'narrator',
    '后面又画着一盆茂兰，旁有一位凤冠霞帔的美人。也有判云——',
    '茂兰册页')
say('C05-067', 'narrator',
    '桃李春风结子完，到头谁似一盆兰。如冰水好空相妒，枉与他人作笑谈。',
    '到头谁似一盆兰')
say('C05-068', 'narrator',
    '后面又画着高楼大厦，有一美人悬梁自缢。其判云——',
    '高楼悬梁册页')
say('C05-069', 'narrator',
    '情天情海幻情身，情既相逢必主淫。漫言不肖皆荣出，造衅开端实在宁。',
    '造衅开端实在宁')
say('C05-070', 'jinghuan',
    '且随我去游玩奇景，何必在此打这闷葫芦！',
    '掩卷转场',
    [move('jinghuan', 'registry', 'courtyard')])

# ===== c5-banquet : the fairy court ============================================
section('c5-banquet', 'c5_taixu', '太虚幻境 · 警幻院', 'courtyard',
        '寶玉還欲看時，那仙姑恐把仙機洩漏', layer='dream')
say('C05-071', 'narrator',
    '宝玉恍恍惚惚，不觉弃了卷册，又随了警幻来至后面。但见珠帘绣幕，画栋雕檐，说不尽那光摇朱户金铺地，雪照琼窗玉作宫。更见仙花馥郁，异草芬芳，真好个所在。',
    '警幻院',
    [move('baoyu', 'registry', 'courtyard'), effect('baoyu', 'greet')])
say('C05-072', 'jinghuan',
    '你们快出来迎接贵客！',
    '众姊妹出场')
say('C05-073', 'narrator',
    '一语未了，早见一群仙女出来了。宝玉自觉身上污秽不堪，警幻忙携住他的手。',
    '污秽不堪')
say('C05-074', 'narrator',
    '警幻向众姊妹道：「你等不知原委：今日原欲往荣府去接绛珠，适从宁府所过，偶遇宁荣二公之灵，嘱吾云：『吾家自国朝定鼎以来，功名奕世，富贵传流，虽历百年，奈运终数尽……』」',
    '宁荣二公之灵')
say('C05-075', 'narrator',
    '警幻说到这里，又道：「如此嘱吾，故发慈心，引彼至此。先以彼家上中下三等女子之终身册籍，令彼熟玩，尚未觉悟，故引彼再至此处，令其再历饮馔声色之幻，或冀将来一悟，亦未可知也。」',
    '引宝玉入局')
say('C05-076', 'narrator',
    '说毕，携了宝玉入室。但闻一缕幽香，竟不知其所焚何物。',
    '一缕幽香',
    [move('jinghuan', 'courtyard', 'fairy_host'), move('baoyu', 'courtyard', 'fairy_host')])
say('C05-077', 'baoyu',
    '这香是什么香？',
    '问香')
say('C05-078', 'jinghuan',
    '此香尘世中既无，尔何能知！此香乃系诸名山胜境内初生异卉之精，合各种宝林珠树之油所制，名「群芳髓」。',
    '群芳髓')
say('C05-079', 'narrator',
    '宝玉将闻之不禁，及请众仙姑姓名。壁上有一副对联云——',
    '室内对联')
say('C05-080', 'narrator',
    '幽微灵秀地，无可奈何天。',
    '幽微灵秀地')
say('C05-081', 'narrator',
    '因又请问众仙姑姓名：一名痴梦仙姑，一名钟情大士，一名引愁金女，一名度恨菩提，各各道号不一。',
    '四仙姑道号')
say('C05-082', 'narrator',
    '少刻，有小丫鬟来调桌安椅，设摆酒馔。真是：琼浆满泛玻璃盏，玉液浓斟琥珀杯。',
    '设摆酒馔',
    [move('baoyu', 'fairy_host', 'banquet')], focus='banquet')
say('C05-083', 'jinghuan',
    '就将新制《红楼梦》十二支演上来。',
    '演十二支',
    [move('jinghuan', 'fairy_host', 'banquet')])
say('C05-084', 'narrator',
    '舞女们答应了，便轻敲檀板，款按银筝，听他歌道是：「开辟鸿蒙……」方歌了一句，警幻便说道：「此曲不比尘世中所填传奇之曲，必有生旦净末之则，又有南北九宫之限。」',
    '红楼梦引子')
say('C05-085', 'narrator',
    '开辟鸿蒙，谁为情种？都只为风月情浓；趁着这奈何天，伤怀日，寂寥时，试遣愚衷，因此上演出这悲金悼玉的「红楼梦」。',
    '开辟鸿蒙')
say('C05-086', 'narrator',
    '终身误都道是金玉良缘，俺只念木石前盟。空对着，山中高士晶莹雪；终不忘，世外仙姝寂寞林。叹人间，美中不足今方信。纵然是齐眉举案，到底意难平。',
    '终身误')
say('C05-087', 'narrator',
    '枉凝眉一个是阆苑仙葩，一个是美玉无瑕。若说没奇缘，今生偏又遇着他；若说有奇缘，如何心事终虚化？一个枉自嗟呀，一个空劳牵挂；一个是水中月，一个是镜中花。想眼中能有多少泪珠儿，怎经得秋流到冬，春流到夏？',
    '枉凝眉')
say('C05-088', 'narrator',
    '宝玉听了此曲，散漫无稽，不见得好处，但其声韵凄婉，竟能销魂醉魄。因此也不察其原委，问其来历，就暂以此释闷而已。',
    '暂以此释闷')
say('C05-089', 'narrator',
    '恨无常喜荣华正好，恨无常又到。眼睁睁，把万事全抛；荡悠悠，把芳魂消耗。望家乡，路远山高。故向爹娘梦里相寻告：儿命已入黄泉，天伦呵，须要退步抽身早。',
    '恨无常')
say('C05-090', 'narrator',
    '乐中悲襁褓中，父母叹双亡，纵居那绮罗丛，谁知娇养？幸生来，英豪阔大宽宏量，从未将儿女私情略萦心上，好一似，霁月光风耀玉堂。厮配得才貌仙郎，博得个地久天长，准折得幼年时坎坷形状。终久是云散高唐，水涸湘江。这是尘寰中消长数应当，何必枉悲伤。',
    '乐中悲')
say('C05-091', 'narrator',
    '世难容气质美如兰，才华阜比仙，天生成孤癖人皆罕。你道是啖肉食腥膻，视绮罗俗厌；却不知太高人愈妒，过洁世同嫌。可叹这，青灯古殿人将老；辜负了，红粉朱楼春色阑；到头来，依旧是风尘肮脏违心愿。好一似，无瑕白玉遭泥陷；又何须，王孙公子叹无缘。',
    '世难容')
say('C05-092', 'narrator',
    '喜冤家中山狼，无情兽，全不念当日根由，一味的骄奢淫荡贪还构。觑着那，侯门艳质同蒲柳；作践的，公府千金似下流。叹芳魂艳魄，一载荡悠悠。',
    '喜冤家')
say('C05-093', 'narrator',
    '虚花悟将那三春看破，桃红柳绿待如何？把这韶华打灭，觅那清淡天和。说什么，天上夭桃盛，云中杏蕊多；到头来，谁把秋挨过？则看那，白杨村里人呜咽，青枫林下鬼吟哦；更兼着，连天衰草遮坟墓，这的是，昨贫今富人劳碌，春荣秋谢花折磨。似这般，生关死劫谁能躲？闻说道，西方宝树唤婆娑，上结着长生果。',
    '虚花悟')
say('C05-094', 'narrator',
    '聪明累机关算尽太聪明，反算了卿卿性命。生前心已碎，死后性空灵。家富人宁，终有个家亡人散各奔腾。枉费了，意悬悬半世心；好一似，荡悠悠三更梦。忽喇喇似大厦倾，昏惨惨似灯将尽。呀，一场欢喜忽悲辛；叹人世，终难定。',
    '聪明累')
say('C05-095', 'narrator',
    '留余庆，留余庆，忽遇恩人；幸娘亲，幸娘亲，积得阴功。劝人生，济困扶穷，休似俺那爱银钱、忘骨肉的狠舅奸兄！正是乘除加减，上有苍穹。',
    '留余庆')
say('C05-096', 'narrator',
    '晚韶华镜里恩情，更那堪梦里功名；那美韶华去之何迅，再休提绣帐鸳衾。只这带珠冠，披凤袄，也抵不了无常性命。虽说是，人生莫受老来贫，也须要阴骘积儿孙。气昂昂头戴簪缨，光灿灿胸悬金印；威赫赫爵禄高登，昏惨惨黄泉路近。问古来将相可还存？也只是虚名儿与后人钦敬。',
    '晚韶华')
say('C05-097', 'narrator',
    '好事终画梁春尽落香尘，擅风情，秉月貌，便是败家的根本；箕裘颓堕皆从敬，家事消亡首罪宁，宿孽总因情。',
    '好事终')
say('C05-098', 'narrator',
    '收尾：飞鸟各投林为官的、家业凋零，富贵的、金银散尽，有恩的、死里逃生，无情的、分明报应，欠命的、命已还，欠泪的、泪已尽。冤冤相报实非轻，分离聚合皆前定；欲知命短问前生，老来富贵也真侥幸。看破的、遁入空门，痴迷的、枉送了性命；好一似食尽鸟投林，落了片白茫茫大地真干净。',
    '飞鸟各投林')
say('C05-099', 'jinghuan',
    '痴儿竟尚未悟！',
    '痴儿竟尚未悟',
    [move('jinghuan', 'banquet', 'courtyard')])
say('C05-100', 'narrator',
    '警幻见宝玉甚无趣味，因叹：「痴儿竟尚未悟！」那宝玉忙止歌姬不必再唱，自觉朦胧恍惚，告醉求卧。',
    '告醉求卧',
    [move('baoyu', 'banquet', 'courtyard')])

# ===== c5-boudoir : the boudoir =================================================
section('c5-boudoir', 'c5_taixu', '太虚幻境 · 香闺绣阁', 'boudoir',
        '警幻便命撤去殘席，送寶玉至一香閨繡閣之中', layer='dream')
say('C05-101', 'narrator',
    '警幻便命撤去残席，送宝玉至一香闺绣阁之中，其间铺陈之盛，乃素所未见之物。',
    '香闺绣阁',
    [move('baoyu', 'courtyard', 'boudoir_door', 'boudoir'),
     move('jinghuan', 'courtyard', 'boudoir_door', 'boudoir')])
say('C05-102', 'narrator',
    '更可骇者，早有一位女子在内，其鲜艳妩媚，有似乎宝钗，风流袅娜，则又如黛玉。正不知何意，忽警幻道：「尘世中多少富贵之家，那些绿窗风月，绣阁烟霞，皆被淫污纨袴与那些流荡女子悉皆玷辱。更可恨者，自古来多少轻薄浪子，皆以『好色不淫』为饰，又以『情而不淫』作案，此皆饰非掩丑之语也。好色即淫，知情更淫。」',
    '警幻设局')
say('C05-103', 'narrator',
    '宝玉道：「仙姑差了。我因懒于读书，家父母尚每垂训饬，岂敢再冒『淫』字。况且年纪尚小，不知『淫』字为何物。」',
    '宝玉不敢')
say('C05-104', 'jinghuan',
    '非也。淫虽一理，意则有别。如世之好淫者，不过悦容貌，喜歌舞，恨行乐，贪声色之乐耳。',
    '淫虽一理')
say('C05-105', 'jinghuan',
    '吾居离恨天之上，灌愁海之中，及放春山遣香洞太虚幻境警幻仙姑是也……',
    '警幻复述来历')
say('C05-106', 'narrator',
    '警幻因又指着宝玉道：「汝今独得此二字，在闺阁中，固可为良友，然于世道中未免迂阔怪诡，百口嘲谤，万目睚眦。今既遇令祖宁荣二公剖腹深嘱，吾不忍君独为我闺阁增光，见弃于世道，是以特引前来，醉以灵酒，沁以仙茗，警以妙曲。」',
    '乳名兼美')
say('C05-107', 'narrator',
    '警幻又道：「再将吾妹一人，乳名兼美字可卿者，许配于汝。今夕良时，即可成姻。不过令汝领略此仙闺幻境之风光尚如此，何况尘境之情景哉？而今后万万解释，改悟前情，留意于孔孟之间，委身于经济之道。」',
    '警幻授物')
say('C05-108', 'narrator',
    '说毕便秘授以云雨之事，推宝玉入房，将门掩上自去。',
    '警幻叮嘱')
say('C05-109', 'narrator',
    '警幻掩门自去，宝玉恍恍惚惚，不知身在梦中还是醒着。',
    '宝玉不解')

# ===== c5-mijing : the ford =====================================================
section('c5-mijing', 'c5_mijing', '迷津 · 黑溪', 'bank',
        '因二人攜手出去遊頑之時，忽至一個所在', layer='dream')
say('C05-110', 'narrator',
    '那宝玉恍恍惚惚，依警幻所嘱之言，未免有儿女之事，难以尽述。至次日，便柔情缱绻，软语温存，与可卿难解难分。',
    '儿女之事',
    # 换场时引擎会把所有立绘置为不可见（engine.ts 的 scene reset），
    # 宝玉必须先 show 再 move，否则 C05-111 会抛「移动角色未显示：baoyu」。
    [hide('jinghuan'), show('qin_ke', 'bank'), show('baoyu', 'bank')])
say('C05-111', 'narrator',
    '因二人携手出去游顽之时，忽至一个所在，但见荆榛遍地，狼虎同群，迎面一道黑溪阻路，并无桥梁可通。',
    '荆榛黑溪')
say('C05-112', 'baoyu',
    '此系何处？',
    '宝玉问路')
say('C05-113', 'narrator',
    '正在犹豫之间，忽见警幻后面追来，告道：「快休前进，作速回头要紧！」',
    '警幻追来',
    [show('jinghuan', 'stream_edge')])
say('C05-114', 'jinghuan',
    '此即迷津也。深有万丈，遥亘千里，中无舟楫可通，只有一个木筏，乃木居士掌舵，灰侍者撑篙，不受金银之谢，但遇有缘者渡之。',
    '迷津')
say('C05-115', 'jinghuan',
    '尔今偶游至此，设如堕落其中，则深负我从前谆谆警戒之语矣。',
    '警戒之语')
say('C05-116', 'narrator',
    '话犹未了，只听迷津内水响如雷，竟有许多夜叉海鬼将宝玉拖将下去。',
    '夜叉海鬼',
    [move('baoyu', 'stream_edge'), hide('qin_ke')])
say('C05-117', 'baoyu',
    '可卿救我！',
    '可卿救我')
say('C05-118', 'narrator',
    '吓得宝玉汗下如雨，一面失声喊叫：「可卿救我！」',
    '汗下如雨')

# ===== c5-wake : back to reality ================================================
section('c5-wake', 'c5_ningfu', '宁国府 · 秦氏卧房', 'bedchamber',
        '嚇得襲人輩眾丫鬟忙上來摟住', layer='present')
say('C05-119', 'narrator',
    '吓得袭人辈众丫鬟忙上来搂住，叫：「宝玉别怕，我们在这里！」',
    '梦醒',
    [hide('baoyu'), hide('jinghuan'), hide('qin_ke'),
     show('baoyu', 'bedchamber'), show('xiren', 'screen_bed'),
     show('qin_ke', 'bedchamber_door')])
say('C05-120', 'narrator',
    '那宝玉从梦中醒来，满头是汗。袭人一面替他整衣，一面埋怨他怎么睡得这样沉。',
    '梦醒余波')
say('C05-121', 'narrator',
    '却说秦氏正在房外嘱咐小丫头们好生看着猫儿狗儿打架，忽听宝玉在梦中唤他的小名，因纳闷道——',
    '秦氏纳闷',
    focus='bedchamber_door')
say('C05-122', 'qin_ke',
    '我的小名这里从没没人知道的，他如何知道，在梦里叫出来？',
    '我的小名这里从没没人知道的')
say('C05-123', 'narrator',
    '一场幽梦同谁诉，千古情人独我知。',
    '一场幽梦同谁诉')


def build_story():
    ids = [s['id'] for s in steps]
    assert len(ids) == len(set(ids)), 'duplicate node id'
    for s in steps:
        assert s['chapter'] in section_titles, f"{s['id']}: unknown section"
    # 镜头要跟着人走。段首的 section(focus=...) 只定一个默认落点，薄命司那 40 个
    # 节点原先全都停在宫门上——读判词、翻册页时画面还对着「孽海情天」四个字。
    # 于是按走位把后半段的焦点推到配殿、再推进薄命司的橱与案。
    for s in steps:
        n = int(s['id'].split('-')[1])
        if s['chapter'] == 'c5-scroll':
            if 35 <= n <= 37:
                s['focus'] = 'hall_left'      # 进二层门，看两边配殿的匾对
            elif 38 <= n <= 44:
                s['focus'] = 'registry'       # 十数个大橱、各省封条、正册
            elif 45 <= n <= 70:
                s['focus'] = 'scroll_desk'    # 取出册页，一页页看判词
        elif s['chapter'] == 'c5-banquet' and n >= 76:
            s['focus'] = 'banquet'            # 入室入席之后镜头才落到席面上
    (ROOT / 'design/chapter05-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': start, 'book': 5}
                for (sid, title, scene), start in zip(
                    SECTIONS, [s['id'] for s in steps
                               if s['chapter'] == SECTIONS[0][0]])]
    # first node of each section
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 5}
                for sid, title, scene in SECTIONS]
    (ROOT / 'design/chapter05-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter05-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter05-sections.json  %d sections' % n_sections)
