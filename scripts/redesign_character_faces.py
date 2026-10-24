#!/usr/bin/env python3
"""Serial, resumable Qwen facial identity edits. Never alters archived originals.
Use managed Python (Pillow/numpy). GPU submission is delegated to local-image-studio.
"""
import argparse, json, math, shutil, subprocess, sys, time, hashlib
from urllib.request import urlopen
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'art/identity'
PLAN=json.loads((BASE/'character-designs.json').read_text())
BOXES=json.loads((BASE/'auto-face-boxes.json').read_text())
BOXES.update({'baoyu-portrait':[90,140,250,285],'xiren-chibi':[16,12,35,34],'fengshi-chibi':[18,11,36,34]})
PYTHON=sys.executable
CLI=ROOT/'.local-tools/local-image-studio/scripts/image_studio.py'

def prepare(key):
 directory=BASE/key;directory.mkdir(parents=True,exist_ok=True)
 original=BASE/'originals'/f'{key}.png';original.parent.mkdir(exist_ok=True)
 if not original.exists():shutil.copy2(ROOT/f'public/assets/rongguo/{key}.png',original)
 im=Image.open(original).convert('RGBA');x0,y0,x1,y1=BOXES[key];w=x1-x0;h=y1-y0
 # Square context includes hair/head, and keeps original feature coordinates in mask.
 side=math.ceil(max(w*1.8,h*1.6));cx=(x0+x1)/2;cy=(y0+y1)/2
 crop=[round(cx-side/2),round(cy-side/2),round(cx+side/2),round(cy+side/2)]
 # A crop that leaves the canvas pads with black, which silently destroys the head.
 # Shrink the context until it fits inside the canvas; the face box must stay whole.
 iw,ih=im.size
 while (crop[0]<0 or crop[1]<0 or crop[2]>iw or crop[3]>ih) and side>max(x1-x0,y1-y0):
  side=int(side*.9);cx=min(max(cx,side/2),max(side/2,iw-side/2));cy=min(max(cy,side/2),max(side/2,ih-side/2))
  crop=[round(cx-side/2),round(cy-side/2),round(cx+side/2),round(cy+side/2)]
 if crop[0]<0 or crop[1]<0 or crop[2]>iw or crop[3]>ih:
  raise ValueError(f'{key}: face box {BOXES[key]} does not fit inside image {im.size}')
 if not (x0>=crop[0] and y0>=crop[1] and x1<=crop[2] and y1<=crop[3]):
  raise ValueError(f'{key}: face box {BOXES[key]} falls outside its crop {crop}')
 face=im.crop(crop);white=Image.new('RGB',face.size,'white');white.paste(face,mask=face.getchannel('A'));white.resize((512,512),Image.Resampling.LANCZOS).save(directory/'input.png')
 # Face outline may change inside this bounded ellipse; body and placement stay exact.
 bound=Image.new('L',im.size);ImageDraw.Draw(bound).ellipse((x0-w*.20,y0-h*.04,x1+w*.20,y1+h*.03),fill=255)
 mask=bound.filter(ImageFilter.GaussianBlur(1.1 if im.height>200 else .45))
 # Feather has finite support; all pixels outside this mask are preserved.
 m=np.asarray(mask).copy();m[m<5]=0;mask=Image.fromarray(m);mask.save(directory/'mask-native.png')
 mask.crop(crop).resize((512,512),Image.Resampling.LANCZOS).save(directory/'mask.png')
 (directory/'geometry.json').write_text(json.dumps({'box':BOXES[key],'crop':crop,'size':list(im.size),'originalSha256':hashlib.sha256(original.read_bytes()).hexdigest()},indent=2))
 return directory

def composite(key):
 directory=BASE/key;geo=json.loads((directory/'geometry.json').read_text());im=Image.open(BASE/'originals'/f'{key}.png').convert('RGBA');crop=geo['crop']
 edit=Image.open(directory/'edit-01.png').convert('RGB').resize((crop[2]-crop[0],crop[3]-crop[1]),Image.Resampling.LANCZOS)
 layer=Image.new('RGB',im.size,'white');layer.paste(edit,(crop[0],crop[1]));mask=Image.open(directory/'mask-native.png')
 output=Image.composite(layer,im.convert('RGB'),mask).convert('RGBA');
 # Recover only newly painted face-edge alpha from the white editing backdrop.
 rgb=np.asarray(edit).astype(int);eligible=(rgb.min(axis=2)>205)&((rgb.max(axis=2)-rgb.min(axis=2))<30)
 from collections import deque
 bg=np.zeros(eligible.shape,dtype=bool);q=deque()
 for yy,xx in [(yy,xx) for yy in range(edit.height) for xx in (0,edit.width-1)]+[(yy,xx) for xx in range(edit.width) for yy in (0,edit.height-1)]:
  if eligible[yy,xx] and not bg[yy,xx]:bg[yy,xx]=True;q.append((yy,xx))
 while q:
  yy,xx=q.popleft()
  for ny,nx in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
   if 0<=ny<edit.height and 0<=nx<edit.width and eligible[ny,nx] and not bg[ny,nx]:bg[ny,nx]=True;q.append((ny,nx))
 cut=Image.fromarray((~bg).astype('uint8')*255).filter(ImageFilter.GaussianBlur(.35));newalpha=Image.new('L',im.size);newalpha.paste(cut,(crop[0],crop[1]))
 alpha=Image.composite(newalpha,im.getchannel('A'),mask)
 aa=np.asarray(alpha).copy();oldalpha=np.asarray(im.getchannel('A'));inside=np.asarray(mask)>0;paint=np.asarray(layer)
 # Generated near-white paper must not become opaque outside the old silhouette.
 aa[inside&(oldalpha==0)&(paint.min(axis=2)>245)]=0
 aa[inside&(aa>200)]=255;aa[inside&(aa<32)]=0
 output.putalpha(Image.fromarray(aa));output.save(directory/'final.png')
 # Face-only reference, no clothing. Chibi gets the paired portrait identity.
 x0,y0,x1,y1=BOXES[key];w=x1-x0;h=y1-y0
 ref=output.crop((round(x0-w*.2),round(y0-h*.15),round(x1+w*.2),round(y1+h*.1)));bg=Image.new('RGB',ref.size,'white');bg.paste(ref,mask=ref.getchannel('A'));bg.thumbnail((512,512));bg.save(directory/'reference.png')

def generate(character,kind):
 key=character['id']+'-'+kind;directory=prepare(key)
 if not (directory/'edit-01.png').exists():
  prompt=(f"Redesign ONLY the facial features of the person in <image1>. The new distinctive identity is: {character['prompt']}. "
   "Keep the head center and angle, hairline, hairstyle, ornaments, clothing and white background. You MUST change the original facial outline and facial proportions to match the specified new identity; do not retain the original pointed doll face when a broad or square face is requested. "
   "Paint the new facial geometry and expression in the SAME delicate Chinese ink and watercolor hand-painted illustration style as image1, with subtle natural skin tones and fine brush lines. "
   "Make the specified face shape, eye shape and spacing, eyebrows, nose and lips clearly visible and character-specific. Emphasize the characteristic facial proportions enough to read in a small game portrait. Use natural eyes and lips, not glamorous makeup, dark eyeliner or a generic beauty filter. Avoid generic identical doll faces. This is a single head detail crop, not a character sheet. No text.")
  cmd=[PYTHON,str(CLI),'qwen21','--variant','edit','--server',PLAN['server'],'--image',str(directory/'input.png')]
  if kind=='chibi':
   cmd+=['--image',str(BASE/(character['id']+'-portrait')/'reference.png')]
   prompt+=' The face in <image2> is the approved SAME CHARACTER identity: transfer its distinctive eyebrow/eye shapes, nose, mouth, age and temperament into the chibi in <image1>, keeping image1 head scale and cute simplified brushwork. Keep eyes readable at tiny map scale; do not copy realistic portrait proportions.'
  seed=character['seed']+(kind=='chibi')
  (directory/'request.json').write_text(json.dumps({'id':key,'seed':seed,'features':character['features'],'prompt':prompt,'model':PLAN['model'],'steps':30},ensure_ascii=False,indent=2))
  cmd+=['--prompt',prompt,'--steps','30','--seed',str(seed),'--name','edit','--out',str(directory),'--keep-old','--max-queue-depth','0','--poll-timeout','1800']
  print(f"GENERATING {key}",flush=True)
  waited=0
  while True:
   with urlopen(PLAN['server']+'/queue',timeout=15) as response:queue=json.load(response)
   depth=len(queue.get('queue_running',[]))+len(queue.get('queue_pending',[]))
   if not depth:break
   if waited%30==0:print(f'Waiting for existing GPU work: {depth} jobs',flush=True)
   if waited>=1800:raise TimeoutError('ComfyUI busy; rerun to resume')
   time.sleep(5);waited+=5
  subprocess.run(cmd,cwd=ROOT,check=True)
 composite(key);print(f'READY {key}',flush=True)

def review():
 chars=[c for c in PLAN['characters'] if (BASE/(c['id']+'-portrait')/'final.png').exists()]
 sheet=Image.new('RGB',(1200,math.ceil(len(chars)/4)*290),'#e9e4d9');d=ImageDraw.Draw(sheet)
 for i,c in enumerate(chars):
  x=i%4*300;y=i//4*290;key=c['id']+'-portrait';box=BOXES[key]
  for j,path in enumerate([BASE/'originals'/f'{key}.png',BASE/key/'final.png']):
   im=Image.open(path).convert('RGBA').crop(box);bg=Image.new('RGB',im.size,'#e9e4d9');bg.paste(im,mask=im.getchannel('A'));im=ImageOps.grayscale(bg).convert('RGB');im.thumbnail((130,220));sheet.paste(im,(x+10+j*145+(130-im.width)//2,y+25+(220-im.height)//2));d.text((x+15+j*145,y+5),'BEFORE' if j==0 else 'AFTER',fill='#555555')
  d.text((x+10,y+260),c['id'],fill='black')
 sheet.save(BASE/'face-comparison.png')
 # Each pair at a readable head-detail scale, final color face vs final chibi face.
 sheet=Image.new('RGB',(1200,math.ceil(len(chars)/6)*230),'#ece6d8');d=ImageDraw.Draw(sheet)
 for i,c in enumerate(chars):
  x=i%6*200;y=i//6*230
  for j,kind in enumerate(['portrait','chibi']):
   key=c['id']+'-'+kind;path=BASE/key/'final.png'
   if not path.exists():continue
   im=Image.open(path).convert('RGBA').crop(BOXES[key]);im.thumbnail((90,180));im=im.resize((round(im.width*min(90/im.width,180/im.height)),round(im.height*min(90/im.width,180/im.height))),Image.Resampling.NEAREST if kind=='chibi' else Image.Resampling.LANCZOS)
   sheet.paste(im,(x+j*100+(100-im.width)//2,y+20+(180-im.height)//2),im)
  d.text((x+5,y+205),c['id'],fill='black')
 sheet.save(BASE/'paired-identities.png')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ids',nargs='*');p.add_argument('--review',action='store_true');p.add_argument('--kind',choices=['portrait','chibi','both'],default='both');args=p.parse_args()
 if not args.review:
  for c in PLAN['characters']:
   if args.ids and c['id'] not in args.ids:continue
   for kind in (['portrait','chibi'] if args.kind=='both' else [args.kind]):generate(c,kind)
   review()
 review()
