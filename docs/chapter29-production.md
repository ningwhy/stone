# 第 29 回制作记录

## 目标与来源

- **回目全名**：第二十九回　享福人福深还祷福　痴情女情重愈斟情
- **底本/版本/来源地址/取得日期**：
  - 版本：维基文库《紅樓夢》第 029 回，程乙本/高鹗本整理稿（繁体）
  - 来源地址：<https://zh.wikisource.org/w/index.php?title=紅樓夢/第029回&action=raw>
  - 取得日期：2026-11-25
  - 处理：OpenCC t2s 转简体，去导航/样式/许可页脚，按维基段落拆行；正文未作增删
  - 底本行 35 的戏名带维基内部链接标记（`《[[白蛇记]]》`、`《[[满床笏]]》`、`《[[南柯梦]]》`），
    那是导航 markup 不是正文：只在**展示用正文**里去掉方括号，`paragraphLead` 保留底本原样，
    以满足 `check_content.mjs` 的逐字校验
- **本地正文**：`docs/chapter29-source.txt`（24 段，段 0 为回目行，**正文段 1–23**）
- **剧情、段落、证据**：`design/chapter29-story.json`、`chapter29-sections.json`、`chapter29-evidence.json`
- **生成器**：`scripts/build_chapter29.py`（沿用第 23–25 回「底本切片 + 标题回锚自愈 + 引号边界」）
- **地图生成器**：`scripts/build_chapter29_maps.py`
- **本回开始/结束、与前后回衔接**：
  - 接第 28 回结尾「宝玉正自发怔，不想黛玉将手帕子甩了来」——本回开篇即这一段
  - 止于袭人劝宝玉「你正经下个气，陪个不是……要知端详，且听下回分解」，第 30 回的起手
- **实际出场 / 转述人物**：
  - **有台词登场（新增 1 人）**：张道士 `zhang_daoshi`（清虚观当家道人，国公替身、掌道录司印）
  - **复用已登记角色且有台词**：宝玉、黛玉、宝钗、凤姐、贾母、薛姨妈、王夫人、贾珍、贾蓉、袭人、紫鹃、周瑞家的
  - **复用已登记但只登场无台词**：平儿、鸳鸯、小红、迎春、探春、惜春、李纨、薛蟠
  - **提及未登场、不入 cast**：小道士（撞凤姐、贾母怜而放走）、林之孝（管家）、贾璜/贾萍/贾芹/贾琼（墙根下溜上来）、
    冯家两个管家娘子、赵侍郎、贾珍贾蓉的妻子婆媳、张法官（带众道士迎接）、奶子与大姐儿/巧姐儿、
    丫鬟名单里的春纤/文杏/司棋/绣桔/侍书/翠墨/入画/彩屏/同喜/同贵/臻儿/素云/碧月/丰儿/金钏/彩云
  - **画外**：结尾贾母「不是冤家不聚头」由叙述转述；黛玉在潇湘馆、宝玉在怡红院「人居两地，情发一心」，
    二人虽同回耳闻却**不同台**
- **梦境 / 现实 / 回忆场景**：全回为 `present` 现实层，无梦层。

---

## 分场表（事件覆盖表）

| 原文起句或事件 | 时间层 | 段落 / 节点 | 地点 / scene | 在场人（speaker） | 压缩/改写说明 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 宝玉发怔，黛玉甩手帕、比呆雁失手 | present | `c29-shoupa` / C29-001… | `yihong` 怡红院 | 叙述、黛玉 | 接第 28 回结尾 | 已生成 |
| 凤姐约看戏，宝钗推热不去；凤姐要赶道士扫楼 | present | `c29-yuexi` | `entry` 贾母院 | 叙述、宝钗、凤姐 | 「一个闲人不许放进庙去」照录 | 已生成 |
| 贾母同去、正面楼/旁边楼；请薛姨妈、传话园里 | present | `c29-yuexi`（同段） | `entry` | 叙述、贾母 | 「老祖宗也去，敢情好了」照录 | 已生成 |
| 初一出门，车辆纷纷；周瑞家的喝止说笑 | present | `c29-shanglu` | `capital` 宁荣街 | 叙述、周瑞家的 | 丫鬟名单择要 show | 已生成 |
| 观前钟鸣鼓响，张法官带道士迎接；贾母住轿看圣像 | present | `c29-shanmen` | `qingxu_guan`（新建） | 叙述、贾珍 | 钟楼/山门锚点 | 已生成 |
| 小道士撞凤姐，凤姐一掌打筋斗；贾母怜而命贾珍放走 | present | `c29-shanmen`（同段） | `qingxu_guan` | 叙述、凤姐、贾母 | 小道士不入 cast，用叙述 | 已生成 |
| 贾珍阶矶问管家，喝命啐贾蓉；贾蓉从钟楼跑出乘凉 | present | `c29-guanjia` | `qingxu_guan` | 贾珍、叙述 | 林之孝等点名不上台 | 已生成 |
| 张道士陪笑求示下，贾珍大笑引进 | present | `c29-zhangdao` | `qingxu_guan` | 叙述、贾珍 | **张道士首次登场** | 已生成 |
| 张道士请安、问宝玉、说像国公爷；贾母落泪 | present | `c29-qingan` | `qingxu_guan` | 张道士、贾母 | 「无量寿佛」「一个稿子」照录 | 已生成 |
| 张道士提亲，贾母以「命里不该早娶」回绝 | present | `c29-tiqin` | `qingxu_guan` | 张道士、贾母 | 为结尾宝黛大闹埋伏笔 | 已生成 |
| 凤姐讨寄名符、笑张道士「化布施」；贾母骂猴儿 | present | `c29-fufu` | `qingxu_guan` | 凤姐、张道士、贾母 | 大殿取符，`M` 走 hall 路线 | 已生成 |
| 张道士请下通灵玉；还玉并送三五十件法器；宝玉要散钱 | present | `c29-qingyu` | `qingxu_guan` | 张道士、贾母、宝玉 | 「请玉」「贺物」两段合并 | 已生成 |
| 上楼归坐，正面楼/东楼/西楼；神前拈戏三本 | present | `c29-loushang` | `qingxu_guan` | 叙述、贾珍、贾母 | 三本戏名照录，去 `[[...]]` | 已生成 |
| 赤金点翠麒麟，宝钗记湘云有；黛玉冷笑，宝玉揣又掏 | present | `c29-qilin` | `qingxu_guan` | 叙述、宝钗、探春、黛玉、宝玉 | 「金玉」试探的伏线 | 已生成 |
| 冯家等送礼，贾母后悔；次日执意不去，凤姐自去 | present | `c29-songli` | `qingxu_guan` | 叙述、凤姐、贾母 | 送礼名单择要 | 已生成 |
| 宝玉黛玉口角升级，摔玉砸玉；紫鹃雪雁袭人夺玉 | present | `c29-danao` | `xiaoxiang` 潇湘馆 | 叙述、黛玉、宝玉、袭人 | **本回高潮**，anger effect | 已生成 |
| 黛玉吐药，四人无言对泣；黛玉剪玉穗 | present | `c29-danao`（同段） | `yihong` | 叙述、袭人、紫鹃 | 「不如来砸我」照录 | 已生成 |
| 老婆子回报，贾母王夫人进园，移祸袭人紫鹃；带出宝玉 | present | `c29-danao`（同段） | `yihong` | 叙述、贾母、王夫人 | 高潮收束 | 已生成 |
| 薛蟠生日，宝玉推病、黛玉后悔；贾母怨「不是冤家不聚头」 | present | `c29-huiyi` | `entry` 贾母院 | 叙述、贾母 | 贾母抱怨照录 | 已生成 |
| 二人闻俗语潸然泣下，虽不会面而情发一心；袭人劝宝玉 | present | `c29-quanbao` | `yihong` | 叙述、袭人 | 黛玉不同台，只叙述 | 已生成 |

---

## 地图、人物、资产

| ID | 新建或复用 | 来源或生成器 | 尺寸 / 锚点 | 状态 |
| --- | --- | --- | --- | --- |
| `qingxu_guan`（清虚观 · 打醮与看戏） | **新建** | `scripts/build_chapter29_maps.py` | 40×40 / 13 锚点 | 已生成；`check:anchors` 与 `map:framing` 通过 |
| `xiaoxiang` | 复用 | 第 26 回新建 | 40×40 / 8 锚点（gate/window_out/door/bed/chair/desk_place/zijun_place/nurse_place） | 可直接用 |
| `yihong` | 复用 | 第 21 回新建 | 40×40 / 17 锚点 | 可直接用 |
| `entry` | 复用 | 基础地图 | 40×40 / 30 锚点 | 可直接用 |
| `capital` | 复用 | 基础地图 | 40×40 / 5 锚点 | 可直接用 |
| `zhang_daoshi`（张道士） | **新增人物** | 已登记 cast / manifest / 美术 | 立绘 600 / Q 版 116 | 已登记，见 `docs/chapter29-characters.md` |

**新 scene（已登记进 `design/scene-places.json`）**：

- `sceneId` = `qingxu_guan`
- 中文名 = `清虚观 · 打醮与看戏`
- 锚点 = `[street, shanmen, ermen, court, main_tower, east_tower, west_tower, stage, zhang_seat, bell_tower, steps, hall_door, hall]`
- theme = `garden`；level/region/col/row 由主 agent 按既有 5 层 10 区域口径补配

---

## 设计推定（写进证据表 design 条目）

| ID | 段落 | 推定 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| C29-D1 | `c29-shanmen` | 新建 `qingxu_guan`，不复用三张佛寺图 | 底明明写张道士、道录司、寄名符、传道法器，是道观；`c15_tiejian`/`c15_shuiyue`/`zhitong` 都是佛寺，且都没有钟楼/阶矶/正面楼·东楼·西楼/戏台 | 新建 13 锚点 |
| C29-D2 | `c29-danao` | 宝黛大闹复用 `xiaoxiang`（潇湘馆） | 底本段 15 宝玉来病中的黛玉房里问安、段 20 贾母王夫人「进园来瞧」、段 22「一个在潇湘馆临风洒泪」；第 26 回已建 `xiaoxiang`，8 锚点全通 | 用 `bed`/`chair`/`zijun_place`/`door`/`gate`/`window_out`，不新建 |
| C29-D3 | `c29-yuexi`/`c29-huiyi` | 约戏与贾母抱怨放 `entry` | 底本段 2、22 均在贾母处 | 用 `grandmother_seat`/`feng_meet`/`xing_seat` 等 |
| C29-D4 | `c29-shanglu` | 出门车辆放 `capital` | 底本「荣国府门前车辆纷纷」「这是街上，看人笑话」 | 用 `rong_gate`/`street_west` |
| C29-D5 | `c29-zhangdao` | 张道士是唯一新角色，只列报告 | 底本段 7–12 有大段台词，必须可见 | 建议 id `zhang_daoshi`，由主 agent 统一登记 |
| C29-D6 | `c29-shanmen` | 小道士、林之孝、冯家管家娘子、贾璜/贾琼/贾萍不入 cast | 只在叙述里点名或只有传话，按第 24、25 回「提及不登场」先例 | 不 show、不注册 |
| C29-D7 | `c29-loushang` | 三本戏名照录 | 底本段 13 明写《白蛇记》《满床笏》《南柯梦》 | 只去掉维基 `[[...]]` 标记，不改字 |
| C29-D8 | `c29-guanjia` | 钟楼无专用美术资产 | manifest 无 bell/tower 类资产，底本只说贾蓉「从钟楼里跑了出来」 | 用 `bell_tower` 锚点 + Labels「钟楼」交代地点 |
| C29-D9 | `c29-quanbao` | 结尾黛玉不 show | 底本「虽不曾会面」，二人分居两地 | 该节点只 show 宝玉，黛玉用叙述 |
| C29-D10 | `c29-danao` | 摔玉用 `anger` effect | 底本段 17「咬牙恨命往地下一摔」；effect.kind 合法值仅五种 | 用 `E:baoyu:anger:2.0`，不发明新 kind |
| C29-D11 | `c29-songli` | 送礼/丫鬟名单择要 show | 底本罗列数十人，逐一点名会塞满舞台 | 只 show 已登记且有戏份者 |
| C29-D12 | `c29-qingyu` | 寄名符、法器、通灵玉只作叙述道具 | 底本段 10–12 都是物件，无台词 | 旁白照录，focus 落 `court`/`main_tower` |

---

## 新角色清单（cast 与美术已登记，视觉设定见 `docs/chapter29-characters.md`）

| 建议 id | 中文名 | 一句话视觉设定（含服饰色彩） | 底本依据 |
| --- | --- | --- | --- |
| `zhang_daoshi` | 张道士 | 清虚观当家道人，八十余岁，鹤发白须，头戴道冠，身穿**月白**道袍、外罩**玄色**鹤氅，手持拂尘，面容慈和而精明；主色月白、玄黑、赭石。 | 段 7「只见张道士站在旁边陪笑说道」、段 11「看著小道是八十多岁的人」、段 12「两眼流下泪来」；底本无具体服饰描写，服饰色彩为视觉设计推定。 |

> 底本对张道士**没有一句外貌描写**，上表的鹤发白须、道袍鹤氅、拂尘与配色均为视觉设计推定，
> 不得冒充原著记载。具体 prompt / features 请主 agent 在 `art/identity/character-designs.json`
> 等权威表里一并登记。

---

## 不入 cast 的本回人物

| 人物 | 出处 | 处置 |
| --- | --- | --- |
| 小道士 | 段 4–5，撞凤姐、被贾母怜而放走 | 只叙述，不 show |
| 林之孝 | 段 6，贾珍问管家 | 只叙述，不 show |
| 贾璜、贾萍、贾芹、贾琼 | 段 6，墙根下溜上来 | 只叙述（贾芹已在 cast，本回无台词） |
| 冯家两个管家娘子、赵侍郎 | 段 14，送礼 | 只叙述 |
| 贾珍贾蓉的妻子婆媳 | 段 14，上楼见贾母 | 只叙述 |
| 张法官 | 段 4，带众道士迎接 | 只叙述 |
| 一众丫鬟/奶子/大姐儿/巧姐儿 | 段 4 名单 | 择要 show 已登记者，其余只叙述 |

---

## 验收清单

- [x] `python3 scripts/build_chapter29_maps.py` —— `maps/qingxu_guan.tmj` 写出（13 锚点）
- [x] `python3 scripts/build_chapter29.py` —— 127 节点 / 16 段 / 139 证据，写盘前自校通过
- [x] `python3 scripts/build_chapter29.py --check` —— 通过
- [x] `npm run check:anchors` —— 415 route anchors 全通（含新图）
- [x] `npm run map:framing` —— 0 framing problem(s)
- [x] `npm run check:content` —— 通过（chapter29 尚未由主 agent 注册，显示为 unregistered draft）
- [ ] 主 agent：登记 `zhang_daoshi` 到 `src/story.ts` cast 与 `public/assets/rongguo/manifest.json`
- [ ] 主 agent：`src/story.ts` import `script29`/`sections29` → 拼 story/chapters → `bookNames`
- [ ] 主 agent：`design/chapter-titles.json` 加回目联；`check_content.mjs` 的 `VERBATIM_BASE` 加 29
- [ ] 主 agent：`design/scene-places.json` 补 `qingxu_guan` 方位
- [ ] 主 agent：新角色美术（立绘/Q 版/facing/faceBox/WebP）与 `tests/chapter29.mjs`、线上定向
- [ ] 主 agent：全链回归与上线
