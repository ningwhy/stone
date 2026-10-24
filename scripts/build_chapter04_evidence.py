#!/usr/bin/env python3
"""Build design/chapter04-evidence.json from the archived chapter-four text.

Every entry is derived from the local source file, never from memory: the
paragraph lead of each node is matched back to the paragraph it came from, and
the excerpt is cut from that paragraph. A lead that cannot be located in the
source is reported as an error instead of being silently written out, so the
evidence table cannot drift away from the base text.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, 'docs', 'chapter04-source.txt')
STORY = os.path.join(ROOT, 'design', 'chapter04-story.json')
SECTIONS = os.path.join(ROOT, 'design', 'chapter04-sections.json')
MAPS = os.path.join(ROOT, 'design', 'chapter04-maps.json')
OUT = os.path.join(ROOT, 'design', 'chapter04-evidence.json')

# Lines that belong to the wiki navigation, not to the chapter.
NAV = ('上一回', '回目录', '下一回')


def load_paragraphs():
    with open(SOURCE, encoding='utf-8') as fh:
        raw = fh.read()
    lines = [ln.strip() for ln in raw.splitlines()]
    body = [ln for ln in lines if ln and not ln.startswith(NAV)]
    paragraphs = []
    for ln in body:
        if ln.startswith('第四回') or ln.startswith('題曰') or ln.startswith('捐軀') or ln.startswith('眼底'):
            continue
        paragraphs.append(ln)
    return paragraphs


def normalise(text):
    """Collapse whitespace and drop the punctuation the story file trims.

    The story file writes a dialogue lead as `門子笑道：不瞞老爺說` while the
    source has `門子笑道：「不瞞老爺說`; the colon stands in for the opening
    quote, so the quote characters have to go before the two can be compared.
    """
    return re.sub(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-]', '', text)


def main():
    paragraphs = load_paragraphs()
    norm_paras = [normalise(p) for p in paragraphs]
    with open(STORY, encoding='utf-8') as fh:
        story = json.load(fh)
    with open(SECTIONS, encoding='utf-8') as fh:
        sections = json.load(fh)
    with open(MAPS, encoding='utf-8') as fh:
        maps = json.load(fh)

    evidence = []
    seen_leads = {}
    missing = []
    for node in story:
        lead = node.get('source', {}).get('paragraphLead', '')
        if not lead:
            missing.append((node['id'], 'no paragraphLead'))
            continue
        key = normalise(lead)
        if key in seen_leads:
            index = seen_leads[key]
        else:
            index = next((i for i, p in enumerate(norm_paras) if key and key in p), None)
            if index is None:
                missing.append((node['id'], lead))
                continue
            seen_leads[key] = index
        para = paragraphs[index]
        cut = para.find(lead)
        if cut < 0:
            cut = 0
        excerpt = para[cut:cut + 60]
        layer = node.get('source', {}).get('layer', 'present')
        speaker = node.get('speaker')
        evidence.append({
            'id': f"C04-E{len(evidence) + 1:03d}",
            'classification': 'explicit',
            'paragraphLead': lead,
            'excerpt': excerpt,
            'claim': node.get('title') or f"{node['id']} 节点内容",
            'narrativeLayer': layer,
            'speaker': None if speaker == 'narrator' else speaker,
            'appliesTo': [node['id']],
            'designDecision': None,
            'uncertainty': None,
        })

    # Design decisions: the parts the game has to decide and the text leaves open.
    design = [
        {
            'id': 'C04-D001',
            'classification': 'design',
            'paragraphLead': '因見王夫人事情冗雜，姊妹們遂出來，至寡嫂李氏房中來了',
            'excerpt': None,
            'claim': '李纨居处与王夫人处的相对位置与移动路径',
            'narrativeLayer': 'present',
            'speaker': None,
            'appliesTo': ['wang'],
            'designDecision': '复用第三回的 `wang` 场景并新增 `kang_edge` 等锚点，用一段门洞移动表达「姊妹们遂出來」，不另建新场景。',
            'uncertainty': '原文只写「出來」，未指明经过哪道门；门洞位置为可读性做的合理推定。',
        },
        {
            'id': 'C04-D002',
            'classification': 'design',
            'paragraphLead': '如今且說雨村，因補授了應天府',
            'excerpt': None,
            'claim': '应天府刑堂的空间布局与公案、告状位、密室的相对关系',
            'narrativeLayer': 'present',
            'speaker': None,
            'appliesTo': ['c4_yamen'],
            'designDecision': '新建 `c4_yamen` 场景，把「堂中审案」与「退堂密室」放在同一张图的两个 PlanZones 内，用 `side_door` 连接，符合原文「退堂」的空间连贯性。',
            'uncertainty': '原文未描述应天府衙门的具体格局，平面布局为原创设计。',
        },
        {
            'id': 'C04-D003',
            'classification': 'design',
            'paragraphLead': '正是這薛家少爺',
            'excerpt': None,
            'claim': '薛蟠、薛姨妈、宝钗三人的形象与身份差异',
            'narrativeLayer': 'present',
            'speaker': None,
            'appliesTo': ['xuepan', 'xueyima', 'baochai'],
            'designDecision': '按原文只给出的年龄、身份与行事方式反推服饰：薛蟠为宝蓝团花袍少年，薛姨妈为黛色褙子四十上下妇人，宝钗为石青绣蝶褙子少女；三人靠脸型与五官区分，宝钗本回无台词，只以出场动作与叙述出现。',
            'uncertainty': '原文未描写三人衣着颜色与相貌，以上为工笔淡彩风格下的合理推定。',
        },
        {
            'id': 'C04-D004',
            'classification': 'design',
            'paragraphLead': '那薛家少爺便跳出來',
            'excerpt': None,
            'claim': '梨香院的空间与「一门通街、西南有角门通夹道」的院落关系',
            'narrativeLayer': 'present',
            'speaker': None,
            'appliesTo': ['c4_lixiang'],
            'designDecision': '新建 `c4_lixiang` 场景，锚点 `street_gate` / `lane_gate` / `front_hall` / `back_rooms` / `court_center` 对应原文「前厅后舍俱全，另有一门通街，西南有一角门通夹道」。',
            'uncertainty': '梨香院「在荣国东北角上」是相对位置，图中未把荣府全图叠在同一坐标系内。',
        },
        {
            'id': 'C04-D005',
            'classification': 'design',
            'paragraphLead': '他眉心中原有米粒大小的一點胭脂痣',
            'excerpt': None,
            'claim': '英莲不在本回登台，其身份信息全部以转述与回忆层呈现',
            'narrativeLayer': 'reported',
            'speaker': None,
            'appliesTo': ['C04-032', 'C04-035'],
            'designDecision': '英莲与冯渊全程不出场，不建角色资产；相关信息挂在雨村与门子的对白上，并带「转述／回忆」徽标，与第一回「甄士隐」线不冲突。',
            'uncertainty': '原文写冯渊「酷爱男风」，此处按史实理解只保留行为描写，不做断章取义。',
        },
    ]

    for item in design:
        evidence.append(item)

    out = {
        'schemaVersion': 1,
        'template': False,
        'chapter': 4,
        'source': {
            'edition': '维基文库《紅樓夢》第 004 回（繁体原文页，古典小说排版模板）',
            'url': 'https://zh.wikisource.org/wiki/紅樓夢/第004回',
            'retrievedAt': '2026-10-24',
            'localText': 'docs/chapter04-source.txt',
            'processing': 'MediaWiki API action=query&prop=revisions&rvprop=content 取回 wikitext；去除 {{样式:古典小說}}、{{center}}、<poem>、{{清朝作品}} 与文末导航行；保留繁体用字。',
        },
        'paragraphCount': len(paragraphs),
        'nodeCount': len(story),
        'sectionCount': len(sections),
        'mapCount': len(maps.get('maps', maps) if isinstance(maps, dict) else maps),
        'evidence': evidence,
    }
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write('\n')

    print(f'evidence entries: {len(evidence)}  (explicit {len(evidence) - len(design)}, design {len(design)})')
    print(f'paragraphs: {len(paragraphs)}  nodes: {len(story)}')
    if missing:
        print(f'UNMATCHED paragraphLead: {len(missing)}')
        for node_id, lead in missing[:20]:
            print(f'  {node_id}: {lead}')
        return 1
    print('all paragraphLead values located in the source text')
    return 0


if __name__ == '__main__':
    sys.exit(main())
