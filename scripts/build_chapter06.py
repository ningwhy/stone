#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-six maps, its playable script and its section table.

Chapter six owns this generator; nothing here touches build_chapter05.py or
write_prequel.py, so re-running it cannot overwrite an earlier chapter.

Outputs (printed at the end):
  maps/c6_village.tmj        new stage: 刘家庄 · 狗儿家
  maps/c6_wangchui.tmj       new stage: 荣府后门 / 周瑞家 / 贾琏院 / 凤姐上房
  design/chapter06-story.json      nodes C06-001..C06-161
  design/chapter06-sections.json   ten sections: c6-qin .. c6-gift
  (复用 maps: c5_ningfu 由第五回生成；grandmother 场景复用 night；capital 既有)

Usage: python3 scripts/build_chapter06.py
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import eave, fit, is_shell  # noqa: E402  (a roof lifts off the floor it covers)
BACKUP = ROOT / 'artifacts/backups/2026-10-27-chapter06'


def at(c, r, dx=0.0, dy=0.0):
    """把屏幕像素偏移换成等距格坐标。

    一处室内的陈设要先定一个落点（人站的地方、炕沿、案心），其余件按**屏幕像素**
    相对它摆；只按整数格摆，相邻一格就是 ±(64,32) 像素，等于把炕桌甩出半张炕。
    x=(c-r)*64, y=(c+r+1)*32  ⇒  dc = dx/128 + dy/64, dr = dy/64 - dx/128
    """
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)

# ---------------------------------------------------------------------------
# Maps
#
# 第六回全部为现实场景。前两段直接衔接第五回末尾的秦氏卧房（c5_ningfu，
# 由第五回生成器产出，本回复用），贾母处复用既有的 night 场景（贾母院·碧纱橱
# 与外间）。本回新建两张舞台：
#   c6_village   —— 刘家庄·狗儿家（乡居，连宗旧事与劝架都在此）
#   c6_wangchui  —— 荣府后门至凤姐上房一段（后门、周瑞家院、倒厅、影壁、
#                    贾琏院正房台矶、堂屋、东屋、凤姐上房），按既定总览道路
#                    另行设计，不改变既有关系。
#
# 各锚点的命名与坐标都是设计决策，记录在证据表（design/chapter06-evidence.json
# 为可选项，本回省略，由叙述层与底本覆盖）。
# ---------------------------------------------------------------------------

scenes = {
    # 刘家庄 · 狗儿家：院门、院子、里屋（炕）、村口。
    'c6_village': {
        'name': '刘家庄 · 狗儿家',
        'theme': 'garden',
        # 农家小院：南面柴门与土墙，北面两间茅屋（里屋一铺炕、一张方桌），
        # 东边一条出村的小路。院里的东西都是农家的：柴灶、水缸、菜畦、鸡窝。
        'zones': [[5, 18, 26, 15], [9, 9, 16, 10, True, 'ROOM'], [22, 3, 13, 10]],
        'anchors': {
            'home_door': [7, 28],
            'home_yard': [18, 24],
            'home_inner': [16, 13],
            'kang': [19, 11],
            'table': [14, 15],
            'village_exit': [28, 6],
            'village_road': [29, 11],
        },
        'routes': {
            'yard': ['home_door', 'home_yard', 'home_inner'],
            'room': ['home_yard', 'home_inner', 'kang'],
            'leave': ['home_inner', 'home_yard', 'home_door', 'village_exit'],
        },
        'labels': [['狗儿家', 18, 26], ['里屋', 16, 11], ['炕', 19, 9], ['村口', 28, 4]],
        'props': [
            # ── 院子：柴门、土墙、一株老树、一畦菜 ──────────────────────────
            ('flower-gate', *at(7, 29), .62),
            ('garden-tree', *at(25, 21), .94),
            ('garden-tree', *at(9, 26), .84),
            ('garden-rock', *at(29, 25), .70),
            # ── 里屋：茅屋两间，一铺砖炕，一张方桌三条凳，隔扇分出里外 ────────
            ('farm-house', *at(18, 12), .82, 'ROOM'),
            ('plain-kang', *at(19, 11, -16, 14), .72, 'ROOM'),
            ('farm-stove', *at(13, 12, -10, 10), .58, 'ROOM'),
            ('square-table', *at(14, 15, -10, 0), .60, 'ROOM'),
            ('square-stool', *at(14, 15, -96, 18), .70, 'ROOM'),
            ('square-stool', *at(14, 15, 88, 18), .70, 'ROOM'),
            ('square-stool', *at(14, 15, -4, -40), .66, 'ROOM'),
            ('wood-screen', *at(16, 14, -40, 0), .62, 'ROOM'),
        ],
        'walls': [[5, 18, 31, 18], [5, 18, 5, 33], [31, 18, 31, 26], [5, 33, 12, 33],
                  [20, 33, 31, 33]],
        'beds': [[9, 27, 4, 3], [24, 28, 4, 3]],
        'terraces': [[6, 26, 3, 8, 'path']],
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
        # The 5th slot marks an indoor floor; the older `indoor_zones` table still works.
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
        # 第六位给「室内陈设」：它跟着屋子的掀顶一起显隐（visibility=interior），
        # 屋顶还盖着的时候不许在院子边上站着——自鸣钟、多宝格曾有一半露在屋墙外。
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
            # The hall roofs the floor named here: the runtime lifts it as soon as
            # somebody stands on that floor, so the room reads as an interior.
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
    ('c6-qin', '秦氏卧房 · 梦醒余波', 'c5_ningfu'),
    ('c6-grandmother', '贾母处 · 晚膳夜话', 'night'),
    ('c6-village', '刘家庄 · 狗儿家', 'c6_village'),
    ('c6-dawn', '刘家庄 · 次日清晨', 'c6_village'),
    ('c6-capital', '宁荣街 · 荣府大门', 'capital'),
    ('c6-backgate', '荣府后门', 'c6_wangchui'),
    ('c6-zhourui', '周瑞家院 · 引见凤姐', 'c6_wangchui'),
    ('c6-feng', '凤姐院 · 平儿与自鸣钟', 'c6_wangchui'),
    ('c6-audience', '凤姐上房 · 拜见', 'c6_wangchui'),
    ('c6-gift', '凤姐上房 · 周济', 'c6_wangchui'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 6, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c6-qin : 秦氏卧房（衔接第五回末） ============================
section('c6-qin', 'c5_ningfu', '宁国府 · 秦氏卧房', 'bedchamber_door',
        '卻說秦氏因聽見寶玉從夢中喚他的乳名，心中自是納悶', layer='present')
say('C06-001', 'narrator',
    '却说秦氏因听见宝玉从梦中唤他的乳名，心中自是纳闷，又不好细问。',
    '梦醒余波', [show('qin_ke', 'bedchamber_door')])
say('C06-002', 'qin_ke',
    '我的小名这里从没没人知道的，他如何知道，在梦里叫出来？',
    '我的小名这里从没没人知道的',
    [show('baoyu', 'bedchamber'), show('xiren', 'screen_bed')])
say('C06-003', 'narrator',
    '众人忙端上桂圆汤来，呷了两口，遂起身整衣。宝玉满头是汗，渐渐的回过神来。',
    '桂圆汤', [hide('qin_ke')])
say('C06-004', 'narrator',
    '袭人伸手与他系裤带时，只觉冰凉一片沾湿，唬的忙退出手来。',
    '冰凉一片', focus='screen_bed')
say('C06-005', 'narrator',
    '袭人本是个聪明女子，年纪又比宝玉大两岁，近来也大了；见此光景，不觉也羞的红涨了脸面。',
    '袭人羞红')
say('C06-006', 'narrator',
    '仍旧理好衣裳，遂至贾母处来，胡乱吃毕了晚饭。',
    '转往贾母处',
    [hide('baoyu'), hide('xiren')])

# ===== c6-grandmother : 贾母处（复用 night） =========================
section('c6-grandmother', 'night', '荣国府 · 贾母院', 'baoyu_bed',
        '仍舊理好衣裳，遂至賈母處來', layer='present')
say('C06-007', 'narrator',
    '到了贾母处，宝玉、袭人胡乱吃毕了晚饭，各自歇下。',
    '贾母处晚膳', [show('baoyu', 'baoyu_bed'), show('xiren', 'xiren_place')])
say('C06-008', 'narrator',
    '袭人忙趁众奶娘丫鬟不在旁时，另取出一件中衣来与宝玉换上。',
    '另取中衣')
say('C06-009', 'baoyu',
    '好姐姐，千万千万别告诉人。',
    '千万千万别告诉人', focus='night_talk')
say('C06-010', 'narrator',
    '袭人笑道：「你梦见什么故事了？是那里流出来的那些脏东西？」',
    '梦中之事', [show('xiren', 'xiren_place')])
say('C06-011', 'baoyu',
    '一言难尽。',
    '一言难尽', focus='night_talk')
say('C06-012', 'narrator',
    '然后说至警幻所授云雨之情，羞的袭人掩面伏身而笑……遂和宝玉偷试一番，自此宝玉视袭人更比别个不同。',
    '袭人掩面', layer='present')
say('C06-013', 'narrator',
    '按荣府中一宅人合算起来，人口日盛，事务日繁。恰好忽从千里之外，芥豆之微，小小一个人家，因与荣府略有些瓜葛，这便引出一个故事来。',
    '千里之外的故事', focus='outer_door', layer='present')

# ===== c6-village : 刘家庄 · 狗儿家（连宗旧事与劝架） ================
section('c6-village', 'c6_village', '刘家庄 · 狗儿家', 'home_inner',
        '方才所說的這小小之家，乃本地人氏，姓王', layer='reported')
say('C06-014', 'narrator',
    '方才所说的这小小之家，乃本地人氏，姓王，祖上曾作过小小的一个京官，久已告退。',
    '姓王的小小之家', [show('liu_lao', 'home_inner'), show('ban_er', 'kang')])
say('C06-015', 'narrator',
    '因贪慕王家的势利，便连了宗认作侄儿，此后便以侄儿自居，与荣国府也渐渐攀上了亲。',
    '连宗认作侄儿')
say('C06-016', 'narrator',
    '这王家本是金陵一族，与贾府原是一脉；那小王家的，靠着这点渊源，在乡里也算个体面人家。',
    '金陵一脉')
say('C06-017', 'narrator',
    '王家的小姐嫁入荣国府，便是如今的王夫人；这层亲戚，后来竟成了刘姥姥进府的由头。',
    '王夫人这层亲戚')
say('C06-018', 'narrator',
    '目今其祖已故，只有一个儿子，名唤王成，家业凋零，搬出城外原乡去了。',
    '王成家业凋零')
say('C06-019', 'narrator',
    '只有其子，小名狗儿，娶妻刘氏，生了一子小名板儿，一家四口仍以务农为业。',
    '狗儿与板儿')
say('C06-020', 'narrator',
    '狗儿亦生一子小名板儿，嫡妻刘氏又生一女名唤青儿；青儿尚在年幼，只在乡下，本回不随来。',
    '一家四口')
say('C06-021', 'narrator',
    '因这年秋尽冬初，天气冷将上来，狗儿未免心中烦虑，白日间又作些生计。',
    '秋尽冬初', layer='present')
say('C06-022', 'narrator',
    '狗儿遂将岳母刘姥姥接来一处过活，帮着照看外孙儿女。',
    '接来刘姥姥')
say('C06-023', 'narrator',
    '这刘姥姥乃是个积年的老寡妇，膝下又无儿女，只靠两亩薄田度日，如今依着女婿过活。',
    '积年老寡妇')
say('C06-024', 'narrator',
    '因狗儿吃了几杯闷酒，在家闲寻气恼，刘氏也不敢顶撞，只低着头做活。',
    '狗儿闲寻气恼', [show('liu_lao', 'home_inner'), show('ban_er', 'kang')])
say('C06-025', 'narrator',
    '刘姥姥看不过，乃劝女婿道：「姑爷，你别嗔着我多嘴。」',
    '刘姥姥劝架')
say('C06-026', 'liu_lao',
    '姑爷，你别嗔着我多嘴。咱们庄稼人，守着这两亩薄田，也饿不死，何苦自寻烦恼。',
    '守着薄田饿不死')
say('C06-027', 'liu_lao',
    '这长安城中，遍地都是钱，只可惜没人会去拿去罢了。',
    '遍地都是钱')
say('C06-028', 'liu_lao',
    '如今这荣国府，正是烈火烹油、鲜花着锦的时节；咱们沾着点边儿，还怕没碗饭吃？',
    '荣国府的时节')
say('C06-029', 'narrator',
    '刘姥姥将那长安城中的繁华，与荣国府的势派，细细说了一遍，狗儿只是冷笑。',
    '细说繁华')
say('C06-030', 'narrator',
    '狗儿听了，便急道：「你老只会炕头上混说，难道叫我打劫偷去不成？」',
    '狗儿冷笑', offscreen=True)
say('C06-031', 'liu_lao',
    '谁叫你偷去呢？到底有多少人，也该想法儿去比咱们强的人家走动走动，不然那银子钱自己跑到咱家来不成？',
    '想法儿走动')
say('C06-032', 'narrator',
    '狗儿冷笑道：「有法儿还等到这会子呢。我又没有收税的亲戚，作官的朋友，有什么法儿？」',
    '狗儿泄气', offscreen=True)
say('C06-033', 'liu_lao',
    '这倒不然。谋事在人，成事在天。咱们如今有这样的机会，我倒替你们想出一个机会来。',
    '谋事在人，成事在天')
say('C06-034', 'narrator',
    '当日你们原是和金陵王家连过宗的，二十年前，王家的二小姐——如今是荣国府的二太太——还未出阁时，我就见过一面。',
    '金陵王家连宗', layer='reported')
say('C06-035', 'narrator',
    '那时王家的二小姐行事爽利，待下人宽厚；刘姥姥当年曾随人进过一回府，远远的见过这位姑娘。',
    '远见二小姐')
say('C06-036', 'narrator',
    '若是他发一点好心，拔一根寒毛比咱们的腰还粗呢。',
    '拔根寒毛比腰粗')
say('C06-037', 'narrator',
    '刘氏一旁接口道：「你老虽说的是，但只你我这样个嘴脸，怎样好到他门上去的。」',
    '刘氏接口', offscreen=True)
say('C06-038', 'narrator',
    '狗儿利名心最重，听了这话便有些心动，道：「况且当年你又见过这姑太太一次，何不你老人家明日就走一趟，先试试风头再说。」',
    '狗儿心动', offscreen=True)
say('C06-039', 'liu_lao',
    '我倒没的能为，只是当年见过太太一面，明日走一趟也使得；成不成，不过碰碰运气。',
    '刘姥姥应承')
say('C06-040', 'liu_lao',
    '侯门深似海，我是个什么东西。倒还是舍着我这付老脸去碰一碰，大不了讨个没趣回来。',
    '侯门深似海')
say('C06-041', 'narrator',
    '刘姥姥打定主意，明日便去荣府走一遭，一则瞧瞧姑太太，二则碰碰运气。',
    '打定主意')
say('C06-042', 'narrator',
    '狗儿道：「你竟带了外孙子板儿，先去找陪房周瑞——这周瑞先时曾和我父亲交过一件事，我们极好的。」',
    '去找周瑞', offscreen=True, focus='kang')
say('C06-043', 'narrator',
    '说毕，大家笑了一回。当晚计议已定，只等明日天明起身。',
    '当晚计议已定', [hide('liu_lao'), hide('ban_er')])

# ===== c6-dawn : 次日清晨 ============================================
section('c6-dawn', 'c6_village', '刘家庄 · 村口', 'village_exit',
        '次日天未明，劉姥姥便起來梳洗了', layer='present')
say('C06-044', 'narrator',
    '次日天未明，刘姥姥便起来梳洗了，又悄没声的收拾了几样乡下土产。',
    '天未明起身', [show('liu_lao', 'home_inner'), show('ban_er', 'kang')])
say('C06-045', 'liu_lao',
    '板儿，你今日跟我去城里逛逛，可别淘气，见了人家规矩些。',
    '带板儿进城', focus='kang')
say('C06-046', 'narrator',
    '又将板儿教训了几句，祖孙两个收拾停当，出了村口望城里去了。',
    '出村口', [move('liu_lao', 'home_inner', 'home_yard', 'village_exit'),
                move('ban_er', 'kang', 'home_yard', 'village_exit')])

# ===== c6-capital : 宁荣街 · 荣府大门 ================================
section('c6-capital', 'capital', '京城 · 宁荣街', 'rong_gate',
        '於是劉姥姥帶他進城，找至宁荣街', layer='present')
say('C06-047', 'narrator',
    '于是刘姥姥带他进城，找至宁荣街。来至荣府大门石狮子前，只见簇簇轿马，刘姥姥便不敢过去。',
    '荣府大门石狮子', [show('liu_lao', 'rong_gate'), show('ban_er', 'rong_gate')])
say('C06-048', 'narrator',
    '刘姥姥只远远的望着那一对蹲狮与朱轮华盖，脚下挪不动步，拉了板儿在街边站着。',
    '立在街边', focus='rong_gate')
say('C06-049', 'narrator',
    '然后蹭到角门前。只见几个挺胸叠肚指手画脚的人，坐在大板凳上，说东谈西，指手画脚。',
    '蹭到角门', [move('liu_lao', 'rong_gate', 'west_corner'), move('ban_er', 'rong_gate', 'west_corner')])
say('C06-050', 'narrator',
    '那些人见他祖孙两个土头土脑的，都只当没看见，依旧说笑。',
    '门上的人', focus='west_corner')
say('C06-051', 'narrator',
    '刘姥姥只得蹭上来问：「太爷们纳福。」',
    '上前问安', [show('liu_lao', 'west_corner')])
say('C06-052', 'narrator',
    '刘姥姥道：「我找太太的陪房周大爷的，烦那位太爷替我请他老出来。」',
    '找周大爷', focus='west_corner')
say('C06-053', 'narrator',
    '那人道：「周大爷已往南边去了。他在后一带住着，他娘子却在家。你要找时，从这边绕到后街上后门上去问就是了。」',
    '门人指路', offscreen=True,
    actions=[move('liu_lao', 'west_corner', 'outside'), move('ban_er', 'west_corner', 'outside')])

# ===== c6-backgate : 荣府后门 =========================================
section('c6-backgate', 'c6_wangchui', '荣府后门', 'back_gate',
        '劉姥姥聽了謝過，遂攜了板兒，繞到後門上', layer='present')
say('C06-054', 'narrator',
    '刘姥姥听了谢过，遂携了板儿，绕到后门上。走了半日，方到后街后门。',
    '绕到后门', [show('liu_lao', 'back_gate'), show('ban_er', 'back_gate')])
say('C06-055', 'narrator',
    '后门一带僻静些，却也常有府里的人出入；刘姥姥只在不远处张望，不敢冒然上前。',
    '后门张望')
say('C06-056', 'narrator',
    '只见门前歇着些生意担子，卖吃食的、卖杂货的都有；闹吵吵三二十个小孩子在那里厮闹，好不热闹。',
    '后门市井', focus='market')

# ===== c6-zhourui : 周瑞家院 =========================================
section('c6-zhourui', 'c6_wangchui', '周瑞家院', 'zhou_court',
        '劉姥姥便拉住一個道：「我問哥兒一聲」', layer='present')
say('C06-057', 'narrator',
    '刘姥姥便拉住一个道：「我问哥儿一声，有个周大娘可在家么？」那孩子道：「你跟我来。」',
    '拉住孩子问', [move('liu_lao', 'back_gate', 'market', 'zhou_court'),
                    move('ban_er', 'back_gate', 'market', 'zhou_court')])
say('C06-058', 'narrator',
    '至一院墙边，指与刘姥姥道：「这就是他家。」又叫道：「周大娘，有个老奶奶来找你呢。」',
    '指与周家', focus='zhou_court')
say('C06-059', 'zhou_rui',
    '是那位？……哟，刘姥姥，你好呀！你说说是几年，我就忘了。请家里来坐罢。',
    '周瑞家的迎出', [show('zhou_rui', 'zhou_court')])
say('C06-060', 'liu_lao',
    '你老是贵人多忘事，那里还记得我们呢。说着，来至房中。',
    '来至房中',
    [move('liu_lao', 'zhou_court', 'zhou_room'), move('ban_er', 'zhou_court', 'zhou_room'),
     move('zhou_rui', 'zhou_court', 'zhou_room')])
say('C06-061', 'narrator',
    '周瑞家的命雇的小丫头倒上茶来吃着，让刘姥姥上炕坐。',
    '倒茶让坐', focus='zhou_room')
say('C06-062', 'zhou_rui',
    '姥姥今日还是路过，还是特来的？',
    '问来意')
say('C06-063', 'liu_lao',
    '原是特来瞧瞧嫂子你，二则也请请姑太太的安；若是方便，给周大娘请个安。',
    '特来请安')
say('C06-064', 'narrator',
    '刘姥姥便将来意明说了几分，只不曾说那借银的话，先探着周瑞家的口气。',
    '探口气')
say('C06-065', 'narrator',
    '只因昔年他丈夫周瑞争买田地一事，其中多得狗儿之父的力量，周瑞家的一直记着这份情。',
    '昔日的人情', layer='reported', actions=[show('zhou_rui', 'zhou_room')])
say('C06-066', 'narrator',
    '今见刘姥姥如此而来，心中难却其意，便存了周全她的心。',
    '难却其意')
say('C06-067', 'zhou_rui',
    '姥姥你放心。大远的诚心诚意来了，岂有个不教你见个真佛去的呢。',
    '见个真佛去')
say('C06-068', 'zhou_rui',
    '我就破个例，给你通个信去，领你去见琏二奶奶。',
    '破例通个信')
say('C06-069', 'zhou_rui',
    '如今太太竟不大管事，都是琏二奶奶管家了。这琏二奶奶，便是当日大舅老爷的女儿，小名凤哥儿的。',
    '点明凤姐身份')
say('C06-070', 'narrator',
    '周瑞家的又道：「这凤姑娘今年大不过二十岁罢，少说也有一万个心眼子，行事比太太还利落些。」',
    '凤姐的心眼')
say('C06-071', 'liu_lao',
    '原来是他！怪道呢，我当日就说他不差呢。既有这层缘分，便更该去见一见。',
    '原是凤哥儿')
say('C06-072', 'zhou_rui',
    '今儿宁可不会太太，倒要见他一面，才不枉这里来一遭。',
    '定要见凤姐')
say('C06-073', 'liu_lao',
    '阿弥陀佛！全仗嫂子方便了。',
    '全仗嫂子')
say('C06-074', 'zhou_rui',
    '与人方便，自己方便。不过用我说一句话罢了，害着我什么。叫小丫头到倒厅上悄悄的打听打听。',
    '与人方便自己方便')
say('C06-075', 'narrator',
    '周瑞家的便命小丫头到倒厅上去，悄悄的打听凤姐如今在何处。',
    '命丫头打听', [move('zhou_rui', 'zhou_room', 'daoting')])

# ===== c6-feng : 凤姐院 · 平儿与自鸣钟 ============================
section('c6-feng', 'c6_wangchui', '凤姐院 · 堂屋', 'platform',
        '小丫頭回來說：「老太太屋裏已擺完了飯了」', layer='present')
say('C06-076', 'narrator',
    '小丫头回来说：「老太太屋里已摆完了饭了，二奶奶在太太屋里呢。」',
    '报信', [show('zhou_rui', 'daoting'), show('liu_lao', 'daoting'), show('ban_er', 'daoting')])
say('C06-077', 'zhou_rui',
    '快走，快走。这一下来他吃饭是个空子，咱们先赶着去。',
    '赶着空子去', [move('zhou_rui', 'daoting', 'yingbi', 'platform'),
                    move('liu_lao', 'daoting', 'yingbi', 'platform'),
                    move('ban_er', 'daoting', 'yingbi', 'platform')])
say('C06-078', 'narrator',
    '随着周瑞家的，逶迤往贾琏的住处来，穿过影壁，进了院门。',
    '过影壁进院', focus='yingbi')
say('C06-079', 'narrator',
    '先到了倒厅，周瑞家的将刘姥姥安插在那里略等一等，自己先过了影壁，进了院门去通禀。',
    '安插倒厅', [move('zhou_rui', 'platform'), show('liu_lao', 'daoting'), show('ban_er', 'daoting')])
say('C06-080', 'narrator',
    '先找着凤姐的一个心腹通房大丫头名唤平儿的。周瑞家的笑道：「平姑娘，这位老奶奶是乡下来的亲戚。」',
    '先见平儿', [show('zhou_rui', 'platform'), show('ping_er', 'platform')])
say('C06-081', 'ping_er',
    '周姐姐来了。这位老奶奶是……？既来了，且随我进来坐着罢。',
    '平儿相问', focus='platform')
say('C06-082', 'narrator',
    '平儿听了，便作了主意：「叫他们进来，先在这里坐着就是了。」',
    '平儿作主', [move('liu_lao', 'daoting', 'platform'), move('ban_er', 'daoting', 'platform')])
say('C06-083', 'narrator',
    '上了正房台矶，小丫头打起猩红毡帘，才入堂屋，满屋中之物都耀眼争光的，使人头悬目眩。',
    '满屋耀眼争光', [move('liu_lao', 'platform', 'hall'), move('ban_er', 'platform', 'hall'),
                      show('ping_er', 'hall')])
say('C06-084', 'narrator',
    '刘姥姥此时只有点头咂嘴念佛而已，不敢轻易落座。',
    '点头念佛', focus='hall')
say('C06-085', 'narrator',
    '于是来至东边这间屋内，乃是贾琏的女儿大姐儿睡觉之所。平儿站在炕沿边，打量了刘姥姥两眼。',
    '东屋大姐儿', [move('liu_lao', 'hall', 'east_room'), move('ban_er', 'hall', 'east_room'),
                     move('ping_er', 'hall', 'east_room')])
say('C06-086', 'ping_er',
    '你便是刘姥姥？且在这里坐着，奶奶下来了便请你们进去。板儿也来，别乱跑。',
    '平儿安置', focus='east_room')
say('C06-087', 'narrator',
    '刘姥姥见平儿遍身绫罗，插金带银，花容玉貌的，便当是凤姐儿了，忙要下拜。',
    '误认平儿为凤姐', focus='east_room')
say('C06-088', 'liu_lao',
    '这位奶奶好生齐整，敢是凤姑娘不成？老身这厢有礼了。',
    '敢是凤姑娘')
say('C06-089', 'narrator',
    '刘姥姥只听见咯当咯当的响声，忽见堂屋中柱子上挂着一个匣子，底下又坠着一个秤砣般一物，却不住的乱幌。',
    '自鸣钟', [move('liu_lao', 'east_room', 'hall'), move('ban_er', 'east_room', 'hall'),
                 move('ping_er', 'east_room', 'hall')])
say('C06-090', 'narrator',
    '不一时，只见小丫头子们齐乱跑，说：「奶奶下来了。」',
    '奶奶下来了', focus='hall')
say('C06-091', 'narrator',
    '正呆时，只听得当的一声，又若金钟铜磬一般，不防倒唬了一跳。原来这就是府里的自鸣钟。',
    '当的一声', focus='hall')
say('C06-092', 'narrator',
    '刘姥姥心中想着：「这是什么东西，会自己响？」只不敢多问，依旧呆呆的望着。',
    '自思自叹')
say('C06-093', 'zhou_rui',
    '周瑞家的与平儿忙起身，命刘姥姥「只管等着，是时候我们来请你」。',
    '且等着', [show('zhou_rui', 'hall')])
say('C06-094', 'narrator',
    '刘姥姥屏声侧耳默候。只听远远有人笑声，约有一二十妇人，衣裙窸窣，渐入堂屋。',
    '远远人笑', focus='hall')
say('C06-095', 'narrator',
    '只听得那边说了声「摆饭」，渐渐的人才散出，院中略静了些。',
    '摆饭人散')
say('C06-096', 'narrator',
    '忽见二人抬了一张炕桌来，放在这边炕上，桌上碗盘森列，鸡鸭鱼肉摆了一桌。',
    '抬上炕桌', [move('liu_lao', 'hall', 'east_room'), move('ban_er', 'hall', 'east_room'),
                  show('ping_er', 'east_room')])
say('C06-097', 'liu_lao',
    '板儿，你瞧这肉，可还吃不得？今日可开了眼了。',
    '板儿看肉', focus='east_room')
say('C06-098', 'narrator',
    '板儿一见了，便吵着要肉吃，刘姥姥一巴掌打了他去，低声喝他安分。',
    '板儿闹食', [move('liu_lao', 'east_room', 'hall'), move('ban_er', 'east_room', 'hall'),
                   show('zhou_rui', 'hall'), show('ping_er', 'hall')])

# ===== c6-audience : 凤姐上房 · 拜见 =================================
section('c6-audience', 'c6_wangchui', '凤姐上房', 'feng_room',
        '忽見周瑞家的笑嘻嘻走過來，招手兒叫他', layer='present')
say('C06-099', 'narrator',
    '忽见周瑞家的笑嘻嘻走过来，招手儿叫他：「快来，奶奶这会儿闲了。」刘姥姥方随了进去。',
    '招手叫进', [move('liu_lao', 'hall', 'feng_room'), move('ban_er', 'hall', 'feng_room'),
                   move('zhou_rui', 'hall', 'feng_room')])
say('C06-100', 'narrator',
    '只见门外鐡铜钩上悬着大红撒花软帘，南窗下是炕。那凤姐儿家常带着秋板貂鼠昭君套，围着攒珠勒子，穿着桃红撒花袄、石青刻丝灰鼠披风、大红洋绉银鼠皮裙。',
    '凤姐服饰', [show('feng', 'feng_room')])
say('C06-101', 'feng',
    '凤姐也不接茶，也不抬头，只管拨手炉内的灰，慢慢的问道：「怎么还不请进来？」',
    '拨手炉问', focus='feng_room')
say('C06-102', 'liu_lao',
    '刘姥姥在地下已是拜了数拜，问姑奶奶安。',
    '拜见凤姐')
say('C06-103', 'feng',
    '周姐姐，快搀起来，别拜罢，请坐。我年轻，不大认得，可也不知是什么辈数，不敢称呼。',
    '搀起让坐', [show('zhou_rui', 'feng_room')])
say('C06-104', 'narrator',
    '板儿便躲在背后，百般的哄他出来作揖，他死也不肯，只拿眼瞅着桌上的吃食。',
    '板儿不肯作揖', [show('ban_er', 'feng_room')])
say('C06-105', 'feng',
    '亲戚们不大走动，都疏远了。知道的呢，说你们弃厌我们，不肯常来；不知道的，还只当我们眼里没人似的。',
    '亲戚疏远了')
say('C06-106', 'liu_lao',
    '我们家道艰难，走不起；来了，也是给姑奶奶打嘴。',
    '家道艰难')
say('C06-107', 'liu_lao',
    '俗话说的好，『朝廷还有三门子穷亲戚』呢，何况你我。老身今日可沾了姑奶奶的光了。',
    '三门子穷亲戚')
say('C06-108', 'feng',
    '这话没的叫人恶心。俗语说，『朝廷还有三门子穷亲戚』呢，何况你我。你既是头一遭来，我岂有不照应的。',
    '凤姐回话')
say('C06-109', 'feng',
    '凤姐又问周瑞家的：「回了太太了没有？」周瑞家的道未回，凤姐道：「你去瞧瞧，要是有人有事就罢，得闲儿呢就回。」',
    '问回太太', [show('zhou_rui', 'feng_room')])
say('C06-110', 'zhou_rui',
    '周瑞家的答应着，自去回王夫人了。',
    '周瑞家去回', [hide('zhou_rui')])
say('C06-111', 'feng',
    '这里凤姐叫人抓些果子与板儿吃。板儿见了果子，方不吵闹。',
    '给板儿果子', [show('ban_er', 'feng_room')])
say('C06-112', 'narrator',
    '就有家下许多媳妇管事的来回话。平儿回了，凤姐道：「我这里陪客呢，晚上再来回。」',
    '管家媳妇回话', [show('ping_er', 'feng_room')])
say('C06-113', 'feng',
    '平儿，你先照应着这些回事的，我陪客说话。',
    '凤姐吩咐平儿', focus='feng_room')
say('C06-114', 'zhou_rui',
    '周瑞家的回来，向凤姐道：「太太说了，今日不得闲，二奶奶陪着便一样。有什么事，只管告诉二奶奶，都是一样的。」一面说，一面递眼色与刘姥姥。',
    '王夫人不现身', [show('zhou_rui', 'feng_room')])
say('C06-115', 'narrator',
    '刘姥姥会意，知道太太是不见的了，便把心一横，准备开口。',
    '刘姥姥会意', focus='feng_room')
say('C06-116', 'liu_lao',
    '刘姥姥会意，未语先飞红的脸，欲待不说，又舍不得到口的钱，忍耻说道：「论理今儿初次见姑奶奶，却不该说……」',
    '欲说还休', focus='feng_room')
say('C06-117', 'liu_lao',
    '只是大远的奔了你老这里来，也少不的说了。',
    '少不的说了')
say('C06-118', 'narrator',
    '刚说到这里，只听二门上小厮们回说：「东府里的小大爷进来了。」凤姐忙止刘姥姥：「不必说了。」',
    '东府小大爷来', focus='feng_room')
say('C06-119', 'jia_rong',
    '只听一路靴子脚响，进来了一个十七八岁的少年，面目清秀，身材俊俏，轻裘宝带，美服华冠。',
    '贾蓉登场', [show('jia_rong', 'feng_room')])
say('C06-120', 'narrator',
    '刘姥姥此时坐不是，立不是，藏没处藏，只把眼皮低着，不敢抬头。',
    '刘姥姥失措', focus='feng_room')

# ===== c6-gift : 凤姐上房 · 周济 ====================================
section('c6-gift', 'c6_wangchui', '凤姐上房', 'feng_room',
        '鳳姐笑道：「你只管坐著，這是我侄兒」', layer='present')
say('C06-121', 'feng',
    '你只管坐着，这是我侄儿。刘姥姥方扭扭捏捏在炕沿上坐了。',
    '这是我侄儿', [show('liu_lao', 'feng_room'), show('jia_rong', 'feng_room')])
say('C06-122', 'jia_rong',
    '我父亲打发我来求婶子，说那架玻璃炕屏要略摆一摆，明日就送过来。',
    '贾蓉借炕屏', focus='feng_room')
say('C06-123', 'narrator',
    '凤姐道：「说迟了一日，昨儿已经给了人了。」贾蓉嘻嘻的笑着，在炕沿上半跪道：「婶子若不借，又说我不会说话了，又挨一顿好打呢。」',
    '半跪求情', [show('feng', 'feng_room')])
say('C06-124', 'jia_rong',
    '婶子若不借，我回去挨一顿好打呢。好婶子，只借这一回。',
    '贾蓉撒娇')
say('C06-125', 'feng',
    '凤姐笑道：「也没见你们，王家的东西都是好的不成？……若碰一点儿，你可仔细你的皮！」',
    '凤姐驳回')
say('C06-126', 'feng',
    '因命平儿拿了楼房的钥匙，传几个妥当人抬去。贾蓉喜的眉开眼笑，千恩万谢的去了。',
    '到底借出', [show('ping_er', 'feng_room'), hide('jia_rong')])
say('C06-127', 'feng',
    '这里凤姐忽又想起一事来，便向窗外叫：「蓉哥回来。」',
    '凤姐叫回', [show('jia_rong', 'feng_room')])
say('C06-128', 'narrator',
    '贾蓉忙回来，垂手侍立，听婶子吩咐。',
    '贾蓉垂手', focus='feng_room')
say('C06-129', 'feng',
    '凤姐只管慢慢的吃茶，出了半日的神，又笑道：「罢了，你且去罢。」贾蓉答应着退下。',
    '出了半日神', [hide('jia_rong')])
say('C06-130', 'liu_lao',
    '今日我带了你侄儿来，也不为别的，只因他老子娘在家里，连吃的都没有，天又冷了……',
    '明言来意', [show('liu_lao', 'feng_room')])
say('C06-131', 'narrator',
    '刘姥姥又推板儿道：「你那爹在家怎么教你的？快见过姑奶奶，讨个赏。」',
    '推板儿见礼', [show('ban_er', 'feng_room')])
say('C06-132', 'liu_lao',
    '板儿，快磕头，姑奶奶疼你，赏你果子吃。',
    '板儿磕头')
say('C06-133', 'ban_er',
    '板儿只扭着不肯，被刘姥姥逼着，胡乱作了个揖。',
    '板儿作揖', focus='feng_room')
say('C06-134', 'feng',
    '凤姐道：「不必说了，我知道了。」因问周瑞家的：「这姥姥不知可用了早饭没有？」',
    '凤姐问饭', [show('zhou_rui', 'feng_room')])
say('C06-135', 'zhou_rui',
    '周瑞家的道：「倒是没用呢，奶奶，我这就传饭去。」',
    '传饭去', [hide('zhou_rui')])
say('C06-136', 'narrator',
    '一时周瑞家的传了一桌客饭来，摆在东边屋内，过来带了刘姥姥和板儿过去吃饭。',
    '传客饭', [move('liu_lao', 'feng_room', 'east_room'), move('ban_er', 'feng_room', 'east_room')])
say('C06-137', 'feng',
    '凤姐说：「周姐姐，好生让着些儿，我不能陪了。」',
    '凤姐让饭', [show('feng', 'feng_room')])
say('C06-138', 'feng',
    '又叫过周瑞家的去，问他才回了太太，说了些什么。',
    '问回话', [show('zhou_rui', 'feng_room')])
say('C06-139', 'zhou_rui',
    '周瑞家的道：「太太说，既是一家子，我如何连影儿也不知道。奶奶只管做主就是了。」',
    '太太原话', focus='feng_room')
say('C06-140', 'narrator',
    '凤姐听了，也不说别的，只微微一笑，心里已有了主意。',
    '凤姐有主')
say('C06-141', 'liu_lao',
    '说话时，刘姥姥已吃毕了饭，拉了板儿过来，抹舌咂嘴的道谢。',
    '饭毕道谢', [move('liu_lao', 'east_room', 'feng_room'), move('ban_er', 'east_room', 'feng_room')])
say('C06-142', 'feng',
    '凤姐笑道：「且请坐下，听我告诉你老人家。今儿你既老远的来了，又是头一次见我张口，怎好叫你空回去呢。」',
    '凤姐周济', [show('feng', 'feng_room')])
say('C06-143', 'narrator',
    '凤姐将家中如何艰难，如何拮据，说了一篇，却满口应承下来。',
    '说艰难应承')
say('C06-144', 'feng',
    '你既来了，我岂有不周济你的理。只是我屋里也得顾着脸面，不能太过。',
    '岂有不周济')
say('C06-145', 'feng',
    '可巧昨儿太太给我的丫头们做衣裳的二十两银子，我还没动呢，你若不嫌少，就暂且先拿了去罢。',
    '二十两银子', focus='feng_room')
say('C06-146', 'narrator',
    '凤姐说着，便命平儿去取那包银子。',
    '命平儿取银', [show('ping_er', 'feng_room')])
say('C06-147', 'liu_lao',
    '瘦死的骆驼比马大。你老拔根寒毛比我们的腰还粗呢！',
    '拔根寒毛比腰粗', focus='feng_room')
say('C06-148', 'narrator',
    '刘姥姥只管这么说，却不知轻重，把个平儿都逗笑了。',
    '刘姥姥粗鄙')
say('C06-149', 'feng',
    '周瑞家的见他说的粗鄙，只管使眼色止他。凤姐看见，笑而不睬，并不着恼。',
    '凤姐笑而不睬', [show('zhou_rui', 'feng_room')])
say('C06-150', 'feng',
    '只命平儿把昨儿那包银子拿来，再拿一吊钱来……「这是二十两银子，暂且给这孩子做件冬衣罢。」',
    '银子加一吊钱', [show('ping_er', 'feng_room')])
say('C06-151', 'ping_er',
    '平儿答应着，去取了银子与钱来，用红封皮封好。',
    '平儿取银钱', focus='feng_room')
say('C06-152', 'narrator',
    '平儿将银子与钱交与刘姥姥，又悄悄的另抓了一把果子与板儿。',
    '交与银钱', [show('liu_lao', 'feng_room'), show('ban_er', 'feng_room')])
say('C06-153', 'feng',
    '这钱雇车坐罢。改日无事，只管来逛逛，亲戚们原该走动。一面说，一面就站了起来。',
    '送客', [show('feng', 'feng_room')])
say('C06-154', 'narrator',
    '刘姥姥只管千恩万谢的，拿了银子钱，随了周瑞家的来至外面。',
    '千恩万谢', [move('liu_lao', 'feng_room', 'platform', 'daoting', 'zhou_court', 'back_gate'),
                   move('ban_er', 'feng_room', 'platform', 'daoting', 'zhou_court', 'back_gate'),
                   show('zhou_rui', 'back_gate'), hide('feng'), hide('ping_er')])
say('C06-155', 'zhou_rui',
    '周瑞家的道：「我的娘啊！你见了他怎么倒不会说了？开口就是『你侄儿』——蓉大爷才是他的正经侄儿呢，你倒认起亲来了。」',
    '周瑞家数落', [show('zhou_rui', 'back_gate')])
say('C06-156', 'liu_lao',
    '我老拙嘴笨，原不会说话，嫂子别笑话。今日多亏了你周全。',
    '刘姥姥赔笑')
say('C06-157', 'narrator',
    '二人说着，又到周瑞家坐了片时。刘姥姥便要留下一块银子与周瑞家孩子们买果子吃。',
    '到周家坐', [move('liu_lao', 'back_gate', 'zhou_court'), move('ban_er', 'back_gate', 'zhou_court'),
                   show('zhou_rui', 'zhou_court')])
say('C06-158', 'liu_lao',
    '这点银子，给孩子们买果子吃罢，老身心领了嫂子的情。',
    '留银买果', focus='zhou_court')
say('C06-159', 'zhou_rui',
    '周瑞家的如何放在眼里，执意不肯。刘姥姥感谢不尽，只得收回。',
    '周瑞家不肯', [hide('zhou_rui')])
say('C06-160', 'narrator',
    '刘姥姥仍从后门去了，祖孙两个欢天喜地，雇了车回乡。',
    '仍从后门去', [move('liu_lao', 'zhou_court', 'back_gate'), move('ban_er', 'zhou_court', 'back_gate')])
say('C06-161', 'narrator',
    '得意浓时易接济，受恩深处胜亲朋。',
    '收束诗', focus='back_gate')


def build_story():
    ids = [s['id'] for s in steps]
    assert len(ids) == len(set(ids)), 'duplicate node id'
    for s in steps:
        assert s['chapter'] in section_titles, f"{s['id']}: unknown section"
    (ROOT / 'design/chapter06-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    # first node of each section
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 6}
                for sid, title, scene in SECTIONS]
    (ROOT / 'design/chapter06-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    BACKUP.mkdir(parents=True, exist_ok=True)
    counts = {}
    for key, scene in scenes.items():
        counts[key] = build_map(key, scene)
    n_steps, n_sections = build_story()
    print('maps  :', json.dumps(counts, ensure_ascii=False))
    print('story : design/chapter06-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter06-sections.json  %d sections' % n_sections)
