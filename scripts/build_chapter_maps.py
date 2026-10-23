#!/usr/bin/env python3
"""Build chapter-three stage maps; preserve the authored Rongguo entry map."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Rectangles are playable floors; walls/props have separately authored footprints.
scenes={
 'lin':{'name':'扬州 · 林府与江岸','theme':'river','zones':[[10,7,15,10],[10,17,10,12],[20,23,11,8]],'anchors':{'study_guest':[15,11],'study_host':[17,10],'daiyu_wait':[18,12],'door':[16,17],'garden':[16,23],'quay':[22,27],'boat':[27,27],'departure':[30,27]},'labels':[['书斋',17,9],['林府',16,19],['江岸',25,28]],'props':[('main-hall',17,14,1),('garden-tree',10,18,1.2),('garden-tree',22,17,1),('garden-rock',20,20,1),('river-boat',27,27,.8),('tea-table',16,10,.65)]},
 'capital':{'name':'京城 · 宁荣街','theme':'street','zones':[[5,22,29,8],[5,12,9,10],[22,10,11,12]],'anchors':{'street_west':[6,26],'ning_gate':[12,23],'rong_gate':[26,23],'west_corner':[24,29],'outside':[8,29]},'labels':[['宁国府',12,16],['荣国府',27,15],['西角门',24,29],['宁荣街',18,27]],'props':[('rongxi-hall',12,20,.9),('rongxi-hall',27,19,1),('garden-tree',5,21,1.1),('garden-tree',33,20,1.2)]},
 'east':{'name':'贾赦院 · 东路小院','theme':'garden','zones':[[10,23,17,7],[10,13,17,10],[13,5,12,8]],'anchors':{'east_gate':[13,28],'small_court':[15,22],'bamboo_door':[17,17],'xing_room':[18,11],'daiyu_guest':[19,13],'xing_host':[17,11],'messenger':[21,12],'return_gate':[23,28]},'labels':[['东路院落',15,24],['垂花门',17,18],['邢夫人房',18,10]],'props':[('main-hall',18,14,.95),('bamboo-gate',17,18,.75),('garden-tree',11,20,1),('garden-tree',25,21,1.2),('garden-tree',25,8,1),('garden-rock',24,18,.9),('tea-table',19,10,.65)]},
 'central':{'name':'荣府中轴 · 荣禧堂','theme':'formal','zones':[[13,22,13,12],[12,10,17,12],[7,8,5,16],[29,8,5,16]],'anchors':{'ceremonial_gate':[19,31],'inner_gate':[19,26],'rongxi_steps':[19,23],'rongxi_door':[19,20],'rongxi_center':[20,16],'west_room':[14,14],'east_door':[27,17],'east_court':[31,19]},'labels':[['荣禧堂',21,13],['内仪门',19,27],['西耳房',13,15],['东角门',29,19]],'props':[('rongxi-hall',20,20,1.15),('main-hall',9,16,.7),('garden-tree',11,26,1.1),('garden-tree',29,26,1.1),('garden-rock',27,22,.9)]},
 'wang':{'name':'王夫人院 · 东廊三间','theme':'interior','zones':[[10,18,20,12],[12,6,16,12]],'anchors':{'court_entry':[14,28],'hall_entry':[18,20],'kang_edge':[19,11],'wang_host':[21,10],'guest_seat':[18,12],'tea_seat':[22,13],'east_corridor':[28,19],'south_passage':[23,24],'back_lane':[17,29],'feng_room':[12,24]},'labels':[['王夫人起居处',20,8],['东廊',28,20],['夹道',17,29],['凤姐院门',12,24]],'props':[('main-hall',20,18,1),('tea-table',20,11,.9),('wood-screen',24,10,.7),('garden-tree',11,24,1),('garden-tree',30,18,1.1),('estate-feng',12,24,.7)]},
 'dinner':{'name':'贾母院 · 后房与晚膳','theme':'interior','zones':[[10,8,20,19]],'anchors':{'back_door':[13,25],'grandmother_place':[19,12],'daiyu_place':[20,14],'wang_place':[23,14],'feng_place':[24,12],'yingchun_place':[16,16],'tanchun_place':[18,17],'xichun_place':[20,18],'liwan_place':[16,13],'baoyu_greet':[21,14],'grandmother_greet':[20,12],'maid_place':[25,18],'tea_place':[21,20]},'labels':[['后房',13,24],['贾母房 · 晚膳',20,10]],'props':[('dining-table',19,14,1),('tea-table',22,20,.8),('wood-screen',26,11,.9),('garden-tree',10,24,1),('garden-tree',30,10,1)]},
 'night':{'name':'贾母院 · 碧纱橱与外间','theme':'night','zones':[[10,7,20,20]],'anchors':{'outer_door':[14,25],'grandmother_bed':[16,10],'daiyu_bed':[21,11],'baoyu_bed':[17,20],'xiren_place':[18,21],'xueyan_place':[23,13],'yingge_place':[23,11],'bedside':[22,11],'night_talk':[21,16],'letter_place':[16,21]},'labels':[['贾母套间',15,10],['碧纱橱',22,9],['外间暖阁',17,21]],'props':[('canopy-bed',21,12,.85),('canopy-bed',16,11,.7),('canopy-bed',17,21,.8),('wood-screen',24,16,.9),('tea-table',13,20,.7)]},
 'yucun':{'name':'京城 · 贾政书房','theme':'formal','zones':[[10,8,20,18]],'anchors':{'visitor':[17,21],'host':[20,13],'guest':[18,15],'door':[17,25]},'labels':[['贾政书房',20,11]],'props':[('main-hall',20,19,1),('tea-table',19,13,.9),('garden-tree',10,23,1),('garden-tree',29,20,1)]}
}
scenes.update(json.loads((ROOT/'design/prequel-maps.json').read_text()))
# Street staging follows the same east/west convention as the estate overview.
scenes['capital'].update(zones=[[3,23,34,12],[3,12,14,11],[23,12,14,11]],anchors={'street_west':[35,29],'ning_gate':[30,25],'rong_gate':[14,25],'west_corner':[4,23],'outside':[4,32]},labels=[['宁国府 · 东',30,18],['荣国府 · 西',14,18],['西墙角门',4,23],['宁荣街',19,30]],props=[('rongxi-hall',30,22,.9),('rongxi-hall',14,22,1),('west-wall-gate',4,23,.55),('garden-tree',36,21,1.1)])
scenes['capital']['props'][0]=('manor-main-gate',30,22,1)
scenes['capital']['props'][1]=('manor-main-gate',14,22,1.2)
scenes['east']['anchors']['east_gate']=[24,28]
scenes['east']['labels'][0]=['南墙黑油大门',24,28]
scenes['east']['labels'][1]=['三层仪门',17,18]
scenes['east']['props'].append(('black-oil-gate',24,28,.6))
manifest_path=ROOT/'public/assets/rongguo/manifest.json';assets=json.loads(manifest_path.read_text())['assets']
ts=json.loads((ROOT/'maps/rongguo-art.tsj').read_text());gids={next(p['value'] for p in t['properties'] if p['name']=='asset'):t['id']+1 for t in ts['tiles']}
for key,s in scenes.items():
 counter=1
 def obj(name,c,r,**kwargs):
  global counter
  o={'id':counter,'name':name,'x':c*64,'y':r*64,'width':0,'height':0,'rotation':0,'visible':True};counter+=1;o.update(kwargs);return o
 zones=[obj(f'A{i} {s["name"]}',c,r,width=w*64,height=h*64) for i,(c,r,w,h) in enumerate(s['zones'])]
 anchors=[obj(n,c+.5,r+.5,point=True) for n,(c,r) in s['anchors'].items()]
 paths=[obj('场景动线',0,0,properties=[{'name':'route_id','value':'main','type':'string'},{'name':'anchor_ids','value':','.join(s['anchors']),'type':'string'}])]
 # All named points are joined by explicit corridors; A* still operates on the grid.
 art=[]
 for asset,c,r,scale in s['props']:
  if asset not in assets:continue
  a=assets[asset];x=(c-r)*64+(a['width']/2-a['anchor'][0])*scale;y=(c+r+1)*32+(a['height']-a['anchor'][1])*scale
  art.append(obj(asset,0,0,x=y+x/2,y=y-x/2,gid=gids[asset],width=a['width']*scale,height=a['height']*scale,type='art',properties=[{'name':'asset','value':asset,'type':'string'},{'name':'visibility','value':'exterior' if asset in ('main-hall','rongxi-hall') and s['theme']!='street' else 'always','type':'string'},{'name':'depthOffset','value':-400 if asset=='canopy-bed' else 0,'type':'float'}]))
 footprints=[]
 for asset,c,r,scale in s['props']:
  if asset in ('wood-screen','dining-table','tea-table','canopy-bed','garden-rock') and [c,r] not in list(s['anchors'].values()):
   footprints.append(obj(asset,c,r,width=64,height=64,type='collision'))
 layers=[]
 for n,entries in [('PlanZones',zones),('PlanBlockers',[]),('Anchors',anchors),('Routes',paths),('Art',art),('ArtFootprints',footprints)]:layers.append({'id':len(layers)+1,'name':n,'type':'objectgroup','x':0,'y':0,'opacity':1,'visible':n=='Art','draworder':'topdown','objects':entries})
 labels=[obj(label,c+.5,r+.5,point=True) for label,c,r in s['labels']];layers.append({'id':len(layers)+1,'name':'Labels','type':'objectgroup','x':0,'y':0,'opacity':1,'visible':False,'objects':labels})
 tmj={'type':'map','version':'1.10','orientation':'isometric','renderorder':'right-down','width':40,'height':40,'tilewidth':128,'tileheight':64,'infinite':False,'layers':layers,'tilesets':[{'firstgid':1,'source':'rongguo-art.tsj'}],'nextlayerid':len(layers)+1,'nextobjectid':counter,'properties':[{'name':'sceneId','type':'string','value':key},{'name':'title','type':'string','value':s['name']},{'name':'theme','type':'string','value':s['theme']}]}
 (ROOT/f'maps/{key}.tmj').write_text(json.dumps(tmj,ensure_ascii=False,indent=2)+'\n')
entry=ROOT/'maps/rongguo-entry.tmj';d=json.loads(entry.read_text());d['properties']=[p for p in d['properties'] if p['name'] not in ('sceneId','title','theme')]+[{'name':'sceneId','type':'string','value':'entry'},{'name':'title','type':'string','value':'荣国府 · 贾母院'},{'name':'theme','type':'string','value':'garden'}]
entry.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(f'Built {len(scenes)} chapter maps + existing entry map')
