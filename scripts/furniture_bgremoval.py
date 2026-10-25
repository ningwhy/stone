#!/usr/bin/env python3
"""Batch background-removal for the new furniture with Qwen Image 2.1.

The server's SAM/SDMatte route is down (BiRefNet fails to load under the
installed transformers), and Qwen's semantic background removal has no depth
cut: objects standing on a table survive whole. Outputs land as
art/matted/<stem>-sam.png, the name the art build reads.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art/matted'
STUDIO = Path.home() / '.workbuddy/skills/local-image-studio/scripts/image_studio.py'
PYTHON = '/Users/bot/.workbuddy/binaries/python/envs/default/bin/python'

ITEMS = [
    ('altar-table', 10224102),
    ('writing-desk', 10224103),
    ('official-chair', 10224104),
    ('round-stool', 10224105),
    ('square-stool', 10224106),
    ('cabinet', 10224107),
    ('brazier', 10224108),
    ('vase-stand', 10224109),
]


def main() -> int:
    only = sys.argv[1:] or None
    for key, seed in ITEMS:
        if only and key not in only:
            continue
        name = f'{key}_s{seed}'
        src = ROOT / f'art/source/{name}-01.png'
        dest = OUT / f'{name}-sam.png'
        if not src.exists():
            print(f'skip {key}: source missing')
            continue
        if dest.exists():
            print(f'skip {key}: matte exists')
            continue
        print(f'=== removing background for {key}')
        cmd = [PYTHON, str(STUDIO), 'qwen21', '--variant', 'bg-removal',
               '--prompt', 'Remove the background, and output a PNG image',
               '--image', str(src), '--steps', '30', '--name', name,
               '--out', str(OUT), '--max-queue-depth', '1']
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-1500:])
            print(r.stderr[-1500:])
            return 1
        produced = OUT / f'{name}-01.png'
        if produced.exists():
            produced.rename(dest)
        print(f'    ok -> {dest.name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
