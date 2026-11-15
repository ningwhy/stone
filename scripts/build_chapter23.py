#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 23 回的剧情、段落、证据数据。

第 23 回底本是维基文库原文全文（docs/chapter23-source.txt），
写法沿用第 18-22 回确立的**底本切片式生成**：不手写正文，
按**句号索引**切片，正文与 source.paragraphLead 都是切出来的。

用法：
    python3 scripts/build_chapter23.py            # 生成
    python3 scripts/build_chapter23.py --check    # 只校验已有文件

这一回的两条戏与几处地点（对照 docs/chapter23-production.md 的分场规划）：

  jialian_home 荣国府 · 贾琏院 —— 凤姐献计，小沙弥道士送铁槛寺
  dinner       贾母院 · 后房 —— 元春下谕，宝玉怕贾政，商量住哪
  wang         王夫人院 · 东廊 —— 金钏儿奚落，贾政训斥宝玉
  yihong       大观园 · 怡红院 —— 宝玉闷，茗烟买书
  qinfang      大观园 · 沁芳闸桃花下 —— 共读西厢，葬花，「多愁多病身」
  c4_lixiang   荣府东北角 · 梨香院 —— 墙外听《牡丹亭》，「如花美眷，似水流年」

**一张新地图**：qinfang（第二十三回新建）。梨香院墙角那一段复用第四回的
c4_lixiang —— 底本明写「刚走到梨香院墙角上」，本回从墙外听声，用它的一角。

**三名新角色**：金钏儿、彩云、贾芹（第 7 回金钏儿、第 13 回贾芹都只在
旁白里被提到，从未现身；彩云此前一个字都没出现过）。周氏若要登场需与
贾芹同时，但底本只写「便坐轿子来求凤姐」一句，没有台词——
本回按「不登场、由叙述带过」处理，不给她立绘（见证据表 C23-D6）。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter23-source.txt'
STORY = ROOT / 'design' / 'chapter23-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter23-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter23-evidence.json'

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


def split_sentences(text: str):
    """按**子句**切分：句末标点（。！？）与句中标点（；，：、）都算断点。

    ★ 第 23 回为什么用子句级，而第 16-22 回用句级：
      本回底本的句子普遍很长（多是三四逗号的长句），一句一节点会把
      「凤姐笑道：『你且站住，听我说话。若是别的事我不管……』」
      整句塞进一个节点，剧情节奏全丢。按子句切才能还原底本的
      「叙述 / 台词」交替。
      闭合引号归到**前**一句（切句时若下一段以 」』 开头就并入上一句），
      这样引号不会单独成一个子句，读起来才顺。
    """
    # 闭合引号归入前一个子句：底本里 “ ” 常紧跟在逗号后面
    # （「…。」→「…」＋「，」「」」），若不并回去，引号会自己成一个子句，
    # 读者就会看到节点正文以孤零零的「」开头。
    # 先在标点后把闭合引号吸进前一段，再切分。
    text = re.sub(r'([，：、；])([”’])', r'\1\2', text)
    parts = re.split(r'(?<=[。！？；，：、])', text)
    out = []
    for s in parts:
        if not s:
            continue
        if out and s[0] in '”’」』':
            out[-1] = out[-1] + s[0]
            s = s[1:]
            if not s:
                continue
        out.append(s)
    return out


SENTENCES = {i: split_sentences(p) for i, p in enumerate(PARAS)}


def cut_sent(para: int, s_from: int, s_to: int):
    """切出底本第 para 段的第 [s_from, s_to) 个子句。返回 (正文, 起句原文)。

    ★ 正文会延伸到该子句所在**整句的末尾**（下一个句末标点之后）：
      第 16-22 回的节点正文九成以上以句末标点收尾，读者看到的是完整句子；
      若停在逗号上，读起来像被拦腰砍断。
      lead 仍取子句起点——它是正文的前缀，且能在底本逐字查到
      （scripts/check_content.mjs 的 VERBATIM_BASE 会验这一条）。
    """
    sents = SENTENCES[para]
    if not (0 <= s_from < s_to <= len(sents)):
        raise ValueError(f'第 {para} 段子句号 [{s_from}, {s_to}) 越界（共 {len(sents)} 句）')
    lead = sents[s_from]
    raw = ''.join(sents[s_from:s_to])
    # 延到整句末：往后吃到下一个句末标点（。！？）为止
    end = s_to
    while end < len(sents) and not re.search(r'[。！？]', sents[end - 1]):
        end += 1
    if end > s_to:
        raw = ''.join(sents[s_from:end])
    if not raw.startswith(lead):
        raise ValueError(f'第 {para} 段第 {s_from} 句定位失败：{lead[:20]}')
    return raw, lead


def to_display(text: str) -> str:
    """底本弯引号 → 「」『』，只换标点不动字（第 16-22 回同一读法）。"""
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
    ('c23-ledong', '大观园 · 勒石题咏', 'dinner'),
    ('c23-tiejian', '贾琏院 · 凤姐献计', 'jialian_home'),
    ('c23-jiaqin', '贾琏院 · 支银送寺', 'jialian_home'),
    ('c23-yuci', '贾母院 · 元春下谕', 'dinner'),
    ('c23-jingong', '贾母院 · 怕与商量', 'dinner'),
    ('c23-jiaozheng', '王夫人院 · 贾政训斥', 'wang'),
    ('c23-fenju', '贾母院 · 分派居所', 'dinner'),
    ('c23-sishi', '怡红院 · 即事诗与闷', 'yihong'),
    ('c23-mingsmoke', '怡红院 · 茗烟买书', 'yihong'),
    ('c23-taohua', '沁芳闸 · 桃花底下', 'qinfang'),
    ('c23-huizhen', '沁芳闸 · 读西厢', 'qinfang'),
    ('c23-madou', '沁芳闸 · 多愁多病', 'qinfang'),
    ('c23-mudanting', '梨香院墙角 · 听曲', 'c4_lixiang'),
    ('c23-luoye', '梨香院墙角 · 落泪', 'c4_lixiang'),
]


# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题, 地点, 底本段号, 起始句号, 结束句号, 动作)
#
# 用句号而不是字符串标记：底本句子里有大量同形短句，字符串检索会命中
# 前一处，切到别人的字；句号唯一定位，且天然保证节点顺序单调。
#
# 底本顺序（段号, 句号）必须全局单调递增——check() 会逐对校验。
CUTS = [
    # ★ 索引是**子句号**（见 split_sentences 的说明），不是句号。
    #   底本第 N 段的第 [s_from, s_to) 个子句。切出来的正文与 paragraphLead
    #   都是底本逐字原文，不作任何改写。
    # 节点顺序按底本位置 (段号, 子句号) 全局单调递增——check() 会逐对校验。
    ('c23-ledong', 'C23-001', 'narrator', '元春命将那日所有的题咏，命探春抄录妥协', '大观园 · 正殿', 1, 0, 2,
     ['S:tanchun:tanchun_place']),
    ('c23-ledong', 'C23-002', 'narrator', '自己编次，叙其优劣，又命在大观园勒石', '大观园 · 正殿', 1, 3, 6,
     ['E:tanchun:rest:1.4']),
    ('c23-ledong', 'C23-003', 'narrator', '贾政命人选拔精工名匠，在大观园磨石镌字', '大观园 · 正殿', 1, 8, 9,
     ['E:tanchun:rest:1.2']),
    ('c23-ledong', 'C23-004', 'narrator', '贾珍率领蓉，萍等监工', '大观园 · 正殿', 1, 10, 12,
     ['E:tanchun:rest:1.2']),
    ('c23-ledong', 'C23-005', 'narrator', '因贾蔷管理著文官等十二个女戏，不大得便', '大观园 · 正殿', 1, 12, 13,
     ['E:tanchun:rest:1.4']),
    ('c23-ledong', 'C23-006', 'narrator', '贾珍又将贾菖，贾菱唤来监工', '大观园 · 正殿', 1, 14, 16,
     ['E:tanchun:rest:1.2']),
    ('c23-ledong', 'C23-007', 'narrator', '一日，汤蜡钉朱，动起手来', '大观园 · 正殿', 1, 16, 19,
     ['E:tanchun:rest:1.2']),
    ('c23-ledong', 'C23-008', 'narrator', '这也不在话下', '大观园 · 正殿', 1, 19, 20,
     ['E:tanchun:rest:1.2']),
    ('c23-tiejian', 'C23-009', 'narrator', '玉皇庙并达摩庵两处，一班小沙弥并小道士，如今挪出大观园来', '贾琏院 · 院中', 2, 0, 3,
     ['S:feng:yard', 'S:jia_lian:table_place']),
    ('c23-tiejian', 'C23-010', 'narrator', '贾政正想发到各庙去分住', '贾琏院 · 院中', 2, 3, 4,
     ['E:feng:rest:1.4']),
    ('c23-tiejian', 'C23-011', 'narrator', '不想后街上住的贾芹之母周氏，正盘算著要谋一个事务', '贾琏院 · 院中', 2, 4, 5,
     ['E:feng:rest:1.4']),
    ('c23-tiejian', 'C23-012', 'narrator', '可巧听见这件事出来，便坐轿子来求凤姐', '贾琏院 · 院中', 2, 7, 9,
     ['E:feng:greet:1.2']),
    ('c23-tiejian', 'C23-013', 'narrator', '凤姐因见他素日不大拿班作势的，便依允了', '贾琏院 · 院中', 2, 9, 11,
     ['E:feng:greet:1.2']),
    ('c23-tiejian', 'C23-014', 'feng', '这些小和尚道士万不可打发到别处去，一时娘娘出来就要承应', '贾琏院 · 院中', 2, 12, 14,
     ['E:feng:greet:1.4']),
    ('c23-tiejian', 'C23-015', 'feng', '倘或散了，若再用时，可是又费事', '贾琏院 · 院中', 2, 14, 17,
     ['E:feng:greet:1.4']),
    ('c23-tiejian', 'C23-016', 'feng', '依我的主意，不如将他们竟送到咱们家庙里铁槛寺去', '贾琏院 · 院中', 2, 17, 19,
     ['E:feng:greet:1.4']),
    ('c23-tiejian', 'C23-017', 'feng', '月间不过派一个人拿几两银子去买柴米就完了', '贾琏院 · 院中', 2, 19, 20,
     ['E:feng:greet:1.4']),
    ('c23-tiejian', 'C23-018', 'feng', '说声用，走去叫来，一点儿不费事呢', '贾琏院 · 院中', 2, 20, 23,
     ['E:feng:greet:1.4']),
    ('c23-tiejian', 'C23-019', 'narrator', '王夫人听了，便商之于贾政', '贾琏院 · 院中', 2, 23, 25,
     ['E:feng:rest:1.2']),
    ('c23-tiejian', 'C23-020', 'zheng', '倒是提醒了我，就是这样', '贾琏院 · 院中', 2, 26, 28,
     ['E:zheng:greet:1.4']),
    ('c23-tiejian', 'C23-021', 'narrator', '即时唤贾琏来', '贾琏院 · 院中', 2, 28, 29,
     ['E:zheng:rest:1.2']),
    ('c23-jiaqin', 'C23-022', 'narrator', '当下贾琏正同凤姐吃饭，一闻呼唤，放下饭便走', '贾琏院 · 正房', 3, 0, 1,
     ['M:jia_lian:table_place>room', 'S:jia_lian:room']),
    ('c23-jiaqin', 'C23-023', 'feng', '你且站住，听我说话', '贾琏院 · 正房', 3, 6, 8,
     ['E:feng:greet:1.4']),
    ('c23-jiaqin', 'C23-024', 'feng', '若是别的事我不管，若是为小和尚们的事，好歹依我这么著', '贾琏院 · 正房', 3, 8, 11,
     ['E:feng:greet:1.4']),
    ('c23-jiaqin', 'C23-025', 'narrator', '如此这般教了一套话', '贾琏院 · 正房', 3, 11, 12,
     ['E:feng:rest:1.2']),
    ('c23-jiaqin', 'C23-026', 'jia_lian', '我不知道，你有本事你说去', '贾琏院 · 正房', 3, 13, 15,
     ['E:jia_lian:greet:1.4']),
    ('c23-jiaqin', 'C23-027', 'narrator', '凤姐把头一梗，把筷子一放，腮上似笑不笑的瞅著贾琏', '贾琏院 · 正房', 3, 18, 19,
     ['E:feng:anger:1.4']),
    ('c23-jiaqin', 'C23-028', 'jia_lian', '西廊下五嫂子的儿子芸儿来求了我两三遭，要个事情管管', '贾琏院 · 正房', 3, 22, 24,
     ['E:jia_lian:greet:1.4']),
    ('c23-jiaqin', 'C23-029', 'jia_lian', '我依了，叫他等著', '贾琏院 · 正房', 3, 24, 26,
     ['E:jia_lian:greet:1.2']),
    ('c23-jiaqin', 'C23-030', 'jia_lian', '好容易出来这件事，你又夺了去', '贾琏院 · 正房', 3, 26, 28,
     ['E:jia_lian:greet:1.4']),
    ('c23-jiaqin', 'C23-031', 'feng', '园子东北角子上，娘娘说了，还叫多多的种松柏树', '贾琏院 · 正房', 3, 30, 33,
     ['E:feng:greet:1.4']),
    ('c23-jiaqin', 'C23-032', 'feng', '等这件事出来，我管保叫芸儿管这件工程', '贾琏院 · 正房', 3, 34, 36,
     ['E:feng:greet:1.4']),
    ('c23-jiaqin', 'C23-033', 'jia_lian', '果这样也罢了', '贾琏院 · 正房', 3, 37, 38,
     ['E:jia_lian:greet:1.2']),
    ('c23-jiaqin', 'C23-034', 'jia_lian', '只是昨儿晚上，我不过是要改个样儿，你就扭手扭脚的', '贾琏院 · 正房', 3, 38, 41,
     ['E:jia_lian:greet:1.4']),
    ('c23-jiaqin', 'C23-035', 'narrator', '凤姐嗤的一声笑了，向贾琏啐了一口，低下头便吃饭', '贾琏院 · 正房', 3, 41, 45,
     ['E:feng:rest:1.2']),
    ('c23-jiaqin', 'C23-036', 'narrator', '贾琏已经笑著去了，到了前面见了贾政，果然是小和尚一事', '贾琏院 · 正房', 4, 0, 3,
     ['M:jia_lian:room>yard', 'E:jia_lian:rest:1.2']),
    ('c23-jiaqin', 'C23-037', 'jia_lian', '如今看来，芹儿倒大大的出息了，这件事竟交予他去管办', '贾琏院 · 院中', 4, 5, 8,
     ['E:jia_lian:greet:1.4']),
    ('c23-jiaqin', 'C23-038', 'jia_lian', '横竖照在里头的规例，每月叫芹儿支领就是了', '贾琏院 · 院中', 4, 8, 10,
     ['E:jia_lian:greet:1.4']),
    ('c23-jiaqin', 'C23-039', 'narrator', '贾政原不大理论这些事，听贾琏如此说，便如此依了', '贾琏院 · 院中', 4, 10, 13,
     ['E:jia_lian:rest:1.2']),
    ('c23-jiaqin', 'C23-040', 'narrator', '贾琏回到房中告诉凤姐儿，凤姐即命人去告诉了周氏', '贾琏院 · 正房', 4, 13, 15,
     ['M:jia_lian:yard>room', 'E:feng:greet:1.2']),
    ('c23-jiaqin', 'C23-041', 'narrator', '凤姐又作情央贾琏先支三个月的，叫他写了领字', '贾琏院 · 正房', 4, 17, 19,
     ['E:feng:greet:1.4']),
    ('c23-jiaqin', 'C23-042', 'narrator', '贾琏批票画了押，登时发了对牌出去', '贾琏院 · 正房', 4, 19, 21,
     ['E:jia_lian:greet:1.2']),
    ('c23-jiaqin', 'C23-043', 'narrator', '银库上按数发出三个月的供给来，白花花二三百两', '贾琏院 · 正房', 4, 21, 23,
     ['E:feng:rest:1.4']),
    ('c23-jiaqin', 'C23-044', 'narrator', '贾芹随手拈一块，撂予掌平的人，叫他们吃茶罢', '贾琏院 · 正房', 4, 23, 26,
     ['S:jia_qin:yard', 'E:jia_qin:greet:1.4']),
    ('c23-jiaqin', 'C23-045', 'narrator', '于是命小厮拿回家，与母亲商议', '贾琏院 · 院中', 4, 26, 28,
     ['M:jia_qin:yard>gate', 'E:jia_qin:rest:1.2']),
    ('c23-jiaqin', 'C23-046', 'narrator', '雇了大叫驴，又雇了几辆车，至荣国府角门，唤出二十四个人来', '贾琏院 · 院中', 4, 30, 34,
     ['E:jia_qin:rest:1.4']),
    ('c23-jiaqin', 'C23-047', 'narrator', '一径往城外铁槛寺去了', '贾琏院 · 院中', 4, 34, 35,
     ['E:jia_qin:rest:1.2']),
    ('c23-yuci', 'C23-048', 'narrator', '贾元春因在宫中自编大观园题咏之后，忽想起那大观园中景致', '贾母院 · 正房', 5, 0, 3,
     ['H:feng', 'H:jia_lian', 'H:jia_qin', 'S:grandmother:grandmother_place']),
    ('c23-yuci', 'C23-049', 'narrator', '况家中现有几个能诗会赋的姊妹，何不命他们进去居住', '贾母院 · 正房', 5, 7, 9,
     ['E:grandmother:rest:1.4']),
    ('c23-yuci', 'C23-050', 'narrator', '若不命他进去，只怕他冷清了，一时不大畅快', '贾母院 · 正房', 5, 13, 16,
     ['E:grandmother:rest:1.4']),
    ('c23-yuci', 'C23-051', 'narrator', '遂命太监夏守忠到荣国府来下一道谕', '贾母院 · 正房', 5, 19, 20,
     ['E:grandmother:rest:1.2']),
    ('c23-yuci', 'C23-052', 'narrator', '命宝钗等只管在园中居住，不可禁约封锢，命宝玉仍随进去读书', '贾母院 · 正房', 5, 20, 23,
     ['E:grandmother:rest:1.4']),
    ('c23-yuci', 'C23-053', 'narrator', '贾政，王夫人接了这谕，便来回明贾母', '贾母院 · 正房', 6, 1, 2,
     ['S:zheng:back_door', 'S:wang:wang_place']),
    ('c23-yuci', 'C23-054', 'narrator', '遣人进去各处收拾打扫，安设帘幔床帐', '贾母院 · 正房', 6, 4, 6,
     ['E:grandmother:rest:1.2']),
    ('c23-yuci', 'C23-055', 'narrator', '别人听了还自犹可，惟宝玉听了这谕，喜的无可不可', '贾母院 · 正房', 6, 6, 9,
     ['S:baoyu:baoyu_greet', 'E:baoyu:greet:1.4']),
    ('c23-jingong', 'C23-056', 'narrator', '正和贾母盘算，要这个，弄那个，忽见丫鬟来说：老爷叫宝玉', '贾母院 · 正房', 6, 9, 14,
     ['S:baoyu:grandmother_place', 'E:baoyu:rest:1.2']),
    ('c23-jingong', 'C23-057', 'narrator', '宝玉听了，好似打了个焦雷，登时扫去兴头，脸上转了颜色', '贾母院 · 正房', 6, 14, 18,
     ['E:baoyu:anger:1.4']),
    ('c23-jingong', 'C23-058', 'narrator', '便拉著贾母扭的好似扭股儿糖，杀死不敢去', '贾母院 · 正房', 6, 18, 20,
     ['E:baoyu:anger:1.4']),
    ('c23-jingong', 'C23-059', 'grandmother', '好宝贝，你只管去，有我呢，他不敢委屈了你', '贾母院 · 正房', 6, 21, 25,
     ['E:grandmother:greet:1.4']),
    ('c23-jingong', 'C23-060', 'grandmother', '况且你又作了那篇好文章', '贾母院 · 正房', 6, 25, 26,
     ['E:grandmother:greet:1.2']),
    ('c23-jingong', 'C23-061', 'grandmother', '他吩咐你几句，不过不教你在里头淘气', '贾母院 · 正房', 6, 27, 29,
     ['E:grandmother:greet:1.4']),
    ('c23-jingong', 'C23-062', 'grandmother', '他说什么，你只好生答应著就是了', '贾母院 · 正房', 6, 29, 31,
     ['E:grandmother:greet:1.4']),
    ('c23-jingong', 'C23-063', 'narrator', '一面安慰，一面唤了两个老嬷嬷来', '贾母院 · 正房', 6, 31, 33,
     ['E:grandmother:rest:1.2']),
    ('c23-jingong', 'C23-064', 'narrator', '吩咐好生带了宝玉去，别叫他老子唬著他', '贾母院 · 正房', 6, 33, 35,
     ['E:grandmother:rest:1.2']),
    ('c23-jingong', 'C23-065', 'narrator', '老嬷嬷答应了', '贾母院 · 正房', 6, 35, 36,
     ['E:grandmother:rest:1.2']),
    ('c23-jingong', 'C23-066', 'narrator', '宝玉一步挪不了三寸，蹭到这边来', '贾母院 · 正房', 7, 0, 2,
     ['M:baoyu:baoyu_greet>tea_place', 'E:baoyu:rest:1.4']),
    ('c23-jiaozheng', 'C23-067', 'narrator', '可巧贾政在王夫人房中商议事情', '王夫人院 · 外廊', 7, 3, 4,
     ['H:grandmother', 'H:zheng', 'H:wang', 'H:baoyu', 'S:jinyuan:east_corridor', 'S:caiyun:east_corridor']),
    ('c23-jiaozheng', 'C23-068', 'narrator', '金钏儿，彩云，彩霞，绣鸾，绣凤等众丫鬟都在廊檐底下站著呢', '王夫人院 · 外廊', 7, 4, 9,
     ['E:jinyuan:rest:1.2']),
    ('c23-jiaozheng', 'C23-069', 'narrator', '一见宝玉来，都抿著嘴笑', '王夫人院 · 外廊', 7, 9, 11,
     ['E:caiyun:rest:1.2']),
    ('c23-jiaozheng', 'C23-070', 'jinyuan', '我这嘴上是才擦的香浸胭脂，你这会子可吃不吃了？', '王夫人院 · 外廊', 7, 13, 15,
     ['S:baoyu:south_passage', 'E:jinyuan:greet:1.4']),
    ('c23-jiaozheng', 'C23-071', 'caiyun', '人家正心里不自在，你还奚落他', '王夫人院 · 外廊', 7, 17, 19,
     ['E:caiyun:greet:1.4']),
    ('c23-jiaozheng', 'C23-072', 'caiyun', '趁这会子喜欢，快进去罢', '王夫人院 · 外廊', 7, 19, 21,
     ['E:caiyun:greet:1.2']),
    ('c23-jiaozheng', 'C23-073', 'narrator', '宝玉只得挨进门去', '王夫人院 · 门内', 7, 21, 22,
     ['M:baoyu:south_passage>hall_entry', 'E:baoyu:rest:1.4']),
    ('c23-jiaozheng', 'C23-074', 'narrator', '原来贾政和王夫人都在里间呢', '王夫人院 · 里间', 7, 22, 23,
     ['S:zheng:wang_host', 'S:wang:tea_seat']),
    ('c23-jiaozheng', 'C23-075', 'narrator', '赵姨娘打起帘子，宝玉躬身进去', '王夫人院 · 里间', 7, 23, 25,
     ['S:zhao_yiniang:guest_seat', 'E:baoyu:rest:1.2']),
    ('c23-jiaozheng', 'C23-076', 'narrator', '贾政和王夫人对面坐在炕上说话，地下一溜椅子', '王夫人院 · 里间', 7, 25, 27,
     ['S:yingchun:kang_edge', 'S:tanchun:guest_seat', 'S:xichun:tea_seat', 'S:jia_huan:li_room']),
    ('c23-jiaozheng', 'C23-077', 'narrator', '迎春，探春，惜春，贾环四个人都坐在那里', '王夫人院 · 里间', 7, 27, 31,
     ['E:tanchun:rest:1.2']),
    ('c23-jiaozheng', 'C23-078', 'narrator', '一见他进来，惟有探春和惜春，贾环站了起来', '王夫人院 · 里间', 7, 31, 34,
     ['E:tanchun:greet:1.2']),
    ('c23-jiaozheng', 'C23-079', 'narrator', '贾政一举目，见宝玉站在跟前，神彩飘逸，秀色夺人', '王夫人院 · 里间', 8, 0, 4,
     ['E:zheng:rest:1.4']),
    ('c23-jiaozheng', 'C23-080', 'narrator', '看看贾环，人物委琐，举止荒疏，忽又想起贾珠来', '王夫人院 · 里间', 8, 4, 8,
     ['E:zheng:rest:1.4']),
    ('c23-jiaozheng', 'C23-081', 'narrator', '再看看王夫人只有这一个亲生的儿子，素爱如珍', '王夫人院 · 里间', 8, 8, 10,
     ['E:zheng:rest:1.2']),
    ('c23-jiaozheng', 'C23-082', 'narrator', '把素日嫌恶处分宝玉之心不觉减了八九', '王夫人院 · 里间', 8, 12, 13,
     ['E:zheng:rest:1.4']),
    ('c23-jiaozheng', 'C23-083', 'zheng', '娘娘吩咐说，你日日外头嬉游，渐次疏懒，如今叫禁管', '王夫人院 · 里间', 8, 14, 18,
     ['E:zheng:greet:1.4']),
    ('c23-jiaozheng', 'C23-084', 'zheng', '同你姊妹在园里读书写字', '王夫人院 · 里间', 8, 18, 19,
     ['E:zheng:greet:1.2']),
    ('c23-jiaozheng', 'C23-085', 'zheng', '你可好生用心习学，再如不守分安常，你可仔细！', '王夫人院 · 里间', 8, 19, 22,
     ['E:zheng:greet:1.4']),
    ('c23-jiaozheng', 'C23-086', 'narrator', '宝玉连连的答应了几个是', '王夫人院 · 里间', 8, 22, 23,
     ['E:baoyu:rest:1.4']),
    ('c23-jiaozheng', 'C23-087', 'narrator', '王夫人便拉他在身旁坐下，他姊弟三人依旧坐下', '王夫人院 · 里间', 8, 23, 25,
     ['E:wang:greet:1.2']),
    ('c23-jiaozheng', 'C23-088', 'wang', '前儿的丸药都吃完了？', '王夫人院 · 里间', 9, 1, 2,
     ['E:wang:greet:1.4']),
    ('c23-jiaozheng', 'C23-089', 'baoyu', '还有一丸', '王夫人院 · 里间', 9, 3, 4,
     ['E:baoyu:greet:1.2']),
    ('c23-jiaozheng', 'C23-090', 'wang', '明儿再取十丸来，天天临睡的时候，叫袭人伏侍你吃了再睡', '王夫人院 · 里间', 9, 5, 8,
     ['E:wang:greet:1.4']),
    ('c23-jiaozheng', 'C23-091', 'baoyu', '只从太太吩咐了，袭人天天晚上想著，打发我吃', '王夫人院 · 里间', 9, 9, 12,
     ['E:baoyu:greet:1.4']),
    ('c23-jiaozheng', 'C23-092', 'zheng', '袭人是何人？', '王夫人院 · 里间', 9, 13, 14,
     ['E:zheng:greet:1.2']),
    ('c23-jiaozheng', 'C23-093', 'wang', '是个丫头', '王夫人院 · 里间', 9, 15, 16,
     ['E:wang:greet:1.2']),
    ('c23-jiaozheng', 'C23-094', 'zheng', '丫头不管叫个什么罢了，是谁这样刁钻，起这样的名字？', '王夫人院 · 里间', 9, 17, 20,
     ['E:zheng:greet:1.4']),
    ('c23-jiaozheng', 'C23-095', 'wang', '是老太太起的', '王夫人院 · 里间', 9, 22, 23,
     ['E:wang:greet:1.2']),
    ('c23-jiaozheng', 'C23-096', 'zheng', '老太太如何知道这话，一定是宝玉', '王夫人院 · 里间', 9, 24, 26,
     ['E:zheng:greet:1.4']),
    ('c23-jiaozheng', 'C23-097', 'baoyu', '因素日读诗，曾记古人有一句诗云：花气袭人知昼暖', '王夫人院 · 里间', 9, 28, 31,
     ['E:baoyu:greet:1.4']),
    ('c23-jiaozheng', 'C23-098', 'narrator', '因这个丫头姓花，便随口起了这个名字', '王夫人院 · 里间', 9, 31, 33,
     ['E:baoyu:rest:1.4']),
    ('c23-jiaozheng', 'C23-099', 'wang', '宝玉，你回去改了罢。老爷也不用为这小事动气', '王夫人院 · 里间', 9, 34, 37,
     ['E:wang:greet:1.4']),
    ('c23-jiaozheng', 'C23-100', 'zheng', '究竟也无碍，又何用改', '王夫人院 · 里间', 9, 38, 40,
     ['E:zheng:greet:1.2']),
    ('c23-jiaozheng', 'C23-101', 'zheng', '只是可见宝玉不务正，专在这些浓词艳赋上作工夫', '王夫人院 · 里间', 9, 40, 42,
     ['E:zheng:greet:1.4']),
    ('c23-jiaozheng', 'C23-102', 'zheng', '作业的畜生，还不出去！', '王夫人院 · 里间', 9, 44, 46,
     ['E:zheng:anger:1.4']),
    ('c23-jiaozheng', 'C23-103', 'wang', '去罢，只怕老太太等你吃饭呢', '王夫人院 · 里间', 9, 47, 49,
     ['E:wang:greet:1.4']),
    ('c23-jiaozheng', 'C23-104', 'narrator', '宝玉慢慢的退出去，向金钏儿笑著伸伸舌头', '王夫人院 · 门内', 9, 51, 52,
     ['M:baoyu:hall_entry>south_passage', 'E:baoyu:greet:1.2']),
    ('c23-jiaozheng', 'C23-105', 'narrator', '刚至穿堂门前，只见袭人倚门立在那里', '王夫人院 · 门内', 9, 53, 55,
     ['S:xiren:east_corridor', 'E:xiren:greet:1.4']),
    ('c23-jiaozheng', 'C23-106', 'xiren', '叫你作什么？', '王夫人院 · 门内', 9, 57, 58,
     ['E:xiren:greet:1.2']),
    ('c23-jiaozheng', 'C23-107', 'baoyu', '没有什么，不过怕我进园去淘气，吩咐吩咐', '王夫人院 · 门内', 9, 59, 62,
     ['E:baoyu:greet:1.4']),
    ('c23-jiaozheng', 'C23-108', 'narrator', '一面说，一面回至贾母跟前，回明原委', '王夫人院 · 门内', 9, 62, 65,
     ['E:baoyu:rest:1.2']),
    ('c23-fenju', 'C23-109', 'narrator', '只见林黛玉正在那里，宝玉便问他：你住那一处好？', '贾母院 · 正房', 9, 65, 68,
     ['H:zheng', 'H:wang', 'H:yingchun', 'H:tanchun', 'H:xichun', 'H:jia_huan', 'H:zhao_yiniang', 'H:jinyuan', 'H:caiyun', 'S:daiyu:daiyu_place', 'S:baoyu:baoyu_greet']),
    ('c23-fenju', 'C23-110', 'daiyu', '我心里想著潇湘馆好，爱那几竿竹子隐著一道曲栏', '贾母院 · 正房', 9, 71, 73,
     ['E:daiyu:greet:1.4']),
    ('c23-fenju', 'C23-111', 'daiyu', '比别处更觉幽静', '贾母院 · 正房', 9, 73, 74,
     ['E:daiyu:greet:1.2']),
    ('c23-fenju', 'C23-112', 'baoyu', '正和我的主意一样，我也要叫你住这里呢', '贾母院 · 正房', 9, 75, 77,
     ['E:baoyu:greet:1.4']),
    ('c23-fenju', 'C23-113', 'baoyu', '我就住怡红院，咱们两个又近，又都清幽', '贾母院 · 正房', 9, 77, 80,
     ['E:baoyu:greet:1.4']),
    ('c23-fenju', 'C23-114', 'narrator', '两人正计较，就有贾政遣人来回贾母说', '贾母院 · 正房', 10, 0, 2,
     ['E:grandmother:rest:1.2']),
    ('c23-fenju', 'C23-115', 'narrator', '二月二十二日子好，哥儿姐儿们好搬进去的', '贾母院 · 正房', 10, 2, 4,
     ['E:grandmother:rest:1.2']),
    ('c23-fenju', 'C23-116', 'narrator', '这几日内遣人进去分派收拾', '贾母院 · 正房', 10, 4, 5,
     ['E:grandmother:rest:1.2']),
    ('c23-fenju', 'C23-117', 'narrator', '薛宝钗住了蘅芜苑，林黛玉住了潇湘馆，贾迎春住了缀锦楼', '贾母院 · 正房', 10, 5, 8,
     ['E:grandmother:rest:1.4']),
    ('c23-fenju', 'C23-118', 'narrator', '探春住了秋爽斋，惜春住了蓼风轩，李氏住了稻香村，宝玉住了怡红院', '贾母院 · 正房', 10, 8, 12,
     ['E:grandmother:rest:1.4']),
    ('c23-fenju', 'C23-119', 'narrator', '每一处添两个老嬷嬷，四个丫头，另有专管收拾打扫的', '贾母院 · 正房', 10, 12, 16,
     ['E:grandmother:rest:1.2']),
    ('c23-fenju', 'C23-120', 'narrator', '至二十二日，一齐进去，登时园内花招绣带，柳拂香风', '贾母院 · 正房', 10, 16, 20,
     ['E:grandmother:rest:1.4']),
    ('c23-sishi', 'C23-121', 'narrator', '且说宝玉自进花园以来，心满意足，再无别项可生贪求之心', '怡红院 · 里间', 11, 1, 4,
     ['S:baoyu:baoyu_kang', 'E:baoyu:rest:1.4']),
    ('c23-sishi', 'C23-122', 'narrator', '每日只和姊妹丫头们一处，或读书，或写字，或弹琴下棋', '怡红院 · 里间', 11, 4, 8,
     ['E:baoyu:rest:1.4']),
    ('c23-sishi', 'C23-123', 'narrator', '作画吟诗，以至描鸾刺凤，斗草簪花，无所不至，倒也十分快乐', '怡红院 · 里间', 11, 8, 14,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-124', 'narrator', '他曾有几首即事诗，虽不算好，却倒是真情真景', '怡红院 · 书案前', 11, 15, 18,
     ['M:baoyu:baoyu_kang>desk_place', 'E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-125', 'narrator', '春夜即事', '怡红院 · 书案前', 12, 0, 1,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-126', 'narrator', '霞绡云幄任舖陈，隔巷蟆更听未真', '怡红院 · 书案前', 13, 0, 2,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-127', 'narrator', '枕上轻寒窗外雨，眼前春色梦中人', '怡红院 · 书案前', 13, 2, 4,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-128', 'narrator', '盈盈烛泪因谁泣，点点花愁为我嗔', '怡红院 · 书案前', 13, 4, 6,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-129', 'narrator', '自是小鬟娇懒惯，拥衾不耐笑言频', '怡红院 · 书案前', 13, 6, 8,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-130', 'narrator', '夏夜即事', '怡红院 · 书案前', 14, 0, 1,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-131', 'narrator', '倦绣佳人幽梦长，金笼鹦鹉唤茶汤', '怡红院 · 书案前', 15, 0, 2,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-132', 'narrator', '窗明麝月开宫镜，室霭檀云品御香', '怡红院 · 书案前', 15, 2, 4,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-133', 'narrator', '琥珀杯倾荷露滑，玻璃槛纳柳风凉', '怡红院 · 书案前', 15, 4, 6,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-134', 'narrator', '水亭处处齐纨动，帘卷朱楼罢晚妆', '怡红院 · 书案前', 15, 6, 8,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-135', 'narrator', '秋夜即事', '怡红院 · 书案前', 16, 0, 1,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-136', 'narrator', '绛芸轩里绝喧哗，桂魄流光浸茜纱', '怡红院 · 书案前', 17, 0, 2,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-137', 'narrator', '苔锁石纹容睡鹤，井飘桐露湿栖鸦', '怡红院 · 书案前', 17, 2, 4,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-138', 'narrator', '抱衾婢至舒金凤，倚槛人归落翠花', '怡红院 · 书案前', 17, 4, 6,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-139', 'narrator', '静夜不眠因酒渴，沉烟重拨索烹茶', '怡红院 · 书案前', 17, 6, 8,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-140', 'narrator', '冬夜即事', '怡红院 · 书案前', 18, 0, 1,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-141', 'narrator', '梅魂竹梦已三更，锦罽鹔衾睡未成', '怡红院 · 书案前', 19, 0, 2,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-142', 'narrator', '松影一庭惟见鹤，梨花满地不闻莺', '怡红院 · 书案前', 19, 2, 4,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-143', 'narrator', '女儿翠袖诗怀冷，公子金貂酒力轻', '怡红院 · 书案前', 19, 4, 6,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-144', 'narrator', '却喜侍儿知试茗，扫将新雪及时烹', '怡红院 · 书案前', 19, 6, 8,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-145', 'narrator', '当时有一等势利人，见是荣国府十二三岁的公子作的，抄录出来各处称颂', '怡红院 · 书案前', 20, 1, 4,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-146', 'narrator', '因此竟有人来寻诗觅字，倩画求题的', '怡红院 · 书案前', 20, 8, 10,
     ['E:baoyu:rest:1.2']),
    ('c23-sishi', 'C23-147', 'narrator', '宝玉亦发得了意，镇日家作这些外务', '怡红院 · 书案前', 20, 10, 12,
     ['E:baoyu:greet:1.2']),
    ('c23-sishi', 'C23-148', 'narrator', '谁想静中生烦恼，忽一日不自在起来，这也不好，那也不好', '怡红院 · 外间', 21, 0, 4,
     ['M:baoyu:desk_place>baoyu_outer', 'E:baoyu:rest:1.4']),
    ('c23-sishi', 'C23-149', 'narrator', '园中那些人多半是女孩儿，坐卧不避，嘻笑无心', '怡红院 · 外间', 21, 5, 6,
     ['E:baoyu:rest:1.4']),
    ('c23-sishi', 'C23-150', 'narrator', '那宝玉心内不自在，便懒在园内，只在外头鬼混，却又痴痴的', '怡红院 · 外间', 21, 11, 15,
     ['E:baoyu:rest:1.4']),
    ('c23-mingsmoke', 'C23-151', 'narrator', '茗烟见他这样，因想与他开心，左思右想，皆是宝玉顽烦了的', '怡红院 · 外间', 21, 15, 19,
     ['S:ming_yan:mirror_place', 'E:ming_yan:rest:1.4']),
    ('c23-mingsmoke', 'C23-152', 'narrator', '惟有这件，宝玉不曾看见过', '怡红院 · 外间', 21, 20, 22,
     ['E:ming_yan:rest:1.2']),
    ('c23-mingsmoke', 'C23-153', 'narrator', '便走去到书坊内，把那古今小说并那飞燕，合德，武则天，杨贵妃的外传买了许多来', '怡红院 · 外间', 21, 23, 28,
     ['E:ming_yan:greet:1.4']),
    ('c23-mingsmoke', 'C23-154', 'narrator', '引宝玉看。宝玉何曾见过这些书，一看见了便如得了珍宝', '怡红院 · 外间', 21, 28, 31,
     ['E:baoyu:greet:1.4']),
    ('c23-mingsmoke', 'C23-155', 'narrator', '茗烟又嘱咐他不可拿进园去', '怡红院 · 外间', 21, 31, 32,
     ['E:ming_yan:rest:1.4']),
    ('c23-mingsmoke', 'C23-156', 'narrator', '若叫人知道了，我就吃不了兜著走呢', '怡红院 · 外间', 21, 32, 34,
     ['E:ming_yan:greet:1.4']),
    ('c23-mingsmoke', 'C23-157', 'narrator', '宝玉那里舍的不拿进园去，踟蹰再三，单把那文理细密的拣了几套进去', '怡红院 · 里间', 21, 34, 37,
     ['M:baoyu:baoyu_outer>book_place', 'E:baoyu:rest:1.2']),
    ('c23-mingsmoke', 'C23-158', 'narrator', '放在床顶上，无人时自己密看', '怡红院 · 里间', 21, 37, 39,
     ['E:baoyu:rest:1.4']),
    ('c23-mingsmoke', 'C23-159', 'narrator', '那粗俗过露的，都藏在外面书房里', '怡红院 · 里间', 21, 39, 41,
     ['E:baoyu:rest:1.2']),
    ('c23-taohua', 'C23-160', 'narrator', '那一日正当三月中浣，早饭后，宝玉携了一套《会真记》', '沁芳闸 · 桃花坡', 22, 0, 3,
     ['H:ming_yan', 'S:baoyu:stone_seat']),
    ('c23-taohua', 'C23-161', 'narrator', '走到沁芳闸桥边桃花底下一块石上坐著，展开《会真记》，从头细玩', '沁芳闸 · 桃花坡', 22, 3, 6,
     ['E:baoyu:rest:1.4']),
    ('c23-taohua', 'C23-162', 'narrator', '正看到落红成阵，只见一阵风过，把树头上桃花吹下一大半来', '沁芳闸 · 桃花坡', 22, 6, 9,
     ['E:baoyu:rest:1.4']),
    ('c23-taohua', 'C23-163', 'narrator', '落的满身满书满地皆是', '沁芳闸 · 桃花坡', 22, 9, 10,
     ['E:baoyu:rest:1.2']),
    ('c23-taohua', 'C23-164', 'narrator', '宝玉要抖将下来，恐怕脚步践踏了，只得兜了那花瓣', '沁芳闸 · 桃花坡', 22, 10, 13,
     ['E:baoyu:rest:1.4']),
    ('c23-taohua', 'C23-165', 'narrator', '来至池边，抖在池内', '沁芳闸 · 池边', 22, 13, 15,
     ['M:baoyu:stone_seat>bank_west', 'E:baoyu:rest:1.2']),
    ('c23-taohua', 'C23-166', 'narrator', '那花瓣浮在水面，飘飘荡荡，竟流出沁芳闸去了', '沁芳闸 · 池边', 22, 15, 18,
     ['E:baoyu:rest:1.4']),
    ('c23-taohua', 'C23-167', 'narrator', '回来只见地下还有许多，宝玉正踟蹰间', '沁芳闸 · 桃花坡', 23, 0, 2,
     ['M:baoyu:bank_west>stone_seat', 'E:baoyu:rest:1.2']),
    ('c23-taohua', 'C23-168', 'narrator', '只听背后有人说道：你在这里作什么？', '沁芳闸 · 桃花坡', 23, 2, 4,
     ['E:baoyu:rest:1.4']),
    ('c23-taohua', 'C23-169', 'narrator', '宝玉一回头，却是林黛玉来了', '沁芳闸 · 桃花坡', 23, 4, 6,
     ['S:daiyu:peach_grove', 'E:daiyu:greet:1.4']),
    ('c23-taohua', 'C23-170', 'narrator', '肩上担著花锄，锄上挂著花囊，手内拿著花帚', '沁芳闸 · 桃花坡', 23, 6, 9,
     ['E:daiyu:rest:1.4']),
    ('c23-taohua', 'C23-171', 'baoyu', '好，好，来把这个花扫起来，撂在那水里', '沁芳闸 · 桃花坡', 23, 10, 14,
     ['E:baoyu:greet:1.4']),
    ('c23-taohua', 'C23-172', 'baoyu', '我才撂了好些在那里呢', '沁芳闸 · 桃花坡', 23, 14, 15,
     ['E:baoyu:greet:1.2']),
    ('c23-taohua', 'C23-173', 'daiyu', '撂在水里不好', '沁芳闸 · 桃花坡', 23, 16, 17,
     ['E:daiyu:greet:1.4']),
    ('c23-taohua', 'C23-174', 'daiyu', '你看这里的水干净，只一流出去，有人家的地方脏的臭的混倒', '沁芳闸 · 桃花坡', 23, 17, 20,
     ['E:daiyu:greet:1.4']),
    ('c23-taohua', 'C23-175', 'daiyu', '仍旧把花遭塌了', '沁芳闸 · 桃花坡', 23, 20, 21,
     ['E:daiyu:greet:1.4']),
    ('c23-taohua', 'C23-176', 'daiyu', '那畸角上我有一个花冢，如今把他扫了，装在这绢袋里，拿土埋上', '沁芳闸 · 桃花坡', 23, 21, 25,
     ['E:daiyu:greet:1.4']),
    ('c23-taohua', 'C23-177', 'daiyu', '日久不过随土化了，岂不干净', '沁芳闸 · 桃花坡', 23, 25, 27,
     ['E:daiyu:greet:1.4']),
    ('c23-huizhen', 'C23-178', 'baoyu', '待我放下书，帮你来收拾', '沁芳闸 · 桃花坡', 24, 2, 4,
     ['S:baoyu:stone_seat', 'S:daiyu:tomb', 'E:baoyu:greet:1.4']),
    ('c23-huizhen', 'C23-179', 'daiyu', '什么书？', '沁芳闸 · 桃花坡', 24, 5, 6,
     ['E:daiyu:greet:1.2']),
    ('c23-huizhen', 'C23-180', 'narrator', '宝玉见问，慌的藏之不迭', '沁芳闸 · 桃花坡', 24, 6, 8,
     ['E:baoyu:rest:1.2']),
    ('c23-huizhen', 'C23-181', 'baoyu', '不过是《中庸》《大学》', '沁芳闸 · 桃花坡', 24, 9, 10,
     ['E:baoyu:greet:1.4']),
    ('c23-huizhen', 'C23-182', 'daiyu', '你又在我跟前弄鬼', '沁芳闸 · 桃花坡', 24, 11, 12,
     ['E:daiyu:greet:1.4']),
    ('c23-huizhen', 'C23-183', 'daiyu', '趁早儿给我瞧，好多著呢', '沁芳闸 · 桃花坡', 24, 12, 14,
     ['E:daiyu:greet:1.4']),
    ('c23-huizhen', 'C23-184', 'baoyu', '好妹妹，若论你，我是不怕的', '沁芳闸 · 桃花坡', 24, 15, 18,
     ['E:baoyu:greet:1.4']),
    ('c23-huizhen', 'C23-185', 'baoyu', '你看了，好歹别告诉别人去', '沁芳闸 · 桃花坡', 24, 18, 20,
     ['E:baoyu:greet:1.4']),
    ('c23-huizhen', 'C23-186', 'baoyu', '真真这是好书！', '沁芳闸 · 桃花坡', 24, 20, 21,
     ['E:baoyu:greet:1.4']),
    ('c23-huizhen', 'C23-187', 'baoyu', '你要看了，连饭也不想吃呢', '沁芳闸 · 桃花坡', 24, 21, 23,
     ['E:baoyu:greet:1.4']),
    ('c23-huizhen', 'C23-188', 'narrator', '一面说，一面递了过去', '沁芳闸 · 桃花坡', 24, 23, 25,
     ['E:baoyu:rest:1.2']),
    ('c23-huizhen', 'C23-189', 'narrator', '林黛玉把花具且都放下，接书来瞧，从头看去，越看越爱看', '沁芳闸 · 桃花坡', 24, 25, 29,
     ['E:daiyu:rest:1.4']),
    ('c23-huizhen', 'C23-190', 'narrator', '不到一顿饭工夫，将十六出俱已看完，自觉词藻警人，余香满口', '沁芳闸 · 桃花坡', 24, 30, 34,
     ['E:daiyu:rest:1.4']),
    ('c23-huizhen', 'C23-191', 'narrator', '虽看完了书，却只管出神，心内还默默记诵', '沁芳闸 · 桃花坡', 24, 33, 36,
     ['E:daiyu:rest:1.2']),
    ('c23-madou', 'C23-192', 'baoyu', '妹妹，你说好不好？', '沁芳闸 · 桃花坡', 25, 1, 3,
     ['S:baoyu:stone_seat', 'S:daiyu:tomb', 'E:baoyu:greet:1.4']),
    ('c23-madou', 'C23-193', 'daiyu', '果然有趣', '沁芳闸 · 桃花坡', 25, 4, 5,
     ['E:daiyu:greet:1.2']),
    ('c23-madou', 'C23-194', 'baoyu', '我就是个多愁多病身，你就是那倾国倾城貌', '沁芳闸 · 桃花坡', 25, 6, 8,
     ['E:baoyu:greet:1.4']),
    ('c23-madou', 'C23-195', 'narrator', '林黛玉听了，不觉带腮连耳通红', '沁芳闸 · 桃花坡', 25, 8, 10,
     ['E:daiyu:anger:1.4']),
    ('c23-madou', 'C23-196', 'narrator', '登时直竖起两道似蹙非蹙的眉，瞪了两只似睁非睁的眼', '沁芳闸 · 桃花坡', 25, 10, 12,
     ['E:daiyu:anger:1.4']),
    ('c23-madou', 'C23-197', 'narrator', '微腮带怒，薄面含嗔，指宝玉道', '沁芳闸 · 桃花坡', 25, 13, 16,
     ['E:daiyu:anger:1.4']),
    ('c23-madou', 'C23-198', 'daiyu', '你这该死的胡说！好好的把这淫词艳曲弄了来，还学了这些混话来欺负我', '沁芳闸 · 桃花坡', 25, 15, 18,
     ['E:daiyu:greet:1.4']),
    ('c23-madou', 'C23-199', 'daiyu', '我告诉舅舅舅母去', '沁芳闸 · 桃花坡', 25, 18, 19,
     ['E:daiyu:greet:1.4']),
    ('c23-madou', 'C23-200', 'narrator', '说到欺负两个字上，早又把眼睛圈儿红了，转身就走', '沁芳闸 · 桃花坡', 25, 19, 22,
     ['E:daiyu:anger:1.4']),
    ('c23-madou', 'C23-201', 'baoyu', '好妹妹，千万饶我这一遭，原是我说错了', '沁芳闸 · 桃花坡', 25, 24, 27,
     ['E:baoyu:greet:1.4']),
    ('c23-madou', 'C23-202', 'baoyu', '若有心欺负我，明儿我掉在池子里，教个癞头鼋吞了去', '沁芳闸 · 桃花坡', 25, 27, 30,
     ['E:baoyu:greet:1.4']),
    ('c23-madou', 'C23-203', 'baoyu', '等你明儿做了一品夫人病老归西的时候，我往你坟上替你驮一辈子的碑去', '沁芳闸 · 桃花坡', 25, 31, 33,
     ['E:baoyu:greet:1.4']),
    ('c23-madou', 'C23-204', 'narrator', '说的林黛玉嗤的一声笑了，揉著眼睛', '沁芳闸 · 桃花坡', 25, 33, 35,
     ['E:daiyu:greet:1.2']),
    ('c23-madou', 'C23-205', 'daiyu', '一般也唬的这个调儿，还只管胡说', '沁芳闸 · 桃花坡', 25, 36, 38,
     ['E:daiyu:greet:1.2']),
    ('c23-madou', 'C23-206', 'daiyu', '呸，原来是苗而不秀，是个银样镴枪头', '沁芳闸 · 桃花坡', 25, 38, 41,
     ['E:daiyu:greet:1.4']),
    ('c23-madou', 'C23-207', 'baoyu', '你这个呢？我也告诉去', '沁芳闸 · 桃花坡', 25, 43, 45,
     ['E:baoyu:greet:1.2']),
    ('c23-madou', 'C23-208', 'daiyu', '你说你会过目成诵，难道我就不能一目十行么？', '沁芳闸 · 桃花坡', 25, 46, 48,
     ['E:daiyu:greet:1.4']),
    ('c23-madou', 'C23-209', 'narrator', '宝玉一面收书，一面笑道：正经快把花埋了罢', '沁芳闸 · 桃花坡', 26, 0, 3,
     ['E:baoyu:rest:1.2']),
    ('c23-madou', 'C23-210', 'narrator', '二人便收拾落花，正才掩埋妥协，只见袭人走来', '沁芳闸 · 花冢', 26, 4, 7,
     ['M:daiyu:peach_grove>tomb', 'M:baoyu:stone_seat>tomb', 'S:xiren:corner']),
    ('c23-madou', 'C23-211', 'xiren', '那里没找到，摸在这里来', '沁芳闸 · 花冢', 26, 8, 10,
     ['E:xiren:greet:1.4']),
    ('c23-madou', 'C23-212', 'xiren', '那边大老爷身上不好，姑娘们都过去请安', '沁芳闸 · 花冢', 26, 10, 12,
     ['E:xiren:greet:1.4']),
    ('c23-madou', 'C23-213', 'xiren', '老太太叫打发你去呢。快回去换衣裳去罢', '沁芳闸 · 花冢', 26, 12, 14,
     ['E:xiren:greet:1.4']),
    ('c23-madou', 'C23-214', 'narrator', '宝玉听了，忙拿了书，别了黛玉，同袭人回房换衣不提', '沁芳闸 · 花冢', 26, 14, 18,
     ['H:baoyu', 'H:daiyu', 'H:xiren']),
    ('c23-mudanting', 'C23-215', 'narrator', '林黛玉见宝玉去了，又听见众姊妹也不在房，自己闷闷的', '梨香院 · 墙外', 27, 0, 3,
     ['S:daiyu:lane_gate']),
    ('c23-mudanting', 'C23-216', 'narrator', '正欲回房，刚走到梨香院墙角上，只听墙内笛韵悠扬，歌声婉转', '梨香院 · 墙外', 27, 3, 7,
     ['E:daiyu:rest:1.4']),
    ('c23-mudanting', 'C23-217', 'narrator', '林黛玉便知是那十二个女孩子演习戏文呢', '梨香院 · 墙外', 27, 7, 8,
     ['E:daiyu:rest:1.2']),
    ('c23-mudanting', 'C23-218', 'narrator', '只是林黛玉素习不大喜看戏文，便不留心，只管往前走', '梨香院 · 墙外', 27, 8, 11,
     ['E:daiyu:rest:1.2']),
    ('c23-mudanting', 'C23-219', 'narrator', '偶然两句吹到耳内，明明白白，一字不落，唱道是', '梨香院 · 墙外', 27, 11, 15,
     ['E:daiyu:rest:1.4']),
    ('c23-mudanting', 'C23-220', 'narrator', '原来姹紫嫣红开遍，似这般都付与断井颓垣', '梨香院 · 墙外', 27, 15, 17,
     ['E:daiyu:rest:1.4']),
    ('c23-mudanting', 'C23-221', 'narrator', '林黛玉听了，倒也十分感慨缠绵，便止住步侧耳细听', '梨香院 · 墙外', 27, 17, 20,
     ['E:daiyu:rest:1.4']),
    ('c23-mudanting', 'C23-222', 'narrator', '又听唱道是：良辰美景奈何天，赏心乐事谁家院', '梨香院 · 墙外', 27, 21, 24,
     ['E:daiyu:rest:1.4']),
    ('c23-mudanting', 'C23-223', 'narrator', '听了这两句，不觉点头自叹', '梨香院 · 墙外', 27, 23, 25,
     ['E:daiyu:rest:1.2']),
    ('c23-mudanting', 'C23-224', 'narrator', '心下自思道：原来戏上也有好文章', '梨香院 · 墙外', 27, 25, 27,
     ['E:daiyu:rest:1.4']),
    ('c23-mudanting', 'C23-225', 'narrator', '可惜世人只知看戏，未必能领略这其中的趣味', '梨香院 · 墙外', 27, 27, 29,
     ['E:daiyu:rest:1.4']),
    ('c23-mudanting', 'C23-226', 'narrator', '想毕，又后悔不该胡想，耽误了听曲子', '梨香院 · 墙外', 27, 29, 32,
     ['E:daiyu:rest:1.2']),
    ('c23-mudanting', 'C23-227', 'narrator', '又侧耳时，只听唱道：则为你如花美眷，似水流年', '梨香院 · 墙外', 27, 33, 36,
     ['E:daiyu:rest:1.4']),
    ('c23-mudanting', 'C23-228', 'narrator', '林黛玉听了这两句，不觉心动神摇', '梨香院 · 墙外', 27, 35, 37,
     ['E:daiyu:anger:1.4']),
    ('c23-mudanting', 'C23-229', 'narrator', '又听道：你在幽闺自怜等句，亦发如醉如痴，站立不住', '梨香院 · 墙外', 27, 37, 40,
     ['E:daiyu:anger:1.4']),
    ('c23-mudanting', 'C23-230', 'narrator', '便一蹲身坐在一块山子石上，细嚼如花美眷，似水流年八个字的滋味', '梨香院 · 墙角', 27, 41, 44,
     ['M:daiyu:lane_gate>court_center', 'E:daiyu:rest:1.4']),
    ('c23-luoye', 'C23-231', 'narrator', '忽又想起前日见古人诗中有水流花谢两无情之句', '梨香院 · 墙角', 27, 44, 45,
     ['S:daiyu:court_center', 'E:daiyu:rest:1.4']),
    ('c23-luoye', 'C23-232', 'narrator', '再又有词中有流水落花春去也，天上人间之句', '梨香院 · 墙角', 27, 45, 47,
     ['E:daiyu:rest:1.4']),
    ('c23-luoye', 'C23-233', 'narrator', '又兼方才所见《西厢记》中花落水流红，闲愁万种之句，都一时想起来', '梨香院 · 墙角', 27, 47, 50,
     ['E:daiyu:rest:1.4']),
    ('c23-luoye', 'C23-234', 'narrator', '仔细忖度，不觉心痛神痴，眼中落泪', '梨香院 · 墙角', 27, 51, 54,
     ['E:daiyu:idle:1.4']),
    ('c23-luoye', 'C23-235', 'narrator', '正没个开交，忽觉背上击了一下，及回头看时，原来是', '梨香院 · 墙角', 27, 54, 58,
     ['E:daiyu:idle:1.4']),
    ('c23-luoye', 'C23-236', 'narrator', '妆晨绣夜心无矣，对月临风恨有之', '梨香院 · 墙角', 28, 0, 2,
     ['E:daiyu:idle:1.4']),
]


# ---------------------------------------------------------------- 证据补充
# 设计决定：哪些底本细节需要在证据表里显式记一笔「这是我们做的选择」。
DESIGN_NOTES = [
    ('C23-D1', 'c23-ledong',
     '勒石题咏一段只让探春一人在台上，其余督工者不作具象化',
     '底本写贾政命人镌字、贾珍率蓉萍监工、贾菖贾菱监工，还写了贾蔷管着'
     '十二个女戏。这些人若都上台就要各补立绘与 Q 版，且他们本回一句台词也没有。',
     '本回只让探春在台上（她是奉命抄录题咏的那个人，底本明写「命探春依次抄录」），'
     '其余监工者全部留在叙述里。这是「只让有动作的人上台」的一贯取舍，'
     '不宣称大观园里只有探春一人在场。'),
    ('C23-D2', 'c23-tiejian',
     '凤姐献计一段放在贾琏院，与第 21、22 回同一处',
     '底本只说周氏「便坐轿子来求凤姐」，未言凤姐在何处；'
     '凤姐院与贾琏院相邻，但项目里凤姐院是 wang 图上的 feng_room 一格。',
     '底本第 3 段明写「当下贾琏正同凤姐吃饭」，所以凤姐与贾琏同在贾琏院，'
     '本回演这段就在贾琏院，与第 21、22 回同一处，不新开图。'),
    ('C23-D3', 'c23-jiaqin',
     '贾芹在本回第一次真正登场——有站位、有动作，没有台词',
     '第 13 回的灵前名单里出现过「贾芹」，但那是一串名字，他从未现身。'
     '本回底本写他「随手拈一块，撂予掌平的人」「命小厮拿回家」'
     '「雇了大叫驴，自己骑上」「唤出二十四个人来」，动作明确，可以登台。',
     '贾芹是本回的新角色，需要补立绘与 Q 版。他在第 13 回没有资产，'
     '本回才第一次有戏份，因此这是「第 13 回提到过名字」与「第 23 回才有戏」的区别。'),
    ('C23-D4', 'c23-jiaqin',
     '周氏不登台：底本只写「便坐轿子来求凤姐」，无台词无动作',
     '周氏是贾芹之母，本回有明确的动作（坐轿子来求凤姐）。'
     '若给她登台就要再做一套立绘与 Q 版，且她没有一句台词。',
     '本回按「不具象化」处理：她来求凤姐这一节由叙述带过，'
     '凤姐的应允与贾芹领银子照常演出。她此后在第 26 回等处再登场，'
     '本回不给她立绘。这是一个「有动作但无台词的人物暂不立绘」的设计决定。'),
    ('C23-D5', 'c23-yuci',
     '元春的谕由叙述转述，夏守忠沿用第 16 回的 messenger 处理',
     '底本点名「太监夏守忠」，且写明全回元春都在宫中。',
     'cast 里没有太监。第 16 回「六宫都太监夏老爷来降旨」也是复用 messenger，'
     '本回沿用同一处理：不新增角色，也不把 messenger 说成是夏守忠。'
     '元春本人不登台——她第 16-23 回都在宫中，本回是第二次在宫。'),
    ('C23-D6', 'c23-jiaozheng',
     '彩霞、绣鸾、绣凤三人只作名单，不登台、不注册 cast',
     '底本写「金钏儿，彩云，彩霞，绣鸾，绣凤等众丫鬟都在廊檐底下站著呢」。'
     '五人当中金钏儿与彩云有台词有动作，彩霞、绣鸾、绣凤只有名字。',
     '本回只为金钏儿与彩云立绘。彩霞、绣鸾、绣凤在叙述里点到即止。'
     '另注：第 18 回 C18-048 出现的「绣凤」是「绣凤版舆」的一部分，'
     '不是人名，所以本回不与她们冲突。'),
    ('C23-D7', 'c23-jiaozheng',
     '金钏儿是本回的新角色——第 7 回她只在周瑞家的台词里被提到过',
     '第 7 回 C07-007「周瑞家的答应了，拿了匣子出来，问金钏儿那香菱是谁」，'
     '她只在旁白里被提到，从未现身。',
     '金钏儿本回有台词（「我这嘴上是才擦的香浸胭脂」）、有动作（拉住宝玉、抿嘴笑），'
     '所以本回是她的第一次登场，需要补立绘与 Q 版。'),
    ('C23-D8', 'c23-jingong',
     '「老爷叫宝玉」一段放在贾母院，元春下谕也在贾母院',
     '底本第 6 段写「便来回明贾母」，第 7 段写「宝玉听了，好似打了个焦雷」'
     '「便拉著贾母扭的好似扭股儿糖」——两人始终在一起。',
     '所以下谕、宝玉的反应、贾母的安慰三段都放在贾母院（dinner）。'
     '第 20、22 回的贾母院戏也都用这张图，本回沿用，不新开图。'),
    ('C23-D9', 'c23-jiaozheng',
     '贾政训斥一段放在王夫人院东廊（图 wang），廊下与里间分开',
     '底本第 7 段明写「可巧贾政在王夫人房中商议事情」，众丫鬟「都在廊檐底下站著」；'
     '第 8、9 段是里间的炕上说话。',
     'wang 图的 east_corridor 一格正是东廊，guest_seat/tea_seat/kang_edge 是里间。'
     '金钏儿与彩云在廊下（east_corridor），宝玉先进门（hall_entry）再入里间。'
     '注意：wang 图的路线是 L 形且在删 blocker 之后生效，'
     '金钏儿与彩云同在 east_corridor 一格，运行时引擎会让后来者让开最近的空格。'),
    ('C23-D10', 'c23-taohua',
     '沁芳闸桃花下是本回新建的一张图（qinfang）',
     '底本第 22 段写「走到沁芳闸桥边桃花底下一块石上坐著」，'
     '第 23 段写「来至池边」「那畸角上我有一个花冢」。'
     '项目原有 45 张图里没有任何一张有桃花、落花或水闸。',
     '所以本回新建 qinfang 图：桃林在桥西、闸台在北、桥横跨水面、'
     '花冢在东墙围出的凹角。桃树用 garden-tree（西府海棠的同一素材），'
     '本项目无桃花素材，记为改编；桥用石台代木石桥，同样记为改编。'),
    ('C23-D11', 'c23-madou',
     '黛玉肩上「花锄、花囊、花帚」不单独做素材',
     '底本第 23 段写「肩上担著花锄，锄上挂著花囊，手内拿著花帚」，'
     '这是黛玉此时最鲜明的形象标志。',
     '本项目的 manifest 里有锄头、扫帚一类的农具素材，但把它们与「花囊」'
     '组合成一套肩上担具需要新的合成图，代价大且容易与既有素材风格脱节。'
     '本回只用黛玉既有的立绘与 Q 版表现她来时的姿态，不额外做道具。'
     '这是「底本细节与产出成本冲突时优先保剧情主干」的取舍。'),
    ('C23-D12', 'c23-mudanting',
     '梨香院墙角那一段复用第四回的 c4_lixiang，不新开图',
     '底本第 27 段写「刚走到梨香院墙角上，只听墙内笛韵悠扬，歌声婉转」。'
     '梨香院是第四回为香菱入府建的专图，本回从墙外听声。',
     'c4_lixiang 的五个锚点里，lane_gate 是巷门、court_center 是院中，'
     '本回让黛玉从 lane_gate 走进院中、在 court_center 停下侧耳。'
     '唱戏的十二个女戏**不登台**——本回只从墙外听声，'
     '与第 18、22 回「戏在台上」的处理不同。'),
    ('C23-D13', 'c23-mudanting',
     '《牡丹亭》的唱词由叙述者引出，不设「唱戏的人」',
     '底本写「偶然两句吹到耳内，明明白白，一字不落，唱道是」，'
     '唱词由叙述者转述。',
     '本回让唱词以叙述节点出现，speaker 为 narrator，不虚构一个唱旦的 speaker。'
     '原曲中的「如花美眷，似水流年」等句照底本录出，'
     '只把弯引号统一成「」『』的排版样式（与第 16-22 回同一读法）。'),
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
                'chapter': 23,
                'paragraphLead': lead,
                'textKind': 'adaptation',
                'layer': 'present',
            },
            'id': nid,
            'speaker': speaker,
            'text': to_display(raw),
            'title': title,
            'actions': parse_actions(codes),
            # 底本位置：单调性校验用，写盘前会删掉。
            '_pos': (para, s_from),
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
    # 节点必须按底本顺序单调推进（段落 + 段内句号）。
    # 同一个句号区间常被拆成「叙述 + 台词」两个节点，它们共享 (段, 句)，
    # 所以第三级用节点在 CUTS 里的次序打破平局——底本位置相同并不代表
    # 顺序矛盾，两者本就是同一段文字的两半。
    pos = []
    for i, step in enumerate(steps):
        para, s_from = step['_pos']
        pos.append((para, s_from, i))
    for i in range(len(pos) - 1):
        if pos[i][:2] > pos[i + 1][:2]:
            errors.append(f'{steps[i]["id"]} → {steps[i+1]["id"]}: '
                          f'节点顺序与底本顺序不符（{pos[i][:2]} → {pos[i+1][:2]}）')
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
            'id': step['id'].replace('C23-', 'C23-E'),
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
        'chapter': 23,
        'source': {
            'edition': '维基文库《紅樓夢》第 023 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第023回&action=raw',
            'retrievedAt': '2026-11-15',
            'localText': 'docs/chapter23-source.txt',
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
        print('第23回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第23回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 23})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第23回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
