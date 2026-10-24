#!/usr/bin/env python3
"""Approximate the Phaser floor + art layout of a TMJ map so interior/exterior
behaviour can be reviewed without booting the dev server.

Mirrors src/MapScene.ts create()/artwork() closely enough for layout checks:
  floor colour per zone, isometric diamond tiles, art anchored bottom-centre.
"""
import json, sys, os, math
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'public/assets/rongguo')
MANIFEST = json.load(open(os.path.join(ASSETS, 'manifest.json')))['assets']


def load_image(asset):
    entry = MANIFEST[asset]
    rel = entry['image'].lstrip('/')
    for ext in ('.png', '.webp'):
        path = os.path.join(ROOT, 'public', rel.replace('.png', ext))
        if os.path.exists(path):
            return Image.open(path).convert('RGBA'), entry['width'], entry['height'], entry['anchor']
    raise FileNotFoundError(asset + ' -> ' + path)


def project(col, row, tw=128, th=64):
    return (col - row) * tw / 2, (col + row + 1) * th / 2


def diamond(d, cx, cy, w, h, fill, outline=None):
    d.polygon([(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)], fill=fill, outline=outline)


def render(map_id, hide=(), scale=0.55, out=None):
    path = os.path.join(ROOT, 'maps', map_id + '.tmj')
    d = json.load(open(path))
    tw, th = d['tilewidth'], d['tileheight']
    W, H = d['width'], d['height']

    zones = {}
    for l in d['layers']:
        if l['name'] == 'PlanZones':
            for o in l['objects']:
                zid = o['name'].split(' ')[0]
                zones[zid] = dict(col=o['x'] / th, row=o['y'] / th, w=o['width'] / th, h=o['height'] / th)

    # Bounding box of the whole iso grid plus art.
    pts = [project(c, r, tw, th) for c in (0, W) for r in (0, H)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    arts = []
    for l in d['layers']:
        if l['name'] == 'Art':
            for o in l['objects']:
                props = {p['name']: p['value'] for p in o.get('properties', [])}
                arts.append((o['name'], props.get('asset'), o['x'], o['y'], o['width'], o['height'],
                             props.get('visibility', 'always')))
    for _, asset, x, y, w, h, _ in arts:
        sx, sy = x - y, (x + y) / 2
        xs += [sx - w / 2, sx + w / 2]; ys += [sy - h, sy]

    pad = 60
    minx, maxx, miny, maxy = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    img = Image.new('RGBA', (int((maxx - minx) * scale), int((maxy - miny) * scale)), (238, 232, 215, 255))
    dr = ImageDraw.Draw(img)

    def T(sx, sy):
        return ((sx - minx) * scale, (sy - miny) * scale)

    def iso(c, r, w=1, h=1, fill=None, outline=None, inset=0.0):
        c0, r0 = c + inset, r + inset
        cx, cy = project(c0 + w / 2 - 0.5, r0 + h / 2 - 0.5, tw, th)
        diamond(dr, *T(cx, cy), w * tw * scale, h * th * scale, fill, outline)

    # Base ground
    iso(0, 0, W, H, fill=(238, 232, 215))

    for zid, z in zones.items():
        indoor = zid == 'F'
        iso(z['col'] - 0.18, z['row'] - 0.18, z['w'] + 0.36, z['h'] + 0.36, fill=(180, 172, 146))
        iso(z['col'], z['row'], z['w'], z['h'], fill=(213, 197, 165) if indoor else (229, 222, 203))
        for c in range(int(z['col']), int(z['col'] + z['w'])):
            for r in range(int(z['row']), int(z['row'] + z['h'])):
                iso(c + 0.025, r + 0.025, 0.95, 0.95,
                    fill=(223, 208, 179) if indoor else (222, 216, 198))

    for name, asset, x, y, w, h, vis in arts:
        if vis == 'exterior' and name in hide:
            continue
        im, aw, ah, anchor = load_image(asset)
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
        sx, sy = T(x - y, (x + y) / 2)
        px = sx - im.width / 2
        py = sy - im.height
        img.alpha_composite(im, (int(px), int(py)))

    if out:
        img.convert('RGB').save(out, quality=92)
    return img


if __name__ == '__main__':
    maps = sys.argv[1].split(',') if len(sys.argv) > 1 else ['entry']
    hide = set(sys.argv[2].split(',')) if len(sys.argv) > 2 and sys.argv[2] != '-' else set()
    outdir = os.path.join(ROOT, 'artifacts/map-previews')
    os.makedirs(outdir, exist_ok=True)
    for m in maps:
        img = render(m, hide=hide)
        path = os.path.join(outdir, f'{m}{"-hidden" if hide else ""}.png')
        img.convert('RGB').save(path, quality=92)
        print(path, img.size)
