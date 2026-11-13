#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 19 回的剧情、段落、证据数据。

第 19 回底本是维基文库原文全文（docs/chapter19-source.txt），
写法沿用第 18 回确立的**底本切片式生成**：不手写正文，
按「起句标记 → 止句标记」切片，正文与 source.paragraphLead 都是切出来的。

用法：
    python3 scripts/build_chapter19.py            # 生成
    python3 scripts/build_chapter19.py --check    # 只校验已有文件

场景与人物（对照 docs/chapter19-production.md 的分场规划）：
  c5_ningfu    宁府看戏 / 小书房撞破 / 后门出府（复用既有图）
  xiren_home   袭人家（本回新建，7 锚点，全部可通行）
  night        怡红院占位（李嬷嬷酥酪 / 花解语三件事 / 三更安歇）
  dinner       黛玉午睡（暖香 / 黛山林子洞故典）
人物：袭人(xiren)、李嬷嬷(nurse_li) 已在 cast；茗烟/花自芳/秋纹/晴雯用
messenger 代指（不新增美术）；卍儿只在书房一场出现，不 show。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter19-source.txt'
STORY = ROOT / 'design' / 'chapter19-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter19-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter19-evidence.json'

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
    """从底本第 para 段起、到 end 之前切出一段文字（同第 18 回）。"""
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


def to_display(text: str) -> str:
    """底本弯引号 → 「」『』，只换标点不动字（第 16-18 回同一读法）。"""
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
SECTIONS = [
    ('c19-ningfu', '宁国府 · 看戏与闲耍', 'c5_ningfu'),
    ('c19-study', '宁国府 · 小书房卍儿', 'c5_ningfu'),
    ('c19-mingyan', '城外半里 · 茗烟引路', 'c5_ningfu'),
    ('c19-xirenhome', '袭人家 · 花家待客', 'xiren_home'),
    ('c19-liaolao', '怡红院 · 李嬷嬷吃酥酪', 'night'),
    ('c19-shuzhen', '怡红院 · 袭人论赎身', 'night'),
    ('c19-huayu', '怡红院 · 花解语三件事', 'night'),
    ('c19-yusheng', '潇湘馆 · 静日玉生香', 'dinner'),
]

# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题, 地点, 底本段号, 起句, 止句, 动作)
CUTS = [
    # ---------------- 段一：宁府看戏 ----------------
    ('c19-ningfu', 'C19-001', 'narrator', '荣宁二府人人力倦', '宁国府 · 戏台', 1,
     '话说贾妃回宫', '偏这日一早', ['S:feng:garden_entry']),
    ('c19-ningfu', 'C19-002', 'narrator', '袭人之母亲来接袭人家去吃年茶', '宁国府 · 戏台', 1,
     '偏这日一早', '宝玉听了，便命换衣裳', ['S:grandmother:upper_room']),
    ('c19-ningfu', 'C19-003', 'narrator', '贾妃赐出糖蒸酥酪', '宁国府 · 戏台', 1,
     '才要去时', '自己回过贾母', ['E:baoyu:jade:1.2']),
    ('c19-ningfu', 'C19-004', 'narrator', '锣鼓喊叫之声远闻巷外', '宁国府 · 戏台', 2,
     '谁想贾珍这边唱的是', '满街之人个个都赞', ['S:baoyu:garden_center']),
    ('c19-ningfu', 'C19-005', 'narrator', '好热闹戏，别人家断不能有的', '宁国府 · 戏台', 2,
     '满街之人个个都赞', '宝玉见繁华热闹到如此不堪的田地', ['E:baoyu:rest:1.2']),
    ('c19-ningfu', 'C19-006', 'narrator', '只略坐了一坐便走开各处闲耍', '宁国府 · 戏台', 2,
     '宝玉见繁华热闹到如此不堪的田地', '待晚间再来', ['M:baoyu:garden_center>upper_room_door']),

    # ---------------- 段二：小书房撞破 ----------------
    ('c19-study', 'C19-007', 'narrator', '须得我去望慰他一回', '宁国府 · 小书房', 3,
     '宝玉见一个人没有', '想著，便往书房里来', ['M:baoyu:upper_room>upper_room_door']),
    ('c19-study', 'C19-008', 'narrator', '闻得房内有呻吟之韵', '宁国府 · 小书房', 3,
     '刚到窗前', '乃乍著胆子', ['E:baoyu:rest:1.0']),
    ('c19-study', 'C19-009', 'narrator', '那轴美人却不曾活', '宁国府 · 小书房', 3,
     '乃乍著胆子', None,
     ['M:baoyu:upper_room_door>upper_room']),
    ('c19-study', 'C19-010', 'baoyu', '青天白日，这是怎么说', '宁国府 · 小书房', 4,
     '茗烟见是宝玉', '一面看那丫头', ['S:messenger:upper_room']),
    ('c19-study', 'C19-011', 'narrator', '还不快跑', '宁国府 · 小书房', 4,
     '一面看那丫头', '急的茗烟在后叫', ['E:baoyu:greet:1.2']),
    ('c19-study', 'C19-012', 'baoyu', '连他的岁属也不问问', '宁国府 · 小书房', 4,
     '急的茗烟在后叫', '又问：“名字叫什么', ['E:messenger:rest:1.0']),
    ('c19-study', 'C19-013', 'messenger', '所以他的名字叫作卍儿', '宁国府 · 小书房', 4,
     '又问：“名字叫什么', '宝玉听了笑道', ['E:messenger:greet:1.2']),
    ('c19-study', 'C19-014', 'narrator', '想必他将来有些造化', '宁国府 · 小书房', 4,
     '宝玉听了笑道', None, ['E:baoyu:rest:1.2']),

    # ---------------- 段三：茗烟引路 ----------------
    ('c19-mingyan', 'C19-015', 'messenger', '二爷为何不看这样的好戏', '宁国府 · 二门外', 5,
     '茗烟因问', '茗烟嘻嘻笑道', ['S:messenger:garden_entry', 'S:baoyu:garden_center']),
    ('c19-mingyan', 'C19-016', 'baoyu', '不如往熟近些的地方去', '宁国府 · 二门外', 5,
     '茗烟嘻嘻笑道', '茗烟道：“熟近地方', ['E:baoyu:greet:1.0']),
    ('c19-mingyan', 'C19-017', 'messenger', '咱们竟找你花大姐姐去', '宁国府 · 二门外', 5,
     '茗烟道：“熟近地方', '茗烟笑道：“好，好', ['E:messenger:greet:1.2']),
    ('c19-mingyan', 'C19-018', 'narrator', '二人从后门就走了', '城外半里 · 途中', 5,
     '又道：“若他们知道了', '展眼已到门前', ['M:baoyu:garden_center>garden_entry']),
    ('c19-xirenhome', 'C19-019', 'narrator', '袭人之母接了袭人与几个外甥女儿来家', '袭人家 · 门前', 5,
     '展眼已到门前', '见是他主仆两个', ['S:messenger:gate']),
    ('c19-xirenhome', 'C19-020', 'narrator', '花自芳忙出去看时', '袭人家 · 门前', 5,
     '见是他主仆两个', '袭人听了，也不知为何', ['S:xiren:gate']),
    ('c19-xirenhome', 'C19-021', 'xiren', '你怎么来了', '袭人家 · 门前', 5,
     '袭人听了，也不知为何', '宝玉笑道：“我怪闷的', ['E:xiren:greet:1.2']),
    ('c19-xirenhome', 'C19-022', 'baoyu', '我怪闷的，来瞧瞧你作什么呢', '袭人家 · 门前', 5,
     '宝玉笑道：“我怪闷的', '一面又问茗烟', ['E:baoyu:greet:1.2']),
    ('c19-xirenhome', 'C19-023', 'xiren', '倘或碰见了人，或是遇见了老爷', '袭人家 · 门前', 5,
     '袭人听了，复又惊慌', '茗烟撅了嘴道', ['E:xiren:rest:1.4']),
    ('c19-xirenhome', 'C19-024', 'messenger', '我说别来罢', '袭人家 · 门前', 5,
     '茗烟撅了嘴道', '花自芳忙劝', ['E:messenger:rest:1.0']),

    # ---------------- 段四：袭人家 ----------------
    ('c19-xirenhome', 'C19-025', 'narrator', '袭人拉了宝玉进去', '袭人家 · 里屋', 6,
     '袭人之母也早迎了出来', '花自芳母子两个百般怕宝玉冷', ['M:xiren:gate>yard']),
    ('c19-xirenhome', 'C19-026', 'narrator', '又让他上炕又忙另摆果桌', '袭人家 · 里屋', 6,
     '花自芳母子两个百般怕宝玉冷', '袭人笑道：“你们不用白忙', ['M:xiren:yard>room']),
    ('c19-xirenhome', 'C19-027', 'xiren', '你们不用白忙，我自然知道', '袭人家 · 里屋', 6,
     '袭人笑道：“你们不用白忙', '一面说，一面将自己的坐褥', ['S:xiren:host', 'S:baoyu:kang']),
    ('c19-xirenhome', 'C19-028', 'narrator', '将自己的茶杯斟了茶送与宝玉', '袭人家 · 里屋', 6,
     '一面说，一面将自己的坐褥', '彼时他母兄已是忙另齐齐整整', ['M:xiren:host>room']),
    ('c19-xirenhome', 'C19-029', 'xiren', '既来了，没有空去之理', '袭人家 · 里屋', 6,
     '袭人见总无可吃之物', None,
     ['M:xiren:room>host', 'E:xiren:greet:1.2']),

    # ---------------- 段五：李嬷嬷吃酥酪 ----------------
    ('c19-liaolao', 'C19-030', 'baoyu', '好好的哭什么', '怡红院 · 炕前', 7,
     '宝玉看见袭人两眼微红', '因此便遮掩过了', ['S:baoyu:baoyu_bed', 'S:xiren:xiren_place']),
    ('c19-liaolao', 'C19-031', 'xiren', '坐一坐就回去罢', '怡红院 · 炕前', 7,
     '当下宝玉穿著大红金蟒狐腋箭袖', '宝玉笑道：“珍大爷那里去看戏换的', ['E:xiren:rest:1.0']),
    ('c19-liaolao', 'C19-032', 'narrator', '悄悄的，叫他们听著什么意思', '怡红院 · 炕前', 7,
     '袭人点头。又道：“坐一坐就回去罢', '一面又伸手从宝玉项上', ['E:baoyu:jade:1.4']),
    ('c19-liaolao', 'C19-033', 'xiren', '你们见识见识', '怡红院 · 炕前', 7,
     '一面又伸手从宝玉项上', '花自芳道：“有我送去', ['M:xiren:xiren_place>outer_door']),
    ('c19-liaolao', 'C19-034', 'narrator', '一直送宝玉至门前', '怡红院 · 外间', 7,
     '花自芳忙去雇了一顶小轿来', '来至宁府街', ['H:xiren', 'H:messenger']),
    ('c19-liaolao', 'C19-035', 'narrator', '茗烟命住轿', '宁府街 · 后门', 7,
     '来至宁府街', '于是仍进后门来', ['S:baoyu:outer_door']),
    ('c19-liaolao', 'C19-036', 'narrator', '房中丫鬟们都越性恣意的顽笑', '怡红院 · 外间', 7,
     '俱不在话下。却说宝玉自出了门', '偏奶母李嬷嬷拄拐进来请安', ['S:messenger:outer_door']),
    ('c19-liaolao', 'C19-037', 'nurse_li', '照见人家，照不见自家', '怡红院 · 外间', 7,
     '偏奶母李嬷嬷拄拐进来请安', '这些丫头们明知宝玉不讲究这些', ['S:nurse_li:xiren_place']),
    ('c19-liaolao', 'C19-038', 'narrator', '好一个讨厌的老货', '怡红院 · 外间', 7,
     '这些丫头们明知宝玉不讲究这些', None, ['E:nurse_li:rest:1.2']),

    # ---------------- 段六：袭人论赎身 ----------------
    ('c19-liaolao', 'C19-039', 'nurse_li', '这盖碗里是酥酪', '怡红院 · 外间', 8,
     '李嬷嬷又问道：“这盖碗里是酥酪', '李嬷嬷听了，又气又愧', ['E:nurse_li:greet:1.0']),
    ('c19-liaolao', 'C19-040', 'nurse_li', '我的血变的奶', '怡红院 · 外间', 8,
     '李嬷嬷听了，又气又愧', '一面说，一面赌气将酥酪吃尽', ['E:nurse_li:rest:1.4']),
    ('c19-liaolao', 'C19-041', 'nurse_li', '打量上次为茶撵茜雪的事我不知道呢', '怡红院 · 外间', 8,
     '又一丫头笑道', '说著，赌气去了', ['H:nurse_li']),
    ('c19-liaolao', 'C19-042', 'narrator', '晴雯躺在床上不动', '怡红院 · 外间', 9,
     '少时，宝玉回来', '宝玉笑道：“你别和他一般见识', ['S:baoyu:outer_door', 'S:messenger:yingge_place']),
    ('c19-liaolao', 'C19-043', 'xiren', '我只想风干栗子吃', '怡红院 · 外间', 9,
     '一时换衣卸妆。宝玉命取酥酪来', None,
     ['S:xiren:xiren_place', 'E:xiren:greet:1.2']),

    # ---------------- 段七：花解语三件事 ----------------
    ('c19-shuzhen', 'C19-044', 'narrator', '今儿那个穿红的是你什么人', '怡红院 · 灯前', 10,
     '宝玉听了信以为真', '袭人道：“那是我两姨妹子', ['M:baoyu:outer_door>baoyu_bed']),
    ('c19-shuzhen', 'C19-045', 'xiren', '那是我两姨妹子', '怡红院 · 灯前', 10,
     '袭人道：“那是我两姨妹子', '袭人道：“叹什么', ['E:xiren:rest:1.0']),
    ('c19-shuzhen', 'C19-046', 'baoyu', '我因为见他实在好的很', '怡红院 · 灯前', 10,
     '袭人道：“叹什么', '袭人冷笑道', ['E:baoyu:greet:1.2']),
    ('c19-shuzhen', 'C19-047', 'xiren', '我一个人是奴才命罢了', '怡红院 · 灯前', 10,
     '袭人冷笑道', '明年就出嫁', ['E:xiren:rest:1.2']),
    ('c19-shuzhen', 'C19-048', 'narrator', '怎么也得他在咱们家就好了', '怡红院 · 灯前', 10,
     '宝玉便不肯再说', None, ['E:baoyu:rest:1.2']),
    ('c19-shuzhen', 'C19-049', 'xiren', '如今我要回去了', '怡红院 · 灯前', 11,
     '宝玉听了“出嫁”二字', '忙丢下栗子', ['E:xiren:rest:1.4']),
    ('c19-shuzhen', 'C19-050', 'baoyu', '你如今要回去了', '怡红院 · 灯前', 11,
     '忙丢下栗子', '袭人道：“我今儿听见我妈和哥哥商议', ['E:baoyu:rest:1.2']),
    ('c19-shuzhen', 'C19-051', 'xiren', '叫我再耐烦一年', '怡红院 · 灯前', 11,
     '袭人道：“我今儿听见我妈和哥哥商议', '宝玉听了这话', ['E:xiren:rest:1.0']),
    ('c19-shuzhen', 'C19-052', 'narrator', '为什么要赎你', '怡红院 · 灯前', 11,
     '宝玉听了这话', None, ['E:baoyu:rest:1.2']),
    ('c19-shuzhen', 'C19-053', 'narrator', '老太太不放你也难', '怡红院 · 灯前', 12,
     '宝玉想一想，果然有理', '宝玉听了这些话', ['E:baoyu:rest:1.0']),
    ('c19-shuzhen', 'C19-054', 'narrator', '竟是有去的理，无留的理', '怡红院 · 灯前', 12,
     '宝玉听了这些话', '宝玉听了，思忖半晌', ['E:xiren:rest:1.0']),
    ('c19-shuzhen', 'C19-055', 'xiren', '去定了', '怡红院 · 灯前', 12,
     '宝玉听了，思忖半晌', '原来袭人在家', ['E:baoyu:rest:1.2']),
    # 这一段是袭人在家哭闹的转述，不在当下场景——layer 用 reported，
    # 人物不出现在台上（无动作）。
    ('c19-shuzhen', 'C19-056', 'narrator', '权当我死了，再不必起赎我的念头', '袭人家 · 转述', 12,
     '原来袭人在家', None, []),
    ('c19-shuzhen', 'C19-057', 'narrator', '故先用骗词以探其情', '怡红院 · 灯前', 14,
     '如今且说袭人自幼见宝玉性格异常', '今见他默默睡去了', ['H:xiren']),
    ('c19-shuzhen', 'C19-058', 'xiren', '你果然留我，我自然不出去了', '怡红院 · 灯前', 14,
     '今见他默默睡去了', '宝玉见这话有文章', ['S:xiren:xiren_place']),
    ('c19-shuzhen', 'C19-059', 'xiren', '我另说出两三件事来', '怡红院 · 灯前', 14,
     '宝玉见这话有文章', None, ['E:xiren:greet:1.2']),

    # ---------------- 段八：花解语三件事（续） ----------------
    ('c19-huayu', 'C19-060', 'baoyu', '就是两三百件，我也依', '怡红院 · 灯前', 15,
     '宝玉忙笑道：“你说，那几件', '话未说完，急的袭人忙握他的嘴', ['S:baoyu:baoyu_bed', 'S:xiren:xiren_place']),
    ('c19-huayu', 'C19-061', 'xiren', '好好的，正为劝你这些', '怡红院 · 灯前', 15,
     '话未说完，急的袭人忙握他的嘴', '袭人道：“这是头一件要改的', ['E:xiren:greet:1.0']),
    ('c19-huayu', 'C19-062', 'xiren', '这是头一件要改的', '怡红院 · 灯前', 15,
     '袭人道：“这是头一件要改的', None, ['E:baoyu:rest:1.0']),
    ('c19-huayu', 'C19-063', 'xiren', '只是在老爷跟前或在别人跟前', '怡红院 · 灯前', 16,
     '袭人道：“第二件', None, ['E:xiren:rest:1.2']),
    ('c19-huayu', 'C19-064', 'xiren', '再不可毁僧谤道，调脂弄粉', '怡红院 · 灯前', 17,
     '袭人道：“再不可毁僧谤道', None, ['E:xiren:greet:1.0']),
    ('c19-huayu', 'C19-065', 'narrator', '快三更了，该睡了', '怡红院 · 灯前', 18,
     '二人正说著', '方从新盥漱，宽衣安歇', ['S:messenger:yingge_place']),
    ('c19-huayu', 'C19-066', 'narrator', '袭人便觉身体发重', '怡红院 · 次日', 18,
     '至次日清晨', '宝玉自去黛玉房中来看视', ['S:xiren:xiren_place', 'E:xiren:rest:1.2']),

    # ---------------- 段九：静日玉生香 ----------------
    ('c19-yusheng', 'C19-067', 'narrator', '满屋内静悄悄的', '潇湘馆 · 里间', 19,
     '彼时黛玉自在床上歇午', '将黛玉唤醒', ['S:daiyu:daiyu_place']),
    ('c19-yusheng', 'C19-068', 'daiyu', '你且出去逛逛', '潇湘馆 · 里间', 19,
     '将黛玉唤醒', '宝玉道：“酸疼事小', ['S:baoyu:baoyu_greet', 'E:daiyu:rest:1.2']),
    ('c19-yusheng', 'C19-069', 'baoyu', '酸疼事小，睡出来的病大', '潇湘馆 · 里间', 19,
     '宝玉道：“酸疼事小', '黛玉只合著眼', ['E:baoyu:greet:1.0']),
    ('c19-yusheng', 'C19-070', 'baoyu', '我往那去呢，见了别人就怪腻的', '潇湘馆 · 里间', 19,
     '黛玉只合著眼', None, ['M:baoyu:baoyu_greet>grandmother_place']),
    ('c19-yusheng', 'C19-071', 'daiyu', '那边去老老实实的坐著', '潇湘馆 · 里间', 20,
     '黛玉听了，嗤的一声笑道', '宝玉出至外间', ['E:daiyu:greet:1.2']),
    ('c19-yusheng', 'C19-072', 'narrator', '黛玉因看见宝玉左边腮上有钮扣大小的一块血渍', '潇湘馆 · 里间', 21,
     '黛玉因看见宝玉左边腮上', '说著，便找手帕子要揩拭', ['E:daiyu:rest:1.0']),
    ('c19-yusheng', 'C19-073', 'narrator', '只闻得一股幽香', '潇湘馆 · 里间', 22,
     '宝玉总未听见这些话', '宝玉笑道：“既然如此', ['E:baoyu:rest:1.2']),
    ('c19-yusheng', 'C19-074', 'baoyu', '不给你个利害，也不知道', '潇湘馆 · 里间', 23,
     '宝玉笑道：“凡我说一句', '黛玉素性触痒不禁', ['E:baoyu:greet:1.4']),
    ('c19-yusheng', 'C19-075', 'daiyu', '蠢才，蠢才', '潇湘馆 · 里间', 24,
     '宝玉见问，一时解不来', '黛玉忙笑道：“好哥哥', ['E:daiyu:greet:1.2']),
    ('c19-yusheng', 'C19-076', 'narrator', '扬州有一座黛山', '潇湘馆 · 里间', 25,
     '便哄他道：“嗳哟', '黛玉听了，翻身爬起来', ['E:baoyu:rest:1.0']),
    ('c19-yusheng', 'C19-077', 'daiyu', '我把你烂了嘴的', '潇湘馆 · 里间', 26,
     '黛玉听了，翻身爬起来', None, ['E:daiyu:greet:1.4']),
    ('c19-yusheng', 'C19-078', 'baochai', '谁说故典呢', '潇湘馆 · 里间', 27,
     '一语未了，只见宝钗走来', None, ['S:baochai:wang_place']),
]

# ---------------------------------------------------------------- 设计推定
DESIGN_NOTES = [
    ('C19-D001', 'c19-ningfu',
     '宁国府戏台、小书房、后门共用 c5_ningfu 一图',
     '原图为会芳园与秦氏卧房；原文只说「东府珍大爷来请过去看戏」与「小书房」，未给平面。',
     '复用 c5_ningfu 的 garden_entry/garden_center/upper_room 表现戏台侧与书房。'),
    ('C19-D002', 'c19-xirenhome',
     '袭人家为新建图 xiren_home（京城市井小户）',
     '原文只说「袭人家不远，不过一半里路程」与「茅檐草舍，又窄又脏」。',
     '新建 40×40 室内主题图：小院（A0）+ 里屋（ROOM），farm-house 壳，7 锚点全部可通行。'),
    ('C19-D003', 'c19-liaolao',
     '怡红院借用 night 图（贾母院碧纱橱与外间）占位',
     '原文是宝玉房中（外间、炕、酥酪）；项目尚无怡红院专图。',
     '用 night 的 outer_door/xiren_place/yingge_place/baoyu_bed 表现外间与炕前。'),
    ('C19-D004', 'c19-yusheng',
     '黛玉歇午处借用 dinner 图（贾母院后房）占位',
     '原文只说「黛玉自在床上歇午」；此时黛玉住贾母院碧纱橱。',
     '用 dinner 的 daiyu_place/baoyu_greet/grandmother_place/wang_place 表现里间与坐处。'),
    ('C19-D005', 'c19-study',
     '卍儿只在书房一场出现，不 show；茗烟、花自芳、秋纹、晴雯以 messenger 代指',
     '原文有卍儿、茗烟、花自芳、秋纹、晴雯等配角台词。',
     '避免美术膨胀：卍儿不入场（叙事带过），其余配角一律用通用 messenger 角色。'),
]


def build():
    steps = []
    for sec_id, nid, speaker, title, place, para, start, end, codes in CUTS:
        raw, lead = cut(para, start, end)
        steps.append({
            'chapter': sec_id,
            'scene': None,
            'place': place,
            'focus': '',
            'source': {
                'chapter': 19,
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
    return errors


def check_anchors(steps):
    """锚点必须在该场景的 Anchors 层里真实存在**且可通行**。

    「名字存在」不等于「格可走」：walkable 只来自 zone id 匹配
    ^(A\\d*|B|C|D|E|F)$ 的地板与 Routes 走廊，c5_ningfu 的
    portrait_wall 就是一个存在但走不上去的锚点（第 5 回留下的），
    引擎 show 会抛「显示地点不可通行」。这里直接用项目自己的
    parseTiledMap 算 walkable，判定与运行期一致。
    """
    import sys as _sys
    _sys.path.insert(0, str(ROOT / 'scripts'))
    errors = []
    anchors = {}
    walkable = {}
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

    # 用 Node 侧的 parseTiledMap 求每张图的 walkable（与运行期同一套逻辑）。
    # 不能用 node -e：相对导入 '../src/model.ts' 在 eval 模式下解析不到根，
    # 写成临时 .mjs 文件放在 scripts/ 旁边执行。
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
            'id': step['id'].replace('C19-', 'C19-E'),
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
        'chapter': 19,
        'source': {
            'edition': '维基文库《紅樓夢》第 019 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第019回&action=raw',
            'retrievedAt': '2026-11-10',
            'localText': 'docs/chapter19-source.txt',
            'processing': '维基限流时先 curl 存 /tmp/ch019_raw.txt 再走脚本缓存；'
                         'MediaWiki action=raw 取回 wikitext，去模板与导航行，OpenCC 转简体；正文未作增删。',
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
        print('第19回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第19回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 19})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第19回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
