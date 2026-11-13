#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cut a prop out of a plain white backdrop, without the server.

The SAM pass on `bamboo-cluster` kept the painting's beige paper ground: the
matte shipped the whole pale square, and the bamboo read on screen as a blank
cream slab — the asset had been broken since it was first committed (2026-10-29)
and thirteen maps have been placing that slab ever since.

SAM is the wrong tool for a prop on a flat backdrop, and it is also
unavailable here: the server's BiRefNet node dies with
`'Config' object has no attribute 'is_encoder_decoder'`. But a prop painted on
pure white needs no model at all. The paper/plant separation is decided by two
measurements taken from the source:

  * `min channel` — the outside white is >= 250 on every channel, while even
    the palest leaf wash sits far below it;
  * `saturation` — the plant is pigmented (leaves ~0.13–0.21), the ground is
    not.

The rule is the same one `repair_matte_bamboo_gate.py` uses, generalised:
"light pixels *reachable from the image border* are background". A flood fill
over near-white from every edge removes the flat backdrop while leaving any
enclosed light area (a highlight between roof tiles, a doorway's own white)
opaque. When a prop was painted with a translucent halo, the halo is kept: a
hard threshold would chew the leaf edges, so the alpha is feathered by how far
each pixel is from the backdrop's own colour.

Usage:
  cutout_white_backdrop.py SOURCE [-o OUT] [--threshold 244] [--pad 0]
"""
import argparse
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def border_flood(mask: np.ndarray) -> np.ndarray:
    """Every True pixel reachable from any image edge, via BFS."""
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    queue = deque()
    for x in range(w):
        for y in (0, h - 1):
            if mask[y, x] and not visited[y, x]:
                visited[y, x] = True
                queue.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if mask[y, x] and not visited[y, x]:
                visited[y, x] = True
                queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True
                queue.append((ny, nx))
    return visited


def cutout(source: Path, threshold: int = 244):
    """Return (rgba array, report)."""
    src = np.asarray(Image.open(source).convert("RGB")).astype(int)
    minc = src.min(axis=2)
    mx = src.max(axis=2)
    sat = np.where(mx > 0, (mx - minc) / np.maximum(mx, 1), 0.0)

    light = minc >= threshold
    backdrop = border_flood(light)
    # A pixel is background when it is part of the flat backdrop *or* when it is
    # flat white with no pigment at all (the outer corners of a repainted prop).
    flat_white = (minc >= 250) & (sat < 0.02)
    bg = backdrop | flat_white

    # Feather the edge: pixels that are near-white but not part of the flat
    # backdrop keep a partial alpha, so a leaf that fades into the white does
    # not end in a cut-off stump.
    alpha = np.where(bg, 0, 255).astype("uint8")
    near = (~bg) & (minc >= threshold - 18) & (sat < 0.10)
    alpha[near] = 120

    out = np.dstack([src.astype("uint8"), alpha])
    report = {
        "source": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
        "threshold": threshold,
        "size": list(src.shape[:2]),
        "transparent_px": int((alpha == 0).sum()),
        "opaque_px": int((alpha == 255).sum()),
        "feathered_px": int((alpha == 120).sum()),
    }
    return out, report


def trim(rgba: np.ndarray, pad: int = 0):
    """Cut the transparent margin away, so the asset's own size is its content."""
    alpha = rgba[:, :, 3]
    ys, xs = np.where(alpha > 0)
    if not len(ys):
        return rgba
    y0, y1 = max(0, ys.min() - pad), min(rgba.shape[0], ys.max() + 1 + pad)
    x0, x1 = max(0, xs.min() - pad), min(rgba.shape[1], xs.max() + 1 + pad)
    return rgba[y0:y1, x0:x1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("-o", "--out", type=Path, required=True)
    parser.add_argument("--threshold", type=int, default=244)
    parser.add_argument("--pad", type=int, default=0)
    parser.add_argument("--no-trim", action="store_true")
    args = parser.parse_args()

    rgba, report = cutout(args.source, args.threshold)
    if not args.no_trim:
        rgba = trim(rgba, args.pad)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(args.out)
    report["out"] = str(args.out.relative_to(ROOT)) if args.out.is_relative_to(ROOT) else str(args.out)
    report["out_size"] = [rgba.shape[1], rgba.shape[0]]
    print(json.dumps(report, ensure_ascii=False))
