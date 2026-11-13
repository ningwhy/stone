"""Propose face boxes for review; identity crops use these checked coordinates."""
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import json
ROOT=Path(__file__).resolve().parents[1]
assets=json.loads((ROOT/'public/assets/rongguo/manifest.json').read_text())['assets']
keys=[k for k in assets if k.endswith(('-portrait','-chibi'))]
# Boxes that were corrected by eye during review. The automatic detector cannot be
# trusted for them: the skin-tone mask latches onto hair or a bald scalp instead
# of the face, so a rerun would put back the oversized box that was just fixed.
# Keeping the reviewed value here is what makes rerunning this script safe.
REVIEWED={
 'oldmonk-portrait':[214,5,400,205],
 'ying_er-portrait':[55,20,180,185],
 # 第二十一回翠缕：自动检测把围裙的米白当成肤色，抓到的是腰腹而非脸
 # （框 [0,99,183,312] 横跨半个身子）。真实脸块由上部 30% 区域内的肤色
 # 连通块给出 [55,23,115,108]，已目视核对。
 'cui_lv-portrait':[55,23,115,108],
}
boxes={};out=Image.new('RGB',(1440,((len(keys)+7)//8)*200),'#e6dfce');d=ImageDraw.Draw(out)
for i,key in enumerate(keys):
 im=Image.open(ROOT/('public'+assets[key]['image'])).convert('RGBA');a=np.asarray(im);r,g,b,al=[a[:,:,j].astype(int) for j in range(4)]
 skin=(r>130)&(r-g>7)&(g-b>6)&(r-g<68)&(al>220);skin[int(im.height*.52):]=False
 scale=1 if im.height<200 else 3
 m=np.asarray(Image.fromarray(skin.astype('uint8')*255).resize((im.width//scale,im.height//scale)))>100;seen=np.zeros_like(m);groups=[]
 for y,x in zip(*np.where(m)):
  if seen[y,x]:continue
  q=[(int(x),int(y))];seen[y,x]=True;pts=[]
  while q:
   x0,y0=q.pop();pts.append((x0,y0))
   for xx,yy in ((x0-1,y0),(x0+1,y0),(x0,y0-1),(x0,y0+1)):
    if 0<=yy<m.shape[0] and 0<=xx<m.shape[1] and m[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;q.append((xx,yy))
  if len(pts)>max(6,im.width*im.height/scale**2*.0009) and min(p[1] for p in pts)*scale<im.height*(.34 if scale==1 else .20):groups.append(pts)
 
 if not groups:raise ValueError(key)
 group=max(groups,key=len);xs=[p[0]*scale for p in group];ys=[p[1]*scale for p in group];box=[min(xs),min(ys),max(xs)+scale,max(ys)+scale];boxes[key]=REVIEWED.get(key,box)
 shown=im.copy();ImageDraw.Draw(shown).rectangle(box,outline='red',width=1 if scale==1 else 2);shown.thumbnail((170,165));x=i%8*180;y=i//8*200;out.paste(shown,(x+(180-shown.width)//2,y),shown);d.text((x+5,y+170),key,fill='black')
(ROOT/'art/identity').mkdir(exist_ok=True);(ROOT/'art/identity/auto-face-boxes.json').write_text(json.dumps(boxes,indent=2));out.save(ROOT/'art/identity/face-box-review.png')
