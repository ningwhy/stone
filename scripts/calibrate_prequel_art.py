"""Explicit anchors/cutouts for the prequel's inspected imagery."""
import json
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];p=R/'art/calibration.json';d=json.loads(p.read_text());ids=set(json.loads((R/'art/prequel-art-ids.json').read_text()))
retained={
 'monk-chibi':[[[550,477],[555,469],[565,466],[573,461],[585,463],[591,468],[591,480],[578,489],[569,495],[558,489]]],
 'oldmonk-portrait':[[[341,566],[350,562],[497,677],[513,661],[521,660],[522,679],[510,695],[482,699],[463,688],[464,680],[479,672],[345,575]]],
 'monk-portrait':[[[250,279],[260,275],[271,283],[277,299],[270,306],[257,305],[249,294]]],
 'taoist-portrait':[[[236,190],[245,194],[244,221],[229,236],[221,235],[234,219]],[[239,218],[246,223],[246,258],[256,274],[254,292],[244,309],[251,351],[255,387],[245,396],[239,354],[236,310],[241,291],[243,269]],[[246,426],[256,426],[280,964],[270,967]]],
 'taoist-chibi':[[[565,303],[573,304],[577,311],[568,324],[563,346],[557,376],[548,400],[540,496],[532,496],[538,398],[548,374],[553,343]],[[529,529],[540,531],[501,904],[489,906]]],
 'kongkong-portrait':[[[536,498],[547,498],[551,505],[648,510],[659,497],[669,497],[672,502],[558,695],[466,698],[459,692],[482,608]]],
 'kongkong-chibi':[[[505,483],[517,483],[580,492],[586,477],[594,476],[598,481],[530,600],[505,610],[449,605],[444,600]]]
}
for a in d['assets']:
 if a['id'] not in ids:continue
 key=a['id'];
 if key=='estate-ruins':a.update(sourceId='estate-ruins-v2',seed=10230402)
 if key in retained:a['restorePolygons']=retained[key]
 if key=='crimson-pearl':a['solidAlphaThreshold']=70
 if key=='taoist-chibi':a['solidAlphaThreshold']=160
 im=Image.open(R/f"art/matted/{a.get('sourceId',key)}_s{a['seed']}-sam.png").convert('RGBA');ys,xs=np.where(np.asarray(im)[:,:,3]>120);top,bottom=int(ys.min()),int(ys.max())
 if key.endswith('-portrait'):
  # Sources occasionally include a full body despite the requested portrait.
  # A shared head-to-upper-body crop makes faces comparable in the fixed dialogue frame.
  right,left=int(xs.max()),int(xs.min());h=bottom-top;w=right-left
  if h/max(w,1)>1.65:
   end=round(top+h*.67);a['clipRect']=[0,0,im.width,end];a['anchor'][1]=end
 if key=='manor-main-gate':a.update(anchor=[553,834],width=650,mirror=True,baseSlope=-.3,targetSlope=-.5)
 if key=='estate-ruins':a.update(anchor=[float(xs.min()+xs.max())/2,bottom-5])
 if key=='west-wall-gate':a.update(anchor=[560,805],width=390)
 if key=='black-oil-gate':
  a.update(anchor=[529,836],width=450,mirror=True,clearPolygons=[[[495,586],[561,559],[561,780],[495,806]]])
 if key=='spirit-stone':a.update(width=260,anchor=[(xs.min()+xs.max())/2,bottom-8])
 if key=='crimson-pearl':a.update(width=200,anchor=[(xs.min()+xs.max())/2,bottom-5])
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('Prequel head crops and gate threshold anchors calibrated.')
