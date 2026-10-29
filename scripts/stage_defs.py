#!/usr/bin/env python3
"""Stage geometry for the prequel chapters and chapter three.

Every entry is a plan, not a copy of one. The novel fixes what stands in each place —
`葫芦庙` next door to 甄宅, 荣禧堂 on the axis behind the 内仪门, 贾母 坐在榻上 with four
empty chairs at either side — and never fixes a drawing, so the drawing is a design
decision recorded in docs/production/maps.md.

Read it as a courtyard grammar:

    zones     walkable floors; the 5th `True` marks an indoor floor, the 6th names it
    terraces  `court` (a raised stone platform) and `path` (the 甬路 on the axis)
    walls     enclosure segments; the gap between two segments is a gate
    water     pond, canal or the ink-black 迷津
    beds      this courtyard's planting, not the old estate beds in every garden alike
    props     (asset, col, row, scale[, zone]) — `at()` offsets by screen pixels

`at(c,r,dx,dy)` exists because one grid cell is 128×64 px: a chair placed on the "next
cell" lands half a table away from its table, which is what made the furniture look
thrown down rather than set out.
"""
def at(c, r, dx=0.0, dy=0.0):
    """Grid position offset by screen pixels (dx right, dy down).

    One grid cell is 128×64 px on screen, so `at(c,r,64,0)` is half a cell east — the
    offset that keeps a chair against its table instead of half a table away.
    """
    return (c + dx / 128 + dy / 64, r + dy / 64 - dx / 128)



def eave(c, r, zone, rects):
    """Where a roof's foot line goes: the south edge of the floor it covers.

    A roof lifts on its front eave. Authored in the middle of its room it left the near half
    of the room roofless after the lift, and put the ridge 200–400 px above the frame — which
    is how 智通寺's hall spent a whole scene out of shot. `rects` maps floor id → (c,r,w,h).
    """
    rect = rects.get(zone) if zone else None
    if not rect:
        return c, r
    zc, zr, zw, zh = rect
    if zc <= c < zc + zw and zr <= r < zr + zh:
        return c, zr + zh - .5
    return c, r


def court(c, r, w, h, gate=None, gw=3):
    """Walls for a rectangular courtyard with a gap in the south wall for the gate."""
    walls = [[c, r, c + w, r], [c, r, c, r + h], [c + w, r, c + w, r + h]]
    if gate is None:
        walls.append([c, r + h, c + w, r + h])
    else:
        walls.append([c, r + h, gate, r + h])
        walls.append([gate + gw, r + h, c + w, r + h])
    return walls


def walk(c, r, w, h):
    """The paved approach inside a courtyard, from gate to hall steps."""
    return [c, r, w, h, 'path']


# Assets that are a roof over a floor rather than a piece of furniture on it. The name is
# not enough: 甄宅 is a `-house`, 葫芦庙 and 智通寺 are `-temple`, 会芳园那间退步 is a
# `-room`. A shell lifts off the courtyard when the walk steps inside; anything else with
# a floor named only appears once you are in there — which is how a bookshelf ended up
# standing in an empty yard with no house around it.
SHELLS = {'farm-house', 'hulu-temple', 'qin-room', 'ruined-house', 'tavern-house',
          'zhen-house', 'zhitong-temple'}


def is_shell(asset):
    return asset.endswith('-hall') or asset in SHELLS



# How tall a thing may stand, in world pixels, before the camera cuts its roof off.
# `fit()` clamps to the section bar and the dialogue box: at zoom .9 a 1440×900 canvas shows
# about 430 px of stage above the camera and 340 below, so a hall taller than ~470 px loses
# its ridge every time and a 970 px hall (main-hall at .84) fills the frame with roof.
MAX_TALL = {'main-hall': 430, 'rongxi-hall': 430, 'wang-hall': 400, 'yamen-hall': 380,
            'fu-hall': 380, 'lixiang-hall': 360, 'main-gate': 340, 'manor-main-gate': 340,
            'screen-wall': 320, 'lantern-booth': 300, 'tavern-house': 350, 'farm-house': 320,
            'zhen-house': 360, 'hulu-temple': 330, 'zhitong-temple': 360, 'ruined-house': 380,
            'ning-hall': 360, 'qin-room': 320, 'taixu-arch': 340, 'taixu-hall': 380, 'spirit-stone': 430}


def _native():
    """Read each asset's painted size, so height can be the thing we author."""
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'maps/rongguo-art.tsj'
    if not path.exists():
        return {}
    return {next(p['value'] for p in t['properties'] if p['name'] == 'asset'):
            (t['imagewidth'], t['imageheight']) for t in json.loads(path.read_text())['tiles']}


NATIVE = _native()


def fit(asset, scale=1.0):
    """Scale a building so it stands `MAX_TALL[asset]` pixels high, never larger than asked.

    Authored scales had drifted to 0.84–0.94 for every hall regardless of how big it was
    painted, so 荣禧堂 (1100×931) stood 780 px tall and 应天府 (900×520) only 440. Capping by
    height makes a hall a hall next door as well as here, and keeps the ridge in frame.
    """
    cap = MAX_TALL.get(asset)
    native = NATIVE.get(asset)
    if not cap or not native:
        return scale
    return min(scale, cap / native[1])


SCENES = {}


def stage(key, name, theme, zones, anchors, props, labels, **extra):
    SCENES[key] = dict(name=name, theme=theme, zones=zones, anchors=anchors,
                       props=props, labels=labels, **extra)


# ---------------------------------------------------------------------------
# 第一回
# ---------------------------------------------------------------------------

# 大荒山无稽崖青埂峰：女娲补天弃下的一块顽石，僧道坐在石旁谈红尘。荒山，不是院子。
stage('myth', '大荒山 · 青埂峰（神话）', 'myth',
      zones=[[12, 8, 16, 12], [17, 19, 5, 11], [26, 24, 8, 6]],
      anchors={'entry': [19, 29], 'path': [19, 23], 'guest': [18, 18], 'host': [21, 15],
               'left': [14, 16], 'right': [24, 18], 'rear': [22, 10], 'exit': [30, 26]},
      labels=[['青埂峰', 20, 11], ['入世之路', 19, 26], ['大荒山', 12, 9]],
      props=[
          ('spirit-stone', *at(20, 13), 2.0),
          ('garden-rock', *at(20, 13, -214, 44), .92),
          ('garden-rock', *at(20, 13, 206, 18), 1.02),
          ('garden-rock', *at(16, 10, -40, -30), .74),
          ('garden-rock', *at(25, 20, 40, 0), .82),
          ('garden-rock', *at(11, 22), .88),
          ('garden-rock', *at(28, 17), 1.10),
          ('garden-tree', *at(13, 13), 1.28),
          ('garden-tree', *at(26, 12), 1.06),
          ('garden-tree', *at(17, 24), .92),
      ],
      terraces=[[18, 20, 3, 9, 'path'], [16, 11, 8, 7, 'court']],
      beds=[])

# 太虚幻境 · 灵河：士隐梦里听僧道说绛珠还泪，接过通灵宝玉，随他们走进牌坊。
stage('dream', '太虚幻境 · 灵河（梦中）', 'dream',
      zones=[[12, 8, 16, 12], [17, 19, 5, 11], [26, 24, 8, 6]],
      anchors={'entry': [19, 29], 'path': [19, 23], 'guest': [18, 18], 'host': [21, 15],
               'left': [14, 16], 'right': [24, 18], 'rear': [22, 10], 'exit': [30, 26]},
      labels=[['太虚幻境', 22, 7], ['灵河', 18, 15], ['三生石', 14, 21]],
      props=[
          ('taixu-arch', *at(20, 9), .70),
          ('garden-rock', *at(14, 20), 1.15),
          ('crimson-pearl', *at(12, 19), .85),
          ('garden-tree', *at(8, 17), 1.10),
          ('garden-tree', *at(30, 16), 1.16),
          ('taixu-rock', *at(27, 21), .80),
      ],
      water=[[12, 13, 17, 4]],
      terraces=[[17, 17, 4, 7, 'path'], [16, 4, 10, 5, 'court']],
      beds=[])

# 姑苏阊门外仁清巷：甄宅与葫芦庙一墙之隔，书斋窗外是花圃，雨村在庙里对月吟诗。
# 两座院子并排摆在一个镜头能扫到的距离里，中间只隔一道墙——书上一句「隔壁」，
# 图上一屏；原来隔着十四格，镜头里只剩空砖地。
stage('suzhou', '姑苏 · 仁清巷与甄宅', 'garden',
      zones=[[16, 14, 11, 8], [20, 14, 5, 4, True, 'STUDY'], [11, 22, 14, 5],
             [7, 20, 9, 8], [26, 21, 4, 4]],
      anchors={'entry': [17, 26], 'path': [20, 22], 'guest': [22, 18], 'host': [24, 19],
               'left': [16, 21], 'right': [26, 19], 'rear': [25, 15], 'exit': [22, 26]},
      labels=[['甄宅', 25, 14], ['书斋', 20, 17], ['葫芦庙', 12, 21], ['仁清巷', 17, 26]],
      props=[
          ('zhen-house', *at(23, 16), .78, 'STUDY'),
          ('bookshelf', *at(23, 16, -40, 10), .62, 'STUDY'),
          ('tea-table', *at(22, 17, 84, 30), .55, 'STUDY'),
          ('hulu-temple', *at(13, 22), .70),
          ('altar-shrine', *at(12, 25, -46, 6), .48),
          # 海棠：原摆在甄宅东南、正压住 host/guest 两个人物锚点（甄士隐的站位），
          # 树冠不透明、淡到 45% 仍盖住人。改放到甄宅东侧空地，不挡任何走位。
          ('garden-tree', *at(27, 14), 1.00),
          # 竹丛原压 left 锚点（英莲/雨村的站位）；改放到葫芦庙院内西南角，
          # 仍在取景框内且不再压任何走位。
          ('bamboo-cluster', *at(13, 24), .92),
          ('garden-rock', *at(19, 24), .74),
      ],
      walls=court(16, 14, 11, 8, gate=21, gw=3) + court(7, 20, 9, 8, gate=10, gw=3),
      beds=[[24, 17, 2, 3], [17, 19, 3, 2]],
      terraces=[walk(21, 18, 3, 5), walk(10, 24, 3, 4)])

# 元宵灯市：一条街，两排灯棚，霍启把孩子放在门槛上，回头人就不见了。
stage('lantern', '姑苏 · 元宵灯市', 'night',
      zones=[[10, 18, 22, 9, False], [12, 12, 16, 7, False], [16, 27, 5, 4, False]],
      anchors={'entry': [18, 29], 'path': [18, 24], 'guest': [20, 19], 'host': [23, 19],
               'left': [14, 20], 'right': [26, 18], 'rear': [12, 15], 'exit': [30, 22]},
      labels=[['社火花灯', 22, 14], ['失散处', 18, 18], ['仁清巷口', 18, 27]],
      props=[
          ('lantern-booth', *at(24, 17), .92),
          # 原 (14,16) 的灯棚正压住 rear 锚点（霍启抱着英莲走到这里的站位），
          # 大件压走位同属需要修掉的遮挡类；东移到 (16,14) 让出走道。
          ('lantern-booth', *at(16, 14), .82),
          ('lantern-booth', *at(19, 13), .86),
          ('zhen-house', *at(10, 23), .66),
          ('garden-tree', *at(28, 25), 1.10),
          ('stone-lion', *at(11, 22, 0, 8), .52),
          # 灯棚原是空竹架，补上货品：酒坛、青花瓷瓶架，让市集有陈列感。
          ('wine-jars', *at(25, 18), .5),
          ('vase-stand', *at(14, 18), .7),
          ('wine-jars', *at(19, 15), .5),
          ('vase-stand', *at(23, 18), .6),
      ],
      beds=[],
      # A string of lanterns along the street and one under each booth's beam: without them
      # the 灯棚 are empty bamboo frames and the market plays in daylight.
      # A row on screen means cells (c+k, r-k): that is the line the street runs along, and
      # lanterns hung two cells apart land 256 px apart in a straight string.
      lights=[(14, 25), (16, 23), (18, 21), (20, 19), (22, 17), (24, 15),
              (24, 18), (14, 17), (19, 14)],
      dusk=True,
      terraces=[[11, 19, 20, 7, 'path']])

# 葫芦庙火后：一条街烧成瓦砾，甄宅只剩焦黑的梁柱。
stage('ruins', '姑苏 · 葫芦庙火后', 'ruins',
      zones=[[12, 10, 18, 12], [16, 22, 5, 8], [26, 18, 8, 6]],
      anchors={'entry': [18, 29], 'path': [18, 24], 'guest': [20, 17], 'host': [19, 14],
               'left': [13, 16], 'right': [25, 15], 'rear': [22, 11], 'exit': [30, 20]},
      labels=[['甄宅废墟', 20, 12], ['葫芦庙遗址', 11, 13]],
      props=[
          ('ruined-house', *at(21, 12), 1.00),
          ('ruined-house', *at(13, 15), .68),
          ('garden-tree', *at(27, 20), .94),
          ('garden-rock', *at(16, 20), .86),
          ('garden-rock', *at(24, 21), .72),
          ('courtyard-wall', *at(26, 17), .72),
      ],
      walls=[[12, 10, 30, 10], [12, 10, 12, 20], [30, 10, 30, 16],
             [20, 22, 26, 22]],
      beds=[],
      terraces=[[17, 21, 3, 9, 'path']])

# 大如州封家田庄：几间薄田朽屋，士隐拄杖出门听好了歌，封氏做针线，娇杏上街买线。
stage('farm', '大如州 · 封家田庄', 'garden',
      zones=[[13, 12, 14, 10], [13, 12, 8, 6, True, 'HOUSE'], [4, 22, 10, 9],
             [16, 22, 5, 8]],
      anchors={'entry': [18, 29], 'path': [18, 24], 'guest': [20, 19], 'host': [22, 16],
               'left': [15, 18], 'right': [26, 17], 'rear': [21, 12], 'exit': [12, 26]},
      labels=[['封家', 21, 11], ['薄田', 7, 24], ['田庄小路', 18, 27]],
      props=[
          ('farm-house', *at(18, 13), .80, 'HOUSE'),
          ('plain-kang', *at(16, 14, -20, 10), .70, 'HOUSE'),
          ('farm-stove', *at(19, 14, 40, 12), .58, 'HOUSE'),
          ('garden-tree', *at(14, 16), 1.10),
          ('garden-tree', *at(26, 21), 1.02),
          ('garden-rock', *at(25, 14), .70),
      ],
      walls=court(13, 12, 14, 10, gate=17, gw=3),
      beds=[[4, 24, 4, 4], [9, 23, 4, 3]],
      terraces=[[17, 21, 3, 9, 'path']])

# 知府衙署：雨村得官又革职，前庭、大堂、阶下鼓。
stage('yamen', '知府衙署 · 雨村仕途', 'formal',
      zones=[[14, 19, 12, 10], [14, 10, 12, 9, True, 'HALL'], [18, 29, 4, 4], [27, 19, 7, 5]],
      anchors={'entry': [19, 30], 'path': [19, 25], 'guest': [19, 21], 'host': [20, 16],
               'left': [16, 18], 'right': [24, 18], 'rear': [22, 12], 'exit': [30, 22]},
      labels=[['公堂', 20, 11], ['府衙外', 19, 29]],
      props=[
          ('yamen-hall', *at(20, 14), .94, 'HALL'),
          ('official-desk', *at(21, 17, -30, 40), .78, 'HALL'),
          ('altar-table', *at(21, 17, -190, -30), .62, 'HALL'),
          ('stone-lion', *at(16, 27), .58),
          ('stone-lion', *at(23, 27), .58),
          ('sedan-chair', *at(26, 25), .74),
          ('garden-tree', *at(14, 26), 1.08),
          ('garden-tree', *at(28, 19), 1.00),
      ],
      walls=court(13, 9, 14, 14, gate=18, gw=4),
      beds=[[26, 11, 3, 3]],
      terraces=[[18, 22, 4, 9, 'path']])

# 扬州林府：盐政御史署，书斋教黛玉读书，内院，江岸码头。
stage('lin', '扬州 · 林府与江岸', 'river',
      zones=[[9, 10, 14, 9], [10, 8, 10, 7, True, 'STUDY'], [20, 24, 12, 6],
             [12, 19, 10, 6]],
      anchors={'study_guest': [15, 11], 'study_host': [17, 10], 'daiyu_wait': [18, 12],
               'door': [16, 17], 'garden': [16, 23], 'quay': [22, 27],
               'boat': [27, 27], 'departure': [30, 27]},
      labels=[['书斋', 15, 9], ['林府', 12, 16], ['江岸', 23, 28]],
      props=[
          ('main-hall', *at(15, 13), .84, 'STUDY'),
          ('bookshelf', *at(15, 11, -46, 16), .68, 'STUDY'),
          ('tea-table', *at(16, 12, 92, 30), .60, 'STUDY'),
          ('round-stool', *at(16, 12, 150, 34), .66, 'STUDY'),
          ('garden-tree', *at(12, 18), 1.12),
          ('garden-tree', *at(22, 19), 1.00),
          ('bamboo-cluster', *at(11, 15), .96),
          ('garden-rock', *at(20, 16), .84),
          ('canal-quay', *at(24, 27), .70),
          ('river-boat', *at(29, 30), .78),
          ('reeds', *at(21, 30), .86),
      ],
      water=[[19, 31, 14, 8]],
      walls=court(9, 8, 15, 12, gate=15, gw=4),
      beds=[[20, 21, 3, 3]],
      terraces=[[15, 19, 4, 10, 'path'], [20, 25, 8, 4, 'path']])

# 郭外山道（guowai）与运河（canal）由 build_travel_maps.py 从 travel-maps.json 生成。

# 智通寺：雨村「走到山环水绕、茂林深竹之处，看见一座破败寺院」。这一眼要看见寺，
# 所以殿前的院子是外场；只有走进殿门那一刻屋顶才掀开，露出粥锅与佛龛。
stage('zhitong', '扬州郭外 · 智通寺', 'garden',
      zones=[[13, 19, 16, 7], [15, 13, 10, 6, True, 'HALL'], [4, 21, 7, 7], [19, 26, 6, 4]],
      anchors={'entry': [21, 28], 'path': [21, 24], 'guest': [19, 22], 'host': [22, 21],
               'left': [15, 22], 'right': [27, 21], 'rear': [20, 18], 'exit': [28, 23]},
      labels=[['智通寺', 20, 12], ['山门', 19, 19]],
      props=[
          ('zhitong-temple', *at(20, 17), .86, 'HALL'),
          ('gruel-pot', *at(21, 20, -30, 16), .50),
          ('altar-shrine', *at(17, 16, 10, 8), .54, 'HALL'),
          ('bamboo-cluster', *at(25, 24), 1.02),
          ('bamboo-cluster', *at(14, 23), 1.06),
          ('garden-tree', *at(12, 24), 1.32),
          ('garden-rock', *at(24, 24), .86),
      ],
      walls=court(13, 12, 14, 9, gate=19, gw=3),
      beds=[],
      terraces=[walk(19, 19, 4, 7)])

# 村肆：雨村与冷子兴同席沽酒，演说荣宁两府。
stage('tavern', '扬州郭外 · 村肆', 'garden',
      zones=[[12, 14, 16, 10], [16, 24, 5, 6], [26, 20, 6, 4]],
      anchors={'entry': [18, 29], 'path': [18, 25], 'guest': [18, 18], 'host': [20, 16],
               'left': [14, 17], 'right': [23, 15], 'rear': [20, 15], 'exit': [27, 22]},
      labels=[['村肆', 20, 12], ['入城之路', 18, 27]],
      props=[
          ('tavern-house', *at(20, 14), .92),
          ('wine-jars', *at(15, 16), .72),
          ('tea-table', *at(19, 18), .78),
          ('tea-table', *at(23, 19), .72),
          ('round-stool', *at(17, 18), .62),
          ('round-stool', *at(21, 18), .62),
          ('garden-tree', *at(12, 24), 1.16),
          ('garden-tree', *at(27, 21), .98),
      ],
      beds=[],
      terraces=[[16, 20, 4, 9, 'path']])

# ---------------------------------------------------------------------------
# 第三回
# ---------------------------------------------------------------------------

# 宁荣街：街东宁国府、街西荣国府，三间兽头大门各悬一匾，门前一对石狮子。
# 两门相距 10 格（约 640px），一屏之内能同时看见街与两门；原来相距 16 格，
# 镜头对准街心时两座门楼都在画面外，街就只剩一片空地。
stage('capital', '京城 · 宁荣街', 'street',
      zones=[[6, 24, 22, 8, False], [7, 16, 11, 10, False], [19, 16, 11, 10, False],
             [4, 19, 4, 7, False]],
      anchors={'street_west': [26, 28], 'ning_gate': [23, 25], 'rong_gate': [13, 25],
               'west_corner': [5, 25], 'outside': [10, 30]},
      labels=[['宁国府 · 东', 23, 18], ['荣国府 · 西', 13, 18], ['西墙角门', 5, 24],
              ['宁荣街', 18, 29]],
      props=[
          ('manor-main-gate', *at(13, 20), 1.04),
          ('manor-main-gate', *at(23, 20), .92),
          ('stone-lion', *at(10, 24, 10, 0), .58),
          ('stone-lion', *at(16, 24, -10, 0), .58),
          ('stone-lion', *at(20, 24, 10, 0), .52),
          ('stone-lion', *at(26, 24, -10, 0), .52),
          ('west-wall-gate', *at(5, 25), .56),
          ('garden-tree', *at(8, 29), 1.02),
          ('garden-tree', *at(27, 30), 1.04),
      ],
      walls=court(7, 16, 11, 9, gate=12, gw=3) + court(19, 16, 11, 9, gate=22, gw=3),
      beds=[])

# 贾赦院：南墙黑油大门（进门有影壁，轿子停在院心），往里三层仪门，正房是邢夫人房。
# 外院与内院各自成院，正房只占一个屋顶——三段都收在一屏之内。
stage('east', '贾赦院 · 东路小院', 'garden',
      zones=[[10, 21, 16, 8, False], [10, 12, 16, 9, False], [12, 5, 13, 7, True, 'ROOM']],
      anchors={'east_gate': [24, 28], 'small_court': [15, 22], 'bamboo_door': [17, 17],
               'xing_room': [18, 11], 'daiyu_guest': [19, 13], 'xing_host': [17, 11],
               'messenger': [21, 12], 'return_gate': [23, 28]},
      labels=[['黑油大门', 24, 27], ['三层仪门', 17, 19], ['邢夫人房', 18, 9]],
      props=[
          ('black-oil-gate', *at(24, 26), .64),
          # 进门一座影壁，轿子停在影壁前——这是外院唯一的两件东西。
          ('screen-wall', *at(16, 24), .62),
          ('sedan-chair', *at(20, 25), .72),
          ('bamboo-gate', *at(17, 20), .70),
          ('main-hall', *at(18, 11), .76, 'ROOM'),
          ('plain-kang', *at(17, 11, -50, 14), .64, 'ROOM'),
          ('tea-table', *at(19, 12, 40, 6), .56, 'ROOM'),
          ('official-chair', *at(17, 13, -100, 30), .70, 'ROOM'),
          ('garden-tree', *at(12, 20), 1.04),
          ('garden-tree', *at(23, 17), 1.10),
          ('garden-tree', *at(25, 8), .94),
          ('bamboo-cluster', *at(13, 14), .86),
          ('garden-rock', *at(22, 14), .86),
      ],
      walls=court(10, 21, 16, 7, gate=15, gw=3) + court(10, 12, 16, 9, gate=16, gw=3),
      beds=[[11, 14, 2, 2], [24, 14, 2, 2]],
      terraces=[[16, 19, 3, 9, 'path']])

# 荣禧堂：中轴正殿，御笔匾下一张紫檀大案、一座古铜鼎，东廊三间是小耳房。
# 内仪门到堂前只隔 6 格：从仪门望进去正好看见堂门与丹陛，不必走一段空场。
stage('central', '荣府中轴 · 荣禧堂', 'formal',
      zones=[[14, 20, 12, 12, False], [14, 11, 12, 9, True, 'HALL'],
             [8, 10, 5, 14, False], [28, 10, 5, 14, False], [24, 12, 6, 9, False]],
      anchors={'ceremonial_gate': [19, 31], 'inner_gate': [19, 26], 'rongxi_steps': [19, 23],
               'rongxi_door': [19, 20], 'rongxi_center': [20, 16], 'west_room': [14, 14],
               'east_door': [27, 17], 'east_court': [31, 19]},
      labels=[['荣禧堂', 24, 13], ['内仪门', 19, 27], ['西耳房', 13, 15], ['东角门', 29, 19]],
      props=[
          ('rongxi-hall', *at(20, 17), 1.02, 'HALL'),
          # 原文：「大紫檀雕螭案上设着三尺来高青绿古铜鼎……一边是金蜼彝，一边是玻璃盆。
          # 地下两溜十六张楠木交椅。」案在中间，鼎在案上，两溜椅子分列东西，屏在案后。
          ('wood-screen', *at(21, 17, 0, -96), .84, 'HALL'),
          ('altar-table', *at(21, 17, 0, 6), .86, 'HALL'),
          ('taixu-brazier', *at(21, 17, -56, -4), .66, 'HALL'),
          ('taixu-vase', *at(21, 17, 108, 6), .40, 'HALL'),
          ('taixu-vase', *at(21, 17, -120, 8), .40, 'HALL'),
          ('official-chair', *at(21, 17, -232, 6), .74, 'HALL'),
          ('official-chair', *at(21, 17, -266, 62), .74, 'HALL'),
          ('official-chair', *at(21, 17, -300, 118), .74, 'HALL'),
          ('official-chair', *at(21, 17, 232, 6), .74, 'HALL'),
          ('official-chair', *at(21, 17, 266, 62), .74, 'HALL'),
          ('official-chair', *at(21, 17, 300, 118), .74, 'HALL'),
          ('flower-gate', *at(19, 26), .72),
          # 原来西边那株种在西夹道 (11,26)：那儿离任何锚点都在一屏之外，站在内仪门
          # 只看得见空砖地。挪进院里、靠着西墙——镜头扫得到，院里也真有一棵树。
          ('garden-tree', *at(16, 27), 1.08),
          ('garden-tree', *at(28, 26), 1.10),
          ('garden-rock', *at(26, 22), .90),
          ('bamboo-cluster', *at(9, 16), .98),
          ('bamboo-cluster', *at(31, 14), .98),
      ],
      walls=court(14, 16, 12, 15, gate=18, gw=4),
      beds=[[9, 22, 2, 4], [30, 22, 2, 4]],
      terraces=[[18, 21, 4, 9, 'path']])

# 王夫人院东廊三间：炕上靠东壁立着半旧的青缎靠背，地下两溜椅子。
stage('wang', '王夫人院 · 东廊三间', 'interior',
      zones=[[10, 18, 20, 12, False], [13, 9, 13, 9, True, 'ROOM'], [26, 18, 5, 10, False],
             [22, 7, 6, 4, True, 'EAST']],
      anchors={'court_entry': [14, 28], 'hall_entry': [18, 17], 'kang_edge': [19, 11],
               'wang_host': [21, 10], 'guest_seat': [18, 12], 'tea_seat': [22, 13],
               'east_corridor': [28, 19], 'south_passage': [23, 23], 'back_lane': [17, 29],
               'feng_room': [12, 24], 'li_room': [24, 8]},
      labels=[['王夫人起居处', 20, 7], ['东廊', 28, 20], ['夹道', 17, 29], ['凤姐院门', 12, 24]],
      props=[
          ('main-hall', *at(20, 14), .90, 'ROOM'),
          ('plain-kang', *at(18, 12, -40, 6), .78, 'ROOM'),
          ('tea-table', *at(21, 12, 60, 10), .58, 'ROOM'),
          ('official-chair', *at(18, 14, -90, 30), .70, 'ROOM'),
          ('official-chair', *at(23, 14, 60, 26), .70, 'ROOM'),
          ('wood-screen', *at(24, 11, 20, 0), .70, 'ROOM'),
          ('garden-tree', *at(11, 24), 1.04),
          ('garden-tree', *at(30, 18), 1.10),
          ('bamboo-cluster', *at(13, 20), .90),
      ],
      walls=court(10, 8, 20, 20, gate=13, gw=4),
      beds=[[26, 22, 3, 3]],
      terraces=[[13, 22, 4, 8, 'path']])

# 贾母后房晚膳：正面榻上独坐，两边四张空椅，李纨捧饭、凤姐安箸、王夫人进羹。
stage('dinner', '贾母院 · 后房与晚膳', 'interior',
      zones=[[14, 10, 11, 9, True, 'ROOM']],
      anchors={'back_door': [14, 18], 'grandmother_place': [19, 12], 'daiyu_place': [20, 13],
               'wang_place': [22, 13], 'feng_place': [23, 12], 'yingchun_place': [16, 15],
               'tanchun_place': [17, 16], 'xichun_place': [18, 17], 'liwan_place': [16, 12],
               'baoyu_greet': [21, 13], 'grandmother_greet': [20, 12],
               'maid_place': [23, 16], 'tea_place': [21, 17]},
      labels=[['后房', 14, 18], ['贾母房 · 晚膳', 20, 10]],
      props=[
          ('main-hall', *at(19, 13), .92, 'ROOM'),
          # 正面榻上独坐：榻在北墙下，四张椅子分列桌案两边。
          ('daybed', *at(19, 11, 0, 0), .76, 'ROOM'),
          ('dining-table', *at(19, 14, 0, 20), .78, 'ROOM'),
          ('official-chair', *at(19, 14, -140, 30), .72, 'ROOM'),
          ('official-chair', *at(19, 14, -140, -18), .68, 'ROOM'),
          ('official-chair', *at(19, 14, 140, 30), .72, 'ROOM'),
          ('official-chair', *at(19, 14, 140, -18), .68, 'ROOM'),
          ('lamp-stand', *at(23, 11, 0, 0), .72, 'ROOM'),
          ('wood-screen', *at(15, 11, 0, 0), .68, 'ROOM'),
          ('taixu-vase', *at(23, 15, 0, 0), .60, 'ROOM'),
      ],
      beds=[])

# 碧纱橱与外间：贾母套间，宝玉睡在碧纱橱外的大床上，袭人坐在床边。
stage('night', '贾母院 · 碧纱橱与外间', 'night',
      zones=[[14, 10, 10, 8, True, 'ROOM']],
      anchors={'outer_door': [15, 17], 'grandmother_bed': [17, 11], 'daiyu_bed': [20, 12],
               'baoyu_bed': [17, 15], 'xiren_place': [18, 16], 'xueyan_place': [21, 13],
               'yingge_place': [21, 11], 'bedside': [20, 13], 'night_talk': [19, 14],
               'letter_place': [16, 15]},
      labels=[['贾母套间', 16, 11], ['碧纱橱', 21, 10], ['外间暖阁', 17, 16]],
      props=[
          ('main-hall', *at(19, 13), .92, 'ROOM'),
          # 碧纱橱：一架纱橱隔出里外，黛玉在橱内，宝玉在橱外大床上。
          ('qin-bed', *at(20, 12, 0, 0), .62, 'ROOM'),
          ('taixu-bed', *at(17, 11, 0, 0), .60, 'ROOM'),
          ('canopy-bed', *at(17, 15, 0, 0), .62, 'ROOM'),
          ('wood-screen', *at(19, 13, 30, -10), .70, 'ROOM'),
          ('lamp-stand', *at(22, 15, 0, 0), .70, 'ROOM'),
          ('tea-table', *at(15, 14, 0, 0), .58, 'ROOM'),
          ('taixu-vase', *at(22, 12, 30, -10), .52, 'ROOM'),
      ],
      beds=[])

# 贾政书房：外书房，案上摊着书，雨村来访，屏风隔出里外。
stage('yucun', '京城 · 贾政书房', 'formal',
      zones=[[10, 8, 20, 18], [12, 9, 16, 12, True, 'ROOM']],
      anchors={'visitor': [17, 21], 'host': [20, 13], 'guest': [18, 15], 'door': [17, 25]},
      labels=[['贾政书房', 20, 10]],
      props=[
          ('main-hall', *at(20, 15), .80, 'ROOM'),
          ('bookshelf', *at(20, 13, -110, 0), .72, 'ROOM'),
          ('writing-desk', *at(20, 13, 40, 18), .78, 'ROOM'),
          ('tea-table', *at(18, 15, -40, 10), .60, 'ROOM'),
          ('round-stool', *at(18, 15, -100, 16), .62, 'ROOM'),
          ('wood-screen', *at(24, 12, 0, 0), .68, 'ROOM'),
          ('garden-tree', *at(10, 23), 1.06),
          # 东边那株原在 (28,20)，正落在书房地坪里、又在客位一屏之外——掀了顶是一棵树
          # 杵在屋里，盖上顶又谁都看不见。挪到院东南，与西边那株夹着院子。
          ('garden-tree', *at(27, 23), 1.02),
      ],
      walls=court(10, 8, 20, 18, gate=16, gw=4),
      beds=[[26, 22, 3, 3]],
      terraces=[[16, 22, 4, 5, 'path']])
