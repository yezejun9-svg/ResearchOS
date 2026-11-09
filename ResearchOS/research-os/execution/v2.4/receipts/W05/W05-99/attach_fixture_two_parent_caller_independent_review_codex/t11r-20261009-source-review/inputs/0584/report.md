## Review Summary

**Verdict:** APPROVE — SOURCE ONLY

**Overview:** 此修订只改变 TestClientSameWriterRenewsExpiredLease 的测试主体，要求 ATT3 原始 handler 返回真实 COMPLETED/AttachResult，并与公开 session.get 和已提交租期一致。未发现新增 Critical 或 Important 问题；该测试的实际结果仍为 OPEN_PENDING_ROOT_EXECUTION。

### Critical Issues

- 无。

### Important Issues

- 无。

### Suggestions

- 无本次必要建议。

### What's Done Well

- candidate-root/internal/domain/client_protocol_control_windows_test.go:49：原过期租约 UPDATE 仅增加 workspace_ref、model_config_ref、core_build_id 三个 fixture 元数据。mixedSessionEvents 原本已映射 session/project、revision1、epoch1、mixed-client 和非空 synthetic upstream ID，但没有提供这三个快照必需字符串。BuildSessionSnapshot 在 client_protocol_journal.go:281–285 对缺失值拒绝；补充值与该本地夹具范围相称，并在报告明确为 synthetic，不能用作真实 workspace/model/native 证明。
- candidate:60：检查的是 svc.Execute 原始返回值；要求 COMPLETED、schema-valid AttachResult、原 command/method/protocol/session、project、owner、revision3、epoch2 和未来租期。没有改写响应、升级 cached ACK 或制造 journal。
- candidate:89：原 SQL writer_epoch/lease_expires_at 读取及 epoch2、未来 deadline 断言逐字保留。
- candidate:99：新 session.get 通过原公开 Execute 路径，验证结果 schema、revision3、整个 snapshot Hash 相等及公开租期与 SQL 的已提交字符串相等。
- candidate:123：旧 expected_revision=1 的 VERSION_CONFLICT 检查逐字保留，未因新增读取而更新旧请求版本。
- 独立前向替换与逆向恢复均通过，base 与 T6 实际 5642 bytes 相同。目标主体外前 1915 bytes、后 1997 bytes 完全相同，imports、两个其他测试和三个原 Test 名称均不变。生产文件未改变。

### Verification Story

- Tests reviewed: yes，先阅读候选差异和原测试主体，再核对 mixedSessionEvents、ATT3 attach 分支、HandoffEpoch、BuildSessionSnapshot、Num/Str。ATT3 对已过期 owner 跳过有效续租分支，HandoffEpoch 增加 revision/epoch，CLIENT_HANDOFF 再增加 revision，因此本夹具的 revision3/epoch2 与现有实现相符。
- Build verified: no。未执行 Go parser/compiler/gofmt/test、SQL、native、模型调用或正式验收。
- Security checked: yes，静态检查原 f.owner 鉴别主体、原回执身份、COMPLETED 门槛、结果 schema 和公开快照一致性。固定 synthetic 输入局限于本测试主体；没有新增生产依赖、绕过或真实资源资格声明。
- Performance checked: 新增一次有限的公开读取，无循环、轮询或额外外部调用。
- 实际入口 HDF 49fcfa0afbb15b0bb65f54cc459fd1abb9da5f973a56c4a55ad3ab237bb4cfda /7604，MF a8590a83c616c510b48d15e43fff4f03ec6426acefe4f3f7da129d0a15a7be12 /6932。18 个清单成员和 78 个唯一输入全部经真实 FILE_SHARE_READ_ONLY SourceReadGuard 核对路径、bytes、SHA256，全部闭合、retained0、errors0；78 个输入副本封存。
- 独立静态校验 fdaf67 outer0 / ROOT_PYTHON_EXIT=0。它是 Python 字节与文本校验，不是测试运行结果。

### Failure Accounting And Scope

- 本审查新增机械失败 857：原 read.py 的 Test 名称正则过度转义，chunk39553e outer0 / ROOT_PYTHON_EXIT=1 / nativeNULL。原脚本、完整输入输出及 78 输入 guard closure 保留，失败未记为通过。新 read_v2.py 修正后检查通过。
- 作者已有 853 /854 /855 的原件包含在 Source MF，并已核验复制；其实际 outer 分别为 1 /0 /NULL，Python/native 均 NULL，855 没有创建进程。沿用 Root 已登记计数，不重复计入，不重置。
- Q5 与 ATT3 仅提供已审 Source 依赖；本修订不证明新的 actual pass。fresh restore、shared TEXT whole-chain、active asynchronous takeover 和 historical cached ACK reconciliation 继续保留 OPEN/BLOCKED。
- 仅写独立审查唯一目录；未改 Main/canonical/T6/作者 Source/生产或他人成果。authority=NONE，formal_acceptance=false。封存后 STOP。

