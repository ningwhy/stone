# 第二十七回制作记录

## 回目与底本

- **回目**：第二十七回　滴翠亭杨妃戏彩蝶　埋香冢飞燕泣残红
- **底本**：`docs/chapter27-source.txt`，中文维基文库《紅樓夢》第 027 回
  （<https://zh.wikisource.org/w/index.php?title=紅樓夢/第027回&action=raw>），
  2026-11-25 取得，OpenCC t2s 转简体、去导航与许可页脚，按维基段落拆行。
- **段数**：源文件切成 20 段（第 0 段为回目，正文 19 段），生成器 `paragraphCount=20`。
- **切分口径**：子句级 `(?<=[。！？；，：、])`，闭合引号归前一个子句；
  正文延伸到整句末，引语开头为延伸边界。葬花吟段的 `<section/>` 与 `<poem>` 排版标记已清除，
  文字本身逐字来自底本。
- **产出**：`design/chapter27-story.json`（128 节点）、
  `design/chapter27-sections.json`（14 段）、
  `design/chapter27-evidence.json`（138 条证据）。

## 分场表

| 段 id | 节点区间 | scene | 内容 |
| --- | --- | --- | --- |
| `c27-daiyu` | C27-001–004 | `daguanyuan` | 潇湘馆院门望宝玉，回房卸妆 |
| `c27-mangzhong` | C27-005–011 | `daguanyuan` | 紫鹃雪雁惯看黛玉闷坐；次日芒种，园中女儿饯花神 |
| `c27-baochai` | C27-012–018 | `daguanyuan` | 园中玩耍，宝钗往潇湘馆，见宝玉进去后抽身 |
| `c27-pudie` | C27-019–024 | `qinfang` | 玉色蝴蝶引宝钗扑至池中滴翠亭 |
| `c27-touting` | C27-025–033 | `qinfang` | 亭外偷听手帕子、谢礼与赌咒 |
| `c27-jintao` | C27-034–043 | `qinfang` | 宝钗「金蝉脱壳」，推窗二人唬怔 |
| `c27-hongyu` | C27-044–048 | `qinfang` | 红玉坠儿后怕；文官香菱司棋待书上亭 |
| `c27-fengjiao` | C27-049–055 | `qinfang` | 凤姐山坡招手，差红玉取银子与荷包 |
| `c27-wen` | C27-056–068 | `daguanyuan` | 红玉问路，遇晴雯绮霰碧痕等，被冷笑「爬上高枝儿」 |
| `c27-lishi` | C27-069–087 | `daguanyuan` | 稻香村回话，凤姐赏识，认作女儿 |
| `c27-daiyu2` | C27-088–093 | `daguanyuan` | 黛玉梳洗出院，不理宝玉；宝玉随后追来 |
| `c27-tanchun` | C27-094–107 | `daguanyuan` | 看鹤舞、石榴树下探春托买物品与说鞋，恼赵姨娘 |
| `c27-huazhong` | C27-108–115 | `qinfang` | 宝玉收落花，登山渡水奔花冢，闻呜咽声 |
| `c27-zanghua` | C27-116–128 | `qinfang` | 黛玉泣残红、葬花吟十二节点、宝玉痴倒 |

## 场景设计与复用推定

| 编号 | 推定 | 依据 | 处理 |
| --- | --- | --- | --- |
| C27-D1 | 潇湘馆代用 `daguanyuan` | 「院门响处」「洒了几点泪」在潇湘馆院内；本项目此前无潇湘馆专图 | 用 `daiyu_place` 锚点，place 写「大观园 · 潇湘馆」 |
| C27-D2 | 芒种园中群像用 `daguanyuan` | 「大观园中之人都早起来了……满园里绣带飘飖」是全景 | `tea_place` 落点，显示探春、惜春 |
| C27-D3 | 滴翠亭复用 `qinfang` | 「四面俱是游廊曲桥，盖造在池中水上」与沁芳亭水景、曲桥语义一致 | `bank_west`/`bridge_head`/`bridge_mid`/`corner` |
| C27-D4 | **花冢复用 `qinfang` 的 `tomb`** | 「那日同林黛玉葬桃花的去处……将已到了花冢」即第 23 回地点；`tomb` 在 `to_tomb` 路线 `anchor_ids` 内、可通行、可立人 | 黛玉 `show` 在 `tomb`，宝玉由 `bridge_mid` 移入；**不新建地图** |
| C27-D5 | 稻香村（李氏房中）代用 `daguanyuan` | 「才往稻香村来……到了李氏房中」；无稻香村专图 | `liwan_place` |
| C27-D6 | 葬花吟作逐字韵文节点 | 「听他哭道是」指明是黛玉哭吟 | 12 节点、speaker `daiyu`、`textKind: verbatim` |
| C27-D7 | 偷听对答一律 narrator | 底本用「只听说道」「又有一人说话」刻意隐去说话人，至段 6 才点出「红儿的言语」 | 不臆断说话人 |
| C27-D8 | 四名有台词角色报登记新 cast | 坠儿、晴雯、司棋、绮霰原 cast 表均无 | 用 snake_case id，见下表 |
| C27-D9 | 提及不登场的人物 | 文官、待书、入画、紫绡等本回无独立台词 | 正文保留，不 show、不注册 |
| C27-D10 | 奔花冢用两段 move 交代 | 「登山渡水，过树穿花」在同段内完成，换场景才清台 | `bank_east>bridge_mid`、`bridge_mid>tomb` |

**地图结论：零新图。** 查 `maps/*.tmj` 后，花冢/桃林由 `qinfang` 的 `tomb` / `peach_grove`
承接，滴翠亭的池中曲桥亦落在同一图；无需新建 `.tmj`，故不触发
`build_chapterNN_maps.py` / `map:framing`。

> 备注：并行制作中出现了 `maps/xiaoxiang.tmj`（潇湘馆，8 锚点）。本回按第 24 回
> 「潇湘馆无专图、以大观园全景代用」的既定口径未切换过去，以免与并行 agent 的
> 地图改动和 scene-places 登记产生耦合；若主 agent 统一登记该 scene，可后续回改。

## 考据更正：司棋的性别与外貌依据

首版司棋立绘被渲染成男性青年，这是错的，2026-11-25 已重做。错因与更正如下。

**性别：女。** 底本称她「这麼大丫頭」「这麼大丫頭了」（第七十一回），与鸳鸯、迎春同为女子。
首版提示词只写了 `a tall broad-shouldered maidservant`，没有锚定性别，
又叠了「宽肩、方脸、粗眉、硬朗」这一串偏男性向的形容，模型据此画成了男性青年。
新版提示词改为 `a tall broad-shouldered FEMALE servant woman … clearly a woman and not a man`。
**教训**：第 26 至 30 回这批角色的提示词风格是「全身场景描述」，与早期角色的
「面部特征 + 性别锚定」（如 `a young BOY rather than a woman`）不同，漏写性别词就会翻车。
已为同批 9 名角色逐条补上 `GIRL` / `WOMAN` / `MAN` / `MALE` 等锚定，并在
`art/identity/character-designs.json` 的 `features` 里写明性别的底本依据。

**「身量高大」与服饰出自第七十一回，不是本回。** 本回正文只写「因见司棋从山洞里出来，
站著系裙子」与「司棋道：『没理论。』」，没有任何外貌描写。
「穿红裙子梳鬅头高大丰壮身材的，是迎春房里的司棋」是第七十一回第七十六行的原话，
由鸳鸯在月下所见。这一回才补录进来，用以确定「身量高大」这个设定并定下红裙与鬅头。
首版设计用「深青夹袄 + 黑发网」，与原文的红裙不合，新版改为 **红裙 + 深青短袄 + 圆髻黑网**。

**年龄是设计推定。** 底本未给司棋年龄，新版写作「late twenties」。

## 新角色清单（cast 与美术已登记，视觉设定见 `docs/chapter27-characters.md`）

| 建议 id | 中文名 | 底本依据 | 一句话视觉设定（含服饰色彩） |
| --- | --- | --- | --- |
| `zhuer` | 坠儿 | 「坠儿道：『何曾见林姑娘了。』」「便是听了，管谁筋疼」 | 十三四岁小丫鬟，双丫髻，浅杏黄细布衫罩青灰比甲，素银耳钉，眉眼机灵里带点憨气。 |
| `qingwen` | 晴雯 | 「晴雯一见了红玉，便说道：『你只是疯罢！』」「冷笑道：『怪道呢！原来爬上高枝儿去了』」 | 十六七岁怡红院大丫鬟，水红绫子袄配月白纱裙，珍珠斜簪，袖口常挽，眉眼尖利、唇薄性烈。 |
| `siqi` | 司棋 | 「因见司棋从山洞里出来，站著系裙子」「司棋道：『没理论。』」 | 十八九岁迎春房大丫鬟，身量高壮，藕荷色比甲压深青裙，髻插银簪，眉目爽利带不耐。 |
| `qixian` | 绮霰 | 「绮霰道：『你听听他的嘴！你们别说了，让他逛去罢。』」 | 十五六岁怡红院丫鬟，鸭蛋青竹布衫配白绫裙，垂双鬟，眉眼平和，是替人解围的温和模样。 |

四人均为 snake_case，台词已在生成器里按真值使用；**未**修改 `src/story.ts`、
`manifest.json`、`art/identity/**`、`character-facing.json`。

## 不入 cast 的本回人物

文官、待书、入画、紫绡、巧姐、大姐、张材家的、旺儿、五奶奶、舅奶奶
（后两位只出现在红玉转述的「四五门子话」里），以及只被提及的林之孝夫妇。
均只在正文出现，无独立台词，**不 show、不登记**。
贾芸（「还芸二爷去」）已在 cast，但本回只被提及，未登场。

## 验收清单

- [x] `python3 scripts/build_chapter27.py` 成功，写出三份 JSON
- [x] `python3 scripts/build_chapter27.py --check` 通过（128 节点 / 14 段）
- [x] 底本 19 段正文的全部子句被节点正文覆盖（漏 0 子句）
- [x] 生成器自校：节点 id 唯一、位置全局单调、focus 非空、lead 逐字可查、move 前必须 show
- [x] `npm run check:anchors` 通过（423 路线锚点全通，37 装饰锚点）
- [x] `npm run check:content` 通过（草稿已接入 story.ts）
- [x] 零新图，`map:framing` / `build_chapter27_maps.py` 不适用
- [x] 未触碰 story.ts / manifest / scene-places / titles / check_content / 共享测试
- [x] 主 agent 登记 4 名新 cast（`zhuer`/`qingwen`/`siqi`/`qixian`）及 portrait/chibi、facing、manifest 资产
- [x] 主 agent 接入 `src/story.ts`、`chapter-titles.json`、`check_content.mjs` 回号与浏览器回归样本
