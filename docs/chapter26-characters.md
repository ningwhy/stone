# 第 26 回新出场4人 · 角色设计说明

《蜂腰桥设言传心事　潇湘馆春困发幽情》这一回有 4 人新进 `cast`：**佳蕙**（`jiahui`）、**坠儿**（`zhuer`）、**晴雯**（`qingwen`）、**冯紫英**（`feng_ziying`）。

本文件说明各人的设计依据、资产参数与本回叙事分工。每人八段，结构一致：身份定位 → 外形锚点 → 色彩标识 → 资产参数 → 朝向裁决 → 本回剧情功能 → 与同回角色的对照 → 边界。

---

## 数据来源与口径

| 用途 | 权威来源 |
| --- | --- |
| 外形设定原文 + 生图提示词 | `art/identity/character-designs.json` |
| 运行资产真实参数 | `public/assets/rongguo/manifest.json` 的 `assets` |
| 朝向裁决 | `design/character-facing.json` 的 `actors` |
| 运行时登记 | `src/story.ts` 的 `cast` |
| 底本正文 | `docs/chapter26-source.txt`（维基文库繁体本，OpenCC t2s，2026-11-25 取得） |
| 本回剧情 | `design/chapter26-story.json` |

三条通用口径：底本没给外貌就不冒充底本；立绘与 Q 版是两张独立图，朝向各自裁决；`faceBox` 在最终 PNG 坐标里。

---

## 佳蕙 `jiahui`

### 身份定位

怡红院小丫头 · 红玉的知心人

底本依据（逐字）：

「佳蕙听了跑进来，就坐在床上，笑道：“我好造化！才刚在院子里洗东西，宝玉叫往林姑娘那里送茶叶”」
「“俗语说的好，‘千里搭长棚，没有个不散的筵席’，谁守谁一辈子呢？”」

### 外形锚点

`features`（设计推定，非底本原文）：
**怡红院小丫头；年纪小，替宝玉送茶叶给黛玉，得了钱便请红玉代收；心直口快，替红玉抱不平，听了「千里搭长棚」的话眼圈发红。性别：女（底本称「个小丫头」，与红玉同为怡红院丫鬟）**。

英文生图提示词：a lively thirteen-year-old maidservant GIRL in a Qing-dynasty noble household, a young girl and not a boy, with a round face, bright curious eyes and a slightly pouty mouth, simple and outspoken, wearing a plain pale celadon short jacket and light grey skirt with a small kerchief at her waist, hair in two small twin buns。

### 色彩标识

身份标识色 `#9fc3a6`。地图上同框时以颜色区分，不与同场角色撞色。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 168×600 | 73×116 |
| anchor | `[80.91, 599.439]` | `[38.473, 115.346]` |
| faceBox | `[42, 37, 93, 83]` | `[14, 24, 53, 53]` |
| seed | 10236100 | 10236101 |
| bodyCompress | — | `{'split': 389, 'factor': 0.64}` |
| hash | `194e574a92ec` | `109249d4dd83` |

### 朝向裁决

- portrait **right**（`visual-review`）
- chibi **right**（`visual-review`）

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 12 个节点涉及她，其中 9 个是她本人的台词节点（C26-005—C26-018）。

怡红院小丫头。本回由红玉从窗眼里认出，唤出她来闲话；她替林姑娘送茶叶、跑腿一路交代院里丫鬟的分等与红玉的处境，说到「可气晴雯，绮霰他们这几个，都算在上等里去」时把红玉的心思说破，红玉「眼睛红了」——她的话是压垮红玉心防的那一句。

她的第一句台词是：「我好造化！才刚在院子里洗东西，宝玉叫往林姑娘那里送茶叶，花大姐姐交给我送去。可巧老太太那里给林姑娘送钱来，正分给……」


### 与同回角色的对照

与红玉（同为怡红院小丫头）相对：红玉心事深、佳蕙口直心热，一个把话闷在肚里，一个把赏钱和委屈都摊开讲。

### 边界

底本只写她送茶叶、收钱、劝红玉，没有一句服饰描写；衣色是设计推定。

---

## 坠儿 `zhuer`

### 身份定位

怡红院小丫头 · 手帕子的中人

底本依据（逐字）：

「红玉抬头见是小丫头子坠儿。红玉道：“那去？”坠儿道：“叫我带进芸二爷来。”」
「“他说我替他找著了，他还谢我呢。”」

### 外形锚点

`features`（设计推定，非底本原文）：
**怡红院小丫头；被李嬷嬷打发引贾芸进院，回头又向红玉索取手帕谢礼；年纪小、贪嘴好利。性别：女（底本与红玉同属怡红院丫鬟，俱称「丫头」）**。

英文生图提示词：a small thin twelve-year-old servant GIRL in a Qing-dynasty noble household, a little girl and not a boy, with a pointed chin, quick glancing eyes and a greedy little smile, wearing a faded pale-yellow cotton jacket and dark skirt, hair in a single small side tuft with a red string。

### 色彩标识

身份标识色 `#c7b06a`。地图上同框时以颜色区分，不与同场角色撞色。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 189×600 | 80×116 |
| anchor | `[105.955, 599.426]` | `[42.966, 115.485]` |
| faceBox | `[58, 53, 109, 100]` | `[10, 23, 51, 58]` |
| seed | 10236110 | 10236111 |
| bodyCompress | — | `{'split': 404, 'factor': 0.64}` |
| hash | `e1cdbb411f86` | `9c100f5e4a3a` |

### 朝向裁决

- portrait **right**（`visual-review`）
- chibi **right**（`visual-review`）

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 6 个节点涉及她，其中 2 个是她本人的台词节点（C26-031—C26-049）。

怡红院小丫头。本回引贾芸进怡红院，「叫我带进芸二爷来」；后与贾芸在路上一长一短说话，被贾芸套出丢手帕子的事，一口回绝「我有那么大工夫管这些事」。

她的第一句台词是：「叫我带进芸二爷来。」


### 与同回角色的对照

与佳蕙相对：佳蕙是红玉的听众，坠儿是贾芸与红玉之间的跑腿——她把两条线接上，自己并不知情。

### 边界

「坠儿」与「红玉」是两人；本回她只跑腿、讨谢礼，不参与滴翠亭私语（那是第 27 回）。

---

## 晴雯 `qingwen`

### 身份定位

怡红院大丫鬟 · 嘴利心高

底本依据（逐字）：

「“你只是疯罢！院子里花儿也不浇，雀儿也不喂”」
「“原来爬上高枝儿去了，把我们不放在眼里”」

### 外形锚点

`features`（设计推定，非底本原文）：
**怡红院大丫鬟；生得模样标致、言谈爽利，性子骄傲尖刻；小红越房使唤时当面讥讽「爬上高枝儿去了」。性别：女（底本称「模样标致」的大丫鬟）**。

英文生图提示词：a tall striking young maidservant WOMAN in a Qing-dynasty noble household, a beautiful young woman and not a man, with an oval fair face, sharp arched brows, bright cutting eyes and a proud tight mouth, haughty and quick-tongued, wearing a coral-red silk jacket with a white collar and a pale skirt, hair in a high bun with a jade clasp。

### 色彩标识

身份标识色 `#c46f7e`。地图上同框时以颜色区分，不与同场角色撞色。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 166×600 | 49×116 |
| anchor | `[96.881, 599.433]` | `[31.677, 115.424]` |
| faceBox | `[38, 57, 89, 93]` | `[4, 29, 41, 58]` |
| seed | 10236120 | 10236121 |
| bodyCompress | — | `{'split': 404, 'factor': 0.64}` |
| hash | `6341b3061298` | `e8782ec95c1c` |

### 朝向裁决

- portrait **right**（`vision-landmark-geometry`）
- chibi **right**（`vision-landmark-geometry`）

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 4 个节点涉及她，其中 3 个是她本人的台词节点（C26-119—C26-122）。

怡红院大丫鬟。本回与碧痕拌了嘴正没气，宝钗来时正撞上，把气撒在宝钗身上——先是抱怨「有事没事跑了来坐着」，继而隔着门回黛玉「凭你是谁，二爷吩咐的，一概不许放人进来呢」，气得黛玉在门外气怔。

她的第一句台词是：「有事没事跑了来坐著，叫我们三更半夜的不得睡觉！」


### 与同回角色的对照

与袭人（xiren）、晴雯与秋纹（qiuwen）皆不同：袭人稳、秋纹使性子，晴雯是尖利里带身份感，一句话就把红玉压回原位。

### 边界

第 30 回晴雯虽有台词，但按第 26/27 回的 cast 口径仍由叙述带过，不为她另造一张立绘。

---

## 冯紫英 `feng_ziying`

### 身份定位

神武将军冯唐之子 · 宝玉的酒友

底本依据（逐字）：

「小厮来回“冯大爷来了”。宝玉便知是神武将军冯唐之子冯紫英来了。」
「冯紫英笑道：“好呀！也不出门了，在家里高乐罢。”」

### 外形锚点

`features`（设计推定，非底本原文）：
**神武将军冯唐之子；宝玉的朋友，邀宝玉到家宴饮，言谈爽快带武人气质。性别：男（底本称「冯大爷」「令表兄弟」）**。

英文生图提示词：a handsome martial young nobleman of twenty, a MAN, in Qing-dynasty China with a square jaw, bold brows and a forthright expression, son of a military commander, wearing a dark blue riding jacket with narrow sleeves and a embroidered sash, hair tied in a neat topknot with a jade pin。

### 色彩标识

身份标识色 `#6f86a8`。地图上同框时以颜色区分，不与同场角色撞色。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 180×600 | 54×116 |
| anchor | `[118.723, 599.454]` | `[36.111, 115.462]` |
| faceBox | `[50, 41, 101, 83]` | `[8, 35, 45, 62]` |
| seed | 10237100 | 10237101 |
| bodyCompress | — | `{'split': 405, 'factor': 0.64}` |
| hash | `71e85c871459` | `b55fc91168b5` |

### 朝向裁决

- portrait **right**（`vision-landmark-geometry`）
- chibi **right**（`visual-review`）

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 10 个节点涉及他，其中 6 个是他本人的台词节点（C26-096—C26-105）。

神武将军冯唐之子，本回回目人物。本回携薛蟠等赴宴，席间先报母病，面上带青伤被薛蟠问起，说是在铁网山打围遇仇都尉之子；众人行令，他以「女儿悲、女儿愁、女儿喜」唱曲并邀众人到东边细谈，是本回后段的主持者。

他的第一句台词是：「好呀！也不出门了，在家里高乐罢。」


### 与同回角色的对照

与薛蟠（xuepan）同席：薛蟠粗豪外露，冯紫英是将门子弟的爽朗，陪酒不低俗；二人同为宝玉的酒友，气质截然不同。

### 边界

第 26/28 回是同一人，复用一套资产；程乙本第 26 回他独自来，不写蒋玉菡云儿（那是脂本系统）。

---
