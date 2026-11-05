#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paint the nine new chapter-13/14/15 characters with the canonical cast pipeline.

第十三至十五回新增人物：戴权（掌宫内相）、宝珠（义女）、来升（宁府总管）、
昭儿（贾琏小厮）、北静王水溶、净虚（馒头庵老尼）、智能儿、小尼姑、二丫头
（村庄纺车丫头）、旺儿（凤姐小厮）。

管线与全部 46 名既有角色完全一致（画风一致性的硬要求，见 docs/production/art.md）：
  image_studio.py generate --model zimage --ckpt z_image_turbo_bf16
    + generation-plan.json['style']（国风工笔重彩锚点）
    + 角色中文描述 + 旧批次尾句模板（半身立绘 / 三头身 Q 版）
  -> art/source/{id}-{kind}_s{seed}-01.png     白底原图
  qwen21 bg-removal -> art/matted/{id}-{kind}_s{seed}-sam.png   透明抠图

绝不能换成别的模型或改写尾句：第八九回曾误用 Qwen 2.1 + 水墨 + 全身站像，
导致画风突变，全部 12 张返工重画。

生成后必须再跑：
  scripts/build_ch1012_assets.py   按当前图重测脚底锚点 + height 键 + Q 版压缩
  npm run art:webp                 转 WebP 并给 manifest 打 cache version

Usage:
  python3 scripts/gen_ch1315_characters.py                  # 9 人 x 2 = 18 张
  python3 scripts/gen_ch1315_characters.py shui_rong:portrait # 单张试生成
"""
import json, subprocess, sys, shutil, glob, time, urllib.request
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

# 角色描述沿用 generation-plan.json 里既有演员的写法：身份 + 年龄 + 五官 + 气质。
# 「二丫头」是村庄丫头，不能画成大家闺秀；「净虚」「智能儿」是尼姑，不能有发髻与钗环。
DESC = {
    'dai_quan': "大明宫掌宫内相戴权，五十余岁老宦，清瘦长脸，稀疏短眉，细长含笑眼，窄直鼻，薄唇机敏。穿石青色内臣蟒袍，腰束玉带，蓄须。",
    'bao_zhu': "宁国府义女宝珠，十四五岁小丫鬟，短圆脸，双丫髻，弯眉大眼，小鼻圆嘴，稚拙孝切。穿素白孝服褙子。",
    'lai_sheng': "宁国府总管家来升，五十许中年男人，方正脸，粗平眉，细长眼，宽鼻薄唇，拘谨本分。穿深褐直裰，戴方巾。",
    'zhao_er': "荣国府小厮昭儿，十六七岁少年，圆润脸，短眉圆眼，小翘鼻厚唇，伶俐怕事。穿青布短褐，腰束布带。",
    'shui_rong': "北静王水溶，年未弱冠的年轻亲王，俊美长脸，修长弯眉，明澈长眼，挺直鼻，薄唇含笑，风流潇洒。穿江牙海水五爪坐龙白蟒袍，头戴银翅王帽。",
    'jing_xu': "水月庵老尼净虚，四十余岁，瘦削长脸，深眼窝，稀疏细眉，长鼻薄唇，老成圆滑。穿深褐僧衣，剃度光头。",
    'zhi_neng': "水月庵小尼智能儿，十六七岁少女，圆润脸，细弯眉，含情杏眼，小翘鼻，樱桃小嘴，青春活泼。穿青灰尼衣，剃度光头。",
    'er_ya_tou': "村庄纺车丫头二丫头，十七八岁村姑，圆润脸，碎刘海，含笑大眼，小圆鼻厚唇，爽朗健壮。穿粗布短褙子与布裙，梳双丫髻。",
    'wang_er': "凤姐的小厮旺儿，二十余岁，结实圆脸，短浓眉，机灵眼，宽鼻厚唇，精明强干。穿青灰短褐，腰束绦带。",
    'qin_ye': "秦业，秦钟之父，六十余岁老官，清癯长脸，花白长眉，深陷老眼，瘦长鼻，薄唇，慈和而多病。穿藏青道袍，蓄花白长须。",
}
# seed 来自 plan_character_identity.py 写入的 character-designs.json（portrait=seed, chibi=seed+1）
_SEEDS = {c['id']: c['seed'] for c in
          json.loads((ROOT / 'art/identity/character-designs.json').read_text())['characters']}
SEEDS = {k: _SEEDS[k] for k in DESC}

# 尾句模板照抄既有 45 人批次，一字不改——改动会让 Z-Image 改变取景。
PORTRAIT_TAIL = ("清雅工笔淡彩手绘，人物衣服细节清楚，纯净纯白背景，背景无建筑、花纹、边框、"
                 "文字或落款。半身立绘，头顶至腰下完整，人物正面略向左，双手自然拢于身前，四周留白。")
CHIBI_TAIL = ("清雅工笔淡彩手绘，人物衣服细节清楚，纯净纯白背景，背景无建筑、花纹、边框、"
              "文字或落款。三头身Q版游戏角色，头部占身体三分之一，全身完整，脚底清楚，"
              "轻微俯视等距，朝右下，站立，无地面无投影，四周留白。")


def run(cmd):
    print('$', ' '.join(str(c) for c in cmd), flush=True)
    return subprocess.run([sys.executable, str(CLI)] + cmd, cwd=ROOT).returncode == 0


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
    """抠图后校验非空：qwen21 bg-removal 有概率返回 0% 不透明的空图，
    静默产出空资产（第八九回踩过：贾瑞那张一度全黑）。"""
    tmp2 = ROOT / 'art/tmp_ch1315' / f'{name}-matte'; tmp2.mkdir(parents=True, exist_ok=True)
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
            with urllib.request.urlopen(SERVER + '/queue', timeout=15) as resp:
                q = json.load(resp)
            if len(q.get('queue_running', [])) + len(q.get('queue_pending', [])) == 0:
                return
        except Exception:
            pass
        time.sleep(5)
    print('WARN: server stayed busy; submitting anyway')


def gen(cid, kind):
    seed = SEEDS[cid] + (1 if kind == 'chibi' else 0)
    name = f'{cid}-{kind}'
    stem = f'{name}_s{seed}'
    src = SRC / f'{stem}-01.png'
    mat = MAT / f'{stem}-sam.png'
    for f in (src, mat):
        if f.exists():
            print('skip existing', f.name); return True
    job = f"独立单个人物设定，红楼梦原创形象。{DESC[cid]}{CHIBI_TAIL if kind == 'chibi' else PORTRAIT_TAIL}"
    prompt = f"{STYLE}\n{job}"

    wait_queue()
    tmp = ROOT / 'art/tmp_ch1315' / name; tmp.mkdir(parents=True, exist_ok=True)
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
        targets = [(c, k) for c in DESC for k in ('portrait', 'chibi')]
    ok = 0
    for cid, kind in targets:
        if cid not in SEEDS:
            print('unknown char', cid); continue
        ok += gen(cid, kind)
    print(f'DONE {ok}/{len(targets)}')
