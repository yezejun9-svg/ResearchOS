# W05 A04 四缺口：实际 producer 与 semantic decoder 接口映射

状态：READONLY_INTERFACE_MAP；未实施接口、未运行候选、未完成 LIVE qualification。A04-03/04/05/06 继续 OPEN。以下行号均对应本目录保存的完整公共源码快照；输入清单记录原路径、SHA-256、字节数与 before/after 复核。冻结 assertions 与对应 refusal 不删除、不改成较弱检查。

## 结论与共用修订

现有 Main 已有恢复 journal/checkpoint、会话接续、CLI JSONL、宿主工具副作用与真实 run_check 回执。它们可作为新 producer 的输入，却没有组成四条所需的完整原始流程。H08 更缺实际 nested admission/执行入口，单加 reader 不能补齐。

A04 source 为 P05/a04_formal_profile_source_revision_codex/02b58e39e08c457a8c48d10ce764fb94（以下简称 A04 Source），SDK runner 为 P05/mu_model_sdk_real_trial_v7_source_codex/73cdde53fe0e4da2ae29fb6898d4b7ef（SDK v7 Source）。两者均为 proposal，不能据此声称 Main 已采用。P05 均指 execution/v2.4/receipts/W05/W05-99。

1. **先对齐实际 DB ABI。** A04 Source formal_profile_w05.final.proposed.py:534 用 kind='TaskRun'，:541 要求每行 content_hash 为裸 64 位 hex。Main internal/domain/runtime.go:45、49 创建/查询 Run；internal/domain/store.go:141-150、187-238 原样用 kind 读写，没有 TaskRun alias。该 put 仅为 receipt 或 Artifact 设置 content_hash，普通 Task/Run 可以 NULL。最小变更是 reader 按真实 Run、Task 的完整 body/revision、关联链和 domain_versions 验证，完整数据库文件本身由 SHA-256 ref 固定；对 mutable body 在 reader 中计算的 hash 必须标为 DERIVED，不伪称生产者的 content_hash。内部返回键可明确映射，但不能在原 DB 注入 TaskRun 或假 hash，也不能放弃 scope/revision/状态/acceptance_count 检查。

2. **复用严格 JSONL 验证，保留 resync 拒绝。** SDK v7 Source:213-375 已检查末尾唯一 command summary、operations 中初始 snapshot/cursor、admission/result、最后已验证 snapshot、连续 event id/sequence、core_build/protocol 与最终 RUN_STATE/ARTIFACT。Main apps/cli/cli_stream.go:493 起接收 admission snapshot，初始快照不是独立 session.snapshot 成功记录。独立 session.snapshot 为 EVENT_RESYNC_REQUIRED；SDK v7:294-304 与 A04:578-579 均拒绝其成功资格。此前“应接受初始 session.snapshot”只是未验证假设，已撤回。A04:557-593 可以补上与 v7 相同的 summary 类型、初始 cursor、event 去重及 artifact 一致性；不能为了通过样本放松 resync。多条命令/多 Run 的旅程应逐次验证单命令流，再用宿主链绑定，不能把多 Run 事件塞入当前单 Run reader。

3. **完整原始采集共同外壳。** 原 contract 要求 root_tool_pair_ref、windows_job_ref、database_ref、jsonl_ref；当前四条还统一要求 sdk_jsonl_ref/action_jsonl_ref/recovery_ref。三个附加 ref 不能用空文件或布尔总结顶替；不适用场景也须由经采用的真实 producer 格式明确表达。每次操作保留完整请求/结果、原始 stdout/stderr/stdin、真实 native exit 与 launcher Job/process/create-time 绑定；Root 先停止所有写入并物化完整 quiescent DB snapshot，再让 reader 内存反序列化。外层工具 exit、Python exit、CLI exit、check 子进程 exit 分开；未知保持 NULL。v7 command_once:989-1104 只支持成功路径 0、保存 stdout/stderr，尚无交互输入和预期失败返回通道。新增 capture-only 路径先保存真实非零结果，再按冻结 lane 解释，不改变已有 success 的零退出门。

4. A04 Source:649-655 和 :785-788 的无条件 OPEN，只能在四个真实 decoder 全部实现、逐 lane 和 refusal 检查后替换。原 assertions、Root issuance、GLOBAL 非作者交付和 owner 接受链全部保留；本报告不授予这些权限。

## A04-03 / recovery

**现在已有：** internal/domain/runtime_coordinator_windows.go:759-847 的 request 有 run_id/task/epoch/context_bundle/inputrefs/checkpoint；:870-896 将 checkpoint 以 artifact、序号、project/run/epoch/dispatch/manifest/content hash 固定；:972-1021 恢复 runtime_dispatches 并调 ReconcileBridge、recoverEffects、recoverCheckpoints、recoverTerminal。internal/domain/runtime_recovery_windows.go:20-92 校验 checkpoint 文件与身份；旧 epoch 贡献可恢复，但不会授予新 lease。:171-285 从 journal/effect/output 恢复终态，仍验证当前 epoch/active task/完整 effect reconciliation。internal/domain/context.go:387-419 生成全新 ContextBundle id、version_vector、facts、unresolved_items、latest_decision_refs、unfinished_commitments、summary_hash、source_manifest_hash、authorized_snapshot_ids 和 receipt_hash，并更新 Task。

**关键语义：** apps/cli/cli_verbs.go:78-110 的 resume 经 session.control RESUME；internal/domain/client_protocol.go:1188-1228 只在 prior Run terminal、children_stopped、queue_empty 等条件下恢复会话保存上下文。它明确不重启 FAILED/CANCELLED Run，后续工作须显式发新 turn。因此“CLI resume exit 0”不能证明崩溃恢复或新 ContextBundle 消费。

**缺失原始证据：** 独立 crash 和 timeout 两次实际 invocation 与 first-cause；切断前后完整 dispatch/journal/checkpoint/effect、Root Job 终态；恢复选择和拒绝原因；真正重新构建 ContextBundle 的内容；新 admission/lease/request 消费同一新 bundle 的链；隔离 worktree、写入数据根与凭据位置的实际 identity；零 blind retry 的 dispatch/operation 全量序列。

**最小切口：** 不把内部 crash hook 暴露为 HTTP 或 task 参数。coordinator:65-75 的 boundaryHook 是仅内部观测 seam，可在经批准的专用 Go runner 接入有限 fault point，producer 由 Root 限定失效操作。为 Recover/recoverCheckpoints/recoverTerminal 和新 ContextBundle admission 加入只追加的 observation sink（完整对象引用、stage、outcome、rejection、run/epoch/dispatch/checkpoint/context ids，失败也落盘）；sink 不决策、不调度、不重试。v7 runner 新增 crash/timeout 的独立步骤，在重启/重连前后封存原件。decoder 分别验证两个 failure、隔离、新 bundle 原文和被新请求实际引用、没有重复 effect 或隐式 retry；未发生新 bundle 消费就继续 OPEN。冻结 crash+timeout、worktree/credential isolation、ContextBundle 与 blind_retry=0 要求不变。

## A04-04 / W05-H08

**现在已有：** adapters/runtime/mu/worker.mjs:695-709 将自定义工具映射为确认后 TOOL effect，但 execute 参数 _toolCallId 没进入 payload；:740 创建一个 in-memory SessionManager；:796-804 一个 createAgentSession 与模型事件 observer；:824 执行 prompt；:835-844 输出当前 task/run/epoch、model_ref/model、effect counts/messages。command controller:586 起能处理队列命令，:683-689 abort effect/session。Main internal/domain/runtime_tools_windows.go:16、57、109 对工具名/权限/当前 Run 做验证并持久化 effect。现有公开检查没有展示真正的 child Run admission 或 child session 生命周期。

**缺失原始证据：** 真实 selected SDK 的 parent/child run 和调用关系；SDK tool-call id 到宿主 effect_id 的绑定；父子共享的有效取消域和预算策略 revision/ledger；取消后父子进程与待处理请求均归零；固定模型配置 before/after；实际运行选中 SDK/adapter/build/安全补丁与兼容矩阵的完整 replay。已有 shared-session harness 的版本断言和旧 prototype 不能替代当前嵌套执行证据。

**最小切口：** 先冻结并实现真实的 nested admission 接口，再写 reader。worker:695、796、804 处捕获 SDK 原始生命周期与 tool-call id；域端在 runtimeToolGate/brokerTool 旁加入独立受信任 child admission 服务，复用宿主 lease、权限、预算与 cancel fencing，返回真实 child task/run/dispatch identity。不能只在 JSONL 中填 parent_run_id，也不能向现有 Run schema 注入未支持字段。若 SDK 只支持同 Run 子会话，冻结 parent_run_id != child_run_id 仍未满足，应 OPEN，不能把 SDK session id 冒充 Run id。最小观测接口是 NestedAdmissionReceipt（父子原始请求/响应 refs、host policy revision、effect lineage）和 SDKEventSink（原始 event bytes + 顺序 + 作用域 + artifact ref）；接口名称仅设计建议，未写 Go 文件、未证明 SDK ABI。

**decoder：** 从完整宿主 admission、DB、SDK JSONL 和 Job 推导唯一父子关系、effect/call id、共享取消/预算；核对固定模型与实际版本/补丁 replay；对不支持组合读取明确的原始拒绝及非零退出。selected runtime/version matrix、security patches、explicit unsupported 等冻结检查全保留。预算额度不得由此新增限制；按现有已冻结有效 policy 验证共享身份和 ledger。

## A04-05 / W05-P01

**现在已有：** apps/cli/cli_verbs.go:67 有 verb 步骤；:225-341 的交互 scanner 读取 os.Stdin，处理中文/多行输入和 /help、/model、/goal、/run、/resume、/status、/cancel。apps/cli/cli_stream.go:160-244 的 f.call 做协议传输及稳定 command_id 重放，:321 起返回 execution identity/status/exit/cursor/cancel_requested/independent_acceptance，:459 起检查终态；:621 起 operations 是摘要，未完整保留每个 wire envelope。v5 cli_stream.context_receipt.v5.proposed.go:759、826 为最后已验证 snapshot 与保存 context 添加 receipt，这仍是 proposal。v7 runner:1316-1444 只走有限 init/goal/config/run，不能代表完整 CLI 旅程。

**缺失原始证据：** PATH/安装产物与实际被启动 researchos binary/build 的同一性；真正交互端输入/输出、中文和多行/粘贴/流式/工具显示行为；完整自动化 JSONL、错误路径真实非零退出、无 stdout 混杂；真实 read/edit/shell/goal/resume/cancel，每次操作的 request/result、宿主 effect 和 native/Job 链；从旧 session 继续以及有子进程工具取消的证据。

**最小切口：** Go 接口仅增加可选、受 Root 限定的 action capture sink，在 f.call 的传输边界记录完整 request/response bytes 和 command_id；不改变完成判定，不将 ACK 当 terminal。交互证据由 runner 包装实际终端/ConPTY，记录原始输入、终端输出及 resize/signal 时间序列；单纯 PIPE 不证明终端显示功能。runner command_once 新增显式 stdin/terminal 驱动和预期失败原件返回。配置/credential 输入使用只含 ref 的回执或受保护原件，不把凭据明文写入公开报告。read/edit 可用现有 Host tools；shell 检查若原合同要求通用能力，不得以固定 run_check 冒充。

**decoder：** 单命令 JSONL 按严格 stream 验证，再关联完整交互 action、wire envelope、安装二进制和 effect。所有冻结 interactive/headless/resume/cancel、fail=>nonzero、exit0!=accepted 检查保持；product.contract P01 和 17_USER_JOURNEYS_AND_VALUE.md:30-34 的中文空格路径、长输出、有限修复、缺模型资源、越界拒绝、子进程取消、取消后 /goal 不自动重启、旧 session 继续均不能被“handler exists”替代。

## A04-06 / W05-U02

**现在已有：** internal/host/runtime_tools_windows.go:45 支持 read/write/edit/run_check；:380 起写入校验 expected hash，:475 保存 preimage。internal/host/runtime_check_windows.go:442-569 接收唯一 check_id、校验冻结 policy/源码/toolchain/vendor，:550 在真实 sandbox Job 运行 go.exe，:558-560 原始证据含 argv_template、source/toolchain/vendor manifest、PID/create time/Job/AppContainer、exit_code、timed_out、children_stopped、streams_drained、cleanup_complete、stdout_raw/stderr_raw 和 hashes。宿主的 bounded model reply 与完整 host_evidence 明确区分。

**缺失原始证据：** 当次冻结的 ISSUE-CONTINUITY-001 范围与中文用户输入；真实 before/after bytes、模型经产品入口完成非平凡编辑、冻结检查真实 native exit 0；所需所有 handler/slash 命令的实际动作；manual admin=0 的完整正常使用记录；与该任务绑定的 cancel settlement。还缺 CLI→Desktop→CLI 的独占 writer handoff、Desktop diff/tool result、一致 Goal/session/file hashes，以及旧 epoch 拒写和重复 command 幂等的原始证据。

**最小切口：** 首先复用上面的 action sink、Host write 的 preimage/hash、run_check.host_evidence；runner 只记录/验证模型真的通过受保护工具改动候选文件并执行冻结检查，不能自行改文件后声称模型完成。最小新增 Go 观测放在宿主 client attach/handoff/control 回复边界，保存原始 writer_epoch/revision/fence 以及 stale writer/duplicate command 响应。Desktop 操作需后续独立授权的实际生产者；本任务未查看或污染 Root 当前桌面观测。当前 CLI 单端 runner 无法独自满足 continuity 旅程。

**decoder：** 冻结 issue_ref/文件/检查/独立接受者，关联同 session/goal/task 的中文输入、工具 effect、before/after 原文 hash 变化、实际 sandbox 原始结果，验证交接两次 writer_epoch 单调改变与旧写拒绝，接续不重贴目标。delivery.contract U02 引用 17_USER_JOURNEYS_AND_VALUE.md；:13 固定 continuity，:38-40 指定跨端 diff/工具/Goal 和 writer_epoch。因此不能将 U02 降为一次 CLI read/write/test。冻结 manual_admin=0、Chinese、before!=after、test native0、固定模型及 init/run/goal/resume/status/cancel/doctor/config/interactive/jsonl/slash 全 handler 集合不变。

## v5 五个 Go proposal 的最小影响范围

cli_stream.context_receipt.v5.proposed.go 提供 context 保存和最终 snapshot 基础，可继续扩充 transport action sink。internal_host_vault.v5.proposed.go:66、113、157 的 readonly credential selection、storage isolation 检查与 internal_host_host.v5.proposed.go:60、107-164 的 Host 配置只作现有隔离基础，恢复/H08 不需扩大凭据读取面。apps_control_main.v5.proposed.go 只需在将来受信任 runner 生命周期接入 observation sink/关闭封存；不新增通过 HTTP 的故障开关。runtime_qualification.unlimited.v5.proposed.go:21-45 保持 UNLIMITED_AMOUNT、cap=null、ALLOW_AND_RECORD，:47-159 的有限 qualification plan/capability 绑定可以复用；不得借补证据重新授予资源或宣称这些提案已在 Main 生效。

建议实施顺序：真实 DB/JSONL decoder ABI → 共用原始 capture 与受控失败保存 → recovery/P01/U02 producer → H08 真实 child admission + SDK ABI → 四个独立 decoder → 全部 frozen assertions/refusal → 新 Root 有限运行与非作者审查/接受。这里只提供可审查接口定位，未写提案 Go 或改任何 Main/旧 Source/canonical。

## 审计范围和错误

只读公共源文件；本目录中的 Python -I -S -X utf8 helper 只读取/哈希/保存原文件，未 import 候选或执行其函数，未运行 Go/SQL/CLI/native target/SDK/model/网络/Git。没有新 runtime 资格、产品结果或 formal case accepted delta。

一次实际 rg 工具调用包含不存在的 apps/mu-worker，原始 outer exit=1；完整初始输入和完整原返回已保存在 failure.origin.8a0dfa.json。未知 native 分层保持 NULL，Root 已收到且计入 current=668 / fixedcut=645；本报告不重复计数。个别原输出被工具截断，original-tool-io.json 保留原样，后来对引用源码以完整 bytes 快照补齐；不声称先前截断输出完整。本报告中按源码推导的接口为设计建议，不是 SDK 实测结论。

