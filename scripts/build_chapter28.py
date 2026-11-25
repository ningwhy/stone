#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 28 回的剧情、段落、证据数据。

第 28 回底本是维基文库原文（docs/chapter28-source.txt，回目行 + 正文 33 段），
写法沿用第 18-25 回确立的**底本切片式生成**：不手写正文，按**子句索引**切片，
正文与 source.paragraphLead 都从底本切出；起点用「标题回锚底本」自愈，
终点由下一节点起点推导（scripts/build_chapter25.py 的 align_cuts 机制）。

用法：
    python3 scripts/build_chapter28.py            # 生成
    python3 scripts/build_chapter28.py --check    # 只校验已有文件

分场（对照 docs/chapter28-production.md）：

    沁芳闸 · 葬花与诉肺腑 → 王夫人上房 · 问药配方 → 凤姐院 · 礼单与红玉
    → 贾母院 · 黛玉裁剪 → 荣府 · 焙茗取衣 → 冯紫英家 · 赴宴行令赠茜香罗
    → 怡红院 · 汗巾与节礼 → 贾母院 · 金玉与红麝串

本回唯一新图：`fengziying_home`（冯紫英家家宴厅）—— 底本段 12「一径到了
冯紫英家门口……然后摆上酒来，依次坐定」，是独立空间，与既有家宴图 `dinner`
（贾母院晚膳）、`tavern`（村肆）语义冲突，故新开。

新角色三人（有实质台词，报告给主 agent 统一登记 cast 与美术）：
    feng_ziying（冯紫英）、jiang_yuhan（蒋玉菡/琪官）、yun_er（云儿）
焙茗即原著第 9 回的茗烟（后改名），复用既有 cast id `ming_yan`，不新增。
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter28-source.txt'
STORY = ROOT / 'design' / 'chapter28-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter28-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter28-evidence.json'

QUOTE_MAP = {c: '"' for c in '“”「」『』‘’'}


def normalize(text: str) -> str:
    return ''.join(QUOTE_MAP.get(c, c) for c in text)


def load_base():
    raw = BASE.read_text(encoding='utf-8')
    raw = re.sub(r'<section(?:begin|end)="[^"]*"\s*/>', '', raw)
    # 维基原文的 <ref> 注（甲戌本生字说明）与 <poem> 包裹不算正文，清掉后
    # 正文仍是逐字底本；曲子本身整段保留，作 verbatim 韵文节点。
    raw = re.sub(r'<ref>.*?</ref>', '', raw, flags=re.S)
    raw = re.sub(r'</?poem>', '', raw)
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
    闭合引号归到前一个子句；索引粒度与 CUTS 起点粒度一致。
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
    """切出底本第 para 段的第 [s_from, s_to) 个子句，返回 (正文, 起句原文)。

    正文延伸到该子句所在整句的末尾（下一个句末标点），但下一子句以
    「“「『」开头就是另一段引语的第一句，不许吞（第 24 回净改进）。
    lead 仍取子句起点，逐字可在底本查到。
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
    ('c28-zanghua', '沁芳闸 · 黛玉葬花宝玉恸倒', 'qinfang'),
    ('c28-supu', '大观园 · 山坡诉肺腑', 'qinfang'),
    ('c28-wenyao', '王夫人上房 · 问药与配方', 'wang'),
    ('c28-fengyuan', '凤姐院 · 礼单与红玉', 'c6_wangchui'),
    ('c28-caijian', '贾母院 · 黛玉裁剪', 'entry'),
    ('c28-chumen', '荣府 · 焙茗取衣裳', 'entry'),
    ('c28-fuyan', '冯紫英家 · 赴宴', 'fengziying_home'),
    ('c28-xingling', '冯紫英家 · 宝玉发令', 'fengziying_home'),
    ('c28-zhongling', '冯紫英家 · 众人行令', 'fengziying_home'),
    ('c28-qixiang', '冯紫英家 · 情赠茜香罗', 'fengziying_home'),
    ('c28-hanjin', '怡红院 · 汗巾与节礼', 'yihong'),
    ('c28-daiyan', '贾母院 · 金玉与红麝串', 'entry'),
]


# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题(底本原文片段), 地点, 底本段号, 起始子句号, 结束子句号, 动作)
# 起点标题是底本原文片段，align_cuts 回锚底本自愈；终点由下一节点起点推导。
CUTS = [
    # ---------------- c28-zanghua：段 1、2 ----------------
    ('c28-zanghua', 'C28-001', 'narrator', '话说林黛玉只因昨夜晴雯不开门一事', '大观园 · 沁芳闸', 1, 0, 9,
     ['S:daiyu:tomb']),
    ('c28-zanghua', 'C28-002', 'narrator', '不想宝玉在山坡上听见', '大观园 · 沁芳闸', 1, 9, 17,
     ['S:baoyu:stone_seat']),
    ('c28-zanghua', 'C28-003', 'narrator', '试想林黛玉的花颜月貌', '大观园 · 沁芳闸', 1, 17, 45,
     ['E:baoyu:rest:1.6']),
    ('c28-zanghua', 'C28-004', 'narrator', '那林黛玉正自伤感', '大观园 · 沁芳闸', 2, 0, 10,
     ['E:daiyu:rest:1.2']),
    ('c28-zanghua', 'C28-005', 'daiyu', '啐！我道是谁', '大观园 · 沁芳闸', 2, 10, 16,
     ['E:daiyu:anger:1.2']),

    # ---------------- c28-supu：段 3、4、5 ----------------
    ('c28-supu', 'C28-006', 'narrator', '这里宝玉悲恸了一回', '大观园 · 沁芳闸', 3, 0, 10,
     ['M:baoyu:stone_seat>bank_east']),
    ('c28-supu', 'C28-007', 'baoyu', '你且站住', '大观园 · 沁芳闸', 3, 10, 22,
     ['E:baoyu:greet:1.2']),
    ('c28-supu', 'C28-008', 'baoyu', '既有今日，何必当初', '大观园 · 沁芳闸', 3, 22, 35,
     ['E:baoyu:anger:1.4']),
    ('c28-supu', 'C28-009', 'baoyu', '当初姑娘来了', '大观园 · 沁芳闸', 3, 35, 55,
     ['E:baoyu:greet:1.6']),
    ('c28-supu', 'C28-010', 'baoyu', '我又没个亲兄弟亲姊妹', '大观园 · 沁芳闸', 3, 55, 67,
     ['E:baoyu:rest:1.6']),
    ('c28-supu', 'C28-011', 'narrator', '黛玉耳内听了这话', '大观园 · 沁芳闸', 4, 0, 7,
     ['E:daiyu:rest:1.2']),
    ('c28-supu', 'C28-012', 'baoyu', '我也知道我如今不好了', '大观园 · 沁芳闸', 4, 7, 25,
     ['E:baoyu:rest:1.6']),
    ('c28-supu', 'C28-013', 'daiyu', '你既这么说，昨儿为什么我去了', '大观园 · 沁芳闸', 5, 0, 6,
     ['E:daiyu:greet:1.2']),
    ('c28-supu', 'C28-014', 'baoyu', '这话从那里说起', '大观园 · 沁芳闸', 5, 6, 16,
     ['E:baoyu:anger:1.4']),
    ('c28-supu', 'C28-015', 'daiyu', '是了。想必是你的丫头们懒待动', '大观园 · 沁芳闸', 5, 16, 29,
     ['E:daiyu:greet:1.2']),
    ('c28-supu', 'C28-016', 'daiyu', '你的那些姑娘们也该教训教训', '大观园 · 沁芳闸', 5, 29, 41,
     ['E:daiyu:greet:1.4']),

    # ---------------- c28-wenyao：段 6、7、8、9、10 前半 ----------------
    ('c28-wenyao', 'C28-017', 'narrator', '二人正说话，只见丫头来请吃饭', '荣国府 · 王夫人上房', 6, 0, 7,
     ['S:baoyu:hall_entry', 'S:daiyu:guest_seat', 'S:wang:wang_host']),
    ('c28-wenyao', 'C28-018', 'wang', '大姑娘，你吃那鲍太医的药可好些', '荣国府 · 王夫人上房', 6, 7, 18,
     ['E:wang:greet:1.2']),
    ('c28-wenyao', 'C28-019', 'wang', '前儿大夫说了个丸药的名字', '荣国府 · 王夫人上房', 6, 18, 26,
     ['E:wang:greet:1.2']),
    ('c28-wenyao', 'C28-020', 'baoyu', '八珍益母丸？左归？右归？', '荣国府 · 王夫人上房', 6, 26, 32,
     ['E:baoyu:greet:1.2']),
    ('c28-wenyao', 'C28-021', 'baoyu', '从来没听见有个什么金刚丸', '荣国府 · 王夫人上房', 6, 32, 40,
     ['E:baoyu:greet:1.4']),
    ('c28-wenyao', 'C28-022', 'wang', '扯你娘的臊！又欠你老子捶你了', '荣国府 · 王夫人上房', 6, 40, 51,
     ['E:wang:anger:1.2']),
    ('c28-wenyao', 'C28-023', 'baoyu', '我老子再不为这个捶我的', '荣国府 · 王夫人上房', 6, 51, 53,
     ['E:baoyu:greet:1.2']),
    ('c28-wenyao', 'C28-024', 'wang', '既有这个名儿，明儿就叫人买些来吃', '荣国府 · 王夫人上房', 7, 0, 11,
     ['E:wang:greet:1.2']),
    ('c28-wenyao', 'C28-025', 'baoyu', '当真的呢，我这个方子比别的不同', '荣国府 · 王夫人上房', 7, 11, 32,
     ['E:baoyu:greet:1.4']),
    ('c28-wenyao', 'C28-026', 'baochai', '我不知道，也没听见', '荣国府 · 王夫人上房', 7, 32, 41,
     ['E:baochai:greet:1.2']),
    ('c28-wenyao', 'C28-027', 'baoyu', '我说的倒是真话呢，倒说我撒谎', '荣国府 · 王夫人上房', 7, 41, 49,
     ['E:baoyu:anger:1.4']),
    ('c28-wenyao', 'C28-028', 'narrator', '只见林黛玉坐在宝钗身后抿著嘴笑', '荣国府 · 王夫人上房', 7, 49, 51,
     ['E:daiyu:rest:1.2']),
    ('c28-wenyao', 'C28-029', 'narrator', '凤姐因在里间屋里看著人放桌子', '荣国府 · 王夫人上房', 8, 0, 27,
     ['S:feng:hall_entry', 'E:feng:greet:1.4']),
    ('c28-wenyao', 'C28-030', 'narrator', '凤姐说一句，那宝玉念一句佛', '荣国府 · 王夫人上房', 8, 27, 42,
     ['E:baoyu:greet:1.2']),
    ('c28-wenyao', 'C28-031', 'wang', '阿弥陀佛，不当家花花的', '荣国府 · 王夫人上房', 8, 42, 49,
     ['E:wang:anger:1.2']),
    ('c28-wenyao', 'C28-032', 'baoyu', '你听见了没有，难道二姐姐也跟著我撒谎不成', '荣国府 · 王夫人上房', 9, 0, 11,
     ['E:baoyu:greet:1.2']),
    ('c28-wenyao', 'C28-033', 'baoyu', '太太不知道这原故', '荣国府 · 王夫人上房', 9, 11, 20,
     ['E:baoyu:greet:1.2']),
    ('c28-wenyao', 'C28-034', 'narrator', '只见贾母房里的丫头找宝玉林黛玉去吃饭', '荣国府 · 王夫人上房', 9, 20, 30,
     ['E:daiyu:rest:1.2']),
    ('c28-wenyao', 'C28-035', 'wang', '罢，罢，我今儿吃斋', '荣国府 · 王夫人上房', 9, 30, 37,
     ['E:wang:greet:1.2']),
    ('c28-wenyao', 'C28-036', 'baoyu', '我也跟著吃斋', '荣国府 · 王夫人上房', 9, 37, 44,
     ['E:baoyu:rest:1.2']),
    ('c28-wenyao', 'C28-037', 'baochai', '你正经去罢。吃不吃，陪著林姑娘走一趟', '荣国府 · 王夫人上房', 9, 44, 52,
     ['E:baochai:greet:1.2']),
    ('c28-wenyao', 'C28-038', 'narrator', '一时吃过饭，宝玉一则怕贾母记挂', '荣国府 · 王夫人上房', 10, 0, 8,
     ['E:baoyu:rest:1.2']),
    ('c28-wenyao', 'C28-039', 'baochai', '你叫他快吃了瞧林妹妹去罢', '荣国府 · 王夫人上房', 10, 8, 11,
     ['E:baochai:greet:1.2']),
    ('c28-wenyao', 'C28-040', 'narrator', '宝玉吃了茶，便出来，一直往西院来', '荣国府 · 王夫人上房', 10, 11, 14,
     ['M:baoyu:hall_entry>south_passage']),

    # ---------------- c28-fengyuan：段 10 中段 ----------------
    ('c28-fengyuan', 'C28-041', 'narrator', '可巧走到凤姐儿院门前', '荣国府 · 凤姐院', 10, 14, 24,
     ['S:baoyu:platform', 'S:feng:hall']),
    ('c28-fengyuan', 'C28-042', 'feng', '你来的好。进来，进来，替我写几个字儿', '荣国府 · 凤姐院', 10, 24, 39,
     ['E:feng:greet:1.4']),
    ('c28-fengyuan', 'C28-043', 'feng', '还有句话告诉你，不知你依不依', '荣国府 · 凤姐院', 10, 39, 53,
     ['E:feng:greet:1.4']),
    ('c28-fengyuan', 'C28-044', 'baoyu', '我屋里的人也多的很，姐姐喜欢谁', '荣国府 · 凤姐院', 10, 53, 58,
     ['E:baoyu:greet:1.2']),
    ('c28-fengyuan', 'C28-045', 'baoyu', '老太太叫我呢，有话等我回来罢', '荣国府 · 凤姐院', 10, 58, 65,
     ['E:baoyu:rest:1.2']),

    # ---------------- c28-caijian：段 10 后段、段 11 ----------------
    ('c28-caijian', 'C28-046', 'narrator', '说著便来至贾母这边', '荣国府 · 贾母院', 10, 65, 69,
     ['S:baoyu:hall_door', 'S:grandmother:grandmother_seat']),
    ('c28-caijian', 'C28-047', 'grandmother', '跟著你娘吃了什么好的', '荣国府 · 贾母院', 10, 67, 73,
     ['E:grandmother:greet:1.2']),
    ('c28-caijian', 'C28-048', 'grandmother', '里头屋里呢', '荣国府 · 贾母院', 10, 73, 76,
     ['E:grandmother:greet:1.2']),
    ('c28-caijian', 'C28-049', 'narrator', '宝玉进来，只见地下一个丫头吹熨斗', '荣国府 · 贾母院', 11, 0, 10,
     ['M:baoyu:hall_door>daiyu_seat', 'S:daiyu:daiyu_seat']),
    ('c28-caijian', 'C28-050', 'daiyu', '理他呢，过一会子就好了', '荣国府 · 贾母院', 11, 10, 21,
     ['E:daiyu:rest:1.2']),
    ('c28-caijian', 'C28-051', 'baochai', '妹妹越发能干了，连裁剪都会了', '荣国府 · 贾母院', 11, 21, 31,
     ['S:baochai:courtyard_center', 'E:baochai:greet:1.2']),
    ('c28-caijian', 'C28-052', 'baochai', '我告诉你个笑话儿', '荣国府 · 贾母院', 11, 31, 39,
     ['E:baochai:greet:1.2']),
    ('c28-caijian', 'C28-053', 'baoyu', '老太太要抹骨牌，正没人呢', '荣国府 · 贾母院', 11, 39, 47,
     ['E:baoyu:greet:1.2']),
    ('c28-caijian', 'C28-054', 'daiyu', '你倒是去罢，这里有老虎', '荣国府 · 贾母院', 11, 47, 56,
     ['E:daiyu:greet:1.2']),
    ('c28-caijian', 'C28-055', 'daiyu', '凭他谁叫我裁，也不管二爷的事', '荣国府 · 贾母院', 11, 56, 62,
     ['E:daiyu:anger:1.2']),
    ('c28-caijian', 'C28-056', 'daiyu', '阿弥陀佛！赶你回来，我死了也罢了', '荣国府 · 贾母院', 11, 62, 70,
     ['E:daiyu:rest:1.2']),

    # ---------------- c28-chumen：段 12 前半 ----------------
    ('c28-chumen', 'C28-057', 'narrator', '宝玉出来，到外面，只见焙茗说道', '荣国府 · 贾母院', 12, 0, 14,
     ['S:baoyu:passage_entry', 'S:ming_yan:outer_turn']),
    ('c28-chumen', 'C28-058', 'ming_yan', '骂的是，我也糊涂了', '荣国府 · 贾母院', 12, 14, 30,
     ['E:ming_yan:greet:1.2']),
    ('c28-chumen', 'C28-059', 'narrator', '回到书房里，宝玉换了，命人备马', '荣国府 · 贾母院', 12, 30, 37,
     ['M:baoyu:passage_entry>west_gate']),

    # ---------------- c28-fuyan：段 12 后半、段 13 ----------------
    ('c28-fuyan', 'C28-060', 'narrator', '一径到了冯紫英家门口', '冯紫英家 · 家宴厅', 12, 37, 45,
     ['S:baoyu:gate', 'S:feng_ziying:host_seat', 'S:xuepan:xuepan_seat',
      'S:jiang_yuhan:jiang_seat', 'S:yun_er:yun_seat']),
    ('c28-fuyan', 'C28-061', 'baoyu', '前儿所言幸与不幸之事', '冯紫英家 · 家宴厅', 12, 45, 57,
     ['E:baoyu:greet:1.2']),
    ('c28-fuyan', 'C28-062', 'narrator', '然后摆上酒来，依次坐定', '冯紫英家 · 家宴厅', 12, 57, 62,
     ['E:baoyu:rest:1.2']),
    ('c28-fuyan', 'C28-063', 'xuepan', '那薛蟠三杯下肚', '冯紫英家 · 家宴厅', 13, 0, 6,
     ['E:xuepan:greet:1.2']),
    ('c28-fuyan', 'C28-064', 'narrator', '云儿听说，只得拿起琵琶来，唱道', '冯紫英家 · 家宴厅', 13, 6, 8,
     ['E:yun_er:rest:1.2']),

    # ---------------- c28-xingling：段 14-19 ----------------
    ('c28-xingling', 'C28-065', 'yun_er', '两个冤家，都难丢下', '冯紫英家 · 家宴厅', 14, 0, 10,
     ['E:yun_er:rest:1.6']),
    ('c28-xingling', 'C28-066', 'yun_er', '唱毕笑道：你喝一坛子罢了', '冯紫英家 · 家宴厅', 15, 0, 6,
     ['E:yun_er:greet:1.2']),
    ('c28-xingling', 'C28-067', 'baoyu', '听我说来：如此滥饮', '冯紫英家 · 家宴厅', 16, 0, 12,
     ['E:baoyu:greet:1.4']),
    ('c28-xingling', 'C28-068', 'baoyu', '如今要说悲、愁、喜、乐四字', '冯紫英家 · 家宴厅', 16, 12, 32,
     ['E:baoyu:greet:1.6']),
    ('c28-xingling', 'C28-069', 'yun_er', '怕什么？这还亏你天天吃酒呢', '冯紫英家 · 家宴厅', 16, 32, 50,
     ['E:yun_er:greet:1.4']),
    ('c28-xingling', 'C28-070', 'baoyu', '女儿悲，青春已大守空闺', '冯紫英家 · 家宴厅', 16, 50, 59,
     ['E:baoyu:greet:1.4']),
    ('c28-xingling', 'C28-071', 'xuepan', '薛蟠独扬著脸摇头说：不好，该罚', '冯紫英家 · 家宴厅', 17, 0, 11,
     ['E:xuepan:anger:1.2']),
    ('c28-xingling', 'C28-072', 'narrator', '于是拿琵琶听宝玉唱道', '冯紫英家 · 家宴厅', 17, 11, 17,
     ['E:baoyu:rest:1.2']),
    ('c28-xingling', 'C28-073', 'baoyu', '滴不尽相思血泪抛红豆', '冯紫英家 · 家宴厅', 18, 0, 11,
     ['E:baoyu:rest:1.8']),
    ('c28-xingling', 'C28-074', 'baoyu', '唱完，大家齐声喝彩', '冯紫英家 · 家宴厅', 19, 0, 8,
     ['E:baoyu:greet:1.2']),

    # ---------------- c28-zhongling：段 20-29 ----------------
    ('c28-zhongling', 'C28-075', 'feng_ziying', '下该冯紫英，说道：女儿悲', '冯紫英家 · 家宴厅', 20, 0, 13,
     ['E:feng_ziying:greet:1.4']),
    ('c28-zhongling', 'C28-076', 'feng_ziying', '你是个可人，你是个多情', '冯紫英家 · 家宴厅', 21, 0, 7,
     ['E:feng_ziying:rest:1.4']),
    ('c28-zhongling', 'C28-077', 'feng_ziying', '鸡声茅店月。令完，下该云儿', '冯紫英家 · 家宴厅', 22, 0, 6,
     ['E:feng_ziying:greet:1.2']),
    ('c28-zhongling', 'C28-078', 'yun_er', '云儿便说道：女儿悲，将来终身指靠谁', '冯紫英家 · 家宴厅', 23, 0, 10,
     ['E:yun_er:greet:1.2']),
    ('c28-zhongling', 'C28-079', 'yun_er', '女儿愁，妈妈打骂何时休', '冯紫英家 · 家宴厅', 23, 10, 18,
     ['E:yun_er:greet:1.2']),
    ('c28-zhongling', 'C28-080', 'xuepan', '没耳性，再不许说了', '冯紫英家 · 家宴厅', 23, 18, 22,
     ['E:xuepan:greet:1.2']),
    ('c28-zhongling', 'C28-081', 'yun_er', '女儿喜，情郎不舍还家里', '冯紫英家 · 家宴厅', 23, 22, 29,
     ['E:yun_er:greet:1.2']),
    ('c28-zhongling', 'C28-082', 'yun_er', '荳蔻开花三月三', '冯紫英家 · 家宴厅', 24, 0, 6,
     ['E:yun_er:rest:1.4']),
    ('c28-zhongling', 'C28-083', 'yun_er', '桃之夭夭。令完了，下该薛蟠', '冯紫英家 · 家宴厅', 25, 0, 6,
     ['E:yun_er:greet:1.2']),
    ('c28-zhongling', 'C28-084', 'xuepan', '我可要说了：女儿悲——', '冯紫英家 · 家宴厅', 26, 0, 14,
     ['E:xuepan:greet:1.2']),
    ('c28-zhongling', 'C28-085', 'xuepan', '一个女儿嫁了汉子，要当忘八', '冯紫英家 · 家宴厅', 26, 14, 24,
     ['E:xuepan:greet:1.2']),
    ('c28-zhongling', 'C28-086', 'xuepan', '女儿愁——', '冯紫英家 · 家宴厅', 26, 24, 32,
     ['E:xuepan:greet:1.2']),
    ('c28-zhongling', 'C28-087', 'baoyu', '押韵就好', '冯紫英家 · 家宴厅', 26, 32, 43,
     ['E:baoyu:greet:1.2']),
    ('c28-zhongling', 'C28-088', 'yun_er', '下两句越发难说了，我替你说罢', '冯紫英家 · 家宴厅', 26, 43, 54,
     ['E:yun_er:greet:1.2']),
    ('c28-zhongling', 'C28-089', 'xuepan', '女儿乐，一根𣬠𣬶往里戳', '冯紫英家 · 家宴厅', 26, 54, 65,
     ['E:xuepan:anger:1.2']),
    ('c28-zhongling', 'C28-090', 'xuepan', '一个蚊子哼哼哼', '冯紫英家 · 家宴厅', 26, 65, 76,
     ['E:xuepan:greet:1.2']),
    ('c28-zhongling', 'C28-091', 'narrator', '众人都道：免了罢，免了罢', '冯紫英家 · 家宴厅', 26, 76, 87,
     ['E:xuepan:rest:1.2']),
    ('c28-zhongling', 'C28-092', 'jiang_yuhan', '于是蒋玉菡说道：女儿悲', '冯紫英家 · 家宴厅', 26, 87, 98,
     ['E:jiang_yuhan:greet:1.4']),
    ('c28-zhongling', 'C28-093', 'jiang_yuhan', '可喜你天生成百媚娇', '冯紫英家 · 家宴厅', 27, 0, 10,
     ['E:jiang_yuhan:rest:1.6']),
    ('c28-zhongling', 'C28-094', 'jiang_yuhan', '唱毕，饮了门杯，笑道', '冯紫英家 · 家宴厅', 28, 0, 12,
     ['E:jiang_yuhan:greet:1.2']),
    ('c28-zhongling', 'C28-095', 'narrator', '众人倒都依了，完令', '冯紫英家 · 家宴厅', 29, 0, 4,
     ['E:jiang_yuhan:rest:1.2']),
    ('c28-zhongling', 'C28-096', 'xuepan', '了不得，了不得！该罚，该罚', '冯紫英家 · 家宴厅', 29, 4, 17,
     ['E:xuepan:anger:1.2']),
    ('c28-zhongling', 'C28-097', 'xuepan', '袭人可不是宝贝是什么', '冯紫英家 · 家宴厅', 29, 17, 27,
     ['E:xuepan:greet:1.2']),
    ('c28-zhongling', 'C28-098', 'narrator', '薛蟠道：该罚，该罚', '冯紫英家 · 家宴厅', 29, 27, 37,
     ['E:jiang_yuhan:greet:1.2']),

    # ---------------- c28-qixiang：段 30 ----------------
    ('c28-qixiang', 'C28-099', 'narrator', '少刻，宝玉出席解手，蒋玉菡便随了出来', '冯紫英家 · 家宴厅', 30, 0, 9,
     ['M:baoyu:hall>corridor']),
    ('c28-qixiang', 'C28-100', 'baoyu', '闲了往我们那里去', '冯紫英家 · 家宴厅', 30, 9, 18,
     ['E:baoyu:greet:1.4']),
    ('c28-qixiang', 'C28-101', 'jiang_yuhan', '就是我的小名儿', '冯紫英家 · 家宴厅', 30, 16, 25,
     ['E:jiang_yuhan:greet:1.2']),
    ('c28-qixiang', 'C28-102', 'narrator', '向袖中取出扇子，将一个玉玦扇坠解下来', '冯紫英家 · 家宴厅', 30, 25, 41,
     ['E:baoyu:greet:1.2']),
    ('c28-qixiang', 'C28-103', 'jiang_yuhan', '这汗巾子是茜香国女国王所贡之物', '冯紫英家 · 家宴厅', 30, 41, 60,
     ['E:jiang_yuhan:greet:1.6']),
    ('c28-qixiang', 'C28-104', 'narrator', '二人方束好，只见一声大叫', '冯紫英家 · 家宴厅', 30, 60, 74,
     ['E:xuepan:anger:1.4']),

    # ---------------- c28-hanjin：段 31、32 ----------------
    ('c28-hanjin', 'C28-105', 'narrator', '宝玉回至园中，宽衣吃茶', '怡红院', 31, 0, 7,
     ['S:baoyu:baoyu_kang', 'S:xiren:xiren_kang']),
    ('c28-hanjin', 'C28-106', 'xiren', '你有了好的系裤子，把我那条还我罢', '怡红院', 31, 7, 19,
     ['E:xiren:greet:1.2']),
    ('c28-hanjin', 'C28-107', 'xiren', '我就知道又干这些事', '怡红院', 31, 19, 29,
     ['E:xiren:anger:1.4']),
    ('c28-hanjin', 'C28-108', 'baoyu', '夜里失了盗也不晓得', '怡红院', 31, 29, 41,
     ['E:baoyu:greet:1.2']),
    ('c28-hanjin', 'C28-109', 'narrator', '宝玉见他如此，只得委婉解劝了一回', '怡红院', 31, 41, 45,
     ['E:baoyu:greet:1.2']),
    ('c28-hanjin', 'C28-110', 'narrator', '过后宝玉出去，终久解下来掷在个空箱子里', '怡红院', 31, 45, 48,
     ['E:xiren:rest:1.2']),
    ('c28-hanjin', 'C28-111', 'xiren', '二奶奶打发人叫了红玉去了', '怡红院', 32, 0, 12,
     ['E:xiren:greet:1.2']),
    ('c28-hanjin', 'C28-112', 'xiren', '昨儿贵妃打发夏太监出来', '怡红院', 32, 12, 28,
     ['E:xiren:greet:1.2']),
    ('c28-hanjin', 'C28-113', 'xiren', '老太太的多著一个香如意', '怡红院', 32, 28, 50,
     ['E:xiren:greet:1.4']),
    ('c28-hanjin', 'C28-114', 'xiren', '昨儿拿出来，都是一份一份的写著签子', '怡红院', 32, 50, 60,
     ['E:xiren:greet:1.2']),
    ('c28-hanjin', 'C28-115', 'baoyu', '拿了这个到林姑娘那里去', '怡红院', 32, 60, 70,
     ['E:baoyu:greet:1.2']),

    # ---------------- c28-daiyan：段 33 ----------------
    ('c28-daiyan', 'C28-116', 'narrator', '宝玉听说，便命人收了。刚洗了脸出来', '荣国府 · 贾母院', 33, 0, 8,
     ['S:baoyu:hall_door']),
    ('c28-daiyan', 'C28-117', 'daiyu', '我没这么大福禁受', '荣国府 · 贾母院', 33, 8, 22,
     ['S:daiyu:daiyu_greet', 'E:daiyu:greet:1.2']),
    ('c28-daiyan', 'C28-118', 'daiyu', '好没意思，白白的说什么誓', '荣国府 · 贾母院', 33, 22, 37,
     ['E:daiyu:greet:1.2']),
    ('c28-daiyan', 'C28-119', 'daiyu', '你也不用说誓，我很知道你心里有妹妹', '荣国府 · 贾母院', 33, 37, 50,
     ['E:daiyu:greet:1.2']),
    ('c28-daiyan', 'C28-120', 'narrator', '只见宝钗从那边来了，二人便走开了', '荣国府 · 贾母院', 33, 50, 69,
     ['S:baochai:courtyard_center', 'E:baochai:rest:1.2']),
    ('c28-daiyan', 'C28-121', 'baoyu', '宝姐姐，我瞧瞧你的红麝串子', '荣国府 · 贾母院', 33, 69, 83,
     ['E:baoyu:greet:1.2']),
    ('c28-daiyan', 'C28-122', 'narrator', '忽然想起金玉一事来', '荣国府 · 贾母院', 33, 83, 96,
     ['E:baoyu:rest:1.4']),
    ('c28-daiyan', 'C28-123', 'baochai', '你又禁不得风吹，怎么又站在那风口里', '荣国府 · 贾母院', 33, 96, 107,
     ['E:baochai:greet:1.2']),
    ('c28-daiyan', 'C28-124', 'daiyu', '何曾不是在屋里的。只因听见天上一声叫唤', '荣国府 · 贾母院', 33, 102, 113,
     ['E:daiyu:greet:1.2']),
    ('c28-daiyan', 'C28-125', 'narrator', '将手里的帕子一甩，向宝玉脸上甩来', '荣国府 · 贾母院', 33, 113, 121,
     ['E:baoyu:anger:1.2']),
]


def _strip_punct(text: str) -> str:
    return re.sub(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\'"]', '', text)


def _title_anchor(sents, para, title, after):
    """在本段里找标题的最佳落点，返回子句号；找不到返回 None。
    after：只考虑严格大于该位置的子句，保证全局单调递增。
    """
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
    limits = []
    for i, c in enumerate(cuts):
        para = c[5]
        if i + 1 < len(cuts) and cuts[i + 1][5] == para:
            limits.append(cuts[i + 1][6])
        else:
            limits.append(len(SENTENCES[para]))
    return limits


DESIGN_NOTES = [
    ('C28-D1', 'c28-zanghua',
     '黛玉葬花、宝玉山坡恸倒、诉肺腑复用 `qinfang`（沁芳闸）',
     '底本段 1「因把些残花落瓣去掩埋」「不觉恸倒山坡之上」，段 2/3 仍在山坡往怡红院路上；'
     '第 23 回沁芳闸桃花图已有 `tomb` 花冢、`stone_seat` 山子石、`bank_west/bank_east` 坡岸。',
     '用 `tomb`/`stone_seat`/`bank_east` 锚点，不新开葬花图。'),
    ('C28-D2', 'c28-wenyao',
     '问药、配药方、凤姐作证、黛玉先走复用 `wang`（王夫人上房）',
     '底本段 6「王夫人见了林黛玉，因问道」，段 8「凤姐因在里间屋里看著人放桌子」——'
     '整段问答都在王夫人处。',
     '用 `hall_entry`/`guest_seat`/`wang_host`/`south_passage`，place 写「荣国府 · 王夫人上房」。'),
    ('C28-D3', 'c28-fengyuan',
     '凤姐院写礼单、讨红玉复用 `c6_wangchui`',
     '底本段 10「可巧走到凤姐儿院门前……替我写几个字儿」，该图 `feng_room`/`hall`/`platform` '
     '正是第 6 回凤姐院场景，语义吻合。',
     '用 `platform`（院门剔牙）与 `hall`（屋里写礼单），不新开凤姐院。'),
    ('C28-D4', 'c28-caijian',
     '贾母院里屋黛玉裁剪复用 `entry`',
     '底本段 10「来至贾母这边……贾母道：里头屋里呢」，段 11「炕上两个丫头打粉线，黛玉弯著腰拿著剪子裁什么呢」；'
     '`entry` 的 `daiyu_seat`/`hall_door`/`grandmother_seat` 覆盖此景。',
     '用 `hall_door`/`daiyu_seat`/`grandmother_seat`/`courtyard_center`。'),
    ('C28-D5', 'c28-fuyan',
     '冯紫英家家宴新建 `fengziying_home`',
     '底本段 12「一径到了冯紫英家门口，有人报与了冯紫英，出来迎接进去……然后摆上酒来，依次坐定」，'
     '段 13-30 整场家宴、唱曲、行令、廊檐下赠罗都在此地；既有 `dinner` 是贾母院晚膳、'
     '`tavern` 是村肆，语义均冲突。',
     '新建室内图 `fengziying_home`，锚点 gate/hall/table/host_seat/baoyu_seat/xuepan_seat/'
     'jiang_seat/yun_seat/singer_place/corridor。'),
    ('C28-D6', 'c28-hanjin',
     '怡红院汗巾与端午节礼复用 `yihong`',
     '底本段 31「宝玉回至园中，宽衣吃茶……睡觉时只见腰里一条血点似的大红汗巾子」，'
     '段 32 袭人逐项分说节礼，仍在怡红院；`yihong` 的 `baoyu_kang`/`xiren_kang` 正合。',
     '用 `baoyu_kang`/`xiren_kang`，不新开宝玉房。'),
    ('C28-D7', 'c28-daiyan',
     '贾母院金玉之争、红麝串、呆雁复用 `entry`',
     '底本段 33「要往贾母那里请安去……然后到了贾母这边，只见宝玉在这里呢」——'
     '结局在贾母院，黛玉蹬门槛、宝钗褪串都在此。',
     '用 `hall_door`/`daiyu_greet`/`courtyard_center`。'),
    ('C28-D8', 'c28-chumen',
     '焙茗复用既有 cast `ming_yan`（茗烟），不新增角色',
     '底本段 12 写「焙茗」，即《红楼梦》第 9 回茗烟（后改名焙茗），同一宝玉小厮；'
     'cast 已有 `ming_yan`，重复登记会造出同一人的两个身份。',
     'speaker/actor 用 `ming_yan`，正文里的「焙茗」照底本保留，报告中说明。'),
    ('C28-D9', 'c28-fuyan',
     '冯紫英、蒋玉菡（琪官）、云儿三人有实质台词，建议入 cast',
     '冯紫英是家宴主人且多次发话；蒋玉菡唱曲、赠茜香罗，是回目人物；'
     '云儿唱曲、与薛蟠打趣，贯穿整场行令。三人均为本回真正登场并有台词的角色。',
     '新 id `feng_ziying`/`jiang_yuhan`/`yun_er`（snake_case），报告中列出视觉设定，'
     '由主 agent 统一登记 cast 与美术。'),
    ('C28-D10', 'c28-xingling',
     '唱曲小厮、二门婆子、门上小厮、紫绡、夏太监、鲍太医/王大夫不入 cast',
     '唱曲小厮、踢球小厮、二门婆子、紫绡（只传话）都无独立台词或仅一句插话；'
     '夏太监、鲍太医、王大夫、珍大爷、北静王只在叙述里被点名。',
     '只在正文里保留，不 show、不注册新 cast。'),
    ('C28-D11', 'c28-xingling',
     '五支曲子作 `verbatim` 韵文节点，speaker 为唱歌角色',
     '底本段 14/18/21/24/27 是云儿、宝玉、冯紫英、云儿、蒋玉菡所唱的曲文，'
     '被 `<poem>` 包裹且无叙述；清洗标签后整段照录。',
     'speaker 分别 yun_er/baoyu/feng_ziying/yun_er/jiang_yuhan，textKind 仍为 verbatim，不改字。'),
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
                'chapter': 28,
                'paragraphLead': lead,
                'textKind': 'verbatim',
                'layer': 'present',
            },
            '_pos': (para, s_from),
        })
    return steps


def assign_scenes(steps):
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
        # 舞台连续性：只查 move——引擎只在换场景时清台，同场景可见性保持。
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
    """锚点必须在该场景 Anchors 层里存在且可通行（用项目自己的 parseTiledMap）。"""
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

    probe_path = ROOT / 'artifacts' / 'probe_walkable_tmp_c28.mjs'
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
            'id': step['id'].replace('C28-', 'C28-E'),
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
        'chapter': 28,
        'source': {
            'edition': '维基文库《紅樓夢》第 028 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第028回&action=raw',
            'retrievedAt': '2026-11-25',
            'localText': 'docs/chapter28-source.txt',
            'processing': 'MediaWiki action=raw 取回 wikitext，去模板与导航行，OpenCC 转简体；'
                         '回目行与正文之间补空行，回目自成一段；<poem>/<ref> 标签清除，曲文整段保留；正文未作增删。',
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
        print('第28回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第28回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 28})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第28回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
