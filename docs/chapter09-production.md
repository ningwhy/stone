# 第九回制作记录 · 恋风流情友入家塾 起嫌疑顽童闹学堂

> 状态：**已完成并接入** —— 全流程通过内容门禁、单元/集成测试与生产构建。

## 目标与来源

- 回目全名：第九回 · 恋风流情友入家塾 · 起嫌疑顽童闹学堂
- 底本：维基文库《红楼梦/第9回》；本地正文：`docs/chapter09-source.txt`（已备齐）
- 剧情、段落：`design/chapter09-story.json`（17 节点）、`design/chapter09-sections.json`（5 段：c9-enter / c9-roll / c9-plot / c9-clash / c9-quit）
- 衔接：紧接第八回；秦钟入贾家家塾，学堂风波起，茗烟闹学堂、李贵喝止。

## 事件覆盖表（完成）

| 原文起句或事件 | 时间层 | 地点/scene | 在场人 | 状态 |
| --- | --- | --- | --- | --- |
| 秦钟入贾府家塾，宝玉荐于代儒 | present | c9_school（家塾） | 宝玉、秦钟、贾代儒 | 已完成 |
| 薛蟠亦在学中，结交香怜、玉爱 | present | c9_school | 薛蟠、香怜、玉爱 | 已完成 |
| 贾瑞代管学堂，图私利不公 | present | c9_school | 贾瑞、金荣 | 已完成 |
| 金荣起衅，茗烟助宝玉闹学堂 | present | c9_school | 金荣、茗烟、宝玉、李贵 | 已完成 |
| 李贵喝止，金荣赔礼散学 | present | c9_school | 李贵、金荣、宝玉、秦钟 | 已完成 |

## 地图、人物、资产

| ID | 新建或复用 | 来源 | 状态 |
| --- | --- | --- | --- |
| c9_school（家塾） | **新建场景** | `scripts/build_chapter09.py` 写入 `maps/c9_school.tmj` | theme=interior，8 锚点（gate/yard/hall/teacher/desk_a/desk_b/desk_c/door），复用 writing-desk/official-chair/bookshelf/flower-gate/garden-tree |
| qin_zhong 秦钟 | 新人物·已立绘 | Z-Image turbo + `generation-plan.json` 风格锚点（与旧 45 人同一管线）+ qwen21 抠图硬化 | portrait + chibi 已入 manifest |
| jia_rui 贾瑞 | 新人物·已立绘 | 同上 | 已入 manifest |
| jin_rong 金荣 | 新人物·已立绘 | 同上（返工一次：初版被画成成年男子，改「十二三岁、稚气未脱、脸颊带婴儿肥」后重画） | 已入 manifest |
| ming_yan 茗烟 | 新人物·已立绘 | 同上 | 已入 manifest |
| li_gui 李贵 | 新人物·已立绘 | 同上 | 已入 manifest |
| xuepan 薛蟠 | 复用 | 第四回已建 | 已存在 |

- 家塾主题用既有 `interior`（已有 bgm-interior），未新建 `study` 主题，避免 check:content 音频门禁报「map themes with no piece」。
- 新增 5 名立绘人物（秦钟/贾瑞/金荣/茗烟/李贵），走与旧 45 人相同的管线：Z-Image 出图 → qwen21 抠图硬化 → 重测锚点校准 → WebP 入册。
- 本回大量使用 `effect(actor,'anger')`（怒形于色，引擎新增红色光环视觉）与 `idle` 节拍。

## 验证结果（接入后）

- `npm run check:content` → **通过**：709 节点 / 67 段 / 30 地图 / 51 人物 / 219 资产；第九回计数为 17 节点。
- `npm test` → **64/64 通过**。
- `npm run build` → **tsc 无错 + vite 构建成功**；运行时美术资产以 WebP 交付。
- `npm run map:framing` → **0 处取景问题**（c9_school 取景经校验）。
- `npm run test:browser` → **通过**：家塾场景、新人物图鉴（51 人含本回 5 人）、跨场景存读档全部 OK。

## 画风一致性返工（2026-10）

用户指出 7–9 回新人物画风与旧人物不一致。本回 5 人最初用 Qwen Image 2.1 + 水墨单色 + 全身站像，与旧 45 人（Z-Image turbo + 工笔重彩 + 半身）错配；已全部用旧管线重画。

- **金荣年龄错配**：初版描述写「十五六岁」但被画成成年男子。原著里他与秦钟、宝玉同在学堂，应约十二三岁；改描述重画后已为稚气男孩（见上表）。
- **锚点与缩放**：与第八回同源的两个问题（锚点按 Qwen 大图测得、换画布后越界；缩放键误用 `width`）已一并修正，本回 10 个资产锚点全部落在位图内，portrait 统一 600 高。
- **朝向**：不再靠目检（50px Q 版目检两次会给出相反答案），改由 `scripts/facing_measure.py` 实测。秦钟 right（nose +0.3398）、贾瑞 left、金荣 right、茗烟 left、李贵 right；贾瑞/金荣/茗烟鼻口偏移极小（<0.04）属近正面，朝向不影响观感。Q 版测不到脸，按同提示词立绘同向**推定**。

**本次目检实际核对项**（未列的项即未验）：

- portrait 6/6 已逐张核性别年龄、半身取景、工笔淡彩画风、朝向（莺儿、秦钟、贾瑞、金荣、茗烟、李贵）。
- chibi 4/6 已核头身比与完整性（莺儿、金荣、秦钟、李贵）；**茗烟、贾瑞的 Q 版未逐张目检**，仅经 `bodyCompress` 同参数处理并确认无空图。
- 抠图透明度：12 条均核对不透明占比（0.58–0.70），无空白抠图。

## 交接

- 第九回已随 `src/story.ts` 的 `script9`/`sections9`、5 条新 cast 与 `bookNames[9]` 一并上线。
- 无遗留阻塞项；后续如需补 `chapter09-evidence.json` 原文证据表可单独追加，不影响门禁。
- 新增人物管线的四条纪律（同模型、重画必重测锚点、缩放用 height、朝向实测）已沉淀进 [美术规范](production/art.md)，避免下一回再犯。
