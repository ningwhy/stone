# 画风、人物身份和美术资产

## 统一画风

共用风格文本以 `art/generation-plan.json.style` 为准：精致国风手绘，工笔线描结合温润水彩与不透明水粉，纸纹、细腻轮廓与材质，低饱和青灰、松绿、暖米白、赭石、暗朱红；柔和光从画面左上照入；无文字、水印、签名。清代贵族宅院气质是原创视觉演绎，不宣传为服饰考古复原。

参考现有校准成图：`public/assets/rongguo/flower-gate.png`、`garden-tree.png`、`main-hall.png`；人物参考新脸的黛玉、凤姐、贾母和冷子兴。新图与它们并排看线条、颜料厚薄、纸感、饱和度、光向和大小，不只看提示词相同。禁止突然混入 3D 塑料、现代动漫高光或写实摄影质感。

固定 seed 是复现手段，不是画风或身份保证。风格需要参考图、明确设定和目检；不得用同一个“漂亮古风脸”生成所有角色。

## 角色先定脸再配衣

`art/identity/character-designs.json` 是前三回 33 人面部设定。新人物记录：脸型/下颌、眉、眼形与眼距、鼻、嘴、常态神情、年龄及原著依据，另外记录发饰/服装。近亲可以有相似点，必须仍能区分。

先用角色立绘确定身份，再用该立绘的脸作为 `<image2>` 参考重绘 Q 版 `<image1>`。指定哪些眼鼻口特征要传递，保留 Q 版比例。不是同时从两段相似文字独立生成两个陌生人。

检查方法：裁掉衣服，统一脸部显示尺度，做灰度对照；查看主要角色放在一起是否仍能分辨，再看立绘/Q 版是否同人。灰度对照不是“像素差异 > 某阈值”的自动辨人测试。儿童要有儿童面部比例；老人、商人、仆妇、文士不能都套年轻美人脸。

当前运行图有 600px 及 720px 高立绘、约 98–118px 的 Q 版，英莲 Q 版 80px。实际尺寸以 manifest 为准；不要把目标尺寸当成实测。新图先在现有对话框/地图中比较头脸大小，不能只统一图片外框高度。

## 本地生成流程

先读 `.local-tools/local-image-studio/SKILL.md`；用户提供的技能保留在项目内，使用 `http://192.168.4.66:8188`。GPU 单进程串行，已有队列先等空，绝不清队列或取消他人作业。`--max-queue-depth 0` 是提交闸门，调用端仍应等待已有任务完成。

- `generate_art.py`：按 plan 用 Z-Image 生成新建筑/道具/初始人物；可 `--only ASSET_ID` 只生成目标。已有成功源图跳过。
- `matte_art.py`：`--only ASSET_ID` 对目标做 SAM/SDMatte 双路分割，保留候选及工作流。
- `redesign_character_faces.py`：Qwen 2.1 edit，先 portrait 再 chibi，30 步、cfg 1，512×512 头部参考；按 `--ids ACTOR_ID` 选择人物，可断点续跑。
- `review_character_identities.py`：输出全人物彩色脸、灰度主角对照；只有目检完成才加 `--record` 写 approved。

AI 生成完成还不能上线。原图保留 `art/source/ASSET_sSEED-01.png`，参数同存；抠图在 `art/matted/`；校准后才写 `public/assets/rongguo/`。新尝试用新 seed/版本 ID；保持旧图归档，`--keep-old` 不替代你对“哪张是最终采用图”的记录。

Qwen 节点需要官方 API JSON，不是 UI 画布导出。图像输入正确格式是 `images.image_1: [LoadImageNode,0]` 的点分扁平键；未用 image2/3 槽删除。技能尾部有旧的嵌套写法，与当前实测实现不符，以脚本和成功工作流为准。prompt 显式写 `<image1>`、`<image2>` 和需要保留/修改的属性。当前项目修正过 SaveImage 前缀，带 seed/唯一 token，避免服务端同名产物混淆。

服务不可达先 health/queue 判断，区分权限、网络和服务停机，不冒称生成完成。不要并行增加作业尝试“加速”。当前人物图不应为文档编辑重复生成。

## WebP 运行副本

运行时通过 `src/art.ts` 统一取素材 URL：manifest 中的 PNG 原图是唯一权威来源（校准、`check:content` 都以它为准），`npm run art:webp`（scripts/build_webp.mjs，需 cwebp）生成同名 `.webp` 并入仓，运行时只请求 WebP；`npm run build` 末尾的 prune_dist 会删除 dist 中未被引用的 PNG。重生成美术后必须重跑 `npm run art:webp`，否则线上请求不到新图。

## 原图 → 校准契约

新增 `art/generation-plan.json.jobs` 项：`id`、唯一 `seed`、`size`、`prompt`、用于分割的 `subject`。同风格前缀加精确主体，明确建筑视角、门向、完整轮廓、纯白背景、接地点、无附属平台；实际纯白与几何都要检查。

`art/calibration.json.assets` 每项包含 `id`、`seed`、原图像素 `anchor`，以及最终 `height` 或 `width`。可用字段：

| 字段 | 用途 |
| --- | --- |
| `sourceId` | 使用不同源图 ID，保留稳定运行素材 ID |
| `clipRect`、`clearPolygons`、`clearRectangles` | 裁切、门洞或误分割清理 |
| `restorePolygons` | 从原图补回被人物分割漏掉的折扇、邸报、竹杖等 |
| `bodyCompress.split/factor` | 现有 Q 版下半身压缩；新图先画对比例，不无脑套用 |
| `baseSlope/targetSlope` | 有限竖向剪切校准底边，目标等距轴约 ±0.5 |
| `mirror` | 固化朝向变体，锚点同步变换 |
| `solidAlphaThreshold` | 最终 alpha 压实阈值，默认 210；特殊细叶/竹杖按目检调整 |

builder 顺序是原 SAM alpha ≥110 二值化 → 恢复道具 → 裁切/清理 → 身体压缩 → 剪切 → 镜像 → alpha 包围盒裁剪 → 缩放 → alpha 压实 → 应用经检查的新脸。锚点随几何变换，不靠剧情站位补偿错位。

`extend_art_calibration.py` 对陌生 ID 可能尺寸字典查不到，且从 jobs 下标 8 开始；`calibrate_missing_art.py`、`calibrate_prequel_art.py` 含既有批次坐标。后续应显式添加经测量的新条目或目标回校准脚本，不把这些当通用向导。

## 人物朝向表

原图脸部朝向并不一致，立绘与 Q 版不能靠同一条全局规则镜像。`design/character-facing.json` 是权威朝向表，每个 actor 分 `portrait` 与 `chibi` 两个字段（`left` / `right`），并附 `evidence`（测量值与方法）。运行时经 `src/story.ts` 的 `paintedFacing(actor, kind)` 查询：对话框立绘按讲话人/听众位置决定是否 `scaleX(-1)`，地图 Q 版整图左右镜像（`setFlipX`，模拟向后转），且镜像条件不再是"只在行走时"——`direction` 停止后、跨场景/跨段落都保持，由引擎在 `show` 与移动到达时按站位写入（见 `docs/design.md` 的朝向演出规则）。

朝向由 Apple Vision 语义关键点的几何关系测得（`scripts/facing_vision.swift` 输出鼻尖/嘴部相对双眼中点的偏移，`scripts/facing_measure.py` 批量跑，`scripts/build_facing.py` 生成 JSON）。可信度来自四条独立证据：`leftEye` 质心 x 恒小于 `rightEye` 质心 x（76/76，符号由几何确定，无需参照图）、关键点落位目检、镜像自洽性（38/38）、鼻/嘴双特征互证（55/61）。眼宽差与 Vision yaw 在水彩古风画上均不可用，已明确弃用；暗部质心、肤色/轮廓质心、Q 版头身偏移等自动法也已证伪。新人物补资产后须重跑测量并更新该表，不能沿用默认 `left`。

例外：原告（plaintiff）。Vision 对其立绘的关键点完全失真（鼻尖落到胸口、唇贴袍面，绿/橙/红质心坐标可复现），测得 `right` 与目视相反——原图与补丁后头部均朝左。`scripts/build_facing.py` 的 `REVIEWED` 表按目视结论改写为 `portrait=left`，`evidence.method` 记为 `visual-review` 并附原因；其 Q 版脸部补丁（mask 仅覆盖脸部窗口 x67-98/y7-30）把原本与身体同向朝左的脸换成了朝右，已用同一 mask 在包围盒内水平镜像改回朝左（`art/identity/plaintiff-chibi/final.png`，`apply_identity` 的遮罩外像素校验仍通过）。`scripts/facing_audit.swift` 可把 Vision 拟合画回图上供这类目检复核。

SAM 与 SDMatte 都保留，但 builder 当前读取 `*-sam.png`。若采用 SDMatte，显式扩展选择契约并留原候选，不把 SDMatte 假装改名为 SAM。

## 旧人物面部更新

源图之外还有 `art/identity/originals`、每人 `input.png`、`edit-01.png`、`mask-native.png`、`geometry.json`、`request.json`、`final.png`、`reference.png`。脸部合成允许限定范围内轮廓变化，遮罩外 RGBA 保持原值，原尺寸/锚点不变。

人物脚本依赖 auto-face-boxes 中的受检坐标，并有少数手工覆盖；检测脚本只是候选，皇冠/衣服可能被误认成脸。新角色须先补设定和脸框并目检，不能只在 cast 注册就宣称身份流水线完整。近景裁切依赖 manifest.identity.faceBox。

`build_art_assets.py` 只应用 approved 里检查过的图，验证原图与当前校准图逐像素一致；校准改变时主动报错。应重新生成/检查补丁，不移除保护或覆盖归档来“修好”错误。保留既有身份，换装以身份参考为基础。

## 美术验收

1. 白/米色/深绿/棋盘底都看轮廓，检查发丝、门洞、石洞、白边、漏道具和透明晕圈。
2. `art/alpha-report.json` 可见像素中 alpha ≥250 的比例 ≥90%；它只检透明度实度，不能证明轮廓或画风正确。
3. 树根、鞋底、门槛与逻辑落点重合，画面不漂浮；人物换图和走路不抖动。
4. 总览用院落外观，书房不能用桌子代表，家具只放局部场景。
5. 新墙/门要检查等距轴、墙向、通行宽度；要拆层就实际提供后墙/前柱/屋檐，而非文字声称已拆层。
6. 检查立绘/Q 版同人及灰度脸辨识；资产从生成、入选、校准、运行到截图每一步有记录。
7. 立绘与 Q 版朝向符合 `design/character-facing.json`：对话框里讲话人朝文本、听众朝讲话人，地图上 Q 版整图镜像跟随 `direction`——行走时朝行走方向，停下、到达与跨场景后保持最后朝向（`node tests/actor-facing.mjs` 可复跑采样）。
