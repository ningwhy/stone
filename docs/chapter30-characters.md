# 第 30 回新出场一人 · 角色设计说明

《宝钗借扇机带双敲　龄官划蔷痴及局外》这一回有 1 人新进 `cast`：**龄官**（`lingguan`）。

本文件说明各人的设计依据、资产参数与本回叙事分工。每人八段，结构一致：身份定位 → 外形锚点 → 色彩标识 → 资产参数 → 朝向裁决 → 本回剧情功能 → 与同回角色的对照 → 边界。

---

## 数据来源与口径

| 用途 | 权威来源 |
| --- | --- |
| 外形设定原文 + 生图提示词 | `art/identity/character-designs.json` |
| 运行资产真实参数 | `public/assets/rongguo/manifest.json` 的 `assets` |
| 朝向裁决 | `design/character-facing.json` 的 `actors` |
| 运行时登记 | `src/story.ts` 的 `cast` |
| 底本正文 | `docs/chapter30-source.txt`（维基文库繁体本，OpenCC t2s，2026-11-25 取得） |
| 本回剧情 | `design/chapter30-story.json` |

三条通用口径：底本没给外貌就不冒充底本；立绘与 Q 版是两张独立图，朝向各自裁决；`faceBox` 在最终 PNG 坐标里。

---

## 龄官 `lingguan`

### 身份定位

梨香院十二官之一 · 唱小旦

底本依据（逐字）：

「“只见这女孩子眉蹙春山，眼颦秋水，面薄腰纤，袅袅婷婷，大有林黛玉之态”」
「“只见他虽然用金簪划地，并不是掘土埋花，竟是向土上画字”」

### 外形锚点

`features`（设计推定，非底本原文）：
**梨香院十二官之一，唱小旦；眉蹙目愁，气质清高孤傲；在蔷薇架下用金簪划「蔷」字，与贾蔷相恋。性别：女（第三十回正文明写「文官等十二个女子」「小生宝官，正旦玉官等两个女孩子」；龄官本回正面姓名未出，为回目及后文称呼）**。

英文生图提示词：a slender melancholy young actress WOMAN in Qing-dynasty China, a young female performer and not a man, with a pale oval face, finely knit brows, downcast eyes and a proud sensitive mouth, wearing a muted lavender-grey opera costume with narrow sleeves, hair in a simple stage bun with a single white flower。

### 色彩标识

身份标识色 `#a99ac4`。地图上同框时以颜色区分，不与同场角色撞色。

### 资产参数

| 项 | 立绘 | Q 版 |
| --- | --- | --- |
| 尺寸 | 172×600 | 59×116 |
| anchor | `[57.879, 599.455]` | `[33.948, 115.501]` |
| faceBox | `[38, 57, 89, 96]` | `[8, 41, 46, 67]` |
| seed | 10230100 | 10230101 |
| bodyCompress | — | `{'split': 392, 'factor': 0.64}` |
| hash | `a1b00c0f6e02` | `7f679c1ea5c0` |

### 朝向裁决

- portrait **right**（`vision-landmark-geometry`）
- chibi **right**（`visual-review`）

立绘与 Q 版是两张独立图，朝向各自裁决，不互相推断。

### 本回剧情功能

本回共 9 个节点涉及她，其中 1 个是她本人的台词节点（C30-097—C30-097）。

梨香院十二官之一，唱小旦，正面姓名本回未出。本回九节点全在蔷薇架下：蹲在花下拿金簪抠土、画字，「画来画去，还是个『蔷』字」「已经画了有几千个『蔷』」；骤雨落下来，黛玉在远处提醒她，她才回头道「多谢姐姐提醒了我」。

她的第一句台词是：「多谢姐姐提醒了我。难道姐姐在外头有什么遮雨的？」


### 与同回角色的对照

与金钏儿（jinyuan）、玉钏儿不同：金钏儿是被撵的旧人，龄官是梨香院在班的角儿；她的「蔷」字是自己的心事，不是谁的丫鬟闲话。

### 边界

「划蔷」的蔷是蔷薇，不是贾蔷；本回贾蔷并未登场，不能凭回目望文生义。

---
