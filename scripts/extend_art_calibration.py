#!/usr/bin/env python3
"""Add inspected chapter-three candidates to the persistent calibration contract."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
plan=json.loads((ROOT/'art/generation-plan.json').read_text());path=ROOT/'art/calibration.json';c=json.loads(path.read_text());ids={a['id'] for a in c['assets']}
widths={'sedan-chair':170,'rongxi-hall':1100,'bamboo-gate':430,'wood-screen':190,'dining-table':230,'canopy-bed':300,'river-boat':340,'tea-table':130,'black-oil-gate':450,'west-wall-gate':390,'spirit-stone':260,'crimson-pearl':200,'manor-main-gate':650}
for j in plan['jobs'][8:]:
 key=j['id']
 if key in ids or key in ('baoyu-portrait-v2','estate-ruins-v2'):continue
 p=ROOT/f"art/matted/{key}_s{j['seed']}-sam.png"
 if not p.exists():continue
 im=Image.open(p).convert('RGBA');a=np.asarray(im)[:,:,3];ys,xs=np.where(a>120);l,t,r,b=int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)
 entry={'id':key,'seed':j['seed'],'anchor':[(l+r)/2,b-2]}
 if key.endswith('-chibi'):
  entry['height']=80 if key=='yinglian-chibi' else 98 if key=='xichun-chibi' else 116
  entry['bodyCompress']={'split':round(t+(b-t)*.28),'factor':.64}
 elif key.endswith('-portrait'):
  entry['height']=600
  if key in ('baoyu-portrait','yucun-portrait','ruhai-portrait'):
   bottom=round(t+(b-t)*.65);entry['clipRect']=[0,0,im.width,bottom];entry['anchor'][1]=bottom
 else:
  entry['width']=800 if key.startswith('estate-') else widths[key]
  # Buildings use a front threshold, furniture its central ground contact.
  if key.startswith('estate-'):entry['anchor']=[(l+r)/2,b-5]
  elif key in ('rongxi-hall','bamboo-gate'):entry['anchor']=[im.width*.47,im.height*.81]
  elif key=='canopy-bed':entry['anchor']=[im.width*.5,b-8]
  elif key in ('dining-table','tea-table'):entry['anchor']=[(l+r)/2,b-2]
 c['assets'].append(entry);ids.add(key)
path.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n');print(f'{len(c["assets"])} assets configured')
