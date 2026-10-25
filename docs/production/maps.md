# 地图构建、方位与准确放置

## 先定叙事关系，再做地图

每张局部舞台 40×40，tilewidth=128、tileheight=64，orientation=isometric。全府总览也用 40×40，但它与局部舞台不是同一物理比例。先列本场地实际地点、入门顺序、可行走区域、阻挡、讲话站位与进出门，再摆建筑；不要先铺满资产再让剧情穿墙。

列 c 增加为东，行 r 增加为南：北在屏幕右上、东右下、南左下、西左上。方向/门向使用世界方位说明，不能用“图像在最下方所以是南门”。沿用 [空间考据](../estate-geography.md) 的既定关系。

## TMJ 契约

根属性 `sceneId` 唯一，另外有 title/theme；40×40 普通等距地图放 `maps/` 顶层自动加载。可选的根属性 `water`（字符串 `"col,row,w,h;…"`，river 主题的水带矩形列表）与 `flowerbeds`（bool，是否画默认花坛，缺省 `true`）只影响地板表现，不改变可走集合：写了 `water` 的 river 舞台按矩形画水面与波纹，取代旧版固定水塘；`flowerbeds=false` 的舞台（如运河纤道）不画花坛。两者都不写时保持旧外观。必要的对象层如下，大小写不可变：

| 层 | 运行作用 |
| --- | --- |
| `PlanZones` | 原型地面区域；A/A数字/B/C/D/E/F ID 的区域纳入可走集合 |
| `PlanBlockers` | 从可走集合中减去矩形障碍 |
| `Anchors` | 命名格心，剧情 focus / show.at / move.via 引用它 |
| `Routes` | 每项属性 route_id、逗号分隔的 anchor_ids；帮助生成通行走廊 |
| `Art`（可选） | 图像对象，属性 asset 指 manifest ID；width/height 为最终显示像素尺寸 |
| `ArtFootprints`（可选） | 独立矩形碰撞，Art 图像不会自动变碰撞 |
| `Labels`（可选） | 格心标签，name 为显示文本 |

Anchors 在 Tiled **对象坐标**里：`x=(c+0.5)×64`、`y=(r+0.5)×64`。例如格 (10,12) 为 (672,800)。矩形区域/障碍为 `x=c×64,y=r×64,width=w×64,height=h×64`。不是把屏幕菱形坐标直接填进点对象。

读取器以对象真实 x/y 为准，旧 col/row 属性只是备注。所有锚点落格心、在界内、不同名称不重复。必需层即使空也保留。Zones 的 ID 取名称第一个空格前的部分，使用如 `A0 前院`；不要用任意名字后期待自动变可走。

Route 折线是 Tiled 示意；运行器消费 `anchor_ids`，先沿列再沿行补走廊，再减障碍。不要把所有锚点随手拼成长路线，否则会造出不该有的捷径。路线应按合法通道分别列出；窄门两侧加途经点。实际 A* 是四邻格，不切斜角。每个 show 点与 move 起终点可通行，所有必要途经点应可达。

## 逻辑格到画面

人物脚下格心屏幕坐标：

```text
Gx = (c-r) × 64
Gy = (c+r+1) × 32
```

图像有像素锚点 A=(ax,ay)，比例 s；锚点是鞋底/树根/门槛/前门台阶，未必是包围盒底中点。Tiled 图像集合 `objectalignment=bottom`，对象图像底部中心 B：

```text
Bx = Gx + (imageWidth/2-ax) × s
By = Gy + (imageHeight-ay) × s
object.x = By + Bx/2
object.y = By - Bx/2
object.width = imageWidth × s
object.height = imageHeight × s
```

网页恢复 Bx=`object.x-object.y`、By=`(object.x+object.y)/2`，图像 origin=(.5,1)。人物 origin 则直接用 `(ax/width,ay/height)`。深度按脚下/门槛地面 y 加 depthOffset，不按屋顶或图像包围盒下缘。

门要先校准透明门洞和门槛位置，再设置两边的行走锚点及碰撞。禁止用挪剧情锚点掩盖鞋底/门槛测错的问题。镜像和剪切在资产校准阶段固定，Tiled 不能代替美术方向制作。

## Tiled 编辑支持范围

支持 Art 真实位置、显示宽高、asset、visibility、depthOffset，以及两个室内外自定义属性：`PlanZones` 对象的 `indoor`（bool，该地面属于建筑内部）与 Art 对象的 `interiorZone`（string，这栋 `visibility=exterior` 的外观盖住哪个室内地面）。`visibility=exterior` 不再只跟随剧本 roof 开关：只要有人站在 `interiorZone` 指向的室内地面上，这栋外观立即隐藏，露出室内地面与室内陈设；人走出来自动恢复。剧本 `roof` 动作仍是显式覆盖（`visible:false` 强制整场室内，`visible:true` 强制看外观）。当前不支持对象旋转、gid 翻转位、分组/层偏移、任意多边形碰撞，也不完整解释 layer opacity、普通地砖层碰撞。旋转/翻转已报错，其余缺失能力不会自动实现。编辑器用默认无偏移对象层、无旋转图像。

两个属性由 `scripts/annotate_interiors.py` 幂等写入已提交的 TMJ（`python3 scripts/annotate_interiors.py`）；新增院落或改室内范围时改脚本里的 `INDOOR_ZONES` / `INTERIOR_OF` 再重跑。室内陈设补齐用 `scripts/furnish_interiors.py`，放置格子先用 `scripts/story_path_cells.py` 确认没有被任何 move 路线占用，避免挡路。`scripts/render_map_preview.py` 可在不起服务的情况下近似渲染地板与 Art 布局，用于快速目检室内外效果。

## 室内家具批次摆位（2026-10）

`scripts/furniture_place.py` 用上面的 Bx/By 公式把 9 件新家具写进 11 张室内图，并把 8 处重复的 `tea-table` 换成更合场景的桌子（条案×3、书案×3、八仙桌×2）。计划表在脚本内，幂等：同资产同格的对象已存在就跳过；换装直接改原对象的 asset/gid/宽高并保持地面格不变，关联 ArtFootprints 同步改名。新增对象一律补 64×64 碰撞（与既有家具同约定），`nextobjectid` 取全图最大值递增。

选格规则：

- 家具地面格必须落在某个 `PlanZones` 内（脚本外由 `verify_furniture.py` 复核）。
- 座位（椅/凳）放在演员身后：该格的 `col+row` 不大于演员格，运行时先绘制，不会盖住人物；西—南向的"背对桌子"方向 col+row 不变，此时凳子与人物同深度并排，同样不遮挡。
- 大件（条案 195px、顶箱柜 130×222）要预演遮挡：按人物实际 Q 版尺寸逐anchor 估算覆盖率，超过脚部级的擦边就换格；既有场景本来就允许桌子盖住坐姿人物脚边（晚膳圆桌盖贾母约 25%），新家具不高于这个基线。
- 换装后不挪剧情锚点；`tea-table` 只留在情境需要处（晚膳斟茶、碧纱橱、王夫人茶座、刑堂密室），从 11 张减到 4 张。

`scripts/verify_furniture.py` 复核四件事：每个 Art 的 asset 在 manifest 内、地面格与 Footprints 都在房区内、没有 Art 画在演员前面却盖住演员盒（按剧情 show/move 取真实演员尺寸）、深度用 `artGround` 的地面 y 比较（同格时人物因 +1 在前）。改完跑 `npm test`（全节点 20 图寻路会暴露挡路）与 `node tests/interior-roof.mjs`。

打开 `maps/rongguo-entry.tmj` 或新局部图，保持相对 TSJ 路径和 asset 属性。移动 Art 后核对关联 Anchors；碰撞另改 ArtFootprints。保存刷新网页，先清理不兼容的测试存档或从段落起点重放。Tiled 中看起来对齐还须网页复核脚下锚点。

`build_art_assets.py` 会更新 TSJ 的全部 gid，校准清单顺序变化时需要重导出引用 gid 的地图。网页按 asset 名称读取，但 Tiled 按 gid，不能只让网页看起来对了。

## 荣府总览与跨院路线

`design/rongguo-world.json` 是总览权威源：locations、gates、walls、network.nodes/edges。SVG 和 `build_world_map.py` 参考同份数据。总览的 Tiled 编辑不会回写。

当前西墙 c=4，西角门 (4,30)；南墙 r=36，正门 (23,36)，黑油门 (35,36)。去贾赦院经过西角门—府外道路—正门外—黑油门；回程按本版选择走正门。墙段在门洞留开口，网络边四邻轴向，检查只在门洞穿墙。新增院落同时改道路、墙、门、地点说明和测试，不能画一条直线越过建筑。

总览院落要用建筑外观；点击标签查看地点，点“从此处剧情开始”才 seek。透明屋顶整块包围盒不能覆盖邻院标签的可点击范围，标签最后绘制并提供可访问名称。外地或梦境场景用行迹目录，不勉强套进荣国府道路。

## 旅行舞台：运河与郭外（2026-10）

地点之间不再硬切场景：扬州→京城的水路、郭外↔智通寺的步行都做成可走舞台，人物在地图上真实走完一段路再进下一场。

- `maps/canal.tmj`（sceneId `canal`，theme river）：第三回黛玉赴京的水路。水带 `water=3,14,34,11` 横贯舞台北侧，纤道沿南岸三列并行东去——黛玉/雪雁/王嬷嬷各走一排（rows 25/26/27），西端 `river-boat` 是扬州渡口，东端 `manor-main-gate` 是京城水门；`flowerbeds=false`，纤道边不画花坛。
- `maps/guowai.tmj`（sceneId `guowai`，theme garden）：第二回雨村出郭闲步与暮色回城。去程一条之字山道（city_gate→field_cross→grove_entry→hill_bend→hill_top→stream_cross→temple_path→temple_gate），东南另有一条归路（tavern_lane→dusk_field→city_gate）；两条路线分列 `Routes` 的 `route_id`，避免运行器补出幽灵走廊。北端 `estate-zhitong` 作智通寺外景，与室内图 `zhitong` 衔接。

两份设计稿在 `design/travel-maps.json`（name/theme/zones/anchors/labels/props，canal 另带 water/flowerbeds），由 `scripts/build_travel_maps.py` 生成 TMJ——只写这两个新文件，不触碰已提交地图，也不会丢室内图的手工属性。回归测试 `node tests/travel-stages.mjs`：逐个 seek 新节点，断言场景 ID、每个可见角色的落点锚点、canal 的 water 带，并核对段落下拉、行迹视图与地图地点表（40×40、锚点数）。

## 地图目检与边界

大地图、局部图、指北针和原文方位保持一致；看人物是否穿门、遮挡是否能读、墙是否留洞、动线是否真实可达。入室时 exterior 整楼隐藏由室内地面占位自动触发（见上文两个自定义属性），不是只靠剧本 roof 动作；当前没有精细前柱/屋顶遮挡系统。新增主题的地板/花坛/水面配置需在对应场景检查。不要以墙画在地板上而声称已自动阻挡。

修改生成器、校准资产前先看 [覆盖表](architecture.md)，保留手工编辑副本。Tiled 应用未实际打开过，就将其列为待验收，不能用 JSON 检查代替目视结论。
