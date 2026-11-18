# 补两张缺图：大观园全景与省亲正殿（2026-11-18）

## 缺口从哪来

第 1–23 回全部上线后，唯一反复被记在「仍缺」一栏的是两张大舞台：

- **大观园全景** —— 第 17 回「大观园试才题对额」35 个节点全挤在 `dinner`
  （贾母院后房与晚膳）。读者看着贾政带宝玉在一间晚膳屋里游园题匾。
- **省亲正殿** —— 第 18 回元妃「换匾受礼」8 个节点借 `central`（荣禧堂）。
  读者看着元妃在贾政家的正房里升座受礼。

两回的制作记录都写明这是同一处缺口：「大观园正殿/行宫仍无专图，用 `dinner` 占位
（与第 17 回同一缺口，`daguanyuan` 图待补）」。

## 权威文件

| 文件 | 作用 |
| --- | --- |
| `scripts/build_daguanyuan_maps.py` | 两张图的生成源；形制依据与考据/改编取舍写在脚本头注释里 |
| `maps/daguanyuan.tmj` | 大观园全景（40×40，theme `garden`），8 锚点 |
| `maps/shengqin.tmj` | 省亲别墅正殿（40×40，theme `formal`），6 锚点 |
| `design/scene-places.json` | 两个新场景的方位（level `daguanyuan`、region `capital`） |
| `design/chapter17-story.json` / `-sections.json` | 35 节点 + 6 段的 `scene` → `daguanyuan` |
| `design/chapter18-story.json` / `-sections.json` | C18-063~070 + `c18-palace` 段的 `scene` → `shengqin` |

## 关键决定：只改 `scene`，锚点名一律沿用

第 17 回 35 节点的 `place` 分了 10 处景点，但 `actions[].at` 只用了 8 个锚点名
（全是 `dinner` 图的名字）；第 18 回受礼段用 `central` 的 6 个锚点名。
所以新图**直接沿用这些锚点名**，剧情只把 `scene` 字段改掉，`focus` / `at` / 正文
一律不动。这样：

- 零锚点重映射风险，`npm test`（全节点寻路）一次通过；
- 存档按 node id 定位，不受影响；
- 景点差异由旁白正文与画面景物承担，符合项目「叙事设计选择，非建筑复原」的既定口径。

★ **场景补进来必须真的被剧情用上**：`scripts/check_content.mjs` 第 258 行会拦
「方位表里有、但没有任何节点/段落使用的场景」。所以「只建图不接剧情」过不了门禁。

## 形制与资产

### 大观园全景（`daguanyuan`）

第十七回底本写「崇阁巍峨，层楼高起……一带清流，从花木深处泻于石隙之下」、
「迎面一带翠嶂挡在前面，白石崚嶒」。图上据此铺：

- 南北游览中轴：园门（牌坊）→ 翠嶂（湖石成片）→ 游廊 → 沁芳亭 → 正殿前月台；
- 一条清流从西北石隙斜贯东南，中轴以石板桥跨过；
- 东岸「有凤来仪」（竹门点潇湘馆）、「稻香村」（小比例厅舍），西岸沁芳亭与花木；
- 粉墙三面围合，南墙在园门处留洞。

资产：`taixu-gate`（牌坊）、`main-hall`/`rongxi-hall`（亭榭）、`bamboo-gate`、
`garden-tree`/`garden-rock`、`reeds`。未生新图。

### 省亲正殿（`shengqin`）

第十八回写元妃下轿看匾、「至行宫升座受礼」、荣国太君「自东阶升月台排班」。
图上一条南北中轴：牌坊（行宫外）→ 影壁 → 石阶 → 殿门 → 殿中御座，东侧另设东阶。

- 正殿用 `taixu-hall`（仙宫规格，1100×784，**此前未上过任何图**）——
  元春归省是全书规格最高的一场，民居正房压不住；
- 东西配殿、丹陛两侧花树按原文「两边排班」作对称；
- **正殿故意不题匾**——原文「此系正殿，外臣未敢擅拟」是情节，不可补匾；
- theme `formal`（板地庄重），与大观园的 `garden`（石地）区分。

## 踩过的坑

1. **取景**：初稿三处布景（`bamboo-gate`/`garden-tree`/`reeds`）摆在园子最西端，
   `npm run map:framing` 报「never in frame」——离任何锚点都超过一屏。
   把它们往沁芳亭锚点收 4–6 格后全绿。（`qinfang` 也有一条同类告警，是既有待清理项，
   不在本次范围。）
2. **写死的测试清单**：`tests/chapter18.mjs` 第 105/124 行写死了「七张复用舞台」的
   清单，把 `central` 换成 `shengqin` 后立刻红。按项目纪律改成**从 sections/story 实读**，
   而不是把清单里的 `central` 改成 `shengqin` 写死——否则下次再调场景又红。
3. **截图抓到转场那一帧**：探针等 400ms 就截图，抓到的是定位转场（点阵图 + 面包屑），
   不是舞台。`reducedMotion` 下转场终点停 900ms，必须等 `.scene-locator` 消失再截。

## 验收证据（2026-11-18）

```sh
python3 scripts/build_daguanyuan_maps.py     # 生成两张 TMJ
npm run check:anchors                        # 365 路线锚点全通（原 351，+14）
npm run map:framing                          # 新图 0 告警（qinfang 1 条既有项）
npm run check:content                        # 48 图，段落起始场景一致
npm test                                     # 97/97，全节点寻路通过
npx tsc --noEmit
npm run test:locator                         # 48 场景转场全覆盖
node tests/chapter18.mjs                     # 16 段 / 135 节点 / 8 舞台
```

浏览器实测（截图 `artifacts/newmap-*.png`）：

| 镜 | 场景 | 所见 |
| --- | --- | --- |
| C17-001 园门 | `daguanyuan` | 牌坊、翠嶂湖石、粉墙、Q 版贾珍/贾政 |
| C17-030 正殿 | `daguanyuan` | 完整大殿 + 翠竹花树、贾政/袭人/清客站位，旁白「这是正殿了」 |
| C18-063 行宫外 | `shengqin` | 牌坊、影壁、元妃立于牌坊下，正文「花溆二字便妥」 |
| C18-067 正殿 | `shengqin` | 仙宫规格正殿 + 东西配殿 + 丹陛，正文「金门玉户神仙府」 |

四镜均无穿帮（屋顶被切、物件浮空、文字重叠、角色穿墙）。

### 上线（2026-11-18）

- 构建 `index-gK5Av-my.js`，md5 `c577eb82f40c9363958f6d5b65b5e366`（本地与线上逐字节一致）；
  CSS 未变（`index-1bfh7WdO.css`，`2100c73893f35c0e3bc27cdbc46a48aa`）。
- 部署 `stone-direct.yan.pub`：服务器回环 200、公网 200。
- 线上复验：`test:locator`（48 场景、overlap 0、挂载时舞台就绪）、
  `online-chapter18`（16 段 / 8 舞台 / 81 立绘无损坏 / 无 403）、
  `verify-album-title`（前二十三回 · 人物图鉴）、`test:online:card-preview`（全绿）。

## 待办 / 边界

- 大观园全景是**一张**舞台承载 10 处景点，靠旁白与景物区分，不是十张分景图；
  原书未给精确尺寸方位，摆位属叙事改编。
- `atlas-maps.json` 的 `daguanyuan` 层仍写「前五回尚未营建」——那是**读者主动打开的
  考据总览**，与本补图（剧情舞台）是两张表，按项目纪律「舆图接入前不接」未动。
- 未生新美术资产，全部复用既有素材。
