#!/usr/bin/env python3
"""Verify the new interior furniture against the maps it was placed in.

Checks, per modified map:
  1. every Art object references a manifest asset (runtime parse contract);
  2. every Art object stands on a floor tile inside some PlanZone;
  3. every ArtFootprints blocker sits on a floor tile inside some PlanZone;
  4. no Art object drawn IN FRONT of an anchor (larger col+row) covers the
     actor box there (chibi sprites are up to 99x118, anchored bottom-centre).

Run:  python3 scripts/verify_furniture.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT = 64
MANIFEST = json.loads((ROOT / 'public/assets/rongguo/manifest.json').read_text())['assets']
ACTOR_W, ACTOR_H = 99, 118
MAPS = ['dinner', 'night', 'central', 'c4_yamen', 'yucun', 'lin',
        'tavern', 'suzhou', 'wang', 'east', 'c4_lixiang']
NEW = {'square-table', 'altar-table', 'writing-desk', 'official-chair', 'round-stool',
       'square-stool', 'cabinet', 'brazier', 'vase-stand'}


def asset_of(o):
    return next((p['value'] for p in o.get('properties', []) if p['name'] == 'asset'), None)


def ground_point(o):
    """artGround() in screen space: the anchor point on the floor tile."""
    a = MANIFEST[asset_of(o)]
    sx, sy = o['width'] / a['width'], o['height'] / a['height']
    bx, by = o['x'] - o['y'], (o['x'] + o['y']) / 2
    gx = bx + (a['anchor'][0] - a['width'] / 2) * sx
    gy = by + (a['anchor'][1] - a['height']) * sy
    return gx, gy


def story_actor_boxes():
    """scene -> [(anchor, actor)] from every show/move action in the design scripts."""
    import glob
    out = {}
    for path in glob.glob(str(ROOT / 'design/chapter0*-story.json')):
        for step in json.loads(Path(path).read_text()):
            scene = step.get('scene')
            if not scene:
                continue
            for act in step.get('actions', []):
                if act.get('type') == 'show' and act.get('at'):
                    out.setdefault(scene, set()).add((act['at'], act['actor']))
                if act.get('type') == 'move':
                    for via in act.get('via') or []:
                        out.setdefault(scene, set()).add((via, act['actor']))
    return out


def project(col, row):
    return (col - row) * UNIT, (col + row + 1) * UNIT / 2


def main() -> int:
    problems = 0
    boxes = story_actor_boxes()
    for map_id in MAPS:
        data = json.loads((ROOT / f'maps/{map_id}.tmj').read_text())
        zones = [l for l in data['layers'] if l['name'] == 'PlanZones'][0]['objects']
        art = [l for l in data['layers'] if l['name'] == 'Art'][0]['objects']
        foot = [l for l in data['layers'] if l['name'] == 'ArtFootprints'][0]['objects']
        anchors = {o['name']: o for o in [l for l in data['layers'] if l['name'] == 'Anchors'][0]['objects']}

        def on_floor(cx, cy):
            return any(z['x'] / UNIT <= cx < z['x'] / UNIT + z['width'] / UNIT and
                       z['y'] / UNIT <= cy < z['y'] / UNIT + z['height'] / UNIT for z in zones)

        for o in art:
            a = asset_of(o)
            if a not in MANIFEST:
                print(f'  !! {map_id}: art {o["name"]} references unknown asset {a}')
                problems += 1
                continue
            gx, gy = ground_point(o)
            col, row = gx / UNIT, gy / (UNIT / 2) - 1
            col, row = (col + row) / 2, (row - col) / 2
            if not on_floor(col, row):
                print(f'  !! {map_id}: art {o["name"]} ({a}) ground ({col:.2f},{row:.2f}) off the floor')
                problems += 1
        for o in foot:
            if not on_floor(o['x'] / UNIT, o['y'] / UNIT):
                print(f'  !! {map_id}: footprint {o["name"]} at ({o["x"]/UNIT:.0f},{o["y"]/UNIT:.0f}) off the floor')
                problems += 1

        # actor box vs art the runtime draws in front of it
        seen = set()
        for an_name, actor in sorted(boxes.get(map_id, ())):
            if an_name not in anchors or (an_name, actor) in seen:
                continue
            seen.add((an_name, actor))
            sprite = MANIFEST.get(f'{actor}-chibi') or MANIFEST.get('sedan-chair')
            aw, ah = (sprite['width'], sprite['height']) if sprite else (ACTOR_W, ACTOR_H)
            an = anchors[an_name]
            acol, arow = an['x'] / UNIT - .5, an['y'] / UNIT - .5
            ax0, ay0 = project(acol, arow)
            abox = (ax0 - aw / 2, ay0 - ah, ax0 + aw / 2, ay0)
            for o in art:
                a = asset_of(o)
                if a not in MANIFEST:
                    continue
                if next((p['value'] for p in o['properties'] if p['name'] == 'visibility'), 'always') == 'exterior':
                    continue
                gx, gy = ground_point(o)
                if gy <= ay0:      # same or further away -> the actor is drawn in front
                    continue
                bx, by = o['x'] - o['y'], (o['x'] + o['y']) / 2
                obox = (bx - o['width'] / 2, by - o['height'], bx + o['width'] / 2, by)
                ox = min(abox[2], obox[2]) - max(abox[0], obox[0])
                oy = min(abox[3], obox[3]) - max(abox[1], obox[1])
                if ox > 0 and oy > 0:
                    cover = ox * oy / (aw * ah)
                    if cover > .02:
                        tag = 'NEW' if a in NEW else '   '
                        print(f'  {tag} {map_id}: {o["name"]} ({a}) covers {an_name}/{actor} '
                              f'({100*cover:.0f}% of the actor box)')
                        if a in NEW:
                            problems += 1
        print(f'  {map_id}: checked')
    print(f'verification done, {problems} problem(s)')
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
