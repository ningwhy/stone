#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-twelve's stages, script and section table.

第十二回 · 王熙凤毒设相思局 · 贾天祥正照风月鉴

Chapter twelve owns this generator; nothing here touches an earlier chapter.

Outputs:
  maps/c12_passage.tmj          新舞台：荣府 · 西边穿堂与房后空屋
  maps/c12_sickbed.tmj          新舞台：贾瑞书房 · 风月宝鉴
  design/chapter12-story.json   节点 C12-001..
  design/chapter12-sections.json

本回复用：maps/c6_wangchui.tmj（凤姐院）、maps/night.tmj（贾母院）。

两张新地图的说明：
  c12_passage 把「西边穿堂」与「房后空屋」画在同一张图的两个室内区域里——
  原文里两处都在凤姐院这一角，凤姐先约穿堂、再约空屋，读者能看出是同一处
  地方换了个屋子，两处相邻也便于走位。
  c12_sickbed 是贾瑞病榻，风月宝鉴用既有 qin-mirror 资产摆在榻边。

人物：贾蔷、贾代儒为本回新立绘；凤姐、平儿、贾瑞、贾蓉、跛足道人、贾母、
黛玉、王夫人复用既有资产。贾琏在原著中只列名（送黛玉回扬州），不造人出场。

Usage: python3 scripts/build_chapter12.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

BACKUP = ROOT / 'artifacts/backups/2026-10-31-chapter12'
PUBLISH_MAP = True
MAP_DIR = ROOT / 'maps' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter12'
STAGE_DIR = ROOT / 'design' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter12'


def at(c, r, dx=0.0, dy=0.0):
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {
    'c12_passage': {
        'name': '荣府 · 西边穿堂与房后空屋',
        'theme': 'interior',
        # 小院（A0，行 20-29）在下，穿堂（PASSAGE，行 10-19）与空屋（EMPTY，行 10-19）
        # 并排在上：两间屋子各自贴着小院，中间隔着院子，走位靠院子串起来。
        # 穿堂落在列 14-20 而不是 12-18：屋壳只在人还在屋外时画，它的脚被 eave()
        # 钉在这块地的南沿（行 19.5）。等距投影里往西挪一列，屏幕上是**同时**往左和往上走，
        # 原先摆在列 15 时，屋脚比站在小院 (17,25) 的人高出 240 px，屋脊比取景上沿还高
        # 25 px——整座穿堂一次也没进过画面。把屋子挪到与院中站位同列，屋脚只高 176 px，
        # 从院里抬头就看得见檐口，这一段本来就是「摸黑钻进穿堂」。
        'zones': [[12, 20, 16, 10], [14, 10, 7, 10, True, 'PASSAGE'],
                  [21, 10, 7, 10, True, 'EMPTY']],
        'anchors': {
            'gate': [22, 28],
            'yard': [17, 25],
            'passage_door': [17, 19],
            'passage': [17, 14],
            'empty_door': [24, 19],
            'empty': [24, 14],
            'corner': [26, 12],
        },
        'routes': {
            'to_passage': ['gate', 'yard', 'passage_door', 'passage'],
            'to_empty': ['gate', 'yard', 'empty_door', 'empty'],
            'to_corner': ['empty', 'corner'],
        },
        'labels': [['西边穿堂', 17, 12], ['房后空屋', 24, 12], ['小院', 17, 26]],
        'props': [
            # 列号跟着上面的 zone 走，行号无所谓——eave() 会把屋壳重新钉到地块南沿。
            ('lixiang-hall', *at(17, 14), .74, 'PASSAGE'),
            ('lamp-stand', *at(18, 17, 0, 0), .62, 'PASSAGE'),
            # 房后空屋：原文说「这屋你还藏不得，少时就来堆东西」，屋里只一架旧屏风。
            ('qin-room', *at(24, 14), .74, 'EMPTY'),
            ('wood-screen', *at(22, 12, 0, 0), .62, 'EMPTY'),
            ('flower-gate', *at(22, 28), .50),
            ('garden-tree', *at(13, 25), 1.00),
            ('garden-tree', *at(27, 25), .94),
            ('courtyard-wall', *at(19, 22), .60),
        ],
        'walls': [[12, 20, 28, 20], [12, 20, 12, 30], [28, 20, 28, 30],
                  [12, 30, 20, 30], [24, 30, 28, 30]],
        'terraces': [[20, 24, 4, 6, 'path']],
    },
    'c12_sickbed': {
        'name': '贾瑞书房 · 风月宝鉴',
        'theme': 'interior',
        'zones': [[14, 10, 12, 10, True, 'ROOM']],
        'anchors': {
            'door': [15, 19],
            'bed': [19, 14],
            'bedside': [21, 15],
            'mirror': [22, 12],
            'window': [16, 12],
        },
        'routes': {
            'main': ['door', 'bed', 'bedside'],
            'to_mirror': ['bedside', 'mirror'],
        },
        'labels': [['贾瑞书房', 19, 11], ['病榻', 19, 15], ['风月宝鉴', 22, 13]],
        'props': [
            ('main-hall', *at(19, 14), .82, 'ROOM'),
            ('canopy-bed', *at(19, 14, 0, 0), .64, 'ROOM'),
            # 风月宝鉴：原文「从褡裢中取出一面镜子来，两面皆可照人，
            # 镜把上面錾着`风月宝鉴'四字」。用既有 qin-mirror 摆在榻边。
            ('qin-mirror', *at(22, 12, 0, 0), .46, 'ROOM'),
            ('lamp-stand', *at(17, 17, 0, 0), .66, 'ROOM'),
            ('tea-table', *at(21, 17, 0, 0), .56, 'ROOM'),
            ('wood-screen', *at(16, 14, 0, 0), .64, 'ROOM'),
        ],
        'terraces': [[18, 15, 3, 4, 'path']],
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
    ('c12-visit', '凤姐院 · 瑞大爷来了', 'c6_wangchui'),
    ('c12-tryst', '穿堂 · 冻了一夜', 'c12_passage'),
    ('c12-second', '凤姐院 · 再约空屋', 'c6_wangchui'),
    ('c12-trap', '空屋 · 贾蔷贾蓉捉奸', 'c12_passage'),
    ('c12-extort', '空屋 · 五十两欠契', 'c12_passage'),
    ('c12-illness', '贾瑞书房 · 病榻', 'c12_sickbed'),
    ('c12-ginseng', '荣府 · 寻人参', 'wang'),
    ('c12-taoist', '贾瑞书房 · 跛足道人', 'c12_sickbed'),
    ('c12-mirror', '风月宝鉴 · 正照而亡', 'c12_sickbed'),
    ('c12-depart', '贾母院 · 黛玉回扬州', 'night'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 12, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c12-visit : 瑞大爷来了 ============================
section('c12-visit', 'c6_wangchui', '凤姐院 · 房内', 'feng_room',
        '话说凤姐正与平儿说话')
say('C12-001', 'narrator',
    '凤姐正与平儿说话，只见有人回说：“瑞大爷来了。”凤姐急命快请进来。'
    '贾瑞见往里让，心中喜出望外，急忙进来，见了凤姐，满面陪笑，连连问好。',
    '瑞大爷来了', [show('feng', 'feng_room'), show('ping_er', 'feng_room'),
                 show('jia_rui', 'back_gate'),
                 move('jia_rui', 'market', 'zhou_court', 'zhou_room', 'daoting',
                      'yingbi', 'platform', 'feng_room')])
say('C12-002', 'feng',
    '凤姐儿也假意殷勤，让茶让坐。（她心里早已定了主意，只是脸上不露。）',
    '假意殷勤', [effect('feng', 'idle')])
say('C12-003', 'jia_rui',
    '贾瑞饧了眼问道：“二哥哥怎么还不回来？”凤姐道：“不知什么原故。”'
    '贾瑞笑道：“别是路上有人绊住了脚了，舍不得回来也未可知？”',
    '二哥哥还不回来', [effect('jia_rui', 'greet')])
say('C12-004', 'jia_rui',
    '贾瑞听了喜的抓耳挠腮，又道：“嫂子天天也闷的很。”凤姐道：“正是呢，'
    '只盼个人来说话解解闷儿。”贾瑞笑道：“我倒天天闲着，天天过来替嫂子解解闲闷可好不好？”',
    '替嫂子解闷', [effect('jia_rui', 'idle')])
say('C12-005', 'feng',
    '凤姐笑道：“你哄我呢，你那里肯往我这里来。”贾瑞道：“我在嫂子跟前，'
    '若有一点谎话，天打雷劈！-死了也愿意！”', '死了也愿意',
    [effect('feng', 'idle')])
say('C12-006', 'feng',
    '凤姐笑道：“果然你是个明白人，比贾蓉两个强远了。我看他那样清秀，'
    '只当他们心里明白，谁知竟是两个胡涂虫，一点不知人心。”',
    '比贾蓉两个强远了', [effect('feng', 'greet')])
say('C12-007', 'feng',
    '凤姐又悄悄的道：“大天白日，人来人往，你就在这里也不方便。你且去，'
    '等着晚上起了更你来，悄悄的在西边穿堂儿等我。”', '约在西边穿堂',
    [effect('feng', 'idle')])
say('C12-008', 'jia_rui',
    '贾瑞听了，如得珍宝，忙问道：“你别哄我。但只那里人过的多，怎么好躲的？”'
    '凤姐道：“我把上夜的小厮们都放了假，两边门一关，再没别人了。”'
    '贾瑞喜之不尽，忙忙的告辞而去，心内以为得手。', '如得珍宝',
    [effect('jia_rui', 'greet'), move('jia_rui', 'platform', 'back_gate')])

# ===== c12-tryst : 穿堂冻一夜 ============================
section('c12-tryst', 'c12_passage', '荣府 · 西边穿堂', 'passage',
        '盼到晚上，果然黑地里摸入荣府')
say('C12-010', 'narrator',
    '盼到晚上，贾瑞果然黑地里摸入荣府，趁掩门时，钻入穿堂。果见漆黑无一人，'
    '往贾母那边去的门户已倒锁，只有向东的门未关。', '摸入穿堂',
    [show('jia_rui', 'gate'), move('jia_rui', 'yard', 'passage_door')])
say('C12-011', 'narrator',
    '贾瑞侧耳听着，半日不见人来。忽听咯噔一声，东边的门也倒关了。'
    '贾瑞急的也不敢则声，只得悄悄的出来，将门撼了撼，关的铁桶一般。',
    '东边门也倒关了', [move('jia_rui', 'passage'), effect('jia_rui', 'anger')])
say('C12-012', 'narrator',
    '此时要求出去亦不能够，南北皆是大房墙，要跳亦无攀援。这屋内又是过门风，'
    '空落落，现是腊月天气，夜又长，朔风凛凛，侵肌裂骨，一夜几乎不曾冻死。',
    '朔风凛凛侵肌裂骨', [effect('jia_rui', 'rest')])
say('C12-013', 'narrator',
    '好容易盼到早晨，只见一个老婆子先将东门开了，进去叫西门。'
    '贾瑞瞅他背着脸，一溜烟抱着肩跑了出来，幸而天气尚早，人都未起，'
    '从后门一径跑回家去。', '一溜烟跑回家', [move('jia_rui', 'passage_door', 'gate')])
say('C12-014', 'jia_dairu',
    '原来贾瑞父母早亡，只有他祖父代儒教养。代儒素日教训最严，今忽见他一夜不归，'
    '只料定他在外非饮即赌，那里想到这段公案，因此气了一夜。',
    '代儒气了一夜', [show('jia_dairu', 'yard'), effect('jia_dairu', 'anger')])
say('C12-015', 'jia_dairu',
    '代儒道：“自来出门，非禀我不敢擅出，如何昨日私自去了？据此亦该打，何况是撒谎。”'
    '因此发狠到底打了三四十扳，不许吃饭，令他跪在院内读文章。',
    '打了三四十扳', [effect('jia_dairu', 'anger')])

# ===== c12-second : 再约空屋 ============================
section('c12-second', 'c6_wangchui', '凤姐院 · 房内', 'feng_room',
        '此时贾瑞前心犹是未改')
say('C12-020', 'narrator',
    '此时贾瑞前心犹是未改，再想不到是凤姐捉弄他。过后两日，得了空，便仍来找凤姐。',
    '前心犹是未改', [show('jia_rui', 'feng_room'), show('feng', 'feng_room')])
say('C12-021', 'feng',
    '凤姐故意抱怨他失信，贾瑞急的赌身发誓。凤姐因见他自投罗网，'
    '少不得再寻别计令他知改。', '故意抱怨失信', [effect('feng', 'anger')])
say('C12-022', 'feng',
    '凤姐故又约他道：“今日晚上，你别在那里了。你在我这房后小过道子里那间空屋里等我，'
    '可别冒撞了。”', '约在房后空屋', [effect('feng', 'idle')])
say('C12-023', 'jia_rui',
    '贾瑞道：“来，来，来。死也要来！”凤姐道：“这会子你先去罢。”'
    '贾瑞料定晚间必妥，此时先去了。', '死也要来',
    [effect('jia_rui', 'greet'), move('jia_rui', 'feng_room', 'hall')])
say('C12-024', 'feng',
    '凤姐在这里便点兵派将，设下圈套。（贾蔷、贾蓉二人是她叫来的，'
    '这一段原著未写在当场对话里，按回目「毒设相思局」演出。）',
    '点兵派将设下圈套', [effect('feng', 'anger')])

# ===== c12-trap : 空屋捉奸 ============================
section('c12-trap', 'c12_passage', '荣府 · 房后空屋', 'empty',
        '那贾瑞只盼不到晚上')
say('C12-030', 'narrator',
    '那贾瑞只盼不到晚上，偏生家里亲戚又来了，直等吃了晚饭才去，'
    '那天已有掌灯时候。又等他祖父安歇了，方溜进荣府，直往那夹道中屋子里来等着，'
    '热锅上的蚂蚁一般，只是干转。', '热锅上的蚂蚁',
    [show('jia_rui', 'gate'), move('jia_rui', 'yard', 'empty_door')])
say('C12-031', 'narrator',
    '左等不见人影，右听也没声响，心下自思：“别是又不来了，又冻我一夜不成？”'
    '正自胡猜，只见黑魆魆的来了一个人，贾瑞便意定是凤姐，不管皂白，饿虎一般，'
    '等那人刚至门前，便如猫捕鼠的一般，抱住叫道：“亲嫂子，等死我了。”',
    '黑魆魆的来了一个人', [move('jia_rui', 'empty'), effect('jia_rui', 'greet')])
say('C12-032', 'narrator',
    '说着，抱到屋里炕上就亲嘴扯裤子，满口里亲娘亲爹的乱叫起来。'
    '那人只不作声。忽见灯光一闪，只见贾蔷举着个捻子照道：“谁在屋里？”'
    '只见炕上那人笑道：“瑞大叔要臊我呢。”', '灯光一闪',
    [show('jia_qiang', 'empty'), show('jia_rong', 'empty'), effect('jia_qiang', 'anger')])
say('C12-033', 'narrator',
    '贾瑞一见，却是贾蓉，真臊的无地可入，不知要怎么样才好，回身就要跑，'
    '被贾蔷一把揪住。', '臊的无地可入', [effect('jia_rui', 'anger')])
say('C12-034', 'jia_qiang',
    '贾蔷一把揪住道：“别走！如今琏二嫂已经告到太太跟前，说你无故调戏他。'
    '他暂用了个脱身计，哄你在这边等着，太太气死过去，因此叫我来拿你。”',
    '琏二嫂告到太太跟前', [effect('jia_qiang', 'anger')])

# ===== c12-extort : 五十两欠契 ============================
section('c12-extort', 'c12_passage', '荣府 · 房后空屋', 'corner',
        '贾瑞听了，魂不附体')
say('C12-040', 'jia_rui',
    '贾瑞听了，魂不附体，只说：“好侄儿，只说没有见我，明日我重重的谢你。”',
    '明日重重的谢你', [effect('jia_rui', 'anger')])
say('C12-041', 'jia_qiang',
    '贾蔷道：“你若谢我，放你不值什么，只不知你谢我多少？况且口说无凭，写一文契来。”'
    '贾瑞道：“这如何落纸呢？”贾蔷道：“写一个赌钱输了外人帐目，借头家银若干两便罢。”',
    '写一文契来', [effect('jia_qiang', 'idle')])
say('C12-042', 'narrator',
    '贾蔷翻身出来，纸笔现成，拿来命贾瑞写。他两个作好作歹，只写了五十两，'
    '然后画了押，贾蔷收起来；然后又撕逻贾蓉，也写了一张五十两欠契才罢。',
    '两张五十两欠契', [effect('jia_rong', 'greet')])
say('C12-043', 'jia_qiang',
    '贾蔷又道：“如今要放你，我就担着不是。老太太那边的门早已关了，'
    '如今只好走后门。这屋你还藏不得，少时就来堆东西。”',
    '这屋还藏不得', [effect('jia_qiang', 'idle')])
say('C12-044', 'narrator',
    '贾蔷拉着贾瑞，仍熄了灯，出至院外，摸着大台矶底下，说道：“这窝儿里好，'
    '你只蹲着，别哼一声，等我们来再动。”说毕，二人去了。', '蹲在大台矶底下',
    [move('jia_rui', 'corner'), hide('jia_qiang'), hide('jia_rong')])
say('C12-045', 'narrator',
    '贾瑞此时身不由己，只得蹲在那里。心下正盘算，只听头顶上一声响，'
    '唿喇喇一净桶尿粪从上面直泼下来，可巧浇了他一身一头。',
    '一净桶尿粪泼下来', [effect('jia_rui', 'anger')])
say('C12-046', 'narrator',
    '贾瑞掌不住嗳哟了一声，忙又掩住口，不敢声张，满头满脸浑身皆是尿屎，冰冷打战。'
    '只见贾蔷跑来叫：“快走，快走！”贾瑞如得了命，三步两步从后门跑到家里。',
    '三步两步跑回家', [move('jia_rui', 'empty_door', 'gate')])

# ===== c12-illness : 病榻 ==================================
# 原文位置：贾瑞自见熙凤后相思成病（2578），百般请医疗治皆不见效（2787）。
# 此段只到「无药不吃」；紧接其后是「往荣府寻人参」，再接跛足道人授镜。
section('c12-illness', 'c12_sickbed', '贾瑞书房 · 病榻', 'bed',
        '那贾瑞此时要命心甚切')
say('C12-050', 'narrator',
    '自此贾瑞满心想凤姐，只不敢往荣府去了。贾蓉两个又常常的来索银子，'
    '他又怕祖父知道。正是相思尚且难禁，更又添了债务，日间工课又紧，'
    '因此三五下里夹攻，不觉就得了一病。', '三五下里夹攻',
    [show('jia_rui', 'bed')])
say('C12-051', 'narrator',
    '那贾瑞此时要命心甚切，无药不吃，只是白花钱，不见效。', '无药不吃',
    [move('jia_rui', 'bed', 'bedside')])

# ===== c12-ginseng : 往荣府寻人参 ============================
# 原文位置：贾瑞病重，代儒各处请医不见效，因要吃「独参汤」只得往荣府来寻；
# 王夫人命凤姐秤二两给他，凤姐推说「前儿都替老太太配了药」，只将渣末泡须凑
# 几钱送去，回王夫人却报「共凑了有二两送去」。
# 这一段是第十二回唯一一笔「药钱」转手：二两人参自荣府流出、给到贾代儒手里，
# 故入账为 granted、金额记二两（原文明写「秤二两给他」）。
section('c12-ginseng', 'wang', '东廊三间 · 王夫人起居处', 'guest_seat',
        '代儒也着了忙，各处请医疗治，皆不见效。因后来吃"独参汤"，代儒如何有这力量，只得往荣府来寻')
say('C12-056', 'narrator',
    '代儒也着了忙，各处请医疗治，皆不见效。因后来要吃「独参汤」，'
    '代儒如何有这力量，只得往荣府来寻。', '只得往荣府来寻',
    [show('jia_dairu', 'court_entry'), move('jia_dairu', 'court_entry', 'guest_seat')])
say('C12-057', 'wang',
    '王夫人命凤姐秤二两给他。凤姐回说：“前儿新近都替老太太配了药，'
    '那整的太太又说留着送杨提督的太太配药，偏生昨儿我已送了去了。”',
    '命凤姐秤二两', [show('wang', 'wang_host'), show('feng', 'tea_seat'),
                      move('wang', 'wang_host', 'guest_seat')])
say('C12-058', 'wang',
    '王夫人道：“就是咱们这边没了，你打发个人往你婆婆那边问问，'
    '或是你珍大哥哥那府里再寻些来，凑着给人家。吃好了，救人一命，也是你的好处。”',
    '再寻些来凑着给人家', [effect('wang', 'idle'), move('feng', 'tea_seat', 'wang_host')])
say('C12-059', 'feng',
    '凤姐听了，也不遣人去寻，只得将些渣末泡须凑了几钱，命人送去，'
    '只说：“太太送来的，再也没了。”然后回王夫人，只说：“都寻了来，'
    '共凑了有二两送去。”', '只将渣末凑了几钱',
    [effect('feng', 'greet'), hide('feng'), hide('wang'), hide('jia_dairu')])

# ===== c12-taoist : 跛足道人授风月宝鉴 ====================
# 原文位置：代儒寻人参（2843）之后、道士来化斋（3118）之前已无文，故紧接寻人参段。
# 场景自 wang 切回 c12_sickbed，所有人都被隐去，故 C12-052 先把贾瑞与道士 show 出来。
section('c12-taoist', 'c12_sickbed', '贾瑞书房 · 病榻', 'bed',
        '忽然这日有个跛足道人来化斋')
say('C12-052', 'narrator',
    '忽然这日有个跛足道人来化斋，口称专治冤业之症。贾瑞偏生在内就听见了，'
    '直着声叫喊说：“快请进那位菩萨来救我！”一面叫，一面在枕上叩首。',
    '跛足道人来化斋', [show('jia_rui', 'bed'), show('taoist', 'door'), effect('jia_rui', 'anger')])
say('C12-053', 'taoist',
    '那道士叹道：“你这病非药可医。我有个宝贝与你，你天天看时，此命可保矣。”'
    '说毕，从褡裢中取出一面镜子来——两面皆可照人，镜把上面錾着风月宝鉴四字。',
    '取出一面镜子来', [move('taoist', 'bedside'), effect('taoist', 'greet')])
say('C12-054', 'taoist',
    '道士递与贾瑞道：“这物出自太虚幻境空灵殿上，警幻仙子所制，专治邪思妄动之症。'
    '千万不可照正面，只照他的背面，要紧，要紧！三日后吾来收取，管叫你好了。”',
    '千万不可照正面', [move('taoist', 'mirror'), effect('taoist', 'anger')])
say('C12-055', 'narrator',
    '说毕，道士佯常而去，众人苦留不住。', '佯常而去', [hide('taoist')])

# ===== c12-mirror : 风月宝鉴 ============================
section('c12-mirror', 'c12_sickbed', '贾瑞书房 · 病榻', 'mirror',
        '贾瑞收了镜子')
say('C12-060', 'jia_rui',
    '贾瑞收了镜子，想道：“这道士倒有意思，我何不照一照试试。”'
    '想毕，拿起风月鉴来，向反面一照，只见一个骷髅立在里面。',
    '反面一照是骷髅',
    # 中间插了「往荣府寻人参」一段，场景切到 wang 再切回病榻，
    # 换场会把所有人物收为不可见，故此处先重新出场再走位。
    [show('jia_rui', 'bedside'), move('jia_rui', 'mirror'), effect('jia_rui', 'anger')])
say('C12-061', 'jia_rui',
    '贾瑞唬得连忙掩了，骂：“道士混帐，如何吓我！我倒再照照正面是什么。”'
    '想着，又将正面一照，只见凤姐站在里面招手叫他。', '正面一照是凤姐',
    [effect('jia_rui', 'greet')], layer='dream')
say('C12-062', 'narrator',
    '贾瑞心中一喜，荡悠悠的觉得进了镜子，与凤姐云雨一番，凤姐仍送他出来。'
    '到了床上，哎哟了一声，一睁眼，镜子从手里掉过来，仍是反面立着一个骷髅。',
    '荡悠悠进了镜子', layer='dream')
say('C12-063', 'narrator',
    '贾瑞心中到底不足，又翻过正面来，只见凤姐还招手叫他，他又进去。如此三四次。',
    '如此三四次', [effect('jia_rui', 'idle')], layer='dream')
say('C12-064', 'narrator',
    '到了这次，刚要出镜子来，只见两个人走来，拿铁锁把他套住，拉了就走。'
    '贾瑞叫道：“让我拿了镜子再走。”只说了这句，就再不能说话了。',
    '拿铁锁把他套住', [effect('jia_rui', 'anger')], layer='dream')
say('C12-065', 'narrator',
    '旁边伏侍贾瑞的众人，只见他先还拿着镜子照，落下来，仍睁开眼拾在手内，'
    '末后镜子落下来便不动了。众人上来看看，已没了气。', '已没了气',
    [effect('jia_rui', 'rest')])
say('C12-066', 'narrator',
    '代儒夫妇哭的死去活来，大骂道士：“是何妖镜！”遂命架火来烧，'
    '只听镜内哭道：“谁叫你们瞧正面了！你们自己以假为真，何苦来烧我？”',
    '是何妖镜', [show('jia_dairu', 'door'), effect('jia_dairu', 'anger')], offscreen=True)
say('C12-067', 'taoist',
    '只见那跛足道人从外面跑来，喊道：“谁毁风月鉴，吾来救也！”'
    '说着，直入中堂，抢入手内，飘然去了。', '吾来救也',
    [show('taoist', 'door'), effect('taoist', 'greet')], offscreen=True)

# ===== c12-depart : 黛玉回扬州 ============================
section('c12-depart', 'night', '贾母院 · 碧纱橱外间', 'grandmother_bed',
        '谁知这年冬底，林如海的书信寄来')
say('C12-070', 'narrator',
    '当下代儒料理丧事，各处去报丧。三日起经，七日发引，寄灵于铁槛寺，'
    '日后带回原籍。', '寄灵于铁槛寺', offscreen=True)
say('C12-071', 'narrator',
    '谁知这年冬底，林如海的书信寄来，却为身染重疾，写书特来接林黛玉回去。'
    '贾母听了，未免又加忧闷，只得忙忙的打点黛玉起身。', '林如海的书信寄来',
    [show('grandmother', 'grandmother_bed'), show('daiyu', 'daiyu_bed')])
say('C12-072', 'grandmother',
    '（贾母定要贾琏送他去，仍叫带回来。一应土仪盘缠，自然要妥贴。）'
    '贾母道：“作了速，择了日期，就打发他们去罢。”', '定要贾琏送他去',
    [effect('grandmother', 'rest')])
say('C12-073', 'narrator',
    '宝玉大不自在，争奈父女之情，也不好拦劝。（贾琏在原著中只列名，'
    '无台词、不另造人出场。）', '宝玉大不自在',
    [show('baoyu', 'baoyu_bed'), effect('baoyu', 'rest')])
say('C12-074', 'narrator',
    '作速择了日期，贾琏与林黛玉辞别了贾母等，带领仆从，登舟往扬州去了。',
    '登舟往扬州去了', [move('daiyu', 'outer_door')])


def verify_sources():
    import re
    base = re.sub(r'\s+', '', Path('docs/chapter12-source.txt').read_text())
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
        raise SystemExit('source leads do not match docs/chapter12-source.txt')
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_DIR / 'chapter12-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 12}
                for sid, title, scene in SECTIONS]
    (STAGE_DIR / 'chapter12-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter12-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter12-sections.json  %d sections' % n_sections)

