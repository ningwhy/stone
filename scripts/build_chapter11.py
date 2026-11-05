#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-eleven's stage, script and section table.

第十一回 · 庆寿辰宁府排家宴 · 见熙凤贾瑞起淫心

Chapter eleven owns this generator; nothing here touches an earlier chapter.

Outputs:
  maps/c11_tianxiang.tmj        新舞台：天香楼 · 戏台与看楼
  design/chapter11-story.json   节点 C11-001..
  design/chapter11-sections.json

本回复用：maps/c5_ningfu.tmj（会芳园 / 上房 / 秦氏卧房）与
maps/c6_wangchui.tmj（凤姐院）。

只被提及、不在场上的人不造人出场：贾敬（只转述）、贾琏（只列名）、
尤氏的母亲（只列名）、南安郡王等（只由贾蓉回话）。

Usage: python3 scripts/build_chapter11.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402

BACKUP = ROOT / 'artifacts/backups/2026-10-31-chapter11'
PUBLISH_MAP = True
MAP_DIR = ROOT / 'maps' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter11'
STAGE_DIR = ROOT / 'design' if PUBLISH_MAP else ROOT / 'artifacts/staging/chapter11'


def at(c, r, dx=0.0, dy=0.0):
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)


scenes = {
    'c11_tianxiang': {
        'name': '天香楼 · 戏台与看楼',
        'theme': 'interior',
        # 看楼（HALL，行 9-19）与小院（A0，行 20-29）贴邻，中间不留空行——
        # 留一行 A* 就找不到上楼的路。
        'zones': [[12, 20, 16, 10], [13, 9, 14, 11, True, 'HALL']],
        'anchors': {
            'gate': [22, 28],
            'yard': [17, 25],
            'stair': [16, 19],
            'box': [18, 13],
            'stage': [23, 11],
        },
        'routes': {
            'entry': ['gate', 'yard', 'stair'],
            'to_box': ['stair', 'box'],
        },
        'labels': [['天香楼', 18, 11], ['戏台', 23, 12], ['楼梯口', 16, 18]],
        'props': [
            ('ning-hall', *at(19, 13), .82, 'HALL'),
            # 戏台：这一段的标题就叫「点戏」，原来「戏台」两个字孤零零挂在空地上，
            # 标签指的东西根本不存在。stage-platform 是为它新做的资产（见
            # scripts/furniture_sources.py），摆在看楼东端，正对着座席。
            ('stage-platform', *at(23, 11), .74, 'HALL'),
            # 看楼的座席：一张桌、两把椅对着戏台方向；屏风挡住楼梯口的风。
            ('square-table', *at(18, 13, 0, 0), .60, 'HALL'),
            ('official-chair', *at(18, 13, -80, 16), .66, 'HALL'),
            ('official-chair', *at(18, 13, 80, 16), .66, 'HALL'),
            ('wood-screen', *at(16, 16, 0, 0), .66, 'HALL'),
            ('lamp-stand', *at(21, 16, 0, 0), .68, 'HALL'),
            ('brazier', *at(15, 14, 0, 0), .56, 'HALL'),
            ('flower-gate', *at(22, 28), .50),
            ('garden-tree', *at(13, 24), 1.00),
            ('garden-tree', *at(26, 24), .94),
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
    ('c11-birthday', '宁府 · 太爷寿辰', 'c5_ningfu'),
    ('c11-guests', '宁府 · 宾客渐至', 'c5_ningfu'),
    ('c11-illness', '宁府 · 说起秦氏之病', 'c5_ningfu'),
    ('c11-gifts', '宁府 · 寿礼到门', 'c5_ningfu'),
    ('c11-visit', '秦氏卧房 · 凤姐探病', 'c5_ningfu'),
    ('c11-garden', '会芳园 · 贾瑞起淫心', 'c5_ningfu'),
    ('c11-opera', '天香楼 · 点戏', 'c11_tianxiang'),
    ('c11-winter', '冬至 · 再看秦氏', 'c5_ningfu'),
    ('c11-ping', '凤姐院 · 平儿报信', 'c6_wangchui'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 11, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c11-birthday : 太爷寿辰 ============================
section('c11-birthday', 'c5_ningfu', '宁国府 · 会芳园', 'garden_entry',
        '话说是日贾敬的寿辰，贾珍先将上等可吃的东西，稀奇些的果品，装了十六大捧盒，着贾蓉带领家下人等')
say('C11-001', 'narrator',
    '是日贾敬的寿辰。贾珍先将上等可吃的东西、稀奇些的果品，装了十六大捧盒，'
    '着贾蓉带领家下人等与贾敬送去。', '十六大捧盒', [show('jia_zhen', 'garden_entry'),
                                          show('jia_rong', 'garden_center')])
say('C11-002', 'jia_zhen',
    '贾珍向贾蓉说道：“你留神看太爷喜欢不喜欢，你就行了礼来。'
    '你说：我父亲遵太爷的话未敢来，在家里率领合家都朝上行了礼了。”', '着贾蓉送去',
    [effect('jia_zhen', 'greet'), move('jia_rong', 'garden_center', 'garden_entry')])
say('C11-003', 'narrator',
    '贾蓉听罢，即率领家人去了。（贾敬在原著中始终未回府，只在道观里，'
    '此处只由贾珍、贾蓉转述，不上场。）', '贾蓉领命去了',
    [move('jia_rong', 'garden_entry', 'garden_center'), hide('jia_rong')])

# ===== c11-guests : 宾客渐至 ============================
section('c11-guests', 'c5_ningfu', '宁国府 · 上房', 'upper_room',
        '这里渐渐的就有人来了。先是贾琏，贾蔷到来')
say('C11-010', 'narrator',
    '这里渐渐的就有人来了。先是贾琏、贾蔷到来，先看了各处的座位，'
    '并问：“有什么顽意儿没有？”（贾琏在原著中只列名，无台词、不上场。）',
    '贾琏贾蔷先到', [show('jia_qiang', 'garden_entry'), move('jia_qiang', 'garden_center')])
say('C11-011', 'narrator',
    '家人答道：“我们爷原算计请太爷今日来家来，所以未敢预备顽意儿。'
    '前日听见太爷又不来了，现叫奴才们找了一班小戏儿并一档子打十番的，'
    '都在园子里戏台上预备着呢。”', '园子里预备着戏', offscreen=True)
say('C11-012', 'narrator',
    '次后邢夫人、王夫人、凤姐儿、宝玉都来了，贾珍并尤氏接了进去。',
    '邢王二夫人到', [show('xing', 'garden_entry'), show('wang', 'garden_center'),
                 show('feng', 'upper_room_door'), show('baoyu', 'garden_center'),
                 show('you_shi', 'upper_room')])
say('C11-013', 'you_shi',
    '尤氏说道：“老太太原是老祖宗，我父亲又是侄儿，这样日子，原不敢请他老人家，'
    '但是这个时候，天气正凉爽，满园的菊花又盛开，请老祖宗过来散散闷。'
    '谁知老祖宗又不肯赏脸。”', '请老祖宗散散闷', [effect('you_shi', 'greet')])
say('C11-014', 'feng',
    '凤姐儿未等王夫人开口，先说道：“老太太昨日还说要来着呢，因为晚上看着宝兄弟他们吃桃儿，'
    '老人家又嘴馋，吃了有大半个，五更天的时候就一连起来了两次，今日早晨略觉身子倦些。”',
    '老太太身子倦', [effect('feng', 'idle')])
say('C11-015', 'jia_zhen',
    '贾珍听了笑道：“我说老祖宗是爱热闹的，今日不来，必定有个原故，若是这么着就是了。”',
    '贾珍解嘲', [effect('jia_zhen', 'greet')])

# ===== c11-illness : 说起秦氏之病 ============================
section('c11-illness', 'c5_ningfu', '宁国府 · 上房', 'upper_room',
        '王夫人道：“前日听见你大妹妹说')
say('C11-020', 'wang',
    '王夫人道：“前日听见你大妹妹说，蓉哥儿媳妇儿身上有些不大好，到底是怎么样？”',
    '王夫人问病', [effect('wang', 'idle')])
say('C11-021', 'you_shi',
    '尤氏道：“他这个病得的也奇。上月中秋还跟着老太太、太太们顽了半夜，回家来好好的。'
    '到了二十后，一日比一日觉懒，也懒待吃东西，这将近有半个多月了。'
    '经期又有两个月没来。”', '尤氏说病程', [effect('you_shi', 'idle')])
say('C11-022', 'you_shi',
    '尤氏道：“昨日冯紫英荐了他从学过的一个先生，医道很好，瞧了说不是喜，'
    '竟是很大的一个症候。昨日开了方子，吃了一剂药，今日头眩的略好些，'
    '别的仍不见怎么样大见效。”', '吃了药头眩略好', [effect('you_shi', 'rest')])
say('C11-023', 'feng',
    '凤姐儿听了，眼圈儿红了半天，半日方说道：“真是天有不测风云，人有旦夕祸福。'
    '这个年纪，倘或就因这个病上怎么样了，人还活着有甚么趣儿！”',
    '天有不测风云', [effect('feng', 'anger')])
say('C11-024', 'narrator',
    '正说话间，贾蓉进来，给邢夫人、王夫人、凤姐儿前都请了安。', '贾蓉进来请安',
    [show('jia_rong', 'upper_room_door'), move('jia_rong', 'upper_room_door', 'upper_room')])
say('C11-025', 'feng',
    '凤姐儿说：“蓉哥儿，你且站住。你媳妇今日到底是怎么着？”', '问蓉哥儿')
say('C11-026', 'jia_rong',
    '贾蓉皱皱眉说道：“不好么！婶子回来瞧瞧去就知道了。”', '贾蓉皱眉',
    [effect('jia_rong', 'anger'), move('jia_rong', 'upper_room', 'upper_room_door'),
     hide('jia_rong')])

# ===== c11-gifts : 各家寿礼到门 ============================
# 原文位置：席散饭毕、正要往园子里去时，贾蓉进来回话——四家王爷与镇国公、忠靖侯
# 两府共十四家差人持名帖送寿礼，礼单已上档子。这一笔是本回唯一「账簿入账」的
# 外来贺礼：寿礼自各家王爷、勋贵流向贾敬，故入账为 granted。
section('c11-gifts', 'c5_ningfu', '宁国府 · 上房', 'upper_room',
        '于是，尤氏的母亲并邢夫人，王夫人，凤姐儿都吃毕饭，漱了口，净了手，才说要往园子里去，贾蓉进来向尤氏说道')
say('C11-027', 'narrator',
    '于是，尤氏的母亲并邢夫人、王夫人、凤姐儿都吃毕饭，漱了口、净了手，'
    '才说要往园子里去，贾蓉进来向尤氏回话。', '饭毕贾蓉进来回话',
    [show('jia_rong', 'upper_room_door'), move('jia_rong', 'upper_room_door', 'upper_room')])
say('C11-028', 'jia_rong',
    '贾蓉说道：“老爷们并众位叔叔哥哥兄弟们也都吃了饭了。大老爷说家里有事，'
    '二老爷是不爱听戏又怕人闹的慌，都才去了。”', '老爷们才去了',
    [move('jia_rong', 'upper_room', 'upper_room_door')])
say('C11-029', 'jia_rong',
    '贾蓉又道：“方才南安郡王、东平郡王、西宁郡王、北静郡王四家王爷，'
    '并镇国公牛府等六家，忠靖侯史府等八家，都差人持了名帖送寿礼来，'
    '俱回了我父亲，先收在帐房里了，礼单都上上档子了。”', '各家送寿礼来',
    [move('jia_rong', 'upper_room_door', 'upper_room'), effect('jia_rong', 'greet')])

# ===== c11-visit : 凤姐探病 ============================
section('c11-visit', 'c5_ningfu', '秦氏卧房', 'screen_bed',
        '凤姐儿，宝玉方和贾蓉到秦氏这边来了')
say('C11-030', 'narrator',
    '凤姐儿、宝玉方和贾蓉到秦氏这边来了。进了房门，悄悄的走到里间房门口，'
    '秦氏见了就要站起来。', '到秦氏这边来',
    [show('feng', 'bedchamber_door'), show('baoyu', 'bedchamber'),
     show('jia_rong', 'bedchamber'), show('qin_ke', 'screen_bed')])
say('C11-031', 'feng',
    '凤姐儿说：“快别起来，看起猛了头晕。”于是紧走了两步，拉住秦氏的手，'
    '说道：“我的奶奶！怎么几日不见，就瘦的这么着了！”', '瘦的这么着了',
    [move('feng', 'bedchamber', 'screen_bed')])
say('C11-032', 'qin_ke',
    '秦氏拉着凤姐儿的手，强笑道：“这都是我没福。这样人家，公公婆婆当自己的女孩儿似的待。'
    '这如今得了这个病，把我那要强的心一分也没了。我自想着，未必熬的过年去呢。”',
    '未必熬的过年去', [effect('qin_ke', 'rest')])
say('C11-033', 'narrator',
    '宝玉正眼瞅着那《海棠春睡图》并那秦太虚写的“嫩寒锁梦因春冷，芳气笼人是酒香”的对联，'
    '不觉想起在这里睡晌觉梦到太虚幻境的事来，正自出神。', '海棠春睡图',
    # C11-030 已经把宝玉摆在卧房里，这里只是让他出神，不必再挪一次。
    # 原来这里 show('baoyu','portrait_wall')：一来 portrait_wall 是**上房**挂《燃藜图》的
    # 那面墙（第五回 C05-013 起用它当镜头焦点），海棠春睡图挂在**秦氏卧房**，两处不是一间；
    # 二来 portrait_wall 落在不可行走的格上（22,12），show 过去引擎直接报「显示地点不可通行」。
    [], focus='bedchamber', layer='recollection')
say('C11-034', 'narrator',
    '宝玉听得秦氏说了这些话，如万箭攒心，那眼泪不知不觉就流下来了。',
    '宝玉落泪', [effect('baoyu', 'rest')], layer='recollection')
say('C11-035', 'feng',
    '凤姐儿见宝玉这个样子，因说道：“宝兄弟，你忒婆婆妈妈的了。他病人不过是这么说，'
    '那里就到得这个田地了？”又向贾蓉道：“你先同你宝叔叔过去罢，我还略坐一坐儿。”',
    '凤姐支开宝玉', [effect('feng', 'idle')])
say('C11-036', 'qin_ke',
    '凤姐儿劝解了一番，秦氏笑道：“任凭神仙也罢，治得病治不得命。婶子，'
    '我知道我这病不过是挨日子。”', '治得病治不得命',
    [hide('baoyu'), hide('jia_rong'), effect('qin_ke', 'rest')])

# ===== c11-garden : 会芳园遇贾瑞 ============================
section('c11-garden', 'c5_ningfu', '会芳园', 'garden_center',
        '凤姐儿正自看园中的景致')
say('C11-040', 'narrator',
    '凤姐儿带领跟来的婆子丫头，从里头绕进园子的便门来。但见石中清流激湍，'
    '篱落飘香，树头红叶翩翻，疏林如画。', '园中景致',
    [show('feng', 'garden_entry'), move('feng', 'garden_center')])
say('C11-041', 'narrator',
    '凤姐儿正自看园中的景致，一步步行来赞赏。猛然从假山石后走过一个人来，'
    '向前对凤姐儿说道：“请嫂子安。”', '假山石后走出人来', [show('jia_rui', 'plum_grove')])
say('C11-042', 'feng',
    '凤姐儿猛然见了，将身子望后一退，说道：“这是瑞大爷不是？”', '猛然一退',
    [effect('feng', 'anger')], focus='plum_grove')
say('C11-043', 'jia_rui',
    '贾瑞说道：“嫂子连我也不认得了？不是我是谁！”', '嫂子连我也不认得',
    [move('jia_rui', 'garden_center'), effect('jia_rui', 'greet')])
say('C11-044', 'jia_rui',
    '贾瑞道：“也是合该我与嫂子有缘。我方才偷出了席，在这个清净地方略散一散，'
    '不想就遇见嫂子也从这里来。这不是有缘么？”一面说着，一面拿眼睛不住的觑着凤姐儿。',
    '合该我与嫂子有缘', [effect('jia_rui', 'idle')])
say('C11-045', 'feng',
    '凤姐儿是个聪明人，见他这个光景，如何不猜透八九分呢，因向贾瑞假意含笑道：'
    '“怨不得你哥哥时常提你，说你很好。今日见了，听你说这几句话儿，'
    '就知道你是个聪明和气的人了。”', '假意含笑', [effect('feng', 'idle')])
say('C11-046', 'feng',
    '（凤姐心里暗忖）这才是知人知面不知心呢，那里有这样禽兽的人呢。'
    '他如果如此，几时叫他死在我的手里，他才知道我的手段！',
    '几时叫他死在我手里', [effect('feng', 'anger')])

# ===== c11-opera : 天香楼点戏 ============================
section('c11-opera', 'c11_tianxiang', '天香楼 · 看楼', 'box',
        '凤姐儿听了，款步提衣上了楼')
say('C11-050', 'narrator',
    '凤姐儿款步提衣上了楼，见尤氏已在楼梯口等着呢。', '上了楼',
    [show('feng', 'gate'), show('you_shi', 'stair'), move('feng', 'yard', 'stair')])
say('C11-051', 'you_shi',
    '尤氏笑说道：“你们娘儿两个忒好了，见了面总舍不得来了。你明日搬来和他住着罢。'
    '你坐下，我先敬你一钟。”', '尤氏敬酒', [move('you_shi', 'box'), effect('you_shi', 'greet')])
say('C11-052', 'narrator',
    '尤氏叫拿戏单来，让凤姐儿点戏。凤姐儿说道：“亲家太太和太太们在这里，我如何敢点。”'
    '（尤氏的母亲在原著中只列名，不另造人出场。）', '让凤姐点戏',
    [show('xing', 'box'), show('wang', 'box')])
say('C11-053', 'feng',
    '凤姐儿立起身来答应了一声，方接过戏单，从头一看，点了一出《还魂》，'
    '一出《弹词》，递过戏单去说：“现在唱的这《双官诰》，唱完了，再唱这两出，'
    '也就是时候了。”', '点还魂与弹词', [move('feng', 'box'), effect('feng', 'idle')])

# ===== c11-winter : 冬至再看秦氏 ============================
section('c11-winter', 'c5_ningfu', '秦氏卧房', 'screen_bed',
        '且说贾瑞到荣府来了几次')
say('C11-060', 'narrator',
    '此后凤姐儿不时亲自来看秦氏。秦氏也有几日好些，也有几日仍是那样。'
    '贾珍、尤氏、贾蓉好不焦心。', '不时来看秦氏')
say('C11-061', 'narrator',
    '且说贾瑞到荣府来了几次，偏都遇见凤姐儿往宁府那边去了。这年正是十一月三十日冬至。',
    '贾瑞来了几次', offscreen=True)
say('C11-062', 'narrator',
    '到交节的那几日，贾母、王夫人、凤姐儿日日差人去看秦氏。'
    '回来的人都说：“这几日也没见添病，也不见甚好。”', '交节那几日',
    [show('feng', 'bedchamber_door')], layer='reported')
say('C11-063', 'narrator',
    '到了初二日，吃了早饭，凤姐儿来到宁府，看见秦氏的光景，虽未甚添病，'
    '但是那脸上身上的肉全瘦干了。', '身上的肉全瘦干了',
    [show('qin_ke', 'screen_bed'), move('feng', 'bedchamber', 'screen_bed')])
say('C11-064', 'qin_ke',
    '秦氏说道：“好不好，春天就知道了。如今现过了冬至，又没怎么样，或者好的了也未可知。'
    '婶子回老太太、太太放心罢。”', '春天就知道了', [effect('qin_ke', 'rest')])
say('C11-065', 'narrator',
    '凤姐儿到了尤氏上房坐下。尤氏道：“你冷眼瞧媳妇是怎么样？”'
    '凤姐儿低了半日头，说道：“这实在没法儿了。你也该将一应的后事用的东西'
    '给他料理料理，冲一冲也好。”', '该料理后事了',
    [show('you_shi', 'bedchamber_door')])

# ===== c11-ping : 平儿报信 ============================
section('c11-ping', 'c6_wangchui', '凤姐院 · 房内', 'feng_room',
        '凤姐儿答应着出来，见过了王夫人')
say('C11-070', 'narrator',
    '凤姐儿回到家中，见了贾母，只说蓉哥儿媳妇请老太太安、说好些了，'
    '求老祖宗放心——她怕吓着老人家，把实情瞒下了。', '瞒着贾母',
    [show('feng', 'back_gate'), move('feng', 'back_gate', 'feng_room')], layer='reported')
say('C11-071', 'narrator',
    '凤姐儿答应着出来，见过了王夫人，到了家中，平儿将烘的家常的衣服给凤姐儿换了。',
    '平儿换衣', [show('ping_er', 'feng_room')])
say('C11-072', 'ping_er',
    '平儿方端了茶来，说道：“没有什么事。就是那三百银子的利银，旺儿媳妇送进来，我收了。'
    '再有瑞大爷使人来打听奶奶在家没有，他要来请安说话。”',
    '瑞大爷使人来打听', [effect('ping_er', 'idle')])
say('C11-073', 'feng',
    '凤姐儿听了，哼了一声，说道：“这畜生合该作死，看他来了怎么样！”', '这畜生合该作死',
    [effect('feng', 'anger')])
say('C11-074', 'ping_er',
    '平儿说道：“癞蛤蟆想天鹅肉吃，没人伦的混帐东西，起这个念头，叫他不得好死！”',
    '癞蛤蟆想天鹅肉', [effect('ping_er', 'anger')])
say('C11-075', 'feng',
    '凤姐儿道：“等他来了，我自有道理。”', '我自有道理', [effect('feng', 'idle')])


def verify_sources():
    import re
    base = re.sub(r'\s+', '', Path('docs/chapter11-source.txt').read_text())
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
        raise SystemExit('source leads do not match docs/chapter11-source.txt')
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_DIR / 'chapter11-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 11}
                for sid, title, scene in SECTIONS]
    (STAGE_DIR / 'chapter11-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter11-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter11-sections.json  %d sections' % n_sections)
