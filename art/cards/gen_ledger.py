#!/usr/bin/env python3
"""账簿流转贴图批量生成（ComfyUI zimage / FE-013 写意水墨）。

与 art/cards/gen.py 同一套纪律与风格（册页卡片已用此风），但母题按账簿的
品类分化：银两是器物与光，衣物是丝缕，人是形貌，物件是案上什物，人情是
文书信物——让贴图能替账目说话，而不是每张都画个一样的钱堆。

纪律（见 local-image-studio SKILL.md）：
- 单进程串行，绝不并行提交（防打爆 GPU）。
- 文件名带唯一 token：账目 id（. 换 _）作 --name，幂等可断点续跑。
- 已存在 public/assets/cards/{name}.webp 则跳过。
- 母题正向描述 + 显式排除；禁文字约束写在 positive 正文（zimage cfg=1.0 负向不生效）。
- 轮询容错：URLError 重试。
产物：art/cards/source/ledger_{name}-NN.png -> public/assets/cards/ledger_{name}.webp
"""
import json, os, subprocess, sys, glob, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, ".local-tools/local-image-studio/scripts/image_studio.py")
PY = "/Users/bot/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
CWEBP = "/opt/homebrew/bin/cwebp"
SRC = os.path.join(ROOT, "art/cards/source")
PUB = os.path.join(ROOT, "public/assets/cards")
JSONP = os.path.join(ROOT, "design/ledger.json")
os.makedirs(SRC, exist_ok=True)
os.makedirs(PUB, exist_ok=True)

# FE-013 伊吹五月：写意水墨古风 + 大面积留白 + 纸纹，与册页卡片同调。
# 账簿贴图一律「纯静物」：器物自己躺在画面里，不要人替它摆放。
#
# 三轮踩坑，都写进正文（zimage cfg=1.0，negative 不生效，只能靠正向约束）：
# 1) 母题里写「置于案上/置于木案」会诱出模型画一只半身人物去摆东西，
#    人物的头被画框裁掉反而喧宾夺主 —— 故正文写死「无人物」。
# 2) 写「半枚鱼符」会被读成一条活鱼 —— 母题改成「刻鱼形纹的木牌」。
# 3) 「古风器物」「静物」是绘画品类词，模型会照静物画范式摆出
#    「瓶 + 罐 + 碗」三件套陪衬；哪怕正文写「不要额外添加瓷瓶」也压不住，
#    甚至在荒田朽屋这种绝不该有瓶子的场景里立一只巨瓶。
#    —— 故把风格基底拆成两套：器物用「只有母题那一两件东西、其余全空」，
#    风景用「只有自然景物、没有任何器物」，并且不再出现会召唤瓶罐的品类词。
STYLE_BASE = ("手绘插画风格：写意水墨、潇洒笔触、大面积留白；"
              "保留明显手绘笔压、停顿与轻微不齐整感，让轮廓产生真实纸上绘制的节奏；"
              "上色保留透明叠染、柔软边缘和纸纹，允许轻微颜色不均与留白。"
              "画面中不要出现任何人物、人体、面孔、手臂、衣袍；"
              "画面中不要出现任何文字、拉丁字母、水印、签名或标语，纸面上不得书写任何字。")

# 器物类：画面里只该有母题写明的那一两件东西，其余留白。
#
# 第四轮踩坑：STYLE_OBJECT 里的「不要额外添加瓶子…」仍然压不住——
# 「器物/静物」本身就是会召唤瓶罐的品类词，模型无视否定句照样摆三件套。
# 有效的做法是不谈品类，只谈「这一件东西」：把母题写成主体特写，
# 强调单一主体占满画面、其余纯空白，不给模型任何「再来几件陪衬」的余地。
STYLE_OBJECT = (STYLE_BASE +
                "画面只画一样东西，它就摆在画面正中央，占据画面的大部分；"
                "除此之外画面完全是空白的宣纸，不要再画别的器物，也不要画桌子、"
                "不要画盘子托着它、不要再添置任何瓶瓶罐罐。")

# 风景类：只有自然景物，画面里不该出现任何人为器物。
STYLE_LAND = (STYLE_BASE +
              "画面中只有自然景物与破败屋舍，是一幅淡墨写意的风景；"
              "画面里不要出现任何器物、瓶罐、器皿、人物。")

# 账目 id -> (母题, 风格基底)
# id 取自 design/ledger.json 的 entries[].id。
# 人物类与四张信物卡不生成：直接复用既有卡图。
# 母题一律写成「器物自陈」：主体在画面中央、大而完整，不借人物之手。
# 母题里只准出现该笔账目真正涉及的东西：多一件陪衬器物就是语义跑偏
# （例：薄田朽屋里不该有瓷瓶，荐书是文书不是鲤鱼）。
SUBJECTS = {
    # --- 银两 money ---
    "ledger.yucun-winter-clothes": ("两件厚实的旧棉冬衣平铺叠放，灰蓝布面、絮棉微露、针脚粗朴，占据画面中央", STYLE_OBJECT),
    "ledger.fengsu-land-money": ("一锭白银与几枚散碎银角静置托盘之上，金属泛冷光、边缘磨损，占据画面中央", STYLE_OBJECT),
    "ledger.shiyin-poor-land": ("一片荒薄田地，远处几间歪斜朽屋，茅草零落、篱笆残破，空旷寂寥的远景风景，占据画面中央", STYLE_LAND),
    "ledger.yucun-fengsu-2liang": ("两枚小银锭并排置于粗陶碟中，器皿朴拙、光泽内敛，占据画面中央", STYLE_OBJECT),
    "ledger.zhen-silver": ("两封束好的银子以红纸包就，封口压痕可见，静静并列，占据画面中央", STYLE_OBJECT),
    "ledger.zhen-brocade": ("四匹锦缎层层叠放成一摞，织金云纹在缎面流动、边缘垂坠，占据画面中央", STYLE_OBJECT),
    "ledger.fengsu-baijin": ("一只鼓胀饱满的锦囊静置案上，囊口金线束紧、垂坠如水，占据画面中央", STYLE_OBJECT),
    "ledger.zhen-thanks-goods": ("数件什物杂陈：布匹、茶罐、纸包散而不乱，静物一组，占据画面中央", STYLE_OBJECT),
    "ledger.fengyuan-silver": ("一只旧木箱敞开，内中白银满箱、缎光溢出箱沿，占据画面中央", STYLE_OBJECT),
    "ledger.feng-burial-silver": ("素白封套内裹着纸钱与银锭，旁边一盏冷落孤灯，静物一组，占据画面中央", STYLE_OBJECT),
    # --- 衣物 clothing ---
    "ledger.xifeng-cloth": ("两匹裁好的缎子折叠齐整，缎面流光、边幅未动，占据画面中央", STYLE_OBJECT),
    # --- 物件 item ---
    # 荐书是「一纸文书」，鱼符是刻鱼形的木牌，都不是活物，更不是瓶子。
    "ledger.ruhai-recommendation": ("一枚扁平的长方形木牌，上面刻着一条鱼的纹样，木纹清晰，占据画面中央", STYLE_OBJECT),
    # 官凭是「盖了朱印的空纸」，纸面不写名字；印是另一枚器物，可以有。
    "ledger.zheng-restoration": ("一枚小小的方形官印立着，印面朝前，印面刻着简洁的阳文纹样，占据画面中央", STYLE_OBJECT),
    "ledger.yucun-letters": ("一只素净的白信封，封缄压好，封皮上没有任何字迹，占据画面中央", STYLE_OBJECT),
}


def name_of(cid): return cid.replace(".", "_")


def run(cmd):
    for attempt in range(4):
        try:
            return subprocess.run([PY, SCRIPT] + cmd, capture_output=True, text=True, timeout=240)
        except subprocess.TimeoutExpired:
            print(f"  [retry {attempt+1}] timeout, retrying..."); time.sleep(3)
    raise RuntimeError("generation failed after retries: " + " ".join(cmd))


def latest_source(name):
    """取该图最新的一张源图，排除 _v{n} 归档。

    --keep-old 有两种落盘路径：目标已存在时旧图改名 _v{n}、新图落 _new；
    目标不存在时直接写原名。所以「最新」要按 mtime 排，不能只认 _new——
    否则第二次重生成时会把上一轮的 _new 当成新图，转出错的 webp。
    """
    cands = [c for c in glob.glob(os.path.join(SRC, f"{name}*.png"))
             if "_v" not in os.path.basename(c)]
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)


def convert(name, src_png):
    webp = os.path.join(PUB, f"{name}.webp")
    subprocess.run([CWEBP, "-q", "84", src_png, "-o", webp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return webp


def inject_json():
    """把生成的图回写进 design/ledger.json 的 art 字段。
    人物类与既有信物卡的 art 已经在数据里，不在这里覆盖。"""
    d = json.load(open(JSONP))
    done = 0
    for e in d["entries"]:
        wp = os.path.join(PUB, f"{name_of(e['id'])}.webp")
        if not os.path.exists(wp):
            continue
        rel = f"/assets/cards/{name_of(e['id'])}.webp"
        if e.get("art") != rel:
            e["art"] = rel; done += 1
    json.dump(d, open(JSONP, "w"), ensure_ascii=False, indent=2)
    return done


def main():
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv[1:]
    todo = {k: v for k, v in SUBJECTS.items() if (not only or k in only)}
    print(f"计划生成 {len(todo)} 张；已存在 webp 的将跳过。")
    skipped = generated = 0
    for cid, (subj, style) in todo.items():
        name = name_of(cid)
        webp = os.path.join(PUB, f"{name}.webp")
        if os.path.exists(webp) and not force:
            skipped += 1; continue
        prompt = f"{style} 画面主题：{subj}。"
        print(f"[gen] {cid} -> {name}", flush=True)
        r = run(["generate", "--model", "zimage", "--preset", "1k-1k",
                 "--out", SRC, "--name", name, "--keep-old", "--prompt", prompt])
        if r.returncode != 0:
            print("  FAIL:", r.stderr[-300:]); continue
        sp = latest_source(name)
        if not sp:
            print(f"  [warn] 未找到产物 {name}"); continue
        convert(name, sp)
        generated += 1
    inj = inject_json()
    print(f"完成：新增生成 {generated}，跳过已存在 {skipped}，回写 art 字段 {inj} 笔。")


if __name__ == "__main__":
    main()
