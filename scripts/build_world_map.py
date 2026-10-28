"""Export every atlas level as a 40x40 Tiled editing reference (single source: atlas-maps.json)."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
atlas=json.loads((root/'design/atlas-maps.json').read_text())
tiles=json.loads((root/'maps/rongguo-art.tsj').read_text())
manifest=json.loads((root/'public/assets/rongguo/manifest.json').read_text())['assets']
tile_ids={next(p['value'] for p in t['properties'] if p['name']=='asset'):t['id']+1 for t in tiles['tiles']}

def build(level_id, level):
    next_id=1
    def obj(name,x,y,**kwargs):
        nonlocal next_id
        result={'id':next_id,'name':name,'type':'','x':x,'y':y,'width':0,'height':0,'rotation':0,'visible':True,**kwargs}
        next_id+=1;return result
    def props(**values):return [{'name':k,'type':'string','value':str(v)} for k,v in values.items()]
    locations=level['locations']
    anchors=[obj(l['id'],(l['col']+.5)*64,(l['row']+.5)*64,point=True,
                 properties=props(sceneId=l.get('scene',''),focus=l.get('focus',''),storyNode=l.get('start',''),
                                  title=l['name'],kind=l['kind'],group=l.get('group',''),drill=l.get('drill',''),
                                  description=l['description'])) for l in locations]
    network=level.get('network')
    roads=[]
    if network:
        for a,b in network['edges']:
            start,end=network['nodes'][a],network['nodes'][b]
            roads.append(obj(a+' → '+b,(start[0]+.5)*64,(start[1]+.5)*64,
                             polyline=[{'x':0,'y':0},{'x':(end[0]-start[0])*64,'y':(end[1]-start[1])*64}]))
    art=[]
    for l in locations:
        if l['asset'] not in manifest:continue
        a=manifest[l['asset']];w=(l.get('width',3)+l.get('height',3))*64*.86
        h=w*a['height']/a['width'];scale=w/a['width']
        dx=(a['anchor'][0]-a['width']/2)*scale;dy=(a['anchor'][1]-a['height'])*scale
        art.append(obj(l['name'],(l['col']+.5)*64-dy-dx/2,(l['row']+.5)*64-dy+dx/2,gid=tile_ids[l['asset']],
                       width=w,height=h,properties=props(asset=l['asset'],sceneId=l.get('scene',''),locationId=l['id'])))
    for g in level.get('gates',[]):
        if g['asset'] not in manifest:continue
        a=manifest[g['asset']];w=94*64/17;scale=w/a['width'];h=a['height']*scale
        dx=(a['anchor'][0]-a['width']/2)*scale;dy=(a['anchor'][1]-a['height'])*scale
        art.append(obj(g['name'],(g['col']+.5)*64-dy-dx/2,(g['row']+.5)*64-dy+dx/2,gid=tile_ids[g['asset']],
                       width=w,height=h,properties=props(asset=g['asset'],gateId=g['id'])))
    layers=[]
    gates=[obj(g['name'],(g['col']+.5)*64,(g['row']+.5)*64,point=True,properties=props(gateId=g['id'],asset=g['asset'])) for g in level.get('gates',[])]
    walls=[obj('院墙',a[0]*64,a[1]*64,polyline=[{'x':0,'y':0},{'x':(b[0]-a[0])*64,'y':(b[1]-a[1])*64}]) for a,b in level.get('walls',[])]
    groups=[obj(g['name'],g['rect'][0]*64,g['rect'][1]*64,width=g['rect'][2]*64,height=g['rect'][3]*64,
                properties=props(groupId=g['id'],note=g.get('note',''))) for g in level.get('groups',[])]
    markers=[obj(m['name'],(m['col']+.5)*64,(m['row']+.5)*64,point=True,properties=props(kind='marker')) for m in level.get('markers',[])]
    for name,objects,color in [('Gates',gates,'#655441'),('Walls',walls,'#83916c'),('Groups',groups,'#9a8f6a'),
                               ('Locations',anchors,'#526b54'),('Roads',roads,'#b99553'),('Markers',markers,'#8a8f7a'),('Art',art,'#83916c')]:
        if objects:layers.append({'id':len(layers)+1,'name':name,'type':'objectgroup','draworder':'topdown','opacity':1,
                                  'visible':True,'x':0,'y':0,'color':color,'objects':objects})
    result={'type':'map','version':'1.10','tiledversion':'1.11.2','orientation':'isometric','renderorder':'right-down',
            'width':40,'height':40,'tilewidth':128,'tileheight':64,'infinite':False,'nextlayerid':len(layers)+1,'nextobjectid':next_id,
            'layers':layers,'tilesets':[{'firstgid':1,'source':'../rongguo-art.tsj'}],
            'properties':props(title=level['title'],subtitle=level['subtitle'],parent=level.get('parent','') or '',
                               note=level.get('note',''),source='design/atlas-maps.json')}
    out=root/'maps/world'/f'{level_id}-overview.tmj'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return out.name,len(locations),len(roads)

for level_id,level in atlas['levels'].items():
    name,loc,roads=build(level_id,level)
    print(f'Exported {name}: {loc} locations, {roads} road segments.')
