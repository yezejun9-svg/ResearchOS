# W14-G01 跨模块夹具

在仓库根目录运行：

```powershell
$env:RESEARCHOS_TASK_ID = 'W14'
$env:PYTHONUTF8 = '1'
python tests/e2e_cycle/run_fixture.py
```

驱动使用 `execution/toolchains/locked.json` 中的 Go，生成一个临时 Go overlay，把 `_fixture/cycle_test.go` 编译进 `internal/domain` 的测试包；不写入该目录、不改产品源、不增加产品 fixture endpoint。`_fixture` 不被普通 `go test ./...` 扫描。三个测试在三个独立进程顺序运行，共用本次新建的临时 SQLite，结束后删除数据库、二进制与临时 overlay。

产品业务请求都经真实 loopback HTTP 和 `Service.Handler`。Go 测试中的 Recorder 只是既有 helper 到真实 HTTP client 的桥，所有请求与响应都由 loopback server 处理；出现已提交请求失败时不自动重发。可信来源注入、运行器观察、实验调度绑定和研究候选评审调用现有产品 Service 方法，未写 SQL 伪造业务状态或验收回执。

流程覆盖 Requirement/Goal/Context → 三来源 Evidence → 预注册 Experiment/Run/Artifact → 独立服务 Acceptance → 负 Decision → 独立 ChangeProposal/apply → COMPLETE → Release/Notification → 新进程恢复 Goal、权威状态、侧栏投影和下一步。实验固定为零收益，不要求采用候选。另验证旧输入、错误预注册哈希、未完成实验、旧 revision、篡改结果、虚报收益、反证压过高分、无依据采用和缺来源的真实拒绝。

`evaluation/project_cycle/fixture_contract.json` 列出必须实际执行的 32 条断言。回执保存在 `execution/receipts/W14/fixture/<run_id>/`，包括逐请求 JSONL（凭据值脱敏、原请求/响应字节哈希）、逐断言预期/实际、源码/命令/overlay/二进制哈希、各阶段原始 stdout/stderr 和跨进程 checkpoint。输出 `PASS` 仅代表这些夹具断言通过；施工接受由独立 Verifier 决定。

边界：三源由 package-local `sourceFixtureAdapter` 提供 synthetic 数据，Jev 使用本机固定 HTTP 回复，执行结束由 `ObserveRuntime` 显式注入；不是实际三来源研究或操作系统执行实验。当前源采集 Service 对这种注入仍写 `LIVE` 对象元数据，所以每条外部回执明确标记 `FIXTURE_SYNTHETIC`，不得把该字段当真实资格。新进程恢复证明持久化 API 状态连续，未证明自主 Agent 接续。W14-G02/A13、实体设备、UI、正式受保护数据集均不在此命令范围。
