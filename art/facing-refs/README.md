# facing 朝向标尺参考样本

这些图是 `scripts/facing_wide_scan.py` 用的**标尺样本**：已知朝向的角色立绘 /
Q 版，用来验证「符号规则」本身是否可信。

## 为什么要有标尺

`scripts/facing_vision.swift` 读出的鼻子/嘴的相对位置，是一个**符号**，
不是方向本身。符号规则（正偏移 = 朝画面右）如果只是巧合，用它去判新角色
就会系统性判反。

**所以标尺必须双向**：只用朝右的样本，无法区分「符号规则是对的」与
「符号规则其实是反的、只是朝右样本恰好没暴露」。必须同时有朝左和朝右的
已知样本，命中率够高才允许用于新样本。

## 本目录的内容

| 文件 | 含义 |
| --- | --- |
| `refL_*.png` | **朝左**样本（10 张）：dai_quan / jia_lian / jia_rui / menzi / ming_yan / monk / ruhai / shui_rong(chibi) / yucun / zhang_youshi 的立绘 |
| `ref_*.png` | **朝右**样本（8 张）：baochai / baoyu / daiyu / feng / she_yue / shui_rong(chibi) / xiren / yuanchun 的 Q 版 |
| `facing_refs.png` | 上述样本的拼版总览，一眼看朝向 |
| `wide_calib3.json` | 宽扫法的标定结果（符号 + 命中明细） |
| `wide_new.json` | 新角色的宽扫读数 |

## 已知的标尺结论（血泪）

- **4 朝右 + 8 朝左 = 11/12 命中**才可用于新样本。
- 唯一未命中的是 `jia_lian-portrait`——**manifest 里没有它的 faceBox**，
  属缺样本，不是规则错。
- **自动宽扫法（7 高度比 × 3 内缩 × 3 放大）已被自己的标尺证伪并废弃**：
  11 个标尺只出 6 个读数，且 2 个与已知答案相反（朝右读成 left、朝左读成 right）。
  所以新角色改用 `scripts/facing_wide_scan.py` 之外的**手工裁切 + 放大到
  760–900px** 再读数。
- **符号要分两用**：`ok` 行的符号直接用，**`SWAPPED` 行的符号取反**。
- 两种符号都要求「鼻与嘴同号」才算有效读数。

## 相关文档

- 权威朝向表：`design/character-facing.json`（由 `scripts/build_facing.py` 生成）
- 朝向清单文档：`docs/production/facing-list.md`（由 `scripts/build_facing_doc.py` 生成）
- **改 facing 必须跑这两个脚本**，否则 `npm run check:content` 报 out of date。
