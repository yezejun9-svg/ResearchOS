# 22 · CLI/Desktop 可实施接口细则

版本：2.4.0。机器定义：`contracts/client.protocol.schema.json`。本文件约束待实现接口；协议校验通过不代表客户端、宿主或外部模型已运行。所有产品验收初始状态为 NOT_RUN。

## 1. 实现边界与协议版本

本包使用 `researchos-client/2`。原有 12 个方法名及其 payload 字段保留；新增有类型的响应、事件、快照和必要本地操作。W02 同步锁定 CLI、Desktop 和宿主的协议版本，旧 `/1` 客户端不能静默接入 `/2`。握手不支持时返回 `UNSUPPORTED_PROTOCOL`，界面提供升级入口；不能把版本不兼容显示为空历史。

只存在一个 ResearchOS 宿主及一个业务调度、事务和验收权威。Mu/Pi worker、CLI、Desktop 均调用它；`SessionSnapshot` 是该宿主对现有 Project/Goal/Task/Run、原生会话映射和事件日志的投影，不是另一套任务状态机。CLI 的 `/goal`、headless run、Desktop 输入框走相同处理器。

Mu 路线优先在 `renderer/pages/native/utils/nativeClient.ts` 的 `NativeClientContext` 注入本协议适配。`NativeHost.ts`/`nodeFork.ts` 可作为唯一宿主启动 worker 的窄切口；源码可复用不等于当前 Windows 包已经验证。

| 原生客户端动作 | 本产品调用 | 必须保留的语义 |
|---|---|---|
| list / create | `session.list` / `session.create` | 只列当前主体有权访问的项目；创建不自动派第二个 Agent |
| open | `session.get` 或 `session.attach(request_write_owner=false)` | 打开页面默认只读订阅，不抢写入权 |
| prompt / steer / follow_up | `session.send` 的 NORMAL / STEER / FOLLOW_UP | 持久入队确认和实际执行分开 |
| abort / pause / resume | `session.control` | 转同一真实工具停止/恢复链 |
| set_model | `host.configure`，绑定当前 session 时必须 CAS | 活跃运行不静默换模型 |
| respond | `permission.respond` | 只响应原 ResourceRequest 的同一冻结动作 |
| events | `session.events` | 按 session sequence 重放，不重发工具 |
| rename / archive | `session.update` | 修改展示元数据；archive 不代表取消或完成 |

禁止将任意上游 `PiCommand`、shell、Node 或 fs API 透传到 renderer。适配器使用此表列出的允许分支；未映射命令明确返回 `UNSUPPORTED_METHOD`。

## 2. 首次本机使用：身份、工作目录、模型

### 2.1 本机主体和连接

首次打开已安装 Desktop 或运行 `researchos` 时，受信 main/CLI 连接同一 OS 用户的本地宿主。Windows 默认使用仅当前 OS SID 可访问的 named pipe；若选其他传输，W02 必须给出等价的身份验证和独占启动证明。宿主发现信息位于当前用户应用数据目录且受 ACL 保护；内容不得包含可被网页读取的长期秘密。

本机 bootstrap 由受信宿主核验 OS 身份后原子执行：已有 OWNER 则绑定现有主体；确无主体时才初始化一次。重复启动不创建第二个 OWNER，不重置权限或数据库。renderer、普通 HTTP 请求、手机配对和不可信页面没有创建 OWNER 的入口。`NativeUserBootstrapResult` 仅包含身份引用、client_id、host_instance_id 和协议版本；`credential_exposed_to_renderer=false`。

短期连接认证由 main/CLI 与宿主完成，过期后重新核验 OS 本地身份并续期。用户不复制后台 token、不翻日志、不读秘密文件；认证过期不得清掉项目和会话。远程手机仍使用原设备配对/TLS 合同，不借本机 bootstrap 提权。

并发 CLI/Desktop 首次启动通过 OS 互斥和活宿主身份探针发现已有实例。陈旧 PID/端口记录不能触发误杀其他进程；启动失败返回诊断，不创建并行可写数据库。

### 2.2 不进入持久命令流的两个 native 入口

以下仅由受信 main/preload 或 CLI 本机交互调用。它们的 Schema 位于 `Native*` 定义中，刻意不属于普通 `CommandEnvelope` 的方法枚举，也不属于协议根消息的 `oneOf`。

| 瞬态入口 | 请求 / 响应定义 | 行为 |
|---|---|---|
| `native.workspace.choose` | NativeWorkspaceChooseRequest → NativeWorkspaceChooseResult | Desktop 使用系统目录选择器；CLI 的显式 `init <path>` 或交互确认提供路径。宿主解析真实路径、junction/symlink、访问范围，生成 5 分钟有效、绑定本机主体/client 的单次 selection_ref。取消选择不产生授权。 |
| `native.credential.import` | NativeCredentialImportRequest → NativeCredentialImportResult | 受控设置表单或隐藏回显的 CLI 输入读取凭据，直接交宿主受保护存储；只返回 credential_ref。替换必须提供已属于该主体/供应商的 replace_credential_ref；不覆盖别人的引用。 |

凭据原值只能短暂存在于输入控件、受信 IPC 和宿主凭据存储。提交/失败/取消均清空输入；不得进入 CommandEnvelope、command journal、事件、Artifact、会话、遥测或日志。验证错误不回显原值。没有“读取秘密”接口；普通响应只返回引用和 AVAILABLE/MISSING/REVOKED 状态。引用撤销后新调用失败，不能自动从其他项目借密钥。

普通 `workspace.register` 消费 selection_ref 并返回持久 `authorized_workspace_ref`。所请求权限不能超过目录选择时的授权；同一次命令重放返回原绑定，换 command_id 重用已消费 selection_ref 返回 `SELECTION_ALREADY_USED`。授权根被撤销后保留历史引用，拒绝新读写，不把不可访问目录显示为空目录。

### 2.3 首次使用的确定顺序

1. 受信本机 bootstrap → `host.status`，取得主体、client_id、已有目录和当前配置 revision。
2. `native.workspace.choose` → `workspace.register`，取得 authorized_workspace_ref；已有目录可从 `workspace.list` 选择。随后 `project.bootstrap` 建立/恢复本地项目身份和盘点任务，此步无需模型；为后续探针提供唯一 project_id 和原费用账本。
3. `native.credential.import`（供应商需要凭据时）→ `host.configure`，填 provider_id、base_url、model_id、credential_ref；`config_revision=current+1`，首次为 1。保存配置不自动发模型请求。
4. 按用户点击“测试连接”或既有明确授权，在上述 project_id 范围内调用一次 `provider.probe`；真实失败保留配置和可离线查看的历史，不谎报已连接。列模型先读缓存，明确刷新才联网。
5. 核对 `project.bootstrap` 返回的当前目录绑定；同一永久项目再次打开复用原 project_id，目录别名变化不新建项目。W04 的本地盘点可先完成，后置研究未完成仍如实显示。
6. `session.create` 使用同一 workspace_ref 和返回的 model_config_ref；`session.attach(request_write_owner=true)` 获得快照和写入 epoch，再发送用户任务。

CLI 的路径识别与 Desktop 选择目录执行同一流程。首次配置之外，恢复已有项目不得要求重复复制已保存设置。headless 缺配置返回退出码 2，缺授权/外部资源返回 3；不突然弹不可见输入框挂住流水线。

## 3. 方法、payload、result 完整映射

本表与机器 Schema 顶层 `x-method-contracts` 相同。所有 COMPLETED 响应必须匹配本方法的 result；响应不能用任意 object 表示成功。公共字段见第 4 节。

| method | payload | COMPLETED result | 处理要点 |
|---|---|---|---|
| host.status | EmptyPayload | HostStatusResult | 本机能力、身份引用、配置、凭据状态和目录绑定；不触发收费探针 |
| host.configure | ConfigurePayload | ConfigureResult | 新配置版本；同 revision 不同内容拒绝 CONFIG_CONFLICT |
| project.bootstrap | BootstrapPayload | BootstrapResult | 引用已授权目录，复用已有项目身份；原项目导入不重置 |
| session.list | ListSessionsPayload | SessionListResult | limit 1–100；cursor 绑定主体、项目和查询 |
| session.create | CreateSessionPayload | SessionSnapshot | 校验目录属于该项目和配置可见性；不复制调度器 |
| session.get | EmptyPayload | SessionSnapshot | 原子快照，包括事件水位、writer、上下文和待处理权限 |
| session.attach | AttachPayload | AttachResult | false 为只读；true 必须 expected_revision 且 writer_epoch=null，经授权/CAS 申请、续租或同主体显式接管 |
| session.send | SendMessagePayload | SendMessageResult | NORMAL/STEER/FOLLOW_UP；入队不等于工具或验收完成 |
| session.control | ControlPayload | ControlResult | PAUSE/RESUME/CANCEL；target 必须属于当前 session 的 Goal/Run |
| session.events | ReadEventsPayload | ReadEventsResult | limit 1–1000；只读重放 |
| session.handoff | HandoffPayload | HandoffResult | WHEN_SETTLED / PAUSE_THEN_TRANSFER；事务转移 owner/epoch |
| goal.start | StartGoalPayload | StartGoalResult | 同现有 Goal 服务；draft 不执行；非 draft 沿现有任务/验收门推进 |
| provider.models | ListModelsPayload | ListModelsResult | 缓存优先；refresh=true 还必须 allow_network=true |
| provider.probe | ProbeProviderPayload | ProbeProviderResult | 一个已配置模型，一次请求，最多 32 输出 token、30 秒、零自动重试 |
| workspace.register | RegisterWorkspacePayload | WorkspaceBinding | 消费受信选择器产生的 selection_ref |
| workspace.list | EmptyPayload | WorkspaceListResult | 仅当前主体可见授权目录，不扫描其他项目 |
| workspace.tree | WorkspaceTreePayload | WorkspaceTreeResult | 当前目录一层、分页、最多 500 项；不递归读全盘 |
| workspace.read | WorkspaceReadPayload | WorkspaceReadResult | 最多 1 MiB UTF-8 文本；返回精确字节 hash，禁止静默截断后保存 |
| workspace.diff | WorkspaceDiffPayload | WorkspaceDiffResult | INDEX 或 HEAD；读实际 Git 差异，未跟踪文件明确列出 |
| workspace.write | WorkspaceWritePayload | WorkspaceWriteResult | session CAS、writer epoch、task 授权、文件 hash CAS；生成新草稿产物 |
| artifact.import | ImportArtifactPayload | ImportArtifactResult | 从已授权路径导入附件/Goal 合同并封存字节；作为资料不自动取得执行授权 |
| session.update | UpdateSessionPayload | SessionSnapshot | RENAME/ARCHIVE/UNARCHIVE；重命名 title 非空，其余 title=null |
| permission.respond | RespondPermissionPayload | RespondPermissionResult | 对原 ResourceRequest 冻结动作 ALLOW_ONCE 或 DENY |

`host.configure` 不携带凭据原值。未提供 session_id 时只更新新会话默认配置，已有会话保留固定 model_config_ref。提供 session_id 时还必须提供 project_id、expected_revision、writer_epoch；宿主只在相关运行已 settled 后更新当前会话配置，忙时返回 SESSION_BUSY。历史 Run 保留原配置/模型版本，下一次运行才用新版本；绝不由失败降级静默换成另一模型。

`provider.models` 明确刷新时最多一次目录请求、30 秒、零自动重试；分页需要新的明确请求。供应商不支持列举时返回 CONFIGURED_ONLY，用户手输的 model_id 不因未出现在列表就被否定。`provider.probe` 只检查已配置端点和模型，不串行尝试别的账户、模型或供应商，不测试全部目录项。真实费用进入原 BudgetLedger；未知 money=null，不能写 0 冒充免费。网络动作仍服从项目授权和策略；allow_network 不是绕过策略的凭证。

## 4. 命令、响应与字段生命周期

CommandEnvelope 固定包含 `protocol_version, command_id, client_id, project_id, session_id, expected_revision, writer_epoch, method, payload`。不适用的作用域字段显式 null。schema 通过只说明形状正确；宿主仍校验认证主体、当前授权、跨项目引用和对象版本。

| 字段/引用 | 产生位置 | 有效范围及失效 |
|---|---|---|
| client_id | 受信宿主登记当前 CLI/Desktop 客户端 | 绑定 OS 主体和客户端实例；同实例重连可恢复，不能由 renderer 冒充别的 owner |
| command_id | 发起客户端生成 UUID | 只表示一个逻辑请求；重试原请求沿用，修改 payload 必须新 ID |
| selection_ref | native.workspace.choose | 一次消费、5 分钟、同主体/client；不是长期目录授权 |
| authorized_workspace_ref / workspace_ref | workspace.register | 两者引用同一目录绑定；真实规范路径、授权 revision 和撤销状态由宿主保存 |
| credential_ref | native.credential.import | 同主体/供应商的受保护引用；撤销即时拒绝新调用，永不解析给 renderer |
| model_config_ref | host.configure | 固定 provider/base_url/model_id/credential_ref/config_revision；已有 Run 永远保留其使用版本 |
| session_id / native_session_ref | session.create 的单一宿主事务 | 客户端 ID 与原生会话映射永久保存；重开不能新建副本冒充恢复 |
| revision | 当前 session 投影 | 修改会话控制状态、配置、owner、标题、Goal/Run 关联时递增；token 事件和 lease 续期不导致无意义的用户命令冲突 |
| writer_epoch | 宿主租约事务 | 每次取得/转移/失效后重新授予严格递增，不能因进程重启归零 |
| event sequence | 宿主持久 session event journal | 每 session 单调递增；与域事件序号分别命名；快照绑定原子水位 |
| ArtifactRef | 原 Artifact 服务 | id/revision/hash 固定；重新编辑生成新 Artifact，不覆盖封存内容 |

`CommandResponse` 包含 method、protocol_version 和原 command_id。状态语义：

- ACKNOWLEDGED：请求已持久接收，result 为 PendingResult，后续通过同命令重放、会话事件和快照对账；不能显示完成。
- COMPLETED：本方法已经完成其操作，result 使用表中类型。`session.send` 的完成只代表合法入队；`goal.start` 的完成只代表 Goal 已按返回状态建立。
- REJECTED：result=null，error_code 与 error.code 相同，附脱敏错误、correlation_id 和明确恢复动作；不产生该命令的新业务副作用。

幂等存储键包含主体和 command_id，存规范化完整请求 hash、接收/完成状态及响应。相同键相同请求重放原状态/结果；不同请求返回 COMMAND_ID_CONFLICT。旧 epoch 的已执行命令可以读取原回执，但不能再次执行；未执行的旧 epoch 请求拒绝。transport 断开或客户端超时不能自动把未知结果当失败后新建命令重试。

本机凭据、网络认证头和瞬态 native 请求不进入普通请求 hash/journal。对 workspace.write 的大文本保存内容寻址引用并按同一原始字节校验；日志只记引用与 hash，不复制整个用户文件。

## 5. 单写入者、取消、恢复和重放

### 5.1 归属和 CAS

session.send/control/handoff/workspace.write 必须带快照中的 expected_revision、writer_epoch；宿主在同一事务核对并写入命令意图。旧 revision 返回 STALE_REVISION，旧 epoch 返回 STALE_WRITER_EPOCH；客户端先刷新快照，显示变化，再决定重新提出请求，不能自动换新 revision 盲重试写入。

`session.attach(request_write_owner=false)` 只读取/订阅，不取得或续期 writer。目标端“在此继续”和 CLI resume 的显式接管入口使用 `session.attach(request_write_owner=true)`：expected_revision 必须是刚读取的快照 revision，writer_epoch 必须为 null，因为请求者尚未取得写入 epoch；不能冒用源客户端的 epoch。返回的新快照才给出可供后续写命令使用的 epoch。

宿主先检查普通项目/角色权限，再核验请求客户端与当前 writer 属于同一已鉴别 OS 本机主体。这个本机接管能力不授予远程 READER/手机或其他主体。普通权限不满足返回 FORBIDDEN；已可读但非同主体的接管返回 WRITER_BUSY。连接认证过期先重新鉴别 OS 身份，不能用旧 epoch 代替身份。

显式接管按以下固定步骤执行：

1. 在事务内核对 expected_revision 和当前 owner，登记已有 command journal 中的唯一待交接意图。快照已变化返回 VERSION_CONFLICT；已有竞争交接返回 WRITER_BUSY。同一 command_id 重放原回执，不重复暂停或转移。
2. 无 writer 且无未决工具时可直接授予；请求者已是当前 writer 时只续租。同主体其他客户端仍持有有效 writer 时，宿主受理显式接管请求，返回 ACKNOWLEDGED，目标客户端继续只读。
3. 若源端正在运行，先暂停新派发，在安全点等待当前工具/子进程 settled 并持久保存检查点。保留原 Goal/Task、工作成果和未消费 follow-up 队列；接管自身不调用业务 CANCEL、不删除队列、不新开一个写入 Agent。
4. 对账完成后再次 CAS 核验当前输入、权限及交接意图，原子转移 owner，增加 epoch 和 session revision，然后发 CLIENT_HANDOFF 并返回 COMPLETED/AttachResult。目标端只有此后才可发写命令；要继续执行仍需显式 RESUME/发送指令，交接本身不自动恢复工作。
5. 并发输家、过期快照或中途发生影响交接的版本变化返回 WRITER_BUSY 或 VERSION_CONFLICT；不得自动替换 revision 重试。无法确认 settled 时不提交转移，保留可见的待处理/阻塞及原归属，不隐式取消来制造成功。
6. 等待期间用户主动 CANCEL 仍服从原控制权和停止链，其优先级高于接管/自动续跑。后续即使合法转移控制权，也不能复活 CANCELLED Run 或清除 resume_requires_explicit_user。

lease 默认 90 秒、受信活客户端每 30 秒以 attach(true) 和当前快照续租，时间由宿主判定；同 owner 续租不改 epoch。续租遇到版本变化先刷新；只有仍确认自己是 owner 才能继续自动续租，不自动变成对别人的接管。其他客户端只读访问不会延长 writer lease。

owner 失联/过期不能证明其工具已停止。若仍有活动运行，显式接管先请求原运行在安全点暂停，并核对工具/队列已 settled；未确认前保留只读、返回 ACKNOWLEDGED 或 CANCEL_UNCONFIRMED，不能给新 owner 启动第二个 Agent。宿主自身崩溃后先按原 Run/checkpoint/副作用账本对账，再递增 epoch。旧工具回报保留审计但不能覆盖新版本。

handoff 是当前 writer 主动交给目标端的入口；目标端主动接管使用上述 attach(true)。handoff 的 target_client_id 必须已鉴别、在线且属于同一本机主体、可访问同一项目。WHEN_SETTLED 等待当前工作稳定结束；PAUSE_THEN_TRANSFER 先走暂停确认。只有完成停止/对账后，单一事务转移 owner、递增 epoch 和 revision，随后发 CLIENT_HANDOFF。旧客户端保持只读；超时、目标离线或 CAS 冲突不能形成双 owner。

### 5.2 人工控制

PAUSE 停止派发新工具并在可中断点保存检查点；有不可中断工具时显示等待，不伪报暂停。CANCEL 清理本任务队列、取消活动工具及子进程，并记录 cancel_requested_at；只有实际确认后填 cancel_confirmed_at/settled_at。无法确认返回可追踪待处理/阻塞，不能把父进程退出当取消成功。

RESUME 只允许当前有效暂停/恢复上下文；显式取消的 Run 不自动复活。用户重新提出继续时，宿主沿原 Goal/Task 和检查点建立有来源的新 attempt/run，原 CANCELLED 记录、预算、失败计数和事件水位保留。`resume_requires_explicit_user=true` 时自动启动、重连、定时器均不得越过。取消一个运行不等于清空项目全部任务。本版不支持任意 command_id 的队列单项撤回；CANCEL 的 target_id 只接受当前 session 关联的 Run/Goal，并清理其所属未消费队列。上游 takeback 单项按钮须移除，不能保留无实现的成功提示。

archive 只调整会话列表展示；活跃运行须先暂停/取消并完成停止确认，否则 SESSION_BUSY。rename/unarchive 使用 expected_revision；不引起模型运行或重放工具，不能把归档视为删除历史或验收通过。

### 5.3 快照与事件

session.get 返回在同一读取边界形成的 SessionSnapshot：session/project/workspace、原生会话引用、核心和模型配置、当前 Goal/Run 原状态、writer、revision、event_sequence、检查点、pending commands/permissions、最近最多 200 条消息及完整 transcript Artifact 引用。没有更早消息时 has_earlier_messages=false；有截断时必须提供完整 transcript_artifact_ref，不能默默丢历史。

客户端先用快照整体替换本地投影，再读取 after_sequence=event_sequence 的事件。每个事件以 event_id 去重、以 session sequence 排序；序号断档停止增量合并并补读。游标早于保留窗口返回 CURSOR_EXPIRED 及 REFRESH_SNAPSHOT；cursor 绑定不同项目/查询返回 CURSOR_INVALID，不能从零重放工具。

MESSAGE 事件绑定 message_id、part_index、START/DELTA/END 和 UTF-8 字节 offset。DELTA offset 必须等于该 part 当前 UTF-8 字节长度；重复 event_id 不重复追加，offset 不符重新取快照。工具 stdout/stderr 存 Artifact，事件只带摘要和引用。ERROR、PERMISSION_REQUIRED、PERMISSION_RESOLVED 都有严格 payload。USAGE 引用唯一 ledger_entry_id，重复事件不重记账。JUDGE_DECISION 标明实际状态和用途/模式，NOT_RUN 不生成虚构成功判断。

只读订阅不能触发模型、工具、费用、通知或自动接受。重开 Desktop/CLI 始终先恢复快照和 owner 状态；renderer 崩溃不会直接更改任务结果。

## 6. 文件、diff、草稿保存和附件

所有 workspace 操作核对 project_id、workspace_ref、真实路径、授权 revision 和当前主体。路径 schema 只是第一层：宿主每次打开前解析 Windows junction/symlink、UNC、设备路径、ADS、大小写和尾点/尾空格别名，拒绝逃出已授权根。不能仅靠字符串 startsWith 判定。目录树可展示不允许进入的链接，但 readable=false 并有原因。

workspace.read 返回 UTF-8 原始字节 hash。二进制返回 UNSUPPORTED_CONTENT，过大文本返回 CONTENT_TOO_LARGE；需要特殊预览走原受控 Artifact 预览，不能将截断文本保存覆盖源文件。界面收到错误保留用户已有草稿。

workspace.diff 的 base=INDEX 是工作区对暂存区，base=HEAD 是工作区/暂存区对 HEAD，未跟踪文件分别标记 UNTRACKED。返回每文件前后 hash、实际 patch 和 base_revision；非 Git 目录返回 NOT_A_REPOSITORY。超过 max_bytes/500 项时 truncated=true，并提供完整 diff Artifact 引用；不以截断预览作为全部变更验收。

workspace.write 只写该 session 关联项目、明确 task_id 授权范围内的工作文件。task_id 必须来自已存在、当前可编辑且已获对应写范围授权的 Task。未选择有效任务时，UI 保留本地草稿并禁用保存，显示“请先选择可编辑任务”，链接到已有 Goal/Task 页面；不得编造 ID、自动创建 DRAFT Goal/Task，或因按下保存启动模型。选择现有合法任务后重新核对当前输入、权限和文件 hash 才启用保存。已有 task 的 accepted 产物/封存 Artifact 不可覆写；后续修改必须由已授权的后续任务承接。保存时：

1. 核对 session revision/epoch、task 当前输入版本、允许路径和写权限；Agent 活跃工具可能改同一路径时先暂停并确认稳定，不能客户端和 worker 同时直写。
2. `create_if_missing=true` 只允许目标不存在且 expected_content_hash=null；已存在返回 CONTENT_CONFLICT。修改已有文件使用 false 和完整读取到的 expected_content_hash；实际字节不符返回 CONTENT_CONFLICT，同时保留用户草稿。
3. 经 CLI、Desktop 和 worker 共用的安全写处理器执行：同根同路径锁、原始字节备份、内容寻址候选、持久写意图、平台原子替换和回读 hash。所有内部写入服从此处理器；不能 UI 写 fs、Agent 另开无约束写路。
4. Windows 外部编辑器不受进程内锁约束。平台适配须保留替换前字节并检测替换窗口竞争；不能证实 CAS 时拒绝 EXTERNAL_WRITE_RACE，保存双方版本并等待选择。不得覆盖后删除冲突版本，也不得以“最后写入者获胜”冒充 CAS。
5. 成功返回 before_hash、after_hash、新草稿 ArtifactRef 和快照。草稿可被继续编辑，每次新产物版本；保存成功不等于 Task 已验收。

artifact.import 只读取授权文件并封存精确字节，返回 ArtifactRef/字节数/media_type；提供 expected_content_hash 时内容不符拒绝。附件中的指令按资料处理，不扩大项目授权。输入框附件使用返回的 artifact id；Goal 合同使用同一导入入口，不让小模型猜如何得到 contract_artifact_ids。

## 7. 权限请求只处理原动作

待决定权限来自现有 category=PERMISSION 的 ResourceRequest。SessionSnapshot 和事件投影其原状态 OPEN/ACKNOWLEDGED/RESOLVED/CANCELLED；不新增另一套权限业务状态。`PermissionActionScope` 正文封存为 Artifact，记录 project/task/run、tool、参数 Artifact、允许路径、输入版本、模型配置、issued_at/expires_at、max_uses=1 和 USER_DECIDABLE/POLICY_DENIED 来源；action_digest 对冻结正文计算。

UI 展示具体动作和范围后才能响应。permission.respond 包含原 resource_request_id、resource_request_revision、action_digest、ALLOW_ONCE 或 DENY 与原因。宿主重新读取当前 ResourceRequest/Task/Run/授权，检查同项目、输入版本未变、请求未关闭、scope 未过期且权限仍允许用户决定；任一不符拒绝，不用前端给出的值覆盖权威记录。

ALLOW_ONCE 仅对原动作的同一 task/run/参数生效，消费写入现有副作用/幂等账本；重放只返回原响应。宿主封存决定 Artifact，并通过原 resolveResourceRequest 流程写入 resolution_evidence_refs。DENY 同样留证，原任务保持适当阻塞/取消，不会因为请求“已处理”就获准继续。未获其他必要资源时 resumption_scheduled=false；解决权限请求不等于任务完成。

系统/平台已拒绝的 policy 动作返回 POLICY_DENIED、policy_allows_user_decision=false，界面不提供允许按钮。普通 permission.respond 不能消除既有 policy 拒绝，不能借新 request_id、新 session 或 OS bootstrap 重新归零；真正外部授权变化仍需原恢复条件和独立证据。

## 8. 错误恢复、实现顺序和验证样例

| 错误类别 | 客户端动作 | 禁止行为 |
|---|---|---|
| UNAUTHENTICATED | main/CLI 重新鉴别 OS 用户；remote 走原设备认证 | 要用户从日志复制 token；重建 OWNER |
| STALE_REVISION / STALE_WRITER_EPOCH / VERSION_CONFLICT | 刷新快照，说明当前 owner/版本，再重新决定；VERSION_CONFLICT 用于接管 CAS | 自动改版本号覆盖当前状态 |
| WRITER_BUSY / SESSION_BUSY / CANCEL_UNCONFIRMED | 保留只读和等待/取消状态 | 新起第二个写同一工作区的 Agent |
| CONTENT_CONFLICT / EXTERNAL_WRITE_RACE | 展示源文件与用户草稿差异，保留双方 | 静默覆盖或丢用户草稿 |
| CREDENTIAL_MISSING / MODEL_UNAVAILABLE / RESOURCE_BLOCKED | 打开原设置或资源请求，继续可离线操作 | 猜供应商、静默换模型、借别项目密钥 |
| POLICY_DENIED | 显示已有拒绝与恢复条件，继续独立支路 | 通过本地确认、重连或新请求绕过 |
| PROVIDER_TIMEOUT / 网络中断 | 读同 command_id 回执，对账未知结果 | 自动新 command_id 重复收费调用 |
| CURSOR_EXPIRED / CURSOR_INVALID | 取当前快照，从原子水位接续 | 重跑已发生工具或重复追加 token |

W02 固定 transport/native bridge 和方法映射；W03 落 Session 映射、typed result/event、幂等/CAS、目录绑定与身份引导；W05 接真实 worker/CLI、provider 配置/探针及安全文件工具；W06 接单 owner、权限动作和独立接受；W13 消费相同接口补齐 Desktop；W17 验证 native/权限边界；W19/W20 用持久宿主和安装包复验。前置 mock/fixture 不能代替后置 live 证据。

最小机器正负样例必须覆盖：

- 正：host.status 的严格响应；完整 SessionSnapshot；MESSAGE 三阶段和 USAGE null 费用；首次目录选择→register→bootstrap；已有 credential_ref 的 configure；有已授权探针；正常 workspace.write CAS；允许一次原权限动作。
- 负：CommandEnvelope 携带 credential_value；随意 result={ok:true}；TOOL_RESULT 缺 tool_call_id；未知 method/event；旧协议当新协议；跨项目 workspace_ref；越界路径；写入无 hash/旧 hash；尚在运行时改模型；失效 owner；不同 payload 重用 command_id；过期权限/已 policy 拒绝仍 ALLOW_ONCE；重复 delta/重复收费。
- 恢复：两客户端并发抢 owner 只一方成功；写入完成但响应丢失重放只发生一次；handoff 中断不双写；取消子进程未停不报成功；关闭窗口重开先快照；游标过期回补后事件/费用不重复。

A04/W05 验真实 CLI 和工具；C01/W06 验协议双向接续；C23–C26/W13 验界面到这些动作的请求和回执；A11/W17 验本机身份/路径/IPC/权限拒绝；A13/W14 和 A15/W20 验最终真实双端项目流程与干净安装。上述新增断言挂回原 22 个 WBS 和 42 个用例，不替换或减少原研究/Jev/恢复/自我改进门。
