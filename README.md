# 红楼一隅 · 等距叙事地图

《红楼梦》前三回的交互改编原型：234 个剧情节点、23 个段落、18 张 40×40 等距局部地图，配有荣国府总览与前两回行迹。33 名人物有立绘和 Q 版，共 66 张人物图；运行美术资产共 99 张。人物五官已分别设计并重绘，图鉴支持头肩近景。

地图为原文关系约束下的叙事舞台，非建筑测绘复原；文字为交互改编，尚需底本逐句校订。人物当前以静态姿态移动，精细建筑遮挡与完整走路帧尚未制作。

## 后续 Agent 从这里开始

先读 [AGENTS.md](AGENTS.md) 和 [开发与制作手册](docs/production/README.md)。新增回目按 [新回目流程](docs/production/chapters.md) 执行，复制 [回目制作记录](docs/production/templates/chapter-brief.md)。

| 制作内容 | 规范入口 |
| --- | --- |
| 文件维护来源、覆盖风险、架构 | [工程结构](docs/production/architecture.md) |
| 底本、人物身份、时间层、方位推定 | [考据与改编](docs/production/research.md) |
| 统一画风、独立五官、成对资产、ComfyUI | [美术生产](docs/production/art.md) |
| Tiled 对象层、脚底锚点、碰撞、总览道路 | [地图构建](docs/production/maps.md) |
| 横版信息布局、对白/行动、缩放、弹窗 | [UI 与交互](docs/production/ui.md) |
| 自动验证、人工目检、交接 | [验收规范](docs/production/verification.md) |

## 运行

Node.js ≥22.18，本机已用 26.10。精确版本由 package-lock 锁定：React 19.3、Phaser 3.90、TypeScript 7、Vite 8。

```sh
npm ci
npm run dev
```

默认 `http://127.0.0.1:5173`。点击“继续剧情”或空格推进，移动期间可跳过；拖动/缩放地图，用“回到剧情镜头”恢复跟随。顶部聚合自动、回看、暂停与推进；设置中有存档、地点目录、人物图鉴和来源说明。首次进入有加载页（Q 版人物沿进度条奔跑）；切换场景时保留上一帧并显示同款加载卡，空闲时预取后续场景素材；美术以 WebP 交付（约 3MB）。竖屏手机会收到横屏邀请，也可选择继续竖屏浏览。

浏览总览不改变剧情，明确点击地点定位才跳转。每条稳定对白自动保存，刷新后恢复；弹窗暂停演出并保留手动暂停状态。当前支持旧第三回 v2 存档迁移到前三回 v3，继续扩回时需另做兼容，不能简单改名字。

## 验证

```sh
npm run check:content
npm test
npm run build
```

开发服务运行后：

```sh
npm run test:browser
node tests/character-identities.mjs
node tests/asset-scenes.mjs
```

主浏览器测试可设置 `TEST_URL`、`CHROME_PATH`；聚焦脚本目前使用本机 Chrome 和 5173，详情见验收规范。输出截图在 `artifacts/`。

图像校准和身份验证需 Pillow/numpy，使用已有合适 Python 环境：

```sh
python3 scripts/verify_character_identities.py
```

普通开发不需要重建地图、美术或调用 GPU。重建前查 [维护来源和覆盖范围](docs/production/architecture.md)；某些生成器会覆盖 Tiled 手工摆放。当前目录没有 Git 元数据，需先保留文件备份。

## 数据与证据

- [前三回覆盖与存档说明](docs/first-three-chapters.md)
- [荣国府方位与原文推定](docs/estate-geography.md)
- [人物身份重绘流程](docs/character-identities.md)
- [主角灰度前后对照](art/identity/main-face-comparison.png)、[全人物面部](art/identity/cast-faces.png)、[立绘/Q 版配对](art/identity/paired-identities.png)
- [透明素材与锚点接触表](art/asset-contact.png)
- [第三回剧情](design/chapter03-story.json)、[入府 Tiled 地图](maps/rongguo-entry.tmj)、[总览 Tiled 参考](maps/world/rongguo-overview.tmj)

网页读取 `maps/*.tmj` 的 18 张局部地图；总览读取 `design/rongguo-world.json`，`maps/world` 为单向导出参考。Tiled 中对象实际坐标优先，资产尺寸与锚点由 manifest 校准契约提供。

西角门在西墙是本项目采用的方案；黑油门位于南墙偏东。原文明示去程出西角门、往东过正门、入黑油门，回程经过正门是本版设计选择。原文没有唯一精确总图。

早期 [设计草案](docs/design.md)、[分镜](docs/storyboard.md)、[布局预览](docs/rongguo-layout.png) 保留作历史资料，不能据此推断当前已覆盖回目或全套地图。Tiled JSON 与网页已有验证，Tiled 应用内目视打开仍需单独验收。
