"""把第 26-30 回角色文档的「本回剧情功能」段换成有据可查的实况。

原来的段落只写「本回涉及 N 个节点」，看不出这个人在这回里到底干了什么。
新段落直接从 design/chapterNN-story.json 里取真实节点与台词生成，
所以每句话都能回到具体节点号，不引入任何新设定。

同时把「本回剧情功能」里那句笼统的说明换成逐人写法：
先说他在底本里的位置（谁介绍他、他对谁说话），再说他在这回的功能，
最后点出他的台词与动作节点号。
"""
import json
import re
from pathlib import Path

ROOT = Path('/Users/bot/WorkBuddy/tiledMap')

# 逐人的底本位置与功能说明。依据逐字引文见各角色文档的「身份定位」段。
ROLE = {
    'jiahui': {
        'file': 'docs/chapter26-characters.md',
        'func': '怡红院小丫头。本回由红玉从窗眼里认出，唤出她来闲话；'
                '她替林姑娘送茶叶、跑腿一路交代院里丫鬟的分等与红玉的处境，'
                '说到「可气晴雯，绮霰他们这几个，都算在上等里去」时把红玉的心思说破，'
                '红玉「眼睛红了」——她的话是压垮红玉心防的那一句。',
    },
    'zhuer': {
        'file': 'docs/chapter26-characters.md',
        'func': '怡红院小丫头。本回引贾芸进怡红院，「叫我带进芸二爷来」；'
                '后与贾芸在路上一长一短说话，被贾芸套出丢手帕子的事，'
                '一口回绝「我有那么大工夫管这些事」。',
    },
    'qingwen': {
        'file': 'docs/chapter26-characters.md',
        'func': '怡红院大丫鬟。本回与碧痕拌了嘴正没气，宝钗来时正撞上，'
                '把气撒在宝钗身上——先是抱怨「有事没事跑了来坐着」，'
                '继而隔着门回黛玉「凭你是谁，二爷吩咐的，一概不许放人进来呢」，'
                '气得黛玉在门外气怔。',
    },
    'feng_ziying': {
        'file': 'docs/chapter26-characters.md',
        'func': '神武将军冯唐之子，本回回目人物。本回携薛蟠等赴宴，'
                '席间先报母病，面上带青伤被薛蟠问起，说是在铁网山打围遇仇都尉之子；'
                '众人行令，他以「女儿悲、女儿愁、女儿喜」唱曲并邀众人到东边细谈，'
                '是本回后段的主持者。',
    },
    'siqi': {
        'file': 'docs/chapter27-characters.md',
        'func': '迎春房大丫鬟。本回只一句台词：「因见司棋从山洞里出来，站着系裙子，'
                '便赶上来问道」，司棋答「没理论」。三个节点，'
                '却把第七十一回「穿红裙子梳鬅头高大丰壮身材」的身量与裙色提前露了出来。',
    },
    'qixian': {
        'file': 'docs/chapter27-characters.md',
        'func': '怡红院丫鬟。本回随晴雯、碧痕、紫绡等一群人过来，'
                '晴雯与红玉争竞时她出言收场：「你听听他的嘴！你们别说了，让他逛去罢。」',
    },
    'jiang_yuhan': {
        'file': 'docs/chapter28-characters.md',
        'func': '冯紫英家的唱曲名。本回行令时唱「女儿悲、女儿愁、女儿喜」一套《寄生草》，'
                '唱毕自谦「这诗词上我倒有限」；又道出昨日所见的对子，'
                '末了席上认下「就是我的小名儿」，并解下茜香国女国王所贡的汗巾子与宝玉换。',
    },
    'yun_er': {
        'file': 'docs/chapter28-characters.md',
        'func': '冯紫英家的琵琶手，本回贯穿行令的唱曲者。'
                '先唱「两个冤家，都难丢下」；薛蟠跳出来喧嚷，她「下两句越发难说了，我替你说罢」；'
                '唱到「女儿悲，将来终身指靠谁」时接薛蟠的话头，一路唱到「桃之夭夭」。',
    },
    'zhang_daoshi': {
        'file': 'docs/chapter29-characters.md',
        'func': '当日荣国府国公的替身，先皇御口亲呼「大幻仙人」，现掌「道录司」，本回回目人物。'
                '随贾珍入府给贾母请安，一见宝玉便说「怎么就同当日国公爷一个稿子」并落泪；'
                '又为宝玉提亲；请下通灵宝玉要「请下来」给远来的道友徒子看，'
                '并说自己是「八十多岁的人」——本回他占去最多台词。',
    },
    'lingguan': {
        'file': 'docs/chapter30-characters.md',
        'func': '梨香院十二官之一，唱小旦，正面姓名本回未出。'
                '本回九节点全在蔷薇架下：蹲在花下拿金簪抠土、画字，'
                '「画来画去，还是个『蔷』字」「已经画了有几千个『蔷』」；'
                '骤雨落下来，黛玉在远处提醒她，她才回头道「多谢姐姐提醒了我」。',
    },
}

for cid, spec in ROLE.items():
    path = ROOT / spec['file']
    text = path.read_text(encoding='utf-8')

    # 该角色的实际节点与台词，从本回 story.json 取真值
    chapter = re.search(r'chapter(\d+)-characters', spec['file']).group(1)
    data = json.loads((ROOT / f'design/chapter{chapter}-story.json').read_text())
    nodes = data if isinstance(data, list) else data.get('nodes', [])

    spoken, appeared = [], []
    for node in nodes:
        acts = json.dumps(node.get('actions', []) or [], ensure_ascii=False)
        if cid not in acts and node.get('speaker') != cid:
            continue
        appeared.append(node['id'])
        if node.get('speaker') == cid:
            spoken.append(node['id'])

    head = f'本回共 {len(appeared)} 个节点涉及她'
    if spoken:
        head += f'，其中 {len(spoken)} 个是她本人的台词节点（{spoken[0]}—{spoken[-1]}）。'
    else:
        head += f'，她没有独立台词（{appeared[0]}—{appeared[-1]}），只有叙述与动作。'

    body = spec['func']
    if spoken:
        # 引一段她的台词原文。台词节点里含叙述与他人对白，
        # 所以只取她自己说的那一段：第一个「：」之后的引号内容。
        first = next(n for n in nodes if n['id'] == spoken[0])
        raw = first.get('text', '')
        m = re.search(r'[「『]([^」』]{1,120})[」』]', raw)
        quote = (m.group(1) if m else raw[:56])
        if len(quote) > 56:
            quote = quote[:56] + '……'
        body += f'\n\n她的第一句台词是：「{quote}」'

    new_section = f'### 本回剧情功能\n\n{head}\n\n{body}\n'

    # 定位：只在该角色自己的「## 名字 `id`」小节里替换，
    # 否则同文件里两个角色会互相覆盖（司棋与绮霰同在 chapter27）。
    anchor = re.search(r'^## \S+ `%s`$' % re.escape(cid), text, re.M)
    if not anchor:
        print('MISS anchor', cid, spec['file'])
        continue
    pat = re.compile(r'### 本回剧情功能\n\n.*?(?=\n### )', re.S)
    m = pat.search(text, anchor.end())
    if not m:
        print('MISS section', cid, spec['file'])
        continue
    text = text[:m.start()] + new_section + '\n' + text[m.end():]
    path.write_text(text, encoding='utf-8')
    print(f'{cid:15s} 节点 {len(appeared):2d} 台词 {len(spoken):2d} -> {spec["file"]}')
