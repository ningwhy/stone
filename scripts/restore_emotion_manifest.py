#!/usr/bin/env python3
"""Re-register portrait emotion variants that lost their manifest entry.

The emotion variants are painted by scripts/build_emotions.py and registered
into public/assets/rongguo/manifest.json. A later full rebuild of the
calibrated assets rewrote that manifest from the calibration list alone, and
the entries that the calibration does not produce were dropped. The bitmaps
stayed on disk, but the runtime looked them up by manifest key, so every
emotion variant silently fell back to the neutral portrait.

This restores the entries from the bitmaps on disk: a variant shares the
geometry and the identity record of the portrait it was painted from, because
it was composited bottom-centred onto that portrait's canvas.

Usage: python3 scripts/restore_emotion_manifest.py [--check]
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print('Pillow is required', file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'public/assets/rongguo'
MANIFEST = ASSETS / 'manifest.json'

VARIANT = re.compile(r'^(?P<actor>.+)-portrait-(?P<emotion>joy|sad|surprise|angry)$')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true',
                        help='report what is missing without writing')
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    assets = manifest['assets']

    missing = []
    for path in sorted(ASSETS.glob('*-portrait-*.png')):
        key = path.stem
        if not VARIANT.match(key):
            continue
        if key in assets:
            continue
        missing.append(key)

    if not missing:
        print(f'manifest is complete: {len(assets)} assets, no orphaned variant')
        return

    for key in missing:
        match = VARIANT.match(key)
        actor = match.group('actor')
        base_key = f'{actor}-portrait'
        base = assets.get(base_key)
        if not base:
            print(f'  {key}: no base portrait {base_key} in manifest, skipped', file=sys.stderr)
            continue
        with Image.open(ASSETS / f'{key}.png') as image:
            width, height = image.size
        if (width, height) != (base['width'], base['height']):
            print(f'  {key}: canvas {width}x{height} differs from the base '
                  f'{base["width"]}x{base["height"]}, skipped', file=sys.stderr)
            continue
        assets[key] = {
            'image': f'/assets/rongguo/{key}.png',
            'width': base['width'],
            'height': base['height'],
            'anchor': base['anchor'],
            'source': base.get('source'),
            'identity': base.get('identity'),
        }
        print(f'  {key}: restored')

    if args.check:
        print(f'--check: {len(missing)} orphaned variant(s) would be restored')
        return

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
    print(f'manifest now holds {len(assets)} assets')


if __name__ == '__main__':
    main()
