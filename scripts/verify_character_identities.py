#!/usr/bin/env python3
"""Check paired identity coverage and preserve original Tiled placement contract."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'art/identity';plan=json.loads((base/'character-designs.json').read_text());approved=json.loads((base/'approved.json').read_text())['assets'];manifest=json.loads((ROOT/'public/assets/rongguo/manifest.json').read_text())['assets'];baseline=json.loads((base/'originals/manifest.json').read_text())['assets']
expected={c['id']+'-'+kind for c in plan['characters'] for kind in ['portrait','chibi']}
assert set(approved)==expected
reports=[]
for key in sorted(expected):
 record=approved[key];original=Image.open(ROOT/record['original']).convert('RGBA');final=Image.open(ROOT/record['final']).convert('RGBA');runtime=Image.open(ROOT/('public'+manifest[key]['image'])).convert('RGBA');mask=np.asarray(Image.open(ROOT/record['mask']))
 assert original.size==final.size==runtime.size,(key,'dimensions')
 old=np.asarray(original);new=np.asarray(final)
 assert np.array_equal(old[mask==0],new[mask==0]),(key,'changed outside face mask')
 assert np.array_equal(new,np.asarray(runtime)),(key,'runtime is stale')
 assert manifest[key]['anchor']==baseline[key]['anchor'],(key,'ground anchor changed')
 assert manifest[key]['width']==baseline[key]['width'] and manifest[key]['height']==baseline[key]['height']
 assert manifest[key]['identity']['character']==key.rsplit('-',1)[0]
 assert manifest[key]['identity']['faceBox']==record['faceBox']
 assert (ROOT/record['request']).exists()
 changed=(old!=new).any(axis=2);assert changed.any(),(key,'no facial change')
 # A wide transparent halo is not a valid cutout: check newly added opacity.
 added=(new[:,:,3]>240)&(old[:,:,3]==0)
 if added.any():
  pale=new[:,:,:3].min(axis=2)>245
  assert (added&pale).sum()<max(8,added.sum()*.2),(key,'opaque white halo')
 reports.append({'asset':key,'pixelsChangedInMask':int(changed.sum()),'outsideMaskIdentical':True,'dimensionsPreserved':True,'anchorPreserved':True})
assert len({c['prompt'] for c in plan['characters']})==len(plan['characters'])
(base/'verification.json').write_text(json.dumps({'assets':len(reports),'checks':reports},ensure_ascii=False,indent=2)+'\n')
print(f'Passed: {len(plan["characters"])} paired identities / {len(reports)} images; runtime matches reviewed art, mask exterior RGBA unchanged, dimensions and Tiled anchors preserved. Facial distinctiveness is reviewed visually, not inferred from pixel differences.')
