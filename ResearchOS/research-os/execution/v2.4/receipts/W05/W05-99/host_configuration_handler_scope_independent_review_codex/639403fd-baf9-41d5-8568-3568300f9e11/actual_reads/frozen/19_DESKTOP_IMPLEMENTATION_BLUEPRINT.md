# 19 · Desktop 可执行实现蓝图

版本：2.4.0；日期：2026-10-01。本文补全 [10_UI_UX_DESIGN.md](10_UI_UX_DESIGN.md) 与 [14_CLI_DESKTOP_PRODUCT.md](14_CLI_DESKTOP_PRODUCT.md) 的实现步骤。最终产品是可安装的 ResearchOS CLI 和 Desktop；本文不是“页面做完即产品完成”的替代验收。当前复用来源 `SOURCE_REVIEWED`，产品集成及安装验收 `NOT_RUN`。

## 1. 冻结目标与默认方案

第一优先级是用户在项目里提出工作，系统读代码、修改、运行检查、展示文件成果，并能隔天接续。研究为当前工作提供可用方案；自身改进依据这条工作流的具体阻碍推进。Desktop 默认打开工作会话，不以监控大屏、技术日志或十一张同权重导航卡作为首页。

默认采用 **现有 Go/SQLite 控制面 + Mu CLI/Agent worker + Mu Native Desktop 前端和 Electron 壳**。Mu 固定 commit `8dfebe36508ac0c2508735bb866756dab9283e74`。这是 W01 优先验证路线，不是假定已通过。只有该路线资格失败且一次定向修复仍无效时，进入 **同一 Go 控制面 + 合格 Pi worker + Craft Agents 前端壳**；Craft 固定 commit `73bd9c2a3573158bea880984eb8d5fdb41e0cac2`。两条来源、许可、源码入口和限制见 [Desktop_Reuse_Verification_2026-10-01.md](references/Desktop_Reuse_Verification_2026-10-01.md)。

Claude/Qoder 是体验参照。本包不把尚未找到开放许可的官方桌面前端当作可下载源码。实施时实际复用 Mu，失败才检查 Craft，不继续无限找壳，不同时安装三套主控。

保留当前 `research-os/apps/web/` 已有领域视图、API 与事件消费逻辑，迁入选定桌面壳；保留手机监督入口。桌面主聊天采用选定上游组件。研究/验收/费用等领域界面通过共享 React 模块复用，避免复制两份可各自修改的业务逻辑。页面拆分和目录移动只在对应 W13 owner 内完成，旧测试证据仍保留。

## 2. 唯一业务权威和进程关系

```text
researchos CLI/TUI ────────────────┐
                                  │ 同一 researchos-client 协议
Desktop renderer → 受限 preload ──┼→ Go control + SQLite
                                  │   项目 / Goal / Task / Run / 权限 / 费用 / 验收
手机监督网页 → 已有受控 API ───────┘           │ 唯一派单、租约与停机策略
                                             ▼
                                   Mu 或 Pi worker adapter
                                             ▼
                                    模型 / 文件工具 / 子进程
```

| 层 | 可以拥有 | 不可以拥有 |
|---|---|---|
| Go control | 已有领域事务、scheduler、acceptance、项目身份；会话/命令/事件索引；writer lease/epoch | 将 renderer 的“完成”作为验收证据 |
| worker | 本轮 Agent 推理、工具执行、上游原始会话日志、可复用上下文；按控制面指令执行 | 独立继续业务 Goal、另发业务 Task、清零领域失败/预算计数、签发 ACCEPTED |
| Desktop main | 窗口/菜单/托盘、目录选择、受控凭据输入、core 启动/发现和连接 | 另一套业务数据库、直接独立启动第二个同会话 Agent |
| renderer / CLI | 投影、草稿、用户输入、已授权操作请求、事件水位 | 直接写领域 SQLite、用缓存覆盖服务端事实、把到达 token 数当完成进度 |

“共享核心”允许 Go 服务与 Node worker 多进程，要求业务真值和会话写入权唯一。Mu 的上游 session file 保留原格式时，由控制面存储稳定的本域 session_id ↔ upstream_session_id/file 映射和 revision；不另复制可写 Goal/Task 状态。Desktop 关闭后是否继续由宿主实际能力和设置决定，不能依赖窗口进程仍在而声称持久后台服务。

W01 的最低试验必须证明：Go 唯一创建一条 Run → Mu/Pi 真实 worker 执行 → CLI 与 Desktop 同时读取 → 交接 writer → 旧 writer 被拒 → 取消收到 settled → 一个业务结算和验收入口。只展示一条 mock 流不能通过路线门。

## 3. 源码切口与落地目录

以下是 W02 要建立并登记的产品目录，不代表当前已经存在。若迁移文档已有更具体等价目录，以其登记为准，禁止为满足目录名字复制功能。

| 责任 | 默认目标 | 实施内容 |
|---|---|---|
| Desktop main / preload | `apps/desktop/` | 从已接受的上游壳接续；限制 bridge，嵌入 Go binary 与选定 worker；重设 ResearchOS 品牌 |
| shared React views | 复用 `apps/web/src/`，必要时提取到单一共享 UI 包 | 现有领域 Screen、API、事件 hook；仅在两端确有共同 import 时提取 |
| client adapter | 选定 shell 内单个 ResearchOS client 模块 | 把既有 client.protocol/API 映射到上游 UI props/context；集中转换错误、snapshot 和 event |
| worker adapter | 既有 `adapters/` 下选定运行器适配目录 | 将 Go runtime 指令转换为固定 Mu/Pi RPC；报告实际工具/费用/进程状态 |
| installer scripts | 复用现有 release/ops 与上游打包入口 | 可复现 Windows x64 安装件和独立 CLI 包；升级/卸载保留用户数据 |

Mu 默认改造点是 `desktop/packages/desktop/src/renderer/pages/native/utils/nativeClient.ts` 的 `NativeClientContext`。注入 ResearchOS 实现，并复用 `NativeConversationScreen`、`NativeComposer`、`NativeSiderGroup`、`NativeDialog` 和消息/diff 组件。禁止逐个组件直接拼控制面 URL。

Mu `NativeHost.ts` 不依赖 Electron，`nodeFork.ts` 提供 Node 子进程宿主；W01 验证能否放到 Go supervisor 下。这里的 Node `process.send` / IPC channel 不能当成普通 stdin 直接从 Go 写入：默认先复用 Mu 已有 `--mode rpc` JSONL stdio 入口，由 Go runtime 启动一个固定版本 worker；如果必须使用 NativeHost 才能保留所需能力，在同一 worker adapter 内加入只转发的 Node 启动器，由它调用 nodeFork，不能再建立 scheduler。

Go→worker 只发送经合同映射的 `prompt`、`steer`、`follow_up`、`abort`、查询和已验证的配置操作，携带相关 request ID；worker→Go 返回 RPC response、message/tool 增量、extension dialog、错误和实际 `agent_settled`。stdout 仅传协议、stderr 记录脱敏诊断；Go 负责关联本域 command_id/session_id/run_id、持久事件、预算和退出对账。使用 NativeHost 路径时，它的内部 `init/in/end` 与 `ready/out/failed` 信封只留在 Node 父子进程之间。

生产路径不同时启用上游 AionCore/ACP 的 classic 会话调度。上游 Native/Classic 回退必须改成显式失败诊断，不能在失配时悄悄绕开 ResearchOS 权威。

备选 Craft 只在路线切换回执接受后接入。可用切口为 `apps/electron/src/preload/bootstrap.ts` 和 `src/transport/`；聊天/历史/diff 见证据文件。不上线其独立 `server-core` sessions/tasks/automations 调度，删除未采用的 Claude SDK、旧品牌服务地址和 updater 资源后才构建 ResearchOS 安装包。

## 4. 主界面与十一视图的主次

默认桌面尺寸沿用 token：顶部 56px，左侧项目/历史 216px，右侧进度 280px，中央至少 560px；宽度不足先折叠右侧，再折叠导航，不能挤没输入框。用户可拖动和收起面板；保存窗口/面板/主题属于外观偏好，不成为业务状态。

```text
┌ ResearchOS · 当前项目 / 会话标题       连接状态   搜索  设置 ┐
│ 新任务 / 项目切换  │ 中央工作区                  │ Goal     │
│ 会话历史和搜索     │ 用户输入与 Agent 回复       │ 当前步骤 │
│ 固定/最近会话      │ 工具调用、可展开命令与结果   │ 待处理   │
│ ───────────────  │ 文件 / Diff 可在此打开       │ 已验收   │
│ 文件 / 变更        │                            │ 费用     │
│ 研究与证据         │ 输入框 · 附件 · 模型 · 模式 │          │
│ 成果 / 资源 / 设置 │ 发送 / 停止 · 队列状态       │          │
└───────────────────┴────────────────────────────┴──────────┘
```

| 视图 | 导航级别 | 必须保留的操作和真实数据 |
|---|---|---|
| S00 项目入口 | 未选项目时首页 | 选择已有目录/新目录、最近项目、目录失效恢复；显示初始化四步及真实阻碍 |
| S01 工作台 | 打开项目后的默认首页 | 项目/会话历史、真实输入、streaming/tool timeline、文件与变更、Goal/资源侧栏 |
| S02 研究周期 | “研究与证据”二级入口 | 当前问题、来源覆盖、候选对比、采用/拒绝/待补证、下一动作 |
| S03 任务详情 | 从 Goal/工具/列表进入主区或详情抽屉 | 当前 Run、执行过程、产物、检查、暂停/恢复/取消；回到原会话不丢输入 |
| S04 成果与审查 | “成果”入口，变更也可直达 | 文件树、diff、候选修改、真实检查、封存成果、版本与下载 |
| S05 来源证据 | “研究与证据”二级入口 | 可定位引用、时间、独立来源、有效性和不可访问原因 |
| S06 实验与评测 | “研究与证据”二级入口 | 冻结基线/候选、指标/费用、负结果、缺证据；holdout 按既有边界隐藏 |
| S07 知识与技能 | 项目工具二级入口 | 候选/稳定、来源、使用范围、评测和撤回；真实 Skills/MCP 状态 |
| S08 团队与运行器 | 项目工具二级入口 | 注册、probe、live、qualification 分开；点击真实 Task，不显示虚构在线员工 |
| S09 费用与资源 | 侧栏待处理及底部资源入口 | 已知/预留/未知消费、模型/API/权限资源请求、解决后恢复 |
| S10 设置与设备 | 固定底部入口 | 模型/端点/凭据状态、工具、目录范围、主题、宿主退出行为、设备配对/撤销 |

保留原 URL 可深链与刷新恢复；壳内可映射 app route，不把旧路由全部打断。切换项目取消旧请求/订阅，响应再次校验 project_id。会话查找支持标题/最近更新时间/项目，不做未经需要的全文搜索服务。

## 5. 首次启动：用户不用找端口或复制内部 token

1. 用户运行安装后的 ResearchOS。main 通过固定安装路径启动或发现已存在的同版本兼容 core，按当前 Windows 用户绑定本地连接；健康握手失败显示诊断和重试，不无限转圈。
2. 本地应用内部鉴权由 main/CLI 与 core 自动建立。token/pipe 凭据不出现在 renderer、URL、命令历史、console 或截图。远程手机配对继续使用原配对流程；provider API key 与本机内部连接 token 分开。
3. 展示“选择项目目录”和最近项目。原生目录选择取消时保持原页面；空目录允许初始化，已有目录显示 Git/已有 ResearchOS 身份，不能初始化成第二身份。中文、空格和长路径纳入 Windows 验证。
4. 模型步骤展示“已有可用连接 / 添加连接 / 稍后配置”。默认按实际注册配置发现，不扫描其他项目私有凭据；读取只显示名称、provider、实际 model ID 和可用状态。
5. 添加连接填写 provider、endpoint、model ID 和遮罩 key；key 仅通过受保护宿主入口提交一次，成功/失败后清理 UI 临时值。host.configure 先做格式、身份和授权检查并生成配置引用；provider.probe 随后仅验证实际 endpoint、鉴权和一次推理，分别显示网络失败、鉴权失败和模型不可用。工具能力由首个真实读取、写入或命令 Run 单独验证；尚未验证显示 NOT_RUN，通过后才显示对应工具资格 PASS。连接 READY 不提前代表工具合格，不用 UI 名称代替真实探针。
6. 若已有授权 Qwen3.8 Flash 连接，展示发现的精确 model ID 并固定，不能默默切换强模型。没有该资源可继续浏览项目/历史并配置，阻塞真实推理；不假装“离线 Agent”可调用云模型。
7. 到 S01，输入框可见并获得焦点，给出一个可执行示例：“检查本项目，完成当前任务并运行必要测试”。首次示例执行遵循范围，不自动重写项目。资源充足时不再要求用户手开终端或启动服务。

当前 `apps/web/src/main.jsx` 的手工 `AuthGate` 不能成为 Desktop 首次路径。W02/W13 将它替换为宿主自动连接；保留浏览器/手机必要的认证流程。首次启动向导状态只说明配置步骤，业务初始化结果从控制面获取。

## 6. 会话与工具流的具体交互

### 6.1 输入与历史

- 输入支持中文 IME、多行、粘贴代码、拖入项目内文件。Enter 发送、Shift+Enter 换行；IME composition 未结束时 Enter 不发送。无消息时发送按钮禁用。仅对本轮已授权路径构造附件引用，不把整目录默默塞进上下文。
- 新建会话、重命名、归档/恢复、搜索和复制会话 ID 可操作。归档不删除业务证据。历史分页/分段加载；长会话加载不阻塞整个应用，也不把所有大文件一次读入 renderer。
- 明确显示精确模型、当前权限模式和项目目录。当前会话切模型通过带 session_id/project_id/revision/epoch 的 host.configure，在 Run settled 后原子绑定新 model_config_ref；运行中控件禁用并说明先等待或停止，服务返回 SESSION_BUSY 时保留选择。无 session_id 的 host.configure 只更新新会话默认。指定模型不可用时停在可解释资源请求，不自动降级到其他模型。
- 空闲发送为 NORMAL；运行中可选择“引导当前任务”STEER 或“完成后继续”FOLLOW_UP，队列可查看。取消 run/goal 时清理该目标所属未消费队列；本版不提供按任意 command_id 撤回，移除上游单项 takeback 按钮。收到命令回执后显示“已入队”；不提前清掉尚未确认保存的草稿。
- 每次发送携带独立 command_id；超时先查原命令回执，再决定重发。同 ID 相同 payload 返回原回执，不能重复创建 Run。

### 6.2 输出与进程控制

Assistant 文本流与工具卡按同一 session 序号排序。工具卡显示名称、用途、目标文件/命令、运行/等待/结束状态、退出码、耗时和可展开输出；大日志分段或打开原 Artifact。不能让工具 stdout 伪装成系统成功提示。

用户向上查看旧消息时不强制滚到底；提供“有新内容”跳转。流式 token 合并渲染，不每 token 重绘全历史、不每条 token 发系统通知。代码/Markdown 复制能保留换行。

停止按钮立即显示“正在停止”，调用统一 control 链；等待 worker、工具进程树和队列 settled。`CANCEL_REQUESTED` 期间不能继续派单。连接断开时显示“停止尚未确认”并重连查状态，不能只关本地动画报“已取消”。取消优先于 Goal 自动续跑。

模型说“已完成”、Mu `met` 或 worker `agent_settled` 只进入执行结果阶段；右侧显示“待验收”。只有当前输入/产物版本绑定的 AcceptanceReceipt 才显示已验收。检查失败可点进对应文件/命令/原始输出。

### 6.3 Goal 与待处理事项

Goal 栏显示目标摘要、已验收/计划数量、当前 Task、下一步、阻碍与最近成果。无有效分母不显示百分比。Goal 的业务继续/暂停/取消由 Go 控制面处理，上游 GoalLine 仅作显示组件；不得让其自有续跑和 Go scheduler 同时决定下一轮。

工具权限、缺凭据、额度/来源缺口和需要用户补充的问题用同一“待处理”入口按真实请求 ID 去重，但保持请求种类。卡片说明需要什么、影响什么、授权范围/期限和可选答复；用户已授权的普通动作直接继续。权限按钮不自动扩大项目路径。回答提交后显示“已提交”，等待服务确认已消费；过期请求不可复用到新 Run。

## 7. 文件、Diff 与编辑审查

工作区文件、当前修改和封存成果是三个明确标签。文件树读取授权根目录，不跟随指向未授权位置的链接；路径解析和边界验证在服务端完成。二进制、大文件或不可预览文件显示类型/大小及受控打开，不显示乱码。

1. 点文件读取内容与 revision/content_hash；同时标明工作区当前版本或封存版本。
2. “变更”显示实际 Git/工作区基线到当前内容的文件列表、增删、unified/split diff、检查状态。基线是这次 Task 开始时登记的 hash/commit；已有用户修改单独归属，不能归功于 Agent。
3. 编辑只发生在工作区草稿或候选版本。先从 Goal 的任务页选择已有可编辑 Task，再进入文件编辑器；未选当前任务时保存禁用并提示“先选择当前任务”。保存携带真实 task_id 和旧 revision/hash，服务端验证任务授权后原子比较写入；UI 不生成占位 task_id。用户外部编辑造成冲突时保留双方内容，显示三方比较/复制，不自动覆盖。
4. “应用建议”针对尚未落盘的候选 patch；Agent 已经落盘的修改只显示“已写入工作区/待检查”，不能再有会重复应用的按钮。拒绝建议只弃用未应用候选。
5. 回退已落盘修改先计算当前 hash 是否仍匹配该次产物。匹配时只反向撤销该次修改；不匹配则显示冲突保留用户内容。不得用 `git reset --hard` 或整目录覆盖实现按钮。
6. “运行检查”调用登记的实际构建/测试命令并显示对应 Run；新编辑使先前验收过期。封存 Artifact 只读，新版本另建；下载由既有访问控制校验。

Markdown/HTML/图片/PDF/代码/JSON/CSV 使用 10 中的预览边界，默认超过 5MiB 分块/下载；不执行 Notebook。HTML 独立受限 iframe，默认无脚本/外网，不授予 preload。

## 8. 状态呈现表

| 状态 | 用户看到 | 可做操作 | 不得出现 |
|---|---|---|---|
| Empty | 选择项目/创建会话和明确示例 | 选择目录、配置模型、输入任务 | 虚构历史、默认跑示例业务 |
| Connecting/Loading | 当前加载区域、耗时、可展开诊断 | 有界重试、返回；历史可用部分继续看 | 永久 spinner、整屏白页 |
| Ready | 当前项目、模型、会话和输入框 | 发送、查文件、切页 | 不明来源绿色“正常” |
| Streaming | 正在回复/当前工具、停止、队列 | 滚动、复制、STEER/FOLLOW_UP | 固定假打字、伪造工具输出 |
| Approval needed | 具体动作/范围/请求 ID、允许/拒绝 | 对真实请求作答 | 每步索要重复授权、默认全盘允许 |
| Credential required | 连接名、缺口、受保护设置入口 | 配置/检查/取消 | 回显已存 key、在聊天里索取 key |
| Execution reported | 产物和“待验收” | 打开 diff/检查 | 把 met 或 0 退出码叫已验收 |
| Check failed | 哪项检查失败、原始输出、下一步 | 修复/重试有效范围 | 隐藏失败后继续显示 PASS |
| Conflict/stale | 外部版本已变化，旧草稿保留 | 查看 diff、合并再保存 | 刷新基线后覆盖旧内容 |
| Offline | 最后同步时间、水位、状态可能过期 | 看缓存历史、恢复连接 | 假推进动画、离线写入报成功 |
| Core/worker lost | 恢复对账中，Run 未确认 | 查看诊断、等待对账/取消 | 自动启动第二 writer |
| Cancel requested | 正在停止或停止未确认 | 查询、重连 | 父进程退出就报工具已停止 |
| Accepted | 当前版本检查与验收回执 | 打开成果、继续下一工作 | 未核实的人造分数 |

UI 状态不能引入新的 Task 枚举；暂停效果按原合同中 Task/Run 与原因组合表达。界面文字简体中文，技术 model ID/路径/命令保留原样。

## 9. API/IPC 对接冻结清单

以 `contracts/client.protocol.schema.json` 的 `researchos-client/2`、`contracts/product.contract.json`、[22_CLIENT_INTERFACE_DETAILS.md](22_CLIENT_INTERFACE_DETAILS.md) 和既有业务 API 为权威。下表给出确定映射，W02 实现对应 handler 与测试，W13 直接消费；不能自行改名、透传任意 PiCommand 或用成功 stub 补接口。

| UI 动作 | 对接责任 | 必须固定的数据/拒绝条件 |
|---|---|---|
| 启动/设置 | host.status、host.configure；瞬态 native bridge `credential.import` | 版本、能力、配置 revision、provider/base_url/model_id/credential_ref；密钥不进入普通 CommandEnvelope/事件 |
| 项目/目录 | 瞬态 native bridge `workspace.choose` → workspace.register/list → project.bootstrap | 稳定项目/目录引用、目录身份；取消 picker 不初始化，失效目录可解释 |
| 会话历史/管理 | session.list/create/get/attach、session.update | 稳定会话 ID、model_config_ref、分页/快照；RENAME/ARCHIVE/UNARCHIVE 由服务处理 |
| 发言/控制 | session.send、session.control、session.handoff、goal.start | command_id、NORMAL/STEER/FOLLOW_UP、expected_revision、writer_epoch、receipt |
| 模型发现/连接检查/选择 | provider.models、provider.probe；配置和当前会话选择写入 host.configure | provider、精确 model_id、连接可用性与配置引用；probe 仅验 endpoint/鉴权/推理，工具资格由真实 Run 单独记录；带 session_id 时必须 revision/epoch 且 Run settled，否则 SESSION_BUSY；刷新 session.get |
| 权限回答 | permission.respond | resource_request_id/revision、action_digest、ALLOW_ONCE/DENY、reason；服务读取冻结 action 并检查当前 Run/输入/范围/有效期 |
| 文件树/读取 | workspace.tree、workspace.read | workspace_ref、相对路径、分页/大小/编码、content_hash；拒绝越界路径 |
| 工作区差异 | workspace.diff | base=INDEX/HEAD、可选 relative_path、max_bytes；返回 before/after hash、patch、binary、truncated 和完整 diff Artifact 引用 |
| 草稿保存 | workspace.write | 从 Goal 任务页选已有可编辑 Task 获得 task_id；未选时保存禁用。提交 workspace_ref、relative_path、task_id、expected_content_hash、text、create_if_missing；覆盖必须匹配旧 hash，创建必须旧 hash=null 且目标不存在 |
| 附件导入 | artifact.import | 受控项目内文件→Artifact 引用；session.send 只传 attachment_artifact_ids，不把任意本地路径当可读附件 |
| 领域页/成果 | 既有 API 中 Project/Goal/Task/Run/Artifact/Decision/Acceptance/Resource/Progress | 权限、ETag/revision、真实状态；没有 API 的按钮不能先假成功 |
| 重连 | session.events + 既有 EventEnvelope/快照 | cursor、session seq、run/command 关联、缺口、重放去重与当前快照 |

Mu NativeClient 的具体适配：list→session.list；create→session.create；open→session.get/attach(request_write_owner=false)；request 中 prompt/steer/follow_up→session.send，abort→session.control(CANCEL)，set_model→带当前 session_id 的 host.configure，其余命令逐项白名单；respond→permission.respond；rename/remove→session.update(RENAME/ARCHIVE)，不用 remove 删除原始证据；onRecord/onChanged/onStatus→session.events 与 SessionSnapshot 投影；pickFolder→瞬态 workspace.choose。打开历史不会抢 writer；控制权只能通过显式 attach/handoff 请求取得。

工作区 diff 的 INDEX/HEAD 基线与 Task 开始前冻结 Artifact 是两个不同视图。任务成果对比读取冻结的 before/after Artifact 内容及 hash，由同一 diff viewer 展示；不得把 workspace.diff 的 base 擅自发送成未定义的 task_id/commit。

Desktop preload 仅暴露本表已登记的窄操作，验证 sender/frame 与输入；禁止通用 `shell(cmd)`、`readFile(anyPath)` 和任意 IPC channel。窗口 `contextIsolation=true`、`nodeIntegration=false`，不可信预览不获得应用桥。外链由受控 main 打开系统浏览器。

## 10. CLI → Desktop → CLI 同会话验收步骤

1. 安装后在授权示例项目执行 `researchos init <path>`，再开启 CLI 会话。记下 project_id/session_id，在会话内要求读取一个文件、作有限修改并运行已有检查。
2. Desktop 从最近项目打开同一个 session_id。可以看到真实先前消息、工具产物和运行状态；不会复制成一个“同标题新会话”。此时默认只读订阅，界面标明控制权在 CLI。
3. 点击“在此继续”。当前只读 Desktop 发送 session.attach(payload.request_write_owner=true)，envelope 携带已观察的 expected_revision（至少 1），writer_epoch 必须为 null；宿主验证与现 owner 属于同一已鉴别 OS 主体，将它作为显式接管请求。忙时先暂停并确认 settled，保留 Task、Goal、队列和检查点，再通过 CAS 原子增加 epoch；并发接管只接受一方。ACK 时仍只读，COMPLETED 的 snapshot 返回新 epoch 后 Desktop 才取得 writer，CLI 降为只读。session.handoff 保留给当前 writer 主动转移，普通打开历史仍 attach(false)。
4. 从 CLI 用旧 epoch 发送一条写命令，应拒绝且不能创建第二 Run/文件修改。Desktop 发 FOLLOW_UP，检查继承实际上下文和文件基线。
5. 关闭窗口再开，恢复该 session 的快照/事件；消息不重复、费用不重复、未确认工具不会自动重做。
6. CLI `researchos resume <session-id>` 请求接回，Desktop 降为只读。CLI 运行剩余检查，再在 Desktop 看真实 diff 与验收结果。
7. 任一端取消长工具，观察两端都等待并最终显示同一取消回执；检查工具子进程已结束，不只检查 UI。

W01 可以用最小壳进行资格试验；W06 是当前协议/核心的真实检查；最终 W13/W14/W20 必须在正式 Windows 安装后的 Desktop 复验。不能以协议测试客户端冒充成品桌面。

## 11. Windows 安装、升级和生命周期

首版目标 Windows 11 x64，默认每用户安装到 `%LOCALAPPDATA%\Programs\ResearchOS`，业务数据到 `%LOCALAPPDATA%\ResearchOS`。安装目录包含 Electron、编译 Go control、选定 worker 及其运行时/许可。普通用户不需先安装 Node/Bun/Go 或打开管理员终端；Git/外部工具若确需单独提供，应在 doctor/向导明确探测和引导，并且基础读取/编辑/非 Git 项目仍可使用。

CLI 独立发行包与 Desktop 使用同一数据根、协议兼容检查和 supervisor 发现机制，不能同时启动两套 core 写同一 SQLite。注册 PATH 如需重新打开终端，安装结束明确说明并提供可复制的程序路径；这不能影响 Desktop 正常启动。

首次默认关闭窗口最小化到托盘时，只在持久宿主门通过后允许“任务继续运行”；托盘菜单必须提供打开、真实任务状态、暂停和退出。显式“退出并停止”先取消/settle/保存再退出。用户选择后台继续时关闭 renderer 不终止 core；启动失败或无持久宿主时，保存检查点并明确暂停。Windows 睡眠与重启后先 RECONCILING，不凭时间推断工作完成。

升级安装前检查运行中任务与数据库版本；只在已保存检查点/安全阶段进行本地替换，迁移失败保持原可启动版本与备份。卸载默认保留业务数据；删除数据是单独明确选择，不能由测试脚本偷偷执行。禁用上游应用更新地址，未配置 ResearchOS 更新服务时采用已验证的本地新安装包更新，不引入额外云服务。

W20 产物至少含 `ResearchOS-<version>-win-x64` 安装件、独立 CLI 包、sha256、来源/许可清单、构建 revision/lockfile、安装/升级/卸载保留数据说明和实际测试回执。是否签名照实标注；没有签名凭据不能写“已签名/无警告”。安装验收必须在没有开发 Node/Go/Bun 的干净 Windows 用户环境完成；源码 `npm run dev` 不替代。

## 12. 分工、实施顺序与必须留下的检查

| 顺序 | WBS owner | 修改范围与具体步骤 | 交付/通过条件 |
|---|---|---|---|
| D01 | W01 | 固定 Mu revision/锁文件/许可；先复用 NativeClientContext，接最小 Go/worker adapter；构建最小窗口；跑第10节核心子集 | 一个 session 一个 writer；真实文件/工具/取消与回执；路线回执包含失败和一次修复记录 |
| D02 | W02 | 冻结第9节全部操作；登记 frontend/worker handler；壳自动发现 core、受限桥、白名单、模型设置骨架 | 同源合同校验；未实现操作明确失败；首次启动不手抄内部 token |
| D03 | W05/W06 | CLI 和壳共享 session identity/lease/command/event；接真实 worker、control、permission、model | 自动化命令与最小交接测试；旧 epoch 拒绝；取消清队列并核对进程树 |
| D04 | W13 | 先 S00/S01/S04/S10，再把现有其余领域视图接入；完成第5–8节状态/交互 | C23/C24/C25/C26 与 P03 真实连接证据；不存在空按钮、fixture 成功或缺 handler |
| D05 | W14/W17/W19 | 真实研究→采用→编辑→检查；IPC/预览/权限；离线、renderer crash、休眠/重连 | 原 A10/A11/A13/A14 相关断言；真实环境缺口单列 BLOCKED，不补假记录 |
| D06 | W20 | 固定发行组成、改品牌/更新源、许可、构建；干净安装、升级、CLI↔Desktop 复验 | P07/A15；安装件 hash 与测试用 binary hash 一致 |

最小检查按真实风险聚合，不为每个样式函数增加测试。必须覆盖：

| 检查 | 断言 | 对应既有门 |
|---|---|---|
| First-run | 干净用户安装后选择目录→配置实际模型→发送一条工具任务；无需手工 token/端口/启动服务 | P03/P07，C23/A15 |
| Stream/input | 中文 IME Enter 不误发，多行/队列/停止正确；长历史不重复、滚动不跳 | C23/C24/C26 |
| Files | 真实修改→diff→检查；并发外部编辑保存冲突不丢内容；已写 patch 不重复应用 | C25，A04/A13 |
| Shared session | 两端同 ID、单 writer、旧 epoch 拒绝、重连 cursor 去重 | P02，C01/C26 |
| Request/security | 真实权限回答幂等，过期不消费，credential 不落 transcript/log，越界 IPC/路径失败 | P04，A11 |
| Lifecycle | renderer crash、关闭/后台/显式退出、取消子进程、睡眠恢复均与 core 一致 | P05，A14 |
| Visual/accessibility | 双主题，既有5视口、320px/200%缩放、键盘焦点/读屏label、减少动效；关键页面截图 | C24 |
| Install | 无开发运行时启动；CLI 同数据；升级保留项目；卸载保留数据 | P07，A15 |

每条回执绑定当前应用版本/源码 revision、操作序列、输入/产物 hash、实际命令、截图/录像或可追溯日志、失败与限制。截图证明实际呈现，后端回执证明业务结果；二者都需要。测试与视觉证据中不得包含凭据正文。

## 13. 此蓝图不允许省掉的差距

Mu 的组件存在、Craft 的 Apache 许可、已有 Go 控制面测试通过，都不能直接宣称 Desktop 合格。W01 未通过不得跳过集成去批量做页面；W13 不得留下“以后接 API”的主流程；W20 不得以网页压缩包替代安装件。首个可用里程碑优先完成完整工作链，完整发行仍保留十一视图、研究/判断/恢复/独立验收的原要求。

## 14. 可打开的交互设计预览

[ui/workbench-prototype.html](ui/workbench-prototype.html) 是本地单文件预览，覆盖 S00/S01/S04/S10 的主要组合。直接用浏览器打开即可；不需 Node、服务或网络。项目/会话导航、主题、Goal/文件/Diff 标签、输入与工具卡、请求答复、首次设置、失败/断线/缺凭据状态和冲突保留草稿可以操作。每个结果都是标明的示例，不连接 provider、不执行命令、不读取项目文件、不保存真实凭据。

顶部状态选择器可切换场景；地址附加 `?theme=dark&view=review` 可直接看深色审查布局，附加 `?selftest=1` 可运行内置 DOM 自检。伪代码只说明视觉布局，真实接口仍以第9节和机器合同为准。预览不增加产品视图数量，也不替代 Mu/Craft 源码复用和正式 Desktop。

本包制作时实际验证：内嵌 JavaScript 语法通过；无外部资源/网络调用；本机 Chrome 的8项 DOM 自检通过（主题、tab、离线禁写、输入、示例消息、冲突保留草稿、历史筛选、dialog）；1440px 浅色与390px深色实际渲染已检查，390/320px 的 document.scrollWidth 等于视口宽度，输入区未越界。没有验证原生安装、真实 Agent、真实 provider、IPC、安全边界或完整无障碍；这些仍由正式验收门承担。
