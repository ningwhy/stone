#!/usr/bin/env python3
"""生成逐张位图的朝向清单文档。

朝向左面是读出来的，不是写死的：design/character-facing.json 由
scripts/facing_assets.py 实测、scripts/build_facing.py 汇总而来。本脚本
只做一件事——把那张表展开成一张人能逐行核对的清单，避免文档里的方向
与实际用的表出现漂移。

用法：
    python3 scripts/build_facing_doc.py            # 写入 docs/production/facing-list.md
    python3 scripts/build_facing_doc.py --check    # 只校验是否最新，不写文件
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TABLE = ROOT / 'design' / 'character-facing.json'
OUT = ROOT / 'docs' / 'production' / 'facing-list.md'

# 中文角色名，只为让清单读起来有人名；取自 src/story.ts 的 cast 表
NAMES: dict[str, str] = {
    'baochai': '薛宝钗', 'baoyu': '贾宝玉', 'daiyu': '林黛玉', 'feng': '王熙凤',
    'fengshi': '王夫人', 'fengsu': '秦可卿', 'grandmother': '贾母', 'guide': '引路人',
    'huoqi': '霍起', 'jiaoxing': '焦大', 'kongkong': '空空道人', 'leng': '冷子兴',
    'liwan': '薛姨妈', 'maid': '丫鬟', 'menzi': '门子', 'messenger': '传话人',
    'monk': '癞头和尚', 'nurse_li': '李嬷嬷', 'nurse_wang': '王嬷嬷', 'oldmonk': '老僧',
    'plaintiff': '原告', 'ruhai': '如来', 'sedan': '小轿', 'shiyin': '侍饮',
    'tanchun': '探春', 'taoist': '道人', 'wang': '王夫人', 'xichun': '惜春',
    'xing': '袭人', 'xiren': '袭人', 'xuepan': '薛蟠', 'xueyan': '薛姨妈',
    'xueyima': '薛姨妈', 'yingchun': '迎春', 'yingge': '莺儿', 'yinglian': '英莲',
    'yucun': '雨村', 'zhang': '张道士', 'zheng': '贾政',
}

METHOD_ZH = {
    'vision-landmark-geometry': '实测',
    'vision-landmark-geometry-on-source-bitmap': '实测(源图)',
    'visual-review': '目视',
    'default-no-painted-head': '默认',
}


def side_cn(side: str) -> str:
    return '朝左' if side == 'left' else '朝右'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    table = json.loads(TABLE.read_text())
    actors: dict = table['actors']
    variants: dict = table.get('variants', {})

    rows: list[tuple[str, str, str, str, str]] = []  # 资产键, 角色, 类别, 朝向, 依据
    props: list[tuple[str, str, str, str, str]] = []
    for actor, rec in actors.items():
        ev = rec.get('evidence', {})
        for kind, kind_cn in (('portrait', '立绘'), ('chibi', 'Q版')):
            side = rec.get(kind)
            if not side:
                continue
            # 证据可能按 kind 分层，也可能整条角色共用一份（无人物头的道具）
            e = ev.get(kind) if isinstance(ev.get(kind), dict) else {}
            method = e.get('method') or ev.get('method', '')
            votes = e.get('votes')
            basis = METHOD_ZH.get(method, method or '-') + (f'·{votes}票' if votes else '')
            # 无人物头的道具（轿子）不参与朝向判定，也不计入人物位图统计
            if method == 'default-no-painted-head':
                props.append((f'{actor}-{kind}', NAMES.get(actor, actor), kind_cn, side_cn(side), basis))
                continue
            rows.append((f'{actor}-{kind}', NAMES.get(actor, actor), kind_cn, side_cn(side), basis))

    for key, rec in variants.items():
        e = rec.get('evidence', {})
        method = METHOD_ZH.get(e.get('method', ''), e.get('method', '-'))
        votes = e.get('votes')
        basis = f'{method}' + (f'·{votes}票' if votes else '')
        actor = key.split('-portrait-')[0]
        name = NAMES.get(actor, actor)
        emotion = {'joy': '欢喜', 'sad': '忧愁', 'surprise': '惊愕', 'angry': '气恼'}.get(
            key.rsplit('-', 1)[-1], key.rsplit('-', 1)[-1])
        rows.append((key, name, f'变体·{emotion}', side_cn(rec['facing']), basis))

    rows.sort(key=lambda r: (r[1], r[2], r[0]))

    left = sum(1 for r in rows if r[3] == '朝左')
    right = sum(1 for r in rows if r[3] == '朝右')
    measured = sum(1 for r in rows if r[4].startswith('实测'))
    visual = sum(1 for r in rows if r[4].startswith('目视'))

    out: list[str] = []
    out.append('# 人物位图朝向清单')
    out.append('')
    out.append('> 本文件由 `scripts/build_facing_doc.py` 从 `design/character-facing.json` 自动生成，请勿手工编辑。')
    out.append('> 权威数据是那张 JSON；改图后重跑 `scripts/facing_assets.py` → `scripts/build_facing.py` → 本脚本。')
    out.append('')
    out.append('## 总览')
    out.append('')
    out.append(f'- 位图总数 **{len(rows)}**（立绘 {sum(1 for r in rows if r[2] == "立绘")}、'
               f'Q版 {sum(1 for r in rows if r[2] == "Q版")}、'
               f'表情变体 {sum(1 for r in rows if r[2].startswith("变体"))}）')
    out.append(f'- 朝左 **{left}**，朝右 **{right}**')
    out.append(f'- 依据：实测 **{measured}**、目视裁决 **{visual}**')
    out.append('')
    out.append('「朝左 / 朝右」指的是**原图**里脸偏向画面的哪一侧——不是角色在剧情里该朝哪边。')
    out.append('运行时用它决定该用原图还是左右镜像：要求显示的一侧与原图不符时才镜像。')
    out.append('')
    out.append('## 逐张清单')
    out.append('')
    out.append('| 资产键 | 角色 | 类别 | 原图朝向 | 判定依据 |')
    out.append('| --- | --- | --- | --- | --- |')
    for key, name, kind, side, basis in rows:
        out.append(f'| `{key}` | {name} | {kind} | **{side}** | {basis} |')
    out.append('')
    out.append('## 朝左的位图（异常项，镜像逻辑要重点看）')
    out.append('')
    out.append('| 资产键 | 角色 | 类别 | 判定依据 |')
    out.append('| --- | --- | --- | --- |')
    for key, name, kind, side, basis in rows:
        if side == '朝左':
            out.append(f'| `{key}` | {name} | {kind} | {basis} |')
    out.append('')
    if props:
        out.append('## 不参与朝向判定的道具')
        out.append('')
        out.append('这些是场景道具，没有人物头，朝向无意义；运行时走各自的绘制分支。')
        out.append('')
        out.append('| 资产键 | 名称 | 类别 | 取值 |')
        out.append('| --- | --- | --- | --- |')
        for key, name, kind, side, _ in props:
            out.append(f'| `{key}` | {name} | {kind} | {side}（默认） |')
        out.append('')

    text = '\n'.join(out) + '\n'

    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            print('facing-list.md is out of date; run scripts/build_facing_doc.py')
            return 1
        print('facing-list.md is up to date')
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f'wrote {OUT.relative_to(ROOT)} ({len(rows)} bitmaps, {left} left, {right} right)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
