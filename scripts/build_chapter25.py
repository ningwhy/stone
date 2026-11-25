#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 24 回的剧情、段落、证据数据。

第 24 回底本是维基文库原文全文（docs/chapter24-source.txt），
写法沿用第 18-23 回确立的**底本切片式生成**：不手写正文，
按**子句索引**切片，正文与 source.paragraphLead 都是切出来的。

用法：
    python3 scripts/build_chapter24.py            # 生成
    python3 scripts/build_chapter24.py --check    # 只校验已有文件

这一回的两条戏（对照 docs/chapter24-production.md 的分场规划）：

  贾芸这一条 —— 卜世仁香料铺 → 醉金刚巷口 → 凤姐院外 → 绮霰斋外书房
  宝玉这一条 —— 怡红院 → 怡红院后院 → 怡红院窗下（遗帕）

第 24 回的三条新场景（scripts/build_chapter24_maps.py）：

  spice_shop  京城 · 卜世仁香料铺 —— 底本「卜世仁现开香料舖」
  ni_er_lane  京城 · 三街六巷 —— 底本「这三街六巷，凭他是谁」
  qiranzhai   荣国府 · 绮霰斋外书房 —— 底本「贾母那边仪门外绮霰斋书房里来」

**八名新角色**：贾芸、小红、倪二、卜世仁、香菱、秋纹、碧痕、鸳鸯。
贾芸在第十三回只在旁白里被提到过一次；香菱在第七、十六、二十回也只是
被提及，本回是**第一次真正登场**。

复用场景：qinfang（黛玉与香菱，本项目无潇湘馆专图）、night（宝玉房里
鸳鸯与袭人）、entry（贾母院请安）、east（贾赦院邢夫人房）、
jialian_home（贾琏院）、c6_wangchui（凤姐院外，周瑞家的在那里）、
yihong（怡红院）、capital（宁荣街，宝玉上马）。
"""
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter25-source.txt'
STORY = ROOT / 'design' / 'chapter25-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter25-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter25-evidence.json'

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

    ★ 第 24 回沿用第 23 回的子句级切法：本回底本的句子同样偏长，
      一句一节点会把凤姐整段「你倒比先越发出挑了」塞进一个节点，
      剧情节奏全丢。闭合引号归到**前**一个子句。
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

    ★ 正文会延伸到该子句所在**整句的末尾**（下一个句末标点之后）：
      读者看到的是完整句子；若停在逗号上，读起来像被拦腰砍断。
      这条口径与第 16-23 回一致（第 23 回的相邻节点正文重复率 21%，
      是本项目既有的取舍），**不单独为第 24 回换口径**。

    ★★ 但加了一条**引号边界**（第 24 回新增的净改进）：
      下一子句以「“「『」开头就是另一段引语的第一句，不许吞。
      老规则一路吃到句末标点，会把下一段引语连开头一起吞掉——
      叙述节点收在「……道：」，台词节点又从引号开始，读者重复读同一句。
      加上这条边界后，台词节点被上一节点吞掉的比例从 26% 降到 4%。

    lead 仍取子句起点——它是正文的前缀，且能在底本逐字查到
    （scripts/check_content.mjs 的 VERBATIM_BASE 会验这一条）。
    """
    sents = SENTENCES[para]
    if not (0 <= s_from < s_to <= len(sents)):
        raise ValueError(f'第 {para} 段子句号 [{s_from}, {s_to}) 越界（共 {len(sents)} 句）')
    lead = sents[s_from]
    raw = ''.join(sents[s_from:s_to])
    if extend:
        end = s_to
        while end < len(sents):
            # 边界：引号开头 = 另一段引语的第一句，不许吞
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
    """底本弯引号 → 「」『』，只换标点不动字（第 16-23 回同一读法）。"""
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
    ('c25-hongyu', '怡红院 · 红玉梦与宝玉寻', 'yihong'),
    ('c25-penh', '沁芳闸 · 借喷壶见贾芸', 'qinfang'),
    ('c25-jiahuan', '王夫人上房 · 贾环抄咒', 'wang'),
    ('c25-tang', '王夫人上房 · 烫脸与责骂', 'wang'),
    ('c25-liao', '王夫人上房 · 敷药回房', 'wang'),
    ('c25-daiyu', '怡红院 · 黛玉瞧伤', 'yihong'),
    ('c25-madaopo', '贾母院 · 马道婆劝海灯', 'entry'),
    ('c25-mou', '赵姨娘房 · 魇魔法定计', 'zhao_room'),
    ('c25-cha', '怡红院 · 吃茶打趣', 'yihong'),
    ('c25-fabing', '怡红院 · 叔嫂疯魔', 'yihong'),
    ('c25-shou', '王夫人上房 · 守病与僧道至', 'wang'),
    ('c25-sengdao', '王夫人上房 · 通灵遇双真', 'wang'),
    ('c25-jie', '王夫人上房 · 病愈与姻缘笑', 'wang'),
]


# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题(底本原文片段), 地点, 底本段号, 起始子句号, 结束子句号, 动作)
# ★ 起点标题是底本原文片段，align_cuts 会拿它回锚底本自愈；终点由下一节点起点推导。
CUTS = [
    # ---------------- c25-hongyu：段 1 ----------------
    ('c25-hongyu', 'C25-001', 'narrator', '话说红玉心神恍惚，情思缠绵', '怡红院', 1, 0, 3,
     ['S:xiaohong:outer_room']),
    ('c25-hongyu', 'C25-002', 'narrator', '忽朦胧睡去，遇见贾芸要拉他', '怡红院', 1, 3, 8,
     ['S:jia_yun:window_place']),
    ('c25-hongyu', 'C25-003', 'narrator', '唬醒过来，方知是梦', '怡红院', 1, 8, 14,
     ['E:xiaohong:rest:1.4']),
    ('c25-hongyu', 'C25-004', 'narrator', '这红玉也不梳洗，向镜中胡乱挽了一挽头发', '怡红院', 1, 14, 19,
     ['M:xiaohong:outer_room>gate']),
    ('c25-hongyu', 'C25-005', 'narrator', '谁知宝玉昨儿见了红玉，也就留了心', '怡红院', 1, 19, 28,
     ['S:baoyu:baoyu_outer']),
    ('c25-hongyu', 'C25-006', 'narrator', '一时下了窗子，隔著纱屉子，向外看的真切', '怡红院', 1, 28, 37,
     ['E:baoyu:greet:1.2']),
    ('c25-hongyu', 'C25-007', 'narrator', '宝玉便靸了鞋晃出了房门，只装著看花儿', '怡红院', 1, 37, 45,
     ['M:baoyu:baoyu_outer>yard']),
    ('c25-hongyu', 'C25-008', 'narrator', '一抬头，只见西南角上游廊底下栏杆上似有一个人倚在那里', '怡红院', 1, 45, 50,
     ['E:baoyu:greet:1.2']),
    ('c25-hongyu', 'C25-009', 'narrator', '正想著，忽见碧痕来催他洗脸', '怡红院', 1, 50, 54,
     ['S:bihen:yard', 'E:baoyu:rest:1.2']),

    # ---------------- c25-penh：段 2 ----------------
    ('c25-penh', 'C25-010', 'narrator', '却说红玉正自出神，忽见袭人招手叫他', '大观园 · 沁芳闸', 2, 0, 3,
     ['S:xiaohong:bank_west', 'S:xiren:bridge_head']),
    ('c25-penh', 'C25-011', 'xiren', '我们这里的喷壶还没有收拾了来呢', '大观园 · 沁芳闸', 2, 3, 7,
     ['E:xiren:greet:1.4']),
    ('c25-penh', 'C25-012', 'narrator', '红玉答应了，便走出来往潇湘馆去', '大观园 · 沁芳闸', 2, 7, 13,
     ['M:xiaohong:bank_west>bridge_mid']),
    ('c25-penh', 'C25-013', 'narrator', '只见山坡上高处都是拦著帏幙，方想起今儿有匠役在里头种树', '大观园 · 沁芳闸', 2, 13, 16,
     ['E:xiaohong:rest:1.2']),
    ('c25-penh', 'C25-014', 'narrator', '只见那边远远一簇人在那里掘土，贾芸正坐在那山子石上', '大观园 · 沁芳闸', 2, 16, 18,
     ['S:jia_yun:stone_seat']),
    ('c25-penh', 'C25-015', 'narrator', '红玉待要过去，又不敢过去', '大观园 · 沁芳闸', 2, 18, 22,
     ['E:xiaohong:rest:1.4']),

    # ---------------- c25-jiahuan：段 3 ----------------
    ('c25-jiahuan', 'C25-016', 'narrator', '展眼过了一日，原来次日就是王子腾夫人的寿诞', '荣国府 · 王夫人上房', 3, 0, 9,
     ['S:wang:wang_host']),
    ('c25-jiahuan', 'C25-017', 'narrator', '可巧王夫人见贾环下了学，便命他来抄个《金刚咒》唪诵唪诵', '荣国府 · 王夫人上房', 3, 9, 14,
     ['S:jia_huan:kang_edge']),
    ('c25-jiahuan', 'C25-018', 'narrator', '一时又叫彩云倒杯茶来，一时又叫玉钏儿来剪剪蜡花', '荣国府 · 王夫人上房', 3, 14, 19,
     ['E:jia_huan:greet:1.2']),
    ('c25-jiahuan', 'C25-019', 'narrator', '只有彩霞还和他合的来，倒了一钟茶来递与他', '荣国府 · 王夫人上房', 3, 19, 25,
     ['S:cai_xia:guest_seat']),
    ('c25-jiahuan', 'C25-020', 'cai_xia', '你安些分罢，何苦讨这个厌那个厌的', '荣国府 · 王夫人上房', 3, 25, 31,
     ['E:cai_xia:greet:1.4']),
    ('c25-jiahuan', 'C25-021', 'jia_huan', '我也知道了，你别哄我', '荣国府 · 王夫人上房', 3, 31, 37,
     ['E:jia_huan:anger:1.4']),
    ('c25-jiahuan', 'C25-022', 'cai_xia', '没良心的！狗咬吕洞宾，不识好人心', '荣国府 · 王夫人上房', 3, 37, 37,
     ['E:cai_xia:anger:1.4']),

    # ---------------- c25-tang：段 4、5 ----------------
    ('c25-tang', 'C25-023', 'narrator', '两人正说著，只见凤姐来了，拜见过王夫人', '荣国府 · 王夫人上房', 4, 0, 8,
     ['S:feng:hall_entry']),
    ('c25-tang', 'C25-024', 'narrator', '说了不多几句话，宝玉也来了', '荣国府 · 王夫人上房', 4, 8, 17,
     ['S:baoyu:hall_entry']),
    ('c25-tang', 'C25-025', 'narrator', '便一头滚在王夫人怀里', '荣国府 · 王夫人上房', 4, 17, 25,
     ['M:baoyu:hall_entry>wang_host']),
    ('c25-tang', 'C25-026', 'wang', '我的儿，你又吃多了酒，脸上滚热', '荣国府 · 王夫人上房', 4, 25, 29,
     ['E:wang:greet:1.4']),
    ('c25-tang', 'C25-027', 'narrator', '在王夫人身后倒下，又叫彩霞来替他拍著', '荣国府 · 王夫人上房', 4, 29, 34,
     ['E:baoyu:rest:1.2']),
    ('c25-tang', 'C25-028', 'baoyu', '好姐姐，你也理我理儿呢', '荣国府 · 王夫人上房', 4, 34, 42,
     ['E:baoyu:greet:1.4']),
    ('c25-tang', 'C25-029', 'narrator', '二人正闹著，原来贾环听的见', '荣国府 · 王夫人上房', 5, 0, 10,
     ['E:jia_huan:anger:1.4']),
    ('c25-tang', 'C25-030', 'narrator', '便要用热油烫瞎他的眼睛', '荣国府 · 王夫人上房', 5, 10, 17,
     ['E:jia_huan:anger:1.6']),
    ('c25-tang', 'C25-031', 'feng', '老三还是这么慌脚鸡似的，我说你上不得高台盘', '荣国府 · 王夫人上房', 5, 20, 25,
     ['E:feng:anger:1.4']),
    ('c25-tang', 'C25-032', 'wang', '养出这样黑心不知道理下流种子来，也不管管', '荣国府 · 王夫人上房', 5, 25, 33,
     ['S:zhao_yiniang:kang_edge', 'E:wang:anger:1.6']),

    # ---------------- c25-liao：段 6 ----------------
    ('c25-liao', 'C25-033', 'narrator', '那赵姨娘素日虽然常怀嫉妒之心', '荣国府 · 王夫人上房', 6, 0, 9,
     ['E:zhao_yiniang:rest:1.2']),
    ('c25-liao', 'C25-034', 'baoyu', '有些疼，还不妨事', '荣国府 · 王夫人上房', 6, 15, 20,
     ['E:baoyu:rest:1.4']),
    ('c25-liao', 'C25-035', 'feng', '便说是自己烫的，也要骂人为什么不小心看著', '荣国府 · 王夫人上房', 6, 20, 26,
     ['E:feng:greet:1.4']),
    ('c25-liao', 'C25-036', 'narrator', '王夫人命人好生送了宝玉回房去后', '荣国府 · 王夫人上房', 6, 26, 29,
     ['H:jia_huan', 'H:zhao_yiniang', 'M:baoyu:wang_host>hall_entry']),

    # ---------------- c25-daiyu：段 7 前半 ----------------
    ('c25-daiyu', 'C25-037', 'narrator', '林黛玉见宝玉出了一天门，就觉闷闷的', '怡红院', 7, 0, 7,
     ['S:daiyu:outer_room', 'S:baoyu:baoyu_kang']),
    ('c25-daiyu', 'C25-038', 'narrator', '只见宝玉正拿镜子照呢，左边脸上满满的敷了一脸的药', '怡红院', 7, 7, 12,
     ['E:baoyu:rest:1.2']),
    ('c25-daiyu', 'C25-039', 'narrator', '宝玉见他来了，忙把脸遮著，摇手叫他出去', '怡红院', 7, 12, 20,
     ['E:baoyu:greet:1.2']),
    ('c25-daiyu', 'C25-040', 'daiyu', '我瞧瞧烫了那里了，有什么遮著藏著的', '怡红院', 7, 20, 26,
     ['E:daiyu:greet:1.4']),
    ('c25-daiyu', 'C25-041', 'baoyu', '也不很疼，养一两日就好了', '怡红院', 7, 26, 32,
     ['E:baoyu:rest:1.2']),

    # ---------------- c25-madaopo：段 7 后半 ----------------
    ('c25-madaopo', 'C25-042', 'narrator', '过了一日，就有宝玉寄名的干娘马道婆进荣国府来请安', '荣国府 · 贾母院', 7, 32, 40,
     ['S:ma_dao_po:passage_entry', 'S:grandmother:grandmother_seat']),
    ('c25-madaopo', 'C25-043', 'narrator', '见了宝玉，唬一大跳，问起原由', '荣国府 · 贾母院', 7, 40, 49,
     ['S:baoyu:grandmother_greet', 'E:ma_dao_po:greet:1.2']),
    ('c25-madaopo', 'C25-044', 'ma_dao_po', '管保就好了，这不过是一时飞灾', '荣国府 · 贾母院', 7, 49, 60,
     ['E:ma_dao_po:greet:1.4']),
    ('c25-madaopo', 'C25-045', 'grandmother', '这有什么佛法解释没有呢', '荣国府 · 贾母院', 7, 60, 64,
     ['E:grandmother:greet:1.2']),
    ('c25-madaopo', 'C25-046', 'ma_dao_po', '西方有位大光明普照菩萨，专管照耀阴暗邪祟', '荣国府 · 贾母院', 7, 64, 73,
     ['E:ma_dao_po:greet:1.4']),
    ('c25-madaopo', 'C25-047', 'ma_dao_po', '不过除香烛供养之外，一天多添几斤香油，点上个大海灯', '荣国府 · 贾母院', 7, 73, 82,
     ['E:ma_dao_po:greet:1.4']),
    ('c25-madaopo', 'C25-048', 'ma_dao_po', '这也不拘，随施主菩萨们随心愿舍罢了', '荣国府 · 贾母院', 7, 82, 107,
     ['E:ma_dao_po:greet:1.6']),
    ('c25-madaopo', 'C25-049', 'ma_dao_po', '还有一件，若是为父母尊亲长上的，多舍些不妨', '荣国府 · 贾母院', 7, 107, 122,
     ['E:ma_dao_po:greet:1.4']),
    ('c25-madaopo', 'C25-050', 'grandmother', '既是这样说，你便一日五斤合准了', '荣国府 · 贾母院', 7, 122, 131,
     ['E:grandmother:greet:1.4']),

    # ---------------- c25-mou：段 8、9、10 ----------------
    ('c25-mou', 'C25-051', 'narrator', '说毕，那马道婆又坐了一回，便又往各院各房问安', '荣国府 · 赵姨娘房', 8, 0, 6,
     ['S:ma_dao_po:door', 'S:zhao_yiniang:kang']),
    ('c25-mou', 'C25-052', 'narrator', '马道婆因见炕上堆著些零碎绸缎湾角，赵姨娘正粘鞋呢', '荣国府 · 赵姨娘房', 8, 6, 10,
     ['E:zhao_yiniang:rest:1.2']),
    ('c25-mou', 'C25-053', 'ma_dao_po', '可是我正没了鞋面子了', '荣国府 · 赵姨娘房', 8, 10, 15,
     ['E:ma_dao_po:greet:1.2']),
    ('c25-mou', 'C25-054', 'zhao_yiniang', '你瞧瞧那里头，还有那一块是成样的', '荣国府 · 赵姨娘房', 8, 15, 25,
     ['E:zhao_yiniang:anger:1.4']),
    ('c25-mou', 'C25-055', 'zhao_yiniang', '前日我送了五百钱去，在药王跟前上供', '荣国府 · 赵姨娘房', 9, 0, 11,
     ['E:zhao_yiniang:greet:1.2']),
    ('c25-mou', 'C25-056', 'ma_dao_po', '将来熬的环哥儿大了，得个一官半职', '荣国府 · 赵姨娘房', 9, 11, 16,
     ['E:ma_dao_po:greet:1.4']),
    ('c25-mou', 'C25-057', 'zhao_yiniang', '如今就是个样儿，我们娘儿们跟的上这屋里那一个儿', '荣国府 · 赵姨娘房', 9, 16, 32,
     ['E:zhao_yiniang:anger:1.6']),
    ('c25-mou', 'C25-058', 'ma_dao_po', '可是琏二奶奶', '荣国府 · 赵姨娘房', 9, 32, 39,
     ['E:ma_dao_po:greet:1.2']),
    ('c25-mou', 'C25-059', 'zhao_yiniang', '了不得，了不得！提起这个主儿', '荣国府 · 赵姨娘房', 9, 39, 44,
     ['E:zhao_yiniang:anger:1.6']),
    ('c25-mou', 'C25-060', 'ma_dao_po', '我还用你说，难道都看不出来', '荣国府 · 赵姨娘房', 10, 0, 7,
     ['E:ma_dao_po:greet:1.4']),
    ('c25-mou', 'C25-061', 'ma_dao_po', '不是我说句造孽的话，你们没有本事', '荣国府 · 赵姨娘房', 10, 7, 20,
     ['E:ma_dao_po:anger:1.6']),
    ('c25-mou', 'C25-062', 'zhao_yiniang', '怎么暗里算计？我倒有这个意思', '荣国府 · 赵姨娘房', 10, 20, 28,
     ['E:zhao_yiniang:greet:1.4']),
    ('c25-mou', 'C25-063', 'ma_dao_po', '阿弥陀佛！你快休问我，我那里知道这些事', '荣国府 · 赵姨娘房', 10, 28, 35,
     ['E:ma_dao_po:greet:1.4']),
    ('c25-mou', 'C25-064', 'ma_dao_po', '靠你有些什么东西能打动我', '荣国府 · 赵姨娘房', 10, 35, 47,
     ['E:ma_dao_po:greet:1.6']),
    ('c25-mou', 'C25-065', 'zhao_yiniang', '把他两个绝了，明日这家私不怕不是我环儿的', '荣国府 · 赵姨娘房', 10, 47, 55,
     ['E:zhao_yiniang:anger:1.4']),
    ('c25-mou', 'C25-066', 'ma_dao_po', '那时候事情妥了，又无凭据，你还理我呢', '荣国府 · 赵姨娘房', 10, 55, 62,
     ['E:ma_dao_po:greet:1.4']),
    ('c25-mou', 'C25-067', 'zhao_yiniang', '也零碎攒了几两梯己，还有几件衣服簪子', '荣国府 · 赵姨娘房', 10, 62, 74,
     ['M:zhao_yiniang:kang>cabinet']),
    ('c25-mou', 'C25-068', 'narrator', '果然写了个五百两欠契来，赵姨娘便印了个手模', '荣国府 · 赵姨娘房', 10, 74, 86,
     ['E:zhao_yiniang:rest:1.4']),
    ('c25-mou', 'C25-069', 'ma_dao_po', '伸手先去抓了银子掖起来，然后收了欠契', '荣国府 · 赵姨娘房', 10, 86, 93,
     ['E:ma_dao_po:greet:1.4']),
    ('c25-mou', 'C25-070', 'ma_dao_po', '把他两个的年庚八字写在这两个纸人身上', '荣国府 · 赵姨娘房', 10, 93, 103,
     ['E:ma_dao_po:anger:1.4']),
    ('c25-mou', 'C25-071', 'narrator', '正才说著，只见王夫人的丫鬟进来找道', '荣国府 · 赵姨娘房', 10, 103, 109,
     ['E:ma_dao_po:rest:1.2']),

    # ---------------- c25-cha：段 11、12、13 ----------------
    ('c25-cha', 'C25-072', 'narrator', '却说林黛玉因见宝玉近日烫了脸，总不出门', '怡红院', 11, 0, 16,
     ['S:daiyu:outer_room']),
    ('c25-cha', 'C25-073', 'narrator', '林黛玉信步便往怡红院中来', '怡红院', 11, 16, 25,
     ['M:daiyu:cui_lv_place>outer_room']),
    ('c25-cha', 'C25-074', 'narrator', '原来是李宫裁，凤姐，宝钗都在这里呢', '怡红院', 11, 25, 31,
     ['S:liwan:desk_place', 'S:feng:baochai_place', 'S:baochai:baochai_place']),
    ('c25-cha', 'C25-075', 'daiyu', '今儿齐全，谁下帖子请来的', '怡红院', 11, 31, 35,
     ['E:daiyu:greet:1.4']),
    ('c25-cha', 'C25-076', 'feng', '前儿我打发了丫头送了两瓶茶叶去，你往那去了', '怡红院', 11, 35, 41,
     ['E:feng:greet:1.4']),
    ('c25-cha', 'C25-077', 'baoyu', '论理可倒罢了，只是我说不大甚好', '怡红院', 11, 41, 45,
     ['S:baoyu:baoyu_outer', 'E:baoyu:greet:1.2']),
    ('c25-cha', 'C25-078', 'baochai', '味倒轻，只是颜色不大好些', '怡红院', 11, 45, 49,
     ['E:baochai:greet:1.2']),
    ('c25-cha', 'C25-079', 'daiyu', '我吃著好，不知你们的脾胃是怎样', '怡红院', 11, 49, 55,
     ['E:daiyu:greet:1.2']),
    ('c25-cha', 'C25-080', 'feng', '你要爱吃，我那里还有呢', '怡红院', 11, 55, 66,
     ['E:feng:greet:1.4']),
    ('c25-cha', 'C25-081', 'feng', '你既吃了我们家的茶，怎么还不给我们家作媳妇', '怡红院', 12, 0, 14,
     ['E:feng:greet:1.6']),
    ('c25-cha', 'C25-082', 'liwan', '真真我们二婶子的诙谐是好的', '怡红院', 12, 14, 20,
     ['E:liwan:greet:1.2']),
    ('c25-cha', 'C25-083', 'feng', '你别作梦！你给我们家作了媳妇，少什么', '怡红院', 12, 20, 31,
     ['E:feng:greet:1.6']),
    ('c25-cha', 'C25-084', 'baochai', '颦儿急了，还不回来坐著', '怡红院', 13, 0, 7,
     ['E:baochai:greet:1.2']),
    ('c25-cha', 'C25-085', 'narrator', '刚至房门前，只见赵姨娘和周姨娘两个人进来瞧宝玉', '怡红院', 13, 7, 20,
     ['S:zhao_yiniang:gate']),
    ('c25-cha', 'C25-086', 'baoyu', '我也不能出去，你们好歹别叫舅母进来', '怡红院', 13, 20, 27,
     ['E:baoyu:greet:1.2']),
    ('c25-cha', 'C25-087', 'baoyu', '林妹妹，你先略站一站，我说一句话', '怡红院', 13, 27, 32,
     ['E:baoyu:greet:1.2']),

    # ---------------- c25-fabing：段 14、15 ----------------
    ('c25-fabing', 'C25-088', 'narrator', '这里宝玉拉著林黛玉的袖子，只是嘻嘻的笑', '怡红院', 14, 0, 9,
     ['E:baoyu:greet:1.2']),
    ('c25-fabing', 'C25-089', 'baoyu', '好头疼', '怡红院', 14, 9, 13,
     ['E:baoyu:anger:1.4']),
    ('c25-fabing', 'C25-090', 'baoyu', '我要死', '怡红院', 14, 13, 18,
     ['E:baoyu:anger:1.8']),
    ('c25-fabing', 'C25-091', 'narrator', '将身一纵，离地跳有三四尺高，口内乱嚷乱叫', '怡红院', 14, 18, 26,
     ['E:baoyu:anger:2']),
    ('c25-fabing', 'C25-092', 'narrator', '贾母，王夫人见了，唬的抖衣而颤', '怡红院', 14, 26, 31,
     ['S:grandmother:outer_room', 'S:wang:outer_room']),
    ('c25-fabing', 'C25-093', 'narrator', '只见凤姐手持一把明晃晃钢刀砍进园来', '怡红院', 14, 31, 48,
     ['E:feng:anger:2']),
    ('c25-fabing', 'C25-094', 'narrator', '周瑞媳妇忙带著几个有力量的胆壮的婆娘上去抱住，夺下刀来', '怡红院', 14, 48, 57,
     ['E:zhou_rui:rest:1.4']),
    ('c25-fabing', 'C25-095', 'narrator', '独有薛蟠更比诸人忙到十分去', '怡红院', 15, 0, 9,
     ['S:xuepan:gate']),

    # ---------------- c25-shou：段 16、17 ----------------
    ('c25-shou', 'C25-096', 'narrator', '当下众人七言八语，有的说请端公送祟的', '荣国府 · 王夫人上房', 16, 0, 16,
     ['S:baoyu:kang_edge', 'S:feng:guest_seat']),
    ('c25-shou', 'C25-097', 'narrator', '他叔嫂二人愈发糊涂，不省人事', '荣国府 · 王夫人上房', 16, 16, 24,
     ['E:baoyu:rest:1.4']),
    ('c25-shou', 'C25-098', 'narrator', '因此把他二人都抬到王夫人的上房内', '荣国府 · 王夫人上房', 16, 24, 29,
     ['M:baoyu:guest_seat>kang_edge', 'H:xuepan']),
    ('c25-shou', 'C25-099', 'zheng', '儿女之数，皆由天命，非人力可强者', '荣国府 · 王夫人上房', 17, 0, 19,
     ['S:zheng:hall_entry', 'E:zheng:greet:1.4']),
    ('c25-shou', 'C25-100', 'narrator', '看看三日光阴，那凤姐和宝玉躺在床上，亦发连气都将没了', '荣国府 · 王夫人上房', 17, 19, 33,
     ['E:baoyu:rest:1.4']),
    ('c25-shou', 'C25-101', 'baoyu', '从今以后，我可不在你家了', '荣国府 · 王夫人上房', 17, 33, 42,
     ['E:baoyu:anger:1.6']),
    ('c25-shou', 'C25-102', 'zhao_yiniang', '老太太也不必过于悲痛', '荣国府 · 王夫人上房', 17, 42, 52,
     ['E:zhao_yiniang:greet:1.4']),
    ('c25-shou', 'C25-103', 'grandmother', '烂了舌头的混帐老婆，谁叫你来多嘴多舌的', '荣国府 · 王夫人上房', 17, 52, 76,
     ['E:grandmother:anger:2']),
    ('c25-shou', 'C25-104', 'narrator', '两口棺椁都做齐了，请老爷出去看', '荣国府 · 王夫人上房', 17, 76, 84,
     ['E:grandmother:anger:1.4']),
    ('c25-shou', 'C25-105', 'narrator', '只闻得隐隐的木鱼声响，念了一句', '荣国府 · 王夫人上房', 17, 84, 94,
     ['S:monk:hall_entry', 'S:taoist:hall_entry']),
    ('c25-shou', 'C25-106', 'narrator', '贾母，王夫人听见这些话，那里还耐得住，便命人去快请进来', '荣国府 · 王夫人上房', 17, 94, 107,
     ['E:grandmother:greet:1.2']),

    # ---------------- c25-sengdao：段 18-25 ----------------
    ('c25-sengdao', 'C25-107', 'narrator', '鼻如悬胆两眉长，目似明星蓄宝光', '荣国府 · 王夫人上房', 18, 0, 4,
     ['E:monk:rest:1.4']),
    ('c25-sengdao', 'C25-108', 'narrator', '那道人又是怎生模样', '荣国府 · 王夫人上房', 19, 0, 1,
     ['E:taoist:rest:1.2']),
    ('c25-sengdao', 'C25-109', 'narrator', '一足高来一足低，浑身带水又拖泥', '荣国府 · 王夫人上房', 20, 0, 4,
     ['E:taoist:rest:1.4']),
    ('c25-sengdao', 'C25-110', 'zheng', '你道友二人在那庙里焚修', '荣国府 · 王夫人上房', 21, 0, 6,
     ['E:zheng:greet:1.2']),
    ('c25-sengdao', 'C25-111', 'monk', '长官不须多话', '荣国府 · 王夫人上房', 21, 6, 9,
     ['E:monk:greet:1.2']),
    ('c25-sengdao', 'C25-112', 'zheng', '倒有两个人中邪，不知你们有何符水', '荣国府 · 王夫人上房', 21, 9, 12,
     ['E:zheng:greet:1.2']),
    ('c25-sengdao', 'C25-113', 'taoist', '你家现有希世奇珍，如何还问我们有符水', '荣国府 · 王夫人上房', 21, 12, 18,
     ['E:taoist:greet:1.4']),
    ('c25-sengdao', 'C25-114', 'zheng', '小儿落草时虽带了一块宝玉下来，上面说能除邪祟', '荣国府 · 王夫人上房', 21, 18, 21,
     ['E:zheng:greet:1.4']),
    ('c25-sengdao', 'C25-115', 'monk', '长官你那里知道那物的妙用', '荣国府 · 王夫人上房', 21, 21, 25,
     ['E:monk:greet:1.6']),
    ('c25-sengdao', 'C25-116', 'narrator', '便向宝玉项上取下那玉来递与他二人', '荣国府 · 王夫人上房', 22, 0, 5,
     ['E:zheng:greet:1.2']),
    ('c25-sengdao', 'C25-117', 'monk', '青埂峰一别，展眼已过十三载矣', '荣国府 · 王夫人上房', 22, 5, 12,
     ['E:monk:rest:1.6']),
    ('c25-sengdao', 'C25-118', 'narrator', '天不拘兮地不羁，心头无喜亦无悲', '荣国府 · 王夫人上房', 23, 0, 4,
     ['E:monk:rest:1.4']),
    ('c25-sengdao', 'C25-119', 'narrator', '可叹你今日这番经历', '荣国府 · 王夫人上房', 24, 0, 1,
     ['E:monk:rest:1.2']),
    ('c25-sengdao', 'C25-120', 'narrator', '粉渍脂痕污宝光，绮栊昼夜困鸳鸯', '荣国府 · 王夫人上房', 25, 0, 4,
     ['E:monk:rest:1.4']),

    # ---------------- c25-jie：段 26 ----------------
    ('c25-jie', 'C25-121', 'monk', '此物已灵，不可亵渎，悬于卧室上槛', '荣国府 · 王夫人上房', 26, 0, 13,
     ['E:monk:greet:1.6']),
    ('c25-jie', 'C25-122', 'narrator', '说著回头便走了', '荣国府 · 王夫人上房', 26, 13, 20,
     ['H:monk', 'H:taoist']),
    ('c25-jie', 'C25-123', 'narrator', '少不得依言将他二人就安放在王夫人卧室之内，将玉悬在门上', '荣国府 · 王夫人上房', 26, 20, 24,
     ['E:wang:rest:1.2']),
    ('c25-jie', 'C25-124', 'narrator', '至晚间他二人竟渐渐醒来，说腹中饥饿', '荣国府 · 王夫人上房', 26, 24, 32,
     ['E:baoyu:rest:1.6']),
    ('c25-jie', 'C25-125', 'narrator', '李宫裁并贾府三艳，薛宝钗，林黛玉，平儿，袭人等在外间听信息', '荣国府 · 王夫人上房', 26, 32, 41,
     ['S:daiyu:guest_seat', 'S:baochai:guest_seat']),
    ('c25-jie', 'C25-126', 'xichun', '宝姐姐，好好的笑什么', '荣国府 · 王夫人上房', 26, 41, 48,
     ['S:xichun:guest_seat', 'E:xichun:greet:1.2']),
    ('c25-jie', 'C25-127', 'baochai', '我笑如来佛比人还忙', '荣国府 · 王夫人上房', 26, 48, 58,
     ['E:baochai:greet:1.6']),
    ('c25-jie', 'C25-128', 'daiyu', '你们这起人不是好人，不知怎么死', '荣国府 · 王夫人上房', 26, 58, 66,
     ['E:daiyu:anger:1.6']),
    ('c25-jie', 'C25-129', 'narrator', '一面说，一面摔帘子出去了', '荣国府 · 王夫人上房', 26, 66, 68,
     ['H:daiyu']),
]


# ★ 第 24 回初版把「起止子句号」全部手写进 CUTS，结果和底本漂移了：
#   9 处区间互相重叠（下一节点被上一节点吞掉）、4 处跳段子句、
#   15 处标题和切出来的正文说的不是一回事。
#   手写索引必然漂——底本一改就全错，而且错了不报错，只是内容错乱。
#
#   这里改成：**CUTS 只声明起点**，终点由下一个节点的起点决定；
#   起点本身用「标题回锚底本」自愈——第 24 回的标题基本就是底本原文片段
#   （369 个节点里 355 个能在底本逐字查到），所以拿标题去底本里找落点，
#   比手写的数字可靠得多。
#
#   align_cuts() 做两件事：
#     1) 起点自愈：在本段里找标题的最佳落点（子句精确命中优先，
#        否则用 difflib 取最像的窗口），并强制全局单调递增。
#     2) 终点推导：prev.s_to = next.s_from，段末节点吃到本段末尾。
#        于是整段底本被**不重不漏**地切开，既不重叠也不跳段。
def _strip_punct(text: str) -> str:
    return re.sub(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\'"]', '', text)


def _title_anchor(sents, para, title, after):
    """在本段里找标题的最佳落点，返回子句号；找不到返回 None。

    after：只考虑严格大于该位置的子句，保证全局单调递增。

    ★ 打分用「标题前缀在候选窗口里匹配了多少字」，不是「标题是否整段出现」。
      只看整段出现会踩一个坑：标题常常在句子中间被截断
      （「这会子还装」是「这会子还装胖呢」的前半截），
      于是「整段出现」会因为后半截对不上而失败，退到下一个位置去，
      把节点锚到段尾去——C24-119「留下外甥挨饿不成？」就是这么被
      锚成了「这会子还装胖呢。」
      按最长前缀打分，「你又糊涂了。说着没有米，……」这种半截标题
      才会锚在它真正开始的地方。
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
        # acc 与 tn 的最长公共前缀长度
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
    """给每个节点算出「延伸到哪里为止」。

    ★ 延伸不能越过下一个节点的起点——否则下一节点的正文被本节点重读一遍。
      这里返回 limit[i] = 本节点最多能延伸到的子句号（不含）。
      跨段时 limit 就是本段末尾。
    """
    limits = []
    for i, c in enumerate(cuts):
        para = c[5]
        if i + 1 < len(cuts) and cuts[i + 1][5] == para:
            limits.append(cuts[i + 1][6])
        else:
            limits.append(len(SENTENCES[para]))
    return limits
DESIGN_NOTES = [
    ('C25-D1', 'c25-hongyu',
     '红玉梦与宝玉寻红玉，复用 `yihong`（怡红院）',
     '底本第 25 回开篇宝玉「晃出了房门……只见西南角上游廊底下栏杆上」，仍在怡红院；'
     '红玉「走来打扫房屋」也是怡红院的差事。',
     '用 `yihong` 的 `outer_room`/`window_place`/`yard` 锚点。'),
    ('C25-D2', 'c25-penh',
     '红玉借喷壶见贾芸种树，复用 `qinfang`（沁芳闸）',
     '底本「正走上翠烟桥……只见山坡上高处都是拦著帏幙……贾芸正坐在那山子石上」——'
     '桥、山坡、山子石与 `qinfang` 的桥/桃林/石景吻合。',
     '用 `bridge_head`/`bridge_mid`/`stone_seat` 锚点；潇湘馆本项目无专图，不新开。'),
    ('C25-D3', 'c25-jiahuan',
     '贾环抄咒、烫宝玉一场放 `wang`（王夫人上房）',
     '底本明写「贾环正在王夫人炕上坐著」「王夫人便用手满身满脸摩挲抚弄他」。',
     '用 `wang` 的 `kang_edge`/`wang_host`/`guest_seat`/`hall_entry`。'),
    ('C25-D4', 'c25-madaopo',
     '马道婆劝贾母供海灯一场放 `entry`（贾母院）',
     '底本「又向贾母道……贾母听了，点头思忖」，是马道婆对贾母说话，在贾母处。',
     '用 `passage_entry`/`grandmother_seat`/`grandmother_greet`，place 写「荣国府 · 贾母院」。'),
    ('C25-D5', 'c25-mou',
     '马道婆与赵姨娘密谋魇魔法，新建 `zhao_room`（赵姨娘房）',
     '底本「来至赵姨娘房内……炕上堆著些零碎绸缎湾角，赵姨娘正粘鞋」，'
     '又「走到橱柜里将梯己拿了出来」，是赵姨娘自己的房，与被魇的人养病的王夫人上房不能混。',
     '新建室内图 `zhao_room`，6 锚点（door/table/kang/zhao_seat/madao_seat/cabinet）。'),
    ('C25-D6', 'c25-shou',
     '宝玉凤姐疯魔、抬到王夫人上房、僧道解厄，均在 `wang`',
     '底本「把他二人都抬到王夫人的上房内」「将他二人就安放在王夫人卧室之内，将玉悬在门上」。',
     '用 `wang` 的 `kang_edge`/`guest_seat`/`hall_entry`，不新开卧室图。'),
    ('C25-D7', 'c25-jiahuan',
     '玉钏儿、金钏儿、周姨娘、丰儿、贾萍不入 cast',
     '均只在叙述里被点名，无独立台词（金钏儿虽已登记，本回也无台词）；'
     '按第 24 回「提及不登场」先例处理。',
     '只在正文里保留，不 show、不注册新 cast。'),
    ('C25-D8', 'c25-sengdao',
     '癞头和尚与跛足道人复用第 1 回 `monk`/`taoist`，不新建',
     '两者第 1 回已是「一僧一道」并登记 cast；本回「通灵遇双真」正是同一 pair。',
     '直接用 `monk`/`taoist` id，台词「长官不须多话」等照录。'),
    ('C25-D9', 'c25-sengdao',
     '四首赞诗作为旁白念出的 `verbatim` 韵文节点',
     '底本段 18/20/23/25 是形容僧道与咏玉的诗，无说话人。',
     'speaker 用 narrator，`textKind: verbatim`，不改字。'),
    ('C25-D10', 'c25-jiahuan',
     '马道婆、彩霞的外形是视觉设计推定，不是原文明示',
     '底本对这两人**没有一句外貌描写**：马道婆只写「宝玉寄名的干娘」与台词，'
     '彩霞只写行为（咬唇、戳额、淡淡不答理、夺手）。',
     'features/prompt 全部标「底本无外貌描写，以下为视觉设计推定」；'
     '不把设计细节冒充原文记载。'),
    ('C25-D11', 'c25-fabing',
     '薛蟠「酥倒」、众人荐张真人等保持叙述，不新增角色',
     '底本段 15「忽一眼瞥见了林黛玉风流婉转，已酥倒在那里」是叙述；'
     '段 16 端公/巫婆/张真人只在众人七言八语里被点名。',
     '薛蟠已在 cast（`xuepan`），用叙述带过；张真人等不登场。'),
]


def build():
    steps = []
    # ★ 先自愈区间（起点按标题回锚底本，终点由下一节点起点推导）。
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
                'chapter': 25,
                'paragraphLead': lead,
                'textKind': 'verbatim',
                'layer': 'present',
            },
            '_pos': (para, s_from),
        })
    return steps


def assign_scenes(steps):
    """定场景与 focus。

    ★ focus 是**锚点名**，不是角色 id（第 23 回踩过这个坑）：
      引擎拿它定位镜头与存档校验（engine.ts 的 `this.anchor(this.step.focus)`），
      所以它必须是该场景 Anchors 层里真实存在且可通行的格子。
      推导规则照第 23 回：优先取本节点动作里的 show 落点，
      其次取 move 的末点，都没有就沿用同段上一次的落点。

    ★ last_focus 必须**按场景**记，不能按段 id（第 24 回踩过这个坑）：
      同一个场景可能横跨好几段（`yihong` 占了 c24-yuanyang / c24-yihong /
      c24-doucha / c24-yipa 四段）。按段 id 记的话，段首那个既没有 show
      也没有 move 的节点就会取不到值，focus 断链成空字符串——引擎会把它
      当成「没有镜头目标」，check_content 则直接报 `unknown focus`。
      按场景记之后，跨段续用同一场景时镜头不会丢。
    """
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
    """写盘前的自校。三条都是踩过坑才加的。"""
    errors = []
    seen_ids = set()
    last = None
    for step in steps:
        if step['id'] in seen_ids:
            errors.append(f'{step["id"]}: 节点 id 重复')
        seen_ids.add(step['id'])
        # (段号, 子句号) 必须全局单调递增——顺序错了读者会看到后面的话又倒回去。
        pos = step['_pos']
        if last is not None and pos <= last:
            errors.append(f'{step["id"]}: 底本位置 {pos} 不大于上一个 {last}')
        last = pos
        if not step['text'].strip():
            errors.append(f'{step["id"]}: 正文为空')
        if not step['source']['paragraphLead'].strip():
            errors.append(f'{step["id"]}: paragraphLead 为空')
        # ★ focus 必须非空：引擎拿它定位镜头（this.anchor(this.step.focus)），
        #   空 focus 等于「镜头落在场景里第一个锚点」，不可控；check_content
        #   也会报 `unknown focus`。这是第 24 回 26 个节点集体断链的根因，
        #   生成器自校必须拦得住，否则要等上线后才发现。
        if not step.get('focus'):
            errors.append(f'{step["id"]}: focus 为空（段首既无 show 也无 move 时会断链）')
        # 正文必须真的来自底本（逐字）——把 lead 去掉标点后应当在底本里找得到。
        stripped_lead = re.sub(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\']', '', step['source']['paragraphLead'])
        if stripped_lead and stripped_lead not in re.sub(
                r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\']', '', BODY):
            errors.append(f'{step["id"]}: paragraphLead 在底本里查不到：{step["source"]["paragraphLead"][:30]}')
        # ★ 舞台连续性自检（只查 move）：
        #   引擎只在换场景时清空舞台，同场景可见性保持。
        #   所以「move 一个从没 show 过的人」不会在数据里报错，
        #   要等读者点到那一步才抛——那时已经上线了。
        #   这里按「同场景内 show 过就可见」来模拟。
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
            'id': step['id'].replace('C25-', 'C25-E'),
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
        'chapter': 25,
        'source': {
            'edition': '维基文库《紅樓夢》第 025 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第025回&action=raw',
            'retrievedAt': '2026-11-25',
            'localText': 'docs/chapter25-source.txt',
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
        print('第25回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第25回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 25})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第25回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
