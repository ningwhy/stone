# 人物位图朝向清单

> 本文件由 `scripts/build_facing_doc.py` 从 `design/character-facing.json` 自动生成，请勿手工编辑。
> 权威数据是那张 JSON；改图后重跑 `scripts/facing_assets.py` → `scripts/build_facing.py` → 本脚本。

## 总览

- 位图总数 **159**（立绘 69、Q版 69、表情变体 21）
- 朝左 **28**，朝右 **131**
- 依据：实测 **108**、目视裁决 **42**

「朝左 / 朝右」指的是**原图**里脸偏向画面的哪一侧——不是角色在剧情里该朝哪边。
运行时用它决定该用原图还是左右镜像：要求显示的一侧与原图不符时才镜像。

## 逐张清单

| 资产键 | 角色 | 类别 | 原图朝向 | 判定依据 |
| --- | --- | --- | --- | --- |
| `ban_er-chibi` | ban_er | Q版 | **朝右** | 目视 |
| `ban_er-portrait` | ban_er | 立绘 | **朝右** | 实测·2票 |
| `bao_zhu-chibi` | bao_zhu | Q版 | **朝右** | 目视 |
| `bao_zhu-portrait` | bao_zhu | 立绘 | **朝右** | 实测·3票 |
| `dai_quan-chibi` | dai_quan | Q版 | **朝右** | 实测·2票 |
| `dai_quan-portrait` | dai_quan | 立绘 | **朝左** | 实测·1票 |
| `er_ya_tou-chibi` | er_ya_tou | Q版 | **朝右** | 目视 |
| `er_ya_tou-portrait` | er_ya_tou | 立绘 | **朝右** | 实测·3票 |
| `hu_shi-chibi` | hu_shi | Q版 | **朝左** | default-unmeasured |
| `hu_shi-portrait` | hu_shi | 立绘 | **朝右** | 实测·3票 |
| `jia_dairu-chibi` | jia_dairu | Q版 | **朝右** | 实测·2票 |
| `jia_dairu-portrait` | jia_dairu | 立绘 | **朝左** | 实测·1票 |
| `jia_qiang-chibi` | jia_qiang | Q版 | **朝左** | default-unmeasured |
| `jia_qiang-portrait` | jia_qiang | 立绘 | **朝右** | 实测·3票 |
| `jia_rong-chibi` | jia_rong | Q版 | **朝左** | 目视 |
| `jia_rong-portrait` | jia_rong | 立绘 | **朝右** | 实测·3票 |
| `jia_rui-chibi` | jia_rui | Q版 | **朝左** | default-unmeasured |
| `jia_rui-portrait` | jia_rui | 立绘 | **朝左** | 实测·3票 |
| `jia_zhen-chibi` | jia_zhen | Q版 | **朝右** | 实测·1票 |
| `jia_zhen-portrait` | jia_zhen | 立绘 | **朝右** | 实测·3票 |
| `jin_rong-chibi` | jin_rong | Q版 | **朝左** | default-unmeasured |
| `jin_rong-portrait` | jin_rong | 立绘 | **朝左** | default-unmeasured |
| `jin_shi-chibi` | jin_shi | Q版 | **朝右** | 实测·3票 |
| `jin_shi-portrait` | jin_shi | 立绘 | **朝右** | 实测·3票 |
| `jing_xu-chibi` | jing_xu | Q版 | **朝右** | 目视 |
| `jing_xu-portrait` | jing_xu | 立绘 | **朝左** | 目视 |
| `jinghuan-chibi` | jinghuan | Q版 | **朝右** | 目视 |
| `jinghuan-portrait` | jinghuan | 立绘 | **朝右** | 实测·3票 |
| `lai_sheng-chibi` | lai_sheng | Q版 | **朝右** | 目视 |
| `lai_sheng-portrait` | lai_sheng | 立绘 | **朝左** | 目视 |
| `li_gui-chibi` | li_gui | Q版 | **朝左** | default-unmeasured |
| `li_gui-portrait` | li_gui | 立绘 | **朝左** | default-unmeasured |
| `liu_lao-chibi` | liu_lao | Q版 | **朝右** | 目视 |
| `liu_lao-portrait` | liu_lao | 立绘 | **朝左** | default-unmeasured |
| `ming_yan-chibi` | ming_yan | Q版 | **朝左** | default-unmeasured |
| `ming_yan-portrait` | ming_yan | 立绘 | **朝左** | 实测·3票 |
| `ping_er-chibi` | ping_er | Q版 | **朝右** | 目视 |
| `ping_er-portrait` | ping_er | 立绘 | **朝右** | 实测·3票 |
| `qin_ke-chibi` | qin_ke | Q版 | **朝右** | 目视 |
| `qin_ke-portrait` | qin_ke | 立绘 | **朝右** | 实测·3票 |
| `qin_ye-chibi` | qin_ye | Q版 | **朝右** | 实测·1票 |
| `qin_ye-portrait` | qin_ye | 立绘 | **朝右** | 实测·3票 |
| `qin_zhong-chibi` | qin_zhong | Q版 | **朝右** | 实测·1票 |
| `qin_zhong-portrait` | qin_zhong | 立绘 | **朝右** | 实测·3票 |
| `shui_rong-chibi` | shui_rong | Q版 | **朝右** | 实测·1票 |
| `shui_rong-portrait-mourning` | shui_rong | 变体·mourning | **朝右** | 实测·1票 |
| `shui_rong-portrait` | shui_rong | 立绘 | **朝右** | 实测·3票 |
| `wang_er-chibi` | wang_er | Q版 | **朝右** | 实测·2票 |
| `wang_er-portrait` | wang_er | 立绘 | **朝左** | 目视 |
| `ying_er-chibi` | ying_er | Q版 | **朝右** | 实测·2票 |
| `ying_er-portrait` | ying_er | 立绘 | **朝右** | 实测·3票 |
| `you_shi-chibi` | you_shi | Q版 | **朝右** | 实测·1票 |
| `you_shi-portrait` | you_shi | 立绘 | **朝右** | 实测·3票 |
| `zhang_youshi-chibi` | zhang_youshi | Q版 | **朝右** | 实测·2票 |
| `zhang_youshi-portrait` | zhang_youshi | 立绘 | **朝左** | 实测·3票 |
| `zhao_er-chibi` | zhao_er | Q版 | **朝右** | 目视 |
| `zhao_er-portrait` | zhao_er | 立绘 | **朝右** | 实测·3票 |
| `zhi_neng-chibi` | zhi_neng | Q版 | **朝右** | 实测·5票 |
| `zhi_neng-portrait` | zhi_neng | 立绘 | **朝右** | 实测·3票 |
| `zhou_rui-chibi` | zhou_rui | Q版 | **朝左** | 目视 |
| `zhou_rui-portrait` | zhou_rui | 立绘 | **朝右** | 实测·3票 |
| `maid-chibi` | 丫鬟 | Q版 | **朝右** | 目视 |
| `maid-portrait` | 丫鬟 | 立绘 | **朝右** | 实测·3票 |
| `messenger-chibi` | 传话人 | Q版 | **朝右** | 目视 |
| `messenger-portrait` | 传话人 | 立绘 | **朝右** | 实测·3票 |
| `shiyin-chibi` | 侍饮 | Q版 | **朝右** | 实测·3票 |
| `shiyin-portrait` | 侍饮 | 立绘 | **朝右** | 实测·3票 |
| `leng-chibi` | 冷子兴 | Q版 | **朝右** | 实测·5票 |
| `leng-portrait` | 冷子兴 | 立绘 | **朝右** | 目视 |
| `plaintiff-chibi` | 原告 | Q版 | **朝右** | 目视 |
| `plaintiff-portrait` | 原告 | 立绘 | **朝右** | 实测·3票 |
| `ruhai-chibi` | 如来 | Q版 | **朝右** | 目视 |
| `ruhai-portrait` | 如来 | 立绘 | **朝左** | 实测·3票 |
| `sedan-chibi` | 小轿 | Q版 | **朝右** | 目视 |
| `sedan-portrait` | 小轿 | 立绘 | **朝右** | 目视 |
| `guide-chibi` | 引路人 | Q版 | **朝右** | 实测·5票 |
| `guide-portrait` | 引路人 | 立绘 | **朝右** | 实测·2票 |
| `zhang-chibi` | 张道士 | Q版 | **朝右** | 目视 |
| `zhang-portrait` | 张道士 | 立绘 | **朝右** | 实测·3票 |
| `xichun-chibi` | 惜春 | Q版 | **朝右** | 目视 |
| `xichun-portrait` | 惜春 | 立绘 | **朝右** | 实测·3票 |
| `tanchun-chibi` | 探春 | Q版 | **朝右** | 实测·3票 |
| `tanchun-portrait` | 探春 | 立绘 | **朝右** | 实测·3票 |
| `nurse_li-chibi` | 李嬷嬷 | Q版 | **朝右** | 实测·4票 |
| `nurse_li-portrait` | 李嬷嬷 | 立绘 | **朝左** | 目视 |
| `daiyu-chibi` | 林黛玉 | Q版 | **朝右** | 实测·3票 |
| `daiyu-portrait-sad` | 林黛玉 | 变体·忧愁 | **朝右** | 实测·3票 |
| `daiyu-portrait-surprise` | 林黛玉 | 变体·惊愕 | **朝右** | 实测·3票 |
| `daiyu-portrait-joy` | 林黛玉 | 变体·欢喜 | **朝右** | 实测·3票 |
| `daiyu-portrait-angry` | 林黛玉 | 变体·气恼 | **朝右** | 实测·3票 |
| `daiyu-portrait` | 林黛玉 | 立绘 | **朝右** | 实测·3票 |
| `jiaoxing-chibi` | 焦大 | Q版 | **朝右** | 实测·3票 |
| `jiaoxing-portrait` | 焦大 | 立绘 | **朝右** | 实测·3票 |
| `fengshi-chibi` | 王夫人 | Q版 | **朝右** | 实测·3票 |
| `wang-chibi` | 王夫人 | Q版 | **朝右** | 实测·5票 |
| `fengshi-portrait` | 王夫人 | 立绘 | **朝右** | 实测·3票 |
| `wang-portrait` | 王夫人 | 立绘 | **朝右** | 实测·3票 |
| `nurse_wang-chibi` | 王嬷嬷 | Q版 | **朝右** | 目视 |
| `nurse_wang-portrait` | 王嬷嬷 | 立绘 | **朝右** | 实测·3票 |
| `feng-chibi` | 王熙凤 | Q版 | **朝右** | 目视 |
| `feng-portrait-mourning` | 王熙凤 | 变体·mourning | **朝右** | 实测·1票 |
| `feng-portrait-sad` | 王熙凤 | 变体·忧愁 | **朝右** | 实测·3票 |
| `feng-portrait-surprise` | 王熙凤 | 变体·惊愕 | **朝右** | 实测·3票 |
| `feng-portrait-joy` | 王熙凤 | 变体·欢喜 | **朝右** | 实测·3票 |
| `feng-portrait-angry` | 王熙凤 | 变体·气恼 | **朝右** | 实测·3票 |
| `feng-portrait` | 王熙凤 | 立绘 | **朝右** | 实测·3票 |
| `monk-chibi` | 癞头和尚 | Q版 | **朝右** | 实测·5票 |
| `monk-portrait` | 癞头和尚 | 立绘 | **朝左** | 实测·3票 |
| `fengsu-chibi` | 秦可卿 | Q版 | **朝右** | 实测·5票 |
| `fengsu-portrait` | 秦可卿 | 立绘 | **朝右** | 实测·3票 |
| `kongkong-chibi` | 空空道人 | Q版 | **朝右** | 目视 |
| `kongkong-portrait` | 空空道人 | 立绘 | **朝右** | 实测·3票 |
| `oldmonk-chibi` | 老僧 | Q版 | **朝右** | 实测·5票 |
| `oldmonk-portrait` | 老僧 | 立绘 | **朝右** | 实测·3票 |
| `yinglian-chibi` | 英莲 | Q版 | **朝右** | 目视 |
| `yinglian-portrait` | 英莲 | 立绘 | **朝右** | 实测·2票 |
| `yingge-chibi` | 莺儿 | Q版 | **朝右** | 实测·3票 |
| `yingge-portrait` | 莺儿 | 立绘 | **朝右** | 实测·3票 |
| `liwan-chibi` | 薛姨妈 | Q版 | **朝右** | 目视 |
| `xueyan-chibi` | 薛姨妈 | Q版 | **朝右** | 实测·4票 |
| `xueyima-chibi` | 薛姨妈 | Q版 | **朝右** | 实测·3票 |
| `liwan-portrait` | 薛姨妈 | 立绘 | **朝右** | 实测·3票 |
| `xueyan-portrait` | 薛姨妈 | 立绘 | **朝右** | 实测·3票 |
| `xueyima-portrait` | 薛姨妈 | 立绘 | **朝右** | 实测·3票 |
| `baochai-chibi` | 薛宝钗 | Q版 | **朝右** | 实测·3票 |
| `baochai-portrait` | 薛宝钗 | 立绘 | **朝右** | 实测·3票 |
| `xuepan-chibi` | 薛蟠 | Q版 | **朝右** | 实测·4票 |
| `xuepan-portrait` | 薛蟠 | 立绘 | **朝右** | 目视 |
| `xing-chibi` | 袭人 | Q版 | **朝右** | 实测·3票 |
| `xiren-chibi` | 袭人 | Q版 | **朝右** | 目视 |
| `xing-portrait` | 袭人 | 立绘 | **朝右** | 实测·3票 |
| `xiren-portrait` | 袭人 | 立绘 | **朝右** | 实测·3票 |
| `baoyu-chibi` | 贾宝玉 | Q版 | **朝右** | 目视 |
| `baoyu-portrait-mourning` | 贾宝玉 | 变体·mourning | **朝右** | 实测·1票 |
| `baoyu-portrait-v2` | 贾宝玉 | 变体·v2 | **朝右** | 实测·1票 |
| `baoyu-portrait-sad` | 贾宝玉 | 变体·忧愁 | **朝右** | 实测·3票 |
| `baoyu-portrait-surprise` | 贾宝玉 | 变体·惊愕 | **朝右** | 实测·3票 |
| `baoyu-portrait-joy` | 贾宝玉 | 变体·欢喜 | **朝右** | 实测·3票 |
| `baoyu-portrait-angry` | 贾宝玉 | 变体·气恼 | **朝右** | 实测·3票 |
| `baoyu-portrait` | 贾宝玉 | 立绘 | **朝右** | 实测·3票 |
| `zheng-chibi` | 贾政 | Q版 | **朝右** | 目视 |
| `zheng-portrait` | 贾政 | 立绘 | **朝左** | 目视 |
| `grandmother-chibi` | 贾母 | Q版 | **朝右** | 实测·5票 |
| `grandmother-portrait-mourning` | 贾母 | 变体·mourning | **朝左** | 目视 |
| `grandmother-portrait-sad` | 贾母 | 变体·忧愁 | **朝左** | 目视 |
| `grandmother-portrait-surprise` | 贾母 | 变体·惊愕 | **朝右** | 目视 |
| `grandmother-portrait-joy` | 贾母 | 变体·欢喜 | **朝右** | 目视 |
| `grandmother-portrait-angry` | 贾母 | 变体·气恼 | **朝右** | 目视 |
| `grandmother-portrait` | 贾母 | 立绘 | **朝左** | 目视 |
| `yingchun-chibi` | 迎春 | Q版 | **朝右** | 实测·3票 |
| `yingchun-portrait` | 迎春 | 立绘 | **朝右** | 实测·3票 |
| `taoist-chibi` | 道人 | Q版 | **朝右** | 实测·2票 |
| `taoist-portrait` | 道人 | 立绘 | **朝右** | 实测·3票 |
| `menzi-chibi` | 门子 | Q版 | **朝右** | 实测·4票 |
| `menzi-portrait` | 门子 | 立绘 | **朝左** | 实测·3票 |
| `yucun-chibi` | 雨村 | Q版 | **朝右** | 目视 |
| `yucun-portrait` | 雨村 | 立绘 | **朝左** | 实测·3票 |
| `huoqi-chibi` | 霍起 | Q版 | **朝右** | 实测·5票 |
| `huoqi-portrait` | 霍起 | 立绘 | **朝右** | 实测·3票 |

## 朝左的位图（异常项，镜像逻辑要重点看）

| 资产键 | 角色 | 类别 | 判定依据 |
| --- | --- | --- | --- |
| `dai_quan-portrait` | dai_quan | 立绘 | 实测·1票 |
| `hu_shi-chibi` | hu_shi | Q版 | default-unmeasured |
| `jia_dairu-portrait` | jia_dairu | 立绘 | 实测·1票 |
| `jia_qiang-chibi` | jia_qiang | Q版 | default-unmeasured |
| `jia_rong-chibi` | jia_rong | Q版 | 目视 |
| `jia_rui-chibi` | jia_rui | Q版 | default-unmeasured |
| `jia_rui-portrait` | jia_rui | 立绘 | 实测·3票 |
| `jin_rong-chibi` | jin_rong | Q版 | default-unmeasured |
| `jin_rong-portrait` | jin_rong | 立绘 | default-unmeasured |
| `jing_xu-portrait` | jing_xu | 立绘 | 目视 |
| `lai_sheng-portrait` | lai_sheng | 立绘 | 目视 |
| `li_gui-chibi` | li_gui | Q版 | default-unmeasured |
| `li_gui-portrait` | li_gui | 立绘 | default-unmeasured |
| `liu_lao-portrait` | liu_lao | 立绘 | default-unmeasured |
| `ming_yan-chibi` | ming_yan | Q版 | default-unmeasured |
| `ming_yan-portrait` | ming_yan | 立绘 | 实测·3票 |
| `wang_er-portrait` | wang_er | 立绘 | 目视 |
| `zhang_youshi-portrait` | zhang_youshi | 立绘 | 实测·3票 |
| `zhou_rui-chibi` | zhou_rui | Q版 | 目视 |
| `ruhai-portrait` | 如来 | 立绘 | 实测·3票 |
| `nurse_li-portrait` | 李嬷嬷 | 立绘 | 目视 |
| `monk-portrait` | 癞头和尚 | 立绘 | 实测·3票 |
| `zheng-portrait` | 贾政 | 立绘 | 目视 |
| `grandmother-portrait-mourning` | 贾母 | 变体·mourning | 目视 |
| `grandmother-portrait-sad` | 贾母 | 变体·忧愁 | 目视 |
| `grandmother-portrait` | 贾母 | 立绘 | 目视 |
| `menzi-portrait` | 门子 | 立绘 | 实测·3票 |
| `yucun-portrait` | 雨村 | 立绘 | 实测·3票 |

