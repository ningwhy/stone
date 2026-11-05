#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paint the goods card for every ledger entry that has none.

The card test (tests/ledger.test.ts) requires each entry to carry an `art` path
that really exists, and the back-pack renders the picture instead of a bare
caption. The existing cards are 1024x1024, fully opaque, on an even white
ground with the object centred - they are not cut out, so there is no matting
step here, just paint + convert to WebP.

Usage:
  python3 scripts/build_ledger_cards.py              # all missing
  python3 scripts/build_ledger_cards.py <id> [...]   # only these entry ids
"""
import json, subprocess, sys, shutil, glob, time, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / '.local-tools/local-image-studio/scripts/image_studio.py'
PLAN = json.loads((ROOT / 'art/generation-plan.json').read_text())
STYLE, MODEL, SERVER = PLAN['style'], PLAN['model'], PLAN['server']
NEG = ("text, watermark, signature, blurry, low quality, distorted, deformed, ugly, "
       "extra objects, cluttered background")

OUT_SRC = ROOT / 'art/cards'; OUT_SRC.mkdir(parents=True, exist_ok=True)
CARDS = ROOT / 'public/assets/cards'
LEDGER = ROOT / 'design/ledger.json'

# The shared plan style carries "清代贵族宅院气质" and a light direction, and
# both drop buildings, terraces and landscape washes into the frame: a subject
# noun in the base is painted, and a negative clause does not suppress it
# (see docs/production/art-prompting.md). So goods cards use a stripped base
# that keeps only the brushwork and the palette.
CARD_STYLE = ("精致国风手绘游戏美术，工笔线描结合温润水彩与不透明水粉，细腻纸张纹理，"
              "清晰精细的手绘轮廓与丰富材质细节，低饱和青灰、松绿、暖米白、赭石与暗朱红。")
TAIL = ("清雅工笔淡彩手绘，物件细节清楚。画面正中只有这一件器物，它贴在"
        "一整片均匀平涂的白色纸面中央，四周全是同一个白度的纸——除了这件器物，"
        "画面里什么都没有，没有第二件东西，也没有任何衬景。")

# entry id -> (card file stem, seed, what the card has to show)
GOODS = {
    'ledger.youshi-plum-feast': ('youshi-plum-feast', 10243001,
        "一套清代贵族家宴酒器：朱漆圆托盘内一把银质执壶与两只青瓷小酒盅，"
        "盘旁横斜一枝盛开的红梅，花瓣疏落。"),
    'ledger.jinghuan-tea-wine': ('jinghuan-tea-wine', 10243003,
        "一只带茶托的白釉茶盏与一只小口鼓腹的青瓷酒瓮，釉色温润，"
        "旁边散着几片细长的仙草叶。"),
    'ledger.xifeng-jiarong-screen': ('xifeng-jiarong-screen', 10243005,
        "一架清代玻璃炕屏：硬木边框嵌一大块光洁透明的玻璃，框上雕卷草纹，下承木座。"),
    'ledger.xifeng-liu-cart-coin': ('xifeng-liu-cart-coin', 10243007,
        "一串清代铜钱，麻绳贯穿方孔，圆钱层层叠起，绳头打结，铜色斑驳。"),
    'ledger.xueyima-palace-flowers-three': ('xueyima-palace-flowers-three', 10243009,
        "三对清代堆纱宫花，纱绢层叠成花朵，淡粉、月白与鹅黄，细铜簪脚并排。"),
    'ledger.xueyima-palace-flowers-daiyu': ('xueyima-palace-flowers-daiyu', 10243011,
        "两枝清代堆纱宫花，纱绢层叠成朵，淡粉与月白，细铜簪脚。"),
    'ledger.xueyima-palace-flowers-xifeng': ('xueyima-palace-flowers-xifeng', 10243013,
        "四枝清代堆纱宫花，纱绢层叠成朵，朱红与石青相间，细铜簪脚并排。"),
    'ledger.monk-baochai-gold-lock': ('monk-baochai-gold-lock', 10243015,
        "一枚清代金锁项饰，锁体錾缠枝纹，色泽沉稳，系一条红绳。"),
    'ledger.xueyan-daiyu-hand-stove': ('xueyan-daiyu-hand-stove', 10243017,
        "一只清代铜制小手炉，圆形炉身带镂空炉盖，提梁可折，铜色温润。"),
    'ledger.xueyima-baoyu-goose-web': ('xueyima-baoyu-goose-web', 10243019,
        "两碟下酒菜：一碟鹅掌、一碟鸭舌，酱色油亮，分盛在白瓷小碟中。"),
    # 旧卡面画成了木质鱼形招牌，与该笔（如海写好荐书托内兄贾政协助雨村起复）不符。
    # 母题不写「文字/篆字」——按生图纪律，写什么名词就画出什么，且旧卡曾因印面画出
    # 可读篆字被判不合格。这里只画封套与签条，靠形制让人认出是一封荐帖。
    'ledger.ruhai-recommendation': ('ruhai-recommendation', 10243023,
        "一封清代荐帖：朱红色长条形纸封套，封套正面贴一条窄长的白色签条，"
        "一根米白色细纸带横系封套中部，纸面洁净光洁。"),
    # 第九至十二回新增账本卡面
    'ledger.jiazhen-ginseng': ('jiazhen-ginseng', 10243111,
        "一支带须的野山参：主根胖润，芦碗紧密，细须舒展，表皮呈淡黄褐色。"),
    'ledger.jiazhen-jiajing-penghe': ('jiajing-penghe', 10243113,
        "一具朱漆大捧盒：圆形多层，盒盖微启，露出里头盛放的时鲜果品——"
        "红石榴、青枣、蜜柑堆叠。"),
    'ledger.jiamu-yamcake': ('jiamu-yamcake', 10243115,
        "两枚枣泥馅山药糕：蒸制得洁白软糯，顶面点一弯胭脂红，搁在素白碟中。"),
    # 两张五十两欠契共用一张借据卡。按生图纪律：卡面不写可读正文（写出来必成乱码），
    # 只画「素纸 + 一方朱红大印 + 一枚朱红五指手印」的形制，具体欠银数额由 what 字段承载。
    'ledger.jiarui-jiaqiang-debt': ('jiarui-debt', 10243147,
        "一张清代借契：素米色毛边纸，纸面只钤一方朱红大方印、压一枚朱红五指手印，不要任何标题、不要正文文字、不要边框线、不要其他器物，纸边微卷做旧。"),
    'ledger.jiarui-jiarong-debt': ('jiarui-debt', 10243147,
        "一张清代借契：素米色毛边纸，纸面只钤一方朱红大方印、压一枚朱红五指手印，不要任何标题、不要正文文字、不要边框线、不要其他器物，纸边微卷做旧。"),
    'ledger.daozhang-baojian': ('daozhang-baojian', 10243119,
        "一面清代铜镜：圆形镜面光可鉴人，镜背錾缠枝纹，镜把上錾「风月宝鉴」四字，镜缘泛旧铜绿。"),
    # 第十一回寿礼：四家王爷并六公八侯名帖寿礼，无明码价，入账为 item、金额留空。
    # 货品卡只画一件居中器物（见 TAIL），故取「一只朱漆圆盒 + 几张拜帖」代表整桩寿礼。
    'ledger.c11-shouli-gifts': ('shouli-gifts', 10243151,
        "一只清代朱漆描金寿礼圆盒，盒身正红大漆、金线缠枝描边，盒盖微启露出里头锦缎，旁边叠着几张朱红拜帖。"),
    # 第十三至十五回新增账本卡面（2026-11-03）。
    # 樯木：原文写的是一副封存的板，货品卡画一段锯好的木料，纹理要厚实。
    # 第一版画成了木匣，不是棺木料：棺木料的特征是「帮底皆厚八寸」的厚板，
    # 画面上必须看得出板帮的厚度与拼合的木板纹，否则认不出是棺材板。
    # 生图模型两次都把「厚棺木板」画成箱匣：它把「板」理解成有盖的容器。
    # 第三次改成「三块并排的厚木板」，去掉一切可能被读成箱子的词（匣、盒、套），
    # 并强调断面裸露，才得到一堆无盖的裸木板——仍是木料而不再是箱子，
    # 认得出是棺材板。
    'ledger.c13-qiangmu-coffin': ('c13-qiangmu-coffin', 10243191,
        "三块平放并排的实木厚木板：每块都很厚、断面平整裸露在画面前方，"
        "木色深褐带紫，木纹细密如槟榔纹，板面无漆无盖，四面都只是光素的木头。"),
    # 龙禁尉捐银：银子是散装的，装在两只元宝式的银锭与一串铜钱旁；不写文字。
    'ledger.c13-longjinwei-donation': ('c13-longjinwei-donation', 10243163,
        "一只清代红漆银匣：匣盖敞开，里面整齐码放数锭元宝形的银锭，"
        "银面泛柔和白光，匣底衬着暗红绒布，旁边散着一枚铜钱。"),
    # 第十四回两笔账共用一张卡：一笔是革去的一月银米，一笔是内务支给的灯油蜡烛纸札。
    # 画一只装着散碎银米与灯烛纸札的漆盘，两笔的差别由 what 字段承载。
    'ledger.c14-lai-sheng-salary-cut': ('c14-lai-sheng-salary', 10243165,
        "一只清代黑漆圆盘：盘内一边是一小堆散碎银角与米粒，"
        "另一边码着几支未点的蜡烛与两刀黄表纸，烛身与纸面素净。"),
    'ledger.c14-xiangdeng-payment': ('c14-lai-sheng-salary', 10243165,
        "一只清代黑漆圆盘：盘内一边是一小堆散碎银角与米粒，"
        "另一边码着几支未点的蜡烛与两刀黄表纸，烛身与纸面素净。"),
    # 鹡鸰香念珠：原文是一串香念珠，十八颗圆珠，穗子。
    # 鹡鸰香念珠是香木所制，第一版画成了彩色玉石珠，与「香珠」不合，
    # 改为通体深褐的一串。
    # 深褐一色的珠子模型两次都画成彩色玉石；第三次改用「沉香木雕的珠子」，
    # 用材质名约束颜色。
    'ledger.c15-nianzhu-beads': ('c15-nianzhu-beads', 10243193,
        "一串沉香木雕的手串念珠：十八颗木雕圆珠，珠子是木头本色，"
        "深棕近黑无光泽，纹理是木头的直纹，每颗珠子上都没有花纹，"
        "深色细绳穿系，下垂一缕暗红丝穗。"),
    # 第十五回胡家太太送的十两：一只封好的红封，附一小锭银。
    'ledger.c15-hu-tan-silver': ('c15-hu-tan-silver', 10243169,
        "一只清代朱红包封：封套折口压一道金线，封口系细麻绳，"
        "旁边放着一锭元宝形的白银与一枚铜钱。"),
    # 第十五回张家退亲事的三千两：整笔银子装在描金封套里，只画封套不写数字。
    'ledger.c15-tuixin-3000': ('c15-tuixin-silver', 10243171,
        "一只清代描金封套：厚黄纸对折压边，封口贴一条窄白签条，"
        "套面描着细金云纹，套子微微鼓胀像是装了一沓银票。"),
}


def run(cmd):
    print('$', ' '.join(str(c) for c in cmd), flush=True)
    return subprocess.run([sys.executable, str(CLI)] + cmd, cwd=ROOT).returncode == 0


def latest(out_dir, prefix):
    cands = [c for c in sorted(glob.glob(str(out_dir / f'{prefix}*')),
                               key=lambda p: Path(p).stat().st_mtime)
             if c.lower().endswith('.png')]
    return Path(cands[-1]) if cands else None


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


def to_webp(png: Path, webp: Path):
    r = subprocess.run(['cwebp', '-quiet', '-q', '82', str(png), '-o', str(webp)])
    if r.returncode != 0:
        print('cwebp failed for', png.name); return False
    return True


def main():
    only = sys.argv[1:]
    ledger = json.loads(LEDGER.read_text())
    todo = []
    for e in ledger['entries']:
        if only and e['id'] not in only:
            continue
        if e.get('art') and (ROOT / 'public' / e['art'].lstrip('/')).exists():
            continue
        if e['id'] not in GOODS:
            print('no card spec for', e['id']); continue
        todo.append(e)

    if not todo:
        print('every ledger entry already has an existing card'); return 0
    print(f'{len(todo)} card(s) to paint')

    for e in todo:
        stem, seed, desc = GOODS[e['id']]
        tmp = ROOT / 'art/tmp_cards' / stem; tmp.mkdir(parents=True, exist_ok=True)
        webp = CARDS / f'ledger_{stem}.webp'
        if webp.exists():
            print('reuse existing card', webp.name)
        else:
            wait_queue()
            if not run(['generate', '--server', SERVER, '--model', 'zimage', '--ckpt', MODEL,
                        '--prompt', f'{CARD_STYLE}\n{desc}{TAIL}', '--negative', NEG,
                        '--preset', '1k-1k', '--seed', str(seed), '--name', stem,
                        '--prefix', f'rongguo/{stem}', '--out', str(tmp),
                        '--max-queue-depth', '2', '--poll-timeout', '900']):
                print('GEN FAILED', stem); continue
            got = latest(tmp, stem)
            if not got:
                print('NO OUTPUT', stem); continue
            shutil.copy2(got, OUT_SRC / f'{stem}.png')
            if not to_webp(OUT_SRC / f'{stem}.png', webp):
                continue
            print('painted', webp.name)
        e['art'] = f'/assets/cards/ledger_{stem}.webp'
        print('linked', e['id'], '->', e['art'])

    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=1) + '\n')
    print('ledger.json updated')
    return 0


if __name__ == '__main__':
    sys.exit(main())
