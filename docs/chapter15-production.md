# 第十五回制作记录 · 王凤姐弄权铁槛寺 秦鲸卿得趣馒头庵

> 状态：**已完成并接入** —— 通过内容门禁、单元测试、地图可达性门禁与剧情走位门禁。
> 剧情、四张新地图、人物资产、账簿与卡面均已上线。

## 目标与来源

- 回目全名：第十五回 · 王凤姐弄权铁槛寺 · 秦鲸卿得趣馒头庵
- 底本：网络公共文本抓取；本地正文 `docs/chapter15-source.txt`（15 554 字节，用 `“”` 引号）
- 剧情、段落：`design/chapter15-story.json`（49 节点）、`design/chapter15-sections.json`（10 段）
- 生成器：`scripts/build_chapter15.py`
- 衔接：紧接第十四回北静王路奠；本回赠念珠、出城送殡、村庄打尖、铁槛寺安灵、水月庵智能儿、净虚求情、秦钟智能儿、旺儿修书。
- 实际出场：北静王水溶、凤姐、宝玉、秦钟、贾珍、贾蓉、宝珠、智能儿、净虚、二丫头、旺儿、传话来人。

## 事件覆盖表

| 原文起句 | 时间层 | 段落 | 地点/scene | 在场人 | 压缩/改写说明 |
| --- | --- | --- | --- | --- | --- |
| 话说宝玉举目见北静王水溶 | present | c15-prince | 会芳园/c14_funeral | 水溶、宝玉、贾政 | 「果灵验否」「雏凤清于老凤声」；赠鹡鸰香念珠一串 |
| 且说宁府送殡，一路热闹非常 | present | c15-road | 出城大路/c15_road | 凤姐、宝玉、秦钟、贾珍 | 凤姐邀宝玉同车；两骑马压地飞来报「这里有下处」 |
| 早有家人将众庄汉撵尽 | present | c15-village | 村庄/c15_village | 凤姐、宝玉、秦钟 | 村姑庄妇；宝玉见锹橛锄犁而问名色 |
| 一面说，一面又至一间房前 | present | c15-spinning | 村庄/c15_village | 宝玉、秦钟、二丫头 | 纺车拧转作耍；二丫头「别动坏了」；秦钟暗拉宝玉「此卿大有意趣」 |
| 走不多时，仍又跟上大殡了 | present | c15-temple | 铁槛寺/c15_tiejian | 凤姐、贾珍、宝珠 | 安灵于内殿偏室；宝珠安于里寝室相伴 |
| 原来这铁槛寺原是宁荣二公当日修造 | present | c15-shuiyue | 水月庵/c15_shuiyue | 凤姐、宝玉、秦钟、净虚、智能儿 | 馒头庵即水月庵；凤姐嫌不便，腾出两间房；智能儿倒茶 |
| 凤姐也略坐片时 | present | c15-petition | 水月庵/c15_shuiyue | 净虚、凤姐 | 张家金哥退亲事；「你叫他拿三千银子来，我就替他出这口气」全句保留 |
| 谁想秦钟趁黑无人 | present | c15-night | 水月庵/c15_shuiyue | 秦钟、智能儿、宝玉 | 智能儿「除非等我出了这牢坑」；宝玉撞破 |
| 一宿无话。至次日一早 | present | c15-letter | 水月庵/c15_shuiyue | 凤姐、宝玉、旺儿 | 凤姐再留一日；命旺儿修书长安，托主文相公假托贾琏所嘱 |
| 却说凤姐等又过一日 | present | c15-farewell | 铁槛寺/c15_tiejian | 凤姐、秦钟、宝珠、贾珍 | 凤姐照望；宝珠执意不肯回家 |

## 地图、人物、资产

| ID | 新建或复用 | 来源 | 状态 |
| --- | --- | --- | --- |
| c15_road（出城大路 · 铁槛寺道） | **新建场景** | `scripts/build_chapter15.py` 写入 `maps/c15_road.tmj` | theme=street，7 锚点 |
| c15_village（铁槛寺下 · 村庄） | **新建场景** | 同上 | 7 锚点 |
| c15_tiejian（铁槛寺） | **新建场景** | 同上 | 7 锚点 |
| c15_shuiyue（水月庵） | **新建场景** | 同上 | 7 锚点 |
| c14_funeral（会芳园） | 复用 | 第十四回已建 | 赠念珠一段 |
| jing_xu 净虚 / zhi_neng 智能儿 / er_ya_tou 二丫头 / wang_er 旺儿 | 新人物·已立绘 | 与旧 45 人同一管线 | portrait + chibi 已入 manifest、calibration、facing |

### 为什么多出一张「出城大路」

初版把「凤姐邀宝玉同车」放在 `c14_funeral`，但那张图是灵前的院落，没有城门、没有路。
补建 `c15_road` 之后，「出城 → 两骑马压地飞来报下处 → 一同往铁槛寺」这一段有了自己的舞台，
走位也才成立（宝玉骑马 → 下车 → 上凤姐的车）。

### `c15_tiejian` 的地板几何修正

初版 `c15_tiejian` 的 A0 地块高度是 9，覆盖行 9–17，而 `court` 锚点在行 18，
于是构建时报 `AssertionError: c15_tiejian: anchor court (20,18) stands outside every floor`。
把 A0 高度改成 11（覆盖行 9–19）之后，`court` 落在地板内，四张图的锚点两两可达。

## 验证结果

- `npm run check:content` → 通过：1016 节点 / 121 段 / 42 地图 / 68 人物 / 254 资产；第十五回 49 节点。
- `npm test` → 65/65 通过（末节点断言为 `C15-091`）。
- `node scripts/verify_map_paths.mjs` → 四张新图全部通过。
- `node scripts/verify_story_walks.mjs` → 全部 308 段 move 都有真实路径。
- `scripts/build_chapter15.py` 内建 `verify_sources()`：本回 10 条 `paragraphLead` 逐条比对底本，0 条不匹配。

## 目检实际核对项

- 10 段各截一张，确认人物落地、屋壳无穿模、控制台无报错。
- 新人物净虚、智能儿、二丫头、旺儿的立绘与 Q 版已目检。
  净虚立绘朝左（脑后发髻在画面右侧），其余三人的立绘朝右；
  智能儿、二丫头、旺儿的 Q 版朝右，净虚的 Q 版朝右。
  其中 8 张检测器读不出，由目视判读登记在 `scripts/build_facing.py` 的 `REVIEWED`。

## 交接

- 已随 `src/story.ts` 的 `script15`/`sections15`、`bookNames[15]` 一并接入。
- 账簿 3 笔（鹡鸰香念珠、胡家十两、张家退亲事三千两），卡面 3 张，见 `docs/production/ledger.md`。
- 未做 `chapter15-evidence.json`（门禁不强制）。
