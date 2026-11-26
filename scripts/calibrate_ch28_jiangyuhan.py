#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新校准第 28 回蒋玉菡的立绘与 Q 版（性别更正后换了 seed）。

第一版把蒋玉菡画成粉衣女子。底本第二十八回明写他是「唱小旦的蒋玉菡」——
小旦是戏曲行当，指**男演员扮演旦角**；本回又与薛蟠、冯紫英并称「令表兄弟」，
可知本名为男性优伶，艺名琪官。

重做后换了 seed（10237110 → 10237120），因此校准条目里的 seed、anchor 与
Q 版的 bodyCompress 都要重算。本脚本只改 `art/calibration.json` 里蒋玉菡的
两条，不动其它资产。

校准口径与 scripts/calibrate_ch24_chars.py 一致：
  * feet anchor = 最底不透明行（alpha >= 110，与 build_art_assets.py 同阈值）
    的中点 x；
  * 按 **height** 缩放（立绘 600、Q 版 116），使人物与全组等高；
  * Q 版给 bodyCompress（split = 0.42 × 脚底行，factor 0.64），与旧 Q 版中位契约一致。

用法：
  python3 scripts/calibrate_ch28_jiangyuhan.py
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT / 'art/matted'
CAL = ROOT / 'art/calibration.json'

CHARS = {'jiang_yuhan': 10237120}
PORTRAIT_H = 600
CHIBI_H = 116
CHIBI_SPLIT_RATIO = 0.42
CHIBI_FACTOR = 0.64


def feet_anchor(stem: str):
    """Bottom-most opaque row, x = centre of that row."""
    p = MAT / f'{stem}-sam.png'
    if not p.exists():
        raise FileNotFoundError(p)
    a = np.asarray(Image.open(p).convert('RGBA'))[..., 3]
    a = np.where(a >= 110, 255, 0).astype(np.uint8)
    rows = np.where(a.max(axis=1) > 0)[0]
    if len(rows) == 0:
        raise ValueError(f'{stem}: no opaque pixels (blank matte?)')
    feet_y = int(rows.max())
    xs = np.where(a[feet_y] > 0)[0]
    cx = int((xs.min() + xs.max()) / 2)
    return [cx, feet_y], (int(rows.min()), feet_y)


def main() -> int:
    cal = json.loads(CAL.read_text(encoding='utf-8'))
    by_id = {a['id']: a for a in cal['assets']}

    for cid, seed_base in CHARS.items():
        for kind, height in (('portrait', PORTRAIT_H), ('chibi', CHIBI_H)):
            sid = f'{cid}-{kind}'
            seed = seed_base + (1 if kind == 'chibi' else 0)
            anchor, (top, bottom) = feet_anchor(f'{sid}_s{seed}')
            item = by_id.get(sid)
            if item is None:
                item = {'id': sid, 'seed': seed}
                cal['assets'].append(item)
            item.pop('width', None)
            item['seed'] = seed
            item['height'] = height
            item['anchor'] = anchor
            if kind == 'chibi':
                item['bodyCompress'] = {'split': round(bottom * CHIBI_SPLIT_RATIO),
                                        'factor': CHIBI_FACTOR}
            print(f'{sid}: anchor={anchor} height={height}'
                  + (f' compress={item["bodyCompress"]}' if kind == 'chibi' else '')
                  + f'  (content rows {top}-{bottom})')

    shutil.copy2(CAL, Path('/tmp/calibration-backup-before-jy.json'))
    CAL.write_text(json.dumps(cal, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'calibration rewritten ({len(cal["assets"])} entries)')
    by_id = {a['id']: a for a in cal['assets']}

    for cid, seed_base in CHARS.items():
        for kind, height in (('portrait', PORTRAIT_H), ('chibi', CHIBI_H)):
            sid = f'{cid}-{kind}'
            seed = seed_base + (1 if kind == 'chibi' else 0)
            src = MAT / f'{sid}_s{seed}-sam.png'
            im = Image.open(src)
            ratio = height / im.height
            w = round(im.width * ratio)
            item = by_id[sid]
            ax, ay = item['anchor']
            ax_scaled, ay_scaled = ax * ratio, ay * ratio
            ok = 0 <= ax_scaled <= w and 0 <= ay_scaled <= height + 1
            print(f'  {sid}: scaled {w}x{height} anchor=({ax_scaled:.0f},{ay_scaled:.0f})'
                  + ('' if ok else '  <== ANCHOR OUT OF BITMAP'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
