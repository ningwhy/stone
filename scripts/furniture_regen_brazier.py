#!/usr/bin/env python3
"""Second attempt for the brazier source: fresh seed, product-photo phrasing.

The first two attempts (seeds 10224108, both with and without the explicit
no-room clause) kept generating a full room around the hearth. This run keeps
the same style template but phrases the subject as an isolated game prop on a
seamless white void and moves to an unused seed to escape the room attractor.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art/source'
MATTED = ROOT / 'art/matted'
STUDIO = Path.home() / '.workbuddy/skills/local-image-studio/scripts/image_studio.py'
PYTHON = '/Users/bot/.workbuddy/binaries/python/envs/default/bin/python'

KEY, SEED = 'brazier', 10224118
NAME = f'{KEY}_s{SEED}'

STYLE = ('精致国风手绘游戏美术，工笔线描结合温润水彩与不透明水粉，细腻纸张纹理，清晰精细的手绘轮廓与'
         '丰富材质细节，低饱和青灰、松绿、暖米白、赭石与暗朱红，安静雅致的清代贵族宅院气质。'
         '柔和日光从画面左上方照射。原创设计，画面中不要出现任何文字、字母、数字、水印、签名、标语或标注。')
SUBJECT = ('独立游戏道具，一只清代青铜三足火盆，圆形宽厚盆沿，沿上铸双耳，盆内盛红热炭火与微微火焰，'
           '三足支架，无人物。画面中只有这一件器物，如商品摄影般孤立呈现，'
           '绝对不要出现房间、墙壁、门窗、窗棂、屋顶、地板、地毯、台阶、平台、庭院、虚空或任何建筑环境，'
           '四周围只有纯白背景。')
ISO = '二比一菱形正交等距俯视，无透视消失点，完整居中，四周留白。纯白背景，无地面平台，无周围建筑，无文字牌匾，无签名。'


def run(cmd: list[str]) -> int:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
    return r.returncode


def main() -> int:
    dest = OUT / f'{NAME}-01.png'
    print(f'=== generating {KEY} (seed {SEED})')
    if run([PYTHON, str(STUDIO), 'generate', '--model', 'zimage', '--preset', '1k-1k',
            '--prompt', f'{STYLE}\n{SUBJECT}\n{ISO}', '--name', NAME, '--out', str(OUT),
            '--seed', str(SEED), '--max-queue-depth', '1']) != 0:
        return 1
    print(f'    source ok -> {dest.name}')
    matte = MATTED / f'{NAME}-sam.png'
    print(f'=== removing background for {KEY}')
    if run([PYTHON, str(STUDIO), 'qwen21', '--variant', 'bg-removal',
            '--prompt', 'Remove the background, and output a PNG image',
            '--image', str(dest), '--steps', '30', '--name', NAME,
            '--out', str(MATTED), '--max-queue-depth', '1']) != 0:
        return 1
    produced = MATTED / f'{NAME}-01.png'
    if produced.exists():
        produced.rename(matte)
    print(f'    matte ok -> {matte.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
