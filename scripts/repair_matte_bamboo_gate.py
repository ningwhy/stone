#!/usr/bin/env python3
"""Rebuild a matte whose alpha punched holes into pale painted interiors.

The SDMatte pass on bamboo-gate treated the cream plaster walls (and the pale
greenery seen through the open doorway) as background and ate irregular holes
into them. The source painting separates cleanly instead: the paper background
is near-pure white and CONNECTED TO THE IMAGE BORDER, while the walls sit far
from it (min channel ~220 vs >=248). So the safe rule is not "light pixels are
background" but "light pixels reachable from the border are background" — a
border flood fill over near-white. Enclosed light areas (highlights between
roof tiles, the doorway's own white) stay opaque, and every eaten wall returns.

Usage: repair_matte_bamboo_gate.py  (paths below are the bamboo-gate pair)
"""
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    ("art/source/bamboo-gate_s10222102-01.png", "art/matted/bamboo-gate_s10222102-sam.png"),
]
THRESHOLD = 244  # walls ~220, paper >=248: anything this light reachable from the border is paper
# The gate is walked THROUGH, so its open doorway must not ship as an opaque white
# sheet. The opening's white is enclosed by the frame, the door leaf and the step,
# so a flood seeded inside it removes exactly that patch (and leaves the pale
# greenery painted inside the opening, which sits below the threshold).
DOORWAY_SEEDS = [(528, 612), (548, 648), (508, 596)]


def seeded_flood(light: np.ndarray, seeds) -> np.ndarray:
    visited = np.zeros_like(light, dtype=bool)
    queue = deque()
    for x, y in seeds:
        if light[y, x] and not visited[y, x]:
            visited[y, x] = True
            queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < light.shape[0] and 0 <= nx < light.shape[1] and light[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True
                queue.append((ny, nx))
    return visited


def border_flood(light: np.ndarray) -> np.ndarray:
    """Light pixels connected to any image edge, via BFS."""
    h, w = light.shape
    visited = np.zeros_like(light, dtype=bool)
    queue = deque()
    for x in range(w):
        for y in (0, h - 1):
            if light[y, x] and not visited[y, x]:
                visited[y, x] = True
                queue.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if light[y, x] and not visited[y, x]:
                visited[y, x] = True
                queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and light[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True
                queue.append((ny, nx))
    return visited


for source_rel, matte_rel in PAIRS:
    source = np.asarray(Image.open(ROOT / source_rel).convert("RGB")).astype(int)
    minc = source.min(axis=2)
    light = minc >= THRESHOLD
    bg = border_flood(light) | seeded_flood(light, DOORWAY_SEEDS)
    before = np.asarray(Image.open(ROOT / matte_rel).convert("RGBA"))
    removed_before = int((before[:, :, 3] == 0).sum())
    alpha = np.where(bg, 0, 255).astype("uint8")
    out = np.dstack([source.astype("uint8"), alpha])
    Image.fromarray(out, "RGBA").save(ROOT / matte_rel)
    report = {
        "source": source_rel,
        "matte": matte_rel,
        "threshold": THRESHOLD,
        "transparent_before": removed_before,
        "transparent_after": int(bg.sum()),
        "restored_pixels": int(bg.sum()) - removed_before,
    }
    print(json.dumps(report))
