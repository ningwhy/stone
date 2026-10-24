#!/usr/bin/env python3
"""Build chapter-four maps and its full playable script.

Chapter four owns this generator; nothing here touches write_prequel.py.

Outputs (printed at the end):
  maps/c4_yamen.tmj          new stage: court hall + the chamber behind the bench
  maps/c4_lixiang.tmj        new stage: the pear-fragrance court of the north-east corner
  maps/wang.tmj              existing stage, gains one li_room anchor (backup made first)
  design/chapter04-story.json      nodes C04-001..C04-076
  design/chapter04-sections.json   nine sections: c4-lady .. c4-pear

Usage: python3 scripts/build_chapter04.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / 'artifacts/backups/2026-10-24-chapter04'

scenes = {
    'c4_yamen': {
        'name': '应天府 · 刑堂与退堂密室',
        'theme': 'formal',
        # Two playable floors: the open court to the south, the private chamber behind the bench.
        'zones': [[8, 18, 24, 14], [12, 6, 16, 12]],
        'anchors': {
            'plaintiff': [12, 28],
            'hall_center': [19, 27],
            'bench': [19, 22],
            'side_door': [19, 18],
            'chamber_host': [19, 9],
            'chamber_seat': [16, 11],
        },
        # Split corridors: the court line and the withdrawal line, so no shortcut appears
        # between the plaintiff's place and the chamber.
        'routes': {
            'court': ['plaintiff', 'hall_center', 'bench'],
            'chamber': ['bench', 'side_door', 'chamber_host'],
            'seat': ['chamber_host', 'chamber_seat'],
        },
        'labels': [['应天府大堂', 19, 26], ['退堂密室', 19, 8]],
        'props': [
            ('main-hall', 20, 11, 1.0),
            ('tea-table', 19, 22, 1.0),
            ('tea-table', 19, 10, .7),
            ('wood-screen', 24, 12, .8),
        ],
    },
    'c4_lixiang': {
        'name': '荣府东北角 · 梨香院',
        'theme': 'garden',
        # A small walled court: the street gate to the south-east, the front hall to the
        # north-west, the back rooms behind it, and the south-west corner gate that leads
        # to the lane running to Wang's quarters (only the relative position is designed).
        'zones': [[9, 20, 22, 12], [11, 8, 18, 12], [20, 16, 8, 6]],
        'anchors': {
            'street_gate': [28, 24],
            'court_center': [19, 25],
            'front_hall': [16, 12],
            'back_rooms': [22, 10],
            'lane_gate': [11, 22],
        },
        'routes': {
            'court': ['street_gate', 'court_center', 'front_hall'],
            'back': ['front_hall', 'back_rooms'],
            'lane': ['lane_gate', 'court_center'],
        },
        'labels': [['梨香院', 19, 22], ['前厅', 16, 10], ['后舍', 22, 8], ['通街门', 28, 24],
                   ['西南角门', 11, 22]],
        'props': [
            ('main-hall', 16, 10, .85),
            ('bamboo-gate', 28, 24, .6),
            ('wood-screen', 22, 11, .7),
            ('garden-tree', 11, 21, 1.0),
            ('garden-tree', 28, 21, 1.05),
            ('garden-rock', 26, 19, .9),
            ('tea-table', 17, 13, .6),
        ],
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

    zones = [obj(f'A{i} {scene["name"]}', c, r, width=w * 64, height=h * 64)
             for i, (c, r, w, h) in enumerate(scene['zones'])]
    anchors = [obj(n, c + .5, r + .5, point=True) for n, (c, r) in scene['anchors'].items()]
    paths = [obj('动线 %s' % rid, 0, 0, properties=[
        {'name': 'route_id', 'value': rid, 'type': 'string'},
        {'name': 'anchor_ids', 'value': ','.join(names), 'type': 'string'},
    ]) for rid, names in scene['routes'].items()]

    art = []
    footprints = []
    for asset, c, r, scale in scene['props']:
        if asset not in assets:
            continue
        a = assets[asset]
        x = (c - r) * 64 + (a['width'] / 2 - a['anchor'][0]) * scale
        y = (c + r + 1) * 32 + (a['height'] - a['anchor'][1]) * scale
        art.append(obj(asset, 0, 0, x=y + x / 2, y=y - x / 2, gid=gids[asset],
                       width=a['width'] * scale, height=a['height'] * scale, type='art',
                       properties=[
                           {'name': 'asset', 'value': asset, 'type': 'string'},
                           {'name': 'visibility',
                            'value': 'exterior' if asset in ('main-hall', 'rongxi-hall') else 'always',
                            'type': 'string'}]))
        if asset in ('wood-screen', 'tea-table', 'garden-rock') and [c, r] not in list(scene['anchors'].values()):
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
                       {'name': 'theme', 'type': 'string', 'value': scene['theme']}],
    }
    (ROOT / f'maps/{key}.tmj').write_text(json.dumps(tmj, ensure_ascii=False, indent=2) + '\n')
    return len(scene['anchors'])


# ---- mutate existing wang map: one extra anchor for Li Wan's room -----------------------
def add_wang_anchor():
    path = ROOT / 'maps/wang.tmj'
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, BACKUP / 'wang.tmj')
    d = json.loads(path.read_text())
    for layer in d['layers']:
        if layer['name'] != 'Anchors':
            continue
        if any(o['name'] == 'li_room' for o in layer['objects']):
            break
        layer['objects'].append(make_obj('li_room', 24 + .5, 8 + .5, point=True,
                                         id=d['nextobjectid']))
        d['nextobjectid'] += 1
        break
    path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


# ---- story --------------------------------------------------------------------------------
chapters = [
    ('c4-lady', '王夫人处 · 寡嫂房中', 'wang'),
    ('c4-court', '应天府 · 争买一婢', 'c4_yamen'),
    ('c4-chamber', '退堂密室 · 葫芦庙旧识', 'c4_yamen'),
    ('c4-protect', '密室 · 护官符', 'c4_yamen'),
    ('c4-truth', '密室 · 英莲身世', 'c4_yamen'),
    ('c4-judge', '密室 · 徇情枉法', 'c4_yamen'),
    ('c4-xue', '入京路上 · 薛家母子', 'capital'),
    ('c4-hall', '荣禧堂 · 姨太太来京', 'central'),
    ('c4-pear', '梨香院 · 安顿新居', 'c4_lixiang'),
]
steps = []
current = {}
section_titles = {a: b for a, b, c in chapters}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 4, 'paragraphLead': lead, 'textKind': 'adaptation',
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


def roof(v):
    return {'type': 'roof', 'visible': v}


# ===== c4-lady : Wang's quarters and Li Wan's room =========================================
section('c4-lady', 'wang', '荣国府 · 王夫人起居处', 'court_entry', '卻說黛玉同姊妹們至王夫人處')
say('C04-001', 'narrator',
    '第四回开场仍在王夫人处。黛玉随姊妹们来问安，正赶上王夫人与薛家来的人计议家务，话里离不开姨母家遭的人命官司。',
    '王家来使', [hide('feng'), hide('tanchun'), hide('messenger'),
                 show('daiyu', 'court_entry'), show('wang', 'wang_host'),
                 move('daiyu', 'kang_edge')], focus='court_entry')
say('C04-002', 'narrator',
    '见王夫人事情冗杂，姊妹们便退了出来，往寡嫂李氏房中去。',
    '出来让席', [move('daiyu', 'kang_edge', 'hall_entry', 'guest_seat')], focus='guest_seat')
section('c4-lady', 'wang', '荣国府 · 李纨居处', 'li_room', '至寡嫂李氏房中來了')
say('C04-003', 'narrator',
    '这位李氏，便是贾珠之妻。贾珠虽已夭亡，幸留一子，取名贾兰，今年方才五岁，已经入学攻书。',
    '珠大嫂子', [show('liwan', 'li_room')], focus='li_room')
say('C04-004', 'narrator',
    '她是金陵名宦之女，父亲李守中做过国子监祭酒，家中男女无不诵诗读书。到了她这一辈，却信「女子无才便有德」，只教认得几个字、记得前朝几个贤女，其余以纺绩井臼为要，因此取名李纨，字宫裁。',
    '取名宫裁')
say('C04-005', 'liwan',
    '青春丧偶，虽居在这膏粱锦绣之中，竟也如槁木死灰一般，一概无见无闻。除去侍亲养子，便是陪着小姑们做些针黹诵读罢了。',
    '槁木死灰')
say('C04-006', 'narrator',
    '如今黛玉客寄于此，日日有这般姐妹相伴，除了老父亲，余人倒都无庸虑及了。',
    '姐妹相伴')

# ===== c4-court : the court and the case ====================================================
section('c4-court', 'c4_yamen', '应天府 · 大堂', 'bench', '如今且說雨村，因補授了應天府')
say('C04-007', 'narrator',
    '按下荣府不提。且说贾雨村补授了应天府，一到任就有案子报到案下：两家争买一个丫头，各不相让，以致殴伤人命。',
    '到任第一案', [roof(True), show('yucun', 'bench')], focus='bench')
say('C04-008', 'narrator',
    '雨村当即传原告到堂。那原告跪在堂下，说被打死的正是他的主人。',
    '传原告', [show('plaintiff', 'plaintiff')], focus='plaintiff')
say('C04-009', 'plaintiff',
    '那日小人主人买了一个丫头，不想是拐子拐来卖的。这拐子先已收了我家的银子，我家小爷原说第三日方是好日子，再接入门。')
say('C04-010', 'plaintiff',
    '谁知拐子又把丫头悄悄卖与薛家。我们去找拿卖主、夺取丫头，无奈薛家原系金陵一霸，倚财仗势，众豪奴竟将我家小主人打死了。')
say('C04-011', 'plaintiff',
    '凶身主仆已皆逃走，无影无踪，只剩了几个局外之人。小人告了一年的状，竟无人作主。望大老爷拘拿凶犯，剪恶除凶，以救孤寡，死者感戴天恩不盡！',
    '告了一年的状')
say('C04-012', 'yucun', '岂有这样放屁的事！打死人命，就白白地走了，再拿不来的！')
say('C04-013', 'narrator',
    '雨村当下发签，差公人立刻将凶犯族中人拿来拷问，令他们实供藏在何处，一面又行文动海捕文书。',
    '发签海捕')
say('C04-014', 'narrator',
    '正要发签时，案边立着的一个门子向他使眼色，示意不要发签。雨村心下甚为疑怪，只得停了手。',
    '门子使眼色', [show('menzi', 'hall_center'), effect('menzi', 'greet')], focus='hall_center')
say('C04-015', 'narrator',
    '他当即退堂，带着门子到了密室，侍从尽皆退出，只留这一个人服侍。',
    '退堂入密室', [hide('plaintiff'),
                   parallel(move('yucun', 'bench', 'side_door', 'chamber_host'),
                            move('menzi', 'hall_center', 'side_door', 'chamber_seat'))],
    focus='chamber_host')

# ===== c4-chamber : the old acquaintance of the gourd temple ================================
section('c4-chamber', 'c4_yamen', '应天府 · 退堂密室', 'chamber_host', '這門子忙上來請安')
say('C04-016', 'menzi',
    '老爷一向加官进禄，八九年來就忘了我了？', '葫芦庙旧识',
    [move('menzi', 'chamber_seat', 'chamber_host')], focus='chamber_host')
say('C04-017', 'yucun', '却十分面善得紧，只是一时想不起来。')
say('C04-018', 'menzi',
    '老爷真是贵人多忘事，把出身之地竟忘了，不记当年葫芦庙里之事？', '葫芦庙旧识')
say('C04-019', 'narrator',
    '雨村听了，如雷震一惊，方想起往事。原来这门子本是葫芦庙内一个小沙弥，因被火之后无处安身，欲投别庙去修行，又耐不得清凉景况，遂趁年纪蓄了发，充了门子。',
    '蓄发充门子', layer='recollection')
say('C04-020', 'yucun', '原来是故人。', '原来是故人',
    [move('yucun', 'chamber_host', 'chamber_seat')], focus='chamber_seat')
say('C04-021', 'narrator',
    '雨村让坐了好谈。这门子不敢坐。', '不敢坐')
say('C04-022', 'yucun',
    '贫贱之交不可忘。你我故人也，二则此系私室，既欲长谈，岂有不坐之理？', '贫贱之交不可忘')
say('C04-023', 'narrator',
    '这门子听说，方告了座，斜签着坐了。', '斜签着坐',
    [move('menzi', 'chamber_host', 'chamber_seat')], focus='chamber_seat')

# ===== c4-protect : the protective talisman ==================================================
section('c4-protect', 'c4_yamen', '应天府 · 退堂密室', 'chamber_seat', '雨村因問方纔何故有不令發簽之意')
say('C04-024', 'yucun', '方才何故有不令发签之意？', '问何以不发签')
say('C04-025', 'menzi',
    '老爷既荣任到这一省，难道就没抄一张本省「护官符」来不成？', '护官符')
say('C04-026', 'yucun', '何为「护官符」？我竟不知。')
say('C04-027', 'menzi',
    '这还了得！连这个不知，怎能作得长远！如今凡作地方官者，皆有一个私单，上面写的是本省最有权有势、极富极贵的大乡绅名姓，各省皆然。倘若不知，一时触犯了这样人家，不但官爵，只怕连性命还保不成呢！所以绰号叫作「护官符」。',
    '何为护官符')
say('C04-028', 'menzi',
    '方才所说的这薛家，老爷如何惹他！他这件官司并无难断之处，皆因都碍着情分面上，所以如此。', '薛家碍着情分',
    [effect('menzi', 'greet')])
say('C04-029', 'narrator',
    '一面说，一面从顺袋中取出一张抄写的「护官符」来，递与雨村。上头皆是本地大族名宦之家的谚俗口碑，排写得明白，下面所注的皆是自始祖官爵并房次。',
    '取出示看', [effect('menzi', 'rest')])
say('C04-030', 'yucun', '贾不假，白玉为堂金作马。', '贾家口碑')
say('C04-031', 'yucun', '阿房宫，三百里，住不下金陵一个史。', '史家口碑')
say('C04-032', 'yucun', '东海缺少白玉床，龙王来请金陵王。', '王家口碑')
say('C04-033', 'yucun', '丰年好大雪，珍珠如土金如铁。', '薛家口碑')
say('C04-034', 'narrator',
    '雨村犹未看完，忽听传点，人报：「王老爷来拜。」雨村听说，忙具衣冠出去迎接。有顿饭工夫，方回来细问。',
    '王老爷来拜', layer='present')
say('C04-035', 'menzi',
    '这四家皆连络有亲，一损皆损，一荣皆荣，扶持遮饰，俱有照应的。今告打死人之薛，就系丰年大雪之「雪」也。也不单靠这三家，他的世交亲友在都在外者，本亦不少。老爷如今拿谁去？',
    '雪与薛的双关')
say('C04-036', 'yucun',
    '如你这样说来，却怎么了结此案？你大约也深知这凶犯躲的方向了？', '问凶犯下落')

# ===== c4-truth : the story of Yinglian ======================================================
section('c4-truth', 'c4_yamen', '应天府 · 退堂密室', 'chamber_seat', '門子笑道：不瞞老爺說')
say('C04-037', 'menzi',
    '不瞒老爷说，不但这凶犯的方向我知道，一并这拐卖之人我也知道，死鬼买主也深知道。待我细说与老爷听。', '我都知道',
    [move('menzi', 'chamber_seat', 'chamber_host')], focus='chamber_host')
say('C04-038', 'menzi',
    '这个被打之死鬼，乃是本地一个小乡绅之子，名唤冯渊，自幼父母早亡，又无兄弟，只他一个人守着些薄产过日子。长到十八九岁上，酷爱男风，最厌女子。', '冯渊身世',
    layer='reported')
say('C04-039', 'menzi',
    '这也是前生冤孽，可巧遇见这拐子卖丫头，他便一眼看上了这丫头，立意买来作妾，立誓再不交结男子，也不再娶第二个了，所以三日后方过门。', '立誓买妾',
    layer='reported')
say('C04-040', 'menzi',
    '谁晓这拐子又偷卖与薛家，他意欲卷了两家的银子，再逃往他省。谁知又不曾走脱，两家拿住，打了个臭死，都不肯收银，只要领人。', '两家拿住拐子',
    layer='reported')
say('C04-041', 'menzi',
    '那薛家公子岂是让人的，便喝着手下人一打，将冯公子打了个稀烂，抬回家去三日死了。', '打死冯渊',
    layer='reported')
say('C04-042', 'menzi',
    '这薛公子原是早已择定日子上京去的，头起身两日前，就偶然遇见这丫头，意欲买了就进京的，谁知闹出这事来。既打了冯公子，夺了丫头，他便没事人一般，只管带了家眷走他的路。', '带家眷上京',
    layer='reported')
say('C04-043', 'menzi',
    '老爷你当被卖之丫头是谁？', '被卖之丫头是谁')
say('C04-044', 'yucun', '我如何得知。')
say('C04-045', 'menzi',
    '这人算来还是老爷的大恩人呢！他就是葫芦庙旁住的甄老爷的小姐，名唤英莲的。', '英莲身世揭晓', layer='reported')
say('C04-046', 'yucun',
    '原来就是他！闻得养至五岁被人拐去，却如今才来卖呢？', '原来是他', layer='recollection')
say('C04-047', 'menzi',
    '这一种拐子单管偷拐五六岁的儿女，养在一个僻静之处，到十一二岁，度其容貌，带至他乡转卖。', '拐子的手法',
    layer='reported')
say('C04-048', 'menzi',
    '当日这英莲，我们天天哄他顽耍，虽隔了七八年，如今十二三岁的光景。其模样虽然出脱得齐整好些，然大概相貌，自是不改，熟人易认。', '十二三岁的模样',
    layer='reported')
say('C04-049', 'menzi',
    '况且他眉心中原有米粒大小的一点胭脂痣，从胎里带来的，所以我却认得。', '眉心胭脂痣', layer='reported')
say('C04-050', 'menzi',
    '偏生这拐子又租了我的房舍居住。那日拐子不在家，我也曾问他，他是被拐子打怕了的，万不敢说，只说拐子系他亲爹，因无钱偿债，故卖他。', '认人经过',
    layer='reported')
say('C04-051', 'menzi',
    '我又哄之再四，他又哭了，只说「我不记得小时之事」！这可无疑了。', '我不记得小时之事',
    layer='reported')
say('C04-052', 'menzi',
    '那日冯公子相看了，兑了银子，拐子醉了，他自叹道：「我今日罪孽可满了！」后又听见冯公子令三日之后过门，他又转有忧愁之态。', '拐子自叹',
    layer='reported')
say('C04-053', 'menzi',
    '我又不忍其形景，等拐子出去，又命内人去解释他：「这冯公子必待好日期来接，可知必不以丫鬟相看。况他是个绝风流人品，家里颇过得，素习又最厌恶堂客，今竟破价买你，后事不言可知。只耐得三两日，何必忧闷！」他听如此说，方才略解忧闷，自为从此得所。', '内人劝解',
    layer='reported')
say('C04-054', 'menzi',
    '谁料天下竟有这等不如意事，第二日，他偏又卖与薛家。', '第二日重卖',
    layer='reported')
say('C04-055', 'menzi',
    '若卖与第二个人还好，这薛公子的混名人称「呆霸王」，最是天下第一个弄性尚气的人，而且使钱如土，遂打了个落花流水，生拖死拽，把个英莲拖去，如今也不知死活。', '呆霸王拖走英莲',
    layer='reported')
say('C04-056', 'menzi',
    '这冯公子空喜一场，一念未遂，反花了钱，送了命，岂不可叹！', '空喜一场',
    layer='reported')

# ===== c4-judge : the biased judgement =======================================================
section('c4-judge', 'c4_yamen', '应天府 · 退堂密室', 'chamber_seat', '雨村聽了，亦歎道')
say('C04-057', 'yucun',
    '这也是他们的孽障遭遇，亦非偶然。不然这冯渊如何偏只看准了这英莲？这英莲受了这拐子这几年折磨，才得了个头路，且又是个多情的，若能聚合了，倒是件美事，偏又生出这段事来。', '薄命儿女',
    [move('yucun', 'chamber_seat', 'chamber_host')], focus='chamber_host')
say('C04-058', 'yucun',
    '这薛家纵比冯家富贵，想其为人，自然姬妾众多，淫佚无度，未必及冯渊定情于一人者。这正是梦幻情缘，恰遇一对薄命儿女。', '梦幻情缘')
say('C04-059', 'yucun',
    '且不要议论他，只目今这官司，如何剖断才好？', '问如何断案')
say('C04-060', 'menzi',
    '老爷当年何其明决，今日何反成了个没主意的人了！小的闻得老爷补升此任，亦系贾府、王府之力，此薛蟠即贾府之亲，老爷何不顺水行舟，作个整人情，将此案了结，日后也好去见贾府王府。', '顺水行舟',
    [move('menzi', 'chamber_host', 'chamber_seat')], focus='chamber_seat')
say('C04-061', 'yucun',
    '你说的何尝不是。但事关人命，蒙皇上隆恩，起复委用，实是重生再造，正当殚心竭力图报之时，岂可因私而废法？是我实不能忍为者。', '岂可因私废法')
say('C04-062', 'menzi',
    '老爷说的何尝不是大道理，但只是如今世上是行不去的。岂不闻古人有云：「大丈夫相时而动」，又曰「趋吉避凶者为君子」。依老爷这一说，不但不能报效朝廷，亦且自身不保，还要三思为妥。', '相时而动',
    layer='reported')
say('C04-063', 'yucun', '依你怎么样？', '低头问计',
    [move('yucun', 'chamber_host', 'chamber_seat')], focus='chamber_seat')
say('C04-064', 'menzi',
    '小人已想了一个极好的主意在此：老爷明日坐堂，只管虚张声势，动文书发签拿人。原凶自然是拿不来的，原告固是要将薛家族中及奴仆人等拿几个来拷问。', '虚张声势')
say('C04-065', 'menzi',
    '小的在暗中调停，令他们报个暴病身亡，令族中及地方上共递一张保呈。老爷只说善能扶鸾请仙，堂上设下乩坛，令军民人等只管来看。', '扶鸾设乩坛')
say('C04-066', 'menzi',
    '老爷就说：「乩仙批了，死者冯渊与薛蟠原因夙孽相逢，今狭路既遇，原应了结。薛蟠今已得了无名之病，被冯魂追索已死。其祸皆因拐子某人而起，拐之人原系某乡某姓人氏，按法处治，余不略及」等语。', '乩仙批语')
say('C04-067', 'menzi',
    '小人暗中嘱托拐子，令其实招。众人见乩仙批语与拐子相符，余者自然也都不虚了。', '嘱拐子实招')
say('C04-068', 'menzi',
    '薛家有的是钱，老爷断一千也可，五百也可，与冯家作烧埋之费。那冯家也无甚要紧的人，不过为的是钱，见有了这个银子，想来也就无话了。老爷细想此计如何？', '烧埋之费')
say('C04-069', 'yucun',
    '不妥，不妥。等我再斟酌斟酌，或可压服口声。', '我再斟酌',
    [move('yucun', 'chamber_seat', 'chamber_host')], focus='chamber_host')
say('C04-070', 'narrator',
    '二人计议，天色已晚，别无话说。', '天色已晚')
section('c4-judge', 'c4_yamen', '应天府 · 大堂', 'bench', '至次日坐堂，勾取一應有名人犯')
say('C04-071', 'narrator',
    '至次日坐堂，勾取一应有名人犯，雨村详加审问，果见冯家人口稀疏，不过赖此欲多得些烧埋之费，薛家仗势倚情，偏不相让，故致颠倒未决。',
    '次日坐堂', [hide('menzi'), move('yucun', 'chamber_host', 'side_door', 'bench')],
    focus='bench')
say('C04-072', 'narrator',
    '雨村便徇情枉法，胡乱判断了此案。冯家得了许多烧埋银子，也就无甚话说了。',
    '徇情枉法')
say('C04-073', 'narrator',
    '雨村断了此案，急忙作书信二封，与贾政并京营节度使王子腾，不过说「令甥之事已完，不必过虑」等语。',
    '两封书信')
say('C04-074', 'narrator',
    '此事皆由葫芦庙内之沙弥新门子所出，雨村又恐他对人说出当日贫贱时的事来，因此心中大不乐业。后来到底寻了个不是，远远的充发了他才罢。',
    '充发门子', layer='reported')

# ===== c4-xue : the Xue family on the road ==================================================
section('c4-xue', 'capital', '京城 · 宁荣街', 'street_west', '且說那買了英蓮打死馮淵的薛公子')
say('C04-075', 'narrator',
    '当下言不着雨村。且说那买了英莲、打死冯渊的薛公子，亦系金陵人氏，本是书香继世之家。只是如今这薛公子幼年丧父，寡母又怜他是个独根孤种，未免溺爱纵容，遂至老大无成。',
    '薛家来历', [roof(True), show('xuepan', 'street_west'), show('xueyima', 'outside'),
                 show('baochai', 'ning_gate')], layer='reported')
say('C04-076', 'narrator',
    '且家中有百万之富，现领着内帑钱粮，采办杂料。这薛公子学名薛蟠，表字文起，五岁上就性情奢侈，言语傲慢。虽也上过学，不过略识几字，终日惟有斗鸡走马、游山玩水而已。',
    '薛蟠其人')
say('C04-077', 'narrator',
    '虽是皇商，一应经济世事全然不知，不过赖祖父之旧情分，户部挂虚名，支领钱粮，其余事体自有伙计老家人等措办。',
    '不谙世事')
say('C04-078', 'narrator',
    '寡母王氏乃现任京营节度使王子腾之妹，与荣国府贾政的夫人王氏，是一母所生的姊妹，今年方四十上下年纪，只有薛蟠一子。',
    '一母所生的姊妹')
say('C04-079', 'narrator',
    '还有一女，比薛蟠小两岁，乳名宝钗，生得肌骨莹润，举止娴雅。当日有他父亲在日，酷爱此女，令其读书识字，较之乃兄竟高过十倍。',
    '宝钗其人', [move('baochai', 'ning_gate', 'street_west')])
say('C04-080', 'narrator',
    '自父亲死后，见哥哥不能依贴母怀，他便不以书字为事，只留心针黹家計等事，好为母亲分忧解劳。',
    '分忧解劳')
say('C04-081', 'narrator',
    '近因今上崇诗尚礼，征采才能，凡仕宦名家之女皆亲名达部，以备选为公主郡主入学陪侍，充为才人赞善之职。',
    '待选之由')
say('C04-082', 'narrator',
    '一为送妹待选，二为望亲，三因亲自入部销算旧帐，再计新支，其实则为游览上国风光之意。',
    '入京三项目的')
say('C04-083', 'narrator',
    '因此早已打点下行装细软，以及馈送亲友各色土物人情等类，正择日一定起身，不想偏遇见了拐子重卖英莲。',
    '正择日起身')
say('C04-084', 'narrator',
    '薛蟠见英莲生得不俗，立意买他，又遇冯家来夺人，因恃强喝令手下豪奴将冯渊打死。',
    '恃强买人', layer='reported')
say('C04-085', 'narrator',
    '他便将家中事务一一的嘱托了族中人并几个老家人，便带了母妹竟自起身长行去了。人命官司一事，他竟视为儿戏，自为花上几个臭钱，没有不了的。',
    '视为儿戏', [move('xuepan', 'street_west', 'rong_gate')])
say('C04-086', 'narrator',
    '在路不记其日。那日已将入都时，却又闻得母舅王子腾升了九省统制，奉旨出都查边。',
    '王子腾升迁')
say('C04-087', 'xuepan',
    '我正愁进京去有个嫡亲的母舅管辖着，不能任意挥霍挥霍，偏如今又升出去了，可知天从人愿。', '天从人愿')
say('C04-088', 'xuepan',
    '咱们京中虽有几处房舍，只是这十来年没人进京居住，那看守的人未免偷着租赁与人，须得先着几个人去打扫收拾才好。', '先打扫房舍')
say('C04-089', 'xueyima',
    '何必如此招摇！咱们这一进京，原该先拜望亲友，或是在你舅舅家，或是你姨爹家。他两家的房舍极是便宜的，咱们先能着住下，再慢慢地着人去收拾，岂不消停些。', '何必如此招摇')
say('C04-090', 'xuepan',
    '如今舅舅正升了外省去，家里自然忙乱起身，咱们这工夫一窝一拖的奔了去，岂不没眼色。', '岂不没眼色')
say('C04-091', 'xueyima',
    '你舅舅家虽升了去，还有你姨爹家。况这几年来，你舅舅姨娘两处，每每带信捎书，接咱们来。如今既来了，你舅舅虽忙着起身，你贾家姨娘未必不苦留我们。', '还有你姨爹家')
say('C04-092', 'xueyima',
    '你既如此，你自去挑所宅子去住，我和你姨娘姊妹们别了这几年，却要厮守几日。我带了你妹子投你姨娘家去，你道好不好？', '你自去挑宅子',
    [move('xueyima', 'outside', 'rong_gate'), move('baochai', 'street_west', 'rong_gate')])
say('C04-093', 'narrator',
    '薛蟠见母亲如此说，情知扭不过的，只得吩咐人夫一路奔荣国府来。',
    '奔荣国府来')

# ===== c4-hall : the welcome at the Rongxi hall ==============================================
section('c4-hall', 'central', '荣禧堂 · 大厅', 'rongxi_center', '那時王夫人已知薛蟠官司一事')
say('C04-094', 'narrator',
    '那时王夫人已知薛蟠官司一事，亏贾雨村维持了结，才放了心。又见哥哥升了边缺，正愁又少了娘家的亲戚来往，略加寂寞。',
    '王夫人放心', [roof(True), show('wang', 'rongxi_center')], focus='rongxi_center')
say('C04-095', 'narrator',
    '过了几日，忽家人传报：「姨太太带了哥儿姐儿，合家进京，正在门外下车。」',
    '家人传报', offscreen=True)
say('C04-096', 'narrator',
    '喜得王夫人忙带了女媳人等，接出大厅，将薛姨妈等接了进去。姊妹们暮年相会，自不必说悲喜交集，泣笑叙阔一番。',
    '接出大厅', [show('xueyima', 'ceremonial_gate'), show('baochai', 'inner_gate'),
                  show('xuepan', 'rongxi_steps'),
                  parallel(move('wang', 'rongxi_center', 'rongxi_steps', 'inner_gate'),
                           move('xueyima', 'ceremonial_gate', 'rongxi_steps', 'inner_gate'),
                           move('baochai', 'inner_gate', 'rongxi_steps'))],
    focus='rongxi_steps')
say('C04-097', 'narrator',
    '忙又引了拜见贾母，将人情土物各种酬献了。合家俱厮见过，忙又治席接风。',
    '拜见贾母', [show('grandmother', 'rongxi_center'),
                  move('xueyima', 'inner_gate', 'rongxi_center')], focus='rongxi_center')
say('C04-098', 'narrator',
    '薛蟠已拜见过贾政，贾琏又引着拜见了贾赦、贾珍等。这些人今日不出场。',
    '拜见贾政等', layer='reported')
say('C04-099', 'narrator',
    '贾政便使人上来对王夫人说：「姨太太已有了春秋，外甥年轻不知世路，在外住着恐有人生事。咱们东北角上梨香院一所十来间房，白空闲着，打扫了，请姨太太和姐儿哥儿住了甚好。」',
    '贾政让梨香院', layer='reported')
say('C04-100', 'narrator',
    '王夫人未及留，贾母也就遣人来说「请姨太太就在这里住下，大家亲密些」等语。',
    '贾母也来相邀', layer='reported')
say('C04-101', 'xueyima',
    '正要同居一处，方可拘紧些儿子，若另住在外，又恐他纵性惹祸，遂忙道谢应允。',
    '道谢应允', [move('xuepan', 'rongxi_steps', 'west_room')], focus='west_room')
say('C04-102', 'xueyima',
    '又私与王夫人说明：「一应日费供给一概免却，方是处常之法。」', '日用供给一概免却')
say('C04-103', 'narrator',
    '王夫人知他家不难于此，遂亦从其愿。从此以后薛家母子就在梨香院住了。',
    '住进梨香院')

# ===== c4-pear : the pear-fragrance court ====================================================
section('c4-pear', 'c4_lixiang', '梨香院 · 院中', 'court_center', '原來這梨香院即當日榮公暮年養靜之所')
say('C04-104', 'narrator',
    '原来这梨香院即当日荣公暮年养静之所，小小巧巧，约有十余间房屋，前厅后舍俱全。',
    '梨香院形制', [roof(True), show('xueyima', 'front_hall'), show('baochai', 'court_center'),
                    show('xuepan', 'street_gate')], focus='court_center')
say('C04-105', 'narrator',
    '另有一门通街，薛蟠家人就走此门出入。西南有一角门，通一夹道，出夹道便是王夫人正房的东边了。',
    '通街门与西南角门', [move('xuepan', 'street_gate', 'court_center')], focus='court_center')
say('C04-106', 'narrator',
    '每日或饭后，或晚间，薛姨妈便过来，或与贾母闲谈，或与王夫人相叙。',
    '往来两处')
say('C04-107', 'narrator',
    '宝钗日与黛玉迎春姊妹等一处，或看书下棋，或作针黹，倒也十分乐业。',
    '宝钗与姊妹同乐', [show('daiyu', 'back_rooms'), show('yingchun', 'lane_gate'),
                        move('baochai', 'court_center', 'back_rooms')], focus='back_rooms')
say('C04-108', 'narrator',
    '只是薛蟠起初之心，原不欲在贾宅居住者，但恐姨父管约拘禁，料必不自在的，无奈母亲执意在此，且宅中又十分殷勤苦留，只得暂且住下，一面使人打扫出自己的房屋，再移居过去的。',
    '只得暂且住下')
say('C04-109', 'narrator',
    '谁知自从在此住了不上一月的光景，贾宅族中凡有的子侄，俱已认熟了一半。凡是那些纨绔气习者，莫不喜与他来往，今日会酒，明日观花，甚至聚赌嫖娼，渐渐无所不至。',
    '纨绔引诱')
say('C04-110', 'narrator',
    '引诱得薛蟠比当日更坏了十倍。虽然贾政训子有方，治家有法，一则族大人多，照管不到这些；二则现任族长乃是贾珍，彼乃宁府长孙，又现袭职，凡族中事自有他掌管；三则公私冗杂，且素性潇洒，不以俗务为要。',
    '比当日更坏十倍')
say('C04-111', 'narrator',
    '况且这梨香院相隔两层房舍，又有街门另开，任意可以出入，所以这些子弟们竟可以放意畅怀的，因此遂将移居之念渐渐打灭了。',
    '移居之念打灭', [move('xuepan', 'court_center', 'street_gate')], focus='street_gate')
say('C04-112', 'narrator',
    '日后如何，下回分解。', '下回分解')

(ROOT / 'design/chapter04-story.json').write_text(json.dumps(steps, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'design/chapter04-sections.json').write_text(
    json.dumps([{'id': a, 'title': b, 'scene': c,
                 'start': next(s['id'] for s in steps if s['chapter'] == a), 'book': 4}
                for a, b, c in chapters], ensure_ascii=False, indent=2) + '\n')

anchor_count = {k: build_map(k, s) for k, s in scenes.items()}
add_wang_anchor()
print('maps:', ', '.join(f'{k}({n} anchors)' for k, n in anchor_count.items()))
print('wang.tmj: added li_room anchor (backup in %s)' % BACKUP.relative_to(ROOT))
print('story: %d nodes; sections: %s' % (len(steps), ', '.join(a for a, b, c in chapters)))
