#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定点重注册蒋玉菡的两条 manifest 条目（性别更正后换了 seed）。

为什么不直接跑 build_art_assets.py
----------------------------------
它会从 calibration 表重写整个 manifest.json，把 86 个「画在标定管线之外」的
资产的 identity 块清空（features 丢失），并删掉 4 个 mourning 资产。像素其实
一致，但那 86 条的 features 会没——所以只能定点改。

为什么不整体 json.dumps
----------------------
manifest.json 是 Python 3.12 的 json.dumps(indent=1) 产物：数组首元素与 '['
同行（`"faceBox": [42,`）。当前是 Python 3.13，首元素会另起一行，整体重写
会让 46 条 faceBox 产生纯格式噪声 diff，看着像改了 46 个角色。

本脚本的做法
------------
在蒋玉菡的两块内**逐字段做行级替换**：找到 `"字段名":` 所在行，把该字段的
值行整体替换掉，缩进与数组风格沿用该字段的既有写法。其它字节一律不动。

几何复刻
--------
`geometry()` 是 `scripts/build_art_assets.py` 单资产流水线的逐行复刻
（alpha 阈值 → bodyCompress → 剪裁 bbox → 按 height 缩放 → anchor 缩放）。
`--verify` 用**旧 seed 的旧素材**跑一遍，和旧 manifest 的数值逐位比对，
确认复刻无误后才允许写入。

用法：
  python3 scripts/reregister_jiangyuhan_manifest.py --verify   # 只比对，不写
  python3 scripts/reregister_jiangyuhan_manifest.py            # 写入
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'public/assets/rongguo/manifest.json'
CAL = ROOT / 'art/calibration.json'
DESIGNS = ROOT / 'art/identity/character-designs.json'
ASSET_DIR = ROOT / 'public/assets/rongguo'

TARGETS = ['jiang_yuhan-portrait', 'jiang_yuhan-chibi']


def geometry(item):
    """复刻 build_art_assets.py 的单资产几何，返回 dict。"""
    stem = f"{item.get('sourceId', item['id'])}_s{item['seed']}"
    im = Image.open(ROOT / f'art/matted/{stem}-sam.png').convert('RGBA')

    # alpha 阈值：只保留实心像素，边缘抗锯齿交给输出尺寸
    a = np.asarray(im.getchannel('A')).copy()
    a = np.where(a >= 110, 255, 0).astype('uint8')
    im.putalpha(Image.fromarray(a))

    for polygon in item.get('clearPolygons', []):
        from PIL import ImageDraw
        ImageDraw.Draw(im).polygon([tuple(p) for p in polygon], fill=(0, 0, 0, 0))

    ax, ay = item['anchor']
    if 'bodyCompress' in item:
        split = item['bodyCompress']['split']
        f = item['bodyCompress']['factor']
        lower = im.crop((0, split, im.width, im.height)).resize(
            (im.width, round((im.height - split) * f)), Image.Resampling.LANCZOS)
        joined = Image.new('RGBA', (im.width, split + lower.height))
        joined.paste(im.crop((0, 0, im.width, split)), (0, 0))
        joined.paste(lower, (0, split))
        im = joined
        ay = split + (ay - split) * f if ay > split else ay

    bbox = im.getbbox()
    im = im.crop(bbox)
    ax -= bbox[0]
    ay -= bbox[1]

    factor = item['height'] / im.height
    size = (round(im.width * factor), round(im.height * factor))
    ax *= size[0] / (bbox[2] - bbox[0])
    ay *= size[1] / (bbox[3] - bbox[1])

    return {
        'width': size[0],
        'height': size[1],
        'anchor': [round(ax, 3), round(ay, 3)],
        'source': f'art/source/{stem}-01.png',
        'matte': f'art/matted/{stem}-sam.png',
        'crop': list(bbox),
        'shear': item.get('targetSlope', 0) - item.get('baseSlope', 0),
        'mirror': item.get('mirror', False),
        'bodyCompress': item.get('bodyCompress'),
    }


# --- 行级定点替换 ------------------------------------------------------------

def find_block(lines, sid):
    """返回 (start, end)：资产块在 lines 中的行区间（end 为块内最后一行）。"""
    start = None
    indent = None
    for i, line in enumerate(lines):
        m = re.match(r'(\s*)"' + re.escape(sid) + r'":\s*\{\s*$', line)
        if m:
            start = i
            indent = m.group(1)
            break
    if start is None:
        raise ValueError(f'未定位 {sid}')
    end = None
    for j in range(start + 1, len(lines)):
        if re.match(re.escape(indent) + r'"[^"]+":\s*\{\s*$', lines[j]):
            end = j - 1
            break
    if end is None:
        raise ValueError(f'未定位 {sid} 的块尾')
    return start, end


def _value_span(lines, i, end):
    """返回 (j, style)：字段值占用的行区间 j（含），以及数组排布风格。

    只有值本身以 '[' 或 '{' 开头时才做括号配平——features 这类字符串里
    可能含方括号，按整行配平会数错，把下一行也吞进字段范围。
    """
    tail = lines[i].split(':', 1)[1].strip()
    if tail == '[':
        style = 'newline-first'    # `"anchor": [` 之后另起一行写首元素
    elif tail == '{':
        style = 'newline-first'
    elif tail.startswith('['):
        style = 'inline-first'      # `"faceBox": [118,` 首元素与 '[' 同行
    elif tail.startswith('{'):
        style = 'inline-first'
    else:
        # 标量值（数字 / 字符串 / null / true）：只占这一行
        return i, 'scalar'
    depth = 0
    j = i
    while j <= end:
        depth += lines[j].count('[') - lines[j].count(']')
        depth += lines[j].count('{') - lines[j].count('}')
        if depth <= 0 and j >= i:
            break
        j += 1
    return j, style


def _render(value, style, indent):
    """按既有排布风格渲染值。

    indent 是字段所在行的缩进列数。文件里的数组/对象一律是「续行缩进 = indent + 1，
    收尾括号缩进 = indent」：

        "anchor": [          <- newline-first：首元素另起一行
         173.465,
         599.444
        ],
        "faceBox": [118,     <- inline-first：首元素与 '[' 同行
         37,
         156,
         69
        ]
    """
    sp = ' ' * indent
    inner = sp + ' '
    if isinstance(value, list):
        if not value:
            return '[]'
        parts = [json.dumps(v, ensure_ascii=False) for v in value]
        if style == 'inline-first':
            body = (',\n' + inner).join(parts)
            return '[' + body + '\n' + sp + ']'
        body = (',\n' + inner).join(parts)
        return '[\n' + inner + body + '\n' + sp + ']'
    if isinstance(value, dict):
        if not value:
            return '{}'
        rows = [f'{inner}{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}'
                for k, v in value.items()]
        return '{\n' + ',\n'.join(rows) + '\n' + sp + '}'
    return json.dumps(value, ensure_ascii=False)


def replace_field(lines, sid, field, value):
    """在 sid 块内把 `"field": ...` 的值替换掉；返回新 lines。

    原值的行尾逗号要保留——JSON 里最后一个成员也可以带逗号之外的标点，
    抹掉它会让文件解析失败。
    """
    lines = list(lines)
    start, end = find_block(lines, sid)
    pat = re.compile(r'^(\s*)"' + re.escape(field) + r'":\s*')
    for i in range(start, end + 1):
        m = pat.match(lines[i])
        if not m:
            continue
        j, style = _value_span(lines, i, end)
        # 记下原值行尾的逗号（标量值就在本行，数组值在收尾行）
        tail_comma = ''
        for k in range(j, i - 1, -1):
            if lines[k].rstrip().endswith(','):
                tail_comma = ','
                break
            if lines[k].rstrip().endswith((']', '}')):
                break
        field_indent = m.group(1)
        value_indent = len(field_indent)
        rendered = _render(value, style, value_indent).split('\n')
        new_block = [f'{field_indent}"{field}": {rendered[0]}'] + rendered[1:]
        if tail_comma and not new_block[-1].endswith(','):
            new_block[-1] = new_block[-1] + ','
        lines[i:j + 1] = new_block
        return lines
    raise ValueError(f'未定位字段 {field} @ {sid}')


def main() -> int:
    verify = '--verify' in sys.argv

    cal = {a['id']: a for a in json.loads(CAL.read_text(encoding='utf-8'))['assets']}
    designs = {c['id']: c for c in
               json.loads(DESIGNS.read_text(encoding='utf-8'))['characters']}
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))

    # --- 自检：先用旧 seed 的旧素材复刻几何，与旧 manifest 逐位比对 ---
    old_cal = {a['id']: a for a in json.loads(
        (ROOT / 'art/calibration.json').read_text(encoding='utf-8'))['assets']}
    legacy = {
        'jiang_yuhan-portrait': {'id': 'jiang_yuhan-portrait', 'seed': 10237110,
                                 'height': 600, 'anchor': [413, 1119]},
        'jiang_yuhan-chibi': {'id': 'jiang_yuhan-chibi', 'seed': 10237111,
                              'height': 116, 'anchor': [429, 945],
                              'bodyCompress': {'split': 397, 'factor': 0.64}},
    }
    for sid, item in legacy.items():
        got = geometry(item)
        want = manifest['assets'][sid]
        for k in ('width', 'height', 'anchor', 'crop', 'bodyCompress'):
            assert got[k] == want[k], f'{sid}.{k}: 复刻={got[k]} 旧manifest={want[k]}'
    print('几何复刻自检通过（旧 seed 与旧 manifest 逐位一致）')

    if verify:
        print('--verify：仅自检，未写文件')
        return 0

    raw = MANIFEST.read_text(encoding='utf-8')
    lines = raw.split('\n')

    # faceBox 来自 art/identity/auto-face-boxes.json（人工目视重标过的那份），
    # 单位是**最终 PNG 的像素坐标**。
    boxes = json.loads((ROOT / 'art/identity/auto-face-boxes.json').read_text(encoding='utf-8'))

    for sid in TARGETS:
        cid = sid.rsplit('-', 1)[0]
        item = cal[sid]
        g = geometry(item)
        stem = f"{item.get('sourceId', sid)}_s{item['seed']}"

        # hash 是 **WebP 的 md5**（scripts/build_webp.mjs 用它做缓存版本号），
        # 不是 PNG 的 sha256。必须先有 .webp 才能算，所以这里读 WebP。
        webp = ASSET_DIR / f'{sid}.webp'
        if not webp.exists():
            raise FileNotFoundError(f'{webp} 不存在；先跑 npm run art:webp')
        digest = hashlib.md5(webp.read_bytes()).hexdigest()[:12]

        new_fields = [
            ('width', g['width']),
            ('height', g['height']),
            ('anchor', g['anchor']),
            ('source', g['source']),
            ('matte', g['matte']),
            ('crop', g['crop']),
            ('bodyCompress', g['bodyCompress']),
            ('hash', digest),
            ('seed', item['seed']),
            ('features', designs[cid]['features']),
            ('faceBox', boxes[sid]),
        ]
        for field, value in new_fields:
            lines = replace_field(lines, sid, field, value)

        print(f'{sid}: {g["width"]}x{g["height"]} anchor={g["anchor"]} '
              f'crop={g["crop"]} hash={digest} faceBox={boxes[sid]}')

    raw = '\n'.join(lines)
    back = json.loads(raw)
    for sid in TARGETS:
        cid = sid.rsplit('-', 1)[0]
        ident = back['assets'][sid]['identity']
        assert ident['seed'] == cal[sid]['seed'], sid
        assert ident['features'] == designs[cid]['features'], sid
        assert ident['faceBox'] == boxes[sid], sid
        # hash 必须等于 WebP 的 md5 —— 运行时把它当缓存版本号用
        assert back['assets'][sid]['hash'] == hashlib.md5(
            (ASSET_DIR / f'{sid}.webp').read_bytes()).hexdigest()[:12], sid
    MANIFEST.write_text(raw, encoding='utf-8')
    print('manifest 已定点更新 2 条')
    return 0


if __name__ == '__main__':
    sys.exit(main())
