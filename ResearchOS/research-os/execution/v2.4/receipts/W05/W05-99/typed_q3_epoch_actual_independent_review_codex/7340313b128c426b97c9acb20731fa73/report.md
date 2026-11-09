## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** Root T6 的 Q3 + epoch 49 Source 实际组合已执行并完整关闭，独立判定为 `FAILED_EXECUTION_CLOSED`。Goal 与 workspace epoch 的实际通过可作为限定范围的分项证据；6 个 runtime 父包装、8 个子叶用例失败，整体 typed runtime/native/FULL/formal 均未通过。

### Critical Issues

- `candidate-root/internal/domain/runtime_tool_integration_windows_test.go:40` 与 `runtime_typed_client_fixture_windows_test.go:571`：`muClientCall` 只允许 `COMPLETED`，却被用于实际返回 `ACKNOWLEDGED`、revision 3 的 `session.attach`。6 个 fresh child runner 下的 8 个叶用例都在该阶段报错，因此后续 runtime 行为尚未获得这次测试证明。应给 attach 使用符合其契约的专用检查，核验 accepted operation、Session 身份、owner/lease 与真实 revision；再在新的 Source 及新的实际组合中验证，保留本次 failure823 与原始事件。不要把通用 helper 放宽为无条件接受任意状态。

### Important Issues

- `candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go:572`：attach helper 还要求响应 revision 等于 created revision。该断言本次未执行到，不能声称已经实际失败；修复状态检查时应结合 attach 的真实写入/lease 状态确认 revision 契约，并用响应与事务读回保持后续命令版本一致。

### Suggestions

- `validate_q3_epoch.actual_owned.py:94`：下次实际运行可把 canonical 的 pre-run hash/bytes 单独落盘。本次 Root 的内存前后比较断言确实通过，当前独立 hash 也匹配旧 CP357 封存，但没有独立保存的 T6 pre-run receipt；本报告保留该边界。

### What's Done Well

- 官方 pinned test2json 输出中的实际 `fail` 没有被文本日志或部分通过覆盖；父包装严格失败，最终 runner exit 1 被完整保留。
- 4 个 owned Job 均关闭，5 组 SourceReadGuard 共用精确输入并全部释放。50 个公开 child evidence 文件已经逐字节复制进正式独立审查包及 MF，包含全部 raw/JSONL/result 和 8 份公开 TLS 证书，不再依赖 `.local` 作为唯一证据。

### Verification Story

- Tests reviewed: yes。从 Source 重建精确 25 父 scope；parent JSONL 有 61 pass、6 fail、0 skip，67 个 run 各有唯一 terminal，package terminal 为 fail。6 个 child runner 为独立 PID，8 个叶全部因 attach 返回状态失败；每个 runner exit 1。native child PID/exit 原字段为 null，未虚构直接观测；官方 reporter 的退出传播只支持静态推断。
- Build verified: yes，复核 Root 实际 receipts/raw 及输入，未重跑。fmt/list/compile/parent exits 为 0/0/0/1。352 packages、3,726 build inputs、600 product inventory、8 compiler tools、36 embeds 均复算并与 Go list、guard 集合相符；总计独立核验 4,141 个唯一文件的精确 hash/bytes。
- Security checked: yes，限定公开证据与 Source。Go/Node/Mu/test2json 由 held input refs 固定；test2json 直接使用官方冻结二进制。此次提供者仅 synthetic loopback TLS，Root 记录 external provider requests 0、original trial provider requests null、original trial DB untouched；未执行新的 Go/native/SQL/model/private workload。
- Main/canonical: 当前 Main 输入匹配 T6 input guard 固定值；CP357/OW/SS/CM 与此前封存精确一致，且本次审查前后无变化。T6 的 closure 在完整内存前后比较通过后写出失败闭合记录。Main 未采纳、formal_acceptance=false。

Goal 的 expired_lease、missing_lease 与 workspace import epoch 均有独立 run/pass 事件，接受仅限本次 synthetic component observed scope。没有把它们升格为 native/runtime/FULL 或产品正式验收。
