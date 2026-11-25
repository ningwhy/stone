# 第 29 回新出场一人 · 角色设计说明

《享福人福深还祷福　痴情女情重愈斟情》这一回有 1 人新进 `cast`：**张道士**（`zhang_daoshi`）。

本文件说明各人的设计依据、资产参数与本回叙事分工。每人八段，结构一致：身份定位 → 外形锚点 → 色彩标识 → 资产参数 → 朝向裁决 → 本回剧情功能 → 与同回角色的对照 → 边界。

---

## 数据来源与口径

| 用途 | 权威来源 |
| --- | --- |
| 外形设定原文 + 生图提示词 | `art/identity/character-designs.json` |
| 运行资产真实参数 | `public/assets/rongguo/manifest.json` 的 `assets` |
| 朝向裁决 | `design/character-facing.json` 的 `actors` |
| 运行时登记 | `src/story.ts` 的 `cast` |
| 底本正文 | `docs/chapter29-source.txt`（维基文库繁体本，OpenCC t2s，2026-11-25 取得） |
| 本回剧情 | `design/chapter29-story.json` |

三条通用口径：底本没给外貌就不冒充底本；立绘与 Q 版是两张独立图，朝向各自裁决；`faceBox` 在最终 PNG 坐标里。

---

## 张道士 `zhang_daoshi`

### 身份定位

清虚观住持 · 宝玉寄名的干爷

底本依据（逐字）：

「只见张道士站在旁边陪笑说道：“论理我不比别人，应该里头伺候。”」
「贾珍知道这张道士虽然是当日荣国府国公的替身，曾经先皇御口亲呼为“大幻仙人”」

### 外形锚点

`features`（设计推定，非底本原文）：
**清虚观住持，宝玉寄名的干爷；须发皆白，言辞谨慎恭敬，贾母称他「老神仙」。性别：男（底本称「老神仙」，为宝玉寄名的「干爷」）**。

英文生图提示词：a venerable white-bearded elderly MALE Taoist abbot in Qing-dynasty China, an old man and not a woman, with a long white beard, deep-set kind eyes and a respectful reserved expression, wearing a grey-blue Taoist robe with a wide sash and a small Taoist crown, thin and stooped with age。

### 色彩标识

身份标识色 `#9aa0a8`。地图上同框时以颜色区分，不与同场角色撞色。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 213×600 | 65×116 |
| anchor | `[120.342, 599.436]` | `[45.728, 115.444]` |
| faceBox | `[55, 57, 111, 100]` | `[13, 27, 49, 52]` |
| seed | 10239100 | 10239101 |
| bodyCompress | — | `{'split': 385, 'factor': 0.64}` |
| hash | `4cf8add8fb05` | `f86bc64a437c` |

### 朝向裁决

- portrait **right**（`vision-landmark-geometry`）
- chibi **right**（`visual-review`）

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 16 个节点涉及他，其中 11 个是他本人的台词节点（C29-044—C29-070）。

当日荣国府国公的替身，先皇御口亲呼「大幻仙人」，现掌「道录司」，本回回目人物。随贾珍入府给贾母请安，一见宝玉便说「怎么就同当日国公爷一个稿子」并落泪；又为宝玉提亲；请下通灵宝玉要「请下来」给远来的道友徒子看，并说自己是「八十多岁的人」——本回他占去最多台词。

他的第一句台词是：「无量寿佛！老祖宗一向福寿安康？众位奶奶小姐纳福？一向没到府里请安，老太太气色越发好了。」


### 与同回角色的对照

与贾珍（jia_zhen）、凤姐（feng）同场：贾珍是主人家、凤姐是打趣的，张道士是外客兼寄名干爷，说话始终带三分谨慎。

### 边界

与清虚观「张法官」不是同一人：张法官是带道士迎接的执行者，只在叙述里出现。

---
