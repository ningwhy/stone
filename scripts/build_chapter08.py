#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter-eight maps, its playable script and its section table.

第八回 · 比通灵金莺微露意 · 探宝钗黛玉半含酸

Chapter eight owns this generator; nothing here touches build_chapter07.py,
so re-running it cannot overwrite an earlier chapter.

Outputs (printed at the end):
  artifacts/staging/chapter08/chapter08-story.json      nodes C08-001..
  artifacts/staging/chapter08/chapter08-sections.json   sections: c8-pear .. c8-anger
  (复用 maps: c7_lixiang 梨香院；night 贾母院)

本回新建舞台：无。探宝钗在梨香院正房（薛姨妈与宝钗同居一院），黛玉赶到亦在
梨香院；李嬷嬷拦酒在贾母院宝玉房。

人物：莺儿（ying_er）为本回新立绘；宝钗、薛姨妈、黛玉、宝玉、雪雁、袭人、李嬷嬷
均复用既有资产。

Usage: python3 scripts/build_chapter08.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from stage_defs import fit  # noqa: E402

# 第八回已接入 story：产物直接进入 design/（check:content 要求 chapterNN-source.txt
# 与 design/chapterNN-*.json 同时存在，且 story.ts 显式 import 后方可登记）。
STAGE_DIR = ROOT / 'design'

# 本回不新建地图：复用第七回的梨香院与既有的贾母院。
scenes = {}

SECTIONS = [
    ('c8-pear', '梨香院 · 探宝钗', 'c7_lixiang'),
    ('c8-gold', '梨香院 · 金莺微露意', 'c7_lixiang'),
    ('c8-sour', '梨香院 · 黛玉半含酸', 'c7_lixiang'),
    ('c8-lunch', '梨香院 · 酸笋鸡皮汤', 'c7_lixiang'),
    ('c8-anger', '贾母院 · 摔杯怒李嬷嬷', 'night'),
]

steps = []
current = {}
section_titles = {a: b for a, b, c in SECTIONS}


def section(ch, scene, place, focus, lead, layer='present'):
    global current
    current = {'chapter': ch, 'scene': scene, 'place': place, 'focus': focus,
               'source': {'chapter': 8, 'paragraphLead': lead, 'textKind': 'adaptation',
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


# ===== c8-pear : 梨香院 · 探宝钗 ============================
section('c8-pear', 'c7_lixiang', '梨香院 · 薛姨妈处', 'yard',
        '宝玉便一溜烟跑了来，一直到了梨香院门口')
say('C08-001', 'narrator',
    '宝玉听说宝钗的病犯了，便辞了贾母，一溜烟往梨香院来。', '往梨香院',
    [show('baoyu', 'entry')])
say('C08-002', 'narrator',
    '进了院门，宝钗正与薛姨妈说话；宝玉相见，问宝钗之病。', '相见问病',
    [show('baochai', 'baochai'), show('xueyima', 'xueyima'),
     move('baoyu', 'entry', 'yard', 'room')])
say('C08-003', 'baochai',
    '宝钗道：“我的病已大好了，多亏姨妈疼我，请了大夫，吃了两剂药。”', '病已大好')
say('C08-004', 'narrator',
    '宝玉见宝钗唇不点而红，眉不画而翠，脸若银盆，眼如水杏，比别个不同， \
  便患上几分留意。', '宝钗之态', [effect('baochai', 'idle')])
say('C08-005', 'baochai',
    '宝钗道：“你那块玉，我倒没仔细瞧过，今儿你来了，必得给我看看。”', '要看通灵玉',
    [move('baoyu', 'room', 'baochai')])

# ===== c8-gold : 金莺微露意 ============================
section('c8-gold', 'c7_lixiang', '梨香院 · 宝钗房中', 'baochai',
        '宝玉听说莺儿来了，转过头来，就把手伸了伸')
say('C08-010', 'narrator',
    '宝玉便把玉解下来，递与宝钗；宝钗翻来覆去念道：“莫失莫忘，仙寿恒昌。”',
    '通灵玉八字')
say('C08-011', 'baochai',
    '宝钗笑道：“我也有一个是和尚给的，你看看。”说毕，莺儿便捧了金锁出来。',
    '金锁出场', [show('ying_er', 'baochai')])
say('C08-012', 'ying_er',
    '莺儿笑道：“是个癞头和尚送的，他说必须錾在金器上——”', '莺儿失言',
    [effect('ying_er', 'idle')])
say('C08-013', 'baochai',
    '宝钗猛回头嗔道：“你这丫头，疯了！还不出去？”莺儿嘻嘻笑着退下。', '宝钗嗔莺儿',
    [move('ying_er', 'baochai', 'yard')])
say('C08-014', 'narrator',
    '宝玉看那金锁，两面錾着八个字：“不离不弃，芳龄永继。”笑道：“姐姐这八个字， \
  倒真与我的是一对。”', '金玉一对', [show('baoyu', 'baochai')])

# ===== c8-sour : 黛玉半含酸 ============================
section('c8-sour', 'c7_lixiang', '梨香院 · 宝钗房中', 'baochai',
        '正说着，只听外面一阵脚步响，黛玉来了')
say('C08-020', 'narrator',
    '正说着，外面一阵脚步响，黛玉来了；一进门便笑道：“我来得不巧了！”',
    '黛玉赶到', [show('daiyu', 'entry'), move('daiyu', 'entry', 'yard', 'room')])
say('C08-021', 'daiyu',
    '黛玉笑道：“你既吃了我们家的茶，怎么还不给我们家作媳妇？”说罢，拿眼睛瞟着宝玉。',
    '半含酸', [effect('daiyu', 'idle')])
say('C08-022', 'narrator',
    '宝玉见宝钗腕上笼着红麝串，要看时宝钗褪将下来，宝玉看着宝钗雪白一段酥臂， \
  不觉看呆了。', '看红麝串', [show('baoyu', 'baochai')])
say('C08-023', 'daiyu',
    '忽见雪雁送手炉来，黛玉便借话敲打：“也亏你倒听她的话。我平日和你说的， \
  全当耳旁风。”雪雁红了脸。', '敲打雪雁', [show('xueyan', 'yard')])

# ===== c8-lunch : 酸笋鸡皮汤 ============================
section('c8-lunch', 'c7_lixiang', '梨香院 · 薛姨妈处', 'room',
        '薛姨妈便命摆酒饭，宝玉吃了半碗酸笋鸡皮汤')
say('C08-030', 'narrator',
    '薛姨妈留饭，摆上酒果；宝玉高兴，便要喝两盅。', '薛姨妈留饭',
    [show('baoyu', 'room'), show('xueyima', 'xueyima')])
say('C08-031', 'baochai',
    '宝钗笑道：“宝兄弟，你妈天天叫你不要喝酒，姨妈这里你便依不得。”', '宝钗劝酒')
say('C08-032', 'narrator',
    '宝玉吃了半碗酸笋鸡皮汤，高兴道：“这个汤倒好！”薛姨妈又拿鹅掌鸭信与他下酒。',
    '酸笋鸡皮汤', [effect('baoyu', 'idle')])
say('C08-033', 'daiyu',
    '黛玉冷眼瞧着，故意道：“落雪时行酒令，也是你赢的，偏今儿连冷酒也不敢吃。” \
  宝玉听这话有因，便放下冷酒。', '借酒敲打', [move('daiyu', 'room', 'xueyima')])

# ===== c8-anger : 摔杯怒李嬷嬷 ============================
section('c8-anger', 'night', '贾母院 · 宝玉房中', 'baoyu_bed',
        '那李嬷嬷又来找宝玉')
say('C08-040', 'narrator',
    '宝玉带着酒兴回到贾母院，在房中歪着歇息。', '回贾母院',
    [show('baoyu', 'outer_door'), move('baoyu', 'outer_door', 'baoyu_bed')])
say('C08-041', 'nurse_li',
    '李嬷嬷上来拦道：“你可反了！爷们回来了，怎么不通报一声，就歪在这里？”',
    '李嬷嬷拦', [show('nurse_li', 'xiren_place')])
say('C08-042', 'nurse_li',
    '李嬷嬷又拿前日枫露茶、奶酪的事数落，一句紧似一句；宝玉本带着酒，心中早不耐烦。',
    '旧账重提')
say('C08-043', 'baoyu',
    '宝玉腾地摔了手边茶钟，怒道：“撵出去！谁许你这般放肆！”', '摔杯大怒',
    [effect('baoyu', 'anger')])
say('C08-044', 'xiren',
    '袭人忙起身按住宝玉，陪笑向李嬷嬷道：“姨奶奶别恼，他今儿吃多了，我慢慢劝。” \
  扶了宝玉睡下。', '袭人解劝', [show('xiren', 'xiren_place')])


def build_story():
    ids = [s['id'] for s in steps]
    assert len(ids) == len(set(ids)), 'duplicate node id'
    for s in steps:
        assert s['chapter'] in section_titles, f"{s['id']}: unknown section"
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    (STAGE_DIR / 'chapter08-story.json').write_text(
        json.dumps(steps, ensure_ascii=False, indent=1) + '\n')
    firsts = {}
    for s in steps:
        firsts.setdefault(s['chapter'], s['id'])
    sections = [{'id': sid, 'title': title, 'scene': scene, 'start': firsts[sid], 'book': 8}
                for sid, title, scene in SECTIONS]
    (STAGE_DIR / 'chapter08-sections.json').write_text(
        json.dumps(sections, ensure_ascii=False, indent=1) + '\n')
    return len(steps), len(sections)


if __name__ == '__main__':
    n_steps, n_sections = build_story()
    print('story : design/chapter08-story.json  %d nodes' % n_steps)
    print('sect  : design/chapter08-sections.json  %d sections' % n_sections)
