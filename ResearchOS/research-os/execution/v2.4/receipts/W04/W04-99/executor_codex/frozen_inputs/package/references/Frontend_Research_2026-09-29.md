# ResearchOS 前端参考清单 v1.0

调研日期：2026-09-29（Asia/Shanghai）

用途：供青哥挑选视觉方向，并供 Codex 编写前端设计包。本文是参考资料，不替代已交付实施规格，不代表已采用依赖或完成前端设计。

## 1. 建议优先看什么

优先看 Craft Agents、Midday、Linear，再补 Plane、Twenty、LobeHub 的局部界面。

建议组合：**Craft Agents 的任务—会话—文档结构 + Midday 的克制排版 + Linear 的成果审查 + Scira 的来源引用方式**。这是针对 ResearchOS 的设计建议，并非这些产品已实现了 ResearchOS 的验收机制。

建议主界面保持浅灰/暖白背景、细边框、清晰文字层级，少量强调色表示状态；深色主题作为另一套完整主题。把目标、当前进展、待处理阻塞和已验证成果放在用户首先看到的位置。研究过程及技术细节可展开查看。

## 2. 产品与项目参考

| 优先级 | 项目、源码与展示入口 | 值得借鉴 | ResearchOS 对应位置 | 本轮证据 |
|---|---|---|---|---|
| 首选 | [Craft Agents 源码](https://github.com/craft-ai-agents/craft-agents-oss) · [官网](https://thecraftagents.com/) | 左侧状态导航、中间任务列表、右侧文档式会话；轻灰层次与少量紫色状态 | 主工作台、任务收件箱、成果正文、跨任务切换 | 已读 README、LICENSE；实际查看仓库完整界面截图 |
| 首选 | [Midday 源码](https://github.com/midday-ai/midday) · [官网](https://midday.ai/) | 低饱和色、细边框、统一表格、紧凑指标、文件收件箱 | 项目总览、费用、资源、候选收件箱 | 已读 README、LICENSE；实际查看官方界面宣传拼图 |
| 首选 | [Linear 产品](https://linear.app/features) · [Reviews 官方说明](https://linear.app/docs/diffs) | 把待评审清单、变更、检查和讨论组织在同一流程；先理解变化再下钻 | 重大成果详情、独立评审展示、历史版本比较 | 官方文档核查；未登录或运行交互测试；产品视觉参考 |
| 补充 | [Plane 源码](https://github.com/makeplane/plane) · [官网](https://plane.so/) | 双级侧栏、轻量任务卡、状态标记、视图切换、全局搜索 | 研究周期、六阶段任务视图、阻塞和漏项 | 已读 README、package.json、LICENSE；实际查看完整看板截图 |
| 补充 | [Twenty 源码](https://github.com/twentyhq/twenty) · [官网](https://twenty.com/) | 白灰数据表、字段与筛选、分类标签、保存视图 | 来源库、证据库、候选比较、筛选条件 | 已读 README 与许可文件；实际查看功能拼图，未运行产品 |
| 补充 | [LobeHub 源码](https://github.com/lobehub/lobehub) · [官网](https://lobehub.com/) | Agent、Pages、项目、计划任务与资产组织；中性色与角色头像 | Agent 团队目录、长期研究项目、定时任务、上下文展示 | 已读 README、package.json、LICENSE；实际查看功能拼图 |
| 功能参考 | [Scira 源码](https://github.com/zaidmukaddam/scira) · [产品入口](https://scira.ai/) | 自然语言研究入口、可点击引用、来源模式、研究任务的组织 | 研究问题输入、来源覆盖、证据引用、研究结果 | 已读最新 README、公开入口；未执行真实搜索，未验证检索质量 |

### Craft Agents：最贴近我们的工作台结构

![Craft Agents 官方仓库界面截图](https://github.com/user-attachments/assets/3f1f2fe8-7cf6-4487-99ff-76f6c8c0a3fb)

图中可见状态导航、任务列表和文档式会话。可借其信息分区，但 ResearchOS 的“已验收”必须来自自身后台验收状态，不能把界面 Done 当作可靠性的证明。

### Midday：整体视觉参考

![Midday 官方仓库界面拼图](https://raw.githubusercontent.com/midday-ai/midday/main/github.png)

这是宣传拼图，可用于观察排版、颜色和数据密度，不能据此判断完整交互。费用页可以借鉴其信息层次；财务专用指标不进入 ResearchOS。

### Plane：阶段与任务组织参考

![Plane 官方看板截图](https://media.docs.plane.so/GitHub-readme/github-top.webp)

这里值得借的是导航、任务卡、状态和视图控制的组织方式。ResearchOS 仍按发现、核验、实验、评审、交付、跟踪展示过程，并明确等待与阻塞。

## 3. X 上的作品与产品演示入口

访问限制：本轮直接读取以下多数 X 原帖时返回 403 或空内容。已通过公开索引、官方页面或带原帖链接的设计档案核对入口；没有声称观看了受阻的视频。设计档案的条目名称不能证明作品已有可运行代码。

| 作品 / 作者 | 原帖 | 建议看什么 | 交叉依据 |
|---|---|---|---|
| AI Workflow Timeline / @kvnkld | [步骤状态与文件标签](https://x.com/kvnkld/status/1947309143217316117) | 六阶段侧栏中的步骤、执行状态与产物入口 | [Richard Pessall 设计档案](https://www.pessall.com/inspiration)，可搜条目标题 |
| Agent investigation timeline / @CrispyUX | [调研时间线](https://x.com/CrispyUX/status/1982371649132667332) | 研究活动如何串成简洁时间线，关键数值如何收起展示 | 同上；目前作为视觉候选，原帖日期未核 |
| Linear / @linear | [Diffs 发布入口](https://x.com/linear/status/2060048202796040655) | 成果的说明、修改、检查和评审上下文如何连在一起 | [官方 Reviews 文档](https://linear.app/docs/diffs) |
| Plane / @planepowers | [视觉改版入口](https://x.com/planepowers/status/2013544551433023610) | 搜索、间距、状态颜色与时间线里程碑 | [2026-01-19 官方更新](https://plane.so/changelog/release-v2-2-0-enterprise-rollout-enhanced-search-workspace-refinements) |
| Midday / @middayai | [公测发布入口](https://x.com/middayai/status/1805206152227217845) | 总览、文件与记录的关联方式 | [当前官网](https://midday.ai/)；该发布为历史参考 |
| LobeHub / @lobehub | [Agent 工作台入口](https://x.com/lobehub/status/2056371816265097337) | Agent、项目、计划和共享页面怎样组织 | [当前官方仓库](https://github.com/lobehub/lobehub) |

两个追加的组件灵感入口：
- [@kvnkld：工作流画布、节点状态与详情面板](https://x.com/kvnkld/status/2017272672636567957)
- [@pontusab：Midday CSV 导入](https://x.com/pontusab/status/1906281281320849593)

这两项同样由 Richard Pessall 档案提供原帖链接，原帖直接读取受阻。适合作为后续视觉采集入口，不据此断言性能、易用性或实现完成度。

## 4. 可单独评估的代码和交互参考

| 项目 | 用途 | 本轮取舍 |
|---|---|---|
| [assistant-ui](https://github.com/assistant-ui/assistant-ui) · [官方示例](https://www.assistant-ui.com/examples) | React 聊天原语、输入框、工具结果、Artifacts、Generative UI | 优先评估局部组件；MIT。界面状态仍接 ResearchOS 自己的合同与事件 |
| [Twenty UI](https://github.com/twentyhq/twenty/tree/main/packages/twenty-ui) | 数据界面的局部组件和样式组织 | 包内 LICENSE 实读为 MIT；和整个 Twenty 产品的许可分开判断 |
| [Vibe Kanban](https://github.com/BloopAI/vibe-kanban) · [官网](https://www.vibekanban.com/) | 任务切换、Agent 对话、diff 与预览并排 | 实际看过完整工作区截图；上游已声明 sunsetting、后续社区维护，保留交互参考 |
| [Onlook](https://github.com/onlook-dev/onlook) · [官网](https://onlook.com/) | 预览与代码并排、选择元素后交给 Agent 调整 | 已看上游编辑器截图；用作后续成果预览参考。开源仓库与新的 hosted 产品须区分 |

## 5. 复用时需要保留的项目差异

以下为本次仓库文件中的声明记录，不是对所有文件的逐项许可审计。

- Craft Agents：LICENSE 为 Apache-2.0；另有 NOTICE、TRADEMARK 文件。前端为 React/Vite/shadcn 的桌面渲染层，直接移入网页仍要做适配。
- Midday：LICENSE 为 AGPL-3.0；README 另有非商用/商业许可联系表述，声明存在差异。因此先作视觉参考。官网当前显示加入 Ramp。
- Plane：AGPL-3.0。当前 apps/web 的依赖显示 React、React Router、Vite、Tailwind、MobX；不要从旧介绍猜当前技术栈。
- Twenty：主体 AGPL，并有 Enterprise 文件范围；twenty-ui 的 MIT 许可单独核对过。当前 README 使用 React、Jotai、Linaria。
- LobeHub：LobeHub Community License，基于 Apache 2.0 加额外条件，不能标为纯 Apache。当前有效仓库为 lobehub/lobehub。
- Scira：本次 README 标注 AGPL-3.0；这轮未做代码集成或完整许可审计。
- assistant-ui：MIT；是可组合组件，不是必须使用的整套业务后台。
- Vibe Kanban：Apache-2.0；维护状态以当前停止官方持续运营、转社区维护的公告为准。
- Onlook：Apache-2.0；仓库 README 明确区分早期开放源码视觉编辑器和新 hosted 产品。

## 6. 给 Codex 的使用方式

将本文件作为前端设计参考输入。先完成一套统一设计规范，再实现界面；不因新增视觉参考改变 W01 的底座资格路线。

第一批设计产物建议为：
1. 桌面主工作台：项目导航、当前任务、过程侧栏与成果正文。
2. 研究周期详情：来源覆盖、候选、核验、实验和决策。
3. 成果审查页：摘要、证据、输入版本、实际验证、限制与下一步。
4. 来源/证据列表：筛选、详情、引用定位和失效状态。
5. 资源与手机监督：用量、阻塞、连接状态及暂停/恢复/取消反馈。

统一定义字体、间距、边框、主题、状态颜色和组件；覆盖空态、等待、失败、过期与离线。展示真实后台状态。手机用抽屉/单列承接桌面分栏，不能简单缩小桌面画面。

候选视觉方案还未由用户选择，当前没有新 UI 原型、前端实现或产品验收通过的结论。组件是否采用须通过对应小样与合同兼容验证。

