# 第十四回制作记录 · 林如海捐馆扬州城 贾宝玉路谒北静王

> 状态：**已完成并接入** —— 通过内容门禁、单元测试、地图可达性门禁与剧情走位门禁。
> 剧情、地图、人物资产、账簿与卡面均已上线。

## 目标与来源

- 回目全名：第十四回 · 林如海捐馆扬州城 · 贾宝玉路谒北静王
- 底本：网络公共文本抓取；本地正文 `docs/chapter14-source.txt`（17 156 字节，**用 `「」` 引号**，与第十三、十五回的 `“”` 不同）
- 剧情、段落：`design/chapter14-story.json`（52 节点）、`design/chapter14-sections.json`（10 段）
- 生成器：`scripts/build_chapter14.py`
- 衔接：紧接第十三回凤姐协理宁国府；本回凤姐立威、昭儿报林如海死讯、发丧、北静王路奠，为第十五回赠念珠与出城送殡留出空场。
- 实际出场：凤姐、平儿、贾珍、尤氏、宝玉、秦钟、来升、昭儿、宝珠、王兴媳妇、北静王水溶、邢夫人、王夫人。

## 事件覆盖表

| 原文起句 | 时间层 | 段落 | 地点/scene | 在场人 | 压缩/改写说明 |
| --- | --- | --- | --- | --- | --- |
| 话说宁国府中都总管来升 | present | c14-warn | 宁国府/c13_funeral | 来升、凤姐 | 「那是个有名的烈货，脸酸心硬」；传凤姐卯正二刻点卯的定规 |
| 按名查点，各项人数都已到齐 | present | c14-duties | 理事堂/c14_office | 凤姐、彩明 | 点卯分派：四十人分四班值事，各司其职 |
| 素日跟我的人 | present | c14-rules | 理事堂/c14_office | 凤姐 | 定则例一整段照录，含「卯正二刻」「戌初烧过黄昏纸」 |
| 凤姐刚欲起身 | present | c14-cry | 会芳园/c14_funeral | 凤姐、平儿、贾珍 | 五七正五日，灵前大哭；「那眼泪恰似断线之珠」 |
| 来旺媳妇献茶漱口毕 | present | c14-beating | 理事堂/c14_office | 凤姐、来旺媳妇 | 误事者打二十板子，革来升一月银米 |
| 如今且说宝玉因见今日人众 | present | c14-baoyu | 理事堂/c14_office | 宝玉、秦钟、凤姐 | 抱厦一段；「好长腿子，快上来罢」 |
| 正闹著，人回：「苏州去的人昭儿来了。」 | present | c14-zhao | 理事堂/c14_office | 昭儿、凤姐 | 林如海九月初三日巳时没，凤姐打点大毛衣服 |
| 凤姐见日期有限 | present | c14-prepare | 宁国府/c13_funeral | 凤姐、贾珍 | 发送殡筹备；并行理事的分派 |
| 至天明，吉时已到 | present | c14-procession | 会芳园/c14_funeral | 凤姐、贾珍、宝珠 | 六十四名青衣请灵，铭旌全称 |
| 只见宁府大殡浩浩荡荡 | present | c14-prince | 会芳园/c14_funeral | 水溶、贾珍、贾赦、贾政 | 四王路奠，北静王水溶出场 |

## 地图、人物、资产

| ID | 新建或复用 | 来源 | 状态 |
| --- | --- | --- | --- |
| c14_office（宁国府 · 理事堂与领牌处） | **新建场景** | `scripts/build_chapter14.py` 写入 `maps/c14_office.tmj` | theme=interior，7 锚点 |
| c14_funeral（宁国府 · 会芳园停灵） | **新建场景** | 同上 | theme=interior，7 锚点（含新增 `door`） |
| c13_funeral（宁国府上房） | 复用 | 第十三回已建 | 来升传话、发送殡筹备两段 |
| lai_sheng 来升 / zhao_er 昭儿 / shui_rong 水溶 | 新人物·已立绘 | 与旧 45 人同一管线 | portrait + chibi 已入 manifest、calibration、facing |

### `c14_funeral` 为什么补了一个 `door` 锚点

原文明写凤姐与平儿是从荣府来，在宁府大门内下车处站定，再往园中灵前。
初版没有这个锚点，剧情只能凭空引用一个不存在的 `street`，导致 `C14-031/032` 的 move 落空。
补 `door: [13, 21]` 并把它接进 `main` route（`door → gate → garden → chair`）之后，
「下车 → 进门 → 走到灵前」这一段走位才真正走得通。

### `C14-040` 的场景切换陷阱（2026-11-03 修复）

`C14-040` 是本回切换到 `c14_office` 的**第一个**节点。engine 的 `enter()` 在切场景时会把
所有人置为不可见，因此该节点若直接写 `move('feng', ...)`，必然撞上
`移动角色未显示：feng`——这正是本轮 `npm test` 里 3 个用例失败的根因。
修法是在同一节点先 `show` 再 `move`：

```python
[show('feng', 'door'), move('feng', 'door', 'hall_door', 'seat')]
```

同一条纪律适用于全项目：**每个场景的首个节点，凡有 move 的角色都必须先 show。**
新增 `scripts/verify_story_walks.mjs` 就是为了把这条纪律变成门禁，而不是靠人记住。

## 验证结果

- `npm run check:content` → 通过：1016 节点 / 121 段 / 42 地图 / 68 人物 / 254 资产；第十四回 52 节点。
- `npm test` → 65/65 通过（`tests/engine.test.ts` 的末节点断言同步改为 `C15-091`）。
- `node scripts/verify_map_paths.mjs` → `c14_office` / `c14_funeral` 锚点两两可达。
- `node scripts/verify_story_walks.mjs` → 全部 308 段 move 都有真实路径。
- `scripts/build_chapter14.py` 内建 `verify_sources()`：本回 10 条 `paragraphLead` 逐条比对底本，0 条不匹配。

## 目检实际核对项

- 10 段各截一张，确认人物落地、屋壳无穿模、控制台无报错。
- 新人物来升、昭儿、水溶的 Q 版与立绘已目检：三人的立绘朝左（净虚之外唯一朝左的两个），
  水溶的 Q 版朝右；这两张立绘的检测器读不出，由目视判读登记在 `scripts/build_facing.py` 的 `REVIEWED`。

## 交接

- 已随 `src/story.ts` 的 `script14`/`sections14`、`bookNames[14]` 一并接入。
- 账簿 2 笔（革来升一月银米、内务支给灯油蜡烛纸札），卡面 1 张（两笔共用），见 `docs/production/ledger.md`。
- 未做 `chapter14-evidence.json`（门禁不强制）。
