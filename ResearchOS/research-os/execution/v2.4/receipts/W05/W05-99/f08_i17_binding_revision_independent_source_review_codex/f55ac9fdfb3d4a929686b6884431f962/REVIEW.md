## Review Summary

**Verdict:** REQUEST CHANGES

本包已把真实私有 factory、三函数注册及独立 pretransition raw 数据接到 domain 测试候选。还有两项需要最小修正；本结论仅针对源码准备，不能作为 I17、三 callback、SQL24 或正式用例接受。

### Critical Issues

无新发现的 Critical 源码问题。

### Important Issues

- **I17-R01 — prepare_binding.py:175；audit_static.py:68、89–92。** v4 test 整个文件从 LF 改成 CRLF，28 个原 Test body 原始字节全部改变；作者审计经过换行规范化才断言相等。whole forward/inverse 确实逐字节闭合，但不能证明旧 body 不变。下一新包保留 LF，重新生成候选与逆差异，先比较原始 byte body。现有 sealed 包保留。
- **I17-R02 — prepare_binding.py:375–379。** 100 个 proof 坏输入全部仅把 action 改为 unbound.action，固定在 v3 f08ProofFrame:396 返回 F08_MODE。它们没有验证 source/member/pin/header/journal 约束。保留这些 dispatch controls，补 minimum-source-fact-plan.json 中五个同 mode/action/typed shape 的 raw 反例。真实 private callback 直接调用、SQL 调用及 generic CHECK 均检查 nil+固定错误、SQLite primary1、失败 INSERT 无增行；真实 v5 DDL 仍 OPEN。保留的原 TestF08FullJournalSingleFactMutations 直接调用 completedJournal，不能替代 raw callback 绑定反例。

### Suggestions

无需扩大本轮产品源码范围。Root 的 I01–I16/I18 独立支路可继续；本包的 I17 仍 FATAL_OPEN。

### What's Done Well

真实 domain 私有 factory 没有新增 public export 或 sqlite→domain 反向依赖。回调错误契约已经修为 nil+fixed error，注册 name/arity/flags 有实际候选断言。四条无 SUT authority evaluation 的 data-only 构造器在变更前冻结 row/OLD/sources；全部 100 frame 与 109 vector 原始字节、347 个 BLOB ref 使用次数已重哈希。生产 v3 source、fork sqlite.go、DDL34 保持原 hash；其余 17 driver Test body 原字节相等。

### Verification Story

实际重哈希作者 431 个成员（27,969,736 B）及 manifest，共 432 ref；46 个原公开输入及既有 mapping 35 源 ref 均 0 drift。whole forward/inverse、ABSENT harness 的创建与逆向还原均逐字节成立。四条序列为 24/24/26/26 frame；109 vector 为 request4/response5/proof100。1,201,048 B 合法 response raw fixture 已核，未新增 response cap。

测试源码及数据已审，目标测试全部 NOT_RUN；没有执行 Go、GoAST、gofmt、编译、driver、SQL、HTTP、SDK、模型，也未验证 Go producer 与 Python raw 字节相等。native raw DDL、type-before-CAST、auth/current-clock、history、SQL24 安装与 legacy rollback、合法大响应 solejournal completion/replay 全部 FATAL_OPEN。元数据 audit 工具 901e8e outer/Python 0。

本轮仅新增一次 functions.exec JavaScript parse origin，工具在启动 shell 前拒绝；outer/native 均 NULL。完整可见工具诊断已保留，原失败输入没有重跑；作者既有 parser 和旧 mapping/fd09 origins 不重计、不重置。

所有新增文件在本独立 UUID 下；Main、canonical、module/cache、旧包、失败计数无写入。完成封存后 STOPPED。

