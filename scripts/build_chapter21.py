#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 21 回的剧情、段落、证据数据。

第 21 回底本是维基文库原文全文（docs/chapter21-source.txt），
写法沿用第 18/19/20 回确立的**底本切片式生成**：不手写正文，
按**句号索引**切片，正文与 source.paragraphLead 都是切出来的。

用法：
    python3 scripts/build_chapter21.py            # 生成
    python3 scripts/build_chapter21.py --check    # 只校验已有文件

这一回的两条戏与两处地点（对照 docs/chapter21-production.md 的分场规划）：

  yihong       大观园 · 怡红院 —— 门口拉扯、外间梳洗画眉、里间娇嗔、
                闷坐续《庄子》「焚花散麝」、掷笔就寝、次日摔断玉簪
  night        贾母院 · 碧纱橱与外间 —— 黛玉房。底本段 2/3 明写
                「往黛玉房中来」「湘云仍往黛玉房中安歇」，梳洗、画眉、
                拂落胭脂都在这里，不在怡红院。第 20 回曾把「贾母院 ·
                碧纱橱」当怡红院用，本回不再沿用那个借用。
  dinner       贾母院 · 后房与晚膳 —— 黛玉翻出《庄子》续书那一段
                （底本段 12：「因翻弄案上书看」），她在宝玉房里翻书，
                用 dinner 的 daiyu_place / back_door 表示。
  wang         王夫人院 · 东廊三间 —— 大姐出痘、凤姐供奉痘疹娘娘
  jialian_home 荣国府 · 贾琏院 —— 抖出青丝、隔窗说话、凤姐进院

人物：宝玉(baoyu)、黛玉(daiyu)、宝钗(baochai)、湘云(shi_xiangyun)、
袭人(xiren)、麝月(she_yue)、雪雁(xueyan)、平儿(ping_er)、贾琏(jia_lian)、
凤姐(feng)、贾母(grandmother)、王夫人(wang) 已在 cast；
新增 3 名需美术：紫鹃(zijun)、翠缕(cui_lv)、四儿(si_er)；
大姐儿、多浑虫、多姑娘儿 只作叙述，不出面（底本段 16 写得直露，
按第 19 回「原文只提及、没有实际到访的地点不安排人物进入」的纪律处理）。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter21-source.txt'
STORY = ROOT / 'design' / 'chapter21-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter21-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter21-evidence.json'

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


def split_sentences(text: str):
    """按句末标点切句，闭合引号归到前一句。

    ★ 句号索引是唯一无歧义的定位方式（第 20 回确立）：
      底本里有大量同形短句（「我知道了」「说的是他」），字符串 find 会
      命中前一处，导致切到别人的字；句号唯一定位，且天然保证单调。
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
    """切出底本第 para 段的第 [s_from, s_to) 句。返回 (正文, 起句原文)。"""
    sents = SENTENCES[para]
    if not (0 <= s_from < s_to <= len(sents)):
        raise ValueError(f'第 {para} 段句号 [{s_from}, {s_to}) 越界（共 {len(sents)} 句）')
    raw = ''.join(sents[s_from:s_to])
    lead = sents[s_from]
    if not raw.startswith(lead):
        raise ValueError(f'第 {para} 段第 {s_from} 句定位失败：{lead[:20]}')
    return raw, lead


def to_display(text: str) -> str:
    """底本弯引号 → 「」『』，只换标点不动字（第 16-20 回同一读法）。"""
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
    ('c21-menkou', '怡红院 · 门口拉扯', 'yihong'),
    ('c21-shuxi', '黛玉房 · 梳洗画眉', 'night'),
    ('c21-jiaochun', '怡红院 · 宝钗问话', 'yihong'),
    ('c21-jiaochun2', '怡红院 · 娇嗔赌气', 'yihong'),
    ('c21-zhuangzi', '怡红院 · 焚花散麝', 'yihong'),
    ('c21-zhuangzi2', '怡红院 · 掷笔就寝', 'yihong'),
    ('c21-xushi', '怡红院 · 摔断玉簪', 'yihong'),
    ('c21-daiyu', '黛玉房 · 无端弄笔', 'dinner'),
    ('c21-chudu', '王夫人院 · 大姐出痘', 'wang'),
    ('c21-qingsi', '贾琏院 · 抖出青丝', 'jialian_home'),
    ('c21-fengjie', '贾琏院 · 凤姐搜检', 'jialian_home'),
    ('c21-chuangwai', '贾琏院 · 隔窗说话', 'jialian_home'),
]

# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题, 地点, 底本段号, 起始句号, 结束句号, 动作)
#
# 用句号而不是字符串标记：底本句子里有大量同形短句，字符串检索会命中
# 前一处，切到别人的字；句号唯一定位，且天然保证节点顺序单调。
#
# 底本顺序（段号, 句号）必须全局单调递增——check() 会逐对校验。
CUTS = [
    # ---------------- 段一：怡红院 · 门口拉扯（底本段 1） ----------------
    ('c21-menkou', 'C21-001', 'narrator', '史湘云跑了出来，怕林黛玉赶上', '怡红院 · 院门', 1, 0, 2,
     ['S:shi_xiangyun:gate', 'S:baoyu:gate_step']),
    ('c21-menkou', 'C21-002', 'baoyu', '仔细绊跌了！那里就赶上了？', '怡红院 · 院门', 1, 0, 2,
     ['E:baoyu:greet:1.2']),
    ('c21-menkou', 'C21-003', 'narrator', '林黛玉赶到门前，被宝玉叉手在门框上拦住', '怡红院 · 院门', 1, 2, 3,
     ['S:daiyu:gate', 'M:baoyu:gate_step>gate']),
    ('c21-menkou', 'C21-004', 'baoyu', '饶他这一遭罢', '怡红院 · 院门', 1, 2, 3,
     ['E:baoyu:greet:1.2']),
    ('c21-menkou', 'C21-005', 'daiyu', '我若饶过云儿，再不活著！', '怡红院 · 院门', 1, 3, 4,
     ['E:daiyu:greet:1.4']),
    ('c21-menkou', 'C21-006', 'narrator', '湘云见宝玉拦住门，料黛玉不能出来', '怡红院 · 院门', 1, 4, 5,
     ['E:shi_xiangyun:greet:1.2']),
    ('c21-menkou', 'C21-007', 'shi_xiangyun', '好姐姐，饶我这一遭罢', '怡红院 · 院门', 1, 4, 5,
     ['E:shi_xiangyun:greet:1.4']),
    ('c21-menkou', 'C21-008', 'narrator', '恰值宝钗来在湘云身后', '怡红院 · 院门', 1, 5, 6,
     ['S:baochai:yard']),
    ('c21-menkou', 'C21-009', 'baochai', '我劝你两个看宝兄弟分上，都丢开手罢', '怡红院 · 院门', 1, 5, 6,
     ['E:baochai:greet:1.4']),
    ('c21-menkou', 'C21-010', 'daiyu', '我不依。你们是一气的，都戏弄我不成！', '怡红院 · 院门', 1, 6, 8,
     ['E:daiyu:greet:1.4']),
    ('c21-menkou', 'C21-011', 'baoyu', '谁敢戏弄你！你不打趣他，他焉敢说你', '怡红院 · 院门', 1, 8, 10,
     ['E:baoyu:greet:1.4']),
    ('c21-menkou', 'C21-012', 'narrator', '四人正难分解，有人来请吃饭', '怡红院 · 院门', 1, 10, 11,
     ['H:shi_xiangyun', 'H:daiyu']),
    ('c21-menkou', 'C21-013', 'narrator', '湘云仍往黛玉房中安歇', '怡红院 · 院门', 1, 11, 13,
     ['E:baochai:rest:1.2']),

    # ---------------- 段二：黛玉房 · 梳洗画眉（底本段 2-3） ----------------
    # 底本：「次日天明时，便披衣靸鞋往黛玉房中来」「湘云仍往黛玉房中安歇」
    ('c21-shuxi', 'C21-014', 'narrator', '次日天明时，便披衣靸鞋往黛玉房中来', '黛玉房 · 外间', 2, 1, 2,
     ['S:baoyu:outer_door', 'S:daiyu:daiyu_bed', 'S:shi_xiangyun:bedside']),
    ('c21-shuxi', 'C21-015', 'narrator', '林黛玉裹著杏子红绫被，安稳合目而睡', '黛玉房 · 外间', 2, 2, 3,
     ['E:daiyu:rest:1.4']),
    ('c21-shuxi', 'C21-016', 'narrator', '湘云一把青丝拖于枕畔，被只齐胸', '黛玉房 · 外间', 2, 3, 4,
     ['E:shi_xiangyun:rest:1.4']),
    ('c21-shuxi', 'C21-017', 'baoyu', '睡觉还是不老实！回来风吹了，又嚷肩窝疼了', '黛玉房 · 外间', 2, 4, 6,
     ['E:baoyu:greet:1.2']),
    ('c21-shuxi', 'C21-018', 'narrator', '林黛玉早已醒了，猜著定是宝玉', '黛玉房 · 外间', 2, 7, 8,
     ['M:baoyu:outer_door>daiyu_bed']),
    ('c21-shuxi', 'C21-019', 'daiyu', '这早晚就跑过来作什么？', '黛玉房 · 外间', 2, 8, 9,
     ['E:daiyu:greet:1.2']),
    ('c21-shuxi', 'C21-020', 'baoyu', '这天还早呢！你起来瞧瞧', '黛玉房 · 外间', 2, 9, 11,
     ['E:baoyu:greet:1.2']),
    ('c21-shuxi', 'C21-021', 'daiyu', '你先出去，让我们起来', '黛玉房 · 外间', 2, 11, 12,
     ['E:daiyu:greet:1.2']),
    ('c21-shuxi', 'C21-022', 'narrator', '宝玉复又进来，坐在镜台旁边', '黛玉房 · 梳妆台前', 3, 1, 2,
     ['M:baoyu:outer_door>letter_place', 'S:zijun:xueyan_place', 'S:xueyan:xueyan_place']),
    ('c21-shuxi', 'C21-023', 'narrator', '湘云洗了面，翠缕便拿残水要泼', '黛玉房 · 梳妆台前', 3, 2, 4,
     ['S:cui_lv:yingge_place', 'E:cui_lv:greet:1.2']),
    ('c21-shuxi', 'C21-024', 'baoyu', '站著，我趁势洗了就完了，省得又过去费事', '黛玉房 · 梳妆台前', 3, 2, 4,
     ['E:baoyu:greet:1.2']),
    ('c21-shuxi', 'C21-025', 'narrator', '紫鹃递过香皂去', '黛玉房 · 梳妆台前', 3, 4, 6,
     ['E:zijun:greet:1.2']),
    ('c21-shuxi', 'C21-026', 'cui_lv', '还是这个毛病儿，多早晚才改', '黛玉房 · 梳妆台前', 3, 6, 7,
     ['E:cui_lv:greet:1.4']),
    ('c21-shuxi', 'C21-027', 'narrator', '见湘云已梳完了头', '黛玉房 · 梳妆台前', 3, 7, 8,
     ['E:shi_xiangyun:rest:1.2']),
    ('c21-shuxi', 'C21-028', 'baoyu', '好妹妹，替我梳上头罢', '黛玉房 · 梳妆台前', 3, 7, 8,
     ['M:baoyu:letter_place>yingge_place', 'E:baoyu:greet:1.4']),
    ('c21-shuxi', 'C21-029', 'shi_xiangyun', '这可不能了', '黛玉房 · 梳妆台前', 3, 8, 9,
     ['E:shi_xiangyun:greet:1.2']),
    ('c21-shuxi', 'C21-030', 'narrator', '湘云只得扶过他的头来，一一梳篦', '黛玉房 · 梳妆台前', 3, 13, 14,
     ['E:shi_xiangyun:greet:1.2']),
    ('c21-shuxi', 'C21-031', 'narrator', '自发顶至辫梢，一路四颗珍珠', '黛玉房 · 梳妆台前', 3, 15, 16,
     ['E:baoyu:rest:1.2']),
    ('c21-shuxi', 'C21-032', 'shi_xiangyun', '这珠子只三颗了，这一颗不是的', '黛玉房 · 梳妆台前', 3, 16, 18,
     ['E:shi_xiangyun:greet:1.4']),
    ('c21-shuxi', 'C21-033', 'shi_xiangyun', '必定是外头去掉下来，倒便宜他', '黛玉房 · 梳妆台前', 3, 19, 20,
     ['E:shi_xiangyun:greet:1.4']),
    ('c21-shuxi', 'C21-034', 'daiyu', '也不知是真丢了，也不知是给了人镶什么戴去了', '黛玉房 · 梳妆台前', 3, 20, 21,
     ['E:daiyu:greet:1.4']),
    ('c21-shuxi', 'C21-035', 'narrator', '顺手拈了胭脂，意欲要往口边送', '黛玉房 · 梳妆台前', 3, 21, 22,
     ['E:baoyu:rest:1.2']),
    ('c21-shuxi', 'C21-036', 'narrator', '湘云果在身后看见', '黛玉房 · 梳妆台前', 3, 22, 24,
     ['M:shi_xiangyun:yingge_place>letter_place', 'E:shi_xiangyun:greet:1.4']),

    # ---------------- 段三：怡红院 · 宝钗问话（底本段 4） ----------------
    ('c21-jiaochun', 'C21-037', 'narrator', '袭人进来，看见这般光景，只得回来自己梳洗', '怡红院 · 外间', 4, 0, 1,
     ['S:xiren:xiren_kang', 'E:xiren:greet:1.2']),
    ('c21-jiaochun', 'C21-038', 'narrator', '忽见宝钗走来，因问道', '怡红院 · 外间', 4, 1, 2,
     ['S:baochai:outer_room']),
    ('c21-jiaochun', 'C21-039', 'baochai', '宝兄弟那去了？', '怡红院 · 外间', 4, 1, 2,
     ['E:baochai:greet:1.2']),
    ('c21-jiaochun', 'C21-040', 'xiren', '宝兄弟那里还有在家的工夫！', '怡红院 · 外间', 4, 2, 3,
     ['E:xiren:greet:1.4']),
    ('c21-jiaochun', 'C21-041', 'xiren', '姊妹们和气，也有个分寸礼节', '怡红院 · 外间', 4, 4, 6,
     ['E:xiren:greet:1.4']),
    ('c21-jiaochun', 'C21-042', 'narrator', '宝钗听了，心中暗忖道', '怡红院 · 外间', 4, 6, 7,
     ['E:baochai:rest:1.4']),
    ('c21-jiaochun', 'C21-043', 'narrator', '宝钗便在炕上坐了，闲言中套问他年纪家乡', '怡红院 · 炕上', 4, 7, 8,
     ['M:baochai:outer_room>xiren_kang', 'E:baochai:rest:1.2']),

    # ---------------- 段四：怡红院 · 娇嗔赌气（底本段 5） ----------------
    ('c21-jiaochun2', 'C21-044', 'narrator', '一时宝玉来了，宝钗方出去', '怡红院 · 外间', 5, 0, 1,
     ['S:baoyu:baoyu_outer', 'H:baochai']),
    ('c21-jiaochun2', 'C21-045', 'baoyu', '怎么宝姐姐和你说的这么热闹，见我进来就跑了', '怡红院 · 外间', 5, 1, 2,
     ['E:baoyu:greet:1.2']),
    ('c21-jiaochun2', 'C21-046', 'narrator', '见他脸上气色非往日可比', '怡红院 · 外间', 5, 4, 5,
     ['E:xiren:rest:1.4']),
    ('c21-jiaochun2', 'C21-047', 'baoyu', '怎么动了真气？', '怡红院 · 外间', 5, 4, 5,
     ['E:baoyu:greet:1.2']),
    ('c21-jiaochun2', 'C21-048', 'xiren', '我那里敢动气！只是从今以后别再进这屋子了', '怡红院 · 外间', 5, 5, 9,
     ['E:xiren:greet:1.4']),
    ('c21-jiaochun2', 'C21-049', 'narrator', '一面说，一面便在炕上合眼倒下', '怡红院 · 炕上', 5, 9, 10,
     ['M:xiren:xiren_kang', 'E:xiren:rest:1.4']),
    ('c21-jiaochun2', 'C21-050', 'narrator', '宝玉见了这般景况，禁不住赶来劝慰', '怡红院 · 炕上', 5, 10, 12,
     ['E:baoyu:rest:1.4']),
    ('c21-jiaochun2', 'C21-051', 'she_yue', '我知道么？问你自己便明白了', '怡红院 · 外间', 5, 12, 15,
     ['S:she_yue:outer_room', 'E:she_yue:greet:1.2']),
    ('c21-jiaochun2', 'C21-052', 'narrator', '便起身叹道：不理我罢，我也睡去', '怡红院 · 里间', 5, 15, 17,
     ['M:baoyu:baoyu_outer>baoyu_kang', 'E:baoyu:rest:1.2']),
    ('c21-jiaochun2', 'C21-053', 'narrator', '袭人听他半日无动静，拿一领斗蓬来', '怡红院 · 炕上', 5, 17, 18,
     ['E:xiren:rest:1.2']),
    ('c21-jiaochun2', 'C21-054', 'xiren', '你也不用生气，从此后我只当哑子', '怡红院 · 炕上', 5, 18, 19,
     ['E:xiren:greet:1.4']),
    ('c21-jiaochun2', 'C21-055', 'baoyu', '我又怎么了？你又劝我', '怡红院 · 里间', 5, 19, 24,
     ['E:baoyu:greet:1.4']),
    ('c21-jiaochun2', 'C21-056', 'xiren', '你心里还不明白，还等我说呢！', '怡红院 · 炕上', 5, 24, 25,
     ['E:xiren:greet:1.4']),
    ('c21-jiaochun2', 'C21-057', 'narrator', '贾母遣人来叫他吃饭，胡乱吃了半碗，仍回自己房中', '怡红院 · 外间', 5, 25, 26,
     ['E:baoyu:rest:1.2']),
    ('c21-jiaochun2', 'C21-058', 'narrator', '袭人睡在外头炕上，麝月在旁边抹骨牌', '怡红院 · 外间', 5, 26, 27,
     ['M:baoyu:baoyu_kang>baoyu_outer', 'E:she_yue:rest:1.2']),
    ('c21-jiaochun2', 'C21-059', 'narrator', '宝玉揭起软帘自往里间来', '怡红院 · 软帘', 5, 27, 28,
     ['M:baoyu:baoyu_outer>curtain', 'E:baoyu:rest:1.2']),
    ('c21-jiaochun2', 'C21-060', 'narrator', '宝玉便推他出去，说：不敢惊动你们', '怡红院 · 里间', 5, 29, 31,
     ['M:she_yue:outer_room>curtain', 'E:baoyu:greet:1.2']),
    ('c21-jiaochun2', 'C21-061', 'narrator', '抬头只见两个小丫头在地下站著', '怡红院 · 里间', 5, 31, 32,
     ['S:si_er:inner_room', 'E:si_er:greet:1.2']),
    ('c21-jiaochun2', 'C21-062', 'baoyu', '你叫什么名字？', '怡红院 · 里间', 5, 32, 33,
     ['E:baoyu:greet:1.2']),
    ('c21-jiaochun2', 'C21-063', 'si_er', '叫蕙香', '怡红院 · 里间', 5, 33, 34,
     ['E:si_er:greet:1.4']),
    ('c21-jiaochun2', 'C21-064', 'narrator', '我原叫芸香的，是花大姐姐改了蕙香', '怡红院 · 里间', 5, 35, 36,
     ['E:si_er:rest:1.2']),
    ('c21-jiaochun2', 'C21-065', 'baoyu', '正经该叫『晦气』罢了，什么蕙香呢', '怡红院 · 里间', 5, 36, 37,
     ['E:baoyu:greet:1.4']),
    ('c21-jiaochun2', 'C21-066', 'narrator', '明儿就叫『四儿』', '怡红院 · 里间', 5, 41, 43,
     ['E:baoyu:greet:1.4']),
    ('c21-jiaochun2', 'C21-067', 'narrator', '袭人和麝月在外间听了抿嘴而笑', '怡红院 · 外间', 5, 44, 45,
     ['E:xiren:rest:1.2', 'E:she_yue:rest:1.2']),

    # ---------------- 段五：怡红院 · 焚花散麝（底本段 6-10） ----------------
    ('c21-zhuangzi', 'C21-068', 'narrator', '这一日，宝玉也不大出房，自己闷闷的', '怡红院 · 里间', 6, 0, 1,
     ['M:baoyu:inner_room>baoyu_kang', 'E:baoyu:rest:1.4']),
    ('c21-zhuangzi', 'C21-069', 'narrator', '他变尽方法笼络宝玉', '怡红院 · 里间', 7, 0, 1,
     ['E:si_er:greet:1.2']),
    ('c21-zhuangzi', 'C21-070', 'narrator', '今日却冷清清的一人对灯，好没兴趣', '怡红院 · 书案前', 7, 1, 2,
     ['M:si_er:inner_room>desk_place', 'E:baoyu:rest:1.4']),
    ('c21-zhuangzi', 'C21-071', 'narrator', '说不得横心只当他们死了', '怡红院 · 书案前', 7, 3, 4,
     ['E:baoyu:rest:1.2']),
    ('c21-zhuangzi', 'C21-072', 'narrator', '因命四儿剪灯烹茶，自己看了一回《南华经》', '怡红院 · 书案前', 7, 5, 7,
     ['E:si_er:greet:1.2']),
    ('c21-zhuangzi', 'C21-073', 'narrator', '看至此，意趣洋洋，趁著酒兴，不禁提笔续曰', '怡红院 · 书案前', 9, 0, 1,
     ['E:baoyu:greet:1.2']),
    ('c21-zhuangzi', 'C21-074', 'narrator', '焚花散麝，而闺阁始人含其劝矣', '怡红院 · 书案前', 10, 0, 1,
     ['E:baoyu:rest:1.4']),
    ('c21-zhuangzi', 'C21-075', 'narrator', '戕宝钗之仙姿，灰黛玉之灵窍', '怡红院 · 书案前', 10, 0, 1,
     ['E:baoyu:rest:1.2']),

    # ---------------- 段六：怡红院 · 掷笔就寝（底本段 11） ----------------
    ('c21-zhuangzi2', 'C21-076', 'narrator', '续毕，掷笔就寝', '怡红院 · 里间', 11, 0, 2,
     ['M:baoyu:desk_place>baoyu_kang', 'E:baoyu:rest:1.4']),
    ('c21-zhuangzi2', 'C21-077', 'narrator', '翻身看时，只见袭人和衣睡在衾上', '怡红院 · 炕上', 11, 2, 3,
     ['S:xiren:xiren_kang', 'E:xiren:rest:1.4']),
    ('c21-zhuangzi2', 'C21-078', 'baoyu', '起来好生睡，看冻著了', '怡红院 · 炕上', 11, 3, 4,
     ['E:baoyu:greet:1.2']),
    ('c21-zhuangzi2', 'C21-079', 'narrator', '袭人将手推开，又自扣了', '怡红院 · 炕上', 11, 7, 8,
     ['E:xiren:rest:1.2']),
    ('c21-zhuangzi2', 'C21-080', 'baoyu', '你到底怎么了？', '怡红院 · 炕上', 11, 8, 9,
     ['E:baoyu:greet:1.2']),
    ('c21-zhuangzi2', 'C21-081', 'xiren', '我也不怎么。你自过那边房里去梳洗', '怡红院 · 炕上', 11, 9, 11,
     ['E:xiren:greet:1.4']),
    ('c21-zhuangzi2', 'C21-082', 'baoyu', '我过那里去？', '怡红院 · 炕上', 11, 11, 12,
     ['E:baoyu:greet:1.2']),
    ('c21-zhuangzi2', 'C21-083', 'xiren', '从今咱们两个丢开手，省得鸡声鹅斗', '怡红院 · 炕上', 11, 12, 15,
     ['E:xiren:greet:1.4']),
    ('c21-zhuangzi2', 'C21-084', 'xiren', '这边又有个什么『四儿』『五儿』伏侍', '怡红院 · 炕上', 11, 15, 17,
     ['E:xiren:greet:1.4']),

    # ---------------- 段七：怡红院 · 摔断玉簪（底本段 11 续） ----------------
    ('c21-xushi', 'C21-085', 'baoyu', '你今儿还记著呢', '怡红院 · 炕上', 11, 17, 18,
     ['M:baoyu:baoyu_kang>xiren_kang', 'E:baoyu:greet:1.4']),
    ('c21-xushi', 'C21-086', 'xiren', '一百年还记著呢', '怡红院 · 炕上', 11, 18, 20,
     ['E:xiren:greet:1.4']),
    ('c21-xushi', 'C21-087', 'narrator', '便向枕边拿起一根玉簪来，一跌两段', '怡红院 · 炕上', 11, 20, 21,
     ['E:baoyu:greet:1.4']),
    ('c21-xushi', 'C21-088', 'xiren', '大清早起，这是何苦来', '怡红院 · 炕上', 11, 21, 23,
     ['E:xiren:greet:1.4']),
    ('c21-xushi', 'C21-089', 'baoyu', '你那里知道我心里急', '怡红院 · 炕上', 11, 23, 24,
     ['E:baoyu:greet:1.4']),
    ('c21-xushi', 'C21-090', 'xiren', '你也知道著急么！可知我心里怎么样', '怡红院 · 炕上', 11, 24, 26,
     ['E:xiren:greet:1.4']),
    ('c21-xushi', 'C21-091', 'narrator', '说著，二人方起来梳洗', '怡红院 · 里间', 11, 26, 28,
     ['E:baoyu:rest:1.2']),

    # ---------------- 段八：黛玉房 · 无端弄笔（底本段 12-14） ----------------
    ('c21-daiyu', 'C21-092', 'narrator', '宝玉往上房去后，谁知黛玉走来', '黛玉房 · 案上', 12, 0, 1,
     ['S:daiyu:daiyu_place', 'E:daiyu:greet:1.2']),
    ('c21-daiyu', 'C21-093', 'narrator', '翻出昨儿的《庄子》来，看至所续之处', '黛玉房 · 案上', 12, 1, 2,
     ['E:daiyu:rest:1.2']),
    ('c21-daiyu', 'C21-094', 'narrator', '无端弄笔是何人？作践南华《庄子因》', '黛玉房 · 案上', 13, 0, 2,
     ['E:daiyu:greet:1.4']),
    ('c21-daiyu', 'C21-095', 'narrator', '不悔自己无见识，却将丑语怪他人', '黛玉房 · 案上', 13, 2, 3,
     ['E:daiyu:greet:1.4']),
    ('c21-daiyu', 'C21-096', 'narrator', '写毕，也往上房来见贾母，后往王夫人处来', '黛玉房 · 案上', 14, 0, 1,
     ['M:daiyu:daiyu_place>back_door', 'E:daiyu:rest:1.2']),

    # ---------------- 段九：王夫人院 · 大姐出痘（底本段 15） ----------------
    ('c21-chudu', 'C21-097', 'narrator', '谁知凤姐之女大姐病了，正乱著请大夫来诊脉', '王夫人院 · 正房', 15, 0, 1,
     ['S:wang:wang_host', 'S:feng:guest_seat', 'E:feng:greet:1.4']),
    ('c21-chudu', 'C21-098', 'narrator', '大夫说：姐儿发热是见喜了，并非别病', '王夫人院 · 正房', 15, 1, 2,
     ['E:wang:rest:1.2']),
    ('c21-chudu', 'C21-099', 'narrator', '凤姐听了，登时忙将起来', '王夫人院 · 东廊', 15, 5, 6,
     ['M:feng:guest_seat>east_corridor', 'E:feng:greet:1.4']),
    ('c21-chudu', 'C21-100', 'narrator', '一面命平儿打点舖盖衣服与贾琏隔房', '王夫人院 · 东廊', 15, 5, 6,
     ['S:ping_er:east_corridor', 'E:ping_er:greet:1.2']),
    ('c21-chudu', 'C21-101', 'narrator', '贾琏只得搬出外书房来斋戒', '王夫人院 · 后巷', 15, 7, 8,
     ['S:jia_lian:back_lane', 'E:jia_lian:rest:1.4']),

    # ---------------- 段十：贾琏院 · 抖出青丝（底本段 18） ----------------
    ('c21-qingsi', 'C21-102', 'narrator', '平儿收拾贾琏在外的衣服舖盖', '贾琏院 · 正房', 18, 0, 1,
     ['S:ping_er:room', 'E:ping_er:rest:1.2']),
    ('c21-qingsi', 'C21-103', 'narrator', '不承望枕套中抖出一绺青丝来', '贾琏院 · 正房', 18, 0, 1,
     ['E:ping_er:greet:1.4']),
    ('c21-qingsi', 'C21-104', 'narrator', '平儿会意，忙拽在袖内', '贾琏院 · 正房', 18, 1, 2,
     ['E:ping_er:rest:1.4']),
    ('c21-qingsi', 'C21-105', 'ping_er', '这是什么？', '贾琏院 · 正房', 18, 1, 2,
     ['M:ping_er:room>jia_lian_bed', 'E:ping_er:greet:1.4']),
    ('c21-qingsi', 'C21-106', 'narrator', '贾琏看见著了忙，抢上来要夺', '贾琏院 · 炕上', 18, 2, 3,
     ['S:jia_lian:bed', 'E:jia_lian:greet:1.4']),
    ('c21-qingsi', 'C21-107', 'jia_lian', '小蹄子，你不趁早拿出来，我把你膀子橛折了', '贾琏院 · 炕上', 18, 3, 4,
     ['E:jia_lian:greet:1.4']),
    ('c21-qingsi', 'C21-108', 'ping_er', '我好意瞒著他来问，你倒赌狠', '贾琏院 · 炕上', 18, 4, 7,
     ['E:ping_er:greet:1.4']),
    ('c21-qingsi', 'C21-109', 'narrator', '贾琏听说，忙陪笑央求道', '贾琏院 · 炕上', 18, 7, 8,
     ['E:jia_lian:rest:1.4']),

    # ---------------- 段十一：贾琏院 · 凤姐搜检（底本段 19） ----------------
    ('c21-fengjie', 'C21-110', 'narrator', '只听凤姐声音进来，贾琏听见松了手', '贾琏院 · 正房', 19, 0, 2,
     ['S:feng:room_door', 'E:feng:greet:1.4']),
    ('c21-fengjie', 'C21-111', 'feng', '拿出去的东西都收进来了么？', '贾琏院 · 正房', 19, 2, 3,
     ['E:feng:greet:1.2']),
    ('c21-fengjie', 'C21-112', 'ping_er', '收进来了', '贾琏院 · 正房', 19, 3, 4,
     ['E:ping_er:greet:1.2']),
    ('c21-fengjie', 'C21-113', 'feng', '可少什么没有？', '贾琏院 · 正房', 19, 4, 5,
     ['E:feng:greet:1.2']),
    ('c21-fengjie', 'C21-114', 'ping_er', '我也怕丢下一两件，细细的查了查，也不少', '贾琏院 · 正房', 19, 5, 6,
     ['E:ping_er:greet:1.4']),
    ('c21-fengjie', 'C21-115', 'feng', '不少就好，只是别多出来罢？', '贾琏院 · 正房', 19, 6, 7,
     ['E:feng:greet:1.2']),
    ('c21-fengjie', 'C21-116', 'narrator', '平儿笑道：不丢万幸，谁还添出来呢', '贾琏院 · 正房', 19, 7, 8,
     ['E:ping_er:greet:1.4']),
    ('c21-fengjie', 'C21-117', 'feng', '或者有相厚的丢下的东西：戒指，汗巾，香袋儿', '贾琏院 · 正房', 19, 8, 9,
     ['E:feng:greet:1.4']),
    ('c21-fengjie', 'C21-118', 'narrator', '一席话，说的贾琏脸都黄了', '贾琏院 · 炕上', 19, 9, 11,
     ['E:jia_lian:rest:1.4']),
    ('c21-fengjie', 'C21-119', 'narrator', '平儿只装著看不见', '贾琏院 · 正房', 19, 11, 14,
     ['E:ping_er:greet:1.4']),
    ('c21-fengjie', 'C21-120', 'narrator', '凤姐笑道：傻丫头，那里就叫咱们翻著了', '贾琏院 · 正房', 19, 14, 15,
     ['E:feng:greet:1.4']),

    # ---------------- 段十二：贾琏院 · 隔窗说话（底本段 20-21） ----------------
    ('c21-chuangwai', 'C21-121', 'narrator', '平儿指著鼻子，晃著头笑道', '贾琏院 · 正房', 20, 0, 1,
     ['M:ping_er:jia_lian_bed>room', 'E:ping_er:greet:1.2']),
    ('c21-chuangwai', 'C21-122', 'narrator', '贾琏跑上来搂著，『心肝肠肉』乱叫乱谢', '贾琏院 · 正房', 20, 1, 2,
     ['E:jia_lian:greet:1.2']),
    ('c21-chuangwai', 'C21-123', 'ping_er', '这是我一生的把柄了', '贾琏院 · 正房', 20, 2, 4,
     ['E:ping_er:greet:1.4']),
    ('c21-chuangwai', 'C21-124', 'narrator', '一面说著，一面便塞于靴掖内', '贾琏院 · 正房', 20, 5, 7,
     ['E:jia_lian:rest:1.2']),
    ('c21-chuangwai', 'C21-125', 'ping_er', '没良心的东西，过了河就拆桥', '贾琏院 · 正房', 20, 7, 8,
     ['E:ping_er:greet:1.4']),
    ('c21-chuangwai', 'C21-126', 'narrator', '被平儿夺手跑了', '贾琏院 · 正房', 20, 8, 10,
     ['E:jia_lian:greet:1.4']),
    ('c21-chuangwai', 'C21-127', 'ping_er', '我浪我的，谁叫你动火了', '贾琏院 · 窗外', 20, 10, 12,
     ['M:ping_er:room>pinger_window', 'E:ping_er:greet:1.4']),
    ('c21-chuangwai', 'C21-128', 'narrator', '贾琏道：他把那醋罐打个稀烂', '贾琏院 · 窗外', 20, 12, 15,
     ['M:jia_lian:jia_lian_bed>window_place', 'E:jia_lian:greet:1.4']),
    ('c21-chuangwai', 'C21-129', 'ping_er', '他醋你使得，你醋他使不得', '贾琏院 · 窗外', 20, 15, 17,
     ['E:ping_er:greet:1.4']),
    ('c21-chuangwai', 'C21-130', 'jia_lian', '你两个一口贼气', '贾琏院 · 窗外', 20, 17, 20,
     ['E:jia_lian:greet:1.4']),
    ('c21-chuangwai', 'C21-131', 'narrator', '凤姐走进院来，因见平儿在窗外', '贾琏院 · 院中', 21, 0, 1,
     ['S:feng:yard', 'E:feng:greet:1.4']),
    ('c21-chuangwai', 'C21-132', 'feng', '怎么跑出一个来，隔著窗子，是什么意思？', '贾琏院 · 院中', 21, 0, 1,
     ['E:feng:greet:1.4']),
    ('c21-chuangwai', 'C21-133', 'jia_lian', '你可问他，倒象屋里有老虎吃他呢', '贾琏院 · 窗外', 21, 1, 2,
     ['E:jia_lian:greet:1.4']),
    ('c21-chuangwai', 'C21-134', 'ping_er', '屋里一个人没有，我在他跟前作什么？', '贾琏院 · 窗外', 21, 2, 3,
     ['E:ping_er:greet:1.4']),
    ('c21-chuangwai', 'C21-135', 'feng', '正是没人才好呢', '贾琏院 · 院中', 21, 3, 4,
     ['E:feng:greet:1.4']),
    ('c21-chuangwai', 'C21-136', 'narrator', '凤姐自掀帘子进来', '贾琏院 · 正房', 21, 7, 9,
     ['M:feng:yard>room_door', 'E:feng:rest:1.2']),
    ('c21-chuangwai', 'C21-137', 'narrator', '贾琏听了，已绝倒在炕上，拍手笑道', '贾琏院 · 炕上', 21, 10, 11,
     ['E:jia_lian:greet:1.4']),
    ('c21-chuangwai', 'C21-138', 'narrator', '贾琏道：我就来', '贾琏院 · 正房', 21, 15, 16,
     ['E:jia_lian:rest:1.2']),
    ('c21-chuangwai', 'C21-139', 'narrator', '不知商量何事，且听下回分解', '贾琏院 · 正房', 21, 16, 19,
     ['E:feng:greet:1.2']),
]

# ---------------------------------------------------------------- 设计推定
DESIGN_NOTES = [
    ('C21-D001', 'c21-menkou',
     '门口拉扯一场用新建的 yihong 图（大观园 · 怡红院）',
     '底本只写「湘云跑了出来」「黛玉赶到门前」，未给地名；'
     '第四十回可证湘云当时住在怡红院一带，且本回后半整场都在宝玉房中。',
     '画在怡红院院门：院门、花门、海棠、山石给出大观园的形制，'
     '西府海棠是第十七回写明的怡红院特征。'),
    ('C21-D002', 'c21-shuxi',
     '梳洗画眉一场用 night 图（贾母院 · 碧纱橱与外间），不当成怡红院',
     '底本段 2/3 明写「往黛玉房中来」「湘云仍往黛玉房中安歇」，'
     '梳洗、画眉、拂落胭脂都发生在黛玉房里。',
     'night 图有 daiyu_bed（黛玉的床）、yingge_place / xueyan_place（丫鬟伏侍处）'
     '与 letter_place（案上），可表现「坐在镜台旁边」与镜前梳洗。'
     '★ 第 20 回曾把「贾母院 · 碧纱橱」当怡红院借用，本回不可沿用。'),
    ('C21-D003', 'c21-jiaochun',
     '宝钗问话一场回到 yihong 的外间与炕',
     '底本段 4 明写「忽见宝钗走来」——宝钗走到宝玉房里来问袭人。',
     'yihong 的 outer_room（外间）与 xiren_kang（里间炕上）'
     '正合「宝钗便在炕上坐了」。'),
    ('C21-D004', 'c21-daiyu',
     '黛玉续书一场用 dinner 图（贾母院 · 后房与晚膳）的 daiyu_place 与 back_door',
     '底本段 12：黛玉在宝玉房里翻书，续了一绝后「也往上房来见贾母」。'
     '宝玉房里没有专图，dinner 的 daiyu_place 即黛玉在贾母院的一处。',
     '用 dinner 的 daiyu_place 表示案上翻书、back_door 表示往上房去。'),
    ('C21-D005', 'c21-chudu',
     '大姐出痘一场用 wang 图（王夫人院 · 东廊三间）',
     '底本段 15 明写「王夫人凤姐听了」「凤姐与平儿都随著王夫人日日供奉娘娘」，'
     '地点在王夫人处；凤姐院一跨与王夫人院相邻。',
     '用 wang 的 wang_host（王夫人）、guest_seat（凤姐）、east_corridor（忙乱处）'
     '与 back_lane（贾琏搬出）表现。'),
    ('C21-D006', 'c21-qingsi',
     '抖出青丝一场用新建的 jialian_home 图（荣国府 · 贾琏院）',
     '底本段 18：平儿收拾贾琏在外的衣服舖盖，抖出枕套中的青丝，'
     '「便走至这边房内来」与贾琏在屋里周旋。',
     'jialian_home 有 room（正房）、jia_lian_bed（炕上）、trunk_place（铺盖）'
     '与 pinger_window（窗外），正合这一场。'),
    ('C21-D007', 'c21-chuangwai',
     '隔窗说话一场留在 jialian_home 的窗外与院中',
     '底本段 20/21 明写「平儿在窗外笑道」「凤姐走进院来，因见平儿在窗外」，'
     '窗内窗外的位置关系是这一幕的关节。',
     '用 pinger_window / window_place（窗下说话位）与 yard（凤姐进院处）表现。'),
    ('C21-D008', 'c21-zhuangzi',
     '多浑虫与多姑娘儿只作叙述，不安排人物进入',
     '底本段 16 写贾琏在外书房与多姑娘儿相会，笔法直露，'
     '且这段地点（外书房）本回没有专门场景。',
     '按第 19 回「原文只提及、没有实际到访的地点不安排人物进入」的既有纪律，'
     '只保留叙述，不建新图、不做美术、不让任何人 show。'),
    ('C21-D009', 'c21-jiaochun2',
     '四儿以 si_er 立绘登场，蕙香是她的原名',
     '底本段 5：她原名芸香，被花袭人改叫蕙香，宝玉当日又改叫四儿。',
     'cast 里登记的是改名后的「四儿」；节点里保留「叫蕙香」这句原文，'
     '让读者看见改名的经过。'),
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
                'chapter': 21,
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
            'id': step['id'].replace('C21-', 'C21-E'),
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
        'chapter': 21,
        'source': {
            'edition': '维基文库《紅樓夢》第 021 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第021回&action=raw',
            'retrievedAt': '2026-11-11',
            'localText': 'docs/chapter21-source.txt',
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
        print('第21回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第21回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 21})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第21回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
