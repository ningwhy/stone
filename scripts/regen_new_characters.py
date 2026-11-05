#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-render the 6 chapter-8/9 characters with the SAME pipeline as the original
45 cast members, so the art style matches.

The earlier batch used Qwen Image 2.1 + ink-wash + full-body, which broke visual
consistency with the existing 45. This script uses the canonical cast pipeline:
  image_studio.py generate --model zimage --ckpt z_image_turbo_bf16
    + plan['style'] (国风工笔重彩 anchor) + role description + 半身/Q版 tail
  -> art/source/{id}-{kind}_s{seed}-01.png  (white bg)
  qwen21 bg-removal -> art/matted/{id}-{kind}_s{seed}-sam.png  (transparent)
Then build_new_char_assets.py rebuilds public/assets/rongguo/* from the matted.

Seeds are kept identical to the existing calibration entries (portrait=seed,
chibi=seed+1), so no manifest/calibration changes are needed.

Usage:
  python3 scripts/regen_new_characters.py            # all 6 x 2
  python3 scripts/regen_new_characters.py ying_er:portrait   # single test
"""
import json, subprocess, sys, shutil, glob, time
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / '.local-tools/local-image-studio/scripts/image_studio.py'
SRC = ROOT / 'art/source'; MAT = ROOT / 'art/matted'
SRC.mkdir(parents=True, exist_ok=True); MAT.mkdir(parents=True, exist_ok=True)
PLAN = json.loads((ROOT / 'art/generation-plan.json').read_text())
STYLE = PLAN['style']; MODEL = PLAN['model']; SERVER = PLAN['server']
NEG = "text, watermark, signature, blurry, low quality, distorted, extra fingers, deformed hands, ugly"

# Chinese role descriptions for the 6 new chapter-8/9 characters.
# Keep the same descriptive register as generation-plan.json's cast jobs.
DESC = {
    'ying_er': "宝钗贴身丫鬟黄金莺，约十三四岁圆润清秀的少女，双丫髻，弯眉灵眼，小翘鼻，丰唇带俏，伶俐活泼。穿浅杏色交领短袄配葱绿长裙，腰系汗巾。",
    'qin_zhong': "秦可卿之弟秦钟，约十二三岁清秀俊美少年，面容娇嫩温婉却分明是男孩，细长眼略垂，鼻梁挺直，唇红齿白。穿淡青色锦绫长袍，颈戴银项圈。",
    'jia_rui': "贾府旁支清客贾瑞，二十余岁瘦长寒酸男子，稀疏眉眼，小眼睛透着贪色，长窄鼻，薄唇歪笑，面色菜黄。穿旧灰青直裰，土布腰带。",
    'jin_rong': "贾府义学中的粗野学生金荣，十二三岁的男孩，稚气未脱、脸颊带婴儿肥，身形尚未长开，粗浓短眉，圆瞪眼，扁宽鼻，厚唇。穿藏青布袄，束腰。",
    'ming_yan': "宝玉的小厮茗烟，约十三四岁机灵少年，圆脸，短直眉，圆眼机警，小翘鼻，利落嘴。穿青布短褐，系腰带，戴小帽。",
    'li_gui': "宝玉的奶兄李贵，三十多岁粗壮朴实男子，浓平眉，小诚实眼，宽鼻，厚实唇。穿深褐粗布直裰，布腰带。",
}
SEEDS = {'ying_er': 10232066, 'qin_zhong': 10232068, 'jia_rui': 10232070,
         'jin_rong': 10232072, 'ming_yan': 10232074, 'li_gui': 10232076}

PORTRAIT_TAIL = ("清雅工笔淡彩手绘，人物衣服细节清楚，纯净纯白背景，背景无建筑、花纹、边框、"
                 "文字或落款。半身立绘，头顶至腰下完整，人物正面略向左，双手自然拢于身前，四周留白。")
CHIBI_TAIL = ("清雅工笔淡彩手绘，人物衣服细节清楚，纯净纯白背景，背景无建筑、花纹、边框、"
              "文字或落款。三头身Q版游戏角色，头部占身体三分之一，全身完整，脚底清楚，"
              "轻微俯视等距，朝右下，站立，无地面无投影，四周留白。")


def run(cmd):
    print('$', ' '.join(str(c) for c in cmd), flush=True)
    r = subprocess.run([sys.executable, str(CLI)] + cmd, cwd=ROOT)
    return r.returncode == 0


def latest(out_dir, prefix):
    cands = sorted(glob.glob(str(out_dir / f'{prefix}*')), key=lambda p: Path(p).stat().st_mtime)
    cands = [c for c in cands if c.lower().endswith('.png')]
    return Path(cands[-1]) if cands else None


def matte_opaque_ratio(p):
    if not p.exists():
        return 0.0
    a = np.asarray(Image.open(p).convert('RGBA'))[..., 3]
    return float((a > 200).sum()) / max(1, a.size)


def matte_with_retry(src, name):
    """Run qwen21 bg-removal, retrying if the cutout comes back blank."""
    tmp2 = ROOT / 'art/tmp_regen' / f'{name}-matte'; tmp2.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        if not run(['qwen21', '--variant', 'bg-removal', '--image', str(src),
                    '--name', name, '--out', str(tmp2),
                    '--max-queue-depth', '1', '--poll-timeout', '1800']):
            print(f'MATTE FAILED (attempt {attempt+1})', name); continue
        got = latest(tmp2, name)
        if not got:
            print(f'NO MATTE OUTPUT (attempt {attempt+1})', name); continue
        if matte_opaque_ratio(got) < 0.05:
            print(f'MATTE BLANK, retry (attempt {attempt+1})', name); continue
        return got
    return None


def wait_queue():
    for _ in range(360):
        try:
            with urllib_request.urlopen(SERVER + '/queue', timeout=15) as resp:
                q = json.load(resp)
            depth = len(q.get('queue_running', [])) + len(q.get('queue_pending', []))
            if depth == 0:
                return
        except Exception:
            pass
        time.sleep(5)
    print('WARN: server stayed busy; submitting anyway')


import urllib.request
urllib_request = urllib.request


def regen(cid, kind):
    seed = SEEDS[cid] + (1 if kind == 'chibi' else 0)
    name = f'{cid}-{kind}'
    stem = f'{name}_s{seed}'
    src = SRC / f'{stem}-01.png'
    mat = MAT / f'{stem}-sam.png'
    desc = DESC[cid]
    job = f"独立单个人物设定，红楼梦原创形象。{desc}{CHIBI_TAIL if kind == 'chibi' else PORTRAIT_TAIL}"
    prompt = f"{STYLE}\n{job}"

    for f in (src, mat):
        if f.exists():
            bk = f.with_name(f.name + '.bak')
            if not bk.exists():
                shutil.move(str(f), str(bk))
            print('backed up', f.name)

    wait_queue()
    tmp = ROOT / 'art/tmp_regen' / f'{name}'; tmp.mkdir(parents=True, exist_ok=True)
    if not run(['generate', '--server', SERVER, '--model', 'zimage', '--ckpt', MODEL,
                '--prompt', prompt, '--negative', NEG, '--preset', '768x1024',
                '--seed', str(seed), '--name', name, '--prefix', f'rongguo/{name}',
                '--out', str(tmp), '--max-queue-depth', '2', '--poll-timeout', '900']):
        print('GEN FAILED', name); return False
    got = latest(tmp, name)
    if not got:
        print('NO GEN OUTPUT', name); return False
    shutil.copy2(got, src); print('saved source', src.name)

    got2 = matte_with_retry(src, name)
    if not got2:
        print('MATTE FAILED after retries', name); return False
    shutil.copy2(got2, mat); print('saved matte', mat.name)
    print('OK', name); return True


if __name__ == '__main__':
    only = sys.argv[1:]
    targets = []
    for a in only:
        if ':' in a:
            c, k = a.split(':', 1)
            targets.append((c, k))
        else:
            targets.append((a, 'portrait')); targets.append((a, 'chibi'))
    if not targets:
        targets = [(c, k) for c in SEEDS for k in ('portrait', 'chibi')]
    for cid, kind in targets:
        if cid not in SEEDS:
            print('unknown char', cid); continue
        regen(cid, kind)
    print('DONE', targets)
