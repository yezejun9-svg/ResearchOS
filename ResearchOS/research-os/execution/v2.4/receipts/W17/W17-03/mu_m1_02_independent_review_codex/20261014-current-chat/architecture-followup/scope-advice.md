# CP480 操作门禁与最小修订范围建议

结论：建议将原 exact3 扩为 **exact8**。保持无操作目的的 `dispatchGate` / `pauseActivationGate` 严格拒绝恢复后处于 BLOCKED 的 Task；为暂停收尾建立 Host 内部显式操作目的与绑定参数，不能用一个 `allowBlocked` 布尔值泛化放行。此文是独立架构建议，不是候选实现接受；未改源码、Main、状态或历史计数，未新跑原生测试。

审查基线仍为 HEAD `ff5ac2047566a52388188b84f267217d8582c571`，tree `e5792b72e0380af65fa1cc5f8b122399c1366d9b`。原审查 manifest `93719e2da9a845c238a9ed3443cfb4ebb83174bc908a800819c3557bb30ee064` 保持冻结。本附录另有 manifest。

## 建议白名单

| 文件 | 允许的必要改动 |
| --- | --- |
| `internal/domain/runtime_pause_windows.go` | 保留 immutable activation 全部验证；区分当前暂停阶段、检查点、心跳、原有 effect 的有限继续；接入 pauseCheckpoint。 |
| `internal/domain/runtime_coordinator_windows.go` | 共用 gate 的内部目的分派、心跳目的；无目的默认仍严格。不得让启动和 legacy checkpoint 继承暂停特例。 |
| `internal/domain/runtime_broker_windows.go` | 两次 gate 显式绑定原 effect，区分查阅/重放与原 PREPARED 开始；新 key 必须拒绝。 |
| `internal/domain/runtime_model_stream_windows.go` | 初始化既有模型流、提交模型观察时，门禁内验证 cutoff 的原 effect 与流绑定。 |
| `internal/domain/runtime_model_windows.go` | 已完成模型响应的交付/terminal 仅对同一 cutoff effect 放行。 |
| `internal/domain/runtime_tools_windows.go` | 工具执行前、物理发布回调和结果交付均携带同一原 effect 的 purpose/binding。 |
| `internal/domain/runtime_pause_windows_test.go` | 操作目的、cutoff、旧 activation、错误绑定和其它 BLOCKED 原因的反例。 |
| `internal/host/runtime_pause_windows_test.go` | 真实第二轮 PAUSE→RESUME→settle；模型/工具在途和恰好一次队列证据。 |

行号均指上述冻结基线：检查点 `runtime_pause_windows.go:157,181,185`；通用 gate/启动/启动前复核/心跳/legacy checkpoint 在 `runtime_coordinator_windows.go:495,525,555,591,804,946`。effect 在 `runtime_broker_windows.go:145,226`；模型流在 `runtime_model_stream_windows.go:83,116`；模型响应交付在 `runtime_model_windows.go:174`；工具在 `runtime_tools_windows.go:122,154,224`。

二次暂停原生复现的模型调用 n=4 已经在途。它收到响应后先调用 modelStreamBinding，再提交 observation，之后完成 effect fact 和 terminal；因此只修改 checkpoint 与 heartbeat 仍会使运行提前 UNKNOWN。作者 coding_profile_fix 已核对上述调用点，并撤回通用 BLOCKED 放行方案。

## 操作判据

所有暂停例外都必须在同一 gate 事务内先验证：仍有效的 scheduler/executor/lease、当前 Owner/Goal/session/context/预算/资格和冻结 manifest、原 activation 的完整不可变证据；再验证**当前 epoch** 的 pause intent/witness、当前 Task active_run、dispatch_key、manifest_hash、process identity、session/generation、PAUSE control 且无 CANCEL。旧 epoch 的 RESUMED 记录不能单独构成当前暂停权限。其它 ResourceRequest 等阻塞条件继续拒绝，不得被“有一个 PAUSE intent”覆盖。

| 操作 | Task BLOCKED 时允许条件 |
| --- | --- |
| native launch、BeforeResume、未启动继任 lease 恢复、普通 dispatch、legacy checkpoint | 必须拒绝；不传暂停目的，旧 activation 不例外。 |
| V1 pause checkpoint 捕获与封存 | 当前 intent 必须为 PAUSE_REQUESTED；原 pause_id、epoch、完整 binding 与捕获 metadata/序号/哈希匹配，继续保持队列截断和 artifact/use 校验。CHECKPOINT_SEALED 不得重做新封存。 |
| 当前进程的暂停维护 heartbeat | 仅 PAUSE_REQUESTED 或 CHECKPOINT_SEALED，精确绑定同一当前进程；仍走公开 heartbeat 的 lease/贡献检查。PAUSED_CONFIRMED、RECONCILING、CANCELLED 不得续命。这个目的不授予执行、恢复或 effect 准入。 |
| effect 查阅、已完成结果重放/交付、模型流观察 | 仅当前 PAUSE_REQUESTED；必须在 gate 内读取已存在的 effect 和带哈希的 EFFECT_CUTOFF，校验 key/request_hash/epoch/原绑定。不得先用宽松 gate 通过、再寄希望于远处下游检查。流观察还须保留 stream_id、sequence、request_hash、session/generation 的原检查。 |
| effect PREPARED→STARTED | 仅截断记录原本就是 PREPARED、当前仍是同一 sequence/request_hash/epoch 的 PREPARED；保留 beginEffectTx 的原子 CAS 和完整 admission。STARTED/UNKNOWN 不允许重发。 |
| 已准入工具实际发布 | 仅同一 cutoff effect 的既有执行路径，保持 Host Revalidate、工作区、路径、policy、permission、计数和其它阻塞校验；不能靠历史已调用次数或旧 activation 放行新副作用。 |
| 新 effect、新模型/工具、新 permission 请求 | 拒绝；不得因操作枚举写成 effect 就获得准入。原响应/billing fact 的保存与向 worker 交付权限仍分开。 |

目的参数由 Host 调用点构造，不取自 worker 的自报权限。建议有限类型和专用入口，未知目的默认拒绝；具体命名由作者决定。仍应复用原 gate 身份/admission 检查，避免复制一份逐渐失配的身份校验。

`sealOutput` 的 upload/seal 是独立公开 API 调用，现有 `pauseOperationGate` 已允许 PAUSE_REQUESTED/CHECKPOINT_SEALED 的这两种收尾；`currentDispatchedRun`、artifact contribution/use 和权限检查不得删除。本修订没有证据要求更改 `runtime_dispatch.go`、`runtime.go` 或 `durability.go`。

`runtime_permission_windows.go:114,243` 暂不列入白名单：保持通用严格门禁，不允许暂停特例创建/消费 permission；沿已有拒绝、关闭和 NOT_APPLIED 路径处理尚未物理执行的工具。若作者认为必须让既有 permission 在暂停期间继续等待/消费，应另报第9文件及独立目的、原 request/decision/one-use 绑定和反例；不得通过通用 gate 顺带放开。

## 候选复验要求

1. 同一 Run/attempt 完成 epoch1→2→3 的两轮原生暂停恢复；第二次暂停分别覆盖模型在途与 Host 工具在途（包括发布前复核），无额外副作用、无新 cutoff 外 effect、队列各一次消费。
2. 已存在 activation 但当前无 PAUSE intent、当前 intent 错 epoch/pause_id/dispatch/identity/session/generation、另一个 BLOCKED 原因、CHECKPOINT_SEALED 下的 effect、UNKNOWN 重发、CANCEL/Owner 撤销/Goal停止均拒绝。
3. 在精确 pauseBLOCKED 下，普通 dispatch、RunAdmitted/BeforeResume 和 permission 创建仍拒绝；只有携带对应完整绑定的 checkpoint/heartbeat/cutoff effect 目的通过。
4. PREPARED 截断后允许原 effect 开始一次，但新 key、变化 request_hash/sequence、旧epoch effect 不得开始；STARTED effect 只能收尾，不重发。保留首次 pause/cancel/prepared-lease-recovery 与原队列回归。

这是允许修订的范围和门判据，不预先保证该实现通过；最终独立审查仍以具体候选源码、失败历史和新鲜原生证据为准。
