# 工程结构、维护来源与覆盖范围

## 运行链路

`src/main.tsx` 自动读取 `maps/*.tmj`，由 `model.ts` 解析为逻辑地图，交给 `StoryEngine`；`MapScene` 用 Phaser 绘制和驱动地图演出，React `App` 管理对白与导航。`story.ts` 当前显式拼接前三回 JSON，不自动发现新回目。

| 文件或目录 | 职责 |
| --- | --- |
| `design/chapterNN-story.json` | 运行时剧情节点、台词、演出动作、原文追踪 |
| `design/chapterNN-sections.json` | 段落下拉选项和各段起点 |
| `src/story.ts` | 角色注册、动作类型、剧情拼接、段落和回目名称 |
| `src/engine.ts` | 状态机、寻路调度、暂停/跳过、回放、存档验证 |
| `src/model.ts` | TMJ 读取、格心投影、可行走网格、四邻格 A* |
| `src/MapScene.ts` | 地板、建筑贴图、Q 版、深度、镜头、标签、动作路线 |
| `src/art.ts`、`src/Portrait.tsx` | 校准素材契约、图片内容版本、立绘与近景 |
| `src/App.tsx`、`src/styles.css` | 页面布局、播放、弹窗、地图视图切换 |
| `src/WorldMap.tsx`、`src/worldRoutes.ts` | 荣国府总览和跨地点道路 |
| `src/JourneyMap.tsx` | 跨城/梦境行迹目录，当前依赖 prequel 地图说明 |
| `public/assets/rongguo/manifest.json` | 运行素材尺寸、锚点、来源、面部版本；由脚本生成 |
| `maps/world/` | 总览的 Tiled 参考导出，不参与局部场景自动加载 |

## 必须先确定的维护来源

当前存在“脚本生成后再由 Tiled 编辑”的混合流程，不能称为全项目单一 JSON 源。以下按真实覆盖行为区分。

| 内容 | 运行读取源 | 再生成来源与风险 |
| --- | --- | --- |
| 回目 1、2 剧情 | chapter01/02 JSON | `write_prequel.py` 写这两回及 sections、prequel-maps；会覆盖直接改的 JSON |
| 回目 3 剧情 | chapter03 JSON | `write_chapter_story.py` 会覆盖第三回剧情与 sections |
| 入府规划层 | `maps/rongguo-entry.tmj` | `build_planning_assets.py` 从 map-plan 重建规划层，保留 Art/ArtFootprints；仍会覆盖手工改的 Anchors/Routes 等 |
| 入府美术层 | 同一 entry TMJ | `build_art_assets.py` 从 calibration 重建 Art/ArtFootprints/tileset；覆盖 Tiled 中这两层的手工摆放 |
| 其余 17 张局部图 | `maps/*.tmj` | `build_chapter_maps.py` 从脚本内 scenes 加 prequel-maps 整张重建；entry 仅更新场景属性 |
| 荣府总览 | `design/rongguo-world.json` | 网页直接读 JSON；`build_world_map.py` 导出 TMJ，不反向同步 |
| 原始画面 | `art/source/` | `generate_art.py` 按 generation-plan；已有成功源图跳过 |
| 抠图候选 | `art/matted/` | `matte_art.py`；SAM / SDMatte 保留，实际校准构建当前固定读取 SAM |
| 几何校准 | `art/calibration.json` | extend / calibrate 脚本是旧批次专用，不能当通用自动校准器 |
| 新脸 | `art/identity/*`、approved.json | builder 校准后合成；原校准变化时拒绝套用旧脸 |

后续每回必须在制作记录中写清“脚本为主”还是“Tiled 文件为主”。若选脚本为主，手工摆放要同步回该回的生成定义；若选 Tiled 为主，不再对该图运行会覆盖它的生成器。不要让两份不同坐标同时宣称权威。

## 有选择地重建

普通 UI 修改只跑前端验证。新增地图若直接保存完整 TMJ，无需运行旧回目生成器。重建已有素材只运行 `build_art_assets.py`；其副作用包括 entry 美术层、TSJ、manifest、透明度报告和接触表。

需要完整恢复既有前三回时，先备份，再按顺序：

```sh
python3 scripts/write_prequel.py
# 必要时修改已有 calibration；不要无缘由跑旧批次校准器。
# 以下解释器需 Pillow/numpy：
python3 scripts/build_art_assets.py
python3 scripts/build_chapter_maps.py
python3 scripts/build_world_map.py
```

这不是日常启动步骤。重新运行 `write_prequel.py` 会覆盖回目 1、2 的直接修订；重新运行 `build_chapter_maps.py` 会覆盖非 entry 局部图。人物脚本不会在网页启动时调用 GPU。

## 现有边界

- 地板主要用 Phaser 绘制；空的 Ground tilelayer 不代表没有地图。读取器不消费普通地砖层作为碰撞。
- 仅有静态人物图和程序移动/轻微效果，没有完整四或八方向走路帧。
- 墙/门/房屋没有完整拆层遮挡；部分整座门淡化，`visibility=exterior` 控制外观隐藏。
- 可行走网格是规划区域加路线走廊减显式障碍，无动态人物避让。
- UI、行迹目录、总览选择和存档含前三回特定逻辑；扩回时逐项处理，不假设只放一个 JSON 就会工作。
- 原文起句用于追踪，前三回还没有逐句校勘完成。文档记录制作规范，不把原型提升为已完成考证的正式底本。
