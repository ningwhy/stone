#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 30 回的剧情、段落、证据数据。

第 30 回底本是维基文库原文全文（docs/chapter30-source.txt），写法沿用第 24/25 回
确立的**底本切片式生成**：不手写正文，按**子句索引**切片，正文与 source.paragraphLead
都是切出来的；起点用「标题回锚底本」自愈，终点由下一个节点起点推导。

用法：
    python3 scripts/build_chapter30.py            # 生成
    python3 scripts/build_chapter30.py --check    # 只校验已有文件

第 30 回《宝钗借扇机带双敲　龄官划蔷痴及局外》分场（底本段 1–17）：

  黛玉房  —— 紫鹃劝解 → 宝玉赔不是 → 戳额递帕 → 凤姐跳来说合拉走
  贾母院  —— 凤姐说合 → 宝钗借扇机带双敲 → 负荆请罪 → 凤姐吃姜
  王夫人上房 —— 金钏儿捶腿 → 调笑、王夫人打骂 → 金钏儿苦求被撵
  蔷薇花架 —— 龄官划蔷（新图 qiangwei）→ 阵雨提醒、宝玉淋雨
  怡红院  —— 宝官玉官玩耍关门 → 叫门 → 误踢袭人 → 夜间秉灯见血

**一名新角色**：龄官 `lingguan`（十二个学戏的女孩子之一，小生；底本无正面姓名，
本回第一次以「画蔷的女孩子」登场，有台词与动作，由主 agent 统一登记 cast 与美术）。
金钏儿 `jinyuan`、贾蔷 `jia_qiang` 均已在 cast（贾蔷本回正文未出场，只在回目里出现「划蔷」）。
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter30-source.txt'
STORY = ROOT / 'design' / 'chapter30-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter30-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter30-evidence.json'

QUOTE_MAP = {c: '"' for c in '“”「」『』‘’'}


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
    闭合引号归到**前**一个子句（沿用第 23–25 回口径）。
    """
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


def cut_sent(para: int, s_from: int, s_to: int, extend=True):
    """切出底本第 para 段的第 [s_from, s_to) 个子句。返回 (正文, 起句原文)。

    正文延伸到该子句所在整句的末尾；下一子句以「“「『」开头就是另一段
    引语的第一句，不吞（第 24 回净改进）。lead 仍取子句起点，逐字可查。
    """
    sents = SENTENCES[para]
    if not (0 <= s_from < s_to <= len(sents)):
        raise ValueError(f'第 {para} 段子句号 [{s_from}, {s_to}) 越界（共 {len(sents)} 句）')
    lead = sents[s_from]
    raw = ''.join(sents[s_from:s_to])
    if extend:
        end = s_to
        while end < len(sents):
            if sents[end].lstrip()[:1] in '“「『':
                break
            end += 1
            if re.search(r'[。！？]', sents[end - 1]):
                break
        if end > s_to:
            raw = ''.join(sents[s_from:end])
    if not raw.startswith(lead):
        raise ValueError(f'第 {para} 段第 {s_from} 句定位失败：{lead[:20]}')
    return raw, lead


def to_display(text: str) -> str:
    """底本弯引号 → 「」『』，只换标点不动字。"""
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
    ('c30-zijuan', '黛玉房 · 紫鹃劝与宝玉叫门', 'night'),
    ('c30-peibushi', '黛玉房 · 宝玉赔不是', 'night'),
    ('c30-chuo', '黛玉房 · 戳额与递帕', 'night'),
    ('c30-fengjie', '黛玉房 · 凤姐跳来说合', 'night'),
    ('c30-jiamu', '贾母院 · 贾母跟前说笑', 'dinner'),
    ('c30-yangfei', '贾母院 · 借扇机带双敲', 'dinner'),
    ('c30-fujing', '贾母院 · 负荆请罪与吃姜', 'dinner'),
    ('c30-chulai', '贾母院 · 黛玉讥宝玉出来', 'dinner'),
    ('c30-wangfuren', '王夫人上房 · 宝玉进房', 'wang'),
    ('c30-jinchu', '王夫人上房 · 金钏儿调笑', 'wang'),
    ('c30-nianchu', '王夫人上房 · 金钏儿被撵', 'wang'),
    ('c30-qiangwei', '大观园 · 龄官划蔷', 'qiangwei'),
    ('c30-yu', '大观园 · 阵雨与提醒', 'qiangwei'),
    ('c30-guamen', '怡红院 · 关门与叫门', 'yihong'),
    ('c30-ti', '怡红院 · 误踢袭人', 'yihong'),
    ('c30-tuxue', '怡红院 · 夜间秉灯见血', 'yihong'),
]


# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题(底本原文片段), 地点, 底本段号, 起始子句号, 结束子句号, 动作)
CUTS = [
    # ---------------- c30-zijuan：段 1、2（黛玉房） ----------------
    ('c30-zijuan', 'C30-001', 'narrator', '话说林黛玉与宝玉角口后', '黛玉房', 1, 0, 7,
     ['S:daiyu:daiyu_bed', 'S:zijun:bedside']),
    ('c30-zijuan', 'C30-002', 'zijun', '若论前日之事', '黛玉房', 1, 7, 13,
     ['E:zijun:greet:1.4']),
    ('c30-zijuan', 'C30-003', 'daiyu', '你倒来替人派我的不是', '黛玉房', 1, 13, 16,
     ['E:daiyu:anger:1.4']),
    ('c30-zijuan', 'C30-004', 'zijun', '好好的，为什么又剪了那穗子', '黛玉房', 1, 16, 24,
     ['E:zijun:greet:1.4']),
    ('c30-zijuan', 'C30-005', 'narrator', '林黛玉正欲答话，只听院外叫门', '黛玉房', 2, 0, 4,
     ['E:daiyu:rest:1.2']),
    ('c30-zijuan', 'C30-006', 'zijun', '这是宝玉的声音', '黛玉房', 2, 4, 7,
     ['E:zijun:greet:1.2']),
    ('c30-zijuan', 'C30-007', 'daiyu', '不许开门', '黛玉房', 2, 7, 8,
     ['E:daiyu:anger:1.2']),
    ('c30-zijuan', 'C30-008', 'narrator', '口里说著，便出去开门，果然是宝玉', '黛玉房', 2, 12, 20,
     ['S:baoyu:outer_door']),
    ('c30-zijuan', 'C30-009', 'baoyu', '你们把极小的事倒说大了', '黛玉房', 2, 20, 25,
     ['E:baoyu:greet:1.4']),
    ('c30-zijuan', 'C30-010', 'narrator', '一面说著，一面进来，只见林黛玉又在床上哭', '黛玉房', 2, 30, 33,
     ['M:baoyu:outer_door>night_talk']),

    # ---------------- c30-peibushi：段 3 ----------------
    ('c30-peibushi', 'C30-011', 'narrator', '那林黛玉本不曾哭', '黛玉房', 3, 0, 6,
     ['E:daiyu:rest:1.2']),
    ('c30-peibushi', 'C30-012', 'baoyu', '妹妹身上可大好了', '黛玉房', 3, 6, 9,
     ['E:baoyu:greet:1.2']),
    ('c30-peibushi', 'C30-013', 'narrator', '宝玉因便挨在床沿上坐了', '黛玉房', 3, 9, 11,
     ['M:baoyu:night_talk>bedside']),
    ('c30-peibushi', 'C30-014', 'baoyu', '我知道妹妹不恼我', '黛玉房', 3, 11, 15,
     ['E:baoyu:greet:1.4']),
    ('c30-peibushi', 'C30-015', 'narrator', '若等他们来劝咱们', '黛玉房', 3, 15, 27,
     ['E:baoyu:greet:1.4']),
    ('c30-peibushi', 'C30-016', 'daiyu', '你也不用哄我', '黛玉房', 3, 27, 32,
     ['E:daiyu:anger:1.4']),
    ('c30-peibushi', 'C30-017', 'baoyu', '你往那去呢', '黛玉房', 3, 32, 34,
     ['E:baoyu:greet:1.2']),
    ('c30-peibushi', 'C30-018', 'daiyu', '我回家去', '黛玉房', 3, 34, 36,
     ['E:daiyu:rest:1.2']),
    ('c30-peibushi', 'C30-019', 'baoyu', '你死了，我做和尚', '黛玉房', 3, 40, 45,
     ['E:baoyu:anger:1.4']),
    ('c30-peibushi', 'C30-020', 'daiyu', '想是你要死了，胡说的是什么', '黛玉房', 3, 45, 51,
     ['E:daiyu:anger:1.6']),

    # ---------------- c30-chuo：段 4 ----------------
    ('c30-chuo', 'C30-021', 'narrator', '宝玉自知这话说的造次了', '黛玉房', 4, 0, 8,
     ['E:baoyu:rest:1.2']),
    ('c30-chuo', 'C30-022', 'narrator', '便咬著牙用指头狠命的在他额颅上戳了一下', '黛玉房', 4, 8, 14,
     ['E:daiyu:anger:1.4']),
    ('c30-chuo', 'C30-023', 'narrator', '不觉滚下泪来', '黛玉房', 4, 21, 25,
     ['E:baoyu:rest:1.2']),
    ('c30-chuo', 'C30-024', 'narrator', '向宝玉怀里一摔', '黛玉房', 4, 31, 34,
     ['E:daiyu:anger:1.4']),
    ('c30-chuo', 'C30-025', 'baoyu', '我的五脏都碎了', '黛玉房', 4, 39, 43,
     ['E:baoyu:greet:1.4']),
    ('c30-chuo', 'C30-026', 'daiyu', '谁同你拉拉扯扯的', '黛玉房', 4, 44, 48,
     ['E:daiyu:anger:1.6']),

    # ---------------- c30-fengjie：段 5 前半（黛玉房） ----------------
    ('c30-fengjie', 'C30-027', 'narrator', '一句没说完，只听喊道', '黛玉房', 5, 0, 8,
     ['S:feng:outer_door']),
    ('c30-fengjie', 'C30-028', 'feng', '老太太在那里抱怨天抱怨地', '黛玉房', 5, 8, 17,
     ['E:feng:greet:1.4']),
    ('c30-fengjie', 'C30-029', 'feng', '也没见你们两个人有些什么可拌的', '黛玉房', 5, 17, 26,
     ['E:feng:greet:1.4']),
    ('c30-fengjie', 'C30-030', 'narrator', '说著拉了林黛玉就走', '黛玉房', 5, 26, 30,
     ['M:daiyu:bedside>outer_door']),
    ('c30-fengjie', 'C30-031', 'narrator', '宝玉在后面跟著出了园门', '黛玉房', 5, 34, 35,
     ['M:baoyu:bedside>outer_door']),

    # ---------------- c30-jiamu：段 5 后半（贾母院） ----------------
    ('c30-jiamu', 'C30-032', 'narrator', '到了贾母跟前', '贾母院', 5, 35, 37,
     ['S:grandmother:grandmother_place', 'S:feng:feng_place', 'S:daiyu:daiyu_place', 'S:baoyu:baoyu_greet']),
    ('c30-jiamu', 'C30-033', 'feng', '我说他们不用人费心，自己就会好的', '贾母院', 5, 37, 44,
     ['E:feng:greet:1.4']),
    ('c30-jiamu', 'C30-034', 'narrator', '倒象黄鹰抓住了鹞子的脚', '贾母院', 5, 44, 47,
     ['E:feng:greet:1.4']),
    ('c30-jiamu', 'C30-035', 'narrator', '说的满屋里都笑起来', '贾母院', 5, 47, 48,
     ['E:grandmother:greet:1.4']),

    # ---------------- c30-yangfei：段 6 ----------------
    ('c30-yangfei', 'C30-036', 'narrator', '此时宝钗正在这里', '贾母院', 6, 0, 5,
     ['S:baochai:tea_place']),
    ('c30-yangfei', 'C30-037', 'baoyu', '大哥哥好日子，偏生我又不好了', '贾母院', 6, 5, 15,
     ['E:baoyu:greet:1.4']),
    ('c30-yangfei', 'C30-038', 'baochai', '这也多事', '贾母院', 6, 15, 21,
     ['E:baochai:greet:1.4']),
    ('c30-yangfei', 'C30-039', 'baoyu', '姐姐怎么不看戏去', '贾母院', 6, 23, 25,
     ['E:baoyu:greet:1.2']),
    ('c30-yangfei', 'C30-040', 'baochai', '我怕热，看了两出', '贾母院', 6, 25, 32,
     ['E:baochai:greet:1.4']),
    ('c30-yangfei', 'C30-041', 'baoyu', '怪不得他们拿姐姐比杨妃', '贾母院', 6, 35, 37,
     ['E:baoyu:anger:1.4']),
    ('c30-yangfei', 'C30-042', 'baochai', '我倒象杨妃，只是没一个好哥哥好兄弟可以作得杨国忠的', '贾母院', 6, 45, 48,
     ['E:baochai:anger:1.6']),
    ('c30-yangfei', 'C30-043', 'narrator', '可巧小丫头靛儿因不见了扇子', '贾母院', 6, 48, 54,
     ['E:baochai:anger:1.4']),
    ('c30-yangfei', 'C30-044', 'baochai', '你要仔细', '贾母院', 6, 54, 60,
     ['E:baochai:anger:1.6']),

    # ---------------- c30-fujing：段 7 ----------------
    ('c30-fujing', 'C30-045', 'narrator', '林黛玉听见宝玉奚落宝钗', '贾母院', 7, 0, 6,
     ['E:daiyu:rest:1.2']),
    ('c30-fujing', 'C30-046', 'daiyu', '宝姐姐，你听了两出什么戏', '贾母院', 7, 6, 13,
     ['E:daiyu:greet:1.4']),
    ('c30-fujing', 'C30-047', 'baochai', '我看的是李逵骂了宋江', '贾母院', 7, 13, 16,
     ['E:baochai:greet:1.4']),
    ('c30-fujing', 'C30-048', 'baoyu', '姐姐通今博古，色色都知道', '贾母院', 7, 16, 22,
     ['E:baoyu:greet:1.4']),
    ('c30-fujing', 'C30-049', 'baochai', '原来这叫作《负荆请罪》', '贾母院', 7, 22, 27,
     ['E:baochai:anger:1.6']),
    ('c30-fujing', 'C30-050', 'feng', '你们大暑天，谁还吃生姜呢', '贾母院', 7, 33, 35,
     ['E:feng:greet:1.4']),
    ('c30-fujing', 'C30-051', 'feng', '既没人吃姜，怎么这么辣辣的', '贾母院', 7, 40, 42,
     ['E:feng:greet:1.4']),
    ('c30-fujing', 'C30-052', 'narrator', '宝玉黛玉二人听见这话，越发不好过了', '贾母院', 7, 42, 51,
     ['E:baoyu:rest:1.2']),

    # ---------------- c30-chulai：段 8 ----------------
    ('c30-chulai', 'C30-053', 'narrator', '一时宝钗凤姐去了', '贾母院', 8, 0, 2,
     ['H:baochai', 'H:feng']),
    ('c30-chulai', 'C30-054', 'daiyu', '你也试著比我利害的人了', '贾母院', 8, 2, 5,
     ['E:daiyu:greet:1.2']),
    ('c30-chulai', 'C30-055', 'narrator', '宝玉正因宝钗多了心', '贾母院', 8, 5, 12,
     ['E:baoyu:anger:1.4']),
    ('c30-chulai', 'C30-056', 'narrator', '无精打采一直出来', '贾母院', 8, 12, 13,
     ['M:baoyu:baoyu_greet>back_door']),

    # ---------------- c30-wangfuren：段 9 ----------------
    ('c30-wangfuren', 'C30-057', 'narrator', '谁知目今盛暑之时', '王夫人上房', 9, 0, 6,
     ['S:baoyu:court_entry']),
    ('c30-wangfuren', 'C30-058', 'narrator', '从贾母这里出来，往西走了穿堂', '王夫人上房', 9, 6, 15,
     ['M:baoyu:court_entry>hall_entry']),
    ('c30-wangfuren', 'C30-059', 'narrator', '遂进角门，来到王夫人上房内', '王夫人上房', 9, 15, 17,
     ['M:baoyu:hall_entry>guest_seat']),
    ('c30-wangfuren', 'C30-060', 'narrator', '只见几个丫头子手里拿著针线，却打盹儿呢', '王夫人上房', 9, 17, 19,
     ['E:baoyu:rest:1.2']),
    ('c30-wangfuren', 'C30-061', 'narrator', '王夫人在里间凉榻上睡著', '王夫人上房', 9, 19, 22,
     ['S:wang:wang_host', 'S:jinyuan:kang_edge']),

    # ---------------- c30-jinchu：段 10 ----------------
    ('c30-jinchu', 'C30-062', 'narrator', '宝玉轻轻的走到跟前', '王夫人上房', 10, 0, 5,
     ['M:baoyu:guest_seat>kang_edge']),
    ('c30-jinchu', 'C30-063', 'baoyu', '就困的这么著', '王夫人上房', 10, 5, 12,
     ['E:baoyu:greet:1.2']),
    ('c30-jinchu', 'C30-064', 'narrator', '便自己向身边荷包里带的香雪润津丹掏了出来', '王夫人上房', 10, 12, 18,
     ['E:baoyu:greet:1.2']),
    ('c30-jinchu', 'C30-065', 'baoyu', '我明日和太太讨你，咱们在一处罢', '王夫人上房', 10, 18, 21,
     ['E:baoyu:greet:1.4']),
    ('c30-jinchu', 'C30-066', 'baoyu', '不然，等太太醒了我就讨', '王夫人上房', 10, 22, 27,
     ['E:baoyu:greet:1.2']),
    ('c30-jinchu', 'C30-067', 'jinyuan', '你忙什么！金簪子掉在井里头', '王夫人上房', 10, 27, 31,
     ['E:jinyuan:greet:1.4']),
    ('c30-jinchu', 'C30-068', 'jinyuan', '我倒告诉你个巧宗儿', '王夫人上房', 10, 31, 34,
     ['E:jinyuan:greet:1.4']),
    ('c30-jinchu', 'C30-069', 'baoyu', '凭他怎么去罢，我只守著你', '王夫人上房', 10, 34, 36,
     ['E:baoyu:greet:1.4']),
    ('c30-jinchu', 'C30-070', 'wang', '下作小娼妇，好好的爷们，都叫你教坏了', '王夫人上房', 10, 39, 42,
     ['E:wang:anger:1.8']),
    ('c30-jinchu', 'C30-071', 'narrator', '宝玉见王夫人起来，早一溜烟去了', '王夫人上房', 10, 42, 44,
     ['M:baoyu:kang_edge>hall_entry', 'H:baoyu']),

    # ---------------- c30-nianchu：段 11 ----------------
    ('c30-nianchu', 'C30-072', 'narrator', '这里金钏儿半边脸火热', '王夫人上房', 11, 0, 5,
     ['E:jinyuan:anger:1.4']),
    ('c30-nianchu', 'C30-073', 'wang', '把你妈叫来，带出你姐姐去', '王夫人上房', 11, 5, 9,
     ['E:wang:anger:1.4']),
    ('c30-nianchu', 'C30-074', 'jinyuan', '我再不敢了', '王夫人上房', 11, 9, 16,
     ['E:jinyuan:anger:1.6']),
    ('c30-nianchu', 'C30-075', 'narrator', '王夫人固然是个宽仁慈厚的人', '王夫人上房', 11, 16, 23,
     ['E:wang:rest:1.2']),
    ('c30-nianchu', 'C30-076', 'narrator', '虽金钏儿苦求，亦不肯收留', '王夫人上房', 11, 23, 26,
     ['E:wang:anger:1.4']),
    ('c30-nianchu', 'C30-077', 'narrator', '那金钏儿含羞忍辱的出去', '王夫人上房', 11, 26, 28,
     ['H:jinyuan']),

    # ---------------- c30-qiangwei：段 12（新图） ----------------
    ('c30-qiangwei', 'C30-078', 'narrator', '且说那宝玉见王夫人醒来', '大观园 · 蔷薇花架', 12, 0, 7,
     ['S:baoyu:garden_path']),
    ('c30-qiangwei', 'C30-079', 'narrator', '刚到了蔷薇花架，只听有人哽噎之声', '大观园 · 蔷薇花架', 12, 7, 15,
     ['M:baoyu:garden_path>fence_hole']),
    ('c30-qiangwei', 'C30-080', 'narrator', '只见一个女孩子蹲在花下', '大观园 · 蔷薇花架', 12, 15, 19,
     ['S:lingguan:under_trellis']),
    ('c30-qiangwei', 'C30-081', 'baoyu', '难道这也是个痴丫头，又象颦儿来葬花不成', '大观园 · 蔷薇花架', 12, 19, 22,
     ['E:baoyu:rest:1.2']),
    ('c30-qiangwei', 'C30-082', 'baoyu', '若真也葬花，可谓东施效颦', '大观园 · 蔷薇花架', 12, 22, 30,
     ['E:baoyu:rest:1.2']),
    ('c30-qiangwei', 'C30-083', 'narrator', '话未出口，幸而再看时', '大观园 · 蔷薇花架', 12, 30, 34,
     ['E:baoyu:rest:1.2']),
    ('c30-qiangwei', 'C30-084', 'narrator', '倒象是那十二个学戏的女孩子之内的', '大观园 · 蔷薇花架', 12, 34, 36,
     ['E:lingguan:rest:1.2']),
    ('c30-qiangwei', 'C30-085', 'narrator', '宝玉忙把舌头一伸，将口掩住', '大观园 · 蔷薇花架', 12, 36, 47,
     ['E:baoyu:rest:1.2']),
    ('c30-qiangwei', 'C30-086', 'narrator', '再留神细看', '大观园 · 蔷薇花架', 12, 47, 52,
     ['E:baoyu:greet:1.2']),
    ('c30-qiangwei', 'C30-087', 'narrator', '大有林黛玉之态', '大观园 · 蔷薇花架', 12, 52, 55,
     ['E:lingguan:rest:1.2']),
    ('c30-qiangwei', 'C30-088', 'narrator', '只见他虽然用金簪划地', '大观园 · 蔷薇花架', 12, 55, 64,
     ['E:lingguan:idle:1.4']),
    ('c30-qiangwei', 'C30-089', 'narrator', '原来就是个蔷薇花的蔷字', '大观园 · 蔷薇花架', 12, 64, 77,
     ['E:baoyu:greet:1.4']),
    ('c30-qiangwei', 'C30-090', 'narrator', '只见那女孩子还在那里画呢', '大观园 · 蔷薇花架', 12, 77, 82,
     ['E:lingguan:idle:1.4']),
    ('c30-qiangwei', 'C30-091', 'narrator', '里面的原是早已痴了', '大观园 · 蔷薇花架', 12, 82, 85,
     ['E:lingguan:idle:1.4']),
    ('c30-qiangwei', 'C30-092', 'narrator', '外面的不觉也看痴了', '大观园 · 蔷薇花架', 12, 85, 95,
     ['E:baoyu:rest:1.4']),

    # ---------------- c30-yu：段 13 ----------------
    ('c30-yu', 'C30-093', 'narrator', '伏中阴晴不定，片云可以至雨', '大观园 · 蔷薇花架', 13, 0, 4,
     ['E:baoyu:rest:1.2']),
    ('c30-yu', 'C30-094', 'narrator', '忽一阵凉风过了，唰唰的落下一阵雨来', '大观园 · 蔷薇花架', 13, 2, 4,
     ['E:lingguan:rest:1.2']),
    ('c30-yu', 'C30-095', 'narrator', '宝玉看著那女子头上滴下水来', '大观园 · 蔷薇花架', 13, 4, 11,
     ['E:lingguan:rest:1.2']),
    ('c30-yu', 'C30-096', 'baoyu', '不用写了', '大观园 · 蔷薇花架', 13, 11, 14,
     ['E:baoyu:greet:1.4']),
    ('c30-yu', 'C30-097', 'lingguan', '多谢姐姐提醒了我', '大观园 · 蔷薇花架', 13, 25, 27,
     ['E:lingguan:greet:1.4']),
    ('c30-yu', 'C30-098', 'narrator', '说声不好，只得一气跑回怡红院去了', '大观园 · 蔷薇花架', 13, 32, 35,
     ['M:baoyu:fence_hole>garden_path', 'H:baoyu']),

    # ---------------- c30-guamen：段 14、15（怡红院） ----------------
    ('c30-guamen', 'C30-099', 'narrator', '原来明日是端阳节', '怡红院', 14, 0, 3,
     ['S:xiren:yard']),
    ('c30-guamen', 'C30-100', 'narrator', '可巧小生宝官，正旦玉官等两个女孩子', '怡红院', 14, 3, 7,
     ['E:xiren:greet:1.2']),
    ('c30-guamen', 'C30-101', 'narrator', '袭人等都在游廊上嘻笑', '怡红院', 14, 17, 18,
     ['E:xiren:rest:1.2']),
    ('c30-guamen', 'C30-102', 'narrator', '宝玉见关著门，便以手扣门', '怡红院', 15, 0, 4,
     ['S:baoyu:gate_step']),
    ('c30-guamen', 'C30-103', 'narrator', '叫了半日，拍的门山响', '怡红院', 15, 4, 9,
     ['E:baoyu:anger:1.4']),
    ('c30-guamen', 'C30-104', 'xiren', '谁这会子叫门，没人开去', '怡红院', 15, 9, 12,
     ['E:xiren:greet:1.2']),
    ('c30-guamen', 'C30-105', 'baoyu', '是我', '怡红院', 15, 12, 14,
     ['E:baoyu:anger:1.2']),
    ('c30-guamen', 'C30-106', 'she_yue', '是宝姑娘的声音', '怡红院', 15, 14, 16,
     ['S:she_yue:outer_room', 'E:she_yue:greet:1.2']),
    ('c30-guamen', 'C30-107', 'narrator', '胡说，宝姑娘这会子做什么来', '怡红院', 15, 16, 19,
     ['E:xiren:greet:1.2']),
    ('c30-guamen', 'C30-108', 'xiren', '让我隔著门缝儿瞧瞧', '怡红院', 15, 19, 32,
     ['M:xiren:yard>gate_step']),

    # ---------------- c30-ti：段 16 ----------------
    ('c30-ti', 'C30-109', 'narrator', '宝玉一肚子没好气', '怡红院', 16, 0, 5,
     ['E:baoyu:anger:1.6']),
    ('c30-ti', 'C30-110', 'narrator', '便抬腿踢在肋上', '怡红院', 16, 5, 8,
     ['E:xiren:anger:1.8']),
    ('c30-ti', 'C30-111', 'baoyu', '下流东西们', '怡红院', 16, 8, 13,
     ['E:baoyu:anger:1.6']),
    ('c30-ti', 'C30-112', 'narrator', '一低头见是袭人哭了', '怡红院', 16, 13, 16,
     ['E:baoyu:rest:1.2']),
    ('c30-ti', 'C30-113', 'baoyu', '嗳哟，是你来了！踢在那里了', '怡红院', 16, 16, 19,
     ['E:baoyu:anger:1.4']),
    ('c30-ti', 'C30-114', 'xiren', '没有踢著，还不换衣裳去', '怡红院', 16, 29, 33,
     ['E:xiren:anger:1.4']),
    ('c30-ti', 'C30-115', 'baoyu', '我长了这么大，今日是头一遭儿生气打人', '怡红院', 16, 33, 38,
     ['E:baoyu:rest:1.4']),
    ('c30-ti', 'C30-116', 'xiren', '我是个起头儿的人', '怡红院', 16, 38, 44,
     ['E:xiren:anger:1.4']),
    ('c30-ti', 'C30-117', 'xiren', '谁说你是安心了', '怡红院', 16, 46, 57,
     ['E:xiren:anger:1.4']),

    # ---------------- c30-tuxue：段 17 ----------------
    ('c30-tuxue', 'C30-118', 'narrator', '说著，那雨已住了', '怡红院', 17, 0, 4,
     ['E:baoyu:rest:1.2']),
    ('c30-tuxue', 'C30-119', 'narrator', '袭人只觉肋下疼的心里发闹', '怡红院', 17, 4, 6,
     ['E:xiren:rest:1.4']),
    ('c30-tuxue', 'C30-120', 'narrator', '至晚间洗澡时脱了衣服', '怡红院', 17, 6, 10,
     ['S:xiren:xiren_kang']),
    ('c30-tuxue', 'C30-121', 'narrator', '一时睡下，梦中作痛', '怡红院', 17, 10, 16,
     ['E:xiren:rest:1.4']),
    ('c30-tuxue', 'C30-122', 'narrator', '忽夜间听得嗳哟', '怡红院', 17, 16, 18,
     ['E:baoyu:rest:1.2']),
    ('c30-tuxue', 'C30-123', 'narrator', '自己下床悄悄的秉灯来照', '怡红院', 17, 18, 31,
     ['S:baoyu:baoyu_kang']),
    ('c30-tuxue', 'C30-124', 'xiren', '我头上发晕，嗓子里又腥又甜，你倒照一照地下罢', '怡红院', 17, 31, 35,
     ['E:xiren:anger:1.4']),
    ('c30-tuxue', 'C30-125', 'narrator', '果然持灯向地下一照，只见一口鲜血在地', '怡红院', 17, 35, 37,
     ['E:baoyu:anger:1.8']),
    ('c30-tuxue', 'C30-126', 'narrator', '要知端的，且听下回分解', '怡红院', 17, 41, 43,
     ['E:xiren:rest:1.2']),
]


def _strip_punct(text: str) -> str:
    return re.sub(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\'"]', '', text)


def _title_anchor(sents, para, title, after):
    """在本段里找标题的最佳落点，返回子句号；找不到返回 None。

    after：只考虑严格大于该位置的子句，保证全局单调递增。
    打分用「标题前缀在候选窗口里匹配了多少字」（启 24 回口径）。
    """
    tn = _strip_punct(title)
    if not tn:
        return None
    best = None
    for j in range(len(sents)):
        if (para, j) <= after:
            continue
        acc = ''
        for k in range(j, min(j + 12, len(sents))):
            acc += _strip_punct(sents[k])
            if len(acc) >= len(tn):
                break
        n = 0
        for x, y in zip(tn, acc):
            if x != y:
                break
            n += 1
        if n == 0:
            continue
        cand = (n, -j)
        if best is None or cand > best:
            best = cand
    if best and best[0] >= max(6, int(len(tn) * 0.6)):
        return -best[1]
    return None


def align_cuts(cuts):
    """自愈 CUTS 的起点并推导终点。返回 (新 CUTS, 报告)。"""
    report = []
    fixed = []
    after = (-1, -1)
    for c in cuts:
        chap, nid, spk, title, place, para, s_from, s_to, acts = c
        sents = SENTENCES[para]
        anchor = _title_anchor(sents, para, title, after)
        if anchor is None:
            anchor = s_from
            if (para, anchor) <= after:
                anchor = after[1] + 1
            report.append((nid, para, s_from, anchor, '保留原起点（标题不是底本片段）'))
        elif anchor != s_from:
            report.append((nid, para, s_from, anchor, '标题回锚'))
        fixed.append([chap, nid, spk, title, place, para, anchor, s_to, acts])
        after = (para, anchor)
    # 终点 = 下一个节点的起点；段末节点吃到本段末尾
    for i in range(len(fixed) - 1):
        if fixed[i][5] == fixed[i + 1][5]:
            fixed[i][7] = fixed[i + 1][6]
        else:
            fixed[i][7] = len(SENTENCES[fixed[i][5]])
    fixed[-1][7] = len(SENTENCES[fixed[-1][5]])
    return fixed, report


def cut_bounds(cuts):
    limits = []
    for i, c in enumerate(cuts):
        para = c[5]
        if i + 1 < len(cuts) and cuts[i + 1][5] == para:
            limits.append(cuts[i + 1][6])
        else:
            limits.append(len(SENTENCES[para]))
    return limits


DESIGN_NOTES = [
    ('C30-D1', 'c30-zijuan',
     '紫鹃劝解与宝玉赔不是放 `night`（黛玉房）',
     '底本段 1–4 全在黛玉房内：黛玉「在床上哭」、宝玉「挨在床沿上坐了」、'
     '戳额递帕，第 21/22 回黛玉房场景即用 `night`。',
     '用 `night` 的 `daiyu_bed`/`bedside`/`night_talk`/`outer_room` 锚点，不新开潇湘馆专图。'),
    ('C30-D2', 'c30-jiamu',
     '贾母院看戏说合一段复用 `dinner`',
     '底本段 5「到了贾母跟前」、段 6「此时宝钗正在这里……姐姐怎么不看戏去」，'
     '是贾母处众姊妹聚坐看戏的场面；`dinner` 有 grandmother_place/daiyu_place/feng_place/tea_place。',
     '用 `dinner` 的 `grandmother_place`/`daiyu_place`/`feng_place`/`baoyu_greet`/`tea_place`。'),
    ('C30-D3', 'c30-yangfei',
     '靛儿不入 cast：她的台词作为叙述节点照录，只 show 宝钗',
     '靛儿是小丫头，只在段 6/7 找扇子时被点名并说两句话；'
     '按本项目「提及不登场」与「配角台词归旁白」先例处理，避免为一次过场新增 cast。',
     'speaker 用 narrator；宝钗「你要仔细」等单独台词节点用 `baochai`。'),
    ('C30-D4', 'c30-wangfuren',
     '金钏儿调笑与被撵放 `wang`（王夫人上房）',
     '底本段 9「来到王夫人上房内……王夫人在里间凉榻上睡著，金钏儿坐在旁边捶腿」，'
     '段 10 王夫人「翻身起来照脸上打了个嘴巴子」，是同一室内。',
     '用 `wang` 的 `wang_host`（王夫人）、`kang_edge`（金钏儿）、`guest_seat`（宝玉）、`hall_entry`。'),
    ('C30-D5', 'c30-qiangwei',
     '龄官划蔷新建 `qiangwei`（蔷薇花架）',
     '底本段 12「刚到了蔷薇花架……蔷薇正是花叶茂盛之际，宝玉便悄悄的隔著篱笆洞儿一看，'
     '只见一个女孩子蹲在花下……在地下画字」；段 13「唰唰的落下一阵雨来」。'
     '现有 `qinfang` 是水闸桥边桃林，丢得掉「篱笆洞儿」与「花下泥地」，语义冲突。',
     '新建 5 锚点（garden_path/fence_hole/outside_trellis/under_trellis/rose_bush），'
     '一条 main 动线全通，`check:anchors` 与 `map:framing` 已过。'),
    ('C30-D6', 'c30-qiangwei',
     '龄官 `lingguan` 是本回必须的新角色（有台词与动作）',
     '底本段 12 写她「手里拿著根绾头的簪子在地下抠土」「画来画去，还是个蔷字」；'
     '段 13 有台词「多谢姐姐提醒了我。难道姐姐在外头有什么遮雨的？」'
     '她被宝玉认作「十二个学戏的女孩子之内」的一个，正面姓名本回未出。',
     '新角色 id 用 `lingguan`，由主 agent 登记 cast 与美术；底本无外貌描写，视觉设定为设计推定。'),
    ('C30-D7', 'c30-guamen',
     '怡红院关门叫门、误踢袭人、夜间见血均在 `yihong`',
     '底本段 14「正在怡红院和袭人玩笑……将院门关了……袭人等都在游廊上嘻笑」；'
     '段 16「抬腿踢在肋上」；段 17「至晚间洗澡时脱了衣服」，同一处所。',
     '用 `yihong` 的 `yard`/`gate_step`/`outer_room`/`xiren_kang`/`baoyu_kang`。'),
    ('C30-D8', 'c30-guamen',
     '麝月有台词且在 cast；晴雯、宝官玉官等不入 cast',
     '段 15 麝月「是宝姑娘的声音」有台词且已在 cast，照录并 show；'
     '晴雯「胡说！宝姑娘这会子做什么来」虽有台词，但 cast 表中 `qiuwen` 是秋纹而非晴雯，'
     '晴雯从未登记，按「配角台词归旁白」处理，避免挂错头像；'
     '宝官、玉官、文官等十二女子只在段 14/17 叙述里点名，无台词。',
     '用 `she_yue` 的台词节点；晴雯台词作 narrator 节点照录，不 show、不注册新 cast。'),
    ('C30-D9', 'c30-nianchu',
     '玉钏儿、白老媳妇、彩云、贾环、贾蔷不入 cast 或只作叙述点名',
     '玉钏儿、白老媳妇在段 11 只被叫来领人；彩云在金钏儿台词里被提及；'
     '贾环只在「拿环哥儿同彩云去」一句里出现；贾蔷本回正文未出场（「划蔷」是画蔷薇的「蔷」字）。',
     '只在正文里保留这些名字，不 show、不为他们新建节点。'),
    ('C30-D10', 'c30-qiangwei',
     '蔷薇花架的美术用 garden-tree / bamboo-gate 承担，是设计推定',
     '底本只写「蔷薇正是花叶茂盛」「隔著篱笆洞儿」，本项目无蔷薇专素材；'
     '以 `garden-tree` 成片代花荫、`bamboo-gate` 代篱笆洞、`wood-screen` 代篱笆。',
     'features/prompt 标「底本只写花叶与篱笆洞，以下为视觉设计推定」，不冒充原著记载。'),
]


def build():
    steps = []
    cuts, report = align_cuts(CUTS)
    if report:
        print(f'区间自愈：{len(report)} 处起点被重算')
        for r in report:
            print(f'  {r[0]} p{r[1]}: {r[2]} -> {r[3]}  {r[4]}')
    for sec_id, node_id, speaker, title, place, para, s_from, s_to, actions in cuts:
        text, lead = cut_sent(para, s_from, s_to)
        steps.append({
            'id': node_id,
            'chapter': sec_id,
            'scene': None,
            'title': title,
            'place': place,
            'focus': '',
            'speaker': speaker,
            'text': to_display(text),
            'actions': parse_actions(actions),
            'source': {
                'chapter': 30,
                'paragraphLead': lead,
                'textKind': 'verbatim',
                'layer': 'present',
            },
            '_pos': (para, s_from),
        })
    return steps


def assign_scenes(steps):
    """定场景与 focus。focus 是锚点名；last_focus 按**场景**记。"""
    scene_of = {s[0]: s[2] for s in SECTIONS}
    last_focus = {}
    for step in steps:
        if step['chapter'] not in scene_of:
            raise ValueError(f'{step["id"]} 的段 id {step["chapter"]} 不在 SECTIONS 里')
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
            focus = last_focus.get(step['scene'], '')
        step['focus'] = focus
        if focus:
            last_focus[step['scene']] = focus


def check(steps):
    """写盘前的自校：唯一 id / 单调 / 正文与 lead 非空且逐字 / focus 非空 / 舞台连续性。"""
    errors = []
    seen_ids = set()
    last = None
    for step in steps:
        if step['id'] in seen_ids:
            errors.append(f'{step["id"]}: 节点 id 重复')
        seen_ids.add(step['id'])
        pos = step['_pos']
        if last is not None and pos <= last:
            errors.append(f'{step["id"]}: 底本位置 {pos} 不大于上一个 {last}')
        last = pos
        if not step['text'].strip():
            errors.append(f'{step["id"]}: 正文为空')
        if not step['source']['paragraphLead'].strip():
            errors.append(f'{step["id"]}: paragraphLead 为空')
        if not step.get('focus'):
            errors.append(f'{step["id"]}: focus 为空（段首既无 show 也无 move 时会断链）')
        stripped_lead = re.sub(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\']', '', step['source']['paragraphLead'])
        if stripped_lead and stripped_lead not in re.sub(
                r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\']', '', BODY):
            errors.append(f'{step["id"]}: paragraphLead 在底本里查不到：{step["source"]["paragraphLead"][:30]}')
    # 舞台连续性：引擎只在换场景时清台，同场景可见性保持。
    onstage = {}
    cur_scene = None
    for step2 in steps:
        if step2['scene'] != cur_scene:
            onstage = {}
            cur_scene = step2['scene']
        for act in step2['actions']:
            if act['type'] == 'show':
                onstage[act['actor']] = step2['id']
            elif act['type'] == 'hide':
                onstage.pop(act['actor'], None)
            elif act['type'] == 'move' and act['actor'] not in onstage:
                errors.append(f'{step2["id"]}: 要移动 {act["actor"]}，但他从未在台上出现')
    return errors


def check_anchors(steps):
    """锚点必须在该场景的 Anchors 层里真实存在且可通行。"""
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

    # 五个 agent 并行，探针文件名必须带回号，否则互相覆盖。
    probe_path = ROOT / 'artifacts' / 'probe_walkable_tmp_c30.mjs'
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
            'id': step['id'].replace('C30-', 'C30-E'),
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
        'chapter': 30,
        'source': {
            'edition': '维基文库《紅樓夢》第 030 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第030回&action=raw',
            'retrievedAt': '2026-11-25',
            'localText': 'docs/chapter30-source.txt',
            'processing': 'MediaWiki action=raw 取回 wikitext，去模板与导航行，OpenCC 转简体；'
                         '按维基段落拆行，正文未作增删。',
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
        print('第30回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第30回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 30})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第30回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
