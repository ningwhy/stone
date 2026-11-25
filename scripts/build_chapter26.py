#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 26 回的剧情、段落、证据数据。

第 26 回底本是维基文库原文全文（docs/chapter26-source.txt，程乙本）。
写法沿用第 25 回模板：**正文与 paragraphLead 都从底本切片**，
按**子句索引**切片，起点用「标题回锚底本」自愈，终点由下一个节点起点推导。

用法：
    python3 scripts/build_chapter26.py            # 生成
    python3 scripts/build_chapter26.py --check    # 只校验已有文件

**本回底本的一条重要事实**（见 DESIGN_NOTES C26-D11）：
后半「薛蟠书房」一段只有冯紫英到场、饮两杯、说「不幸之幸」后执手而去，
**没有脂本第二十八回才有的蒋玉菡/云儿饮酒唱曲**。不凭印象补写。

场景复用/新建：
  怡红院 yihong（红玉佳蕙、贾芸见宝玉、坠儿传帕、宝玉出逛、宝钗、晴雯不开门）
  沁芳 qinfang（李嬷嬷、蜂腰桥四目相对）
  荣府 entry（老爷叫宝玉、焙茗二门等候）
  梨香院 c4_lixiang（薛蟠书房：寿礼、唐寅、冯紫英）
  **新建 xiaoxiang**（潇湘馆：回目明写，现有图无潇湘馆专图）

**四名新角色**（只在本脚本里用 snake_case id，cast/美术由主 agent 登记）：
  佳蕙 jiahui / 坠儿 zhuer / 晴雯 qingwen / 冯紫英 feng_ziying
焙茗即第 9 回的茗烟，沿用已有 id `ming_yan`，不另立。
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter26-source.txt'
STORY = ROOT / 'design' / 'chapter26-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter26-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter26-evidence.json'

QUOTE_MAP = {c: '"' for c in '“”「」『』‘’'}


def normalize(text: str) -> str:
    return ''.join(QUOTE_MAP.get(c, c) for c in text)


def load_base():
    raw = BASE.read_text(encoding='utf-8')
    raw = re.sub(r'<section(?:begin|end)="[^"]*"\s*/>', '', raw)
    # 本回底本两首诗带 <poem> 标记；与第 25 回的无标记诗歌统一，剥掉标签不动正文。
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
    """按子句切分：句末标点（。！？）与句中标点（；，：、）都算断点。

    本回底本句子偏长（怡红院景、薛蟠寿礼、晴雯不开门一大段都是长句），
    子句级切法才能保住节奏。闭合引号归到前一个子句。
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

    正文延伸到该子句所在整句的末尾（下一个句末标点之后）；
    但下一子句以「“「『」开头就是另一段引语的第一句，不许吞。
    lead 仍取子句起点——它是正文前缀，且能在底本逐字查到。
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
    ('c26-hongyu', '怡红院 · 红玉与佳蕙', 'yihong'),
    ('c26-yangzi', '怡红院 · 描花样与取笔', 'yihong'),
    ('c26-qinfang', '沁芳亭 · 李嬷嬷说云哥儿', 'qinfang'),
    ('c26-fengyao', '蜂腰桥 · 四目相对', 'qinfang'),
    ('c26-yihong', '怡红院 · 贾芸见宝玉', 'yihong'),
    ('c26-shoupa', '怡红院外 · 坠儿传帕', 'yihong'),
    ('c26-chuguang', '怡红院 · 宝玉出逛与贾兰射鹿', 'yihong'),
    ('c26-xiaoxiang', '潇湘馆 · 春困发幽情', 'xiaoxiang'),
    ('c26-jiaozheng', '荣府二门 · 老爷叫宝玉', 'entry'),
    ('c26-xuepan', '薛蟠书房 · 寿礼与唐寅', 'c4_lixiang'),
    ('c26-fengziying', '薛蟠书房 · 冯紫英赴宴', 'c4_lixiang'),
    ('c26-baochai', '怡红院 · 宝钗说新鲜', 'yihong'),
    ('c26-bumen', '怡红院门外 · 晴雯不开门', 'yihong'),
]


# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题(底本原文片段), 地点, 底本段号, 起始子句号, 结束子句号, 动作)
CUTS = [
    # ---------------- c26-hongyu：段 1、2、3 ----------------
    ('c26-hongyu', 'C26-001', 'narrator', '话说宝玉养过了三十三天之后', '大观园 · 怡红院', 1, 0, 5,
     ['S:xiaohong:outer_room']),
    ('c26-hongyu', 'C26-002', 'narrator', '且说近日宝玉病的时节', '大观园 · 怡红院', 1, 5, 11,
     ['S:jia_yun:yard']),
    ('c26-hongyu', 'C26-003', 'narrator', '那红玉见贾芸手里拿的手帕子', '大观园 · 怡红院', 1, 11, 18,
     ['E:xiaohong:rest:1.4']),
    ('c26-hongyu', 'C26-004', 'narrator', '忽听窗外问道', '大观园 · 怡红院', 1, 23, 34,
     ['S:jiahui:window_place']),
    ('c26-hongyu', 'C26-005', 'jiahui', '我好造化', '大观园 · 怡红院', 1, 34, 44,
     ['M:jiahui:window_place>outer_room', 'E:jiahui:greet:1.2']),
    ('c26-hongyu', 'C26-006', 'narrator', '便把手帕子打开', '大观园 · 怡红院', 1, 44, 47,
     ['E:xiaohong:greet:1.2']),
    ('c26-hongyu', 'C26-007', 'jiahui', '你这一程子心里到底觉怎么样', '大观园 · 怡红院', 2, 1, 10,
     ['E:jiahui:greet:1.2']),
    ('c26-hongyu', 'C26-008', 'jiahui', '我想起来了，林姑娘生的弱', '大观园 · 怡红院', 2, 11, 19,
     ['E:jiahui:greet:1.2']),
    ('c26-hongyu', 'C26-009', 'jiahui', '你这也不是个长法儿', '大观园 · 怡红院', 2, 20, 26,
     ['E:jiahui:greet:1.2']),
    ('c26-hongyu', 'C26-010', 'xiaohong', '怕什么，还不如早些儿死了倒干净', '大观园 · 怡红院', 2, 24, 26,
     ['E:xiaohong:anger:1.6']),
    ('c26-hongyu', 'C26-011', 'jiahui', '好好的，怎么说这些话', '大观园 · 怡红院', 2, 28, 30,
     ['E:jiahui:greet:1.2']),
    ('c26-hongyu', 'C26-012', 'xiaohong', '你那里知道我心里的事', '大观园 · 怡红院', 2, 31, 31,
     ['E:xiaohong:rest:1.4']),
    ('c26-hongyu', 'C26-013', 'jiahui', '可也怨不得，这个地方难站', '大观园 · 怡红院', 3, 2, 14,
     ['E:jiahui:anger:1.6']),
    ('c26-hongyu', 'C26-014', 'jiahui', '袭人那怕他得十分儿', '大观园 · 怡红院', 3, 14, 22,
     ['E:jiahui:greet:1.2']),
    ('c26-hongyu', 'C26-015', 'jiahui', '可气晴雯，绮霰他们这几个', '大观园 · 怡红院', 3, 22, 28,
     ['E:jiahui:anger:1.6']),
    ('c26-hongyu', 'C26-016', 'xiaohong', '也不犯著气他们', '大观园 · 怡红院', 3, 29, 37,
     ['E:xiaohong:greet:1.2']),
    ('c26-hongyu', 'C26-017', 'narrator', '这两句话不觉感动了佳蕙的心肠', '大观园 · 怡红院', 3, 37, 41,
     ['E:jiahui:rest:1.4']),
    ('c26-hongyu', 'C26-018', 'jiahui', '你这话说的却是', '大观园 · 怡红院', 3, 41, 46,
     ['E:jiahui:greet:1.2']),

    # ---------------- c26-yangzi：段 4 前半 ----------------
    ('c26-yangzi', 'C26-019', 'narrator', '红玉听了冷笑了两声', '大观园 · 怡红院', 4, 0, 9,
     ['E:xiaohong:anger:1.6']),
    ('c26-yangzi', 'C26-020', 'narrator', '红玉便赌气把那样子掷在一边', '大观园 · 怡红院', 4, 17, 29,
     ['E:xiaohong:anger:1.6']),
    ('c26-yangzi', 'C26-021', 'narrator', '便向佳惠道', '大观园 · 怡红院', 4, 29, 40,
     ['E:jiahui:greet:1.2']),
    ('c26-yangzi', 'C26-022', 'narrator', '说著，自己便出房来', '大观园 · 怡红院', 4, 40, 44,
     ['M:xiaohong:outer_room>gate']),

    # ---------------- c26-qinfang：段 4 后半 ----------------
    ('c26-qinfang', 'C26-023', 'narrator', '刚至沁芳亭畔', '大观园 · 沁芳亭', 4, 44, 50,
     ['S:xiaohong:bank_west', 'S:nurse_li:bridge_head']),
    ('c26-qinfang', 'C26-024', 'nurse_li', '你说说，好好的又看上了那个种树的', '大观园 · 沁芳亭', 4, 50, 56,
     ['E:nurse_li:anger:1.6']),
    ('c26-qinfang', 'C26-025', 'xiaohong', '你老人家当真的就依了他去叫了', '大观园 · 沁芳亭', 4, 56, 63,
     ['E:xiaohong:greet:1.2']),
    ('c26-qinfang', 'C26-026', 'nurse_li', '他又不痴，为什么不进来', '大观园 · 沁芳亭', 4, 63, 66,
     ['E:nurse_li:greet:1.2']),
    ('c26-qinfang', 'C26-027', 'xiaohong', '既是进来，你老人家该同他一齐来', '大观园 · 沁芳亭', 4, 66, 71,
     ['E:xiaohong:greet:1.2']),
    ('c26-qinfang', 'C26-028', 'nurse_li', '我有那样工夫和他走', '大观园 · 沁芳亭', 4, 71, 76,
     ['E:nurse_li:greet:1.2']),
    ('c26-qinfang', 'C26-029', 'narrator', '说著，拄著拐杖一径去了', '大观园 · 沁芳亭', 4, 76, 81,
     ['H:nurse_li', 'E:xiaohong:rest:1.4']),

    # ---------------- c26-fengyao：段 5 ----------------
    ('c26-fengyao', 'C26-030', 'narrator', '一时，只见一个小丫头子跑来', '大观园 · 蜂腰桥', 5, 0, 7,
     ['S:zhuer:bridge_head']),
    ('c26-fengyao', 'C26-031', 'zhuer', '叫我带进芸二爷来', '大观园 · 蜂腰桥', 5, 10, 12,
     ['E:zhuer:greet:1.2']),
    ('c26-fengyao', 'C26-032', 'narrator', '这里红玉刚走至蜂腰桥门前', '大观园 · 蜂腰桥', 5, 12, 18,
     ['S:jia_yun:bridge_mid']),
    ('c26-fengyao', 'C26-033', 'narrator', '四目恰相对时', '大观园 · 蜂腰桥', 5, 18, 22,
     ['E:xiaohong:greet:1.2']),

    # ---------------- c26-yihong：段 6、7、8 ----------------
    ('c26-yihong', 'C26-034', 'narrator', '这里贾芸随著坠儿', '大观园 · 怡红院', 6, 0, 8,
     ['S:jia_yun:gate', 'S:zhuer:gate']),
    ('c26-yihong', 'C26-035', 'narrator', '一溜回廊上吊著各色笼子', '大观园 · 怡红院', 6, 8, 18,
     ['E:jia_yun:greet:1.2']),
    ('c26-yihong', 'C26-036', 'narrator', '正想著，只听里面隔著纱窗子笑说道', '大观园 · 怡红院', 6, 18, 28,
     ['M:jia_yun:gate>outer_room', 'S:baoyu:inner_room']),
    ('c26-yihong', 'C26-037', 'narrator', '一回头，只见左边立著一架大穿衣镜', '大观园 · 怡红院', 6, 28, 46,
     ['M:baoyu:inner_room>baoyu_kang', 'M:jia_yun:outer_room>inner_room']),
    ('c26-yihong', 'C26-038', 'baoyu', '只从那个月见了你', '大观园 · 怡红院', 6, 46, 51,
     ['E:baoyu:greet:1.2']),
    ('c26-yihong', 'C26-039', 'jia_yun', '总是我没福', '大观园 · 怡红院', 6, 51, 55,
     ['E:jia_yun:greet:1.2']),
    ('c26-yihong', 'C26-040', 'baoyu', '大好了。我倒听见说你辛苦了好几天', '大观园 · 怡红院', 6, 56, 58,
     ['E:baoyu:greet:1.2']),
    ('c26-yihong', 'C26-041', 'jia_yun', '辛苦也是该当的', '大观园 · 怡红院', 6, 58, 62,
     ['E:jia_yun:greet:1.2']),
    ('c26-yihong', 'C26-042', 'narrator', '说著，只见有个丫鬟端了茶来与他', '大观园 · 怡红院', 7, 0, 11,
     ['S:xiren:desk_place']),
    ('c26-yihong', 'C26-043', 'jia_yun', '姐姐怎么替我倒起茶来', '大观园 · 怡红院', 7, 17, 25,
     ['E:jia_yun:greet:1.2']),
    ('c26-yihong', 'C26-044', 'jia_yun', '虽如此说，叔叔房里姐姐们', '大观园 · 怡红院', 7, 25, 31,
     ['E:jia_yun:greet:1.2']),
    ('c26-yihong', 'C26-045', 'narrator', '那宝玉便和他说些没要紧的散话', '大观园 · 怡红院', 8, 0, 11,
     ['E:baoyu:greet:1.2']),
    ('c26-yihong', 'C26-046', 'baoyu', '你明儿闲了，只管来', '大观园 · 怡红院', 8, 13, 16,
     ['E:baoyu:greet:1.2', 'H:jia_yun', 'H:xiren']),

    # ---------------- c26-shoupa：段 9 ----------------
    ('c26-shoupa', 'C26-047', 'narrator', '出了怡红院，贾芸见四顾无人', '大观园 · 怡红院外', 9, 0, 12,
     ['S:jia_yun:yard', 'S:zhuer:yard']),
    ('c26-shoupa', 'C26-048', 'jia_yun', '才刚那个与你说话的', '大观园 · 怡红院外', 9, 12, 21,
     ['E:jia_yun:greet:1.2']),
    ('c26-shoupa', 'C26-049', 'zhuer', '他问了我好几遍', '大观园 · 怡红院外', 9, 21, 35,
     ['E:zhuer:greet:1.2']),
    ('c26-shoupa', 'C26-050', 'narrator', '原来上月贾芸进来种树之时', '大观园 · 怡红院外', 9, 35, 42,
     ['E:jia_yun:greet:1.2']),
    ('c26-shoupa', 'C26-051', 'jia_yun', '我给是给你，你若得了他的谢礼', '大观园 · 怡红院外', 9, 42, 50,
     ['E:jia_yun:greet:1.2']),
    ('c26-shoupa', 'C26-052', 'narrator', '坠儿满口里答应了', '大观园 · 怡红院外', 9, 50, 55,
     ['H:jia_yun', 'H:zhuer']),

    # ---------------- c26-chuguang：段 10、11 ----------------
    ('c26-chuguang', 'C26-053', 'narrator', '如今且说宝玉打发了贾芸去后', '大观园 · 怡红院', 10, 0, 9,
     ['S:baoyu:baoyu_kang', 'S:xiren:xiren_kang']),
    ('c26-chuguang', 'C26-054', 'baoyu', '我要去，只是舍不得你', '大观园 · 怡红院', 10, 11, 17,
     ['E:baoyu:greet:1.2']),
    ('c26-chuguang', 'C26-055', 'xiren', '你出去了就好了', '大观园 · 怡红院', 10, 21, 24,
     ['E:xiren:greet:1.2']),
    ('c26-chuguang', 'C26-056', 'narrator', '宝玉无精打采的，只得依他', '大观园 · 怡红院', 11, 0, 9,
     ['M:baoyu:baoyu_kang>yard']),
    ('c26-chuguang', 'C26-057', 'narrator', '只见贾兰在后面拿著一张小弓追了下来', '大观园 · 怡红院', 11, 9, 15,
     ['S:jia_lan:yard']),
    ('c26-chuguang', 'C26-058', 'baoyu', '你又淘气了', '大观园 · 怡红院', 11, 16, 18,
     ['E:baoyu:anger:1.6']),
    ('c26-chuguang', 'C26-059', 'jia_lan', '这会子不念书，闲著作什么', '大观园 · 怡红院', 11, 18, 22,
     ['E:jia_lan:greet:1.2']),
    ('c26-chuguang', 'C26-060', 'baoyu', '把牙栽了，那时才不演呢', '大观园 · 怡红院', 11, 22, 25,
     ['E:baoyu:greet:1.2']),

    # ---------------- c26-xiaoxiang：段 12、13、14、15 前半 ----------------
    ('c26-xiaoxiang', 'C26-061', 'narrator', '顺著脚一径来至一个院门前', '大观园 · 潇湘馆', 12, 1, 11,
     ['S:baoyu:gate']),
    ('c26-xiaoxiang', 'C26-062', 'narrator', '宝玉便将脸贴在纱窗上', '大观园 · 潇湘馆', 12, 11, 19,
     ['M:baoyu:gate>window_out']),
    ('c26-xiaoxiang', 'C26-063', 'baoyu', '为甚么每日家情思睡昏昏', '大观园 · 潇湘馆', 12, 20, 23,
     ['E:baoyu:greet:1.2']),
    ('c26-xiaoxiang', 'C26-064', 'narrator', '林黛玉自觉忘情，不觉红了脸', '大观园 · 潇湘馆', 13, 0, 11,
     ['S:daiyu:bed']),
    ('c26-xiaoxiang', 'C26-065', 'daiyu', '谁睡觉呢', '大观园 · 潇湘馆', 13, 11, 16,
     ['E:daiyu:greet:1.2']),
    ('c26-xiaoxiang', 'C26-066', 'narrator', '便叫紫鹃说', '大观园 · 潇湘馆', 13, 16, 21,
     ['S:zijun:desk_place']),
    ('c26-xiaoxiang', 'C26-067', 'daiyu', '人家睡觉，你进来作什么', '大观园 · 潇湘馆', 14, 2, 10,
     ['E:daiyu:greet:1.2']),
    ('c26-xiaoxiang', 'C26-068', 'baoyu', '你才说什么', '大观园 · 潇湘馆', 14, 10, 16,
     ['E:baoyu:greet:1.2']),
    ('c26-xiaoxiang', 'C26-069', 'narrator', '二人正说话，只见紫鹃进来', '大观园 · 潇湘馆', 15, 0, 5,
     ['E:zijun:greet:1.2']),
    ('c26-xiaoxiang', 'C26-070', 'daiyu', '别理他，你先给我舀水去罢', '大观园 · 潇湘馆', 15, 10, 12,
     ['E:daiyu:greet:1.2']),
    ('c26-xiaoxiang', 'C26-071', 'zijun', '他是客，自然先倒了茶来再舀水去', '大观园 · 潇湘馆', 15, 13, 16,
     ['E:zijun:greet:1.2']),
    ('c26-xiaoxiang', 'C26-072', 'baoyu', '好丫头，若共你多情小姐同鸳帐', '大观园 · 潇湘馆', 15, 17, 20,
     ['E:baoyu:greet:1.2']),
    ('c26-xiaoxiang', 'C26-073', 'daiyu', '二哥哥，你说什么', '大观园 · 潇湘馆', 15, 22, 26,
     ['E:daiyu:anger:1.6']),
    ('c26-xiaoxiang', 'C26-074', 'daiyu', '如今新兴的，外头听了村话来', '大观园 · 潇湘馆', 15, 27, 35,
     ['E:daiyu:anger:1.6']),
    ('c26-xiaoxiang', 'C26-075', 'baoyu', '好妹妹，我一时该死', '大观园 · 潇湘馆', 15, 38, 44,
     ['E:baoyu:anger:1.6']),

    # ---------------- c26-jiaozheng：段 15 后半 ----------------
    ('c26-jiaozheng', 'C26-076', 'narrator', '正说著，只见袭人走来说道', '荣国府 · 二门', 15, 44, 48,
     ['S:xiren:hall_door', 'S:baoyu:hall_door']),
    ('c26-jiaozheng', 'C26-077', 'narrator', '宝玉听了，不觉打了个雷的一般', '荣国府 · 二门', 15, 48, 52,
     ['E:baoyu:anger:1.6']),
    ('c26-jiaozheng', 'C26-078', 'narrator', '出园来，只见焙茗在二门前等著', '荣国府 · 二门', 15, 52, 55,
     ['S:ming_yan:passage_entry']),
    ('c26-jiaozheng', 'C26-079', 'baoyu', '你可知道叫我是为什么', '荣国府 · 二门', 15, 55, 56,
     ['E:baoyu:greet:1.2']),
    ('c26-jiaozheng', 'C26-080', 'ming_yan', '爷快出来罢', '荣国府 · 二门', 15, 57, 62,
     ['E:ming_yan:greet:1.2']),

    # ---------------- c26-xuepan：段 16 ----------------
    ('c26-xuepan', 'C26-081', 'narrator', '转过大厅，宝玉心里还自狐疑', '薛蟠书房 · 梨香院', 16, 0, 7,
     ['S:baoyu:street_gate', 'S:xuepan:front_hall']),
    ('c26-xuepan', 'C26-082', 'narrator', '宝玉怔了半天', '薛蟠书房 · 梨香院', 16, 10, 17,
     ['E:baoyu:anger:1.6']),
    ('c26-xuepan', 'C26-083', 'baoyu', '你哄我也罢了', '薛蟠书房 · 梨香院', 16, 18, 29,
     ['E:baoyu:anger:1.6']),
    ('c26-xuepan', 'C26-084', 'baoyu', '嗳，嗳，越发该死了', '薛蟠书房 · 梨香院', 16, 30, 37,
     ['E:baoyu:anger:1.6']),
    ('c26-xuepan', 'C26-085', 'xuepan', '要不是我也不敢惊动', '薛蟠书房 · 梨香院', 16, 38, 63,
     ['E:xuepan:greet:1.2']),
    ('c26-xuepan', 'C26-086', 'narrator', '一面说，一面来至他书房里', '薛蟠书房 · 梨香院', 16, 63, 78,
     ['M:baoyu:street_gate>front_hall']),
    ('c26-xuepan', 'C26-087', 'baoyu', '我的寿礼还未送来', '薛蟠书房 · 梨香院', 16, 80, 82,
     ['E:baoyu:greet:1.2']),
    ('c26-xuepan', 'C26-088', 'xuepan', '可是呢，明儿你送我什么', '薛蟠书房 · 梨香院', 16, 83, 86,
     ['E:xuepan:greet:1.2']),
    ('c26-xuepan', 'C26-089', 'baoyu', '我可有什么可送的', '薛蟠书房 · 梨香院', 16, 86, 92,
     ['E:baoyu:greet:1.2']),

    # ---------------- c26-fengziying：段 17、18 ----------------
    ('c26-fengziying', 'C26-090', 'xuepan', '你提画儿，我才想起来', '薛蟠书房 · 梨香院', 17, 1, 10,
     ['E:xuepan:greet:1.2']),
    ('c26-fengziying', 'C26-091', 'baoyu', '古今字画也都见过些', '薛蟠书房 · 梨香院', 17, 12, 19,
     ['E:baoyu:greet:1.2']),
    ('c26-fengziying', 'C26-092', 'baoyu', '别是这两字罢', '薛蟠书房 · 梨香院', 17, 24, 31,
     ['E:baoyu:greet:1.2']),
    ('c26-fengziying', 'C26-093', 'xuepan', '谁知他糖银果银的', '薛蟠书房 · 梨香院', 17, 33, 34,
     ['E:xuepan:greet:1.2']),
    ('c26-fengziying', 'C26-094', 'narrator', '正说著，小厮来回冯大爷来了', '薛蟠书房 · 梨香院', 17, 34, 39,
     ['S:feng_ziying:street_gate']),
    ('c26-fengziying', 'C26-095', 'narrator', '只见冯紫英一路说笑，已进来了', '薛蟠书房 · 梨香院', 17, 39, 43,
     ['M:feng_ziying:street_gate>front_hall']),
    ('c26-fengziying', 'C26-096', 'feng_ziying', '好呀！也不出门了', '薛蟠书房 · 梨香院', 17, 43, 47,
     ['E:feng_ziying:greet:1.2']),
    ('c26-fengziying', 'C26-097', 'feng_ziying', '家父倒也托庇康健', '薛蟠书房 · 梨香院', 17, 50, 53,
     ['E:feng_ziying:greet:1.2']),
    ('c26-fengziying', 'C26-098', 'xuepan', '这脸上又和谁挥拳的', '薛蟠书房 · 梨香院', 17, 55, 57,
     ['E:xuepan:greet:1.2']),
    ('c26-fengziying', 'C26-099', 'feng_ziying', '从那一遭把仇都尉的儿子打伤了', '薛蟠书房 · 梨香院', 17, 58, 64,
     ['E:feng_ziying:greet:1.2']),
    ('c26-fengziying', 'C26-100', 'baoyu', '怪道前儿初三四儿', '薛蟠书房 · 梨香院', 17, 70, 77,
     ['E:baoyu:greet:1.2']),
    ('c26-fengziying', 'C26-101', 'feng_ziying', '可不是家父去', '薛蟠书房 · 梨香院', 17, 77, 85,
     ['E:feng_ziying:greet:1.2']),
    ('c26-fengziying', 'C26-102', 'narrator', '薛蟠众人见他吃完了茶', '薛蟠书房 · 梨香院', 18, 0, 6,
     ['E:xuepan:greet:1.2']),
    ('c26-fengziying', 'C26-103', 'feng_ziying', '这又奇了', '薛蟠书房 · 梨香院', 18, 14, 21,
     ['E:feng_ziying:greet:1.2']),
    ('c26-fengziying', 'C26-104', 'narrator', '众人听说，只得罢了', '薛蟠书房 · 梨香院', 18, 21, 29,
     ['E:xuepan:greet:1.2']),
    ('c26-fengziying', 'C26-105', 'feng_ziying', '今儿说的也不尽兴', '薛蟠书房 · 梨香院', 18, 31, 36,
     ['E:feng_ziying:greet:1.2']),
    ('c26-fengziying', 'C26-106', 'narrator', '说著执手就走', '薛蟠书房 · 梨香院', 18, 36, 38,
     ['H:feng_ziying']),
    ('c26-fengziying', 'C26-107', 'xuepan', '越发说的人热剌剌的丢不下', '薛蟠书房 · 梨香院', 18, 38, 43,
     ['E:xuepan:greet:1.2']),
    ('c26-fengziying', 'C26-108', 'narrator', '一面说，一面出门上马去了', '薛蟠书房 · 梨香院', 18, 45, 48,
     ['H:feng_ziying']),
    ('c26-fengziying', 'C26-109', 'narrator', '众人回来，依席又饮了一回方散', '薛蟠书房 · 梨香院', 18, 48, 49,
     ['E:xuepan:rest:1.4']),

    # ---------------- c26-baochai：段 19 ----------------
    ('c26-baochai', 'C26-110', 'narrator', '宝玉回至园中', '大观园 · 怡红院', 19, 0, 7,
     ['S:baoyu:outer_room', 'S:xiren:desk_place']),
    ('c26-baochai', 'C26-111', 'xiren', '人家牵肠挂肚的等著', '大观园 · 怡红院', 19, 7, 11,
     ['E:xiren:anger:1.6']),
    ('c26-baochai', 'C26-112', 'baoyu', '我何尝不要送信儿', '大观园 · 怡红院', 19, 11, 14,
     ['E:baoyu:greet:1.2']),
    ('c26-baochai', 'C26-113', 'baochai', '偏了我们新鲜东西了', '大观园 · 怡红院', 19, 15, 20,
     ['S:baochai:baochai_place', 'E:baochai:greet:1.2']),
    ('c26-baochai', 'C26-114', 'baochai', '昨儿哥哥倒特特的请我吃', '大观园 · 怡红院', 19, 21, 30,
     ['E:baochai:greet:1.2']),

    # ---------------- c26-bumen：段 20、21、22、23、24、25 ----------------
    ('c26-bumen', 'C26-115', 'narrator', '却说那林黛玉听见贾政叫了宝玉去了', '大观园 · 怡红院门外', 20, 0, 9,
     ['S:daiyu:gate']),
    ('c26-bumen', 'C26-116', 'narrator', '刚到了沁芳桥', '大观园 · 怡红院门外', 20, 9, 15,
     ['M:daiyu:gate>yard']),
    ('c26-bumen', 'C26-117', 'narrator', '再往怡红院来，只见院门关著', '大观园 · 怡红院门外', 20, 15, 18,
     ['E:daiyu:rest:1.4']),
    ('c26-bumen', 'C26-118', 'narrator', '谁知晴雯和碧痕正拌了嘴', '大观园 · 怡红院门外', 21, 0, 5,
     ['S:qingwen:gate_step', 'S:bihen:yard']),
    ('c26-bumen', 'C26-119', 'qingwen', '有事没事跑了来坐著', '大观园 · 怡红院门外', 21, 5, 11,
     ['E:qingwen:anger:1.6']),
    ('c26-bumen', 'C26-120', 'qingwen', '都睡下了，明儿再来罢', '大观园 · 怡红院门外', 21, 11, 13,
     ['E:qingwen:anger:1.6']),
    ('c26-bumen', 'C26-121', 'daiyu', '是我，还不开么', '大观园 · 怡红院门外', 21, 19, 21,
     ['E:daiyu:greet:1.2']),
    ('c26-bumen', 'C26-122', 'qingwen', '凭你是谁，二爷吩咐的', '大观园 · 怡红院门外', 21, 23, 26,
     ['E:qingwen:anger:1.6']),
    ('c26-bumen', 'C26-123', 'narrator', '林黛玉听了，不觉气怔在门外', '大观园 · 怡红院门外', 21, 26, 39,
     ['E:daiyu:anger:1.6']),
    ('c26-bumen', 'C26-124', 'narrator', '正没主意，只听里面一阵笑语之声', '大观园 · 怡红院门外', 21, 42, 46,
     ['E:daiyu:anger:1.6']),
    ('c26-bumen', 'C26-125', 'daiyu', '必竟是宝玉恼我要告他的原故', '大观园 · 怡红院门外', 21, 49, 55,
     ['E:daiyu:anger:1.6']),
    ('c26-bumen', 'C26-126', 'narrator', '越想越伤感起来', '大观园 · 怡红院门外', 21, 55, 66,
     ['E:daiyu:anger:1.6']),
    ('c26-bumen', 'C26-127', 'narrator', '花魂默默无情绪', '大观园 · 怡红院门外', 22, 0, 3,
     ['E:daiyu:rest:1.4']),
    ('c26-bumen', 'C26-128', 'narrator', '因有一首诗道', '大观园 · 怡红院门外', 23, 0, 1,
     ['E:daiyu:rest:1.4']),
    ('c26-bumen', 'C26-129', 'narrator', '颦儿才貌世应希', '大观园 · 怡红院门外', 24, 0, 5,
     ['E:daiyu:rest:1.4']),
    ('c26-bumen', 'C26-130', 'narrator', '那林黛玉正自啼哭', '大观园 · 怡红院门外', 25, 0, 6,
     ['E:daiyu:rest:1.4']),
]


# 起点用标题回锚底本（标题常在句子中间被截断，按最长公共前缀打分），
# 终点由下一节点起点推导，段末节点吃到本段末尾。
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
    limits = []
    for i, c in enumerate(cuts):
        para = c[5]
        if i + 1 < len(cuts) and cuts[i + 1][5] == para:
            limits.append(cuts[i + 1][6])
        else:
            limits.append(len(SENTENCES[para]))
    return limits


DESIGN_NOTES = [
    ('C26-D1', 'c26-hongyu',
     '红玉与佳蕙对话、贾芸带小厮看守、描花样取笔，均在怡红院，复用 `yihong`',
     '底本段 1「红玉同众丫鬟也在这里守著宝玉」、段 4「出了怡红院，一径往宝钗院内来」，'
     '前半全在怡红院内。',
     '用 `yihong` 的 `outer_room`/`window_place`/`gate`/`yard` 锚点。'),
    ('C26-D2', 'c26-qinfang',
     '沁芳亭遇李嬷嬷、蜂腰桥四目相对，复用 `qinfang`',
     '底本段 4「刚至沁芳亭畔，只见宝玉的奶娘李嬷嬷从那边走来」，段 5「红玉刚走至蜂腰桥门前」——'
     '桥、岸、山子石与 `qinfang` 的桥/水岸吻合。',
     '用 `bank_west`/`bridge_head`/`bridge_mid` 锚点；蘅芜苑无专图，红玉一扭身去了只作叙述。'),
    ('C26-D3', 'c26-xiaoxiang',
     '潇湘馆新建 `xiaoxiang`：回目明写，现有图无潇湘馆专图',
     '底本段 12「匾上写著『潇湘馆』三字」「湘帘垂地」「一缕幽香从碧纱窗中暗暗透出」，'
     '段 13 黛玉在床上、段 15 紫鹃倒茶——是一处有床有窗有茶几的内室。'
     '现有 `daguanyuan` 只是大观园全景俯瞰、`night` 是贾母院碧纱橱，都不是大观园里的潇湘馆。',
     '新建室内图 `xiaoxiang`，8 锚点（gate/window_out/door/bed/chair/desk_place/zijun_place/nurse_place）。'),
    ('C26-D4', 'c26-jiaozheng',
     '袭人传「老爷叫你」、焙茗二门等候，复用 `entry`（荣国府 · 贾母院）',
     '底本段 15「出园来，只见焙茗在二门前等著」——二门与过厅属荣府内院动线。',
     '用 `entry` 的 `hall_door`/`passage_entry`，place 写「荣国府 · 二门」。'),
    ('C26-D5', 'c26-xuepan',
     '薛蟠书房复用 `c4_lixiang`（梨香院）：薛家住所的前厅即宴客处',
     '底本段 16「一面说，一面来至他书房里」，薛家住荣府东北角梨香院；'
     '底本未另写一处府外别业，不新开图。',
     '用 `street_gate`/`front_hall` 锚点；詹光、程日兴、胡斯来、单聘仁与唱曲小么儿只在正文里。'),
    ('C26-D6', 'c26-hongyu',
     '四名新角色只列报告，cast 与美术由主 agent 统一登记',
     '佳蕙（段 1–4 有台词）、坠儿（段 5/9 有台词）、晴雯（段 21 拒门两句）、'
     '冯紫英（段 17/18 大段对话）均不在现有 cast，按 25 回先例先以 snake_case id 写入生成器。',
     '建议 id：`jiahui` / `zhuer` / `qingwen` / `feng_ziying`；报告中附一句视觉设定。'),
    ('C26-D7', 'c26-jiaozheng',
     '焙茗即茗烟，沿用已有 cast id `ming_yan`，不另立角色',
     '第 9 回名茗烟，本回段 15/16 称焙茗，是同一小厮的别名；再造一个 id 会与既有图鉴冲突。',
     '台词与动作都用 `ming_yan`，正文保留底本「焙茗」二字不改。'),
    ('C26-D8', 'c26-xuepan',
     '只在叙述里被点名、没有独立台词的本回人物不入 cast',
     '黛玉的奶娘并两个婆子、未留头送花样的小丫头、唱曲儿的小么儿、古董行程日兴、'
     '清客詹光/程日兴/胡斯来/单聘仁、沈世兄、仇都尉之子、冯唐、云哥儿雨哥儿等。',
     '只在正文里保留，不 show、不注册新 cast。'),
    ('C26-D9', 'c26-bumen',
     '两首诗作旁白念出的 `verbatim` 韵文节点',
     '底本段 22「花魂默默无情绪，鸟梦痴痴何处惊」与段 24「颦儿才貌世应希……」无说话人，'
     '是形容黛玉之哭的贊诗；段 23「因有一首诗道」是过渡句。',
     'speaker 用 narrator，`textKind: verbatim`，只剥 `<poem>` 标记不改字。'),
    ('C26-D10', 'c26-fengziying',
     '冯紫英「面上有些青伤」是底本明写，其余外形为设计推定',
     '底本段 17「薛蟠见他面上有些青伤」「是前日打围，在铁网山教兔鹘捎一翅膀」——'
     '伤痕有据；服饰颜色底本无描写。',
     '报告中标注：「底本无服饰描写，配色为视觉设计推定」，不冒充原文。'),
    ('C26-D11', 'c26-fengziying',
     '本回底本**没有**蒋玉菡/云儿饮酒唱曲一段，不凭印象补写',
     '所用程乙本（docs/chapter26-source.txt）段 17–18 只写冯紫英到场、问安、'
     '说脸上青伤与「大不幸之中又大幸」，两次推辞后饮两大杯，便「执手就走」「出门上马去了」。'
     '蒋玉菡（琪官）与云儿唱曲见于脂本系统第二十八回，不在本回底本。',
     '严格按底本切片，不新增这两人，也不写唱曲情节。'),
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
                'chapter': 26,
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

    # 五个 agent 并行，探针文件名必须带本回号，否则互相覆盖。
    probe_path = ROOT / 'artifacts' / 'probe_walkable_tmp_c26.mjs'
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
            'id': step['id'].replace('C26-', 'C26-E'),
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
        'chapter': 26,
        'source': {
            'edition': '维基文库《紅樓夢》第 026 回（繁体原文页，程乙本整理稿）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第026回&action=raw',
            'retrievedAt': '2026-11-25',
            'localText': 'docs/chapter26-source.txt',
            'processing': 'MediaWiki action=raw 取回 wikitext，去模板与导航行，OpenCC 转简体；'
                         '剥去两处 <poem> 标记（不动诗句），回目自成一段；正文未作增删。',
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
        print('第26回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第26回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 26})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第26回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
