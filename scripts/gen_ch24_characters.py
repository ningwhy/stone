#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate portrait + chibi for the chapter-24 characters.

Who they are (chapter 24 《醉金刚轻财尚义侠　痴女儿遗帕惹相思》)
------------------------------------------------------------------
  * **jia_yun** (贾芸) — 荣国府后廊上住着的五嫂子之子,十八岁,「生得著实斯文清秀,
    倒也十分面善」。他这一回是主线人物:求卜世仁赊账被拒、遇醉金刚倪二慷慨解囊、
    拿冰麝孝敬凤姐、被派种树工程。**前十三回只在旁白里被提到过一次**。
  * **xiaohong** (小红,本姓林,小名红玉) — 十六岁,「容长脸面,细巧身材,却十分俏丽干净」,
    怡红院丫头。她的「遗帕」是回目下联的落点。
  * **ni_er** (倪二,「醉金刚」) — 市井泼皮,专放重利债。底本明写「泼皮无赖,却因人而使,
    颇颇的有义侠之名」。
  * **bu_shi_ren** (卜世仁) — 贾芸的母舅,开香料铺,精瘦刻薄,推脱赊欠。
  * **xiangling** (香菱) — 本姓甄,名英莲,甄士隐之女,幼年被拐、卖与薛家后改名香菱,
    现为薛宝钗的丫头。本回开头与黛玉一处。**身世依据取第七回**:周瑞家的初见香菱,
    拉了她的手细细的看了一会,说「倒好个模样儿,竟有些象咱们东府里蓉大奶奶的品格儿」
    ——即像秦可卿,不是「像黛玉」(此说系后人讹传,底本无此句);
    她在第七、十六、二十回都只被提及过,本回是**第一次真正登场**。
  * **qiuwen** (秋纹) — 怡红院丫鬟,本回与碧痕一同奚落小红。
  * **bihen** (碧痕) — 同上。
  * **yuan_yang** (鸳鸯) — 贾母房首席大丫头,本回开篇与宝玉的「涎皮」戏。

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

CHARS = ['jia_yun', 'xiaohong', 'ni_er', 'bu_shi_ren', 'xiangling', 'qiuwen', 'bihen', 'yuan_yang']

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
