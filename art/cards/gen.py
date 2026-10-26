#!/usr/bin/env python3
"""册页卡片插画批量生成（ComfyUI zimage / FE-013 写意水墨）。

纪律（见 local-image-studio SKILL.md）：
- 单进程串行，绝不并行提交（防打爆 GPU）。
- 文件名带唯一 token：以 card id（. 换 _）作 --name，幂等可断点续跑。
- 已存在 public/assets/cards/{name}.webp 则跳过该卡（断点续跑）。
- 母题正向描述 + 显式排除；禁文字约束写在 positive 正文（zimage cfg=1.0 负向不生效）。
- 轮询容错：URLError 重试。
产物：art/cards/source/{name}-NN.png -> public/assets/cards/{name}.webp
"""
import json, os, subprocess, sys, glob, time, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, ".local-tools/local-image-studio/scripts/image_studio.py")
PY = "/Users/bot/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
CWEBP = "/opt/homebrew/bin/cwebp"
SRC = os.path.join(ROOT, "art/cards/source")
PUB = os.path.join(ROOT, "public/assets/cards")
JSONP = os.path.join(ROOT, "design/collection-cards.json")
os.makedirs(SRC, exist_ok=True)
os.makedirs(PUB, exist_ok=True)

# FE-013 伊吹五月：写意水墨古风人物 + 大面积留白 + 纸纹，契合册页宣纸气质。
STYLE = ("手绘插画风格：水墨人物、古风衣袂、潇洒笔触、大面积留白；"
         "保留明显手绘笔压、停顿与轻微不齐整感，让轮廓产生真实纸上绘制的节奏；"
         "上色保留透明叠染、柔软边缘和纸纹，允许轻微颜色不均与留白。"
         "画面中不要出现任何文字、拉丁字母、水印、签名或标语。")

# card id -> 母题（正向描述，含易混姿态的显式排除）
SUBJECTS = {
    # place 22
    "place.myth": "大荒山无稽崖青埂峰下一块顽石，女娲补天所遗，云气缭绕、孤峰独立，水墨写意仙境，画面中不要出现人物",
    "place.suzhou": "江南姑苏城外仁清巷，粉墙黛瓦、小桥流水，市井人家错落，水墨写意江南水乡",
    "place.lantern": "元宵佳节姑苏灯市，花灯如昼、人流如织，暖色光晕映水，水墨写意",
    "place.ruins": "葫芦庙焚后断壁残垣，焦木颓垣、暮色苍凉，水墨写意废墟",
    "place.farm": "大如州封家田庄，茅舍疏篱、田畴远山，水墨写意田园",
    "place.dream": "太虚幻境云雾缭绕，楼阁隐现于祥云之间，仙气缥缈，水墨写意",
    "place.tavern": "扬州郭外村肆酒棚，老僧枯坐、疏木寒鸦，水墨写意",
    "place.zhitong": "智通寺山门破败，古木萧疏、石径荒凉，水墨写意",
    "place.guowai": "扬州城郭外山道，竹林柴门、田垄远山，水墨写意",
    "place.yamen": "知府衙署大堂，肃穆公案、肃静回避牌列立，水墨写意官衙",
    "place.lin": "扬州林府书斋与江岸，疏朗水阁、孤帆远影，水墨写意",
    "place.canal": "运河舟楫北上，长河如带、岸边垂柳，水墨写意水路",
    "place.yucun": "京城官衙书房，书案卷帙陈列、规制整肃，水墨写意",
    "place.capital": "京城宁荣街，巍峨府第门楼、车马往来，水墨写意都城",
    "place.entry": "荣国府垂花门与抄手游廊，庭院深深，水墨写意宅院",
    "place.east": "贾赦院东路小院，山石海棠、幽静别院，水墨写意",
    "place.dinner": "贾母院后房晚膳，暖阁圆桌、明灯锦帐，水墨写意",
    "place.night": "贾母院碧纱橱外间，湘帘绣榻、月色入户，水墨写意内室",
    "place.central": "一座古典中国贵族府邸的正厅，朱红立柱、雕花楠木屏风、高悬匾额，庭院深深，暖光自檐下洒落，水墨写意",
    "place.wang": "王夫人院东廊三间，起居内室、陈设雅洁，水墨写意",
    "place.c4_yamen": "应天府大堂与退堂密室，案卷堆叠、屏壁森然，水墨写意官衙",
    "place.c4_lixiang": "荣府东北角梨香院，梨花满庭、清幽小院，水墨写意",
    # line 6
    "line.stone": "青埂峰下一块遗石兀立，两位仙人身形飘渺立于侧论道，水墨写意，画面中不要出现人物面孔文字",
    "line.haoliao": "破足道人疯跛而行，张口吟唱、衣衫褴褛，市井背景，水墨写意人物",
    "line.haoliao-note": "一位文人随道人回首功名尘土，神色豁然顿悟，水墨写意人物",
    "line.jade": "一位锦衣少年独立于水亭之中，若有所思眺望远方，古风衣袂随风轻动，水墨写意人物",
    "line.water": "一位贵族少年立于阶前，环侍数名丫鬟，眉眼温润，水墨写意人物",
    "line.huguanfu": "一名衙门门子自靴筒取出一张抄本，附耳向官长低语，水墨写意人物",
    # token 4
    "token.huguanfu": "一张泛黄抄本置于古朴木案之上，一角朱红印记，纸上密列数行小字，水墨古风",
    "token.yincun-mishu": "一封密信摊于案上，封缄朱印、笺纸工整，水墨古风",
    "token.huazhang": "藕合色花帐与锦被缎褥并陈，绫罗堆叠、色泽温润，水墨古风",
    "token.yinbi": "一封纹银与四匹锦缎置于木盘之中，红绳系扎，水墨古风",
    # bond 4
    "bond.xiren": "一位温婉丫鬟梳双丫髻、着浅色襦裙，侍立于朱红廊柱之下，水墨古风人物",
    "bond.yingge": "一位聪慧丫鬟随老夫人身侧，欲往小姐房中，水墨古风人物",
    "bond.jiaoxing": "一位清秀丫鬟隔窗窥看、回身欲避，水墨古风人物",
    "bond.yinglian": "一位幼女被簇拥于人群之中，神色惶然四顾，水墨古风人物",
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
    cands = sorted(glob.glob(os.path.join(SRC, f"{name}*.png")),
                   key=os.path.getmtime, reverse=True)
    # --keep-old 下新图落 _new、旧图归档为 _v{n}；优先取 _new，其次普通名，跳过 _v 归档。
    for c in cands:
        b = os.path.basename(c)
        if "_v" in b:
            continue
        if b.endswith("_new.png"):
            return c
    for c in cands:
        b = os.path.basename(c)
        if "_v" in b or "_new" in b:
            continue
        return c
    return cands[0] if cands else None

def convert(name, src_png):
    webp = os.path.join(PUB, f"{name}.webp")
    subprocess.run([CWEBP, "-q", "84", src_png, "-o", webp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return webp

def inject_json():
    d = json.load(open(JSONP))
    cards = d["cards"] if isinstance(d, dict) else d
    done = 0
    for c in cards:
        n = name_of(c["id"])
        wp = os.path.join(PUB, f"{n}.webp")
        if os.path.exists(wp):
            rel = f"/assets/cards/{n}.webp"
            if c.get("image") != rel:
                c["image"] = rel; done += 1
    json.dump(d, open(JSONP, "w"), ensure_ascii=False, indent=2)
    return done

def main():
    only = sys.argv[1:]  # 可选：只生成指定 card id
    todo = {k: v for k, v in SUBJECTS.items() if (not only or k in only)}
    print(f"计划生成 {len(todo)} 张；已存在 webp 的将跳过。")
    skipped = generated = 0
    for cid, subj in todo.items():
        name = name_of(cid)
        webp = os.path.join(PUB, f"{name}.webp")
        if os.path.exists(webp):
            skipped += 1; continue
        prompt = f"{STYLE} 画面主题：{subj}。"
        print(f"[gen] {cid} -> {name}")
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
    print(f"完成：新增生成 {generated}，跳过已存在 {skipped}，回写 image 字段 {inj} 张。")

if __name__ == "__main__":
    main()
