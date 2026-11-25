# 第 28 回制作记录

## 目标与来源

- **回目全名**：第二十八回　蒋玉菡情赠茜香罗　薛宝钗羞笼红麝串
- **底本 / 版本 / 来源地址 / 取得日期**：
  - 版本：维基文库《紅樓夢》第 028 回，程乙本 / 高鹗本整理稿（繁体）
  - 来源地址：<https://zh.wikisource.org/w/index.php?title=紅樓夢/第028回&action=raw>
  - 取得日期：2026-11-25
  - 处理：维基 raw 取回，去导航 / 样式 / 许可页脚，OpenCC t2s 转简体，按维基段落拆行；正文未作增删
- **本地正文**：`docs/chapter28-source.txt`（回目行 + 正文 33 段，段 0 为回目，正文段 1–33；本回对白极多，含 5 支曲子）
- **剧情、段落、证据**：`design/chapter28-story.json`、`chapter28-sections.json`、`chapter28-evidence.json`
- **生成器**：`scripts/build_chapter28.py`（底本切片 + 标题回锚自愈 + 引号边界，沿用第 24/25 回机制）
- **本回开始 / 结束、与前后回衔接**：
  - 接第 27 回（黛玉昨夜晴雯不开门错疑宝玉）——开篇「话说林黛玉只因昨夜晴雯不开门一事，错疑在宝玉身上」，正接上回
  - 止于黛玉甩帕打中宝玉、宝玉「嗳哟」一声（「要知端的，且听下回分解」）
- **`<poem>` / `<ref>` 处理**：生成器 `load_base()` 清掉维基 `<poem>` 包裹与 `<ref>` 注（甲戌本生字说明），曲文整段保留为 `verbatim`；正文汉字未作增删
- **实际出场 / 转述人物**：
  - **有台词登场（新增 3 人）**：冯紫英（家宴主人）、蒋玉菡 / 琪官（唱小旦，回目人物）、云儿（锦香院妓女）
  - **有台词复用已登记角色**：宝玉、黛玉、宝钗、王夫人、凤姐、薛蟠、袭人、贾母、焙茗（复用 `ming_yan`）
  - **复用已登记但只登场无台词**：探春、惜春（段 10 同笑一句，合在叙述节点，未单列 speaker）
  - **提及未登场、不入 cast**：唱曲儿的小厮、二门上婆子、门上踢球小厮、锄药 / 双瑞 / 双寿、紫绡、夏太监、鲍太医 / 王大夫、珍大爷（贾珍）、北静王
  - **叙事层级**：全回为 `present` 现实层；五支曲子（段 14/18/21/24/27）是角色当席所唱，归各唱歌角色，仍为 `verbatim` 不改字

---

## 事件覆盖表

| 原文起句或事件 | 时间层 | 段落 / 节点 | 地点 / scene | 在场人（speaker） | 压缩 / 改写说明 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 黛玉葬花、宝玉山坡听到「花落人亡两不知」恸倒 | present | `c28-zanghua` / C28-001… | `qinfang` 沁芳闸 | 叙述 | 复用第 23 回花冢 / 山子石 | 已生成 |
| 黛玉见宝玉躲开，「啐！我道是谁」；宝玉下山追上 | present | `c28-zanghua` / `c28-supu` | `qinfang` | 叙述、黛玉 | 「既有今日，何必当初」照录 | 已生成 |
| 宝玉诉肺腑「当初姑娘来了」，黛玉泪下 | present | `c28-supu` | `qinfang` | 宝玉、黛玉 | 大段独白按子句切成 5 节点 | 已生成 |
| 释疑「昨儿为什么我去了你不叫丫头开门」，宝玉咬牙笑 | present | `c28-supu` | `qinfang` | 黛玉、宝玉 | 「宝姑娘来，什么贝姑娘来」照录 | 已生成 |
| 王夫人问鲍太医药、金刚丸 / 菩萨散 / 天王补心丹 | present | `c28-wenyao` | `wang` 王夫人上房 | 叙述、王夫人、宝玉、宝钗 | 满屋笑、王夫人骂「扯你娘的臊」照录 | 已生成 |
| 宝玉讨三百六十两配药、凤姐作证薛蟠寻珍珠 | present | `c28-wenyao` | `wang` | 王夫人、宝玉、宝钗、凤姐 | 黛玉在宝钗身后画羞照录 | 已生成 |
| 黛玉先走、宝玉跟王夫人吃斋、宝钗劝陪林姑娘 | present | `c28-wenyao` | `wang` | 宝玉、王夫人、宝钗、叙述 | 「理他呢，过一会子就好了」照录 | 已生成 |
| 探春惜春笑、凤姐院写礼单、讨红玉 | present | `c28-wenyao` / `c28-fengyuan` | `wang` → `c6_wangchui` | 叙述、宝钗、凤姐、宝玉 | 复用第 6 回凤姐院图 | 已生成 |
| 贾母院里屋黛玉裁剪，宝钗打趣，黛玉赶宝玉 | present | `c28-caijian` | `entry` 贾母院 | 叙述、黛玉、宝钗、宝玉 | 「这里有老虎，看吃了你」照录 | 已生成 |
| 焙茗取衣裳、婆子骂、备马往冯紫英家 | present | `c28-chumen` | `entry` → `fengziying_home` | 叙述、焙茗（`ming_yan`） | 焙茗复用第 9 回茗烟 id | 已生成 |
| 冯紫英家赴宴，见薛蟠、蒋玉菡、云儿，吃茶让酒 | present | `c28-fuyan` | `fengziying_home`（本回新建） | 叙述、宝玉、冯紫英 | **冯紫英 / 蒋玉菡 / 云儿本回首登场** | 已生成 |
| 薛蟠拉云儿唱「两个冤家」；宝玉发令说悲愁喜乐 | present | `c28-fuyan` / `c28-xingling` | `fengziying_home` | 薛蟠、云儿、宝玉 | 宝玉「女儿悲，青春已大守空闺」照录 | 已生成 |
| 宝玉唱红豆曲「滴不尽相思血泪抛红豆」、拈梨完令 | present | `c28-xingling` | `fengziying_home` | 宝玉、叙述、薛蟠、云儿 | 曲文 verbatim；薛蟠说「无板」 | 已生成 |
| 冯紫英、云儿、薛蟠依次行令唱曲 | present | `c28-zhongling` | `fengziying_home` | 冯紫英、云儿、薛蟠、宝玉 | 薛蟠「乌龟 / 大马猴 / 哼哼韵」照录 | 已生成 |
| 蒋玉菡行令唱曲、念「花气袭人知昼暖」，薛蟠喧嚷 | present | `c28-zhongling` | `fengziying_home` | 蒋玉菡、薛蟠、叙述 | 云儿说破「袭人是宝贝」，琪官陪罪 | 已生成 |
| 廊檐下宝玉与琪官互赠玉玦扇坠、茜香罗大红汗巾 | present | `c28-qixiang` | `fengziying_home` | 叙述、宝玉、蒋玉菡 | **回目正戏**；「茜香国女国王所贡」照录 | 已生成 |
| 回园袭人见汗巾、夜间互换、掷空箱子 | present | `c28-hanjin` | `yihong` 怡红院 | 叙述、袭人、宝玉 | 「我不希罕这行子，趁早儿拿了去」照录 | 已生成 |
| 端午节礼：红麝香珠，你的同宝姑娘的一样 | present | `c28-hanjin` | `yihong` | 袭人、宝玉 | 紫绡传话走叙述，不入 cast | 已生成 |
| 黛玉顶头「什么金什么玉」，宝玉发誓 | present | `c28-daiyan` | `entry` 贾母院 | 叙述、黛玉、宝玉 | 「第四个就是妹妹了」照录 | 已生成 |
| 宝玉看宝钗红麝串、看酥臂呆住；黛玉甩帕「呆雁」 | present | `c28-daiyan` | `entry` | 宝玉、宝钗、黛玉、叙述 | **本回收束**；「忒儿一声飞了」照录 | 已生成 |

---

## 地图、人物、资产

| ID | 新建或复用 | 来源或生成器 | 尺寸 / 锚点 | 状态 | 证据截图 |
| --- | --- | --- | --- | --- | --- |
| `qinfang` | 复用（第 23 回新建） | `scripts/build_chapter23_maps.py` | 40×40 / 9 锚点 | 可直接用 | — |
| `wang` | 复用 | `scripts/build_chapter_maps.py` | 40×40 / 11 锚点 | 可直接用 | — |
| `c6_wangchui` | 复用 | `scripts/build_chapter_maps.py` | 40×40 / 10 锚点（含 hall / platform / feng_room） | 可直接用 | — |
| `entry` | 复用 | `scripts/build_chapter_maps.py` | 40×40 / 30 锚点 | 可直接用 | — |
| `yihong` | 复用（第 21 回新建） | `scripts/build_chapter21_maps.py` | 40×40 / 17 锚点 | 可直接用 | — |
| `fengziying_home` | **新建**（`scripts/build_chapter28_maps.py`） | 冯紫英家家宴——底本写「一径到了冯紫英家门口……然后摆上酒来，依次坐定」，段 30「二人站在廊檐下」 | 40×40 / 11 锚点 | `scene-places.json` 已补 | — |
| `feng_ziying`（冯紫英） | **新增人物** | 已登记 cast 与美术 | 立绘 600 / Q 版 116 | 已登记，见 `docs/chapter26-characters.md` | — |
| `jiang_yuhan`（蒋玉菡） | **新增人物** | 已登记 cast 与美术 | 立绘 600 / Q 版 116 | 已登记，见 `docs/chapter28-characters.md` | — |
| `yun_er`（云儿） | **新增人物** | 已登记 cast 与美术 | 立绘 600 / Q 版 116 | 已登记，见 `docs/chapter28-characters.md` | — |
| `ming_yan`（茗烟 / 焙茗） | 复用（第 9 回登记） | 已有资产 | 立绘 600 / Q 版 116 | 可直接用 | — |

> 上表 `fengziying_home` 的最终处置由地图制作阶段已按锚点与底本逐字核定；未预先多生成美术。

---

## 设计推定（写进证据表 design 条目）

| ID | 段落 | 推定 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| C28-D1 | `c28-zanghua` | 葬花与诉肺腑复用 `qinfang`（沁芳闸） | 底本「因把些残花落瓣去掩埋」「不觉恸倒山坡之上」，第 23 回已有花冢 `tomb` / 山子石 `stone_seat` | 用 `tomb`/`stone_seat`/`bank_east`，不新开葬花图 |
| C28-D2 | `c28-wenyao` | 问药配药、凤姐作证放 `wang` | 「王夫人见了林黛玉，因问道」「凤姐因在里间屋里看著人放桌子」 | 用 `hall_entry`/`guest_seat`/`wang_host`/`south_passage` |
| C28-D3 | `c28-fengyuan` | 凤姐院写礼单、讨红玉复用 `c6_wangchui` | 「可巧走到凤姐儿院门前……替我写几个字儿」，第 6 回凤姐院图语义吻合 | 用 `platform`（剔牙）/ `hall`（写礼单） |
| C28-D4 | `c28-caijian` | 贾母院里屋黛玉裁剪复用 `entry` | 「来至贾母这边……贾母道：里头屋里呢」「炕上两个丫头打粉线，黛玉弯著腰裁剪」 | 用 `hall_door`/`daiyu_seat`/`grandmother_seat` |
| C28-D5 | `c28-fuyan` | 冯紫英家家宴新建 `fengziying_home` | 「一径到了冯紫英家门口……摆上酒来，依次坐定」；`dinner` 是贾母晚膳、`tavern` 是村肆，语义冲突 | 新建室内图，11 锚点 |
| C28-D6 | `c28-hanjin` | 怡红院汗巾与节礼复用 `yihong` | 「宝玉回至园中，宽衣吃茶……腰里一条血点似的大红汗巾子」 | 用 `baoyu_kang`/`xiren_kang` |
| C28-D7 | `c28-daiyan` | 金玉之争、红麝串、呆雁复用 `entry` | 「要往贾母那里请安去……然后到了贾母这边」 | 用 `hall_door`/`daiyu_greet`/`courtyard_center` |
| C28-D8 | `c28-chumen` | 焙茗复用既有 `ming_yan`，不新增角色 | 底本「焙茗」即第 9 回茗烟（后改名），同一宝玉小厮 | speaker/actor 用 `ming_yan`，正文「焙茗」照底本保留 |
| C28-D9 | `c28-fuyan` | 冯紫英、蒋玉菡、云儿三人入 cast | 三人是本回真正登场、有实质台词的关键角色（家宴主人 / 回目人物 / 贯穿行令的唱曲者） | 视觉设定见 `docs/chapter28-characters.md`；cast 与美术已登记 |
| C28-D10 | `c28-xingling` | 唱曲小厮、婆子、紫绡、夏太监等不入 cast | 均无独立台词或仅叙述点名 | 只在正文保留，不 show、不注册 |
| C28-D11 | `c28-xingling` | 五支曲子作 verbatim 韵文节点 | 段 14/18/21/24/27 是角色当席所唱、被 `<poem>` 包裹 | speaker 归各唱歌角色，textKind 仍 verbatim |

---

## 新角色清单（cast 与美术已登记，视觉设定见 `docs/chapter28-characters.md`）

| 建议 id | 中文名 | 一句话视觉设定（含服饰色彩） | 身份 / 本回功能 |
| --- | --- | --- | --- |
| `feng_ziying` | 冯紫英 | 将门少年公子，眉目爽朗英武，月白锦袍束发、腰悬佩剑，杯盏间有江湖气 | 紫英家宴主人，发令邀饮，串起整场家宴 |
| `jiang_yuhan` | 蒋玉菡（琪官） | 唱小旦的优伶，面容妩媚温柔，藕荷色戏装、鬓边簪花，举止轻柔含情 | 回目人物；行令唱曲，廊檐下与宝玉互赠茜香罗 |
| `yun_er` | 云儿 | 锦香院妓女，风情圆熟、眉眼带笑，桃红裙袄配石青比甲，怀抱琵琶 | 唱曲敬酒、与薛蟠插科打诨，贯穿行令 |

> 三人 id 均为 snake_case，与 `src/story.ts` 现有 cast 命名风格一致。底本对蒋玉菡有「妩媚温柔」四字、对冯紫英与云儿无外貌描写，配色为视觉设计推定，不冒充原文记载。

---

## 不入 cast 的本回人物

唱曲儿的小厮、二门上老婆子、门上踢球小厮、锄药 / 双瑞 / 双寿（宝玉四个随行小厮）、紫绡（宝玉遣送节礼，只传话）、夏太监（贵妃差送节礼）、鲍太医 / 王大夫（多在叙述里被点名）、珍大爷（贾珍，段 32 提及）、北静王（段 30 蒋玉菡提及赠汗巾）。上述人物均只在正文里保留，不 show、不注册新 cast。

---

## 验收清单

- [x] `python3 scripts/build_chapter28_maps.py` —— `maps/fengziying_home.tmj` 写出（11 锚点）
- [x] `npm run check:anchors` —— 434 个路线锚点全通（新图在内）
- [x] `npm run map:framing` —— 0 framing problem(s)
- [x] `python3 scripts/build_chapter28.py` —— 125 节点 / 12 段 / 136 证据，自校通过
- [x] `python3 scripts/build_chapter28.py --check` —— 校验通过，未写盘
- [ ] 主 agent：新角色（`feng_ziying` / `jiang_yuhan` / `yun_er`）登记 cast + manifest + 美术 + facing（本 agent 只列报告，不登记）
- [ ] 主 agent：`design/scene-places.json` 补 `fengziying_home` 方位（level / region / col / row / name）
- [ ] 主 agent：`src/story.ts` import script28/sections28、拼 story/chapters、`bookNames` 加 `"28":"第二十八回"`
- [ ] 主 agent：`design/chapter-titles.json` 回目联、`check_content.mjs` VERBATIM_BASE 加 28（已含）
- [ ] 全链：`check:content` → `tsc --noEmit` → `npm test` → `test:locator` → `build`
