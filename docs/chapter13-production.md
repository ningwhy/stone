# 第十三回制作记录 · 秦可卿死封龙禁尉 王熙凤协理宁国府

> 状态：**已完成并接入** —— 通过内容门禁、单元测试、地图可达性门禁与剧情走位门禁。
> 剧情、地图、人物资产、账簿与卡面均已上线。

## 目标与来源

- 回目全名：第十三回 · 秦可卿死封龙禁尉 · 王熙凤协理宁国府
- 底本：网络公共文本（gb18030）抓取；本地正文 `docs/chapter13-source.txt`（15 847 字节）
- 剧情、段落：`design/chapter13-story.json`（62 节点）、`design/chapter13-sections.json`（10 段）
- 生成器：`scripts/build_chapter13.py`（剧情与地图的唯一真相源）
- 衔接：紧接第十二回年关黛玉返扬州；本回开篇凤姐夜梦秦氏托预言「月满则亏」，末段凤姐协理宁国府引出第十四回点卯理事。
- 实际出场：凤姐、平儿、秦可卿（梦中）、贾珍、贾蓉、宝玉、袭人、贾母、邢夫人、王夫人、尤氏、薛蟠、秦业、秦钟、戴权、宝珠。

## 事件覆盖表

| 原文起句 | 时间层 | 段落 | 地点/scene | 在场人 | 压缩/改写说明 |
| --- | --- | --- | --- | --- | --- |
| 话说凤姐和宝钗去后 | dream | c13-dream | 凤姐院/c6_wangchui | 凤姐、平儿、秦可卿 | 秦氏托梦献策：置祭田、设家塾；「树倒猢狲散」「盛筵必散」全句保留 |
| 忽听一声云板 | present | c13-news | 凤姐院/c6_wangchui | 凤姐、宝玉 | 云板三声，报可卿死了；凤姐「手足无用」 |
| 贾母见他要去 | present | c13-mourning | 贾母院/night | 贾母、宝玉、袭人 | 宝玉急火攻心呕血，坚持即刻过去 |
| 一直到了宁国府前 | present | c13-ningguo | 宁国府/c13_funeral | 贾珍、尤氏、贾蓉、秦业、秦钟 | 停灵会芳园登仙阁，七七四十九日，僧道对坛 |
| 贾珍见父亲不管 | present | c13-coffin | 宁国府/c13_funeral | 贾珍、薛蟠 | 樯木板一段全句保留，「拿一千两银子来，只怕也没处买去」 |
| 可巧这日正是首七第四日 | present | c13-title | 宁国府/c13_funeral | 贾珍、戴权 | 捐龙禁尉；「平准一千二百两银子，送到我家就完了」全句保留 |
| 合族人丁并家下诸人 | present | c13-visitors | 宁国府/c13_funeral | 宝珠、贾珍 | 瑞珠触柱而亡，宝珠甘愿为义女摔丧驾灵 |
| 宝玉听说笑道 | present | c13-recommend | 宁国府/c13_funeral | 宝玉、贾珍、凤姐 | 宝玉耳语荐凤姐，贾珍拉了宝玉往上房来 |
| 贾珍便忙向袖中取了宁国府对牌 | present | c13-assist | 宁国府/c13_funeral | 贾珍、凤姐、王夫人 | 交对牌；「只求别存心替我省钱，只要好看为上」全句保留 |
| 凤姐儿听了这话 | present | c13-five | 三间抱厦/c13_baosha | 凤姐、贾珍 | 五件弊病与三件 wax 断语；点卯看戏两件事的伏笔 |

## 地图、人物、资产

| ID | 新建或复用 | 来源 | 状态 |
| --- | --- | --- | --- |
| c13_funeral（宁国府 · 会芳园停灵） | **新建场景** | `scripts/build_chapter13.py` 写入 `maps/c13_funeral.tmj` | theme=interior，8 锚点，锚点两两可达 |
| c13_baosha（宁国府 · 三间抱厦） | **新建场景** | 同上 | theme=interior，4 锚点，锚点两两可达 |
| c6_wangchui（凤姐院） | 复用 | 第六回已建 | 托梦与云板报丧两段 |
| night（贾母院） | 复用 | 第三回已建 | 宝玉呕血一段 |
| dai_quan 戴权 / bao_zhu 宝珠 | 新人物·已立绘 | 与旧 45 人同一管线 | portrait + chibi 已入 manifest、calibration、facing |

### 为什么本回要另起两张图

第十四回的宁国府是「理事堂 + 领牌处」，第十三回的宁国府是「停灵 + 抱厦」。二者不是同一处空间：
停灵在会芳园登仙阁，抱厦是内宅三间房；把它们塞进一张图会让「灵前」和「办公」混为一谈。
所以第十三回自建 `c13_funeral`，第十四回自建 `c14_office` 与 `c14_funeral`。

### 樯木一段为什么让薛蟠「一千两」不作金额

原文写的是「拿一千两银子来，只怕也没处买去。什么价不价，赏他们几两工钱就是了」——
贾珍实际付的只是几两工钱，全本 `amount` 硬约束为 `[2, 20, 50, 100]`（见 `tests/ledger.test.ts`），
故 `ledger.c13-qiangmu-coffin` 的 `amount` 记 `null`，实数写进 `what`（`scripts/build_ch1315_ledger.py`）。

## 验证结果

- `npm run check:content` → 通过：1016 节点 / 121 段 / 42 地图 / 68 人物 / 254 资产；第十三回 62 节点。
- `npm test` → 65/65 通过。
- `node scripts/verify_map_paths.mjs` → 42 张图中 36 张通过（6 张失败全是既有图的装饰锚点，剧情从未引用）。
- `node scripts/verify_story_walks.mjs` → 全部 308 段 move 都有真实路径。
- `scripts/build_chapter13.py` 内建 `verify_sources()`：本回 10 条 `paragraphLead` 逐条比对底本，0 条不匹配。

## 目检实际核对项

- 10 段各截一张，确认人物落地、屋壳无穿模、控制台无报错。
- 第十三回新人物戴权、宝珠的 Q 版已目检：两人面部朝右，与检测器/目视判读一致。

## 交接

- 已随 `src/story.ts` 的 `script13`/`sections13`、`bookNames[13]` 一并接入。
- 账簿 2 笔（樯木、捐龙禁尉一千二百两），卡面 2 张，见 `docs/production/ledger.md`。
- 未做 `chapter13-evidence.json`（门禁不强制）。
