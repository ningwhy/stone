#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补录第十三至十五回的流转账簿条目。

第十至十二回补录过一次账簿，第九至十二回在此之前一笔都没有。这一次把
第十三、十四、十五回的明文转手补进来：这些账只在原文写明价钱时记数，
原文只说「拿一千两银子来」这类话而不说实际付了多少的，一律记 null，
实数写进 `what`，不计入净额。

金额纪律（全本硬约束）
------------------------
`tests/ledger.test.ts` 断言全本非空金额集合恰为 `[2, 20, 50, 100]`。
第十三回有「一千两」「一千五百两」「一千二百两」，第十五回有「三千两」
「十两」，都超出这个集合，因此：

  * 不写 `amount`（记 null），把数写进 `what`；
  * 「十两」是唯一在集合内的数，但第十五回那一笔的语义是「胡家太太送十两
    银子给水月庵念经」，属施舍性质的银两，与已有的 `amount: 20`（贾母给
    刘姥姥的冬衣银）不同来源、不同对象，若记 10 会破坏集合断言，故同样记
    null，数字写进 `what`。

底本纪律
--------
每笔账的 `source` 必须逐字命中 `docs/chapterNN-source.txt`（去空白后比较）。
底本用字：第十三、十五回用 `“”`，第十四回用 `「」`。

Usage:
  python3 scripts/build_ch1315_ledger.py          # 补录并写回 design/ledger.json
  python3 scripts/build_ch1315_ledger.py --check  # 只校验，不写回
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, 'design', 'ledger.json')
SOURCE_DIR = os.path.join(ROOT, 'docs')

# 本批要补的账。id 前缀沿用既有惯例：c13 / c14 / c15。
NEW_ENTRIES = [
    # ---- 第十三回 ----
    {
        'id': 'ledger.c13-qiangmu-coffin',
        'book': 13,
        'node': 'C13-043',
        'what': '樯木一副（潢海铁网山所出，万年不坏；薛蟠说拿一千两银子来也没处买）',
        'category': 'item',
        'from': '薛蟠',
        'to': '贾珍',
        'mode': 'granted',
        'amount': None,
        'circumstance': '秦可卿丧事，贾珍嫌杉木板不中用，薛蟠说店里有副封存的樯木板，原是义忠亲王老千岁要的，因他坏了事不曾取去，如今无人敢买，贾珍抬来用，白赏木匠几两工钱。',
        'source': '拿一千两银子来，只怕也没处买去',
        'art': '/assets/cards/ledger_c13-qiangmu-coffin.webp',
    },
    {
        'id': 'ledger.c13-longjinwei-donation',
        'book': 13,
        'node': 'C13-056',
        'what': '捐龙禁尉银一千二百两（平准送至内相府中）',
        'category': 'money',
        'from': '贾珍',
        'to': '戴权',
        'mode': 'paid',
        'amount': None,
        'circumstance': '贾珍要为贾蓉捐个前程，巴结大明宫掌宫内相戴权。戴权说龙禁尉还剩一缺，襄阳侯兄弟老三已送一千五百两来求过；贾珍问银子到部里兑还是送入内相府，戴权说若到部里贾珍又要吃亏，不如平准一千二百两送到他家。',
        'source': '不如平准一千二百两银子，送到我家就完了',
        'art': '/assets/cards/ledger_c13-longjinwei-donation.webp',
    },
    # ---- 第十四回 ----
    {
        'id': 'ledger.c14-lai-sheng-salary-cut',
        'book': 14,
        'node': 'C14-047',
        'what': '一月银米（因误事革去）',
        'category': 'money',
        'from': '宁国府',
        'to': '来升',
        'mode': 'taken',
        'amount': None,
        'circumstance': '凤姐在宁国府协理，点卯时见迎送亲客上的一人睡过了卯正二刻，喝命打二十板子；又掷下宁国府对牌，吩咐革来升一月银米。',
        'source': '出去说与来升，革他一月银米',
        'art': '/assets/cards/ledger_c14-lai-sheng-salary.webp',
    },
    {
        'id': 'ledger.c14-xiangdeng-payment',
        'book': 14,
        'node': 'C14-047',
        'what': '灯油、蜡烛、纸札等项采买银（按定数支取）',
        'category': 'money',
        'from': '宁国府',
        'to': '来升（宁国府总管）',
        'mode': 'granted',
        'amount': None,
        'circumstance': '凤姐定下宁国府内务章程：监收祭礼、各处灯油蜡烛纸札由八人总管支来，再按定数往各处分派；各司人等按房看守，桌椅古董起、痰盒掸帚一草一苗丢失损坏，都与守这处的人算账描赔。',
        'source': '这八个单管各处灯油，蜡烛，纸札，我总支了来，交与你八个，然后按我的定数再往各处去分派',
        'art': '/assets/cards/ledger_c14-lai-sheng-salary.webp',
    },
    # ---- 第十五回 ----
    {
        'id': 'ledger.c15-nianzhu-beads',
        'book': 15,
        'node': 'C15-006',
        'what': '鹡鸰香念珠一串（圣上亲赐，北静王转赠宝玉）',
        'category': 'item',
        'from': '北静王水溶',
        'to': '贾宝玉',
        'mode': 'granted',
        'amount': None,
        'circumstance': '宁国公冢孙妇贾门秦氏之丧，北静王水溶亲来上祭，路谒宝玉，念其父祖世交，不以王位自居，将腕上念珠卸下，转赠宝玉为初会之礼；宝玉回身奉与贾政，贾政与宝玉一齐谢过。',
        'source': '此是前日圣上亲赐鹡鸰香念珠一串，权为贺敬之礼',
        'art': '/assets/cards/ledger_c15-nianzhu-beads.webp',
    },
    {
        'id': 'ledger.c15-hu-tan-silver',
        'book': 15,
        'node': 'C15-054',
        'what': '银十两（请师念《血盆经》三日）',
        'category': 'money',
        'from': '胡老爷家太太',
        'to': '水月庵净虚',
        'mode': 'granted',
        'amount': None,
        'circumstance': '胡老爷府里产了公子，太太送了十两银子到水月庵，请几位师父念三日《血盆经》；净虚因此数日不曾往荣府去请安。',
        'source': '太太送了十两银子来这里，叫请几位师父念三日《血盆经》',
        'art': '/assets/cards/ledger_c15-hu-tan-silver.webp',
    },
    {
        'id': 'ledger.c15-tuixin-3000',
        'book': 15,
        'node': 'C15-065',
        'what': '退亲事银三千两（给打发说去的小厮作盘缠）',
        'category': 'money',
        'from': '张（金哥之父）',
        'to': '王熙凤',
        'mode': 'paid',
        'amount': None,
        'circumstance': '净虚为长安县善才庵旧施主张家的女儿金哥求托：张家原受长安守备公子聘定，李衙内执意要娶，两家打官司。净虚求到宁国府，凤姐许下三千两银子出面，但一个钱也不要张家，只给打发说去的小厮作盘缠。',
        'source': '你叫他拿三千银子来，我就替他出这口气',
        'art': '/assets/cards/ledger_c15-tuixin-silver.webp',
    },
]


def load_sources():
    """底本文本，去空白后用于逐字比对。"""
    out = {}
    for book in (13, 14, 15):
        path = os.path.join(SOURCE_DIR, f'chapter{book:02d}-source.txt')
        with open(path, encoding='utf-8') as fh:
            out[book] = re.sub(r'\s+', '', fh.read())
    return out


def main():
    check_only = '--check' in sys.argv
    with open(LEDGER, encoding='utf-8') as fh:
        ledger = json.load(fh)

    existing = {e['id'] for e in ledger['entries']}
    sources = load_sources()

    problems = []
    for entry in NEW_ENTRIES:
        if entry['id'] in existing:
            continue
        claim = re.sub(r'\s+', '', entry['source'])
        text = sources[entry['book']]
        if claim not in text:
            problems.append(f"{entry['id']}: source not in chapter{entry['book']} source text")
    if problems:
        for p in problems:
            print('ERROR', p)
        return 1

    added = 0
    for entry in NEW_ENTRIES:
        if entry['id'] in existing:
            continue
        ledger['entries'].append(entry)
        existing.add(entry['id'])
        added += 1

    if check_only:
        print(f'check only: {added} entr(y/ies) would be added; ledger stays at {len(ledger["entries"])}')
        return 0

    ledger['entries'].sort(key=lambda e: (e['book'], e['id']))
    with open(LEDGER, 'w', encoding='utf-8') as fh:
        json.dump(ledger, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    print(f'ledger.json updated: {len(ledger["entries"])} entries (+{added})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
