#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paint the seven new chapter-10/11/12 characters with the canonical cast pipeline.

第十至十二回新增人物：尤氏、贾珍、金氏（璜大奶奶）、胡氏（金寡妇）、
张友士（张太医）、贾蔷、贾代儒。

管线与最初 45 名既有角色完全一致（这是画风一致性的硬要求，见 docs/production/art.md）：
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
  python3 scripts/gen_ch1012_characters.py                  # 7 人 x 2 = 14 张
  python3 scripts/gen_ch1012_characters.py you_shi:portrait # 单张试生成
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
DESC = {
    'you_shi': "宁国府当家奶奶尤氏，三十余岁丰满温厚的少奶奶，圆融能持事。穿赭石色绣花褙子配青缎长裙，头戴珠翠。",
    'jia_zhen': "宁国府当家贾珍，三十余岁世袭贵族，长方阔脸，神情浮散而自得，纵欲纨绔气。穿石青暗纹锦袍，腰束玉带，蓄短须。",
    'jin_shi': "贾璜之妻金氏，人称璜大奶奶，三十余岁小户人家的媳妇，眉眼灵动而嘴快，泼辣能争。穿半旧的藕荷色袄裙，簪银钗。",
    'hu_shi': "金荣之母胡氏，守寡多年的贫寒妇人，四十余岁，面容瘦削含愁，隐忍劳碌。穿灰布夹袄，素色包头，无首饰。",
    'zhang_youshi': "儒医张友士，四十余岁清瘦学者气度的先生，眉目沉静有神，不卑不亢。穿靛青色直裰，头戴方巾，蓄短须。",
    'jia_qiang': "贾府正派玄孙贾蔷，十六七岁俊俏机灵的少年，眉眼灵活带笑。穿月白洒花锦袍，束发戴冠。",
    'jia_dairu': "贾家义学塾师贾代儒，六十余岁老秀才，瘦削严肃，威严而衰迈。穿深灰布直裰，戴瓜皮帽，蓄花白长须。",
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
    tmp2 = ROOT / 'art/tmp_ch1012' / f'{name}-matte'; tmp2.mkdir(parents=True, exist_ok=True)
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
    tmp = ROOT / 'art/tmp_ch1012' / name; tmp.mkdir(parents=True, exist_ok=True)
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
