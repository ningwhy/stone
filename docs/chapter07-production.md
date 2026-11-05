# 第七回制作记录 · 送宫花贾琏戏熙凤 宴宁府宝玉会秦钟

> 复制自 templates/chapter-brief.md，已替换为本回实际内容。状态与证据如实填写。

## 目标与来源

- 回目全名：第七回 · 送宫花贾琏戏熙凤 · 宴宁府宝玉会秦钟
- 底本：人民文学出版社《红楼梦》（庚辰本系统）；线上参考维基文库《红楼梦/第7回》。
- 本地正文：`docs/chapter07-source.txt`
- 剧情、段落、证据：`design/chapter07-story.json`、`design/chapter07-sections.json`、`design/chapter07-evidence.json`（证据表本轮暂缓，待底本校订后补）
- 本回开始/结束、与前后回衔接：紧接第六回刘姥姥去后；薛家已住进荣府梨香院（第四回迁入）；本回送宫花引出众女儿，宁府宴引出秦钟，为第九回家塾与第十六回秦可卿之死伏线。
- 实际出场 / 转述人物：
  - 出场：薛姨妈、周瑞家的、迎春、探春、惜春、王熙凤、平儿、王夫人、贾宝玉、林黛玉、袭人、雪雁、贾母、薛宝钗；宁府宴一段：贾珍、尤氏、贾蓉、秦钟、焦大（秦钟/贾珍/尤氏/焦大本轮为桩段，待立绘）。
  - 转述/未当场：贾琏（原文"贾琏戏熙凤于房中"，本轮以凤姐旁白带过，不置角色于场上）、智能儿（惜春玩笑提及）、金荣等学堂人物（第九回）。
- 梦境 / 现实 / 回忆场景：本回全现实。

## 事件覆盖表

| 原文起句或事件 | 时间层 | 节点 | 地点/scene | 在场人 | 压缩/改写说明 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 薛姨妈拿出十二枝宫花，托周瑞家的分送贾府众姊妹 | present | c7-xue-01.. | c7_lixiang（梨香院） | 薛姨妈、周瑞家的、宝钗 | 薛姨妈交代"迎春、探春、惜春每人一对，剩下四枝给凤哥、黛玉"；宝钗在旁因热毒养病不戴花 | 已规划 |
| 周瑞家的顺路先到三春处送花 | present | c7-san-01.. | c7_sanchun（三春院） | 迎春、探春、惜春、周瑞家的 | 惜春正与智能儿玩笑，说"明儿也剃了头同他作姑子去"；收下花 | 已规划 |
| 到凤姐院，凤姐白日与贾琏戏，平儿代收两枝 | present | c7-feng-01.. | c6_wangchui（凤姐院·feng_room） | 凤姐、平儿、周瑞家的 | 贾琏以旁白带过（无立绘），平儿替凤姐收花 | 已规划（贾琏待美术） |
| 到贾母院黛玉处，黛玉冷笑"别人不挑剩下的也不给我" | present | c7-dai-01.. | night（贾母院·daiyu_bed） | 黛玉、宝玉、袭人、雪雁、周瑞家的 | 黛玉问"还是单送我一个人的"，闻众人都有了，冷笑讽之 | 已规划 |
| 宁府宴，宝玉随贾母赴宁国府，会秦可卿之弟秦钟 | present | c7-ning-01.. | c5_ningfu（宁府·garden/bedchamber） | 宝玉、凤姐、贾蓉、秦钟、贾珍、尤氏 | 秦钟/贾珍/尤氏待立绘；本轮桩段 | 桩段（待美术） |
| 焦大醉骂"爬灰的爬灰，养小叔子的养小叔子" | present | c7-jiao-01.. | c5_ningfu | 焦大（及宁府众人转述） | 焦大醉后当众痛骂，众小厮捆起塞马粪 | 桩段（待美术） |

## 地图、人物、资产

| ID | 新建或复用 | 来源或生成器 | 尺寸/锚点/脸部参考 | 状态 | 证据截图 |
| --- | --- | --- | --- | --- | --- |
| c7_lixiang（梨香院） | 新建场景 | build_chapter07.py | estate-lixiang 壳 + 室内 props | 已规划 | 待 framing 门禁 |
| c7_sanchun（三春院） | 新建场景 | build_chapter07.py | estate-east 壳 + 室内 props | 已规划 | 待 framing 门禁 |
| c6_wangchui（凤姐院） | 复用 | 第六回已建 | feng_room / platform 锚点 | 已存在 | — |
| night（贾母院） | 复用 | 第三回已建 | daiyu_bed 锚点 | 已存在 | — |
| c5_ningfu（宁府） | 复用 | 第五回已建 | garden / bedchamber 锚点 | 已存在 | — |
| jia_lian 贾琏 | 新人物·待立绘 | ComfyUI 人脸管线 | 待生成 portrait/chibi + facing | 待美术 | — |
| jia_zhen 贾珍 | 新人物·待立绘 | ComfyUI 人脸管线 | 待生成 | 待美术 | — |
| you_shi 尤氏 | 新人物·待立绘 | ComfyUI 人脸管线 | 待生成 | 待美术 | — |
| qin_zhong 秦钟 | 新人物·待立绘 | ComfyUI 人脸管线 | 待生成 | 待美术 | — |
| jiao_da 焦大 | 新人物·待立绘 | ComfyUI 人脸管线 | 待生成 | 待美术 | — |
| xiang_ling 香菱 | 新人物·待立绘（甄英莲长大） | ComfyUI 人脸管线 | 待生成 | 待美术 | — |

- 地图维护方式：脚本为主（build_chapter07.py 自含 `scenes` 几何 + `build_map`）。
- 重建命令：`python3 scripts/build_chapter07.py`（只产出本回 tmj 与 json，不触碰其它回）。
- 备份路径：`artifacts/backups/2026-10-30-chapter07/`（构建前 `cp -a maps /tmp/maps-bak-<ts>`）。
- GPU 在途任务：本轮不生成新立绘；新人物美术由独立 ComfyUI 人脸任务批量生成后接入。

## 原著约束与设计推定

- 明示证据：送宫花顺序原著为"迎春、探春、惜春→凤姐→黛玉→（宝钗最后，因梨香院远）"；黛玉冷笑为原文名句；惜春"作姑子"玩笑明示。
- 转述/回忆：贾琏戏熙凤为原文明示（"贾琏戏熙凤于房中"），本轮以凤姐旁白表现，不强行置贾琏于场上。
- 位置推定：梨香院在荣府东北角（第四回薛家入住）；三春院位置依总览设计推定；宁府宴复用第五回宁国府地图。
- 未解决争议：送花收尾处宝钗为何"最后"——依原著梨香院较远，放在顺路末站。
- 禁止误加入场：智能儿、金荣、茗烟、李贵等第九回人物不得提前置于本回场上；秦钟本回仅宁府宴桩段出现，不展开家塾。

## 接入与兼容

- story、sections、bookNames、顶部回组：src/story.ts 显式 `import script7/sections7`、`story=[...script6, ...script7]`、`chapters=[...sections6.map(...,book:6), ...sections7.map(...,book:7)]`、`bookNames[7]="第七回"`。
- 本回总览/行迹策略：JourneyMap 自动从 story 派生场景列表，无需改 prequel-maps；行迹卡片名取自 tmj `title`/`place`。
- 新演员注册与配对资产：jia_lian 等六人需先经 ComfyUI 人脸管线生成 portrait/chibi + manifest + facing 后，再补入 cast 并接入桩段。
- 存档版本：当前 v4；第七回为追加，旧 v4 中段/终幕仍兼容（引擎以数组末节点判终幕，不按 END 字样）。新增演员接入时按架构.md 做缺字段补初态。
- 文案、统计与回归测试变更：README 覆盖范围更新至第七回；check:content 新增 chapter07-source.txt 与 chapter07-story/sections.json 引用。

## 验证结果

| 命令/人工检查 | 日期 | 实测结果 | 输出或截图路径 |
| --- | --- | --- | --- |
| npm run check:content | 2026-10-30 | 通过：669 节点、57 段落、29 地图、45 人物、207 资产；第七回 31 节点；无警告 | 命令输出 |
| npm test | 2026-10-30 | 64/64 通过（据新回更新了地图数与回数断言） | 命令输出 |
| npm run build | 2026-10-30 | 通过：tsc 0 错误，vite 构建成功 | 命令输出 |
| npm run map:framing | 2026-10-30 | 0 个取景问题（c7_lixiang / c7_sanchun 两张新图） | 命令输出 |
| npm run test:browser | 2026-10-30 | EXIT=0，全部通过；374 节点全程演出，三视口、暂停、存档、总览均正常 | artifacts/ 截图 |
| 引擎逐节点走查（临时脚本） | 2026-10-30 | 第七回 31 节点场景切换正确（c7_lixiang → c7_sanchun → c6_wangchui → night → c5_ningfu），在场人物均站在可通行格上，移动无报错 | 脚本已删除，结论已记入本表 |
| 面部灰度与配对/暗底/锚点 | — | 未检查（本回未新增立绘） | — |
| Tiled 应用目检 | — | 未检查 | — |

## 交接

- 已完成：送宫花主线（薛姨妈托花→三春→凤姐→黛玉）可运行实装，复用既有场景与人物；新建梨香院、三春院两处 40×40 舞台；已接入 `src/story.ts`（script7/sections7、bookNames[7]）与 `App.tsx` 原文说明；目录面板可按回分组到第七回、搜索可跨回命中。
- 未完成及原因：宁府宴/秦钟/焦大段为桩段，依赖 jia_lian/jia_zhen/you_shi/qin_zhong/jiao_da/xiang_ling 六人立绘（ComfyUI 人脸生成，本轮未执行 GPU 任务）；证据表 `design/chapter07-evidence.json` 待底本校订后补（check:content 只在证据表存在时强制每个节点有出处）。
- 下一步可直接执行的文件和命令：
  1. `python3 scripts/build_chapter07.py`（只重出本回地图与 JSON，不触碰其它回）
  2. 新立绘到位后：补 `src/story.ts` 的 cast 条目 → 在 `scripts/build_chapter07.py` 的 c7-ning / c7-jiao 段把旁白改为 show/speak → 重跑生成器
  3. `npm run check:content && npm test && npm run build && npm run map:framing`
- 给下一位 agent 的续作提示词：见 docs/chapter07-production.md「未完成」与 docs/chapter08/09-production.md 的事件覆盖表；第八、九回的生成器骨架在 `scripts/build_chapter08.py`、`scripts/build_chapter09.py`，产物暂存在 `artifacts/staging/`，接入时把 `STAGE_DIR`/`PUBLISH_MAP` 改回 `design/` 与 `maps/`。
