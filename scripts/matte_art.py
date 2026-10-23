#!/usr/bin/env python3
"""Run only the SAM + SDMatte ancestors of the supplied skill's save nodes.
The template's unrelated BiRefNet preview branch is incompatible with this server.
"""
import importlib.util,json,time,argparse
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('studio',ROOT/'.local-tools/local-image-studio/scripts/image_studio.py')
studio=importlib.util.module_from_spec(spec);spec.loader.exec_module(studio)
plan=json.loads((ROOT/'art/generation-plan.json').read_text())
p=argparse.ArgumentParser();p.add_argument('--only',nargs='+');args=p.parse_args()
out=ROOT/'art/matted';out.mkdir(exist_ok=True)
for job in plan['jobs']:
 if job['id']=='courtyard-concept' or args.only and job['id'] not in args.only:continue
 name=f"{job['id']}_s{job['seed']}"
 if (out/f'{name}-sdmatte.png').exists():continue
 while True:
  with urlopen(plan['server']+'/queue',timeout=20) as r:q=json.load(r)
  if not q.get('queue_running') and not q.get('queue_pending'):break
  print('Waiting for ComfyUI queue',flush=True);time.sleep(10)
 wf=studio.load_reference_workflow('matte-workflow.json')
 needed=set()
 def visit(k):
  if k in needed:return
  needed.add(k)
  for v in wf[k]['inputs'].values():
   if isinstance(v,list) and len(v)==2 and isinstance(v[0],str) and v[0] in wf:visit(v[0])
 visit('209');visit('398');wf={k:v for k,v in wf.items() if k in needed}
 wf['122']['inputs']['image']=studio.upload_image(plan['server'],ROOT/f'art/source/{name}-01.png')
 subject=job.get('subject') or {'garden-tree':'tree','garden-rock':'rock','daiyu-chibi':'girl','daiyu-portrait':'girl'}.get(job['id'],'building')
 wf['399']['inputs']['text']=subject
 for k in ['209','398']:wf[k]['inputs']['filename_prefix']=f'rongguo/matte_{name}_{k}'
 pid=studio.queue_prompt(plan['server'],wf);print(f'Matting {name}: {pid}',flush=True)
 entry=studio.poll_history(plan['server'],pid,timeout=900)
 for node,label in [('209','sdmatte'),('398','sam')]:
  files=studio.collect_output_files(entry,save_nodes=[node])
  if not files:raise RuntimeError(f'No output for {node}')
  studio.download_output(plan['server'],files[0],out/f'{name}-{label}.png',keep_old=True)
 (out/f'{name}.json').write_text(json.dumps({'promptId':pid,'subject':subject,'source':f'art/source/{name}-01.png','workflow':wf},ensure_ascii=False,indent=2))
 print(f'Saved {name}',flush=True)
