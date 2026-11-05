# 第十一回制作记录 · 庆寿辰宁府排家宴 见熙凤贾瑞起淫心

> 状态：**已完成并接入** —— 通过内容门禁、单元测试、生产构建、取景门禁与浏览器冒烟。

## 目标与来源

- 回目全名：第十一回 · 庆寿辰宁府排家宴 · 见熙凤贾瑞起淫心
- 底本：网络公共文本（gb18030）抓取；本地正文 `docs/chapter11-source.txt`（19 段 / 5739 字）
- 剧情、段落：`design/chapter11-story.json`（49 节点）、`design/chapter11-sections.json`（9 段）
- 衔接：紧接第十回张太医论病；贾敬寿辰宁府排家宴，凤姐探秦氏，园中遇贾瑞，第十二回接相思局。
- 实际出场：尤氏、贾珍、贾蓉、凤姐、宝玉、秦可卿、贾瑞、平儿、邢王二夫人（列名不逐一造人）。转述不出场：贾敬（只在宁府烧丹、寿辰由贾珍备礼转述）、贾琏（只列名）、尤氏的母亲（只列名）、冯紫英（只列名）、南安郡王等（只由贾蓉回话）。

## 事件覆盖表

| 原文起句 | 时间层 | 段落 | 地点/scene | 在场人 | 压缩/改写说明 |
| --- | --- | --- | --- | --- | --- |
| 贾敬寿辰，贾珍备十六大捧盒着贾蓉送去 | present | c11-birthday | 宁府/c5_ningfu | 尤氏、贾珍、贾蓉 | 贾敬本人不登场，改由贾珍、贾蓉当场交代 |
| 邢王二夫人、凤姐、宝玉到宁府 | present | c11-guests | 宁府/c5_ningfu | 尤氏、凤姐、宝玉 | 宾客名单原文很长，压成在场三人 + 叙述带过 |
| 尤氏说起秦氏之病 | present | c11-illness | 宁府/c5_ningfu | 尤氏、凤姐、贾珍 | 「治得病治不得命」全句保留 |
| 饭毕贾蓉回话，各家王爷送寿礼来 | present | c11-gifts | 宁府上房/c5_ningfu | 贾蓉、尤氏 | 新增段落（2026-11-02）：饭毕贾蓉回尤氏「四家王爷并六公八侯持名帖送寿礼来，收在帐房、礼单上档」 |
| 凤姐探病，秦氏自道心事 | present | c11-visit | 秦氏卧房/c5_ningfu | 凤姐、秦可卿、宝玉、贾蓉 | 宝玉见《海棠春睡图》出神一段标 `recollection` |
| 凤姐自园中便门出来，贾瑞从假山石后走出 | present | c11-garden | 会芳园/c5_ningfu | 凤姐、贾瑞 | 「猛然从假山石后走出」按原文位置演出 |
| 点了一出《还魂》、一出《弹词》 | present | c11-opera | 天香楼/c11_tianxiang | 尤氏、凤姐 | 戏文名保留；舞台为新做资产 |
| 冬至前后，再看秦氏 | present | c11-winter | 宁府/c5_ningfu | 尤氏、凤姐 | 原文「这年正是十一月三十日冬至」的时间推移 |
| 平儿报信 | present | c11-ping | 凤姐院/c6_wangchui | 凤姐、平儿 | 收束到凤姐院，为第十二回开门 |

## 地图、人物、资产

| ID | 新建或复用 | 来源 | 状态 |
| --- | --- | --- | --- |
| c11_tianxiang（天香楼 · 戏台与看楼） | **新建场景** | `scripts/build_chapter11.py` 写入 `maps/c11_tianxiang.tmj` | theme=interior，5 锚点（gate/yard/stair/box/stage） |
| **stage-platform（戏台）** | **新做资产** | `scripts/furniture_sources.py`（seed 10243101）→ `furniture_bgremoval.py` → `art/calibration.json`（width 420 / anchor [500,913]）→ `build_art_assets.py` | 420×438，实心占比 0.981，已入 manifest 与 WebP |
| c5_ningfu（宁国府） | 复用 | 第五回已建 | 会芳园 / 上房 / 秦氏卧房 |
| c6_wangchui（凤姐院） | 复用 | 第六回已建 | 平儿报信一段 |
| you_shi / jia_zhen / jin_shi / hu_shi / zhang_youshi / jia_qiang / jia_dairu | 新人物·已立绘 | 与旧 45 人同一管线（Z-Image turbo + 风格锚点 + qwen21 抠图 + 重测锚点） | 7 人 × (portrait + chibi) = 14 张，全部入册 |

### 戏台为什么是新做的

截图目检发现「天香楼 · 点戏」那一段，**「戏台」两个字孤零零挂在空地上，标签指的东西根本不存在**——既有资产里没有一件戏台（`lantern-booth` 画的是竹架、没有灯，元宵灯市用得，当戏台就是空的）。这一件按项目既有的家具流水线补做：源图 → 抠图 → 标定 → 入册 → 转 WebP，与 `square-table`、`cabinet` 等同一路。

### 修掉的一个语义错配（C11-033）

原本 `C11-033` 写的是 `show('baoyu','portrait_wall')`。两处错：

1. `portrait_wall` 是**上房**挂《燃藜图》的那面墙（第五回 C05-013 起用它当镜头焦点）；而海棠春睡图挂在**秦氏卧房**，两处不是一间屋子。
2. `portrait_wall` 落在不可行走的格上（22,12），`show` 过去引擎直接报「显示地点不可通行」，于是**第十一回从这里往后的所有节点都走不动**——表现是单元测试里「贾代儒从未出场」（第十二回根本没跑到）。

改为 `focus='bedchamber'`，动作留空：C11-030 已经把宝玉摆在卧房里，这一段只是让他出神。

## 验证结果

- `npm run check:content` → 通过：853 节点 / 91 段 / 34 地图 / 58 人物 / 234 资产；第十一回 49 节点（含 2026-11-02 新增 `c11-gifts` 段 3 节点）。
- `npm test` → 65/65 通过。
- `npm run build` → tsc 无错 + vite 构建成功。
- `npm run map:framing` → 0 处取景问题。
- `npm run test:browser` → 通过。
- `scripts/build_chapter11.py` 内建 `verify_sources()`：本回 9 条 `paragraphLead` 逐条比对底本，0 条不匹配。

## 目检实际核对项

- 9 段各截一张（`artifacts/ch1012/c11-*.png`）。`c11-opera` 已确认戏台实体在位、与看楼座席无穿模、控制台无报错。
- 未逐张目检：本回 14 张新人立绘/Q 版中的多数，以及 c11_tianxiang 的家具摆位间距。

## 交接

- 第十一回已随 `src/story.ts` 的 `script11`/`sections11`、`bookNames[11]` 一并接入。
- 未做 `chapter11-evidence.json`（门禁不强制）。
