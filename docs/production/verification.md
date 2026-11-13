# 验收、故障定位与交接

## 常用命令

在项目根目录执行。无需为文档修改生成图片、重建地图或启动 GPU。

```sh
npm run check:content
npm test
npm run build
```

`check:content` 是静态内容检查：已接入回目、段落、地图、原文起句、演员与资产引用；不启动浏览器或 GPU。它扫描已注册的 chapter JSON，不把未接入的草稿当成已发布内容。`npm test` 包含引擎动作、全节点自然移动与 skip 一致性、段落 seek、暂停、存档、美术与地理检查。

已有开发服务后：

```sh
npm run test:browser
node tests/asset-scenes.mjs
node tests/character-identities.mjs
node tests/interior-roof.mjs      # 外观随室内占位隐藏/恢复、按栋隔离、roof 覆盖
node tests/actor-facing.mjs       # 全剧情行走帧与对话框立绘的镜像方向（含表情变体）
npm run test:locator              # 大地图定位转场：45 场景方位表、触发链、两拍动画、跳过/设置
```

`test:locator` 见 [大地图定位转场](scene-locator.md)：既查 `design/scene-places.json`
的静态覆盖，也在浏览器里验回目开篇 / 换场景两种触发、天下层推镜与府内层下钻、
跳过与自动收起、设置开关、指针透传，以及普通动效下的逐帧单调推进。支持 `TEST_URL`，
线上可跑 `TEST_URL=https://stone-direct.yan.pub npm run test:locator`。

人物位图新增或重画后，朝向表按下面两步重建，再跑 `actor-facing`：

```sh
python3 scripts/facing_assets.py       # 按资产键多裁切投票测量，写 art/identity/facing-assets.json
python3 scripts/build_facing.py        # 合并目视裁决，写 design/character-facing.json
python3 scripts/facing_review_sheet.py # 导出目检表 art/identity/facing-review-sheet.png
```

`check:content` 会检查两件事：磁盘上每个 PNG 都已在 manifest 内登记（否则运行时查不到），以及每张人物位图都有朝向记录（否则镜像由偶然决定）。

`interior-roof.mjs` 与 `actor-facing.mjs` 默认连本地 5173，支持 `TEST_URL` / `CHROME_PATH`。地图侧辅助脚本（都不起浏览器）：`python3 scripts/story_path_cells.py <mapId>` 在新增陈设前确认没有挡住 move 路线；`python3 scripts/render_map_preview.py <mapId> "<外观名,...>"` 近似渲染室内外布局用于目检；`python3 scripts/annotate_interiors.py` / `scripts/furnish_interiors.py` 幂等写回 Tiled 自定义属性与室内陈设。

主浏览器测试支持 `TEST_URL` 和 `CHROME_PATH`；聚焦脚本当前写死本地 5173 与 macOS Chrome，换机器先调整，不能声称环境变量对所有脚本都有效。新回接入时，主测试当前手工拼接 1–3 的 story，需要扩展；地图/人物数量与场景截图断言也要按新范围调整，保留前三回回归。

美术面部修改后，使用带 Pillow/numpy 的 Python：

```sh
python3 scripts/verify_character_identities.py
```

它验证 33 人/66 图的配对清单、遮罩外 RGBA 不变、运行图与入选图相同、尺寸及旧脚底锚点不变。新增人物后同步身份计划和覆盖基线。原图比较是定位与合成保障，不代替人工判断像不像同一角色、是否还同脸。

## 验证矩阵

| 改动 | 必要检查 |
| --- | --- |
| 纯文档 | 相对链接、文件存在、示例对照实际 API、当前统计、覆盖风险说明 |
| 新对白/剧情 | 内容检查、全节点引擎、段落 seek、回目顺序、信息时间层、长对白目检 |
| 地图/碰撞/锚点 | 内容检查、实际 A*、门洞及墙穿越、Tiled↔屏幕往返、自然走路和 skip 一致 |
| 室内外/朝向 | 内容检查、`node tests/interior-roof.mjs`（外观随室内占位隐藏/恢复、按栋隔离）、`node tests/actor-facing.mjs`（行走帧与立绘镜像一致，含表情变体按自身朝向裁决；静止与到达帧的朝向由引擎按站位写入，seek 重放与顺序播放结果一致）、`story_path_cells.py`（新陈设不挡路）、全节点引擎与浏览器回归 |
| 新增/重画人物位图 | `python3 scripts/facing_assets.py`（按资产键多裁切投票测量）→ `python3 scripts/build_facing.py`（合并目视裁决，生成 `design/character-facing.json`）→ `node tests/actor-facing.mjs`；`check:content` 会检查每张位图都有朝向记录 |
| 资产/新人物 | 原图参数/候选留存、透明度报告、暗底接触表、脸部灰度与配对、位置/尺寸、浏览器加载 |
| AI 生图贴图 | 逐条对照母题验收（画面里每件东西都能在母题找到出处）、拼图审图、webp 与生效源图 MSE 对齐，见 [生图纪律](art-prompting.md) |
| 页面/CSS | 三视口、换立绘不跳高、按钮命中、缩放可读性、弹窗暂停、键盘操作；尺寸类问题加 DOM 实测（`getBoundingClientRect`），详见 [UI 改造的诊断纪律](ui-diagnosis.md) |
| 定位转场 / 新增 scene | `check:content`（方位表覆盖门禁）、`npm run test:locator`、`npm run test:browser`；新增 scene 必须先在 `design/scene-places.json` 补坐标，见 [大地图定位转场](scene-locator.md) |
| 新回/存档 | 全流程、新旧中段及旧终幕迁移、坏档恢复、所有演员状态、回看历史无重复 |

不能为了通过测试而把“必须有废墟建筑”改成任意占位；也不能把每张图都必须有两个道具当成美术质量标准。测试应验证实际语义与不变量。截图用于人工判断，新运行成功证据与旧基线截图分别记录。

## 人工目检清单

- 原文：事件覆盖、称谓身份、原文起句、实际出现与转述、未见面人物、年龄。
- 地图：罗盘、入口墙面、门洞与路线、院落相对关系；总览与局部同一解释。
- 美术：五官/脸型差异、年龄、立绘/Q 版同人、光向和色调、白边、漏道具、脚底漂移。
- UI：一屏地图与主控件、对白稳定、长文可读、缩放不误触、隐形区域不抢点击。
- 流程：自动、暂停/继续、跳过、段落定位、资料弹窗、回看、保存/读取、刷新。
- Tiled：若声称兼容，实际打开目标图确认 TSJ、gid、图像相对路径和层；没打开则明确仍待应用内目检。

## 常见故障

| 现象 | 优先查哪里 |
| --- | --- |
| 新回没有出现在目录里 | story.ts import/chapters/bookNames、目录面板按 book 分组的数据 |
| 新图缺失或启动失败 | maps 顶层、sceneId 唯一、必需层、focus 与格心 |
| 演员忽然不见/不能走 | scene 切换会隐藏全部人；是否先 show、站点是否可走 |
| 人物穿墙或抄近路 | Route 走廊先列后行补网格、PlanBlockers/ArtFootprints 缺失 |
| 建筑位置对但人物漂浮 | 原图锚点、裁剪/镜像/缩放传播，不改剧情去补误差 |
| Tiled 素材变错而网页正常 | TSJ gid 重排、旧 TMJ gid 未同步；网页按 asset 名读取 |
| 生成后仍看到旧脸 | 是否 builder 应用 approved；artImage 内容版本；浏览器重新载入 |
| 面部重建报校准变化 | 原图校准与存档补丁不同，重新评审补丁，不绕校验 |
| 新回让旧档无法恢复 | 旧 index/终幕 ended 校验、新演员缺状态、没有版本迁移 |
| 新回上线后**上一回**的封底说「全书至此」 | `design/chapter-titles.json` 缺新回目的回目联 → `Leaves.tsx` 的 `chapterTitle(nextBook)` 返回 null → 走 else 分支。**先在 Node 里实读 `chapterLeaves()`/`bookNames` 确认「下一回是哪一回」算对了，再看组件读的是什么**：数据层对、组件层错 = 某个 lookup 返 null |
| 收起封底后「回到封底」按钮不见了 | `src/App.tsx` 顶栏按钮的三态判断顺序：凡按**全书状态**判定的分支（如 `ended`，只在全书末节点为真）排在 `foldedBack` 前面，就会在末回把「回到封底」顶掉。**这类分支在非末回永远走不到 = 藏着的缺陷**，加一回当末回时才暴露。修法：`foldedBack && ended` 提到最前面（**且只在末回接管**——见下一条） |
| 收起封底后读者推不动了 | 反过来：把 `foldedBack` 无条件接到最前面，顶栏被锁成「回到封底」，读者收起封底 → 点「回到封底」翻回纸页 → 再收起，又是「回到封底」，**回末节点上再无前进的路**。而且它挡着的那个理由（「会跳过下一回封面」）**实测不成立**：封面是到达下一回首节点时由 `src/leaves.ts` 的 `leafTrigger` 翻出来的，与封底收没收起无关。修法：`foldedBack` 只在**末回**接管按钮，非末回照旧推进 |
| 断言把另一个缺陷挡在后面 | `tests/lib/backcover.mjs` 的 `assertFoldedBackIsNotAPassThrough` 曾断言「收起封底后『继续剧情』必须消失」，理由是防「跳过封面」——那条理由是假的，于是断言逼出了一个真缺陷（顶栏死路），还把 `browser-smoke` 弄红了。**改断言前先问「它的理由实测成立吗」**；断言挡住的也许是另一个缺陷，而不是它自己声称的那个 |
| 渲染机连不上 | 先分清**端口不通**（服务没起：`curl /system_stats` 超时但 ping 得通）与**主机不通**（`route` 报 `REJECT`、`arp` 报 `incomplete` = 整台脱网）。后者要另找出图通道：内置图像生成 → `scripts/cutout_white_backdrop.py` 抠白底（纯白底不需要 SAM）→ 校准 → manifest |
| 回归报「走到了这一回不该有的场景」 | **先分清是产品的错还是测试的错**。第 20 回曾报 `unexpected stage yihong`（第 21 回的新图）：产品行为是对的，**是测试点错了按钮**——顶栏那**一个**按钮在「跳过移动」/「继续剧情」之间换身份且占同一位置，`if(await skip.isVisible())await skip.click()` 的时间窗里 React 换了按钮，Playwright 重新解析 locator 后那一下落在「继续剧情」上 → **剧情多走一步** → 跨过本回末节点（封底没翻出来、下一回封面也没翻）。修法：改用 `tests/lib/pickup.mjs` 的 `clickSkipIfShown`/`clickForwardIfShown`（按**当下真实文案**取元素 + `dispatchEvent`）。**排查靠探针不靠猜**：插桩 `engine.advance` 看索引、查 DOM 与 `engine.step` 是否撕裂、用 `page.exposeFunction` 把点击实时送回 Node 侧统一时钟对齐事件流（`performance.now()` 跨 `page.evaluate` 不可比） |
| 线上测试报 `Failed to fetch dynamically imported module: /design/xxx.json` | **`design/` 是开发目录，不随 `dist` 部署**，线上必然 404。测试**不要**在浏览器上下文里 `import('/design/...')` 或 `fetch('/design/...')`——设计数据在测试机上现成，一律在 Node 侧 `readFileSync` 读。`browser-smoke.mjs` 的「第 1 回段落数」曾这么写，线上第一步就挂 |
| Qwen 图与参考无关 | 官方 API/点分图槽/未删示例槽、prompt 图号、实际保存节点 |
| ComfyUI 卡住 | 当前队列/服务与网络；不清别人任务、不并行轰炸 |
| 表情变体不生效 | `manifest.json` 里有没有该 `*-portrait-<emotion>` 条目；`build_art_assets.py` 重建 manifest 会抹掉非校准来源的条目，现已改为合并保留；`check:content` 会检查磁盘上每个 PNG 都已登记 |
| 某张脸朝向反了 | 该位图在 `design/character-facing.json` 里的记录；先跑 `scripts/facing_assets.py` 重测，再看 `scripts/facing_review_sheet.py` 的目检表；表情变体按自己的键查表，不继承基础立绘 |
| 改完样式别的界面乱了 | 改了全局选择器却漏了使用点；`grep -rn "\.xxx" src/` 查全使用方，优先加限定而非改基类 |
| 换场景后大地图切到一片没名字的点 | 该 scene 是 `realm` 层（姑苏/扬州/太虚/京郊…），不该下钻；查 `drill = level !== 'realm'` 与 `detailOpacity`，见 [大地图定位转场](scene-locator.md) |
| 转场一开，几十个旧测试各自慢一拍 | 小场景图被设成了 `visibility:hidden`；Playwright 判为不可见。改用 `opacity:0`，上面的覆盖层本来就不透明 |
| 「跳过移动」点击挂 30 秒超时 | 它是一次性演出按钮，会在 `isVisible()` 与 `click()` 之间自己收起。给它短超时并吞掉：跳过是可选加速，不是必经步骤。第 18–21 回及四份线上脚本已统一 |
| 贴图一直不加载 | 给 `IntersectionObserver` 的 root（`dialog`）或其祖先加了 `overflow`；视口内外各验一次 |
| 文字排版看着都一样大 | 祖先的通用规则特异性更高（`.atlas-body p` 0,1,1 压过 `.bond-note` 0,1,0）；补同等特异度，改后实测计算字号 |
| 卡片大小不一 | 内容字数不同导致外框变化；同类卡片外框尺寸必须唯一，文字折行数固定 |
| 生图里多了没要的器物 | 母题里写了它（托盘/碟子/灯/陪衬）；**从母题删掉**，加否定句无效 |
| 生成了但图没变 | `latest_source` 只认 `_new` 取错图；按 mtime 取并排除 `_v` 归档 |
| webp 与源图对不上 | webp 是有损压缩，MD5 不可用；用 64×64 灰度 MSE（阈值 d<5）判定 |

## 交接格式

每回 `docs/chapterNN-production.md` 记录：范围与底本、事件覆盖、人物/场景/资产清单、维护来源、生成任务/seed、推定与争议、存档变更、运行命令与通过时间、截图路径、未完成事项和下一步。建议包含下一位 agent 可直接使用的一段续作提示词。

状态使用“已规划 / 已生成 / 已目检 / 已校准 / 已接入 / 已验证”，不要把它们混为一个“完成”。计数从实际文件和检查结果取值，正文里的历史数量随接入更新；不要靠修改数字掩盖缺内容。没有 Git 时给出备份路径；有 Git 后记录提交/工作区状态，但用户未要求时不自行发布或部署。
