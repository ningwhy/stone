# AI 素材接入与定位：入口

完整规范已集中至 [画风、角色与资产生产](production/art.md) 和 [地图与 Tiled](production/maps.md)，后续以这两份为准，避免多份独立维护的坐标公式和旧数量冲突。

当前为 99 张运行 PNG，其中 33 人的立绘/Q 版共 66 张。入府图 Art 层为 22 个对象；共 18 张局部地图。生成源、参数、SAM/SDMatte 候选、校准和面部旧图均保留。

最短流程：确定人物身份/资产规格 → 本地 ComfyUI 串行生成 → 抠图候选目检 → 写 calibration 中的源图锚点与尺寸 → build_art_assets → 更新目标地图的摆放和碰撞 → 页面目检。定位依靠像素锚点及格心投影，不能靠提示词保证几何准确。

相关文件：

- [素材计划](../art/generation-plan.json)
- [校准契约](../art/calibration.json)
- [运行 manifest](../public/assets/rongguo/manifest.json)
- [透明度报告](../art/alpha-report.json)
- [素材接触表](../art/asset-contact.png)
- [面部重绘规范](character-identities.md)
- [生成器覆盖范围](production/architecture.md)

不要直接执行全部旧校准脚本来接新回；现有 extend/calibrate 脚本含旧批次专用坐标与尺寸映射。Tiled 手工放置也不会自动反写 calibration，重建前必须保存其维护来源与副本。
