#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 27 回的剧情、段落、证据数据。

第 27 回《滴翠亭杨妃戏彩蝶　埋香冢飞燕泣残红》，底本
docs/chapter27-source.txt（维基文库原文，繁体转简体，19 段正文）。
写法沿用第 18-25 回确立的**底本切片式生成**：不手写正文，
按**子句索引**切片，正文与 source.paragraphLead 都是切出来的。

用法：
    python3 scripts/build_chapter27.py            # 生成
    python3 scripts/build_chapter27.py --check    # 只校验已有文件

分场（对照 docs/chapter27-production.md）：

  宝钗一条 —— 潇湘馆外 → 扑蝶至滴翠亭 → 亭外偷听 → 金蝉脱壳 → 红玉坠儿后怕
  红玉一条 —— 凤姐山坡使唤 → 园中问路遇晴雯 → 稻香村回话，得凤姐赏识
  宝黛一条 —— 潇湘馆梳洗 → 石榴树下探春说鞋 → 花冢收落花 → 黛玉泣残红

**零新图**：底本「花冢 / 桃林」可由 `qinfang`（沁芳闸桃花下）的 `tomb` /
`peach_grove` 锚点直接承接；滴翠亭「四面俱是游廊曲桥，盖造在池中水上」
亦落在同一张水景图的桥 / 亭角锚点上。复用场景：
  daguanyuan 大观园全景（潇湘馆、稻香村、石榴树下的代用图，本项目无潇湘馆专图）
  qinfang    沁芳闸桃花下（扑蝶、滴翠亭、花冢、葬花吟）
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter27-source.txt'
STORY = ROOT / 'design' / 'chapter27-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter27-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter27-evidence.json'

QUOTE_MAP = {c: '"' for c in '“”「」『』‘’'}


def normalize(text: str) -> str:
    return ''.join(QUOTE_MAP.get(c, c) for c in text)


def load_base():
    raw = BASE.read_text(encoding='utf-8')
    raw = re.sub(r'<section\s+(?:begin|end)="[^"]*"\s*/>', '', raw)
    # 葬花吟段被维基 <poem> 包裹；这是排版标记不是正文，清掉后文字仍逐字来自底本。
    raw = raw.replace('<poem>', '').replace('</poem>', '')
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

    沿用第 23-25 回的子句级切法：本回宝钗偷听、凤姐使唤、探春说鞋与
    葬花吟句句都长，一句一节点会把整段话塞进一个节点，节奏全丢。
    闭合引号归到**前**一个子句。
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
        # 葬花吟的维基排版在部分诗句前留了一个空格，不是正文内容。
        out.append(s.lstrip())
    return out


SENTENCES = {i: split_sentences(p) for i, p in enumerate(PARAS)}


def cut_sent(para: int, s_from: int, s_to: int, extend=True):
    """切出底本第 para 段的第 [s_from, s_to) 个子句。返回 (正文, 起句原文)。

    正文会延伸到该子句所在**整句的末尾**（下一个句末标点之后），
    读者看到的是完整句子；lead 仍取子句起点——它是正文的前缀，
    且能在底本逐字查到（check_content 的 VERBATIM_BASE 会验这一条）。

    ★ 引号边界：下一子句以「“「『」开头就是另一段引语的第一句，不许吞。
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
    ('c27-daiyu', '潇湘馆 · 黛玉悲泣卸妆', 'daguanyuan'),
    ('c27-mangzhong', '大观园 · 芒种饯花神', 'daguanyuan'),
    ('c27-baochai', '大观园 · 宝钗往潇湘馆', 'daguanyuan'),
    ('c27-pudie', '沁芳亭 · 宝钗扑蝶到滴翠亭', 'qinfang'),
    ('c27-touting', '滴翠亭 · 亭外偷听手帕子', 'qinfang'),
    ('c27-jintao', '滴翠亭 · 金蝉脱壳', 'qinfang'),
    ('c27-hongyu', '滴翠亭 · 红玉坠儿后怕', 'qinfang'),
    ('c27-fengjiao', '沁芳亭 · 凤姐山坡使唤', 'qinfang'),
    ('c27-wen', '大观园 · 红玉问路遇晴雯', 'daguanyuan'),
    ('c27-lishi', '稻香村 · 回话李纨凤姐', 'daguanyuan'),
    ('c27-daiyu2', '潇湘馆 · 黛玉梳洗见宝玉', 'daguanyuan'),
    ('c27-tanchun', '大观园 · 石榴树下探春说鞋', 'daguanyuan'),
    ('c27-huazhong', '花冢 · 宝玉收落花', 'qinfang'),
    ('c27-zanghua', '花冢 · 黛玉泣残红与葬花吟', 'qinfang'),
]


# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题(底本原文片段), 地点, 底本段号, 起始子句号, 结束子句号, 动作)
# ★ 起点标题是底本原文片段，align_cuts 会拿它回锚底本自愈；终点由下一节点起点推导。
# ★ actor id 一律与 src/story.ts cast 逐字一致；zhuer/qingwen/siqi/qixian 为本回新角色，
#   已报主 agent 登记（见 docs/chapter27-production.md）。
CUTS = [
    # ---------------- c27-daiyu：段 1 ----------------
    ('c27-daiyu', 'C27-001', 'narrator', '话说林黛玉正自悲泣', '大观园 · 潇湘馆', 1, 0, 4,
     ['S:daiyu:daiyu_place']),
    ('c27-daiyu', 'C27-002', 'narrator', '待要上去问著宝玉', '大观园 · 潇湘馆', 1, 4, 10,
     ['E:daiyu:rest:1.4']),
    ('c27-daiyu', 'C27-003', 'narrator', '犹望著门洒了几点泪', '大观园 · 潇湘馆', 1, 10, 11,
     ['E:daiyu:rest:1.4']),
    ('c27-daiyu', 'C27-004', 'narrator', '自觉无味', '大观园 · 潇湘馆', 1, 11, 14,
     ['E:daiyu:rest:1.2']),

    # ---------------- c27-mangzhong：段 2 ----------------
    ('c27-mangzhong', 'C27-005', 'narrator', '紫鹃雪雁素日知道林黛玉的情性', '大观园 · 潇湘馆', 2, 0, 6,
     ['S:zijun:daiyu_place', 'S:xueyan:daiyu_place']),
    ('c27-mangzhong', 'C27-006', 'narrator', '先时还有人解劝', '大观园 · 潇湘馆', 2, 6, 17,
     ['E:zijun:greet:1.2']),
    ('c27-mangzhong', 'C27-007', 'narrator', '那林黛玉倚著床栏杆', '大观园 · 潇湘馆', 2, 17, 21,
     ['E:daiyu:rest:1.4']),
    ('c27-mangzhong', 'C27-008', 'narrator', '直坐到二更多天方才睡了', '大观园 · 潇湘馆', 2, 21, 23,
     ['E:daiyu:rest:1.2']),
    ('c27-mangzhong', 'C27-009', 'narrator', '至次日乃是四月二十六日', '大观园 · 芒种', 2, 23, 36,
     ['E:zijun:rest:1.2']),
    ('c27-mangzhong', 'C27-010', 'narrator', '那些女孩子们', '大观园 · 芒种', 2, 36, 43,
     ['S:tanchun:tea_place', 'S:xichun:tea_place']),
    ('c27-mangzhong', 'C27-011', 'narrator', '满园里绣带飘飖', '大观园 · 芒种', 2, 43, 48,
     ['E:tanchun:greet:1.2']),

    # ---------------- c27-baochai：段 3 ----------------
    ('c27-baochai', 'C27-012', 'narrator', '且说宝钗', '大观园 · 园中', 3, 0, 10,
     ['S:baochai:grandmother_place', 'S:yingchun:grandmother_place']),
    ('c27-baochai', 'C27-013', 'yingchun', '林妹妹怎么不见', '大观园 · 园中', 3, 10, 14,
     ['E:yingchun:greet:1.4']),
    ('c27-baochai', 'C27-014', 'baochai', '你们等著', '大观园 · 园中', 3, 14, 16,
     ['E:baochai:greet:1.4']),
    ('c27-baochai', 'C27-015', 'narrator', '说著便丢下了众人', '大观园 · 园中', 3, 16, 27,
     ['M:baochai:grandmother_place>feng_place>daiyu_place']),
    ('c27-baochai', 'C27-016', 'narrator', '忽然抬头见宝玉进去了', '大观园 · 潇湘馆', 3, 27, 28,
     ['S:baoyu:daiyu_place', 'E:baochai:rest:1.2']),
    ('c27-baochai', 'C27-017', 'narrator', '此刻自己也跟了进去', '大观园 · 潇湘馆', 3, 28, 39,
     ['E:baochai:rest:1.4']),
    ('c27-baochai', 'C27-018', 'narrator', '想毕抽身回来', '大观园 · 潇湘馆', 3, 39, 40,
     ['M:baochai:daiyu_place>feng_place']),

    # ---------------- c27-pudie：段 4 ----------------
    ('c27-pudie', 'C27-019', 'narrator', '刚要寻别的姊妹去', '大观园 · 沁芳亭', 4, 0, 5,
     ['S:baochai:bank_west']),
    ('c27-pudie', 'C27-020', 'narrator', '宝钗意欲扑了来玩耍', '大观园 · 沁芳亭', 4, 5, 8,
     ['E:baochai:greet:1.2']),
    ('c27-pudie', 'C27-021', 'narrator', '只见那一双蝴蝶忽起忽落', '大观园 · 沁芳亭', 4, 8, 12,
     ['M:baochai:bank_west>bridge_head']),
    ('c27-pudie', 'C27-022', 'narrator', '倒引的宝钗蹑手蹑脚的', '大观园 · 沁芳亭', 4, 12, 16,
     ['M:baochai:bridge_head>bridge_mid']),
    ('c27-pudie', 'C27-023', 'narrator', '宝钗也无心扑了', '大观园 · 滴翠亭', 4, 16, 18,
     ['E:baochai:rest:1.2']),
    ('c27-pudie', 'C27-024', 'narrator', '只听滴翠亭里边嘁嘁喳喳有人说话', '大观园 · 滴翠亭', 4, 18, 22,
     ['E:baochai:rest:1.4']),

    # ---------------- c27-touting：段 5 ----------------
    ('c27-touting', 'C27-025', 'narrator', '宝钗在亭外听见说话', '大观园 · 滴翠亭', 5, 0, 2,
     ['E:baochai:rest:1.2']),
    ('c27-touting', 'C27-026', 'narrator', '只听说道：“你瞧瞧这手帕子', '大观园 · 滴翠亭', 5, 2, 8,
     ['E:baochai:rest:1.2']),
    ('c27-touting', 'C27-027', 'narrator', '又听道：“你拿什么谢我呢', '大观园 · 滴翠亭', 5, 11, 14,
     ['E:baochai:rest:1.2']),
    ('c27-touting', 'C27-028', 'narrator', '又听说道：“我寻了来给你', '大观园 · 滴翠亭', 5, 17, 22,
     ['E:baochai:rest:1.2']),
    ('c27-touting', 'C27-029', 'narrator', '又回道：“你别胡说', '大观园 · 滴翠亭', 5, 22, 28,
     ['E:baochai:rest:1.2']),
    ('c27-touting', 'C27-030', 'narrator', '又听说道：“你不谢他', '大观园 · 滴翠亭', 5, 28, 34,
     ['E:baochai:rest:1.2']),
    ('c27-touting', 'C27-031', 'narrator', '半晌，又听答道：“也罢', '大观园 · 滴翠亭', 5, 34, 41,
     ['E:baochai:rest:1.4']),
    ('c27-touting', 'C27-032', 'narrator', '又听说道：“我要告诉一个人', '大观园 · 滴翠亭', 5, 41, 45,
     ['E:baochai:rest:1.2']),
    ('c27-touting', 'C27-033', 'narrator', '又听说道：“嗳呀', '大观园 · 滴翠亭', 5, 45, 55,
     ['E:baochai:rest:1.4']),

    # ---------------- c27-jintao：段 6 ----------------
    ('c27-jintao', 'C27-034', 'narrator', '宝钗在外面听见这话', '大观园 · 滴翠亭', 6, 0, 8,
     ['E:baochai:rest:1.2']),
    ('c27-jintao', 'C27-035', 'narrator', '况才说话的语音', '大观园 · 滴翠亭', 6, 8, 17,
     ['E:baochai:anger:1.4']),
    ('c27-jintao', 'C27-036', 'narrator', '如今便赶著躲了', '大观园 · 滴翠亭', 6, 17, 21,
     ['E:baochai:anger:1.4']),
    ('c27-jintao', 'C27-037', 'narrator', '只听”咯吱”一声', '大观园 · 滴翠亭', 6, 21, 24,
     ['E:baochai:greet:1.2']),
    ('c27-jintao', 'C27-038', 'baochai', '颦儿，我看你往那里藏', '大观园 · 滴翠亭', 6, 24, 28,
     ['E:baochai:greet:1.6']),
    ('c27-jintao', 'C27-039', 'narrator', '那亭内的红玉坠儿刚一推窗', '大观园 · 滴翠亭', 6, 28, 34,
     ['S:xiaohong:corner', 'S:zhuer:corner']),
    ('c27-jintao', 'C27-040', 'zhuer', '何曾见林姑娘了', '大观园 · 滴翠亭', 6, 34, 36,
     ['E:zhuer:rest:1.2']),
    ('c27-jintao', 'C27-041', 'baochai', '我才在河那边看著林姑娘', '大观园 · 滴翠亭', 6, 36, 42,
     ['E:baochai:greet:1.4']),
    ('c27-jintao', 'C27-042', 'narrator', '一面说一面故意进去寻了一寻', '大观园 · 滴翠亭', 6, 42, 45,
     ['M:baochai:corner>bridge_mid']),
    ('c27-jintao', 'C27-043', 'baochai', '一定是又钻在山子洞里去了', '大观园 · 滴翠亭', 6, 45, 52,
     ['E:baochai:greet:1.2']),

    # ---------------- c27-hongyu：段 7 ----------------
    ('c27-hongyu', 'C27-044', 'narrator', '谁知红玉听了宝钗的话', '大观园 · 滴翠亭', 7, 0, 4,
     ['E:xiaohong:rest:1.2']),
    ('c27-hongyu', 'C27-045', 'xiaohong', '了不得了！林姑娘蹲在这里', '大观园 · 滴翠亭', 7, 4, 9,
     ['E:xiaohong:anger:1.4']),
    ('c27-hongyu', 'C27-046', 'zhuer', '便是听了，管谁筋疼', '大观园 · 滴翠亭', 7, 12, 15,
     ['E:zhuer:rest:1.2']),
    ('c27-hongyu', 'C27-047', 'xiaohong', '若是宝姑娘听见', '大观园 · 滴翠亭', 7, 16, 23,
     ['E:xiaohong:anger:1.4']),
    ('c27-hongyu', 'C27-048', 'narrator', '二人正说著', '大观园 · 滴翠亭', 7, 23, 30,
     ['S:xiangling:corner', 'S:siqi:corner']),

    # ---------------- c27-fengjiao：段 8 ----------------
    ('c27-fengjiao', 'C27-049', 'narrator', '只见凤姐儿站在山坡上招手叫', '大观园 · 沁芳亭', 8, 0, 4,
     ['S:feng:bank_east']),
    ('c27-fengjiao', 'C27-050', 'xiaohong', '奶奶使唤作什么事', '大观园 · 沁芳亭', 8, 4, 9,
     ['M:xiaohong:corner>bank_east', 'E:xiaohong:greet:1.2']),
    ('c27-fengjiao', 'C27-051', 'feng', '我的丫头今儿没跟进我来', '大观园 · 沁芳亭', 8, 9, 20,
     ['E:feng:greet:1.4']),
    ('c27-fengjiao', 'C27-052', 'xiaohong', '奶奶有什么话，只管吩咐我说去', '大观园 · 沁芳亭', 8, 15, 21,
     ['E:xiaohong:greet:1.4']),
    ('c27-fengjiao', 'C27-053', 'feng', '你是那位小姐房里的', '大观园 · 沁芳亭', 8, 21, 27,
     ['E:feng:greet:1.2']),
    ('c27-fengjiao', 'C27-054', 'xiaohong', '我是宝二爷房里的', '大观园 · 沁芳亭', 8, 26, 28,
     ['E:xiaohong:greet:1.2']),
    ('c27-fengjiao', 'C27-055', 'feng', '你到我们家，告诉你平姐姐', '大观园 · 沁芳亭', 8, 34, 43,
     ['E:feng:greet:1.6']),

    # ---------------- c27-wen：段 9 ----------------
    ('c27-wen', 'C27-056', 'narrator', '红玉听说撤身去了', '大观园 · 园中', 9, 0, 2,
     ['S:xiaohong:feng_place']),
    ('c27-wen', 'C27-057', 'narrator', '因见司棋从山洞里出来', '大观园 · 园中', 9, 2, 5,
     ['S:siqi:feng_place']),
    ('c27-wen', 'C27-058', 'xiaohong', '姐姐，不知道二奶奶往那里去了', '大观园 · 园中', 9, 5, 8,
     ['E:xiaohong:greet:1.2']),
    ('c27-wen', 'C27-059', 'siqi', '司棋道：“没理论', '大观园 · 园中', 9, 7, 11,
     ['E:siqi:rest:1.2']),
    ('c27-wen', 'C27-060', 'tanchun', '往你大奶奶院里找去', '大观园 · 池边', 9, 15, 17,
     ['S:tanchun:tea_place', 'S:baochai:tea_place', 'E:tanchun:greet:1.2']),
    ('c27-wen', 'C27-061', 'narrator', '才往稻香村来', '大观园 · 稻香村', 9, 17, 18,
     ['M:xiaohong:feng_place>liwan_place']),
    ('c27-wen', 'C27-062', 'narrator', '顶头只见晴雯', '大观园 · 稻香村', 9, 18, 28,
     ['S:qingwen:liwan_place', 'S:bihen:liwan_place', 'S:qixian:liwan_place']),
    ('c27-wen', 'C27-063', 'qingwen', '便说道：“你只是疯罢', '大观园 · 稻香村', 9, 26, 34,
     ['E:qingwen:anger:1.4']),
    ('c27-wen', 'C27-064', 'xiaohong', '昨儿二爷说了', '大观园 · 稻香村', 9, 34, 40,
     ['E:xiaohong:greet:1.2']),
    ('c27-wen', 'C27-065', 'qixian', '你听听他的嘴', '大观园 · 稻香村', 9, 45, 49,
     ['E:qixian:rest:1.2']),
    ('c27-wen', 'C27-066', 'narrator', '说著将荷包举给他们看', '大观园 · 稻香村', 9, 51, 55,
     ['E:xiaohong:greet:1.2']),
    ('c27-wen', 'C27-067', 'qingwen', '怪道呢！原来爬上高枝儿去了', '大观园 · 稻香村', 9, 55, 65,
     ['E:qingwen:anger:1.6']),
    ('c27-wen', 'C27-068', 'narrator', '一面说著去了', '大观园 · 稻香村', 9, 65, 66,
     ['H:qingwen', 'H:bihen', 'H:qixian']),

    # ---------------- c27-lishi：段 10、11、12、13 ----------------
    ('c27-lishi', 'C27-069', 'narrator', '这里红玉听说', '大观园 · 稻香村', 10, 0, 6,
     ['S:feng:liwan_place', 'S:liwan:liwan_place']),
    ('c27-lishi', 'C27-070', 'xiaohong', '平姐姐说，奶奶刚出来了', '大观园 · 稻香村', 10, 6, 13,
     ['E:xiaohong:greet:1.4']),
    ('c27-lishi', 'C27-071', 'xiaohong', '平姐姐说：我们奶奶问这里奶奶好', '大观园 · 稻香村', 10, 20, 36,
     ['E:xiaohong:greet:1.6']),
    ('c27-lishi', 'C27-072', 'liwan', '话未说完，李氏道', '大观园 · 稻香村', 11, 0, 6,
     ['E:liwan:greet:1.4']),
    ('c27-lishi', 'C27-073', 'feng', '怨不得你不懂，这是四五门子的话呢', '大观园 · 稻香村', 11, 6, 9,
     ['E:feng:greet:1.4']),
    ('c27-lishi', 'C27-074', 'feng', '好孩子，难为你说的齐全', '大观园 · 稻香村', 11, 9, 15,
     ['E:feng:greet:1.4']),
    ('c27-lishi', 'C27-075', 'feng', '他们必定把一句话拉长了作两三截儿', '大观园 · 稻香村', 11, 15, 26,
     ['E:feng:anger:1.4']),
    ('c27-lishi', 'C27-076', 'liwan', '都象你泼皮破落户才好', '大观园 · 稻香村', 11, 26, 28,
     ['E:liwan:greet:1.2']),
    ('c27-lishi', 'C27-077', 'feng', '你明儿伏侍我去罢', '大观园 · 稻香村', 11, 33, 36,
     ['E:feng:greet:1.6']),
    ('c27-lishi', 'C27-078', 'feng', '红玉听了，扑哧一笑', '大观园 · 稻香村', 12, 0, 14,
     ['E:feng:anger:1.4']),
    ('c27-lishi', 'C27-079', 'xiaohong', '我不是笑这个', '大观园 · 稻香村', 12, 14, 19,
     ['E:xiaohong:greet:1.2']),
    ('c27-lishi', 'C27-080', 'liwan', '你原来不认得他？他是林之孝之女', '大观园 · 稻香村', 12, 21, 25,
     ['E:liwan:greet:1.2']),
    ('c27-lishi', 'C27-081', 'feng', '林之孝两口子都是锥子扎不出一声儿来的', '大观园 · 稻香村', 12, 28, 36,
     ['E:feng:greet:1.4']),
    ('c27-lishi', 'C27-082', 'xiaohong', '红玉道：“十七岁了', '大观园 · 稻香村', 12, 35, 39,
     ['E:xiaohong:greet:1.2']),
    ('c27-lishi', 'C27-083', 'xiaohong', '原叫红玉的，因为重了宝二爷', '大观园 · 稻香村', 12, 39, 42,
     ['E:xiaohong:greet:1.2']),
    ('c27-lishi', 'C27-084', 'feng', '凤姐听说将眉一皱', '大观园 · 稻香村', 13, 0, 8,
     ['E:feng:anger:1.4']),
    ('c27-lishi', 'C27-085', 'feng', '既这么著，明儿我和宝玉说', '大观园 · 稻香村', 13, 23, 29,
     ['E:feng:greet:1.4']),
    ('c27-lishi', 'C27-086', 'xiaohong', '愿意不愿意，我们也不敢说', '大观园 · 稻香村', 13, 29, 35,
     ['E:xiaohong:greet:1.4']),
    ('c27-lishi', 'C27-087', 'narrator', '刚说著，只见王夫人的丫头来请', '大观园 · 稻香村', 13, 35, 40,
     ['H:feng', 'H:liwan', 'H:xiaohong']),

    # ---------------- c27-daiyu2：段 14 ----------------
    ('c27-daiyu2', 'C27-088', 'narrator', '如今且说林黛玉因夜间失寐', '大观园 · 潇湘馆', 14, 0, 8,
     ['S:daiyu:daiyu_place']),
    ('c27-daiyu2', 'C27-089', 'baoyu', '好妹妹，你昨儿可告我了不曾', '大观园 · 潇湘馆', 14, 8, 12,
     ['S:baoyu:daiyu_place', 'E:baoyu:greet:1.4']),
    ('c27-daiyu2', 'C27-090', 'daiyu', '把屋子收拾了', '大观园 · 潇湘馆', 14, 12, 18,
     ['E:daiyu:greet:1.2']),
    ('c27-daiyu2', 'C27-091', 'narrator', '林黛玉正眼也不看', '大观园 · 潇湘馆', 14, 23, 26,
     ['M:daiyu:daiyu_place>feng_place']),
    ('c27-daiyu2', 'C27-092', 'narrator', '宝玉心中纳闷', '大观园 · 潇湘馆', 14, 26, 33,
     ['E:baoyu:rest:1.4']),
    ('c27-daiyu2', 'C27-093', 'narrator', '一面想，一面由不得随后追了来', '大观园 · 潇湘馆', 14, 33, 35,
     ['M:baoyu:daiyu_place>feng_place']),

    # ---------------- c27-tanchun：段 15、16 ----------------
    ('c27-tanchun', 'C27-094', 'narrator', '只见宝钗探春正在那边看鹤舞', '大观园 · 池边', 15, 0, 5,
     ['S:baochai:tea_place', 'S:tanchun:tea_place']),
    ('c27-tanchun', 'C27-095', 'tanchun', '宝哥哥，身上好', '大观园 · 池边', 15, 5, 9,
     ['E:tanchun:greet:1.2']),
    ('c27-tanchun', 'C27-096', 'baoyu', '妹妹身上好？我前儿还在大嫂子跟前问你呢', '大观园 · 池边', 15, 9, 12,
     ['S:baoyu:tea_place', 'E:baoyu:greet:1.2']),
    ('c27-tanchun', 'C27-097', 'narrator', '到了一棵石榴树下', '大观园 · 石榴树下', 15, 12, 20,
     ['M:tanchun:tea_place>baoyu_greet', 'M:baoyu:tea_place>baoyu_greet']),
    ('c27-tanchun', 'C27-098', 'tanchun', '这几个月，我又攒下有十来吊钱了', '大观园 · 石榴树下', 15, 30, 38,
     ['E:tanchun:greet:1.4']),
    ('c27-tanchun', 'C27-099', 'baoyu', '我这么城里城外，大廊小庙的逛', '大观园 · 石榴树下', 15, 38, 44,
     ['E:baoyu:greet:1.4']),
    ('c27-tanchun', 'C27-100', 'tanchun', '谁要这些。怎么象你上回买的那柳枝儿编的小篮子', '大观园 · 石榴树下', 15, 44, 58,
     ['E:tanchun:greet:1.4']),
    ('c27-tanchun', 'C27-101', 'baoyu', '宝玉笑道：“你提起鞋来', '大观园 · 石榴树下', 16, 0, 24,
     ['E:baoyu:greet:1.6']),
    ('c27-tanchun', 'C27-102', 'narrator', '登时沉下脸来', '大观园 · 石榴树下', 16, 24, 26,
     ['E:tanchun:anger:1.4']),
    ('c27-tanchun', 'C27-103', 'tanchun', '这话糊涂到什么田地', '大观园 · 石榴树下', 16, 26, 41,
     ['E:tanchun:anger:1.6']),
    ('c27-tanchun', 'C27-104', 'tanchun', '连你也糊涂了', '大观园 · 石榴树下', 16, 49, 63,
     ['E:tanchun:anger:1.6']),
    ('c27-tanchun', 'C27-105', 'tanchun', '还有笑话呢：就是上回我给你那钱', '大观园 · 石榴树下', 16, 63, 78,
     ['E:tanchun:anger:1.4']),
    ('c27-tanchun', 'C27-106', 'narrator', '正说著，只见宝钗那边笑道', '大观园 · 石榴树下', 16, 78, 80,
     ['E:baochai:greet:1.2']),
    ('c27-tanchun', 'C27-107', 'narrator', '探春宝玉二人方笑著来了', '大观园 · 石榴树下', 16, 86, 88,
     ['E:tanchun:greet:1.2']),

    # ---------------- c27-huazhong：段 17 ----------------
    ('c27-huazhong', 'C27-108', 'narrator', '宝玉因不见了林黛玉', '大观园 · 花冢', 17, 0, 8,
     ['S:baoyu:bank_east']),
    ('c27-huazhong', 'C27-109', 'baoyu', '这是他心里生了气', '大观园 · 花冢', 17, 8, 17,
     ['E:baoyu:rest:1.4']),
    ('c27-huazhong', 'C27-110', 'narrator', '等他二人去远了', '大观园 · 花冢', 17, 17, 19,
     ['M:baoyu:bank_east>bridge_mid']),
    ('c27-huazhong', 'C27-111', 'narrator', '便把那花兜了起来', '大观园 · 花冢', 17, 18, 22,
     ['M:baoyu:bridge_mid>tomb']),
    ('c27-huazhong', 'C27-112', 'narrator', '将已到了花冢', '大观园 · 花冢', 17, 22, 24,
     ['E:baoyu:rest:1.4']),
    ('c27-huazhong', 'C27-113', 'narrator', '只听山坡那边有呜咽之声', '大观园 · 花冢', 17, 24, 27,
     ['S:daiyu:tomb']),
    ('c27-huazhong', 'C27-114', 'narrator', '宝玉心下想道', '大观园 · 花冢', 17, 27, 31,
     ['E:baoyu:rest:1.4']),
    ('c27-huazhong', 'C27-115', 'narrator', '一面想，一面煞住脚步', '大观园 · 花冢', 17, 31, 34,
     ['E:baoyu:rest:1.2']),

    # ---------------- c27-zanghua：段 18、19 ----------------
    ('c27-zanghua', 'C27-116', 'daiyu', '花谢花飞花满天', '大观园 · 花冢', 18, 0, 2,
     ['E:daiyu:rest:1.6']),
    ('c27-zanghua', 'C27-117', 'daiyu', '闺中女儿惜春暮', '大观园 · 花冢', 18, 4, 8,
     ['E:daiyu:rest:1.4']),
    ('c27-zanghua', 'C27-118', 'daiyu', '三月香巢已垒成', '大观园 · 花冢', 18, 12, 16,
     ['E:daiyu:anger:1.4']),
    ('c27-zanghua', 'C27-119', 'daiyu', '一年三百六十日', '大观园 · 花冢', 18, 16, 20,
     ['E:daiyu:anger:1.6']),
    ('c27-zanghua', 'C27-120', 'daiyu', '杜鹃无语正黄昏', '大观园 · 花冢', 18, 24, 28,
     ['E:daiyu:rest:1.4']),
    ('c27-zanghua', 'C27-121', 'daiyu', '怪奴底事倍伤神', '大观园 · 花冢', 18, 28, 32,
     ['E:daiyu:rest:1.4']),
    ('c27-zanghua', 'C27-122', 'daiyu', '愿奴胁下生双翼', '大观园 · 花冢', 18, 36, 38,
     ['E:daiyu:rest:1.4']),
    ('c27-zanghua', 'C27-123', 'daiyu', '天尽头，何处有香丘', '大观园 · 花冢', 18, 38, 40,
     ['E:daiyu:anger:1.4']),
    ('c27-zanghua', 'C27-124', 'daiyu', '质本洁来还洁去', '大观园 · 花冢', 18, 42, 44,
     ['E:daiyu:rest:1.4']),
    ('c27-zanghua', 'C27-125', 'daiyu', '尔今死去侬收葬', '大观园 · 花冢', 18, 44, 46,
     ['E:daiyu:anger:1.6']),
    ('c27-zanghua', 'C27-126', 'daiyu', '试看春残花渐落', '大观园 · 花冢', 18, 48, 50,
     ['E:daiyu:anger:1.6']),
    ('c27-zanghua', 'C27-127', 'daiyu', '一朝春尽红颜老，花落人亡两不知', '大观园 · 花冢', 18, 50, 53,
     ['E:daiyu:anger:1.8']),
    # 末节点吃到段 19 末尾（含「要知端详，且听下回分解」），不再拆出重复收尾节点。
    ('c27-zanghua', 'C27-128', 'narrator', '宝玉听了不觉痴倒', '大观园 · 花冢', 19, 0, 3,
     ['E:baoyu:rest:1.8', 'H:daiyu']),
]


# ★ 沿用第 24、25 回的「区间自愈」：CUTS 只声明起点，终点由下一节点起点推导；
#   起点用「标题回锚底本」自愈（最长公共前缀打分），标题必须是底本原文片段。
def _strip_punct(text: str) -> str:
    return re.sub(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\'"]', '', text)


def _title_anchor(sents, para, title, after):
    """在本段里找标题的最佳落点，返回子句号；找不到返回 None。"""
    tn = _strip_punct(title)
    if not tn:
        return None
    best = None  # (匹配字数, -j)
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
    for i in range(len(fixed) - 1):
        if fixed[i][5] == fixed[i + 1][5]:
            fixed[i][7] = fixed[i + 1][6]
        else:
            fixed[i][7] = len(SENTENCES[fixed[i][5]])
    fixed[-1][7] = len(SENTENCES[fixed[-1][5]])
    return fixed, report


def cut_bounds(cuts):
    """给每个节点算出「延伸到哪里为止」（本模板不使用，保留供对照）。"""
    limits = []
    for i, c in enumerate(cuts):
        para = c[5]
        if i + 1 < len(cuts) and cuts[i + 1][5] == para:
            limits.append(cuts[i + 1][6])
        else:
            limits.append(len(SENTENCES[para]))
    return limits


DESIGN_NOTES = [
    ('C27-D1', 'c27-daiyu',
     '黛玉悲泣卸妆与紫鹃雪雁闷坐，复用 `daguanyuan`（大观园全景）代潇湘馆',
     '底本「忽听院门响处……宝玉等进去关了门，方转过来，犹望著门洒了几点泪」，'
     '仍是潇湘馆院中；本项目无潇湘馆专图。',
     '用 `daiyu_place` 锚点，`place` 写「大观园 · 潇湘馆」；场景语义由标题与正文承担。'),
    ('C27-D2', 'c27-mangzhong',
     '芒种饯花神的大观园女儿群像，复用 `daguanyuan`',
     '底本「大观园中之人都早起来了……满园里绣带飘飖，花枝招展」，'
     '是园中全景而非某一院落。',
     '用 `tea_place` 作群像落点，显示探春、惜春。'),
    ('C27-D3', 'c27-pudie',
     '宝钗扑蝶至滴翠亭、亭外偷听、金蝉脱壳，复用 `qinfang`（沁芳闸桃花下）',
     '底本「一直跟到池中滴翠亭上……原来这亭子四面俱是游廊曲桥，盖造在池中水上」，'
     '与 `qinfang` 的水体、曲桥、亭角语义一致；无需为滴翠亭另开图。',
     '用 `bank_west`/`bridge_head`/`bridge_mid`/`corner` 承接扑蝶、亭外与推窗。'),
    ('C27-D4', 'c27-huazhong',
     '「埋香冢黛玉泣残红」的花冢，复用 `qinfang` 已有的 `tomb` 锚点',
     '底本「一直奔了那日同林黛玉葬桃花的去处来。将已到了花冢」——'
     '第 23 回葬桃花已在 `qinfang` 的桃林/花冢处，此处是同一地点，'
     '且 `tomb` 在 `to_tomb` 路线的 `anchor_ids` 里、可通行、可立人。',
     '黛玉 `show` 在 `tomb`，宝玉由 `bridge_mid` 移至 `tomb`，不新建地图。'),
    ('C27-D5', 'c27-lishi',
     '李氏房中（稻香村）复用 `daguanyuan` 的 `liwan_place`',
     '底本「才往稻香村来……到了李氏房中，果见凤姐儿在这里和李氏说话儿呢」，'
     '本项目无稻香村专图；沿用大观园全景扮演各院的做法。',
     '用 `liwan_place` 作红玉回话、凤姐认女的场景落点。'),
    ('C27-D6', 'c27-zanghua',
     '葬花吟作为旁白念出的 `verbatim` 韵文节点，speaker 用 `daiyu`',
     '底本段 18 是黛玉哭吟的全文，无独立说话标记但「听他哭道是」指明是黛玉；'
     '按第 25 回四首赞诗的口径逐字切出，不改字。',
     '按 2-4 句一切分成 12 个节点，`textKind: verbatim`。'),
    ('C27-D7', 'c27-touting',
     '亭内两人对答保持 `narrator`：底本用「只听说道」「又有一人说话」转述',
     '宝钗在亭外偷听，看不清谁说的哪句，底本刻意隐去说话人；'
     '直到段 6 才点出「大似宝玉房里的红儿的言语」。',
     '偷听段全部用 narrator，不臆断说话人；段 6 之后才点名红玉。'),
    ('C27-D8', 'c27-wen',
     '晴雯、坠儿、司棋、绮霰四名有台词的角色报主 agent 登记为新 cast',
     '四人底本都有直接引语：坠儿「何曾见林姑娘了」、晴雯「你只是疯罢」、'
     '司棋「没理论」、绮霰「你听听他的嘴」；原 cast 表中四人均不存在。',
     '生成器用 snake_case id `zhuer`/`qingwen`/`siqi`/`qixian`；'
     '视觉设定见 docs/chapter27-production.md，由主 agent 统一登记 cast 与美术。'),
    ('C27-D9', 'c27-wen',
     '文官、待书、入画、紫绡、巧姐、大姐、张材家的、旺儿等只在叙述里点名',
     '这些人本回无一句独立台词，按第 24、25 回「提及不登场」先例处理。',
     '正文保留原名，不 show、不注册新 cast。'),
    ('C27-D10', 'c27-huazhong',
     '宝玉「登、渡、穿、奔」到花冢用两段 move 交代，不另开转场',
     '底本「登山渡水，过树穿花，一直奔了那日同林黛玉葬桃花的去处来」'
     '在同段内完成，引擎换场景才清台。',
     '`bank_east>bridge_mid`、`bridge_mid>tomb` 两个 move 沿 `qinfang` 既有路线。'),
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
                'chapter': 27,
                'paragraphLead': lead,
                'textKind': 'verbatim',
                'layer': 'present',
            },
            '_pos': (para, s_from),
        })
    return steps


def assign_scenes(steps):
    """定场景与 focus（focus 是锚点名；last_focus 按**场景**记）。"""
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
    """写盘前的自校。"""
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
        # 舞台连续性自检（只查 move）：引擎只在换场景时清空舞台。
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

    probe_path = ROOT / 'artifacts' / 'probe_walkable_tmp_c27.mjs'
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
            'id': step['id'].replace('C27-', 'C27-E'),
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
        'chapter': 27,
        'source': {
            'edition': '维基文库《紅樓夢》第 027 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第027回&action=raw',
            'retrievedAt': '2026-11-25',
            'localText': 'docs/chapter27-source.txt',
            'processing': 'MediaWiki action=raw 取回 wikitext，去模板与导航行，OpenCC 转简体；'
                         '回目行与正文之间补空行，回目自成一段；葬花吟段的 <poem> 排版标记清除；'
                         '正文未作增删。',
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
        print('第27回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第27回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 27})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第27回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
