#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 character-designs.json 的每个角色注入显式性别锚定。

起因：第 26-30 回的司棋因提示词缺性别词，被 qwen21 画成男性青年。
本脚本把 scripts/character_gender_map.py 的底本依据固化到
art/identity/character-designs.json 的 prompt 与 features。

规则：
  · prompt 开头插入「<ANCHOR>, 」形式的性别锚（qwen 对大写关键词敏感）。
  · features 末尾追加「性别：…（依据：…）」，依据逐字来自底本。
  · 已有性别锚的角色不重复插入，只补 features 依据。
  · 只改 prompt/features，不动 seed，因此不触发重新生图。

用法：
  python3 scripts/build_gender_anchored_prompts.py            # 写入
  python3 scripts/build_gender_anchored_prompts.py --check    # 只校验不写
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from character_gender_map import table  # noqa: E402

DESIGNS = ROOT / 'art/identity/character-designs.json'
ANCHOR_RE = re.compile(r'\b(WOMAN|GIRL|FEMALE|MAN|MALE|BOY)\b')
# 「更明确的否定式」锚：女性加 not a man，男性加 not a woman
NEG = {
    'WOMAN': 'a WOMAN, not a man',
    'GIRL': 'a GIRL, not a boy',
    'FEMALE': 'a FEMALE, not a man',
    'MAN': 'a MAN, not a woman',
    'MALE': 'a MALE, not a woman',
    'BOY': 'a BOY, not a woman',
}


def _tidy(text: str) -> str:
    """收掉注入锚时可能留下的多余空白与重复逗号。

    旧锚是从句时被整句删掉，接缝处常留下「a WOMAN, not a man,  angular ...」
    这样的双空格。提示词里多一个空格不会让模型画错，但会让 diff 出现噪声，
    所以这里统一压平。
    """
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r',\s*,', ',', text)
    text = re.sub(r'\s+,', ',', text)
    return text.strip()


def inject(prompt: str, anchor: str) -> str:
    """在 prompt 开头插入性别锚；若已带锚则按需补强否定式。"""
    head = NEG[anchor]
    existing = ANCHOR_RE.search(prompt)
    if existing:
        if 'not a' in prompt:
            # 已经是「a WOMAN, not a man」这种写法：只把空白收平，不动语义。
            # 不收平的话，旧锚是从句被删掉时接缝处会留「not a man,  angular」
            # 的双空格——不影响出图，但会让 diff 出现噪声。
            return _tidy(prompt)
        # 旧锚是「; a young BOY rather than a woman」这类从句，
        # 直接删掉旧锚所在分句，再在句首插入新锚，避免语义重复。
        m = re.search(r'[;,]\s*[^;,]*\b' + re.escape(existing.group(0)) +
                      r'\b[^;,]*(?:rather than|not a)\s+(?:a\s+)?(?:woman|man|boy|girl)\b',
                      prompt, re.I)
        if m:
            rest = (prompt[:m.start()] + prompt[m.end():]).strip()
            rest = re.sub(r'[,;]\s*[,;]', ',', rest).strip(' ,;')
            return _tidy(f'{head}, {rest}')
        # 兜底：直接替换锚词
        before = prompt[:existing.start()].rstrip()
        after = prompt[existing.end():].lstrip()
        if before.endswith('a') or before.endswith('an'):
            before = before[:-2].rstrip().rstrip(',')
        after = after.lstrip(',').lstrip()
        prompt = f'{before} {head}, {after}'.replace('  ', ' ')
        prompt = re.sub(r',\s*,', ',', prompt)
        prompt = re.sub(r'\s+,', ',', prompt)
        return prompt
    # 新插入时避免与后文冠词重复（"a a MAN"）
    body = prompt
    if body.startswith('a ') or body.startswith('an '):
        body = body[2:]
    return _tidy(f'{head}, {body}')


def gender_feature(anchor: str, evidence: str) -> str:
    label = {
        'WOMAN': '女', 'GIRL': '女', 'FEMALE': '女',
        'MAN': '男', 'MALE': '男', 'BOY': '男',
    }[anchor]
    return f'性别：{label}（依据：{evidence}）'


def main():
    check_only = '--check' in sys.argv
    data = json.loads(DESIGNS.read_text(encoding='utf-8'))
    t = table()
    changed = 0
    missing = []
    for c in data['characters']:
        cid = c['id']
        if cid not in t:
            missing.append(cid)
            continue
        anchor, evidence = t[cid]
        new_prompt = inject(c['prompt'], anchor)
        gf = gender_feature(anchor, evidence)
        new_features = c['features']
        # 已有一段性别依据时不重复追加；改为把新依据并入原有依据的括号里
        m = re.search(r'性别：([男女])（([^）]*)）', new_features)
        if m:
            old = m.group(2)
            if evidence not in old:
                merged = f'{old}；{evidence}'
                new_features = new_features[:m.start(2)] + merged + new_features[m.end(2):]
        elif gf not in new_features:
            new_features = f'{new_features}；{gf}' if new_features else gf
        if new_prompt != c['prompt'] or new_features != c['features']:
            changed += 1
            if not check_only:
                c['prompt'] = new_prompt
                c['features'] = new_features

    if missing:
        print('性别表缺失的角色：', missing)

    # 校验：每个角色必须有锚 + features 必须含性别依据
    bad = []
    for c in data['characters']:
        if not ANCHOR_RE.search(c['prompt']):
            bad.append(f"{c['id']}: prompt 无性别锚")
        if '性别：' not in c['features']:
            bad.append(f"{c['id']}: features 无性别依据")

    if check_only:
        print(f'校验：{len(data["characters"])} 个角色，问题 {len(bad)} 条')
        for b in bad:
            print('  ', b)
        return 1 if bad else 0

    if bad:
        print('写入前校验未通过，已中止：')
        for b in bad:
            print('  ', b)
        return 1

    DESIGNS.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'已更新 {changed} 个角色（共 {len(data["characters"])}）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
