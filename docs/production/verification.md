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
```

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
| 页面/CSS | 三视口、换立绘不跳高、按钮命中、缩放可读性、弹窗暂停、键盘操作 |
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
| 新回下拉没有出现 | story.ts import/chapters/bookNames、App 分组仍写死前三回 |
| 新图缺失或启动失败 | maps 顶层、sceneId 唯一、必需层、focus 与格心 |
| 演员忽然不见/不能走 | scene 切换会隐藏全部人；是否先 show、站点是否可走 |
| 人物穿墙或抄近路 | Route 走廊先列后行补网格、PlanBlockers/ArtFootprints 缺失 |
| 建筑位置对但人物漂浮 | 原图锚点、裁剪/镜像/缩放传播，不改剧情去补误差 |
| Tiled 素材变错而网页正常 | TSJ gid 重排、旧 TMJ gid 未同步；网页按 asset 名读取 |
| 生成后仍看到旧脸 | 是否 builder 应用 approved；artImage 内容版本；浏览器重新载入 |
| 面部重建报校准变化 | 原图校准与存档补丁不同，重新评审补丁，不绕校验 |
| 新回让旧档无法恢复 | 旧 index/终幕 ended 校验、新演员缺状态、没有版本迁移 |
| Qwen 图与参考无关 | 官方 API/点分图槽/未删示例槽、prompt 图号、实际保存节点 |
| ComfyUI 卡住 | 当前队列/服务与网络；不清别人任务、不并行轰炸 |
| 表情变体不生效 | `manifest.json` 里有没有该 `*-portrait-<emotion>` 条目；`build_art_assets.py` 重建 manifest 会抹掉非校准来源的条目，现已改为合并保留；`check:content` 会检查磁盘上每个 PNG 都已登记 |
| 某张脸朝向反了 | 该位图在 `design/character-facing.json` 里的记录；先跑 `scripts/facing_assets.py` 重测，再看 `scripts/facing_review_sheet.py` 的目检表；表情变体按自己的键查表，不继承基础立绘 |

## 交接格式

每回 `docs/chapterNN-production.md` 记录：范围与底本、事件覆盖、人物/场景/资产清单、维护来源、生成任务/seed、推定与争议、存档变更、运行命令与通过时间、截图路径、未完成事项和下一步。建议包含下一位 agent 可直接使用的一段续作提示词。

状态使用“已规划 / 已生成 / 已目检 / 已校准 / 已接入 / 已验证”，不要把它们混为一个“完成”。计数从实际文件和检查结果取值，正文里的历史数量随接入更新；不要靠修改数字掩盖缺内容。没有 Git 时给出备份路径；有 Git 后记录提交/工作区状态，但用户未要求时不自行发布或部署。
