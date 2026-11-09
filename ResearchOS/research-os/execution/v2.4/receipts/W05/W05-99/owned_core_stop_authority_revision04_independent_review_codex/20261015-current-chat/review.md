# STOP-r4 独立审查

结论：**NEEDS_CHANGES**。候选 `ab308912117dac59cadd5aa2e75b46a418e41b6b` / tree `c45e5bd0a1890c6789ddb590e57d9d7db0f67521` 保持干净；全19路径及r4两路径delta与冻结输入一致。r4的owner/ACE修复获得独立支持，但全19检查发现一项新增P2问题，尚不能接受整个候选。

## STOP-R4-F01：额外 MODEL effect 的 state 缺失/null 会被漏计

位置：`internal/store/owned_stop_barrier_windows.go:163-165`，调用点 `internal/ownedcorestop/stop_windows.go:119`、`:292`。

当old subject已有一条CONFIRMED MODEL effect，另一个同project/run effect_key的最新记录为 `{"payload":{"capability":"MODEL"}}` 或 `state:null`，SQLite `json_extract` 返回NULL。`IN (...)` 和 `!= 'CONFIRMED'` 都不会计入该行，三个effect计数仍表现为0/0/1，`ExactOldSubjectSafe()`误返true。

独立真实schema24 SQLite + reserved writer复现了missing/null两例。16项有限矩阵中仅这两项失败：bool、number、array、object、empty、unknown enum、额外CONFIRMED、capability缺失/null均被拒绝；old-model最新state缺失/null因确认数0被拒绝；更早history被有效最新sequence覆盖，符合当前latest-state设计。

真实compiled PREFLIGHT_ONLY CLI也将坏基线标记 `ELIGIBLE_FOR_INDEPENDENT_REVIEW`，`missing=[]`，基线87表36行、`quick_check=ok`。该用例没有生成STOP grant，没有调用Commit，没有发native signal。完整baseline hash无法识别在preflight之前就存在的分类遗漏；Commit复用同一catalog是源码结论，不是已经执行的坏基线停止。

最小修复路径为 `internal/store/owned_stop_barrier_windows.go` 和 `internal/store/owned_stop_barrier_windows_test.go`：将最新effect的缺失/null state明确计为不安全或拒绝，并保留最新sequence与subject约束。后续须验证坏基线真实preflight拒绝、0 STOP grant、0 native signal，以及原有效正向。

## 已支持的修复和执行证据

- 原STOP-R3-F01：可信owner明确为current operator/System/Administrators/TrustedInstaller；直接/继承的Everyone/Users危险ACE、unsupported/malformed ACE被拒绝。实际copied parent+child安全路径通过，D不可信安装继续拒绝。
- 目录 `GENERIC_WRITE` 实际OPENED事实保留。持有该writer时选定ancestor rename仍被拒绝；final写入、删除、重命名、覆盖及同名替换拒绝。没有把OPENED当作替换成功或宣称目录完全不可写。
- 自加native用例允许孤立FILE_ADD_SUBDIRECTORY，验证选定路径保留；INHERIT_ONLY在parent不生效但传播到final后被拒绝；即使ACL改后仍满足可信策略，ancestor/final同句柄SDDL漂移也被拒绝。
- 原数值native proof修复：28项字段测试通过；真实missing-worker-exit preflight为STOP_UNAVAILABLE且未编译STOP grant。
- Caller ctx/earlier deadline/final prewait取消三项native边界测试通过，durable claim/intent的synthetic journal检查通过。完整Commit在自身durable intent之后被取消仍为未执行的集成边界。
- 自行构建两个不同grant CLI、独立C copied helper+child、D SQLite/data/operation：`STOPPED_LEASE_VERIFIED`，一次TerminateProcess，同一保留句柄观察exit `1381191507`，postflight87表35行且quick_check=ok；inspect/repeat commit结果及journal字节稳定。

全19逐路径语义记录、源码SHA、case及capture引用见 `review.json`。历史worker/verifier凭据在这些用例中明确为synthetic；只有自己的copied Core真实native signal/wait被执行。

## 证据边界和失败保留

作者20个nonzero已逐条读stderr/stdout：4个cross-phase ACTION_DENIED得到独立确认，其余16个历史diagnostic原样保留（包括错误测试期待、路径、编码及harness失败），不抹去中途行为。Root已有22 mixed records（另含初始相邻E和未授权C根偏差），本轮不重新计数。作者后续C data/operation与amendment措辞的歧义单列；本轮data/operation全部位于获准D TMP。

本轮所有失败、父/子命令退出均保存在diagnostic-ledger；一条PowerShell管道解析失败未进入child logger，其捕获缺口明确单列。工具模块/参数问题不是Source测试通过；新增安全断言失败归入STOP-R4-F01，不归为工具diagnostic。

仍未覆盖：foreign-user token实际执行、hostile race穷尽、power-loss、full Commit intent后取消、所有深层SafetySnapshot分支。未碰实际Core/DB/API/keys/model，未新增proof class，未改Source/shared state，formal increment为0。Root单独决定采用，不签发自身接受或实际/正式完成。
