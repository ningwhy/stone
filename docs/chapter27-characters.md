# 第 27 回新出场2人 · 角色设计说明

《滴翠亭杨妃戏彩蝶　埋香冢飞燕泣残红》这一回有 2 人新进 `cast`：**司棋**（`siqi`）、**绮霰**（`qixian`）。

本文件说明各人的设计依据、资产参数与本回叙事分工。每人八段，结构一致：身份定位 → 外形锚点 → 色彩标识 → 资产参数 → 朝向裁决 → 本回剧情功能 → 与同回角色的对照 → 边界。

---

## 数据来源与口径

| 用途 | 权威来源 |
| --- | --- |
| 外形设定原文 + 生图提示词 | `art/identity/character-designs.json` |
| 运行资产真实参数 | `public/assets/rongguo/manifest.json` 的 `assets` |
| 朝向裁决 | `design/character-facing.json` 的 `actors` |
| 运行时登记 | `src/story.ts` 的 `cast` |
| 底本正文 | `docs/chapter27-source.txt`（维基文库繁体本，OpenCC t2s，2026-11-25 取得） |
| 本回剧情 | `design/chapter27-story.json` |

三条通用口径：底本没给外貌就不冒充底本；立绘与 Q 版是两张独立图，朝向各自裁决；`faceBox` 在最终 PNG 坐标里。

---

## 司棋 `siqi`

### 身份定位

迎春房中大丫鬟

底本依据（逐字）：

第二十七回：「司棋道：“没理论。”红玉听了，抽身又往四下里一看」

第七十一回（补录，为外貌与性别提供依据）：「鸳鸯眼尖，趁月色见准一个穿红裙子梳鬅头高大丰壮身材的，是迎春房里的司棋」

**性别：女。** 底本称她「这麼大丫頭」「这麼大丫頭了」，与鸳鸯、迎春同为女子；第七十一回「穿红裙子梳鬅头」也是女子装束。首版立绘因提示词只写 `maidservant` 未锚定性别，且叠了「宽肩、方脸、粗眉」等偏男性向的形容，被模型渲染成男性青年，已重做。

### 外形锚点

`features`（设计推定，非底本原文）：
**迎春房中的大丫鬟；身量高大、性情硬朗，回红玉「没理论」。「身量高大」据第七十一回「穿红裙子梳鬅头高大丰壮身材的，是迎春房里的司棋」；红裙、鬅头亦据此。性别：女（底本称「这麼大丫頭」「这麼大丫頭了」，与鸳鸯、迎春同为女子）**。

英文生图提示词：a tall broad-shouldered FEMALE servant woman in a Qing-dynasty noble household, a sturdy young woman in her late twenties with a broad square face, heavy brows, steady blunt eyes and a firm mouth, plain and forthright, strong and capable, clearly a woman and not a man, wearing a RED long skirt with a dark teal short jacket over it, hair gathered into a plain high rounded bun with a black hairnet, female servant of a young mistress。

### 色彩标识

身份标识色 `#7f9a8c`。地图上同框时以颜色区分，不与同场角色撞色。红裙是底本明写的服色，与迎春房系色不冲突。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 185×600 | 60×116 |
| anchor | `[103.096, 599.428]` | `[24.217, 115.913]` |
| faceBox | `[43, 42, 80, 84]` | `[18, 43, 48, 66]` |
| seed | 10237140 | 10237141 |
| bodyCompress | — | `{'split': 394, 'factor': 0.64}` |
| hash | `7014b79e2a7b` | `afebd68d2b66` |

faceBox 为目视重标：立绘取眉（y=42）到下巴（y=84）、x 43..80；Q 版取眉（y=43）到嘴下（y=66）、x 18..48。

### 朝向裁决

- portrait **left**（`vision-landmark-geometry`）
- chibi **right**（`visual-review`）

立绘鼻偏移 -0.005、嘴偏移 -0.074，同为负号即朝画面左，目视复核一致（鼻尖与嘴都在眼中点左侧，右颊更开）。Q 版检测的左右眼命名检查为 SWAPPED，符号无意义，故目视裁定：鼻尖落在眼中点、略偏右，按「鼻嘴同号、正号朝右」的先例记为朝右。

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 3 个节点涉及她，其中 1 个是她本人的台词节点（C27-059—C27-059）。

迎春房大丫鬟。本回只一句台词：「因见司棋从山洞里出来，站着系裙子，便赶上来问道」，司棋答「没理论」。三个节点，却把第七十一回「穿红裙子梳鬅头高大丰壮身材」的身量与裙色提前露了出来。

她的第一句台词是：「没理论。」


### 与同回角色的对照

与红玉相对：红玉要往上走，司棋是迎春房里的老人，答复简短、不带情绪，正好衬出红玉四处打听的急切。

### 边界

底本里她与「待书」并列，待书只是名单上的一个名字，不登记为 cast。

---

## 绮霰 `qixian`

### 身份定位

怡红院丫鬟 · 描花样那位

底本依据（逐字）：

「“你听听他的嘴！你们别说了，让他逛去罢。”」
「“你们再问问我逛了没有。二奶奶使唤我说话取东西的。”」

### 外形锚点

`features`（设计推定，非底本原文）：
**怡红院丫鬟，又称绮大姐姐；命小红描花样，说话带讥诮。性别：女（底本称「绮大姐姐」，怡红院丫鬟）**。

英文生图提示词：a quiet-looking young maidservant WOMAN in a Qing-dynasty noble household, a young woman and not a man, with a softly rounded face, level brows, slightly sarcastic closed mouth, wearing a pale sage-green jacket and cream skirt with an embroidery purse at her waist, hair in a simple low bun。

### 色彩标识

身份标识色 `#9fb8a0`。地图上同框时以颜色区分，不与同场角色撞色。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 168×600 | 58×116 |
| anchor | `[71.12, 599.439]` | `[28.638, 115.47]` |
| faceBox | `[48, 39, 99, 76]` | `[7, 24, 41, 53]` |
| seed | 10236130 | 10236131 |
| bodyCompress | — | `{'split': 396, 'factor': 0.64}` |
| hash | `c5419181046a` | `edb11e3ec707` |

### 朝向裁决

- portrait **left**（`vision-landmark-geometry`）
- chibi **right**（`visual-review`）

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 3 个节点涉及她，其中 1 个是她本人的台词节点（C27-065—C27-065）。

怡红院丫鬟。本回随晴雯、碧痕、紫绡等一群人过来，晴雯与红玉争竞时她出言收场：「你听听他的嘴！你们别说了，让他逛去罢。」

她的第一句台词是：「你听听他的嘴！你们别说了，让他逛去罢。」


### 与同回角色的对照

与晴雯同场：晴雯主攻，绮霰补刀；一个正言厉色，一个轻描淡写，两个人的话叠起来才是红玉在怡红院的处境。

### 边界

本回只以群体身份出现，台词很少；不为了凑人物给她加戏。

---
