"""Export the shared estate geography as a 40x40 Tiled editing reference."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data=json.loads((root/'design/rongguo-world.json').read_text())
tiles=json.loads((root/'maps/rongguo-art.tsj').read_text())
manifest=json.loads((root/'public/assets/rongguo/manifest.json').read_text())['assets']
tile_ids={next(p['value'] for p in t['properties'] if p['name']=='asset'):t['id']+1 for t in tiles['tiles']}
next_id=1

def obj(name,x,y,**kwargs):
    global next_id
    result={'id':next_id,'name':name,'type':'','x':x,'y':y,'width':0,'height':0,'rotation':0,'visible':True,**kwargs};next_id+=1;return result

def props(**values):return [{'name':k,'type':'string','value':str(v)} for k,v in values.items()]
locations=[l for l in data['locations'] if not l['external']]
anchors=[obj(l['id'],(l['col']+.5)*64,(l['row']+.5)*64,point=True,properties=props(sceneId=l['scene'],focus=l['focus'],storyNode=l['start'],title=l['name'],description=l['description'])) for l in locations]
network=data['network']
roads=[]
for a,b in network['edges']:
    start,end=network['nodes'][a],network['nodes'][b]
    roads.append(obj(a+' → '+b,(start[0]+.5)*64,(start[1]+.5)*64,polyline=[{'x':0,'y':0},{'x':(end[0]-start[0])*64,'y':(end[1]-start[1])*64}]))
art=[]
for l in locations:
    a=manifest[l['asset']];w=(l['width']+l['height'])*64*.86;h=w*a['height']/a['width'];scale=w/a['width']
    # Match Tiled bottom-center coordinates to the calibrated ground anchor.
    dx=(a['anchor'][0]-a['width']/2)*scale;dy=(a['anchor'][1]-a['height'])*scale
    art.append(obj(l['name'],(l['col']+.5)*64-dy-dx/2,(l['row']+.5)*64-dy+dx/2,gid=tile_ids[l['asset']],width=w,height=h,properties=props(asset=l['asset'],sceneId=l['scene'],locationId=l['id'])))
for g in data['gates']:
    if g['id']=='west_gate':continue
    a=manifest[g['asset']];w=94*64/17;scale=w/a['width'];h=a['height']*scale
    dx=(a['anchor'][0]-a['width']/2)*scale;dy=(a['anchor'][1]-a['height'])*scale
    art.append(obj(g['name'],(g['col']+.5)*64-dy-dx/2,(g['row']+.5)*64-dy+dx/2,gid=tile_ids[g['asset']],width=w,height=h,properties=props(asset=g['asset'],gateId=g['id'])))
layers=[]
gates=[obj(g['name'],(g['col']+.5)*64,(g['row']+.5)*64,point=True,properties=props(gateId=g['id'],wall=g['wall'],asset=g['asset'])) for g in data['gates']]
walls=[obj('院墙',a[0]*64,a[1]*64,polyline=[{'x':0,'y':0},{'x':(b[0]-a[0])*64,'y':(b[1]-a[1])*64}]) for a,b in data['walls']]
for name,objects,color in [('Gates',gates,'#655441'),('Walls',walls,'#83916c'),('Locations',anchors,'#526b54'),('Roads',roads,'#b99553'),('Art',art,'#83916c')]:
    layers.append({'id':len(layers)+1,'name':name,'type':'objectgroup','draworder':'topdown','opacity':1,'visible':True,'x':0,'y':0,'color':color,'objects':objects})
result={'type':'map','version':'1.10','tiledversion':'1.11.2','orientation':'isometric','renderorder':'right-down','width':40,'height':40,'tilewidth':128,'tileheight':64,'infinite':False,'nextlayerid':len(layers)+1,'nextobjectid':next_id,'layers':layers,'tilesets':[{'firstgid':1,'source':'../rongguo-art.tsj'}],'properties':props(title='荣国府总览',note=data['note'],source='design/rongguo-world.json')}
(root/'maps/world/rongguo-overview.tmj').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(f'Exported estate: {len(locations)} locations, linked roads, calibrated artwork.')
