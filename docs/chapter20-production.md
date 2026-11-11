# 第二十回制作记录 · 王熙凤正言弹妒意　林黛玉俏语谑娇音

> 状态：**已完成并上线（2026-11-11）。39 节点 / 7 段 / 45 条证据；4 名新角色美术已入库；全套验收通过。**

## 一、底本

- 文件：`docs/chapter20-source.txt`（2026-11-11 重新生成，5289 字）
- **曾有的坑**：维基第 20 回的回目行（`{{center}}` 模板）与正文首句之间**没有空行**，
  `fetch_chapter_source.py` 的并段逻辑把回目粘进了正文首段（「…玉生香话说宝玉在林黛玉房中」）。
  已修：`to_plain` 里回目替换后补 `\n\n`，回目永远自成一段（段 1），正文段 2~12。
- 结构：段 0=文件头、段 1=回目联、段 2~12=正文 11 段（对白密集的长段），末段以「要知端详，下回分解。」收束。

## 二、剧情生成：句号索引切片

生成脚本 `scripts/build_chapter20.py`。**这一回把切片方法从「字符串标记」换成了「句号索引」**：

```python
def split_sentences(text):        # 按 (?<=[。！？]) 切句，闭合引号归入前一句
def cut_sent(para, s_from, s_to): # 切出第 para 段的第 [s_from, s_to) 句
```

**为什么换**：底本里大量同形短句（「我知道了」「说的是他」），字符串 `find` 会命中前一处，
切到别人的字。句号唯一定位，而且天然保证节点顺序单调。

**双层单调校验**：`(段号, 句号)` 必须全局严格递增，`check()` 逐对校验。实测踩了 3 处
（叙述引入与对白同段切片重叠、莺儿委屈的顺序排在贾环问话之后、段 5 末尾范围重叠）。

**新增舞台连续性自检** `check_stage()`：引擎只在**换场景**时清空舞台（`engine.ts` 的 `enter()`），
同一场景里角色可见性一直保持。「move 一个从没 show 过的人」会在运行期抛
`[节点] 移动角色未显示：xxx`，而且是在读者点到那一步时才炸。实测抓到 5 处：

| 节点 | 问题 | 修法 |
|---|---|---|
| C20-026 / C20-027 | 贾环被 move，却从未 show | C20-023 补 `show jia_huan @east_corridor`（他本就跟赵姨娘在东廊） |
| C20-032 / C20-036 | 宝玉被 move，却从未 show | C20-028 补 `show baoyu @grandmother_greet` + `show baochai @wang_place`（原著「宝玉正和宝钗顽笑」） |

> `effect` 动作不要求角色在台（只是播特效），`hide` 对不在台上的角色也是空操作，
> 所以自检只查 `move`。

## 三、分场与节点（7 段 / 39 节点）

| 段 | 场景 | 底本段 | 内容 |
|---|---|---|---|
| c20-momo | `night`（怡红院占位） | 2 | 李嬷嬷骂袭人「忘了本的小娼妇」 |
| c20-fengjie | `night` | 3 | 凤姐一阵风撮走李嬷嬷；宝玉「只拣软的排揎」 |
| c20-shuyao | `night` | 4-5 | 麝月守夜看牌；宝玉替她篦头；晴雯（以 messenger 代指）冷笑 |
| c20-jinghuan | `c7_lixiang`（梨香院） | 6 | 赶围棋赖钱；莺儿委屈「一个作爷的，还赖我们这几个钱」 |
| c20-tanyi | `wang` | 7 | 赵姨娘啐骂；凤姐隔窗正言「他现是主子，与你什么相干」；训贾环 |
| c20-xiangyun | `dinner`（贾母院） | 8 | 史湘云到；黛玉赌气「在宝姐姐家的」 |
| c20-qiaoyu | `dinner` | 9-11 | 「亲不间疏，先不僭后」；湘云「明儿得一个咬舌的林姐夫」 |

## 四、新角色美术（4 名，已完成）

`art/identity/character-designs.json` 已登记 seed：

| 角色 | id | seed | 立绘设定 |
|---|---|---|---|
| 贾环 | `jia_huan` | 10234010 | 少年庶出，尖削小脸，三角眼带忌刻，衣色暗沉 |
| 赵姨娘 | `zhao_yiniang` | 10234020 | 薄长脸，稀眉细眼，颧骨略高，半旧俗艳 |
| 史湘云 | `shi_xiangyun` | 10234030 | 苹果脸，浓眉大眼，笑意常开，英气洒脱 |
| 麝月 | `she_yue` | 10234040 | 少女清秀鹅蛋脸，细长眉，眼尾微垂含蓄 |

- 生成：`scripts/gen_ch20_characters.py`（t2i + bg-removal，串行可续跑）→ 8 张全部成功。
- 入库：`scripts/build_ch20_char_assets.py`（量脚底锚点 → 追加 `art/calibration.json` →
  跑 `build_art_assets.py`）→ `scripts/rebuild_new_character_manifest.py` 注册 manifest。
  最终 270 个资产，126 个 identity 块全部带 `character` 字段。
- 校准用 **height**（portrait 600 / chibi 116），chibi 另带 `bodyCompress`（split=anchorY×0.42, factor=0.64）。

### facing（sprite 朝向）——新管线

第 20 回落后的角色**没走 identity 管线**，官方裁切（tight/wide）读不到脸。用了一套新办法：

1. 先用 **10 个已知朝向的 chibi** 标定符号规则：`ok` 行符号直接用，**`SWAPPED` 行符号取反**，
   两者都要求「鼻与嘴同号」；跨 7 种高度比例 × 3 种水平内缩 × 3 档放大投票。
2. 标尺 **7/7 全部命中**已知朝向后，才把规则用到新样本。
3. 结论：`jia_huan-chibi`（33 读数全正）、`she_yue-chibi`、`shi_xiangyun-chibi`（读数全负，
   SWAPPED 取反）**都是 right**，与各自立绘同向。

判据已写进 `scripts/build_facing.py` 的 `REVIEWED` 钉死表，重跑不会翻转。

## 五、注册清单（已完成）

- `src/story.ts` 四处（import script20/sections20 → story → chapters + book → bookNames）
- `design/chapter-titles.json`（回目联「王熙凤正言弹妒意 / 林黛玉俏语谑娇音」）
- `scripts/check_content.mjs` 的 `VERBATIM_BASE` 加 20
- browser-smoke「查无此人」样本：麝月在第 20 回登场，已换成**紫鹃**（全部 story 数据里计数 0）。
  并加了一条静态断言：样本名一旦被某一回用掉，测试立刻报错，而不是误判成搜索功能坏了。
- **browser-smoke 的一个既存 bug 顺手修掉**：它自己拼中文回次名（`第十${CN[11]}`），
  拼到第二十回就断了，测试期望值变成「第十undefined回」，误报成「目录少了一回」。
  改为从 `src/story.ts` 的 `bookNames` 实读，不再维护第二份中文数字表。

## 六、验收与部署

build 脚本（含 walkable 校验）→ check:content → tsc → build → `tests/chapter20.mjs` 定向 →
save-compat → browser-smoke → 部署（改 JSON 后必须重新 build！）→ 线上复验。

**部署纪律**：`stone-direct.yan.pub` 与 `stone.yan.pub` 共用 web 根 `/www/wwwroot/stone`，
`stone-direct` 用独立 Let's Encrypt 证书。**切勿用通用 `yanpub-deploy` 脚本**（会建错目录并用
共享证书覆盖，破坏现有 vhost）。正确做法：`rsync -az --delete dist/ → /www/wwwroot/stone.new/`
→ 原子 `mv` 覆盖 `stone`，vhost 与证书不动、无需 reload。
