#!/usr/bin/env python3
"""Build a contact sheet of every runtime asset for the manual art review.

The sheet renders each asset on a dark backdrop (so stray white or black halos
show up), marks the gameplay anchor, and reports the measured geometry so the
reviewer can check transparency, outline, size and foot anchoring in one pass.
"""
import json
import os
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'public', 'assets', 'rongguo', 'manifest.json')
OUT_DIR = os.path.join(ROOT, 'artifacts', 'asset-audit')
COLS = 8
CELL = 210
PAD = 14
LABEL_H = 42


def load_font(size):
    for path in ('/System/Library/Fonts/Helvetica.ttc',
                 '/System/Library/Fonts/Supplemental/Arial.ttf',
                 '/Library/Fonts/Arial.ttf'):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def build_sheet(keys, manifest, out_path, title):
    assets = manifest['assets']
    font = load_font(13)
    font_title = load_font(20)
    rows = (len(keys) + COLS - 1) // COLS
    head = 44
    width = COLS * CELL
    height = head + rows * (CELL + LABEL_H)
    sheet = Image.new('RGB', (width, height), (26, 30, 34))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), f'{title}  ({len(keys)} assets)', font=font_title, fill=(232, 226, 210))

    for i, key in enumerate(keys):
        entry = assets[key]
        col, row = i % COLS, i // COLS
        x0 = col * CELL
        y0 = head + row * (CELL + LABEL_H)
        # Checkerboard so transparency problems are visible, not guessed.
        box = Image.new('RGB', (CELL - PAD * 2, CELL - PAD * 2), (44, 50, 56))
        bd = ImageDraw.Draw(box)
        step = 16
        for yy in range(0, box.height, step):
            for xx in range(0, box.width, step):
                if (xx // step + yy // step) % 2 == 0:
                    bd.rectangle([xx, yy, xx + step - 1, yy + step - 1], fill=(58, 66, 72))
        path = os.path.join(ROOT, 'public', entry['image'].lstrip('/'))
        if not os.path.exists(path):
            path = path.replace('.png', '.webp')
        try:
            im = Image.open(path).convert('RGBA')
        except OSError as exc:
            draw.text((x0 + PAD, y0 + PAD), f'LOAD FAIL\n{exc}', font=font, fill=(240, 120, 120))
            continue
        scale = min((box.width) / im.width, (box.height) / im.height)
        w, h = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        # Composite the alpha onto the checkerboard instead of pasting RGBA onto
        # RGB: pasting RGBA with a mask argument drops the alpha channel and the
        # asset lands in the wrong corner of the cell.
        resized = im.resize((w, h), Image.LANCZOS)
        backdrop = box.crop(((box.width - w) // 2, (box.height - h) // 2,
                             (box.width - w) // 2 + w, (box.height - h) // 2 + h))
        box.paste(Image.alpha_composite(backdrop.convert('RGBA'), resized).convert('RGB'),
                  ((box.width - w) // 2, (box.height - h) // 2))
        # The gameplay anchor, scaled with the asset.
        ax = (box.width - w) // 2 + entry['anchor'][0] * scale
        ay = (box.height - h) // 2 + entry['anchor'][1] * scale
        bd = ImageDraw.Draw(box)
        bd.ellipse([ax - 5, ay - 5, ax + 5, ay + 5], outline=(255, 96, 96), width=2)
        bd.line([ax - 9, ay, ax + 9, ay], fill=(255, 96, 96))
        bd.line([ax, ay - 9, ax, ay + 9], fill=(255, 96, 96))
        sheet.paste(box, (x0 + PAD, y0 + PAD))
        label = key
        has_id = 'yes' if entry.get('identity') else 'no'
        draw.text((x0 + PAD, y0 + CELL - PAD + 2), label, font=font, fill=(226, 220, 200))
        draw.text((x0 + PAD, y0 + CELL - PAD + 18),
                  f"{entry['width']}x{entry['height']} id:{has_id}", font=font, fill=(150, 158, 166))
    sheet.save(out_path)
    return out_path


def main():
    with open(MANIFEST, encoding='utf-8') as fh:
        manifest = json.load(fh)
    keys = sorted(manifest['assets'])
    os.makedirs(OUT_DIR, exist_ok=True)
    chunks = [keys[i:i + 32] for i in range(0, len(keys), 32)]
    written = []
    for i, chunk in enumerate(chunks):
        out = os.path.join(OUT_DIR, f'sheet-{i + 1}.png')
        written.append(build_sheet(chunk, manifest, out, f'Runtime asset review sheet {i + 1}/{len(chunks)}'))
    for path in written:
        print(path)
    print(f'{len(keys)} assets on {len(written)} sheets')


if __name__ == '__main__':
    sys.exit(main())
