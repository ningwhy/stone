"""Point every story node's `source.paragraphLead` at the original paragraph.

Chapters 1-15 record the opening words of the original paragraph each node
adapts, so the lead can be found in the base text and a reader can trace the
adaptation back to the book. Chapters 16 and 17 were written with a short
paraphrase in that field instead, which cannot be located in the base text.

This script rewrites those leads to the real opening words. The mapping is
made explicit per node, because a guess would put a wrong citation on the
record. Each lead is then verified to occur in the base text before anything
is written, so a stale mapping fails loudly instead of silently mis-citing.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
STRIP = re.compile(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-]')


def key(text: str) -> str:
    return STRIP.sub('', text)


# The original paragraph each node of chapter 16 and 17 adapts, given by the
# opening words of that paragraph in the base text.
LEADS: dict[str, dict[str, str]] = {
    '16': {
        # 一、庆贺贾政生辰
        'C16-001': '一日正是贾政的生辰，宁荣二处人丁都齐集庆贺',
        'C16-002': '一日正是贾政的生辰，宁荣二处人丁都齐集庆贺',
        'C16-003': '一日正是贾政的生辰，宁荣二处人丁都齐集庆贺',
        'C16-004': '一日正是贾政的生辰，宁荣二处人丁都齐集庆贺',
        # 二、六宫都太监降旨
        'C16-010': '一日正是贾政的生辰，宁荣二处人丁都齐集庆贺',
        'C16-011': '早见六宫都太监夏守忠乘马而至',
        'C16-012': '贾母等合家人等心中皆惶惶不定',
        'C16-013': '贾母等合家人等心中皆惶惶不定',
        # 三、元春晋封贤德妃
        'C16-020': '忽见赖大等三四个管家喘吁吁跑进仪门报喜',
        'C16-021': '忽见赖大等三四个管家喘吁吁跑进仪门报喜',
        'C16-022': '那时贾母正心神不定，在大堂廊下伫立',
        'C16-023': '贾琏笑道：“虽不十分准，也有八分准了。”',
        'C16-024': '贾政不惯于俗务，只凭贾赦，贾珍，贾琏，赖大',
        # 四、秦业气死
        'C16-030': '谁知近日水月庵的智能私逃进城',
        'C16-031': '谁知近日水月庵的智能私逃进城',
        'C16-032': '谁知近日水月庵的智能私逃进城',
        # 五、秦钟夭逝
        'C16-040': '且说宝玉近因家中有这等大事',
        'C16-041': '此时秦钟已发过两三次昏了',
        'C16-042': '此时秦钟已发过两三次昏了',
        'C16-043': '此时秦钟已发过两三次昏了',
        'C16-044': '此时秦钟已发过两三次昏了',
        # 六、黛玉回府
        'C16-050': '好容易盼至明日午错',
        'C16-051': '好容易盼至明日午错',
        'C16-052': '且说贾琏自回家参见过众人',
        'C16-053': '且说贾琏自回家参见过众人',
        'C16-054': '且说贾琏自回家参见过众人',
        'C16-055': '好容易盼至明日午错',
        'C16-056': '贾政不惯于俗务，只凭贾赦，贾珍，贾琏，赖大',
    },
    '17': {
        # 一、贾政入园
        'C17-001': '这日贾珍等来回贾政',
        'C17-002': '贾政听了，沉思一回',
        'C17-003': '可巧近日宝玉因思念秦钟',
        'C17-004': '贾政近因闻得塾掌称赞宝玉专能对对联',
        'C17-005': '众人笑道：“老爷今日一拟定佳',
        'C17-006': '贾政刚至园门前',
        # 二、题咏对额
        'C17-010': '说著，进入石洞来',
        'C17-011': '贾政与诸人上了亭子',
        'C17-012': '贾政听了，便回头命宝玉拟来',
        'C17-013': '说著，进入石洞来',
        'C17-014': '有一客道：“是极，是极。竟是‘泻玉’二字妙。”',
        'C17-015': '有一客道：“是极，是极。竟是‘泻玉’二字妙。”',
        # 三、宝玉题匾对联
        'C17-020': '贾政笑道：“不可谬奖',
        'C17-021': '众人听了，都赞道',
        'C17-022': '贾政听了，便回头命宝玉拟来',
        'C17-023': '贾政道：“匾上二字容易。再作一副七言对联来。”',
        'C17-024': '宝玉听说，立于亭上，四顾一望',
        'C17-025': '贾政拈髯点头不语',
        # 四、宣旨省亲
        'C17-030': '这里贾珍等来回贾政',
        'C17-031': '这里贾珍等来回贾政',
        'C17-032': '这里贾珍等来回贾政',
        'C17-033': '这里贾珍等来回贾政',
        'C17-034': '这里贾珍等来回贾政',
        'C17-035': '这里贾珍等来回贾政',
        # 五、采办与添景
        'C17-040': '次早贾琏起来，见过贾赦贾政',
        'C17-041': '次早贾琏起来，见过贾赦贾政',
        'C17-042': '次早贾琏起来，见过贾赦贾政',
        'C17-043': '贾政不惯于俗务，只凭贾赦',
        'C17-044': '贾政不惯于俗务，只凭贾赦',
        'C17-045': '贾政不惯于俗务，只凭贾赦',
        # 六、宝玉伤聚散
        'C17-050': '贾政不惯于俗务，只凭贾赦',
        'C17-051': '贾政不惯于俗务，只凭贾赦',
        'C17-052': '贾政不惯于俗务，只凭贾赦',
        'C17-053': '贾政不惯于俗务，只凭贾赦',
        'C17-056': '贾政不惯于俗务，只凭贾赦',
    },
}


def main() -> None:
    ok = True
    for book, mapping in LEADS.items():
        book_no = int(book)
        path = ROOT / f'design/chapter{book}-story.json'
        base = (ROOT / f'docs/chapter{book_no:02d}-source.txt').read_text()
        stripped = key(base)
        steps = json.loads(path.read_text())
        index = {s['id']: s for s in steps}
        unknown = [k for k in mapping if k not in index]
        uncovered = [s['id'] for s in steps if s['id'] not in mapping]
        if unknown:
            print(f'chapter {book}: unknown node ids {unknown}')
            ok = False
        if uncovered:
            print(f'chapter {book}: nodes without a lead mapping {uncovered}')
            ok = False
        missing = [(n, lead) for n, lead in mapping.items() if key(lead) not in stripped]
        if missing:
            print(f'chapter {book}: leads not found in the base text:')
            for node_id, lead in missing:
                print(f'   {node_id}: {lead}')
            ok = False
        if not ok:
            continue
        for node_id, lead in mapping.items():
            index[node_id]['source']['paragraphLead'] = lead
        path.write_text(json.dumps(steps, ensure_ascii=False, indent=2) + '\n')
        print(f'chapter {book}: rewrote {len(mapping)} leads, all verified in the base text')
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
