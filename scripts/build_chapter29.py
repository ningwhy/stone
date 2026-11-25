#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 29 回的剧情、段落、证据数据。

第 29 回底本 `docs/chapter29-source.txt`（维基文库原文，繁体转简体，正文 23 段）。
写法沿用第 23–25 回确立的**底本切片式生成**：不手写正文，按**子句索引**切片，
正文与 `source.paragraphLead` 都是从底本切出来的；`--check` 在写盘前自校。

用法：
    python3 scripts/build_chapter29.py           # 生成
    python3 scripts/build_chapter29.py --check   # 只校验已有文件

分场（对照 docs/chapter29-production.md）：

  怡红院 → 贾母院 → 宁荣街 → 清虚观（山门 / 阶矶 / 张道士 / 楼上）
  → 潇湘馆宝黛大闹 → 贾母院「不是冤家不聚头」→ 怡红院袭人劝宝玉

新建场景只有 `qingxu_guan`（清虚观 · 打醮与看戏）：现有 `c15_tiejian`
（铁槛寺）、`c15_shuiyue`（水月庵）、`zhitong`（智通寺）都是**佛寺**，与
道观语义冲突，且都没有钟楼/阶矶/正面楼·东楼·西楼/戏台这组地点。
宝黛大闹复用第 26 回新建的 `xiaoxiang`（潇湘馆），不新建。

**一名新角色**：张道士 `zhang_daoshi`（清虚观当家道人，详见制作记录），
按规范只列报告，不登记 cast / manifest；由主 agent 统一处理。
小道士、林之孝、冯家管家娘子、贾璜/贾琼/贾萍等只在叙述里点名，不入 cast。
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter29-source.txt'
STORY = ROOT / 'design' / 'chapter29-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter29-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter29-evidence.json'

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

    本回底本句子偏长（段 4 有 132 子句、段 14 有 102 子句），一句一节点会
    把整段送礼名单或整段心理描写塞进一个节点。沿用第 23–25 回的子句级切法，
    闭合引号归到前一个子句。
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

    正文延伸到该子句所在整句的末尾（下一个句末标点之后）；下一子句以
    「“「『」开头就停（那是另一段引语的第一句，不许吞）。lead 仍取子句起点。
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
    """底本弯引号 → 「」『』，只换标点不动字。

    底本行 35 的戏名带维基内部链接标记（《[[白蛇记]]》等），那是导航 markup
    不是正文，只在**展示用正文**里去掉方括号；`paragraphLead` 仍保留底本原样，
    以满足 check_content 的 VERBATIM_BASE 逐字校验。
    """
    text = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', r'\1', text)
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
    ('c29-shoupa', '怡红院 · 手帕与怔忡', 'yihong'),
    ('c29-yuexi', '贾母院 · 凤姐约看戏', 'entry'),
    ('c29-shanglu', '宁荣街 · 车辆纷纷', 'capital'),
    ('c29-shanmen', '清虚观 · 山门与小道士', 'qingxu_guan'),
    ('c29-guanjia', '清虚观 · 阶矶与钟楼', 'qingxu_guan'),
    ('c29-zhangdao', '清虚观 · 张道士进见', 'qingxu_guan'),
    ('c29-qingan', '清虚观 · 无量寿佛与像国公', 'qingxu_guan'),
    ('c29-tiqin', '清虚观 · 提亲与回绝', 'qingxu_guan'),
    ('c29-fufu', '清虚观 · 寄名符与化布施', 'qingxu_guan'),
    ('c29-qingyu', '清虚观 · 请玉与贺物', 'qingxu_guan'),
    ('c29-loushang', '清虚观 · 正面楼拈戏', 'qingxu_guan'),
    ('c29-qilin', '清虚观 · 赤金麒麟', 'qingxu_guan'),
    ('c29-songli', '清虚观 · 送礼与执意不去', 'qingxu_guan'),
    ('c29-danao', '潇湘馆 · 宝黛大闹', 'xiaoxiang'),
    ('c29-huiyi', '贾母院 · 不是冤家不聚头', 'entry'),
    ('c29-quanbao', '怡红院 · 袭人劝宝玉', 'yihong'),
]


# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题(底本原文片段), 地点, 底本段号, 起始子句号, 结束子句号, 动作)
# ★ 起点标题是底本原文片段，align_cuts 拿它回锚底本自愈；终点由下一节点起点推导。
CUTS = [
    # ---------------- c29-shoupa：段 1 ----------------
    ('c29-shoupa', 'C29-001', 'narrator', '话说宝玉正自发怔', '大观园 · 怡红院', 1, 0, 2,
     ['S:baoyu:baoyu_outer', 'S:daiyu:window_place']),
    ('c29-shoupa', 'C29-002', 'narrator', '倒唬了一跳，问是谁', '大观园 · 怡红院', 1, 3, 5,
     ['E:baoyu:anger:1.0']),
    ('c29-shoupa', 'C29-003', 'daiyu', '不敢，是我失了手', '大观园 · 怡红院', 1, 6, 10,
     ['E:daiyu:greet:1.2']),
    ('c29-shoupa', 'C29-004', 'narrator', '宝玉揉著眼睛，待要说什么', '大观园 · 怡红院', 1, 11, 14,
     ['E:baoyu:rest:1.2']),

    # ---------------- c29-yuexi：段 2、3、4 前半 ----------------
    ('c29-yuexi', 'C29-005', 'narrator', '一时，凤姐儿来了，因说起初一日在清虚观打醮的事来', '荣国府 · 贾母院', 2, 0, 3,
     ['S:grandmother:grandmother_seat', 'S:feng:feng_meet', 'S:daiyu:daiyu_seat']),
    ('c29-yuexi', 'C29-006', 'baochai', '罢，罢，怪热的', '荣国府 · 贾母院', 2, 7, 12,
     ['E:baochai:greet:1.2']),
    ('c29-yuexi', 'C29-007', 'feng', '他们那里凉快，两边又有楼', '荣国府 · 贾母院', 2, 13, 22,
     ['E:feng:greet:1.4']),
    ('c29-yuexi', 'C29-008', 'feng', '我已经回了太太了，你们不去我去', '荣国府 · 贾母院', 2, 22, 27,
     ['E:feng:greet:1.4']),
    ('c29-yuexi', 'C29-009', 'grandmother', '既这么著，我同你去', '荣国府 · 贾母院', 3, 2, 8,
     ['E:grandmother:greet:1.4']),
    ('c29-yuexi', 'C29-010', 'grandmother', '到明儿，我在正面楼上', '荣国府 · 贾母院', 3, 10, 14,
     ['E:grandmother:greet:1.4']),
    ('c29-yuexi', 'C29-011', 'grandmother', '你也去，连你母亲也去', '荣国府 · 贾母院', 3, 18, 23,
     ['E:grandmother:greet:1.2']),
    ('c29-yuexi', 'C29-012', 'narrator', '贾母又打发人去请了薛姨妈', '荣国府 · 贾母院', 4, 0, 8,
     ['S:xueyima:xing_seat', 'S:wang:wang_seat']),
    ('c29-yuexi', 'C29-013', 'narrator', '因打发人去到园里告诉', '荣国府 · 贾母院', 4, 9, 23,
     ['E:grandmother:greet:1.2']),

    # ---------------- c29-shanglu：段 4 中段 ----------------
    ('c29-shanglu', 'C29-014', 'narrator', '单表到了初一这一日，荣国府门前车辆纷纷', '京城 · 宁荣街', 4, 23, 34,
     ['S:grandmother:rong_gate', 'S:baoyu:street_west']),
    ('c29-shanglu', 'C29-015', 'narrator', '少时，贾母等出来', '京城 · 宁荣街', 4, 34, 45,
     ['S:feng:rong_gate', 'S:daiyu:rong_gate']),
    ('c29-shanglu', 'C29-016', 'narrator', '然后贾母的丫头鸳鸯，鹦鹉，琥珀，珍珠', '京城 · 宁荣街', 4, 45, 68,
     ['S:yuan_yang:rong_gate', 'S:zijun:rong_gate', 'S:ping_er:rong_gate']),
    ('c29-shanglu', 'C29-017', 'narrator', '奶子抱著大姐儿带著巧姐儿另在一车', '京城 · 宁荣街', 4, 69, 76,
     ['E:feng:greet:1.0']),
    ('c29-shanglu', 'C29-018', 'narrator', '这个说：“我不同你在一处”', '京城 · 宁荣街', 4, 77, 84,
     ['E:daiyu:greet:1.0']),
    ('c29-shanglu', 'C29-019', 'zhou_rui', '姑娘们，这是街上，看人笑话', '京城 · 宁荣街', 4, 84, 90,
     ['S:zhou_rui:rong_gate', 'E:zhou_rui:greet:1.2']),
    ('c29-shanglu', 'C29-020', 'narrator', '前头的全副执事摆开，早已到了清虚观了', '京城 · 宁荣街', 4, 90, 95,
     ['E:baoyu:greet:1.0']),

    # ---------------- c29-shanmen：段 4 末、段 5 ----------------
    ('c29-shanmen', 'C29-021', 'narrator', '宝玉骑著马，在贾母轿前', '清虚观', 4, 92, 99,
     ['S:grandmother:street', 'S:baoyu:shanmen', 'S:feng:street']),
    ('c29-shanmen', 'C29-022', 'narrator', '贾母的轿刚至山门以内', '清虚观', 4, 99, 106,
     ['M:grandmother:street>shanmen', 'S:jia_zhen:shanmen']),
    ('c29-shanmen', 'C29-023', 'narrator', '凤姐儿知道鸳鸯等在后面', '清虚观', 4, 106, 115,
     ['M:feng:street>shanmen']),
    ('c29-shanmen', 'C29-024', 'narrator', '凤姐便一扬手，照脸一下', '清虚观', 4, 115, 119,
     ['E:feng:anger:1.6']),
    ('c29-shanmen', 'C29-025', 'feng', '野牛肏的，胡朝那里跑', '清虚观', 4, 119, 121,
     ['E:feng:anger:1.6']),
    ('c29-shanmen', 'C29-026', 'narrator', '那小道士也不顾拾烛剪，爬起来往外还要跑', '清虚观', 4, 121, 132,
     ['E:feng:anger:1.2']),
    ('c29-shanmen', 'C29-027', 'grandmother', '是怎么了？', '清虚观', 5, 0, 2,
     ['E:grandmother:greet:1.2']),
    ('c29-shanmen', 'C29-028', 'feng', '一个小道士儿，剪灯花的，没躲出去', '清虚观', 5, 5, 9,
     ['E:feng:greet:1.2']),
    ('c29-shanmen', 'C29-029', 'grandmother', '快带了那孩子来，别唬著他', '清虚观', 5, 11, 18,
     ['E:grandmother:greet:1.6']),
    ('c29-shanmen', 'C29-030', 'narrator', '便叫贾珍去好生带了来', '清虚观', 5, 19, 27,
     ['S:jia_zhen:shanmen', 'E:jia_zhen:greet:1.0']),
    ('c29-shanmen', 'C29-031', 'narrator', '这里贾母带著众人，一层一层的瞻拜观玩', '清虚观', 5, 30, 44,
     ['M:grandmother:shanmen>ermen>court', 'E:jia_zhen:greet:1.0']),

    # ---------------- c29-guanjia：段 6 ----------------
    ('c29-guanjia', 'C29-032', 'jia_zhen', '管家在那里？', '清虚观', 6, 1, 3,
     ['S:jia_zhen:steps', 'E:jia_zhen:anger:1.2']),
    ('c29-guanjia', 'C29-033', 'jia_zhen', '虽说这里地方大，今儿不承望来这么些人', '清虚观', 6, 6, 19,
     ['E:jia_zhen:greet:1.4']),
    ('c29-guanjia', 'C29-034', 'jia_zhen', '怎么不见蓉儿？', '清虚观', 6, 24, 28,
     ['S:jia_rong:bell_tower', 'E:jia_zhen:anger:1.2']),
    ('c29-guanjia', 'C29-035', 'jia_zhen', '你瞧瞧他，我这里也还没敢说热', '清虚观', 6, 29, 36,
     ['E:jia_zhen:anger:1.4']),
    ('c29-guanjia', 'C29-036', 'narrator', '那小厮便问贾蓉道：爷还不怕热', '清虚观', 6, 38, 50,
     ['E:jia_rong:anger:1.0']),
    ('c29-guanjia', 'C29-037', 'jia_zhen', '你站著作什么？还不骑了马跑到家里', '清虚观', 6, 51, 57,
     ['E:jia_zhen:anger:1.4']),
    ('c29-guanjia', 'C29-038', 'narrator', '贾蓉听说，忙跑了出来，一叠声要马', '清虚观', 6, 57, 71,
     ['M:jia_rong:bell_tower>steps', 'E:jia_rong:anger:1.2']),

    # ---------------- c29-zhangdao：段 7 ----------------
    ('c29-zhangdao', 'C29-039', 'narrator', '且说贾珍方要抽身进去', '清虚观', 7, 0, 7,
     ['S:zhang_daoshi:zhang_seat', 'S:jia_zhen:steps', 'E:zhang_daoshi:greet:1.4']),
    ('c29-zhangdao', 'C29-040', 'narrator', '贾珍知道这张道士虽然是当日荣国府国公的替身', '清虚观', 7, 11, 16,
     ['E:zhang_daoshi:greet:1.2']),
    ('c29-zhangdao', 'C29-041', 'jia_zhen', '咱们自己，你又说起这话来', '清虚观', 7, 21, 25,
     ['E:jia_zhen:greet:1.4']),
    ('c29-zhangdao', 'C29-042', 'narrator', '那张道士呵呵大笑，跟了贾珍进来', '清虚观', 7, 26, 28,
     ['M:zhang_daoshi:zhang_seat>court', 'E:zhang_daoshi:greet:1.0']),

    # ---------------- c29-qingan：段 8 ----------------
    ('c29-qingan', 'C29-043', 'narrator', '贾珍到贾母跟前，控身陪笑说', '清虚观', 8, 0, 3,
     ['M:jia_zhen:steps>court', 'E:jia_zhen:greet:1.2']),
    ('c29-qingan', 'C29-044', 'zhang_daoshi', '无量寿佛！老祖宗一向福寿安康', '清虚观', 8, 8, 12,
     ['E:zhang_daoshi:greet:1.6']),
    ('c29-qingan', 'C29-045', 'grandmother', '老神仙，你好？', '清虚观', 8, 14, 16,
     ['E:grandmother:greet:1.4']),
    ('c29-qingan', 'C29-046', 'zhang_daoshi', '托老太太万福万寿，小道也还康健', '清虚观', 8, 17, 27,
     ['E:zhang_daoshi:greet:1.4']),
    ('c29-qingan', 'C29-047', 'narrator', '一面回头叫宝玉', '清虚观', 8, 30, 34,
     ['S:baoyu:court', 'E:baoyu:greet:1.4']),
    ('c29-qingan', 'C29-048', 'grandmother', '他外头好，里头弱', '清虚观', 8, 38, 42,
     ['E:grandmother:greet:1.4']),
    ('c29-qingan', 'C29-049', 'zhang_daoshi', '我看见哥儿的这个形容身段', '清虚观', 8, 49, 54,
     ['E:zhang_daoshi:rest:1.6']),
    ('c29-qingan', 'C29-050', 'grandmother', '正是呢，我养这些儿子孙子', '清虚观', 8, 57, 61,
     ['E:grandmother:rest:1.6']),

    # ---------------- c29-tiqin：段 9 ----------------
    ('c29-tiqin', 'C29-051', 'zhang_daoshi', '当日国公爷的模样儿', '清虚观', 9, 1, 6,
     ['E:zhang_daoshi:greet:1.2']),
    ('c29-tiqin', 'C29-052', 'zhang_daoshi', '前日在一个人家看见一位小姐', '清虚观', 9, 8, 16,
     ['E:zhang_daoshi:greet:1.4']),
    ('c29-tiqin', 'C29-053', 'zhang_daoshi', '但不知老太太怎么样，小道也不敢造次', '清虚观', 9, 16, 20,
     ['E:zhang_daoshi:greet:1.2']),
    ('c29-tiqin', 'C29-054', 'grandmother', '上回有和尚说了，这孩子命里不该早娶', '清虚观', 9, 21, 24,
     ['E:grandmother:greet:1.4']),
    ('c29-tiqin', 'C29-055', 'grandmother', '便是那家子穷，不过给他几两银子罢了', '清虚观', 9, 28, 31,
     ['E:grandmother:greet:1.2']),

    # ---------------- c29-fufu：段 10 ----------------
    ('c29-fufu', 'C29-056', 'feng', '张爷爷，我们丫头的寄名符儿你也不换去', '清虚观', 10, 2, 7,
     ['S:feng:court', 'E:feng:greet:1.4']),
    ('c29-fufu', 'C29-057', 'zhang_daoshi', '你瞧，我眼花了', '清虚观', 10, 9, 18,
     ['E:zhang_daoshi:greet:1.2']),
    ('c29-fufu', 'C29-058', 'narrator', '说著跑到大殿上去', '清虚观', 10, 19, 23,
     ['M:zhang_daoshi:court>steps>hall_door>hall', 'E:zhang_daoshi:greet:1.0']),
    ('c29-fufu', 'C29-059', 'feng', '你就手里拿出来罢了，又用个盘子托著', '清虚观', 10, 25, 32,
     ['E:feng:greet:1.2']),
    ('c29-fufu', 'C29-060', 'feng', '你只顾拿出盘子来，倒唬我一跳', '清虚观', 10, 32, 37,
     ['E:feng:anger:1.2']),
    ('c29-fufu', 'C29-061', 'grandmother', '猴儿猴儿，你不怕下割舌头地狱', '清虚观', 10, 40, 47,
     ['E:grandmother:anger:1.2']),

    # ---------------- c29-qingyu：段 11、12 ----------------
    ('c29-qingyu', 'C29-062', 'zhang_daoshi', '我拿出盘子来一举两用', '清虚观', 11, 1, 4,
     ['E:zhang_daoshi:greet:1.4']),
    ('c29-qingyu', 'C29-063', 'grandmother', '既这们著，你老人家老天拔地的跑什么', '清虚观', 11, 6, 10,
     ['E:grandmother:greet:1.2']),
    ('c29-qingyu', 'C29-064', 'zhang_daoshi', '老太太不知道，看著小道是八十多岁的人', '清虚观', 11, 12, 20,
     ['E:zhang_daoshi:greet:1.2']),
    ('c29-qingyu', 'C29-065', 'narrator', '便命宝玉摘下通灵玉来，放在盘内', '清虚观', 11, 21, 26,
     ['E:baoyu:greet:1.4']),
    ('c29-qingyu', 'C29-066', 'narrator', '这里贾母与众人各处游玩了一回，方去上楼', '清虚观', 12, 0, 2,
     ['M:grandmother:court>main_tower', 'E:grandmother:rest:1.2']),
    ('c29-qingyu', 'C29-067', 'zhang_daoshi', '众人托小道的福，见了哥儿的玉', '清虚观', 12, 5, 14,
     ['M:zhang_daoshi:hall>steps>court>main_tower', 'E:zhang_daoshi:greet:1.4']),
    ('c29-qingyu', 'C29-068', 'narrator', '只见也有金璜，也有玉玦', '清虚观', 12, 17, 24,
     ['E:grandmother:greet:1.2']),
    ('c29-qingyu', 'C29-069', 'grandmother', '你也胡闹。他们出家人是那里来的', '清虚观', 12, 24, 28,
     ['E:grandmother:anger:1.2']),
    ('c29-qingyu', 'C29-070', 'zhang_daoshi', '这是他们一点敬心，小道也不能阻挡', '清虚观', 12, 29, 36,
     ['E:zhang_daoshi:greet:1.2']),
    ('c29-qingyu', 'C29-071', 'baoyu', '老太太，张爷爷既这么说，又推辞不得', '清虚观', 12, 37, 55,
     ['E:baoyu:greet:1.4']),
    ('c29-qingyu', 'C29-072', 'narrator', '宝玉听说，便命收下，等晚间拿钱施舍罢了', '清虚观', 12, 55, 60,
     ['E:baoyu:rest:1.2', 'H:zhang_daoshi']),

    # ---------------- c29-loushang：段 13 ----------------
    ('c29-loushang', 'C29-073', 'narrator', '这里贾母与众人上了楼，在正面楼上归坐', '清虚观', 13, 0, 4,
     ['S:grandmother:main_tower', 'S:feng:east_tower', 'S:daiyu:main_tower',
      'S:baochai:main_tower', 'S:ping_er:west_tower']),
    ('c29-loushang', 'C29-074', 'jia_zhen', '神前拈了戏，头一本《白蛇记》', '清虚观', 13, 5, 12,
     ['S:jia_zhen:stage', 'E:jia_zhen:greet:1.2']),
    ('c29-loushang', 'C29-075', 'grandmother', '这倒是第二本上？也罢了', '清虚观', 13, 12, 17,
     ['E:grandmother:rest:1.2']),
    ('c29-loushang', 'C29-076', 'jia_zhen', '第三本是《南柯梦》', '清虚观', 13, 17, 21,
     ['E:jia_zhen:greet:1.2']),
    ('c29-loushang', 'C29-077', 'narrator', '贾珍退了下来，至外边预备著申表，焚钱粮，开戏', '清虚观', 13, 21, 26,
     ['M:jia_zhen:stage>steps', 'E:jia_zhen:greet:1.0']),

    # ---------------- c29-qilin：段 14 前半 ----------------
    ('c29-qilin', 'C29-078', 'narrator', '且说宝玉在楼上，坐在贾母旁边', '清虚观', 14, 0, 5,
     ['S:baoyu:main_tower', 'E:baoyu:greet:1.2']),
    ('c29-qilin', 'C29-079', 'narrator', '贾母因看见有个赤金点翠的麒麟', '清虚观', 14, 6, 9,
     ['E:grandmother:greet:1.2']),
    ('c29-qilin', 'C29-080', 'baochai', '史大妹妹有一个，比这个小些', '清虚观', 14, 10, 14,
     ['E:baochai:greet:1.2']),
    ('c29-qilin', 'C29-081', 'tanchun', '宝姐姐有心，不管什么他都记得', '清虚观', 14, 18, 21,
     ['E:tanchun:greet:1.2']),
    ('c29-qilin', 'C29-082', 'daiyu', '他在别的上还有限', '清虚观', 14, 21, 25,
     ['E:daiyu:anger:1.2']),
    ('c29-qilin', 'C29-083', 'narrator', '宝玉听见史湘云有这件东西', '清虚观', 14, 26, 35,
     ['E:baoyu:greet:1.4']),
    ('c29-qilin', 'C29-084', 'baoyu', '这个东西倒好顽，我替你留著', '清虚观', 14, 37, 47,
     ['E:baoyu:greet:1.4']),
    ('c29-qilin', 'C29-085', 'narrator', '刚要说话，只见贾珍贾蓉的妻子婆媳两个来了', '清虚观', 14, 48, 56,
     ['S:jia_zhen:main_tower', 'E:grandmother:greet:1.0']),

    # ---------------- c29-songli：段 14 后半 ----------------
    ('c29-songli', 'C29-086', 'narrator', '只见人报：冯将军家有人来了', '清虚观', 14, 55, 67,
     ['S:feng:main_tower', 'E:feng:greet:1.4']),
    ('c29-songli', 'C29-087', 'narrator', '只见冯家的两个管家娘子上楼来了', '清虚观', 14, 68, 76,
     ['E:feng:greet:1.2']),
    ('c29-songli', 'C29-088', 'grandmother', '又不是什么正经斋事，我们不过闲逛逛', '清虚观', 14, 77, 83,
     ['E:grandmother:anger:1.2']),
    ('c29-songli', 'C29-089', 'narrator', '因此虽看了一天戏，至下午便回来了', '清虚观', 14, 83, 89,
     ['E:grandmother:rest:1.2']),
    ('c29-songli', 'C29-090', 'narrator', '那贾母因昨日张道士提起宝玉说亲的事来', '清虚观', 14, 90, 99,
     ['E:baoyu:anger:1.2']),
    ('c29-songli', 'C29-091', 'narrator', '凤姐见不去，自己带了人去', '清虚观', 14, 99, 101,
     ['E:feng:greet:1.0']),

    # ---------------- c29-danao：段 15–20 ----------------
    ('c29-danao', 'C29-092', 'narrator', '且说宝玉因见林黛玉又病了', '大观园 · 潇湘馆', 15, 0, 4,
     ['S:daiyu:bed', 'S:baoyu:chair']),
    ('c29-danao', 'C29-093', 'daiyu', '你只管看你的戏去，在家里作什么', '大观园 · 潇湘馆', 15, 5, 8,
     ['E:daiyu:greet:1.2']),
    ('c29-danao', 'C29-094', 'narrator', '宝玉因昨日张道士提亲，心中大不受用', '大观园 · 潇湘馆', 15, 8, 20,
     ['E:baoyu:anger:1.2']),
    ('c29-danao', 'C29-095', 'baoyu', '我白认得了你。罢了，罢了', '大观园 · 潇湘馆', 15, 20, 24,
     ['E:baoyu:anger:1.4']),
    ('c29-danao', 'C29-096', 'daiyu', '我也知道白认得了我', '大观园 · 潇湘馆', 15, 24, 28,
     ['E:daiyu:anger:1.4']),
    ('c29-danao', 'C29-097', 'baoyu', '你这么说，是安心咒我天诛地灭', '大观园 · 潇湘馆', 15, 28, 38,
     ['E:baoyu:anger:1.6']),
    ('c29-danao', 'C29-098', 'daiyu', '我要安心咒你，我也天诛地灭', '大观园 · 潇湘馆', 15, 38, 51,
     ['E:daiyu:anger:1.6']),
    ('c29-danao', 'C29-099', 'narrator', '原来那宝玉自幼生成有一种下流痴病', '大观园 · 潇湘馆', 15, 52, 72,
     ['E:baoyu:rest:1.2']),
    ('c29-danao', 'C29-100', 'narrator', '即如此刻，宝玉的心内想的是', '大观园 · 潇湘馆', 15, 73, 99,
     ['E:baoyu:anger:1.4']),
    ('c29-danao', 'C29-101', 'narrator', '看来两个人原本是一个心', '大观园 · 潇湘馆', 16, 0, 3,
     ['E:baoyu:rest:1.0']),
    ('c29-danao', 'C29-102', 'narrator', '那宝玉心中又想著', '大观园 · 潇湘馆', 16, 3, 25,
     ['E:baoyu:rest:1.2']),
    ('c29-danao', 'C29-103', 'narrator', '如今只述他们外面的形容', '大观园 · 潇湘馆', 17, 0, 6,
     ['E:baoyu:anger:1.6']),
    ('c29-danao', 'C29-104', 'narrator', '便赌气向颈上抓下通灵宝玉', '大观园 · 潇湘馆', 17, 6, 15,
     ['E:baoyu:anger:2.0']),
    ('c29-danao', 'C29-105', 'daiyu', '何苦来，你摔砸那哑吧物件', '大观园 · 潇湘馆', 17, 15, 22,
     ['E:daiyu:anger:1.6']),
    ('c29-danao', 'C29-106', 'narrator', '二人闹著，紫鹃雪雁等忙来解劝', '大观园 · 潇湘馆', 17, 22, 29,
     ['S:zijun:zijun_place', 'S:xueyan:door', 'E:zijun:anger:1.2']),
    ('c29-danao', 'C29-107', 'narrator', '袭人忙赶了来，才夺了下来', '大观园 · 潇湘馆', 17, 29, 34,
     ['S:xiren:door', 'E:baoyu:anger:1.4']),
    ('c29-danao', 'C29-108', 'xiren', '你同妹妹拌嘴，不犯著砸他', '大观园 · 潇湘馆', 18, 0, 13,
     ['E:xiren:greet:1.4']),
    ('c29-danao', 'C29-109', 'narrator', '林黛玉一行哭著，一行听了这话说到自己心坎儿上来', '大观园 · 潇湘馆', 18, 13, 26,
     ['E:daiyu:anger:1.6', 'E:zijun:greet:1.4']),
    ('c29-danao', 'C29-110', 'narrator', '宝玉听了这话说到自己心坎儿上来', '大观园 · 潇湘馆', 18, 27, 41,
     ['E:baoyu:rest:1.4']),
    ('c29-danao', 'C29-111', 'narrator', '袭人见他两个哭，由不得守著宝玉也心酸起来', '大观园 · 潇湘馆', 18, 41, 57,
     ['E:xiren:rest:1.4']),
    ('c29-danao', 'C29-112', 'xiren', '你不看别的，你看看这玉上穿的穗子', '大观园 · 潇湘馆', 19, 0, 5,
     ['E:xiren:greet:1.2']),
    ('c29-danao', 'C29-113', 'narrator', '林黛玉听了，也不顾病，赶来夺过去', '大观园 · 潇湘馆', 19, 5, 15,
     ['E:daiyu:anger:1.4']),
    ('c29-danao', 'C29-114', 'baoyu', '你只管剪，我横竖不带他', '大观园 · 潇湘馆', 19, 18, 22,
     ['E:baoyu:anger:1.2']),
    ('c29-danao', 'C29-115', 'narrator', '只顾里头闹，谁知那些老婆子们见林黛玉大哭大吐', '大观园 · 潇湘馆', 20, 0, 9,
     ['E:daiyu:anger:1.2']),
    ('c29-danao', 'C29-116', 'narrator', '那贾母王夫人见他们忙忙的作一件正经事来告诉', '大观园 · 潇湘馆', 20, 9, 24,
     ['S:grandmother:gate', 'S:wang:window_out', 'E:grandmother:anger:1.4']),
    ('c29-danao', 'C29-117', 'narrator', '还是贾母带出宝玉去了，方才平服', '大观园 · 潇湘馆', 20, 25, 27,
     ['M:baoyu:door>chair', 'E:grandmother:rest:1.2']),

    # ---------------- c29-huiyi：段 21、22 前半 ----------------
    ('c29-huiyi', 'C29-118', 'narrator', '过了一日，至初三日，乃是薛蟠生日', '荣国府 · 贾母院', 21, 0, 5,
     ['S:grandmother:grandmother_seat']),
    ('c29-huiyi', 'C29-119', 'narrator', '宝玉因得罪了林黛玉，二人总未见面', '荣国府 · 贾母院', 21, 5, 11,
     ['E:baoyu:rest:1.2']),
    ('c29-huiyi', 'C29-120', 'narrator', '林黛玉不过前日中了些暑溽之气', '荣国府 · 贾母院', 21, 11, 24,
     ['E:daiyu:rest:1.2']),
    ('c29-huiyi', 'C29-121', 'grandmother', '我这老冤家是那世里的孽障', '荣国府 · 贾母院', 22, 4, 16,
     ['E:grandmother:anger:1.6']),
    ('c29-huiyi', 'C29-122', 'narrator', '自己抱怨著也哭了', '荣国府 · 贾母院', 22, 16, 17,
     ['E:grandmother:rest:1.2']),

    # ---------------- c29-quanbao：段 22 后半、23 ----------------
    ('c29-quanbao', 'C29-123', 'narrator', '这话传入宝林二人耳内', '大观园 · 怡红院', 22, 17, 20,
     ['S:baoyu:baoyu_kang']),
    ('c29-quanbao', 'C29-124', 'narrator', '如今忽然得了这句话，好似参禅的一般', '大观园 · 怡红院', 22, 20, 23,
     ['E:baoyu:rest:1.4']),
    ('c29-quanbao', 'C29-125', 'narrator', '虽不曾会面，然一个在潇湘馆临风洒泪', '大观园 · 怡红院', 22, 23, 27,
     ['E:baoyu:rest:1.4']),
    ('c29-quanbao', 'C29-126', 'xiren', '千万不是，都是你的不是', '大观园 · 怡红院', 23, 0, 14,
     ['S:xiren:xiren_kang', 'E:xiren:greet:1.4']),
    ('c29-quanbao', 'C29-127', 'narrator', '那宝玉听见了不知依与不依，要知端详', '大观园 · 怡红院', 23, 20, 23,
     ['E:baoyu:rest:1.2']),
]


# 起点用「标题回锚底本」自愈，终点由下一节点起点推导（沿用第 24、25 回）。
def _strip_punct(text: str) -> str:
    return re.sub(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\'"]', '', text)


def _title_anchor(sents, para, title, after):
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
    ('C29-D1', 'c29-shanmen',
     '清虚观打醮新建 `qingxu_guan`，不复用三张佛寺图',
     '底本明写张道士、道录司、寄名符、传道法器，是一座道观；'
     '现有 `c15_tiejian`（铁槛寺）、`c15_shuiyue`（水月庵）、`zhitong`（智通寺）均为佛寺，'
     '且都没有「钟楼／阶矶／正面楼·东楼·西楼／戏台」这组打醮看戏地点。',
     '新建 13 锚点（street/shanmen/ermen/court/main_tower/east_tower/west_tower/'
     'stage/zhang_seat/bell_tower/steps/hall_door/hall）。'),
    ('C29-D2', 'c29-danao',
     '宝黛大闹复用 `xiaoxiang`（潇湘馆），不再以怡红院替代',
     '底本段 15 宝玉「见林黛玉又病了……不时来问」、段 20 贾母王夫人「进园来瞧他兄妹」，'
     '段 22 明写「一个在潇湘馆临风洒泪，一个在怡红院对月长吁」——大闹一场在黛玉养病的潇湘馆。'
     '本项目已有第 26 回新建的 `xiaoxiang`（8 锚点全通），语义吻合，直接复用。',
     '用 `bed`/`chair`/`zijun_place`/`door`/`gate`/`window_out` 等锚点；'
     '开篇甩手帕与结尾袭人劝宝玉仍在 `yihong`（怡红院）。'),
    ('C29-D3', 'c29-yuexi',
     '凤姐约戏、请薛姨妈、贾母抱怨「不是冤家不聚头」复用 `entry`',
     '底本段 2「凤姐儿来了，因说起初一日在清虚观打醮的事」，段 22 贾母抱怨，'
     '都在贾母处。',
     '用 `grandmother_seat`/`feng_meet`/`daiyu_seat`/`xing_seat`/`wang_seat`，不新开贾母院图。'),
    ('C29-D4', 'c29-shanglu',
     '初一出门、车辆纷纷复用 `capital`（宁荣街）',
     '底本段 4「荣国府门前车辆纷纷，人马簇簇」「周瑞家的走来过去的说道：姑娘们，这是街上」。',
     '用 `rong_gate`/`street_west`，让宝玉骑马与贾母轿同框。'),
    ('C29-D5', 'c29-zhangdao',
     '张道士是唯一新角色 `zhang_daoshi`，只列报告不登记',
     '底本段 7–12 他是清虚观当家道人、国公替身、掌道录司印，有大段台词，'
     '必须作为可见角色登场。',
     '视觉设定见制作记录与报告；由主 agent 统一登记 cast / manifest / 美术。'),
    ('C29-D6', 'c29-shanmen',
     '小道士、林之孝、冯家管家娘子、贾璜/贾琼/贾萍不入 cast',
     '这些人物只在叙述里被点名或只有一两句传话，按第 24、25 回'
     '「提及不登场」先例处理。',
     '只在正文里保留，不 show、不注册新 cast；贾珍的斥责由贾珍自己演出。'),
    ('C29-D7', 'c29-loushang',
     '神前拈的三本戏《白蛇记》《满床笏》《南柯梦》照录',
     '底本段 13 贾珍报戏名、贾母问故事，三本皆有原文。',
     'speaker 分别用 jia_zhen / grandmother，正文逐字来自底本，不改戏名。'),
    ('C29-D8', 'c29-guanjia',
     '钟楼无专用美术资产，用标牌与场景陈设交代',
     'manifest 里没有 bell/tower 类资产；底本只说贾蓉「从钟楼里跑了出来」。',
     '以 `bell_tower` 锚点 + 地图 Labels「钟楼」点明地点，不生造资产。'),
    ('C29-D9', 'c29-quanbao',
     '结尾「人居两地，情发一心」为画外叙述，黛玉不 show',
     '底本段 22 明写二人「虽不曾会面」，一个在潇湘馆、一个在怡红院。',
     '该节点只 show 宝玉在 `baoyu_kang`，黛玉只用叙述，避免把两人同台。'),
    ('C29-D10', 'c29-danao',
     '宝玉摔玉、砸玉用既有 `anger` effect，不发明新 kind',
     '底本段 17「抓下通灵宝玉，咬牙恨命往地下一摔」；'
     'effect.kind 合法值仅 jade/greet/rest/idle/anger（第 25 回踩过 joy 的坑）。',
     '用 `E:baoyu:anger:2.0` 表达高潮，不改运行时类型与校验。'),
    ('C29-D11', 'c29-songli',
     '送礼名单与丫鬟名单只择要 show，避免满台',
     '底本段 4、14 罗列数十名丫鬟与送礼人家，逐一点名会把舞台塞满。',
     '只 show 已登记且有戏份的鸳鸯/紫鹃/平儿/凤姐等，其余留在正文里。'),
    ('C29-D12', 'c29-qingyu',
     '寄名符、传道法器、通灵玉均作为叙述道具，不新增角色',
     '底本段 10–12 的茶盘、蟒袱子、金璜玉玦是物件，无台词。',
     '用旁白节点照录，focus 落在 `court`/`main_tower`，不 show 道具。'),
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
                'chapter': 29,
                'paragraphLead': lead,
                'textKind': 'verbatim',
                'layer': 'present',
            },
            '_pos': (para, s_from),
        })
    return steps


def assign_scenes(steps):
    """定场景与 focus（按场景记 last_focus，focus 取锚点名）。"""
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
        # 舞台连续性：同场景 show 过才可见，只查 move。
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

    # ★ 五个 agent 并行，探针文件名带回号，避免互相覆盖。
    probe_path = ROOT / 'artifacts' / 'probe_walkable_tmp_c29.mjs'
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
            'id': step['id'].replace('C29-', 'C29-E'),
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
        'chapter': 29,
        'source': {
            'edition': '维基文库《紅樓夢》第 029 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第029回&action=raw',
            'retrievedAt': '2026-11-25',
            'localText': 'docs/chapter29-source.txt',
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
        print('第29回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1
    if '--check' in sys.argv:
        print(f'第29回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0
    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 29})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第29回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
