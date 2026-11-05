#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-thirteen's stages, script and section table.

第十三回 · 秦可卿死封龙禁尉 · 王熙凤协理宁国府

Chapter thirteen owns this generator; nothing here touches an earlier chapter.

Outputs:
  maps/c13_funeral.tmj        新舞台：宁国府 · 会芳园停灵与穿堂
  maps/c13_baosha.tmj         新舞台：宁国府 · 三间抱厦（凤姐理事处）
  design/chapter13-story.json   节点 C13-001..
  design/chapter13-sections.json

本回用：maps/night.tmj（贾母院）、maps/c6_wangchui.tmj（凤姐院）、
maps/c5_ningfu.tmj（宁府会芳园与秦氏卧房）、maps/c11_tianxiang.tmj（天香楼）。

三张地图的分工：
  c13_funeral  宁府停灵：门洞大开、灯笼照如白昼，正中是灵前的抱厦与大厅，
                贾珍在这里见客、设醮、议事。原文说「一条白漫漫人来人往」，
                所以门与厅之间留一条贯通的动线，人物从街上一路走进灵前。
  c13_baosha   三间抱厦：凤姐列五件弊病的地方。原文「凤姐儿来至三间一所
                抱厦内坐了，因想……此五件实是宁国府中风俗」——是一间独立的
                小屋，与停灵厅隔开，好让读者看见她独自坐定想事。
  c5_ningfu    秦氏卧房（第十二回已建）：停灵前夜贾蓉奔丧之地不在此段，
                本回只用会芳园与上房的贾珍、尤氏。

人物：戴权、宝珠为本回新立绘；凤姐、平儿、宝玉、袭人、贾母、贾珍、尤氏、
贾蓉、薛蟠、贾代儒、秦业、秦钟复用既有资产。贾敬始终未归府（原文写明
「不肯回家染了红尘」），不造人出场；贾赦、贾政只在列名与祭吊中提及，不上场。

Usage: python3 scripts/build_chapter13.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

BACKUP = ROOT / 'artifacts/backups/2026-11-03-chapter13'
PUBLISH_MAP = True
MAP_DIR = ROOT / 'maps' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter13'
STAGE_DIR = ROOT / 'design' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter13'


def at(c, r, dx=0.0, dy=0.0):
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {
    # 宁国府停灵：府门洞开，街上一条白漫漫；往里是上房（贾珍与宝玉议协理）
    # 与大厅（停灵、见客、议事）。动线自街心直入大厅，人物一路走进灵前。
    'c13_funeral': {
        'name': '宁国府 · 上房与停灵',
        'theme': 'interior',
        # 大厅（HALL，行 7-16）在上，上房（SHANG，行 17-26）在中间，
        # 街面（A0，行 27-33）在下。三段贴邻：门洞大开，人来人往，
        # 站着说话的人不必另起一张图。
        'zones': [[10, 27, 22, 7, False], [14, 17, 14, 10, True, 'SHANG'],
                  [12, 7, 18, 10, True, 'HALL']],
        'anchors': {
            'street': [20, 30],
            'gate': [20, 27],
            'room_door': [18, 18],
            'room': [20, 20],
            'hall_door': [19, 11],
            'hall': [21, 12],
            'altar': [24, 10],
            'you_room': [15, 12],
        },
        'routes': {
            'to_hall': ['street', 'gate', 'room_door', 'room', 'hall_door', 'hall'],
            'to_altar': ['hall', 'altar'],
            'to_you': ['hall', 'you_room'],
        },
        'labels': [['宁国府门', 20, 29], ['上房', 19, 21], ['大厅 · 停灵', 21, 8],
                   ['灵前', 25, 9]],
        'props': [
            ('ning-hall', *at(21, 12), .74, 'HALL'),
            # 灵前：棺木与供案。棺用 canopy-bed 倒过来的意象不贴切，
            # 这里用既有 qin-bed（秦氏卧房的架子床）改成停灵木榻的意象不对，
            # 故灵前只摆供桌与屏风，棺木以「大台矶」意象省去，避免家具错读。
            ('altar-table', *at(24, 10, 0, 0), .70, 'HALL'),
            ('wood-screen', *at(26, 11, 0, -60), .74, 'HALL'),
            ('brazier', *at(17, 11, 0, 0), .62, 'HALL'),
            ('lamp-stand', *at(15, 15, 0, 0), .64, 'HALL'),
            ('official-chair', *at(19, 13, -180, 40), .70, 'HALL'),
            ('official-chair', *at(19, 13, -180, -40), .66, 'HALL'),
            # 上房：贾珍与宝玉议协理的地方，内眷陪坐于此。
            ('square-table', *at(22, 21, 0, 0), .58, 'SHANG'),
            ('official-chair', *at(18, 22, 0, 0), .62, 'SHANG'),
            ('tea-table', *at(25, 19, 0, 0), .52, 'SHANG'),
            ('lamp-stand', *at(16, 24, 0, 0), .60, 'SHANG'),
            ('bamboo-gate', *at(18, 18, 0, 0), .56, 'SHANG'),
            # 街面：府门洞开，灯笼照如白昼。
            ('manor-main-gate', *at(20, 28, 0, 0), .70),
            ('flower-gate', *at(14, 30, 0, 0), .48),
            ('garden-tree', *at(27, 30, 0, 0), .94),
            # 原 at(12,30) 落在取景框外（偏西偏北），沿南缘东移到 at(18,31)，
            # 仍贴街面、避开两只石狮与门洞，由 street / gate 锚点取景到。
            ('garden-tree', *at(18, 31, 0, 0), .90),
            ('stone-lion', *at(16, 29, 0, 0), .54),
            ('stone-lion', *at(24, 29, 0, 0), .54),
        ],
        'walls': [[10, 27, 32, 27], [10, 27, 10, 34], [32, 27, 32, 34],
                  [10, 34, 32, 34], [14, 17, 14, 27], [28, 17, 28, 27]],
        'terraces': [[18, 27, 4, 6, 'path'], [19, 18, 3, 9, 'path']],
    },
    # 三间抱厦：凤姐独坐，想出宁国府的五件弊病。
    'c13_baosha': {
        'name': '宁国府 · 三间抱厦',
        'theme': 'interior',
        'zones': [[13, 10, 14, 9, True, 'ROOM']],
        'anchors': {
            'door': [14, 18],
            'seat': [19, 12],
            'desk': [24, 13],
            'side': [16, 15],
        },
        'routes': {
            'main': ['door', 'seat'],
            'to_desk': ['seat', 'desk'],
            'to_side': ['door', 'side'],
        },
        'labels': [['抱厦', 19, 10], ['理事处', 19, 15]],
        'props': [
            ('main-hall', *at(19, 13), .72, 'ROOM'),
            # 座位在走道北侧（走道是 row 18 与 col 19），家具一律避开这两条线，
            # 否则 footprint 会把走廊拦腰截断，人物走不到座位。
            ('official-chair', *at(19, 12, 0, 0), .66, 'ROOM'),
            ('square-table', *at(17, 13, 0, 0), .58, 'ROOM'),
            ('writing-desk', *at(24, 13, 0, 0), .64, 'ROOM'),
            ('tea-table', *at(16, 15, 0, 0), .54, 'ROOM'),
            ('lamp-stand', *at(24, 10, 0, 0), .60, 'ROOM'),
            ('wood-screen', *at(15, 11, 0, 0), .62, 'ROOM'),
        ],
        'terraces': [[17, 17, 4, 3, 'path']],
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
    ('c13-dream', '凤姐院 · 秦氏托梦', 'c6_wangchui'),
    ('c13-news', '凤姐院 · 云板报丧', 'c6_wangchui'),
    ('c13-mourning', '贾母院 · 宝玉呕血', 'night'),
    ('c13-ningguo', '宁国府 · 停灵', 'c13_funeral'),
    ('c13-coffin', '宁国府 · 樯木板', 'c13_funeral'),
    ('c13-title', '宁国府 · 捐龙禁尉', 'c13_funeral'),
    ('c13-visitors', '宁国府 · 亲友祭吊', 'c13_funeral'),
    ('c13-recommend', '宁国府 · 宝玉荐凤姐', 'c13_funeral'),
    ('c13-assist', '宁国府 · 凤姐协理', 'c13_funeral'),
    ('c13-five', '三间抱厦 · 五件弊病', 'c13_baosha'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 13, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c13-dream : 秦氏托梦 ==============================
# 原文位置：开篇「话说凤姐儿自贾琏送黛玉往扬州去后」，
# 凤姐夜梦秦氏，交代祖茭祭祀与家塾供给两件未妥，并留下「三春过后诸芳尽」的谶语。
section('c13-dream', 'c6_wangchui', '凤姐院 · 房内', 'feng_room',
        '话说凤姐儿自贾琏送黛玉往扬州去后，心中实在无趣')
say('C13-001', 'narrator',
    '话说凤姐儿自贾琏送黛玉往扬州去后，心中实在无趣，每到晚间，'
    '不过和平儿说笑一回，就胡乱睡了。', '心中实在无趣',
    [show('feng', 'feng_room'), show('ping_er', 'feng_room')])
say('C13-002', 'narrator',
    '这日夜间，正和平儿灯下拥炉倦绣，早命浓薰绣被，二人睡下。'
    '屈指算行程该到何处，不知不觉已交三鼓，平儿已睡熟了。'
    '凤姐方觉星眼微朦，恍惚只见秦氏从外走来。', '恍惚只见秦氏从外走来',
    [effect('feng', 'rest'), hide('ping_er')])
say('C13-003', 'qin_ke',
    '秦氏含笑说道：“婶子好睡！我今日回去，你也不送我一程。'
    '因娘儿们素日相好，我舍不得婶子，故来别你一别。'
    '还有一件心愿未了，非告诉婶子，别人未必中用。”', '非告诉婶子，别人未必中用',
    [show('qin_ke', 'back_gate'), move('qin_ke', 'market', 'zhou_court', 'zhou_room',
                                       'daoting', 'yingbi', 'platform', 'feng_room')])
say('C13-004', 'feng',
    '凤姐听了，恍惚问道：“有何心愿？你只管托我就是了。”'
    '秦氏道：“婶婶，你是个脂粉队里的英雄……'
    '常言‘月满则亏，水满则溢’，又道是‘登高必跌重’。'
    '如今我们家赫赫扬扬，已将百载，一日倘或乐极悲生，'
    '若应了那句‘树倒猢狲散’的俗语，岂不虚称了一世的诗书旧族了！”',
    '月满则亏，水满则溢', [effect('feng', 'greet')])
say('C13-005', 'qin_ke',
    '秦氏冷笑道：“婶子好痴也。否极泰来，荣辱自古周而复始，岂人力能可保常的。'
    '但如今能于荣时筹划下将来衰时的世业，亦可谓常保永全了。'
    '即如今日诸事都妥，只有两件未妥。', '只有两件未妥',
    [effect('qin_ke', 'idle')])
say('C13-006', 'narrator',
    '秦氏道：“目今祖茭虽四时祭祀，只是无一定的钱粮；第二，家塾虽立，无一定的供给。'
    '依我想来，如今盛时固不缺祭祀供给，但将来败落之时，此二项有何出处？'
    '莫若依我定见，趁今日富贵，将祖茭附近多置田庄房舍地亩，以备祭祀供给之费，'
    '皆出自此处，将家塾亦设于此。', '只有两件未妥',
    [effect('qin_ke', 'greet')])
say('C13-007', 'qin_ke',
    '合同族中长幼，大家定了则例，日后按房掌管这一年的地亩、钱粮、祭祀、供给之事。'
    '如此周流，又无争竞，亦不有典卖诸弊。'
    '便是有了罪，凡物可入官，这祭祀产业连官也不入的。'
    '便败落下来，子孙回家读书务农，也有个退步，祭祀又可永继。',
    '祭祀产业连官也不入的', [effect('qin_ke', 'idle')])
say('C13-008', 'qin_ke',
    '秦氏道：“眼见不日又有一件非常喜事，真是烈火烹油，鲜花著锦之盛。'
    '要知道，也不过是瞬间的繁华，一时的欢乐，万不可忘了那‘盛筵必散’的俗语。'
    '此时若不早为后虑，临期只恐后悔无益了。”', '盛筵必散',
    [effect('qin_ke', 'idle')])
say('C13-009', 'feng',
    '凤姐忙问：“有何喜事？”秦氏道：“天机不可泄漏。'
    '只是我与婶子好了一场，临别赠你两句话，须要记著。”', '天机不可泄漏',
    [effect('feng', 'greet')])
say('C13-010', 'narrator',
    '因念道：三春过后诸芳尽，各自须寻各自门。',
    '三春过后诸芳尽', [effect('feng', 'rest')])
say('C13-011', 'narrator',
    '凤姐还欲问时，只听二门上传事云板连叩四下，将凤姐惊醒。'
    '人回：“东府蓉大奶奶没了。”', '云板连叩四下',
    [hide('qin_ke'), effect('feng', 'anger')])

# ===== c13-news : 云板报丧 ==============================
section('c13-news', 'c6_wangchui', '凤姐院 · 房内', 'feng_room',
        '凤姐闻听，吓了一身冷汗')
say('C13-012', 'narrator',
    '凤姐闻听，吓了一身冷汗，出了一回神，只得忙忙的穿衣，往王夫人处来。',
    '忙忙的穿衣', [move('feng', 'feng_room', 'hall')])
say('C13-013', 'narrator',
    '彼时合家皆知，无不纳罕，都有些疑心。那长一辈的想他素日孝顺，'
    '平一辈的想他素日和睦亲密，下一辈的想他素日慈爱，'
    '以及家中仆从老小想他素日怜贫惜贱，慈老爱幼之恩，莫不悲嚎痛哭者。',
    '无不纳罕', offscreen=True)

# ===== c13-mourning : 宝玉呕血 ==========================
section('c13-mourning', 'night', '贾母院 · 碧纱橱外间', 'baoyu_bed',
        '如今从梦中听见说秦氏死了')
say('C13-020', 'narrator',
    '却说宝玉因近日林黛玉回去，剩得自己孤凄，也不和人顽耍，'
    '每到晚间便索然睡了。如今从梦中听见说秦氏死了，'
    '连忙翻身爬起来，只觉心中似戳了一刀的不忍，哇的一声，直奔出一口血来。',
    '直奔出一口血来', [show('baoyu', 'baoyu_bed'), show('xiren', 'xiren_place')])
say('C13-021', 'baoyu',
    '袭人等慌慌忙忙上来搀扶，问是怎么样，又要回贾母来请大夫。'
    '宝玉笑道：“不用忙，不相干，这是急火攻心，血不归经。”', '急火攻心，血不归经',
    [move('xiren', 'xiren_place', 'bedside'), effect('baoyu', 'anger')])
say('C13-022', 'narrator',
    '说着便爬起来，要衣服换了，来见贾母，即时要过去。'
    '袭人见他如此，心中虽放不下，又不敢拦，只是由他罢了。', '即时要过去',
    [move('baoyu', 'baoyu_bed', 'outer_door')])
say('C13-023', 'grandmother',
    '贾母见他要去，因说：“才咽气的人，那里不干净，二则夜里风大，'
    '等明早再去不迟。”宝玉那里肯依。', '等明早再去不迟',
    [show('grandmother', 'grandmother_bed'), effect('grandmother', 'rest')])
say('C13-024', 'narrator',
    '贾母命人备车，多派跟随人役，拥护前来。'
    '一直到了宁国府前，只见府门洞开，两边灯笼照如白昼，'
    '乱烘烘人来人往，里面哭声摇山振岳。', '府门洞开，灯笼照如白昼',
    [move('baoyu', 'outer_door', 'night_talk')])

# ===== c13-ningguo : 宁国府停灵 ==========================
# 原文位置：宝玉到了宁国府，奔至停灵之室痛哭；见过尤氏与贾珍；
# 贾珍命人择日停灵七七四十九日，单请一百单八众禅僧在大厅拜大悲忏，
# 另设一坛于天香楼上，九十九位全真道士打四十九日解冤洗业醮。
section('c13-ningguo', 'c13_funeral', '宁国府 · 停灵大厅', 'hall',
        '宝玉下了车，忙忙奔至停灵之室，痛哭一番')
say('C13-030', 'narrator',
    '宝玉下了车，忙忙奔至停灵之室，痛哭一番。'
    '然后见过尤氏。谁知尤氏正犯了胃疼旧疾，睡在床上。'
    '然后又出来见贾珍。', '痛哭一番',
    [show('baoyu', 'gate'), move('baoyu', 'room_door', 'room', 'hall_door', 'hall'),
     show('you_shi', 'you_room'), show('jia_zhen', 'hall')])
say('C13-031', 'narrator',
    '彼时贾代儒、贾敕、贾效、贾敦、贾赦、贾政、贾琮、贾璘、贾蔷、'
    '贾芸、贾芹、贾蓁、贾萍、贾藻、贾蘅、贾芬、贾芳、贾兰、贾菌、贾芝等都来了。'
    '贾珍哭的泪人一般。', '贾珍哭的泪人一般',
    [effect('jia_zhen', 'anger')])
say('C13-032', 'jia_zhen',
    '贾珍正和贾代儒等说道：“合家大小，远近亲友，谁不知我这媳妇比儿子还强十倍。'
    '如今伸腿去了，可见这长房内绝灭无人了。”说着又哭起来。',
    '比儿子还强十倍', [effect('jia_zhen', 'anger')])
say('C13-033', 'narrator',
    '众人忙劝：“人已辞世，哭也无益，且商议如何料理要紧。”'
    '贾珍拍手道：“如何料理，不过尽我所有罢了！”', '尽我所有罢了',
    [effect('jia_zhen', 'anger')])
say('C13-034', 'narrator',
    '正说着，只见秦业、秦钟并尤氏的几个眷属尤氏姊妹也都来了。'
    '贾珍便命贾琼、贾琛、贾璘、贾蔷四个人去陪客，'
    '一面吩咐去请钦天监阴阳司来择日，择准停灵七七四十九日。',
    '停灵七七四十九日', [show('qin_ye', 'room'), show('qin_zhong', 'room')])
say('C13-035', 'narrator',
    '贾珍命，三日后开丧送讣闻。这四十九日，单请一百单八众禅僧在大厅上拜大悲忏，'
    '超度前亡后化诸魂，以免亡者之罪；另设一坛于天香楼上，'
    '是九十九位全真道士，打四十九日解冤洗业醮。', '一百单八众禅僧',
    [effect('jia_zhen', 'greet')])
say('C13-036', 'narrator',
    '然后停灵于会芳园中，灵前另外五十众高僧、五十众高道，对坛按七作好事。'
    '那贾敬闻得长孙媳死了，因自为早晚就要飞升，'
    '如何肯又回家染了红尘，将前功尽弃呢，因此并不在意，只凭贾珍料理。',
    '只凭贾珍料理', [effect('jia_zhen', 'idle')])

# ===== c13-coffin : 樯木板 ==============================
# 原文位置：贾珍嫌杉木板不中用，薛蟠说店里有一副「樯木」，
# 帮底皆厚八寸，纹若槟榔，味若檀麝，以手扣之，玎珰如金玉；
# 薛蟠道「拿一千两银子来，只怕也没处买去」——这是本回最大的一笔银子。
section('c13-coffin', 'c13_funeral', '宁国府 · 停灵大厅', 'hall',
        '贾珍见父亲不管，亦发恣意奢华')
say('C13-040', 'narrator',
    '贾珍见父亲不管，亦发恣意奢华。看板时，几副杉木板皆不中用。'
    '可巧薛蟠来吊问，因见贾珍寻好板，便说道：“我们木店里有一副板，'
    '叫作什么樯木，出在潢海铁网山上，作了棺材，万年不坏。”',
    '叫作什么樯木', [show('xuepan', 'gate'), move('xuepan', 'room_door', 'room', 'hall')])
say('C13-041', 'xuepan',
    '薛蟠道：“这还是当年先父带来，原系义忠亲王老千岁要的，'
    '因他坏了事，就不曾拿去。现在还封在店内，也没有人出价敢买。'
    '你若要，就抬来使罢。”', '就抬来使罢',
    [effect('xuepan', 'greet')])
say('C13-042', 'narrator',
    '贾珍听说，喜之不尽，即命人抬来。大家看时，只见帮底皆厚八寸，'
    '纹若槟榔，味若檀麝，以手扣之，玎珰如金玉。大家都奇异称赞。',
    '帮底皆厚八寸', [effect('jia_zhen', 'greet')])
say('C13-043', 'xuepan',
    '贾珍笑问：“价值几何？”薛蟠笑道：“拿一千两银子来，只怕也没处买去。'
    '什么价不价，赏他们几两工钱就是了。”', '拿一千两银子来',
    [effect('xuepan', 'idle')])
say('C13-044', 'narrator',
    '贾珍听说，忙谢不尽，即命解锯糊漆。'
    '贾政因劝道：“此物恐非常人可享者，殓以上等杉木也就是了。”'
    '此时贾珍恨不能代秦氏之死，这话如何肯听。', '殓以上等杉木也就是了',
    [effect('jia_zhen', 'anger')])
say('C13-045', 'narrator',
    '因忽又听得秦氏之丫鬟名唤瑞珠者，见秦氏死了，他也触柱而亡。'
    '此事可罕，合族人也都称叹。贾珍遂以孙女之礼敛殡，'
    '一并停灵于会芳园中之登仙阁。', '触柱而亡',
    [effect('jia_zhen', 'rest')])
say('C13-046', 'narrator',
    '小丫鬟名宝珠者，因见秦氏身无所出，乃甘心愿为义女，'
    '誓任摔丧驾灵之任。贾珍喜之不尽，即时传下，从此皆呼宝珠为小姐。'
    '那宝珠按未嫁女之丧，在灵前哀哀欲绝。', '愿为义女',
    [show('bao_zhu', 'altar'), move('bao_zhu', 'hall_door', 'altar'),
     effect('bao_zhu', 'anger')])

# ===== c13-title : 捐龙禁尉 ==============================
# 原文位置：首七第四日，大明宫掌宫内相戴权来上祭；贾珍趁机要为贾蓉捐个前程，
# 「平准一千二百两银子，送到我家就完了」。
section('c13-title', 'c13_funeral', '宁国府 · 停灵大厅', 'hall',
        '可巧这日正是首七第四日')
say('C13-050', 'narrator',
    '贾珍因想着贾蓉不过是个黉门监，灵幡经榜上写时不好看，便是执事也不多，'
    '因此心下甚不自在。可巧这日正是首七第四日，'
    '早有大明宫掌宫内相戴权先备了祭礼遣人来，次后坐了大轿，打伞鸣锣，亲来上祭。',
    '大明宫掌宫内相戴权', [show('dai_quan', 'gate'), move('dai_quan', 'room_door', 'room', 'hall')])
say('C13-051', 'narrator',
    '贾珍忙接着，让至逗蜂轩献茶。贾珍心中打算定了主意，'
    '因而趁便就说要与贾蓉捐个前程的话。戴权会意，因笑道：'
    '“想是为丧礼上风光些。”', '要与贾蓉捐个前程',
    [effect('dai_quan', 'greet'), effect('jia_zhen', 'greet')])
say('C13-052', 'dai_quan',
    '戴权道：“事倒凑巧，正有个美缺，如今三百员龙禁尉短了两员。'
    '昨儿襄阳侯的兄弟老三来求我，现拿了一千五百两银子，送到我家里。'
    '还剩了一个缺，谁知永兴节度使冯胖子来求，要与他孩子捐，我就没工夫应他。'
    '既是咱们的孩子要捐，快写个履历来。”', '快写个履历来',
    [effect('dai_quan', 'idle')])
say('C13-053', 'narrator',
    '贾珍听说，忙吩咐：“快命书房里人恭敬写了大爷的履历来。”'
    '小厮不敢怠慢，去了一刻，便拿了一张红纸来与贾珍。'
    '贾珍看了，忙送与戴权。', '一张红纸来与贾珍',
    [effect('jia_zhen', 'greet')])
say('C13-054', 'narrator',
    '看时，上面写道：江南江宁府江宁县监生贾蓉，年二十岁。'
    '曾祖，原任京营节度使世袭一等神威将军贾代化，'
    '祖，乙卯科进士贾敬，父，世袭三品爵威烈将军贾珍。',
    '世袭三品爵威烈将军贾珍', [effect('dai_quan', 'idle')])
say('C13-055', 'dai_quan',
    '戴权看了，回手便递与一个贴身的小厮收了，说道：'
    '“回来送与户部堂官老赵，说我拜上他，起一张五品龙禁尉的票，'
    '再给个执照，就把这履历填上，明儿我来兑银子送去。”',
    '起一张五品龙禁尉的票', [effect('dai_quan', 'greet')])
say('C13-056', 'narrator',
    '小厮答应了，戴权也就告辞了。贾珍十分款留不住，只得送出府门。'
    '临上轿，贾珍因问：“银子还是我到部兑，还是一并送入老内相府中？”'
    '戴权道：“若到部里，你又吃亏了。不如平准一千二百两银子，送到我家就完了。”',
    '平准一千二百两银子', [move('dai_quan', 'hall_door', 'room', 'gate'),
                             effect('jia_zhen', 'greet')])
say('C13-057', 'narrator',
    '贾珍感谢不尽，只说：“待服满后，亲带小犬到府叩谢。”于是作别。',
    '亲带小犬到府叩谢', [hide('dai_quan')])

# ===== c13-visitors : 亲朋祭吊 ==========================
section('c13-visitors', 'c13_funeral', '宁国府 · 停灵大厅', 'hall',
        '接著，便又听喝道之声')
say('C13-060', 'narrator',
    '接著，便又听喝道之声，原来是忠靖侯史鼎的夫人来了。'
    '王夫人、邢夫人、凤姐等刚迎入上房，又见锦乡侯、川宁侯、寿山伯三家祭礼摆在灵前。'
    '少时，三人下轿，贾政等忙接上大厅。', '锦乡侯、川宁侯、寿山伯',
    [show('wang', 'hall'), show('xing', 'hall'), show('feng', 'hall')])
say('C13-061', 'narrator',
    '如此亲朋你来我去，也不能胜数。只这四十九日，宁国府街上一条白漫漫人来人往，'
    '花簇簇官去官来。', '一条白漫漫人来人往',
    [effect('feng', 'idle')])
say('C13-062', 'narrator',
    '贾珍命贾蓉次日换了吉服，领凭回来。'
    '灵前供用执事等物俱按五品职例。'
    '灵牌疏上皆写「天朝诰授贾门秦氏恭人之灵位」。'
    '会芳园临街大门洞开，旋在两边起了鼓乐厅，'
    '两班青衣按时奏乐，一对对执事摆的刀斩斧齐。',
    '灵前供用执事等物俱按五品职例', [show('jia_rong', 'gate'),
                                     move('jia_rong', 'room_door', 'room', 'hall')])
say('C13-063', 'narrator',
    '更有两面朱红销金大字牌对竖在门外，上面大书：'
    '「防护内廷紫禁道御前侍卫龙禁尉」。'
    '对面高起著宣坛，僧道对坛榜文。', '防护内廷紫禁道御前侍卫龙禁尉',
    offscreen=True)

# ===== c13-recommend : 宝玉荐凤姐 ========================
section('c13-recommend', 'c13_funeral', '宁国府 · 停灵大厅', 'hall',
        '只是贾珍虽然此时心意满足')
say('C13-070', 'narrator',
    '只是贾珍虽然此时心意满足，但里面尤氏又犯了旧疾，不能料理事务，'
    '惟恐各诰命来往，亏了礼数，怕人笑话，因此心中不自在。'
    '当下正忧虑时，因宝玉在侧问道：“事事都算安贴了，大哥哥还愁什么？”',
    '大哥哥还愁什么', [show('baoyu', 'hall'), effect('jia_zhen', 'idle')])
say('C13-071', 'jia_zhen',
    '贾珍见问，便将里面无人的话说了出来。宝玉听说笑道：'
    '“这有何难，我荐一个人与你权理这一个月的事，管必妥当。”'
    '贾珍忙问：“是谁？”', '我荐一个人与你',
    [effect('jia_zhen', 'greet')])
say('C13-072', 'narrator',
    '宝玉见座间还有许多亲友，不便明言，走至贾珍耳边说了两句。'
    '贾珍听了喜不自禁，连忙起身笑道：“果然安贴，如今就去。”'
    '说着拉了宝玉，辞了众人，便往上房里来。', '走至贾珍耳边说了两句',
    [move('baoyu', 'hall', 'room'), move('jia_zhen', 'hall', 'room')])

# ===== c13-assist : 凤姐协理 ============================
section('c13-assist', 'c13_funeral', '宁国府 · 上房', 'room',
        '可巧这日非正经日期')
say('C13-080', 'narrator',
    '可巧这日非正经日期，亲友来的少，里面不过几位近亲堂客，'
    '邢夫人、王夫人、凤姐并合族中的内眷陪坐。'
    '闻人报：“大爷进来了。”唬的众婆娘忽的一声，往后藏之不迭，'
    '独凤姐款款站了起来。', '独凤姐款款站了起来',
    [show('xing', 'room'), show('wang', 'room'), show('feng', 'room'),
     hide('baoyu'), hide('jia_zhen')])
say('C13-081', 'narrator',
    '贾珍此时也有些病症在身，二则过于悲痛了，因拄个拐踱了进来。'
    '邢夫人等因说道：“你身上不好，又连日事多，该歇歇才是，又进来做什么？”',
    '因拄个拐踱了进来', [show('jia_zhen', 'room'), effect('jia_zhen', 'rest')])
say('C13-082', 'narrator',
    '贾珍一面扶拐，扎挣著要蹲身跪下请安道乏。'
    '邢夫人等忙叫宝玉搀住，命人挪椅子来与他坐。贾珍断不肯坐，'
    '因勉强陪笑道：“侄儿进来有一件事要求二位婶子并大妹妹。”',
    '侄儿进来有一件事要求', [effect('jia_zhen', 'greet')])
say('C13-083', 'jia_zhen',
    '贾珍忙笑道：“婶子自然知道，如今孙子媳妇没了，侄儿媳妇偏又病倒，'
    '我看里头著实不成个体统。怎么屈尊大妹妹一个月，在这里料理料理，'
    '我就放心了。”', '屈尊大妹妹一个月',
    [effect('jia_zhen', 'greet')])
say('C13-084', 'wang',
    '邢夫人笑道：“原来为这个。你大妹妹现在你二婶子家，只和你二婶子说就是了。”'
    '王夫人忙道：“他一个小孩子家，何曾经过这样事，倘或料理不清，反叫人笑话，'
    '倒是再烦别人好。”', '倒叫人笑话',
    [effect('wang', 'idle')])
say('C13-085', 'jia_zhen',
    '贾珍笑道：“婶子的意思侄儿猜著了，是怕大妹妹劳苦了。'
    '若说料理不开，我包管必料理的开，便是错一点儿，别人看著还是不错的。'
    '从小儿大妹妹顽笑著就有杀伐决断，如今出了阁，又在那府里办事，越发历练老成了。'
    '我想了这几日，除了大妹妹再无人了。'
    '婶子不看侄儿，侄儿媳妇的分上，只看死了的分上罢！”说着滚下泪来。',
    '只看死了的分上罢', [effect('jia_zhen', 'anger')])
say('C13-086', 'feng',
    '王夫人心中怕的是凤姐儿未经过丧事，怕他料理不清，惹人耻笑。'
    '今见贾珍苦苦的说到这步田地，心中已活了几分，却又眼看著凤姐出神。'
    '那凤姐素日最喜揽事办，好卖弄才干，虽然当家妥当，也因未办过婚丧大事，'
    '恐人还不伏，巴不得遇见这事。', '巴不得遇见这事',
    [effect('feng', 'greet')])
say('C13-087', 'feng',
    '凤姐见王夫人不允，后见贾珍说的情真，王夫人有活动之意，'
    '便向王夫人道：“大哥哥说的这么恳切，太太就依了罢。”'
    '王夫人悄悄的道：“你可能么？”凤姐道：“有什么不能的。'
    '外面的大事已经大哥哥料理清了，不过是里头照管照管，'
    '便是我有不知道的，问问太太就是了。”', '你可能么',
    [effect('feng', 'greet')])
say('C13-088', 'jia_zhen',
    '王夫人见说的有理，便不作声。贾珍见凤姐允了，又陪笑道：'
    '“也管不得许多了，横竖要求大妹妹辛苦辛苦。我这里先与妹妹行礼，'
    '等事完了，我再到那府里去谢。”说着就作揖下去，凤姐儿还礼不迭。',
    '我这里先与妹妹行礼', [effect('jia_zhen', 'greet'), effect('feng', 'idle')])
say('C13-089', 'narrator',
    '贾珍便忙向袖中取了宁国府对牌出来，命宝玉送与凤姐，'
    '又说：“妹妹爱怎样就怎样，要什么只管拿这个取去，也不必问我。'
    '只求别存心替我省钱，只要好看为上，二则也要同那府里一样待人才好，'
    '不要存心怕人抱怨。只这两件外，我再没不放心的了。”',
    '要什么只管拿这个取去', [show('baoyu', 'room'), effect('jia_zhen', 'idle')])
say('C13-090', 'narrator',
    '凤姐不敢就接牌，只看著王夫人。王夫人道：“你哥哥既这么说，'
    '你就照看照看罢了。只是别自作主意，有了事，打发人问你哥哥，嫂子要紧。”'
    '宝玉早向贾珍手里接过对牌来，强递与凤姐了。', '打发人问你哥哥',
    [effect('wang', 'idle'), effect('feng', 'greet')])
say('C13-091', 'jia_zhen',
    '又问：“妹妹住在这里，还是天天来呢？若是天天来，越发辛苦了。'
    '不如我这里赶著收拾出一个院落来，妹妹住过这几日倒安稳。”'
    '凤姐笑道：“不用。那边也离不得我，倒是天天来的好。”'
    '贾珍听说，只得罢了。然后又说了一回闲话，方才出去。',
    '不如我这里赶著收拾出一个院落来', [move('jia_zhen', 'room', 'gate'), hide('jia_zhen')])

# ===== c13-five : 五件弊病 ==============================
# 原文位置：凤姐独坐抱厦，想出宁国府五件弊病：人口混杂遗失东西、事无专执临期推委、
# 需用过费滥支冒领、任无大小苦乐不均、家人豪纵有脸者不服钤束。
section('c13-five', 'c13_baosha', '宁国府 · 三间抱厦', 'seat',
        '一时女眷散后，王夫人因问凤姐')
say('C13-100', 'narrator',
    '一时女眷散后，王夫人因问凤姐：“你今儿怎么样？”'
    '凤姐儿道：“太太只管请回去，我须得先理出一个头绪来，才回去得呢。”'
    '王夫人听说，便先同邢夫人等回去，不在话下。', '须得先理出一个头绪来',
    [hide('wang'), hide('xing')])
say('C13-101', 'narrator',
    '这里凤姐儿来至三间一所抱厦内坐了，因想：头一件是人口混杂，遗失东西；'
    '第二件，事无专执，临期推委；第三件，需用过费，滥支冒领；'
    '第四件，任无大小，苦乐不均；第五件，家人豪纵，有脸者不服钤束，'
    '无脸者不能上进。', '头一件是人口混杂，遗失东西',
    [show('feng', 'door'), move('feng', 'door', 'seat'), effect('feng', 'idle')])
say('C13-102', 'narrator',
    '此五件实是宁国府中风俗，不知凤姐如何处治，且听下回分解。'
    '正是：金紫万千谁治国，裙钗一二可齐家。', '裙钗一二可齐家',
    [effect('feng', 'greet')])


def verify_sources():
    import re
    base = re.sub(r'\s+', '', Path('docs/chapter13-source.txt').read_text())
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
        raise SystemExit('source leads do not match docs/chapter13-source.txt')
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_DIR / 'chapter13-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 13}
                for sid, title, scene in SECTIONS]
    (STAGE_DIR / 'chapter13-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter13-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter13-sections.json  %d sections' % n_sections)
