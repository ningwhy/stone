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
- `matte_paper_key.py`：`--only ASSET_ID` 走宣纸底键控，见下节「一群人抬着的东西怎么抠」。
- `redesign_character_faces.py`：Qwen 2.1 edit，先 portrait 再 chibi，30 步、cfg 1，512×512 头部参考；按 `--ids ACTOR_ID` 选择人物，可断点续跑。
- `review_character_identities.py`：输出全人物彩色脸、灰度主角对照；只有目检完成才加 `--record` 写 approved。

AI 生成完成还不能上线。原图保留 `art/source/ASSET_sSEED-01.png`，参数同存；抠图在 `art/matted/`；校准后才写 `public/assets/rongguo/`。新尝试用新 seed/版本 ID；保持旧图归档，`--keep-old` 不替代你对“哪张是最终采用图”的记录。

Qwen 节点需要官方 API JSON，不是 UI 画布导出。图像输入正确格式是 `images.image_1: [LoadImageNode,0]` 的点分扁平键；未用 image2/3 槽删除。技能尾部有旧的嵌套写法，与当前实测实现不符，以脚本和成功工作流为准。prompt 显式写 `<image1>`、`<image2>` 和需要保留/修改的属性。当前项目修正过 SaveImage 前缀，带 seed/唯一 token，避免服务端同名产物混淆。

服务不可达先 health/queue 判断，区分权限、网络和服务停机，不冒称生成完成。不要并行增加作业尝试“加速”。当前人物图不应为文档编辑重复生成。

母题怎么写、生成后怎么验、`--keep-old` 怎么落盘与归一化，见 [生图纪律：母题、验收与落盘](art-prompting.md)。一句话：**母题里出现的任何名词都会被画出来，风格基底里的否定句救不了你。**

## WebP 运行副本

运行时通过 `src/art.ts` 统一取素材 URL：manifest 中的 PNG 原图是唯一权威来源（校准、`check:content` 都以它为准），`npm run art:webp`（scripts/build_webp.mjs，需 cwebp）生成同名 `.webp` 并入仓，运行时只请求 WebP；`npm run build` 末尾的 prune_dist 会删除 dist 中未被引用的 PNG。重生成美术后必须重跑 `npm run art:webp`，否则线上请求不到新图。

### 缓存版本号：URL 必须随内容变

`build_webp.mjs` 给每个 manifest 条目写入 WebP 自身的 md5 前 12 位（`hash` 字段），`src/art.ts` 的 `artImage()` / `assetImage()` 把它拼成 `?v=<hash>`。此前只有带 `identity` 的人物资产有版本号（用 `identity.revision`），道具与家具的 URL 永远不变——轿子重画成四轿夫后，线上文件已是新的，浏览器却一直展示缓存的旧图，就是这个原因。**教训：凡是会被重绘的资产，URL 都要带内容摘要**，nginx 对 `.webp` 是 30d 长缓存，没有版本号就只能等读者手动强刷。

## 音效与音乐

声音全部由 `scripts/build_audio.py` 在本地合成（numpy 振荡器 + 滤波噪声 → WAV → ffmpeg libopus → ogg），不依赖采样库：十首 BGM 共 4.7MB、九个音效共 75KB。生成命令 `npm run art:audio`；`scripts/check_audio.py` 重新测量成品。

这两个脚本需要 numpy（以及 `check_audio.py` 需要的 `ffmpeg`）。PATH 上的 python3 未必装了它，本机可用的是 `/Users/bot/.workbuddy/binaries/python/envs/default/bin/python` 或系统 `/usr/bin/python3`——缺 numpy 时表现为 `ModuleNotFoundError`，换一个解释器即可。

## 十首曲子为什么不一样

第一版是四个场景共用一套 D 宫五声音阶，彼此响度差不到 2dB，其中三首的音高重心都落在同一个音级上——听上去就是一首曲子到处放。现在每一首都规定了调式、主音、速度、主奏乐器和音区，`scripts/check_audio.py` 把「主音级、起音密度、谱心」三项测出来并要求互不相同，防止再次趋同。

**六首场景曲**（跟着地点走）：

| 文件 | 场景 / 调式 | 主音 | 起音密度 | 谱心 |
| --- | --- | --- | --- | --- |
| `bgm-garden.ogg` | 园林白天（宫·D，默认） | D | 2.62/s | 1345Hz |
| `bgm-street.ogg` | 京城街市（宫·G） | G | 2.16/s | 2361Hz |
| `bgm-water.ogg` | 运河舟行北上（羽·B） | B | 2.63/s | 1022Hz |
| `bgm-night.ogg` | 夜（商·E） | E | 0.35/s | 394Hz |
| `bgm-interior.ogg` | 室内正堂（徵·A） | A | 0.83/s | 1966Hz |
| `bgm-myth.ogg` | 太虚 / 梦境 / 废墟（角·F#） | F# | 0.52/s | 659Hz |

**四首回目曲**（跟着回目走，一回一首）：

| 文件 | 回目 / 调式 | 主音 | 起音密度 | 谱心 |
| --- | --- | --- | --- | --- |
| `bgm-book-one.ogg` | 第一回 · 石头与还泪（羽·Bb） | Bb | 0.66/s | 650Hz |
| `bgm-book-two.ogg` | 第二回 · 仕途与冷暖（徵·C） | C | 2.43/s | 2080Hz |
| `bgm-book-three.ogg` | 第三回 · 入府与初见（宫·Db） | Db | 0.88/s | 1229Hz |
| `bgm-book-four.ogg` | 第四回 · 判案与安顿（商·Eb） | Eb | 0.63/s | 349Hz |

十首的主音互不相同（场景曲占去 D/G/B/E/A/F#，回目曲正好落在 Bb/C/Db/Eb），密度跨度 7.5 倍，谱心从 349Hz 到 2361Hz。门禁脚本断言的就是这三件事。

**选曲优先级**（`src/audio.ts` 的 `setTheme(theme, sceneId, book)`）：

1. **场景专属曲**——运河、街市、夜、太虚/梦境/废墟自带一首；
2. **回目曲**——园林、室内、正堂、衙署这类「无场景专属曲」的地方，取当前回目那一首；
3. **兜底**——`bgm-garden`。

例外：`SCENE_WITHOUT_OWN_PIECE = ['lin']`。林如海家因为院中有水而用了 river 主题，但它的内容是父女对话与托付，不是舟行，因此不吃运河的急流曲，落回第三回的 `bgm-book-three`。

| 文件 | 用途 | 时长 |
| --- | --- | --- |
| `bgm-garden.ogg` | 园林、扬州、郭外（默认） | 69.2s 循环 |
| `bgm-street.ogg` | 京城街市 | 53.1s 循环 |
| `bgm-water.ogg` | 运河 · 舟行北上 | 54.3s 循环 |
| `bgm-night.ogg` | 夜（灯市、碧纱橱） | 73.6s 循环 |
| `bgm-interior.ogg` | 室内正堂（荣禧堂、衙署、王夫人院） | 61.8s 循环 |
| `bgm-myth.ogg` | 太虚/梦境/废墟（开场大荒山即此曲） | 71.7s 循环 |
| `bgm-book-one.ogg` | 第一回底乐（甄宅、姑苏、大如州一带） | 62.2s 循环 |
| `bgm-book-two.ogg` | 第二回底乐（雨村仕途、扬州郭外） | 52.6s 循环 |
| `bgm-book-three.ogg` | 第三回底乐（扬州入京、荣府内院） | 58.0s 循环 |
| `bgm-book-four.ogg` | 第四回底乐（应天府、梨香院） | 67.0s 循环 |
| `sfx-step-board.ogg` | 脚步 · 室内木地板 | 0.17s |
| `sfx-step-stone.ogg` | 脚步 · 室外石板（默认） | 0.15s |
| `sfx-step-earth.ogg` | 脚步 · 郭外土路 | 0.18s |
| `sfx-oar.ogg` | 运河上的篙/桨（代替脚步） | 0.55s |
| `sfx-tap.ogg` | UI 与点选人物（小磬） | 1.6s |
| `sfx-page.ogg` | 推进对白（纸页） | 0.42s |
| `sfx-door.ogg` | 进入室内场景（木门吱呀 + 闷响） | 1.5s |
| `sfx-bell.ogg` | 场景开启（远钟） | 6.0s |
| `sfx-chair.ogg` | 轿子移动（轿杆吱呀） | 1.1s |

脚步声按地表选取，判定在 `MapScene.ts` 的 `stepSurface()`：室内为木地板，郭外为土路，运河没有地面、用篙声。每次播放再把 sample 随机变速 ±7%，所以连着走不会像节拍器。

设计约束，改动时保持：

- **五声音阶 + 慢板**，但十首各有调式（宫/商/角/徵/羽各一），每首 40–52 BPM，旋律以级进为主并刻意留白（近静音占比 12–16%），红楼是安静的宅院。
- **RMS 约 -25dBFS**，这是「淡」的来源；不要为了「听得见」抬高整体音量，那是把 BGM 变成噪音。音效比最响的一首乐曲高 5.7dB——再高就会盖住对白。
- **乐器是少量泛音的加法/减法合成**：古筝 18 个泛音 1/n 衰减、箫带 5.3Hz 颤音与气噪声、磬用非谐波分音比（1, 2.76, 5.40, 8.93…）。加新乐器优先加泛音，不要加采样。
- **循环无缝**：`loop_seam()` 把开头两小节以 0.55 音量在结尾重述，首尾能量对齐；fade 只用 0.15s 消爆音，长 fade 会让循环周期性「呼吸」。
- **纸底类素材混响 wet 0.30，音效 0.12–0.20**；IR 是合成的小厅（2.6s 指数衰减噪声 + 5 个早期反射 + 18ms 前延迟）。

运行时是 `src/audio.ts` 的单例（原生 Web Audio，**不挂 Phaser sound**——GameMap 每换地图重建 Phaser.Game，会把音频反复重新解码）。要点：

- AudioContext 在读者首次手势时创建（自动播放策略），`unlock()` 由 App 的一次性 pointerdown/keydown 触发。
- `setTheme(theme, sceneId, book)` 三级优先级选曲，1.4s crossfade；同曲重复调用是 no-op，屋内走动不会重启音乐。**`wantedTheme` 永远存曲名而不是主题名**，否则把音乐关掉再打开会经一次主题映射落到默认曲（这个 bug 曾让测试超时）。
- `warm()` 在 stage preload 时排队，context 不存在就先入队，unlock 后补加载——否则第一次脚步会有延迟。
- 音量（bgm 0.5 / sfx 0.75 默认）存 `localStorage['honglou.audio.v1']`，设置面板两个滑块实时写 GainNode；bgm 拨到 0 会淡出停止而不是静音一个运行中的 source。
- **总开关** `setMuted()` 把 master 增益降到 0（0.06s 淡出，不是硬切），状态存 `localStorage['honglou.audio.muted.v1']`。**滑杆位置不受它影响**——关掉再打开，平衡原样回来。静音时滑杆被 disable，避免看起来还能调。
- `check_content.mjs` 守卫：引擎引用的每个文件必须已构建；地图声明的每个 theme 必须有映射（新增 theme 忘了配曲会直接报错）；构建了却没人引用的文件给 WARN。

测试：`node tests/audio.mjs`（连 dev server）验证 context 解锁、19 个文件实际请求、十首曲子的选曲优先级、四种地表脚步、总开关与滑块的持久化。

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
| `alphaFloor` | 最终 alpha 透明侧阈值，默认 16；细结构家具（椅枨、凳腿、花架立柱）在 70–110px 输出宽度下 1px 抗锯齿边占轮廓比例过大，会把 ≥90% 实度门槛拖到线下，按 128 压平 |
| `matteKind` | 取哪一路抠图，默认 `sam`；成群人物改用 `paper-key`（见下节） |

builder 顺序是原 SAM alpha ≥110 二值化 → 恢复道具 → 裁切/清理 → 身体压缩 → 剪切 → 镜像 → alpha 包围盒裁剪 → 缩放 → alpha 压实 → 应用经检查的新脸。锚点随几何变换，不靠剧情站位补偿错位。

`extend_art_calibration.py` 对陌生 ID 可能尺寸字典查不到，且从 jobs 下标 8 开始；`calibrate_missing_art.py`、`calibrate_prequel_art.py` 含既有批次坐标。后续应显式添加经测量的新条目或目标回校准脚本，不把这些当通用向导。

## 一群人抬着的东西怎么抠（2026-10，轿子加轿夫）

轿子原本是「无人抬轿」的单独一顶，2026-10 改成四名轿夫抬着走。这打破了两条既有假设，值得记下来。

**SAM 处理不了成群的人。** `subject` 写 `people` 只抠出四个轿夫、轿身整个丢掉；写 `people, sedan chair` 会把人和轿子分别成多个实例，合成后人身上出现空洞——躯干是半透明的，棋盘底能透出来。SDMatte 那一路方向相反，把背景建筑一起留下了。原因是 GroundingDINO 按文本找实例，而这里的语义单元是「一整套正在移动的载具」，不是一个可枚举的物体。

改用**宣纸底键控**（`scripts/matte_paper_key.py`）。这批画都画在均匀的宣纸底上，按离底色的距离切比按语义切可靠。三个要点：

- **底色要实测**：取四边各 20px 的中位色，纸纹和暖调都在里面，不要假设纯白。
- **只留大块连通域**：纸纹自身的起伏会过阈值、散落整幅，按面积（默认 2000px）滤掉碎点。连通域用闭运算 + 填洞收一下，避免人物轮廓被纹理切断。
- **贴边的连通域一律丢弃**：模型爱在角落补一段墙或檐，那块一定连着画布边缘；真实主体四周留白、碰不到边。这条规则比逐图量坐标干净，也不会切到人。轿子那张因此自动丢掉了左上角的门楼和墙帽各一块。

产出 `art/matted/<stem>-paper-key.png`，同时写一份 `-paper-key.json` 记录底色、阈值、被丢弃的贴边块和包围盒。`build_art_assets.py` 按 calibration 的 `matteKind` 取对应那一路。实测轿子这套的 alpha 实心率 0.968（门槛 0.90）。

**摆位要跟着改。** 成品从 170×146 变成 230×195。地图里的美术对象由 `build_chapter_maps.py` 用 `manifest 尺寸 × scale` 算，手工放的那份 `maps/yamen.tmj` 要按同一公式同步宽高与落位——`setDisplaySize` 直接吃 Tiled 宽高，不改就会被拉伸。锚点仍取包围盒水平中心与底边，与其它资产一致。

尺度参照：Q 版人物高 116–118px，新图里的轿夫约 95px，轿顶仍在人头之上，比例可接受。

## 人物朝向表

原图脸部朝向并不一致，立绘与 Q 版不能靠同一条全局规则镜像。`design/character-facing.json` 是权威朝向表，**按资产键**记录（`left` / `right`），并附 `evidence`（测量值与方法）：`actors` 下每个角色分 `portrait` 与 `chibi`，`variants` 下每张表情变体各一条。运行时经 `src/story.ts` 的 `paintedFacingOf(assetKey, actor, kind)` 查询：对话框立绘按讲话人/听众位置决定是否 `scaleX(-1)`，地图 Q 版整图左右镜像（`setFlipX`，模拟向后转），且镜像条件不再是"只在行走时"——`direction` 停止后、跨场景/跨段落都保持，由引擎在 `show` 与移动到达时按站位写入（见 `docs/design.md` 的朝向演出规则）。

**逐张清单见 [facing-list.md](./facing-list.md)**——那是由 `scripts/build_facing_doc.py` 从权威 JSON 自动展开的 92 张位图逐行清单（38 立绘 + 38 Q 版 + 16 表情变体），可直接核对哪张朝左、依据是实测还是目视。

载具是唯一不按人脸记的条目：轿子由四名轿夫抬着，轿夫的脸都朝内对着轿身，整组没有单一朝向，所以 `sedan` 记 `evidence.method = default-vehicle-group`、取左为默认，运行时按行进方向整图翻转。它不计入那 92 张。

### 为什么按资产键而不是按角色

一个角色不是一张图。他有立绘、Q 版图，还有若干张各自重画过的表情变体。**表情变体由图像模型重绘，同一角色的不同变体朝向可以不同**——实测贾母的常态立绘朝左、忧愁变体朝右、惊愕变体朝右、欢喜变体朝右。Q 版图也是独立画的一套，不是立绘缩小。早期版本按角色记一个朝向、Q 版"假定与立绘同向"，实测后发现 9 处与画不符（贾母立绘、门子立绘、癞头和尚 Q 版、李嬷嬷立绘、原告立绘与 Q 版、如海立绘、雨村立绘、贾政立绘），已按实测修正。

### 测量方法

朝向由 Apple Vision 语义关键点的几何关系测得（`scripts/facing_vision.swift` 输出鼻尖/嘴部相对双眼中点的偏移，`scripts/facing_assets.py` 批量跑并投票，`scripts/build_facing.py` 生成 JSON）。可信度来自四条独立证据：`leftEye` 质心 x 恒小于 `rightEye` 质心 x（符号由几何确定，无需参照图）、关键点落位目检、镜像自洽性、鼻/嘴双特征互证。眼宽差与 Vision yaw 在水彩古风画上均不可用，已明确弃用；暗部质心、肤色/轮廓质心、Q 版头身偏移等自动法也已证伪。

**多裁切投票**是这一版的关键。Q 版图只有约 50px 宽、头只占其中一小块，低于检测器能接受的尺寸；裁紧了掉头发和轮廓，裁宽了把身体带进画面、检测器可能认出衣领上的"脸"。因此每张图用多种裁切各测一次并投票（`tight` / `wide` / `wider` / `whole`），三种失败各有判据：

- 检不出脸 → 该裁切无效，不算票。
- 鼻与嘴方向相反 → 该裁切的拟合没落在它声称的特征上，不算票。
- `nameCheck` 不是 `ok`（Vision 说的 `leftEye` 没在 `rightEye` 左边）→ 拟合落到的不是脸，偏移的符号毫无意义，不算票。

这条 `nameCheck` 守卫抓到过 `xiren-chibi`：唯一给出读数的裁切返回 `SWAPPED`，测出 `left`，目视是 `right`——没有这道守卫就会写进错误结果。

### 测不出与读不稳的部分

24 张图检测器没能独自定下来（14 张完全测不出，10 张只有一票），由目视裁决并记在 `scripts/build_facing.py` 的 `REVIEWED` 表里，每条附原因，`evidence.method` 记为 `visual-review`，表可复现。目检表由 `scripts/facing_review_sheet.py` 生成（`art/identity/facing-review-sheet.png`）。

**源图不能替代成品图**。`art/identity/<actor>-chibi/edit-01.png` 是 512px 高分辨率源图，Vision 在多数 chibi 上能读出脸——但那是错的图：本项目全部 38 张 Q 版都经过身份系统换脸，换上去的脸可能与身体朝向不一致（旧版就有原告换脸后与身体反向的病灶）。所以测量以出货位图为准，源图只作最后兜底，且读数来源会标为 `vision-landmark-geometry-on-source-bitmap` 以示区别。

例外：原告（plaintiff）。Vision 对其立绘的关键点曾完全失真（鼻尖落到胸口、唇贴袍面），旧表据此按目视改写为 `portrait=left`。本轮用整图与脸窗两种裁切重测，鼻与嘴同向且为 `right`，目视复核（低头、鼻在右）一致，故改回 `right`；其 Q 版同样复核为 `right`。`scripts/facing_audit.swift` 可把 Vision 拟合画回图上供这类目检复核。

SAM 与 SDMatte 都保留，但 builder 当前读取 `*-sam.png`。若采用 SDMatte，显式扩展选择契约并留原候选，不把 SDMatte 假装改名为 SAM。

## 室内家具批次（2026-10）：桌面器皿与家具多样化

问题有两个。其一，SAM/SDMatte 的"仅人物"遮罩把桌面当作深度面，桌上立着的器皿（盖碗、茶盅、饭碗、玉壶春瓶）在桌面高度被整排切断，只留贴桌面的残根，看上去像漏画。其二，11 张室内图反复摆放同一张 `tea-table`，且各图缩放比例 0.6–1.0 不一。

修复与扩充按以下顺序，全部可复跑：

1. `restorePolygons` 从源图补回被切断的器皿：`tea-table` 补盖碗/茶盅/小盅 3 件，`dining-table` 补玉壶春瓶 + 6 碗 7 件（`scripts/furniture_mattes.py`，多边形坐标在源图像素空间，沿物品轮廓留小余量并保持在桌面深色区内）。builder 的"遮罩外逐像素不变"守卫保持通过；`art/alpha-report.json` 只有这两个条目变化。
2. 新增 9 件家具源图：八仙桌、条案、书案、太师椅、圆凳、方凳、顶箱柜、火盆、花架（`scripts/furniture_sources.py`，同风格模板、1024×1024、固定 seed）。
3. 抠图改走 Qwen Image 2.1 `bg-removal` 语义分割（`scripts/furniture_bgremoval.py`）：服务端 SAM/SDMatte 路由因 transformers 与 BiRefNet 不兼容已崩；Qwen 语义抠图没有深度切断，桌上器物完整保留。产物重命名为 `<stem>-sam.png` 供 builder 读取。
4. 条案与火盆两次生成都带出完整房间（墙、窗、屋顶、地板），改用显式"无房间"文案重生成（`scripts/furniture_regen.py`、`furniture_regen_brazier.py`，火盆另换未用 seed）；仍不过关的旧 seed 产物已从仓库清除。
5. `scripts/furniture_calibrate.py` 按阈值化 matte（alpha ≥110）的不透明包围盒算锚点 `[中心x, 底边-2]`，按设计宽度追加到 `calibration.json` 末尾（不打乱既有 gid）；细结构四件加 `alphaFloor:128`。
6. 校验用三重数值判据替代不可靠目测：不透明连通域（最大连通域须 ≥99.9%）、6 倍最近邻边缘放大、输出→源图逐像素 diff（坏点集中在轮廓边缘即插值噪声，顶部区域坏点率与整体持平即无背景泄漏）。
7. 摆位与目检见 `maps.md`；全量回归见 `verification.md`。

教训：生成模板里的"纯白背景、无周围建筑"对场景型主体（正房条案、火盆）不总生效，subject 里要显式写"绝对不要出现房间、墙壁、门窗、屋顶、地板"，并在洋红底接触表上确认只剩主体再入库。

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

### 验收必须带口径

「已目检」不是一个结论，是一个**带检查项的记录**。写交接或制作记录时，要列出这次实际查了哪几项，不能只写「已目检通过」——否则下一位会以为整张图都被验过。

真实教训：账簿 14 张贴图曾被记为「零人物 / 无可读文字 / 主体居中，验收通过」，但清单里**没有「画面里的器物是否属于这一笔账目」这一项**。事后拼图复核才发现 5 张多出了托盘、碟子、孤灯、茶罐套组，另有 1 张印面画出了可读的篆字。清单漏项 = 漏检，漏检就是没验。

所以：

- AI 生成的贴图按 [生图纪律](art-prompting.md) 的逐条清单验收，并注明**本次实际核对了哪几条**。
- 清单要**逐条对照母题写**，不能凭印象列。母题里写了什么，画面里就允许出现什么——多出来的每一件都要能在母题里找到出处。
- 批量图用**拼图**审，不是一张张看（14 张各看一遍容易漏，4×4 网格一眼能看出哪格多东西）。
- 同理，人物资产的「已目检」要写明是查了**同脸辨识**、**朝向**、**锚点**还是**透明度**——只查了其中一项就只写那一项。
