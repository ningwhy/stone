#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-ten's stage, script and section table.

第十回 · 金寡妇贪利权受辱 · 张太医论病细穷源

Chapter ten owns this generator; nothing here touches an earlier chapter's file,
so re-running it cannot overwrite chapters 7-9.

Outputs:
  maps/c10_jinhome.tmj          新舞台：金荣家（小院与里屋）
  design/chapter10-story.json   节点 C10-001..
  design/chapter10-sections.json  段落 c10-home .. c10-diagnose

本回复用：maps/c5_ningfu.tmj（宁国府 · 会芳园与秦氏卧房）——会芳园、上房、
秦氏卧房三个空间与「璜大奶奶求见尤氏」「贾珍议医」「张太医诊脉」三处戏完全对应，
锚点（upper_room / bedchamber / screen_bed）已在第五回建好，不重建。

人物：尤氏、贾珍、金氏（璜大奶奶）、胡氏（金寡妇）、张友士为本回新立绘；
金荣、贾蓉、秦可卿、宝玉、秦钟复用既有资产。

Usage: python3 scripts/build_chapter10.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

BACKUP = ROOT / 'artifacts/backups/2026-10-31-chapter10'
PUBLISH_MAP = True
MAP_DIR = ROOT / 'maps' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter10'
STAGE_DIR = ROOT / 'design' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter10'


def at(c, r, dx=0.0, dy=0.0):
    """把屏幕像素偏移换成等距格坐标（同 stage_defs.at）。"""
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


# ---------------------------------------------------------------------------
# Maps
#
# 金荣家：京城里的一个小户人家。原文说「其族人那里皆能象宁荣二府的家势」，
# 胡氏又说「咱们家里还有力量请的起先生？」——一处靠人资助度日的窄院。
# 屋舍用最朴素的 farm-house 壳表现，是设计取舍，不是原文写明的形制。
# ---------------------------------------------------------------------------

scenes = {
    'c10_jinhome': {
        'name': '金荣家 · 小院与里屋',
        'theme': 'interior',
        # 里屋（ROOM，行 10-19）与小院（A0，行 20-29）必须贴邻：中间只要空一行，
        # A* 就找不到从院门进屋的路，人物会卡在院里走不进里屋。
        'zones': [[12, 20, 16, 10], [13, 10, 14, 10, True, 'ROOM']],
        'anchors': {
            'gate': [22, 28],
            'yard': [17, 25],
            'room_door': [16, 19],
            'room': [18, 13],
            'kang': [15, 12],
            'table': [21, 14],
        },
        'routes': {
            'main': ['gate', 'yard', 'room_door'],
            'inner': ['yard', 'room_door', 'room'],
        },
        'labels': [['金家', 16, 22], ['里屋', 18, 11], ['小院', 22, 26]],
        'props': [
            ('farm-house', *at(18, 13), .78, 'ROOM'),
            ('plain-kang', *at(15, 12, -20, 10), .68, 'ROOM'),
            ('square-table', *at(21, 14, 0, 0), .62, 'ROOM'),
            ('round-stool', *at(21, 14, 70, 20), .58, 'ROOM'),
            ('cabinet', *at(22, 12, 0, 0), .60, 'ROOM'),
            ('lamp-stand', *at(19, 16, 0, 0), .66, 'ROOM'),
            ('flower-gate', *at(22, 28), .50),
            ('garden-tree', *at(14, 24), .96),
            ('courtyard-wall', *at(25, 22), .62),
        ],
        'walls': [[12, 20, 28, 20], [12, 20, 12, 30], [28, 20, 28, 30],
                  [12, 30, 20, 30], [24, 30, 28, 30]],
        'terraces': [[20, 24, 4, 6, 'path']],
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
#
# 引文纪律：source.paragraphLead 一律照抄 docs/chapter10-source.txt 的段落起句，
# 脚本末尾会逐条回验。改写台词用 textKind=adaptation；原著只提及、不在场上的人
# （冯紫英、贾敬、来升、薛大爷）不造人出场，只用旁白或人物转述。
# ---------------------------------------------------------------------------

SECTIONS = [
    ('c10-home', '金家 · 金荣忍气', 'c10_jinhome'),
    ('c10-aunt', '金家 · 璜大奶奶动怒', 'c10_jinhome'),
    ('c10-ning', '宁府 · 尤氏说病', 'c5_ningfu'),
    ('c10-physician', '宁府 · 贾珍议医', 'c5_ningfu'),
    ('c10-diagnose', '秦氏卧房 · 张太医论病', 'c5_ningfu'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 10, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c10-home : 金荣回家，胡氏劝子 ============================
section('c10-home', 'c10_jinhome', '金荣家 · 里屋', 'room',
        '话说金荣因人多势众，又兼贾瑞勒令，赔了不是，给秦钟磕了头，宝玉方才不吵闹了。')
say('C10-001', 'narrator',
    '金荣散了学回到家中，越想越气。他咕咕嘟嘟地说：秦钟不过是贾蓉的小舅子，'
    '又不是贾家的子孙，附学读书也不过和自己一样；如今仗着宝玉和他好，就目中无人。',
    '金荣回家越想越气', [show('jin_rong', 'gate'), move('jin_rong', 'yard', 'room_door')])
say('C10-002', 'jin_rong',
    '金荣跺脚道：“今日他又去勾搭人，偏偏的撞在我眼睛里。就是闹出事来，我还怕什么不成？”',
    '金荣不服', [effect('jin_rong', 'anger')], focus='room')
say('C10-003', 'narrator',
    '他母亲胡氏听见了，忙问他又争什么闲气。', '胡氏听见', [show('hu_shi', 'room')])
say('C10-004', 'hu_shi',
    '胡氏叹道：“好容易我望你姑妈说了，你姑妈千方百计的才向他们西府里的琏二奶奶跟前说了，'
    '你才得了这个念书的地方。若不是仗着人家，咱们家里还有力量请的起先生？”',
    '胡氏劝子', [effect('hu_shi', 'idle')])
say('C10-005', 'hu_shi',
    '胡氏又道：“况且人家学里，茶也是现成的，饭也是现成的。你这二年在那里念书，'
    '家里也省好大的嚼用呢。再者，不是因你在那里念书，你就认得什么薛大爷了？'
    '那薛大爷这二年也帮了咱们有七八十两银子。”',
    '算计嚼用', [effect('hu_shi', 'rest')])
say('C10-006', 'hu_shi',
    '胡氏道：“你如今要闹出了这个学房，再要找这么个地方，我告诉你说罢，比登天还难呢！”',
    '比登天还难', [effect('hu_shi', 'anger')])
say('C10-007', 'narrator',
    '于是金荣忍气吞声，不多一时自去睡了。次日仍旧上学去了。', '忍气吞声',
    [hide('hu_shi'), hide('jin_rong')])

# ===== c10-aunt : 璜大奶奶登门动怒 ============================
section('c10-aunt', 'c10_jinhome', '金荣家 · 小院', 'yard',
        '且说他姑娘，原聘给的是贾家玉字辈的嫡派，名唤贾璜。')
say('C10-010', 'narrator',
    '金荣的姑妈原聘给贾家“玉”字辈的嫡派贾璜。这贾璜夫妻守着些小小的产业，'
    '又时常到宁荣二府里去请安，又会奉承凤姐儿并尤氏，所以凤姐儿、尤氏也时常资助他。',
    '璜大奶奶的家世', [show('jin_shi', 'gate'), move('jin_shi', 'yard')])
say('C10-011', 'narrator',
    '这一日天气晴明，家中无事，璜大奶奶带了一个婆子坐车来，瞧瞧寡嫂并侄儿。',
    '姑嫂闲话', [show('hu_shi', 'room_door')])
say('C10-012', 'hu_shi',
    '胡氏闲话之间，偏提起昨日贾家学房里的那事，从头至尾、一五一十都向小姑子说了。',
    '提起学房之事', [effect('hu_shi', 'idle')])
say('C10-013', 'jin_shi',
    '璜大奶奶一时怒从心上起，说道：“这秦钟小崽子是贾门的亲戚，难道荣儿不是贾门的亲戚？'
    '人都别忒势利了！”',
    '怒从心上起', [effect('jin_shi', 'anger')])
say('C10-014', 'jin_shi',
    '璜大奶奶道：“等我去到东府瞧瞧我们珍大奶奶，再向秦钟他姐姐说说，叫他评评这个理。”',
    '要往东府理论', [effect('jin_shi', 'anger')])
say('C10-015', 'hu_shi',
    '胡氏急的了不得，忙道：“这都是我的嘴快，告诉了姑奶奶了，求姑奶奶别去！'
    '倘或闹起来，怎么在那里站得住？”',
    '胡氏急劝', [effect('hu_shi', 'anger')])
say('C10-016', 'narrator',
    '璜大奶奶哪里肯听，一面叫老婆子瞧了车，就坐上往宁府里来。', '坐车往宁府',
    [hide('hu_shi'), move('jin_shi', 'gate')])

# ===== c10-ning : 宁府，尤氏说病 ============================
section('c10-ning', 'c5_ningfu', '宁国府 · 上房', 'upper_room',
        '到了宁府，进了车门，到了东边小角门前下了车，进去见了贾珍之妻尤氏。')
say('C10-020', 'narrator',
    '璜大奶奶到了宁府，进了东边小角门下车，进去见了尤氏。她原是带着气来的，'
    '见了尤氏却未敢气高，只殷殷勤勤叙过寒温。',
    '见尤氏', [show('jin_shi', 'garden_entry'), show('you_shi', 'upper_room'),
               move('jin_shi', 'garden_center', 'upper_room_door')])
say('C10-021', 'jin_shi',
    '璜大奶奶说了些闲话，方问道：“今日怎么没见蓉大奶奶？”', '问起蓉大奶奶',
    [effect('jin_shi', 'idle')])
say('C10-022', 'you_shi',
    '尤氏说道：“他这些日子不知怎么着，经期有两个多月没来。叫大夫瞧了，又说并不是喜。'
    '那两日，到了下半天就懒待动，话也懒待说，眼神也发眩。”',
    '尤氏说病', [effect('you_shi', 'idle')])
say('C10-023', 'you_shi',
    '尤氏又道：“婶子，你是知道那媳妇的：虽则见了人有说有笑，会行事儿，他可心细，心又重，'
    '不拘听见个什么话儿，都要度量个三日五夜才罢。这病就是打这个秉性上头思虑出来的。”',
    '病从思虑上来', [effect('you_shi', 'rest')])
say('C10-024', 'you_shi',
    '尤氏道：“他听了这事，今日索性连早饭也没吃。我方才看着他吃了半盏燕窝汤，才过来了。'
    '婶子，你说我心焦不心焦？你们知道有什么好大夫没有？”',
    '问有好大夫没有', [effect('you_shi', 'anger')])
say('C10-025', 'narrator',
    '金氏听了这半日话，把方才在嫂子家那一团要向秦氏理论的盛气，早吓的都丢在爪洼国去了。',
    '盛气丢在爪洼国', [effect('jin_shi', 'rest')])
say('C10-026', 'jin_shi',
    '金氏连忙答道：“我们这么听着，实在也没见人说有个好大夫。如今听起大奶奶这个来，'
    '定不得还是喜呢。嫂子倒别教人混治。”',
    '转怒为歉', [effect('jin_shi', 'idle')])

# ===== c10-physician : 贾珍议医，太爷寿日 ============================
section('c10-physician', 'c5_ningfu', '宁国府 · 上房', 'upper_room',
        '金氏去后，贾珍方过来坐下，问尤氏道')
say('C10-030', 'narrator',
    '正说话间，贾珍从外进来，见了金氏便问尤氏：“这不是璜大奶奶么？”'
    '金氏向前给贾珍请了安。', '贾珍进来',
    [show('jia_zhen', 'upper_room_door'), move('jia_zhen', 'upper_room_door', 'upper_room')])
say('C10-031', 'jia_zhen',
    '贾珍向尤氏说道：“让这大妹妹吃了饭去。”说着话，就过那屋里去了。',
    '让大妹妹吃饭', [effect('jia_zhen', 'greet'), move('jia_zhen', 'upper_room', 'upper_room_door')])
say('C10-032', 'narrator',
    '金氏此来原要向秦氏说说秦钟欺负了他侄儿的事，听见秦氏有病，不但不能说，亦且不敢提了；'
    '况且贾珍、尤氏又待的很好，便反转怒为喜，又说了一会子话儿，方家去了。',
    '反转怒为喜', [hide('jin_shi')])
say('C10-033', 'you_shi',
    '尤氏道：“如今且说媳妇这病，你到那里寻一个好大夫来与他瞧瞧要紧，可别耽误了。'
    '现今咱们家走的这群大夫，那里要得？”',
    '求好大夫', [effect('you_shi', 'idle')])
say('C10-034', 'jia_zhen',
    '贾珍道：“衣裳任凭是什么好的，可又值什么，孩子的身子要紧。我正进来要告诉你：'
    '方才冯紫英来看我，他说起有个幼时从学的先生，姓张名友士，学问最渊博的，更兼医理极深。”'
    '（冯紫英在原著中只被转述，不在场上。）',
    '冯紫英荐张友士', [effect('jia_zhen', 'idle')])
say('C10-035', 'jia_zhen',
    '贾珍道：“今年他是上京给他儿子来捐官，现在冯家住着呢。我已差人拿我的名帖请去了，'
    '等这个张先生来瞧了再说罢。”',
    '差人拿名帖去请', [effect('jia_zhen', 'greet')])
say('C10-036', 'you_shi',
    '尤氏听了心中甚喜，因说道：“后日是太爷的寿日，到底怎么办？”', '问太爷寿日')
say('C10-037', 'jia_zhen',
    '贾珍道：“我方才到了太爷那里去请安。太爷说：`我是清净惯了的，'
    '我不愿意往你们那是非场中去闹去。你们必定说是我的生日，'
    '莫过你把我从前注的《阴骘文》给我令人好好的写出来刻了。’”'
    '（贾敬在原著中只被转述，不回府、不上场。）',
    '太爷要刻阴骘文', [effect('jia_zhen', 'rest')])

# ===== c10-diagnose : 张太医诊脉穷源 ============================
section('c10-diagnose', 'c5_ningfu', '秦氏卧房', 'screen_bed',
        '且说次日午间，人回道')
say('C10-040', 'narrator',
    '次日午间，人回道：“请的那张先生来了。”贾珍遂延入大厅坐下，'
    '说道：“就请先生进去看看儿妇，仰仗高明，以释下怀。”',
    '张先生来了', [show('zhang_youshi', 'bedchamber_door'), show('jia_rong', 'bedchamber'),
                   show('qin_ke', 'screen_bed')])
say('C10-041', 'zhang_youshi',
    '张先生道：“依小弟的意思，竟先看过脉再说的为是。如今看了脉息，看小弟说的是不是，'
    '再将这些日子的病势讲一讲，大家斟酌一个方儿。”',
    '先看脉', [effect('zhang_youshi', 'idle')])
say('C10-042', 'narrator',
    '家下媳妇们捧过大迎枕来，拉着袖口露出脉来。先生伸手按在右手脉上，'
    '宁神细诊了有半刻的工夫，方换过左手，亦复如是。',
    '凝神细诊', [move('zhang_youshi', 'bedchamber', 'screen_bed')])
say('C10-043', 'zhang_youshi',
    '先生道：“看得尊夫人这脉息：左寸沉数，左关沉伏，右寸细而无力，右关需而无神。'
    '或以这个脉为喜脉，则小弟不敢从其教也。”',
    '断脉非喜', [effect('zhang_youshi', 'idle')])
say('C10-044', 'narrator',
    '旁边贴身伏侍的婆子道：“真正先生说的如神，倒不用我们告诉了。”',
    '婆子称如神', offscreen=True)
say('C10-045', 'zhang_youshi',
    '先生道：“大奶奶是个心性高强、聪明不过的人。聪明忒过，则不如意事常有；'
    '不如意事常有，则思虑太过。此病是忧虑伤脾，肝木忒旺，经血所以不能按时而至。”',
    '论病源', [effect('zhang_youshi', 'greet')])
say('C10-046', 'zhang_youshi',
    '先生又问：“大奶奶从前的行经的日子问一问，断不是常缩，必是常长的。是不是？”',
    '问行经日子', [effect('zhang_youshi', 'idle')])
say('C10-047', 'narrator',
    '那婆子答道：“可不是，从没有缩过，或是长两日三日，以至十日都长过。”'
    '先生听了道：“妙啊！这就是病源了。”', '这就是病源', offscreen=True)
say('C10-048', 'zhang_youshi',
    '于是先生写了方子递与贾蓉，上写的是“益气养荣补脾和肝汤”。', '开方',
    [effect('zhang_youshi', 'rest')])
say('C10-049', 'jia_rong',
    '贾蓉看了说：“高明的很。还要请教先生，这病与性命终久有妨无妨？”', '问性命有妨无妨')
say('C10-050', 'zhang_youshi',
    '先生笑道：“大爷是最高明的人。人病到这个地位，非一朝一夕的症候，吃了这药也要看医缘了。'
    '依小弟看来，今年一冬是不相干的。总是过了春分，就可望全愈了。”',
    '过春分可望全愈', [effect('zhang_youshi', 'greet')])
say('C10-051', 'jia_zhen',
    '贾珍道：“他那方子上有人参，就用前日买的那一斤好的罢。”'
    '贾蓉出来叫人打药去煎给秦氏吃。', '用那斤好人参',
    [show('jia_zhen', 'bedchamber_door')])


def verify_sources():
    """逐条回验引文确实落在底本里——底本是抓取来的，必须查过才能引用。"""
    import re
    base = re.sub(r'\s+', '', Path('docs/chapter10-source.txt').read_text())
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
        raise SystemExit('source leads do not match docs/chapter10-source.txt')
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_DIR / 'chapter10-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 10}
                for sid, title, scene in SECTIONS]
    (STAGE_DIR / 'chapter10-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter10-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter10-sections.json  %d sections' % n_sections)
