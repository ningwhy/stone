# 下一回从立项到接入

下文用 `NN` 表示目标回两位编号，`N` 表示数值回号。模板路径需替换后再使用。当前工程没有第四回内容；示例不是第四回原文，也不会自动成为运行剧情。

## 1. 创建制作记录并拆原文

复制 [回目记录模板](templates/chapter-brief.md) 到 `docs/chapterNN-production.md`。读上一回结尾和目标回全文，按 [考据规范](research.md) 保存底本、证据表、事件覆盖清单。列出实际场景、叙事时间层、新/复用人物、出场顺序与哪些人只是被提及。

先产出一条可验证的最小演出：一个段落、两个讲话人、一段经过门洞的移动、一次场景切换。复用既有画风样本和校准资产，确定新地图能走通后再量产。

## 2. 设计稳定 ID

- 新回节点建议 `C04-001`、`C04-002`；段落建议 `c4-opening`；场景如 `c4_yamen`，人物用既有 ID 或新的稳定拼音 ID。
- 不重命名旧节点。第三回目前存在 `P001`、`A001` 等早期 ID 和旧终幕 `END`，它们也是存档标识。
- `StoryStep.chapter` 是**段落 ID 字符串**，`source.chapter` 才是**原著回数整数**；不要混写。
- `scene` 必须与 TMJ 的 `sceneId` 相同；`focus` 和 `at`、`via` 中每个名字必须是该图 Anchors 里的名称。

## 3. 写剧情和段落 JSON

以下是结构示例，台词、出处和坐标名必须用目标回实际内容替换：

```json
{
  "id": "C04-001",
  "chapter": "c4-opening",
  "scene": "c4_stage",
  "title": "本段事件标题",
  "place": "当前地点",
  "focus": "guest",
  "speaker": "narrator",
  "text": "依据目标回改写的叙述。",
  "actions": [{"type": "show", "actor": "yucun", "at": "guest"}],
  "source": {
    "chapter": 4,
    "paragraphLead": "目标回原文对应段落的准确起句",
    "textKind": "adaptation",
    "layer": "present"
  }
}
```

段落文件每项：`{"id":"c4-opening","title":"本段名称","scene":"c4_stage","start":"C04-001","book":4}`。全部节点/段落 ID 全局唯一，段落起点所属回数和场景必须一致。

| 动作 | JSON | 运行含义 |
| --- | --- | --- |
| 登场 | `{"type":"show","actor":"yucun","at":"entry"}` | 直接站到可通行格心 |
| 移动 | `{"type":"move","actor":"yucun","via":["door","guest"]}` | 依次穿过命名地点，段间由四邻 A* 求路 |
| 同时移动 | `{"type":"parallel","moves":[…]}` | moves 只能是 move，同一人物不能同时走两次 |
| 离场 | `{"type":"hide","actor":"yucun"}` | 隐藏人物 |
| 屋顶/外观 | `{"type":"roof","visible":false}` | 切换现有外观显示规则，不自动拆楼 |
| 小动作 | `{"type":"effect","actor":"baoyu","kind":"jade","duration":1}` | 当前支持 jade / greet / rest，duration 为秒 |

动作数组顺序执行；一段 move 完成后才做下一个动作。要同步走路必须用 parallel。先 show 再 move，演员需已可见。切换 scene 会把全部人物隐藏，需要重新 show；同场景人物则会延续，离场要显式 hide。画外声用 `offscreen:true`，不为旁白或画外声音硬塞人物到图上。`mood` 目前没有独立表情集，不能写个 sad 就声称已有悲伤差分。

每个节点执行完动作后才显示稳定对白；移动期是行动模式，不存在单独的 `type:action` 剧情结构。引擎以数组最后一个节点判终幕，不按 ID 是否叫 END。

如果以脚本生成 JSON，新增回目自己的生成器，明示输出清单，记录到制作单。不要把新回剧情混进 `write_prequel.py` 再运行旧脚本覆盖前三回。

## 4. 接入地图与人物资产

按 [地图规范](maps.md) 创建 TMJ：独特 sceneId、40×40、128×64、必要对象层、格心 Anchors、合法走廊与碰撞。地图放 `maps/` 顶层会被自动发现；总览参考放子目录。新人物注册 `src/story.ts` 的 cast，提供 name/fullName/color/css/relation/description，并按 [美术流程](art.md) 交付成对图像。

新地图主题先检查 `MapScene` 支持的绘制分支，新的河岸不因 theme=river 自动适配任何码头坐标。旧 floor 主题存在固定花坛/河面位置，必须目检、必要时按地图配置扩展。

## 5. 修改所有回目入口

| 必改位置 | 工作 |
| --- | --- |
| `src/story.ts` | import 新 story/sections，按叙事顺序追加 story/chapters，bookNames 增加回名；保留 chapter3Story 供旧存档迁移 |
| `src/App.tsx` | 顶部分组 `[1,2,3]` 扩充；选择本回行迹或府内总览的条件不再只靠 `<3`；更新静态“前三回”标题与原文说明 |
| `src/JourneyMap.tsx` | 若使用新回行迹，为场景名称、图像与地点说明补元数据；它当前只 import prequel-maps，不能保证识别后回新场景 |
| `design/rongguo-world.json` / `WorldMap` | 仅在事件确实涉及府内既定道路时复用；跨城/回忆用行迹；定位 start 不能把第 N 回按钮跳回第三回 |
| `src/engine.ts` / `src/main.tsx` | 新演员与扩展剧情的存档兼容，见下节 |
| `tests/` | 扩全节点覆盖和新增地图/人物；原有回归继续通过，历史统计断言按范围调整 |
| `README`、制作记录 | 更新覆盖范围、素材数、限制和实测验证 |

目前总览 target 搜索明确限定第三回，且行迹说明依赖 prequel 数据。需要按回目有意识地选用，不要把所有后回也硬叫“荣国府总览”。不必为后回提前实现分支任务、战斗或服务器存档。

## 6. 明确存档迁移策略

当前 v3 是 `chapter:'first-three'`，旧 v2 仅第三回。restore 严格检查 index、node、最后节点 ended、所有 cast 状态；因此**只追加第四回也会使旧 v3 终幕不兼容，新增演员也会使旧 v3 缺字段**。

扩回需要版本化迁移，建议新格式 v4；保留 v2/v3 读取，用稳定 node ID 找新索引，验证旧记录再迁移；新增演员补不可见初态。旧 END 如不再是全书终幕，应迁成 reading，从旧终幕继续新回；不要提前删除旧存档键。保留旧历史与节点顺序，未知或损坏的节点明示回退。

必须覆盖：旧第三回中段 v2、旧前三回中段 v3、旧前三回终幕 v3、新回中段、新增人物、坏档拒绝且不破坏当前状态。迁移是下一回接入时应实现的工作，这里没有声称已实现 v4。

## 7. 自检、扩量、交接

先用 `npm run check:content` 查数据，再运行引擎自然走路与 skip 的一致性测试。通过最小段落后补全部剧情、美术、地点与行迹。按 [验收规范](verification.md) 检查每个稳定节点及至少一次自然移动、暂停、跳过、重载。

交付时用覆盖表说明本回每个事件/地点/人物的落点，给出截图与真实计数，明确原文推定和未完成工作。文件全在不等于一回已完成；缺图、路线穿墙、隐藏演员讲话、破坏旧存档，均不能列为完成。
