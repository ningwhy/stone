# 第 24 回制作记录

## 目标与来源

- **回目全名**：第二十四回　醉金刚轻财尚义侠　痴女儿遗帕惹相思
- **底本/版本/来源地址/取得日期**：
  - 版本：维基文库《紅樓夢》第 024 回，程乙本/高鹗本整理稿（繁体）
  - 来源地址：<https://zh.wikisource.org/w/index.php?title=紅樓夢/第024回&action=raw>
  - 取得日期：2026-11-18（首次抓取遭维基限流 429，换浏览器 UA + `--compressed`、180 秒超时重取成功）
  - 处理：`scripts/fetch_chapter_source.py 24` → OpenCC t2s 转简体，去导航/样式/许可页脚，按维基段落拆行；正文未作增删
- **本地正文**：`docs/chapter24-source.txt`（8474 字 / 25 段）
- **剧情、段落、证据**：`design/chapter24-story.json`、`chapter24-sections.json`、`chapter24-evidence.json`
- **生成器**：`scripts/build_chapter24.py`（**第 24 回新增「区间自愈」机制**，见下）
- **本回开始/结束、与前后回衔接**：
  - 接第 23 回（黛玉读《牡丹亭》落泪，被袭人一掌打断）→ 第 24 回开篇仍是黛玉，香菱从背后拍她一下
  - 止于小红遗帕、贾芸窗外唤她（「要知端的，下回分解」），第 25 回的起手
- **实际出场 / 转述人物**：
  - **有台词登场（新增 8 人）**：贾芸、小红、倪二（醉金刚）、卜世仁、香菱、秋纹、碧痕、鸳鸯
  - **复用已登记角色**：黛玉、宝玉、袭人、凤姐、贾琏、邢夫人、贾环、贾兰、周瑞家的、焙茗
  - **提及未登场**：贾赦（宝玉到贾赦院请安，底本只写「见了贾赦，不过是偶感些风寒……自己请了安」，贾赦无一句台词）、贾芹（贾琏说花木工程「前儿……给了贾芹了」）、方椿（花儿匠，「出西门找到花儿匠方椿家里去买树」）、王短腿（马贩子，倪二托话处）、贾母、王夫人、薛宝钗、檀云、麝月、紫鹃
  - **只在叙述里被提及、不入 cast**：卜世仁的**娘子**与**银姐**（底本里各有一句台词，但都在「卜世仁夫妻两个说话」的叙述里，属画外音；银姐连台词都没有，只有名字）、贾芸的**母亲**（底本写「见他母亲自在炕上拈线」，她只有叙述、没有台词）、倪二的**娘子**（「先到隔壁将倪二的信捎了与他娘子知道」）
- **梦境 / 现实 / 回忆场景**：全回为 `present` 现实层，无梦境、无回忆

---

## 事件覆盖表

| 原文起句或事件 | 时间层 | 段落 / 节点 | 地点/scene | 在场人（speaker） | 压缩/改写说明 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 黛玉情思萦逗，香菱从背后击掌 | present | `c24-xiangling` / C24-001…005 | `qinfang` 沁芳闸桃花下 | 叙述、黛玉、香菱 | **香菱本回首次真正登场**（第七、十六、二十回只被提及） | 待上线 |
| 香菱寻紫鹃，说琏二奶奶送茶叶来；同归潇湘馆 | present | `c24-xiangling`（同段） | `qinfang` | 香菱、黛玉、叙述 | 「说琏二奶奶送了什么茶叶来给你的」照录 | 待上线 |
| 宝玉被袭人带回房，鸳鸯歪在床上看针线 | present | `c24-yuanyang` / C24-012…026 | `yihong` 怡红院 | 叙述、鸳鸯、宝玉、袭人 | **鸳鸯本回首次登场**；「其白腻不在袭人之下」「把你嘴上的胭脂赏我吃了罢」照录 | 待上线 |
| 鸳鸯叫袭人出来，袭人劝宝玉；同见贾母 | present | `c24-yuanyang`（同段） | `yihong` | 鸳鸯、袭人、宝玉、叙述 | 「你跟他一辈子，也不劝劝」照录 | 待上线 |
| 宝玉上马，贾琏回来；贾芸转出请安 | present | `c24-huijian` / C24-027…031 | `capital` 宁荣街 | 叙述、贾芸、贾琏、宝玉 | **贾芸本回首次登场**（第十三回只在旁白里被提到一次） | 待上线 |
| 贾琏说花木工程许给贾芹；贾芸「摇车里的爷爷」 | present | `c24-huijian`（同段） | `capital` | 贾芸、贾琏、宝玉、叙述 | 「俗语说的，摇车里的爷爷，拄拐的孙孙」照录 | 待上线 |
| 宝玉认作儿子，约贾芸明儿到书房里来 | present | `c24-huijian`（同段） | `capital` | 宝玉、贾芸、贾琏 | 「我带你园里顽耍去」照录 | 待上线 |
| 贾赦院：邢夫人奚落贾环，宝玉问姊妹们 | present | `c24-jiashe` / C24-050…077 | `east` 贾赦院东路小院 | 叙述、邢夫人、宝玉、贾环、贾兰 | 「那里找活猴儿去」照录；贾赦本回无台词 | 待上线 |
| 贾琏院：贾芸打听花木工程，贾琏许「后日起更以后」讨信 | present | `c24-jialian` / C24-078…087 | `jialian_home` 贾琏院 | 叙述、贾芸、贾琏 | 「贾芸恐他母亲生气，便不说起卜世仁的事来」是下一段的伏笔 | 待上线 |
| 卜世仁香料铺：贾芸求赊冰片麝香，卜世仁拒绝 | present | `c24-bu` / C24-088…123 | `spice_shop`（新建） | 叙述、贾芸、卜世仁 | **卜世仁本回首次登场**；「立了合同，再不许替亲友赊欠……罚他二十两银子的东道」照录 | 待上线 |
| 卜世仁娘子说「你又糊涂了」，叫银姐去借钱 | present | `c24-bu`（同段） | `spice_shop` | 叙述 | **娘子与银姐不上台**（见「设计推定」D4） | 待上线 |
| 三街六巷：贾芸撞上醉汉，正是倪二 | present | `c24-nier` / C24-124…139 | `ni_er_lane`（新建） | 叙述、贾芸、倪二 | **倪二（醉金刚）本回首次登场**；「臊你娘的！瞎了眼睛」照录 | 待上线 |
| 倪二认「原来是贾二爷」，骂卜世仁，掏出银子 | present | `c24-nier`（同段） | `ni_er_lane` | 倪二、贾芸、叙述 | 「这三街六巷，凭他是谁，有人得罪了我醉金刚倪二的街坊，管叫他人离家散！」照录 | 待上线 |
| 倪二不要利钱、不要文约，把十五两三钱有零的银子借给贾芸 | present | `c24-nier`（同段） | `ni_er_lane` | 倪二、贾芸、叙述 | 「既肯青目，这是十五两三钱有零的银子，便拿去治买东西」照录 | 待上线 |
| 贾芸回家，先到隔壁捎信，见母亲不吐实情 | present | `c24-jiayin` / C24-169…176 | `jia_yun_home`（新建） | 叙述、贾芸 | **底本明写「见他母亲自在炕上拈线」，故新开一张图** | 待上线 |
| 次日贾芸买冰麝，往荣国府凤姐院外献香 | present | `c24-huojing` / C24-177…206 | `c6_wangchui` 荣府后门 | 叙述、贾芸、周瑞家的、凤姐 | 「大香舖里买了冰麝」照录；锦匣不做立绘（D3） | 待上线 |
| 凤姐止步问「怎么好好的你娘儿们在背地里嚼起我来」 | present | `c24-huojing`（同段） | `c6_wangchui` | 凤姐、贾芸、叙述 | 「别说明年贵妃宫中」——底本作「今年」，照录不改 | 待上线 |
| 凤姐收香，隐瞒派他种树的事 | present | `c24-huojing`（同段） | `c6_wangchui` | 凤姐、贾芸、叙述 | 「便把派他监种花木工程的事都隐瞒的一字不提」照录 | 待上线 |
| 绮霰斋外书房：焙茗、小厮顽耍；贾芸等宝玉 | present | `c24-qiranzhai` / C24-218…253 | `qiranzhai`（新建） | 叙述、贾芸、焙茗、小红 | **小红本回首次登场**；「好，好，正抓不著个信儿」照录 | 待上线 |
| 小红说「二爷竟请回家去」，贾芸只得走 | present | `c24-qiranzhai`（同段） | `qiranzhai` | 小红、贾芸、焙茗、叙述 | 「依我说，二爷竟请回家去，有什么话明儿再来」照录 | 待上线 |
| 荣国府门前：凤姐叫住贾芸，许他种树 | present | `c24-paihu` / C24-254…277 | `capital` 宁荣街 | 叙述、凤姐、贾芸 | 「你到午错的时候来领银子，后儿就进去种树」照录 | 待上线 |
| 绮霰斋领票领银二百两 | present | `c24-lingpai` / C24-278…286 | `qiranzhai` | 叙述、贾芸 | 「看那批上银数批了二百两」照录 | 待上线 |
| 次日五鼓还倪二银子，按数收回；拿五十两买树 | present | `c24-huanshui` / C24-287…289 | `ni_er_lane` | 叙述、贾芸、倪二 | 「那倪二见贾芸有了银子，他便按数收回」照录 | 待上线 |
| 怡红院：宝玉房里只剩他一人，要茶没人 | present | `c24-yihong` / C24-290…301 | `yihong` 怡红院 | 叙述、宝玉 | 袭人、秋纹、碧痕、檀云、麝月都不在（照录底本） | 待上线 |
| 小红从后门进来递茶，宝玉问「你在那里的」 | present | `c24-doucha` / C24-302…333 | `yihong` | 叙述、宝玉、小红、秋纹、碧痕 | **秋纹、碧痕本回首次登场**；「倒是一头黑鬒鬒的好头发」照录 | 待上线 |
| 秋纹碧痕奚落小红「你也拿镜子照照，配递茶递水不配」 | present | `c24-doucha`（同段） | `yihong` | 秋纹、碧痕、小红、叙述 | 底本用「䰖」（髻的异体），照录不改 | 待上线 |
| 老嬷嬷传凤姐话：明日带花儿匠来种树 | present | `c24-yipa` / C24-334…369 | `yihong` | 叙述、秋纹、碧痕、小红 | 「什么后廊上的芸哥儿」照录 | 待上线 |
| 小红本姓林、小名红玉，因避讳「玉」字改叫小红 | present | `c24-yipa`（同段） | `yihong` | 叙述、小红 | 底本原文明写，是全回伏笔的关键 | 待上线 |
| 贾芸窗外唤「红玉，你的手帕子我拾在这里呢」 | present | `c24-yipa`（同段） | `yihong` | 叙述、贾芸、小红 | **本回题目「痴女儿遗帕惹相思」的落点**；帕子不做立绘（D6） | 待上线 |

---

## 地图、人物、资产

| ID | 新建或复用 | 来源或生成器 | 尺寸/锚点/脸部参考 | 状态 | 证据截图 |
| --- | --- | --- | --- | --- | --- |
| `spice_shop` | **新建** | `scripts/build_chapter24_maps.py` | 40×40 / 等距 128×64 / 7 锚点 / 3 条动线 / 街面、铺面前堂、里间货架、隔壁门脸 | **已完成** | `maps/spice_shop.tmj` |
| `ni_er_lane` | **新建** | 同上 | 40×40 / 6 锚点 / 3 条动线 / 街面、欠钱人家门脸、酒肆（`TAVERN` indoor zone） | **已完成** | `maps/ni_er_lane.tmj` |
| `qiranzhai` | **新建** | 同上 | 40×40 / 7 锚点 / 3 条动线 / 院子、书房（`STUDY` indoor zone）、棋摊、房檐掏雀处 | **已完成** | `maps/qiranzhai.tmj` |
| `jia_yun_home` | **新建** | 同上 | 40×40 / 7 锚点 / 4 条动线 / 街面、贾芸家屋与炕、隔壁倪二家门脸 | **已完成** | `maps/jia_yun_home.tmj` |
| `qinfang` | 复用（第 23 回新建） | `scripts/build_chapter23_maps.py` | 40×40 / 9 锚点 | 可直接用 | — |
| `yihong` | 复用（第 21 回新建） | `scripts/build_chapter21_maps.py` | 40×40 / 17 锚点 | 可直接用 | — |
| `capital` | 复用 | `scripts/build_chapter_maps.py` | 40×40 / 宁荣街 | 可直接用 | — |
| `east` | 复用 | `scripts/build_chapter_maps.py` | 40×40 / 贾赦院东路小院 | 可直接用 | — |
| `jialian_home` | 复用（第 21 回新建） | `scripts/build_chapter21_maps.py` | 40×40 / 10 锚点 | 可直接用 | — |
| `c6_wangchui` | 复用（第 6 回新建） | `scripts/build_chapter_maps.py` | 40×40 / 10 锚点 | 可直接用 | — |
| `jia_yun`（贾芸） | **新增人物** | 渲染机 `192.168.4.66` ComfyUI 0.45.0（qwen21 t2i + bg-removal，seed 10234120/10234121） | 立绘 600 / Q 版 116 | **已完成**（立绘 600 / Q 版 116，faceBox 已标，facing 已裁决） | `art/source/jia_yun-{portrait,chibi}_s1023412*-01.png` |
| `xiaohong`（小红） | **新增人物** | 同上（seed 10234130/10234131） | 立绘 600 / Q 版 116 | **已完成** | `art/source/xiaohong-*` |
| `ni_er`（倪二/醉金刚） | **新增人物** | 同上（seed 10234140/10234141） | 立绘 600 / Q 版 116 | **已完成** | `art/source/ni_er-*` |
| `bu_shi_ren`（卜世仁） | **新增人物** | 同上（seed 10234150/10234151） | 立绘 600 / Q 版 116 | **已完成** | `art/source/bu_shi_ren-*` |
| `xiangling`（香菱） | **新增人物** | 同上（seed 10234160/10234161） | 立绘 600 / Q 版 116 | **已完成** | `art/source/xiangling-*` |
| `qiuwen`（秋纹） | **新增人物** | 同上（seed 10234170/10234171） | 立绘 600 / Q 版 116 | **已完成** | `art/source/qiuwen-*` |
| `bihen`（碧痕） | **新增人物** | 同上（seed 10234180/10234181） | 立绘 600 / Q 版 116 | **已完成** | `art/source/bihen-*` |
| `yuan_yang`（鸳鸯） | **新增人物** | 同上（seed 10234190/10234191） | 立绘 600 / Q 版 116 | **已完成** | `art/source/yuan_yang-*` |
| 卜家娘子 / 银姐 / 贾芸之母 / 倪二娘子 | **不登记** | — | — | **不上台** | 底本里或只有名字、或只有叙述里的画外音；进 cast 就要配资产，不值当 |

- **地图维护方式**：脚本为主（`scripts/build_chapter24_maps.py`，幂等重写 4 张 `.tmj`）
- **重建命令及覆盖清单**：
  ```bash
  python3 scripts/build_chapter24_maps.py   # 覆盖 maps/{spice_shop,ni_er_lane,qiranzhai,jia_yun_home}.tmj
  python3 scripts/build_chapter24.py         # 覆盖 design/chapter24-{story,sections,evidence}.json
  npm run check:anchors                      # 新地图必跑
  npm run map:framing                        # 新地图必跑
  ```

### 八人的角色设计说明 → `docs/chapter24-characters.md`

2026-11-24 补写。仓库此前**没有角色设计说明先例**，这是第一份。每人固定八段：
身份定位 → 外形锚点 → 色彩标识 → 资产参数 → 朝向裁决 → 本回剧情功能 → 与同回角色的对照 → 边界。
末尾附汇总对照表、「必须一眼分辨的三组对立」、「不入 cast 的本回人物」表（引用上方 D4/D7/D8）与重建校验命令。

数据全部取自权威源而非推测：外形取 `art/identity/character-designs.json`（`features` + 英文 `prompt`）、
资产参数逐项抄 manifest、朝向取 `design/character-facing.json` 的 `actors`、
剧情数据取 `design/chapter24-story.json`（台词数 / show 场景数 / 锚点 / 首次登场节点）。
校验：尺寸/faceBox/seed/hash/bodyCompress/台词数/show 场景数 → 「全部一致 ✓」；
朝向 → 「全部一致 ✓」；底本引文 → **89 条第 24 回逐字命中 + 7 条跨回命中（均已标注回次）+ 0 条未命中**。

**本节同时修掉两处实质考据错误（香菱）**，详见下方「考据更正」。

---

## 考据更正（2026-11-24）：香菱的身世与外貌

香菱的 `features` 原写「周瑞家的女儿，眉眼像黛玉」，两处**都不对**：

| 原写法 | 实据 | 结论 |
| --- | --- | --- |
| 周瑞家的女儿 | 香菱本姓**甄**，名**英莲**，甄士隐之女，幼年被拐卖与薛家后改名香菱 | 原写法无据，改为「甄士隐之女英莲」 |
| 眉眼像黛玉 | 第 7 回周瑞家的「倒好个模样儿，竟有些象咱们东府里**蓉大奶奶**的品格儿」；第 5 回「其鮮艷嫵媚，有似乎寶釵，風流裊娜，則又如黛玉」是**对秦可卿**的评语 | 「像黛玉」两句都不指香菱，改为「像东府蓉大奶奶秦可卿的品格」 |

「眉眼像黛玉」不见于任何一回底本，系后人讹传。影响面仅 4 个文件
（`art/identity/character-designs.json` / `public/assets/rongguo/manifest.json` 两处 /
`src/story.ts` 的 cast 描述 / `scripts/gen_ch24_characters.py` 注释），
**不涉及任何剧情节点、台词与底本正文**，也**不影响任何测试断言**（`tests/online-chapter24.mjs` 只断言 id 列表）。
**seed 与已生成资产未动**（改 `features`/`prompt` 不触发重新生图）。

同时补录 `docs/chapter07-source.txt` 被截断的香菱段（取维基文库 `action=raw` wikitext，
本地 `opencc` `t2s` 转简体后接在原第 9 行之后），使「便拉了他的手，细细的看了一会」
「你父母今在何处」「不记得了」三处引文**在本仓库可逐字核验**。

---

## 生成器：第 24 回新增的「区间自愈」

第 16-23 回的生成器把「底本段号 + 起止子句号」全部**手写**进 CUTS。第 24 回初版照做，结果立刻暴露手写索引必然漂移：

- **9 处区间互相重叠** —— 下一节点被上一节点吞掉一截
- **4 处跳段子句** —— 底本有字但没进任何节点
- **15 处标题与正文对不上** —— 标题和正文说的不是一回事

根因不是某几处写错，而是**手写索引和底本之间没有约束关系**：底本一改就全错，而且错了不报错，只是内容悄悄错乱。

第 24 回改成：

1. **只声明起点，终点自动推导** —— `prev.s_to = next.s_from`，整段底本被首尾相接地、不重不漏地切开。
2. **起点用「标题回锚底本」自愈** —— 第 24 回的标题基本就是底本原文片段（369 个节点里 355 个能在底本逐字查到），拿标题去底本里找落点，比手写的数字可靠得多。打分用**最长公共前缀长度**而不是「标题是否整段出现」——标题常在句子中间被截断（「这会子还装」是「这会子还装胖呢」的前半截），只看整段出现会锚错位置。
3. **引号边界** —— 正文延伸到整句末尾，但**不越过引号开头**：下一子句以「“「『」开头就是另一段引语的第一句，不许吞。加这条边界后，台词节点被上一节点吞掉的比例从 26% 降到 4%。

对齐脚本：`scripts/align_ch24_cuts.py`（只报告 / `--write` 写回），生成器内 `align_cuts()` 是同一套逻辑。

**效果**：第 24 回相邻节点正文重复率 22%、台词被吞 18 处，与已上线第 23 回（21% / 11 处）同级；标题与正文对不上从 15 处降到 10 处，且剩下的全是**标题压缩摘要**（第 23 回同样的惯例，本项目既有口径）。

---

## 设计推定（写进证据表 design 条目）

| ID | 段落 | 推定 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| C24-D1 | `c24-xiangling` | 开篇复用 `qinfang`（沁芳闸桃花下），不新开潇湘馆专图 | 本项目无潇湘馆地图；第 23 回黛玉的戏也在 `qinfang`。底本只说「回潇湘馆来了」，未描述室内陈设 | 沿用桃林与水岸作背景；不画潇湘馆内部 |
| C24-D2 | `c24-yuanyang` | 鸳鸯与宝玉的「涎皮」一场放在 `yihong`（怡红院） | 底本第 24 回写「宝玉因被袭人找回房去，果见鸳鸯歪在床上看袭人的针线」——第 23 回末尾宝玉已被袭人带回怡红院 | 用 `yihong` 图的 `baoyu_outer` / `xiren_kang` / `inner_room` 等锚点，place 写「怡红院 · 外间」 |
| C24-D3 | `c24-huojing` | 献给凤姐的冰麝用一只锦匣，不做专门立绘 | 底本只写「一边说，一边将一个锦匣举起来」，没有描述锦匣的样子 | 用叙述带过，不加道具立绘 |
| C24-D4 | `c24-bu` | 卜世仁的娘子与银姐不登场、不入 cast | 底本里两人各有一句台词，但都在「卜世仁夫妻两个说话」的叙述里，属画外音；银姐更是连台词都没有 | 按第 23 回周氏的先例处理：只在叙述里点名 |
| C24-D5 | `c24-nier` | 倪二称贾芸为「贾二爷」照录，但 cast 用 `jia_yun` 一个 id | 底本：「原来是贾二爷，我该死，我该死。」——这里指的是贾芸，不是贾琏或贾环 | 登记名仍为「贾芸」，台词照录不改字 |
| C24-D6 | `c24-yipa` | 遗帕一场：帕子不单独做立绘，用叙述与动作表达 | 底本只写「红玉，你的手帕子我拾在这里呢」 | 用叙述带过 |
| C24-D7 | `c24-jiayin` | 贾芸之母不上台、不入 cast | 底本写「见他母亲自在炕上拈线，见他进来，便问那去了一日」，她只有叙述、没有台词 | 只在叙述里点名；图上留炕位（`mother` 锚点） |
| C24-D8 | `c24-huojing` | 彩明与方椿不上台 | 彩明是绮霰斋的小厮（底本「命人通报了，彩明走了出来」，只作叙述）；方椿是花儿匠（底本「出西门找到花儿匠方椿家里去买树」） | 只在叙述里点名 |

---

## 验收与上线清单

- [x] `npm run check:anchors` —— 391 个路线锚点全部可通行且连通，37 个装饰锚点
- [x] `npm run map:framing` —— 0 framing problem(s)
- [x] `python3 scripts/build_chapter24.py` —— 生成器自校：节点 id 唯一、底本位置全局单调、正文非空、paragraphLead 逐字可查、舞台连续性（move 前必须 show 过）、锚点存在且可通行
- [x] 美术后半程：校准 → manifest → facing 目视裁决 → faceBox 重标 → WebP
      —— 校准 16 条（`scripts/calibrate_ch24_chars.py`）；成品 PNG 16 张 + WebP 16 张严格成对；
      faceBox 16 条经「程序化测量 + 12 倍放大目视」双核对（3 处修正：`bu_shi_ren-chibi` 下沿压嘴→[2,19,46,66]、
      `xiaohong-chibi` 上沿切刘海/下沿切嘴→[6,27,48,62]、`qiuwen-chibi` 盖双髻/切嘴→[8,30,56,63]）；
      facing：7 立绘朝右 + `ni_er` 立绘朝左（目视裁决）+ 8 Q 版全部朝右（5 张 Vision 多票、3 张目视）；
      manifest 284 → **300** 条，既有 284 条（除 hash）零改动，identity 148 → 164；
      `art:webp` 后 300 条全部带 hash；`art:audit` → `300 assets on 10 sheets`；
      `check:content` → `Content passed: … 89 humans, 300 assets`
- [x] 图鉴 QA：`tests/character-identities.mjs` → `Passed: 89 versioned portraits, 全部 89 张带 faceBox 并已裁成脸部特写（无缺元数据全身像）；manifest 共 164 个 identity 块`
- [x] 人物美术 QA：`tests/character-art-qa.mjs` → 图鉴 89 张像素去重无重复 / 体型档位 0.72 / 脚底偏差 0px / 层级遮挡成立
- [x] 注册 8 个新角色到 `src/story.ts` 的 `cast`
- [x] `src/story.ts`：import script24/sections24 → 拼 `story` → 拼 `chapters` → `bookNames` 加 `"24":"第24回"`
- [x] `design/chapter-titles.json` 加回目联
- [x] `scripts/check_content.mjs` 的 `VERBATIM_BASE` 加 24
- [x] `design/scene-places.json` 补 4 个新 scene 的方位
      —— `spice_shop`(capital 7,21) / `ni_er_lane`(capital 10,24) / `jia_yun_home`(capital 13,25) /
      `qiranzhai`(rongguo 9,12)；坐标已逐点验证不与同层既有点位的**标签框**重叠
      （转场下钻后同层十几个地名会同时画出来，坐标近了会糊成一团）
- [x] `tests/browser-smoke.mjs` 的「查无此人」样本**无需重选**
      —— 「侍书」在第 24 回的全部可搜路径（正文/标题/地点/在场人物/段 id）里仍是 0 命中，
      也不在 cast 里。顺带把静态断言升级成**复刻运行时索引**（src/toc.ts 的 searchText 六项），
      上一版只扫 chapter*-story.json，「在地点名里出现」这类情况根本查不出来
- [x] 写 `tests/chapter24.mjs` 与 `tests/online-chapter24.mjs`
- [x] `npm run check:content` → `check:anchors` → `tsc` → `npm test` → `test:locator` → `build` → 图鉴 → 定向测试 → browser-smoke
      —— check:content `Content passed: 2293 nodes, 214 sections, 52 maps, 89 humans, 300 assets`
      —— check:anchors `391 route anchors, 37 decorative anchors`
      —— map:framing `0 framing problem(s)`
      —— npm test `97 pass / 0 fail`
      —— test:locator `places: 52 scenes, 5 levels, 10 regions` + `non-overlap: … overlap 0`
      —— character-identities / character-art-qa 全绿
      —— chapter24 `Passed: chapter 24 — 16 sections walked, 369 nodes, 10 stages, TOC search, back cover correct, all node text verbatim.`
      —— browser-smoke `Passed: all 354 nodes, 52 maps, …`
- [x] 部署到 `stone-direct.yan.pub` 并线上复验
      —— 服务器回环 `curl -sk -H 'Host: stone-direct.yan.pub' https://127.0.0.1/` → 200；直连 200
      —— online-chapter24 `Passed (direct): chapter 24 is live — 16 sections, 10 stages (incl. 4 new maps),
         TOC lists 第二十四回, back cover ends the book, 89 portraits render (incl. 8 new).`；0 失败请求
      —— verify-album-title `面板标题: 前二十四回 · 人物图鉴`（回目数自动派生）
      —— online-chapter23 回归：第 23 回封底自动变成「开启下一回 → 第二十四回 醉金刚轻财尚义侠 痴女儿遗帕惹相思」
      —— 提交 `7dc5d39`，已推送 `origin/main`

---

## 接入时修掉的两个真缺陷

这两个都不是「接一下就行」能绕过去的，是接入时**门禁逼出来的**真问题：

### 一、生成器的 `last_focus` 按段 id 记 → 26 个节点 focus 断链成空

**现象**：`check_content` 报 `ERROR C24-334…C24-359: unknown focus `（空字符串）。

**根因**：`assign_scenes()` 的 `last_focus` 以**段 id** 为键，但一个场景可以横跨好几段 ——
`yihong` 占了 `c24-yuanyang` / `c24-yihong` / `c24-doucha` / `c24-yipa` 四段。
`c24-yipa` 的段首节点（C24-334）既没有 `show` 也没有 `move`，
按段 id 找「上一次落点」就找不到了 → focus 断链成空串。

**为什么以前没炸**：第 23 回一个场景只跨一段，按段 id 记和按场景记等价。
第 24 回第一次让同一场景跨四段，这个隐患才暴露。

**修法**：改成**按场景**记（`last_focus[step['scene']]`），跨段续用同一场景时镜头不丢；
同时给 `c24-yipa` 段首补上 `show`（秋纹、碧痕正是在这里登场）；
并在生成器自校里加一条「focus 不得为空」——
**不然要等上线后读者点到那一步才发现**。

### 二、C24-174 的 `show jia_yun_mother` 引用了不在 cast 里的角色

**现象**：`ERROR C24-174: unknown actor jia_yun_mother`。

**根因**：生成器里给「贾芸之母」写了个 `show`，但按设计推定 **D7** 她**不上台、不入 cast**
（底本只写「见他母亲自在炕上拈线」，她没有台词）。

**修法**：去掉那个 `show`，镜头落在里屋 `room`；母亲的存在由正文和图上那张炕交代。
**教训**：生成器里凡是 `show` 的 actor，都必须在 cast 里；「不入 cast」的角色只能用叙述与场景美术交代。

