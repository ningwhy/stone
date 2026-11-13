"""Point chapter 17's story nodes at the original paragraphs they adapt.

The chapter was drafted with a paraphrase in `source.paragraphLead`, while the
rest of the book records the opening words of the paragraph each node comes
from. This rewrites the remaining paraphrases into real leads, taken from the
base text in `docs/chapter17-source.txt`.

Every lead is checked against the base text before anything is written, and the
mapping is written out node by node: a guessed citation is worse than no
citation at all.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
STRIP = re.compile(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-]')


def key(text: str) -> str:
    return STRIP.sub('', text)


LEADS = {
    # 一、入园
    'C17-001': '话说秦钟既死，宝玉痛哭不已',
    'C17-002': '贾珍先去园中知会众人',
    'C17-003': '可巧近日宝玉因思念秦钟',
    'C17-004': '贾政近因闻得塾掌称赞宝玉专能对对联',
    'C17-005': '贾政听了，沉思一回',
    'C17-006': '贾政刚至园门前',
    # 二、题咏对额
    'C17-010': '说著，进入石洞来',
    'C17-011': '贾政与诸人上了亭子',
    'C17-012': '有一客道：“是极，是极。竟是‘泻玉’二字妙。”',
    'C17-013': '说著，进入石洞来',
    'C17-014': '有一客道：“是极，是极。竟是‘泻玉’二字妙。”',
    'C17-015': '有一客道：“是极，是极。竟是‘泻玉’二字妙。”',
    # 三、书匾拟联
    'C17-020': '贾政笑道：“不可谬奖',
    'C17-021': '众人听了，都赞道',
    'C17-022': '贾政听了，便回头命宝玉拟来',
    'C17-023': '贾政道：“匾上二字容易。再作一副七言对联来。”',
    'C17-024': '宝玉听说，立于亭上，四顾一望',
    'C17-025': '贾政听了，点头微笑',
    # 六、收尾
    'C17-053': '那宝玉一心只记挂著里边',
    'C17-056': '宝玉听说，方退了出来',
}


def main() -> None:
    base = (ROOT / 'docs/chapter17-source.txt').read_text()
    stripped = key(base)
    path = ROOT / 'design/chapter17-story.json'
    steps = json.loads(path.read_text())
    index = {s['id']: s for s in steps}
    missing = [(n, l) for n, l in LEADS.items() if key(l) not in stripped]
    unknown = [n for n in LEADS if n not in index]
    if missing:
        print('leads not found in the base text:')
        for n, l in missing:
            print(f'   {n}: {l}')
    if unknown:
        print(f'unknown node ids: {unknown}')
    if missing or unknown:
        sys.exit(1)
    for node_id, lead in LEADS.items():
        index[node_id]['source']['paragraphLead'] = lead
    path.write_text(json.dumps(steps, ensure_ascii=False, indent=2) + '\n')
    print(f'chapter 17: rewrote {len(LEADS)} leads, all verified in the base text')


if __name__ == '__main__':
    main()
