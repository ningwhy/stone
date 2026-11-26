#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 character-designs.json 的 features（含性别依据）同步到 manifest。

纪律：
  · 只改 assets/*/identity/features 这一个字段，不动其它键序。
  · 用正则定点替换，避免 json.dump 全量重排 manifest 缩进。
  · 表情变体（-angry/-joy/-sad/-surprise）继承同一 features。

用法：
  python3 scripts/sync_gender_features_to_manifest.py           # 写入
  python3 scripts/sync_gender_features_to_manifest.py --check   # 只校验
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGNS = ROOT / 'art/identity/character-designs.json'
MANIFEST = ROOT / 'public/assets/rongguo/manifest.json'


def main():
    check_only = '--check' in sys.argv
    designs = json.loads(DESIGNS.read_text(encoding='utf-8'))
    feats = {c['id']: c['features'] for c in designs['characters']}

    raw = MANIFEST.read_text(encoding='utf-8')
    manifest = json.loads(raw)
    assets = manifest['assets']

    # 收集需要改的资产：键形如 {cid}-portrait / {cid}-chibi / {cid}-portrait-angry
    targets = []
    for key, val in assets.items():
        ident = val.get('identity')
        if not isinstance(ident, dict):
            continue
        cid = ident.get('character')
        if not cid or 'features' not in ident:
            continue
        if cid not in feats:
            continue
        targets.append((key, ident['features'], feats[cid]))

    diffs = [(k, o, n) for k, o, n in targets if o != n]
    if check_only:
        stale = [k for k, o, n in diffs]
        print(f'待同步 {len(diffs)} 条 / 共 {len(targets)} 条身份记录')
        for k in stale[:10]:
            print('  ', k)
        return 0

    if not diffs:
        print('manifest 已是最新，无需改动')
        return 0

    # 定点替换：把 "features": "<旧值>" 换成新值。
    # 用 json.dumps 的字符串转义保证与文件里的写法一致。
    changed = 0
    for key, old, new in diffs:
        old_lit = json.dumps(old, ensure_ascii=False)
        new_lit = json.dumps(new, ensure_ascii=False)
        # 定位该资产块内的 features 字段
        km = re.search(r'"' + re.escape(key) + r'"\s*:\s*\{', raw)
        if not km:
            print(f'  !! 未定位资产 {key}')
            continue
        # 从资产起点往后找第一个 features
        fm = re.search(r'"features"\s*:\s*' + re.escape(old_lit), raw[km.end():])
        if not fm:
            print(f'  !! 未定位 {key} 的 features（值可能已变）')
            continue
        start = km.end() + fm.start()
        end = km.end() + fm.end()
        raw = raw[:start] + '"features": ' + new_lit + raw[end:]
        changed += 1

    # 复核：解析后的 JSON 里 features 必须等于设计表
    back = json.loads(raw)
    bad = []
    for key, val in back['assets'].items():
        ident = val.get('identity')
        if isinstance(ident, dict) and 'features' in ident:
            cid = ident.get('character')
            if cid in feats and ident['features'] != feats[cid]:
                bad.append(key)
    if bad:
        print(f'写入后校验失败 {len(bad)} 条：{bad[:10]}')
        return 1

    MANIFEST.write_text(raw, encoding='utf-8')
    print(f'已同步 {changed} 条 manifest features')
    return 0


if __name__ == '__main__':
    sys.exit(main())
