#!/usr/bin/env python3
"""Restore the tableware the SAM matte sliced off the two table assets.

The person-only SAM mask treats a tabletop as a depth surface and cuts every
object standing on it at the surface, so the tea set and the dinner bowls ship
as flat stubs. calibration.json's restorePolygons pastes the reviewed source
back through a hand-traced silhouette, which is the same mechanism already used
for held objects on the character sprites. Polygons are in the 1024x1024 source
space; each follows the item outline with a small margin and stays on the dark
tabletop (identical pixels in the matte) except where the item itself rises
above the table's far edge.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'art/calibration.json'


def bowl(cx: float, cy_rim: float, rx: float, ry: float, base: float) -> list:
    """One open bowl: rim ellipse plus the body tucked under it."""
    return [
        [cx - rx * .72, cy_rim - ry * .72], [cx, cy_rim - ry],
        [cx + rx * .72, cy_rim - ry * .72], [cx + rx, cy_rim],
        [cx + rx * .98, cy_rim + ry * .8], [cx + rx * .82, base - 9],
        [cx + rx * .55, base], [cx, base + 3],
        [cx - rx * .55, base], [cx - rx * .82, base - 9],
        [cx - rx * .98, cy_rim + ry * .8], [cx - rx, cy_rim],
    ]


# art/source/tea-table_s10222107-01.png — covered bowl, open bowl, small cup.
TEA = [
    # 盖碗: knob, lid dome, then the body widening onto the tabletop.
    [[558, 527], [580, 527], [585, 533], [596, 538], [606, 544], [611, 556],
     [612, 572], [611, 588], [606, 596], [597, 601], [583, 603], [568, 601],
     [556, 596], [549, 588], [545, 572], [545, 556], [549, 544], [552, 538]],
    # 茶盅 with its saucer.
    bowl(522, 567, 29, 7, 641),
    # 小茶盅.
    bowl(602, 621, 20, 6, 649),
]

# art/source/dining-table_s10222104-01.png — centre vase plus six bowls.
DINING = [
    # 玉壶春瓶: flared mouth, neck, wide belly, standing at the table centre.
    [[521, 477], [547, 478], [550, 485], [549, 495], [554, 505], [560, 518],
     [563, 533], [562, 548], [557, 560], [549, 568], [538, 572], [524, 570],
     [513, 563], [507, 550], [505, 535], [508, 520], [514, 508], [518, 498],
     [519, 487]],
    bowl(449, 496, 27, 6, 553),   # back left
    bowl(572, 506, 27, 6, 563),   # back right
    bowl(385, 563, 26, 6, 618),   # middle left
    bowl(630, 563, 26, 6, 618),   # middle right
    bowl(445, 626, 27, 6, 683),   # front left
    bowl(595, 626, 27, 6, 683),   # front right
]

RESTORE = {'tea-table': TEA, 'dining-table': DINING}

config = json.loads(CONFIG.read_text())
for item in config['assets']:
    if item['id'] in RESTORE:
        item['restorePolygons'] = [[[round(v, 1) for v in p] for p in poly] for poly in RESTORE[item['id']]]
        print(f"{item['id']}: {len(RESTORE[item['id']])} restore polygons")
CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
