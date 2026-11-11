#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 20 回的剧情、段落、证据数据。

第 20 回底本是维基文库原文全文（docs/chapter20-source.txt），
写法沿用第 18/19 回确立的**底本切片式生成**：不手写正文，
按「起句标记 → 止句标记」切片，正文与 source.paragraphLead 都是切出来的。

用法：
    python3 scripts/build_chapter20.py            # 生成
    python3 scripts/build_chapter20.py --check    # 只校验已有文件

场景与人物（对照 docs/chapter20-production.md 的分场规划）：
  night        怡红院（外间/炕/灯前）—— 李嬷嬷骂袭人、凤姐撮去、麝月守夜、晴雯撞见
  c7_lixiang   梨香院 · 薛姨妈处 —— 贾环赶围棋、莺儿赖钱、宝玉解劝
  wang         王夫人院 —— 赵姨娘骂贾环、凤姐隔窗正言
  dinner       贾母院 —— 史湘云到、黛玉赌气、湘云打趣"爱哥哥"
人物：袭人(xiren)、李嬷嬷(nurse_li)、宝钗(baochai)、黛玉(daiyu)、宝玉(baoyu)、凤姐(feng)、
莺儿(ying_er)、香菱(maid 代指) 已在 cast；
新增 4 名需美术：贾环(jia_huan)、赵姨娘(zhao_yiniang)、史湘云(shi_xiangyun)、麝月(she_yue)；
晴雯/绮霰/秋纹/碧痕/鸳鸯/琥珀/丰儿 以 messenger 代指（不新增美术）。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter20-source.txt'
STORY = ROOT / 'design' / 'chapter20-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter20-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter20-evidence.json'

STRIP_RE = re.compile(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-]')
QUOTE_MAP = {c: '"' for c in '“”「」『』‘’'}


def strip_marks(text: str) -> str:
    return STRIP_RE.sub('', text)


def normalize(text: str) -> str:
    return ''.join(QUOTE_MAP.get(c, c) for c in text)


def load_base():
    raw = BASE.read_text(encoding='utf-8')
    raw = re.sub(r'<section(?:begin|end)="[^"]*"\s*/>', '', raw)
    raw = re.sub(r'==注释==.*', '', raw, flags=re.S)
    body = raw.split('================================================')[-1]

    paras, offsets = [], []
    cursor = body.index('\n\n') + 2 if '\n\n' in body else 0
    for chunk in body.split('\n\n'):
        chunk = chunk.strip()
        if not chunk:
            continue
        start = body.index(chunk, cursor)
        offsets.append(start)
        paras.append(chunk)
        cursor = start + len(chunk)

    norm_chars, origin = [], []
    for i, ch in enumerate(body):
        norm_chars.append(QUOTE_MAP.get(ch, ch))
        origin.append(i)
    norm_body = ''.join(norm_chars)

    norm_ranges = []
    for off, p in zip(offsets, paras):
        norm_ranges.append((off, off + len(normalize(p))))
    return body, paras, offsets, norm_body, origin, norm_ranges


BODY, PARAS, OFFSETS, NORM_BODY, ORIGIN, NORM_RANGES = load_base()


def para_end(para: int) -> int:
    off = OFFSETS[para]
    return off + len(PARAS[para])


def cut(para: int, start: str, end=None):
    """从底本第 para 段起、到 end 之前切出一段文字（同第 18/19 回）。"""
    ns, ne = NORM_RANGES[para]
    n = NORM_BODY.find(normalize(start), ns, ne)
    if n < 0:
        raise ValueError(f'第 {para} 段找不到起句：{start}')
    orig_start = ORIGIN[n]
    lead = BODY[orig_start:orig_start + len(start)]

    if end is None:
        orig_end = para_end(para)
    elif end.startswith('@P'):
        orig_end = para_end(int(end[2:]))
    else:
        m = NORM_BODY.find(normalize(end), n + len(start))
        if m < 0:
            raise ValueError(f'第 {para} 段起句「{start}」之后找不到止句：{end}')
        orig_end = ORIGIN[m]
        if orig_end - orig_start > 900:
            raise ValueError(f'起句「{start}」与止句「{end}」相距过远（{orig_end - orig_start} 字），标记可能有误')
    if orig_end <= orig_start:
        raise ValueError(f'第 {para} 段的起止顺序不对：{start} → {end}')
    return BODY[orig_start:orig_end].replace('\n\n', '\n'), lead


def split_sentences(text: str):
    """按句末标点切句，闭合引号归到前一句。

    ★ 与第 18/19 回的字符串标记法相比，句号索引是唯一无歧义的定位方式：
      底本里有大量同形短句（「说的是他」「我知道了」），字符串 find 会命中前一处，
      导致切到别人的字；句号唯一定位，且天然保证节点顺序单调。
    """
    parts = re.split(r'(?<=[。！？])', text)
    out = []
    for s in parts:
        if not s:
            continue
        if out and s[0] in '」』':
            out[-1] = out[-1] + s[0]
            s = s[1:]
            if not s:
                continue
        out.append(s)
    return out


SENTENCES = {i: split_sentences(p) for i, p in enumerate(PARAS)}


def cut_sent(para: int, s_from: int, s_to: int):
    """切出底本第 para 段的第 [s_from, s_to) 句。

    返回 (正文, 起句原文)。起句取该区间的第一句，
    保证 paragraphLead 是底本里逐字可查的起句。
    """
    sents = SENTENCES[para]
    if not (0 <= s_from < s_to <= len(sents)):
        raise ValueError(f'第 {para} 段句号 [{s_from}, {s_to}) 越界（共 {len(sents)} 句）')
    raw = ''.join(sents[s_from:s_to])
    lead = sents[s_from]
    if not raw.startswith(lead):
        raise ValueError(f'第 {para} 段第 {s_from} 句定位失败：{lead[:20]}')
    return raw, lead


def to_display(text: str) -> str:
    """底本弯引号 → 「」『』，只换标点不动字（第 16-19 回同一读法）。"""
    return text.replace('‘', '『').replace('’', '』').replace('“', '「').replace('”', '」')


# ---------------------------------------------------------------- 动作速记
def parse_actions(codes):
    out = []
    for code in codes:
        kind = code[0]
        if kind == 'S':
            _, actor, at = code.split(':')
            out.append({'type': 'show', 'actor': actor, 'at': at})
        elif kind == 'H':
            _, actor = code.split(':')
            out.append({'type': 'hide', 'actor': actor})
        elif kind == 'M':
            _, actor, path = code.split(':')
            out.append({'type': 'move', 'actor': actor, 'via': path.split('>')})
        elif kind == 'E':
            _, actor, kind2, dur = code.split(':')
            out.append({'type': 'effect', 'actor': actor, 'kind': kind2, 'duration': float(dur)})
        else:
            raise ValueError(f'看不懂的动作记法：{code}')
    return out


# ---------------------------------------------------------------- 段落定义
# 分段按底本顺序推进，每段一个场景：换场只在底本真的换了地方时发生。
SECTIONS = [
    ('c20-momo', '怡红院 · 李嬷嬷骂袭人', 'night'),
    ('c20-fengjie', '怡红院 · 凤姐排揎', 'night'),
    ('c20-shuyao', '怡红院 · 麝月守夜篦头', 'night'),
    ('c20-jinghuan', '梨香院 · 赶围棋赖钱', 'c7_lixiang'),
    ('c20-tanyi', '王夫人院 · 凤姐正言', 'wang'),
    ('c20-xiangyun', '贾母院 · 湘云到来', 'dinner'),
    ('c20-qiaoyu', '贾母院 · 亲不间疏', 'dinner'),
]

# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题, 地点, 底本段号, 起始句号, 结束句号, 动作)
# 句号是「句」的下标（见 split_sentences 的切分规则），范围为 [起, 止)。
# 用句号而不是字符串标记：底本句子里有大量同形短句（「我知道了」「说的是他」），
# 字符串检索会命中前一处，切到别人的字；句号唯一定位，且天然保证节点顺序单调。
#
# 底本顺序（段号, 句号）必须全局单调递增——check() 会逐对校验。
# 段 3 末尾（凤姐拉走李嬷嬷）与段 4 开头（黛玉宝钗劝说）之间，
# 底本里凤姐拉人发生在劝说之后，节点按底本先后排，不按"戏"排。
CUTS = [
    # ---------------- 段一：怡红院 · 李嬷嬷骂袭人 ----------------
    ('c20-momo', 'C20-001', 'narrator', '房中嚷起来，大家侧耳听了一听', '怡红院 · 外间', 1, 2, 4,
     ['S:daiyu:daiyu_bed', 'S:baochai:yingge_place']),
    ('c20-momo', 'C20-002', 'narrator', '宝玉忙要赶过来，宝钗忙一把拉住', '怡红院 · 外间', 2, 0, 2,
     ['S:baoyu:outer_door', 'E:baochai:greet:1.2']),
    ('c20-momo', 'C20-003', 'narrator', '李嬷嬷拄著拐棍，在当地骂袭人', '怡红院 · 外间', 2, 2, 3,
     ['S:nurse_li:xiren_place', 'S:xiren:baoyu_bed']),
    ('c20-momo', 'C20-004', 'nurse_li', '忘了本的小娼妇', '怡红院 · 外间', 2, 3, 7,
     ['E:nurse_li:greet:1.4']),
    ('c20-momo', 'C20-005', 'narrator', '由不得又愧又委屈，禁不住哭起来', '怡红院 · 外间', 2, 7, 9,
     ['E:xiren:rest:1.4']),

    # ---------------- 段二：怡红院 · 凤姐排揎 ----------------
    ('c20-fengjie', 'C20-006', 'baoyu', '你不信，只问别的丫头们', '怡红院 · 外间', 3, 0, 1,
     ['S:baoyu:outer_door', 'E:baoyu:greet:1.2']),
    ('c20-fengjie', 'C20-007', 'nurse_li', '你只护著那起狐狸', '怡红院 · 外间', 3, 1, 7,
     ['E:nurse_li:greet:1.4']),
    ('c20-fengjie', 'C20-008', 'narrator', '彼时黛玉宝钗等也走过来劝说', '怡红院 · 外间', 3, 7, 9,
     ['S:daiyu:daiyu_bed', 'S:baochai:yingge_place']),
    ('c20-fengjie', 'C20-009', 'narrator', '便知是李嬷嬷老病发了', '怡红院 · 外间', 3, 9, 11,
     ['S:feng:outer_door']),
    ('c20-fengjie', 'C20-010', 'feng', '好妈妈，别生气', '怡红院 · 外间', 3, 11, 15,
     ['M:feng:outer_door>xiren_place', 'E:feng:greet:1.4']),
    ('c20-fengjie', 'C20-011', 'narrator', '宝玉替他吃了药，命小丫头子们铺炕', '怡红院 · 外间', 4, 0, 4,
     ['E:baoyu:rest:1.2']),

    # ---------------- 段三：怡红院 · 麝月守夜与篦头 ----------------
    ('c20-shuyao', 'C20-012', 'narrator', '独见麝月一个人在外间房里灯下抹骨牌', '怡红院 · 外间', 4, 5, 8,
     ['S:she_yue:yingge_place']),
    ('c20-shuyao', 'C20-013', 'she_yue', '没有钱', '怡红院 · 外间', 4, 8, 10,
     ['S:baoyu:bedside', 'E:she_yue:greet:1.2']),
    ('c20-shuyao', 'C20-014', 'narrator', '那一个又病了，满屋里上头是灯', '怡红院 · 外间', 4, 10, 16,
     ['E:she_yue:rest:1.2']),
    ('c20-shuyao', 'C20-015', 'narrator', '公然又是一个袭人', '怡红院 · 外间', 5, 0, 2,
     ['E:baoyu:rest:1.2']),
    ('c20-shuyao', 'C20-016', 'baoyu', '我替你篦头罢', '怡红院 · 外间', 5, 2, 7,
     ['M:baoyu:bedside>yingge_place', 'E:baoyu:greet:1.2']),
    ('c20-shuyao', 'C20-017', 'narrator', '晴雯冷笑：交杯盏还没吃，倒上头了', '怡红院 · 外间', 5, 7, 12,
     ['S:messenger:outer_door', 'E:messenger:greet:1.2']),

    # ---------------- 段四：梨香院 · 赶围棋赖钱 ----------------
    ('c20-jinghuan', 'C20-018', 'narrator', '宝钗香菱莺儿三个赶围棋作耍', '梨香院 · 廊下', 6, 13, 19,
     ['S:jia_huan:yard', 'S:baochai:room', 'S:ying_er:room']),
    ('c20-jinghuan', 'C20-019', 'narrator', '若掷个七点便赢，若掷个六点', '梨香院 · 廊下', 6, 19, 22,
     ['E:jia_huan:rest:1.2']),
    ('c20-jinghuan', 'C20-020', 'narrator', '贾环急了，伸手便抓起骰子来', '梨香院 · 廊下', 6, 22, 25,
     ['E:jia_huan:greet:1.2']),
    ('c20-jinghuan', 'C20-021', 'ying_er', '一个作爷的，还赖我们这几个钱', '梨香院 · 廊下', 6, 28, 31,
     ['E:ying_er:greet:1.2']),
    ('c20-jinghuan', 'C20-022', 'jia_huan', '你们怕他，都和他好', '梨香院 · 廊下', 6, 31, 35,
     ['E:jia_huan:rest:1.4']),

    # ---------------- 段五：王夫人院 · 凤姐隔窗正言 ----------------
    ('c20-tanyi', 'C20-023', 'narrator', '赵姨娘啐骂下流没脸的东西', '王夫人院 · 东廊', 7, 2, 6,
     ['S:zhao_yiniang:east_corridor', 'S:jia_huan:east_corridor', 'E:zhao_yiniang:greet:1.4']),
    ('c20-tanyi', 'C20-024', 'feng', '大正月又怎么了', '王夫人院 · 东廊', 7, 8, 13,
     ['S:feng:south_passage', 'E:feng:greet:1.4']),
    ('c20-tanyi', 'C20-025', 'narrator', '他现是主子，与你什么相干', '王夫人院 · 东廊', 7, 13, 15,
     ['E:zhao_yiniang:rest:1.2']),
    ('c20-tanyi', 'C20-026', 'feng', '输了几个钱，就这么个样儿', '王夫人院 · 东廊', 7, 15, 21,
     ['M:jia_huan:east_corridor>south_passage', 'E:feng:greet:1.4']),
    ('c20-tanyi', 'C20-027', 'narrator', '贾环诺诺的跟了丰儿，得了钱', '王夫人院 · 东廊', 7, 26, 29,
     ['H:zhao_yiniang', 'E:jia_huan:rest:1.0']),

    # ---------------- 段六：贾母院 · 湘云到来与黛玉赌气 ----------------
    # 原著：「宝玉正和宝钗顽笑，忽见人说史大姑娘来了」——宝玉、宝钗同在。
    ('c20-xiangyun', 'C20-028', 'narrator', '忽见人说：史大姑娘来了', '贾母院 · 堂前', 8, 0, 4,
     ['S:baoyu:grandmother_greet', 'S:baochai:wang_place', 'S:shi_xiangyun:grandmother_greet',
      'E:shi_xiangyun:greet:1.4']),
    ('c20-xiangyun', 'C20-029', 'daiyu', '在那里的', '贾母院 · 堂前', 8, 5, 7,
     ['S:daiyu:daiyu_place', 'E:daiyu:greet:1.2']),
    ('c20-xiangyun', 'C20-030', 'daiyu', '亏在那里绊住，不然早就飞了来了', '贾母院 · 堂前', 8, 7, 10,
     ['E:daiyu:greet:1.4']),
    ('c20-xiangyun', 'C20-031', 'narrator', '便赌气回房去了', '贾母院 · 堂前', 8, 10, 14,
     ['M:daiyu:daiyu_place>back_door']),

    # ---------------- 段七：贾母院 · 亲不间疏，先不僭后 ----------------
    ('c20-qiaoyu', 'C20-032', 'narrator', '宝玉忙跟了来', '贾母院 · 堂前', 9, 0, 3,
     ['M:baoyu:grandmother_greet>daiyu_place', 'E:baoyu:greet:1.2']),
    ('c20-qiaoyu', 'C20-033', 'daiyu', '我作践坏了身子，我死，与你何干', '贾母院 · 堂前', 9, 5, 6,
     ['E:daiyu:greet:1.4']),
    ('c20-qiaoyu', 'C20-034', 'narrator', '宝钗走来推宝玉走了', '贾母院 · 堂前', 9, 14, 16,
     ['S:baochai:wang_place', 'E:baochai:rest:1.2']),
    ('c20-qiaoyu', 'C20-035', 'narrator', '黛玉越发气闷，只向窗前流泪', '贾母院 · 堂前', 9, 16, 17,
     ['E:daiyu:rest:1.4']),
    ('c20-qiaoyu', 'C20-036', 'narrator', '亲不间疏，先不僭后', '贾母院 · 堂前', 10, 6, 10,
     ['E:baoyu:greet:1.2']),
    ('c20-qiaoyu', 'C20-037', 'narrator', '湘云走来笑说：也不理我一理儿', '贾母院 · 堂前', 11, 0, 1,
     ['S:shi_xiangyun:grandmother_greet', 'E:shi_xiangyun:greet:1.2']),
    ('c20-qiaoyu', 'C20-038', 'daiyu', '偏是咬舌子爱说话', '贾母院 · 堂前', 11, 1, 3,
     ['E:daiyu:greet:1.4']),
    ('c20-qiaoyu', 'C20-039', 'narrator', '我只保佑著明儿得一个咬舌的林姐夫', '贾母院 · 堂前', 11, 13, 17,
     ['E:shi_xiangyun:greet:1.4']),
]

# ---------------------------------------------------------------- 设计推定
DESIGN_NOTES = [
    ('C20-D001', 'c20-momo',
     '怡红院借用 night 图（贾母院碧纱橱与外间）占位',
     '原文是宝玉房中（外间、炕、灯下抹骨牌）；项目尚无怡红院专图。',
     '用 night 的 outer_door/xiren_place/yingge_place/baoyu_bed/bedside 表现外间、炕前与灯前。'),
    ('C20-D002', 'c20-jinghuan',
     '赶围棋一场借用 c7_lixiang 图（梨香院 · 薛姨妈处）',
     '原文说宝玉饭后到薛姨妈这边闲逛，正遇见宝钗、香菱、莺儿三个赶围棋作耍。',
     'c7_lixiang 正是薛姨妈处，有 baochai/zhou（莺儿位）/room/yard 锚点，可表现廊下围棋。'),
    ('C20-D003', 'c20-tanyi',
     '赵姨娘与贾环一场借用 wang 图（王夫人院 · 东廊三间）',
     '原文只说「可巧凤姐在窗外过」并「隔窗说道」，未给平面；赵姨娘住贾政外院偏所。',
     '用 wang 的 east_corridor/south_passage 表现窗外过与隔窗说话的位置关系。'),
    ('C20-D004', 'c20-xiangyun',
     '贾母院借用 dinner 图占位；黛玉处沿用 dinner 的 daiyu_place',
     '原文写「同宝玉一齐来至贾母这边」，此后黛玉赌气回房（此时黛玉仍在贾母院碧纱橱）。',
     '用 dinner 的 grandmother_greet/daiyu_place/back_door/room 表现堂前与回房。'),
    ('C20-D005', 'c20-shuyao',
     '晴雯、绮霰、秋纹、碧痕、鸳鸯、琥珀、丰儿以 messenger 代指',
     '底本点名七名丫鬟，但除晴雯有两句台词外均无独立戏份。',
     '避免美术膨胀：晴雯用 messenger 承担两句冷语，其余丫鬟只在叙述中出现、不 show。'),
    ('C20-D006', 'c20-jinghuan',
     '香菱以 maid 代指',
     '底本香菱只在「宝钗，香菱，莺儿三个赶围棋作耍」一句里出现，无台词。',
     '香菱不 show，由宝钗与莺儿代表这一组人。'),
]


def build():
    steps = []
    for sec_id, nid, speaker, title, place, para, s_from, s_to, codes in CUTS:
        raw, lead = cut_sent(para, s_from, s_to)
        steps.append({
            'chapter': sec_id,
            'scene': None,
            'place': place,
            'focus': '',
            'source': {
                'chapter': 20,
                'paragraphLead': lead,
                'textKind': 'adaptation',
                'layer': 'present',
            },
            'id': nid,
            'speaker': speaker,
            'text': to_display(raw),
            'title': title,
            'actions': parse_actions(codes),
        })
    return steps


def assign_scenes(steps):
    scene_of = {s[0]: s[2] for s in SECTIONS}
    last_focus = {}
    for step in steps:
        step['scene'] = scene_of[step['chapter']]
        focus = ''
        for act in step['actions']:
            if act['type'] == 'show':
                focus = act['at']
                break
        if not focus:
            for act in step['actions']:
                if act['type'] == 'move' and act['via']:
                    focus = act['via'][-1]
                    break
        if not focus:
            focus = last_focus.get(step['chapter'], '')
        step['focus'] = focus
        if focus:
            last_focus[step['chapter']] = focus


def check(steps):
    errors = []
    ids = [s['id'] for s in steps]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f'节点 id 重复：{sorted(dupes)}')

    stripped_base = strip_marks(BODY)
    section_ids = {s[0] for s in SECTIONS}
    for step in steps:
        nid = step['id']
        if step['chapter'] not in section_ids:
            errors.append(f'{nid}: 段落 id {step["chapter"]} 不在 sections 中')
        lead = step['source']['paragraphLead']
        if not lead.strip():
            errors.append(f'{nid}: lead 为空')
        elif strip_marks(lead) not in stripped_base:
            errors.append(f'{nid}: lead 在底本中查不到 —— {lead}')
        text = strip_marks(step['text'])
        if not text:
            errors.append(f'{nid}: 正文为空')
        elif text not in stripped_base:
            errors.append(f'{nid}: 正文不在底本中 —— {step["text"][:40]}')
        if not step['focus']:
            errors.append(f'{nid}: 没有落点（focus 为空）')
    # 节点必须按底本顺序单调推进（段落+段内偏移）。
    pos = []
    for step in steps:
        nl = normalize(step['source']['paragraphLead'])
        for i, p in enumerate(PARAS):
            if nl in normalize(p):
                off = normalize(p).find(nl)
                pos.append((i, off))
                break
        else:
            pos.append((-1, -1))
    for i in range(len(pos) - 1):
        if pos[i] >= pos[i + 1]:
            errors.append(f'{steps[i]["id"]} → {steps[i+1]["id"]}: 节点顺序与底本顺序不符（{pos[i]} → {pos[i+1]}）')
    errors.extend(check_stage(steps))
    return errors


def check_stage(steps):
    """舞台连续性：谁在台上，谁可以动。

    引擎只在**换场景**时清空舞台（engine.ts 的 enter()），同一场景里角色的
    可见性一直保持。所以「move 一个从没 show 过的人」会在运行期抛
    「移动角色未显示」，而且它是在读者点到那一步时才炸——必须在这里拦住。

    只有 move 会在运行期抛错：effect 只是播一个特效，hide 对不在台上的角色
    也是空操作。所以这里只查 move。
    """
    errors = []
    onstage = {}
    scene = None
    for step in steps:
        if step['scene'] != scene:
            onstage = {}          # 换场景 → 舞台重置
            scene = step['scene']
        for action in step.get('actions', []):
            actor = action.get('actor')
            if not actor:
                continue
            kind = action['type']
            if kind == 'show':
                onstage[actor] = step['id']
            elif kind == 'hide':
                onstage.pop(actor, None)
            elif kind == 'move' and actor not in onstage:
                errors.append(f'{step["id"]}: 要移动 {actor}，但他从未在台上出现')
    return errors


def check_anchors(steps):
    """锚点必须在该场景的 Anchors 层里真实存在**且可通行**。

    「名字存在」不等于「格可走」：walkable 只来自 zone id 匹配
    ^(A\\d*|B|C|D|E|F)$ 的地板与 Routes 走廊。这里直接用项目自己的
    parseTiledMap 算 walkable，判定与运行期一致。
    """
    errors = []
    anchors = {}
    for tmj in (ROOT / 'maps').glob('*.tmj'):
        data = json.loads(tmj.read_text(encoding='utf-8'))
        props = {p.get('name'): p.get('value') for p in (data.get('properties') or []) if isinstance(p, dict)}
        sid = props.get('sceneId')
        if not sid:
            continue
        names = set()
        for layer in (data.get('layers') or []):
            if isinstance(layer, dict) and layer.get('type') == 'objectgroup' and 'anchor' in (layer.get('name') or '').lower():
                names = {o.get('name') for o in (layer.get('objects') or [])}
        anchors[sid] = names

    probe_path = ROOT / 'artifacts' / 'probe_walkable_tmp.mjs'
    probe_path.parent.mkdir(exist_ok=True)
    probe_path.write_text(
        "import {readdirSync,readFileSync} from 'node:fs';\n"
        "import {parseTiledMap} from '../src/model.ts';\n"
        "const out={};\n"
        "for(const f of readdirSync(new URL('../maps',import.meta.url).pathname).filter(x=>x.endsWith('.tmj'))){\n"
        "  const j=JSON.parse(readFileSync(new URL('../maps/'+f,import.meta.url).pathname,'utf8'));\n"
        "  const props={};for(const p of (j.properties||[]))props[p.name]=p.value;\n"
        "  if(!props.sceneId)continue;\n"
        "  const m=parseTiledMap(j);\n"
        "  const w={};\n"
        "  for(const[name,p]of Object.entries(m.anchors))w[name]=m.walkable.has(p.col+','+p.row);\n"
        "  out[props.sceneId]=w;\n"
        "}\n"
        "console.log(JSON.stringify(out));\n", encoding='utf-8')
    proc = subprocess.run(['node', '--experimental-strip-types', str(probe_path)],
                          capture_output=True, text=True, cwd=str(ROOT))
    if proc.returncode != 0:
        raise RuntimeError('walkable 探针失败：' + proc.stderr[:400])
    walkable = json.loads(proc.stdout.strip().split('\n')[-1])

    for step in steps:
        scene = step['scene']
        names = anchors.get(scene)
        if names is None:
            errors.append(f'{step["id"]}: 场景 {scene} 不存在')
            continue
        w = walkable.get(scene, {})
        for act in step['actions']:
            at = act.get('at')
            if at and at not in names:
                errors.append(f'{step["id"]}: 锚点 {at} 不在场景 {scene} 中')
            elif at and not w.get(at):
                errors.append(f'{step["id"]}: 锚点 {at} 在场景 {scene} 中不可通行')
            for anchor in act.get('via') or []:
                if anchor not in names:
                    errors.append(f'{step["id"]}: 路径锚点 {anchor} 不在场景 {scene} 中')
                elif not w.get(anchor):
                    errors.append(f'{step["id"]}: 路径锚点 {anchor} 在场景 {scene} 中不可通行')
        if step['focus'] and step['focus'] not in names:
            errors.append(f'{step["id"]}: focus {step["focus"]} 不在场景 {scene} 中')
        elif step['focus'] and not w.get(step['focus']):
            errors.append(f'{step["id"]}: focus {step["focus"]} 在场景 {scene} 中不可通行')
    return errors


def build_evidence(steps):
    evidence = []
    for step in steps:
        excerpt = step['text']
        if len(excerpt) > 120:
            excerpt = excerpt[:120] + '…'
        evidence.append({
            'id': step['id'].replace('C20-', 'C20-E'),
            'classification': 'explicit',
            'paragraphLead': step['source']['paragraphLead'],
            'excerpt': excerpt,
            'claim': step['title'],
            'narrativeLayer': 'present',
            'speaker': None if step['speaker'] == 'narrator' else step['speaker'],
            'appliesTo': [step['id']],
            'designDecision': None,
            'uncertainty': None,
        })
    for eid, sec_id, claim, uncertainty, decision in DESIGN_NOTES:
        first = next(s for s in steps if s['chapter'] == sec_id)
        evidence.append({
            'id': eid,
            'classification': 'design',
            'paragraphLead': first['source']['paragraphLead'],
            'excerpt': None,
            'claim': claim,
            'narrativeLayer': 'present',
            'speaker': None,
            'appliesTo': [s['id'] for s in steps if s['chapter'] == sec_id],
            'designDecision': decision,
            'uncertainty': uncertainty,
        })
    return {
        'schemaVersion': 1,
        'template': False,
        'chapter': 20,
        'source': {
            'edition': '维基文库《紅樓夢》第 020 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第020回&action=raw',
            'retrievedAt': '2026-11-11',
            'localText': 'docs/chapter20-source.txt',
            'processing': 'MediaWiki action=raw 取回 wikitext，去模板与导航行，OpenCC 转简体；'
                         '回目行与正文之间补空行，回目自成一段；正文未作增删。',
        },
        'paragraphCount': len(PARAS),
        'nodeCount': len(steps),
        'sectionCount': len(SECTIONS),
        'mapCount': len({s[2] for s in SECTIONS}),
        'evidence': evidence,
    }


def main() -> int:
    steps = build()
    assign_scenes(steps)

    errors = check(steps) + check_anchors(steps)
    if errors:
        print('第20回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第20回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 20})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第20回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
