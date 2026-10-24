#!/usr/bin/env python3
"""Report which cells of a map the story actually walks over, so interior
furnishings can be placed without blocking a route.

Usage: python3 scripts/story_path_cells.py <mapId> [mapId ...]
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_map(map_id):
    d = json.load(open(os.path.join(ROOT, 'maps', map_id + '.tmj')))
    scene_id = next((p['value'] for p in d.get('properties', []) if p['name'] == 'sceneId'), map_id)
    th = d['tileheight']
    zones = []
    for l in d['layers']:
        if l['name'] == 'PlanZones':
            for o in l['objects']:
                zones.append((o['name'].split(' ')[0], o['x'] / th, o['y'] / th, o['width'] / th, o['height'] / th))
    anchors = {}
    for l in d['layers']:
        if l['name'] == 'Anchors':
            for o in l['objects']:
                anchors[o['name']] = (o['x'] / th - 0.5, o['y'] / th - 0.5)
    walkable = set()
    for zid, zc, zr, zw, zh in zones:
        if not (zid.startswith('A') and zid[1:].isdigit()) and zid not in list('BCDEFGHI'):
            continue
        for c in range(int(zc), int(zc + zw)):
            for r in range(int(zr), int(zr + zh)):
                walkable.add((c, r))
    for l in d['layers']:
        if l['name'] == 'ArtFootprints':
            for o in l['objects']:
                for c in range(int(o['x'] / th), int(o['x'] / th + o['width'] / th)):
                    for r in range(int(o['y'] / th), int(o['y'] / th + o['height'] / th)):
                        walkable.discard((c, r))
    return d, scene_id, anchors, walkable


def astar(walkable, start, goal):
    import heapq
    def h(p): return abs(p[0] - goal[0]) + abs(p[1] - goal[1])
    openq = [(h(start), 0, start)]
    best = {start: 0}
    parent = {}
    while openq:
        _, g, cur = heapq.heappop(openq)
        if cur == goal: break
        for dc, dr in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            nxt = (cur[0] + dc, cur[1] + dr)
            if nxt not in walkable: continue
            ng = g + 1
            if ng < best.get(nxt, 1 << 30):
                best[nxt] = ng; parent[nxt] = cur
                heapq.heappush(openq, (ng + h(nxt), ng, nxt))
    if goal not in best: return None
    path = []
    cur = goal
    while cur in parent:
        path.append(cur); cur = parent[cur]
    path.append(start)
    return list(reversed(path))


def main(map_ids):
    scenes = {}
    for f in ('chapter03-story.json', 'chapter04-story.json'):
        p = os.path.join(ROOT, 'design', f)
        if not os.path.exists(p): continue
        d = json.load(open(p))
        steps = d if isinstance(d, list) else d.get('steps', d.get('nodes', []))
        for s in steps:
            scenes.setdefault(s.get('scene'), []).append(s)

    for map_id in map_ids:
        d, scene_id, anchors, walkable = load_map(map_id)
        used = set()
        occupied = set()
        for s in scenes.get(scene_id, []):
            for a in s.get('actions', []):
                if a['type'] == 'show':
                    name = a.get('at')
                    if name in anchors:
                        c, r = int(anchors[name][0]), int(anchors[name][1])
                        occupied.add((c, r))
                        for dc in (-1, 0, 1):
                            for dr in (-1, 0, 1):
                                used.add((c + dc, r + dr))
                elif a['type'] == 'move':
                    via = a.get('via') or []
                    pts = []
                    for name in via:
                        if name not in anchors:
                            pts = None; break
                        pts.append((int(anchors[name][0]), int(anchors[name][1])))
                    if pts is None: continue
                    occupied.update(pts)
                    for p in pts:
                        for dc in (-1, 0, 1):
                            for dr in (-1, 0, 1):
                                used.add((p[0] + dc, p[1] + dr))
                    for i in range(1, len(pts)):
                        path = astar(walkable, pts[i - 1], pts[i])
                        if path is None:
                            print(f'  !! no path {pts[i-1]} -> {pts[i]}')
                            continue
                        used.update(path)
        print(f'=== {map_id}: {len(anchors)} anchors, {len(walkable)} walkable cells')
        zones = {}
        for l in d['layers']:
            if l['name'] == 'PlanZones':
                for o in l['objects']:
                    zones[o['name'].split(' ')[0]] = (int(o['x'] / 64), int(o['y'] / 64), int(o['width'] / 64), int(o['height'] / 64))
        for zid, (zc, zr, zw, zh) in sorted(zones.items()):
            free = []
            for c in range(zc, zc + zw):
                for r in range(zr, zr + zh):
                    if (c, r) in walkable and (c, r) not in used:
                        free.append((c, r))
            print(f'  zone {zid} ({zc},{zr},{zw}x{zh}): {len(free)} free cells')
            if free:
                print('     ', ' '.join(f'{c},{r}' for c, r in free))


if __name__ == '__main__':
    main(sys.argv[1:] or ['central'])
