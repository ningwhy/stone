# 第 23 回制作记录

## 目标与来源

- **回目全名**：第二十三回　西厢记妙词通戏语　牡丹亭艳曲警芳心
- **底本/版本/来源地址/取得日期**：
  - 版本：维基文库《紅樓夢》第 023 回，程乙本/高鹗本整理稿（繁体）
  - 来源地址：<https://zh.wikisource.org/w/index.php?title=紅樓夢/第023回&action=raw>
  - 取得日期：2026-11-15（首次抓取遭维基限流，退避 20 秒后重取成功）
  - 处理：`scripts/fetch_chapter_source.py 23` → OpenCC t2s 转简体，去导航/样式/许可页脚，按维基段落拆行；正文未作增删
- **本地正文**：`docs/chapter23-source.txt`（5429 字 / 16707 字节 / 29 段）
- **剧情、段落、证据**：`design/chapter23-story.json`、`chapter23-sections.json`、`chapter23-evidence.json`
- **生成器**：`scripts/build_chapter23.py`（**第 20 回确立的「句号索引」切片法**：正文与 `paragraphLead` 全部从底本切出，写盘前自校，失败即退出不落盘）
- **本回开始/结束、与前后回衔接**：
  - 接第 22 回（元春灯谜、贾政悲谶）→ 元春归宫后命勒石题咏，再命众人入住大观园
  - 止于黛玉听《牡丹亭》落泪、被袭人一掌打断（「且听下回分解」），第 24 回的起手
- **实际出场 / 转述人物**：
  - **有台词登场**：贾元春（叙述中发谕，无一句直接台词）、凤姐、贾琏、贾政、王夫人、贾母、宝玉、黛玉、探春、惜春、迎春、贾环、赵姨娘、袭人、茗烟、金钏儿、彩云、贾芹
  - **提及未登场**：夏守忠（传旨太监，沿用第 16 回 `messenger` 的处理）、宝钗、李纨、彩霞、绣鸾、绣凤、贾芸（芸儿）、贾珍、贾蓉、贾萍、贾蔷、贾菖、贾菱、十二个女戏
  - **只在叙述里被提及、无台词不上台**：周氏（贾芹之母，来求凤姐并得了信；底本只写她「坐轿子来求凤姐」一句，凤姐命人告诉贾琏去回话，她并未现身，因此不进 cast）
- **梦境 / 现实 / 回忆场景**：全回为 `present` 现实层，无梦境、无回忆

---

## 事件覆盖表

| 原文起句或事件 | 时间层 | 段落 / 节点 | 地点/scene | 在场人（speaker） | 压缩/改写说明 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 元春命勒石题咏，贾珍督工 | present | `c23-ledong` / C23-001…008 | `dinner` 贾母院后房 | 叙述 | 底本只写勒石监工，无人登场；探春奉命抄录只作叙述 | 已上线 |
| 凤姐献计：小沙弥道士送铁槛寺 | present | `c23-tiejian` / C23-009…021 | `jialian_home` | 叙述、凤姐、贾政 | 凤姐先与王夫人商、与贾政商，再拉贾琏教话 | 已上线 |
| 贾琏领银、贾芹往铁槛寺 | present | `c23-jiaqin` / C23-022…047 | `jialian_home` | 叙述、凤姐、贾琏 | 贾芹领二三百两、雇车往铁槛寺 | 已上线 |
| 元春下谕：命宝钗等入住大观园 | present | `c23-yuci` / C23-048…055 | `dinner` | 叙述 | 太监夏守忠沿用 `messenger`；谕由叙述转述 | 已上线 |
| 宝玉听了喜，又怕贾政 | present | `c23-jingong` / C23-056…066 | `dinner` | 叙述、贾母 | 「一步挪不了三寸」「扭股儿糖」 | 已上线 |
| 金钏儿奚落，彩云推开；贾政训斥宝玉「作业的畜生」 | present | `c23-jiaozheng` / C23-067…108 | `wang` 王夫人院 | 叙述、金钏儿、彩云、贾政、王夫人、宝玉、袭人 | **本回新登场的两个丫鬟**在此登场；「袭人是何人」「花气袭人知昼暖」一段完整保留 | 已上线 |
| 宝玉问黛玉住哪，商量潇湘馆 | present | `c23-fenju` / C23-109…120 | `dinner` | 叙述、黛玉、宝玉 | 「爱那几竿竹子隐著一道曲栏」 | 已上线 |
| 贾政遣人分派居所 | present | `c23-fenju`（同段） | `dinner` | 叙述 | 七人居所逐个报出（蘅芜苑/潇湘馆/缀锦楼/秋爽斋/蓼风轩/稻香村/怡红院） | 已上线 |
| 宝玉园中快乐，作四首即事诗 | present | `c23-sishi` / C23-121…150 | `yihong` | 叙述 | 四首诗按底本逐首切出，不合改 | 已上线 |
| 宝玉闷，茗烟买书 | present | `c23-mingsmoke` / C23-151…159 | `yihong` | 叙述 | 茗烟买「飞燕、合德、武则天、杨贵妃外传」 | 已上线 |
| 桃花底下共读《会真记》 | present | `c23-taohua` / C23-160…177 | `qinfang`（新建） | 叙述、宝玉 | 「落红成阵」一段，风吹桃花落满身书地 | 已上线 |
| 黛玉担花锄来，扫花入冢 | present | `c23-huizhen` / C23-178…191 | `qinfang` | 宝玉、黛玉 | 黛玉「撂在水里不好」，要扫进花冢 | 已上线 |
| 黛玉偷看《会真记》，宝玉说「多愁多病身」 | present | `c23-madou` / C23-192…214 | `qinfang` | 宝玉、黛玉、叙述、袭人 | 「倾国倾城貌」「苗而不秀」「银样镴枪头」 | 已上线 |
| 掩埋落花，袭人唤宝玉回去 | present | `c23-madou`（同段） | `qinfang` | 宝玉、黛玉、袭人 | 大老爷身上不好，老太太打发他去 | 已上线 |
| 黛玉行至梨香院墙角，听《牡丹亭》 | present | `c23-mudanting` / C23-215…230 | `c4_lixiang` | 叙述 | 「原来姹紫嫣红开遍」「良辰美景奈何天」「如花美眷，似水流年」 | 已上线 |
| 黛玉心痛落泪，被袭人一掌打断 | present | `c23-luoye` / C23-231…236 | `c4_lixiang` | 叙述 | 「正是：妆晨绣夜心无矣」 | 已上线 |

---

## 地图、人物、资产

| ID | 新建或复用 | 来源或生成器 | 尺寸/锚点/脸部参考 | 状态 | 证据截图 |
| --- | --- | --- | --- | --- | --- |
| `qinfang` | **新建** | `scripts/build_chapter23_maps.py` | 40×40 / 等距 128×64 / 9 锚点 / 3 条动线 / 桃林、闸墩、坐石、山子石、芦苇、粉墙围出的花冢凹角 | **已完成** | `maps/qinfang.tmj`（351 个路线锚点全通） |
| `jialian_home` | 复用（第 21 回新建） | `scripts/build_chapter21_maps.py` | 40×40 / 10 锚点 | 可直接用 | — |
| `dinner` | 复用 | `scripts/build_chapter_maps.py` | 40×40 / 贾母院后房 | 可直接用 | — |
| `wang` | 复用 | `scripts/build_chapter_maps.py` | 40×40 / 王夫人院东廊三间 | 可直接用 | — |
| `yihong` | 复用（第 21 回新建） | `scripts/build_chapter21_maps.py` | 40×40 / 16 锚点 | 可直接用 | — |
| `c4_lixiang` | 复用（第 4 回新建） | `scripts/build_chapter_maps.py` | 40×40 / 梨香院 | 可直接用 | — |
| `jinyuan`（金钏儿） | **新增人物** | 渲染机 `192.168.4.66` ComfyUI 0.45.0（qwen21 t2i + bg-removal，seed 10234090/10234091） | 立绘 600（214×600）/ Q 版 116（75×116） | **已完成** | `public/assets/rongguo/jinyuan-{portrait,chibi}.{png,webp}` |
| `caiyun`（彩云） | **新增人物** | 同上（seed 10234100/10234101） | 立绘 600（166×600）/ Q 版 116（64×116） | **已完成** | `public/assets/rongguo/caiyun-{portrait,chibi}.{png,webp}` |
| `jia_qin`（贾芹） | **新增人物** | 同上（seed 10234110/10234111） | 立绘 600（192×600）/ Q 版 116（60×116） | **已完成** | `public/assets/rongguo/jia_qin-{portrait,chibi}.{png,webp}` |
| `zhou_shi`（周氏） | **不登记** | — | — | **不上台** | 底本只写她「坐轿子来求凤姐」一句，无台词无动作，全回只在叙述里被提及；进 cast 就要配资产，不值当 |
| `caixia`（彩霞） | 复用/提及 | 底本只写名字，无台词无动作 | — | **不登记**（见「禁止误加入场」） | — |
| `xiu_luan`/`xiu_feng` | 提及 | 底本只写名字 | — | **不登记** | — |

- **地图维护方式**：脚本为主（`scripts/build_chapter23_maps.py`，照 `build_chapter21_maps.py` 的写法，幂等重写 `maps/qinfang.tmj`）
- **重建命令及覆盖清单**：
  ```bash
  python3 scripts/build_chapter23_maps.py   # 覆盖 maps/qinfang.tmj
  python3 scripts/build_chapter23.py         # 覆盖 design/chapter23-{story,sections,evidence}.json
  npm run check:anchors                      # 新地图必跑
  ```
- **备份路径**：`maps/` 在 git 内，无独立备份；脚本重写前先 `git status` 确认工作树干净
- **GPU 在途任务、prompt_id、服务器、待轮询内容**：无
- **已归档旧图、新 seed、入选结果**：
  - 设计表：`art/identity/character-designs.json` 追加三人（seed 10234090 / 10234100 / 10234110，其后各自 +1 是 Q 版）
  - 源图：`art/source/{jinyuan,caiyun,jia_qin}-{portrait,chibi}_s*.png`（各一张入选，未淘汰）
  - 抠图：`art/matted/*-sam.png`（SAM 过一遍，边缘干净）
  - 校准：`art/calibration.json` 六条；chibi 带 `bodyCompress`（split ≈ 0.42×feet_row，factor 0.64）
  - 朝向：三人的**立绘**由 Vision 语义地标测出（各 3 票一致，jinyuan 朝左、caiyun/jia_qin 朝右）；
    三人的 **Q 版** 检测器在任何裁切、任何倍率、乃至 768×1024 的原始 matte 上都读不出人脸
    （Q 版大头身画风不在 Vision 的拟合范围内），改走目视裁决：判读标准先在
    `cui_lv-chibi`（朝右）与 `jia_rong-chibi`（朝左）上标定——鼻嘴落红线右侧为朝右、
    左侧为朝左；三个新 Q 版的鼻嘴基本落在眼中点上、极轻微右偏，且整身姿态是正面站姿
    （朝左标尺是明显侧身），故记为朝右。裁决写入 `scripts/build_facing.py` 的 `REVIEWED`
  - 面部框：立绘三张由自动检测全部偏离，改为带坐标网格的放大图目视重标；
    `caiyun-chibi`／`jia_qin-chibi` 自动检测报「no face candidate found」，手工标注；
    `jinyuan-chibi` 的自动框下沿落到 70（压进衣领），按既有 chibi 规范（59~60，下巴线）
    重标为 62。六条都写进 `inspect_face_boxes.py` 的 `REVIEWED` 防重跑打回

---

## 原著约束与设计推定

- **明示证据**：
  - 回目联「西厢记妙词通戏语　牡丹亭艳曲警芳心」——底本段 0
  - 「沁芳闸桥边桃花底下一块石上坐著」——段 22，**本回新建地图的直接依据**
  - 「肩上担著花锄，锄上挂著花囊，手内拿著花帚」——段 23，黛玉落花冢的形象
  - 「刚走到梨香院墙角上，只听墙内笛韵悠扬，歌声婉转」——段 27，**复用 `c4_lixiang`（梨香院）的直接依据**
  - 「原来姹紫嫣红开遍」「良辰美景奈何天」「则为你如花美眷，似水流年」——段 27，《牡丹亭》原句
  - 七人居所逐个点名——段 10
  - 「花气袭人知昼暖」——段 9，袭人名字的来历
- **转述/回忆**：无回忆场景；元春的谕、贾政的分派都是转述，由叙述者说出，不安排元春登台
- **位置、距离、衣饰、年龄的推定与其他解释**：
  - **凤姐献计一段的地点**：底本只说「便坐轿子来求凤姐」，未言何处。凤姐在贾琏院吃饭（第 22 回即在 `jialian_home`），本回沿用同一处
  - **贾政训宝玉的地点**：底本明写「可巧贾政在王夫人房中商议事情」，用 `wang`（王夫人院）
  - **分派居所的地点**：底本说「就有贾政遣人来回贾母说」，在贾母处，用 `dinner`
  - **金钏儿、彩云的站位**：底本写「都在廊檐底下站著」，在王夫人房外廊，仍用 `wang`
  - **茗烟买书的地点**：底本说「便走去到书坊内」后回怡红院，用 `yihong` 演他带书回来
  - **「四个丫头」**：底本只说每处添两个老嬷嬷、四个丫头，不点名，不具象化
  - **夏守忠**：底本点名。cast 里没有太监，第 16 回「六宫都太监夏守忠降旨」已用 `messenger` 承载，本回沿用同一处理，**不新增角色，也不把 `messenger` 说成是夏守忠**
- **未解决争议**：
  - 第 23 回的「四首即事诗」究竟是不是宝玉作，学界有讨论。本回按底本叙述（"他曾有几首即事诗"）呈现，不加评点
  - 「花气袭人知昼暖」是陆游《村居书喜》句。底本引作「古人有一句诗云」，本回照录，不改出处
- **禁止误加入场的人物或事件**：
  - **彩霞、绣鸾、绣凤**：底本只列为「众丫鬟都在廊檐底下站著」的名单，三人无台词无动作。**本回不为她们立绘、不注册 cast**，只在叙述里点名
  - **宝钗、李纨**：段 10 只是被分派住处的名字，无台词。宝钗在前 22 回已有戏份与资产，本回仍只作叙述提及，**不上台**
  - **贾芸（芸儿）**：凤姐承诺日后让他管种树工程。底本只写「我管保叫芸儿管这件工程」这一句承诺，事未发生。**本回不给贾芸立绘**，只作提及
  - **十二个女戏**：唱《牡丹亭》的是梨香院十二个女戏，但本回只从墙外听声，**不安排任何女戏登台**（与第 18、22 回「点戏四出」的处理不同——那两回戏在台上）
  - **元春**：全回在宫中，**不登台**
  - **周氏**：凤姐允了周氏所求，但周氏只「来求凤姐」一句，无台词。周氏若要登场须与贾芹同时；若只按「来求凤姐」处理，可以用叙述带过（见下方设计决定）

---

## 接入与兼容

- **story、sections、bookNames、顶部回组**：
  - `src/story.ts`：`import script23` / `sections23` → `story` 末尾追加 → `chapters` 追加并 `.map(s=>({...s,book:23}))` → `bookNames` 加 `23:"第二十三回"`
  - `design/chapter-titles.json`：`books["23"] = {first:"西厢记妙词通戏语", second:"牡丹亭艳曲警芳心"}`
  - `scripts/check_content.mjs`：`VERBATIM_BASE` 加 `23`
  - `design/scene-places.json`：补 `qinfang` 条目
- **本回总览/行迹策略、首次定位**：`qinfang` 属 `daguanyuan` 层（与 `yihong` 同层），`scene-places.json` 里 level=`daguanyuan`、region=`capital`
- **新演员注册与配对资产**：新资产须**先进 manifest 再注册 cast**（顺序反了图鉴断言立刻挂）。`tests/character-identities.mjs` 断言 `images.length===castCount`
- **存档版本、旧中段、新增演员、旧终幕迁移**：`engine.ts` 现为 v5。追加新回只增加尾部节点，不改既有节点 ID；旧档落在既有节点上仍可恢复。**新增演员须在 restore 时补不可见初态**（沿用第 21、22 回的做法）。第 22 回的封底「开启下一回」在第 23 回上线后必须指向第 23 回——由 `leaves.ts` 的 `chapterLeaf(nextBook)` 自动派生，**不写死**
- **文案、统计与回归测试变更**：
  - `tests/browser-smoke.mjs` 的「查无此人」样本：当前是 `彩云`，**它在第 23 回会登场 → 必须换**。候选（已核查 `design/`、`src/`、`docs/chapter*-source.txt` 零命中）：`坠儿`/`佳蕙`/`翠墨`/`佩凤`/`偕鸾`/`文杏`/`春燕`/`小红`/`芳官`/`素云`/`碧月`/`小螺`/`入画`/`侍书`/`绣橘`/`司棋`/`藕官`/`蕊官`/`葵官`/`豆官`/`艾官`/`宝官`/`玉官`
  - `src/App.tsx` 的 `bookScope` 已按 `bookNames` 算法派生（`src/cnNumber.ts`），**新增回不用改**
  - 封底「终幕」只标在全书末节点（`state.index===story.length-1`），第 23 回上线后全书末节点变成第 23 回末节点，**「全书至此」应改由数据判定而非写死**（第 22 回已抽 `tests/lib/backcover.mjs`）

---

## 验证结果

| 命令/人工检查 | 日期 | 实测结果 | 输出或截图路径 |
| --- | --- | --- | --- |
| `npm run check:content` | 2026-11-16 | 通过 — 1924 节点 / 198 段 / 46 图 / 81 人 / 284 资产；回目节点数 `{"22":218,"23":236}`；1007 条证据 | — |
| `npm run check:anchors` | 2026-11-16 | 通过 — 351 个路线锚点全部可通行且两两连通（36 个装饰锚点不计入） | — |
| `npx tsc --noEmit` | 2026-11-16 | 通过（exit 0，无输出） | — |
| `npm test` | 2026-11-16 | 通过 — 84 项全绿，0 失败 | — |
| `npm run test:locator` | 2026-11-16 | 通过 — 45 个场景已映射；章回触发、天下层推镜 vs 府内下钻、跳过/自动关闭/设置开关、点击不被吞、121 帧动画全部验证 | — |
| `npm run build` | 2026-11-16 | 通过 — `prune_dist: removed 284 PNG files (61.4 MB), 0 kept without WebP` | `dist/` |
| `node tests/verify-album-title.mjs` | 2026-11-16 | 通过 — 面板标题「前二十三回 · 人物图鉴」，图鉴 81 人（含金钏儿、彩云、贾芹），金钏儿立绘 214×600 已绘出 | `artifacts/` |
| 第 23 回定向浏览器测试（`tests/chapter23.mjs`） | 2026-11-16 | 通过 — 14 段全部推进，落点与场景逐段一致；6 张场景图（含新建 `qinfang`）全部走到；目录搜「西厢记」只命中 `c23-*`；封底为全书末回形态；236 个节点正文逐字出自底本 | `artifacts/c23-*.png`（15 张） |
| `npm run test:browser`（browser-smoke） | 2026-11-16 | 通过 — 354 节点 / 46 图全通，跨场景存档恢复、离屏揭示、自然移动、暂停、设置、图鉴、稳定地图区、最小可读精灵与标签、缩放命中区、总览浏览、暂停estate travel、1440×900 / 1280×720 / 390×844 三视口控件可见、坏档恢复 | — |
| `node tests/character-art-qa.mjs` | 2026-11-16 | 通过 — 81 张立绘去重无重复、脚底偏差 0px、层级遮挡正确 | — |
| 浏览器三视口/暂停/存档 | 2026-11-16 | 通过 — 由 browser-smoke 覆盖（三视口 + 跨场景存档恢复 + 暂停） | — |
| 面部灰度与配对/暗底/锚点 | 2026-11-16 | 通过 — 284 条资产 PNG/WebP **284/284 成对**，hash 全在；六条新资产 faceBox 与 `auto-face-boxes.json` 完全一致（`jinyuan-portrait` [78,22,128,72] / `jinyuan-chibi` [13,27,62,62] / `caiyun-portrait` [46,38,88,82] / `caiyun-chibi` [9,30,59,64] / `jia_qin-portrait` [63,42,107,82] / `jia_qin-chibi` [7,30,57,64]） | `public/assets/rongguo/manifest.json` |
| Tiled 应用目检 | 2026-11-16 | 通过 — `qinfang` 经 Tiled 官方渲染器 + 运行时截图双重确认：桃林成片、闸墩、坐石、山子石、芦苇、花冢、桥、水面均正常；底本三要素「桃林／水／闸桥」都能入画 | `/tmp/qinfang-tiled.png`、`artifacts/c23-c23-taohua.png` |
| 部署 | 2026-11-16 | 通过 — `rsync -az --delete dist/ lighthouse:/www/wwwroot/stone.new/` → `cd /www/wwwroot && rm -rf stone.prev && mv stone stone.prev && mv stone.new stone && chown -R www:www stone` → 回环 `curl -sk -H 'Host: stone-direct.yan.pub' https://127.0.0.1/` 返 **200**；`stone.prev` 留作备份 | — |
| 线上复验（`stone-direct.yan.pub`） | 2026-11-16 | 通过 — 目录里有第二十三回、14 段；14 段逐段推进落点与场景全对，6 张场景图（含新建 `qinfang`）全走到；封底为全书末回形态（「全书至此，砖石犹温。」，无「开启下一回」）；图鉴 81 张立绘全画得出来（含金钏儿、彩云、贾芹）；非 403 失败请求 **0**；页面无 JS 错误 | `artifacts/direct-c23-back-cover.png` |

---

## 交接

- **已完成**：
  - 底本抓取与落盘（`docs/chapter23-source.txt`）
  - 底本 29 段的**句号索引**全量核对（已打印每段每句，供切片用）
  - cast 缺口盘点（缺 `jinyuan`/`caiyun`/`caixia`；`ming_yan` 已有资产）
  - 45 张现有地图的 sceneId 与锚点盘点（**无桃花/落花/水闸场景 → 必须新建**）
  - 「查无此人」样本候选核查（24 个候选名全量零命中）
  - 历史处理先例核查：金钏儿（第 7 回）、贾芹（第 13 回）此前只作旁白提及、未立绘；「绣凤」（第 18 回）是「绣凤版舆」的误配，不是人名
  - 地图生成器 `scripts/build_chapter23_maps.py` → `maps/qinfang.tmj` → `npm run check:anchors` 通过
  - 剧情生成器 `scripts/build_chapter23.py` → `design/chapter23-{story,sections,evidence}.json`（**236 节点 / 14 段 / 249 证据**，子句级切分，写盘前自校）
  - 三名新角色美术全流程：渲染机生成 → SAM 抠图 → 校准 → manifest → facing → faceBox 重标
  - 接入：`src/story.ts` / `chapter-titles.json` / `check_content.mjs` / `scene-places.json` / `browser-smoke.mjs` 样本
  - 新增 `tests/chapter23.mjs`（定向验收）与 `tests/online-chapter23.mjs`（线上复验）
  - 全链路验收通过 → 部署 → 线上复验通过（详见上方「验证结果」表）
- **未完成及原因**：无。第 23 回已上线。
- **后续可选工作**（不属于本回）：
  1. 第 24 回《醉金刚轻财尚义侠　痴女儿遗帕染相思》——底本与切分方式照第 23 回办
  2. 仍然缺的两张大地图：**大观园全景**与**省亲正殿**
  3. `design/atlas-maps.json`（读者可交互总览）仍有 29 张图未接入，与既有回一致，本项目前不接
- **给下一位 agent 的续作提示词**：
  > 继续第 24 回制作。底本从维基文库《紅樓夢》第 024 回抓取（`scripts/fetch_chapter_source.py 24`）。生成器照 `scripts/build_chapter23.py` 的结构改写：**正文与 paragraphLead 都从底本切出，写盘前自校**；`(段号, 句/子句号)` 全局严格递增；**舞台连续性自检（只查 move）必须保留**——引擎只在换场景时清空舞台，同场景可见性保持，「move 一个从没 show 过的人」会在读者点到那步才抛。**切分粒度按底本句长定**：第 23 回底本句子偏长，用的是子句级 `(?<=[。！？；，：、])`，且**索引粒度必须与 CUTS 粒度一致**，否则切分点对不上。闭合引号（`”’」』`）必须归入前一个子句。新建地图后**必须跑 `npm run check:anchors`**（路线锚点必须可通行且两两连通；装饰锚点不算问题；修法取「挪家具」而非改路线表）。新角色资产**先进 manifest 再注册 cast**。新 scene 必须补 `design/scene-places.json`，否则定位转场门禁拦。`tests/browser-smoke.mjs` 与 `tests/toc.test.ts` 的「查无此人」样本**每加一回就要重选**（当前样本 `侍书`，第 23 回起；候选：坠儿/佳蕙/翠墨/佩凤/偕鸾/文杏/春燕/小红/芳官/素云/碧月/小螺/入画/绣橘/司棋/藕官/蕊官/葵官/豆官/艾官/宝官/玉官，已核查零命中）——判据要覆盖**所有可搜路径**（正文/标题/地点/在场人物/段 id），只查正文不够，第 23 回的 `檀云` 就是被底本原句「室霭檀云品御香」推翻的。**Q 版朝向**：Vision 对大头身画风可能完全失效（读不出人脸），此时改走项目既有的「目视 + 双向标尺 + 全身姿态交叉验证」，裁决写进 `scripts/build_facing.py` 的 `REVIEWED`；**标尺必须双向**（只用朝右样本无法区分「符号规则」与「巧合」）。改 facing 一定要跑 `build_facing.py` + `build_facing_doc.py`，否则 check:content 报 out of date。
