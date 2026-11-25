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
 # 第二十三回三个新角色：金钏儿、彩云、贾芹。
 # 自动检测在两个 Q 版上完全失败（caiyun-chibi / jia_qin-chibi 报「no face
 # candidate found」——脸太小，肤色连通块达不到阈值）；jinyuan-chibi 虽检测出
 # 框，但下沿落到 70（已经压进衣领），与既有 Q 版「下沿在 59~60 即下巴线」
 # 的规范不符。三个 Q 版由肤色分带量化 + 目视重标：上沿在发际线略下、
 # 下沿在下巴线、左右含双耳。三张立绘的自动框经目视核对无误，登记在此
 # 是为了让重跑不把它们打回自动值。
 'jinyuan-portrait':[78,22,128,72],
 'jinyuan-chibi':[13,27,62,62],
 'caiyun-portrait':[46,38,88,82],
 'caiyun-chibi':[9,30,59,64],
 'jia_qin-portrait':[63,42,107,82],
 'jia_qin-chibi':[7,30,57,64],
 # 第二十四回的八个新角色：贾芸、小红、倪二、卜世仁、香菱、秋纹、碧痕、鸳鸯。
 # 这一批的自动检测完全不可用，已全部改为「Vision 语义地标 + 目视」标注：
 #
 # · 立绘：肤色连通块在 xiaohong（框到躯干）、ni_er（络腮胡）、qiuwen（衣领）
 #   上都抓错了地方。改用 scripts/detect_face_landmarks.swift 取 Apple Vision
 #   的眼/鼻/嘴地标，用「嘴 y − 眼中点 y」当尺度，把标定关系从第二十三回
 #   已审核的三张立绘上量出来（框高 ≈ 2.18×眼嘴距、框宽 ≈ 0.87×Vision 人脸框宽、
 #   下沿 ≈ 嘴下 0.35×眼嘴距），再套到这八张上，最后逐张目视核对修正。
 # · Q 版：Vision 的检测器在六张上直接返回 NOFACE（Q 版大头身画风不在拟合
 #   范围，与第二十三回记录一致），ni_er / bu_shi_ren 两张虽检出也把胡须和
 #   白发算进了脸。八张全部按既有 Q 版规范手��标注：上沿在发际线略下、
 #   下沿在下巴线、左右含双耳，框高 33~35、中心 x 对齐图宽中点。
 'jia_yun-portrait':[44,34,91,82],
 'jia_yun-chibi':[3,19,39,52],
 'xiaohong-portrait':[60,37,104,80],
 # 小红的 Q 版刘海压得很低：上沿 25 会切进头发，下沿 59 会切掉嘴。改为
 # 上沿落到额头（27）、下沿落到下巴（62）。
 'xiaohong-chibi':[6,27,48,62],
 'ni_er-portrait':[84,19,135,66],
 'ni_er-chibi':[16,18,62,52],
 'bu_shi_ren-portrait':[53,24,108,83],
 # 卜世仁的 Q 版下沿在 52 压住了嘴：他这张脸画得长，肤色一直延伸到 y≈68
 # 才收成下巴线，与其余几张（下巴在 52~58）不同。框改为把整张脸收进去。
 'bu_shi_ren-chibi':[2,19,46,66],
 'xiangling-portrait':[47,38,93,82],
 'xiangling-chibi':[10,23,58,58],
 'qiuwen-portrait':[86,45,136,92],
 # 秋纹的 Q 版双髻压得很低：额头在 30，下巴在 63（肤色分布实测）。
 'qiuwen-chibi':[8,30,56,63],
 'bihen-portrait':[64,34,107,73],
 'bihen-chibi':[12,22,56,55],
 'yuan_yang-portrait':[51,46,95,89],
 'yuan_yang-chibi':[7,25,50,58],
 # 贾兰的两张是自动检测产出的值，重跑时会在 1~5 像素上抖动。它们没有经
 # 人工裁决，但既然已经落库并被 manifest 引用，钉在这里可以让重跑保持稳定，
 # 免得每次重建 manifest 都带着一次无意义的 diff。
 'jia_lan-portrait':[152,45,250,158],
 'jia_lan-chibi':[24,16,83,60],
 # 第二十五回两个新角色：马道婆、彩霞。底本无外貌描写，均为设计推定形象。
 # 立绘的肤色连通块自动框把整个上身都算进去（下沿到 312），完全不可用；
 # 改用 3 倍网格放大目视：上沿在额头/发际线略下、下沿在下巴与衣领之间、
 # 左右贴脸颊。Q 版按既有惯例上沿发际线下、下沿下巴线。
 'ma_dao_po-portrait':[82,30,130,80],
 'ma_dao_po-chibi':[8,17,54,51],
 'cai_xia-portrait':[64,28,112,82],
 'cai_xia-chibi':[7,27,49,53],
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
