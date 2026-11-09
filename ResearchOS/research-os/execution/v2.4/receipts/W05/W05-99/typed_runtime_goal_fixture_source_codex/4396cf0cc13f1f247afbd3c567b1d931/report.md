# Typed runtime / Goal fixture Source

状态：SOURCE_CONSTRUCTED_NOT_EXECUTED_PENDING_ROOT_ACTUAL_AND_INDEPENDENT_REVIEW；authority NONE；formal_acceptance false。

候选目录只含 5 个完整 *_test.go：runtime_permission_windows_test.go、runtime_tool_integration_windows_test.go、runtime_session_events_windows_test.go、client_protocol_goal_test.go，以及新增 runtime_typed_client_fixture_windows_test.go。输入只取 Root 指定的 T5；Main/T3/T4/T5/canonical 均未编辑；生产 Source 成员为 0。

本包只恢复原 FULL 的 10 个失败叶节点。原 FULL 1261 pass /25 fail /4 skip、既有计数和关闭回执不改；scope-map.json 保存每个实际失败事件、原始 JSONL 行号、对应 fixture 变化与仍须实际执行的原断言。

| 原失败叶节点 | Fixture 变化 | 保留断言 |
|---|---|---|
| Permission ALLOW_ONCE / DENY | 独立 TLS 子进程，公开 host.configure，冻结同 ref profile，创建、同 owner attach、原 send | 原冻结动作、单次物理写入/拒绝、provider calls、权限/费用/回放/Run/Task 状态 |
| Permission EXPIRE | 同上述 typed fixture | 过期权限不物理写、原超时与对账状态 |
| Permission BLOCKED_ALLOW | 同上述 typed fixture | 已处理权限不越过另一资源门，仍不写入 |
| MuSessionToolAndIndependentAcceptance | 同上述 typed fixture，原资格和 Model/Tool route | 真实文件 witness、MODEL/TOOL/MODEL、独立 acceptance、recovery、调用次数、单次 assistant projection |
| MuToolRefusalAllowsNextTurn | 同上述 typed fixture | FAILED Run/Task、NOT_APPLIED、不自动重试、下一显式 turn |
| Event rollback=false / true | 同上述 typed fixture | TOOL_STARTED 先提交后 IO、TOOL_RESULT 一次；注入失败无物理 IO/STARTED effect/事件 |
| Goal expired_lease / missing_lease | synthetic unit port 增加原创建主体、project/Session/workspace/model 的有作用域验证 | 原 goal-model 绑定断言、LEASE_EXPIRED、goals=1/tasks=1/runs=0、其余 writer/settlement 断言 |

三个 native builder 只替换目标函数内的 muBrokerFixtureProgram 调用。新 helper 先在相同 fixture 数据库调用真实公共 host.configure（HTTPS loopback/openai/fixture-model/同 synthetic credential_ref），取返回 model_config_ref，再通过既有 handlerTLSCoordinatorFixture 封存 profile 和资格 Task。原 qualifyNativeCoordinator、runtime purpose、executor、tool callbacks 及所有业务断言保留。

ClientService 和 RuntimeCoordinator 使用同一个严格限定 principal/provider/credential ref 的 synthetic metadata port。model config、provider endpoint/hash、CredentialRef/Revision、MODEL effect route、model_qualification hash 完全同源；新增 ModelCredential 只对同 project/runtime/route/purpose/capability/endpoint/hash/ref/revision 返回明确 synthetic token。没有真实账户、DPAPI 或 private claim，日志不回显 token。

正式 create 后新增公开 attach(true, after_sequence=0)，检查同 owner 续租没有改变 Session/revision；原 send 的 revision=1/writer_epoch=1 不改，不静默改 writer claim。Goal 的生产 gate 与 lease 检查顺序不改；mock 验证唯一真实 Goal 创建回执，不能作为真实 runtime/profile/model 资格证明，仍保留原 unqualified admission 行为。

TLS 只在精确子进程中使用项目既有 handlerTLSRootsOnce/x509.SetFallbackRoots；没有 InsecureSkipVerify。检查正常证书/127.0.0.1、空信任拒绝、错误主机名拒绝。loopback readiness 是模型请求前的只读 404，不计业务 model calls，也不重试业务动作。

6 个原 native 顶层 case 包装器逐一运行其完整原子 case；子进程只允许精确原 test name，拒绝 --- SKIP / --- FAIL、缺少预期 RUN/PASS 标记或非零 exit。父进程成功必须存在原 8 leaf 的真实子执行，未执行或缺资源必须失败；不是 skip 或合成 PASS。

Root 实际验证必须提供：

- RESEARCHOS_TYPED_RUNTIME_EVIDENCE_DIR：绝对、Root-owned、全新每次运行目录；case 目录与 raw 文件独占创建，禁止复用同 run 自动重试。
- RESEARCHOS_NODE / RESEARCHOS_MU_BUNDLE：Root 已审的固定资源；Node alias 与 resolved bytes 相等，profile 冻结 binary/bundle hash。缺失直接失败，不给 PASS。
- Root-owned Go Job：覆盖外层 Go test、明确 child、所有 SDK/native descendants；父 exit0 不证明关闭，仍须 Root 的完整 descendant/lease/Job 对账与独立检查。

每个 parent case 保存 child-invocation.json、child.stdout.raw、child.stderr.raw、child-result.json、parent-result.json；每个实际 TLS leaf 保存 tls-public-cert.der。记录精确 Go binary hash、argv、cwd、有限环境变化、PID、实际 exit/原始 bytes/hash。parent-result 的 descendant_closure 固定为 REQUIRES_ROOT_GO_JOB_RECEIPT，authority NONE/formal_acceptance false。完整 raw 仅含 synthetic fixture 路线；用户侧日志另替换已知 synthetic token。

检查边界：使用 Python AST 只选取本包词法检查函数，再对 Go 的 token/括号、原断言调用和 if 节点作文本核对。没有运行 Go AST/parser/compiler/gofmt、Go/native/SQL/model；类型、编译、真实 TLS/SDK/native、Run/lease/permission 行为仍待 Root。不能用静态检查替代实际通过或正式用例接受。

四原文件的 181 个 t.Fatal/Error/Skip 调用与 196 个含断言 if 节点保持；原测试名集合和顺序保持。新 helper 无 skip call，正常 TLS，不改生产字段或 gates。新增 helper 及 4 个完整文件的最终 pins、依赖 pins、最小 diff、原始工具 IO 和 Source 施工结果由 HDF/MF 绑定。

所有 metadata、credential、loopback model、workspace 和 Goal port 均明确 SYNTHETIC / NOT_FORMAL。原 4 个 skip 与本任务外 epoch/ledger/W16/history Source 不在修改范围。本包封存后停止施工，Root 实际执行及另一独立审查者复核之后才能决定接受。

