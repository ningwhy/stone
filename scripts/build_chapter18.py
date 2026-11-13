#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成第 18 回的剧情、段落、证据数据。

第 18 回底本是维基文库原文全文（docs/chapter18-source.txt），
因此每个节点的正文与 source.paragraphLead 都必须**逐字来自底本**。

写法上不手写正文：脚本按「起句标记 → 止句标记」在底本里切片，
正文、lead 都是切出来的，因此不可能出现原著没有的对白或杜撰的诗句。
标记找不到、顺序不对，脚本直接报错退出，不写错数据。

用法：
    python3 scripts/build_chapter18.py            # 生成
    python3 scripts/build_chapter18.py --check    # 只校验已有文件
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs' / 'chapter18-source.txt'
STORY = ROOT / 'design' / 'chapter18-story.json'
SECTION_FILE = ROOT / 'design' / 'chapter18-sections.json'
EVIDENCE = ROOT / 'design' / 'chapter18-evidence.json'

# 底本正文里，标点与空白不算内容——比对时按这个口径。
STRIP_RE = re.compile(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-]')
# 找标记时把各种引号一律视作同一个字符：维基底本的内层用 ‘’，
# 而剧本标记可能写成 “”。字形不同，说的却是同一句话。
QUOTE_MAP = {c: '"' for c in '“”「」『』‘’'}


def strip_marks(text: str) -> str:
    return STRIP_RE.sub('', text)


def normalize(text: str) -> str:
    return ''.join(QUOTE_MAP.get(c, c) for c in text)


def load_base():
    """读底本，返回正文、段落列表、每段的原文字符区间，以及归一化检索表。"""
    raw = BASE.read_text(encoding='utf-8')
    # 维基用 <sectionbegin="诗题"/>…<sectionend="诗题"/> 把诗句括起来，
    # 标记夹在文字中间，剥不掉就会在比对时多出几个字。
    raw = re.sub(r'<section(?:begin|end)="[^"]*"\s*/>', '', raw)
    raw = re.sub(r'<section(?:begin|end)\s*/>', '', raw)
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

    # 归一化正文 + 「归一化下标 → 原文字符下标」的对照表
    norm_chars, origin = [], []
    for i, ch in enumerate(body):
        norm_chars.append(QUOTE_MAP.get(ch, ch))
        origin.append(i)
    norm_body = ''.join(norm_chars)

    # 每段的归一化区间：必须按原文偏移换算，不能拿 find 去搜——
    # 「杏帘在望」这样的短标题在前面已经出现过，find 会命中前一处，
    # 段落区间于是整体错位，后面的切片就都切到别人的字上去了。
    # normalize 是 1:1 映射（引号换成引号），长度不变，所以归一化下标
    # 与原文字符下标一一对应，直接用偏移即可。
    norm_ranges = []
    for off, p in zip(offsets, paras):
        norm_ranges.append((off, off + len(normalize(p))))
    return body, paras, offsets, norm_body, origin, norm_ranges


BODY, PARAS, OFFSETS, NORM_BODY, ORIGIN, NORM_RANGES = load_base()


def para_end(para: int) -> int:
    """某一段在正文里的结束位置。"""
    off = OFFSETS[para]
    return off + len(PARAS[para])


def cut(para: int, start: str, end=None):
    """从底本第 para 段起、到 end 之前切出一段文字。

    end 的三种写法：
      None        —— 到该段末尾
      '@P<n>'     —— 到第 n 段末尾（诗与匾额在维基排版里各占一段）
      '某句'      —— 到这句之前（可跨段，但相距过远就报错）

    返回 (正文, 起句原文)。起句原文直接从底本取，因此 lead 与底本逐字一致。
    """
    ns, ne = NORM_RANGES[para]
    n = NORM_BODY.find(normalize(start), ns, ne)
    if n < 0:
        raise ValueError(f'第 {para} 段找不到起句：{start}')
    orig_start = ORIGIN[n]
    lead = BODY[orig_start:orig_start + len(start)]

    if end is None:
        orig_end = para_end(para)
    elif end.startswith('@P'):
        orig_end = para_end(int(end[2:]))
    else:
        m = NORM_BODY.find(normalize(end), n + len(start))
        if m < 0:
            raise ValueError(f'第 {para} 段起句「{start}」之后找不到止句：{end}')
        orig_end = ORIGIN[m]
        if orig_end - orig_start > 900:
            raise ValueError(f'起句「{start}」与止句「{end}」相距过远（{orig_end - orig_start} 字），标记可能有误')
    if orig_end <= orig_start:
        raise ValueError(f'第 {para} 段的起止顺序不对：{start} → {end}')
    return BODY[orig_start:orig_end].replace('\n\n', '\n'), lead


def to_display(text: str) -> str:
    """底本用弯引号；正文改用「」，与第十六、十七回同一读法。

    只换标点，不动一个字——校验时标点一律被 strip 掉，所以换引号
    不影响「正文出自底本」这件事。
    """
    return text.replace('‘', '『').replace('’', '』').replace('“', '「').replace('”', '」')


# ---------------------------------------------------------------- 动作速记
# 'S:角色:锚点'      show
# 'H:角色'            hide
# 'M:角色:a>b>c'      move（via）
# 'E:角色:kind:秒'    effect
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
# (id, 标题, 场景)
SECTIONS = [
    ('c18-lipouch', '荣国府 · 小厮解去佩物', 'entry'),
    ('c18-cut', '贾母院 · 黛玉误剪香囊袋', 'dinner'),
    ('c18-grandma', '贾母院 · 一处顽顽', 'dinner'),
    ('c18-xiren', '王夫人上房 · 女戏与妙玉', 'wang'),
    ('c18-busy', '王夫人上房 · 昼夜不闲', 'wang'),
    ('c18-prepare', '荣禧堂 · 择日题本', 'central'),
    ('c18-lantern', '宁荣街 · 元宵关防', 'capital'),
    ('c18-welcome', '宁荣街 · 跪迎与版舆', 'capital'),
    ('c18-change', '荣国府 · 体仁沐德', 'entry'),
    ('c18-boat', '大观园 · 登舟', 'canal'),
    ('c18-palace', '省亲别墅 · 换匾受礼', 'central'),
    ('c18-home', '贾母正室 · 家礼相见', 'dinner'),
    ('c18-name', '大观园 · 赐名题诗', 'dinner'),
    ('c18-poem', '大观园 · 绿蜡与杏帘', 'dinner'),
    ('c18-drama', '梨香院 · 点戏四出', 'c11_tianxiang'),
    ('c18-gift', '梨香院 · 赐物与回銮', 'c11_tianxiang'),
]

# ---------------------------------------------------------------- 节点定义
# (段id, 节点id, 说话人, 小标题, 地点, 底本段号, 起句, 止句, 动作)
CUTS = [
    # ---------------- 段一：小厮解去佩物 ----------------
    ('c18-lipouch', 'C18-001', 'narrator', '小厮拦腰抱住宝玉', '荣国府 · 院外', 0,
     '话说宝玉来至院外', '宝玉笑道', ['S:baoyu:west_gate']),
    ('c18-lipouch', 'C18-002', 'baoyu', '一吊钱打发', '荣国府 · 院外', 0,
     '宝玉笑道', '说著，一个上来解荷包', ['S:baoyu:west_gate', 'E:baoyu:jade:1.2']),
    ('c18-lipouch', 'C18-003', 'narrator', '解去荷包扇囊', '荣国府 · 二门前', 0,
     '说著，一个上来解荷包', '那时贾母已命人看了几次', ['M:baoyu:west_gate>handoff']),
    ('c18-lipouch', 'C18-004', 'narrator', '知不曾难为着他', '荣国府 · 二门前', 0,
     '那时贾母已命人看了几次', None,
     ['S:baoyu:courtyard_center', 'S:grandmother:grandmother_seat']),

    # ---------------- 段二：黛玉误剪香囊袋 ----------------
    ('c18-cut', 'C18-005', 'xiren', '带的东西又是那起没脸的东西们解了去了', '贾母院 · 后房', 1,
     '少时袭人倒了茶来', '林黛玉听说，走来瞧瞧', ['S:xiren:maid_place', 'S:baoyu:baoyu_greet']),
    ('c18-cut', 'C18-006', 'narrator', '果然一件无存', '贾母院 · 后房', 1,
     '林黛玉听说，走来瞧瞧', '说毕，赌气回房', ['S:daiyu:daiyu_place']),
    ('c18-cut', 'C18-007', 'daiyu', '我给的那个荷包也给他们了', '贾母院 · 后房', 1,
     '说毕，赌气回房', '宝玉见他生气，便知不妥', ['M:daiyu:daiyu_place>back_door']),
    ('c18-cut', 'C18-008', 'narrator', '早已剪破', '贾母院 · 黛玉房', 1,
     '宝玉见他生气，便知不妥', '因忙把衣领解了', ['S:baoyu:back_door', 'S:daiyu:daiyu_place']),
    ('c18-cut', 'C18-009', 'baoyu', '你瞧瞧，这是什么', '贾母院 · 黛玉房', 1,
     '因忙把衣领解了', '林黛玉见他如此珍重', ['E:baoyu:jade:1.4']),
    ('c18-cut', 'C18-010', 'narrator', '又自悔莽撞', '贾母院 · 黛玉房', 1,
     '林黛玉见他如此珍重', '宝玉道：“你也不用剪', ['E:daiyu:rest:1.2']),
    ('c18-cut', 'C18-011', 'baoyu', '我连这荷包奉还，何如', '贾母院 · 黛玉房', 1,
     '宝玉道：“你也不用剪', '黛玉见如此，越发气起来', ['M:baoyu:daiyu_place>back_door']),
    ('c18-cut', 'C18-012', 'narrator', '拿起荷包来又剪', '贾母院 · 黛玉房', 1,
     '黛玉见如此，越发气起来', '宝玉见他如此，忙回身抢住', ['E:daiyu:rest:1.4']),
    ('c18-cut', 'C18-013', 'baoyu', '好妹妹，饶了他罢', '贾母院 · 黛玉房', 1,
     '宝玉见他如此，忙回身抢住', '黛玉将剪子一摔',
     ['M:baoyu:back_door>daiyu_place', 'E:baoyu:greet:1.2']),
    ('c18-cut', 'C18-014', 'daiyu', '要恼，就撂开手', '贾母院 · 黛玉房', 1,
     '黛玉将剪子一摔', '禁不住宝玉上来', ['E:daiyu:rest:1.2']),
    ('c18-cut', 'C18-015', 'narrator', '妹妹长妹妹短赔不是', '贾母院 · 黛玉房', 1,
     '禁不住宝玉上来', None, ['E:baoyu:greet:1.0']),

    # ---------------- 段三：贾母许一处顽顽 ----------------
    ('c18-grandma', 'C18-016', 'narrator', '贾母一片声找宝玉', '贾母院', 2,
     '前面贾母一片声找宝玉', '贾母听说道', ['S:grandmother:grandmother_place']),
    ('c18-grandma', 'C18-017', 'grandmother', '让他姊妹们一处顽顽', '贾母院', 2,
     '贾母听说道', '黛玉被宝玉缠不过', ['E:grandmother:greet:1.0']),
    ('c18-grandma', 'C18-018', 'daiyu', '我就离了你', '贾母院 · 后房', 2,
     '黛玉被宝玉缠不过', '宝玉笑道：“你到那里，我跟到那里',
     ['S:daiyu:daiyu_place', 'S:baoyu:baoyu_greet']),
    ('c18-grandma', 'C18-019', 'baoyu', '你到那里我跟到那里', '贾母院 · 后房', 2,
     '宝玉笑道：“你到那里，我跟到那里', '宝玉道：“好妹妹，明儿另替我作个香袋儿罢',
     ['E:baoyu:greet:1.2']),
    ('c18-grandma', 'C18-020', 'daiyu', '那也只瞧我高兴', '贾母院 · 后房', 2,
     '宝玉道：“好妹妹，明儿另替我作个香袋儿罢', '一面说，一面二人出房', ['E:daiyu:greet:1.0']),
    ('c18-grandma', 'C18-021', 'narrator', '二人出房，到王夫人上房中去', '贾母院 · 房门口', 2,
     '一面说，一面二人出房', None, ['M:daiyu:daiyu_place>back_door']),

    # ---------------- 段四：女戏与妙玉 ----------------
    ('c18-xiren', 'C18-022', 'narrator', '贾蔷已从姑苏采买了十二个女孩子', '王夫人上房', 3,
     '此时王夫人那边热闹非常', '那时薛姨妈另迁于东北上', ['S:jia_qiang:court_entry']),
    ('c18-xiren', 'C18-023', 'narrator', '将梨香院早已腾挪出来', '王夫人上房', 3,
     '那时薛姨妈另迁于东北上', '又另派家中旧有曾演学过歌唱的女人们',
     ['S:xueyima:guest_seat']),
    ('c18-xiren', 'C18-024', 'narrator', '贾蔷总理物料账目', '王夫人上房', 3,
     '又另派家中旧有曾演学过歌唱的女人们', '又有林之孝家的来回', ['S:jia_qiang:court_entry']),
    ('c18-xiren', 'C18-025', 'messenger', '采访聘买得十个小尼姑，小道姑都有了', '王夫人上房', 3,
     '又有林之孝家的来回', '王夫人不等回完',
     ['S:wang:wang_host', 'S:messenger:guest_seat']),
    ('c18-xiren', 'C18-026', 'wang', '既这样，我们何不接了他来', '王夫人上房', 3,
     '王夫人不等回完', '林之孝家的回道', ['E:wang:greet:1.2']),
    ('c18-xiren', 'C18-027', 'messenger', '侯门公府，必以贵势压人', '王夫人上房', 3,
     '林之孝家的回道', '林之孝家的答应了出去', ['E:messenger:rest:1.2']),
    ('c18-xiren', 'C18-028', 'narrator', '命书启相公写请帖去请妙玉', '王夫人上房', 3,
     '林之孝家的答应了出去', None, ['H:messenger']),

    # ---------------- 段五：昼夜不闲 ----------------
    ('c18-busy', 'C18-029', 'narrator', '请凤姐去开楼拣纱绫', '荣府各处', 4,
     '当下又有人回，工程上等著糊东西的纱绫', '宝钗便说', ['S:feng:feng_room']),
    ('c18-busy', 'C18-030', 'baochai', '咱们别在这里碍手碍脚', '王夫人上房', 4,
     '宝钗便说', None,
     ['S:baochai:guest_seat', 'S:baoyu:tea_seat', 'S:daiyu:south_passage']),

    # ---------------- 段六：择日题本 ----------------
    ('c18-prepare', 'C18-031', 'narrator', '各处古董文玩，皆已陈设齐备', '荣禧堂', 5,
     '王夫人等日日忙乱，直到十月将尽', '贾政方略心意宽畅', ['S:wang:west_room']),
    ('c18-prepare', 'C18-032', 'narrator', '色色斟酌，点缀妥当', '荣禧堂', 5,
     '贾政方略心意宽畅', '于是贾政方择日题本', ['S:zheng:rongxi_center']),
    ('c18-prepare', 'C18-033', 'narrator', '奉朱批准奏：恩准贾妃省亲', '荣禧堂', 5,
     '于是贾政方择日题本', '贾府领了此恩旨', ['E:zheng:jade:1.4']),
    ('c18-prepare', 'C18-034', 'narrator', '昼夜不闲', '荣禧堂', 5,
     '贾府领了此恩旨', None, ['E:zheng:greet:1.0']),

    # ---------------- 段七：元宵关防 ----------------
    ('c18-lantern', 'C18-035', 'narrator', '太监出来先看方向', '宁荣街 · 街口', 6,
     '展眼元宵在迩，自正月初八日', '又有巡察地方总理关防太监等', ['S:messenger:outside']),
    ('c18-lantern', 'C18-036', 'narrator', '各处关防，挡围幙', '宁荣街 · 街口', 6,
     '又有巡察地方总理关防太监等', '外面又有工部官员', ['M:messenger:outside>west_corner']),
    ('c18-lantern', 'C18-037', 'narrator', '打扫街道，撵逐闲人', '宁荣街 · 街口', 6,
     '外面又有工部官员', '贾赦等督率匠人扎花灯烟火之类', ['S:zheng:rong_gate']),
    ('c18-lantern', 'C18-038', 'narrator', '这一夜，上下通不曾睡', '宁荣街 · 街口', 6,
     '贾赦等督率匠人扎花灯烟火之类', None, ['H:messenger']),
    ('c18-lantern', 'C18-039', 'narrator', '皆按品服大妆', '宁荣街 · 街口', 7,
     '至十五日五鼓，自贾母等有爵者', '贾赦等在西街门外',
     ['S:grandmother:rong_gate', 'S:xing:ning_gate']),
    ('c18-lantern', 'C18-040', 'narrator', '正等的不耐烦', '宁荣街 · 街口', 7,
     '贾赦等在西街门外', '太监道：“早多著呢', ['M:grandmother:outside>west_corner']),
    ('c18-lantern', 'C18-041', 'messenger', '只怕戌初才起身呢', '宁荣街 · 街口', 7,
     '太监道：“早多著呢', '凤姐听了道', ['S:messenger:outside']),
    ('c18-lantern', 'C18-042', 'feng', '等是时候再来也不迟', '宁荣街 · 街口', 7,
     '凤姐听了道', '于是贾母等暂且自便', ['S:feng:rong_gate', 'E:feng:greet:1.2']),
    ('c18-lantern', 'C18-043', 'narrator', '园中悉赖凤姐照理', '宁荣街 · 街口', 7,
     '于是贾母等暂且自便', None, ['M:grandmother:west_corner>rong_gate']),

    # ---------------- 段八：跪迎与版舆 ----------------
    ('c18-welcome', 'C18-044', 'narrator', '各处点灯', '宁荣街 · 街上', 8,
     '一时传人一担一担的挑进蜡烛来', '一时，有十来个太监都喘吁吁跑来拍手儿',
     ['S:messenger:street_west']),
    ('c18-welcome', 'C18-045', 'narrator', '都知道是“来了，来了”', '宁荣街 · 街上', 8,
     '一时，有十来个太监都喘吁吁跑来拍手儿', '贾赦领合族子侄在西街门外', ['E:messenger:greet:1.2']),
    ('c18-welcome', 'C18-046', 'narrator', '合族子侄跪迎', '宁荣街 · 街上', 8,
     '贾赦领合族子侄在西街门外', '忽见一对红衣太监骑马缓缓的走来',
     ['S:xing:ning_gate', 'S:grandmother:rong_gate']),
    ('c18-welcome', 'C18-047', 'narrator', '一对红衣太监骑马缓缓的走来', '宁荣街 · 街上', 8,
     '忽见一对红衣太监骑马缓缓的走来', '一对对龙旌凤翣',
     ['M:messenger:street_west>west_corner']),
    ('c18-welcome', 'C18-048', 'narrator', '龙旌凤翣，黄金伞', '宁荣街 · 街上', 8,
     '一对对龙旌凤翣', '贾母等连忙路旁跪下', ['E:messenger:greet:1.4']),
    ('c18-welcome', 'C18-049', 'narrator', '贾母等路旁跪下', '宁荣街 · 街上', 8,
     '贾母等连忙路旁跪下', '于是抬舆入门',
     ['E:grandmother:rest:1.2', 'S:wang:rong_gate']),

    # ---------------- 段九：体仁沐德 ----------------
    ('c18-change', 'C18-050', 'narrator', '抬舆入门', '荣国府 · 仪门', 8,
     '于是抬舆入门', '元春入室', ['S:yuanchun:hall_steps']),
    ('c18-change', 'C18-051', 'narrator', '体仁沐德', '荣国府 · 院落', 8,
     '元春入室', '只见园中香烟缭绕',
     ['M:yuanchun:hall_steps>hall_door', 'E:yuanchun:greet:1.2']),
    ('c18-change', 'C18-052', 'narrator', '太平气象，富贵风流', '荣国府 · 院落', 8,
     '只见园中香烟缭绕', '此时自己回想当初在大荒山中', ['E:yuanchun:greet:1.4']),
    ('c18-change', 'C18-053', 'narrator', '回想当初在大荒山中', '荣国府 · 院落', 8,
     '此时自己回想当初在大荒山中', None, ['E:yuanchun:rest:1.4']),

    # ---------------- 段十：登舟 ----------------
    ('c18-boat', 'C18-054', 'narrator', '默默叹息奢华过费', '大观园 · 园中', 9,
     '且说贾妃在轿内看此园内外如此豪华', '忽又见执拂太监跪请登舟', ['S:yuanchun:quay_west']),
    ('c18-boat', 'C18-055', 'narrator', '跪请登舟', '大观园 · 码头', 9,
     '忽又见执拂太监跪请登舟', '只见清流一带', ['M:yuanchun:quay_west>reed_bend']),
    ('c18-boat', 'C18-056', 'narrator', '清流一带，势如游龙', '大观园 · 水上', 9,
     '只见清流一带', '诸灯上下争辉', ['E:yuanchun:greet:1.4']),
    ('c18-boat', 'C18-057', 'narrator', '玻璃世界，珠宝乾坤', '大观园 · 水上', 9,
     '诸灯上下争辉', '船上亦系各种精致盆景诸灯', ['E:yuanchun:jade:1.2']),
    ('c18-boat', 'C18-058', 'narrator', '蓼汀花溆', '大观园 · 石港', 9,
     '船上亦系各种精致盆景诸灯', '按此四字并', ['M:yuanchun:reed_bend>bank_near']),
    ('c18-boat', 'C18-059', 'narrator', '皆系上回贾政偶然一试', '大观园 · 石港', 9,
     '按此四字并', '待蠢物将原委说明，大家方知', ['S:zheng:quay_east']),
    ('c18-boat', 'C18-060', 'narrator', '自幼亦系贾母教养', '大观园 · 舟中', 10,
     '当日这贾妃未入宫时', '眷念切爱之心，刻未能忘', ['E:yuanchun:rest:1.4']),
    ('c18-boat', 'C18-061', 'narrator', '聊一试其情思之清浊', '大观园 · 舟中', 10,
     '前日贾政闻塾师背后赞宝玉偏才尽有', '然想来倒不如这本家风味有趣',
     ['E:yuanchun:rest:1.2']),
    ('c18-boat', 'C18-062', 'narrator', '故此竟用了宝玉所题之联额', '大观园 · 舟中', 10,
     '更使贾妃见之，知系其爱弟所为', None, ['E:yuanchun:greet:1.2']),

    # ---------------- 段十一：换匾受礼 ----------------
    ('c18-palace', 'C18-063', 'yuanchun', '“花溆”二字便妥', '省亲别墅 · 行宫外', 11,
     '闲文少述，且说贾妃看了四字', '侍座太监听了',
     ['S:yuanchun:ceremonial_gate', 'E:yuanchun:greet:1.2']),
    ('c18-palace', 'C18-064', 'narrator', '贾政听了，即忙移换', '省亲别墅 · 岸边', 11,
     '侍座太监听了', '一时，舟临内岸', ['S:zheng:rongxi_steps']),
    ('c18-palace', 'C18-065', 'narrator', '天仙宝境改省亲别墅', '省亲别墅 · 牌坊', 11,
     '一时，舟临内岸', '但见庭燎烧空', ['S:yuanchun:ceremonial_gate', 'E:yuanchun:jade:1.2']),
    ('c18-palace', 'C18-066', 'narrator', '庭燎烧空，香屑布地', '省亲别墅 · 行宫', 11,
     '但见庭燎烧空', None, ['E:yuanchun:greet:1.4']),
    ('c18-palace', 'C18-067', 'narrator', '金门玉户神仙府', '省亲别墅 · 正殿', 12,
     '金门玉户神仙府', None, ['S:yuanchun:rongxi_center']),
    ('c18-palace', 'C18-068', 'narrator', '此殿何无匾额', '省亲别墅 · 正殿', 13,
     '贾妃乃问：“此殿何无匾额', '礼仪太监跪请升座受礼', ['S:messenger:rongxi_door']),
    ('c18-palace', 'C18-069', 'narrator', '殿上昭容传谕曰“免”', '省亲别墅 · 月台下', 13,
     '礼仪太监跪请升座受礼', '又有太监引荣国太君', ['S:zheng:rongxi_steps']),
    ('c18-palace', 'C18-070', 'narrator', '自东阶升月台上排班', '省亲别墅 · 东阶', 13,
     '又有太监引荣国太君', None, ['S:grandmother:east_door', 'S:wang:east_court']),

    # ---------------- 段十二：家礼相见 ----------------
    ('c18-home', 'C18-071', 'narrator', '退入侧殿更衣', '贾母正室 · 侧殿', 14,
     '茶已三献，贾妃降座，乐止', '至贾母正室，欲行家礼', ['S:yuanchun:tea_place']),
    ('c18-home', 'C18-072', 'narrator', '一手搀贾母，一手搀王夫人', '贾母正室', 14,
     '至贾母正室，欲行家礼', '邢夫人，李纨，王熙凤',
     ['S:yuanchun:grandmother_place', 'S:grandmother:grandmother_greet']),
    ('c18-home', 'C18-073', 'narrator', '俱在旁围绕，垂泪无言', '贾母正室', 14,
     '邢夫人，李纨，王熙凤', '邢夫人等忙上来解劝',
     ['S:xing:tea_place', 'S:liwan:liwan_place', 'S:feng:feng_place',
      'S:yingchun:yingchun_place', 'S:tanchun:tanchun_place', 'S:xichun:xichun_place']),
    ('c18-home', 'C18-074', 'narrator', '半日，贾妃方忍悲强笑', '贾母正室', 14,
     '邢夫人等忙上来解劝', '然后东西两府掌家执事人丁',
     ['E:yuanchun:rest:1.4', 'H:xing', 'H:liwan', 'H:feng', 'H:yingchun', 'H:tanchun', 'H:xichun']),
    ('c18-home', 'C18-075', 'narrator', '执事人丁在厅外行礼', '贾母正室 · 厅外', 14,
     '然后东西两府掌家执事人丁', '贾妃因问', ['S:messenger:back_door']),
    ('c18-home', 'C18-076', 'yuanchun', '薛姨妈，宝钗，黛玉因何不见', '贾母正室', 14,
     '贾妃因问', '贾妃听了，忙命快请', ['E:yuanchun:greet:1.2']),
    ('c18-home', 'C18-077', 'narrator', '忙命快请', '贾母正室', 14,
     '贾妃听了，忙命快请', '又有贾妃原带进宫去的丫鬟抱琴等',
     ['S:xueyima:tea_place', 'S:baochai:baoyu_greet', 'S:daiyu:daiyu_place']),
    ('c18-home', 'C18-078', 'narrator', '抱琴等上来叩见', '贾母正室', 14,
     '又有贾妃原带进宫去的丫鬟抱琴等', '执事太监及彩嫔',
     ['H:xueyima', 'H:baochai', 'H:daiyu', 'S:messenger:maid_place']),
    ('c18-home', 'C18-079', 'narrator', '母女姊妹深叙离别情景', '贾母正室', 14,
     '执事太监及彩嫔', '又有贾政至帘外问安', ['E:yuanchun:rest:1.2']),
    ('c18-home', 'C18-080', 'narrator', '贾政至帘外问安', '贾母正室 · 帘外', 14,
     '又有贾政至帘外问安', '又隔帘含泪谓其父曰', ['S:zheng:back_door']),
    ('c18-home', 'C18-081', 'yuanchun', '今虽富贵已极，骨肉各方', '贾母正室 · 帘外', 14,
     '又隔帘含泪谓其父曰', '贾政亦含泪启道', ['E:yuanchun:rest:1.4']),
    ('c18-home', 'C18-082', 'zheng', '臣，草莽寒门', '贾母正室 · 帘外', 14,
     '贾政亦含泪启道', '贾妃亦嘱', ['E:zheng:rest:1.4']),
    ('c18-home', 'C18-083', 'yuanchun', '只以国事为重', '贾母正室', 14,
     '贾妃亦嘱', '贾政又启：“园中所有亭台轩馆', ['E:yuanchun:greet:1.0']),
    ('c18-home', 'C18-084', 'narrator', '果进益了', '贾母正室', 14,
     '贾政又启：“园中所有亭台轩馆', '贾妃见宝，林二人亦发',
     ['S:baoyu:baoyu_greet', 'E:yuanchun:greet:1.2']),
    ('c18-home', 'C18-085', 'narrator', '真是姣花软玉一般', '贾母正室', 14,
     '贾妃见宝，林二人亦发', '因问：“宝玉为何不进见', ['S:daiyu:daiyu_place']),
    ('c18-home', 'C18-086', 'yuanchun', '比先竟长了好些', '贾母正室', 14,
     '因问：“宝玉为何不进见', None,
     ['M:baoyu:baoyu_greet>grandmother_greet', 'E:yuanchun:rest:1.6']),

    # ---------------- 段十三：赐名题诗 ----------------
    ('c18-name', 'C18-087', 'narrator', '筵宴齐备，请贵妃游幸', '大观园 · 园门', 15,
     '尤氏，凤姐等上来启道', '进园来先从', ['S:you_shi:tea_place', 'S:feng:feng_place']),
    ('c18-name', 'C18-088', 'narrator', '登楼步阁，涉水缘山', '大观园 · 园中', 15,
     '进园来先从', '贾妃极加奖赞', ['M:yuanchun:grandmother_place>baoyu_greet']),
    ('c18-name', 'C18-089', 'yuanchun', '以后不可太奢', '大观园 · 园中', 15,
     '贾妃极加奖赞', '已而至正殿，谕免礼归座', ['E:yuanchun:greet:1.2']),
    ('c18-name', 'C18-090', 'narrator', '大开筵宴', '大观园 · 正殿', 15,
     '已而至正殿，谕免礼归座', None, ['H:you_shi', 'S:liwan:liwan_place', 'H:feng']),
    ('c18-name', 'C18-091', 'narrator', '亲搦湘管，择其几处最喜者赐名', '大观园 · 正殿', 16,
     '元妃乃命传笔砚伺候', None, ['S:yuanchun:grandmother_place', 'E:yuanchun:jade:1.4']),
    ('c18-name', 'C18-092', 'narrator', '顾恩思义', '大观园 · 正殿', 17,
     '“顾恩思义”匾额', '@P18', ['E:yuanchun:jade:1.4']),
    ('c18-name', 'C18-093', 'narrator', '大观园之名', '大观园 · 正殿', 20,
     '“大观园”园之名', '又命旧有匾联俱不必摘去', ['E:yuanchun:greet:1.4']),
    ('c18-name', 'C18-094', 'narrator', '衔山抱水建来精', '大观园 · 正殿', 21,
     '衔山抱水建来精', None, ['S:yuanchun:tea_place']),
    ('c18-name', 'C18-095', 'yuanchun', '今夜聊以塞责', '大观园 · 正殿', 22,
     '写毕，向诸姊妹笑道', '是我意外之想', ['E:yuanchun:greet:1.2']),
    ('c18-name', 'C18-096', 'yuanchun', '我所极爱的是潇湘馆与蘅芜苑', '大观园 · 正殿', 22,
     '此中“潇湘馆”，“蘅芜苑”二处，我所极爱', None, ['E:yuanchun:greet:1.2']),
    ('c18-name', 'C18-097', 'narrator', '要算探春又出于姊妹之上', '大观园 · 正殿', 23,
     '迎，探，惜三人之中', None,
     ['S:tanchun:tanchun_place', 'S:xichun:xichun_place', 'S:yingchun:yingchun_place',
      'S:liwan:liwan_place']),
    ('c18-name', 'C18-098', 'yingchun', '旷性怡情', '大观园 · 正殿', 24,
     '“旷性怡情”匾额', '@P26', ['E:yingchun:jade:1.4']),
    ('c18-name', 'C18-099', 'tanchun', '万象争辉', '大观园 · 正殿', 27,
     '“万象争辉”匾额', '@P29', ['E:tanchun:jade:1.4']),
    ('c18-name', 'C18-100', 'xichun', '文章造化', '大观园 · 正殿', 30,
     '“文章造化”匾额', '@P32', ['E:xichun:jade:1.4']),
    ('c18-name', 'C18-101', 'liwan', '文采风流', '大观园 · 正殿', 33,
     '“文采风流”匾额', '@P35', ['E:liwan:jade:1.4']),
    ('c18-name', 'C18-102', 'baochai', '凝晖钟瑞', '大观园 · 正殿', 36,
     '“凝晖钟瑞”匾额', '@P38', ['S:baochai:tea_place', 'E:baochai:jade:1.4']),
    ('c18-name', 'C18-103', 'daiyu', '世外仙源', '大观园 · 正殿', 39,
     '“世外仙源”匾额', '@P41', ['S:daiyu:daiyu_place', 'E:daiyu:jade:1.4']),
    ('c18-name', 'C18-104', 'yuanchun', '终是薛林二妹之作与众不同', '大观园 · 正殿', 42,
     '贾妃看毕，称赏一番', '原来林黛玉安心今夜大展奇才', ['E:yuanchun:greet:1.2']),
    ('c18-name', 'C18-105', 'narrator', '只胡乱作一首五言律应景罢了', '大观园 · 正殿', 42,
     '原来林黛玉安心今夜大展奇才', None, ['E:daiyu:rest:1.2']),

    # ---------------- 段十四：绿蜡与杏帘 ----------------
    ('c18-poem', 'C18-106', 'narrator', '起草内有“绿玉春犹卷”一句', '大观园 · 宝玉案旁', 43,
     '彼时宝玉尚未作完', '宝钗转眼瞥见', ['S:baoyu:baoyu_greet', 'E:baoyu:jade:1.4']),
    ('c18-poem', 'C18-107', 'baochai', '岂不是有意和他争驰了', '大观园 · 宝玉案旁', 43,
     '宝钗转眼瞥见', '宝玉见宝钗如此说',
     ['S:baochai:tea_place', 'M:baochai:tea_place>baoyu_greet']),
    ('c18-poem', 'C18-108', 'baoyu', '总想不起什么典故出处来', '大观园 · 宝玉案旁', 43,
     '宝玉见宝钗如此说', '宝钗笑道：“你只把“绿玉”的“玉”字改作“蜡”字就是了',
     ['E:baoyu:rest:1.2']),
    ('c18-poem', 'C18-109', 'baochai', '改作“蜡”字就是了', '大观园 · 宝玉案旁', 43,
     '宝钗笑道：“你只把“绿玉”的“玉”字改作“蜡”字就是了', '宝玉听了，不觉洞开心臆',
     ['E:baochai:greet:1.4']),
    ('c18-poem', 'C18-110', 'baochai', '冷烛无烟绿蜡干', '大观园 · 宝玉案旁', 43,
     '宝钗见问，悄悄的咂嘴点头笑道', '宝玉听了，不觉洞开心臆', ['E:baochai:rest:1.2']),
    ('c18-poem', 'C18-111', 'baoyu', '真可谓“一字师”了', '大观园 · 宝玉案旁', 43,
     '宝玉听了，不觉洞开心臆', '宝钗亦悄悄的笑道', ['E:baoyu:greet:1.4']),
    ('c18-poem', 'C18-112', 'baochai', '那上头穿黄袍的才是你姐姐', '大观园 · 宝玉案旁', 43,
     '宝钗亦悄悄的笑道', None, ['E:baochai:greet:1.2']),
    ('c18-poem', 'C18-113', 'narrator', '何不代他作两首', '大观园 · 宝玉案旁', 44,
     '此时林黛玉未得展其抱负', '想著，便也走至宝玉案旁', ['E:daiyu:rest:1.2']),
    ('c18-poem', 'C18-114', 'daiyu', '我也替你作出这首了', '大观园 · 宝玉案旁', 44,
     '想著，便也走至宝玉案旁', '说毕，低头一想',
     ['M:daiyu:daiyu_place>baoyu_greet']),
    ('c18-poem', 'C18-115', 'narrator', '比自己所作的三首高过十倍', '大观园 · 宝玉案旁', 44,
     '说毕，低头一想', None, ['E:baoyu:greet:1.4']),
    ('c18-poem', 'C18-116', 'baoyu', '有凤来仪', '大观园 · 宝玉案旁', 45,
     '有凤来仪', '@P47', ['E:baoyu:jade:1.4']),
    ('c18-poem', 'C18-117', 'baoyu', '蘅芷清芬', '大观园 · 宝玉案旁', 48,
     '蘅芷清芬', '@P49', ['E:baoyu:jade:1.4']),
    ('c18-poem', 'C18-118', 'baoyu', '怡红快绿', '大观园 · 宝玉案旁', 50,
     '怡红快绿', '@P51', ['E:baoyu:jade:1.4']),
    ('c18-poem', 'C18-119', 'daiyu', '杏帘在望', '大观园 · 宝玉案旁', 52,
     '杏帘在望', '@P53', ['E:daiyu:jade:1.6']),

    # ---------------- 段十五：点戏四出 ----------------
    ('c18-drama', 'C18-120', 'narrator', '快拿戏目来', '梨香院 · 楼下', 55,
     '那时贾蔷带领十二个女戏', '贾蔷急将锦册呈上', ['S:jia_qiang:yard']),
    ('c18-drama', 'C18-121', 'messenger', '只点了四出戏', '梨香院 · 楼下', 55,
     '贾蔷急将锦册呈上', None, ['S:messenger:gate']),
    ('c18-drama', 'C18-122', 'narrator', '作尽悲欢情状', '梨香院 · 戏台前', 56,
     '贾蔷忙张罗扮演起来', '刚演完了', ['S:jia_qiang:stair']),
    ('c18-drama', 'C18-123', 'messenger', '谁是龄官', '梨香院 · 席前', 56,
     '刚演完了', '太监又道：“贵妃有谕', ['S:messenger:box']),
    ('c18-drama', 'C18-124', 'messenger', '龄官极好，再作两出戏', '梨香院 · 席前', 56,
     '太监又道：“贵妃有谕', '龄官自为此二出原非本角之戏', ['E:jia_qiang:greet:1.2']),
    ('c18-drama', 'C18-125', 'narrator', '定要作《相约》《相骂》二出', '梨香院 · 戏台前', 56,
     '龄官自为此二出原非本角之戏', '贾妃甚喜', ['E:jia_qiang:rest:1.2']),
    ('c18-drama', 'C18-126', 'yuanchun', '不可难为了这女孩子', '梨香院 · 席前', 56,
     '贾妃甚喜', '然后撤筵', ['S:yuanchun:box', 'E:yuanchun:greet:1.4']),
    ('c18-drama', 'C18-127', 'narrator', '苦海慈航', '梨香院 · 佛寺', 56,
     '然后撤筵', None, ['E:yuanchun:jade:1.2']),

    # ---------------- 段十六：赐物与回銮 ----------------
    ('c18-gift', 'C18-128', 'messenger', '赐物俱齐，请验等例', '梨香院 · 席前', 57,
     '少时，太监跪启：“赐物俱齐，请验等例', '原来贾母的是', ['S:messenger:gate']),
    ('c18-gift', 'C18-129', 'narrator', '金、玉如意各一柄', '梨香院 · 席前', 57,
     '原来贾母的是', '邢夫人、王夫人二分', ['S:grandmother:box']),
    ('c18-gift', 'C18-130', 'narrator', '宝钗，黛玉诸姊妹等', '梨香院 · 席前', 57,
     '邢夫人、王夫人二分', '外表礼二十四端',
     ['S:baochai:stair', 'S:daiyu:yard']),
    ('c18-gift', 'C18-131', 'narrator', '是赐东西两府凡园中管理工程的人', '梨香院 · 席前', 57,
     '外表礼二十四端', None, ['S:baoyu:box', 'S:jia_qiang:yard']),
    ('c18-gift', 'C18-132', 'narrator', '时已丑正三刻，请驾回銮', '梨香院 · 席前', 58,
     '众人谢恩已毕，执事太监启道', '贾妃听了', ['E:yuanchun:rest:1.2']),
    ('c18-gift', 'C18-133', 'yuanchun', '好生自养', '梨香院 · 席前', 58,
     '贾妃听了', '贾母等已哭的哽噎难言了', ['E:yuanchun:rest:1.4']),
    ('c18-gift', 'C18-134', 'narrator', '忍心上舆去了', '梨香院 · 席前', 58,
     '贾母等已哭的哽噎难言了', '这里诸人好容易', ['E:grandmother:rest:1.4']),
    ('c18-gift', 'C18-135', 'narrator', '且看下回', '梨香院 · 园门', 58,
     '这里诸人好容易', None, ['M:yuanchun:box>gate']),
]

# 改编推定：不是原文写明的取舍，在证据表里如实记下。
DESIGN_NOTES = [
    ('C18-D001', 'c18-boat', '大观园登舟一段复用 `canal`（运河）舞台',
     '原文只写「忽又见执拂太监跪请登舟」「清流一带，势如游龙」，没有写园中水道的样子。',
     '复用已有运河图表现舟行；`canal` 的三组码头与苇岸用来分置下舆、临岸与传话的位置。'
     '大观园专属地图尚不存在，此处为就近取用，不改写原文的「登舟」二字。'),
    ('C18-D002', 'c18-name', '赐名题诗一段复用 `dinner`（贾母院）舞台',
     '原文写元妃在园中赐名命题，园内各景并未逐一落到某处屋宇。',
     '大观园专图尚未建成，`dinner` 是第 17 回试才题对额已验证过的舞台，本回沿用同一处，'
     '避免同一场景在相邻两回之间跳变。'),
    ('C18-D003', 'c18-drama', '点戏与焚香两处并入 `c11_tianxiang`（天香楼）舞台',
     '原文先写女戏在楼下点戏四出，撤筵后又写「忽见山环佛寺」焚香拜佛。',
     '铁槛寺、水月庵都是第 15 回为停灵与尼庵所建，若挪来当大观园里的佛寺，'
     '图鉴上会出现「铁槛寺」的字样，与本回的大观园相混。故并入戏台一段，'
     '以叙述交代其另有一处佛寺，不另开场景。'),
    ('C18-D004', 'c18-xiren', '林之孝家的与龄官均以 `messenger`（来人）代指',
     '原文写林之孝家的回话、龄官拒演《游园》《惊梦》，二人都有名字与性情。',
     '本回不新增角色立绘，来人一栏沿用 `messenger` 代指所有传话、传旨、跑腿之人；'
     '龄官因「执意不作」而见性情，见于节点正文，未单独立绘。'),
    ('C18-D005', 'c18-home', '抱琴、执事太监、随行宫人皆以 `messenger` 代指',
     '原文写抱琴等叩见、执事太监与彩嫔昭容侍从人等，另有贾珍、贾琏、贾环、贾蓉等受赐。',
     '这些人只在传话与受赐名录中出现，未与主角对谈，故不入 cast，'
     '一律以 `messenger` 代指；受赐名录里出现的名字保留在正文中。'),
]


def build():
    """把节点定义转成 story step。"""
    steps = []
    for sec_id, nid, speaker, title, place, para, start, end, codes in CUTS:
        raw, lead = cut(para, start, end)
        steps.append({
            'chapter': sec_id,
            'scene': None,
            'place': place,
            'focus': '',
            'source': {
                'chapter': 18,
                'paragraphLead': lead,
                'textKind': 'adaptation',
                'layer': 'present',
            },
            'id': nid,
            'speaker': speaker,
            'text': to_display(raw),
            'title': title,
            'actions': parse_actions(codes),
        })
    return steps


def assign_scenes(steps):
    """段落定 scene；focus 优先取第一个 show 的落点，其次取 move 的终点，
    都没有就沿用同一段里上一个节点的落点——镜头该看哪儿，得跟着人走。"""
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
    """逐条校验，返回错误列表。"""
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
    return errors


def check_anchors(steps):
    """锚点必须在该场景的 Anchors 层里真实存在。"""
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

    for step in steps:
        scene = step['scene']
        names = anchors.get(scene)
        if names is None:
            errors.append(f'{step["id"]}: 场景 {scene} 不存在')
            continue
        for act in step['actions']:
            at = act.get('at')
            if at and at not in names:
                errors.append(f'{step["id"]}: 锚点 {at} 不在场景 {scene} 中')
            for anchor in act.get('via') or []:
                if anchor not in names:
                    errors.append(f'{step["id"]}: 路径锚点 {anchor} 不在场景 {scene} 中')
        if step['focus'] and step['focus'] not in names:
            errors.append(f'{step["id"]}: focus {step["focus"]} 不在场景 {scene} 中')
    return errors


def build_evidence(steps):
    """证据表：每个节点一条原文依据，外加改编推定条目。"""
    evidence = []
    for step in steps:
        excerpt = step['text']
        if len(excerpt) > 120:
            excerpt = excerpt[:120] + '…'
        evidence.append({
            'id': step['id'].replace('C18-', 'C18-E'),
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
        'chapter': 18,
        'source': {
            'edition': '维基文库《紅樓夢》第 018 回（繁体原文页）',
            'url': 'https://zh.wikisource.org/w/index.php?title=紅樓夢/第018回&action=raw',
            'retrievedAt': '2026-11-10',
            'localText': 'docs/chapter18-source.txt',
            'processing': 'MediaWiki API action=query&prop=revisions&rvprop=content 取回 wikitext；'
                         '去除模板与文末导航行；由 OpenCC t2s 转简体，按维基段落拆行；正文未作增删。',
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
        print('第18回校验未通过，未写盘：')
        for e in errors:
            print('  ERROR', e)
        return 1

    if '--check' in sys.argv:
        print(f'第18回校验通过：{len(steps)} 节点 / {len(SECTIONS)} 段')
        return 0

    STORY.write_text(json.dumps(steps, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    sections = []
    for sec_id, title, scene in SECTIONS:
        start = next(st['id'] for st in steps if st['chapter'] == sec_id)
        sections.append({'id': sec_id, 'title': title, 'scene': scene, 'start': start, 'book': 18})
    SECTION_FILE.write_text(json.dumps(sections, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    evidence = build_evidence(steps)
    EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'第18回已写入：{len(steps)} 节点 / {len(sections)} 段 / {len(evidence["evidence"])} 条证据')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
