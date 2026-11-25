#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Refresh the asset tables in the chapter 26-30 character sheets.

The sheets are written by hand, but the numbers in them — size, anchor,
faceBox, seed, hash, facing, and the prompt the picture was made from — are
copies of what the manifest and the facing table actually hold. When a
character is repainted (as 司棋 was, after the first portrait came out as a
man), those copies go stale and the sheet starts describing a picture that is
no longer in the build.

This script rewrites those blocks from the authoritative files:

    public/assets/rongguo/manifest.json   -> 尺寸 / anchor / faceBox / seed /
                                            bodyCompress / hash
    design/character-facing.json           -> 朝向裁决
    art/identity/character-designs.json    -> 英文生图提示词 / features

Only the blocks it recognises are touched; the prose around them is left
alone, because the prose is the part that carries the research.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())['assets']
FACING = json.loads((ROOT / 'design/character-facing.json').read_text())['actors']
DESIGNS = {c['id']: c for c in
           json.loads((ROOT / 'art/identity/character-designs.json').read_text())['characters']}

CHAPTERS = {
    26: ['jiahui', 'zhuer', 'qingwen', 'feng_ziying'],
    27: ['siqi', 'qixian'],
    28: ['jiang_yuhan', 'yun_er'],
    29: ['zhang_daoshi'],
    30: ['lingguan'],
}

ASSET_RE = re.compile(
    r'(### 资产参数\n\n\| 项 \| 立绘 \| Q 版 \|\n\| --- \| --- \| --- \|\n)'
    r'\| 尺寸 \| .*? \|\n'
    r'\| anchor \| .*? \|\n'
    r'\| faceBox \| .*? \|\n'
    r'\| seed \| .*? \|\n'
    r'\| bodyCompress \| .*? \|\n'
    r'\| hash \| .*? \|\n')

FACING_RE = re.compile(
    r'(- portrait \*\*(\w+)\*\*（`([\w-]+)`）\n'
    r'- chibi \*\*(\w+)\*\*（`([\w-]+)`）\n)')

PROMPT_RE = re.compile(r'(英文生图提示词：)(.+?)。\n')


def asset_block(cid: str) -> str:
    p = MANIFEST[f'{cid}-portrait']
    c = MANIFEST[f'{cid}-chibi']
    bc = c.get('bodyCompress')
    bc_txt = '—' if not bc else f"`{{'split': {bc['split']}, 'factor': {bc['factor']}}}`"
    return (
        '| 尺寸 | {pw}×{ph} | {cw}×{ch} |\n'
        '| anchor | `[{pa[0]}, {pa[1]}]` | `[{ca[0]}, {ca[1]}]` |\n'
        '| faceBox | `[{pf[0]}, {pf[1]}, {pf[2]}, {pf[3]}]` | `[{cf[0]}, {cf[1]}, {cf[2]}, {cf[3]}]` |\n'
        '| seed | {pseed} | {cseed} |\n'
        '| bodyCompress | — | {bc} |\n'
        '| hash | `{phash}` | `{chash}` |\n'
    ).format(pw=p['width'], ph=p['height'], cw=c['width'], ch=c['height'],
             pa=p['anchor'], ca=c['anchor'],
             pf=p['identity']['faceBox'], cf=c['identity']['faceBox'],
             pseed=p['identity']['seed'], cseed=c['identity']['seed'],
             bc=bc_txt, phash=p.get('hash', ''), chash=c.get('hash', ''))


def facing_block(cid: str) -> str:
    f = FACING[cid]
    pe = f['evidence']['portrait']
    ce = f['evidence']['chibi']
    return ('- portrait **{p}**（`{pm}`）\n'
            '- chibi **{c}**（`{cm}`）\n').format(
        p=f['portrait'], c=f['chibi'], pm=pe['method'], cm=ce['method'])


def refresh(path: Path, ids) -> int:
    text = path.read_text(encoding='utf-8')
    changed = 0
    for cid in ids:
        # The character section starts at its heading; work within that slice
        # so one character's blocks never leak into the next.
        head = re.search(r'^## \S+ `%s`$' % re.escape(cid), text, re.M)
        if not head:
            print(f'  {cid}: no section heading in {path.name}')
            continue
        tail = re.search(r'^## \S+ `', text[head.end():], re.M)
        end = head.end() + tail.start() if tail else len(text)
        section = text[head.start():end]

        new_section, n1 = ASSET_RE.subn(lambda m: m.group(1) + asset_block(cid), section)
        new_section, n2 = FACING_RE.subn(lambda m: facing_block(cid), new_section)
        design = DESIGNS[cid]
        new_section, n3 = PROMPT_RE.subn(
            lambda m: m.group(1) + design['prompt'] + '。\n', new_section)
        # features: the sheet quotes it verbatim inside bold markers.
        new_section = new_section.replace(
            f"**{design['features'].split('。性别')[0]}**。",
            f"**{design['features']}**。")

        if new_section != section:
            text = text[:head.start()] + new_section + text[end:]
            changed += 1
            print(f'  {cid}: asset={n1} facing={n2} prompt={n3}')
    if changed:
        path.write_text(text, encoding='utf-8')
    return changed


def main():
    total = 0
    for ch, ids in CHAPTERS.items():
        path = ROOT / f'docs/chapter{ch}-characters.md'
        print(f'--- {path.name}')
        total += refresh(path, ids)
    print(f'refreshed {total} character sheets')


if __name__ == '__main__':
    main()
