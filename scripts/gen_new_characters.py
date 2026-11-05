#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate portrait + chibi for the 6 new chapter-8/9 characters.

Pipeline per character/kind:
  qwen21 t2i  -> art/source/{id}-{kind}_s{seed}-01.png   (white-bg ink bust)
  qwen21 bg-removal -> art/matted/{id}-{kind}_s{seed}-sam.png (transparent)
Serial, resumable (skips files already present). Submits to the ComfyUI server.
"""
import json, subprocess, sys, shutil, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / '.local-tools/local-image-studio/scripts/image_studio.py'
SRC = ROOT / 'art/source'; MAT = ROOT / 'art/matted'
SRC.mkdir(parents=True, exist_ok=True); MAT.mkdir(parents=True, exist_ok=True)
PY = sys.executable
PLAN = json.loads((ROOT / 'art/identity/character-designs.json').read_text())
byid = {c['id']: c for c in PLAN['characters']}

CHARS = ['ying_er', 'qin_zhong', 'jia_rui', 'jin_rong', 'ming_yan', 'li_gui']

PORTRAIT_STYLE = (
    "Chinese ink-and-wash hand-painted illustration, delicate brush lines, soft natural skin tones, "
    "a FULL-BODY standing figure from head to feet, traditional Qing-dynasty Han clothing with "
    "flowing long sleeves and a long skirt or robe, standing pose with feet visible at the bottom, "
    "slightly turned toward the viewer, gentle studio lighting. Pure white background, "
    "no text, no signature, no watermark. Game dialogue portrait.")
CHIBI_STYLE = (
    "Chinese ink-and-wash hand-painted cute chibi character, big-head small-body proportion, "
    "simplified brushwork, traditional Qing-dynasty clothing, full tiny body. Pure white background, "
    "no text, no signature, no watermark. Game map icon.")

def run(cmd):
    print('$', ' '.join(str(c) for c in cmd), flush=True)
    r = subprocess.run([PY, str(CLI)] + cmd, cwd=ROOT)
    return r.returncode == 0

def latest(out_dir, prefix):
    cands = sorted(glob.glob(str(out_dir / f'{prefix}*')), key=lambda p: Path(p).stat().st_mtime)
    cands = [c for c in cands if c.lower().endswith('.png')]
    return Path(cands[-1]) if cands else None

def gen_one(cid, kind):
    c = byid[cid]
    seed = c['seed'] + (1 if kind == 'chibi' else 0)
    stem = f'{cid}-{kind}_s{seed}'
    src = SRC / f'{stem}-01.png'
    mat = MAT / f'{stem}-sam.png'
    face = c['prompt']
    if kind == 'portrait':
        prompt = f"{face}. {PORTRAIT_STYLE}"
        w, h = 768, 1152
    else:
        prompt = f"{face}. {CHIBI_STYLE}"
        w, h = 768, 1024
    if not src.exists():
        tmp = ROOT / 'art/tmp_gen' / cid; tmp.mkdir(parents=True, exist_ok=True)
        if not run(['qwen21', '--variant', 't2i', '--prompt', prompt, '--seed', str(seed),
                    '--steps', '30', '--width', str(w), '--height', str(h),
                    '--name', f'{cid}-{kind}', '--out', str(tmp),
                    '--max-queue-depth', '1', '--poll-timeout', '1800']):
            print('T2I FAILED', cid, kind); return False
        got = latest(tmp, f'{cid}-{kind}')
        if not got: print('NO OUTPUT', cid, kind); return False
        shutil.copy2(got, src); print('saved source', src.name)
    if not mat.exists():
        tmp2 = ROOT / 'art/tmp_gen' / f'{cid}-{kind}-matte'; tmp2.mkdir(parents=True, exist_ok=True)
        if not run(['qwen21', '--variant', 'bg-removal', '--image', str(src),
                    '--name', f'{cid}-{kind}', '--out', str(tmp2),
                    '--max-queue-depth', '1', '--poll-timeout', '1800']):
            print('BG-REMOVAL FAILED', cid, kind); return False
        got = latest(tmp2, f'{cid}-{kind}')
        if not got: print('NO MATTE', cid, kind); return False
        shutil.copy2(got, mat); print('saved matte', mat.name)
    print('OK', cid, kind); return True

if __name__ == '__main__':
    for cid in CHARS:
        for kind in ('portrait', 'chibi'):
            gen_one(cid, kind)
    print('ALL DONE')
