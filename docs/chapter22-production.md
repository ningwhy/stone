# 第二十二回 制作记录

> 听曲文宝玉悟禅机　制灯谜贾政悲谶语

状态：**已上线**（剧情 218 节点 / 8 段 / 7 张复用地图、贾兰美术全套已补齐；
2026-11-13 部署至 `stone-direct.yan.pub`，线上定向回归与定位转场全部通过）

## 一、底本

`docs/chapter22-source.txt`（21302 字节，40 段，维基文库原文，简体）。

维基文库 `action=raw` 初次请求遭限流（返回 `Wikimedia Error` HTML），
最终通过手工 `curl` 缓存 `/tmp/ch022_raw.txt` 后交由
`scripts/fetch_chapter_source.py` 转换生成。

校验：开头为回目行「第二十二回　听曲文宝玉悟禅机　制灯谜贾政悲谶语」；
尾部为「且听下回分解」；保留 1 处维基繁简标记 `-{云}-`（与 `chapter17-source.txt`
同样 1 处，属既有惯例）。

**这一回有三条互不相干的戏**，各要各的屋：

1. **生日与点戏**：贾琏院商量宝钗生辰 → 贾母院蠲资办酒戏 → 天香楼点戏听曲。
2. **宝玉悟禅**：怡红院湘云更衣摔手 → 黛玉房闭门问答 → 怡红院偈语与烧偈。
3. **灯谜与悲谶**：贾母院元春灯谜 → 荣禧堂贾政逐谜、悲谶成疾。

## 二、分场（实际落地：8 段）

**零新增地图**：本回七张图全是第 16-21 回已经建好的，
这是本项目第一个「不新建任何地图」的新回目。

| 段 id | 标题 | 场景 | 起始节点 |
|---|---|---|---|
| `c22-shengri` | 贾琏院 · 生日怎么料理 | `jialian_home` | C22-001 |
| `c22-yanqing` | 贾母院 · 蠲资办酒戏 | `dinner` | C22-014 |
| `c22-dianxi` | 天香楼 · 点戏听曲 | `c11_tianxiang` | C22-033 |
| `c22-gengyi` | 怡红院 · 更衣与摔手 | `yihong` | C22-061 |
| `c22-bimen` | 黛玉房 · 闭门与问答 | `night` | C22-072 |
| `c22-wuchan` | 怡红院 · 偈语与烧偈 | `yihong` | C22-089 |
| `c22-dengmi` | 贾母院 · 元春灯谜 | `entry` | C22-134 |
| `c22-beichen` | 荣禧堂 · 贾政悲谶 | `central` | C22-150 |

**三处借图必须说明白**（都写进了证据表的 design 条目）：

1. **点戏借天香楼**（`c11_tianxiang`）：底本明写戏台搭在「贾母内院」，
   不是梨香院也不是天香楼。本项目尚无「贾母院戏台」专图，
   第 18 回点戏四出已用天香楼作梨香院代用，本回沿用同一张图，
   把 place 写成「天香楼 · 看楼」并在段标题里点明是看楼，
   **不宣称那就是荣府内院的原样**。
2. **湘云更衣放在怡红院**（`c22-gengyi`）：底本只说「晚间，湘云更衣时」，
   未言何处。依第 21 回「湘云住怡红院」的场景线承接。
3. **黛玉闭门放在贾母院碧纱橱**（`night`）：底本只说「又来寻黛玉」。
   第 21 回已把「黛玉房」统一到 `night` 场景，本回沿用，
   不新开一张图，也不声称这就是大观园里的潇湘馆。

## 三、新出场人物

**本回只有一名新角色**：贾兰（贾政长子，宝玉的堂侄）。

- 前 21 回贾兰只在叙述里被提到（第 4、13、18 回各一次），**从未现身**，
  所以本回是他第一次有戏份，属于新角色，要补立绘与 Q 版。
- 底本里贾兰本人**一句台词也没有**：段 20 是贾政问「怎么不见兰哥？」，
  李氏转述「他说方才老爷并没去叫他，他不肯来」；段 21 是贾母命他在身旁坐了，
  抓果品与他吃。本回照实切，不替他编台词。
- 设计：`art/identity/character-designs.json` 加 `jia_lan`（seed 10234080）；
  生成脚本 `scripts/gen_ch22_characters.py`；
  `scripts/rebuild_new_character_manifest.py` 的 `NEW_CHARACTERS` 加 `jia_lan`。

**太监沿用第 16 回的做法**：复用 `messenger`（传话来人）。他不属于 cast 里
任何一个原著人物，只代表「宫里来的那个传话人」——第 16 回「六宫都太监夏守忠降旨」
也是这么处理的，本回沿用，不新增角色，也不把 messenger 说成是夏守忠。

### 三之二、美术通道：服务器脱网时的替代路径（这一回实战用上了）

贾兰的立绘与 Q 版**没有**走通常的 ComfyUI 管线。写这份记录的时候，
渲染机 `192.168.4.66` 整台脱网了：

```
route -n get 192.168.4.66 → flags: <UP,HOST,REJECT,DONE,…>   # 网络层不可达
arp -a | grep 192.168.4.66 → (incomplete)                    # 主机彻底离线
curl http://192.168.4.66:8188/system_stats → 超时（40 次探测全灭）
```

Tailscale 地址 `100.105.115.68:8188` 同样不通；扫了网段内 60-80 也没有
第二台 ComfyUI。所以**不是端口或防火墙问题，是主机没了**。

替代路径（本回实际走通）：

1. **出图**：用会话内置的图像生成能力，按 `character-designs.json` 的
   `prompt` 出**白底全身像**（portrait 768×1152 / chibi 768×1024）。
   画风必须对齐既有素材——柔和水墨线条、淡彩、全身、手交、鞋履可见；
   竖构图比方构图更接近既有立绘。生成后与既有角色并排比对过画风。
2. **抠图**：`scripts/cutout_white_backdrop.py`——纯白底不需要 SAM，
   从四边泛洪去掉背景 + 按饱和度去纯白 + 羽化边缘。抠完逐张目视核对
   （棋盘格底），确认没有啃掉衣服边缘、头发或鞋。
3. **校准**：`scripts/calibrate_jia_lan.py`（新写）——测脚底锚点（alpha≥110）、
   按 **height** 缩放（portrait 600 / chibi 116）、chibi 另带 `bodyCompress`
   （split = 0.42×脚底行，factor 0.64，与既有 38 个压缩 Q 版的中位数一致）。
4. **生成 PNG**：`scripts/build_art_assets.py`。**跑完必须
   `git diff public/assets/rongguo/manifest.json`**——它按校准表重写整个
   manifest，会把 `hash` 字段清空（那是 `npm run art:webp` 盖的章，
   跑一次 WebP 就会补回来）。本回实测：身份块零丢失，
   `maps/rongguo-entry.tmj` 未被误改。
5. **脸框**：`scripts/detect_face_box_one.py`（新写）——既有
   `inspect_face_boxes.py` 从 manifest 读资产列表，贾兰还没注册时**是鸡生蛋**，
   所以另写一份对单张图跑同一套算法（同样的肤色掩码、同样只在**上部 30%**
   做连通块分析——这条规则正是为了躲开「米白围裙被当成肤色」的坑）。
   **自动检测只是提案**：立绘的框切进头发又过到衣领，Q 版的框过到下巴以下，
   两张都靠目视重标（[152,45,250,158] 与 [24,16,83,60]）。
   既有 chibi 的框下沿统一在 59~60（下巴线），贾兰按同一口径。
6. **注册**：`scripts/rebuild_new_character_manifest.py`（只重写自己的块，
   不重排整个文件）。
7. **朝向**：`scripts/facing_wide_scan.py` 先 `--calibrate` 跑标尺
   （11 个样本 10 个有效读数，方向与已知答案一致），再扫贾兰：
   portrait 3/3 全 right，chibi 2/2 全 right（tight 那次标 `(swapped)`，
   符号取反后与 wide 一致）。目视复核：左耳可见、鼻与嘴都在两眼中点右侧 → 朝右。
   写进 `art/identity/facing-assets.json`，再跑 `scripts/build_facing.py`
   + `scripts/build_facing_doc.py`（**两个都要跑**，否则 `check:content` 报过期）。

> **教训**：渲染机脱网不等于「这回出不了图」。先分清是**端口不通**
> （服务没起）还是**主机不通**（路由 REJECT / ARP incomplete）——
> 后者要另找出图通道。本地已有的 `cutout_white_backdrop.py` 说明
> **纯白底的图根本不需要 SAM**，「必须有渲染机」的印象是管线自己造成的。

## 四、剧情生成

`scripts/build_chapter22.py` → `design/chapter22-{story,sections,evidence}.json`

### 句号索引切片（本回沿用第 20 回的方法论）

正文与 `source.paragraphLead` **都从底本切出**，写盘前自校，失败即退出不落盘。
底本同形短句多（「是」「我知道了」），字符串 `find` 会命中前一处切到别人的字，
所以一律用 `(段号, 句号)` 唯一定位。

**硬门槛**：`(段号, 句号)` 全局严格递增。同一句号区间拆成「叙述 + 台词」
两个节点时共享 `(段, 句)`，用节点在 CUTS 里的次序打破平局；
只在**严格倒退**时报错，相等不算矛盾。

### 舞台连续性自检

引擎只在**换场景**时清空舞台（`engine.ts` 的 `enter()`），同场景可见性保持 →
「move 一个从没 show 过的人」会在读者点到那一步才抛
`[节点] 移动角色未显示：xxx`。**生成期必须拦住**，只查 `move`
（`effect`/`hide` 对不在台上的角色是空操作）。

### 锚点必须可通行

「名字存在」≠「可通行」。`walkable` 只来自 zone id 匹配 `^(A\d*|B|C|D|E|F)$`
的地板与 Routes 走廊。生成器直接调项目自己的 `parseTiledMap` 算 walkable，
判定与运行期一致。

> 本回踩到的坑：`entry` 与 `central` 两张图的锚点名与 `dinner` 完全不同。
> 初稿照抄 `dinner` 的 `grandmother_place`/`back_door`/`tea_place`，
> 被锚点校验拦下 32 条错误后才改成 `entry` 的 `grandmother_seat`/`hall_door`/
> `wang_seat` 与 `central` 的 `rongxi_door`/`east_court`。
> **校验器拦住的就是真实缺陷，不要绕过它。**

## 五、注册

- `src/story.ts`：import script22/sections22 → 拼 `story` → 拼 `chapters`
  并 `.map(s=>({...s,book:22}))` → `bookNames` 加 `"22":"第二十二回"`；
  `cast` 加 `jia_lan`（79 人）。
- `design/chapter-titles.json` 加回目联：
  `{"first":"听曲文宝玉悟禅机","second":"制灯谜贾政悲谶语"}`。
  ★ **这一条不做，第 21 回的封底会立刻显示错**——见第六节。
- `scripts/check_content.mjs` 的 `VERBATIM_BASE` 加 22。

## 六、这一回带出的两处真缺陷（**下一回照做**）

### 1. 漏登记第 N 回的回目联，会让**上一回**的封底说错话

第 22 回上线后跑第 21 回的定向测试，报：

```
the back cover of book 21 must offer the next book, got:
本回目完 | 第二十一回 | 已读完 | 全书至此，砖石犹温。 | 收起封底，回看本回
```

根因不在第 21 回，也不在封底逻辑，而在
`src/Leaves.tsx` 的 `ChapterBackCover`：

```tsx
const nextTitle = nextBook != null ? chapterTitle(nextBook) : null;
...
{nextBook != null && nextTitle
  ? <div className="leaf-next">…「开启下一回」…</div>
  : <p className="leaf-next-title leaf-final">全书至此，砖石犹温。</p>}
```

`nextBook` 算对了（=22），但 `chapterTitle(22)` 因为
`design/chapter-titles.json` 里没有第 22 回的回目联而返回 `null`，
于是走进 else 分支显示「全书至此」。

**这就是「加回目的五步」里第 4 步（登记回目联）为什么不能省**：
它影响的是**上一回**的封底文案，而上一回有自己的测试守着——
所以这个错一定会被测出来，但会在一个看起来不相干的测试里报错。

**排查手法**：先在 Node 里实读 `chapterLeaves()` 与 `bookNames`，
确认「下一回是哪一回」算对了；再看封底组件读的是什么。
数据层对、组件层错，就是「某个 lookup 返回了 null」。
本回最终用 `chapter-titles.json` 补登记解决。

### 2. 顶栏「回到封底」被「再走一回」顶掉（只在**末回**暴露）

第 22 回是全书末回，封底折叠后，测试断言「回到封底」按钮必须出现，却没出现：

```
after folding the back cover of book 22 the reader must be offered a way back to it
(node=终幕, leaf=0, forward=false)
```

根因在 `src/App.tsx` 顶栏按钮的**三态判断顺序**：

```tsx
{ended ? <button>再走一回</button>
: inMotion ? <button>跳过移动</button>
: leaf==='back' ? <span>本回目完 · 请在封底开启下一回</span>
: foldedBack ? <button>回到封底</button>
: <button>继续剧情</button>}
```

`ended`（`state.status==='ended'`，只在**全书末节点**为真）排在 `foldedBack` 前面。
第 21 回不是末回，所以这条分支永远走不到——**缺陷只在末回暴露**，
第 21 回上线时它是隐形的。

> **教训**：凡是「按**全书**状态」判定的分支，都要问一句
> 「它在**非末回**时走不到吗」。走不到的分支就是藏着的缺陷，
> 而它会在某一回变成末回的那天突然冒出来。

### 2之二、同一条分支上的第二个缺陷：把顶栏锁死成死路

修好上面的顺序问题之后，`browser-smoke` 反而红了：

```
waiting for getByRole('button', { name: '继续剧情', exact: true })
    Timeout 30000ms exceeded.
```

排查下来是**上一轮那条断言本身的设计有问题**。它断言「收起封底后
『继续剧情』必须消失」，理由是「读者再点一下就会跨进下一回，还跳过了
下一回的封面」。

**那条理由经实测不成立。** 下一回的封面是到达那一回**首个节点**时自己
翻出来的（`src/leaves.ts` 的 `leafTrigger`：`nodeId === leaf.firstNode`
时返回 `'cover'`），与封底收没收起毫无关系。浏览器实测（收起封底 →
推进）：节点走到 `C2-001`，**封面照样翻出来**，标题是
「贾夫人仙逝扬州城冷子兴演说荣国府」。

而那个「锁死」的设计反倒制造了真缺陷：顶栏被固定成「回到封底」，
读者收起封底之后**再也推不动了**——点「回到封底」把纸页翻回来，
再收起，又是「回到封底」。回末节点上除了封底自己的「开启下一回」，
没有一条前进的路（实测复现）。

**修法**：`foldedBack` 只在**全书末节点**接管按钮。

```tsx
{foldedBack && ended ? <button>回到封底</button>
: inMotion ? <button>跳过移动</button>
: leaf==='back' ? (ended ? <button>再走一回</button> : <span>本回目完 …</span>)
: ended ? <button>再走一回</button>
: <button>继续剧情</button>}
```

- **末回**：没有下一回可进，「继续剧情」按下去只会重走已读完的戏，
  不如把封底重新翻出来（「回到封底」）。「再走一回」仍然保留在封底展开时，
  所以它没有变成不可达的动作：回到封底 → 封底翻回 → 顶栏又是「再走一回」。
- **非末回**：收起封底后照旧可以推进，下一回的封面由 `leafTrigger` 照常翻出。

共享断言 `tests/lib/backcover.mjs` 的 `assertFoldedBackIsNotAPassThrough`
也随之改写，从「『继续剧情』必须消失」改成守两条真正的不变量：
①收起封底不前进节点；②收起封底之后读者**仍能前进**，且下一回的封面照常翻出。
第 22 回是末回，走的是「回到封底」分支。

> **教训**：修一条断言之前，先问「这条断言的理由**实测**成立吗」。
> 断言挡住的也许是另一个缺陷，而不是它自己声称的那个。
> 这里的代价是：一个为了防「跳过封面」而写的断言，把顶栏锁成了死路，
> 而且它连带把 `browser-smoke` 也弄红了——真缺陷藏在一个假理由后面。

## 七、验收

- `npm run check:content`：全部通过（0 ERROR）。
- `npm run check:anchors`：**通过**（342 个路线锚点全部可通行且两两连通，
  36 个装饰锚点按设计不可站人）。这个门禁是本轮新加的，见第六节之五。
- `npx tsc --noEmit`：通过。
- `npm run test:locator`：通过（45 scenes mapped）。
- `node --experimental-strip-types tests/chapter22.mjs`：
  `Passed: chapter 22 — 8 sections walked, 218 nodes, 7 stages, TOC search, back cover correct, all node text verbatim.`
- `node --experimental-strip-types tests/character-identities.mjs`：
  `Passed: 78 versioned portraits, 全部 78 张带 faceBox 并已裁成脸部特写…`
- `npm test`：84/84 全过（含新增的 `tests/cnnumber.test.ts`）。
- `npm run test:browser`：`Passed: all 354 nodes, 45 maps, …corrupt-save recovery.`
- 第 18-22 回回归：**全部通过**（第 20 回那一轮先红过一次，是测试自身的缺陷，
  排查过程见第六节之三）。

### 六之三、第 20 回回归红过一次：顶栏按钮的「身份漂移」（不是产品缺陷）

第 20 回的「段内连贯」断言报
`c20-qiaoyu walked into an unexpected stage yihong`。
`yihong` 是**第 21 回**才建的新图，第 20 回的数据里根本没有它——
所以读者是**跨过了第 20 回的末节点**走进了第 21 回。

**产品行为是对的**（第 20 回末节点 `C20-039` 确实翻出了封底），
错的是**测试点到了另一个按钮**：

顶栏那**一个**按钮在「跳过移动」和「继续剧情」之间来回换身份，且**占同一位置**。
测试的写法是：

```js
const skip=page.getByRole('button',{name:'跳过移动',exact:true});
if(await skip.isVisible().catch(()=>false)){await skip.click({timeout:1500}).catch(()=>{});…}
```

`isVisible()` 判到「跳过移动」，可等 `click()` 真正落手时 React 早已把那个按钮
换成了「继续剧情」。Playwright 的 `click()` 会**重新解析 locator**，于是那一下
落在「继续剧情」上——剧情就多走了一步。统一时钟下的现场：

```
19.212 MARK step1:skipVisible#0     ← 判的是「跳过移动」
19.255 ★    click "继续剧情"          ← 点的其实是「继续剧情」
19.257 ★    advance 1324->1325
19.389 MARK step1:skipVisible#1     ← 又判一次「跳过移动」
19.421 ★    click "跳过移动"          ← 这次才真的点到
```

**一步多走不是「多读一句」**：它会跨过本回末节点，末节点的封底还没翻出来
就被跨过去，下一回的封面也来不及翻。

**修法**：`tests/lib/pickup.mjs` 新增两个共享 helper——

```js
clickSkipIfShown(page, limit, settle)    // 按当下真实文案取「跳过移动」
clickForwardIfShown(page)                 // 按当下真实文案取「继续剧情」
```

两者都用 `document.querySelectorAll('nav button')` 比对 `textContent` 取元素，
再用 `dispatchEvent('click')` 派发：元素一旦取到就是那个元素，React 中途把它
换掉也换不掉这一下**已经派发出去**的 click。全部浏览器测试统一改用它们。

**排查方法（值得照做）**：别猜，写探针逐步收窄。本次连写七支：
打节点/场景 → 插桩 `engine.advance` 看索引 → 查 DOM 与 `engine.step` 是否撕裂
→ 最后用 `page.exposeFunction` 把点击实时送回 Node 侧**统一时钟**对齐事件流。
前六支都证伪了当时的假设（**引擎没跳节点、DOM 也没撕裂**），第七支才抓到真凶。

> 探针里的 `performance.now()` 跨 `page.evaluate` **不可比**（各自的 time origin），
> 要用 Node 侧 `Date.now()` 打点。

### 六之四、上线（2026-11-13）

部署走 `AGENTS.md` 里的路径（**不要用通用 `yanpub-deploy` 脚本**）：

```bash
rsync -az --delete dist/ lighthouse:/www/wwwroot/stone.new/
ssh lighthouse "rm -rf /www/wwwroot/stone.prev && \
  mv /www/wwwroot/stone /www/wwwroot/stone.prev && \
  mv /www/wwwroot/stone.new /www/wwwroot/stone && \
  chown -R www:www /www/wwwroot/stone"
# 回环判定
ssh lighthouse "curl -sk -o /dev/null -w '%{http_code}' -H 'Host: stone-direct.yan.pub' https://127.0.0.1/"
```

`lighthouse` 是 `~/.ssh/config` 里的别名（`154.8.237.35` + `tencent_lighthouse.pem`）。
**vhost 与独立证书不动，不需要 nginx reload。**

**线上复验**（验收域名一律用 `stone-direct.yan.pub`）：

| 项 | 结果 |
| --- | --- |
| 首页 | HTTP 200，产物 `index-CWJL65eW.js` 与本地构建一致 |
| 图鉴标题 | 「前二十二回 · 人物图鉴」，78 人含贾兰，立绘 385×600 已绘出 |
| 第 22 回定向回归 | `Passed: chapter 22 — 8 sections walked, 218 nodes, 7 stages, TOC search, back cover correct, all node text verbatim.` |
| 定位转场 | `Passed: scene locator — 45 scenes mapped, chapter + scene triggers, realm push-in vs estate drill-down, skip/auto-dismiss/settings, no swallowed clicks, animated frames verified.` |
| 完整冒烟 | `Passed: all 354 nodes, 45 maps, complete history, chapter 1–4 selection, cross-scene save/reload, offscreen reveal, natural movement, pause, settings, atlas, stable map area, minimum readable sprites/labels, zoom hit targets, overview browsing, paused estate travel, controls visible at 1440×900 / 1280×720 / 390×844, corrupt-save recovery.` |
| 卡片图鉴 | `Passed: https://stone-direct.yan.pub serves the 36-card album with four token cards and four bond cards.`（信物来路：贾母→宝玉（赏给）、贾母→黛玉（赏给）、封肃→贾雨村（买卖）、甄士隐→薛蟠（被夺）） |
| 第 18–21 回定向回归 | `online-chapter18/19/20/21` 全部 `Passed (direct)` |
| 其余线上脚本 | `online-verify`、`online-ledger`（54 行 / 20 解锁 / 8 张图全加载）、`online-leaves`、`online-batch5` 全过 |

**新增验收脚本**：`tests/verify-album-title.mjs`——在 **preview（dist 产物）**上验面板标题
与贾兰立绘，部署前后各跑一次。**注意图鉴是长列表 + `loading="lazy"`**：
不滚到视口里图片压根不加载，`naturalWidth` 是 0——那是懒加载，不是图没画出来。

**线上脚本的两个坑（这次踩到了）**：

1. **`design/` 不随 `dist` 部署**——线上绝不能在浏览器上下文里
   `import('/design/xxx.json')`，必然 `Failed to fetch dynamically imported module`。
   设计数据一律在 Node 侧 `readFileSync` 读。
2. **`page.reload()` 之后封面会重新盖上来**——那张纸是模态的，会把「设置」按钮
   挡在底下（`intercepts pointer events`）。循环里每次 reload 后都要补收一次封面
   （`dismissLeaf(page,false,true)`），不能只在循环外收一次。

### 六之五、一个定时炸弹：路线走廊被道具切断了（**下一回务必跑 `check:anchors`**）

这一回上线后做入库整理时，顺手把 `probe21.mjs`（锚点可通行性检查）归位到
`scripts/`，结果它报出一件**从来没被任何测试发现过**的事：

```
DISCONNECTED to_outer: yard -> outer_room
DISCONNECTED to_outer: yard -> mirror_place
DISCONNECTED to_outer: yard -> zijun_place
DISCONNECTED to_outer: yard -> cui_lv_place
DISCONNECTED to_outer: yard -> baochai_place
DISCONNECTED to_outer: yard -> baoyu_outer
```

**`yihong`（第 21 回新建的怡红院）的 `to_outer` 路线是断的。**

### 为什么之前全是绿的

- 第 21、22 回的剧情**根本没走这条路线**：怡红院的戏走的是
  `to_inner`（`baoyu_outer → curtain → inner_room → …`），那条路是通的。
- 浏览器回归只覆盖**剧情实际走过的路径**，没覆盖**路线表里声明的路径**。

所以它是一颗**定时炸弹**：哪天有人写一段剧情让人从院子走到外厅，
引擎就会抛 `没有可行走路线：21,26 → 18,25`，读者点到那一步就走不动。

### 根因

引擎的路线走廊生成（`src/model.ts` 的 `parseTiledMap`）：

```js
for (const route of Object.values(map.routes)) {
  for (let i = 1; i < route.length; i++) {
    const from = anchors[route[i-1]], to = anchors[route[i]];
    let c = from.col, r = from.row;
    map.walkable.add(cellKey(c, r));
    while (c !== to.col) { c += Math.sign(to.col - c); map.walkable.add(cellKey(c, r)); }
    while (r !== to.row) { r += Math.sign(to.row - r); map.walkable.add(cellKey(c, r)); }
  }
}
// ↓ 在这之后才删 blocker
for (const b of map.blockers) … map.walkable.delete(cellKey(c, r));
```

三个要点叠在一起：

1. 走廊是 **L 形**：先沿**行**走到底，再沿**列**走到底（`to.col` 先收敛）。
2. 走廊生成**在 blocker 删除之前**，删 blocker 会把刚画好的走廊切断。
3. `yard` 在 (21,26)，`outer_room` 在 (18,25)。L 形走廊第一步必然是
   `(20,26)`——而那正是 **`tea-table` 的 ArtFootprints**。

于是从 `yard` 出发的任何横向走廊都被茶几一刀两断。

> 顺带记一个坐标坑：Tiled 网格是 **128×64 的菱形**，`unit = tileheight = 64`，
> 不是 `tilewidth`。锚点换算是 `col = x/64 - 0.5`（`row` 同），
> footprint 是 `col = x/64`（不带 -0.5）。用 `tilewidth` 换算会全错。

### 修法

**把茶几挪走**（不是改路线表）——改路线表会让「院中茶席」这个陈设失去意义，
而挪家具是零成本的：茶几从 (20,26) 挪到 (21,25)，紧邻 `yard` 一格，
正是院中待客处，且 (21,25) 不在任何路线的走廊上。圆凳同步位移。

挪完后 `yihong` 的 **16 段路线全部可达**（用引擎自己的 `findPath` 逐段验过）。

### 为什么不能只改这一张图

因为**同类问题会在每一张新地图上重演**。所以把它做成了门禁：

```bash
npm run check:anchors
# all route anchors walkable and connected — 342 route anchors, 36 decorative anchors
```

`scripts/check_anchors_walkable.mjs` 做三件事：

1. **区分两类锚点**——
   - **路线锚点**（出现在某条 route 的 `anchor_ids` 里）：必须可通行，且同 route
     内两两连通。**硬门禁**。
   - **装饰锚点**（不在任何 route 里）：挂画、戏台、桌案一类，设计上就不可站人
     （`c11_tianxiang:stage`、`c5_ningfu:portrait_wall`、`c10_jinhome:kang/table`、
     `c6_village:table`、`c12_sickbed:window`），**不算问题**。
2. **连通性直接用引擎的 `findPath` 判定**，别自己重写一套 BFS——
   引擎的走廊是 L 形且要扣 blocker，自己写的 BFS 与引擎实际可达性可能不一致。
3. **退出码非 0**，可以直接挂进 CI 或验收链。

> **下一回照做**：新建地图后**必须**跑 `npm run check:anchors`。
> 它能抓到浏览器回归抓不到的那类问题——**剧情没走到的断路**。

## 八、留给下一位

1. **第 23 回加进来时，别忘了 `design/chapter-titles.json`**——
   漏了会让第 22 回的封底误显「全书至此」，见第六节。
2. **新建地图后必须跑 `npm run check:anchors`**——
   浏览器回归只覆盖剧情**实际走过**的路径，覆盖不到路线表里**声明了但没走**的断路。
   `yihong` 的 `to_outer` 就是这么藏了整整两回，详见第六节之五。
3. **「查无此人」的样本已换成「彩云」**（`tests/browser-smoke.mjs`）。
   判据要覆盖**所有可搜路径**：正文、标题、地点、在场人物、段 id。
   只查正文不够——名字出现在地点或人物表里照样能命中。
4. **美术服务器离线时的替代通道**（这一回实战用上了，值得记住）：
   - `192.168.4.66` 整台机器脱网了（ARP `incomplete`、路由 `REJECT`），
     不是端口或防火墙问题；Tailscale 地址同样不通；网段内也没有备用主机。
   - 替代路径：内置的图像生成能力出**白底全身像** → `scripts/cutout_white_backdrop.py`
     抠图（纯白底的道具/人物不需要 SAM）→ 本项目的校准 → manifest。
   - 画风要与既有素材对齐：柔和水墨线条、淡彩、全身、手交、鞋履可见；
     竖构图比方构图更贴近既有立绘。
   - 详见第五节之二。
5. **提交前先 `git status`**：这一轮整理时发现**第 16–22 回的工作全部没提交**
   （本地 HEAD 还停在第 20 回，远端更停在第 19 回之前）。
   `AGENTS.md` 里写的「本仓库的工作树长期处于大量未提交状态」是**历史遗留的描述**，
   别当成可以一直不提交的许可证——那意味着几轮回目的成果随时可能丢。
   一次推上去：217 个文件、42367 行。
