#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重生成第 28 回蒋玉菡（jiang_yuhan）的立绘与 Q 版。

为什么重做
----------
第一版把蒋玉菡画成了粉衣女子，这是错的。底本第二十八回明写：

  「只见薛蟠早已在那里久候，还有许多唱曲儿的小厮并唱小旦的蒋玉菡，
    锦香院的妓女云儿。」                                  —— 唱小旦者，与「妓女云儿」并列

  「冯紫英笑道：…你才信了。…你们令表兄弟倒都心实。」     —— 与薛蟠、冯紫英并称「令表兄弟」

  「宝玉见他妩媚温柔，心中十分留恋」                       —— 「妩媚温柔」形容其柔和气质，非指女性

「小旦」是戏曲行当，指**男演员扮演旦角**。蒋玉菡本名为男性优伶，
艺名琪官。第一版提示词只写「a beautiful young MALE opera singer … wearing a
rose-pink silk robe … a small flower pin」，模型按「旦角妆」理解，直接画成女子。

改法
----
1. 提示词显式写明 `a male performer of the female dan role (xiaodan)`，
   并补上「defined jawline / clean-shaven chin / straight dark eyebrows /
   slender straight shoulders and a tall masculine build」等男性骨骼特征，
   把「薄施脂粉」限定为**舞台妆**，而非女性化外形。
2. seed 10237110 → 10237120，避免旧图残留影响。

提示词仍从 art/identity/character-designs.json 读取（唯一权威源）。

Pipeline per character/kind:
  qwen21 t2i  -> art/source/{id}-{kind}_s{seed}-01.png   (white-bg ink figure)
  qwen21 bg-removal -> art/matted/{id}-{kind}_s{seed}-sam.png (transparent)
Serial, resumable (skips files already present). Submits to the ComfyUI server.
"""
import json
import subprocess
import sys
import shutil
import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / '.local-tools/local-image-studio/scripts/image_studio.py'
SRC = ROOT / 'art/source'
MAT = ROOT / 'art/matted'
SRC.mkdir(parents=True, exist_ok=True)
MAT.mkdir(parents=True, exist_ok=True)
PY = sys.executable
PLAN = json.loads((ROOT / 'art/identity/character-designs.json').read_text(encoding='utf-8'))
byid = {c['id']: c for c in PLAN['characters']}

CHARS = ['jiang_yuhan']

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


def wait_for_queue(attempts=60, gap=15):
    """Wait until the server queue is empty before submitting.
    The ComfyUI host is shared: another project's job can be running when this
    script starts. This is a plain poll — no cancellation, no queue clearing.
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
        tmp = ROOT / 'art/tmp_gen' / cid
        tmp.mkdir(parents=True, exist_ok=True)
        wait_for_queue()
        if not run(['qwen21', '--variant', 't2i', '--prompt', prompt, '--seed', str(seed),
                    '--steps', '30', '--width', str(w), '--height', str(h),
                    '--name', f'{cid}-{kind}', '--out', str(tmp),
                    '--max-queue-depth', '1', '--poll-timeout', '1800']):
            print('T2I FAILED', cid, kind)
            return False
        got = latest(tmp, f'{cid}-{kind}')
        if not got:
            print('NO OUTPUT', cid, kind)
            return False
        shutil.copy2(got, src)
        print('saved source', src.name, flush=True)
    if not mat.exists():
        tmp2 = ROOT / 'art/tmp_gen' / f'{cid}-{kind}-matte'
        tmp2.mkdir(parents=True, exist_ok=True)
        wait_for_queue()
        if not run(['qwen21', '--variant', 'bg-removal', '--image', str(src),
                    '--name', f'{cid}-{kind}', '--out', str(tmp2),
                    '--max-queue-depth', '1', '--poll-timeout', '1800']):
            print('BG-REMOVAL FAILED', cid, kind)
            return False
        got = latest(tmp2, f'{cid}-{kind}')
        if not got:
            print('NO MATTE', cid, kind)
            return False
        shutil.copy2(got, mat)
        print('saved matte', mat.name, flush=True)
    print('OK', cid, kind, flush=True)
    return True


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
