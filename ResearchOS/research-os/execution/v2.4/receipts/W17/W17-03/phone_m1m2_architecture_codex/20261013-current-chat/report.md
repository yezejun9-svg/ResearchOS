# M1/M2 手机真实暂停与恢复：独立架构续审

状态：READ_ONLY_ARCHITECTURE_DESIGN；PHONE_PRODUCT_NOT_READY；正式接受新增 0/42。此轮没有运行模型、手机、产品 API、GUI、隧道、安装或测试，没有修改 Source、Canon、DB、冻结合同或历史计数。只新增本回执及输入副本。

## 结论与先前建议纠正

普通安全暂停后的恢复，建议保留同一个 Run，仅递增执行 lease_epoch，并记录新的 dispatch/SDK 激活 lineage。冻结规格没有要求所有 PAUSE→RESUME 都新建 Run。此前 report-01.md 把“新 Run/新 queue attempt”作为 M2 必需条件过强，应由本报告纠正；历史报告保留。显式 CANCEL 后用户重新继续才受 B22:153 的“原 Goal/Task、检查点、有来源的新 attempt/run”要求约束，不能复活原 CANCELLED Run。FAILED 后新工作也不得将原失败和费用归零。

这不表示现有 ResumeCheckpoint 已能直接承接手机恢复：其 Task RUNNING/Goal ACTIVE、非 CANCEL_REQUESTED、queue_empty、native proof 前置条件，与当前 PAUSE 和有未消费 SDK 队列的实际路径冲突。保留该方法的同 Run/epoch 与 carryCheckpoint 核心，抽出同一事务内可复用的恢复步骤，增加明确暂停恢复分支；不要从 DeviceActor 直接调用 scheduler token 方法，或先开启 Task 再另发非原子恢复。

M1 当前最先要闭合的是生产 worker/bridge/checkpoint ACK 的协议和真实安全点；M2 随后闭合冻结队列与新 epoch 的绑定。在这两步、手机资源响应和撤销完整闭合前，不邀请用户把只读页面当成完整手机流程验收。

## 输入与证据级别

主线固定为 91218bdd3901bae94a2c1c90521a4d133c59026d。本轮从独立现有 cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8 checkout 读取核心文件，并用 git show Main:path 逐文件比较；source-manifest.json 分别记录原始字节和 LF 归一化是否相同，不能把换行相同称作原始 hash 相同。所有列入核心文件的代码内容均与 Main 一致。

权威规格为 current_spec.json 指向的 .local/worktrees/v24-continuation/spec/v2.4，规格 manifest SHA256 为 4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964。B22 文件 SHA256 为 01b3d5eaeff08d8c5c496631a7334fbf50361b8da27b032f4efd9eba06bedd48；acceptance.json 为 ae8aa1ce632aecce595b2adbcb05fd73aa7360b8fd4186fcef6fd5e7872caa66。00/08/12/18/21/22 与 W17-03/harness 均另存实际 hash。

已安装 Mu pin 仍为 8dfebe36508ac0c2508735bb866756dab9283e74。本轮读取的 M0 V5 是隔离候选的在途文件快照，仅为 PROVISIONAL 设计输入；未收到 FINAL，未认定已接受或已安装。候选 SDK 原语与脚本具备实现参考价值，但它们与生产 worker 的协议不相同，不能直接覆盖或从 fixture 推导生产能力。

## 约束决策表

| 决策 | 分类 | 原文/事实 | 最小处理 |
|---|---|---|---|
| 同一个产品 session、Goal/Task，保留未消费 follow-up | SPEC_REQUIRED | B22:108,138-145；08:64 | session/native_session_ref 映射保留，暂停不得 clearQueue/CANCEL |
| 暂停后每次都必须新 Run | ROOT_DESIGN_ASSUMPTION，撤回硬约束 | B22:151-153 无此要求；现有 durability.go:255-403 明确保留 Run | 优先 same Run + lease_epoch 递增 |
| 取消后重新继续建立有来源的新 attempt/run | SPEC_REQUIRED | B22:153 | 保留终态和 resume_requires_explicit_user；单独实现后取消新工作路径 |
| 暂停已确认必须等真实安全点及持久检查点 | SPEC_REQUIRED | B22:138,140,145,151；W17-03:27 | ACKNOWLEDGED/等待与已暂停分开；不以 BLOCKED 或 HTTP 200 推导停止 |
| 单一 Go 调度/预算/最终接受权威 | SPEC_REQUIRED | 18:26,33 | 新暂停 ledger 属于原控制面，不开第二调度器或 Mu Goal 队列 |
| Run.status=PAUSED | 仅 native journal 已实现，非现有公共 Run 合同 | bridge_windows.go 已有 PAUSED；Run frozen enum 无此值 | 不写非法 enum。内部暂停生命周期绑定 canonical Run，再通过合法快照/控制回执投影真实暂停；如要新增公共枚举需正式版本决策 |
| 未知费用一律禁止保存暂停快照 | 不受规格支持的混淆 | 08:112；既有 unknown-budget verifier | 未知副作用需对账；已停止且已知效果的未知金额继续保留原 UNKNOWN/null 责任，恢复新调用重新做预算准入 |

## M1 最小生产因果链

1. V1 Task/Goal PAUSE 或合法本机 V2 control 先在同一事务保存 pause intent、输入/Run/epoch/CAS 身份，并停止新 effect、模型、工具与队列派发。当前 orchestration_controls.go:8-55 对 PAUSE 写 CANCEL_REQUESTED 与 cancel_requested_at，不能沿用该行为；CANCEL 仍具最高优先级。Goal PAUSE 当前仅阻止新 claim，必须显式覆盖所请求的活动运行，不能宣称已有工具停了。
2. sole RuntimeCoordinator 发送明确带 process identity/run/epoch/dispatch/manifest 的 pause 控制。worker createCommandController 当前只识别 deliver/seal/clear_abort（worker.mjs:583 起）；新增路径需能力/协议协商，旧安装版本不支持时返回真实不支持/等待。不可中断工具继续等待，不能杀父进程制造成功。
3. worker 调用候选 SDK requestPause，确认活动模型流/工具已停止，提取完整 checkpoint：session header/tree/leaf/messages、steering 和 follow-up 两条队列、已消费水位及 command/message/content hash、输入/模型版本、原 lease binding。worker 当前 SessionManager.inMemory(cwd) 每次创建新 SDK session（720 起），需显式使用持久映射与恢复材料，不能将随机 SDK ID 冒充产品 native_session_ref。
4. checkpoint 经当前 bridge sequence 及大小边界传输并写入可信文件。Core 验证 binding/hash、存储内容、seal CHECKPOINT Artifact、绑定 artifact-use 与 Run、写 bridge journal，全部成功后才给 ACK。核心现有 checkpoint() 在 runtime_coordinator_windows.go:906 起，已经可复用封存和 heartbeat 绑定；旧 epoch 的 carryCheckpoint 留下 from_use_receipt_hash，不能重标成新结果。
5. worker 收到匹配 ACK 后以新的 sequence 发 turn.paused，再停止本轮执行。主机需同时核对真实进程树已退出、流关闭、ACK 完整、效果已对账、SDK 剩余队列已冻结并可重建；最后以一个可恢复事务确认 PAUSED 内部状态和用户回执。当前 coordinator 在 native PAUSED 后直接 return nil（734 附近），没有 canonical 暂停投影闭环。原 terminal recovery 也不处理 PAUSED，须新增崩溃恢复分支。

### 不能直接复用候选 fixture wire

| 当前差异 | 实际生产约束 | 实施选择 |
|---|---|---|
| 候选 checkpoint 顶层有 binding/hash/bytes | BridgeFrame:27 仅 sequence/type/key/route/capability/payload/path，DisallowUnknownFields | 把有效绑定与 payload 放入既有 envelope，或明确内部版本扩展并做双端协商 |
| 候选 checkpoint 最多 12 MiB | bridge:337 帧 64 KiB；recoverCheckpoint:18 全事实约 128 KiB | SDK snapshot 可走受约束本地文件 + 小 hash/path frame；Core 严格核对大小、路径、内容和身份，再 seal artifact。同步调整恢复读取能力，禁止只提高 sender 限制 |
| 候选 ACK=checkpoint.ack/persisted=true | Core 返回 checkpoint.sealed + artifact_ref，Bridge.Ack 先持久化后写进程 | 用生产 ACK 的封存引用/原 sequence/hash 校验，不认任意 boolean 为持久性证明 |
| 候选 turn.paused 重用 checkpoint sequence | bridge:355 要严格下一个 sequence | 每个发出 frame 都递增，ACK 自己关联被确认帧；重放按 journal 处理 |
| 候选 !unknownCost | 原账本允许受限 UNKNOWN 金额路径 | worker 提供实际停止/未决效果事实，主机决定 budget admissibility；不抹除未知金额 |
| 生产 queue_empty 仅在 SEALED 或 CANCEL+idle 成立 | 暂停保留 SDK_ACCEPTED/ENQUEUED 消息 | 引入可证明的执行队列已停止/快照已封存事实；不得将未消费 durable 队列伪称为空 |

## M2：保留 Run 的最小恢复路径

恢复入口必须重新 authenticate/authorize/CAS，再检查该暂停 intent 未被取消、输入与模型版本未变、checkpoint Artifact 与 use receipt 可用、真实旧进程及流已停、未知 effect 已对账、预算和权限仍允许。显式恢复幂等键绑定原 device/local actor、完整规范化请求和暂停上下文。并发 RESUME 只有一个 successor epoch；重复返回同一回执，不产生第二次启动。

复用 ResumeCheckpoint 的 context rebuild、当前 admission/dependency checks、rebuildResourceSession、carryCheckpoint 和 dispatch 机制，但将其内核拆成事务函数，使 V1 控制意图与恢复切换可原子提交。新的 lease_epoch 和 process identity 拒绝旧 frame/ACK/lease；旧事件允许审计但不能改变现态。产品 session/native_session_ref 保留；SDK tree/header 从原 checkpoint 重建，明确 epoch transition 验证，不能以改 checkpoint JSON 伪造原绑定。

SQL22 目前一条 fence/project/task，bindClientQueueRun:35 只允许同 Run 同 epoch；pending/settled 查询把 SDK_ACCEPTED 视为未结清。故同 Run 恢复仍需队列 epoch 设计，但无需先假设整个 queue generation 每次换号。建议保持原 generation、command_id、message_id、content_hash 与次序，追加 checkpoint/activation ledger 保存每个 epoch 的不可变 binding、冻结消费水位、sealed Artifact、successor epoch 和当前 active 指针；受控事务只从有效 PAUSED 迁移到下一激活，不打开旧 SEALED/CANCEL_FENCED/restore_fenced 围栏。新投递只发送确定尚未进入 SDK 的 ENQUEUED；已在 checkpoint 的 SDK_ACCEPTED 通过 restore 恢复一次；CONSUMED 不重发；UNKNOWN 先对账。

这属于新的连续编号内部迁移，编号由迁移 owner 登记。禁止修改旧 0022、冻结 schema21 或历史回执。client_control_receipts 的 previous_receipt_id 保持追溯，消费在暂停前后竞态以持久消费水位对账。backup_command_queue.go、backup_queue_upgrade.go、backup_configuration_upgrade.go 的白名单/引用核验需同步认识新表，并在全新目录 restore 保持 epoch/取消围栏；不新增另一套真值队列。

取消/失败后新工作独立处理：原终态、旧 generation、budget/effect key、origin 失败计数、水位保留，显式新 attempt/Run 携 checkpoint 来源。不能为了普通暂停恢复引入这整个复杂分支，也不能以其尚未完成为由伪称普通恢复已满足取消后继续要求。

## 文件与所有权建议

| 因果范围 | 精确既有文件 | 必需内容 |
|---|---|---|
| 控制意图/恢复事务 | internal/domain/orchestration_controls.go、orchestration.go、orchestration_recovery.go、durability.go、durability_session.go、durability_checkpoint.go | pause/cancel 区分，显式恢复同 Run，原幂等/计数/预算不变 |
| 生产 SDK 与 wire | adapters/runtime/mu/worker.mjs、bridge_windows.go；受批准候选 Mu SDK 文件 | 真 pause/restore，持久 ACK、顺序/有界文件、身份协商 |
| sole coordinator | internal/domain/runtime_coordinator_windows.go、runtime_command_queue_windows.go、runtime_recovery_windows.go、runtime_dispatch.go、runtime_sessions_windows.go | effect drain、checkpoint seal、进程/流停止、暂停恢复崩溃对账及事件投影 |
| 队列/迁移 | internal/domain/client_command_queue.go；新增暂停/epoch ledger 实现及新连续 migration | 同 generation 的每 epoch activation lineage，禁止 CANCEL/SEALED 复活 |
| 备份 | internal/domain/backup_command_queue.go、backup_queue_upgrade.go、backup_configuration_upgrade.go | 新表引用/完整性/恢复围栏 |
| 本机 V2 接线 | internal/domain/client_protocol.go 与对应 control tests | 当前仅 CANCEL Run / RESUME session，后者只返回快照；应串行绑定合法 Run/Goal PAUSE/RESUME，保持 frozen request/result |

本表是可登记的候选精确范围，不给本 agent 新写权限。M1/M2 共享状态，交给同一实施 owner 连续实现；迁移/共享合同由 root 串行整合。不要把这些修改夹入当前 exact6 的纯只读手机 lane。测试文件跟随触及模块，不扩大整个 internal/domain/**。

## DeviceActor、回放与 UNKNOWN 不变量

手机始终保留真实 DeviceActor principal。remote_auth.go:21 在每次请求动态交集设备与 issuing owner 项目 grant，当前实现还要求 issuing owner 保持全局 OWNER 且未撤销；owner 丧失 OWNER 是整个设备不可认证，不能描述成自动降为只读。device 自身 OWNER→READER 可保留允许读而拒绝控制。当前授权检查必须在 V1/V2 幂等回放之前，撤销后的旧成功响应也不得成为新执行授权。手机不得通过 attach(true)/handoff 取得本机 writer（B22:132,147）。V1 合法监督控制与只读 V2 查询可按各自现有边界并存，不把 issuing owner 作为 actor。

UNKNOWN 有两类：resource_effects 最新 STARTED/UNKNOWN 代表效果未定，durability.go:27 必须阻止盲重试；budget_usage 的 money=null/UNKNOWN 是价格未知，不能改零或删除责任。当前 runtime_model_unknown_verification.go 只对无凭据 loopback MODEL 且所有预算祖先 unlimited+ALLOW_AND_RECORD 的严格分支允许金额未知，不可推广到任意 provider。暂停确认应保留已产生责任；恢复新调用仍重新执行最严格预算准入，严格上界不足则仅该分支阻塞。

## 验证矩阵及正式门

| 验证层 | 关键证据 | 现有可复用测试/新增必要断言 |
|---|---|---|
| 源码/单元 | PAUSE 不设置 cancel 时间、不丢 FOLLOW_UP，CANCEL 胜出；实际 V1/V2 handler 映射 | orchestration_controls_test.go 旧 PAUSE=CANCEL_REQUESTED 断言须明确更新因果行为；不是删门槛 |
| Windows native fixture | checkpoint seal ACK 丢失/重放/乱序，文件损坏/超限/跨 epoch，真进程与流停止；先 crash 再恢复 | bridge_control_windows_test.go、runtime_recovery_windows_test.go；新增 paused journal 恢复测试 |
| 同 Run 恢复 fixture | same Run、新 epoch、单 dispatch、旧 frame 拒绝；两条 SDK 队列保留且效果只一次 | TestRuntimeCoordinatorCheckpointResume 保留原语义并新增真实 Mu queue 变体；既有 fixture 不证明 production SDK 恢复 |
| 预算/效果 | UNKNOWN amount 仍 null，late confirmed 只计一次；effect UNKNOWN 不盲重放 | runtime_model_unknown_verification_test.go、runtime_drain_windows_test.go，现有 unknown liability 保留 |
| 迁移/备份 | pause 后新目录恢复，旧 epoch/取消围栏不开放，queue/reference hash 守恒 | backup_command_queue/queue_upgrade tests；失败不把 schema_version 写成功 |
| 真实本机/模型 | 从真实产品控制入口跑 pause/restore，模型配置不变，未消费指令执行一次 | 当前构建与真实 provider 资格单列，不能用 SDK fixture 顶替 |
| 手机 A10/A11、W17-03 | 配对→查看→PAUSE→资源响应→RESUME→撤销；离线恢复、撤权回放拒绝 | A10:2765/2772、A11 对应冻结断言；真实手机/独立观察，responsive screenshot 无效 |

W17-03:48 仍归原 A10/A11/C17，父任务/42正式用例最终门不动；C01 的双向接续、A14 的恢复计数也需按实际受影响范围回归。新内部断言只补入原门，不形成第二完成总账。正式接受、独立 native/phone LIVE 均未在本轮运行。

## 本轮检查限制

仅静态因果分析和输入 hash 核对，无测试 PASS 声明。候选 Mu 在途内容是有时间戳的不可变输入副本，后续 FINAL 若变化需只重审差异。本轮发生定位通配符/路径错误和一次输出摘要 KeyError；已纠正，不是产品失败，不重置任何历史失败。没有产生需清理的产品临时文件，inputs 是本报告可审计证据。

## 出稿时收到的 V5 FINAL 补充

V5 FINAL 于本报告封存时收到，manifest SHA256 已实读验证为 41ac355e5a71b3092748c0c1061cb7cfd7c562b3cc158b89154f1a9f7e22c127，patch 声明 58f666d66749e0e5e16fdc62f9095cbbaba1cdb0ca3e434c8b7166071a32f519。其专职独立审查进行中，尚未接受、未安装。source-manifest.json 的 late_v5_final 记录本报告六个 Mu 快照与 FINAL 文件逐一比较结果；不把独审尚未完成变为通过。本文生产协议差异仍须 M1 实际双端接线验证。
