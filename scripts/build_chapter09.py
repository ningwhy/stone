#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-nine maps, its playable script and its section table.

第九回 · 恋风流情友入家塾 · 起嫌疑顽童闹学堂

Chapter nine owns this generator; nothing here touches build_chapter08.py,
so re-running it cannot overwrite an earlier chapter.

Outputs (printed at the end):
  maps/c9_school.tmj            new stage: 贾家家塾
  design/chapter09-story.json      nodes C09-001..
  design/chapter09-sections.json   sections: c9-enter .. c9-quit
  (复用 maps: capital 宁荣街等)

本回新建舞台：贾家家塾（塾室、书案、塾师席、门），用既有室内资产拼出，
不依赖新美术生成。

人物：秦钟、贾瑞、金荣、茗烟、李贵为本回新立绘（已在 art/matted 与 public/assets/rongguo
生成并校准）；薛蟠、宝玉复用既有资产。

Usage: python3 scripts/build_chapter09.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

BACKUP = ROOT / 'artifacts/backups/2026-10-30-chapter09'
# 第九回已接入 story：地图与剧情直接进入 maps/ 与 design/。
# maps/ 下的每一张地图都会被册页逐张列出，运行器也按目录自动发现；剧情节点
# 已覆盖该地图，读者可正常进入。
PUBLISH_MAP = True
MAP_DIR = ROOT / 'maps' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter09'
# design/ 下的 chapter*-story.json 与 story.ts 显式 import 配对后方可登记。
STAGE_DIR = ROOT / 'design' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter09'


def at(c, r, dx=0.0, dy=0.0):
    """把屏幕像素偏移换成等距格坐标（同 stage_defs.at）。"""
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


# ---------------------------------------------------------------------------
# Maps
#
# 第九回新建「贾家家塾」一处舞台：塾室（qin-room 屋顶壳）、塾师席、讲席、
# 若干书案与官椅、外院门与甬路。用既有资产拼出，不新增美术。
# ---------------------------------------------------------------------------

scenes = {
    'c9_school': {
        'name': '贾家家塾',
        # 家塾是室内塾室，用 interior 主题（已有 bgm-interior）。新增一个 study 主题
        # 会让 check:content 的音频门禁报「map themes with no piece」。
        'theme': 'interior',
        'zones': [[10, 16, 20, 18], [14, 17, 12, 9, True, 'HALL']],
        'anchors': {
            'gate': [20, 31],
            'yard': [20, 28],
            'hall': [20, 24],
            'teacher': [15, 21],
            'desk_a': [18, 20],
            'desk_b': [22, 20],
            'desk_c': [24, 22],
            'door': [20, 17],
        },
        'routes': {
            'main': ['gate', 'yard', 'hall'],
            'inner': ['yard', 'hall', 'door'],
        },
        'labels': [['家塾', 20, 30], ['塾室', 20, 22], ['塾师席', 15, 19]],
        'props': [
            ('qin-room', *at(20, 18), .60, 'HALL'),
            ('writing-desk', *at(18, 20, 0, 0), .62, 'HALL'),
            ('writing-desk', *at(22, 20, 0, 0), .62, 'HALL'),
            ('writing-desk', *at(24, 22, 0, 0), .58, 'HALL'),
            ('official-chair', *at(15, 21, 0, 0), .58, 'HALL'),
            ('official-desk', *at(15, 19, 0, 0), .60, 'HALL'),
            ('bookshelf', *at(17, 17, 0, 0), .52, 'HALL'),
            ('flower-gate', *at(20, 31), .52),
            ('garden-tree', *at(27, 27), .72),
        ],
        'walls': [[10, 16, 30, 16], [10, 16, 10, 33], [30, 16, 30, 33],
                  [10, 33, 18, 33], [22, 33, 30, 33]],
        'terraces': [[18, 28, 5, 6, 'path']],
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
                         if scene.get('beds') == [] else []),
    }
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    (MAP_DIR / f'{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')
    return len(scene['anchors'])


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

SECTIONS = [
    ('c9-enter', '家塾 · 秦钟入塾', 'c9_school'),
    ('c9-roll', '家塾 · 薛蟠与香怜玉爱', 'c9_school'),
    ('c9-plot', '家塾 · 贾瑞图私利', 'c9_school'),
    ('c9-clash', '家塾 · 金荣起衅', 'c9_school'),
    ('c9-quit', '家塾 · 顽童闹学堂', 'c9_school'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 9, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c9-enter : 秦钟入塾 ============================
section('c9-enter', 'c9_school', '贾家家塾', 'gate',
        '却原来宝玉和秦钟两个你来我往的越发亲密')
say('C09-001', 'narrator',
    '宝玉与秦钟越发亲密，秦钟意欲附学读书；宝玉大喜，引他去拜见塾师贾代儒。',
    '秦钟欲附学', [show('baoyu', 'yard'), show('qin_zhong', 'gate')])
say('C09-002', 'narrator',
    '贾代儒见秦钟眉清目秀、举止斯文，便应允了；秦钟收拾书囊，与宝玉同窗而处。',
    '代儒允入塾', [show('jia_dairu', 'teacher'),
                    move('qin_zhong', 'yard', 'hall', 'teacher')])
say('C09-003', 'qin_zhong',
    '秦钟拱手道：“钟儿久慕家塾藏书，今日得附骥尾，幸甚。”宝玉拉他同坐。',
    '秦钟谢座', [effect('qin_zhong', 'idle'),
                  parallel(move('qin_zhong', 'desk_a'), move('baoyu', 'desk_a'))])

# ===== c9-roll : 薛蟠与香怜玉爱 ============================
section('c9-roll', 'c9_school', '贾家家塾', 'hall',
        '那薛蟠又看上两个小厮')
say('C09-010', 'narrator',
    '薛蟠本是浮萍心性，又看上学堂里两个小厮香怜、玉爱，便时时招惹。',
    '薛蟠招惹二童', [show('xuepan', 'hall')])
say('C09-011', 'narrator',
    '香怜、玉爱原是些没正经的，见了薛蟠的银钱，便与他眉来眼去；宝玉在旁，早看不过。',
    '二童逢迎')
say('C09-012', 'baoyu',
    '宝玉皱眉道：“越发不成体统了。”便拉了秦钟避到一隅，不与他们厮混。',
    '宝玉不屑', [parallel(move('baoyu', 'desk_c'), move('qin_zhong', 'desk_c'))])

# ===== c9-plot : 贾瑞图私利 ============================
section('c9-plot', 'c9_school', '贾家家塾', 'teacher',
        '那贾瑞管着学堂，图薛蟠的谢礼')
say('C09-020', 'narrator',
    '贾瑞讨了代儒的权，管起学堂来；他原是个图便宜没刚性的，见薛蟠撒漫使钱，便一心回护。',
    '贾瑞管学堂', [show('jia_rui', 'teacher')])
say('C09-021', 'jia_rui',
    '贾瑞板着脸假意申斥几句，转脸却向薛蟠使个眼色，悄悄受了他的东道。',
    '假公济私', [effect('jia_rui', 'idle')])
say('C09-022', 'narrator',
    '金荣在旁看得分明，素与薛蟠不睦，心中早存了几分不忿。', '金荣生怨',
    [move('jia_rui', 'teacher', 'hall'), show('jin_rong', 'desk_b')])

# ===== c9-clash : 金荣起衅 ============================
section('c9-clash', 'c9_school', '贾家家塾', 'hall',
        '金荣是和薛蟠有些旧怨的')
say('C09-030', 'narrator',
    '金荣借着昨日的由头，又见秦钟、宝玉亲厚，便当着众人出言讥讽，语带污蔑。',
    '金荣起衅', [move('jin_rong', 'desk_b', 'hall'), show('qin_zhong', 'desk_a')])
say('C09-031', 'jin_rong',
    '金荣冷笑道：“姓秦的，不过是个……也配在我们跟前充什么斯文！”满堂哗然。',
    '当面羞辱', [effect('jin_rong', 'anger')])
say('C09-032', 'baoyu',
    '宝玉拍案怒道：“休得胡言乱语，伤犯我友！”秦钟涨红了脸，低头不语。',
    '宝玉护友', [move('baoyu', 'desk_c', 'hall'), effect('baoyu', 'anger')])
say('C09-033', 'narrator',
    '金荣撒起泼来，拍桌蹬凳，学堂里登时乱作一团；贾瑞假意弹压，却并不认真。',
    '学堂大乱')

# ===== c9-quit : 顽童闹学堂 ============================
section('c9-quit', 'c9_school', '贾家家塾', 'yard',
        '茗烟便大闹学堂')
say('C09-040', 'narrator',
    '茗烟在门外听得主子受辱，哪里忍得，闯进学堂便骂。', '茗烟闯入',
    [show('ming_yan', 'gate')])
say('C09-041', 'ming_yan',
    '茗烟叫道：“姓金的算什么东西，也敢欺负我们二爷！”扑上去与金荣扭作一团。',
    '茗烟揪打', [parallel(move('ming_yan', 'gate', 'yard'), move('jin_rong', 'hall', 'yard'))])
say('C09-042', 'li_gui',
    '李贵赶来，一把扯开二人，喝道：“作死的小崽子！这是读书的地方，也由得你们撒野？”',
    '李贵喝住', [show('li_gui', 'door')])
say('C09-043', 'narrator',
    '李贵连推带拽分开众人，贾瑞也来装腔作势弹压；众顽童方才悻悻散了学。',
    '散学', [move('li_gui', 'door', 'yard'), effect('li_gui', 'idle')])


def build_story():
    ids = [s['id'] for s in steps]
    assert len(ids) == len(set(ids)), 'duplicate node id'
    for s in steps:
        assert s['chapter'] in section_titles, f"{s['id']}: unknown section"
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_DIR / 'chapter09-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 9}
                for sid, title, scene in SECTIONS]
    (STAGE_DIR / 'chapter09-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter09-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter09-sections.json  %d sections' % n_sections)
