#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把第 20 回的 4 名新角色（贾环/赵姨娘/史湘云/麝月）装进运行时资产。

流程（照第 16 回 yuanchun/jia_lian 的做法）：
  1. 从 art/matted/{id}-{kind}_s{seed}-sam.png 量脚底锚点；
  2. 追加 art/calibration.json 条目（portrait height=600 / chibi height=116，
     chibi 另带 bodyCompress，让 Q 版保持大头小身）；
  3. 跑 build_art_assets.py 生成 public/assets/rongguo/{id}.png 与 manifest；
     该脚本会重排整个 manifest，所以先备份、跑完再由
     rebuild_new_character_manifest.py 把 identity 块注回去；
  4. 用 art/identity/auto-face-boxes.json 里的脸框补 identity.faceBox
     （没有脸框的以全身像呈现，不是错误）。

★ 校准用 height 而不是 width：老角色都是按 height 统一到 600/116，
  新角色若按 width 缩放会跟旧角色站在不同高度上。
★ build_art_assets.py 曾经会静默抹掉不在 approved 集里的 identity 块，
  已修为保留既有 identity；跑完仍要 git diff manifest 看 identity 在不在。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAT = ROOT / 'art/matted'
CAL = ROOT / 'art/calibration.json'
ENTRY = ROOT / 'maps/rongguo-entry.tmj'

# 角色 id -> (portrait seed, chibi seed)
CHARS = {
    'jia_huan': (10234010, 10234011),
    'zhao_yiniang': (10234020, 10234021),
    'shi_xiangyun': (10234030, 10234031),
    'she_yue': (10234040, 10234041),
}
PORTRAIT_H = 600
CHIBI_H = 116
CHIBI_SPLIT_RATIO = 0.42   # 38 张压缩 Q 版 split/anchorY 的中位数
CHIBI_FACTOR = 0.64        # 它们的多数取值


def feet_anchor(stem: str):
    """最底下一行不透明像素的中点（与 build_art_assets 的阈值一致）。"""
    p = MAT / f'{stem}-sam.png'
    if not p.exists():
        raise FileNotFoundError(p)
    im = Image.open(p).convert('RGBA')
    a = np.asarray(im)[..., 3]
    a = np.where(a >= 110, 255, 0).astype(np.uint8)
    rows = np.where(a.max(axis=1) > 0)[0]
    if len(rows) == 0:
        raise ValueError(f'{stem}: no opaque pixels')
    feet_y = int(rows.max())
    row = a[feet_y]
    xs = np.where(row > 0)[0]
    cx = int((xs.min() + xs.max()) / 2) if len(xs) else im.width // 2
    return [cx, feet_y]


def main() -> int:
    cal = json.loads(CAL.read_text(encoding='utf-8'))
    existing = {a['id'] for a in cal['assets']}
    added = 0
    for cid, (p_seed, c_seed) in CHARS.items():
        for kind, seed, height in (('portrait', p_seed, PORTRAIT_H), ('chibi', c_seed, CHIBI_H)):
            sid = f'{cid}-{kind}'
            if sid in existing:
                print('skip (calibrated)', sid)
                continue
            stem = f'{sid}_s{seed}'
            anchor = feet_anchor(stem)
            entry = {'id': sid, 'seed': seed, 'anchor': anchor, 'height': height}
            if kind == 'chibi':
                split = int(round(anchor[1] * CHIBI_SPLIT_RATIO))
                entry['bodyCompress'] = {'split': split, 'factor': CHIBI_FACTOR}
            cal['assets'].append(entry)
            print(f'add {sid} anchor={anchor} height={height}'
                  + (f' bodyCompress={entry["bodyCompress"]}' if kind == 'chibi' else ''))
            added += 1
    if added:
        CAL.write_text(json.dumps(cal, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(f'calibration updated (+{added})')
    else:
        print('calibration already up to date')

    # build_art_assets.py 会重排整个 map 的 Art 层；立绘不进地图，
    # 所以备份 rongguo-entry.tmj，跑完原样恢复。
    backup = Path('/tmp/rongguo-entry-backup.tmj')
    if ENTRY.exists():
        shutil.copy2(ENTRY, backup)
    print('running build_art_assets.py ...')
    r = subprocess.run([sys.executable, str(ROOT / 'scripts/build_art_assets.py')], cwd=ROOT)
    if ENTRY.exists() and backup.exists():
        shutil.copy2(backup, ENTRY)
        print('restored maps/rongguo-entry.tmj')
    if r.returncode != 0:
        print('build_art_assets.py FAILED')
        return r.returncode

    man = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text(encoding='utf-8'))['assets']
    for cid in CHARS:
        for kind in ('portrait', 'chibi'):
            key = f'{cid}-{kind}'
            a = man.get(key)
            print(f'  {key}:', f"{a['width']}x{a['height']} anchor={a['anchor']}" if a else 'MISSING')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
