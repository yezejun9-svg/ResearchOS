## Review Summary

**Verdict: REQUEST CHANGES — I17 binding preparation only.**

目前能定位完整的三函数候选体、注册名、冻结 schema、真实原始 header producer 和 SQL24 候选 DDL，但没有已采用的 Main 三 callback，也没有已经封存并独立验证的完整 I17 raw vectors。现有 I17 应继续 FATAL_OPEN。旧 fd09 的 driver18 源码准备结论、driver 接受状态、失败与 cleanup 均未改动。

### Critical Issues

本次只读映射未发现需要通过扩大授权来处理的 Critical 项；未执行候选或 SQL。

### Important Issues

- **I17 坏向量断言不符合真实 callback 合同。** a84ef 的 innocuous_test.go.proposed.txt:289 要求坏输入返回整数 0，:291 要求 CHECK 275。v3 源码 :109–110、:120–121、:157–158、:1613 明确为成功 1 / 失败 nil+固定错误；v5 source-contract.md:31 也规定错误中止 SQL。下一新候选应给每个坏向量增加 CALLBACK_ERROR 类型与固定 F08 error code，直接调用及 INSERT 都核对真实 callback error，坏写入后的计数保持。原生 SQLite primary error 1 只是待实际受控执行验证的预期，本次没有执行证明。只有真实会返回 0 的单独向量才能保留 CHECK 275；不得把错误包装成 0。
- **真实函数的 package 边界尚未接通。** v3 :92 的 factory 是 domain 私有函数，Main module 是 researchos.local/research-os，driver18 :4 是 modernc.org/sqlite 的 sqlite 包。直接导入 internal/domain 违反 internal 可见范围，且 domain 已依赖 sqlite；复制候选或造全拒绝函数不构成绑定。最小下一准备可在 ResearchOS domain 包内创建独立 I17 integration harness，使用真实 domain init 注册和私有 factory，保留单独受控进程与实际 SQL function_list / trusted_schema=OFF 检查。Root 还需明确该 selector 的模块/目录协调范围。当前没有采用或执行此方案。
- **完整 raw vector 和生产 DDL 绑定仍缺。** v3 request/response 的 raw envelope、header、identity、ACK/COMPLETED builders 可用；完整 NO_RUN fixture 的 step() :482–485 会调用被测 evaluator，再推进状态。不能运行完整 builder 后将结果包装为独立预期。下一候选需封存每一步前的原始 {action,row,old,sources} 与指定单事实坏输入、storage classes、固定预期、原字节 hash。v5 DDL 直接调用 proof_v1 共 22 处，request/response 名称出现 0 次；其验证由 proof 内部 groupRequest/finalResponse :815/:1453 调用。通用 CHECK 表不足以证明这些真实 trigger/view/relational 前提。

### 可直接用于下一 Source 准备的来源

完整 path、SHA256、bytes、lines 和只读副本见 selected-inputs.before.json、source.locators.json 和 mapping.json：

- v3 source SHA 73fe76a6… / 117346B：:66–90 注册 request_v1(2)、response_v1(5)、proof_v1(2)，全部 deterministic+innocuous；:92–145 是实际 pure closures。
- v3 tests SHA 55c2e4a8… / 61131B：:31–50 raw header/原 envelope/完整 identity；:104–119 request 好/坏来源，principal 改动故意仍合法，不能作坏向量；:156–192 三种 response 模式及 ACK operation 反例；:196–203 合法 >1MiB response；:492–537 四种 NO_RUN journal 路径数据，:542–555 单事实反例。
- 原 producer frozen 005-client_command_identity.go:222–230 保存 env.originalRaw 的 padded Base64 header；Main client_protocol.go:367 使用真实 Envelope.ContentHash。不能以 JCS(raw-envelope) 的 digest 替代 request_hash。
- frozen 015/016 schemas SHA 8943fe36… / 161794B、b53d9e6e… / 204466B；LoadSchemaWithExternals、DecodeEnvelope/Response、ValidateResultAgainstMethod、Hash/Receipt/JCS 公有源已定位。此列表是具体闭包依赖入口，未声称 Go 编译闭包通过。
- v5 candidate.sql SHA e3d58e53… / 77333B：:317–350 提供真实 34 类 source 元组，:359 admitted mode0，:364 final mode1，:369/:374/:379 materialization mode7，:384 origin mode2，:393 derive mode8，:398 dispatch mode4，:410/:415/:430 journal/commit mode5，:436/:441 control mode6。必须原 typeof 后 CAST BLOB，并对原 body/header 使用 hex(actual bytes)，保留 SQL NULL、重复引用及完整 member/pin 集合。

### 下一最小函数组与缺项

先准备三个独立的数据构造函数，分别给 request、response、NO_RUN proof 提供冻结 raw args 和坏输入的固定错误预期；构造函数不能调用 callback/evaluate 获取预期。proof 最小正例从 admitted.insert 前完整状态开始，并另封完整 journal.update/commit 路径反例，避免仅用 digest mode 或空 sources。再准备 domain 内的真实三函数 SQL 集成 harness、类型化 corruption expectation 和实际 v5 DDL 作用点的用例清单。所有新数据与代码应在新 namespace，须 Root 批准下一 scope 后才能取用。

初始化授权的 auth_principals/auth_grants/有效时钟事实、mode3 caller、later epoch operation producer、普通 native/SDK 与历史闭包仍 OPEN；v3 明确 fail closed。当前源码与四条 NO_RUN 合法路径的静态准备不能升级为三 callback 完成。合法 >1MiB 完整 solejournal 完成/回放也仍待真实用例；不得恢复已经撤去的新 response cap。

### What's Done Well

候选保留真实错误和 OPEN 拒绝，未以 profile 标签造授权。I17 缺资源时直接 FATAL_OPEN，能阻止空绑定或全拒绝替身被计为通过；冻结 DDL保留完整 source tuples、BLOB 原字节和关系约束入口。

### Verification Story

已只读核对测试意图与 callback/DDL 调用链，34份选定输入加1份 journal 具有原字节副本及前后 hash；Main internal 非测试 Go 注册检索为 0。未运行 Go/gofmt/AST/build/SQL/native driver/HTTP/SDK/model，所有向量 NOT_RUN，SQLite SQL24 未采用。只检查公有源码的接口/拒绝边界，未读取密钥或运行时授权状态。

本轮 metadata 新 origins 为 b9d4f8（outer 1/native NULL）、bafc93（outer 1/native NULL）、427f1a（outer/Python 1/1），各一次，原命令和工具诊断见 origins.json；未重跑失败原输入或修改任何失败计数。旧 fd09 cleanup 拒绝及误写文件保持原状。
