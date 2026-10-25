#!/usr/bin/env python3
"""Regenerate the two furniture sources that drifted into full-room scenes.

altar-table and brazier were generated with "正房"/hearth subjects and the model
added a whole room (walls, windows, roof, floor), which the semantic matte then
kept as the subject. Same style template, same seeds, but the subject now states
the no-room constraint explicitly, so the shipped asset is the furniture alone.

Run:  python3 scripts/furniture_regen.py
Then: python3 scripts/furniture_bgremoval.py altar-table brazier  (or let this
script chain it). Strictly sequential: one ComfyUI host, one job at a time.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art/source'
MATTED = ROOT / 'art/matted'
STUDIO = Path.home() / '.workbuddy/skills/local-image-studio/scripts/image_studio.py'
PYTHON = '/Users/bot/.workbuddy/binaries/python/envs/default/bin/python'

STYLE = ('精致国风手绘游戏美术，工笔线描结合温润水彩与不透明水粉，细腻纸张纹理，清晰精细的手绘轮廓与'
         '丰富材质细节，低饱和青灰、松绿、暖米白、赭石与暗朱红，安静雅致的清代贵族宅院气质。'
         '柔和日光从画面左上方照射。原创设计，画面中不要出现任何文字、字母、数字、水印、签名、标语或标注。')
ISO = ('二比一菱形正交等距俯视，无透视消失点，完整居中，四周留白。纯白背景，'
       '无地面平台，无周围建筑，无文字牌匾，无签名。')
NOROOM = ('绝对不要出现房间、墙壁、门窗、窗棂、屋顶、地板、地毯、台阶、平台、庭院或任何建筑环境，'
          '主体家具孤立放置，四周围只有纯白背景。')

# (id, seed, subject)
REGEN = [
    ('altar-table', 10224102,
     '独立游戏素材，清代条案一张，长条形厚案面，两头翘头，四条案腿与横枨，'
     '案面上同一平面置青花瓷瓶一只与小香炉一座，两件器物都摆放在案面上，无人物'),
    ('brazier', 10224108,
     '独立游戏素材，清代铜火盆一只，宽厚盆沿带双耳，盆内盛红热炭火，下承三足支架，无人物'),
]


def run(cmd: list[str]) -> int:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
    return r.returncode


def main() -> int:
    for key, seed, subject in REGEN:
        name = f'{key}_s{seed}'
        dest = OUT / f'{name}-01.png'
        prompt = f'{STYLE}\n{subject}。{ISO}\n{NOROOM}'
        print(f'=== generating {key} (seed {seed})')
        if run([PYTHON, str(STUDIO), 'generate', '--model', 'zimage', '--preset', '1k-1k',
                '--prompt', prompt, '--name', name, '--out', str(OUT), '--seed', str(seed),
                '--max-queue-depth', '1']) != 0:
            return 1
        print(f'    source ok -> {dest.name}')

        matte = MATTED / f'{name}-sam.png'
        print(f'=== removing background for {key}')
        if run([PYTHON, str(STUDIO), 'qwen21', '--variant', 'bg-removal',
                '--prompt', 'Remove the background, and output a PNG image',
                '--image', str(dest), '--steps', '30', '--name', name,
                '--out', str(MATTED), '--max-queue-depth', '1']) != 0:
            return 1
        produced = MATTED / f'{name}-01.png'
        if produced.exists():
            produced.rename(matte)
        print(f'    matte ok -> {matte.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
