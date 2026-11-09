# Desktop managed qualification Core 独立审查

结论：**REQUEST_CHANGES / NOT_PUBLISH_READY**。候选 `63dec0f43b7a30d36e68a9826dc36e633936318f` 的私有协议、事务确认和真实进程退出已有有效证据，但连续会话入口封锁仍存在两处 P1。

- **DMQ-P1-001：拒绝 SHUTDOWN 清除原资格任务的入口封锁。** `runtime_drain_windows.go:64-79` 在拒绝未结算 Run 后写入 `intakeClosed=false`，后续 `Scan` 又因 `qualificationActive` 提前返回，无法恢复。独立 overlay 实测原 Run 仍 QUEUED、activeRuns=1、qualificationActive=true、intakeOpen=true。建议失败 drain 恢复原封锁状态，release abort 同样保留资格任务的封锁。此证据证明入口错误开放，没有证明发生第二次 MODEL 调用。
- **DMQ-P1-002：初始化没有同步恢复持久入口封锁。** `runtime_coordinator_windows.go:151-167` 构造返回时 `intakeClosed` 为 false，已有未结算 Run 要等首次 Scan 才恢复封锁；`ManagedStartupHold` 分支甚至跳过该恢复。两个独立构造器反例均失败。建议在对外提供 coordinator 前同步建立入口封锁，并在验证恢复完成后才开放。

独立基线：domain 30 个顶层 / 73 个子用例、host 7 / 12、verifier 2 / 9，全部 PASS、无 skip；新增反例 3 个按预期 FAIL。原始命令、环境、退出码和完整输出见各 `*.invocation.json`、`*.stdout`、`*.summary.json`。12 个来源文件、15 份作者证据、2 个二进制共 29 项 provenance 核验通过；审查后候选工作树干净、源码与二进制哈希匹配。

真实 control 生命周期和 host 内 synthetic qualification 分别通过；后者使用实际 verifier/native runtime，但不等于已经完成真实 Desktop 客户端 + 实际 control + Ollama 的完整资格流程。真实模型调用数为 0，正式父任务接受增量为 0。UNKNOWN ledger 导致拒绝退出的问题仍为 OPEN。

保留所有已有失败记录与 reviewer 原始反例。后续应冻结修复候选，再复核这两个 P1 及相邻资格、退出路径。
