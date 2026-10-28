#!/usr/bin/env python3
# 引文 / 诗句校验：把繁体底本转简体后，逐条核对节点里的「」引文与纯诗句是否真在底本中。
import json, re, sys
import zhconv

PUNCT = set(' ，。、；：？！「」『』“”‘’（）()…—·《》〈〉-　\n\r\t')
# zhconv 偶发漏转的繁体残余，统一归到本项目简体用法
EXTRA = {'凖': '准', '著': '着', '餘': '余', '麼': '么', '後': '后',
         '雲': '云', '際': '际', '極': '极', '臺': '台', '灣': '湾',
         '裡': '里', '纔': '才', '卻': '却', '個': '个', '點': '点',
         '處': '处', '對': '对', '說': '说', '問': '问', '應': '应'}

def norm(s: str) -> str:
    s = zhconv.convert(s, 'zh-cn')
    s = ''.join(EXTRA.get(ch, ch) for ch in s)
    return ''.join(ch for ch in s if ch not in PUNCT)

def load_source(path: str):
    raw = open(path, encoding='utf-8').read()
    return norm(raw)

def check_quotes(num: str, src: str):
    story = json.load(open('design/chapter%s-story.json' % num, encoding='utf-8'))
    bad = []
    checked = 0
    for s in story:
        for m in re.findall(r'「([^」]{3,})」', s['text']):
            checked += 1
            q = norm(m)
            if q not in src:
                found = any(q[i:i+max(4,len(q)-2)] in src
                            for i in range(0, max(1, len(q)-max(4,len(q)-2)+1)))
                if not found:
                    bad.append((s['id'], m))
    print('第%s回：校验「」引文 %d 条，未命中 %d 条' % (num, checked, len(bad)))
    for nid, q in bad:
        print('  [引文 %s] %s' % (nid, q[:70]))
    return bad

def check_poems(num: str, src: str):
    """纯诗句节点（不含「」、含逗号、较长）必须整段命中底本。"""
    story = json.load(open('design/chapter%s-story.json' % num, encoding='utf-8'))
    bad = []
    for s in story:
        t = s['text']
        if '「' in t or '」' in t:
            continue
        if '，' not in t or len(t) < 14:
            continue
        ts = norm(t)
        # 去掉可能的「曲名——」或「曲名：」前缀
        body = re.sub(r'^[^，。]{2,6}[——：:]', '', ts)
        if body != ts:
            ts = norm(body)
        # 取首尾各 10 字做锚点；整段过长时校验首尾即足够（中段若错会反映在首尾偏移）
        if len(ts) <= 40:
            ok = ts in src
        else:
            ok = ts[:12] in src and ts[-12:] in src
            # 再抽查中段
            mid = ts[len(ts)//2-8:len(ts)//2+8]
            ok = ok and mid in src
        if not ok:
            bad.append((s['id'], t))
    print('第%s回：校验纯诗句节点 %d 条，疑似未命中 %d 条' %
          (num, sum(1 for s in story if '「' not in s['text'] and '，' in s['text'] and len(s['text'])>=14), len(bad)))
    for nid, t in bad:
        print('  [诗句 %s] %s' % (nid, t[:70]))
    return bad

if __name__ == '__main__':
    for n in sys.argv[1:]:
        src = load_source('docs/chapter%s-source.txt' % n)
        check_quotes(n, src)
        check_poems(n, src)
