#!/usr/bin/env python3
"""切开宣纸底，只留下画上去的东西。

为什么不用 SAM：这批素材的画在**宣纸底**上而不是纯白底，主体又常常是一群人
叠在一起。GroundingDINO + SAM 是按文本找实例的，subject 写 "people" 只抠出
轿夫、漏掉轿身；写 "people, sedan chair" 会把几个人分别成不同实例，合成后
人身上出现空洞（棋盘底从躯干透出来）。SDMatte 那一路更糟，连背景建筑都留。

宣纸底是均匀的，所以按底色键控反而更可靠：离底色足够远的像素留下、够近的
丢掉，中间线性过渡。三个细节决定了它能不能直接用：

1. **底色要实测**，不能假设纯白。取四边各 20px 的中位色，纸纹与暖色调都在里面。
2. **只留大块连通域**。纸纹自身的起伏会超过阈值，散落整幅画面；按面积过滤掉
   这些碎点，主体的边缘不受影响。
3. **贴边的连通域一律丢弃**。模型经常在画面角落补一段墙或檐，那块一定连着
   画布边缘；真实主体四周留白、碰不到边。这条规则比硬编码矩形干净——不用
   为每张图量坐标，也不会切到人。

产出 `<out>/<stem>-paper-key.png`，alpha 已压平到实体为主，供 build_art_assets.py
按 calibration 的 matteKind 取用。

用法：
    python3 scripts/matte_paper_key.py --only sedan-chair
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULTS = {
    'threshold': 36,     # 离底色多远算内容（最大通道差）
    'minArea': 2000,     # 小于这个面积的连通域当纸纹丢掉
    'softLow': 14,       # 低于此差值 → 全透明
    'softHigh': 40,      # 高于此差值 → 全不透明
    'edgeBand': 20,      # 取底色用的边缘带宽
}


def paper_colour(a: np.ndarray, band: int) -> np.ndarray:
    edge = np.concatenate([
        a[:band].reshape(-1, 3), a[-band:].reshape(-1, 3),
        a[:, :band].reshape(-1, 3), a[:, -band:].reshape(-1, 3),
    ])
    return np.median(edge, axis=0)


def key_alpha(rgb: np.ndarray, cfg: dict) -> tuple[np.ndarray, list[dict]]:
    """Return a flat alpha channel and a record of what the border rule removed."""
    paper = paper_colour(rgb, cfg['edgeBand'])
    dist = np.abs(rgb - paper).max(axis=2)

    seed = dist > cfg['threshold']
    labels, _ = ndimage.label(seed)
    height, width = seed.shape
    keep = np.zeros_like(seed)
    dropped: list[dict] = []
    for index, box in enumerate(ndimage.find_objects(labels), start=1):
        if box is None:
            continue
        mask = labels[box] == index
        area = int(mask.sum())
        if area < cfg['minArea']:
            continue
        y0, x0 = box[0].start, box[1].start
        touches = y0 == 0 or x0 == 0 or box[0].stop >= height or box[1].stop >= width
        if touches:
            dropped.append({'area': area, 'box': [x0, y0, box[1].stop, box[0].stop]})
            continue
        keep[box] |= mask

    keep = ndimage.binary_closing(keep, iterations=2)
    keep = ndimage.binary_fill_holes(keep)

    soft = np.clip((dist - cfg['softLow']) / (cfg['softHigh'] - cfg['softLow']), 0, 1)
    # 保住主体内部：边缘用 soft 过渡，内部按 0.35 起步，永远不会掉成全透明
    alpha = np.where(keep, 0.35 + 0.65 * soft, 0.0)
    return (np.clip(alpha, 0, 1) * 255).astype(np.uint8), dropped


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', nargs='+', help='calibration 里的资产 id')
    args = parser.parse_args()

    calibration = json.loads((ROOT / 'art/calibration.json').read_text())
    out = ROOT / 'art/matted'
    out.mkdir(exist_ok=True)
    targets = [a for a in calibration['assets'] if a.get('matteKind') == 'paper-key']
    if args.only:
        targets = [a for a in targets if a['id'] in args.only]
    if not targets:
        print('no calibration entry asks for matteKind=paper-key')
        return 0

    for item in targets:
        key = item['id']
        stem = f"{item.get('sourceId', key)}_s{item['seed']}"
        source = ROOT / f'art/source/{stem}-01.png'
        if not source.is_file():
            print(f'{key}: missing {source.relative_to(ROOT)}')
            continue
        cfg = {**DEFAULTS, **item.get('paperKey', {})}
        rgb = np.asarray(Image.open(source).convert('RGB')).astype(np.float32)
        alpha, dropped = key_alpha(rgb, cfg)

        image = Image.open(source).convert('RGBA')
        image.putalpha(Image.fromarray(alpha))
        target = out / f'{stem}-paper-key.png'
        image.save(target)

        visible = alpha > 0
        ys, xs = np.where(visible)
        solid = float((alpha[visible] >= 250).mean()) if visible.any() else 0.0
        record = {
            'source': str(source.relative_to(ROOT)),
            'config': cfg,
            'droppedBorderComponents': dropped,
            'bbox': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            'solidAlpha250Ratio': round(solid, 5),
        }
        (out / f'{stem}-paper-key.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        print(f'{key}: {target.relative_to(ROOT)} bbox={record["bbox"]} '
              f'solid={solid:.3f} dropped={len(dropped)} border component(s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
