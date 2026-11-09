# R03 执行前路径检查

目标 source `27ced22e73da7631d65bdd6e1844de24dd198065`。现有大量未跟踪证据与并行 UI 工作保留。仅本目录可写；选中 Go 测试使用自建临时目录。

| 测试 | 已追踪 helper / 产品调用 | 执行决定 |
| --- | --- | --- |
| TestW11HardGates | orchestrationSetup → contextFixture → setup：临时 SQLite/迁移/New；task/claim → RegisterOrchestrationFixture → claimTaskMode 的 fixture 分支，仅 reserveFixtureDispatch，未 prepareRuntimeDispatch；report → 本地 heartbeat/upload/seal/ObserveRuntime；acceptance → prepareTaskAcceptance 中 orchestration.json-equals 纯 JSON 比较；w11Client → httptest loopback、Fixture=true | 全部 3 分支可执行 |
| TestW11ManualDecisionHardGate | contextFixture/w11Body/公开 artifact；新记录通过 handler，legacy 只向临时 SQLite 写合成 immutable DecisionReceipt；change proposal 的硬门检查，无外部 IO | 全部 4 分支可执行 |
| TestW11HostAndFallback | contextFixture；w11Client 固定 httptest URL，Fixture=true，无 token/env provider；positive/timeout/model mismatch/低置信度/contradictory 本地固定响应 | 全部 5 分支可执行 |
| TestW11PromptBoundaries | contextFixture；文本/JSON/二进制/超限为公开合成 body；protected-* 只创建分类元数据，storage_key 未绑定、byte_size=0，无 private payload；rubric-race 只更新临时库；Fixture=true loopback server | 全部 8 分支可执行 |
| TestIndependentW21AcceptedA08PolicyReferences | 本次新增纯函数 overlay；只读已经接受的公开 qualification/acceptance/summary/artifact 响应；SafeSummary.Validate、qualificationReceiptBinding、hash/scope/计数推导；不调用 import/prepare/service/query/provider | 可执行 |

`setup` 的 Service.Protected 保持 nil；没有注册 coordinator/runner。fixture.request 用 httptest.NewRecorder 直接调 handler。fixtureHTTPServer 仅在当前 Go 测试进程内建 loopback listener；readiness 只读探针，未执行 native child。decision.Client.Call 在 Fixture=true 时限制 loopback HTTP，显式设置 JevCalled=false，不读环境凭证。所有所选测试及其 helper 没有 Getenv 驱动的真实 provider 分支。

未执行：ImportFrozenQualifications、prepareQualification 及其 HTTP 真实准备路径，因为会 QueryFrozenService；任何 protected/native/30-call producer/旧对抗与资格 helper；SOURCE3/CLI/activation/S2。A08 仅重验保存的公开证据在当前纯 binding 上是否成立，不能形成当前安装服务 freshness 证明。

依据文件：internal/domain/{decision_test.go,decision_regression_test.go,decision_boundaries_test.go,domain_test.go,context_test.go,orchestration_test.go,runtime_test.go,decision.go,orchestration.go,runtime_dispatch.go,acceptance.go,qualification.go,qualification_import.go,qualification_live.go,store.go}、adapters/decision/jev.go、adapters/protectedstore/frozen_summary.go。init/TestMain 搜索未发现选中路径的环境/native 自动启动入口；decision init 只登记 operation。
