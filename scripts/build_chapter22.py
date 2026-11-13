#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 22 回的剧情、段落、证据数据。

第 22 回底本是维基文库原文全文（docs/chapter22-source.txt），
写法沿用第 18/19/20/21 回确立的**底本切片式生成**：不手写正文，
按**句号索引**切片，正文与 source.paragraphLead 都是切出来的。

用法：
    python3 scripts/build_chapter22.py            # 生成
    python3 scripts/build_chapter22.py --check    # 只校验已有文件

这一回的两条戏与几处地点（对照 docs/chapter22-production.md 的分场规划）：

  jialian_home 荣国府 · 贾琏院 —— 宝钗生日怎么料理，贾琏与凤姐商量
  dinner       贾母院 · 后房与晚膳 —— 贾母蠲资办酒戏、问宝钗爱听何戏
  night        贾母院 · 碧纱橱与外间 —— 宝玉寻黛玉、湘云更衣摔手
  c11_tianxiang 天香楼 · 戏台与看楼 —— 点戏、听《寄生草》、小旦小丑
  yihong       大观园 · 怡红院 —— 黛玉闭门、宝玉悟禅、偈语与《寄生草》
  entry        荣国府 · 垂花门 · 贾母院 —— 元春送灯谜、众人猜谜
  central      荣禧堂 · 五间大正房 —— 贾政悲谶、逐谜

**零新增地图**：本回七段全部复用第 16-21 回已经建好的图。
**仅新增 1 名角色**：贾兰（底本段 20、21 两次出场，有台词「他不肯来」；
  前 21 回只在叙述里被提到，从未现身，所以本回是新角色，要补美术）。
太监沿用第 16 回的做法，复用 messenger（传话来人）——他不属于 cast 里
任何一个原著人物，只代表「宫里来的那个传话人」，与第 16 回六宫都太监
夏守忠同一个处理方式。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter22-source.txt'
STORY = ROOT / 'design' / 'chapter22-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter22-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter22-evidence.json'

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
    """底本弯引号 → 「」『』，只换标点不动字（第 16-21 回同一读法）。"""
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
    ('c22-shengri', '贾琏院 · 生日怎么料理', 'jialian_home'),
    ('c22-yanqing', '贾母院 · 蠲资办酒戏', 'dinner'),
    ('c22-dianxi', '天香楼 · 点戏听曲', 'c11_tianxiang'),
    ('c22-gengyi', '怡红院 · 更衣与摔手', 'yihong'),
    ('c22-bimen', '黛玉房 · 闭门与问答', 'night'),
    ('c22-wuchan', '怡红院 · 偈语与烧偈', 'yihong'),
    ('c22-dengmi', '贾母院 · 元春灯谜', 'entry'),
    ('c22-beichen', '荣禧堂 · 贾政悲谶', 'central'),
]


# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题, 地点, 底本段号, 起始句号, 结束句号, 动作)
#
# 用句号而不是字符串标记：底本句子里有大量同形短句，字符串检索会命中
# 前一处，切到别人的字；句号唯一定位，且天然保证节点顺序单调。
#
# 底本顺序（段号, 句号）必须全局单调递增——check() 会逐对校验。
CUTS = [
    # ---------------- 段一：贾琏院 · 生日怎么料理（底本段 1） ----------------
    ('c22-shengri', 'C22-001', 'narrator', '贾琏听凤姐说有话商量，因止步问是何话', '贾琏院 · 院中', 1, 0, 1,
     ['S:jia_lian:yard', 'S:feng:room_door']),
    ('c22-shengri', 'C22-002', 'feng', '二十一是薛妹妹的生日，你到底怎么样呢？', '贾琏院 · 院中', 1, 1, 2,
     ['E:feng:greet:1.4']),
    ('c22-shengri', 'C22-003', 'jia_lian', '我知道怎么样！', '贾琏院 · 院中', 1, 2, 3,
     ['E:jia_lian:greet:1.2']),
    ('c22-shengri', 'C22-004', 'jia_lian', '你连多少大生日都料理过了，这会子倒没了主意？', '贾琏院 · 院中', 1, 3, 4,
     ['E:jia_lian:greet:1.4']),
    ('c22-shengri', 'C22-005', 'feng', '大生日料理，不过是有一定的则例在那里', '贾琏院 · 院中', 1, 4, 5,
     ['E:feng:greet:1.4']),
    ('c22-shengri', 'C22-006', 'feng', '如今他这生日，大又不是，小又不是，所以和你商量', '贾琏院 · 院中', 1, 5, 6,
     ['E:feng:greet:1.4']),
    ('c22-shengri', 'C22-007', 'jia_lian', '现有比例，那林妹妹就是例', '贾琏院 · 院中', 1, 7, 8,
     ['E:jia_lian:greet:1.2']),
    ('c22-shengri', 'C22-008', 'jia_lian', '往年怎么给林妹妹过的，如今也照依给薛妹妹过就是了', '贾琏院 · 院中', 1, 8, 9,
     ['E:jia_lian:greet:1.4']),
    ('c22-shengri', 'C22-009', 'feng', '我原也这么想定了', '贾琏院 · 院中', 1, 10, 11,
     ['E:feng:greet:1.2']),
    ('c22-shengri', 'C22-010', 'narrator', '老太太说要替他作生日', '贾琏院 · 院中', 1, 12, 13,
     ['E:feng:rest:1.4']),
    ('c22-shengri', 'C22-011', 'feng', '我想来若果真替他作，自然比往年与林妹妹的不同了', '贾琏院 · 院中', 1, 13, 14,
     ['E:feng:greet:1.4']),
    ('c22-shengri', 'C22-012', 'jia_lian', '既如此，比林妹妹的多增些', '贾琏院 · 院中', 1, 14, 15,
     ['E:jia_lian:greet:1.2']),
    ('c22-shengri', 'C22-013', 'narrator', '说著，一径去了，不在话下', '贾琏院 · 院中', 1, 19, 20,
     ['M:feng:room_door>yard', 'E:feng:rest:1.2']),

    # ---------------- 段二：贾母院 · 蠲资办酒戏（底本段 2-3） ----------------
    # 底本段 2 讲湘云留下作针线，段 3 讲贾母蠲资、凤姐凑趣、点戏前问话。
    ('c22-yanqing', 'C22-014', 'narrator', '史湘云住了两日，因要回去', '贾母院 · 后房', 2, 0, 1,
     ['S:shi_xiangyun:back_door', 'S:grandmother:grandmother_place']),
    ('c22-yanqing', 'C22-015', 'grandmother', '等过了你宝姐姐的生日，看了戏再回去', '贾母院 · 后房', 2, 1, 2,
     ['E:grandmother:greet:1.4']),
    ('c22-yanqing', 'C22-016', 'narrator', '又遣人回去，将旧日作的两色针线活计取来', '贾母院 · 后房', 2, 3, 4,
     ['E:shi_xiangyun:rest:1.2']),
    ('c22-yanqing', 'C22-017', 'narrator', '贾母蠲资二十两，唤了凤姐来，交与他置酒戏', '贾母院 · 后房', 3, 0, 1,
     ['H:shi_xiangyun', 'S:feng:feng_place']),
    ('c22-yanqing', 'C22-018', 'feng', '一个老祖宗给孩子们作生日，谁还敢争，又办什么酒戏', '贾母院 · 后房', 3, 1, 2,
     ['E:feng:greet:1.4']),
    ('c22-yanqing', 'C22-019', 'feng', '巴巴的找出这霉烂的二十两银子来作东道，这意思还叫我赔上', '贾母院 · 后房', 3, 3, 4,
     ['E:feng:greet:1.4']),
    ('c22-yanqing', 'C22-020', 'narrator', '说的满屋里都笑起来', '贾母院 · 后房', 3, 10, 11,
     ['E:grandmother:rest:1.2']),
    ('c22-yanqing', 'C22-021', 'grandmother', '你们听听这嘴！', '贾母院 · 后房', 3, 11, 12,
     ['E:grandmother:greet:1.2']),
    ('c22-yanqing', 'C22-022', 'grandmother', '我也算会说的，怎么说不过这猴儿', '贾母院 · 后房', 3, 12, 13,
     ['E:grandmother:greet:1.4']),
    ('c22-yanqing', 'C22-023', 'feng', '我婆婆也是一样的疼宝玉，我也没处去诉冤', '贾母院 · 后房', 3, 14, 15,
     ['E:feng:greet:1.4']),
    ('c22-yanqing', 'C22-024', 'narrator', '到晚间，贾母因问宝钗爱听何戏，爱吃何物', '贾母院 · 后房', 3, 16, 17,
     ['S:baochai:tea_place', 'E:grandmother:greet:1.4']),
    ('c22-yanqing', 'C22-025', 'narrator', '宝钗深知贾母喜热闹戏文，便总依贾母素喜者说了出来', '贾母院 · 后房', 3, 17, 18,
     ['E:baochai:rest:1.2']),
    ('c22-yanqing', 'C22-026', 'narrator', '至二十一日，就贾母内院中搭了家常小巧戏台', '贾母院 · 后房', 3, 20, 21,
     ['E:grandmother:rest:1.2']),
    ('c22-yanqing', 'C22-027', 'narrator', '就在贾母上房排了几席家宴酒席，并无一个外客', '贾母院 · 后房', 3, 21, 22,
     ['E:grandmother:rest:1.4']),
    ('c22-yanqing', 'C22-028', 'narrator', '这日早起，宝玉因不见林黛玉，便到他房中来寻', '贾母院 · 后房', 3, 22, 23,
     ['S:baoyu:back_door']),
    ('c22-yanqing', 'C22-029', 'baoyu', '起来吃饭去，就开戏了', '贾母院 · 后房', 3, 23, 24,
     ['E:baoyu:greet:1.2']),
    ('c22-yanqing', 'C22-030', 'daiyu', '你既这样说，你特叫一班戏来，拣我爱的唱给我看', '贾母院 · 后房', 3, 26, 28,
     ['S:daiyu:daiyu_place', 'E:daiyu:greet:1.4']),
    ('c22-yanqing', 'C22-031', 'baoyu', '这有什么难的', '贾母院 · 后房', 3, 28, 29,
     ['E:baoyu:greet:1.2']),
    ('c22-yanqing', 'C22-032', 'narrator', '一面说，一面拉起他来，携手出去', '贾母院 · 后房', 3, 30, 31,
     ['M:baoyu:back_door>daiyu_place', 'E:baoyu:rest:1.2']),

    # ---------------- 段三：天香楼 · 点戏听曲（底本段 4-6） ----------------
    ('c22-dianxi', 'C22-033', 'narrator', '吃了饭点戏时，贾母一定先叫宝钗点', '天香楼 · 看楼', 4, 0, 1,
     ['S:grandmother:box', 'S:baochai:stair']),
    ('c22-dianxi', 'C22-034', 'narrator', '宝钗推让一遍，只得点了一折《西游记》', '天香楼 · 看楼', 4, 1, 2,
     ['E:baochai:rest:1.2']),
    ('c22-dianxi', 'C22-035', 'narrator', '然后便命凤姐点', '天香楼 · 看楼', 4, 2, 3,
     ['S:feng:yard']),
    ('c22-dianxi', 'C22-036', 'feng', '凤姐亦知贾母喜热闹，更喜谑笑科诨，便点了一出《刘二当衣》', '天香楼 · 看楼', 4, 3, 4,
     ['E:feng:greet:1.4']),
    ('c22-dianxi', 'C22-037', 'narrator', '然后便命黛玉点', '天香楼 · 看楼', 4, 4, 5,
     ['S:daiyu:yard']),
    ('c22-dianxi', 'C22-038', 'grandmother', '今日原是我特带著你们取笑，咱们只管咱们的', '天香楼 · 看楼', 4, 6, 7,
     ['E:grandmother:greet:1.4']),
    ('c22-dianxi', 'C22-039', 'grandmother', '我巴巴的唱戏摆酒，为他们不成？', '天香楼 · 看楼', 4, 7, 8,
     ['E:grandmother:greet:1.4']),
    ('c22-dianxi', 'C22-040', 'narrator', '黛玉方点了一出', '天香楼 · 看楼', 4, 10, 11,
     ['E:daiyu:rest:1.2']),
    ('c22-dianxi', 'C22-041', 'narrator', '至上酒席时，贾母又命宝钗点', '天香楼 · 看楼', 4, 12, 13,
     ['E:grandmother:rest:1.2']),
    ('c22-dianxi', 'C22-042', 'narrator', '宝钗点了一出《鲁智深醉闹五台山》', '天香楼 · 看楼', 4, 13, 14,
     ['E:baochai:rest:1.2']),
    ('c22-dianxi', 'C22-043', 'baoyu', '只好点这些戏', '天香楼 · 看楼', 4, 14, 15,
     ['S:baoyu:box', 'E:baoyu:greet:1.2']),
    ('c22-dianxi', 'C22-044', 'baochai', '你白听了这几年的戏，那里知道这出戏的好处', '天香楼 · 看楼', 4, 15, 16,
     ['M:baochai:stair>box', 'E:baochai:greet:1.4']),
    ('c22-dianxi', 'C22-045', 'baochai', '是一套北《点绛唇》，只那词藻中有一支《寄生草》，填的极妙', '天香楼 · 看楼', 4, 19, 20,
     ['E:baochai:greet:1.4']),
    ('c22-dianxi', 'C22-046', 'baoyu', '好姐姐，念与我听听', '天香楼 · 看楼', 4, 20, 21,
     ['E:baoyu:greet:1.4']),
    ('c22-dianxi', 'C22-047', 'narrator', '宝钗便念道', '天香楼 · 看楼', 4, 21, 22,
     ['E:baochai:rest:1.2']),
    ('c22-dianxi', 'C22-048', 'narrator', '漫揾英雄泪，相离处士家', '天香楼 · 看楼', 5, 0, 1,
     ['E:baochai:rest:1.4']),
    ('c22-dianxi', 'C22-049', 'narrator', '赤条条来去无牵挂', '天香楼 · 看楼', 5, 3, 4,
     ['E:baochai:rest:1.4']),
    ('c22-dianxi', 'C22-050', 'baoyu', '宝玉听了，喜的拍膝画圈，称赏不已', '天香楼 · 看楼', 6, 0, 1,
     ['E:baoyu:greet:1.4']),
    ('c22-dianxi', 'C22-051', 'daiyu', '安静看戏罢，还没唱《山门》，你倒《妆疯》了', '天香楼 · 看楼', 6, 0, 1,
     ['E:daiyu:greet:1.4']),
    ('c22-dianxi', 'C22-052', 'narrator', '至晚散时，贾母深爱那作小旦的与一个作小丑的', '天香楼 · 看楼', 6, 3, 4,
     ['E:grandmother:rest:1.4']),
    ('c22-dianxi', 'C22-053', 'narrator', '因问年纪，那小旦才十一岁，小丑才九岁', '天香楼 · 看楼', 6, 4, 5,
     ['E:grandmother:rest:1.2']),
    ('c22-dianxi', 'C22-054', 'narrator', '贾母令人另拿些肉果与他两个，又另外赏钱两串', '天香楼 · 看楼', 6, 5, 6,
     ['E:grandmother:rest:1.2']),
    ('c22-dianxi', 'C22-055', 'feng', '这个孩子扮上活象一个人，你们再看不出来', '天香楼 · 看楼', 6, 6, 7,
     ['S:feng:gate', 'E:feng:greet:1.4']),
    ('c22-dianxi', 'C22-056', 'narrator', '宝钗心里也知道，便只一笑不肯说', '天香楼 · 看楼', 6, 7, 8,
     ['E:baochai:rest:1.2']),
    ('c22-dianxi', 'C22-057', 'shi_xiangyun', '倒象林妹妹的模样儿', '天香楼 · 看楼', 6, 9, 10,
     ['S:shi_xiangyun:stair', 'E:shi_xiangyun:greet:1.4']),
    ('c22-dianxi', 'C22-058', 'narrator', '宝玉听了，忙把湘云瞅了一眼，使个眼色', '天香楼 · 看楼', 6, 10, 11,
     ['E:baoyu:idle:1.2']),
    ('c22-dianxi', 'C22-059', 'narrator', '众人却都听了这话，留神细看，都笑起来了', '天香楼 · 看楼', 6, 11, 12,
     ['E:daiyu:rest:1.2']),
    ('c22-dianxi', 'C22-060', 'narrator', '一时散了', '天香楼 · 看楼', 6, 12, 13,
     ['H:grandmother', 'H:baochai', 'H:baoyu', 'H:daiyu', 'H:feng', 'H:shi_xiangyun']),

    # ---------------- 段四：怡红院 · 更衣与摔手（底本段 7） ----------------
    ('c22-gengyi', 'C22-061', 'narrator', '晚间，湘云更衣时，便命翠缕把衣包打开收拾', '怡红院 · 外间', 7, 0, 1,
     ['S:shi_xiangyun:outer_room', 'S:cui_lv:cui_lv_place']),
    ('c22-gengyi', 'C22-062', 'cui_lv', '忙什么，等去的日子再包不迟', '怡红院 · 外间', 7, 1, 2,
     ['E:cui_lv:greet:1.2']),
    ('c22-gengyi', 'C22-063', 'shi_xiangyun', '明儿一早就走', '怡红院 · 外间', 7, 2, 3,
     ['E:shi_xiangyun:greet:1.2']),
    ('c22-gengyi', 'C22-064', 'shi_xiangyun', '看人家的鼻子眼睛，什么意思！', '怡红院 · 外间', 7, 4, 5,
     ['E:shi_xiangyun:greet:1.4']),
    ('c22-gengyi', 'C22-065', 'narrator', '宝玉听了这话，忙赶近前拉他说道', '怡红院 · 外间', 7, 5, 6,
     ['S:baoyu:baoyu_outer', 'E:baoyu:greet:1.4']),
    ('c22-gengyi', 'C22-066', 'baoyu', '林妹妹是个多心的人', '怡红院 · 外间', 7, 6, 7,
     ['E:baoyu:greet:1.2']),
    ('c22-gengyi', 'C22-067', 'baoyu', '别人分明知道，不肯说出来，也皆因怕他恼', '怡红院 · 外间', 7, 7, 8,
     ['E:baoyu:greet:1.4']),
    ('c22-gengyi', 'C22-068', 'baoyu', '我是怕你得罪了他，所以才使眼色', '怡红院 · 外间', 7, 9, 10,
     ['E:baoyu:greet:1.4']),
    ('c22-gengyi', 'C22-069', 'shi_xiangyun', '你那花言巧语别哄我', '怡红院 · 外间', 7, 12, 13,
     ['E:shi_xiangyun:greet:1.2']),
    ('c22-gengyi', 'C22-070', 'shi_xiangyun', '他原是公侯的小姐，我原是贫民的丫头', '怡红院 · 外间', 7, 14, 15,
     ['E:shi_xiangyun:greet:1.4']),
    ('c22-gengyi', 'C22-071', 'narrator', '说著，一径至贾母里间，忿忿的躺著去了', '怡红院 · 外间', 7, 21, 22,
     ['M:shi_xiangyun:outer_room>inner_room', 'E:shi_xiangyun:anger:1.4']),

    # ---------------- 段五：黛玉房 · 闭门与问答（底本段 8-9） ----------------
    ('c22-bimen', 'C22-072', 'narrator', '宝玉没趣，只得又来寻黛玉', '黛玉房 · 外间', 8, 0, 1,
     ['S:baoyu:outer_door']),
    ('c22-bimen', 'C22-073', 'narrator', '刚到门槛前，黛玉便推出来，将门关上', '黛玉房 · 外间', 8, 1, 2,
     ['S:daiyu:daiyu_bed']),
    ('c22-bimen', 'C22-074', 'narrator', '在窗外只是吞声叫「好妹妹」，黛玉总不理他', '黛玉房 · 外间', 8, 2, 4,
     ['E:baoyu:rest:1.4']),
    ('c22-bimen', 'C22-075', 'narrator', '袭人早知端的，当此时断不能劝', '黛玉房 · 外间', 8, 5, 6,
     ['S:xiren:xiren_place', 'E:xiren:rest:1.2']),
    ('c22-bimen', 'C22-076', 'narrator', '黛玉只当他回房去了，便起来开门', '黛玉房 · 外间', 8, 7, 8,
     ['E:daiyu:rest:1.2']),
    ('c22-bimen', 'C22-077', 'narrator', '黛玉反不好意思，不好再关，只得抽身上床躺著', '黛玉房 · 外间', 8, 8, 9,
     ['E:daiyu:rest:1.4']),
    ('c22-bimen', 'C22-078', 'baoyu', '凡事都有个原故，说出来，人也不委曲', '黛玉房 · 外间', 8, 9, 10,
     ['M:baoyu:outer_door>bedside', 'E:baoyu:greet:1.4']),
    ('c22-bimen', 'C22-079', 'baoyu', '好好的就恼了，终是什么原故起的？', '黛玉房 · 外间', 8, 10, 11,
     ['E:baoyu:greet:1.4']),
    ('c22-bimen', 'C22-080', 'daiyu', '问的我倒好，我也不知为什么原故', '黛玉房 · 外间', 8, 11, 12,
     ['E:daiyu:greet:1.2']),
    ('c22-bimen', 'C22-081', 'daiyu', '我原是给你们取笑的——拿我比戏子取笑', '黛玉房 · 外间', 8, 12, 13,
     ['E:daiyu:greet:1.4']),
    ('c22-bimen', 'C22-082', 'baoyu', '我并没有比你，我并没笑，为什么恼我呢？', '黛玉房 · 外间', 8, 13, 14,
     ['E:baoyu:greet:1.4']),
    ('c22-bimen', 'C22-083', 'daiyu', '你还要比？你还要笑？', '黛玉房 · 外间', 8, 14, 16,
     ['E:daiyu:greet:1.4']),
    ('c22-bimen', 'C22-084', 'daiyu', '你不比不笑，比人比了笑了的还利害呢！', '黛玉房 · 外间', 8, 16, 17,
     ['E:daiyu:greet:1.4']),
    ('c22-bimen', 'C22-085', 'narrator', '宝玉听说，无可分辩，不则一声', '黛玉房 · 外间', 8, 17, 18,
     ['E:baoyu:rest:1.4']),
    ('c22-bimen', 'C22-086', 'daiyu', '再你为什么又和云儿使眼色？', '黛玉房 · 外间', 9, 1, 2,
     ['E:daiyu:greet:1.4']),
    ('c22-bimen', 'C22-087', 'daiyu', '他原是公侯的小姐，我原是贫民的丫头', '黛玉房 · 外间', 9, 4, 5,
     ['E:daiyu:greet:1.4']),
    ('c22-bimen', 'C22-088', 'daiyu', '我恼他，与你何干？', '黛玉房 · 外间', 9, 9, 10,
     ['E:daiyu:greet:1.4']),

    # ---------------- 段六：怡红院 · 偈语与烧偈（底本段 10-16） ----------------
    ('c22-wuchan', 'C22-089', 'narrator', '宝玉见说，细想自己原为他二人，怕生隙恼', '怡红院 · 外间', 10, 0, 2,
     ['S:baoyu:baoyu_outer', 'E:baoyu:rest:1.4']),
    ('c22-wuchan', 'C22-090', 'narrator', '正合著前日所看《南华经》上有「巧者劳而智者忧」', '怡红院 · 外间', 10, 2, 3,
     ['E:baoyu:rest:1.4']),
    ('c22-wuchan', 'C22-091', 'narrator', '想到其间也无庸分辩回答自己转身回房来', '怡红院 · 外间', 10, 5, 6,
     ['M:baoyu:baoyu_outer>desk_place', 'E:baoyu:rest:1.2']),
    ('c22-wuchan', 'C22-092', 'daiyu', '这一去，一辈子也别来，也别说话', '怡红院 · 外间', 10, 6, 7,
     ['S:daiyu:gate', 'E:daiyu:rest:1.4']),
    ('c22-wuchan', 'C22-093', 'narrator', '宝玉不理，回房躺在床上，只是瞪瞪的', '怡红院 · 里间', 11, 0, 1,
     ['H:daiyu', 'M:baoyu:desk_place>baoyu_kang', 'E:baoyu:rest:1.4']),
    ('c22-wuchan', 'C22-094', 'xiren', '今儿看了戏，又勾出几天戏来', '怡红院 · 里间', 11, 1, 2,
     ['S:xiren:xiren_kang', 'E:xiren:greet:1.4']),
    ('c22-wuchan', 'C22-095', 'xiren', '宝姑娘一定要还席的', '怡红院 · 里间', 11, 2, 3,
     ['E:xiren:greet:1.2']),
    ('c22-wuchan', 'C22-096', 'baoyu', '他还不还，管谁什么相干', '怡红院 · 里间', 11, 3, 4,
     ['E:baoyu:greet:1.4']),
    ('c22-wuchan', 'C22-097', 'xiren', '好好的大正月里，娘儿们姊妹们都喜喜欢欢的', '怡红院 · 里间', 11, 5, 6,
     ['E:xiren:greet:1.4']),
    ('c22-wuchan', 'C22-098', 'baoyu', '他们娘儿们姊妹们欢喜不欢喜，也与我无干', '怡红院 · 里间', 11, 6, 7,
     ['E:baoyu:greet:1.4']),
    ('c22-wuchan', 'C22-099', 'baoyu', '什么是「大家彼此」！', '怡红院 · 里间', 11, 8, 9,
     ['E:baoyu:greet:1.4']),
    ('c22-wuchan', 'C22-100', 'baoyu', '我有「赤条条来去无牵挂」', '怡红院 · 里间', 11, 9, 10,
     ['E:baoyu:rest:1.4']),
    ('c22-wuchan', 'C22-101', 'narrator', '谈及此句，不觉泪下', '怡红院 · 里间', 11, 10, 11,
     ['E:baoyu:rest:1.4']),
    ('c22-wuchan', 'C22-102', 'narrator', '宝玉细想这句趣味，不禁大哭起来，翻身起来至案', '怡红院 · 书案前', 11, 12, 13,
     ['M:baoyu:baoyu_kang>desk_place', 'E:baoyu:anger:1.4']),
    ('c22-wuchan', 'C22-103', 'narrator', '你证我证，心证意证', '怡红院 · 书案前', 12, 0, 1,
     ['E:baoyu:rest:1.4']),
    ('c22-wuchan', 'C22-104', 'narrator', '是无有证，斯可云证', '怡红院 · 书案前', 12, 1, 2,
     ['E:baoyu:rest:1.4']),
    ('c22-wuchan', 'C22-105', 'narrator', '无可云证，是立足境', '怡红院 · 书案前', 12, 2, 3,
     ['E:baoyu:rest:1.4']),
    ('c22-wuchan', 'C22-106', 'narrator', '又填一支《寄生草》，也写在偈后', '怡红院 · 书案前', 13, 0, 1,
     ['E:baoyu:rest:1.2']),
    ('c22-wuchan', 'C22-107', 'narrator', '自觉无挂碍，中心自得，便上床睡了', '怡红院 · 里间', 13, 1, 2,
     ['M:baoyu:desk_place>baoyu_kang', 'E:baoyu:rest:1.2']),
    ('c22-wuchan', 'C22-108', 'narrator', '谁想黛玉见宝玉此番果断而去，故以寻袭人为由', '怡红院 · 外间', 14, 0, 1,
     ['S:daiyu:outer_room']),
    ('c22-wuchan', 'C22-109', 'xiren', '已经睡了', '怡红院 · 外间', 14, 1, 2,
     ['E:xiren:greet:1.2']),
    ('c22-wuchan', 'C22-110', 'xiren', '姑娘请站住，有一个字帖儿，瞧瞧是什么话', '怡红院 · 外间', 14, 3, 4,
     ['E:xiren:greet:1.4']),
    ('c22-wuchan', 'C22-111', 'narrator', '便将方才那曲子与偈语悄悄拿来，递与黛玉看', '怡红院 · 外间', 14, 4, 5,
     ['E:daiyu:rest:1.2']),
    ('c22-wuchan', 'C22-112', 'daiyu', '作的是玩意儿，无甚关系', '怡红院 · 外间', 14, 5, 6,
     ['E:daiyu:greet:1.2']),
    ('c22-wuchan', 'C22-113', 'narrator', '次日又与宝钗看', '怡红院 · 外间', 14, 7, 8,
     ['E:baochai:rest:1.2']),
    ('c22-wuchan', 'C22-114', 'narrator', '无我原非你，从他不解伊', '怡红院 · 外间', 15, 0, 1,
     ['E:baochai:rest:1.4']),
    ('c22-wuchan', 'C22-115', 'narrator', '从前碌碌却因何，到如今回头试想真无趣！', '怡红院 · 外间', 15, 3, 4,
     ['E:baochai:rest:1.4']),
    ('c22-wuchan', 'C22-116', 'narrator', '看毕，又看那偈语，又笑道：这个人悟了', '怡红院 · 外间', 16, 0, 1,
     ['E:baochai:greet:1.4']),
    ('c22-wuchan', 'C22-117', 'baochai', '都是我的不是，都是我昨儿一支曲子惹出来的', '怡红院 · 外间', 16, 1, 2,
     ['E:baochai:greet:1.4']),
    ('c22-wuchan', 'C22-118', 'baochai', '明儿认真说起这些疯话来，存了这个意思', '怡红院 · 外间', 16, 3, 4,
     ['E:baochai:greet:1.4']),
    ('c22-wuchan', 'C22-119', 'narrator', '说着，便撕了个粉碎，递与丫头们说：快烧了罢', '怡红院 · 外间', 16, 4, 5,
     ['E:baochai:rest:1.2']),
    ('c22-wuchan', 'C22-120', 'daiyu', '不该撕，等我问他', '怡红院 · 外间', 16, 5, 6,
     ['E:daiyu:greet:1.2']),
    ('c22-wuchan', 'C22-121', 'narrator', '三人果然都往宝玉屋里来', '怡红院 · 外间', 16, 7, 8,
     ['E:shi_xiangyun:rest:1.2']),
    ('c22-wuchan', 'C22-122', 'daiyu', '宝玉，我问你：至贵者是「宝」，至坚者是「玉」', '怡红院 · 里间', 16, 8, 9,
     ['M:baoyu:baoyu_kang>inner_room', 'E:daiyu:greet:1.4']),
    ('c22-wuchan', 'C22-123', 'daiyu', '尔有何贵？尔有何坚？', '怡红院 · 里间', 16, 9, 11,
     ['E:daiyu:greet:1.4']),
    ('c22-wuchan', 'C22-124', 'narrator', '宝玉竟不能答', '怡红院 · 里间', 16, 11, 12,
     ['E:baoyu:idle:1.4']),
    ('c22-wuchan', 'C22-125', 'narrator', '三人拍手笑道：这样钝愚，还参禅呢', '怡红院 · 里间', 16, 12, 13,
     ['E:baochai:greet:1.2']),
    ('c22-wuchan', 'C22-126', 'daiyu', '你那偈末云「无可云证，是立足境」，固然好了，只是据我看，还未尽善', '怡红院 · 里间', 16, 13, 14,
     ['E:daiyu:greet:1.4']),
    ('c22-wuchan', 'C22-127', 'daiyu', '无立足境，是方干净', '怡红院 · 里间', 16, 15, 16,
     ['E:daiyu:greet:1.4']),
    ('c22-wuchan', 'C22-128', 'baochai', '实在这方悟彻', '怡红院 · 里间', 16, 16, 17,
     ['E:baochai:greet:1.4']),
    ('c22-wuchan', 'C22-129', 'baochai', '当日南宗六祖惠能，初寻师至韶州，闻五祖弘忍在黄梅', '怡红院 · 里间', 16, 17, 18,
     ['E:baochai:rest:1.4']),
    ('c22-wuchan', 'C22-130', 'narrator', '宝玉自己以为觉悟，不想忽被黛玉一问，便不能答', '怡红院 · 里间', 16, 28, 29,
     ['E:baoyu:rest:1.4']),
    ('c22-wuchan', 'C22-131', 'baoyu', '原来他们比我的知觉在先，尚未解悟，我如今何必自寻苦恼', '怡红院 · 里间', 16, 29, 30,
     ['E:baoyu:greet:1.4']),
    ('c22-wuchan', 'C22-132', 'baoyu', '谁又参禅，不过一时顽话罢了', '怡红院 · 里间', 16, 30, 31,
     ['E:baoyu:greet:1.2']),
    ('c22-wuchan', 'C22-133', 'narrator', '忽然人报，娘娘差人送出一个灯谜儿', '怡红院 · 里间', 16, 32, 33,
     ['E:baoyu:rest:1.2']),

    # ---------------- 段七：贾母院 · 元春灯谜（底本段 16-19） ----------------
    ('c22-dengmi', 'C22-134', 'narrator', '四人听说忙出去，至贾母上房', '贾母院 · 正房', 16, 33, 34,
     ['S:grandmother:grandmother_seat', 'S:baoyu:daiyu_greet', 'S:daiyu:daiyu_seat', 'S:baochai:grandmother_greet']),
    ('c22-dengmi', 'C22-135', 'narrator', '只见一个小太监，拿了一盏四角平头白纱灯', '贾母院 · 正房', 16, 34, 35,
     ['S:messenger:hall_door']),
    ('c22-dengmi', 'C22-136', 'messenger', '众小姐猜著了，不要说出来，每人只暗暗的写在纸上', '贾母院 · 正房', 16, 35, 36,
     ['E:messenger:greet:1.4']),
    ('c22-dengmi', 'C22-137', 'narrator', '宝钗等听了，是一首七言绝句，并无甚新奇', '贾母院 · 正房', 16, 36, 37,
     ['E:baochai:rest:1.4']),
    ('c22-dengmi', 'C22-138', 'narrator', '宝玉，黛玉，湘云，探春四个人也都解了', '贾母院 · 正房', 16, 37, 38,
     ['S:tanchun:tanchun_seat', 'S:shi_xiangyun:grandmother_greet']),
    ('c22-dengmi', 'C22-139', 'narrator', '然后各人拈一物作成一谜，恭楷写了，挂在灯上', '贾母院 · 正房', 16, 39, 40,
     ['E:baoyu:rest:1.2']),
    ('c22-dengmi', 'C22-140', 'narrator', '太监去了，至晚出来传谕：前娘娘所制，俱已猜著', '贾母院 · 正房', 17, 0, 1,
     ['H:messenger', 'E:grandmother:rest:1.2']),
    ('c22-dengmi', 'C22-141', 'narrator', '太监又将颁赐之物送与猜着之人，每人一个宫制诗筒', '贾母院 · 正房', 17, 4, 5,
     ['E:grandmother:rest:1.4']),
    ('c22-dengmi', 'C22-142', 'narrator', '独迎春，贾环二人未得', '贾母院 · 正房', 17, 4, 5,
     ['S:yingchun:yingchun_seat', 'S:jia_huan:wang_seat']),
    ('c22-dengmi', 'C22-143', 'narrator', '迎春自为玩笑小事，并不介意，贾环便觉得没趣', '贾母院 · 正房', 17, 5, 6,
     ['E:jia_huan:rest:1.4']),
    ('c22-dengmi', 'C22-144', 'messenger', '三爷说的这个不通，娘娘也没猜，叫我带回问三爷是个什么', '贾母院 · 正房', 17, 6, 7,
     ['S:messenger:hall_door', 'E:messenger:greet:1.4']),
    ('c22-dengmi', 'C22-145', 'narrator', '大哥有角只八个，二哥有角只两根', '贾母院 · 正房', 18, 0, 1,
     ['E:jia_huan:rest:1.2']),
    ('c22-dengmi', 'C22-146', 'narrator', '大哥只在床上坐，二哥爱在房上蹲', '贾母院 · 正房', 18, 1, 2,
     ['E:jia_huan:rest:1.4']),
    ('c22-dengmi', 'C22-147', 'narrator', '众人看了，大发一笑', '贾母院 · 正房', 19, 0, 1,
     ['E:grandmother:rest:1.4']),
    ('c22-dengmi', 'C22-148', 'jia_huan', '一个枕头，一个兽头', '贾母院 · 正房', 19, 1, 2,
     ['E:jia_huan:greet:1.4']),
    ('c22-dengmi', 'C22-149', 'narrator', '太监记了，领茶而去', '贾母院 · 正房', 19, 2, 3,
     ['H:messenger', 'E:grandmother:rest:1.2']),

    # ---------------- 段八：荣禧堂 · 贾政悲谶（底本段 20-39） ----------------
    ('c22-beichen', 'C22-150', 'narrator', '贾母命速作一架小巧精致围屏灯来，设于当屋', '荣禧堂 · 正房', 20, 0, 1,
     ['S:grandmother:rongxi_center', 'S:zheng:rongxi_steps']),
    ('c22-beichen', 'C22-151', 'narrator', '贾政朝罢，见贾母高兴，况在节间，晚上也来承欢取乐', '荣禧堂 · 正房', 20, 1, 2,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-152', 'narrator', '设了酒果，备了玩物，上房悬了彩灯，请贾母赏灯取乐', '荣禧堂 · 正房', 20, 2, 3,
     ['E:zheng:rest:1.2']),
    ('c22-beichen', 'C22-153', 'narrator', '上面贾母，贾政，宝玉一席，下面王夫人、宝钗、黛玉、湘云又一席', '荣禧堂 · 正房', 20, 3, 4,
     ['S:baoyu:rongxi_door', 'S:wang:west_room', 'S:baochai:east_court', 'S:daiyu:east_court',
      'S:shi_xiangyun:east_court', 'S:yingchun:east_court', 'S:tanchun:east_court', 'S:xichun:east_court']),
    ('c22-beichen', 'C22-154', 'narrator', '李宫裁、王熙凤二人在里间又一席', '荣禧堂 · 正房', 20, 5, 6,
     ['S:liwan:east_court', 'S:feng:east_door']),
    ('c22-beichen', 'C22-155', 'narrator', '贾政因不见贾兰，便问：怎么不见兰哥？', '荣禧堂 · 正房', 20, 6, 7,
     ['E:zheng:greet:1.4']),
    ('c22-beichen', 'C22-156', 'liwan', '他说方才老爷并没去叫他，他不肯来', '荣禧堂 · 正房', 20, 7, 8,
     ['E:liwan:greet:1.4']),
    ('c22-beichen', 'C22-157', 'narrator', '贾政忙遣贾环与两个婆娘将贾兰唤来', '荣禧堂 · 正房', 20, 10, 11,
     ['S:jia_huan:rongxi_steps', 'S:jia_lan:rongxi_center']),
    ('c22-beichen', 'C22-158', 'narrator', '贾母命他在身旁坐了，抓果品与他吃', '荣禧堂 · 正房', 20, 11, 12,
     ['E:jia_lan:rest:1.4']),
    ('c22-beichen', 'C22-159', 'narrator', '往常间只有宝玉长谈阔论，今日贾政在这里，便惟有唯唯而已', '荣禧堂 · 正房', 21, 0, 1,
     ['E:baoyu:rest:1.4']),
    ('c22-beichen', 'C22-160', 'narrator', '故此一席虽是家常取乐，反见拘束不乐', '荣禧堂 · 正房', 21, 4, 5,
     ['E:grandmother:rest:1.2']),
    ('c22-beichen', 'C22-161', 'narrator', '酒过三巡，便撵贾政去歇息', '荣禧堂 · 正房', 21, 5, 6,
     ['E:grandmother:greet:1.4']),
    ('c22-beichen', 'C22-162', 'zheng', '今日原听见老太太这里大设春灯雅谜，故也备了彩礼酒席', '荣禧堂 · 正房', 21, 7, 8,
     ['E:zheng:greet:1.4']),
    ('c22-beichen', 'C22-163', 'zheng', '何疼孙子孙女之心，便不略赐以儿子半点？', '荣禧堂 · 正房', 21, 8, 9,
     ['E:zheng:greet:1.4']),
    ('c22-beichen', 'C22-164', 'grandmother', '你在这里，他们都不敢说笑，没的倒叫我闷', '荣禧堂 · 正房', 21, 9, 10,
     ['E:grandmother:greet:1.4']),
    ('c22-beichen', 'C22-165', 'grandmother', '你要猜谜时，我便说一个你猜，猜不著是要罚的', '荣禧堂 · 正房', 21, 10, 11,
     ['E:grandmother:greet:1.4']),
    ('c22-beichen', 'C22-166', 'narrator', '贾政忙笑道：自然要罚', '荣禧堂 · 正房', 21, 11, 12,
     ['E:zheng:greet:1.2']),
    ('c22-beichen', 'C22-167', 'narrator', '猴子身轻站树梢——打一果名', '荣禧堂 · 正房', 22, 0, 2,
     ['E:grandmother:rest:1.4']),
    ('c22-beichen', 'C22-168', 'narrator', '贾政已知是荔枝，便故意乱猜别的，罚了许多东西', '荣禧堂 · 正房', 23, 0, 1,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-169', 'narrator', '身自端方，体自坚硬', '荣禧堂 · 正房', 24, 0, 2,
     ['E:grandmother:rest:1.4']),
    ('c22-beichen', 'C22-170', 'narrator', '虽不能言，有言必应——打一用物', '荣禧堂 · 正房', 24, 1, 3,
     ['E:grandmother:rest:1.2']),
    ('c22-beichen', 'C22-171', 'narrator', '说毕，便悄悄的说与宝玉', '荣禧堂 · 正房', 25, 0, 1,
     ['M:zheng:rongxi_steps>rongxi_door', 'E:zheng:rest:1.2']),
    ('c22-beichen', 'C22-172', 'baoyu', '宝玉意会，又悄悄的告诉了贾母', '荣禧堂 · 正房', 25, 1, 2,
     ['E:baoyu:rest:1.2']),
    ('c22-beichen', 'C22-173', 'grandmother', '是砚台', '荣禧堂 · 正房', 25, 2, 3,
     ['E:grandmother:greet:1.4']),
    ('c22-beichen', 'C22-174', 'zheng', '到底是老太太，一猜就是', '荣禧堂 · 正房', 25, 3, 4,
     ['E:zheng:greet:1.2']),
    ('c22-beichen', 'C22-175', 'narrator', '宝玉执壶，迎春送酒', '荣禧堂 · 正房', 25, 7, 8,
     ['M:baoyu:rongxi_door>rongxi_center', 'M:yingchun:east_court>rongxi_door', 'E:yingchun:rest:1.2']),
    ('c22-beichen', 'C22-176', 'narrator', '贾政答应，起身走至屏前，只见头一个写道是', '荣禧堂 · 正房', 26, 0, 1,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-177', 'narrator', '能使妖魔胆尽摧，身如束帛气如雷', '荣禧堂 · 正房', 27, 0, 1,
     ['E:zheng:rest:1.2']),
    ('c22-beichen', 'C22-178', 'narrator', '一声震得人方恐，回首相看已化灰', '荣禧堂 · 正房', 27, 1, 2,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-179', 'zheng', '这是炮竹嗄', '荣禧堂 · 正房', 28, 0, 1,
     ['E:zheng:greet:1.2']),
    ('c22-beichen', 'C22-180', 'baoyu', '是', '荣禧堂 · 正房', 28, 1, 2,
     ['E:baoyu:greet:1.2']),
    ('c22-beichen', 'C22-181', 'narrator', '天运人功理不穷，有功无运也难逢', '荣禧堂 · 正房', 29, 0, 1,
     ['E:zheng:rest:1.2']),
    ('c22-beichen', 'C22-182', 'narrator', '因何镇日纷纷乱，只为阴阳数不同', '荣禧堂 · 正房', 29, 1, 2,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-183', 'zheng', '是算盘', '荣禧堂 · 正房', 30, 0, 1,
     ['E:zheng:greet:1.2']),
    ('c22-beichen', 'C22-184', 'yingchun', '是', '荣禧堂 · 正房', 30, 1, 2,
     ['E:yingchun:greet:1.2']),
    ('c22-beichen', 'C22-185', 'narrator', '阶下儿童仰面时，清明妆点最堪宜', '荣禧堂 · 正房', 31, 0, 1,
     ['E:zheng:rest:1.2']),
    ('c22-beichen', 'C22-186', 'narrator', '游丝一断浑无力，莫向东风怨别离', '荣禧堂 · 正房', 31, 1, 2,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-187', 'zheng', '这是风筝', '荣禧堂 · 正房', 32, 0, 1,
     ['E:zheng:greet:1.2']),
    ('c22-beichen', 'C22-188', 'tanchun', '是', '荣禧堂 · 正房', 32, 1, 2,
     ['E:tanchun:greet:1.2']),
    ('c22-beichen', 'C22-189', 'narrator', '前身色相总无成，不听菱歌听佛经', '荣禧堂 · 正房', 33, 0, 1,
     ['E:zheng:rest:1.2']),
    ('c22-beichen', 'C22-190', 'narrator', '莫道此生沉黑海，性中自有大光明', '荣禧堂 · 正房', 33, 1, 2,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-191', 'zheng', '这是佛前海灯嗄', '荣禧堂 · 正房', 34, 0, 1,
     ['E:zheng:greet:1.2']),
    ('c22-beichen', 'C22-192', 'xichun', '是海灯', '荣禧堂 · 正房', 34, 1, 2,
     ['E:xichun:greet:1.2']),
    ('c22-beichen', 'C22-193', 'narrator', '贾政心内沉思道：娘娘所作爆竹，此乃一响而散之物', '荣禧堂 · 正房', 35, 0, 1,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-194', 'narrator', '迎春所作算盘，是打动乱如麻', '荣禧堂 · 正房', 35, 1, 2,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-195', 'narrator', '探春所作风筝，乃飘飘浮荡之物', '荣禧堂 · 正房', 35, 2, 3,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-196', 'narrator', '惜春所作海灯，一发清净孤独', '荣禧堂 · 正房', 35, 3, 4,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-197', 'narrator', '今乃上元佳节，如何皆作此不祥之物为戏耶？', '荣禧堂 · 正房', 35, 4, 5,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-198', 'narrator', '心内愈思愈闷，因在贾母之前，不敢形于色', '荣禧堂 · 正房', 35, 5, 6,
     ['E:zheng:anger:1.4']),
    ('c22-beichen', 'C22-199', 'narrator', '只见后面写著七言律诗一首，却是宝钗所作', '荣禧堂 · 正房', 35, 6, 7,
     ['E:zheng:rest:1.2']),
    ('c22-beichen', 'C22-200', 'narrator', '朝罢谁携两袖烟，琴边衾里总无缘', '荣禧堂 · 正房', 36, 0, 1,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-201', 'narrator', '晓筹不用鸡人报，五夜无烦侍女添', '荣禧堂 · 正房', 36, 1, 2,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-202', 'narrator', '焦首朝朝还暮暮，煎心日日复年年', '荣禧堂 · 正房', 36, 2, 3,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-203', 'narrator', '光阴荏苒须当惜，风雨阴晴任变迁', '荣禧堂 · 正房', 36, 3, 4,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-204', 'narrator', '贾政看完，心内自忖道：此物还倒有限', '荣禧堂 · 正房', 37, 0, 1,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-205', 'narrator', '只是小小之人作此词句，更觉不祥，皆非永远福寿之辈', '荣禧堂 · 正房', 37, 1, 2,
     ['E:zheng:anger:1.4']),
    ('c22-beichen', 'C22-206', 'narrator', '因而将适才的精神减去十分之八九，只垂头沉思', '荣禧堂 · 正房', 37, 2, 3,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-207', 'grandmother', '你竟不必猜了，去安歇罢', '荣禧堂 · 正房', 38, 0, 2,
     ['E:grandmother:greet:1.4']),
    ('c22-beichen', 'C22-208', 'narrator', '贾政一闻此言，连忙答应几个「是」字，又勉强劝了贾母一回酒', '荣禧堂 · 正房', 38, 2, 3,
     ['E:zheng:rest:1.2']),
    ('c22-beichen', 'C22-209', 'narrator', '回至房中只是思索，翻来复去竟难成寐', '荣禧堂 · 正房', 38, 3, 4,
     ['E:zheng:rest:1.4']),
    ('c22-beichen', 'C22-210', 'narrator', '贾母见贾政去了，便道：你们可自在乐一乐罢', '荣禧堂 · 正房', 39, 0, 1,
     ['H:zheng', 'E:grandmother:greet:1.4']),
    ('c22-beichen', 'C22-211', 'narrator', '早见宝玉跑至围屏灯前，指手画脚，满口批评', '荣禧堂 · 正房', 39, 1, 2,
     ['M:baoyu:rongxi_center>rongxi_steps', 'E:baoyu:greet:1.4']),
    ('c22-beichen', 'C22-212', 'baochai', '还象适才坐著，大家说说笑笑，岂不斯文些儿', '荣禧堂 · 正房', 39, 2, 3,
     ['E:baochai:greet:1.4']),
    ('c22-beichen', 'C22-213', 'feng', '你这个人，就该老爷每日令你寸步不离方好', '荣禧堂 · 正房', 39, 3, 4,
     ['E:feng:greet:1.4']),
    ('c22-beichen', 'C22-214', 'feng', '为什么不当著老爷，撺掇叫你也作诗谜儿', '荣禧堂 · 正房', 39, 4, 5,
     ['E:feng:greet:1.4']),
    ('c22-beichen', 'C22-215', 'narrator', '说的宝玉急了，扯著凤姐儿，扭股儿糖似的只是厮缠', '荣禧堂 · 正房', 39, 6, 7,
     ['E:baoyu:idle:1.2']),
    ('c22-beichen', 'C22-216', 'narrator', '贾母又与李宫裁并众姊妹说笑了一会', '荣禧堂 · 正房', 39, 7, 8,
     ['E:grandmother:rest:1.4']),
    ('c22-beichen', 'C22-217', 'narrator', '听了听已是漏下四鼓，命将食物撤去，赏散与众人', '荣禧堂 · 正房', 39, 8, 9,
     ['E:grandmother:rest:1.2']),
    ('c22-beichen', 'C22-218', 'narrator', '我们安歇罢。明日还是节下，该当早起', '荣禧堂 · 正房', 39, 9, 11,
     ['E:grandmother:greet:1.4']),
]


# ---------------------------------------------------------------- 证据补充
# 设计决定：哪些底本细节需要在证据表里显式记一笔「这是我们做的选择」。
DESIGN_NOTES = [
    ('C22-D1', 'c22-shengri',
     '宝钗生辰的酒戏由贾母出银子、凤姐承办；贾琏只「站着商量」不出资',
     '底本没有写贾母「蠲资」之外还另外拨了多少，也没写宝钗生辰的花费由谁账上；'
     '本回不额外虚构数目。',
     '底本写「贾母蠲资二十两」，全由内帑出；贾琏一句「既如此，比林妹妹的多增些」'
     '是替凤姐出主意，不是掏腰包，所以贾琏在本段不出银子。'),
    ('C22-D2', 'c22-dianxi',
     '点戏地点借天香楼（c11_tianxiang）演「贾母内院中搭了家常小巧戏台」',
     '底本明写戏台搭在「贾母内院」，不是梨香院也不是天香楼。',
     '本项目尚无「贾母院戏台」专图，第 18 回点戏四出已用天香楼作梨香院代用，'
     '本回沿用同一张图，把 place 写成「天香楼 · 看楼」并在标题里点明是看楼，'
     '不宣称那就是荣府内院的原样。'),
    ('C22-D3', 'c22-gengyi',
     '湘云更衣摔手放在怡红院外间；翠缕随侍在旁',
     '底本只说「晚间，湘云更衣时」，没有交代具体屋子；'
     '本回依第 21 回「湘云住怡红院」的场景线承接，未另立新地点。',
     '底本只说「晚间，湘云更衣时」，未言何处。第 21 回湘云与宝玉同住怡红院'
     '（第 21 回段 11「湘云仍往黛玉房中安歇」之前曾同住），此处依第 21 回'
     '「湘云在怡红院」的场景线承接。'),
    ('C22-D4', 'c22-bimen',
     '黛玉闭门一段放在贾母院碧纱橱（night 场景）',
     '底本只说「又来寻黛玉」，未言屋在何处；本回沿用第 21 回已统一的'
     '「黛玉房 = 贾母院碧纱橱」，不新开一张图，也不声称这就是大观园里的潇湘馆。',
     '底本只说「又来寻黛玉」，未言何处。第 21 回已把「黛玉房」统一到 night '
     '场景（贾母院碧纱橱），本回沿用同一处，不新开一张图。'),
    ('C22-D5', 'c22-dengmi',
     '元春的灯谜由「传话来人」（messenger）执灯入场',
     '底本只写「一个小太监」，未给名字。',
     'cast 里没有太监这个人物。第 16 回「六宫都太监夏守忠降旨」也是复用 '
     'messenger，本回沿用同一处理：不新增角色，也不把 messenger 说成是夏守忠。'),
    ('C22-D6', 'c22-beichen',
     '贾兰是本回唯一的新角色：底本段 20 他被唤来入席，段 21 他仍「不肯来」',
     '底本只写「他说方才老爷并没去叫他，他不肯来」，是李氏转述，'
     '贾兰本人一句台词也没有；本回只让他在席上坐下吃果子，不替他编台词。',
     '前 21 回贾兰只在叙述里被提到（第 4、13、18 回各一次），从未现身，'
     '所以本回是他第一次有戏份，需要补立绘与 Q 版。'),
    ('C22-D7', 'c22-beichen',
     '「炮竹」「算盘」「风筝」「海灯」四首灯谜逐个由贾政点破、作者当场应声',
     '底本在谜面之间留了作者插话（宝玉、迎春、探春、惜春各应一声），'
     '这些是原书本来就有的节奏，照实切成节点；本回不另加评点、不改动原句。',
     '底本在「又看道是」与谜面之间留了作者插话（宝玉、迎春、探春、惜春各应'
     '一声），这些是原书本来就有的节奏，照实切成节点，不另加评点。'),
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
                'chapter': 22,
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
            'id': step['id'].replace('C22-', 'C22-E'),
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
        'chapter': 22,
        'source': {
            'edition': '维基文库《紅樓夢》第 022 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第022回&action=raw',
            'retrievedAt': '2026-11-13',
            'localText': 'docs/chapter22-source.txt',
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
        print('第22回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第22回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 22})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第22回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
