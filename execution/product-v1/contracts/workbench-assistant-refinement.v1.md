# ResearchOS 工作台小范围改进审查

日期：2026-11-05。只读工程/产品表面审查；交付在 C 盘。未改 D 盘、未占生产源文件 lease、未启动应用/浏览器/Codex CLI/模型、未运行测试。此文是待实施提案，不是完成验收。未使用正式 Product Design audit：其 shared critical-overrides 资源不可用；不作 WCAG 合规结论。

## 结论与优先级

保留现有 React 工作台，将 Native Codex 主流程收敛成一个对话画布、一处常驻输入区、一条简短上下文栏和真实事件侧栏。优先修复 FAILED 后仍“等待真实运行回执”的状态矛盾，再减少空态前置面板；不需要新原型、框架、后端协议或新的审批流程。

1. **失败状态可信度（优先）**：`blocked.png` 中 Host 明确返回 “Native preparation failed before model launch; no automatic replay”，下方仍显示“任务已接收，等待真实运行回执”。`workbench.jsx:465–474` 将 submit 的 accepted 布尔值当作持续等待状态；`harness.js:139–154` 在 ACK 后会读取当前 Task，可能已经 FAILED，也可能读取断开，但 accepted 仍应为 true。这不是 controller 错误；不要为消除文案而改变 ACK、journal 或重发语义。
2. **第一屏主次（优先）**：`04-1440x1000-dark-initial.png` 顶部依次出现 Harness、项目标题、项目会话空态、工作区、任务标题、禁用操作、无 Task 提示，然后才是欢迎与输入。receipt 记录 welcome heading y=667.99、composer y=825.88；页面总高 1807。`04-390x844-light-initial.png` 输入区 y=984.53，首屏不可见；welcome y=737.84 已贴近底部导航。根因包括 `workbench-layout.jsx:4–10` 无任务时默认展开历史，`workbench.jsx:481–486` 连续空态，以及 `workbench.css:7–10,15` 最小高度叠加、移动端 composer 改成 static。
3. **右栏价值**：`workbench.jsx:488` 把 14 行实现/不支持清单放在 ActivityRail 前，挤走项目近况和事件。真实投影已存在于 `activity-rail.jsx:7–36`，工具/运行事件无需新造数据。`harness-progress.js:18–39` 也已按 Task/Run/epoch 去重计数，必须保留“当前事件窗口”限定。

## 建议的实际行为

**首次进入**：保留左侧既有功能、数据入口和主题设置；中心顶部只显示简短项目名，以及 Harness / 已授权工作区选择。移除重复的 RESEARCH/WORKSPACE 介绍层级；Harness 切换说明放详情，选择器的可访问名称不改。历史收起为“最近任务（数量）”，无任务时只出现一句空态。工作区选择从历史面板移到上下文，不能因为收起历史而隐藏首次提交所需选择。未授权时在输入区旁显示真实阻止原因与现有项目入口；不新增路径授权机制。

中心空态采用简短欢迎语和适合只读模式的建议（例如“梳理目录与入口”“解释 README”“查看现有测试说明”）；当前共享欢迎项“运行必要测试”不应诱导 Codex 只读首版超出能力。建议通过参数给现有 ConversationWelcome 传 Codex 专用短项，Mu 保持原行为。无 Task 时不渲染 HarnessRunProgress 占位和取消/暂停/恢复行。已有 Task 时将现有进度组件放到右栏，主画布先显示用户目标和回答/失败结果。

**布局**：沿用现有色彩 token，深色优先检查；弱边框、单一强调色，等宽字体仅用于 `researchos >`、工具名和技术标识。桌面画布是可收缩内容行 + 输入行，避免多个 min-height 累加；右栏保持约 280px。移动端使用可用高度内的对话区域和输入行，考虑现有 64px 底部导航/safe-area；上下文可换行，次要内容放可展开“运行与项目近况”。不要仅用 fixed 浮层盖住消息。小高度/放大时允许必要滚动，不能裁掉阻止原因或操作。输入区与发送按钮在常规 1440×1000、390×844 首次进入均应无需滚动可见，长历史滚动时仍可发现输入入口。

**有 Task**：中心保留用户消息及真实 ASSISTANT_MESSAGE/result；没有模型回答时不补写回答。右栏按当前任务进度 → 项目近况/最近真实事件 → 状态与能力详情排列。复用 ActivityRail 和 HarnessRunProgress；无记录时显示真实空态，绝不补造工具过程、提交、百分比或思维链。其事件轨迹是当前 Task 已读历史，进度工具计数是当前 Run 窗口；不要把两者都标成“当前 Run”。

**本次失败**：主结果展示“任务未完成”，结合已返回的明确 preparation 文本显示“准备阶段失败，模型未启动；未自动重试”。不能仅凭 HARNESS_UNAVAILABLE 代码推断所有失败都发生在模型启动前；未识别原因使用一般失败提示。详细 code、原始 message、Task ID、revision、Run/epoch 放“技术回执” disclosure。输入区可保留新的用户草稿，失败本身不触发重发。刷新操作仍只读刷新；新提交由现有 canSend、pending 和权限规则决定。终态时取消不再可执行，绝不把 CANCEL_REQUESTED 显示成已停止。

**状态投影**：取消“提交成功即写入永久等待文案”的副作用。让当前 Task status、pending journal、读取错误驱动展示；ACK 后快照读取失败应提示已记录请求但结果待核对，不能用 null Task 推断未提交。明确区分 queued/starting/running/cancel-requested/failed/blocked/unknown/completed/cancelled。切换 Task/项目时旧成功提示不跟随；pending UNKNOWN 的原请求核对始终可达。保留现有 draftVersion/controller 身份防护，不增加自动 retry。

**权限与实现状态**：上下文或输入区附近保持简短但明确的“只读 · 执行未验证/范围未验证/取消未验证”摘要，阻止提交的 HarnessPermissionNotice 保持可见。安装/登录不等于执行验证。详细能力表收入“状态与能力”，用“接口已实现；实际验证状态见下方”区分 source-implemented 与 execution-verified。禁止将 captured UNVERIFIED 变成已验证；不宣称取消已被 live-qualified。保留 Native picker、opaque workspace refs、submit/cancel 参数、ARIA 名称、草稿及 journal。

## 建议隔离 lease：仅 4 个生产文件

| 文件 | 必要改动 |
| --- | --- |
| `apps/web/src/workbench.jsx` | Codex 专用紧凑上下文、工作区移出历史、按 Task 渲染空态/结果、状态驱动提示、右栏重排与能力详情、只读建议项；保留原边界调用和草稿保护。 |
| `apps/web/src/workbench.css` | 对紧凑 Codex 布局用角色/状态类控制高度、间距、输入行和右栏；保持浅深主题、焦点、减弱动画和移动端导航边界。 |
| `apps/web/src/components/workbench-layout.jsx` | 添加可选历史标题/初始展开策略及布局 variant，Codex 空态默认收起；默认值保持 Mu 行为；仍为纯展示组件。 |
| `apps/web/src/harness-progress.js` | 增加小型纯回执展示投影供 workbench 调用，状态/未知/错误有优先级且不持久化等待文案；保留既有 scope-bound progress 逻辑。 |

不需要改 `harness.js`、`activity.js`、`activity-rail.jsx`、`harness-run-progress.jsx` 或 Desktop/Host/DTO。它们是审查与回归依赖，不在建议写范围。后端 owner 的现有 exact4 domain scope 与本提案无交叉。注册未来独立 lease 后可实施，不必再造用户审批步骤。

## 最小验证计划（尚未执行）

- 扩展现有 `tests/ui/desktop/harness-workbench.test.mjs`：真实 controller+受控 bridge 返回 ACK 后立即 FAILED，及 QUEUED→tick→FAILED；断言实际视图/其生产回执投影不再声称等待运行，submit 始终只一次。覆盖 ACK 后 get 失败、Task 切换及新草稿、UNKNOWN pending、取消请求非终态。保留既有 edit-away-and-back、卸载、替换 controller 防丢草稿用例。
- 扩展现有 `tests/ui/harness-progress.test.mjs`：新回执投影覆盖所有终态与 pending/error 优先级、空 Task、明确 preparation 原因与一般 HARNESS_UNAVAILABLE 的区别；保留工具去重、旧 epoch、外 Task 和无事件窗口语义。
- 在前述 workbench 测试里以实际组件渲染/受控更新断言：仅一主输入；工作区/输入/阻止原因不藏在默认关闭的历史或技术详情里；ActivityRail 在能力详情之前；空态没有取消/暂停/恢复噪声；切历史不丢草稿。不要用 CSS 字符串存在性或复写视图算法充当行为测试；如当前测试设施仅适合纯函数，明确把布局行为留给以下真实渲染检查。
- 后续由 Root 在授权的隔离验证环境复用现有几何探针，检查两种主题的 1440×1000 与 390×844 初始页、长历史、失败页及移动端输入聚焦：输入框与发送按钮实际可见且命中、无横向溢出、不遮消息/底栏、历史/技术详情可展开、关键权限原因可达。这是必要的真实布局证据，不能由 unit test 替代。本审查不启动它。
- 仅回归读取/执行已有 `tests/ui/desktop/activity-projection.test.mjs` 和 `tests/ui/desktop/assistant-startup.test.mjs` 的相关用例；无需为未修改的桥接协议新增镜像测试。此处所有测试仍是计划，未声称通过。

## 证据与限制

实际查看三张图：`04-1440x1000-dark-initial.png`、`04-390x844-light-initial.png`、`blocked.png`，目录为 `C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-native-synthetic-acceptance-中文-run-01/screenshots/`；均为合成测试内容。

读取 `receipts/workbench-responsive-visual.json`：18 scenarios，父任务说明 15 screenshots；本审查仅直接查看上述 3 张。JSON 自报 `PASS_MEASURED_VISUAL_GEOMETRY` / `NOT_RUN_ZERO_BUDGET`，其“通过”不能证明首屏信息层次合适，因为 390 初始场景明确 `composer_visible=false`。source_head 为 `998fc6330ba735056cd31f8ebf68dd50a8251c1b`；父任务当前 Main 为 `8fa407dbf393f94424e1612748d9e6041db35fcd`、CP687。审查时实际文件 SHA256 与捕获指定一致：workbench `7855f855814feb99e5d96f25f762cfb1abeba3ee211e3c214e5b2d0f447c62fd`，CSS `432e001ee045d6881f449a5a02aa76c365e8776b5c979d074d94d27496d0598e`。这是文件级对应，不把两次 HEAD 混为一谈。

父任务提供的真实流程结论：NativeShell 选源 → 单一实际 Task → preparation FAILED，未得到模型回答；原 Job 经强制超时现为 STOPPED / active0。完整旅程 0/13、正式验收 0/42；本审查未重新验证这些运行状态，也不推断强制停止等于产品取消资格。源码可证明已实现投影和控制入口，不能证明模型执行/只读隔离/取消通过实际验证。

剩余事项：本轮只完成审查与提案；UI 未实施，布局未重捕获，失败根因仍属后端 owner 范围。没有阻断本审查的权限拒绝或待审批动作。