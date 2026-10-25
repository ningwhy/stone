#!/usr/bin/env python3
"""Batch-generate the new indoor furniture sources on the local ComfyUI server.

Same style template and 1024x1024 canvas as the shipped art/source furniture, so
the calibrated pipeline (SAM matte -> build_art_assets.py) treats them like any
other asset. One process, strictly sequential: concurrent jobs on the single
ComfyUI host crash the server.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art/source'
STUDIO = Path.home() / '.workbuddy/skills/local-image-studio/scripts/image_studio.py'
PYTHON = '/Users/bot/.workbuddy/binaries/python/envs/default/bin/python'

STYLE = ('精致国风手绘游戏美术，工笔线描结合温润水彩与不透明水粉，细腻纸张纹理，清晰精细的手绘轮廓与'
         '丰富材质细节，低饱和青灰、松绿、暖米白、赭石与暗朱红，安静雅致的清代贵族宅院气质。'
         '柔和日光从画面左上方照射。原创设计，画面中不要出现任何文字、字母、数字、水印、签名、标语或标注。')
ISO = '二比一菱形正交等距俯视，无透视消失点，完整居中，四周留白。纯白背景，无地面平台，无周围建筑，无文字牌匾，无签名。'

# (id, seed, subject). Subjects stay on the dark-wood / blue-and-white palette
# the shipped furniture uses, and every piece is a complete standalone object.
FURNITURE = [
    ('square-table', 10224101, '独立游戏素材，清代八仙桌一张，正方形桌面，四腿与横枨粗壮坚实，桌面置青花茶壶一只、茶盅两只，无人物无椅子'),
    ('altar-table', 10224102, '独立游戏素材，清代正房条案一张，长条形厚案面，两头翘头，案上置青花瓷瓶一只、小香炉一座，无人物'),
    ('writing-desk', 10224103, '独立游戏素材，清代书房书案一张，宽大案面铺宣纸，案上置笔筒、毛笔、砚台与印章盒，无人物'),
    ('official-chair', 10224104, '独立游戏素材，清代太师椅一把，宽大靠背与扶手，座面为暗朱红锦缎垫，木质坚实，无人物'),
    ('round-stool', 10224105, '独立游戏素材，清代圆凳一只，圆形座面，四条凳腿向外撇开，木质坚实，无人物'),
    ('square-stool', 10224106, '独立游戏素材，清代方凳一只，正方形座面，四条直腿与横枨，木质坚实，无人物'),
    ('cabinet', 10224107, '独立游戏素材，清代顶箱柜一只，对开柜门带铜饰件与门闩，柜身高大庄严，无人物'),
    ('brazier', 10224108, '独立游戏素材，清代铜火盆一只，宽厚盆沿，盆内盛红热炭火，下承三足支架，无人物'),
    ('vase-stand', 10224109, '独立游戏素材，清代花架一只，两层木板架，置青花大瓷瓶一只、插时令花卉，无人物'),
]


def main() -> int:
    only = sys.argv[1:] or None
    for key, seed, subject in FURNITURE:
        if only and key not in only:
            continue
        name = f'{key}_s{seed}'
        dest = OUT / f'{name}-01.png'
        if dest.exists():
            print(f'skip {key}: {dest.name} exists')
            continue
        prompt = f'{STYLE}\n{subject}。{ISO}'
        print(f'=== generating {key} (seed {seed})')
        cmd = [PYTHON, str(STUDIO), 'generate', '--model', 'zimage', '--preset', '1k-1k',
               '--prompt', prompt, '--name', name, '--out', str(OUT), '--seed', str(seed),
               '--max-queue-depth', '1']
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:])
            print(r.stderr[-2000:])
            return 1
        print(f'    ok -> {dest.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
