I17 绑定修订已准备，所有候选均未采用、未编译、未运行。三个真实 callback 继续成功返回 int64(1)，失败返回 nil 和固定错误；坏输入 SQL 的 primary code 1 是源码推断，等待独立受控原生执行。driver 旧包 I01..I16/I18 的测试正文及原 v3 的 28 个测试正文逐字保留。旧 partial17 author/controller 未写。

innocuous_test.go.proposed.txt 只修订 I17 error 合同和坏 INSERT 后行数不变断言。原 adapter 仍为空，因私有 domain factory 无法接入 driver module，该旧 selector 仍 FATAL_OPEN。真正的下一 I17 selector 位于 proposed internal/domain/client_cancel_finalization_i17_integration_test.go；它直接调用私有 factory，并查询 domain init 实际注册的三个名称、arity、scalar 与 deterministic+innocuous flags。没有公共生产 export、反向依赖或复制替身。

client_cancel_finalization_test.v4.go.proposed.txt 把数据构造拆为 f08FullJournalDataFixture 与完成后 replay 的原 f08FullJournalFixture。step 在修改状态前封存不可变原字节，不再调用 evaluate；data setup 不调用 factory。原单事实反例和 R2/初始化/profile OPEN 拒绝断言全部保留。未来 TestF08I17ProducerFreeze 必须用实际 Go data producer 对独立 raw 帧逐字核对后，才允许另一受控进程测试 callback。

vector-manifest.json 含 109 组 source-derived 好/坏向量：request 原 envelope、padded Base64 私有 header、实际 Envelope.ContentHash 合同、单字段 project 错误、BLOB→TEXT、NUL/无效 UTF8；response mode0/1/2、old nullness、ACK operation、合法超过 1MiB 响应；proof 四条 NO_RUN 路径共100个转换前 {action,row,old,sources} 帧。单 action 字段反例由 f08ProofFrame 规定 F08_MODE。好向量的 1 及所有固定错误都是 NOT_RUN 预期，未从 SUT 输出生成。

raw-sequences.json 的 SQL key-order recipe 只是数据配方，不是实际 SQL 捕获。v5-candidate.sql.unchanged.txt 逐字保留原 v5 DDL，v5-source-tuples.exact.json 从真实 DDL 提取34类元组，保留 body/header 原字节 hex、SQL NULL、journal typeof 字段和重复关系。原生数据库行/视图顺序、typeof-before-CAST、所有34源与同事务 parent/member/pin closure 均仍 FATAL_OPEN。通用 CHECK harness 仅证明未来 SQL callback 绑定，不能通过它宣称真实 DDL/SQL24 完成。

下一执行必须由 Root 在独立 fresh worktree/module/resource lease 中整合候选，重读独立审查与全部 source refs，再登记每个 selector 的实际 process/Job/模块和 close proofs。root-resource.proposed.json 故意未填资源，不可直接运行。当前不写 Main、canonical、module/cache、旧封存目录、原 partial17 controller 或任何失败计数；旧 fd09 cleanup 自动审查拒绝保持。

仍 OPEN：真实初始化 auth_principals/auth_grants/有效时钟/current ownerRoot/executor/profile 权限；mode3 原 caller；later-epoch operation producer；普通 native/SDK 最终权限与历史/备份闭包；真实 v5 DDL 源捕获与迁移22/23兼容回退；大响应完整 solejournal 完成/回放；完整 Go module/compiler/purity 闭包。不能以当前四条 NO_RUN 静态数据代替这些门。

static-byte-audit.json 验证完整正向/逆向 diff 字节、17个其他 driver 测试和28个原 v3 测试正文、数据构造无 callback/evaluate、原始 args 类型/hash、34类来源计数以及46份输入前后不变。仅 Python AST 与文本结构检查，不是 Go AST/编译。实际 Python preparation/audit native exit 均为0；一次 PowerShell parser 失败 outer1/native NULL 单独保留，未重跑同失败输入或改计数。
