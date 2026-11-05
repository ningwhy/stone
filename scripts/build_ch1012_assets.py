#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibrate and build the seven chapter-10/11/12 characters.

为什么不是直接跑 build_new_char_assets.py：那脚本按「校准条目已存在就跳过」设计，
而这里需要的恰恰是**按当前这张图重新测锚点**，并套用旧 45 人的缩放契约。

契约（与第十回之前所有人物一致，见 docs/production/art.md）：
  - portrait 用 `height: 600` / chibi 用 `height: 116`
    旧人物按高缩放，所以众人等高、只有胖瘦改宽度；用 width 会高矮参差。
  - chibi 带 `bodyCompress`（split = 脚底锚点 × 0.42，factor = 0.64）
    —— 大头小身的比例靠它，没有就不是 Q 版。
  - anchor 从当前 matted 位图实测脚底：换过画布就必须重测，
    沿用旧坐标会让人物在地图上悬空或沉地。

幂等：重复跑会重新测量并收敛。

Usage: python3 scripts/build_ch1012_assets.py
"""
import json, shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT / 'art/matted'
CAL = ROOT / 'art/calibration.json'
ENTRY = ROOT / 'maps/rongguo-entry.tmj'
BACKUP = Path('/tmp/rongguo-entry-backup.tmj')

_SEEDS = {c['id']: c['seed'] for c in
          json.loads((ROOT / 'art/identity/character-designs.json').read_text())['characters']}
CHARS = {k: _SEEDS[k] for k in
         ('you_shi', 'jia_zhen', 'jin_shi', 'hu_shi', 'zhang_youshi', 'jia_qiang', 'jia_dairu')}

PORTRAIT_H = 600
CHIBI_H = 116
CHIBI_SPLIT_RATIO = 0.42
CHIBI_FACTOR = 0.64


def feet_anchor(stem):
    """Bottom-most opaque row, x = centre of that row. Same threshold as build_art_assets."""
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


def main():
    cal = json.loads(CAL.read_text())
    shutil.copy2(CAL, Path('/tmp/calibration-backup-before-ch1012.json'))
    by_id = {a['id']: a for a in cal['assets']}
    changed = 0
    for cid, seed in CHARS.items():
        for kind, height in (('portrait', PORTRAIT_H), ('chibi', CHIBI_H)):
            sid = f'{cid}-{kind}'
            s = seed + (1 if kind == 'chibi' else 0)
            anchor, (top, bottom) = feet_anchor(f'{sid}_s{s}')
            item = by_id.get(sid)
            if item is None:
                # 新人物第一次入册。字段必须与旧人物一致：build_art_assets.py 靠
                # `seed` 拼源图名（`{id}_s{seed}-sam.png`），缺了会直接 KeyError。
                item = {'id': sid, 'seed': s}
                cal['assets'].append(item)
                by_id[sid] = item
                print('NEW calibration entry', sid)
            item['seed'] = s
            item.pop('width', None)
            item['height'] = height
            item['anchor'] = anchor
            if kind == 'chibi':
                item['bodyCompress'] = {'split': round(bottom * CHIBI_SPLIT_RATIO),
                                        'factor': CHIBI_FACTOR}
            print(f'{sid}: anchor={anchor} height={height}'
                  + (f' compress={item["bodyCompress"]}' if kind == 'chibi' else '')
                  + f'  (content rows {top}-{bottom})')
            changed += 1
    CAL.write_text(json.dumps(cal, ensure_ascii=False, indent=1) + '\n')
    print(f'calibration rewritten ({changed} entries)')

    if ENTRY.exists():
        shutil.copy2(ENTRY, BACKUP)
    print('running build_art_assets.py ...')
    r = subprocess.run([sys.executable, str(ROOT / 'scripts/build_art_assets.py')], cwd=ROOT)
    if ENTRY.exists() and BACKUP.exists():
        shutil.copy2(BACKUP, ENTRY)
        print('restored maps/rongguo-entry.tmj (portraits are not map props)')
    r.check_returncode()

    man = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())['assets']
    print('--- rebuilt ---')
    bad = 0
    for cid in CHARS:
        for kind in ('portrait', 'chibi'):
            key = f'{cid}-{kind}'
            a = man.get(key)
            if not a:
                print('  MISSING', key); bad += 1; continue
            ax, ay = a['anchor']
            ok = 0 <= ax <= a['width'] and 0 <= ay <= a['height'] + 1
            if not ok:
                bad += 1
            print(f"  {key}: {a['width']}x{a['height']} anchor={a['anchor']}"
                  + ('' if ok else '  <== ANCHOR OUT OF BITMAP'))
    print('anchor problems:', bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
