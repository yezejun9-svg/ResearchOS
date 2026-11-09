# W05 独立架构核对

审查者：codex:/root/w1702_review。类型：只读源码和冻结合同核对；不是产品执行、资格或父任务接受回执。

基线 candidate HEAD `f68c83c2918ae25d9811e4e9f703f1a158e143d2`；读取时主库 HEAD `37b2f33f2848b2f786bbb065b40ca4e22da020f6`。已核对上述两个提交之间 apps/cli、internal/domain、adapters/runtime、internal/host、internal/api/contracts 无差异；所读源码也无工作区 diff。原有 dirty 证据全部保留。

## 结论

现有 Mu 宿主执行与副作用边界可以复用。最短修复是接通已有客户端协议的等待、交互、取消、Goal 与工具事件，不另建 CLI 直接写文件/执行模型的第二条权限路径。旧 `coding_task.go` 的 `NotRoutedWriter` 不应作为本次主链修复入口。

该实现切片不足以自动满足 W05 全门：A04 的正式模式是 LIVE_WINDOWS，W05-G02 还要求 LIVE_WINDOWS_AND_SERVICE。H08 的嵌套运行与版本/安全补丁、P01 的真实模型读改测/Goal、U02 的当前未解决问题必须分别取证。源码/fixture 通过和旧 W14 失败均不能转成新 LIVE PASS。

## 当前事实与最小修复

1. `apps/cli/cli_verbs.go` 的 `run` 只发一次 limit=200 的 session.events；`cliHostCommand` 随后输出 COMPLETED。`apps/cli/cli_v2.go` 将 ACKNOWLEDGED 和 IN_PROGRESS 都映射为 exit 0。应区分协议接收与任务结清，持续按 next_sequence/high_watermark/has_more 读取，处理重复事件与水位缺口，最终再给执行退出码。不能见到上一轮 terminal RUN_STATE 就结束新一轮，须绑定本轮 command/message/task/run，支持 send 回执 run_id 尚为 null 的异步绑定。

2. `cliInteractive` 先读完整 stdin，再创建/发送会话；没有运行中的 slash/取消分发。应边读边调度同一 session，保留中文、多行/粘贴边界、已保存会话和输出流。当前 session.send 的 STEER/FOLLOW_UP 明确拒绝；不能通过默默新建 session/第二 writer 冒充支持。若此切片未实现，继续列为完整 JRN-02 的缺口。

3. `apps/cli/cli_contract.go:571` 的 interruptGuard 只退出本地 CLI，没有宿主 cancel。应将中断送到已知当前宿主 Run/Goal，等待 cancel_confirmed_at、children_stopped、queue_empty 等真实终止事实；请求尚未绑定 Run 时必须有明确 pending-cancel 处理，不能因 run_id=null 丢失取消意图。等待超时/断网用非成功并保留 UNKNOWN/CANCEL_UNCONFIRMED，不声称进程已停。旧函数仍用于只读短命令时可保留，但不能覆盖新的任务跟随流程。

4. `goal.start` 存在于方法/schema/CLI 表，却没有 handleWrite 分支。冻结 schema 允许 session_id=null 的项目级 Goal，只有带 session 时才要求该 session 的 revision/epoch。应同时修 decode、dispatch 和 handler 三层；无 session 的入口必须取当前项目 Owner、唯一已授权 workspace/model 绑定，并使用宿主生成的 session 身份。歧义、越权、已撤销绑定应在创建业务对象前拒绝。带 session 的入口保留当前 revision/epoch/writer gate。返回冻结 StartGoalResult 的 goal_id/revision/status 与真实 SessionSnapshot，不能省掉快照或虚构它。

5. 复用有限 turn 构造应抽取内部共用函数，而不是在 Goal handler 中伪造 session.send 成功后改写已冻结 Goal/Task 合同。`start_as_draft` 应只保存草稿，不派发；contract_artifact_ids 必须验证项目、当前版本、sealed/hash、可用合同结构并作为实际合同输入。无合同的默认有限执行合同必须仍需独立验收，不能把 Mu 最后文本等同业务目标达成。重复 command_id 同回执、不同请求同key拒绝、拒绝回滚中间 session/Goal/Task 均须保留。Goal 取消要阻止后来重新派发；新 Goal/session 不能用于重置原问题失败/预算计数。

6. 宿主 `runtime_sessions_windows.go` 当前只投影 RUN_STATE、ARTIFACT 和 SETTLED 后最终 MESSAGE；`runtime_tools_windows.go` 无 TOOL_STARTED/TOOL_RESULT 生产 emit。现有 schema 已具备 TOOL_STARTED/TOOL_RESULT/USAGE，无需为了事件显示改冻结 schema。工具真实开始/完成处按原 effect key、session/run、版本与事件水位写 durable 事件；原事实恢复/replay 应可补投影但不能重做工具。结果长输出绑定实际 artifact/hash，不能仅给成功摘要。工具结果失败、拒绝、UNKNOWN、取消分别保留。

7. `runtime_model_windows.go` 用 ReadAll 收完 provider SSE 才给 Mu，`worker.mjs` 没有订阅增量 assistant 事件。因此 CLI 轮询实时工具事件可称宿主事件流，不能把最终文本拆段称 provider token 实时流。若此轮只做工具事件，文案和证据应保留该限制，完整流式响应仍需后续实际实现/验证。

## 必须保留的边界

- `client_protocol_sessions.go:365` 的 clientTurnSettled 要求 Run 真终态、子进程停止、队列空、effectsReconciled、时间字段和当前 revision 的 RUN_STATE 投影。新的 CLI 完成判断不得弱于宿主事实；Task ACCEPTED 仍只由独立验收路径写入。
- `RuntimeCoordinator.sessionModel` 校验单一固定 model ref/route；`runtimeToolGate` 校验当前 owner、workspace、frozen tool schema/call bound；物理写前 `Revalidate` 再查 Run/lease/当前权限。不得为方便演示绕过这些门。
- `brokerModel` 收到完整响应时 actual_cost=null，`ingestEffectFact` 保留上界 reservation 等真实账单；worker 的零费率和 sdk_cost_is_placeholder 不能拿来结算。USAGE 可以展示未知费用和已知 token/预留，但未知不得变成0。旧 STARTED→UNKNOWN 与401保留，不自动重试同效果。
- 工具子进程已有 `internal/host/runtime_check_windows.go` 的 sandbox.Run 与真实进程/清理回执。取消验证需观察其宿主侧子进程与 Mu worker 两条链，不能只测手工 StartChild 夹具。
- 原问题、candidate、输入hash和预算/尝试计数继续由原宿主合同约束；已取消任务不得被 /goal 自动复活。

## 建议精确源码范围（供主 Agent 登记，尚非写授权）

必需：`apps/cli/cli_verbs.go`、`apps/cli/cli_v2.go`、`apps/cli/cli_contract.go`、新 `apps/cli/cli_stream.go` 及对应专用测试；`internal/domain/client_protocol.go`、`internal/domain/client_protocol_sessions.go`、新 `internal/domain/client_protocol_goal.go` 及专用测试；`internal/domain/runtime_tools_windows.go`、`internal/domain/runtime_sessions_windows.go` 或新的 `runtime_session_events_windows.go` 与专用测试。

有条件追加：若投影必须覆盖 durable effect ingestion/recovery，精确增加 `internal/domain/runtime_broker_windows.go` 的投影调用；若实现真正 token streaming，再单独提出 `runtime_model_windows.go`/worker/bridge 的相称范围。暂不批准 wildcard、schema/迁移/锁文件/路由登记、旧 CLI coding_task、底层sandbox重写、第三方SDK升级或宿主凭据配置改动。

## 本切片必要验证

无需paid call即可测：超过200事件与duplicate/reconnect gap；延迟 Run绑定；旧轮终态不能结清新轮；RUNNING/ACK不退出0；BLOCKED/FAILED/UNKNOWN/取消退出码；中文stdin首行未EOF就触达宿主；slash被真实分发；Ctrl+C发出宿主取消并等结清；project-level/session-level Goal权限和幂等/rollback/draft；工具 STARTED 在实际完成前可见、RESULT/恢复exactly-once且绑定原effect；费用unknown保留。

正式LIVE前须冻结真正未完成 issue 的 baseline_failure_command/output_hash、allowed_files、expected_behavior、frozen_checks、independent_verifier；不使用已修复问题、人工植入bug、零diff或施工Agent工作冒充产品Agent执行。当前审查未运行产品、测试、模型或dispatcher；没有读取凭据值，没有修改源码或canonical施工状态。
