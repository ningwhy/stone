# 第八回制作记录 · 比通灵金莺微露意 探宝钗黛玉半含酸

> 状态：**已完成并接入** —— 全流程通过内容门禁、单元/集成测试与生产构建。

## 目标与来源

- 回目全名：第八回 · 比通灵金莺微露意 · 探宝钗黛玉半含酸
- 底本：维基文库《红楼梦/第8回》；本地正文：`docs/chapter08-source.txt`（已备齐，check:content 硬要求）
- 剧情、段落：`design/chapter08-story.json`（23 节点）、`design/chapter08-sections.json`（5 段：c8-pear / c8-gold / c8-sour / c8-lunch / c8-anger）
- 衔接：紧接第七回；宝玉探宝钗在梨香院（复用 c7_lixiang），黛玉随后赶到「半含酸」，末段回荣府摔杯怒李嬷嬷。

## 事件覆盖表（完成）

| 原文起句或事件 | 时间层 | 地点/scene | 在场人 | 状态 |
| --- | --- | --- | --- | --- |
| 宝玉往梨香院探宝钗，见金锁与通灵宝玉 | present | c7_lixiang（梨香院） | 宝玉、宝钗、薛姨妈、莺儿 | 已完成 |
| 金莺（莺儿）微露意：金锁乃癞头和尚所送，须錾在金器上 | present | c7_lixiang | 莺儿、宝钗、宝玉 | 已完成 |
| 黛玉赶到，见宝玉在此，半含酸，借雪雁送手炉讽之 | present | c7_lixiang | 黛玉、宝玉、宝钗、雪雁 | 已完成 |
| 薛姨妈留饭，宝玉喝酸笋鸡皮汤、酒，李嬷嬷拦酒 | present | c7_lixiang | 薛姨妈、宝玉、李嬷嬷 | 已完成 |
| 宝玉回荣府，摔茶杯怒李嬷嬷 | present | night / capital | 宝玉、李嬷嬷、袭人 | 已完成 |

## 地图、人物、资产

| ID | 新建或复用 | 来源 | 状态 |
| --- | --- | --- | --- |
| c7_lixiang（梨香院） | 复用 | 第七回已建 | 已存在 |
| night / capital | 复用 | 既有时间/场景层 | 已存在 |
| ying_er 莺儿 | 新人物·已立绘 | Z-Image turbo + `generation-plan.json` 风格锚点（与旧 45 人同一管线）+ qwen21 抠图硬化 | portrait + chibi 已入 manifest |

- 本回不新建地图，复用第七回梨香院与贾母院/夜景。
- 新增 1 名人物（莺儿），立绘经 `plan_character_identity` 定脸、`regen_new_characters` 出图、`recalibrate_new_chars` 重测锚点、`art:webp` 转码入册。
- `idle` 效果已纳入引擎（与 `jade`/`greet`/`rest`/`anger` 并列），本回多用 `effect(actor,'idle')` 作静立节拍。

## 验证结果（接入后）

- `npm run check:content` → **通过**：709 节点 / 67 段 / 30 地图 / 51 人物 / 219 资产；各回计数为 {7:31, 8:23, 9:17…}。
- `npm test` → **64/64 通过**（修正了「终章节点」「目录七回→九回」「宝钗在台书目」三处硬编码断言）。
- `npm run build` → **tsc 无错 + vite 构建成功**；`prune_dist` 移除 219 张 PNG，运行时改用 WebP（约 3MB）。
- `npm run map:framing` → **0 处取景问题**。
- `npm run test:browser` → **通过**：354 节点逐节点回放、目录九回、跨场景存读档、册页与图鉴（51 人）、总览钻取全部 OK。

## 画风一致性返工（2026-10）

用户指出 7–9 回新人物画风与旧人物不一致。根因是生成管线错配：新角色最初用 Qwen Image 2.1 + 水墨单色 + 全身站像，而旧 45 人是 Z-Image turbo + 工笔重彩 + 半身。已用旧管线重画本回莺儿的 portrait 与 chibi。

返工中另发现两处更严重的问题并一并修掉：

- **锚点越界**：锚点是原图像素坐标，原按 Qwen 大图测得（`[364,1138]`），换到 Z-Image 的 768×1024 画布后落到图外（锚点 y=878 而图高 779），地图上人物会悬空/偏位。已按当前 matted 图重测，12 条锚点全部落在位图内。
- **缩放键用错**：portrait 由 `width:300` 改回旧人主流的 `height:600`，chibi 改 `height:116` 并补 `bodyCompress`（split=脚底×0.42，factor 0.64）。改后 portrait 宽度 231–321，落在旧人 206–346 区间内。

**本次目检实际核对项**（未列的项即未验）：

- 莺儿 portrait：性别年龄（十三四岁少女·双丫髻）、半身取景、工笔淡彩画风、朝向 —— 4 项均核对。
- 莺儿 chibi：头身比（2–3 头身）、头到脚完整、五官可辨、朝向 —— 4 项均核对。
- 朝向不用目检定：改由 `scripts/facing_measure.py` 的 Vision 语义 landmark 实测（莺儿 portrait nose +0.2925 / mouth +0.1643 → right），写入 `character-facing.json` 的 `evidence`。Q 版约 50px 宽测不到脸，按同提示词立绘同向**推定**，`method` 记 `visual-review`。

## 交接

- 第八回已随 `src/story.ts` 的 `script8`/`sections8`、新 cast（ying_er）与 `bookNames[8]` 一并上线。
- 无遗留阻塞项；后续如需补 `chapter08-evidence.json` 原文证据表可单独追加，不影响门禁。
- 新增人物管线的四条纪律（同模型、重画必重测锚点、缩放用 height、朝向实测）已沉淀进 [美术规范](production/art.md)，避免下一回再犯。
