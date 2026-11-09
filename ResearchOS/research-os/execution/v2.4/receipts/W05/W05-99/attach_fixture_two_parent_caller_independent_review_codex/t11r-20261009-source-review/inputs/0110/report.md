# ATT3 independent Source review

**Verdict: APPROVE — SOURCE ONLY**

**Decision: SOURCE_ONLY_APPROVE_WITH_FRESH_POSITIVE_BLOCKED**

ATT3 在恢复 helper 中消除了 ATTACH-RESTORE-001 的旧 lease 续租旁路和 ATTACH-RESTORE-002 的 RFC3339Nano 文本排序反例。未发现新的 Critical 或 Important Source 阻断项。此结论只允许 Root 将冻结候选送入后续独立编译/验证，不授予产品、Owner、native 或 formal authority；fresh restore positive 仍为 BLOCKED/PENDING_ROOT_RESOURCE。

## Critical Issues

无新增问题。

## Important Issues

无新增问题。缺少真实恢复正向资源是已明确保留的接受边界，没有用人工观测或静态检查替代。

## Suggestions

- **既有依赖边界，不是 ATT3 新回归：**T6 `client_session_fence.go:71`、`backup_recovery.go:236` 仍将 observed_at/restored_at 按 TEXT 比较，`runtime.go:121` 仍按 observed_at TEXT 取最新。ATT3 仅替换恢复 helper，未修改这些共享依赖。混合小数精度可使 helper 的时间结论与旧触发器不同，例如 barrier=.1Z、实际较新的 observation=.11Z。后续完整恢复链必须另行验证这些现有条件；当前 Source 批准不能宣传为整条恢复链时间语义修复，也不能绕过共享 gate。

## What's Done Well

- 全部时间归一到 UTC instant，latest 同时刻存在任何不完整或绑定无效事实即拒绝，结果不依赖数据库行顺序。
- 恢复判断在续租前执行，并保留实际 observation hash、project/run/current Run epoch、task 绑定与双 settled 标志。
- 原五个 attach 测试和两项 restore 测试文件原字节保留；旧十类 × 两客户端 negative 仍在，新时间 fixture 明确只提供拒绝场景。

## Control-flow and contract review

固定合同 `22_CLIENT_INTERFACE_DETAILS.md:130–147` 要求 takeover 用当前 revision、不可冒用 writer epoch；恢复后须先对账再增加 epoch，handoff 不得自动恢复工作。

| 检查 | 当前 Source 证据 | 结论 |
| --- | --- | --- |
| barrier 最大时刻 | client_protocol.go:1310–1340 遍历所有匹配 project/run 行，逐项 parse，使用 After 更新最大值；未知值直接拒绝 | 不依赖 max(TEXT)，无 barrier 返回普通路径 |
| 最新 observation | :1350 查询同 project/run/current Run lease_epoch；:1362 未知时间拒绝；:1370–1374 校验 receipt/hash/spec/settled 后调用 accumulator | 实际最大 instant，不靠 SQL 字符顺序 |
| 最新同刻冲突 | :1293–1300 对 Equal instant 累积 valid AND | 任一 partial/错绑定均使最新事实无效 |
| 首次新鲜事实 | :1375–1387 只有实际最新集合有效后，earliest valid fresh 才可用于 generation 先后关系 | 旧 .1Z settled 无法掩盖 .11Z partial |
| handoff 全遍历 | :1389–1433 查询关联 project/session/run 的 CLIENT_HANDOFF；所有行先解析 payload/effective/expiry；expiry 必须严格晚于 effective | 匹配事件不会提前 return 并隐藏坏时间 |
| 当前 generation | :1411–1422 保留 sequence 范围、command/protocol/session/run、writer=current epoch、previous=current−1、target/current owner；effective 在 barrier 后且不早于 fresh evidence | 恢复前 future lease 单独不足以授权续租 |
| 写入边界 | :1128 helper 在任何 writer 写入前运行；不 ready 返回 SESSION_BUSY；未恢复 generation 走既有 HandoffEpoch/CAS/journal | 不清除 barrier/queue/control/explicit-resume |
| 普通续租 | 无 run/no barrier 返回 renew=true；原 owner future lease 路径 :1138–1168 保持 | lease-only CAS，不增加 generation |
| 命令及事务 | Execute :727–832 保留 exact replay、identity reservation、savepoint、拒绝回滚和响应 schema；dispatch :901–966 保留 project/principal/revision/epoch gates；handoff/journal 在原 tx 内 | 此段相对 ATT2 全字节不变 |

helper 只含 SELECT。出现解析失败或 latest 不成立时，不进入 writer mutation；错误从原事务路径返回。唯一 production replacement 逆变换精确恢复 ATT2，helper 外前后两段均原字节相同。没有添加网络依赖、runtime observation producer、签名者或执行权。

## Verification Story

- **Tests reviewed: yes。**先读旧拒绝报告、合同映射及全部三个候选测试文件，再沿 producer、barrier、HandoffEpoch、journal 和 Execute 调用链检查。
- **Build verified: no。**未运行 Go/gofmt/parser/compiler/test、SQL、native 产品、模型或网络。不能用词法或 Python 事实替代 Go 编译。
- **Security checked: yes，静态范围。**参数化的 project/run/epoch 查询、既有 trusted native producer 的 dispatch identity/hash/sequence gate、session generation 绑定及写入前拒绝路径均核查；未读取私有文件。
- ATT3 HDF/MF 和 ATT2 reject-review HDF/MF 的四个 Root anchors 在 decode 前逐项匹配。ATT3 的 15 manifest members、关联固定 Source/合同及当前 reviewer runtime 纳入同一 151-entry SourceReadGuard。
- Guard 最终 verification=PASSED、closed=true、retained_handles_count=0、errors=[]；55 份公开输入从受保护缓冲复制，input-copy-index.json 给出原始 pin 到归档副本的映射。未持有 Root canonical/CP360 文件锁。
- 唯一 replacement 位置47875，before4436 bytes、after5793 bytes；逆变换精确。两份旧 test Source 的 SHA256/bytes 分别为180523…/10682、38071a…/4770，byte equality 成立。
- 新增三个测试：生产 parser/accumulator 的时间顺序、相关时间解析，以及四种 malformed/misordered negative × 两客户端。新 negative 同时检查拒绝、Session/Run/barrier 不变、无 CLIENT_HANDOFF、exact command replay；没有写入伪造的正向 handoff。
- 独立 Python 证据使用整数纳秒，覆盖 .1/.11、整秒/1ns、时区等价及两种行顺序；全部翻译 accumulator 拒绝结果符合期望。该证据严格标注为 Python 时间向量/算法翻译，不是 Go、SQL 或 handler 执行。
- **机械错误842保留。**一次只读诊断误把 production-replacements.json 的 list 当 dict 调用.items()。原始 command、traceback 和工具返回完整归档。actual_outer_exit=1；无独立 Python marker，actual_Python_exit=null，inferred_Python_exit=1 单列。不同入口按实际 list 结构读取成功。后续 guarded verifier 为 outer0 且原始输出含 ROOT_PYTHON_EXIT=0。既有失败前缀不 reset。

## Remaining acceptance boundary

真实正向恢复仍需 Root 的授权 coordinator/native 观测、当前 Run epoch 与最新 barrier 后的 durable stop/queue 证据；再验证单次 generation 转移、exact replay、恢复后 lease-only 续租、较新同 epoch 观测、后续 partial、后续 barrier/epoch 改变。新人工 negative 不能提供这些正向证据。active asynchronous takeover 和历史 cached ACK reconciliation 仍按作者声明保持 open。

本 reviewer 仅写入本次独立 namespace；没有改 Main、T6、canonical、ATT3/ATT2/旧审查包或任何 SQL。收到 Root 入口后不再对旧包做写入。FINAL STOP。

