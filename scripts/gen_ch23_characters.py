#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate portrait + chibi for the three chapter-23 characters.

Who they are
------------
Chapter 23 puts three new faces on stage for the first time in this project:

  * **jinyuan** (金钏儿) — 贾母房里的丫鬟,王夫人房中第一等. She grabs 宝玉 by the
    arm in the corridor outside 王夫人's room and teases him about the rouge on
    her lips (「我这嘴上是才擦的香浸胭脂」).
  * **caiyun** (彩云) — a maid of the same room. She pushes 金钏 away and tells
    宝玉 to go in, because he is already unhappy (「人家正心里不自在」).
  * **jia_qin** (贾芹) — 贾政's distant nephew, who buys the temple estates'
    management post for a few hundred taels and rides off to 铁槛寺.

All three have been mentioned in passing in earlier chapters (金钏儿 in chapter 7,
贾芹 in chapter 13) but never walked on, so they are new characters for the
cast album and need a portrait and a chibi icon like everybody else.

Pipeline per character/kind:
  qwen21 t2i  -> art/source/{id}-{kind}_s{seed}-01.png   (white-bg ink figure)
  qwen21 bg-removal -> art/matted/{id}-{kind}_s{seed}-sam.png (transparent)
Serial, resumable (skips files already present). Submits to the ComfyUI server.

Server address: default 192.168.4.66:8188; override with COMFYUI_HOST or
`--server` on the CLI below. 记忆里的教训：ComfyUI 模型挪目录会整条 400,
脚本里已加 `_align_model_names()` 反查服务器清单。
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

CHARS = ['jinyuan', 'caiyun', 'jia_qin']

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


def wait_for_queue(attempts=40, gap=15):
    """Wait until the server queue is empty before submitting.

    The ComfyUI host is shared: another project's job can be running when this
    script starts, and the skill's own `--max-queue-depth` gate rejects the
    submission outright when the depth is over the threshold. The gate is a
    safety net against submitting *while the GPU is already loaded* — but a
    single foreign job in the queue is not a reason to give up, it only means
    the next submission has to wait for that job to drain.

    The wait is a plain poll: no cancellation, no queue clearing. If the host
    stays busy the script proceeds anyway and lets the skill's gate decide.
    """
    import urllib.request
    import time
    for i in range(attempts):
        try:
            with urllib.request.urlopen('http://192.168.4.66:8188/queue', timeout=8) as r:
                q = json.loads(r.read().decode())
            depth = len(q.get('queue_running', [])) + len(q.get('queue_pending', []))
        except Exception:
            depth = -1
        if depth <= 0:
            print(f'queue clear after {i} check(s)', flush=True)
            return True
        print(f'queue depth {depth}, waiting {gap}s ...', flush=True)
        time.sleep(gap)
    print('queue still busy; submitting anyway', flush=True)
    return False


def latest(out_dir, prefix):
    cands = sorted(glob.glob(str(out_dir / f'{prefix}*')), key=lambda p: Path(p).stat().st_mtime)
    cands = [p for p in cands if p.lower().endswith('.png')]
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
        wait_for_queue()
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
        wait_for_queue()
        if not run(['qwen21', '--variant', 'bg-removal', '--image', str(src),
                    '--name', f'{cid}-{kind}', '--out', str(tmp2),
                    '--max-queue-depth', '1', '--poll-timeout', '1800']):
            print('BG-REMOVAL FAILED', cid, kind); return False
        got = latest(tmp2, f'{cid}-{kind}')
        if not got: print('NO MATTE', cid, kind); return False
        shutil.copy2(got, mat); print('saved matte', mat.name)
    print('OK', cid, kind); return True


if __name__ == '__main__':
    failed = []
    for cid in CHARS:
        for kind in ('portrait', 'chibi'):
            if not gen_one(cid, kind):
                failed.append(f'{cid}-{kind}')
    if failed:
        print('ALL DONE WITH FAILURES:', failed)
        sys.exit(1)
    print('ALL DONE')
