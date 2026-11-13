"""Rebuild the last three sections of chapter 17 so the chapter stays inside
its own boundaries in the original book.

Chapter 17 of the novel is the tour of the new garden: 贾政 walks 宝玉 round,
the visitors argue over names for every spot, and 宝玉 writes the plaques. The
chapter ends with the visitors leaving and 贾政 giving 宝玉 one night to come
up with a title for the main hall.

The draft had drifted past that. It carried the announcement by 夏守忠 that
belongs to the end of chapter 16 (where chapter 16 already has it, twice over),
and then the purchase of the festival goods, the drilling of the reception
ceremony and the countdown to the Lantern Festival, which all belong to
chapter 18. That put the edict after the tour even though the tour already
refers to the coming visit — the events ran backwards.

This script replaces those three sections with the tour's real ending, taken
from the base text in `docs/chapter17-source.txt`: the main hall and its stone
archway, 宝玉's sudden recognition of a place he cannot place, 贾政's one-night
ultimatum, and the walk out through 沁芳闸.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
STORY = ROOT / 'design/chapter17-story.json'
SECTIONS = ROOT / 'design/chapter17-sections.json'


def step(node_id, chapter, scene, place, focus, lead, speaker, title, text, actions):
    return {
        'chapter': chapter,
        'scene': scene,
        'place': place,
        'focus': focus,
        'source': {'chapter': 17, 'paragraphLead': lead, 'textKind': 'adaptation', 'layer': 'present'},
        'id': node_id,
        'speaker': speaker,
        'text': text,
        'title': title,
        'actions': actions,
    }


# The tour's own ending. Every paragraph lead is the opening words of the
# paragraph it adapts, as the other chapters record them.
NEW_NODES = [
    # 四、正殿题额 · 蓬莱仙境
    step('C17-030', 'c17-edict', 'dinner', '大观园 · 正殿', 'tea_place',
         '说著，大家出来。行不多远，则见崇阁巍峨',
         'narrator', '正殿崇阁',
         '说著大家出来，行不多远，便见崇阁巍峨，层楼高起，面面琳宫合抱，迢迢复道萦纡，青松拂檐，玉栏绕砌，金辉兽面，彩焕螭头。贾政道：「这是正殿了，只是太富丽了些。」',
         [{'type': 'show', 'actor': 'zheng', 'at': 'tea_place'},
          {'type': 'show', 'actor': 'baoyu', 'at': 'baoyu_greet'}]),
    step('C17-031', 'c17-edict', 'dinner', '大观园 · 正殿', 'wang_place',
         '这是正殿了，只是太富丽了些',
         'zheng', '太富丽了些',
         '贾政道：「这是正殿了，只是太富丽了些。」众人都道：「要如此方是。虽然贵妃崇节尚俭，天性恶繁悦朴，然今日之尊，礼仪如此，不为过也。」',
         [{'type': 'show', 'actor': 'zheng', 'at': 'wang_place'},
          {'type': 'show', 'actor': 'messenger', 'at': 'feng_place'}]),
    step('C17-032', 'c17-edict', 'dinner', '大观园 · 牌坊', 'feng_place',
         '一面说，一面走，只见正面现出一座玉石牌坊来',
         'narrator', '玉石牌坊',
         '一面说，一面走，只见正面现出一座玉石牌坊来，上面龙蟠螭护，玲珑凿就。贾政道：「此处书以何文？」众人道：「必是『蓬莱仙境』方妙。」贾政摇头不语。',
         [{'type': 'show', 'actor': 'baoyu', 'at': 'feng_place'},
          {'type': 'show', 'actor': 'messenger', 'at': 'tea_place'}]),
    step('C17-033', 'c17-edict', 'dinner', '大观园 · 牌坊', 'baoyu_greet',
         '宝玉见了这个所在，心中忽有所动',
         'baoyu', '若有所悟',
         '宝玉见了这个所在，心中忽有所动，寻思起来，倒象那里曾见过的一般，却一时想不起那年月日的事了。贾政又命他作题，宝玉只顾细思前景，全无心于此了。',
         [{'type': 'show', 'actor': 'baoyu', 'at': 'baoyu_greet'}]),
    step('C17-034', 'c17-edict', 'dinner', '大观园 · 牌坊', 'tea_place',
         '众人不知其意，只当他受了这半日的折磨',
         'messenger', '清客劝罢',
         '众人不知其意，只当他受了这半日的折磨，精神耗散，才尽词穷了，再要考难逼迫，著了急，或生出事来，倒不便。遂忙都劝贾政：「罢，罢，明日再题罢了。」',
         [{'type': 'show', 'actor': 'messenger', 'at': 'tea_place'}]),
    step('C17-035', 'c17-edict', 'dinner', '大观园 · 牌坊', 'wang_place',
         '限你一日，明日若再不能，我定不饶',
         'zheng', '限题一日',
         '贾政心中也怕贾母不放心，遂冷笑道：「你这畜生，也竟有不能之时了。也罢，限你一日，明日若再不能，我定不饶。这是要紧一处，更要好生作来！」',
         [{'type': 'show', 'actor': 'zheng', 'at': 'wang_place'}]),

    # 五、沁芳闸 · 归途
    step('C17-040', 'c17-jubilant', 'dinner', '大观园 · 沁芳闸', 'baoyu_greet',
         '说著，引客行来，至一大桥前',
         'narrator', '至一大桥前',
         '说著引客行来，至一大桥前，见水如晶帘一般奔入。原来这桥便是通外河之闸，引泉而入者。贾政因问：「此闸何名？」',
         [{'type': 'show', 'actor': 'zheng', 'at': 'tea_place'},
          {'type': 'show', 'actor': 'baoyu', 'at': 'baoyu_greet'}]),
    step('C17-041', 'c17-jubilant', 'dinner', '大观园 · 沁芳闸', 'baoyu_greet',
         '此乃沁芳泉之正源，就名「沁芳闸」',
         'baoyu', '沁芳闸',
         '宝玉道：「此乃沁芳泉之正源，就名『沁芳闸』。」贾政道：「胡说，偏不用『沁芳』二字。」',
         [{'type': 'show', 'actor': 'baoyu', 'at': 'baoyu_greet'}]),
    step('C17-042', 'c17-jubilant', 'dinner', '大观园 · 归途', 'wang_place',
         '或清堂茅舍，或堆石为垣，或编花为牖',
         'narrator', '园中诸景',
         '于是一路行来，或清堂茅舍，或堆石为垣，或编花为牖，或山下得幽尼佛寺，或林中藏女道丹房，或长廊曲洞，或方厦圆亭，贾政皆不及进去。',
         [{'type': 'show', 'actor': 'zheng', 'at': 'wang_place'}]),
    step('C17-043', 'c17-jubilant', 'dinner', '大观园 · 归途', 'feng_place',
         '一入门，两边都是游廊相接',
         'narrator', '蕉棠映粉墙',
         '说着一径引人绕著碧桃花，穿过一层竹篱花障编就的月洞门，俄见粉墙环护，绿柳周垂。贾政与众人进去，一入门，两边都是游廊相接。院中点衬几块山石，一边种著数本芭蕉，那一边乃是一棵西府海棠，其势若伞，丝垂翠缕，葩吐丹砂。',
         [{'type': 'show', 'actor': 'messenger', 'at': 'feng_place'}]),
    step('C17-044', 'c17-jubilant', 'dinner', '大观园 · 归途', 'baoyu_greet',
         '若只说蕉，则棠无著落，若只说棠，蕉亦无著落',
         'baoyu', '蕉棠两植',
         '宝玉道：「此处蕉棠两植，其意暗蓄『红』『绿』二字在内。若只说蕉，则棠无著落，若只说棠，蕉亦无著落。固有蕉无棠不可，有棠无蕉更不可。」贾政道：「依你如何？」宝玉道：「依我，题『红香绿玉』四字，方两全其妙。」贾政摇头道：「不好，不好！」',
         [{'type': 'show', 'actor': 'baoyu', 'at': 'baoyu_greet'}]),
    step('C17-045', 'c17-jubilant', 'dinner', '大观园 · 归途', 'wang_place',
         '老爷随我来。从这门出去，便是后院',
         'narrator', '穿堂而出',
         '众人都赞：「好精致想头！难为怎么想来。」原来贾政等走了进来，未进两层，便都迷了旧路，左瞧也有门可通，右瞧又有窗暂隔。贾珍笑道：「老爷随我来。从这门出去，便是后院，从后院出去，倒比先近了。」',
         [{'type': 'show', 'actor': 'zheng', 'at': 'wang_place'},
          {'type': 'hide', 'actor': 'messenger'}]),

    # 六、惜聚散 · 且听下回
    step('C17-050', 'c17-vision', 'dinner', '大观园 · 归途', 'baoyu_greet',
         '那宝玉一心只记挂著里边',
         'narrator', '宝玉一心只记挂',
         '大家出来，众人都道：「有趣，有趣，真搜神夺巧之至！」于是大家出来。那宝玉一心只记挂著里边，又不见贾政吩咐，少不得跟到书房。',
         [{'type': 'show', 'actor': 'baoyu', 'at': 'baoyu_greet'}]),
    step('C17-051', 'c17-vision', 'dinner', '大观园 · 书房', 'baoyu_greet',
         '贾政忽想起他来，方喝道：「你还不去',
         'zheng', '喝退宝玉',
         '贾政忽想起他来，方喝道：「你还不去？难道还逛不足！也不想逛了这半日，老太太必悬挂著。快进去，疼你也白疼了。」',
         [{'type': 'show', 'actor': 'zheng', 'at': 'wang_place'}]),
    step('C17-052', 'c17-vision', 'dinner', '大观园 · 书房', 'baoyu_greet',
         '宝玉听说，方退了出来',
         'narrator', '退了出来',
         '宝玉听说，方退了出来。少不得跟到书房，随众清客退出园门。',
         [{'type': 'hide', 'actor': 'zheng'}]),
    step('C17-053', 'c17-vision', 'dinner', '大观园 · 书房', 'baoyu_greet',
         '正在看下回分解',
         'narrator', '且听下回',
         '正是：园中佳景题不尽，万千心事付瑶琴。未知那宝玉明日如何应对这要紧一题，且听下回分解——林黛玉误剪香囊袋，贾元春归省庆元宵。',
         []),
    step('C17-056', 'c17-vision', 'dinner', '大观园 · 书房', 'baoyu_greet',
         '林黛玉误剪香囊袋，贾元春归省庆元宵',
         'narrator', '下回目录',
         '下回：林黛玉误剪香囊袋，贾元春归省庆元宵。',
         []),
]


def main() -> None:
    steps = json.loads(STORY.read_text())
    replacing = {n['id'] for n in NEW_NODES}
    replaced = [n['id'] for n in NEW_NODES if n['id'] in {s['id'] for s in steps}]
    kept = [s for s in steps if s['id'] not in replacing]
    merged = kept + NEW_NODES
    # The chapter is read in order, so the nodes keep the slot they already
    # held; a node that is new takes the slot of the one it replaces.
    slot = {s['id']: i for i, s in enumerate(steps)}
    for i, n in enumerate(NEW_NODES):
        slot.setdefault(n['id'], len(steps) + i)
    merged.sort(key=lambda s: slot.get(s['id'], len(steps)))
    STORY.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + '\n')

    sections = json.loads(SECTIONS.read_text())
    titles = {
        'c17-edict': ('正殿牌坊 · 限题一日', 'dinner', 'C17-030'),
        'c17-jubilant': ('沁芳闸 · 蕉棠两植', 'dinner', 'C17-040'),
        'c17-vision': ('归途 · 且听下回', 'dinner', 'C17-050'),
    }
    for s in sections:
        if s['id'] in titles:
            title, scene, start = titles[s['id']]
            s['title'] = title
            s['scene'] = scene
            s['start'] = start
    SECTIONS.write_text(json.dumps(sections, ensure_ascii=False, indent=2) + '\n')

    print(f'chapter 17: replaced {len(replaced)} nodes with {len(NEW_NODES)} '
          f'({len(merged)} total); sections retitled')


if __name__ == '__main__':
    main()
