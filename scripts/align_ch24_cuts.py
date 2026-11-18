#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 build_chapter24.py 的 CUTS 区间**按底本重算**。

为什么需要这个脚本
------------------
第 24 回初版把「底本段号 + 起止子句号」全部手写进 CUTS，结果是：
  · 9 处区间互相重叠（下一节点被上一节点吞掉一截）
  · 4 处跳段子句（底本有字但没进任何节点）
  · 15 处标题与切出来的正文对不上（标题和正文说的不是一回事）

根因是手写索引必然会和底本漂移。这个脚本改成**只保留起点**：
每个节点只声明它在底本第几段、从第几个子句开始；**终点由下一个
节点的起点决定**，于是整段底本被首尾相接地、不重不漏地切开。

匹配方式
--------
每个节点的标题基本是底本原文的片段。脚本在底本子句里找标题的最佳
落点（归一化后用 difflib 比对），并强制起点严格递增：
  · 起点沿用原值 → 标题匹配分最高但会破坏单调性时，退回原值
  · 标题匹配不到 → 保留原起点（标题是压缩摘要，不是原文片段）

用法
----
    python3 scripts/align_ch24_cuts.py           # 只报告，不改文件
    python3 scripts/align_ch24_cuts.py --write   # 把重算结果写回 build_chapter24.py
"""
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'scripts' / 'build_chapter24.py'

PUNCT = re.compile(r'[\s，。、；：？！」』“”‘’「」『』（）()…—·《》〈〉\-`\'"]')


def strip(t: str) -> str:
    return PUNCT.sub('', t)


def load_module():
    """把 build_chapter24.py 跑到 CUTS 定义完但不执行 main 的位置。"""
    src = GEN.read_text(encoding='utf-8')
    head = src.split('def build(')[0]
    ns = {'__file__': str(GEN)}
    exec(compile(head, str(GEN), 'exec'), ns)
    return ns


def score_window(sents, j, title_norm):
    """标题与从 j 起最长 8 个子句的拼接有多像。"""
    acc = ''
    for k in range(j, min(j + 8, len(sents))):
        acc += strip(sents[k])
        if len(acc) >= len(title_norm):
            break
    if not acc or not title_norm:
        return 0.0
    return difflib.SequenceMatcher(None, title_norm, acc).ratio()


def align(ns):
    sents = ns['SENTENCES']
    cuts = [list(c) for c in ns['CUTS']]
    report = []
    prev_pos = (-1, -1)
    prev_para = None
    for c in cuts:
        chap, nid, spk, title, place, para, a, b, acts = c
        title_norm = strip(title)
        best = None
        if title_norm:
            cands = []
            for j in range(len(sents[para])):
                if (para, j) <= prev_pos:
                    continue
                sc = score_window(sents[para], j, title_norm)
                cands.append((sc, j))
            if cands:
                sc, j = max(cands)
                # 匹配分不够高就别乱动（标题是压缩摘要时保持原起点）
                if sc >= 0.72:
                    best = j
        if best is None:
            best = a
            if (para, best) <= prev_pos:
                best = prev_pos[1] + 1
        if best != a:
            report.append((nid, para, a, best, title[:30]))
        c[6] = best
        prev_pos = (para, best)
        prev_para = para
    # 终点由下一个节点的起点决定；段末节点吃到本段末尾
    for i in range(len(cuts) - 1):
        if cuts[i][5] == cuts[i + 1][5]:
            cuts[i][7] = cuts[i + 1][6]
        else:
            cuts[i][7] = len(sents[cuts[i][5]])
    cuts[-1][7] = len(sents[cuts[-1][5]])
    return cuts, report


def rewrite(cuts):
    """把重算后的 CUTS 写回生成器（保持原有的排版风格）。"""
    src = GEN.read_text(encoding='utf-8')
    head, rest = src.split('CUTS = [', 1)
    _, tail = rest.split('\n]\n', 1)
    lines = ['CUTS = [']
    for c in cuts:
        chap, nid, spk, title, place, para, a, b, acts = c
        lines.append(
            f"    ('{chap}', '{nid}', '{spk}', {title!r}, {place!r}, {para}, {a}, {b},")
        lines.append(f'     {acts!r}),')
    lines.append(']')
    GEN.write_text(head + '\n'.join(lines) + '\n' + tail, encoding='utf-8')


def main():
    ns = load_module()
    cuts, report = align(ns)
    print(f'共 {len(cuts)} 个节点；起点被重算的有 {len(report)} 个')
    for r in report[:80]:
        print(f'  {r[0]} p{r[1]}: {r[2]} -> {r[3]}  {r[4]}')
    if '--write' in sys.argv:
        rewrite(cuts)
        print('已写回 build_chapter24.py')


if __name__ == '__main__':
    main()
