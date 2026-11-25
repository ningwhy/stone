# 第 30 回制作记录

## 目标与来源

- **回目全名**：第三十回　宝钗借扇机带双敲　龄官划蔷痴及局外
- **底本/版本/来源地址/取得日期**：
  - 版本：维基文库《紅樓夢》第 030 回，程乙本/高鹗本整理稿（繁体）
  - 来源地址：<https://zh.wikisource.org/w/index.php?title=紅樓夢/第030回&action=raw>
  - 取得日期：2026-11-25
  - 处理：`scripts/fetch_chapter_source.py 30` → OpenCC t2s 转简体，去导航/样式/许可页脚，按维基段落拆行；正文未作增删
- **本地正文**：`docs/chapter30-source.txt`（回目行 + 正文 17 段；底本切片时 para 0 为回目行，正文 para 1–17）
- **剧情、段落、证据**：`design/chapter30-story.json`、`chapter30-sections.json`、`chapter30-evidence.json`
- **生成器**：`scripts/build_chapter30.py`（沿用第 24/25 回「底本切片 + 标题回锚自愈 + 引号边界」）
- **地图生成器**：`scripts/build_chapter30_maps.py`（新建 `qiangwei` 蔷薇花架）
- **本回开始/结束、与前后回衔接**：
  - 接第 29 回（黛玉与宝玉口角后自悔，紫鹃劝解），本回开篇「话说林黛玉与宝玉角口后，也自后悔」正接这一处
  - 止于宝玉误踢袭人、夜间秉灯照见一口鲜血（「要知端的，且听下回分解」），为第 31 回「撕扇子作千金一笑」的伏笔
- **实际出场 / 转述人物**：
  - **有台词登场（新增 1 人）**：龄官 `lingguan`（十二个学戏的女孩子之一，本回「画蔷的女孩子」，有动作与一句台词）
  - **复用已登记角色且有台词**：黛玉、紫鹃、宝玉、凤姐、贾母、宝钗、王夫人、金钏儿 `jinyuan`、麝月 `she_yue`
  - **复用已登记但只登场无台词**：袭人（有台词）、无
  - **提及未登场、不入 cast**：靛儿（找扇子两句台词归旁白）、晴雯（「胡说！宝姑娘这会子做什么来」归旁白；cast 中 `qiuwen` 是秋纹不是晴雯）、玉钏儿、白老媳妇、彩云、贾环、宝官、玉官、文官等十二女子
  - **正文未出现**：贾蔷 —— 只在回目「龄官划蔷」里出现「蔷」字（画的是蔷薇花的「蔷」），本回正文无此人，不 show、不登记
- **梦境 / 现实 / 回忆场景**：全回为 `present` 现实层；段 14 端阳节十二女子放学玩耍是当下情形的叙述，不单开时间层

---

## 事件覆盖表

| 原文起句或事件 | 时间层 | 段落 / 节点 | 地点/scene | 在场人（speaker） | 压缩/改写说明 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 黛玉角口后自悔，紫鹃劝其勿浮躁 | present | `c30-zijuan` / C30-001… | `night` 黛玉房 | 叙述、紫鹃、黛玉 | 「若论前日之事，竟是姑娘太浮躁了些」照录 | 已接入 |
| 院外叫门，紫鹃开门，宝玉赔不是 | present | `c30-zijuan`（同段） | `night` | 叙述、紫鹃、黛玉、宝玉 | 「我便死了，魂也要一日来一百遭」照录 | 待接入 |
| 宝玉「你死了我做和尚」，黛玉变脸 | present | `c30-peibushi` / C30-011… | `night` | 叙述、宝玉、黛玉 | 「你死了，我做和尚！」照录 | 待接入 |
| 黛玉戳额、摔帕、拉手摔手 | present | `c30-chuo` / C30-021… | `night` | 叙述、黛玉、宝玉 | 「我的五脏都碎了，你还只是哭」照录 | 待接入 |
| 凤姐跳进来说合，拉黛玉去贾母跟前 | present | `c30-fengjie` / C30-027… | `night` → `dinner` | 叙述、凤姐 | 「黄鹰抓住了鹞子的脚」照录 | 待接入 |
| 贾母跟前凤姐说合，满屋笑 | present | `c30-jiamu` / C30-032… | `dinner` 贾母院 | 叙述、凤姐、贾母、黛玉、宝玉 | 场景在此切换为 `dinner` | 待接入 |
| 宝玉向宝钗赔不是、问看戏；比杨妃 | present | `c30-yangfei` / C30-036… | `dinner` | 叙述、宝玉、宝钗 | 「怪不得他们拿姐姐比杨妃，原来也体丰怯热」照录 | 待接入 |
| 宝钗怒答杨国忠；靛儿找扇借题发挥 | present | `c30-yangfei`（同段） | `dinner` | 叙述、宝钗 | 靛儿台词归旁白，只 show 宝钗 | 待接入 |
| 负荆请罪与凤姐「吃生姜」双敲 | present | `c30-fujing` / C30-045… | `dinner` | 叙述、黛玉、宝钗、宝玉、凤姐 | 「你们大暑天，谁还吃生姜呢？」照录 | 待接入 |
| 宝钗凤姐去，黛玉讥宝玉，宝玉无精打采出来 | present | `c30-chulai` / C30-053… | `dinner` | 叙述、黛玉、宝玉 | 「你也试著比我利害的人了」照录 | 待接入 |
| 宝玉出贾母院，过穿堂进王夫人上房 | present | `c30-wangfuren` / C30-057… | `wang` 王夫人上房 | 叙述、宝玉、王夫人、金钏儿 | 「王夫人在里间凉榻上睡著，金钏儿坐在旁边捶腿」照录 | 待接入 |
| 宝玉摘坠子、送润津丹、讨金钏儿 | present | `c30-jinchu` / C30-062… | `wang` | 叙述、宝玉、金钏儿 | 「金簪子掉在井里头，有你的只是有你的」照录 | 待接入 |
| 王夫人翻身打骂，宝玉一溜烟去了 | present | `c30-jinchu`（同段） | `wang` | 叙述、王夫人、宝玉 | 「下作小娼妇，好好的爷们，都叫你教坏了」照录 | 待接入 |
| 金钏儿跪哭苦求，仍被撵出 | present | `c30-nianchu` / C30-072… | `wang` | 叙述、王夫人、金钏儿 | 「别叫我出去就是天恩了」照录 | 待接入 |
| 宝玉进大观园，隔篱笆洞儿看龄官划蔷 | present | `c30-qiangwei` / C30-078… | `qiangwei` 蔷薇花架（本回新建） | 叙述、宝玉、龄官 | **龄官本回首次登场**；「画来画去，还是个蔷字」照录 | 待接入 |
| 阵雨落下，龄官误认宝玉为丫头提醒避雨 | present | `c30-yu` / C30-093… | `qiangwei` | 叙述、宝玉、龄官 | 「多谢姐姐提醒了我。难道姐姐在外头有什么遮雨的？」照录 | 待接入 |
| 宝官玉官在怡红院玩水关院门；宝玉叫门 | present | `c30-guamen` / C30-099… | `yihong` 怡红院 | 叙述、袭人、宝玉、麝月 | 晴雯台词归旁白，不 show | 待接入 |
| 宝玉误踢开门的袭人，二人对话 | present | `c30-ti` / C30-109… | `yihong` | 叙述、宝玉、袭人 | 「我长了这么大，今日是头一遭儿生气打人」照录 | 待接入 |
| 夜间秉灯照见地下口鲜血 | present | `c30-tuxue` / C30-118… | `yihong` | 叙述、宝玉、袭人 | 本回收束；「要知端的，且听下回分解」照录 | 待接入 |

---

## 地图、人物、资产

| ID | 新建或复用 | 来源或生成器 | 尺寸/锚点 | 状态 | 证据截图 |
| --- | --- | --- | --- | --- | --- |
| `night` | 复用（第 21 回起用于黛玉房） | `scripts/build_chapter_maps.py` | 40×40 / 10 锚点（daiyu_bed/bedside/night_talk/outer_room） | 可直接用 | — |
| `dinner` | 复用（贾母院宴集） | `scripts/build_chapter_maps.py` | 40×40 / 13 锚点（grandmother_place/daiyu_place/feng_place/tea_place/baoyu_greet） | 可直接用 | — |
| `wang` | 复用 | `scripts/build_chapter_maps.py` | 40×40 / 11 锚点（wang_host/kang_edge/guest_seat/hall_entry） | 可直接用 | — |
| `yihong` | 复用（第 21 回新建） | `scripts/build_chapter21_maps.py` | 40×40 / 17 锚点（yard/gate_step/outer_room/xiren_kang/baoyu_kang） | 可直接用 | — |
| `qiangwei` | **新建**（`scripts/build_chapter30_maps.py`） | 蔷薇花架：底本写「蔷薇正是花叶茂盛」「隔著篱笆洞儿一看，只见一个女孩子蹲在花下……在地下画字」 | 40×40 / 5 锚点（garden_path/fence_hole/outside_trellis/under_trellis/rose_bush） | 已生成，待补 `scene-places.json` | — |
| `lingguan`（龄官） | **新增人物** | id `lingguan`；底本无正面姓名与外貌描写（只写「面薄腰纤，袅袅婷婷，大有林黛玉之态」「倒象是那十二个学戏的女孩子之内的」） | 立绘 600 / Q 版 116 | 已登记，见 `docs/chapter30-characters.md` | — |

> `qiangwei` 的 sceneId、中文名与锚点见文末报告；主 agent 需补 `design/scene-places.json` 的方位条目（level/region/col/row/name）。美术只生成龄官一人，不预先多生成。

---

## 设计推定（写进证据表 design 条目）

| ID | 段落 | 推定 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| C30-D1 | `c30-zijuan` | 紫鹃劝解与宝玉赔不是放 `night`（黛玉房） | 底本段 1–4 全在黛玉房内：黛玉「在床上哭」、宝玉「挨在床沿上坐了」、戳额递帕；第 21/22 回黛玉房即用 `night` | 用 `daiyu_bed`/`bedside`/`night_talk`/`outer_room`，不新开潇湘馆专图 |
| C30-D2 | `c30-jiamu` | 贾母院看戏说合复用 `dinner` | 底本「到了贾母跟前」「姐姐怎么不看戏去」，是贾母处众姊妹聚坐看戏 | 用 `grandmother_place`/`daiyu_place`/`feng_place`/`baoyu_greet`/`tea_place` |
| C30-D3 | `c30-yangfei` | 靛儿不入 cast，台词归旁白 | 小丫头，只在找扇子时说两句话；按「提及不登场/配角台词归旁白」先例 | speaker 用 narrator，只 show 宝钗 |
| C30-D4 | `c30-wangfuren` | 金钏儿调笑与被撵放 `wang` | 底本「来到王夫人上房内……金钏儿坐在旁边捶腿」，同一室内 | 用 `wang_host`/`kang_edge`/`guest_seat`/`hall_entry` |
| C30-D5 | `c30-qiangwei` | 龄官划蔷新建 `qiangwei` | 底本明写「蔷薇花架」「篱笆洞儿」「在地下画字」；`qinfang` 是水闸桃林，语义冲突 | 新建 5 锚点、一条 main 动线，`check:anchors`/`map:framing` 已过 |
| C30-D6 | `c30-qiangwei` | 龄官 `lingguan` 为本回新角色 | 段 12 有动作、段 13 有台词；正面姓名本回未出，底本无外貌描写 | id `lingguan`，cast 与美术已登记；视觉设定标「设计推定」 |
| C30-D7 | `c30-guamen` | 怡红院关门、误踢、夜间见血均在 `yihong` | 底本「正在怡红院和袭人玩笑……将院门关了」「抬腿踢在肋上」「至晚间洗澡时脱了衣服」 | 用 `yard`/`gate_step`/`outer_room`/`xiren_kang`/`baoyu_kang` |
| C30-D8 | `c30-guamen` | 麝月在 cast；晴雯等不入 cast | 麝月「是宝姑娘的声音」照录并 show；cast 中 `qiuwen` 是秋纹不是晴雯，晴雯从未登记 | 晴雯台词作 narrator 节点，不 show、不注册新 cast |
| C30-D9 | `c30-nianchu` | 玉钏儿、白老媳妇、彩云、贾环、贾蔷不入 cast | 玉钏儿/白老媳妇只被叫来领人；彩云、贾环在台词里提及；**贾蔷本回正文未出场**（「划蔷」是画蔷薇的「蔷」） | 只在正文保留名字，不 show、不新建节点 |
| C30-D10 | `c30-qiangwei` | 蔷薇花架美术用 garden-tree / bamboo-gate 承担 | 底本只写「花叶茂盛」「篱笆洞儿」，本项目无蔷薇专素材 | 以 `garden-tree` 成片代花荫、`bamboo-gate` 代篱笆洞、`wood-screen` 代篱笆，标「设计推定」 |

---

## 新角色清单（cast 与美术已登记，视觉设定见 `docs/chapter30-characters.md`）

| 建议 id | 中文名 | 身份 | 一句话视觉设定（含服饰色彩） | 底本依据 / 推定边界 |
| --- | --- | --- | --- | --- |
| `lingguan` | 龄官 | 十二个学戏的女孩子之一（小生），在蔷薇花架下划蔷 | 身量纤细、眉目含愁的少女戏子，藕荷色水袖戏衣配月白中衣，乌发垂鬟、鬓边一支素银簪；蹲地时以手中绾头金簪画字，整体色调偏淡青与藕粉，与黛玉的竹青、宝钗的浅碧区分 | 底本只写「面薄腰纤，袅袅婷婷，大有林黛玉之态」「倒象是那十二个学戏的女孩子之内的」；**正面姓名、行当与服饰颜色均为设计推定**，不可冒充原著记载 |

---

## 验收与上线清单

- [x] `python3 scripts/build_chapter30_maps.py` —— `maps/qiangwei.tmj` 已写出（5 锚点）
- [x] `npm run check:anchors` —— 402 路线锚点全通（含新图 `qiangwei` 的 5 个）
- [x] `npm run map:framing` —— 0 framing problem(s)
- [x] `python3 scripts/build_chapter30.py` —— 126 节点 / 16 段 / 136 证据，自校通过
- [x] `python3 scripts/build_chapter30.py --check` —— 校验通过
- [x] 生成器自校保留：节点 id 唯一、底本位置单调、正文与 paragraphLead 逐字可查、focus 非空、move 前必须 show
- [x] 探针文件名 `artifacts/probe_walkable_tmp_c30.mjs`（与其他 agent 隔离）
- [ ] 美术：龄官 `lingguan` 立绘/Q 版 → 校准 → faceBox → facing → WebP 成对（主 agent）
- [ ] 注册 `lingguan` 到 `src/story.ts` 的 cast（主 agent）
- [ ] `src/story.ts`：import script30/sections30 → 拼 story/chapters → `bookNames` 加 `"30":"第三十回"`（主 agent）
- [ ] `design/chapter-titles.json` 加回目联；`check_content.mjs` 的 `VERBATIM_BASE` 加 30（主 agent）
- [ ] `design/scene-places.json` 补新 scene 方位（`qiangwei`，主 agent）
- [ ] 全链验收：`check:content` → `tsc` → `npm test` → `test:locator` → `build` → 定向测试 → `browser-smoke`（主 agent）
