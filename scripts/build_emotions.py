#!/usr/bin/env python3
"""Generate portrait emotion variants with the local ComfyUI (Qwen Image 2.1).

edit (expression rewrite) -> bg-removal (the edit pass paints over the alpha) ->
composite bottom-centred onto the base canvas -> register in the manifest.
Incremental: a pair is skipped when its final PNG already exists. Jobs run
sequentially: the skill forbids concurrent prompts on one GPU.

Usage: python3 scripts/build_emotions.py [actor ...] [--emotions joy,sad,...]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'public/assets/rongguo'
MANIFEST = ASSETS / 'manifest.json'
STUDIO = Path.home() / '.workbuddy/skills/local-image-studio/scripts/image_studio.py'
WORK = ROOT / 'art/emotions'

EMOTIONS = {
    'joy': '面露柔和的喜悦：眼角微微弯起，唇边含着浅笑，神情明快',
    'sad': '眉尖轻蹙，眼含泪光欲泣，神情哀愁低落',
    'surprise': '双眼睁大，唇微微张开，神情讶异',
    'angry': '眉头紧蹙，目光含恼，神情愠怒',
}
SUFFIX = '。保持人物的发型、发饰、服饰、身姿比例与画面构图完全不变，保持手绘淡彩水彩画风，画面干净无杂物；人物身后就是透明背景，绝不要添加光晕、光环、白色椭圆、云雾或任何背景装饰元素。'
BATCH1 = ['daiyu', 'baoyu', 'feng', 'grandmother']


def generate(variant: str, image: Path, name: str, prompt: str) -> Image.Image:
    for stale in WORK.glob(f'{name}*.png'):
        stale.unlink()
    args = ['--variant', variant, '--image', str(image), '--name', name, '--out', str(WORK)]
    if prompt:
        args += ['--prompt', prompt]
    result = subprocess.run([sys.executable, str(STUDIO), 'qwen21', *args],
                            capture_output=True, text=True)
    made = sorted(WORK.glob(f'{name}*.png'))
    if result.returncode != 0 or not made:
        raise RuntimeError(f'{name}: studio failed\n{result.stdout[-400:]}\n{result.stderr[-400:]}')
    print(f'  {name}: {made[0].name}', flush=True)
    return Image.open(made[0]).convert('RGBA')


def composite(base: Image.Image, cut: Image.Image) -> Image.Image:
    canvas = Image.new('RGBA', base.size, (0, 0, 0, 0))
    scaled = cut.copy()
    scaled.thumbnail(base.size, Image.LANCZOS)
    canvas.paste(scaled, ((base.width - scaled.width) // 2, base.height - scaled.height), scaled)
    return canvas


def opaque_ratio(image: Image.Image) -> float:
    hist = image.getchannel('A').histogram()
    return sum(hist[200:]) / sum(hist)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('actors', nargs='*', default=BATCH1)
    parser.add_argument('--emotions', default=','.join(EMOTIONS))
    args = parser.parse_args()
    wanted = args.emotions.split(',')
    unknown = [e for e in wanted if e not in EMOTIONS]
    if unknown:
        raise SystemExit(f'unknown emotions: {unknown}')

    manifest = json.loads(MANIFEST.read_text())
    todo = [(a, e) for a in args.actors for e in wanted]
    print(f'{len(todo)} pairs queued: {todo}', flush=True)
    done = 0
    for actor, emotion in todo:
        key = f'{actor}-portrait'
        base_entry = manifest['assets'].get(key)
        if not base_entry:
            print(f'  {key}: not in manifest, skipped', flush=True)
            continue
        out_key = f'{key}-{emotion}'
        out_path = ASSETS / f'{out_key}.png'
        if out_path.exists():
            print(f'  {out_key}: exists, skipped', flush=True)
            continue
        base = Image.open(ASSETS / f'{key}.png').convert('RGBA')
        raw_name = f'{actor}-{emotion}-raw'
        raw = generate('edit', ASSETS / f'{key}.png', raw_name,
                       f'让<image1>中的古装人物{EMOTIONS[emotion]}{SUFFIX}')
        cut = generate('bg-removal', WORK / f'{raw_name}-01.png', f'{actor}-{emotion}-cut', '')
        if opaque_ratio(cut) < 0.05:
            raise SystemExit(f'  {out_key}: bg-removal returned an empty mask, aborting '
                             f'(raw kept at {WORK / f"{raw_name}-01.png"} for a manual retry)')
        final = composite(base, cut)
        final.save(out_path)
        manifest['assets'][out_key] = {
            'image': f'/assets/rongguo/{out_key}.png',
            'width': base.width,
            'height': base.height,
            'anchor': base_entry['anchor'],
            'source': str(WORK / f'{raw_name}-01.png'),
            'identity': base_entry.get('identity'),
        }
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
        done += 1
        print(f'  {out_key}: registered ({done}/{len(todo)})', flush=True)
    print(f'batch complete: {done} new variants', flush=True)


if __name__ == '__main__':
    main()
