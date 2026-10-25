#!/usr/bin/env python3
"""Place the new indoor furniture into the interior maps, and swap the repeated
tea-table for a varied table where the scene calls for one.

Placement contract (identical to build_art_assets.py / src/art.ts artGround):
  groundx=(col-row)*64; groundy=(col+row+1)*32
  bx=groundx+(W/2-ax)*s; by=groundy+(H-ay)*s
  tiled x=by+bx/2; tiled y=by-bx/2; width=W*s; height=H*s
with W/H/anchor from public/assets/rongguo/manifest.json. ArtFootprints stay on
the 64x64 tile (x=col*64, y=row*64) as every shipped interior already does.

Seats: a chair/stool is placed on the tile whose (col+row) is not larger than the
actor's, so it draws BEHIND the person and never covers them.

Idempotent: an object already sitting on the same ground tile with the same
asset is left untouched. Run twice -> no diff.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / 'maps'
UNIT = 64
MANIFEST = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())['assets']
GIDS = {t['properties'][0]['value']: t['id'] + 1
        for t in json.loads((ROOT / 'maps/rongguo-art.tsj').read_text())['tiles']}

# map -> {'swap': [(name, col, row, new_asset, scale)], 'add': [(name, asset, col, row, scale)]}
PLAN = {
    # 贾母院晚膳：圆桌换八仙桌，八人各一凳，太师椅归贾母，另置顶箱柜与花架
    'dinner': {
        'swap': [],
        'add': [
            ('chair-grandmother', 'official-chair', 19, 11, 1.0),
            ('stool-liwan', 'round-stool', 15, 12, 1.0),
            ('stool-yingchun', 'round-stool', 15, 17, 1.0),
            ('stool-tanchun', 'round-stool', 17, 18, 1.0),
            ('stool-xichun', 'round-stool', 19, 19, 1.0),
            ('stool-daiyu', 'round-stool', 21, 12, 1.0),
            ('stool-wang', 'round-stool', 23, 13, 1.0),
            ('stool-feng', 'round-stool', 24, 11, 1.0),
            ('square-table', 'square-table', 16, 21, 0.8),
            ('cabinet', 'cabinet', 28, 16, 1.0),
            ('vase-stand', 'vase-stand', 12, 11, 1.0),
        ],
    },
    # 碧纱橱外间：火盆取暖，顶箱柜与花架填空
    'night': {
        'swap': [],
        'add': [
            ('brazier', 'brazier', 19, 14, 1.0),
            ('cabinet', 'cabinet', 26, 20, 1.0),
            ('vase-stand', 'vase-stand', 13, 15, 1.0),
        ],
    },
    # 荣禧堂：两处茶几换条案作正厅陈设，中心太师椅一对，花架两具
    'central': {
        'swap': [('tea-table', 25, 20, 'altar-table', 1.0),
                 ('tea-table', 16, 20, 'altar-table', 1.0)],
        'add': [
            ('official-chair-left', 'official-chair', 18, 16, 1.0),
            ('official-chair-right', 'official-chair', 22, 16, 1.0),
            ('vase-stand-left', 'vase-stand', 15, 17, 1.0),
            ('vase-stand-right', 'vase-stand', 25, 17, 1.0),
        ],
    },
    # 应天府刑堂：公案换条案，堂后加太师椅
    'c4_yamen': {
        'swap': [('tea-table', 19, 22, 'altar-table', 0.8)],
        'add': [('official-chair', 'official-chair', 19, 20, 1.0)],
    },
    # 贾政书房：茶几换书案，加太师椅与顶箱柜
    'yucun': {
        'swap': [('tea-table', 19, 13, 'writing-desk', 1.0)],
        'add': [
            ('official-chair', 'official-chair', 20, 11, 1.0),
            ('cabinet', 'cabinet', 26, 18, 1.0),
        ],
    },
    # 林府书斋：茶几换书案，加太师椅与花架
    'lin': {
        'swap': [('tea-table', 16, 10, 'writing-desk', 0.8)],
        'add': [
            ('official-chair', 'official-chair', 17, 9, 1.0),
            ('vase-stand', 'vase-stand', 14, 12, 1.0),
        ],
    },
    # 村肆：茶几换八仙桌，四条方凳
    'tavern': {
        'swap': [('tea-table', 20, 19, 'square-table', 0.7)],
        'add': [
            ('square-stool-guest', 'square-stool', 17, 17, 1.0),
            ('square-stool-host', 'square-stool', 21, 15, 1.0),
            ('square-stool-left', 'square-stool', 14, 17, 1.0),
            ('square-stool-right', 'square-stool', 25, 18, 1.0),
        ],
    },
    # 甄宅：同村肆格局
    'suzhou': {
        'swap': [('tea-table', 21, 18, 'square-table', 0.8)],
        'add': [
            ('square-stool-guest', 'square-stool', 17, 17, 1.0),
            ('square-stool-host', 'square-stool', 21, 15, 1.0),
            ('square-stool-left', 'square-stool', 14, 17, 1.0),
            ('square-stool-right', 'square-stool', 25, 18, 1.0),
        ],
    },
    # 王夫人起居处：茶座后加太师椅，东北角顶箱柜，西侧花架
    'wang': {
        'swap': [],
        'add': [
            ('official-chair', 'official-chair', 21, 14, 1.0),
            ('cabinet', 'cabinet', 27, 7, 1.0),
            ('vase-stand', 'vase-stand', 15, 16, 1.0),
        ],
    },
    # 贾赦院东路小院：茶几换八仙桌，太师椅、花架、方凳
    'east': {
        'swap': [('tea-table', 19, 10, 'square-table', 0.7)],
        'add': [
            ('official-chair', 'official-chair', 16, 10, 1.0),
            ('vase-stand', 'vase-stand', 14, 7, 1.0),
            ('square-stool', 'square-stool', 16, 12, 1.0),
        ],
    },
    # 梨香院：茶几换书案，前厅太师椅，花架与方凳
    # 书案原落在 (17,13)，紧贴 front_hall 锚点 (16,12)，桌面遮住薛姨妈下身
    # 约 21%；移到 (19,15) 后与人物分离，且仍在室内地面 A1 内。
    'c4_lixiang': {
        'swap': [('tea-table', 17, 13, 'writing-desk', 0.6)],
        'add': [
            ('official-chair', 'official-chair', 16, 11, 1.0),
            ('vase-stand', 'vase-stand', 25, 12, 1.0),
            ('square-stool', 'square-stool', 19, 11, 1.0),
            ('writing-desk', 'writing-desk', 19, 15, 0.6),
        ],
    },
}


def placement(asset, col, row, scale):
    """Tiled x/y/w/h for an asset whose anchor ground point is tile (col,row)."""
    a = MANIFEST[asset]
    w, h, (ax, ay) = a['width'] * scale, a['height'] * scale, a['anchor']
    groundx = (col - row) * UNIT
    groundy = (col + row + 1) * UNIT / 2
    bx = groundx + (a['width'] / 2 - ax) * scale
    by = groundy + (a['height'] - ay) * scale
    return by + bx / 2, by - bx / 2, w, h


def asset_of(o):
    return next(p['value'] for p in o['properties'] if p['name'] == 'asset')


def ground_tile(o):
    """(col,row) of an art object's ground tile, from its Tiled x/y.

    Exact inverse of `placement`, so hand-scaled objects (several tea-tables
    ship with a squashed height) still resolve to the tile they stand on.
    """
    a = MANIFEST[asset_of(o)]
    sx, sy = o['width'] / a['width'], o['height'] / a['height']
    bx, by = o['x'] - o['y'], (o['x'] + o['y']) / 2
    gx = bx + (a['anchor'][0] - a['width'] / 2) * sx
    gy = by + (a['anchor'][1] - a['height']) * sy
    d, s = gx / UNIT, gy / (UNIT / 2) - 1
    return (d + s) / 2, (s - d) / 2


def next_id(data):
    return max(o['id'] for l in data['layers'] for o in l.get('objects', [])) + 1


def props(asset, visibility='always', depth=0):
    return [{'name': 'asset', 'type': 'string', 'value': asset},
            {'name': 'visibility', 'type': 'string', 'value': visibility},
            {'name': 'depthOffset', 'type': 'float', 'value': depth}]


def furnish(map_id, plan):
    path = MAPS / f'{map_id}.tmj'
    data = json.loads(path.read_text())
    art = next(l for l in data['layers'] if l['name'] == 'Art')
    foot = next(l for l in data['layers'] if l['name'] == 'ArtFootprints')
    nid = next_id(data)
    changed = False

    for name, col, row, new_asset, scale in plan.get('swap', []):
        target = next((o for o in art['objects']
                       if o['name'] == name and
                       abs(ground_tile(o)[0] - col) < .01 and abs(ground_tile(o)[1] - row) < .01), None)
        if target is None:
            # The swap may already have run, which renames the object to the
            # new asset; a later move is then expressed as an 'add' entry.
            renamed = next((o for o in art['objects']
                            if o['name'] == new_asset and
                            abs(ground_tile(o)[0] - col) < .01 and abs(ground_tile(o)[1] - row) < .01), None)
            if renamed is not None:
                print(f'  {map_id}: {name} at ({col},{row}) already swapped to {new_asset}')
                continue
            # The swapped object may have been moved since; the new asset
            # elsewhere in the map counts as the swap already done.
            moved = next((o for o in art['objects'] if o['name'] == new_asset), None)
            if moved is not None:
                print(f'  {map_id}: {name} already swapped to {new_asset} and moved to '
                      f'({ground_tile(moved)[0]:.0f},{ground_tile(moved)[1]:.0f})')
                continue
            print(f'  !! {map_id}: swap source {name} at ({col},{row}) not found')
            return False
        cur = asset_of(target)
        if cur == new_asset:
            print(f'  {map_id}: {name} at ({col},{row}) already {new_asset}')
            continue
        x, y, w, h = placement(new_asset, col, row, scale)
        target['name'] = new_asset
        target['x'], target['y'] = x, y
        target['width'], target['height'] = w, h
        target['gid'] = GIDS[new_asset]
        for p in target['properties']:
            if p['name'] == 'asset':
                p['value'] = new_asset
        for fo in foot['objects']:
            if fo['name'] == name and abs(fo['x'] - col * UNIT) < 1 and abs(fo['y'] - row * UNIT) < 1:
                fo['name'] = new_asset
        changed = True
        print(f'  {map_id}: swapped {name} -> {new_asset} at ({col},{row}) {w:.0f}x{h:.0f}')

    for name, asset, col, row, scale in plan.get('add', []):
        x, y, w, h = placement(asset, col, row, scale)
        if any(o['name'] == name and abs(ground_tile(o)[0] - col) < .01 and abs(ground_tile(o)[1] - row) < .01
               for o in art['objects']):
            print(f'  {map_id}: {name} at ({col},{row}) already present')
            continue
        art['objects'].append({
            'id': nid, 'name': name, 'x': x, 'y': y, 'width': w, 'height': h,
            'rotation': 0, 'visible': True, 'gid': GIDS[asset], 'type': 'art',
            'properties': props(asset)})
        nid += 1
        if not any(o['name'] == name and abs(o['x'] - col * UNIT) < 1 and abs(o['y'] - row * UNIT) < 1
                   for o in foot['objects']):
            foot['objects'].append({
                'id': nid, 'name': name, 'x': col * UNIT, 'y': row * UNIT,
                'width': float(UNIT), 'height': float(UNIT), 'rotation': 0, 'visible': True,
                'type': 'collision'})
            nid += 1
        changed = True
        print(f'  {map_id}: added {name} ({asset}) at ({col},{row}) {w:.0f}x{h:.0f}')

    if changed:
        data['nextobjectid'] = max(nid, data.get('nextobjectid', 0))
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    return changed


def main() -> int:
    only = sys.argv[1:] or None
    n = 0
    for map_id, plan in PLAN.items():
        if only and map_id not in only:
            continue
        if furnish(map_id, plan):
            n += 1
    print(f'{len(PLAN)} map(s) planned, {n} rewritten')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
