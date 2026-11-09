# 现有 status 作用域缺陷对真实生命周期门的影响

状态：`EXISTING_BEHAVIOR_BLOCKS_PLANNED_NATIVE_STATUS_FLOW`。该问题在 ecc28 基线也存在，不能归因于新 exact14；但其真实业务路径会阻断本轮准备的 native controller，因此不能把它仅视作无关 fixture 失败或通过忽略 exit code 消掉。

静态因果链已核对冻结 5ee2c694：

- apps/cli/cli_verbs.go 的 verbSteps(status) 在 ctx.sessionID 非空时首先添加 session.get，然后用同一上下文添加 host.status。
- apps/cli/cli_v2.go 的 v2EnvelopeFor 把 ctx.sessionID 无条件写入 env.SessionID，没有针对 host.status 的清空规则。
- internal/domain/client_protocol.go:902–905 对 host.status/workspace.list 的任何非 null SessionID/ExpectedRevision/WriterEpoch 返回 INVALID_REQUEST。
- apps/cli/cli_continuation_test.go 的 TestW18ContinuationStatusProcess 真实 API fixture 与 CLI test child 原始输出恰为 session.get COMPLETED、host.status REJECTED:INVALID_REQUEST、整体 exit2。作者 baseline-w18-01 在 ecc28 archive 重现相同分支，证明旧版本已存在，不证明未来 native 可绕过。

planned native 使用 `researchos status --project <project_id> --session <session_id>`，必然走以上路径。新创建离线 session 是否有 goal 不能改变 host.status 拒绝条件。该CLI调用本身需要按合同报告两个步骤，不能仅在controller接受session.get那一步就称status正常。

处理建议：由 Root 明确登记最小 CLI host-level scope 修复及回归，保证 host.status/workspace metadata envelope 不携 session/writer 字段，同时原上下文和session.get身份保持不变；不能放宽Core合同，也不能改变fixture来接纳非法envelope。若当前exact14不可变，作为后续单独修复，但在修复验收前不启动声称能通过此status路径的native验收。另一条 pagination CONTINUATION_HTTP_403 单独诊断，不与本问题混合。

本报告只读源码并复核已有原始输出；没有新增Core、Electron、provider调用，没有修改源码或计数。建议发出时CP561仍按既有授权针对冻结5ee2运行，不能悄悄在运行期间改源。