## Review Summary

**Verdict:** APPROVE — SOURCE ONLY

**Overview:** Q5 将三处运行时测试的首次 session.send 绑定到 session.attach 原始 COMPLETED/AttachResult 返回的项目、会话、writer、revision 和 epoch，并验证公开 Session 状态、提交事件和原命令重放。静态审查未发现新增 Critical 或 Important 问题；本结论不代表已编译、已通过 Go/native 测试或已满足正式验收。

### Critical Issues

- 无新增发现。

### Important Issues

- 无新增发现。范围外的 TestClientSameWriterRenewsExpiredLease 仍期待 ACKNOWLEDGED，需由 Root 单独组合已经授权的修订；Q5 未将该冲突伪报为解决。

### Suggestions

- candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go:867：大于 2^53 的新增测试直接构造 typedRuntimeFixtureSnapshot，因此证明的是 int64 代际比较。后续如需扩大数字精度证据，可增加完整 SessionSnapshot 经 typedRuntimeFixtureSnapshotBinding 解码后的高整数精度测试。当前代码从原始 map 的 JSON 直接解码为 int64，未把 normalizeNumbers 的 float64 输出用于绑定；本项不是本次 Source 阻断项。

### What's Done Well

- 原始四文件的 181 个 t.Fatal/Error/Skip 系列调用、20 个 Test 名称、196 个含断言或错误的 if token 序列全部相等；其中 190 个严格 t 断言分支、6 个 fmt.Errorf 分支。独立校验从 Q3 顺序应用替换后完整还原 Q5，再逆向恢复 Q3。
- Goal 文件 16059 bytes、SHA256 4809121015b1345adc4777385236cf692f2e4b53de2ab56cc97b89acffeb30e0 与 Q3 完全相同，expired_lease / missing_lease 的 LEASE_EXPIRED 断言保留。
- helper 前 24950 bytes 完全相同：严格 JSONL、原 pass/fail/skip 状态机、固定 Go/test2json/Node/Mu 资源、Root Job 来源、TLS、配置与 provider/profile 路由未改动。
- helper:629–661 只接受原命令的 COMPLETED、正确 method/protocol/command/session/revision、schema-valid AttachResult、write_owner_acquired=true 及匹配的 project/writer。ACK 和只读结果不会被升级。
- helper:697–755 从公开 session.get 取得当前 revision，再以 null writer_epoch 调用原 session.attach；之前的 session.create 身份绑定仍需一致。命令通过原 muClientCall/handlerCommand 使用 f.owner 鉴别主体。
- helper:666–694 对同 owner 有效租约要求 revision/epoch/event_sequence 不变；真实接管要求 revision +2、epoch +1、event_sequence +1，并核对命令时间区间和未来租约。该 +2 与 ATT3 的 HandoffEpoch + journal 两次 revision 写入一致。
- helper:750–803 核对原 AttachResult 与实际公开 SessionSnapshot 相等；接管必须只有一个与原 command_id、前后 owner/epoch、时间和 writer lease 全部相符的 CLIENT_HANDOFF；续租无新事件；精确重放必须返回相同 terminal，且公开状态/事件不发生二次修改。
- 三个 runtime 文件分别只有两处输入修改，首次 session.send 使用返回绑定的五个字段；原业务断言、后续失败/旧绑定分支不变。helper 新增 17 类 terminal 变异拒绝和 7 类代际变异拒绝，明确仅为 Source 测试。

### Verification Story

- Tests reviewed: yes，先读新增测试，随后读取公开契约 22_CLIENT_INTERFACE_DETAILS.md:120–147、ATT3 attach 写入实现及实际 snapshot/事件/鉴别 helper。所有测试仅静态审阅；未执行 Go AST/compiler/gofmt/test、SQL、native 或模型调用。
- Build verified: no，按本任务授权范围留给 Root 的隔离组合和运行。
- Security checked: yes，静态检查原鉴别主体、不可伪造完成状态、快照/schema 边界、精确命令重放和资源配置不变。无新增生产代码或依赖。
- Performance checked: 新 helper 仅增加有限次数的公开读取和一次精确重放；events limit=2 且拒绝 has_more，没有无界轮询。
- 入口 HDF 5a503f141b0c167eb5071f8224c0b9594700f86b18855ca3903339b6f6f0a5af /10563 和 MF c8bd3b7a4256c1e619d319d4debc745d91e98059ccb82e01e8ec51f44b0784e7 /10896 均实际核验；27 个 MF 成员、177 个唯一输入引用经真实 Windows FILE_SHARE_READ_ONLY SourceReadGuard 获取并核对 SHA256/bytes/final-path，已闭合，无保留句柄。独立来源副本 81 个。
- 自编 Python 词法校验 ca7d80 为 outer exit0 / ROOT_PYTHON_EXIT=0，前向/逆向、token 比较及新增 17+7 模式计数通过。这不是 Go 构建或测试证据。

### Scope And Failure Accounting

- 新增审查机械失败 848：首次已枚举为 HDF.json/MF.json，但 reader 错用 HANDOFF.json/MANIFEST.json，CreateFileW 报 FileNotFoundError；原 entry.py、完整输入输出、失败 guard closure 保留。chunk25a6b5 outer0 / markedPython1 / nativeNULL。
- 新增审查机械失败 852：自编静态校验错把顺序替换坐标当原始文件坐标；原 static_analysis.py、当次 read.py 输入版本、完整 IO 和 177 输入闭合记录保留。chunka51ac3 outer0 / markedPython1 / nativeNULL。新 static_analysis_v2.py / read_verify2.py 按顺序坐标正向和逆向校验通过；失败未重置。
- 作者既有失败 845 原件 ecba74f5cd81851e11963d74182b85ac3c593bbe6454ec7560bedc3238adfbbd /30466 已核对和复制，沿用 Root 已计数记录，不新增计数。其他分支失败不归入本支。
- ATT3 仍仅为 SOURCE_ONLY_APPROVE_WITH_FRESH_POSITIVE_BLOCKED。active asynchronous takeover、historical cached ACK reconciliation、true fresh restore positive 和 shared TEXT-dependent whole-chain 验收继续 OPEN/BLOCKED；纯 tuple 测试不提供这些能力的证据。
- 原 T6 的 49 Sources /25 selected parents、61 PASS /6 FAIL /0 SKIP 和八个 attach 失败 leaf 均属于历史实际运行，未被本次 Source 审查覆盖或改写。
- 仅写本独立审查唯一目录，未改 Main、canonical、T6、作者 Source 或他人成果。无发布/签署/正式验收权限。封存后 STOP。

