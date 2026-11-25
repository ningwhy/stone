# 第 26 回制作记录

## 目标与来源

- **回目全名**：第二十六回　蜂腰桥设言传心事　潇湘馆春困发幽情
- **底本/版本/来源地址/取得日期**：
  - 版本：维基文库《紅樓夢》第 026 回，程乙本/高鹗本整理稿（繁体）
  - 来源地址：<https://zh.wikisource.org/w/index.php?title=紅樓夢/第026回&action=raw>
  - 取得日期：2026-11-25
  - 处理：OpenCC t2s 转简体，去导航/样式/许可页脚，按维基段落拆行；正文未作增删。两处 `<poem>` 标记在生成器里剥去，诗句一字不动。
- **本地正文**：`docs/chapter26-source.txt`（26 段，段 0 为回目行，正文段 1–25；含段 22/24 两首诗与段 23 过渡句）
- **剧情、段落、证据**：`design/chapter26-story.json`、`chapter26-sections.json`、`chapter26-evidence.json`
- **生成器**：`scripts/build_chapter26.py`（沿用第 24/25 回「底本切片 + 标题回锚自愈 + 引号边界 + last_focus 按场景记」）
- **地图生成器**：`scripts/build_chapter26_maps.py`（新建 `xiaoxiang`）
- **与前后回衔接**：
  - 接第 25 回（宝玉凤姐病愈、宝钗拿姻缘打趣、黛玉摔帘子出去）→ 第 26 回开篇「宝玉养过了三十三天之后……仍回大观园内去」
  - 止于黛玉在怡红院门外哭、「忽听『吱喽』一声，院门开处，不知是那一个出来。要知端的，且听下回分解」，留给第 27 回「滴翠亭杨妃戏彩蝶」
- **实际出场 / 转述人物**：
  - **有台词登场（新增 4 人）**：佳蕙、坠儿、晴雯、冯紫英（id 与视觉设定见下表；cast 与美术已登记，见 `docs/chapter26-characters.md`）
  - **复用已登记角色且有台词**：宝玉、小红/红玉、贾芸、袭人、李嬷嬷（`nurse_li`）、贾兰、黛玉、紫鹃、薛蟠、宝钗、焙茗（沿用 `ming_yan`）
  - **复用已登记但只登场无台词**：碧痕（段 21 与晴雯拌嘴）
  - **提及未登场、不入 cast**：黛玉的奶娘并两个婆子、未留头送花样的小丫头、唱曲儿的小么儿、古董行程日兴、清客詹光/程日兴/胡斯来/单聘仁、沈世兄、仇都尉之子、冯唐、贾政（被称「老爷/姨父」，只增援不露面）、云哥儿雨哥儿（李嬷嬷口中）
  - **画外/韵文**：段 22「花魂默默无情绪」与段 24「颦儿才貌世应希」两首贊诗，无说话人，照录为旁白念出的 `verbatim` 节点
- **梦境 / 现实 / 回忆场景**：全回为 `present` 现实层。第 25 回的魇魔法余波只作「养过了三十三天」的叙述交代，不单开回忆层。

---

## 分场表

| 段 id | 场景标题 | scene | 底本段 | 节点 | 主要内容 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| `c26-hongyu` | 怡红院 · 红玉与佳蕙 | `yihong` | 1–3 | C26-001…019 | 宝玉病愈回园；红玉与贾芸混熟、疑手帕；佳蕙送钱、劝医、怨晴雯绮霰；「千里搭长棚」 | 已生成 |
| `c26-yangzi` | 怡红院 · 描花样与取笔 | `yihong` | 4 前半 | C26-020…024 | 小丫头送绮霰花样；找笔、莺儿拿去、佳蕙不肯代取；红玉出院往宝钗处 | 已生成 |
| `c26-qinfang` | 沁芳亭 · 李嬷嬷说云哥儿 | `qinfang` | 4 后半 | C26-025…031 | 沁芳亭遇李嬷嬷；「云哥儿雨哥儿」；红玉叮嘱同来，李嬷嬷拄杖去了 | 已生成 |
| `c26-fengyao` | 蜂腰桥 · 四目相对 | `qinfang` | 5 | C26-032…035 | 坠儿带贾芸来；红玉与贾芸四目相对、脸红扭身往蘅芜苑 | 已生成 |
| `c26-yihong` | 怡红院 · 贾芸见宝玉 | `yihong` | 6–8 | C26-036…048 | 怡红快绿匾、镜后丫头、碧纱厨见宝玉；袭人倒茶；闲话告辞 | 已生成 |
| `c26-shoupa` | 怡红院外 · 坠儿传帕 | `yihong` | 9 | C26-049…054 | 贾芸盘问坠儿；认出小红遗帕，以己帕相授、索谢礼 | 已生成 |
| `c26-chuguang` | 怡红院 · 宝玉出逛与贾兰射鹿 | `yihong` | 10–11 | C26-055…062 | 袭人拉宝玉出房；沁芳溪看鱼；贾兰演习骑射、宝玉调侃 | 已生成 |
| `c26-xiaoxiang` | 潇湘馆 · 春困发幽情 | `xiaoxiang`（**新建**） | 12–15 前半 | C26-063…077 | 「每日家情思睡昏昏」；黛玉装睡、婆子进来；紫鹃倒茶；「若共你多情小姐同鸳帐」惹哭黛玉 | 已生成 |
| `c26-jiaozheng` | 荣府二门 · 老爷叫宝玉 | `entry` | 15 后半 | C26-078…082 | 袭人传「老爷叫你」；焙茗二门等候催行 | 已生成 |
| `c26-xuepan` | 薛蟠书房 · 寿礼与唐寅 | `c4_lixiang` | 16 | C26-083…091 | 薛蟠哄宝玉出场；五月初三寿礼四样；书房摆酒；「庚黄」笑谈 | 已生成 |
| `c26-fengziying` | 薛蟠书房 · 冯紫英赴宴 | `c4_lixiang` | 17–18 | C26-092…109 | 唐寅辨字；冯紫英到、脸上青伤、铁网山打围；「不幸之幸」；饮两杯执手而去 | 已生成 |
| `c26-baochai` | 怡红院 · 宝钗说新鲜 | `yihong` | 19 | C26-110…114 | 宝玉醉归、袭人埋怨；宝钗「偏了我们新鲜东西了」 | 已生成 |
| `c26-bumen` | 怡红院门外 · 晴雯不开门 | `yihong` | 20–25 | C26-115…130 | 黛玉沁芳桥看水禽；晴雯移气不开门；黛玉墙角呜咽；两首贊诗；院门「吱喽」一声 | 已生成（本回收束） |

---

## 地图、人物、资产

| ID | 新建或复用 | 来源或依据 | 锚点 | 状态 |
| --- | --- | --- | --- | --- |
| `yihong` | 复用（第 21 回新建） | 怡红院，本回占 7 段 | gate / yard / gate_step / outer_room / mirror_place / inner_room / kang / baoyu_kang / xiren_kang / desk_place / book_place / window_place / curtain / cui_lv_place / zijun_place / baochai_place | 可直接用 |
| `qinfang` | 复用（第 23 回新建） | 沁芳亭、蜂腰桥都在沁芳一带 | bank_west / bridge_head / bridge_mid / bank_east / stone_seat / peach_grove / corner / tomb / sluice | 可直接用 |
| `entry` | 复用 | 荣府二门、过厅 | hall_door / passage_entry / outer_turn 等 30 锚点 | 可直接用 |
| `c4_lixiang` | 复用（梨香院） | 薛蟠书房＝薛家住所前厅，底本未另写府外别业 | street_gate / court_center / front_hall / back_rooms / lane_gate | 可直接用 |
| `xiaoxiang` | **新建**（`scripts/build_chapter26_maps.py`） | 回目明写「潇湘馆」；底本段 12「匾上写著『潇湘馆』三字」「湘帘垂地」「一缕幽香从碧纱窗中暗暗透出」，段 13 床、段 15 茶几 | gate / window_out / door / bed / chair / desk_place / zijun_place / nurse_place（8 个） | 地图已生成，`scene-places.json` 已补 |

### 新角色清单（只列报告，不登记；cast 与美术由主 agent 统一处理）

| 建议 id | 中文名 | 一句话视觉设定（含服饰色彩） | 底本依据 |
| --- | --- | --- | --- |
| `jiahui` | 佳蕙 | 怡红院小丫鬟，十三四岁双丫髻，淡青布衫配月白裙，捧钱时一脸雀跃 | 段 1「本院的个小丫头名叫佳蕙的」「林姑娘就抓了两把给我」；底本无服饰描写，配色为设计推定 |
| `zhuer` | 坠儿 | 怡红院小丫头，圆脸伶俐，穿藕荷色短袄、葱绿裤，跑动时辫梢一甩 | 段 5「叫我带进芸二爷来」、段 9 与贾芸讨帕；底本无服饰描写，配色为设计推定 |
| `qingwen` | 晴雯 | 怡红院大丫鬟，眉眼俏丽、性子刚烈，银红撒花袄配石青背心，抱臂立在院门内 | 段 21「晴雯和碧痕正拌了嘴」「凭你是谁，二爷吩咐的」；底本无服饰描写，配色为设计推定 |
| `feng_ziying` | 冯紫英 | 神武将军冯唐之子，英武少年，石青箭袖袍束玄带，左颊一处青伤，豪爽中带英气 | 段 17「神武将军冯唐之子冯紫英」「面上有些青伤……铁网山教兔鹘捎一翅膀」；青伤有据，服饰配色为设计推定 |

> 焙茗＝第 9 回的茗烟，沿用已有 cast id `ming_yan`，不另立角色；正文保留底本「焙茗」二字。

---

## 设计推定（已写进证据表 design 条目）

| ID | 段落 | 推定 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| C26-D1 | `c26-hongyu` | 红玉佳蕙、贾芸看守、描花样取笔复用 `yihong` | 段 1「红玉同众丫鬟也在这里守著宝玉」、段 4「出了怡红院，一径往宝钗院内来」 | 用 `outer_room`/`window_place`/`gate`/`yard` |
| C26-D2 | `c26-qinfang` | 沁芳亭、蜂腰桥复用 `qinfang` | 段 4「刚至沁芳亭畔」、段 5「红玉刚走至蜂腰桥门前」 | 用 `bank_west`/`bridge_head`/`bridge_mid`；蘅芜苑无专图，只作叙述 |
| C26-D3 | `c26-xiaoxiang` | 新建 `xiaoxiang` | 段 12 匾额、湘帘、碧纱窗；段 13 床；段 15 茶几。`daguanyuan` 是全景俯瞰、`night` 是贾母院碧纱橱 | 新建室内图，8 锚点 |
| C26-D4 | `c26-jiaozheng` | 二门一段复用 `entry` | 段 15「出园来，只见焙茗在二门前等著」 | 用 `hall_door`/`passage_entry` |
| C26-D5 | `c26-xuepan` | 薛蟠书房复用 `c4_lixiang`（梨香院） | 段 16「来至他书房里」；薛家住荣府东北角梨香院 | 用 `street_gate`/`front_hall` |
| C26-D6 | `c26-hongyu` | 四名新角色由主 agent 统一登记 | 佳蕙/坠儿/晴雯/冯紫英均不在现有 cast | id 见上表；已登记 cast 与美术 |
| C26-D7 | `c26-jiaozheng` | 焙茗沿用 `ming_yan` | 第 9 回茗烟，本回焙茗，同一小厮别名 | 正文不改字 |
| C26-D8 | `c26-xuepan` | 只被点名、无台词的本回人物不入 cast | 奶娘婆子、小丫头、小么儿、程日兴、詹光、胡斯来、单聘仁、沈世兄等 | 只在正文保留，不 show |
| C26-D9 | `c26-bumen` | 两首诗与过渡句作旁白 `verbatim` 节点 | 段 22/24 贊诗无说话人；段 23「因有一首诗道」 | speaker `narrator`，不改字 |
| C26-D10 | `c26-fengziying` | 冯紫英青伤是底本明写，服饰为推定 | 段 17「面上有些青伤」「铁网山教兔鹘捎一翅膀」 | 报告标注「底本无服饰描写」 |
| C26-D11 | `c26-fengziying` | **底本没有蒋玉菡/云儿饮酒唱曲一段** | 程乙本段 17–18 只写冯紫英到场、问安、说青伤与「不幸之幸」，饮两杯后「执手就走」「出门上马去了」；蒋玉菡（琪官）与云儿唱曲见于脂本第二十八回 | 严格按底本切片，不新增这两人，不写唱曲 |

---

## 验收与上线清单

- [x] `python3 scripts/build_chapter26_maps.py` —— `maps/xiaoxiang.tmj` 写出（8 锚点）
- [x] `npm run check:anchors` —— 423 路线锚点全通（含新图 `xiaoxiang` 的 8 个锚点）
- [x] `npm run map:framing` —— 0 framing problem(s)
- [x] `python3 scripts/build_chapter26.py` —— 130 节点 / 13 段 / 141 证据，自校通过
- [x] `python3 scripts/build_chapter26.py --check` —— 校验通过
- [x] 底本段覆盖核对：正文段 1–25 全覆盖（916 子句不重不漏），区间无重叠
- [ ] 主 agent：登记 4 名新角色（`jiahui`/`zhuer`/`qingwen`/`feng_ziying`）到 `src/story.ts` cast 与美术管线
- [ ] 主 agent：`src/story.ts` import script26/sections26 → 拼 story/chapters → `bookNames` 加 `"26":"第二十六回"`
- [ ] 主 agent：`design/chapter-titles.json` 加回目联（已由 `check_content.mjs` 的 `VERBATIM_BASE` 含 26）
- [ ] 主 agent：`design/scene-places.json` 补新 scene `xiaoxiang` 方位
- [ ] 主 agent：`check_content.mjs` 全链通过（新角色注册后才不会报 unknown actor）
- [ ] 主 agent：写 `tests/chapter26.mjs`，跑全链与部署复验
