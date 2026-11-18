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
鸳鸯与袭人）、rongguo-entry（贾母院请安）、east（贾赦院邢夫人房）、
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
BASE = ROOT / 'docs' / 'chapter24-source.txt'
STORY = ROOT / 'design' / 'chapter24-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter24-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter24-evidence.json'

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
    ('c24-xiangling', '沁芳闸 · 香菱拍醒黛玉', 'qinfang'),
    ('c24-yuanyang', '怡红院 · 鸳鸯与胭脂', 'yihong'),
    ('c24-huijian', '宁荣街 · 贾芸见宝玉', 'capital'),
    ('c24-jiashe', '贾赦院 · 邢夫人待客', 'east'),
    ('c24-jialian', '贾琏院 · 花木工程', 'jialian_home'),
    ('c24-bu', '香料铺 · 卜世仁推赊', 'spice_shop'),
    ('c24-nier', '三街六巷 · 醉金刚义侠', 'ni_er_lane'),
    ('c24-jiayin', '贾芸家 · 见母不吐实情', 'jia_yun_home'),
    ('c24-huojing', '凤姐院外 · 献冰麝', 'c6_wangchui'),
    ('c24-qiranzhai', '绮霰斋 · 小红挡驾', 'qiranzhai'),
    ('c24-paihu', '荣国府门前 · 凤姐许差事', 'capital'),
    ('c24-lingpai', '绮霰斋 · 领银种树', 'qiranzhai'),
    ('c24-huanshui', '三街六巷 · 还银赎义', 'ni_er_lane'),
    ('c24-yihong', '怡红院 · 只剩宝玉', 'yihong'),
    ('c24-doucha', '怡红院 · 递茶与奚落', 'yihong'),
    ('c24-yipa', '怡红院窗下 · 遗帕', 'yihong'),
]


# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题, 地点, 底本段号, 起始子句号, 结束子句号, 动作)
#
# ★ 索引是**子句号**（见 split_sentences 的说明），不是句号。
#   底本第 N 段的第 [s_from, s_to) 个子句。切出来的正文与 paragraphLead
#   都是底本逐字原文，不作任何改写。
# 节点顺序按底本位置 (段号, 子句号) 全局单调递增——check() 会逐对校验。
CUTS = [
    # ---------------- c24-xiangling：段 1 ----------------
    ('c24-xiangling', 'C24-001', 'narrator', '黛玉正自情思萦逗，缠绵固结之时', '大观园 · 沁芳闸', 1, 0, 2,
     ['S:daiyu:bank_west']),
    ('c24-xiangling', 'C24-002', 'narrator', '忽有人从背后击了一掌', '大观园 · 沁芳闸', 1, 2, 4,
     ['S:xiangling:bank_west']),
    ('c24-xiangling', 'C24-003', 'xiangling', '你作什么一个人在这里？', '大观园 · 沁芳闸', 1, 4, 5,
     ['E:xiangling:greet:1.2']),
    ('c24-xiangling', 'C24-004', 'narrator', '回头看时，不是别人，却是香菱', '大观园 · 沁芳闸', 1, 5, 9,
     ['E:daiyu:rest:1.2']),
    ('c24-xiangling', 'C24-005', 'daiyu', '你这个傻丫头，唬我这么一跳好的', '大观园 · 沁芳闸', 1, 9, 13,
     ['E:daiyu:greet:1.4']),
    ('c24-xiangling', 'C24-006', 'xiangling', '我来寻我们的姑娘的，找他总找不著', '大观园 · 沁芳闸', 1, 13, 16,
     ['E:xiangling:greet:1.4']),
    ('c24-xiangling', 'C24-007', 'xiangling', '你们紫鹃也找你呢，说琏二奶奶送了什么茶叶来给你的', '大观园 · 沁芳闸', 1, 16, 18,
     ['E:xiangling:greet:1.4']),
    ('c24-xiangling', 'C24-008', 'xiangling', '走罢，回家去坐著', '大观园 · 沁芳闸', 1, 18, 20,
     ['E:xiangling:greet:1.2']),
    ('c24-xiangling', 'C24-009', 'narrator', '一面拉著黛玉的手回潇湘馆来了，果然凤姐儿送了两小瓶新茶', '大观园 · 沁芳闸', 1, 20, 23,
     ['E:daiyu:rest:1.4']),
    ('c24-xiangling', 'C24-010', 'narrator', '不过说些这一个绣的好，那一个刺的精，又下一回棋，看两句书', '大观园 · 沁芳闸', 1, 23, 29,
     ['E:xiangling:rest:1.4']),
    ('c24-xiangling', 'C24-011', 'narrator', '香菱便走了', '大观园 · 沁芳闸', 1, 29, 31,
     ['H:xiangling']),

    # ---------------- c24-yuanyang：段 2 ----------------
    ('c24-yuanyang', 'C24-012', 'narrator', '宝玉因被袭人找回房去，果见鸳鸯歪在床上看袭人的针线', '怡红院 · 外间', 2, 0, 3,
     ['S:baoyu:baoyu_outer', 'S:xiren:desk_place', 'S:yuan_yang:xiren_kang']),
    ('c24-yuanyang', 'C24-013', 'yuan_yang', '你往那里去了？老太太等著你呢', '怡红院 · 外间', 2, 3, 7,
     ['E:yuan_yang:greet:1.4']),
    ('c24-yuanyang', 'C24-014', 'yuan_yang', '叫你过那边请大老爷的安去，还不快换了衣服走呢', '怡红院 · 外间', 2, 7, 8,
     ['E:yuan_yang:greet:1.2']),
    ('c24-yuanyang', 'C24-015', 'narrator', '袭人便进房去取衣服，宝玉坐在床沿上褪鞋等靴子', '怡红院 · 外间', 2, 8, 11,
     ['M:xiren:desk_place>inner_room', 'E:baoyu:rest:1.2']),
    ('c24-yuanyang', 'C24-016', 'narrator', '回头见鸳鸯穿著水红绫子袄儿，青缎子背心，束著白绉绸汗巾儿', '怡红院 · 外间', 2, 11, 15,
     ['E:yuan_yang:rest:1.4']),
    ('c24-yuanyang', 'C24-017', 'narrator', '脸向那边低著头看针线，脖子上戴著花领子', '怡红院 · 外间', 2, 15, 16,
     ['E:yuan_yang:rest:1.2']),
    ('c24-yuanyang', 'C24-018', 'narrator', '宝玉便把脸凑在他脖项上，闻那香油气', '怡红院 · 外间', 2, 16, 18,
     ['M:baoyu:baoyu_outer>xiren_kang', 'E:baoyu:greet:1.2']),
    ('c24-yuanyang', 'C24-019', 'narrator', '不住用手摩挲，其白腻不在袭人之下', '怡红院 · 外间', 2, 18, 20,
     ['E:baoyu:greet:1.2']),
    ('c24-yuanyang', 'C24-020', 'baoyu', '好姐姐，把你嘴上的胭脂赏我吃了罢', '怡红院 · 外间', 2, 20, 23,
     ['E:baoyu:greet:1.4']),
    ('c24-yuanyang', 'C24-021', 'narrator', '一面扭股糖似的粘在身上', '怡红院 · 外间', 2, 23, 25,
     ['E:baoyu:greet:1.2']),
    ('c24-yuanyang', 'C24-022', 'yuan_yang', '袭人，你出来瞧瞧', '怡红院 · 外间', 2, 25, 28,
     ['E:yuan_yang:greet:1.4']),
    ('c24-yuanyang', 'C24-023', 'yuan_yang', '你跟他一辈子，也不劝劝，还是这么著', '怡红院 · 外间', 2, 28, 31,
     ['E:yuan_yang:greet:1.2']),
    ('c24-yuanyang', 'C24-024', 'xiren', '左劝也不改，右劝也不改，你到底是怎么样？', '怡红院 · 外间', 2, 31, 36,
     ['M:xiren:inner_room>desk_place', 'E:xiren:greet:1.4']),
    ('c24-yuanyang', 'C24-025', 'xiren', '你再这么著，这个地方可就难住了', '怡红院 · 外间', 2, 36, 38,
     ['E:xiren:greet:1.2']),
    ('c24-yuanyang', 'C24-026', 'narrator', '一边催他穿了衣服，同鸳鸯往前面来见贾母', '怡红院 · 外间', 2, 38, 41,
     ['E:baoyu:rest:1.4']),

    # ---------------- c24-huijian：段 3、4 ----------------
    ('c24-huijian', 'C24-027', 'narrator', '见过贾母，出至外面，人马俱已齐备，刚欲上马', '宁荣街 · 荣府门前', 3, 0, 4,
     ['S:baoyu:rong_gate', 'S:jia_lian:street_west']),
    ('c24-huijian', 'C24-028', 'narrator', '只见贾琏请安回来了，正下马，二人对面彼此问了两句话', '宁荣街 · 荣府门前', 3, 4, 8,
     ['E:jia_lian:greet:1.2']),
    ('c24-huijian', 'C24-029', 'narrator', '只见旁边转出一个人来，请宝叔安', '宁荣街 · 荣府门前', 3, 8, 10,
     ['S:jia_yun:west_corner']),
    ('c24-huijian', 'C24-030', 'narrator', '宝玉看时，这人容长脸，长挑身材，年纪只好十八九岁', '宁荣街 · 荣府门前', 3, 10, 14,
     ['E:jia_yun:rest:1.4']),
    ('c24-huijian', 'C24-031', 'narrator', '生得著实斯文清秀，倒也十分面善，只是想不起是那一房的', '宁荣街 · 荣府门前', 3, 14, 17,
     ['E:jia_yun:rest:1.2']),
    ('c24-huijian', 'C24-032', 'jia_lian', '你怎么发呆，连他也不认得？他是后廊上住的五嫂子的儿子芸儿', '宁荣街 · 荣府门前', 3, 18, 22,
     ['E:jia_lian:greet:1.4']),
    ('c24-huijian', 'C24-033', 'baoyu', '是了，是了，我怎么就忘了', '宁荣街 · 荣府门前', 3, 22, 26,
     ['E:baoyu:greet:1.2']),
    ('c24-huijian', 'C24-034', 'narrator', '因问他母亲好，这会子什么勾当', '宁荣街 · 荣府门前', 3, 26, 28,
     ['E:jia_yun:rest:1.2']),
    ('c24-huijian', 'C24-035', 'jia_yun', '找二叔说句话', '宁荣街 · 荣府门前', 3, 28, 30,
     ['E:jia_yun:greet:1.2']),
    ('c24-huijian', 'C24-036', 'baoyu', '你倒比先越发出挑了，倒象我的儿子', '宁荣街 · 荣府门前', 3, 30, 33,
     ['E:baoyu:greet:1.4']),
    ('c24-huijian', 'C24-037', 'jia_lian', '好不害臊！人家比你大四五岁呢，就替你作儿子了？', '宁荣街 · 荣府门前', 3, 33, 37,
     ['E:jia_lian:greet:1.4']),
    ('c24-huijian', 'C24-038', 'baoyu', '你今年十几岁了？', '宁荣街 · 荣府门前', 3, 37, 39,
     ['E:baoyu:greet:1.2']),
    ('c24-huijian', 'C24-039', 'jia_yun', '十八岁', '宁荣街 · 荣府门前', 3, 39, 41,
     ['E:jia_yun:greet:1.2']),
    ('c24-huijian', 'C24-040', 'narrator', '原来这贾芸最伶俐乖觉，便笑道', '宁荣街 · 荣府门前', 4, 0, 3,
     ['E:jia_yun:greet:1.4']),
    ('c24-huijian', 'C24-041', 'jia_yun', '俗语说的，摇车里的爷爷，拄拐的孙孙', '宁荣街 · 荣府门前', 4, 3, 6,
     ['E:jia_yun:greet:1.4']),
    ('c24-huijian', 'C24-042', 'jia_yun', '虽然岁数大，山高高不过太阳', '宁荣街 · 荣府门前', 4, 6, 8,
     ['E:jia_yun:greet:1.2']),
    ('c24-huijian', 'C24-043', 'jia_yun', '只从我父亲没了，这几年也无人照管教导', '宁荣街 · 荣府门前', 4, 8, 10,
     ['E:jia_yun:greet:1.4']),
    ('c24-huijian', 'C24-044', 'jia_yun', '如若宝叔不嫌侄儿蠢笨，认作儿子，就是我的造化了', '宁荣街 · 荣府门前', 4, 10, 13,
     ['E:jia_yun:greet:1.4']),
    ('c24-huijian', 'C24-045', 'jia_lian', '你听见了？认儿子不是好开交的呢', '宁荣街 · 荣府门前', 4, 13, 16,
     ['E:jia_lian:greet:1.2']),
    ('c24-huijian', 'C24-046', 'narrator', '说著就进去了', '宁荣街 · 荣府门前', 4, 16, 17,
     ['H:jia_lian']),
    ('c24-huijian', 'C24-047', 'baoyu', '明儿你闲了，只管来找我，别和他们鬼鬼祟祟的', '宁荣街 · 荣府门前', 4, 17, 21,
     ['E:baoyu:greet:1.4']),
    ('c24-huijian', 'C24-048', 'baoyu', '明儿你到书房里来，和你说天话儿，我带你园里顽耍去', '宁荣街 · 荣府门前', 4, 21, 25,
     ['E:baoyu:greet:1.4']),
    ('c24-huijian', 'C24-049', 'narrator', '说著扳鞍上马，众小厮围随往贾赦这边来', '宁荣街 · 荣府门前', 4, 25, 27,
     ['H:baoyu', 'H:jia_yun']),

    # ---------------- c24-jiashe：段 5、6 前半 ----------------
    ('c24-jiashe', 'C24-050', 'narrator', '见了贾赦，不过是偶感些风寒，先述了贾母问的话，然后自己请了安', '贾赦院 · 上房', 5, 0, 4,
     ['S:baoyu:xing_room', 'S:xing:xing_host']),
    ('c24-jiashe', 'C24-051', 'narrator', '贾赦先站起来回了贾母话，次后便唤人来', '贾赦院 · 上房', 5, 4, 6,
     ['E:xing:rest:1.2']),
    ('c24-jiashe', 'C24-052', 'xing', '带哥儿进去太太屋里坐著', '贾赦院 · 上房', 5, 6, 7,
     ['E:xing:greet:1.2']),
    ('c24-jiashe', 'C24-053', 'narrator', '宝玉退出，来至后面，进入上房', '贾赦院 · 上房', 5, 7, 10,
     ['E:baoyu:rest:1.4']),
    ('c24-jiashe', 'C24-054', 'narrator', '邢夫人见了他来，先倒站了起来，请过贾母安，宝玉方请安', '贾赦院 · 上房', 5, 10, 14,
     ['E:xing:greet:1.4']),
    ('c24-jiashe', 'C24-055', 'narrator', '邢夫人拉他上炕坐了，方问别人好，又命人倒茶来', '贾赦院 · 上房', 5, 14, 17,
     ['E:xing:rest:1.4']),
    ('c24-jiashe', 'C24-056', 'narrator', '一钟茶未吃完，只见那贾琮来问宝玉好', '贾赦院 · 上房', 5, 17, 19,
     ['E:baoyu:rest:1.2']),
    ('c24-jiashe', 'C24-057', 'xing', '那里找活猴儿去！你那奶妈子死绝了', '贾赦院 · 上房', 5, 19, 22,
     ['E:xing:greet:1.4']),
    ('c24-jiashe', 'C24-058', 'xing', '也不收拾收拾你，弄的黑眉乌嘴的，那里象大家子念书的孩子！', '贾赦院 · 上房', 5, 22, 25,
     ['E:xing:greet:1.4']),
    ('c24-jiashe', 'C24-059', 'narrator', '只见贾环，贾兰小叔侄两个也来了，请过安', '贾赦院 · 上房', 5, 25, 29,
     ['S:jia_huan:daiyu_guest', 'S:jia_lan:messenger']),
    ('c24-jiashe', 'C24-060', 'narrator', '邢夫人便叫他两个椅子上坐了', '贾赦院 · 上房', 5, 29, 30,
     ['E:xing:rest:1.2']),
    ('c24-jiashe', 'C24-061', 'narrator', '贾环见宝玉同邢夫人坐在一个坐褥上，早已心中不自在了', '贾赦院 · 上房', 5, 30, 33,
     ['E:jia_huan:rest:1.4']),
    ('c24-jiashe', 'C24-062', 'narrator', '坐不多时，便和贾兰使眼色儿要走', '贾赦院 · 上房', 5, 33, 35,
     ['E:jia_huan:rest:1.2']),
    ('c24-jiashe', 'C24-063', 'narrator', '贾兰只得依他，一同起身告辞', '贾赦院 · 上房', 5, 35, 37,
     ['M:jia_lan:messenger>daiyu_guest', 'M:jia_huan:daiyu_guest>return_gate']),
    ('c24-jiashe', 'C24-064', 'narrator', '宝玉见他们要走，自己也就起身，要一同回去', '贾赦院 · 上房', 5, 37, 40,
     ['E:baoyu:rest:1.4']),
    ('c24-jiashe', 'C24-065', 'xing', '你且坐著，我还和你说话呢', '贾赦院 · 上房', 5, 40, 43,
     ['E:xing:greet:1.4']),
    ('c24-jiashe', 'C24-066', 'narrator', '宝玉只得坐了', '贾赦院 · 上房', 5, 43, 44,
     ['E:baoyu:rest:1.2']),
    ('c24-jiashe', 'C24-067', 'xing', '你们回去，各人替我问你们各人母亲好', '贾赦院 · 上房', 5, 44, 47,
     ['E:xing:greet:1.4']),
    ('c24-jiashe', 'C24-068', 'xing', '你们姑娘，姐姐，妹妹都在这里呢，闹的我头晕，今儿不留你们吃饭了', '贾赦院 · 上房', 5, 47, 52,
     ['E:xing:greet:1.4']),
    ('c24-jiashe', 'C24-069', 'narrator', '贾环等答应著，便出来回家去了', '贾赦院 · 上房', 5, 52, 54,
     ['H:jia_huan', 'H:jia_lan']),
    ('c24-jiashe', 'C24-070', 'baoyu', '可是姐姐们都过来了，怎么不见？', '贾赦院 · 上房', 6, 0, 3,
     ['E:baoyu:greet:1.4']),
    ('c24-jiashe', 'C24-071', 'xing', '他们坐了一会子，都往后头不知那屋里去了', '贾赦院 · 上房', 6, 3, 6,
     ['E:xing:greet:1.4']),
    ('c24-jiashe', 'C24-072', 'baoyu', '大娘方才说有话说，不知是什么话？', '贾赦院 · 上房', 6, 6, 9,
     ['E:baoyu:greet:1.4']),
    ('c24-jiashe', 'C24-073', 'xing', '那里有什么话，不过是叫你等著，同你姊妹们吃了饭去', '贾赦院 · 上房', 6, 9, 13,
     ['E:xing:greet:1.4']),
    ('c24-jiashe', 'C24-074', 'xing', '还有一个好玩的东西给你带回去玩', '贾赦院 · 上房', 6, 13, 14,
     ['E:xing:greet:1.2']),
    ('c24-jiashe', 'C24-075', 'narrator', '娘儿两个说话，不觉早又晚饭时节', '贾赦院 · 上房', 6, 14, 16,
     ['E:xing:rest:1.4']),
    ('c24-jiashe', 'C24-076', 'narrator', '母女姊妹们吃毕了饭，宝玉去辞贾赦，同姊妹们一同回家', '贾赦院 · 上房', 6, 16, 20,
     ['E:baoyu:rest:1.4']),
    ('c24-jiashe', 'C24-077', 'narrator', '见过贾母，王夫人等，各自回房安息', '贾赦院 · 上房', 6, 20, 24,
     ['E:baoyu:rest:1.2']),

    # ---------------- c24-jialian：段 6 后半 ----------------
    ('c24-jialian', 'C24-078', 'narrator', '且说贾芸进去见了贾琏，因打听可有什么事情', '贾琏院 · 院中', 6, 25, 27,
     ['S:jia_yun:yard', 'S:jia_lian:table_place']),
    ('c24-jialian', 'C24-079', 'jia_lian', '前儿倒有一件事情出来，偏生你婶子再三求了我，给了贾芹了', '贾琏院 · 院中', 6, 27, 31,
     ['E:jia_lian:greet:1.4']),
    ('c24-jialian', 'C24-080', 'jia_lian', '他许了我，说明儿园里还有几处要栽花木的地方，等这个工程出来，一定给你就是了', '贾琏院 · 院中', 6, 31, 35,
     ['E:jia_lian:greet:1.4']),
    ('c24-jialian', 'C24-081', 'narrator', '贾芸听了，半晌说道', '贾琏院 · 院中', 6, 35, 37,
     ['E:jia_yun:rest:1.2']),
    ('c24-jialian', 'C24-082', 'jia_yun', '既是这样，我就等著罢', '贾琏院 · 院中', 6, 37, 39,
     ['E:jia_yun:greet:1.2']),
    ('c24-jialian', 'C24-083', 'jia_yun', '叔叔也不必先在婶子跟前提我今儿来打听的话，到跟前再说也不迟', '贾琏院 · 院中', 6, 39, 41,
     ['E:jia_yun:greet:1.4']),
    ('c24-jialian', 'C24-084', 'jia_lian', '提他作什么，我那里有这些工夫说闲话儿呢', '贾琏院 · 院中', 6, 41, 44,
     ['E:jia_lian:greet:1.4']),
    ('c24-jialian', 'C24-085', 'jia_lian', '明儿一个五更，还要到兴邑去走一趟，须得当日赶回来才好', '贾琏院 · 院中', 6, 44, 47,
     ['E:jia_lian:greet:1.4']),
    ('c24-jialian', 'C24-086', 'jia_lian', '你先去等著，后日起更以后你来讨信儿，来早了我不得闲', '贾琏院 · 院中', 6, 47, 50,
     ['E:jia_lian:greet:1.4']),
    ('c24-jialian', 'C24-087', 'narrator', '说著便回后面换衣服去了', '贾琏院 · 院中', 6, 50, 51,
     ['M:jia_lian:table_place>room']),

    # ---------------- c24-bu：段 7、8 ----------------
    ('c24-bu', 'C24-088', 'narrator', '贾芸出了荣国府回家，一路思量，想出一个主意来', '香料铺 · 街面', 7, 0, 3,
     ['S:jia_yun:street']),
    ('c24-bu', 'C24-089', 'narrator', '便一径往他母舅卜世仁家来，原来卜世仁现开香料舖', '香料铺 · 街面', 7, 3, 5,
     ['M:jia_yun:street>shop_door']),
    ('c24-bu', 'C24-090', 'narrator', '忽见贾芸进来，彼此见过了，因问他这早晚什么事跑了来', '香料铺 · 柜台', 7, 5, 9,
     ['S:bu_shi_ren:counter', 'M:jia_yun:shop_door>counter']),
    ('c24-bu', 'C24-091', 'jia_yun', '有件事求舅舅帮衬帮衬', '香料铺 · 柜台', 7, 9, 11,
     ['E:jia_yun:greet:1.2']),
    ('c24-bu', 'C24-092', 'jia_yun', '我有一件事，用些冰片麝香使用，好歹舅舅每样赊四两给我', '香料铺 · 柜台', 7, 11, 14,
     ['E:jia_yun:greet:1.4']),
    ('c24-bu', 'C24-093', 'jia_yun', '八月里按数送了银子来', '香料铺 · 柜台', 7, 14, 15,
     ['E:jia_yun:greet:1.2']),
    ('c24-bu', 'C24-094', 'bu_shi_ren', '再休提赊欠一事', '香料铺 · 柜台', 7, 15, 17,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-095', 'bu_shi_ren', '前儿也是我们舖子里一个伙计，替他的亲戚赊了几两银子的货，至今总未还上', '香料铺 · 柜台', 7, 17, 20,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-096', 'bu_shi_ren', '因此我们大家赔上，立了合同，再不许替亲友赊欠', '香料铺 · 柜台', 7, 20, 23,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-097', 'bu_shi_ren', '谁要赊欠，就要罚他二十两银子的东道', '香料铺 · 柜台', 7, 23, 25,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-098', 'bu_shi_ren', '况且如今这个货也短，你就拿现银子到我们这不三不四的舖子里来买，也还没有这些，只好倒扁儿去', '香料铺 · 柜台', 7, 25, 29,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-099', 'narrator', '这是一。二则你那里有正经事，不过赊了去又是胡闹', '香料铺 · 柜台', 7, 29, 32,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-100', 'bu_shi_ren', '你只说舅舅见你一遭儿就派你一遭儿不是', '香料铺 · 柜台', 7, 32, 33,
     ['E:bu_shi_ren:greet:1.2']),
    ('c24-bu', 'C24-101', 'bu_shi_ren', '你小人儿家很不知好歹，也到底立个主见，赚几个钱，弄得穿是穿吃是吃的，我看著也喜欢', '香料铺 · 柜台', 7, 33, 38,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-102', 'jia_yun', '舅舅说的倒干净', '香料铺 · 柜台', 8, 0, 2,
     ['E:jia_yun:greet:1.2']),
    ('c24-bu', 'C24-103', 'jia_yun', '我父亲没的时候，我年纪又小，不知事', '香料铺 · 柜台', 8, 2, 5,
     ['E:jia_yun:greet:1.4']),
    ('c24-bu', 'C24-104', 'jia_yun', '后来听见我母亲说，都还亏舅舅们在我们家出主意，料理的丧事', '香料铺 · 柜台', 8, 5, 8,
     ['E:jia_yun:greet:1.4']),
    ('c24-bu', 'C24-105', 'jia_yun', '难道舅舅就不知道的，还是有一亩地两间房子，如今在我手里花了不成？', '香料铺 · 柜台', 8, 8, 11,
     ['E:jia_yun:greet:1.4']),
    ('c24-bu', 'C24-106', 'jia_yun', '巧媳妇做不出没米的粥来，叫我怎么样呢？', '香料铺 · 柜台', 8, 11, 13,
     ['E:jia_yun:greet:1.4']),
    ('c24-bu', 'C24-107', 'jia_yun', '还亏是我呢，要是别个，死皮赖脸三日两头儿来缠著舅舅，要三升米二升豆子的，舅舅也就没有法呢', '香料铺 · 柜台', 8, 13, 18,
     ['E:jia_yun:greet:1.4']),
    ('c24-bu', 'C24-108', 'narrator', '卜世仁道', '香料铺 · 柜台', 9, 0, 1,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-109', 'bu_shi_ren', '我的儿，舅舅要有，还不是该的', '香料铺 · 柜台', 9, 1, 4,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-110', 'bu_shi_ren', '我天天和你舅母说，只愁你没算计儿', '香料铺 · 柜台', 9, 4, 6,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-111', 'bu_shi_ren', '你但凡立的起来，到你大房里，就是他们爷儿们见不著，便下个气', '香料铺 · 柜台', 9, 6, 10,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-112', 'bu_shi_ren', '和他们的管家或者管事的人们嬉和嬉和，也弄个事儿管管', '香料铺 · 柜台', 9, 10, 12,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-113', 'bu_shi_ren', '前日我出城去，撞见了你们三房里的老四，骑著大叫驴，带著五辆车，有四五十和尚道士，往家庙去了', '香料铺 · 柜台', 9, 12, 18,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-114', 'bu_shi_ren', '他那不亏能干，这事就到他了！', '香料铺 · 柜台', 9, 18, 20,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-115', 'narrator', '贾芸听他韶刀的不堪，便起身告辞', '香料铺 · 柜台', 9, 20, 22,
     ['E:jia_yun:rest:1.4']),
    ('c24-bu', 'C24-116', 'bu_shi_ren', '怎么急的这样，吃了饭再去罢', '香料铺 · 柜台', 9, 22, 25,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-117', 'narrator', '只见他娘子说道', '香料铺 · 柜台', 9, 25, 27,
     ['E:bu_shi_ren:rest:1.2']),
    ('c24-bu', 'C24-118', 'narrator', '你又糊涂了。说著没有米，这里买了半斤面来下给你吃，这会子还装胖呢', '香料铺 · 柜台', 9, 27, 31,
     ['E:bu_shi_ren:greet:1.4']),
    ('c24-bu', 'C24-119', 'narrator', '留下外甥挨饿不成？', '香料铺 · 柜台', 9, 31, 32,
     ['E:bu_shi_ren:greet:1.2']),
    ('c24-bu', 'C24-120', 'narrator', '卜世仁说：再买半斤来添上就是了', '香料铺 · 柜台', 9, 32, 34,
     ['E:bu_shi_ren:greet:1.2']),
    ('c24-bu', 'C24-121', 'narrator', '他娘子便叫女孩儿：银姐，往对门王奶奶家去问', '香料铺 · 柜台', 9, 34, 37,
     ['E:bu_shi_ren:rest:1.2']),
    ('c24-bu', 'C24-122', 'narrator', '有钱借二三十个，明儿就送过来', '香料铺 · 柜台', 9, 37, 39,
     ['E:bu_shi_ren:greet:1.2']),
    ('c24-bu', 'C24-123', 'narrator', '夫妻两个说话，那贾芸早说了几个不用费事，去的无影无踪了', '香料铺 · 柜台', 9, 39, 42,
     ['M:jia_yun:counter>shop_door>street', 'E:jia_yun:rest:1.4']),

    # ---------------- c24-nier：段 9 后半、10、11 ----------------
    ('c24-nier', 'C24-124', 'narrator', '贾芸赌气离了母舅家门，一径回归旧路', '三街六巷 · 街口', 9, 42, 45,
     ['S:jia_yun:lane']),
    ('c24-nier', 'C24-125', 'narrator', '心下正自烦恼，一边想，一边低头只管走', '三街六巷 · 街口', 9, 45, 48,
     ['M:jia_yun:lane>street_center']),
    ('c24-nier', 'C24-126', 'narrator', '不想一头就碰在一个醉汉身上，把贾芸唬了一跳', '三街六巷 · 街心', 9, 48, 50,
     ['S:ni_er:drunk', 'M:jia_yun:street_center>bully']),
    ('c24-nier', 'C24-127', 'ni_er', '臊你娘的！瞎了眼睛，碰起我来了', '三街六巷 · 街心', 9, 50, 54,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-128', 'narrator', '贾芸忙要躲身，早被那醉汉一把抓住', '三街六巷 · 街心', 9, 54, 56,
     ['E:ni_er:greet:1.2']),
    ('c24-nier', 'C24-129', 'narrator', '对面一看，不是别人，却是紧邻倪二', '三街六巷 · 街心', 9, 56, 59,
     ['E:ni_er:rest:1.4']),
    ('c24-nier', 'C24-130', 'narrator', '原来这倪二是个泼皮，专放重利债，在赌博场吃闲钱，专管打降吃酒', '三街六巷 · 街心', 9, 59, 63,
     ['E:ni_er:rest:1.4']),
    ('c24-nier', 'C24-131', 'narrator', '如今正从欠钱人家索了利钱，吃醉回来，不想被贾芸碰了一头', '三街六巷 · 街心', 9, 63, 66,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-132', 'narrator', '正没好气，抡拳就要打', '三街六巷 · 街心', 9, 66, 68,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-133', 'narrator', '只听那人叫道：老二住手！是我冲撞了你', '三街六巷 · 街心', 9, 68, 71,
     ['E:jia_yun:greet:1.4']),
    ('c24-nier', 'C24-134', 'narrator', '倪二听见是熟人的语音，将醉眼睁开看时，见是贾芸，忙把手松了', '三街六巷 · 街心', 9, 71, 75,
     ['E:ni_er:rest:1.4']),
    ('c24-nier', 'C24-135', 'ni_er', '原来是贾二爷，我该死，我该死', '三街六巷 · 街心', 9, 75, 79,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-136', 'ni_er', '这会子往那里去？', '三街六巷 · 街心', 9, 79, 80,
     ['E:ni_er:greet:1.2']),
    ('c24-nier', 'C24-137', 'jia_yun', '告诉不得你，平白的又讨了个没趣儿', '三街六巷 · 街心', 9, 80, 83,
     ['E:jia_yun:greet:1.4']),
    ('c24-nier', 'C24-138', 'ni_er', '不妨不妨，有什么不平的事，告诉我，替你出气', '三街六巷 · 街心', 9, 83, 88,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-139', 'ni_er', '这三街六巷，凭他是谁，有人得罪了我醉金刚倪二的街坊，管叫他人离家散！', '三街六巷 · 街心', 9, 88, 92,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-140', 'jia_yun', '老二，你且别气，听我告诉你这原故', '三街六巷 · 街心', 10, 0, 4,
     ['E:jia_yun:greet:1.4']),
    ('c24-nier', 'C24-141', 'narrator', '说著，便把卜世仁一段事告诉了倪二', '三街六巷 · 街心', 10, 4, 6,
     ['E:jia_yun:greet:1.2']),
    ('c24-nier', 'C24-142', 'ni_er', '要不是令舅，我便骂不出好话来，真真气死我倪二', '三街六巷 · 街心', 10, 6, 10,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-143', 'ni_er', '也罢，你也不用愁烦，我这里现有几两银子，你若用什么，只管拿去买办', '三街六巷 · 街心', 10, 10, 15,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-144', 'ni_er', '但只一件，你我作了这些年的街坊，我在外头有名放帐，你却从没有和我张过口', '三街六巷 · 街心', 10, 15, 19,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-145', 'ni_er', '也不知你厌恶我是个泼皮，怕低了你的身分，也不知是你怕我难缠，利钱重？', '三街六巷 · 街心', 10, 19, 23,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-146', 'ni_er', '若说怕利钱重，这银子我是不要利钱的，也不用写文约', '三街六巷 · 街心', 10, 23, 26,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-147', 'ni_er', '若说怕低了你的身分，我就不敢借给你了，各自走开', '三街六巷 · 街心', 10, 26, 29,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-148', 'narrator', '一面说，一面果然从搭包里掏出一卷银子来', '三街六巷 · 街心', 10, 29, 31,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-149', 'narrator', '贾芸心下自思：素日倪二虽然是泼皮无赖，却因人而使，颇颇的有义侠之名', '三街六巷 · 街心', 11, 0, 4,
     ['E:jia_yun:rest:1.4']),
    ('c24-nier', 'C24-150', 'jia_yun', '若今日不领他这情，怕他臊了，倒恐生事', '三街六巷 · 街心', 11, 4, 7,
     ['E:jia_yun:greet:1.4']),
    ('c24-nier', 'C24-151', 'jia_yun', '不如借了他的，改日加倍还他也倒罢了', '三街六巷 · 街心', 11, 7, 9,
     ['E:jia_yun:greet:1.4']),
    ('c24-nier', 'C24-152', 'jia_yun', '老二，你果然是个好汉，我何曾不想著你，和你张口', '三街六巷 · 街心', 11, 9, 14,
     ['E:jia_yun:greet:1.4']),
    ('c24-nier', 'C24-153', 'jia_yun', '但只是我见你所相与交结的，都是些有胆量的有作为的人，似我们这等无能无力的你倒不理', '三街六巷 · 街心', 11, 14, 17,
     ['E:jia_yun:greet:1.4']),
    ('c24-nier', 'C24-154', 'jia_yun', '我若和你张口，你岂肯借给我。今日既蒙高情，我怎敢不领', '三街六巷 · 街心', 11, 17, 21,
     ['E:jia_yun:greet:1.4']),
    ('c24-nier', 'C24-155', 'jia_yun', '回家按例写了文约过来便是了', '三街六巷 · 街心', 11, 21, 22,
     ['E:jia_yun:greet:1.2']),
    ('c24-nier', 'C24-156', 'ni_er', '好会说话的人。我却听不上这话', '三街六巷 · 街心', 11, 22, 25,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-157', 'ni_er', '既说相与交结四个字，如何放帐给他，使他的利钱！', '三街六巷 · 街心', 11, 25, 28,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-158', 'ni_er', '既把银子借与他，图他的利钱，便不是相与交结了', '三街六巷 · 街心', 11, 28, 31,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-159', 'ni_er', '闲话也不必讲。既肯青目，这是十五两三钱有零的银子，便拿去治买东西', '三街六巷 · 街心', 11, 32, 35,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-160', 'ni_er', '你要写什么文契，趁早把银子还我，让我放给那些有指望的人使去', '三街六巷 · 街心', 11, 35, 38,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-161', 'narrator', '贾芸听了，一面接了银子，一面笑道', '三街六巷 · 街心', 11, 38, 41,
     ['E:jia_yun:greet:1.4']),
    ('c24-nier', 'C24-162', 'jia_yun', '我便不写罢了，有何著急的', '三街六巷 · 街心', 11, 41, 43,
     ['E:jia_yun:greet:1.2']),
    ('c24-nier', 'C24-163', 'ni_er', '这不是话。天气黑了，也不让茶让酒', '三街六巷 · 街心', 11, 43, 47,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-164', 'ni_er', '我还到那边有点事情去，你竟请回去', '三街六巷 · 街心', 11, 47, 49,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-165', 'ni_er', '我还求你带个信儿与舍下，叫他们早些关门睡罢，我不回家去了', '三街六巷 · 街心', 11, 49, 52,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-166', 'ni_er', '倘或有要紧事儿，叫我们女儿明儿一早到马贩子王短腿家来找我', '三街六巷 · 街心', 11, 52, 54,
     ['E:ni_er:greet:1.4']),
    ('c24-nier', 'C24-167', 'narrator', '一面说，一面趔趄著脚儿去了，不在话下', '三街六巷 · 街心', 11, 54, 57,
     ['H:ni_er']),

    # ---------------- c24-huojing：段 12、13、14、15 前半 ----------------
    ('c24-nier', 'C24-168', 'narrator', '贾芸偶然碰了这件事，心中也十分罕希，想那倪二倒果然有些意思', '三街六巷 · 街心', 12, 0, 3,
     ['S:jia_yun:street_center']),
    ('c24-jiayin', 'C24-169', 'narrator', '只是还怕他一时醉中慷慨，到明日加倍的要起来，便怎处', '贾芸家 · 街口', 12, 3, 6,
     ['S:jia_yun:street', 'E:jia_yun:rest:1.4']),
    ('c24-jiayin', 'C24-170', 'narrator', '忽又想道：不妨，等那件事成了，也可加倍还他', '贾芸家 · 街口', 12, 7, 11,
     ['E:jia_yun:greet:1.4']),
    ('c24-jiayin', 'C24-171', 'narrator', '想毕，一直走到个钱舖里，将那银子称一称，十五两三钱四分二厘', '贾芸家 · 街口', 12, 11, 15,
     ['E:jia_yun:rest:1.4']),
    ('c24-jiayin', 'C24-172', 'narrator', '贾芸见倪二不撒谎，心下越发欢喜，收了银子，来至家门', '贾芸家 · 街口', 12, 15, 21,
     ['M:jia_yun:street>home_door', 'E:jia_yun:rest:1.4']),
    ('c24-jiayin', 'C24-173', 'narrator', '先到隔壁将倪二的信捎了与他娘子知道，方回家来', '贾芸家 · 隔壁倪家门口', 12, 19, 21,
     ['M:jia_yun:home_door>neighbor_door', 'E:jia_yun:rest:1.2']),
    # ★ 贾芸之母**不上台、不入 cast**（设计推定 D7：底本只写「见他母亲自在炕上
    #   拈线」，她没有台词）。所以这里不能 show 她——show 一个不在 cast 里的
    #   actor 会被 check_content 拦（unknown actor）。镜头落在里屋 room，
    #   母亲的存在由正文与图上那张炕交代。
    ('c24-jiayin', 'C24-174', 'narrator', '见他母亲自在炕上拈线，见他进来，便问那去了一日', '贾芸家 · 里屋', 12, 21, 24,
     ['M:jia_yun:neighbor_door>home_door>room', 'E:jia_yun:rest:1.2']),
    ('c24-jiayin', 'C24-175', 'narrator', '贾芸恐他母亲生气，便不说起卜世仁的事来，只说在西府里等琏二叔的', '贾芸家 · 里屋', 12, 24, 27,
     ['E:jia_yun:greet:1.4']),
    ('c24-jiayin', 'C24-176', 'narrator', '那天已是掌灯时候，贾芸吃了饭收拾歇息，一宿无话', '贾芸家 · 里屋', 13, 0, 3,
     ['E:jia_yun:rest:1.2']),
    ('c24-huojing', 'C24-177', 'narrator', '次日一早起来，洗了脸，便出南门，大香舖里买了冰麝，便往荣国府来', '凤姐院外 · 后门', 13, 3, 8,
     ['S:jia_yun:back_gate']),
    ('c24-huojing', 'C24-178', 'narrator', '打听贾琏出了门，贾芸便往后面来', '凤姐院外 · 巷道', 13, 8, 10,
     ['E:jia_yun:rest:1.4']),
    ('c24-huojing', 'C24-179', 'narrator', '到贾琏院门前，只见几个小厮拿著大高笤帚在那里扫院子呢', '凤姐院外 · 巷道', 13, 10, 12,
     ['E:jia_yun:rest:1.2']),
    ('c24-huojing', 'C24-180', 'narrator', '忽见周瑞家的从门里出来叫小厮们：先别扫，奶奶出来了', '凤姐院外 · 院门', 13, 12, 15,
     ['S:zhou_rui:zhou_court', 'M:jia_yun:back_gate>market']),
    ('c24-huojing', 'C24-181', 'jia_yun', '二婶婶那去？', '凤姐院外 · 院门', 13, 15, 17,
     ['E:jia_yun:greet:1.2']),
    ('c24-huojing', 'C24-182', 'zhou_rui', '老太太叫，想必是裁什么尺头', '凤姐院外 · 院门', 13, 17, 20,
     ['E:zhou_rui:greet:1.4']),
    ('c24-huojing', 'C24-183', 'narrator', '正说著，只见一群人簇著凤姐出来了', '凤姐院外 · 院门', 13, 20, 22,
     ['S:feng:platform', 'M:feng:hall>platform']),
    ('c24-huojing', 'C24-184', 'narrator', '贾芸深知凤姐是喜奉承尚排场的，忙把手逼著，恭恭敬敬抢上来请安', '凤姐院外 · 院门', 13, 22, 25,
     ['M:jia_yun:market>daoting', 'E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-185', 'narrator', '凤姐连正眼也不看，仍往前走著，只问他母亲好', '凤姐院外 · 院门', 13, 25, 28,
     ['E:feng:rest:1.4']),
    ('c24-huojing', 'C24-186', 'feng', '怎么不来我们这里逛逛？', '凤姐院外 · 院门', 13, 28, 29,
     ['E:feng:greet:1.4']),
    ('c24-huojing', 'C24-187', 'jia_yun', '只是身上不大好，倒时常记挂著婶子，要来瞧瞧，又不能来', '凤姐院外 · 院门', 13, 29, 34,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-188', 'feng', '可是会撒谎，不是我提起他来，你就不说他想我了', '凤姐院外 · 院门', 13, 34, 38,
     ['E:feng:greet:1.4']),
    ('c24-huojing', 'C24-189', 'jia_yun', '侄儿不怕雷打了，就敢在长辈前撒谎', '凤姐院外 · 院门', 13, 38, 41,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-190', 'jia_yun', '昨儿晚上还提起婶子来，说婶子身子生的单弱，事情又多', '凤姐院外 · 院门', 13, 41, 44,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-191', 'jia_yun', '亏婶子好大精神，竟料理的周周全全', '凤姐院外 · 院门', 13, 44, 46,
     ['E:jia_yun:greet:1.2']),
    ('c24-huojing', 'C24-192', 'jia_yun', '要是差一点儿的，早累的不知怎么样呢', '凤姐院外 · 院门', 13, 46, 48,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-193', 'narrator', '凤姐听了满脸是笑，不由的便止了步，问道', '凤姐院外 · 院门', 14, 0, 4,
     ['E:feng:greet:1.4']),
    ('c24-huojing', 'C24-194', 'feng', '怎么好好的你娘儿们在背地里嚼起我来？', '凤姐院外 · 院门', 14, 3, 5,
     ['E:feng:greet:1.4']),
    ('c24-huojing', 'C24-195', 'jia_yun', '有个原故，只因我有个朋友，家里有几个钱，现开香舖', '凤姐院外 · 院门', 14, 4, 9,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-196', 'jia_yun', '只因他身上捐著个通判，前儿选了云南不知那一处，连家眷一齐去', '凤姐院外 · 院门', 14, 9, 12,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-197', 'jia_yun', '把这香舖也不在这里开了，便把帐物攒了一攒', '凤姐院外 · 院门', 14, 12, 14,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-198', 'jia_yun', '该给人的给人，该贱发的贱发了，象这细贵的货，都分著送与亲朋', '凤姐院外 · 院门', 14, 14, 18,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-199', 'jia_yun', '他就一共送了我些冰片，麝香', '凤姐院外 · 院门', 14, 18, 20,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-200', 'jia_yun', '我就和我母亲商量，若要转买，不但卖不出原价来', '凤姐院外 · 院门', 14, 20, 23,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-201', 'jia_yun', '而且谁家拿这些银子买这个作什么，便是很有钱的大家子，也不过使个几分几钱就挺折腰了', '凤姐院外 · 院门', 14, 23, 26,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-202', 'jia_yun', '若说送人，也没人配使这些，倒叫他一文不值半文转卖了', '凤姐院外 · 院门', 14, 26, 29,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-203', 'jia_yun', '因此我就想起婶子来', '凤姐院外 · 院门', 14, 29, 30,
     ['E:jia_yun:greet:1.2']),
    ('c24-huojing', 'C24-204', 'jia_yun', '别说明年贵妃宫中，就是这个端阳节下，不用说这些香料自然是比往常加上十倍去的', '凤姐院外 · 院门', 14, 30, 34,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-205', 'jia_yun', '因此想来想去，只孝顺婶子一个人才合式，方不算遭塌这东西', '凤姐院外 · 院门', 14, 34, 37,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-206', 'narrator', '一边说，一边将一个锦匣举起来', '凤姐院外 · 院门', 14, 37, 39,
     ['E:feng:greet:1.4']),
    ('c24-huojing', 'C24-207', 'narrator', '凤姐正是要办端阳的节礼，采买香料药饵的时节', '凤姐院外 · 院门', 15, 0, 2,
     ['E:feng:greet:1.4']),
    ('c24-huojing', 'C24-208', 'narrator', '忽见贾芸如此一来，听这一篇话，心下又是得意又是欢喜', '凤姐院外 · 院门', 15, 2, 5,
     ['E:feng:greet:1.4']),
    ('c24-huojing', 'C24-209', 'feng', '接过芸哥儿的来，送了家去，交给平儿', '凤姐院外 · 院门', 15, 5, 9,
     ['E:feng:greet:1.4']),
    ('c24-huojing', 'C24-210', 'feng', '看著你这样知好歹，怪道你叔叔常提你，说你说话儿也明白，心里有见识', '凤姐院外 · 院门', 15, 9, 14,
     ['E:feng:greet:1.4']),
    ('c24-huojing', 'C24-211', 'narrator', '贾芸听这话入了港，便打进一步来，故意问道', '凤姐院外 · 院门', 15, 14, 18,
     ['E:jia_yun:greet:1.4']),
    ('c24-huojing', 'C24-212', 'jia_yun', '原来叔叔也曾提我的？', '凤姐院外 · 院门', 15, 16, 18,
     ['E:jia_yun:greet:1.2']),
    ('c24-huojing', 'C24-213', 'narrator', '凤姐见问，才要告诉他与他管事情的那话，便忙又止住', '凤姐院外 · 院门', 15, 18, 21,
     ['E:feng:rest:1.4']),
    ('c24-huojing', 'C24-214', 'narrator', '心下想道：我如今要告诉他那话，倒叫他看著我见不得东西似的', '凤姐院外 · 院门', 15, 21, 24,
     ['E:feng:rest:1.4']),
    ('c24-huojing', 'C24-215', 'narrator', '为得了这点子香，就混许他管事了，今儿先别提起这事', '凤姐院外 · 院门', 15, 24, 27,
     ['E:feng:rest:1.4']),
    ('c24-huojing', 'C24-216', 'narrator', '便把派他监种花木工程的事都隐瞒的一字不提，随口说了两句淡话，便往贾母那里去了', '凤姐院外 · 院门', 15, 27, 31,
     ['M:feng:platform>hall', 'E:feng:rest:1.4']),
    ('c24-huojing', 'C24-217', 'narrator', '贾芸也不好提的，只得回来', '凤姐院外 · 院门', 15, 31, 33,
     ['H:feng', 'E:jia_yun:rest:1.4']),

    # ---------------- c24-qiranzhai：段 15 后半、16、17 ----------------
    ('c24-qiranzhai', 'C24-218', 'narrator', '因昨日见了宝玉，叫他到外书房等著', '绮霰斋 · 院中', 15, 33, 36,
     ['S:jia_yun:gate', 'S:ming_yan:chess']),
    ('c24-qiranzhai', 'C24-219', 'narrator', '到贾母那边仪门外绮霰斋书房里来', '绮霰斋 · 院中', 15, 36, 37,
     ['E:ming_yan:greet:1.2']),
    ('c24-qiranzhai', 'C24-220', 'narrator', '只见焙茗，锄药两个小厮下象棋，为夺车正拌嘴', '绮霰斋 · 院中', 15, 37, 40,
     ['E:jia_yun:greet:1.4']),
    ('c24-qiranzhai', 'C24-221', 'narrator', '还有引泉、扫花、挑云、伴鹤四五个，又在房檐上掏小雀儿玩', '绮霰斋 · 院中', 15, 40, 45,
     ['E:jia_yun:greet:1.4']),
    ('c24-qiranzhai', 'C24-222', 'jia_yun', '猴头们淘气，我来了', '绮霰斋 · 院中', 15, 45, 50,
     ['E:jia_yun:greet:1.4']),
    ('c24-qiranzhai', 'C24-223', 'narrator', '众小厮看见贾芸进来，都才散了', '绮霰斋 · 院中', 15, 50, 52,
     ['H:ming_yan', 'E:jia_yun:rest:1.2']),
    ('c24-qiranzhai', 'C24-224', 'narrator', '贾芸进入房内，便坐在椅子上问', '绮霰斋 · 书房', 15, 52, 55,
     ['M:jia_yun:yard>door>study', 'E:jia_yun:greet:1.2']),
    ('c24-qiranzhai', 'C24-225', 'jia_yun', '宝二爷没下来？', '绮霰斋 · 书房', 15, 54, 55,
     ['E:jia_yun:greet:1.2']),
    ('c24-qiranzhai', 'C24-226', 'ming_yan', '今儿总没下来。二爷说什么，我替你哨探哨探去', '绮霰斋 · 书房', 15, 55, 59,
     ['E:ming_yan:greet:1.4']),
    ('c24-qiranzhai', 'C24-227', 'narrator', '说著，便出去了', '绮霰斋 · 书房', 15, 59, 61,
     ['H:ming_yan']),
    ('c24-qiranzhai', 'C24-228', 'narrator', '这里贾芸便看字画古玩，有一顿饭工夫还不见来', '绮霰斋 · 书房', 16, 0, 2,
     ['E:jia_yun:rest:1.4']),
    ('c24-qiranzhai', 'C24-229', 'narrator', '再看看别的小厮，都顽去了。正是烦闷', '绮霰斋 · 书房', 16, 2, 5,
     ['E:jia_yun:rest:1.4']),
    ('c24-qiranzhai', 'C24-230', 'narrator', '只听门前娇声嫩语的叫了一声哥哥', '绮霰斋 · 书房门前', 16, 5, 6,
     ['S:xiaohong:door', 'E:xiaohong:greet:1.4']),
    ('c24-qiranzhai', 'C24-231', 'narrator', '贾芸往外瞧时，看是一个十六七岁的丫头，生的倒也细巧干净', '绮霰斋 · 书房门前', 16, 6, 9,
     ['E:xiaohong:rest:1.4']),
    ('c24-qiranzhai', 'C24-232', 'narrator', '那丫头见了贾芸，便抽身躲了过去', '绮霰斋 · 书房门前', 16, 9, 11,
     ['E:xiaohong:rest:1.2']),
    ('c24-qiranzhai', 'C24-233', 'narrator', '恰值焙茗走来，见那丫头在门前，便说道', '绮霰斋 · 书房门前', 16, 11, 14,
     ['S:ming_yan:yard', 'E:ming_yan:greet:1.2']),
    ('c24-qiranzhai', 'C24-234', 'ming_yan', '好，好，正抓不著个信儿', '绮霰斋 · 书房门前', 16, 14, 17,
     ['E:ming_yan:greet:1.4']),
    ('c24-qiranzhai', 'C24-235', 'narrator', '贾芸见了焙茗，也就赶了出来，问怎么样', '绮霰斋 · 书房门前', 16, 17, 20,
     ['M:jia_yun:study>door', 'E:jia_yun:greet:1.2']),
    ('c24-qiranzhai', 'C24-236', 'ming_yan', '等了这一日，也没个人儿过来。这就是宝二爷房里的', '绮霰斋 · 书房门前', 16, 20, 24,
     ['E:ming_yan:greet:1.4']),
    ('c24-qiranzhai', 'C24-237', 'ming_yan', '好姑娘，你进去带个信儿，就说廊上的二爷来了', '绮霰斋 · 书房门前', 16, 24, 27,
     ['E:ming_yan:greet:1.4']),
    ('c24-qiranzhai', 'C24-238', 'narrator', '那丫头听说，方知是本家的爷们，便不似先前那等回避', '绮霰斋 · 书房门前', 17, 0, 3,
     ['E:xiaohong:rest:1.4']),
    ('c24-qiranzhai', 'C24-239', 'narrator', '下死眼把贾芸钉了两眼', '绮霰斋 · 书房门前', 17, 3, 4,
     ['E:xiaohong:greet:1.2']),
    ('c24-qiranzhai', 'C24-240', 'jia_yun', '什么是廊上廊下的，你只说是芸儿就是了', '绮霰斋 · 书房门前', 17, 4, 7,
     ['E:jia_yun:greet:1.4']),
    ('c24-qiranzhai', 'C24-241', 'narrator', '半晌，那丫头冷笑了一笑', '绮霰斋 · 书房门前', 17, 7, 9,
     ['E:xiaohong:rest:1.2']),
    ('c24-qiranzhai', 'C24-242', 'xiaohong', '依我说，二爷竟请回家去，有什么话明儿再来', '绮霰斋 · 书房门前', 17, 9, 12,
     ['E:xiaohong:greet:1.4']),
    ('c24-qiranzhai', 'C24-243', 'xiaohong', '今儿晚上得空儿我回了他', '绮霰斋 · 书房门前', 17, 12, 13,
     ['E:xiaohong:greet:1.2']),
    ('c24-qiranzhai', 'C24-244', 'ming_yan', '这是怎么说？', '绮霰斋 · 书房门前', 17, 13, 15,
     ['E:ming_yan:greet:1.2']),
    ('c24-qiranzhai', 'C24-245', 'xiaohong', '他今儿也没睡中觉，自然吃的晚饭早。晚上他又不下来', '绮霰斋 · 书房门前', 17, 15, 19,
     ['E:xiaohong:greet:1.4']),
    ('c24-qiranzhai', 'C24-246', 'xiaohong', '难道只是耍的二爷在这里等著挨饿不成！不如家去，明儿来是正经', '绮霰斋 · 书房门前', 17, 19, 22,
     ['E:xiaohong:greet:1.4']),
    ('c24-qiranzhai', 'C24-247', 'xiaohong', '便是回来有人带信，那都是不中用的。他不过口里应著，他倒给带呢！', '绮霰斋 · 书房门前', 17, 22, 26,
     ['E:xiaohong:greet:1.4']),
    ('c24-qiranzhai', 'C24-248', 'narrator', '贾芸听这丫头说话简便俏丽，待要问他的名字，因是宝玉房里的，又不便问', '绮霰斋 · 书房门前', 17, 26, 30,
     ['E:jia_yun:rest:1.4']),
    ('c24-qiranzhai', 'C24-249', 'jia_yun', '这话倒是，我明儿再来', '绮霰斋 · 书房门前', 17, 30, 33,
     ['E:jia_yun:greet:1.4']),
    ('c24-qiranzhai', 'C24-250', 'narrator', '说著便往外走', '绮霰斋 · 书房门前', 17, 33, 34,
     ['E:jia_yun:rest:1.2']),
    ('c24-qiranzhai', 'C24-251', 'ming_yan', '我倒茶去，二爷吃了茶再去', '绮霰斋 · 书房门前', 17, 34, 37,
     ['E:ming_yan:greet:1.4']),
    ('c24-qiranzhai', 'C24-252', 'jia_yun', '不吃茶，我还有事呢', '绮霰斋 · 书房门前', 17, 37, 40,
     ['E:jia_yun:greet:1.2']),
    ('c24-qiranzhai', 'C24-253', 'narrator', '口里说话，眼睛瞧那丫头还站在那里呢', '绮霰斋 · 书房门前', 17, 40, 43,
     ['H:xiaohong']),

    # ---------------- c24-paihu：段 18、19 ----------------
    ('c24-paihu', 'C24-254', 'narrator', '那贾芸一径回家', '宁荣街 · 荣府门前', 18, 0, 1,
     ['S:jia_yun:outside', 'S:baoyu:rong_gate']),
    ('c24-paihu', 'C24-255', 'narrator', '至次日来至大门前，可巧遇见凤姐往那边去请安，才上了车', '宁荣街 · 荣府门前', 18, 1, 4,
     ['S:feng:outside', 'E:feng:rest:1.2']),
    ('c24-paihu', 'C24-256', 'narrator', '见贾芸来，便命人唤住，隔窗子笑道', '宁荣街 · 荣府门前', 18, 4, 7,
     ['M:jia_yun:outside>street_west', 'E:feng:greet:1.4']),
    ('c24-paihu', 'C24-257', 'feng', '芸儿，你竟有胆子在我的跟前弄鬼', '宁荣街 · 荣府门前', 18, 7, 9,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-258', 'feng', '怪道你送东西给我，原来你有事求我', '宁荣街 · 荣府门前', 18, 9, 11,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-259', 'feng', '昨儿你叔叔才告诉我说你求他', '宁荣街 · 荣府门前', 18, 11, 12,
     ['E:feng:greet:1.2']),
    ('c24-paihu', 'C24-260', 'jia_yun', '求叔叔这事，婶子休提，我昨儿正后悔呢', '宁荣街 · 荣府门前', 18, 12, 16,
     ['E:jia_yun:greet:1.4']),
    ('c24-paihu', 'C24-261', 'jia_yun', '早知这样，我竟一起头求婶子，这会子也早完了', '宁荣街 · 荣府门前', 18, 16, 19,
     ['E:jia_yun:greet:1.4']),
    ('c24-paihu', 'C24-262', 'jia_yun', '谁承望叔叔竟不能的', '宁荣街 · 荣府门前', 18, 19, 20,
     ['E:jia_yun:greet:1.2']),
    ('c24-paihu', 'C24-263', 'feng', '怪道你那里没成儿，昨儿又来寻我', '宁荣街 · 荣府门前', 18, 20, 23,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-264', 'jia_yun', '婶子辜负了我的孝心，我并没有这个意思', '宁荣街 · 荣府门前', 18, 23, 26,
     ['E:jia_yun:greet:1.4']),
    ('c24-paihu', 'C24-265', 'jia_yun', '若有这个意思，昨儿还不求婶子', '宁荣街 · 荣府门前', 18, 26, 28,
     ['E:jia_yun:greet:1.4']),
    ('c24-paihu', 'C24-266', 'jia_yun', '如今婶子既知道了，我倒要把叔叔丢下，少不得求婶子好歹疼我一点儿', '宁荣街 · 荣府门前', 18, 28, 31,
     ['E:jia_yun:greet:1.4']),
    ('c24-paihu', 'C24-267', 'narrator', '凤姐冷笑道', '宁荣街 · 荣府门前', 19, 0, 1,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-268', 'feng', '你们要拣远路儿走，叫我也难说', '宁荣街 · 荣府门前', 19, 1, 3,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-269', 'feng', '早告诉我一声儿，有什么不成的，多大点子事，耽误到这会子', '宁荣街 · 荣府门前', 19, 3, 7,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-270', 'feng', '那园子里还要种花，我只想不出一个人来，你早来不早完了', '宁荣街 · 荣府门前', 19, 7, 10,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-271', 'jia_yun', '既这样，婶子明儿就派我罢', '宁荣街 · 荣府门前', 19, 10, 13,
     ['E:jia_yun:greet:1.4']),
    ('c24-paihu', 'C24-272', 'feng', '这个我看著不大好。等明年正月里烟火灯烛那个大宗儿下来，再派你罢', '宁荣街 · 荣府门前', 19, 13, 17,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-273', 'jia_yun', '好婶子，先把这个派了我罢。果然这个办的好，再派我那个', '宁荣街 · 荣府门前', 19, 17, 22,
     ['E:jia_yun:greet:1.4']),
    ('c24-paihu', 'C24-274', 'feng', '你倒会拉长线儿', '宁荣街 · 荣府门前', 19, 22, 24,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-275', 'feng', '罢了，要不是你叔叔说，我不管你的事', '宁荣街 · 荣府门前', 19, 24, 27,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-276', 'feng', '你到午错的时候来领银子，后儿就进去种树', '宁荣街 · 荣府门前', 19, 27, 30,
     ['E:feng:greet:1.4']),
    ('c24-paihu', 'C24-277', 'narrator', '说毕，令人驾起香车，一径去了', '宁荣街 · 荣府门前', 19, 30, 33,
     ['H:feng']),

    # ---------------- c24-lingpai：段 20 ----------------
    ('c24-lingpai', 'C24-278', 'narrator', '贾芸喜不自禁，来至绮霰斋打听宝玉', '绮霰斋 · 院中', 20, 0, 2,
     ['S:jia_yun:gate', 'E:jia_yun:greet:1.2']),
    ('c24-lingpai', 'C24-279', 'narrator', '谁知宝玉一早便往北静王府里去了', '绮霰斋 · 院中', 20, 2, 3,
     ['E:jia_yun:rest:1.2']),
    ('c24-lingpai', 'C24-280', 'narrator', '贾芸便呆呆的坐到晌午，打听凤姐回来', '绮霰斋 · 院中', 20, 3, 5,
     ['E:jia_yun:rest:1.4']),
    ('c24-lingpai', 'C24-281', 'narrator', '便写个领票来领对牌', '绮霰斋 · 院中', 20, 5, 6,
     ['E:jia_yun:rest:1.2']),
    ('c24-lingpai', 'C24-282', 'narrator', '至院外，命人通报了，彩明走了出来', '绮霰斋 · 院中', 20, 6, 9,
     ['M:jia_yun:gate>yard', 'E:jia_yun:rest:1.2']),
    ('c24-lingpai', 'C24-283', 'narrator', '单要了领票进去，批了银数年月，一并连对牌交与了贾芸', '绮霰斋 · 院中', 20, 9, 12,
     ['E:jia_yun:rest:1.4']),
    ('c24-lingpai', 'C24-284', 'narrator', '贾芸接了，看那批上银数批了二百两，心中喜不自禁', '绮霰斋 · 院中', 20, 12, 15,
     ['E:jia_yun:greet:1.4']),
    ('c24-lingpai', 'C24-285', 'narrator', '翻身走到银库上，交与收牌票的，领了银子', '绮霰斋 · 院中', 20, 15, 18,
     ['E:jia_yun:rest:1.4']),
    ('c24-lingpai', 'C24-286', 'narrator', '回家告诉母亲，自是母子俱各欢喜', '绮霰斋 · 院中', 20, 18, 20,
     ['E:jia_yun:rest:1.2']),
    ('c24-huanshui', 'C24-287', 'narrator', '次日一个五鼓，贾芸先找了倪二，将前银按数还他', '三街六巷 · 街心', 20, 20, 23,
     ['S:jia_yun:lane', 'S:ni_er:drunk', 'M:jia_yun:lane>street_center']),
    ('c24-huanshui', 'C24-288', 'narrator', '那倪二见贾芸有了银子，他便按数收回，不在话下', '三街六巷 · 街心', 20, 23, 26,
     ['E:ni_er:rest:1.4']),
    ('c24-huanshui', 'C24-289', 'narrator', '这里贾芸又拿了五十两，出西门找到花儿匠方椿家里去买树，不在话下', '三街六巷 · 街心', 20, 26, 29,
     ['H:ni_er', 'E:jia_yun:rest:1.4']),

    # ---------------- c24-yihong：段 21 ----------------
    ('c24-yihong', 'C24-290', 'narrator', '如今且说宝玉，自那日见了贾芸，曾说明日著他进来说话儿', '怡红院 · 外间', 21, 0, 3,
     ['S:baoyu:baoyu_outer']),
    ('c24-yihong', 'C24-291', 'narrator', '如此说了之后，他原是富贵公子的口角，那里还把这个放在心上，因而便忘怀了', '怡红院 · 外间', 21, 3, 7,
     ['E:baoyu:rest:1.4']),
    ('c24-yihong', 'C24-292', 'narrator', '这日晚上，从北静王府里回来，见过贾母，王夫人等，回至园内，换了衣服，正要洗澡', '怡红院 · 外间', 21, 7, 14,
     ['E:baoyu:rest:1.4']),
    ('c24-yihong', 'C24-293', 'narrator', '袭人因被薛宝钗烦了去打结子', '怡红院 · 外间', 21, 14, 15,
     ['E:baoyu:rest:1.2']),
    ('c24-yihong', 'C24-294', 'narrator', '秋纹、碧痕两个去催水', '怡红院 · 外间', 21, 15, 17,
     ['E:baoyu:rest:1.2']),
    ('c24-yihong', 'C24-295', 'narrator', '檀云又因他母亲的生日接了出去，麝月又现在家中养病', '怡红院 · 外间', 21, 17, 19,
     ['E:baoyu:rest:1.2']),
    ('c24-yihong', 'C24-296', 'narrator', '虽还有几个作粗活听唤的丫头，估著叫不著他们，都出去寻伙觅伴的玩去了', '怡红院 · 外间', 21, 19, 22,
     ['E:baoyu:rest:1.4']),
    ('c24-yihong', 'C24-297', 'narrator', '不想这一刻的工夫，只剩了宝玉在房内', '怡红院 · 外间', 21, 22, 24,
     ['E:baoyu:rest:1.4']),
    ('c24-yihong', 'C24-298', 'narrator', '偏生的宝玉要吃茶，一连叫了两三声，方见两三个老嬷嬷走进来', '怡红院 · 外间', 21, 24, 27,
     ['E:baoyu:rest:1.4']),
    ('c24-yihong', 'C24-299', 'narrator', '宝玉见了他们，连忙摇手儿说', '怡红院 · 外间', 21, 27, 29,
     ['E:baoyu:greet:1.2']),
    ('c24-yihong', 'C24-300', 'baoyu', '罢，罢，不用你们了', '怡红院 · 外间', 21, 29, 32,
     ['E:baoyu:greet:1.4']),
    ('c24-yihong', 'C24-301', 'narrator', '老婆子们只得退出', '怡红院 · 外间', 21, 32, 33,
     ['E:baoyu:rest:1.2']),

    # ---------------- c24-doucha：段 22、23、24 前半 ----------------
    ('c24-doucha', 'C24-302', 'narrator', '宝玉见没丫头们，只得自己下来，拿了碗向茶壶去倒茶', '怡红院 · 外间', 22, 0, 3,
     ['M:baoyu:baoyu_outer>desk_place']),
    ('c24-doucha', 'C24-303', 'narrator', '只听背后说道：二爷仔细烫了手，让我们来倒', '怡红院 · 外间', 22, 3, 6,
     ['S:xiaohong:window_place', 'E:xiaohong:greet:1.4']),
    ('c24-doucha', 'C24-304', 'narrator', '一面说，一面走上来，早接了碗过去', '怡红院 · 外间', 22, 6, 9,
     ['M:xiaohong:window_place>desk_place', 'E:xiaohong:greet:1.2']),
    ('c24-doucha', 'C24-305', 'narrator', '宝玉倒唬了一跳，问：你在那里的？忽然来了，唬我一跳', '怡红院 · 外间', 22, 9, 14,
     ['E:baoyu:greet:1.4']),
    ('c24-doucha', 'C24-306', 'narrator', '那丫头一面递茶，一面回说', '怡红院 · 外间', 22, 14, 16,
     ['E:xiaohong:greet:1.2']),
    ('c24-doucha', 'C24-307', 'xiaohong', '我在后院子里，才从里间的后门进来，难道二爷就没听见脚步响？', '怡红院 · 外间', 22, 16, 19,
     ['E:xiaohong:greet:1.4']),
    ('c24-doucha', 'C24-308', 'narrator', '宝玉一面吃茶，一面仔细打量那丫头', '怡红院 · 外间', 22, 19, 21,
     ['E:baoyu:rest:1.4']),
    ('c24-doucha', 'C24-309', 'narrator', '穿著几件半新不旧的衣裳，倒是一头黑鬒鬒的好头发，挽著个髻', '怡红院 · 外间', 22, 21, 24,
     ['E:xiaohong:rest:1.4']),
    ('c24-doucha', 'C24-310', 'narrator', '容长脸面，细巧身材，却十分俏丽干净', '怡红院 · 外间', 22, 24, 27,
     ['E:xiaohong:rest:1.4']),
    ('c24-doucha', 'C24-311', 'narrator', '宝玉看了，便笑问道', '怡红院 · 外间', 23, 0, 2,
     ['E:baoyu:greet:1.4']),
    ('c24-doucha', 'C24-312', 'baoyu', '你也是我这屋里的人么？', '怡红院 · 外间', 23, 2, 3,
     ['E:baoyu:greet:1.4']),
    ('c24-doucha', 'C24-313', 'xiaohong', '是的', '怡红院 · 外间', 23, 3, 5,
     ['E:xiaohong:greet:1.2']),
    ('c24-doucha', 'C24-314', 'baoyu', '既是这屋里的，我怎么不认得？', '怡红院 · 外间', 23, 5, 8,
     ['E:baoyu:greet:1.4']),
    ('c24-doucha', 'C24-315', 'narrator', '那丫头听说，便冷笑了一声道', '怡红院 · 外间', 23, 8, 10,
     ['E:xiaohong:greet:1.2']),
    ('c24-doucha', 'C24-316', 'xiaohong', '认不得的也多，岂只我一个', '怡红院 · 外间', 23, 10, 12,
     ['E:xiaohong:greet:1.4']),
    ('c24-doucha', 'C24-317', 'xiaohong', '从来我又不递茶递水，拿东拿西，眼见的事一点儿不作，那里认得呢', '怡红院 · 外间', 23, 12, 16,
     ['E:xiaohong:greet:1.4']),
    ('c24-doucha', 'C24-318', 'baoyu', '你为什么不作那眼见的事？', '怡红院 · 外间', 23, 16, 18,
     ['E:baoyu:greet:1.4']),
    ('c24-doucha', 'C24-319', 'xiaohong', '这话我也难说', '怡红院 · 外间', 23, 18, 20,
     ['E:xiaohong:greet:1.2']),
    ('c24-doucha', 'C24-320', 'xiaohong', '只是有一句话回二爷：昨儿有个什么芸儿来找二爷', '怡红院 · 外间', 23, 20, 22,
     ['E:xiaohong:greet:1.4']),
    ('c24-doucha', 'C24-321', 'xiaohong', '我想二爷不得空儿，便叫焙茗回他，叫他今日早起来', '怡红院 · 外间', 23, 22, 25,
     ['E:xiaohong:greet:1.4']),
    ('c24-doucha', 'C24-322', 'xiaohong', '不想二爷又往北府里去了', '怡红院 · 外间', 23, 25, 26,
     ['E:xiaohong:greet:1.2']),
    ('c24-doucha', 'C24-323', 'narrator', '刚说到这句话，只见秋纹，碧痕嘻嘻哈哈的说笑著进来', '怡红院 · 外间', 23, 26, 29,
     ['S:qiuwen:curtain', 'S:bihen:zijun_place']),
    ('c24-doucha', 'C24-324', 'narrator', '两个人共提著一桶水，一手撩著衣裳，趔趔趄趄，泼泼撒撒的', '怡红院 · 外间', 23, 29, 33,
     ['M:qiuwen:curtain>baoyu_outer', 'M:bihen:zijun_place>baoyu_outer']),
    ('c24-doucha', 'C24-325', 'narrator', '那丫头便忙迎去接', '怡红院 · 外间', 23, 33, 34,
     ['M:xiaohong:desk_place>baoyu_outer']),
    ('c24-doucha', 'C24-326', 'narrator', '那秋纹，碧痕正对著抱怨，你湿了我的裙子，那个又说，你踹了我的鞋', '怡红院 · 外间', 23, 34, 38,
     ['E:qiuwen:greet:1.4']),
    ('c24-doucha', 'C24-327', 'narrator', '忽见走出一个人来接水，二人看时，不是别人，原来是小红', '怡红院 · 外间', 23, 38, 42,
     ['E:xiaohong:rest:1.4']),
    ('c24-doucha', 'C24-328', 'narrator', '二人便都诧异，将水放下，忙进房来东瞧西望，并没个别人，只有宝玉', '怡红院 · 外间', 23, 42, 47,
     ['M:qiuwen:baoyu_outer>outer_room', 'M:bihen:baoyu_outer>outer_room', 'H:xiaohong']),
    ('c24-doucha', 'C24-329', 'narrator', '便心中大不自在，只得预备下洗澡之物，待宝玉脱了衣裳', '怡红院 · 外间', 23, 47, 50,
     ['E:qiuwen:greet:1.4']),
    ('c24-doucha', 'C24-330', 'narrator', '二人便带上门出来，走到那边房内便找小红，问他方才在屋里说什么', '怡红院 · 外间', 23, 50, 53,
     ['E:qiuwen:greet:1.4']),
    ('c24-doucha', 'C24-331', 'xiaohong', '我何曾在屋里的？只因我的手帕子不见了，往后头找手帕子去', '怡红院 · 外间', 23, 53, 57,
     ['S:xiaohong:cui_lv_place', 'E:xiaohong:greet:1.4']),
    ('c24-doucha', 'C24-332', 'xiaohong', '不想二爷要茶吃，叫姐姐们一个没有，是我进去了，才倒了茶', '怡红院 · 外间', 23, 57, 61,
     ['E:xiaohong:greet:1.4']),
    ('c24-doucha', 'C24-333', 'xiaohong', '姐姐们便来了', '怡红院 · 外间', 23, 61, 62,
     ['E:xiaohong:greet:1.2']),

    # ---------------- c24-yipa：段 24 后半 ----------------
    # ★ 本段首节点必须自带 show：段首既无 show 也无 move 时，focus 会断链成空，
    #   而空 focus 在引擎里等于「镜头落在场景里第一个锚点」——不可控，且会被
    #   check_content 的 `unknown focus` 拦下。秋纹、碧痕在此登场，就在这里 show。
    ('c24-yipa', 'C24-334', 'narrator', '秋纹听了，兜脸啐了一口，骂道', '怡红院 · 外间', 24, 0, 3,
     ['S:qiuwen:curtain', 'S:bihen:zijun_place', 'E:qiuwen:greet:1.4']),
    ('c24-yipa', 'C24-335', 'qiuwen', '没脸的下流东西！正经叫你去催水去，你说有事故，倒叫我们去', '怡红院 · 外间', 24, 3, 7,
     ['E:qiuwen:greet:1.4']),
    ('c24-yipa', 'C24-336', 'qiuwen', '你可等著做这个巧宗儿。一里一里的，这不上来了', '怡红院 · 外间', 24, 7, 10,
     ['E:qiuwen:greet:1.4']),
    ('c24-yipa', 'C24-337', 'qiuwen', '难道我们倒跟不上你了？你也拿镜子照照，配递茶递水不配！', '怡红院 · 外间', 24, 10, 13,
     ['E:qiuwen:greet:1.4']),
    ('c24-yipa', 'C24-338', 'narrator', '碧痕道', '怡红院 · 外间', 24, 13, 14,
     ['E:qiuwen:rest:1.2']),
    ('c24-yipa', 'C24-339', 'bihen', '明儿我说给他们，凡要茶要水送东送西的事，咱们都别动', '怡红院 · 外间', 24, 14, 18,
     ['E:bihen:greet:1.4']),
    ('c24-yipa', 'C24-340', 'bihen', '只叫他去便是了', '怡红院 · 外间', 24, 18, 19,
     ['E:bihen:greet:1.2']),
    ('c24-yipa', 'C24-341', 'narrator', '秋纹道', '怡红院 · 外间', 24, 19, 20,
     ['E:qiuwen:greet:1.2']),
    ('c24-yipa', 'C24-342', 'qiuwen', '这么说，不如我们散了，单让他在这屋里呢', '怡红院 · 外间', 24, 19, 22,
     ['E:qiuwen:greet:1.4']),
    ('c24-yipa', 'C24-343', 'narrator', '二人你一句，我一句，正闹著，只见有个老嬷嬷进来传凤姐的话说', '怡红院 · 外间', 24, 22, 26,
     ['E:bihen:greet:1.2']),
    ('c24-yipa', 'C24-344', 'narrator', '明日有人带花儿匠来种树，叫你们严禁些，衣服裙子别混晒混晾的', '怡红院 · 外间', 24, 26, 29,
     ['E:qiuwen:rest:1.2']),
    ('c24-yipa', 'C24-345', 'narrator', '那土山上一溜都拦著帏幙呢，可别混跑', '怡红院 · 外间', 24, 29, 31,
     ['E:qiuwen:rest:1.2']),
    ('c24-yipa', 'C24-346', 'narrator', '秋纹便问：明儿不知是谁带进匠人来监工？', '怡红院 · 外间', 24, 31, 33,
     ['E:qiuwen:greet:1.4']),
    ('c24-yipa', 'C24-347', 'narrator', '那婆子道：说什么后廊上的芸哥儿', '怡红院 · 外间', 24, 33, 35,
     ['E:qiuwen:rest:1.2']),
    ('c24-yipa', 'C24-348', 'narrator', '秋纹，碧痕听了都不知道，只管混问别的话', '怡红院 · 外间', 24, 35, 38,
     ['E:qiuwen:rest:1.2']),
    ('c24-yipa', 'C24-349', 'narrator', '那小红听见了，心内却明白，就知是昨儿外书房所见那人了', '怡红院 · 外间', 24, 38, 41,
     ['E:xiaohong:greet:1.4']),
    ('c24-yipa', 'C24-350', 'narrator', '原来这小红本姓林，小名红玉', '怡红院 · 外间', 24, 41, 43,
     ['E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-351', 'narrator', '只因玉字犯了林黛玉、宝玉，便都把这个字隐起来，便都叫他小红', '怡红院 · 外间', 24, 43, 47,
     ['E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-352', 'narrator', '原是荣国府中世代的旧仆，他父母现在收管各处房田事务', '怡红院 · 外间', 24, 47, 50,
     ['E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-353', 'narrator', '这红玉年方十六岁，因分人在大观园的时节，把他便分在怡红院中，倒也清幽雅静', '怡红院 · 外间', 24, 49, 53,
     ['E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-354', 'narrator', '不想后来命人进来居住，偏生这一所儿又被宝玉占了', '怡红院 · 外间', 24, 53, 55,
     ['E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-355', 'narrator', '这红玉虽然是个不谙事的丫头，却因他有三分容貌，心内著实妄想痴心的往上攀高', '怡红院 · 外间', 24, 55, 58,
     ['E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-356', 'narrator', '每每的要在宝玉面前现弄现弄', '怡红院 · 外间', 24, 58, 60,
     ['E:xiaohong:rest:1.2']),
    ('c24-yipa', 'C24-357', 'narrator', '只是宝玉身边一干人，都是伶牙利爪的，那里插的下手去', '怡红院 · 外间', 24, 59, 62,
     ['E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-358', 'narrator', '不想今儿才有些消息，又遭秋纹等一场恶意，心内早灰了一半', '怡红院 · 外间', 24, 62, 65,
     ['E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-359', 'narrator', '正闷闷的，忽然听见老嬷嬷说起贾芸来，不觉心中一动', '怡红院 · 外间', 24, 65, 68,
     ['E:xiaohong:greet:1.4']),
    ('c24-yipa', 'C24-360', 'narrator', '便闷闷的回至房中，睡在床上暗暗盘算，翻来掉去，正没个抓寻', '怡红院 · 外间', 24, 68, 72,
     ['M:xiaohong:cui_lv_place>inner_room', 'E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-361', 'narrator', '忽听窗外低低的叫道：红玉，你的手帕子我拾在这里呢', '怡红院 · 窗下', 24, 72, 75,
     ['S:jia_yun:window_place', 'E:jia_yun:greet:1.4']),
    ('c24-yipa', 'C24-362', 'narrator', '红玉听了忙走出来看，不是别人，正是贾芸', '怡红院 · 窗下', 24, 75, 78,
     ['M:xiaohong:inner_room>window_place', 'E:xiaohong:rest:1.4']),
    ('c24-yipa', 'C24-363', 'narrator', '红玉不觉的粉面含羞，问道', '怡红院 · 窗下', 24, 78, 80,
     ['E:xiaohong:greet:1.4']),
    ('c24-yipa', 'C24-364', 'xiaohong', '二爷在那里拾著的？', '怡红院 · 窗下', 24, 79, 81,
     ['E:xiaohong:greet:1.4']),
    ('c24-yipa', 'C24-365', 'narrator', '贾芸笑道', '怡红院 · 窗下', 24, 81, 82,
     ['E:jia_yun:greet:1.2']),
    ('c24-yipa', 'C24-366', 'jia_yun', '你过来，我告诉你', '怡红院 · 窗下', 24, 82, 84,
     ['E:jia_yun:greet:1.4']),
    ('c24-yipa', 'C24-367', 'narrator', '一面说，一面就上来拉他', '怡红院 · 窗下', 24, 84, 86,
     ['E:jia_yun:greet:1.2']),
    ('c24-yipa', 'C24-368', 'narrator', '那红玉急回身一跑，却被门槛绊倒', '怡红院 · 窗下', 24, 86, 88,
     ['E:xiaohong:greet:1.4']),
    ('c24-yipa', 'C24-369', 'narrator', '要知端的，下回分解', '怡红院 · 窗下', 24, 88, 90,
     ['E:xiaohong:rest:1.4']),
]


# ---------------------------------------------------------------- 区间自愈
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
    ('C24-D1', 'c24-xiangling',
     '开篇黛玉与香菱一处，复用 `qinfang`（沁芳闸桃花下），不新开潇湘馆专图',
     '本项目无潇湘馆地图。第 23 回黛玉的戏也在 `qinfang`，沿用同一张图保持一致。'
     '底本只说「回潇湘馆来了」，未描述室内陈设。',
     '沿用 qinfang 的桃林与水岸作黛玉独处的背景；不画潇湘馆内部。'),
    ('C24-D2', 'c24-yuanyang',
     '鸳鸯与宝玉的「涎皮」一场放在 `night`（贾母院 · 碧纱橱与外间）',
     '底本第 24 回写「宝玉因被袭人找回房去，果见鸳鸯歪在床上看袭人的针线」——'
     '第 23 回末尾宝玉已被袭人带回怡红院。但 `night` 的标题是「贾母院 · 碧纱橱与外间」，'
     '与怡红院不是一处。',
     '本项目对第 19-23 回已多次借用 `night` 当怡红院外间（见 agent-notes 二），'
     '沿用同一处理，并在 place 上写「怡红院 · 外间」；不新开第三张同类图。'),
    ('C24-D3', 'c24-huojing',
     '贾芸献给凤姐的冰麝用一只锦匣，不做专门立绘',
     '底本只写「一边说，一边将一个锦匣举起来」，没有描述锦匣的样子。',
     '用叙述带过，不加道具立绘；避免为一句动作生成资产。'),
    ('C24-D4', 'c24-bu',
     '卜世仁的娘子与银姐不登场、不入 cast',
     '底本里两人各有一句台词（娘子「你又糊涂了」、银姐被叫去借钱），但都在'
     '「卜世仁夫妻两个说话」的叙述里，属于画外音。银姐更是连台词都没有，只有名字。',
     '按第 23 回周氏的先例处理：只在叙述里点名，不立绘、不注册 cast。'),
    ('C24-D5', 'c24-nier',
     '倪二称贾芸为「贾二爷」照录，但 cast 用 `jia_yun` 一个 id',
     '底本：「原来是贾二爷，我该死，我该死。」——这里的「贾二爷」指的是贾芸，'
     '不是贾琏或贾环。',
     '登记名仍为「贾芸」，台词照录不改字。'),
    ('C24-D6', 'c24-yipa',
     '小红的遗帕一场：帕子不单独做立绘，用叙述与动作表达',
     '底本只写「你的手帕子我拾在这里呢」「红玉……粉面含羞」，没有描写帕子的花样。',
     '不生成帕子贴图；小红与贾芸的动作（拉、绊倒）承担这一场。'),
    ('C24-D7', 'c24-lingpai',
     '「彩明」与「花儿匠方椿」只在叙述里被提及，不登场',
     '底本：「彩明走了出来，单要了领票进去」「出西门找到花儿匠方椿家里去买树」。'
     '两人各只有这一句叙述，没有台词。',
     '不立绘、不注册 cast；领票与买树两处动作交给叙述。'),
    ('C24-D8', 'c24-yihong',
     '「檀云」不登场——底本用的是「檀云」作丫头名，但本项目此前无此角色',
     '底本第 24 回：「檀云又因他母亲的生日接了出去」。这个名字在第 23 回被'
     '「室霭檀云品御香」误搜过（本项目已把样本从檀云换成坠儿）。',
     '她在本回只有「接了出去」一句，无台词无动作，不立绘；'
     '但**必须保留在正文里**——它是原文，且是「怡红院只剩宝玉」的因果之一。'),
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
                'chapter': 24,
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
            'id': step['id'].replace('C24-', 'C24-E'),
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
        'chapter': 24,
        'source': {
            'edition': '维基文库《紅樓夢》第 024 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第024回&action=raw',
            'retrievedAt': '2026-11-18',
            'localText': 'docs/chapter24-source.txt',
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
        print('第24回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第24回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    for step in steps:
        step.pop('_pos', None)
    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 24})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第24回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
