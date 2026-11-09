# CP494 qualification 只读独立诊断

结论：`QUALIFICATION_NOT_ACCEPTED_PROTOCOL_UNRESOLVED`。本次请求已消费，MODEL 记录 1 个已确认 effect，HTTP 200；模型响应要求调用 `run_check`，worker 发出 1 个 TOOL 请求，但没有 TOOL effect 或实际工具执行证据。公开 bridge 已记录 native worker 清理完成，数据库 dispatch 仍 UNKNOWN、Run 仍 RUNNING。不得重放 CONFIRM，不得将此改称资格成功。此前 verifier registration 的 LIMITED_ACTUAL_REGISTRATION_ACCEPTED 不受影响；正式增量 0，正式 0/42，22 父任务仍开放。

## 输入、操作边界与独立证据

- Scope：`resume_cp398_codex/20261015-current-chat/continuation-cp494/normal-desktop-reopen-new-qualification-scope.json`，SHA-256 `5b91c531d7b5549af10f51332b9308d9a1c5244323adb78ec0f55e9b7af1c5a5`。
- Request `bc269e772ada7e1bce54439fd080550c`，hash `sha256:ba2d3061ad1c14efd4912fb1a53e427d5d3ef58ee6fd115de62f28ebc2e0f24e`；Run `f3dcb996b2e43cf52cba874be7abfc70`；dispatch `705b11ec99044fef19e85f57e2d2b712`。
- `01-public-observation.json`：本观察者重新读取 exact dispatch 的公开 journal，并在 SQLite URI mode=ro/query_only/BEGIN-ROLLBACK 下只读 exact Run 的状态、effect 和 acceptance。不读取 credentials、私钥、management 私有帧；无产品 API、模型请求、启动、停止、恢复或 DB 写入。
- `02-process-snapshot.json`：只读 Win32_Process 元数据，Desktop 69996/Core 54076 存活，worker 69860 未出现在结果，Core 的直接子进程仅观察到 conhost。PID 缺失本身不是完整清理证明。
- `03-effect-and-native-lock.json`：公开 MODEL effect receipt 的 SSE 元数据；同时以 GENERIC_READ/share=0/OPEN_EXISTING 成功打开原有 worker owner.lock 并关闭，未创建或修改锁文件。
- `04-source-refs.json`：本次读取生产源码的内容哈希。实际 Main 为 `4f4023c956f84d65743f39ce77d6c8899a21ada1`。当前 composition 工作树在检查时已为 `2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02`，不能继续按先前简写 53 当作当前头。

## 已观察事实

1. Root 的 UI 回执为 `CONFIRM_REJECTED_CHECK_STATUS` / `UNRESOLVED`。已有独立观察记录确认消费时间 09:43:24.1209795Z，早于 request expires_at 09:43:25.1164527Z。expired 是事后状态，不能解释已经成功消费后发生的拒绝。session writer lease 曾在 09:43:10 到期，现有证据没有建立其为本次拒绝原因的因果链。
2. admission 为 `qualification_bootstrap=true`，purpose=`runtime_qualification`；`model_qualification.max_calls=1`。但 staged model config 是持久 coding 配置：`max_calls=8`，工具 schema 为 read/write/edit/run_check；实际 MODEL request 携带全部四个 schema，未设置 tool_choice。
3. actual MODEL effect receipt HTTP 200、CONFIRMED，SSE `finish_reason=tool_calls`，工具名 `run_check`，无普通文本内容，随后 `[DONE]`。worker stdout 第 3 帧为 TOOL effect.request，check_id=`cli-local-model-endpoint`。本回执只保存字段摘要，不复制模型消息、实际文件正文或凭据。
4. DB 只有一个 MODEL effect key 的 PREPARED/STARTED/CONFIRMED 三阶段；它们不是三次调用。`model_transport=1`、HTTP status=200；TOOL effect 为 0，AcceptanceReceipt 为 0。该证据支持一次记录的模型传输，不能单凭数据库 key 数把它提升为独立网络抓包证明的恰好一次 HTTP。
5. bridge 为 FAILED，frames=3、acknowledged=2、protocol_complete=false、cancelled=true，最终 reason=`coordinator control channel closed`。sandbox receipt 为 exit_code=124、timed_out=true、children_stopped=true、job_total_processes=2、streams_drained=true、cleanup_complete=true、output_copied=true；finish 09:43:32.8733359Z，journal ended 09:43:32.9018391Z。
6. DB dispatch reason=`protocol not reconciled`，updated_at=09:43:32.907264Z，observation_sequence=0、observation_hash 为空；Run revision=2/status=RUNNING、exit/settlement/children_stopped 仍空。这不是 native 子进程仍运行的证明，而是事实尚未进入业务终态。

## 生产调用链与错误层次

路径均相对 Main 仓库，行号按本次哈希冻结的源码。

| 环节 | 位置与行为 |
| --- | --- |
| UI 一次确认 | `apps/desktop/main/lib/desktop-management.js:523-539`：先设置 confirmSent，再 exchange CONFIRM；reply.kind 非 RESULT 就统一变成 CONFIRM_REJECTED_CHECK_STATUS，原始错误未向 UI 暴露。195000ms timeout 不是本次已证实的原因。 |
| 管理入口 | `internal/host/desktop_management_windows.go:249-256`：LoadLocalConfirmation 后，以 3 分钟 context 调用 QualifyLocalRuntime；`:180-184` 把所有异常转为 ERROR / MANAGEMENT_REJECTED，正文为 e.Error()。本观察者没有读取私有帧，故不声称抓到了其正文。 |
| 独立 verifier 生命周期 | `internal/host/runtime_qualification_windows.go:179-198`：先启动 verifier/记录 provenance，再 ExecuteLocalQualification；若执行返回错误，返回 QUALIFICATION_NOT_ACCEPTED，跳过 LocalQualificationReview、发 verifier job、独立验收和 purpose authorization。`:185` defer process.close；`runtime_verifier_process_windows.go` 的 close 会 cancel、关闭管道并 Wait，但数值退出码被丢弃。 |
| 消费和执行 | `internal/domain/runtime_qualification_execution_windows.go:169-181,204-228`：原请求唯一消费并创建 Run，随后 RunAdmitted；存在原消费会 STATE_CONFLICT，不允许自动重放。 |
| 资格输入问题 | `internal/domain/runtime_model_windows.go:19-45` 把 profile.model_config 原样写成 worker.json；`adapters/runtime/mu/worker.mjs:730-741` 注册所有 config.tools 为可执行 SDK 工具，`:877` 强制把 config.tools 放入模型请求，`:910-915` 把它们注册进 Agent session。没有资格任务的工具输入收窄。任务本身是正常 qualification task，明确说不使用工具；不能称作投递了 CLI 修复任务。携带 run_check schema 与通用系统提示使模型仍能选择工具。 |
| 资格权限拒绝 | `runtime_broker_windows.go:148-155` 先 dispatchGate 后 providerRoute；`:84-86` 的 qualification_bootstrap 分支调用 `runtime_model.go:100-103`，收到非 MODEL 立即 `Fail(503,"RESOURCE_UNAVAILABLE","qualification grants no unplanned effect authority")`，早于 prepareEffectTx (`runtime_broker_windows.go:201`) 和 RunTool。不是工具额度耗尽分支，更不是放行工具执行。 |
| 错误上返 | `runtime_command_queue_windows.go:457-465,490-497`：brokerEffect 的错误导致退出，不为拒绝帧写 acknowledgment；`runtime_coordinator_windows.go:661-670`：Cancel(protocol reconciliation failed)，等待 bridge.Done，然后 markUnknown(protocol not reconciled) 并返回，跳过正常 Finalize/ingestObservation/recoverTerminal。 |
| reason 覆盖与 124 | `adapters/runtime/bridge_windows.go:612-625` Cancel 总是覆盖 reason 且调用 w.cancel；`:513-515` 的 ctx.Done 监听可再 Cancel(control channel closed)，覆盖原始错误。`ops/experiment_sandbox/sandbox_windows.go:346-351` 在 ctx.Err()!=nil **或** deadline 到期时均标 timed_out 并 TerminateJobObject(124)。因此 124/timed_out 不等于已证明超时，更不能归因于 request TTL。 |

错误分层结论：实际公开记录确认 generic UI error、DB protocol not reconciled、bridge 最终 control channel closed。与第 3 帧 TOOL 精确对应的生产拒绝为 RESOURCE_UNAVAILABLE/503（源码推导，可信但不是已捕获的原始管理回复）。拒绝发生前还存在 dispatchGate 和控制循环其他错误分支，公开回执未持久化 original protocolError，故不能把源码推导标成原始 error 实测。最小补证应持久化经白名单清理的原始 fault code/stage/frame sequence，不读管理私有正文、不重试请求。

## Native closure 与禁止重放

native worker 的 stopped/drained/cleanup/output-copy 四项为公开持久回执事实，owner.lock 已独立验证释放；本次观察未执行 process wait，不能声称得到新的原生数值 wait status。独立 verifier 的 deferred close/Wait 是生产逻辑，当前 Core 子进程观察没有 verifier，但该 verifier 精确 PID/创建时间/数值退出码没有在本诊断中重新取得，保留为未独立观察项。没有验收结果不代表 verifier 本身校验失败：该调用链在执行错误后尚未进入 verify job。

`worker.mjs:870` maxRetries=0、`runtime_model_windows.go:97` 单一 client.Do、qualificationModelEffectAllowed/runtimeModelCallGate 及消费记录共同限制继续调用；已确认 MODEL 不能重新发送。SOURCE read/write/run_check 均未授权本轮执行。不得点击 CONFIRM、生成新请求绕过 unresolved Run，或把 effect UNKNOWN-cost 账本解释为未知是否调用：本次模型 effect 已 CONFIRMED，金额 UNKNOWN 是另一维度。

## 最小修复建议，须独立新 scope 实施

**A. 资格输入收窄，保留持久 coding profile。** 在已冻结 admission purpose 为 runtime_qualification 时定义确定性的有效执行投影：max_model_calls=1、工具调用为 0；worker 不注册 coding customTools，不向模型提供可调用工具（或采用严格 host 校验的 tool_choice=none 方案，但要明确仍保留 schema 的折衷）。原 model config/profile ref/hash 与 coding 授权保持不变；记录有效投影如何由原 profile 与 qualification permission 导出。不能只把 worker.tools 改成空数组：现有 `runtime_model.go:163-169` 要求 request tools 与 frozen config 完全一致，独立 verifier `runtime_model_verification.go:648` 也重验同一规则。必须把 staging、worker、Host request validation 和 verifier 检查一致适配到受绑定的资格投影，普通 mu_turn 仍使用原 schema/额度。不要靠改提示词或把工具额度提高到 1 修复。

**B. 失败事实收尾，保留 UNKNOWN 的真实性。** 对明确的 pre-dispatch 拒绝持久化 exact request/frame/hash、fault code/stage、NO_EFFECT/NOT_APPLIED 依据；不能假造已发生的 TOOL effect。形成带绑定的拒绝帧处理/失败协议终止事实后，再结合已有 MODEL CONFIRMED、children stopped、streams drained、cleanup 和队列核对进入 FAILED/CANCELLED 的合法路径。保留原始取消原因，单独记录后续 context close。只有实际未决外部效果、缺失 native receipt、未核对帧/队列仍保持 UNKNOWN；不得无条件 mark FAILED 或直接改 Run 字段。Host/GUI 可显示可公开的 failure stage、原 request/Run 和是否已消费，避免 generic error掩盖阶段。

**C. 原 Run 的现有恢复能力。** STATUS 只读并保留 consumed/UNRESOLVED（`runtime_qualification_confirmation_windows.go:95-174`），可以观察，不恢复。Recover 导入持久事实而不重启 worker；但本 journal.Cancelled=true 会令 Observation.state=CANCELLED，且 frames3/ack2 使 queue_empty=false（`bridge_windows.go:796-799`）。`recoverTerminal` 对当前 RUNNING + CANCELLED observation 不会 report 成功（`runtime_recovery_windows.go:265-274`）。即使未来授权 cancelRun，acknowledgeRunCancellation 仍要求 queue_empty=true（`runtime.go:306-307`）；当前证据不能证明既有取消入口能完成收尾。reconcileRun 仅转 RECONCILING，不会清掉未知（`runtime.go:324-327`）。因此不要用“重开应用/点取消即可”作保证；先为旧第 3 帧的确定拒绝及缺失 acknowledgment 设计合法、不可重放的失败收尾证据路径，检查 exact Run/epoch/manifest/effect/native 绑定，再另行授权实际恢复。没有调用这些写入口。

**D. 基线与验证。** 本次实际运行来自 Main 4f，最小复现/修复先在 4f 的隔离工作树；composition 当前 2a2 已改动 runtime_broker、runtime_coordinator、runtime_command_queue、bridge 的 pause gate/恢复路径，不能把其已有 source/fixture 接受直接带入本 bug。输入漏洞涉及的 stageRuntimeProgram、worker makeTools/onPayload、qualification gate 在两者仍同根；修复应随后在 2a2 上独立适配并验证 pause/queue/current-admission 行为。无需为了此诊断先迁移 actual DB。必要测试包括：资格 projection tools0、恶意/违约 tool_calls 拒绝无执行且可合法终止、MODEL只发一次、原始错误不被覆盖、失败后不重放、旧UNKNOWN仅在完整证据下收尾、普通mu_turn coding能力保持、composition pause/queue回归。实际产品重启/新资格/旧Run恢复均需另定 scope；本诊断没有实施任何修复。
