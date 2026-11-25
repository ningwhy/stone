# 第 28 回新出场2人 · 角色设计说明

《蒋玉菡情赠茜香罗　薛宝钗羞笼红麝串》这一回有 2 人新进 `cast`：**蒋玉菡**（`jiang_yuhan`）、**云儿**（`yun_er`）。

本文件说明各人的设计依据、资产参数与本回叙事分工。每人八段，结构一致：身份定位 → 外形锚点 → 色彩标识 → 资产参数 → 朝向裁决 → 本回剧情功能 → 与同回角色的对照 → 边界。

---

## 数据来源与口径

| 用途 | 权威来源 |
| --- | --- |
| 外形设定原文 + 生图提示词 | `art/identity/character-designs.json` |
| 运行资产真实参数 | `public/assets/rongguo/manifest.json` 的 `assets` |
| 朝向裁决 | `design/character-facing.json` 的 `actors` |
| 运行时登记 | `src/story.ts` 的 `cast` |
| 底本正文 | `docs/chapter28-source.txt`（维基文库繁体本，OpenCC t2s，2026-11-25 取得） |
| 本回剧情 | `design/chapter28-story.json` |

三条通用口径：底本没给外貌就不冒充底本；立绘与 Q 版是两张独立图，朝向各自裁决；`faceBox` 在最终 PNG 坐标里。

---

## 蒋玉菡 `jiang_yuhan`

### 身份定位

唱小旦的伶人 · 艺名琪官

底本依据（逐字）：

「还有许多唱曲儿的小厮并唱小旦的蒋玉菡，锦香院的妓女云儿。」
「“将系小衣儿一条大红汗巾子解了下来，递与宝玉”」

### 外形锚点

`features`（设计推定，非底本原文）：
**唱小旦的伶人，艺名琪官；容貌俊美，性情温软，席间唱曲，解下茜香罗汗巾赠宝玉。性别：男（底本称「小旦」即男扮旦角，宝玉见其「妩媚温柔」；本回与薛蟠、冯紫英并称「令表兄弟」）**。

英文生图提示词：a beautiful young MALE opera singer in Qing-dynasty China, a handsome young man and not a woman, with a delicate oval face, fine arched brows, soft moist eyes and rouged lips, gentle and ingratiating manner, wearing a rose-pink silk robe with long flowing water sleeves and a crimson sash, hair in a soft stage coiffure with a small flower pin。

### 色彩标识

身份标识色 `#c48fa8`。地图上同框时以颜色区分，不与同场角色撞色。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 293×600 | 61×116 |
| anchor | `[173.465, 599.444]` | `[39.783, 115.421]` |
| faceBox | `[118, 37, 156, 69]` | `[8, 31, 43, 57]` |
| seed | 10237110 | 10237111 |
| bodyCompress | — | `{'split': 397, 'factor': 0.64}` |
| hash | `e496221d5ea2` | `d1287120ca19` |

### 朝向裁决

- portrait **right**（`vision-landmark-geometry`）
- chibi **right**（`vision-landmark-geometry`）

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 8 个节点涉及他，其中 5 个是他本人的台词节点（C28-092—C28-103）。

冯紫英家的唱曲名。本回行令时唱「女儿悲、女儿愁、女儿喜」一套《寄生草》，唱毕自谦「这诗词上我倒有限」；又道出昨日所见的对子，末了席上认下「就是我的小名儿」，并解下茜香国女国王所贡的汗巾子与宝玉换。

他的第一句台词是：「女儿悲，丈夫一去不回归。女儿愁，无钱去打桂花油。女儿喜，灯花并头结双蕊。女儿乐，夫唱妇随真和合。」


### 与同回角色的对照

与云儿（yun_er）同席：两人都是唱曲的，蒋玉菡唱的是名角风度，云儿是风月场的熟络；一个赠帕传情，一个举杯玩笑。

### 边界

艺名琪官与本名蒋玉菡是同一人，只登记一次；茜香罗是信物，不另做器物卡。

---

## 云儿 `yun_er`

### 身份定位

锦香院陪酒女子 · 席间唱曲

底本依据（逐字）：

「锦香院的妓女云儿。大家都见过了，然后吃茶。」
「“云儿听说，只得拿起琵琶来，唱道”」

### 外形锚点

`features`（设计推定，非底本原文）：
**锦香院陪酒的妓女；席间弹琵琶唱曲，言语风泼，与薛蟠冯紫英熟稔。性别：女（底本称「妓女」）**。

英文生图提示词：a voluptuous young courtesan WOMAN in Qing-dynasty China, a female singer and not a man, with a rounded face, painted brows, laughing eyes and a bold smiling mouth, wearing a peach-red silk jacket and a deep crimson pleated skirt with a gold hair ornament, holding a small pipa lute。

### 色彩标识

身份标识色 `#d08a92`。地图上同框时以颜色区分，不与同场角色撞色。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 214×600 | 72×116 |
| anchor | `[99.377, 599.437]` | `[40.399, 115.456]` |
| faceBox | `[95, 35, 151, 79]` | `[12, 29, 49, 63]` |
| seed | 10237120 | 10237121 |
| bodyCompress | — | `{'split': 390, 'factor': 0.64}` |
| hash | `dd89a5ed9f73` | `3c559fdb3644` |

### 朝向裁决

- portrait **right**（`vision-landmark-geometry`）
- chibi **right**（`vision-landmark-geometry`）

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 11 个节点涉及她，其中 9 个是她本人的台词节点（C28-065—C28-088）。

冯紫英家的琵琶手，本回贯穿行令的唱曲者。先唱「两个冤家，都难丢下」；薛蟠跳出来喧嚷，她「下两句越发难说了，我替你说罢」；唱到「女儿悲，将来终身指靠谁」时接薛蟠的话头，一路唱到「桃之夭夭」。

她的第一句台词是：「两个冤家，都难丢下，想著你来又记挂著他。两个人形容俊俏，都难描画。想昨宵幽期私订在荼縻架，一个偷情，一个寻拿，拿」


### 与同回角色的对照

与蒋玉菡相对：同在席上唱曲，云儿更市井、更热络；她把酒宴的气氛撑起来，蒋玉菡则把宝玉的心事牵出去。

### 边界

身份是锦香院陪酒的女子，底本未给年龄与容貌细节，形象为设计推定。

---
