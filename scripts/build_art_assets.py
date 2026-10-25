#!/usr/bin/env python3
"""Calibrate RGBA assets; export one shared Tiled/runtime placement contract.
Run with a Python having Pillow and numpy. Source images are never overwritten.
"""
import json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from character_identity_assets import apply_identity
ROOT=Path(__file__).resolve().parents[1]
config=json.loads((ROOT/'art/calibration.json').read_text())
output=ROOT/'public/assets/rongguo';output.mkdir(parents=True,exist_ok=True)
assets={};reports=[]
for item in config['assets']:
 key=item['id'];stem=f"{item.get('sourceId',key)}_s{item['seed']}"
 # Most assets are cut by SAM. A group of overlapping figures defeats it, so those
 # entries ask for the paper-key matte instead (see scripts/matte_paper_key.py).
 source=ROOT/f"art/matted/{stem}-{item.get('matteKind','sam')}.png"
 im=Image.open(source).convert('RGBA');a=np.asarray(im.getchannel('A')).copy()
 # Keep solid painted interiors. Only the final edge is antialiased at output size.
 a=np.where(a>=110,255,0).astype('uint8');im.putalpha(Image.fromarray(a))
 # Retain held objects explicitly when the person-only SAM mask omits them.
 if item.get('restorePolygons'):
  original=Image.open(ROOT/f'art/source/{stem}-01.png').convert('RGBA')
  retained=Image.new('L',im.size,0);brush=ImageDraw.Draw(retained)
  for polygon in item['restorePolygons']:brush.polygon([tuple(p) for p in polygon],fill=255)
  im.paste(original,(0,0),retained)

 if 'clipRect' in item:
  mask=Image.new('L',im.size,0);ImageDraw.Draw(mask).rectangle(item['clipRect'],fill=255);im.putalpha(Image.fromarray(np.minimum(np.asarray(im.getchannel('A')),np.asarray(mask))))
 draw=ImageDraw.Draw(im)
 for polygon in item.get('clearPolygons',[]):draw.polygon([tuple(p) for p in polygon],fill=(0,0,0,0))
 for rect in item.get('clearRectangles',[]):draw.rectangle(rect,fill=(0,0,0,0))
 ax,ay=item['anchor'];matrix=np.eye(3)
 if 'bodyCompress' in item:
  split=item['bodyCompress']['split'];f=item['bodyCompress']['factor']
  lower=im.crop((0,split,im.width,im.height)).resize((im.width,round((im.height-split)*f)),Image.Resampling.LANCZOS)
  joined=Image.new('RGBA',(im.width,split+lower.height));joined.paste(im.crop((0,0,im.width,split)),(0,0));joined.paste(lower,(0,split));im=joined
  ay=split+(ay-split)*f if ay>split else ay
 if 'baseSlope' in item:
  shear=item['targetSlope']-item['baseSlope']
  matrix[1,0]=shear
 corners=np.array([[0,0,1],[im.width,0,1],[0,im.height,1],[im.width,im.height,1]]).T
 pts=matrix@corners;minx,miny=np.floor(pts[:2].min(axis=1));maxx,maxy=np.ceil(pts[:2].max(axis=1))
 matrix[0,2]=-minx;matrix[1,2]=-miny
 inv=np.linalg.inv(matrix)
 im=im.transform((int(maxx-minx),int(maxy-miny)),Image.Transform.AFFINE,tuple(inv[:2].ravel()),Image.Resampling.BICUBIC)
 anchor=matrix@np.array([ax,ay,1.]);ax,ay=anchor[:2]
 if item.get('mirror'):
  im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);ax=im.width-ax
 bbox=im.getbbox();im=im.crop(bbox);ax-=bbox[0];ay-=bbox[1]
 factor=item['width']/im.width if 'width' in item else item['height']/im.height
 size=(round(im.width*factor),round(im.height*factor));im=im.resize(size,Image.Resampling.LANCZOS)
 ax*=size[0]/(bbox[2]-bbox[0]);ay*=size[1]/(bbox[3]-bbox[1])
 a=np.asarray(im.getchannel('A')).copy();a[a<item.get('alphaFloor',16)]=0;a[a>item.get('solidAlphaThreshold',210)]=255;im.putalpha(Image.fromarray(a))
 assets[key]={'image':f'/assets/rongguo/{key}.png','width':im.width,'height':im.height,'anchor':[round(ax,3),round(ay,3)],'source':f'art/source/{stem}-01.png','matte':str(source.relative_to(ROOT)),'crop':list(bbox),'shear':item.get('targetSlope',0)-item.get('baseSlope',0),'mirror':item.get('mirror',False),'bodyCompress':item.get('bodyCompress')}
 im=apply_identity(ROOT,key,im,assets[key]);im.save(output/f'{key}.png');a=np.asarray(im.getchannel('A'))
 visible=a>0;solid=float((a[visible]>=250).mean()) if visible.any() else 0
 reports.append({'asset':key,'visiblePixels':int(visible.sum()),'solidAlpha250Ratio':round(solid,5),'width':im.width,'height':im.height})
# The manifest is shared with assets that are not calibrated here: the portrait
# emotion variants are painted by scripts/build_emotions.py and registered
# separately. Rebuilding from the calibration alone would silently drop them,
# so the entries that this run does not produce are carried over.
existing={}
manifest_path=output/'manifest.json'
if manifest_path.exists():
    try: existing=json.loads(manifest_path.read_text()).get('assets',{})
    except json.JSONDecodeError: existing={}
calibrated=set(assets)
for key,entry in existing.items():
    if key in calibrated: continue
    if not (ROOT/'public'/entry.get('image','').lstrip('/')).exists(): continue
    assets[key]=entry
manifest={'version':1,'tilewidth':128,'tileheight':64,'assets':assets}
# indent=1 matches build_emotions.py and restore_emotion_manifest.py, so whichever
# of the three writers runs last the file keeps the same shape and the diff stays
# about content instead of being a full reindent.
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=1)+'\n')
(ROOT/'art/alpha-report.json').write_text(json.dumps(reports,indent=2)+'\n')
# A collection of images uses standard bottom alignment in Tiled. Gameplay anchors
# are converted to image-bottom coordinates at export, so no private tileoffset convention.
tiles=[];gids={}
for i,(key,a) in enumerate(assets.items()):
 gids[key]=i+1;tiles.append({'id':i,'image':f'../public{a["image"]}','imagewidth':a['width'],'imageheight':a['height'],'properties':[{'name':'asset','type':'string','value':key}]})
ts={'type':'tileset','version':'1.10','name':'荣国府手绘素材','tilewidth':max(a['width'] for a in assets.values()),'tileheight':max(a['height'] for a in assets.values()),'tilecount':len(assets),'columns':0,'objectalignment':'bottom','tiles':tiles}
(ROOT/'maps/rongguo-art.tsj').write_text(json.dumps(ts,ensure_ascii=False,indent=2)+'\n')
path=ROOT/'maps/rongguo-entry.tmj';tmj=json.loads(path.read_text())
# Explicit rebuild command replaces generated Art only. Normal Tiled edits are read directly.
tmj['layers']=[l for l in tmj['layers'] if l['name'] not in ('Art','ArtFootprints')]
objects=[];blockers=[];nextid=max(o['id'] for l in tmj['layers'] for o in l.get('objects',[]))+1
for p in config['placements']:
 a=assets[p['asset']];s=p.get('scale',1);w,h=a['width']*s,a['height']*s
 groundx=(p['col']-p['row'])*64;groundy=(p['col']+p['row']+1)*32
 bx=groundx+(a['width']/2-a['anchor'][0])*s;by=groundy+(a['height']-a['anchor'][1])*s
 props=[{'name':'asset','type':'string','value':p['asset']},{'name':'visibility','type':'string','value':p.get('visibility','always')},{'name':'depthOffset','type':'float','value':p.get('depthOffset',0)}]
 objects.append({'id':nextid,'name':p['name'],'type':'art','gid':gids[p['asset']],'x':by+bx/2,'y':by-bx/2,'width':w,'height':h,'rotation':0,'visible':True,'properties':props});nextid+=1
 if 'collision' in p:
  c,r,cw,rh=p['collision'];blockers.append({'id':nextid,'name':p['name'],'type':'collision','x':c*64,'y':r*64,'width':cw*64,'height':rh*64,'rotation':0,'visible':True});nextid+=1
for name,entries,visible in [('Art',objects,True),('ArtFootprints',blockers,False)]:
 tmj['layers'].append({'id':max(l['id'] for l in tmj['layers'])+1,'name':name,'type':'objectgroup','x':0,'y':0,'opacity':1,'visible':visible,'draworder':'topdown','objects':entries})
tmj['tilesets']=[{'firstgid':1,'source':'rongguo-art.tsj'}];tmj['nextobjectid']=nextid;tmj['nextlayerid']=max(l['id'] for l in tmj['layers'])+1
for p in tmj['properties']:
 if p['name']=='status':p['value']='art-sample'
path.write_text(json.dumps(tmj,ensure_ascii=False,indent=2)+'\n')
# Contact sheet includes actual alpha on a contrasting ground and calibrated anchors.
sheet=Image.new('RGB',(1200,math.ceil(len(assets)/4)*360),'#ece6d8');d=ImageDraw.Draw(sheet)
for i,(key,a) in enumerate(assets.items()):
 x=(i%4)*300;y=(i//4)*360
 for yy in range(y,y+320,16):
  for xx in range(x,x+300,16):d.rectangle((xx,yy,xx+15,yy+15),fill='#455956' if ((xx-x)//16+(yy-y)//16)%2 else '#536864')
 im=Image.open(output/f'{key}.png');s=min(280/im.width,295/im.height);im=im.resize((round(im.width*s),round(im.height*s)))
 px=x+(300-im.width)//2;py=y+310-im.height;sheet.paste(im,(px,py),im)
 ax=px+a['anchor'][0]*s;ay=py+a['anchor'][1]*s;d.line((ax-8,ay,ax+8,ay),fill='#f4be6b',width=2);d.line((ax,ay-8,ax,ay+8),fill='#f4be6b',width=2)
 d.text((x+12,y+330),key,fill='#344b42')
sheet.save(ROOT/'art/asset-contact.png')
print(f'Calibrated {len(assets)} assets; exported {len(objects)} Tiled image objects.')
print(json.dumps(reports,indent=2))
