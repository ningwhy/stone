# 人物五官与身份一致性

原素材过度依赖同一套俊美脸模板。新设计把脸型、眉形、眼形与眼距、鼻形、唇形、下颌和常态神情分别写入 `art/identity/character-designs.json`，覆盖前三回有形出场的 33 名人物。外貌是原文描述与原创视觉解释的结合，不将全部设计细节冒充原文记载。

立绘先定面部，再用对应立绘的面部作为第二张参考图重绘 Q 版。发饰、服装、身体和姿势不承担唯一辨识任务。凤姐突出高挑眉与细长凤眼；黛玉突出清瘦、细眉与含愁目光；宝玉突出饱满的少年面部与明亮神情；迎春圆润温和，探春眉眼舒展而有精神。长辈、书生、商人、僧道与仆妇也分别设计，不共用面部模板。

## 生成与重建

使用项目提供的 local-image-studio 技能，局域网 ComfyUI，Qwen Image 2.1 edit，30 步、cfg 1。GPU 作业串行执行，提交前队列闸门为 0。保存输入、完整生成图、种子与提示词、原图、原生尺寸遮罩和最终合成图。面部轮廓允许在限定范围内变化，遮罩外 RGBA 像素保持不变；图片尺寸和脚下锚点保持原值。

1. 用带 Pillow/numpy 的 Python 执行 `scripts/redesign_character_faces.py`。可用 `--ids` 选择人物、`--kind portrait/chibi` 选择类型，默认跳过已存在生成结果。
2. 查看 `art/identity/face-comparison.png`（去服饰的灰度前后对照）及 `paired-identities.png`（立绘与 Q 版配对）。灰度图用于人工检查，不把像素差异率当成人物可辨识的自动证明。
3. 评审记录在 `art/identity/approved.json`。运行 `scripts/build_art_assets.py` 时，标准校准后应用这些已检查的面部版本。原素材或校准变化时会拒绝盲贴旧补丁，要求重新检查。
4. 执行 `scripts/verify_character_identities.py`，验证覆盖范围、遮罩外不变、尺寸、锚点和运行素材一致。人物图鉴采用头肩近景；对话与地图分别继续使用完整立绘和 Q 版。图片 URL 带内容版本，避免浏览器继续显示旧脸。

所有旧 PNG 均保存在 `art/identity/originals`；第一轮试稿另存 `art/identity/first-pass`，不覆盖最初的 AI 源图与抠图结果。

## 已知修正：原告 Q 版脸部补丁朝向

原告 Q 版（`plaintiff-chibi`）的脸部补丁把原本与身体同向（朝左下）的脸换成了朝右，与身体垂直，公堂截图里读作"只镜像了脸"。修正方式：沿用同一审核遮罩（`mask-native.png`，脸部窗口 x67-98/y7-30）在包围盒内水平镜像 `final.png` 的脸部区域，遮罩外像素仍与原图逐像素一致（`apply_identity` 的 `np.array_equal` 守卫通过），身份细节保留、朝向与身体一致。修正后 `design/character-facing.json` 的 `plaintiff.chibi` 为 `left`（`visual-review` 证据），`plaintiff.portrait` 同为 `left`——Vision 对原告立绘的关键点拟合失真（鼻尖落在胸口），两处原测量均不可信。视觉证据：`scripts/facing_audit.swift` 的拟合叠加图与前后对比（原图/补丁/镜像后三栏 8 倍放大）。
