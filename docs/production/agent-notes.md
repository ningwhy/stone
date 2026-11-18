# 生产笔记（agent 交接用）

> 本文是**长格式**版本，`.workbuddy/memory/MEMORY.md` 是它的浓缩索引。
> 两者同源：MEMORY.md 里被截断的细节，原文都在这里。

## 一、新增一回目（SOP 七步的工程细节）

### 1. 底本切片式生成

生成器一律 `scripts/build_chapterNN.py`，**正文与 `paragraphLead` 都从底本切出**，写盘前自校，失败即退出不落盘。

- **切分粒度按底本句长定**：
  - 16-22 回：句级 `(?<=[。！？])`
  - 底本句子长时：子句级 `(?<=[。！？；，：、])`（23 回：29 段 / 199 句 / 669 子句）
  - **索引粒度必须与 CUTS 粒度一致**，否则切分点对不上、报越界。
- 闭合引号（`”’」』`）必须**归入前一个**子句，否则出现以孤立 `」` 开头的节点。
- 节点正文宜**延到整句末**（下个 `。！？` 之后），否则读感像拦腰砍断（16-22 回 98-100% 以句末标点收尾）；`lead` 仍取子句起点（是正文前缀且逐字可查）。
- **硬门槛**：`(段号, 句/子句号)` 全局单调递增；允许同号两节点（叙述+台词）、允许跳句。
- 坑：
  - 引号 `“”` vs `「」` 要**归一化检索**；
  - 段落区间按偏移换算，别用 `find`；
  - 维基 `<sectionbegin="诗题"/>` 要清干净。
- **舞台连续性自检必须写进 build 脚本**：引擎只在**换场景**时清空舞台 → 「move 一个从没 show 过的人」要到读者点那步才抛。**换场景的首节点必须补 `show`**。只查 `move`（`effect`/`hide` 对不在台上的人是空操作）。
- `effect.kind` 合法值仅 `'jade'|'greet'|'rest'|'idle'|'anger'`。

### 2. 接入顺序（顺序反了会立刻挂）

1. 美术入 `public/assets/rongguo/manifest.json`；
2. **之后**才注册 cast（`src/story.ts`）——顺序反了图鉴断言立刻挂（`tests/character-identities.mjs` 断言 `images.length===castCount`）。
3. `src/story.ts`：import scriptNN/sectionsNN → 拼 `story` → 拼 `chapters` 并 `.map(s=>({...s,book:NN}))` → `bookNames` 加 `"NN":"第NN回"`。
4. `design/chapter-titles.json` 加 `books["NN"] = {first, second}`。
   - ★ **漏了回目联，报错会出现在「上一回」的测试里**：`src/Leaves.tsx` 的 `ChapterBackCover` 用 `chapterTitle(nextBook)` 取下一回的回目联，取不到（null）就走进 else 显示「全书至此」——于是第 21 回的封底在第 22 回上线后说错话。
   - 排查手法：**先在 Node 里实读 `chapterLeaves()`/`bookNames` 确认「下一回是哪一回」算对了，再看组件读的是什么**。数据层对、组件层错 → 某个 lookup 返回了 null。
5. `scripts/check_content.mjs` 的 `VERBATIM_BASE` 加回号（`{16,17,18,19,20,21,22}`，集合内每节点 lead 须在 `docs/chapterNN-source.txt` 逐字可查）。
6. **新 scene 必须先补 `design/scene-places.json`**（level/region/col/row/name）——定位转场静态门禁会拦。
7. `tests/browser-smoke.mjs` 换「查无此人」样本（见下）。

### 3. 验收链

```
check:content → check:anchors → tsc --noEmit → npm test → test:locator
→ build → verify-album-title → 定向测试 → browser-smoke → 部署 → 线上复验
```

---

## 二、回次纪律（每加一回就会咬人的地方）

### 「查无此人」样本

判据要覆盖**所有可搜路径**（正文 / 标题 / 地点 / 在场人物 / 段 id）——**只查正文不够**，名字出现在地点或人物表里照样能命中。

- 样本随回目推移而失效：妙玉 →（18 回）晴雯 →（19 回）麝月 →（21 回）紫鹃 →（22 回）檀云 →（23 回）彩云。
  - 23 回的 `檀云` 是被底本原句「室霭檀云品御香」推翻的——那句说的是檀香熏的云气。
- **当前样本：`侍书`**（黛玉房里的丫鬟，原著确有此人，但二十三回里一次也没出现，也不在 cast 表里）。
- 零命中候选池：檀云 / 坠儿 / 佳蕙 / 翠墨 / 佩凤 / 偕鸾 / 文杏 / 春燕 / 小红 / 芳官 / 素云 / 碧月 / 小螺 / 入画 / 绣橘 / 司棋 / 藕官 / 蕊官 / 葵官 / 豆官 / 艾官 / 宝官 / 玉官。

### 「写死旧回次」的测试断言

每加一回就变红，**都不是产品缺陷**，是测试把自己的历史快照当成了不变量。21 回一次性暴露 5 处：

1. **封底形态不是「某一回的属性」，是「后面还有没有回」的属性**。第 18/19/20 回都断言「全书至此」——那只是它们当时恰是末回。
   → 已抽 `tests/lib/backcover.mjs`，判据与产品代码（`App.tsx` 的 `nextBook`、`leaves.ts` 的 `chapterLeaf`）看同一份数据。**新回不用再改。**
2. **「终幕」只标在全书末节点**（`App.tsx`：`state.index===story.length-1`），不是「某一回末节点」。
   → 用 `assertNodeLabel()` 实读 `story` 判定。
3. 「查无此人」样本（见上）。
4. `engine.test.ts` 写死 `story.at(-1)==='C15-091'` → 改为「末节点属于最高的那一回」。
5. `toc.test.ts` 写死「宝钗只在前四五六八回在台」→ 她在 18/19/20/21 回都有戏份，改为实读。

### 回次文案不得写死数字

`src/App.tsx` 已按 `bookNames` 派生 `bookScope`。中文数字**已改成算法派生**（`src/cnNumber.ts` + `tests/cnnumber.test.ts`），不再是查表——查表上限一满就得回去加一条，加漏了标题上就露出阿拉伯数字。**新回不用再改。** 写这类「N 回」文案时优先按数据算。

### 存档兼容

`src/engine.ts` 的 `SaveData = {version:5; chapter:'five-six'; node:string; state:StoryState}`，`SAVE_KEY='honglou-five-six-chapters:v5'`。

- `restore()` 按 **node id** 定位（`this.steps.findIndex(s=>s.id===data.node)`），追加新回不影响旧档。
- 第 315 行 `if(!state.actors[id])state.actors[id]={col:13,row:28,visible:false,moving:false,direction:1};` 对**所有 cast 角色**补不可见初态，新角色自动覆盖。
- 结论：**新回/新角色无需改动存档逻辑**（23 回核查确认）。

---

## 三、地图与锚点

### 三张「地图表」各管各的

| 文件 | 作用 | 门禁 |
| --- | --- | --- |
| `design/atlas-maps.json` | 读者主动打开的可交互总览（28 个考据建筑） | 无 |
| `design/scene-places.json` | **定位转场**的叙事方位表（45 scene 全覆盖、5 层 10 区域） | 新 scene 漏配被 `check_content` 拦 |
| `maps/*.tmj` | 实际地图（46 张） | `check:anchors` |

**别把前两张搞混。** 舆图接入现状：45 张图里 29 张未进 `atlas-maps.json`（含 16-21 回新建图），与既有回一致，**本项目前不接**。

### 可通行格

仅两来源（`src/model.ts`）：zone id 匹配 `^(A\d*|B|C|D|E|F)$` 的地板 + Routes 层路线沿途走廊。

- **要站人的锚点必须在某条 route 的 `anchor_ids` 里**；名字存在 ≠ 可通行（`show` 会抛「显示地点不可通行」）。
- 已知不可通行（装饰位，设计上不可站人，36 个，不算问题）：`c11_tianxiang:stage`、`c5_ningfu:portrait_wall`、`c10_jinhome:kang/table`、`c6_village:table`、`c12_sickbed:window`。
- **用 `parseTiledMap` 查 walkable。**

### 坐标坑

Tiled 网格是 **128×64 菱形**，`unit = tileheight = 64`（**不是 tilewidth**）；锚点 `col = x/64 - 0.5`，footprint `col = x/64`（不带 -0.5）。

### 路线走廊是 L 形，且在删 blocker 之前生成

`src/model.ts` 的路线走廊是 **L 形（先收敛 col，再收敛 row）**，且走廊生成**在 blocker 删除之前** → 删 blocker 会切断刚画好的走廊。

- `yard`(21,26) 出发的任何横向走廊第一步必过 (20,26)，那正是 `tea-table` 的 ArtFootprints。
- → **修法取「挪家具」而不是改路线表**（改表会让陈设失去意义）：茶几 (20,26) → (21,25)。

### 新建地图后必跑 `npm run check:anchors`

`scripts/check_anchors_walkable.mjs` 区分**路线锚点**（在 route 的 `anchor_ids` 里 → 必须可通行且两两连通，硬门禁）与**装饰锚点**（挂画/戏台/桌案，36 个，不算问题）。**连通性直接用引擎的 `findPath` 判定**（别自己写 BFS，与引擎实际可达性可能不一致）。当前：342→351 个路线锚点全通。

### 「路线声明了但剧情没走」的断路，浏览器回归永远抓不到

22 回实战：`yihong` 的 `to_outer` 断了整整两回都没人发现——第 21/22 回的剧情走的是 `to_inner`（通的），浏览器回归只覆盖**剧情实际走过的路径**，覆盖不到路线表里**声明了但没走**的路径。→ 靠 `check:anchors` 兜底。

### 水渲染

`water` 写在**地图级 properties**（`maps/qinfang.tmj` → `"water": "19,15,3,14"`），`src/model.ts` 的 `rects('water')` 解析，`src/MapScene.ts:207-220` 渲染成河岸 + 水体 + 波纹。

实测运行时像素 `0x93a89f` / `0xa8c5c2` / `0x576e61` **确实出现在画面上**——水没缺，只是被镜头裁在画面边缘（构图问题，非缺陷）。

### 场景键陷阱

`maps/rongguo-entry.tmj` 的 sceneId 是 **`entry`**，切勿改。

---

## 四、cast 与美术管线

### manifest 硬耦合

cast 每加一个非 sedan 角色，须同时在 `public/assets/rongguo/manifest.json` 补 `xxx-portrait` / `xxx-chibi`（image/hash/anchor），否则 `tests/character-identities.mjs` 的 `images.length===castCount` 挂。

### 校准

用 **height**（portrait 600 / chibi 116），chibi 另带 `bodyCompress`（`split=anchorY×0.42, factor=0.64`）。

### faceBox

- **`identity.faceBox` 存在最终 PNG 坐标里**，不是 matte 坐标。matte→最终要过 bodyCompress → 裁切 → 缩放，全是仿射的，可用 `scripts/map_facebox_to_final.py` 精确换算（脚本自带自检，0px 误差）。
- `art/identity/auto-face-boxes.json` 也是最终坐标。
- **缺 `identity.faceBox` → 图鉴以全身像呈现**（非错误）。
- **自动检测只是提案，必须目视重标**：既有 chibi 的框下沿统一在 59~60（下巴线），立绘上沿在发际线略下、下沿到衣领上缘。
- `scripts/inspect_face_boxes.py` 从 manifest 读资产列表 → **新角色未注册时是鸡生蛋**：用 `scripts/detect_face_box_one.py` 跑单张（同一套算法：肤色掩码 + 只在**上部 30%** 做连通块分析，躲开「米白围裙被当肤色」）。
- `inspect_face_boxes.py` 纯自动检测，重跑会打回人工修小过的框（oldmonk / ying_er），有 `REVIEWED` 覆盖层，**新人工裁决的框必须加进去**。

### ★ faceBox 同步纪律（23 回踩过两个坑）

1. **人工重标值要同时写进 `auto-face-boxes.json` 和 manifest**。
   23 回的三个新立绘目视重标值只写进了前者，manifest 里仍是自动检测旧值（`jinyuan-portrait` [134,47,245,198] vs 正确的 [78,22,128,72]）。
   → 修法：走 `scripts/rebuild_new_character_manifest.py` 的 `entry_for()`，它用 `FACE_BOXES.get(key)`（即 auto-face-boxes）作为 faceBox 来源。
2. **绝不可拿 auto-face-boxes 全量覆盖 manifest**。
   那是**自动检测表**，会连带改错 99 条历史人工裁决值（`baoyu-portrait` [90,140,250,285] → [81,12,195,90]、`yingchun-portrait` → [0,54,171,312] 明显错误）。
   → 回滚 `git checkout -- manifest.json` 也不行：**回滚会连带删掉新登记的角色条目**（`KeyError: 'jinyuan-portrait'`，manifest 变回 258 条）。回滚前先备份（23 回用的 `/tmp/manifest-before-rebuild.json`）。

### `build_art_assets.py` 跑完必 `git diff manifest.json`

它按校准表重写整个文件，会清空 `hash`（`npm run art:webp` 盖的章，跑一次补回）；也会抹掉非校准来源角色的 identity 块。

### 入库惯例

`public/assets/rongguo/*.png` 与 `*.webp` **严格成对**，运行时只请求 WebP（`src/art.ts` 换后缀），PNG 是原件存档。`art/source/*` 入库，`art/matted/*` / `*-sam.png` 不入库。

### 渲染机脱网时的替代通道（22 回实战）

先分清「端口不通」与「主机不通」（路由 `REJECT` / ARP `incomplete` = 整台掉线）。后者走：

内置图像生成出**白底全身像** → `scripts/cutout_white_backdrop.py` 抠图（**纯白底不需要 SAM**）→ 校准 → manifest → facing。

画风须对齐既有素材（柔和水墨、淡彩、全身、手交、鞋履可见；竖构图更接近既有立绘）。

### 其他

- **`-portrait-mourning` 从不被 SAM 抠图**（源图纯黑 → 黑方块）。新增同管线情绪变体必须显式过 SAM。`emotion.ts` mourning 正则 `/丧|灵|祭|奠|孝|缟|素|白|素服|素衣/g`。
- **ComfyUI 模型挪目录整条 400**：已加 `_align_model_names()`（按 basename 反查服务器清单）。
- **竹丛教训**：共用 `bamboo-cluster` 源图本身错（绿色 0.0%），SAM 救不回 → 共用素材必须逐张目视。

---

## 五、facing（sprite 朝向）

### 权威表与脚本

- 权威表 `design/character-facing.json`（`scripts/build_facing.py`）
- 文档 `docs/production/facing-list.md`（`scripts/build_facing_doc.py`）
- **改 facing 必须跑这两个脚本**，否则 `check:content` 报 out of date。
- `build_facing.py` 读 `src/story.ts` 的 cast 列表生成权威表。
- 当前：82 actors（62 portraits right / 76 chibis right）、21 variants（19 right）；185 bitmaps, 28 left, 157 right。

### 测量

`scripts/facing_assets.py` + `scripts/facing_vision.swift`。

- **正偏移 = 朝画面右**；`ok` 行符号直接用，**`SWAPPED` 行符号取反**；都要求「鼻与嘴同号」。
- `facing_vision.swift` 的 `nameCheck` 校验 `leftEye < rightEye`。
- 新角色（未走 identity 管线）官方裁切读不到脸 → 改用 `scripts/facing_wide_scan.py`：按 faceBox **手工裁切头部 + 放大到 760-900px**，再用 `facing_vision.swift` 读数。

### ★ Vision 对 Q 版大头身画风可能彻底失效（23 回实战）

三个新 Q 版：成品 64×116 读不出、放大到 1400/2200px 读不出、**768×1024 原始 matte 上也读不出**（`NONE`）；`facing_yaw.swift` 的轮廓路径也返回 `NOFACE`。

**原因不是分辨率，而是 Q 版大头身画风不在 Vision 的拟合范围内。** 既有 79 个角色里立绘全部可读，Q 版有 **33 个靠目视裁决**（既有先例）。

### ★ 被标尺证伪的自动判据（别再试）

| 判据 | 标尺命中率 | 备注 |
| --- | --- | --- |
| 暴力裁切扫描（44 种窗口） | 3 个 right（`jia_rong-chibi` 权威朝左） | 不可采信 |
| 虹膜中线法（成品 64px） | 1/5 | 不可用 |
| 瞳孔双暗簇质心法 | 1/5 | 不可用 |
| 眼白连通域内虹膜偏移法 | 1/2；高分辨率 matte 版 4/6 | 不可用 |
| 鼻影列法 / 嘴唇红簇+鼻影法 | 4/7 | 不可用 |
| 头部轮廓不对称度 | 朝右组均值 +0.0042、朝左组 +0.0077 | 两阵营无法区分 |

- Vision 的 Q 版读数还会**反向**：最终 PNG 上 `jinyuan-chibi` 读出 `right`（wider 裁切），但 768px matte 上读不出。
- **立绘与 Q 版朝向的一致率只有 60/79（76%）**，不能用作推断依据（16 个是「立绘朝左、Q 版朝右」的系统性差异）。

### ★ 目视裁决法（最终采用）

判读标准先在**双向标尺**上标定：

- `cui_lv-chibi`（朝右）→ 鼻尖与嘴落在红线**右侧**
- `jia_rong-chibi`（朝左）→ 鼻尖与嘴落在红线**左侧**

判读底图用 **matte 原生 768px**（不是 64px 成品），并画红线（faceBox 中心）与蓝色坐标网格。

全身姿态交叉验证：朝左标尺是**明显侧身站姿**（单肩、侧脸）；朝右标尺 `cui_lv` / `jia_lan` 是**正面站姿**。

三个新 Q 版（jinyuan/caiyun/jia_qin）鼻嘴基本落在眼中点上、极轻微右偏，且都是正面站姿 → 与 `cui_lv` 同型 → **记为朝右**。

**标尺必须双向**：只用朝右样本无法区分「符号规则」与「巧合」。用 4 朝右（baochai/daiyu/feng/baoyu-chibi）+ 8 朝左，11/12 命中（`jia_lian-portrait` 因 manifest 无 faceBox 属缺样本）才可用于新样本。

样本在 `art/facing-refs/`。

### 其他 facing 纪律

- `build_facing.py` 的 `REVIEWED` 是目视裁决钉死表，**新裁决必须写进去**（含判定理由，供后人复核）。既有 33 个 chibi 走 `method:'visual-review'`。
- **`facing_assets.py --only` 是替换语义** → 会把 `art/identity/facing-assets.json`（145 行历史读数）整体覆盖成 4 行。
  → 修法：先 `cp` 备份，跑完 `--only` 后用 Python 把新旧按 asset key 合并回 149 行。
- Q 版朝向分布惯例：既有 79 个角色中 chibi 为 **73 朝右 / 6 朝左**；portrait 为 60 右 / 19 左。

---

## 六、测试与浏览器坑

### 顶栏按钮「身份漂移」

「跳过移动」和「继续剧情」是**同一个位置上的同一个按钮**，随演出状态换身份。

```js
if(await skip.isVisible())await skip.click();
```

有个时间窗：`isVisible()` 判到「跳过移动」，React 换成「继续剧情」，Playwright 的 `click()` **重新解析 locator** → 点中「继续剧情」→ **剧情多走一步**。

后果不是「多读一句」：一步多走会**跨过本回末节点**，末节点的封底还没翻出来就被跨过去，下一回的封面也来不及翻（第 20 回因此走到了第 21 回的 `yihong` 场景上）。

→ **一律用 `tests/lib/pickup.mjs` 的 `clickSkipIfShown` / `clickForwardIfShown`**：按按钮**当下真实的文案**取元素（`nav button` 比对 textContent）+ `dispatchEvent('click')`，元素一旦取到就是那个元素，React 中途换掉也换不掉已派发的 click。

**排查手段**：别猜，写探针逐步收窄；**探针里 `performance.now()` 跨 `page.evaluate` 不可比**，要用 Node 侧 `Date.now()` 打点 + `page.exposeFunction` 实时回传。

**断言红了先分清是产品的错还是测试的错**（这次产品完全正确，错的是测试点到了另一个按钮）。

### 「改断言前先问它的理由实测成立吗」（22 回教训）

`assertFoldedBackIsNotAPassThrough` 曾断言「收起封底后『继续剧情』必须消失」，理由是防「跳过下一回封面」——**那条理由实测不成立**：封面由 `src/leaves.ts` 的 `leafTrigger`（`nodeId===leaf.firstNode` → `'cover'`）在到达首节点时翻出，与封底收没收起无关。

而这个断言逼出了**真缺陷**：顶栏被锁成「回到封底」，回末节点上读者收起封底后再也推不动。

→ 改为守两条真不变量：①收起封底不前进节点 ②收起后仍能前进且下一回封面照常翻出。
**产品侧**：`foldedBack` 只在**末回**接管按钮（`foldedBack && ended`）。

### 顶栏三态判断顺序

凡按**全书状态**判定的分支（如 `ended`，只在全书末节点为真）排在 `foldedBack` 前面，末回折叠封底后「回到封底」会被「再走一回」顶掉。**这类分支在非末回永远走不到 = 藏着的缺陷**，加一回当末回时才暴露。

### 其它

- **「开启下一回」点击无反应**（独立 bug）：封底在效果演出播完前翻出（status 仍 'moving'）→ `advance()` 被拒。已修：封底 onOpen 先 `if(status==='moving') engine.skip();` 再 `advance()`。
- **测试脚本坑**：封底第一个按钮就是「开启下一回」，通用「关掉任何弹层」的 helper 会点掉它 → 只关 `.leaf-cover`。TOC 是原生 `<dialog>`，用其自带关闭按钮；TOC 里回目是**中文数字**。
- **Vite 旧进程未热更新 JSON import**：测试前必须重启 5173；改 `.tmj` 也要重启。
- **定位转场隐藏小场景图只能用 `opacity:0`，绝不能 `visibility:hidden`**：Playwright 把后者判为不可见，几十个既有测试都在等 `.game-map[data-scene-ready] visible`，会每次换场景白等一整个转场。覆盖层本身不透明，opacity 足够。
- **覆盖层不吞指针**：整层 `pointer-events:none`，只让「跳过」按钮 `auto`；不进 `inMotion`、不暂停引擎，否则顶栏和既有浏览器测试全被挡。
- **天下层场景不要下钻**：`level==='realm'` 的 20 个 scene（姑苏/扬州/太虚/京郊…）没有更细一级，切到无地名点阵反而更空 → 第二拍留在天下图用 `translate(T-z·P) scale(z)` 推镜 + 到位光环 + 地名浮签。
- **图鉴是长列表 + `loading="lazy"`**：不滚到视口 `naturalWidth` 是 0 → 验证脚本要 `scrollIntoView` 再等 `img.complete`。
- **线上脚本用一次性 profile**：持久化 profile 里存着读过的档，开书会落在回中间 → `rmSync` + `launchPersistentContext`。

### ★ 加载成功 ≠ 画出来了（卡片页上线后返工一次）

卡片页第一版上线，线上截图里**卡面一片空白渐变，没有脸**，
而所有自动断言都绿了——`naturalWidth: 317`，图片明明加载成功。

根因在 CSS 层叠：

```css
/* 册页卡片的通用规则：卡面里的文字要浮在图上面 */
.card-face>*:not(.card-thumb):not(.card-blank){position:relative;z-index:2}
```

这条的特异性是 **(0,3,0)**（两个 `:not()` 各计一个类，再加 `.card-face`），
而 `.preview-face .card-face-portrait` 只有 **(0,2,0)** → **输了** →
`position:absolute` 被覆盖成 `relative` → `relative` + `inset:0` 撑不开盒子 →
holder `height:0` → 图片 `0×0`。
**但 `<img>` 的 `naturalWidth` 仍是 317 —— 图片下载到了，只是没有尺寸可画。**

修法：写成**同等特异性、靠后出现**即可取胜，不动通用规则（它是册页卡片的既有行为）：

```css
.card-face.preview-face>.card-face-portrait{position:absolute;inset:0;…}
```

`.preview-badge` / `.preview-title` / `.card-face-seal` 同样被那条通用规则误伤，一并改。

> **判据**：`naturalWidth>0` 只证明下载到了。验收要**量盒子**
> （`getBoundingClientRect()`）**并且看图**。
> 现在的断言：图片要有可见尺寸且**从卡面顶部开始**；花押要**铺满**卡面。

### ★ 同一个通用规则压了 `position` **和** `z-index`——只解一个不够（返工第二次）

上面那条通用规则 `.card-face>*:not(...){position:relative;z-index:2}`
**两个属性都压**。上一轮只解了 `position`（图画出来了），却漏了 `z-index`：

- 立绘容器被抬到 `z-index:2`，而卡面底部的托底渐变 `.preview-face::after` 只有 `z-index:1`
  → **渐变被立绘盖住**；
- 后果：图正常显示，但**卡名与副题没有深色托底**，直接压在浅色衣服上
  （实测卡面最下缘亮度 **150**，理论应降到 30；花押卡是浅底浅字，等于白字写白纸）。

→ **三处都要压 `z-index:0`**：`.card-face-portrait` / `.card-face-seal` / `.card-face-img`。
（器物图是直接挂在卡面上的 `<img>`，也会被那条通用规则命中。）

### ★ 有些毛病只有像素能看见——读截图，别只读 DOM

上面两个坑 **DOM 全都看不出来**：图片在 DOM 里、`naturalWidth` 非零、
`getBoundingClientRect()` 非零；渐变也在 DOM 里、`::after` 确实存在。
但读者看到的是「空卡」和「看不清的字」。

→ 项目没有 pngjs/sharp，**自写了一个最小 PNG 解码器 `tests/lib/png.mjs`**
（8bit RGB/RGBA、非隔行、5 种 filter）。
→ `tests/card-preview.mjs` 的 `checkNameLegible()` 对**人物 / 物品 / 花押三种卡**各查一遍。

**卡名挪到卡纸之后，判据换了一套**（深墨字压米色卡纸，不再是奶油色字压深墨托底）：

| 判据 | 实测（人物 / 物品 / 花押） |
|---|---|
| 卡名行**墨迹跨度内**的墨迹占比 `> 15%` | 35.0% / 27.8% / 48.3% |
| 卡名行**墨迹跨度内**的纸面均值 `> 150` | 162 / 182 / 153 |

> 怎么取「那一行」：`strong` 是 block，盒子占满整行（272px），字只在中间一小段。
> → 扫一整行 → 取**首末暗像素之间的跨度** → 只在这段里算占比与均值。
> 整行均值会被左右空白稀释，算出来会误判成「没有字」。
>
> ★ 旧判据（「卡面下缘亮度 < 110」「亮笔画占比 > 2%」「峰均差 > 50」）
> 是为「字压在图上」那版结构写的，卡名挪到卡纸后**全部作废**。

> ★ 判据**不能用整行均值**定胜负：均值被画面本身带偏——深色袍子拉低、浅色袍子拉高，
> 两种人都不该被判成「看不清」。要问的是「笔画占比」和「纸面亮度」。

### ★ 转场必须等「这个场景」的图画完才播——而且判据得是 scene-id 粒度

用户反馈：「**现在大地图还没加载出来的时候，就开始播放动画了。然后直接进入场景图。
到时大地图都看不到。**」

根因是**转场与场景加载并行**：转场一出现就把小场景图 `.local-map` 设 `opacity:0`
藏起来，而 Phaser 那张图还在加载 → 底下要么空白要么还是上一张。读者从头到尾
没看清一张大地图，转场一结束场景图直接顶上来。

改成串行：场景图画完 → 才放转场 → 转场结束后露出已经画好的场景图。

**放行判据必须是 scene-id 粒度，不能是布尔。**

```tsx
const [readyScene,setReadyScene]=useState('');   // 「哪个」场景画完了
// onScene 里 setReadyScene(scene.mapData.id)   ← MapScene 没有 id 属性
const stageReady = readyScene === state.sceneId;  // 唯一的放行判据
```

换场景时 `state.sceneId` **先变**、Phaser 图**后画完**。只看布尔 `sceneReady`：
① 转场在旧图还亮着时就放出去；② 旧图刚卸、新图未画时就放出去（底下空白）。
实测第 ② 种：转场在 t=152ms 挂载，舞台 `data-scene-ready` 还是「无」，9ms 后被收掉重放。

> ★ **绝不要在收旧转场时把 `pendingLocator` 一起清掉**——新场景的那份已经挂在那儿了，
> 一起清掉就等于「等图就绪再放」永远等不到东西放（表现为转场只播 274ms 就没了）。

### ★ 两拍不能交叠——交叉淡化等于两张地图压在一起

原来的两拍是**交叉淡化**：天下层与府内层各半透明地叠着。实测那一帧里
「天下舆图」的大区域名（大荒山·青埂峰、姑苏·阊门…）和府内点阵的小地名
（荣府后门、贾母院…）糊成一片——读者既看不清天下、也看不清府内，两拍都没交代到。

→ 中间留一段「什么都没有」的空档：**第一拍完全淡出 → 空档 → 第二拍完全淡入**。

```tsx
const outTo = SWITCH - BLEND;   const inFrom = SWITCH + BLEND;
const realmOpacity  = drill ? 1 - smooth((p - outTo) / BLEND) : 1;
const detailOpacity = drill ? smooth((p - inFrom) / BLEND) : 0;
```

配套：**第二拍要自己的进度 `detailRun`**（从淡入算起，不是从 `SWITCH` 算起）。
`detailToken`（光点）、`detailRun > .72`（到位高亮）、`litCount`（面包屑点亮）三处都要改用它。

### ★ 断言几毫秒的窗口，定时采样抓不住——用 MutationObserver

上面两个坑都只存在于**几毫秒**内：布尔判据下转场抢跑的那一瞬只有 **9ms**。
`setInterval(30ms)` 的定时采样**会漏掉它**（实测照样全绿）→ 断言必须换手段：

```js
const mo = new MutationObserver(muts => {
  for (const n of muts[0].addedNodes) {
    const loc = n.matches?.('[data-testid=scene-locator]') ? n : n.querySelector?.('[data-testid=scene-locator]');
    if (!loc) continue;
    // 此刻读 .game-map 的 data-scene-ready，必须 === loc.dataset.scene
  }
});
mo.observe(document.body, { childList: true, subtree: true });
```

挂在 `document.body` 的 `childList/subtree` 上，在转场元素**被插入 DOM 的同一帧**
读舞台状态，精度到毫秒。

> ★ 通用教训：**「定时采样全绿」不等于「没这个 bug」**。断言的采样频率必须**细于**
> 缺陷的时间窗；否则要换更精确的观测手段（MutationObserver / rAF 逐帧）。
> 本轮两条新断言都做了反向验证：回退两拍交叠 → 12 帧交叠报红；
> 回退布尔判据 → 挂载时舞台无 ready 报红。
> ★ 新断言**必须反向验证过**：回退修复 → 立刻报；恢复 → 绿。

### ★ `dialog` 的 `margin:auto` 只在尺寸固定时才算居中（卡片页返工第三轮）

第一版弹框**贴左上角**，右侧空一大片。根因是 `dialog` 的 UA 默认样式
`position:absolute; left:0; right:0;` —— 一个**撑满全宽**的绝对定位盒。
`width:auto` + `inset:0` + `margin:auto` 看着该居中，实际不行：

```
A: inset+margin:auto          → computed margin: "0px"，盒子 1280×720（=视口）
B: inset+margin:auto!important→ computed margin: "0px"，盒子 1280×720（=视口）
C: width:860px + margin:auto  → computed margin: "260px 210px"，盒子居中 ✓
```

**`auto` 的外边距只有在尺寸确定时才有意义**；`width:auto` 时它退化成 0。
→ `width:min(820px,calc(100vw - 24px)); height:fit-content; inset:0; margin:auto`。

> ★ **断言也要小心**：光断言「中心离视口中心多远」是**抓不住**这个 bug 的——
> 撑满全屏的盒子，中心恰好也在视口中心（实测 offX=0、offY=0）。
> 必须**同时断言盒子尺寸**（不该等于视口）。
> 回退固定宽度后立刻报 `the card must be a card-sized box, but it spans 1440px of 1440`。

### ★ 立绘是窄长全身像，卡面必须竖版 + `contain`（卡片页返工第三轮）

用户反馈「**卡片没有显示全人物的立绘**」。根因：**立绘资产是窄长的一幅**
——多数 600 高、190~350 宽（`yinglian-portrait` 301×600、`yucun-portrait` 317×600）。
横版画框塞不下全身，只能裁：早先按 `faceBox` 裁头肩（看得见脸看不见人），
改成 `object-fit:cover` 铺满又切掉头顶或脚底。

→ 竖版画框（宽高比 5:7）+ `object-fit:contain` → **整幅立绘一像素不裁地放进去**。

> ★ **断言陷阱**：`object-fit:contain` 时 `<img>` 的**元素盒子仍撑满画框**，
> `getBoundingClientRect()` 返回的是盒子、不是绘制尺寸。
> → 不能用盒子宽高比判断是否裁切，要**算 contain 后的实际绘制尺寸**：
> `fitScale = min(imgW/natural.w, imgH/natural.h)`，断言绘制尺寸 ≤ 画框，
> 且高度填满 > 80%（否则人成了中间一枚小邮票）。
>
> ★ 早先按 `faceBox` 裁的 `PortraitCloseup` 组件已删（`PortraitFull`）。

### ★ 立绘资产本身是**半身像**，不是全身像——别当成裁切 bug 查

上面那条「显示全」的准确含义是：**画框里放的是这资产的完整原图，一像素不裁**。
但**资产本身就画不到脚**：

- 81 个立绘宽高比 0.245（`she_yue-portrait` 147×600）~ 0.912（`kongkong-portrait` 547×600），
  全是同一套「头部特写 + 大半身」画法；
- `yinglian-portrait` 画到裙摆、`yucun-portrait` 画到袍摆，**都没有脚**；
- 逐行 alpha 实测：底行 maxAlpha=255 / meanAlpha=213 → **硬切，没有渐隐**
  → 人物是被画布边缘截断的，不是淡出；
- **只有 Q 版（`-chibi`，约 50×116）才是完整全身**，但那是大头身画风，
  放不进写实卡面。

→ 想要真正从头顶到脚底的全身像，只能重画立绘。
→ ★ **断言不能写「画框底部能看到脚」**——那是在断言美术管线的能力，
  不是断言卡片页。卡片页能保证的只有「不裁、不切、整幅缩进去」。

### ★ 卡名不要压在画上

压在画上就要靠一层**很重的墨色渐变**托底，一重就把画闷掉；
挪到画框外的**卡纸上**（深墨字压米色卡纸），字始终清楚，画也干净。
副作用：画框下缘那层墨**不再承担「垫字」的职责**，只留很薄的一层落地影（压太重会把脚底压脏）。

### ★ 长测试跑着跑着别改 `src/`（我犯过）

smoke 走到一半我改了 `src/cardPreview.ts` → vite 整页重载 → 页面恢复到存档、
推进节奏被打乱 → 节点序列错位，`U001 !== U002` 挂掉。
**不是产品缺陷**。改源码前先把长测试停掉。

### ★ 渐变与 border 不重叠（**已作废，见下条**）
`.preview-face::after` 的渐变铺到 padding-box 底，**不覆盖 border** →
分类色用 `border-bottom` 时，最下缘会露出一条亮线（实测末行亮度 30 → 149 硬跳）。
→ 分类色改用 `box-shadow: inset 0 -2px 0 <色>`（inset 在 border-box 内），改后 30 → 26 平滑。

> ⚠️ 卡片页改成竖版卡牌后，**分类色已经挪到卡牌本体上**
> （`.preview-card.cat-money{box-shadow:… inset 0 -3px 0 #b8933c}`），
> 画框 `.preview-face` 自己 `border:0`。
> 这条现在的意思是「分类色不要用 border-bottom，要用 inset 阴影」——仍在成立。

---

## 七、部署

- **验收域名一律 `stone-direct.yan.pub`**（DNS-only 直连，无 Cloudflare 托管挑战），别用 `stone.yan.pub`。
  - 正式域名在 Cloudflare 后面，托管挑战把 `curl` 和有头 Chrome 一视同仁地挡成 403；直连域名是 DNS-only，自带 Let's Encrypt 证书，不过挑战，拿到的是同一批部署字节。
- **部署路径陷阱**：`stone-direct` 与 `stone` 共用 web 根 `/www/wwwroot/stone`，`stone-direct` 用**独立 Let's Encrypt 证书**。
  - **切勿用通用 `yanpub-deploy` 脚本**（建错目录 + 共享证书覆盖，破坏 vhost）。
  - 正确：
    ```bash
    rsync -az --delete dist/ lighthouse:/www/wwwroot/stone.new/
    ssh lighthouse "cd /www/wwwroot && rm -rf stone.prev && mv stone stone.prev && mv stone.new stone && chown -R www:www stone"
    curl -sk -H 'Host: stone-direct.yan.pub' https://127.0.0.1/   # 返 200 才算成功
    ```
  - **SSH 别名是 `lighthouse`**（不是 `root@IP`，直连会 Permission denied），密钥在 `~/.ssh/tencent_lighthouse.pem`。
  - **ssh 非交互会话的工作目录不是 `/www/wwwroot`** → 相对路径的 `mv` 会报 `cannot stat 'stone'`。必须显式 `cd`。
- **改 design JSON 后必须重新 build**（部署的是 dist）。`design/` 不随 dist 部署，线上别 `import('/design/...')`。
- **每轮收尾必须 `git status` 看一眼再提交**——历史上长期未提交导致回退事故。

---

## 八、进度

- **大地图定位转场（全局能力，21 回上线后追加）**：`design/scene-places.json`(45 scene) + `src/scenePlaces.ts` + `src/SceneLocator.tsx` + `App.tsx` 触发链/跳过/设置 + `src/styles.css`；`npm run test:locator` 定向验收；文档 `docs/production/scene-locator.md`。触发＝换场景 + 每回开篇，两拍＝天下图光点飞行 → 府内下钻 / 天下层推镜，可跳过 + 设置可关 + reducedMotion 退化。
- **第 1-23 回全部完成并上线**（23 回于 2026-11-16 部署 `stone-direct.yan.pub`，线上定向回归/定位转场/图鉴标题全通过）。
  - 23=236 节点/14 段/249 证据/3 新角色（金钏儿、彩云、贾芹）/新建 1 图（`qinfang` 沁芳闸桃花图）
  - 22=218 节点/8 段/1 新角色（贾兰）/零新图
  - 21=139 节点/12 段/3 新角色/新建 2 图（`yihong`、`jialian_home`）
  - 20=39 节点/7 段/4 新角色；19=78 节点/8 段/新建 `xiren_home`；18=135 节点/16 段；17=35 节点；16=28 节点/零新图
- 全局规模：1924 节点 / 198 段 / 46 图 / 81 人 / 284 资产 / 1007 证据。
- **背包卡片页已上线**（23 回之后，2026-11-16）：`src/cardPreview.ts`（数据层）+ `src/CardPreview.tsx`（UI）+ `src/styles.css`。账簿里点人/物 → 弹卡牌式大图预览。文档 `docs/production/card-preview.md`；测试 `tests/card-preview.test.ts`（13 项）/`.mjs`（浏览器）/`.mjs`（线上 `npm run test:online:card-preview`）。
- **两张曾缺的大地图已补**（2026-11-18，详见 `docs/production/missing-maps.md`）：大观园全景 `daguanyuan`（第 17 回，35 节点）+ 省亲正殿 `shengqin`（第 18 回 C18-063~070），生成器 `scripts/build_daguanyuan_maps.py`。只改 `scene` 字段、锚点名沿用，零重映射风险。
- 制作记录在 `docs/chapterNN-production.md`，底本在 `docs/chapterNN-source.txt`。
