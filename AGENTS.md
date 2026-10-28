# 《红楼梦》等距叙事项目：Agent 工作入口

先读 [制作手册索引](docs/production/README.md)，开始下一回前读 [新增回目流程](docs/production/chapters.md)。这些是当前工程规范；`docs/design.md`、`docs/storyboard.md` 和布局 PNG 是早期原型资料，不是完整运行规格。

## 固定的产品要求

- 40×40、128×64、2:1 等距菱形局部地图；手绘工笔淡彩、水彩纸感、低饱和青灰松绿暖米白。
- 地图占据横版主舞台。只保留一条紧凑顶部导航；不再增加大标题、重复地点文案或底部播放栏。
- 对白固定高度，讲话人立绘在左、在场人物在右，头肩可突出；换图不能撑高对话框。移动用行动提示、真实路线和人物动作吸引视线。
- 人物必须靠脸型与五官区分，不能只换发型、衣服、年龄。新人物先定立绘面部，再用其参考生成 Q 版；见 [美术规范](docs/production/art.md)。
- 原文明示、人物转述、设计推定分开记录；只被提及的人物不凭空加入当下场景。西角门在西墙是本项目既定方案，回程走正门是设计选择，不能写成原文明示。
- 用户已要求自主完成，不为普通文件编辑、制作和验证重复征求许可；实际执行仍服从工具权限。不要自行开新的对话任务或派生 agent。

## 工程纪律

- 保留 AI 原图、参数、抠图与旧人物脸。生成结果不是运行素材；必须经透明度、轮廓、尺寸、脚底锚点与页面目检。
- ComfyUI 为用户授权的 `http://192.168.4.66:8188`。先读项目 `.local-tools/local-image-studio/SKILL.md`；同一服务器只串行执行 GPU 任务，队列空闲后再提交，禁止取消别人的任务。生图母题写法与验收清单见 [生图纪律](docs/production/art-prompting.md)：母题里出现的任何名词都会被画出来，风格基底里的否定句压不住。
- 界面反馈（「丑/乱/不齐/太小」）不要靠看图猜。截图只用来发现问题，尺寸、溢出、等高一律用 DOM 实测确认；见 [UI 改造的诊断纪律](docs/production/ui-diagnosis.md)。改全局样式前先查该选择器的全部使用点。
- 普通网页修改不要运行全量地图/美术重建。修改生成文件前查 [维护来源及覆盖表](docs/production/architecture.md)。Tiled 不是所有数据的双向编辑器。
- **不要用 `git checkout -- <文件>` / `git restore` 撤销改动**：本仓库的工作树长期处于「大量未提交」状态（地图、设计数据、美术校准全在里面），撤销一个文件等于删掉前几轮的设计结果，且无法恢复。要改回某段内容，先 `git diff` 看清再手工改；要留退路就 `cp` 一份到 `/tmp`。已经因此丢过 `design/travel-maps.json` 的 props/terraces（靠 `maps/*.tmj` 反解才补回来）。
- 不要用 `scripts/extend_art_calibration.py` 自动扩展陌生资产：当前尺寸分支是旧批次专用。已有面部补丁遇校准变化会拒绝重建，应重新检查，不能绕过保护。
- 新回目必须接入 story、sections、bookNames、顶部回目分组、总览策略、存档兼容、测试、文档统计。当前运行器不是自动发现回目的框架。
- 默认不随意改旧节点 ID、角色 ID、场景 ID 和存档版本。追加剧情也会改变旧终幕状态；按 [新增回目流程](docs/production/chapters.md) 处理迁移。

## 上线与线上可达性

线上站点是 `https://stone.yan.pub/`（腾讯云 154.8.237.35，站点根 `/www/wwwroot/stone`，`*.yan.pub` 走 CF Tunnel）。
部署：`bash ~/.workbuddy/skills/yanpub-deploy/scripts/deploy.sh stone <项目>/dist --no-build`，部署前先 `cp -a` 一份
`/www/wwwroot/stone.bak-<时间戳>` 作回滚点。

- **CF 的托管挑战会拦住 HTML，且不只拦 curl**：`curl https://stone.yan.pub/` 与**有头 Chrome** 都只拿到
  `403` + `cf-mitigated: challenge`（页面里是 `managed`，即 Managed Challenge）。静态资源不过挑战，`.js/.webp/.css/.ogg`
  一律 200——所以「首页打不开、资源都正常」时不要怀疑构建，先查 CF。判定命令：
  `curl -s -o /dev/null -D - https://stone.yan.pub/ | grep -i cf-mitigated`。
- **`stone-direct.yan.pub` 是绕过 CF 的直连域名**（DNS-only A 记录 + Let's Encrypt 单域名证书 + 独立 vhost）。
  挑战没解除时，这是唯一能打开整站的公开地址。`stone.yan.pub` 的源站证书是 Cloudflare Origin CA，
  **不能**把它的 DNS 改成 DNS-only，否则浏览器直接报证书错误。
- `~/.config/yanpub/cf_token` 只有 DNS 读写与 zone 读权限：zone settings、WAF、page rules、缓存 purge 全部
  返回 `9109 Unauthorized`。要改安全级别/关掉 Managed Challenge，只能由用户在 CF 面板操作，或换成带
  `Zone Settings:Edit` / `Zone WAF:Edit` 的 token。
- 线上验收：`ORIGIN_DIRECT=1 node tests/online-verify.mjs`（用 `--host-resolver-rules` 把域名指到源站 IP，
  绕开挑战；`tests/online-verify.mjs` 同时校验六回分组、第四章新舞台、肖像、总览缩略图、播放开关、回看、
  每回 BGM，以及**第五回必须给「本回行迹」而不是荣国府总览**）。

## 每次交付

运行与改动相符的验证，记录真实结果。基本检查：`npm run check:content`、`npm test`、`npm run build`；运行素材或页面改变时加浏览器检查。详见 [验收与交接](docs/production/verification.md)。只有亲自打开 Tiled 验收后，才能声称已在 Tiled 中目视通过。

更新回目制作记录，写明已完成、未完成、考据推定、生成任务状态、验证证据以及下一步。不要把“已写提示词”计为“已生产资产”，不要把自动测试通过计为画面美术通过。

“已目检”不是结论，是**带检查项的记录**：写明这次实际核对了哪几项，没查的就别算进去。清单漏项等于漏检——账簿 14 张贴图曾因清单没列「画面里的器物是否属于这一笔」而漏过 5 张（另有 1 张印面画出了可读篆字）。
