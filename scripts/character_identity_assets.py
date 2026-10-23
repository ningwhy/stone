"""Apply reviewed face edits after standard geometry calibration.
No GPU calls here. Changing source calibration invalidates the stored face patch.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image

def apply_identity(root:Path,key:str,image:Image.Image,asset:dict):
 approved=root/'art/identity/approved.json'
 if not approved.exists():return image
 records=json.loads(approved.read_text())['assets']
 if key not in records:return image
 record=records[key];original=Image.open(root/record['original']).convert('RGBA')
 if image.size!=original.size or not np.array_equal(np.asarray(image),np.asarray(original)):
  raise ValueError(f'{key}: source calibration changed; review face patch before rebuilding')
 final=Image.open(root/record['final']).convert('RGBA')
 mask=np.asarray(Image.open(root/record['mask']).convert('L'))
 if final.size!=image.size or not np.array_equal(np.asarray(final)[mask==0],np.asarray(original)[mask==0]):
  raise ValueError(f'{key}: face edit changes pixels outside its reviewed mask')
 asset['identity']={k:record[k] for k in ['character','features','seed','faceBox']}
 asset['identity']['revision']=hashlib.sha256((root/record['final']).read_bytes()).hexdigest()[:12]
 asset['identity']['source']=record['request']
 return final
