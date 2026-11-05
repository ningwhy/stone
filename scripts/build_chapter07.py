#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-seven maps, its playable script and its section table.

Chapter seven owns this generator; nothing here touches build_chapter06.py or
write_prequel.py, so re-running it cannot overwrite an earlier chapter.

第七回 · 送宫花贾琏戏熙凤 · 宴宁府宝玉会秦钟

Outputs (printed at the end):
  maps/c7_lixiang.tmj       new stage: 梨香院 · 薛姨妈处 / 宝钗
  maps/c7_sanchun.tmj       new stage: 三春院 · 迎春探春惜春
  design/chapter07-story.json      nodes C07-001..
  design/chapter07-sections.json   sections: c7-xue .. c7-jiao
  (复用 maps: night 贾母院；c6_wangchui 凤姐院；c5_ningfu 宁国府)

贾琏 / 秦钟 / 焦大 / 贾珍 / 尤氏 等本回人物待 ComfyUI 人脸管线生成立绘，
本轮以旁白或现存人物代出，桩段见 docs/chapter07-production.md。

Usage: python3 scripts/build_chapter07.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402  (a roof lifts off the floor it covers)
BACKUP = ROOT / 'artifacts/backups/2026-10-30-chapter07'


def at(c, r, dx=0.0, dy=0.0):
    """把屏幕像素偏移换成等距格坐标（同 stage_defs.at）。"""
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


# ---------------------------------------------------------------------------
# Maps
#
# 第七回送宫花主线需要两处新建舞台：梨香院（薛姨妈 / 宝钗）与三春院（迎春探春
# 惜春）。其余段落复用既有舞台：凤姐院 c6_wangchui、贾母院 night、宁国府 c5_ningfu。
# 两处新舞台均以既有的 estate-* 院落壳 + 室内陈设拼出，不依赖新美术生成。
# ---------------------------------------------------------------------------

scenes = {
    # 梨香院 · 薛姨妈携宝钗居所（第四回薛家入住）。南向院门、甬路、正房（estate-lixiang 壳），
    # 室内炕、茶案、花瓶架；院中一株老树、一道花篱门。
    'c7_lixiang': {
        'name': '梨香院 · 薛姨妈处',
        'theme': 'garden',
        'zones': [[12, 15, 18, 18], [18, 16, 10, 9, True, 'ROOM']],
        'anchors': {
            'entry': [22, 32],
            'yard': [22, 26],
            'room': [22, 21],
            'xueyima': [18, 20],
            'wang': [21, 20],
            'baochai': [25, 20],
            'zhou': [15, 24],
        },
        'routes': {
            'main': ['entry', 'yard', 'room'],
            'back': ['room', 'yard', 'entry'],
        },
        'labels': [['梨香院', 22, 30], ['正房', 22, 19], ['院门', 22, 33]],
        'props': [
            ('estate-lixiang', *at(22, 16), .66),
            ('wang-kang', *at(19, 19, -14, 12), .55, 'ROOM'),
            ('tea-table', *at(24, 19, 0, 0), .5, 'ROOM'),
            ('vase-stand', *at(27, 18, 10, 0), .5, 'ROOM'),
            ('garden-tree', *at(29, 25), .82),
            ('flower-gate', *at(22, 33), .55),
        ],
        'walls': [[12, 15, 30, 15], [12, 15, 12, 32], [30, 15, 30, 32],
                  [12, 32, 20, 32], [24, 32, 30, 32]],
        'terraces': [[18, 28, 8, 6, 'path']],
        'beds': [[16, 24, 3, 2], [27, 24, 3, 2]],
    },
    # 三春院 · 迎春探春惜春所居。正房（estate-east 壳）、榻、茶案、坐椅、院树、花篱门。
    'c7_sanchun': {
        'name': '三春院 · 迎春探春惜春',
        'theme': 'garden',
        'zones': [[12, 15, 18, 18], [18, 16, 10, 9, True, 'ROOM']],
        'anchors': {
            'entry': [22, 32],
            'yard': [22, 26],
            'room': [22, 21],
            'yingchun': [18, 20],
            'tanchun': [21, 20],
            'xichun': [25, 20],
            'zhou': [15, 24],
        },
        'routes': {
            'main': ['entry', 'yard', 'room'],
            'back': ['room', 'yard', 'entry'],
        },
        'labels': [['三春院', 22, 30], ['正房', 22, 19], ['院门', 22, 33]],
        'props': [
            ('estate-east', *at(22, 16), .66),
            ('daybed', *at(19, 19, -14, 12), .5, 'ROOM'),
            ('tea-table', *at(24, 19, 0, 0), .5, 'ROOM'),
            ('square-stool', *at(24, 19, -70, 20), .6, 'ROOM'),
            ('square-stool', *at(24, 19, 70, 20), .6, 'ROOM'),
            ('garden-tree', *at(29, 25), .82),
            ('flower-gate', *at(22, 33), .55),
        ],
        'walls': [[12, 15, 30, 15], [12, 15, 12, 32], [30, 15, 30, 32],
                  [12, 32, 20, 32], [24, 32, 30, 32]],
        'terraces': [[18, 28, 8, 6, 'path']],
        'beds': [[16, 24, 3, 2], [27, 24, 3, 2]],
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
                         if scene.get('beds') == [] else []),
    }
    (ROOT / f'maps/{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')
    return len(scene['anchors'])


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

SECTIONS = [
    ('c7-xue', '梨香院 · 薛姨妈托花', 'c7_lixiang'),
    ('c7-san', '三春院 · 周瑞家的送花', 'c7_sanchun'),
    ('c7-feng', '凤姐院 · 平儿收花', 'c6_wangchui'),
    ('c7-dai', '贾母院 · 黛玉冷笑', 'night'),
    ('c7-ning', '宁国府 · 宝玉会秦钟', 'c5_ningfu'),
    ('c7-jiao', '宁国府 · 焦大醉骂', 'c5_ningfu'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 7, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c7-xue : 梨香院 · 薛姨妈托花 ============================
section('c7-xue', 'c7_lixiang', '梨香院 · 薛姨妈处', 'entry',
        '话说周瑞家的送了刘姥姥去后，便上来回王夫人话')
say('C07-001', 'narrator',
    '周瑞家的送罢刘姥姥，来回王夫人话，却知王夫人往梨香院薛姨妈处说话去了，便过东院前来。',
    '往梨香院', [show('zhou_rui', 'entry')])
say('C07-002', 'narrator',
    '刚至院前，听见房里一阵笑声，却是贾琏的声音；平儿拿了大铜盆出来，叫丰儿舀水进去。',
    '院前听得', [move('zhou_rui', 'entry', 'yard')])
say('C07-003', 'xueyima',
    '薛姨妈见周瑞家的，拿出十二支宫里的新鲜纱堆花儿，道：“这是宫里头的新鲜样法，白放着可惜了儿的，何不给他们姊妹们戴去。”',
    '托花', [show('xueyima', 'xueyima'), show('wang', 'wang'), show('baochai', 'baochai')])
say('C07-004', 'wang',
    '王夫人道：“留着给宝丫头戴罢，又想着他们作什么。”', '王夫人说')
say('C07-005', 'xueyima',
    '薛姨妈道：“姨娘不知道，宝丫头古怪着呢，他从来不爱这些花儿粉儿的。”', '宝钗不戴花')
say('C07-006', 'xueyima',
    '薛姨妈便分派：“你家的三位姑娘，每人一对；剩下六枝，送林姑娘两枝，那四枝给了凤哥罢。”',
    '分派')
say('C07-007', 'zhou_rui',
    '周瑞家的答应了，拿了匣子出来，问金钏儿那香菱是谁；正说时，香菱笑嘻嘻走来。（香菱待立绘，本轮以旁白带过）',
    '问香菱', [move('zhou_rui', 'yard', 'zhou')])

# ===== c7-san : 三春院 · 周瑞家的送花 ============================
section('c7-san', 'c7_sanchun', '三春院 · 迎春探春惜春', 'yingchun',
        '周瑞家的因问智能儿：“你是什么时候来的？你师父那秃歪剌往那里去了？”')
say('C07-010', 'narrator',
    '周瑞家的往三春院来，迎春、探春正在窗下围棋，便将花送上。',
    '送迎春探春', [show('zhou_rui', 'zhou'), show('yingchun', 'yingchun'), show('tanchun', 'tanchun')])
say('C07-011', 'yingchun',
    '迎春、探春忙住了棋，都欠身道谢。', '道谢')
say('C07-012', 'tanchun',
    '探春笑问：“这花却好，只是我屋里没有这么个体面东西插他。”', '探春笑问')
say('C07-013', 'narrator',
    '又说一回闲话，往惜春处来；惜春正同水月庵智能儿一处顽笑。',
    '往惜春处', [show('xichun', 'xichun'), hide('yingchun'), hide('tanchun')])
say('C07-014', 'xichun',
    '惜春笑道：“我这里正和智能儿说，我明儿也剃了头同他作姑子去呢，可巧又送了花儿来；若剃了头，可把这花儿戴在那里呢。”',
    '惜春玩笑')
say('C07-015', 'zhou_rui',
    '周瑞家的笑说：“你这小嘴，越发刁了。”便将花递与惜春。', '递花',
    [hide('xichun'), move('zhou_rui', 'zhou', 'room')])

# ===== c7-feng : 凤姐院 · 平儿收花 ============================
section('c7-feng', 'c6_wangchui', '凤姐院 · 堂屋', 'feng_room',
        '送至贾母处，凤姐正与王夫人说闲话')
say('C07-020', 'narrator',
    '周瑞家的来至凤姐院，凤姐正与平儿说闲话。（贾琏在房中戏耍，本轮以旁白带过，不置角色于场上）',
    '来至凤姐院', [show('zhou_rui', 'platform'), show('feng', 'feng_room')])
say('C07-021', 'feng',
    '凤姐听完周瑞家的来意，便命平儿将花儿收了。', '凤姐命收')
say('C07-022', 'ping_er',
    '平儿答应，接了匣子，拣出两枝，替凤姐收下。', '平儿收花',
    [show('ping_er', 'feng_room')])
say('C07-023', 'narrator',
    '周瑞家的又往黛玉处来，打听着凤姐与贾琏戏耍，在窗外站了一回。',
    '往黛玉处', [hide('zhou_rui'), hide('feng'), hide('ping_er')])

# ===== c7-dai : 贾母院 · 黛玉冷笑 ============================
section('c7-dai', 'night', '贾母院 · 黛玉房中', 'daiyu_bed',
        '周瑞家的又往黛玉处来')
say('C07-030', 'narrator',
    '周瑞家的往贾母处来，黛玉正在宝玉房中顽耍。',
    '往贾母处', [show('zhou_rui', 'daiyu_bed'), show('daiyu', 'daiyu_bed'), show('baoyu', 'baoyu_bed')])
say('C07-031', 'zhou_rui',
    '周瑞家的道：“林姑娘，姨太太着我送花儿与姑娘戴。”', '送花与黛玉')
say('C07-032', 'baoyu',
    '宝玉听说，便先问：“什么花儿？拿来给我。”接了花，送与黛玉。', '宝玉先问',
    [move('baoyu', 'baoyu_bed', 'daiyu_bed')])
say('C07-033', 'daiyu',
    '黛玉只就宝玉手中看了一看，便问：“还是单送我一个人的，还是别的姑娘们都有了？”', '黛玉问')
say('C07-034', 'zhou_rui',
    '周瑞家的道：“各位都有了，这两枝是姑娘的。”', '周瑞家的答')
say('C07-035', 'daiyu',
    '黛玉冷笑道：“我就知道，别人不挑剩下的也不给我。”', '黛玉冷笑')
say('C07-036', 'narrator',
    '周瑞家的出去了。宝玉见黛玉如此，只默默的；袭人、雪雁在旁，也不好言语。',
    '出去', [hide('zhou_rui'), hide('daiyu'), hide('baoyu')])

# ===== c7-ning : 宁国府 · 宝玉会秦钟（桩段，秦钟待立绘）============
section('c7-ning', 'c5_ningfu', '宁国府 · 会芳园', 'garden_center',
        '且说宁国府中，这日贾珍之妻尤氏请贾母、邢夫人、王夫人等赏花吃酒')
say('C07-040', 'narrator',
    '宁国府中，尤氏请贾母、邢王二夫人赏花吃酒；宝玉随了凤姐来至宁府。（秦钟、贾珍、尤氏待立绘，本轮以旁白带过）',
    '宁府赴宴', [show('baoyu', 'garden_center'), show('feng', 'garden_center')])
say('C07-041', 'jia_rong',
    '秦氏引了尤氏、贾蓉之妻来拜见。贾蓉陪笑，引宝玉往园中顽耍。',
    '秦氏引见', [show('jia_rong', 'garden_entry')])
say('C07-042', 'baoyu',
    '宝玉见秦氏之弟秦钟，生得眉清目秀、粉面朱唇，便有些留恋之意；秦钟亦自思慕，二人你言我语，十分相投。',
    '宝玉会秦钟')
say('C07-043', 'narrator',
    '二人约定同入贾家家塾读书，自此情同手足。', '约定同窗',
    [hide('baoyu'), hide('feng'), hide('jia_rong')])

# ===== c7-jiao : 宁国府 · 焦大醉骂（桩段，焦大待立绘）============
section('c7-jiao', 'c5_ningfu', '宁国府 · 门前', 'garden_center',
        '却说宁国府中老仆焦大，从小儿跟着太爷出过三四回兵')
say('C07-050', 'narrator',
    '宁府老仆焦大，从小儿随太爷出兵，从死人堆里把太爷背了出来。（焦大待立绘，本轮以旁白叙述）这日因喝了酒，越发无礼起来。',
    '焦大醉酒')
say('C07-051', 'narrator',
    '焦大当着众小厮的面，趁着酒兴骂道：“爬灰的爬灰，养小叔子的养小叔子，我什么不知道？咱们胳膊折了往袖子里藏！”',
    '焦大醉骂')
say('C07-052', 'narrator',
    '众小厮听他说出这些没天日的话，唬得魂飞魄散，忙将他捆起来，用土和马粪满满填了他一嘴。',
    '捆起塞粪')


def build_story():
    ids = [s['id'] for s in steps]
    assert len(ids) == len(set(ids)), 'duplicate node id'
    for s in steps:
        assert s['chapter'] in section_titles, f"{s['id']}: unknown section"
    (ROOT / 'design/chapter07-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 7}
                for sid, title, scene in SECTIONS]
    (ROOT / 'design/chapter07-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter07-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter07-sections.json  %d sections' % n_sections)
