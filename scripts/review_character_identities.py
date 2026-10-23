"""Export human-readable review sheets; --record stores the reviewed asset list.
Run --record only after inspecting every final face and pair, not at generation time.
"""
from pathlib import Path
import argparse,json,math
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'art/identity';plan=json.loads((BASE/'character-designs.json').read_text());characters=plan['characters']
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',23);small=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',15)
sheet=Image.new('RGB',(1440,math.ceil(len(characters)/6)*260),'#eee8dc');d=ImageDraw.Draw(sheet)
for i,c in enumerate(characters):
 x=i%6*240;y=i//6*260;key=c['id']+'-portrait';directory=BASE/key
 if not (directory/'final.png').exists():continue
 box=json.loads((directory/'geometry.json').read_text())['box'];w=box[2]-box[0];h=box[3]-box[1];im=Image.open(directory/'final.png').convert('RGBA').crop((round(box[0]-w*.15),round(box[1]-h*.2),round(box[2]+w*.15),round(box[3]+h*.05)));scale=min(200/im.width,205/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);sheet.paste(im,(x+(240-im.width)//2,y+8+(205-im.height)//2),im);d.text((x+120,y+228),c['name'],font=font,fill='#405343',anchor='mm')
sheet.save(BASE/'cast-faces.png')
sheet.crop((0,0,1440,520)).save(BASE/'principal-faces.png')
# Main face comparison at a consistent face height, no clothing/hairstyle cues.
chosen=['daiyu','baoyu','feng','yingchun','tanchun','wang','xing','yucun','ruhai','zhang','leng','guide']
comparison=Image.new('RGB',(1440,math.ceil(len(chosen)/4)*310),'#eee8dc');d=ImageDraw.Draw(comparison)
for i,id in enumerate(chosen):
 c=next(c for c in characters if c['id']==id);key=id+'-portrait';directory=BASE/key
 if not (directory/'final.png').exists():continue
 x=i%4*360;y=i//4*310;box=json.loads((directory/'geometry.json').read_text())['box']
 for j,path in enumerate([BASE/'originals'/f'{key}.png',directory/'final.png']):
  im=Image.open(path).convert('RGBA').crop(box);bg=Image.new('RGB',im.size,'#eee8dc');bg.paste(im,mask=im.getchannel('A'));bg=ImageOps.grayscale(bg).convert('RGB');scale=min(160/bg.width,210/bg.height);bg=bg.resize((round(bg.width*scale),round(bg.height*scale)),Image.Resampling.LANCZOS);comparison.paste(bg,(x+j*180+(180-bg.width)//2,y+40+(210-bg.height)//2));d.text((x+j*180+90,y+18),'原图' if j==0 else '重绘',font=small,fill='#64715f',anchor='mm')
 d.text((x+180,y+281),c['name'],font=font,fill='#405343',anchor='mm')
comparison.save(BASE/'main-face-comparison.png')
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
if args.record:
 records={}
 for c in characters:
  for kind in ['portrait','chibi']:
   key=c['id']+'-'+kind;directory=BASE/key
   for filename in ['final.png','request.json','geometry.json','mask-native.png','edit-01.png']:assert (directory/filename).exists(),(key,filename)
   request=json.loads((directory/'request.json').read_text());geo=json.loads((directory/'geometry.json').read_text())
   records[key]={'character':c['id'],'features':c['features'],'seed':request['seed'],'faceBox':geo['box'],'original':str((BASE/'originals'/f'{key}.png').relative_to(ROOT)),'final':str((directory/'final.png').relative_to(ROOT)),'mask':str((directory/'mask-native.png').relative_to(ROOT)),'request':str((directory/'request.json').relative_to(ROOT)),'portraitReference':f"art/identity/{c['id']}-portrait/reference.png" if kind=='chibi' else None}
 (BASE/'approved.json').write_text(json.dumps({'version':1,'review':'Visual review of gray face-only comparisons, color full cast, and portrait/chibi pairs. All 33 identities / 66 images.','assets':records},ensure_ascii=False,indent=2)+'\n')
 print(f'Recorded {len(records)} reviewed face assets')
