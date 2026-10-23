#!/usr/bin/env python3
"""Generate planning SVG and an object-only Tiled map, using only the stdlib."""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
plan = json.loads((ROOT / 'design/map-plan.json').read_text())
W, H, TW, TH = (plan[k] for k in ('width', 'height', 'tilewidth', 'tileheight'))
anchors = plan['anchors']


def require(ok, message):
    if not ok:
        raise ValueError(message)


require(W == H == 40 and TW == 2 * TH, 'Expected a 40×40 2:1 isometric map')
for name, point in anchors.items():
    require(len(point) == 2 and all(isinstance(v, int) for v in point), f'Invalid anchor: {name}')
    require(0 <= point[0] < W and 0 <= point[1] < H, f'Out of bounds: {name}')
for z in plan['zones'] + plan['blockers']:
    c, r, w, h = z['rect']
    require(w > 0 and h > 0 and c >= 0 and r >= 0 and c+w <= W and r+h <= H, f'Invalid zone: {z["id"]}')
require(len({x['id'] for x in plan['cast']}) == len(plan['cast']), 'Duplicate cast ID')
cast_positions = []
for actor in plan['cast']:
    require(actor['anchor'] in anchors, f'Unknown cast anchor: {actor["id"]}')
    cast_positions.append(tuple(anchors[actor['anchor']]))
require(len(set(cast_positions)) == len(cast_positions), 'Overlapping cast planning positions')


def inside(x, y, rect):
    c, r, w, h = rect
    return c <= x < c+w and r <= y < r+h


for route in plan['routes']:
    require(all(a in anchors for a in route['anchors']), f'Unknown route anchor: {route["id"]}')
    points = [anchors[a] for a in route['anchors']]
    for start, end in zip(points, points[1:]):
        # Sample the entire straight segment against the current explicit blockers.
        steps = max(abs(end[0]-start[0]), abs(end[1]-start[1])) * 20
        for i in range(steps+1):
            t = i / max(steps, 1)
            x = start[0]+0.5+(end[0]-start[0])*t
            y = start[1]+0.5+(end[1]-start[1])*t
            require(not any(inside(x, y, b['rect']) for b in plan['blockers']), f'Route hits blocker: {route["id"]}')
for name, (c, r) in anchors.items():
    require(not any(inside(c+0.5, r+0.5, b['rect']) for b in plan['blockers']), f'Anchor hits blocker: {name}')

# Tiled isometric object coordinates: one logical grid unit = tileheight pixels.
objects = []
next_id = 1


def obj(name, kind, c, r, **extra):
    global next_id
    value = dict(id=next_id, name=name, type=kind, x=c*TH, y=r*TH,
                 width=0, height=0, rotation=0, visible=True)
    value.update(extra)
    next_id += 1
    return value


layers = [dict(id=1, name='Ground', type='tilelayer', x=0, y=0, width=W,
               height=H, opacity=1, visible=True, data=[0]*(W*H))]


def layer(name, entries, color):
    layers.append(dict(id=len(layers)+1, name=name, type='objectgroup', x=0, y=0,
                       opacity=1, visible=True, draworder='topdown', color=color, objects=entries))


layer('PlanZones', [obj(z['id']+' '+z['name'], 'plan_zone', *z['rect'][:2],
                       width=z['rect'][2]*TH, height=z['rect'][3]*TH) for z in plan['zones']], '#687e68')
layer('PlanBlockers', [obj(b['name'], 'plan_blocker', *b['rect'][:2],
                          width=b['rect'][2]*TH, height=b['rect'][3]*TH) for b in plan['blockers']], '#9c5b50')
layer('Anchors', [obj(name, 'anchor', c+0.5, r+0.5, point=True,
                     properties=[dict(name='col', type='int', value=c), dict(name='row', type='int', value=r)])
                  for name, (c, r) in anchors.items()], '#8b603f')
route_objects = []
for route in plan['routes']:
    points = [anchors[a] for a in route['anchors']]
    c0, r0 = points[0]
    route_objects.append(obj(route['name'], 'route', c0+0.5, r0+0.5,
        polyline=[dict(x=(c-c0)*TH, y=(r-r0)*TH) for c, r in points],
        properties=[dict(name='route_id', type='string', value=route['id']),
                    dict(name='anchor_ids', type='string', value=','.join(route['anchors']))]))
layer('Routes', route_objects, '#b07746')
layer('Cast', [obj(a['name'], 'cast_plan', anchors[a['anchor']][0]+0.5,
                   anchors[a['anchor']][1]+0.5, point=True,
                   properties=[dict(name='actor_id', type='string', value=a['id']),
                               dict(name='anchor', type='string', value=a['anchor']),
                               dict(name='shown_from', type='string', value=a['shownFrom'])])
                for a in plan['cast']], '#775a7b')
tiled = dict(type='map', version='1.10', orientation='isometric', renderorder='right-down',
             width=W, height=H, tilewidth=TW, tileheight=TH, infinite=False,
             nextlayerid=len(layers)+1, nextobjectid=next_id, layers=layers, tilesets=[],
             backgroundcolor='#f3ecdf', properties=[dict(name='status', type='string', value='planning-only'),
                dict(name='source', type='string', value='../design/map-plan.json'),
                dict(name='adaptation', type='bool', value=True)])
(ROOT/'maps').mkdir(exist_ok=True)
# Preserve authored image placements when regenerating the planning layers.
existing_path = ROOT/'maps/rongguo-entry.tmj'
if existing_path.exists():
    previous = json.loads(existing_path.read_text())
    for authored in previous.get('layers', []):
        if authored['name'] in ('Art', 'ArtFootprints'):
            authored['id'] = len(tiled['layers'])+1
            for item in authored.get('objects', []):
                item['id'] = next_id
                next_id += 1
            tiled['layers'].append(authored)
    tiled['tilesets'] = previous.get('tilesets', [])
    tiled['nextlayerid'] = len(tiled['layers'])+1
    tiled['nextobjectid'] = next_id
    if tiled['tilesets']:
        tiled['properties'][0]['value'] = 'art-sample'
existing_path.write_text(json.dumps(tiled, ensure_ascii=False, indent=2)+'\n')

# Static project diagram. Smaller projected grid, full-scale readable labels.
OX, OY, SX, SY = 690, 145, 15.5, 7.75


def project(c, r):
    return OX+(c-r)*SX, OY+(c+r)*SY


def coords(points):
    return ' '.join(f'{x:.2f},{y:.2f}' for x, y in points)


def text(x, y, value, size=16, fill='#403c35', anchor='middle', extra=''):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" {extra}>{escape(value)}</text>'


svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1380" height="1120" viewBox="0 0 1380 1120" role="img" aria-labelledby="title desc">',
       '<title id="title">荣国府入府片区：40×40 等距地图布局草案</title>',
       '<desc id="desc">叙事改编示意。黛玉从西角门经前段通道、垂花门、穿堂进入贾母院落和正房。实线为入府路线，虚线为凤姐入场路线。</desc>',
       '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#aa633e" stroke-width="1.5"/></marker></defs>',
       '<rect width="1380" height="1120" fill="#f6f0e5"/>',
       '<g font-family="PingFang SC,Microsoft YaHei,sans-serif">',
       text(65, 53, '荣国府 · 入府片区', 30, anchor='start'),
       text(65, 85, '40×40 格 / 等距菱形 / 第三回入府至凤姐迎客 / 布局草案 v0.1', 17, anchor='start'),
       text(65, 113, '改编示意，非建筑复原；区域尺寸、方位、站位与演出均为设计假定。', 15, '#796d5c', 'start')]
base = [project(0,0), project(W,0), project(W,H), project(0,H)]
svg.append(f'<polygon points="{coords(base)}" fill="#e9e3d6" stroke="#b3a58c"/>')
for z in plan['zones']:
    c,r,w,h = z['rect']
    pts=[project(c,r),project(c+w,r),project(c+w,r+h),project(c,r+h)]
    color = '#d7c5ab' if z['id'] in ['C','D','F','G','H'] else '#d6ddcc'
    if z['id']=='I': color='#ddd9d0'
    svg.append(f'<polygon points="{coords(pts)}" fill="{color}" stroke="#a89a81" stroke-width="1.4"/>')
for i in range(W+1):
    for start,end in [(project(i,0),project(i,H)),(project(0,i),project(W,i))]:
        svg.append(f'<line x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" stroke="#b5ad9b" stroke-opacity="{0.55 if i%5==0 else 0.24}" stroke-width="{0.8 if i%5==0 else 0.55}"/>')
for b in plan['blockers']:
    c,r,w,h=b['rect']
    svg.append(f'<polygon points="{coords([project(c,r),project(c+w,r),project(c+w,r+h),project(c,r+h)])}" fill="#86594a"/>')
for n,route in enumerate(plan['routes']):
    pts=[project(anchors[a][0]+0.5,anchors[a][1]+0.5) for a in route['anchors']]
    dash=' stroke-dasharray="7 5"' if n else ''
    svg.append(f'<polyline points="{coords(pts)}" fill="none" stroke="#aa633e" stroke-width="3" stroke-linejoin="round" marker-end="url(#arrow)"{dash}/>')
    for x,y in pts:
        svg.append(f'<circle cx="{x}" cy="{y}" r="2.7" fill="#aa633e"/>')
# IDs label broad regions; names and exact logical coordinates live in the legend.
for z in plan['zones']:
    c,r,w,h=z['rect']
    x,y=project(c+w-1,r+1)
    svg.append(f'<circle cx="{x}" cy="{y}" r="13" fill="#f6f0e5" stroke="#a89a81"/>')
    svg.append(text(x,y+5,z['id'],15))

# Mark major meeting points only; the crowded interior is shown separately below.
for name, label, dx, dy in [('west_gate','入府',-38,24),('flower_gate_stop','下轿',-45,17),
                          ('screen_detour','绕插屏',-55,-7),('hall_door','入室',-43,-4),('feng_entry','凤姐入场',80,4)]:
    c,r=anchors[name]; x,y=project(c+0.5,r+0.5)
    svg.append(text(x+dx,y+dy,label,15))
for i in range(0,41,10):
    x,y=project(i,0)
    svg.append(text(x+15,y-10,str(i),13,'#796d5c'))
    x,y=project(0,i)
    svg.append(text(x-18,y-2,str(i),13,'#796d5c'))
svg.append(text(1030,162,'列 →',14,'#796d5c'))
svg.append(text(338,162,'← 行',14,'#796d5c'))
svg.append(text(65,790,'区域索引  ·  (列,行,宽,高)，索引从 0 开始',17,anchor='start'))
for index,z in enumerate(plan['zones']):
    x=65+(index//5)*395; y=824+(index%5)*29
    label=f'{z["id"]}  {z["name"]}   ({",".join(map(str,z["rect"]))})'
    svg.append(text(x,y,label,16,anchor='start'))

# Interior inset is a logical top-down coordinate reference, clearly labeled.
svg.append(text(900,790,'室内站位索引（俯视，非等距）',17,anchor='start'))
IX,IY,STEP=905,815,28
for row in range(6):
    for col in range(12):
        svg.append(f'<rect x="{IX+col*STEP}" y="{IY+row*STEP}" width="{STEP}" height="{STEP}" fill="none" stroke="#b9ad98" stroke-width="0.6"/>')
for a,label in [('grandmother_seat','贾'),('daiyu_greet','黛'),('xing_seat','邢'),('wang_seat','王'),
                ('liwan_seat','李'),('yingchun_seat','迎'),('tanchun_seat','探'),('xichun_seat','惜'),('feng_meet','凤')]:
    c,r=anchors[a]; x=IX+(c-16+0.5)*STEP; y=IY+(r-4+0.5)*STEP
    svg.append(f'<circle cx="{x}" cy="{y}" r="11" fill="#f6f0e5" stroke="#8d7760"/>')
    svg.append(text(x,y+5,label,14))
svg.append(text(900,1008,'黛：迎接点；安坐后移至 (20,6)',14,'#796d5c','start'))
svg.append(text(65,1003,'━━  黛玉入府路线       ┄┄  凤姐入场路线       深色短块：插屏',16,anchor='start'))
svg.append(text(65,1038,'路线与人物站位以 design/map-plan.json 为准；占位图尚不包含贴图、完整墙体或可行走网格。',15,'#796d5c','start'))
svg.append(text(65,1073,'比例：地砖 128×64 px；图中缩小展示。阅读分镜：docs/storyboard.md',15,'#796d5c','start'))
svg.extend(['</g>','</svg>'])
(ROOT/'docs/rongguo-layout.svg').write_text('\n'.join(svg)+'\n')
print(f'Validated {len(anchors)} anchors, {len(plan["cast"])} cast positions and {len(plan["routes"])} routes.')
print('Generated docs/rongguo-layout.svg and maps/rongguo-entry.tmj (planning objects only).')
