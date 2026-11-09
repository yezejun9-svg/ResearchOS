# 配对手机监督与 Mu 暂停恢复：独立架构诊断

状态：READ_ONLY_ARCHITECTURE_DIAGNOSIS；手机产品未就绪，正式接受新增 0/42。本报告只确认当前 Source 的因果路径与可审查施工范围；未运行产品、测试、手机、GUI、模型、隧道或外发消息，未生成配对秘密。用户偏好已固定为“产品流程准备好后使用自己的真实手机”，无需再次询问。

输入 Main 为 `1004cf9b8414ee4a248301ead447bc4a022f87d7`。当前规格来自 `execution/v2.4/current_spec.json` 指向的 `.local/worktrees/v24-continuation/spec/v2.4`，manifest SHA256 `4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964`。上游只读诊断为 `execution/v2.4/receipts/W05/W05-99/phone_product_flow_readonly_diagnosis_codex/20261012-current-chat/diagnosis-01.md`；本目录 manifest 记录实际重新读取的文件 hash。旧回执、失败计数、Source、Canon 和冻结门槛均未改动。

## 结论

可以独立准备配对后的只读会话与项目监督，但不能把这一步称为“手机监督准备好”。真正暂停/恢复还有明确的 Mu 队列、检查点及运行恢复缺口；原工具权限审批也未闭合。网关和 V2 核心接线应在 workspace4 冻结后由 Root 串行整合。与 workspace4 四文件不重叠的 Runtime 因果修复可作为第二 Source 候选，须先登记精确范围与单一 owner。

手机始终是实际 DeviceActor。issuing owner 仅用来计算当前项目授权与只读会话归属委托，不替换调用 principal，不继承本机 OS 主体或 writer。`22_CLIENT_INTERFACE_DETAILS.md:132,147` 禁止远程 attach(true)/handoff 取得本机 writer；OWNER 项目 grant 不改变该限制。正常 V1 项目监督控制可以保留其既有角色和 ETag/幂等契约，不能借此绕过 V2 writer 或本机工具权限。

## 已核对的生产路径

| 位置 | 当前事实 | 影响 |
|---|---|---|
| `remote_auth.go:21` | authenticate 后动态交集 device 与 issuing owner 的授权；禁止受限资源和创建项目 | 复用真实身份，不另造 Owner token |
| `gateway/main.go:106,121` | 仅 V1 与静态白名单；V2 POST 落入静态限制 | `/v2/command` 当前不可达；只允许精确单一路径，不开放 `/v2/*` |
| `api/v2.go:154,185` | token 和 project grant 后直接 Execute，无 remote marker/device-only 边界 | 只改网关不安全；直接 loopback 的 device token 也要受相同方法限制 |
| `client_protocol.go:710,902` | Execute 在 dispatch 前幂等回放；session owner 检查是 creator principal | 当前授权及远程方法限制必须在 replay 前；只读归属要显式委托 |
| `client_protocol_sessions.go:69,103,251` | creation receipt 唯一性核验；list 过滤其他 principal；旧无 receipt 会话本机兼容 | 远程缺失或冲突创建证据默认拒绝；不能将同项目任意会话授权给设备 |
| `Continuity.jsx:60,75,79` | client_id 固定 desktop-renderer；token 变化重建 client；快照 epoch 自动 adopt | 手机使用独立稳定 client_id 与凭据 getter；不把 writer epoch 变为手机权力 |
| `orchestration_controls.go:8,22,35` | 仅 CANCEL 调 fenceClientTask；PAUSE 标 Task BLOCKED、Run CANCEL_REQUESTED | Task 状态不能证明 Mu 安全暂停 |
| `runtime_coordinator_windows.go:627` | CANCEL_REQUESTED 取消 broker；QueueRequired 时不立即 bridge.Cancel | 还需正确的队列停止协议 |
| `runtime_command_queue_windows.go:225,495` | 只有 CANCEL_FENCED 发 command.clear_abort；未 fenced 的 broker error 直接失败 | 当前 V1 PAUSE 可能进入错误/恢复路径，不能宣称正确暂停 |
| `orchestration.go:314,344,384` | RESUME 等待 Run terminal 后将 Task READY；claim 拒绝非 OPEN、restore_fenced 或已绑定 run 队列 | 原 Mu 队列不能被 V1 RESUME 重派发 |
| `client_protocol_queue_control.go:45..109` | fenceClientTask 将未派发 ENQUEUED 标 DROPPED，其余要求 clear 证据；设置显式恢复标记 | 取消围栏不能直接作为保留队列的 PAUSE 实现 |
| `adapters/runtime/mu/worker.mjs:681` | clear_abort 调 clearQueue/abortEffects/abort，未消费项发 cleared | 把取消按钮换名暂停会丢后续消息 |
| `adapters/runtime/bridge_windows.go:370` | turn.paused 需持久 checkpoint 已 ACK | 有接收端约束，不等于 Mu 实际支持暂停 |
| `worker.mjs:818..845` | 实际启动 session.prompt，最终产 turn.completed；未发现 checkpoint/turn.paused 生产与恢复入口 | 必须补生产接线，不能以 Bridge 类型存在宣称能力 |
| `migrations/sqlite/0022_client_command_queue.sql` | fence 主键为 project/task；generation 唯一；queue 引用 generation；状态不含 PAUSED | 同 Task 多 attempt/generation 不能通过重写旧 fence 或加字符串解决 |
| `client_permission.go:217`、`client_workspace.go` | 原 permission 要 workspace 本机绑定及原 principal，device 被拒 | 手机响应一般资源请求不等于批准原工具动作 |
| `resources_recovery.go:8` | 通用 recovery 明确不授 runtime permission | 不可将 ResourceRequest RESOLVED 当作 permission ALLOW_ONCE |

以上是源码因果判断，没有运行断言。原 `orchestration_controls_test.go` 使用通用 Run 夹具，不能替代真实 Mu queue/checkpoint/worker 路径证明。

## 最小生产增量：手机只读

保持冻结方法/结果形状。允许设备调用 `session.list/get/events/attach(false)`；拒绝其他 V2 方法及 null-project 请求。attach(false) 只读、不续 writer 租约；返回快照包含 writer 的既有字段并不授予权限。绑定服务端可验证的每设备 client_id（例如从 DeviceID 确定的命名空间），不能信任客户端自报 desktop-renderer 或其他设备 ID。

每次调用同一动作事务中重新读取 device 状态、issuing owner 状态、双方当前 project grant、请求方法及目标会话唯一 creation receipt。actor/幂等记录/审计仍使用 DeviceID；owner 仅是只读资源归属 resolver 的输入。cursor 绑定实际 device/project。该核验必须在两种幂等回放路径之前，且设备撤销、移除项目、issuing owner 撤销/撤权立即作用于重放。OWNER 降为 READER 后，合法只读仍允许，控制拒绝；不把正常降权误写成所有读取禁用。

| 批次及 owner | 精确候选 Source | 完成判据 |
|---|---|---|
| 远程边界，Root 串行 | `ops/remote_access/gateway/main.go`、`main_test.go`；`internal/api/v2.go`；新增 `internal/api/v2_remote_test.go` | exact-origin/TLS/header 边界不退化；只放行精确 POST `/v2/command`；网关本机 token 拒绝；device 直连也拒写 |
| DeviceActor 只读授权 | 新 `internal/domain/client_remote.go`、`client_remote_test.go`；`internal/domain/client_protocol_sessions.go` | 活授权、唯一归属、分页、跨设备/跨项目/缺 receipt/冲突 receipt/撤销及 replay 负例；不做 Owner impersonation |
| 核心接线，等待 workspace4 freeze | `internal/domain/client_protocol.go` 仅 Execute replay 前 policy 调用、只读 dispatch resolver 接线 | shared file 不并行编辑；两个 replay 路径均受门控；普通本机行为保持契约 |
| 手机界面 | `apps/web/src/Pairing.jsx`、`main.jsx`、`screens.jsx`；新增 `RemoteSupervision.jsx`、`remote-session-client.js`、`tests/ui/mobile/remote-session-client.test.mjs` | 配对后真实项目/会话选择；费用/通知/任务来自现有 V1 投影；凭据轮换不重置客户端身份或未决操作；禁止本机配置/目录/模型/写入表面 |

project-supervision 不需要新 V2 method：复用已授权 V1 getProjectState/getProgressProjection/listNotification 与必要 task/run/resource 读取，按实际 session 的 project/task/run 关系绑定；客户端输入不能伪造映射。只读阶段不自动 markNotificationRead，不控制 Runtime。QR 可后加本地编码；依赖和 lock 必须 Root 精确登记，不使用外部 QR 服务。首批可复用正常复制链接；但不能据此宣称用户手机流程已准备齐全。

## 第二 Source：W12 Mu PAUSE/RESUME 因果范围

回答是否可复用现有 fence：可以复用身份校验、CAS、append-only receipt、epoch/process binding、停止观察和 effects reconciliation 的原语；**不能直接调用 CANCEL fence 来完成 PAUSE**。它会把 ENQUEUED 变成 DROPPED、清 SDK 队列，并保持不可重开。PAUSE 必须保留可恢复的已接受未消费消息与检查点；明确 CANCEL 仍清队列且优先于 PAUSE/RESUME。强行把 state 改 OPEN、清 run_id、删除旧 receipt 或换 Task 绕过计数都不合规。

冻结 22 §5.1/5.2 要求在安全点停止新工具、保存检查点，未知停止时可见等待；同一 Goal/Task 恢复，有来源的新 attempt/run，原 CANCELLED/预算/失败计数/事件水位保留。完整恢复不能把整个原 prompt 再跑一遍。旧 Run 已确认的外部副作用和工具结果只能对账/复用，UNKNOWN 不能当未执行或免费。保持模型/账户/用途/预算原约束，缺资源只阻塞本支路。

建议分两次可审查 Source，不将阶段一冒充手机 ready：

1. **M1 安全暂停与持久恢复上下文。** 以既有 V1 actOnTask 为生产入口，识别 mu_turn，原事务登记幂等暂停意图与接纳围栏，停止新队列/工具派发，保留未消费消息。worker 在可中断安全点发真实 checkpoint、等待宿主封存 ACK，再发 turn.paused；非中断工具继续显示等待。真实进程停止、流结束、effects 与费用观测持久后才确认暂停。共享 CANCEL 仍拥有优先权；崩溃按原 journal 恢复，不虚构 stopped/queue_empty。此阶段有真正暂停证据，但尚未完成恢复就保持控制流程未就绪。
2. **M2 同 Task 显式恢复与代际接续。** 只有 M1 checkpoint 与旧 Run/SDK/子进程/流/副作用均可核验，当前权限/输入/模型/预算有效且用户明确 RESUME，才原子保留 Goal/Task/session，建立新 Run ID 与递增 lease_epoch，绑定 checkpoint 来源及新的 queue attempt。只迁移有确定未消费证据的消息，保持 command_id/content_hash/次序与既有 receipt lineage；CONSUMED 不重发，UNKNOWN 先对账。旧 Run/generation 不开放，迟到 frame 不覆盖新 epoch；断网/reconnect/重复 RESUME 不造第二个 Run。

M2 需要内部存储设计先明确：`0022` 仅一条 fence/project/task，不能容纳多个不可变 generation。Root/migration owner 应登记**新的追加迁移**及 per-attempt queue/lineage 支持；不得修改旧 `0022` 或冻结 schema21/合同。可采用保留原 generation 的 per-attempt ledger 与明确 successor 关系，但必须让 runtime binding、pending/settled 查询、恢复和备份统一认识新 attempt；不能旁路第二队列调度器。迁移文件名/编号由 owner 分配，本报告不猜号。若暂不授权迁移，完整 M2 仅该支路 BLOCKED，其他已授权源代码工作可继续。

| M1/M2 因果模块 | 精确候选文件 | 责任与范围 |
|---|---|---|
| V1 操作→暂停/恢复 | `internal/domain/orchestration_controls.go`、`orchestration.go`、`orchestration_recovery.go`；新增 `mu_supervision.go`、`mu_supervision_test.go` | Mu 分支的原意图、停止条件、恢复 CAS；保留通用 Task 行为、取消优先与失败计数 |
| 运行/队列调度 | `internal/domain/runtime_coordinator_windows.go`、`runtime_command_queue_windows.go`、`runtime_recovery_windows.go`、`runtime_sessions_windows.go`；新增 `runtime_supervision_windows.go`、`runtime_supervision_windows_test.go` | 既有 sole coordinator 接线；pause 控制、checkpoint ACK、原 epoch 对账与真实投影；不得另开 scheduler |
| 队列接纳/停止查询 | `internal/domain/client_command_queue.go`；新增 `client_queue_resume.go`、`client_queue_resume_test.go` | 显式暂停围栏，不消费/丢弃消息；M2 attempt lineage、pending/settled 语义；原 generation 永不重开 |
| worker 生产者与 bridge | `adapters/runtime/mu/worker.mjs`、`worker-control.test.mjs`；`adapters/runtime/bridge_windows.go`、`bridge_control_windows_test.go` | 真安全点暂停、checkpoint emit/ACK/restore；保留 SDK receipt、进程身份和流完成证明；third_party/mu 只读 |
| 新 Run/checkpoint 绑定 | `internal/domain/runtime.go`、`runtime_dispatch.go` | 只在明确 M2 因果需要时登记：新 Run 初值 checkpoint 当前为 null；需要有来源恢复材料而非篡改旧 Run |
| 追加内部迁移及恢复兼容 | 新迁移（owner 分配）；`internal/domain/backup_command_queue.go`、`backup_command_queue_test.go`、`backup_queue_upgrade.go`、`backup_queue_upgrade_test.go` | 由迁移/备份 owner 串行；若 per-attempt 设计触及备份，证明新空目录还原仍保留围栏和 lineage，不引入秘密 |

这是明确候选集，不是已获写授权。Root 可以先登记 M1 前五行中的实际因果文件与测试，再在 M2 数据设计冻结后登记迁移及备份文件；无需先动 `client_protocol.go`、`client_protocol_workspaces.go`、`client_protocol_workspaces_test.go`、`internal/api/v2_configuration_windows_test.go`。这四个 workspace4 文件严格排除，相关 V2 session.control 接线等 workspace4 冻结后串行。M1/M2 共用因果状态，不再拆成并行多个 writer。W12-02 原 write_scope 并不自然覆盖上述所有 domain 文件，必须由 Root 通过现有 W02 精确问题映射登记，不可凭“属于 W12”自行扩写。

## 验收矩阵与阻塞边界

| 层次 | 必须证明 | 不能替代 |
|---|---|---|
| DeviceActor Source/fixture | local-token remote 拒绝；device spoof client_id/跨项目/cursor/creator 拒绝；唯一 issuing owner 只读；撤销/撤权在 replay 前生效；写/attach(true)/handoff 拒绝 | A11 LIVE |
| Mu M1 fixture + native Windows worker | 原 V1 PAUSE→真实 checkpoint→ACK→turn.paused→进程/流停止；未消费 FOLLOW_UP 保留；中途不可中断/崩溃/未知副作用保持等待；CANCEL 胜出 | 手机控制与真实 provider LIVE |
| Mu M2 fixture + native Windows worker | 原 Task/session/Goal；新 Run/epoch/attempt 单次创建；消费消息不重发、未知消息对账；旧 frame/旧 receipt/旧 token/并发 cancel 无副作用；费用 UNKNOWN 不归零，已确认费用不重复累计；恢复不换模型 | 原实时任务、真实手机恢复 |
| A10-01/02 | 真实手机内容、六阶段/计数/覆盖缺口/阻塞、可关闭抽屉、窄屏及焦点/操作 | 响应式截图 |
| A10-03 | 真 Run 等待/失败/只读/陈旧标识，PAUSE/CANCEL实际服务回执；Root另核W17-03真实RESUME | 动画、BLOCKED状态或仅HTTP 200 |
| A10-04 | 自动 accessibility 与独立人工实际操作、缺陷定位与结论 | 实施者自签 |
| A10-05 | 干净 Windows 安装包首次使用、目录/已有模型/真实会话、跨15分钟重开、无手工 Owner token | 只读手机或本机旧验收 |
| A11-01/02 | 真实单次短时限项目配对；过期/重放/无认证；撤销下一请求拒绝、敏感控制每次核验；若有已连事件流≤30秒断开 | poll方案不能自行删掉冻结事件流断言；应由正式selector覆盖相应宿主流边界 |
| A11-03/04/05 | 真秘密隔离、已验证TLS/default-local、IPC sender/frame及本机凭据边界；当前构建CLI/Desktop回归 | 网关单测或模板描述 |
| 工具权限审批 | 原请求revision/action_digest/USER_DECIDABLE/expiry/task/run/input/授权；独立手机委托契约与生产 handler | 通用资源 resolve |

可以写到本机的候选测试包括现有 `orchestration_controls_test.go`、`runtime_command_queue_windows_test.go`、`runtime_recovery_windows_test.go` 和上列新增测试。测试必须通过生产 V1 handler/coordinator/worker，不直接写 DB 设置已暂停来造成功。native 夹具与真实模型测试区分；本轮不运行任何模型或手机请求。

W17 最终 A10=`test.ui`、A11=`test.security`，均 LIVE_WINDOWS。当前 formal_case_requirements 中两者 `registered_selectors=[]`，需注册者实际绑定逐断言执行器；未注册/零断言不能 PASS。C17 最终 Owner 是 W13，不因列入 W17-03 就转移；A02 是 W06/core.qualify，C10 是 W16/test.orchestration，均不是手机终验。W17-03 仍须依赖 W17-02/W13-03/W12-02 有效当前状态；本报告不更改 step_state。

用户手机/授权通道尚未实际准备只阻塞 LIVE 分支；Mu pause/resume 缺口只阻塞控制就绪；原权限审批缺口单列。只读 UI/安全 fixture 与 workspace4 可继续推进，最终22父/42正式目标保持未完成。既有 UNKNOWN 费用、历史失败和不可重开的旧世代都保留。

## 下一最小可执行范围

按 Root 最新约束，最多两个 Source writer：workspace4 加下面 M0；手机 UI/helper 暂不再启第三个 writer。shared API/gateway/protocol 接线等 workspace4 freeze 后串行。M1/M2 是后续因果范围，不是当前第二 writer 可立即触及的范围。直到配对、真实查看、暂停、资源响应、恢复、撤销完整准备完成才邀请用户手机操作；M0、只读或仅配对都保留 PHONE_PRODUCT_NOT_READY。

### 可先独立实施的 M0：隔离 Mu 候选 fork 的暂停快照与恢复原语

可行，但只能作为“候选 SDK/worker fixture 能力”，不能声明生产已接线。Root 登记新的隔离候选根，例如 `.local/live/candidate/mu-pause-checkpoint-sdk/`，从精确冻结 pin `8dfebe36508ac0c2508735bb866756dab9283e74` 的可验证源码建立候选 fork，记录 candidate base/tree hash。当前仓库的 `third_party/mu` 是受保护输入；对该子目录执行 git rev-parse 实际返回父 ResearchOS HEAD，不能冒充它是独立 Mu checkout 或证明安装 SDK 版本。候选来源须用冻结 Mu manifest 逐项核对。Root 当前 pin、已安装 SDK、锁文件、package resolution、产品 worker 与 runtime/迁移文件都不改。

候选根内精确允许文件（不存在的标明新增）：`packages/agent/src/agent.ts`、`packages/agent/src/types.ts`；`packages/coding-agent/src/core/agent-session.ts`、`packages/coding-agent/src/core/session-manager.ts`；新增相应 `test/*pause-checkpoint*.test.ts`；另在候选验证目录放一份明确未安装的 `worker-pause-checkpoint.mjs` 与 `worker-pause-checkpoint.test.mjs`。若新增 public export 确需 package index，先由 Root 追加实际 index 路径；不提前扩大整个 packages/**。不执行真实 provider，不把候选覆盖当前 adapter。

本次只读已发现可复用的 SDK 部分：SessionManager.inMemory(cwd, options, entries) 可从外部 entries 建会话；getEntries 返回不含 header 的追加历史。AgentSession.abort 等待 idle，但不是保留队列暂停的证明。Agent.peekQueuedMessages 只返回 steering 非空时的 steering，否则返回 follow-up，不能用它导出所有队列；AgentSession.getSteeringMessages/getFollowUpMessages 是字符串 UI 队列，不能替代含 command/message/content hash 的 CustomMessage 持久快照。因此 M0 必须明确导出两个原始队列的完整冻结消息、模式/顺序、session header/leaf/context 与实际消费水位，不能只序列化 messages 或文本。

| 接口/协议 | M0 候选要求 | 原协议兼容边界 |
|---|---|---|
| SDK pause/snapshot（新候选 API） | 请求后阻止下一工具/模型/队列消费；可中断点或安全完成当前不可中断动作后获得精确 snapshot；保持未消费 CustomMessage 身份和次序 | 不重定义 abort/clearQueue；不自动调用 provider；只有 fixture 显式调用新 API |
| SDK restore（新候选 API） | 校验版本/hash/有界大小/header/leaf/消费边界，再从已保存 entries 与两个队列恢复；restore 本身零新工作 | 显式 resume 才可继续；不能 session.prompt 原任务全文重新执行；不清旧计数/UNKNOWN |
| worker checkpoint frame | 复用现有 `checkpoint` 类型，保存规范化 bytes/hash；宿主 ACK 前不能出 paused | 原 Bridge 已识别 checkpoint/turn.paused；必须保持现有 frame序列、ACK、run/epoch/input/process绑定 |
| worker turn.paused | 只能在 checkpoint 已 ACK 且真实安全点/流与工具状态可核验后发出 | 不能把 turn.completed、command.cleared 或普通退出改名成 paused；生产接线留到 M1 |
| Host→worker pause/restore 控制 | 候选 harness 传递带原 binding 的新内部控制与恢复材料 | 当前 worker 对未知 control 拒绝；所以新控制尚不兼容生产，须 M1 双端版本/能力协商后启用，不能单边上线 |
| 现有 deliver/clear_abort/prepare_seal/commit_seal | 默认路径和返回语义不变，既有控制测试要通过 | CANCEL 继续清队列；PAUSE 从不产生假 DROPPED；未知控制仍拒绝 |
| researchos-client/2、Native3、V1、schema21 | M0 零变化 | 不新增手机 writer、不绕过 frozen method/result与授权；没有生产调用就不计生产完成 |

M0 测试必须用真实候选 SDK + 受控工具/模型夹具，验证：工具前/工具中可中断与不可中断/模型流中/turn结束边界；同时存在 steering 与 follow-up 且后者不丢；checkpoint ACK 丢失/重复/乱序；snapshot破损/跨session/epoch拒绝；restore无调用，显式resume后确认效果计数不重复；UNKNOWN效果仍阻塞，费用unknown标志不归零；CANCEL与PAUSE竞态；旧消息已CONSUMED不重派发。模拟宿主 ACK 标注 FIXTURE，不能当真实持久化、Windows原生停止或模型LIVE。

M0 接受只表示 candidate SDK 原语和 worker协议夹具可审查。Root 后续再串行登记 M1 runtime coupling、M2 migration/queue attempt lineage 和升级兼容验收；在旧 Run、效果、费用、未知消息对账门未闭合时，禁止打开恢复开关。formal 仍为0/42。

本轮只新写本目录 report/manifest。只读探索出现 Windows shell 不展开传给 rg 的文件通配符、一次过宽目录清单截断及 Python 控制台编码问题；后续用 `rg -g`、精确路径和 UTF-8输出纠正。它们是定位失误，不是产品测试，不改变任何失败计数。
