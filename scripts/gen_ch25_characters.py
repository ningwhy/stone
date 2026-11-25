#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate portrait + chibi for the chapter-25 characters.

Who they are (chapter 25 《魇魔法姊弟逢五鬼　红楼梦通灵遇双真》)
------------------------------------------------------------------
  * **ma_dao_po** (马道婆) — 宝玉寄名的干娘,常走荣府各院念佛化缘的庙里婆子。
    本回先劝贾母供「大光明普照菩萨」点海灯,再到赵姨娘房里定下魇魔法之计:
    收五百两欠契,掏出十个青面白发的纸鬼与两个纸人,教赵姨娘写下宝玉凤姐的年庚
    **底本对她没有一句外貌描写**,features/prompt 全部是视觉设计推定,不是原文明示。
  * **cai_xia** (彩霞) — 王夫人房中丫鬟,与贾环相好。底本写她「悄悄的向贾环说道：
    你安些分罢」「咬著嘴唇,向贾环头上戳了一指头」「淡淡的不大答理,两眼睛只向贾环处看」,
    宝玉拉她的手她「夺手不肯,便说：再闹,我就嚷了」。
    **注意彩霞与已登记的彩云(caiyun)是两个人**:底本同段「又叫彩云倒杯茶来……只有彩霞
    还和他合的来」,两人并列。同样**底本无外貌描写**,外形为设计推定。

本回其余说话人全部复用已有 cast（宝玉/凤姐/赵姨娘/贾母/黛玉/宝钗/贾政/马道婆之外,
还有赓续的惜春等）,以及第 1 回已登记的癞头和尚(monk)与跛足道人(taoist)
——「通灵遇双真」正是这一僧一道,直接复用,不新建。

Pipeline per character/kind:
  qwen21 t2i  -> art/source/{id}-{kind}_s{seed}-01.png   (white-bg ink figure)
  qwen21 bg-removal -> art/matted/{id}-{kind}_s{seed}-sam.png (transparent)
Serial, resumable (skips files already present). Submits to the ComfyUI server.

Server address: default 192.168.4.66:8188; override with COMFYUI_HOST or
`--server` on the CLI below.
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

CHARS = ['ma_dao_po', 'cai_xia']

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
