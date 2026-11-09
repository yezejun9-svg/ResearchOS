# B-r3 独立审查

结论：**PASS_WITH_LIMITS**。冻结 candidate `fec4a4d7bc8aa4ce6ee1e0f9a7da024bd528ca3f`、tree `730be49f57988da8be32af27225848690d202e63` 的 full9 Source 审查未发现新的可操作问题；B-r2 两项 P1 已由新独立反例复测证明修复。Root 可据此审查是否接受这个精确 Source 切片。本报告不执行接纳，也不增加 actual 或 formal。

## 核心证据

- F01：旧 namespace-swap 反例原样运行，最终目录 rename 被 Windows sharing violation 拒绝。文件正常 write／Sync／read 成功，竞争 write／delete／rename 被拒绝，祖先句柄持续保留。
- F02：实际私有消费者重读原始 raw4 和 MODEL Host 文件并保留句柄。旧 raw4 反例全部拒绝。新独立测试证明全部 5 文件在真实 Commit 和 Rollback 前后都保持锁定，直至显式 Close；Close 后可写可 rename，Check-after-Close 拒绝。
- 新独立 missing5、rejection whitespace、Host bytes、subject4 拒绝与错误退出锁释放通过。原 7 项 MODEL DB tamper 通过。完整 87 应用表按行值核对：仅允许的 9 表变化，精确新增 5 个 version 和 1 个 upload；实际 completed-marker closure replay 为零逻辑增量，MODEL 不重复、被拒绝 TOOL 无 effect。
- 候选作者测试新跑 15 组／83 子项：first gate 正例及 24 拒绝、current Owner、native identity／cleanup／reparse／ACL、20 个真实事务故障（包括 deferred FK 在 COMMIT 失败）。这些结果与独立测试分开计量。
- 原普通 Mu 新跑 3 组／2 子项，零 SKIP，保持 same-process、cancel UNKNOWN 和 claim/cancel 顺序行为。
- 总计 23 个顶层测试组及 117 个子项通过，0 test FAIL、0 SKIP。计数是测试结果，不是正式用例接受数。

## 实际生产调用与未来 C 合同

所有生产 `validatedQualificationFailureTx` 调用均在 `closeOnlineQualificationFailure` 的两个已完成分支。它们先 Check，再 Rollback，最后 Close。新创建分支保留外层 nativeHold 经过校验、写入、Check 和 Commit；错误路径的 defer 逆序先 Rollback 后 Close。私有 helper 成功时把 hold 所有权交给返回值，没有在返回前关闭。

未来 C 必须在自己的 transaction 内按精确 subject 调用私有消费者；成功后持续持有返回的 opaque closure，接受证明及提交依赖操作前 Check，Commit／Rollback 完成后 Close，每条错误路径都释放并处理 Close 错误。不能拿缓存 proof／marker 替代这一流程。本次没有 C 的实现或接纳。

作者部分旧 test helper 在 transaction 结束前 Close，只用于正负校验，**未作为生命周期证据**；新独立 Commit／Rollback 矩阵直接补足本轮所需证明。

## 限制与诊断

精确 15 秒排空边界、全部 cleanup missing/null 组合、foreign SID、敌意并发 race、native CloseHandle／Close 错误注入未执行；历史 worker/verifier Wait 仍未知。directory guard 忽略 CloseHandle 返回状态的既有行为未改，本轮不把正常释放证明扩展为关闭故障证明。未跑全仓测试，未接触原始运行资源，也未替代线上／父任务／正式验收。

reviewer 自身保留：一次上下文恢复时只读 receipt 查询未单独捕获 raw；一次错猜测试文件名导致 native exit1；两次 history schema 调用错误。实际测试和 Source 核验均有预写 recipe、invocation、stdout/stderr 与 native exit。历史作者和旧审查计数不重置；Root 已纠正的 missing73 文件名假设不是 73 个作者缺口。

旧 overlay 三份原文在新证据目录逐字复制并校验哈希；domain 的唯一必要改动是正例 helper 的 Check／Rollback／Close 适配，差异记录在 command005。生产工作树复查 clean，full9 SHA256 见 `final-source-pins.json`。本轮独占临时 cache 已按绝对路径检查后删除，全部证据与原作者被策略拒绝删除的目录保持原样。

详见 `review.json`、`test-summary.json`、`command-index.json`、`diagnostic-ledger.jsonl`。最终 manifest 排除自身和相邻 seal；seal 绑定 manifest 及已关闭的末条 native streams/result，避免自引用哈希。Root 仍是唯一 Source 接纳者。

