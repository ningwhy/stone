# 第十九回制作记录 · 情切切良宵花解语　意绵绵静日玉生香

> 状态：**剧情数据已生成并通过定向验收**（2026-11-11 凌晨）。

## 一、底本

- 文件：`docs/chapter19-source.txt`
- 来源：中文维基文库《紅樓夢》第 019 回（维基限流时先 curl 存 `/tmp/ch019_raw.txt` 再走脚本缓存）
- 规模：**29 段**（段 0 是回目联）、9187 字（简体），无 `<sectionbegin>` / `<poem>` 残留
- **注意**：第 19 回底本把回目联单独作段 0（第 18 回没有）——切片段号全部按「段 1 起」计。

## 二、生成方式（底本切片）

沿用第 18 回方法论：`scripts/build_chapter19.py` 按「起句 → 止句」切片，
正文与 `source.paragraphLead` 都从底本切出，写盘前自校（lead 与正文逐字落在底本），
失败即退出不落盘。

**本回新增的校验**：`check_anchors` 从「锚点名存在」升级为「**锚点可通行**」——
用项目自己的 `parseTiledMap` 算 walkable（与运行期同一套判定）。
这是第 18 回踩过的坑：`c11_tianxiang` 的 `stage`、`c5_ningfu` 的 `portrait_wall`
都是「存在但走不上去」的锚点，引擎 `show` 会抛「显示地点不可通行」。

## 三、产出

- `design/chapter19-story.json`：**78 节点**（C19-001~078）
- `design/chapter19-sections.json`：**8 段**
- `design/chapter19-evidence.json`：**83 条证据**（78 explicit + 5 design）

### 分段与场景

| 段 | 场景 | 节点 | 内容 |
|---|---|---|---|
| c19-ningfu | `c5_ningfu` | 001-006 | 贾妃赐酥酪、宁府看戏（《丁郎认父》《孙行者大闹天宫》）、宝玉走开闲耍 |
| c19-study | `c5_ningfu` | 007-014 | 小书房撞破茗烟与卍儿、宝玉放那丫头去、问名字岁属 |
| c19-mingyan | `c5_ningfu` | 015-018 | 茗烟提议出城、找花大姐姐、二人从后门走了、半里路到门前 |
| c19-xirenhome | `xiren_home` **（新建）** | 019-029 | 花自芳迎客、袭人用手炉脚炉茶杯待宝玉、摘通灵玉与姊妹传看、松子穰 |
| c19-liaolao | `night`（怡红院占位） | 030-043 | 雇轿送归、李嬷嬷吃酥酪、照见人家照不见自家、茜雪旧事、晴雯赌气、风干栗子 |
| c19-shuzhen | `night` | 044-059 | 穿红的两姨妹子、赎身之论、死契来历（转述）、去定了 |
| c19-huayu | `night` | 060-066 | 三件事（不说化灰化烟 / 喜读书的样子 / 不毁僧谤道吃胭脂）、三更安歇、次日袭人感寒 |
| c19-yusheng | `dinner`（黛玉歇午占位） | 067-078 | 黛玉歇午、幽香、暖香冷香、黛山林子洞故典、宝钗走来 |

### 新建地图 `xiren_home`

`scripts/build_chapter19_map.py`：40×40 室内主题，小院（zone A0，16×10）+ 里屋（zone ROOM，14×10 贴邻），
`farm-house` 壳 + `plain-kang` / `square-table` / `round-stool` / `cabinet` / `lamp-stand` / `flower-gate`。
锚点 7 个：`gate / yard / room_door / room / kang / table / host`，**全部可通行**
（可通行的真正来源：zone id 匹配 `^(A\d*|B|C|D|E|F)$` 的地板 + Routes 走廊——
每一个要站人的锚点都必须出现在某条 route 的 `anchor_ids` 里，见 `src/model.ts`）。

## 四、美术

零新增。袭人（`xiren`）与李嬷嬷（`nurse_li`）已在 cast 与 manifest；
茗烟 / 花自芳 / 秋纹 / 晴雯 / 卍儿均以 `messenger` 代指或叙事带过（不新增立绘）。

## 五、注册清单（全部完成）

- `src/story.ts`：import ×2 + story 数组 + chapters 数组 + bookNames `"19":"第十九回"`
- `design/chapter-titles.json`：「情切切良宵花解语 / 意绵绵静日玉生香」（与底本逐字相符）
- `scripts/check_content.mjs`：`VERBATIM_BASE={16,17,18,19}`
- `tests/browser-smoke.mjs`：「查无此人」样本「晴雯」→「麝月」（晴雯恰在第 19 回登场；
  **每个新回目上线都要重核这个样本**——妙玉被 18 回推翻，晴雯被 19 回推翻，麝月要到 20 回才登场）
- `src/App.tsx`：「原文与改编」面板补第 19 回描述（引文逐字核过在底本）；「前十八回」→「前十九回」

## 六、踩坑实录（新增 5 条）

1. **段落号偏移**：第 19 回底本段 0 是回目联 → 切片段号整体 -1。
2. **止句必须逐字**：底本是「**待**晚间再来」不是「至晚间再来」；「好**哥哥**」不是「好宝玉」。
3. **长段拆分**：段 13（777 字）拆 4 节点；「原来袭人在家…哭闹」是**转述**（layer=reported、无动作、人物不上台）。
4. **dev server 缓存**：旧 vite 实例不会热更新 JSON import → 测新回目前先 kill 5173 重启。
5. **TOC 搜索测什么**：搜索覆盖段落标题+正文（`toc.ts` 的 haystack），
   但测「正文词」必须先确认该词真的在某个节点的 text 里（「茅檐草舍」在段尾被切掉了，改用「卍儿」）。

## 七、验证

| 检查 | 结果 |
|---|---|
| `python3 scripts/build_chapter19.py` | 78 节点 / 8 段 / 83 条证据，全部校验通过（含 walkable） |
| 锚点可通行探针 | 全部锚点可通行 ✓ |
| `npm run check:content` | 1292 nodes / 157 sections / **43 maps** / 0 ERROR；19:78 |
| `npx tsc --noEmit` | 通过 |
| `npm run build` | 通过 |
| `node --experimental-strip-types tests/chapter19.mjs` | **通过**：8 段推进、4 场景（含新 xiren_home）、搜索「卍儿」落 c19-*、封底「全书至此」（第 20 回未上线）、78 节点正文逐字在底本 |
| `node --experimental-strip-types tests/save-compat.mjs` | 通过：第 17 回旧档读回原位、缺角补隐、能继续读 |
| `npm run test:browser` | **通过**（18 分 09 秒）：354 节点、43 张地图（含新 xiren_home）、0 断言失败 |
| 线上 `tests/online-chapter19.mjs` | **通过**：目录 19 回全列、8 段推进、4 场景、封底「全书至此」、70 图 0 破图、0 非 403 失败 |

### 部署记录（2026-11-11）
- 第一次部署的 dist 是修正 `portrait_wall` 之前构建的 → 线上 seek 抛错。
  **教训：改 design JSON 后必须 `npm run build` 再 rsync——部署的是 dist，不是 design。**
- 第二次构建 `index-Dfyvxe00.js` 部署后线上全绿（回环 200 / 外网 200 / 关键词逐字命中）。

## 八、部署与线上复验

同第 18 回纪律：rsync → `/www/wwwroot/stone.new` → 原子 `mv` 覆盖（勿用通用 yanpub-deploy）。
线上复验可参照 `tests/online-chapter18.mjs` 写 `tests/online-chapter19.mjs`。

## 九、给第 20 回的提示

- 底本已就绪：`docs/chapter20-source.txt`（30 段 / 5287 字）。
- 第 20 回 = 王熙凤正言弹妒意（赵姨娘、贾环）+ 林黛玉俏语谑娇音（史湘云首次登场）。
  **需要新角色美术**：贾环（`jia_huan`）、赵姨娘（`zhao_yiniang`）、史湘云（`shi_xiangyun`）。
  记住硬耦合：cast 每加一人，manifest 必须同时补 `-portrait` 与 `-chibi`，
  否则 `tests/character-identities.mjs` 的 `images.length===castCount` 失败。
- browser-smoke 的「查无此人」样本：麝月若在第 20 回登场（原著如此，第二十回她有戏份），**还得再换**。
