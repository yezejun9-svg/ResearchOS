# CP480 第9文件：local launch 旧预算释放幂等

结论：**建议必要扩展 `internal/domain/budget_scopes.go`，形成 exact9**。这是共享 `reserveRuntimeLocalLaunch` 的旧 RELEASE 幂等缺陷。不得为了避开它绕过预算 admission，也不应修改 `appendBudget` 的全局幂等语义。

本次是独立只读架构判断。作者工作树为 `D:/作品集/ResearchOS/research-os/.local/worktrees/mu-m1-second-pause-20261014`，基线 HEAD 为 `ff5ac2047566a52388188b84f267217d8582c571`，其中 exact8 修订仍在进行。本文不声称候选已冻结或接受，未改源码、Main、状态，未启动新原生测试。输入副本和哈希由本附录 manifest 单独绑定。

## 已见证据与原因

作者 `06-native-observe/stdout.jsonl` 的 TestProductMuSecondPauseResumeNative 在第二次 successor scan 报 `IDEMPOTENCY_CONFLICT: provider event payload changed`，`exit.txt=1`。同次 `after-second-pause.json` 已记录 epoch1 RESUMED、epoch2 PAUSED_CONFIRMED，第二轮 checkpoint hash 非空。它证明此前 gate 修订推进到了第二次恢复，但不证明修订已完成。

代码链条为当前候选 `runtime_pause_windows.go:532` → `reserveRuntimeLocalLaunch` → `budget_scopes.go:250-279`。该函数遍历全部旧 epoch 的 RESERVE，没有排除已经释放者；每轮都以固定的原 request + `/released` 再调用 appendBudget，却使用新的 `occurred_at=Now()`。`budget.go:272-286` 按 provider_event_id 查旧记录并比较全部请求字段，时间改变必然触发冲突。因此 epoch2 已释放 epoch1 后，epoch3再次处理 epoch1会失败。幂等性判断应在这个特定零费用 local-launch caller 完成，不能把预算全局冲突改成成功。

作者采证没有导出 budget ledger 行；具体旧 RELEASE 的字段关系来自源码追踪，并与失败日志一致。这是可复查的因果判断，不把缺失 ledger 行伪称为已独立原生采证。

## 最小修订边界

仅在 `reserveRuntimeLocalLaunch` 的旧 hold 处理处加入“已正确释放则不再追加”的校验分支，并可在本文件增加小型专用 helper。原 admission、同 epoch 处理、新 RESERVE、预算 exposure 与事务边界保留；`budget.go`、调用者和 ledger schema 不需扩范围。

已有 RELEASE 不能仅凭 count、operation 或 event ID 判定安全：

- 先确认原 hold 是当前 project/run 的规范 local-launch RESERVE，request/event 与原 epoch 一致、reservation_id=null、UPPER_BOUND、零金额且币种有效、policy属于原合法绑定、receipt_hash可重算通过。不能把 prefix 扫描结果自动视为可释放的其它 provider/非零/UNKNOWN 账。
- 以该 hold 对应的确切 `/released` 查记录；必须为同 project/run/request、该 event、RELEASE、reservation_id=原 hold.id、同 policy、ACTUAL、零金额同币种，且 receipt_hash 与内容一致。已存在错误绑定、错误 operation/hash 或歧义记录时返回错误，不能跳过或重写。
- 真正匹配的历史 RELEASE 直接保留，包括其原 occurred_at；只为尚未释放的旧 hold 追加一次。保持 append-only，不删除、修改旧行，不生成新 event ID 来掩盖重复，不统一捕获 IDEMPOTENCY_CONFLICT 当成功。
- 继续在调用方事务内完成；任一绑定失败或新 RESERVE失败，旧 hold处理、新 epoch、checkpoint carry、activation/dispatch 不得部分提交。不要用当前 policy/币种替换旧记录来使比较通过；若发生不兼容绑定，明确拒绝。

## 共享调用路径与必要验证

共享调用者包括 `orchestration.go:507` 的初始准入、`durability.go:394` 的 checkpoint/current-context 重建、`resources.go:346` 的 resource switch，以及本次 sealed pause successor。影响范围是同一 Run 的重复 local-launch epoch；不能把它描述成仅适用于 Mu 第二次暂停的临时分支。当前 `TestW12BudgetLeaseTakeover` 只覆盖 epoch1→2 和 epoch2重放，未覆盖再进入 epoch3。

候选必须补足：

1. epoch1→2→3，最好再到4，每次独立提交；每个历史 RESERVE 恰有一个绑定自己的 RELEASE，当前 epoch只有一个 open hold。同epoch重复调用不增行、不改旧行hash。断言按 request/reservation_id 对应关系计算，不能仅统计 RELEASE 数量。
2. 错 run/project/request/event/reservation/policy/currency/operation、非零金额、错误 receipt_hash 的“已有 release”不得被当成幂等成功；没有匹配 release时不得静默漏放旧 hold。保留非 local-launch provider、MODEL UNKNOWN和历史账。
3. 对错误 release，验证整笔 successor事务回滚：当前 Run epoch、pause状态、carry、activation/dispatch和 ledger均不部分推进。
4. 原 `TestW12BudgetLeaseTakeover`、`TestCompletedRuntimeLocalLaunchRelease` 回归；本次真实两轮 PAUSE→RESUME→最终settle，并导出预算ledger，证明epoch1/2各一次释放、epoch3按终态既有逻辑释放。模型/工具和queue计数仍须原计划证明。

新增定向预算反例可放在已获授权的 `runtime_pause_windows_test.go`，原预算测试文件只运行、不修改，故此轮无需第10文件。如果作者选择改动跨平台预算测试文件，应先列明该额外路径，由Root另行登记。

最终接受依赖作者具体候选和新鲜独立验证。作者06失败与此前所有失败都必须保留。
