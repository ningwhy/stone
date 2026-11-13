# 大地图定位转场（换场景 / 回目开篇）

小场景图只画一间屋、一处院：读者能看见宝玉站在碧纱橱里，却看不出碧纱橱在荣国府
哪一角，更看不出这一回是在姑苏还是京城。这个转场专治这件事——**每回开篇、每次换
场景**，先在地图区域铺一张大舆图，把「这段戏在哪儿」交代清楚，再让位回小场景图。

## 权威数据与边界

| 文件 | 职责 |
| --- | --- |
| `design/scene-places.json` | 唯一权威的叙事方位表：45 个 scene → 层级 / 区域 / 等距格坐标 / 地名 / 备注 |
| `src/scenePlaces.ts` | 等距投影、区域点、层内点、面包屑、点阵、贝塞尔、缓动 |
| `src/SceneLocator.tsx` | 两拍 SVG 动画与顶部信息卡 |
| `src/App.tsx` | 触发链、封面挂起、计时、跳过、设置开关 |
| `src/styles.css` | `.scene-locator*` 一族 |
| `scripts/check_content.mjs` | 静态门禁：剧情用到的 scene 必须全部有坐标，且表里不能有孤儿 |
| `tests/scene-locator.mjs` | 定向验收（静态数据 + 触发 + 两拍 + 跳过/设置 + 逐帧动画） |

**刻意不复用 `design/atlas-maps.json` / `WorldMap`**：那是读者主动打开的可交互总览，
只画了 28 个考据过的建筑，剧情 45 个 scene 里有 18 个（怡红院、贾琏院、袭人家…）
在它上面查无此地。定位动画覆盖的是**全部**回目，包括跳读、读档、回看造成的跳变，
所以另立一张叙事方位示意表；它是示意，不是考据地图，不要拿它反推原著地理。

五个层级：`realm`（天下舆图）、`capital`（京城总览）、`rongguo`（荣国府）、
`ningguo`（宁国府）、`daguanyuan`（大观园）。其中 20 个 scene 本身就在 `realm` 层。

## 触发链（`App.tsx`）

判据是 **`scene` 变了 / `chapter` 变了**，不是 `index` 差多少，也不是「自然 +1 步」：
跳读、读档、回看造成的场景跳变也要交代方位。这与第 3–6 回的 `travel`（荣国府内沿路
走的演出）是两件事，互不复用。

- `locatorPrev` 初值 `{scene:'',chapter:0,enabled:false}`：开卷第一帧没有「从上一处
  变过来」，但那正是一次回目开篇。哨兵初值保证第一回也能看到第一次定位。
- 回目开篇时封面（`z-index 58`）正盖在舞台上，转场先放进 `pendingLocator`，等
  `leaf===null` 再播，否则会被暗色毛玻璃压住白播一次。
- 设置里重新打开开关时 `justEnabled` 立刻补一次，让开关效果当场看得见。
- 计时：`progress` 每 50ms 推进 `0.032 × speed`，到 1 后再停 420ms 自动收起；
  `reducedMotion` 下步长 0.12、终点停 900ms，组件内部直接渲染静态终点。
  封面/封底期间与 `state.paused` 期间冻结，免得读者还没翻页图就自己淡出。

## 两拍

`progress 0 → .44` 天下舆图：光点从上一处所在区域飞到新区域，面包屑只亮第一级。

`progress .44 → 1` 分两种：

- **府内层**（`capital` / `rongguo` / `ningguo` / `daguanyuan`）：天下图淡出、目标层
  淡入，光点从层入口飞到目标院落，面包屑逐级点亮，目标点加定位环与到位高亮。
- **天下层本身**（姑苏、扬州、太虚、京郊…共 20 个 scene）：这些地方没有更细的一级
  可钻，硬切到一张没有地名的空点阵图反而更空（实测过）。改为**留在天下图上推镜**：
  `translate(T - z·P) scale(z)` 把目标区域 P 映射向画面中心 T，`z` 从 1 放大到 1.2；
  同时补到位光环与地名浮签，面包屑追加区域名，第二拍仍有「逐级点亮」的进展。

点阵图必须带地名。一层里十几个点全标会糊成一团，所以 `detailLabels` 用
**目标优先 + 贪心避让**：取地名末段作短名（≤9 字）→ 目标排第一 → 按距目标由近及远
依次放置 → 与已放置标签会重叠的直接省略。目标标签加粗放大，保证「就是这里」不含糊。

## 交互纪律（都是踩过的坑）

- **不吞指针**：覆盖层 `pointer-events:none`，只有「跳过」按钮 `auto`。读者随时能点
  顶栏「继续剧情」，`tests/scene-locator.mjs` 用 `elementFromPoint` 断言按钮中心仍是
  按钮本身。
- **不进 `inMotion`、不暂停引擎**：转场只是给地图区域换一层画面，不是一次演出。
  顶栏按钮、对白面板、存档状态机都不该因它改变；只有自动播放定时器在转场期间
  让一拍（`!!locator`），免得读者还没看清地名剧情就走了。
- **空格先收转场**：Space 已是翻页键，转场盖在地图上时应先把它收掉，不同时翻页。
- **小场景图只用 `opacity:0` 隐藏，不能用 `visibility:hidden`**：Playwright 把
  `visibility:hidden` 判为不可见，几十个既有测试都在等 `.game-map[data-scene-ready]`
  visible，改 `visibility` 会让它们每次换场景白等一整个转场。上面那层不透明背景
  已经完整盖住小图。
- **信息卡放顶部居中**：左上角是「当前场景 / 本回行迹」切换、右上角是缩放工具条、
  下方两侧是立绘；放底部被立绘压住，放左右被工具条挡住（都在实测截图里出现过）。
- **覆盖层不吃全屏**：`inset:0 0 226px`，给对白面板留原位；封面/封底仍压在最上。

## 验收

```sh
npm run test:locator          # 静态数据 + 触发 + 两拍 + 跳过/设置 + 逐帧动画
npm run check:content         # scene-places 门禁
npm test                     # 78 项单测
npm run test:browser          # 354 节点全量冒烟
npm run build
```

定向测试用 `data-testid=scene-locator` 与 `data-scene / data-reason / data-level /
data-drill / data-progress / data-zoom` 读状态；两个 `<g>` 分别带
`data-layer=realm|detail`。普通动效下用 `requestAnimationFrame` 采集整段动画的帧，
断言天下层场景 `detailOpacity` 全程为 0、`realmOpacity` 全程为 1、推镜缩放单调不减。
`reducedMotion:'reduce'` 下断言静态终点，避免时间竞态。

线上复验：`TEST_URL=https://stone-direct.yan.pub npm run test:locator`。

## 新增回目照做

1. 新 scene 必须在 `design/scene-places.json` 补 `level / region / col / row / name`；
   `npm run check:content` 会在构建前拦住漏配，也会拦住表里没人用的孤儿条目。
2. 别把新 scene 塞进 `atlas-maps.json` 了事——那张总览表覆盖不了全部剧情场景。
3. 新增区域（`regions`）要检查等距投影后色块不重叠：早期 `suburb` 与 `jingdong`
   曾撞在一起，改坐标后才干净。
4. 回目开篇、跨回换场景各目检一次；`artifacts/locator/` 下留四张参考截图：
   `01-chapter-start.png`、`02-drill-down.png`（天下层推镜）、
   `03-drill-estate.png`（府内下钻带地名）。
