# W17-02 development execution

状态：`EXECUTED / PENDING_INDEPENDENT_REVIEW`。本文件不签发 Acceptance，不接受本卡、父任务或正式 C22/A11/C07。

Owner 为 `codex-w1702-impl`，模型按项目安全工作策略使用 `gpt-6-astra` 高推理。候选分支 `work/codex-w1702`，开发基线 `7431aa82`。在已登记的测试与本卡回执范围内工作，未改共享合同、命令登记、路由、schema、step_state 或其他任务文件。

## 交付及结论

- 新增 `tests/security/w1702.py`，只接受 `TASK=W17 / CHECK=W17-02` 且无 CASE、无额外参数，固定 FIXTURE。保持旧 C22/W17-G03 handler 与历史回执不变。主线精确 selector 由共享命令登记 owner 整合。
- 复用当前生产 `domain.New` 与 Handler 执行现有 C22 闭环。基线已有当前 client session schema 初始化；原始基线运行 exit 0，不重复修复旧版本的问题。
- 在 `internal/domain/protected_artifacts_test.go` 补充角色、授权转换与提供方失效检查。受限 grant 本身不能让 EXECUTOR/PLANNER 读元数据、正文、列表或登记受限对象；注册 IO 中撤销凭据后对象不落库；读取 IO 中撤销角色、提供方不可用或返回私有错误均不返回私有正文。
- 实测未发现新的生产权限缺陷，因此不修改已经正确工作的生产授权逻辑。明确有权 Owner 的既有核查权限按冻结合同保留。
- 增量与已有读取重验证共 17 断言，加既有 C22 137 断言，总计 154 个唯一、非零断言。已检查当前源码 hash 在执行前后相同。

## 当前权威开发证据

最终开发运行：`20261005T193538Z-b41b6c472b/report.json`。两个真实 Go 命令 exit 均为 0：

1. `go test ./internal/domain -run ^TestW17C22ProtectedIsolation$ -count=1 -timeout=120s -json`
2. `go test ./internal/domain -run ^(TestW1702AuthorityTransitions|TestProtectedReadRevalidation)$ -count=1 -timeout=120s -json`

实际工具为锁定的 Go 1.27.1 与 Python 3.14.3；绝对路径、工具 SHA-256、项目输入源码 SHA-256、base commit、cwd、时间戳、实际命令与退出码在该运行的 `source-manifest.json` 和 `report.json` 中。冻结任务及引用文档输入 hash 单独保存在 `frozen-inputs.json`。`evidence-index.json` 覆盖原始产物及 report 的 hash。

最终运行共有 304 次真实 loopback HTTP 交互，其中候选权限请求 229 次，授权正文正向对照 29 次。3 个独立 control 进程覆盖重启及无提供方情形，4 个 AppContainer 子进程覆盖真实文件/目录读写拒绝。秘密 marker 与受限元数据扫描均无泄漏。HTTP 由宿主以受限凭据发出，AppContainer 文件拒绝是另一层证据，不能合并为“AppContainer 发起 HTTP”。

`handler-tests.stderr.log` 保存 6 个校验器测试的原始结果，exit 0。它们检查空证据、重复 assertion、失败或跳过或缺失测试、expected/actual 不一致、错误 selector 与 LIVE 拒绝。这些合成校验器输入不计入 154 个产品断言。

`baseline/` 保留实施前现有 C22 原始执行输出、原始 HTTP/OS/进程证据与 exit-code.txt。该辅助历史运行未单独捕获完整源码 manifest；不能替代上述最终运行。首轮新增测试通过的 `20261005T193413Z-4c0a1dcd59` 回执也原样保留；后续只收紧资源措辞及增加 handler 校验器测试，最终证据以上述当前运行为准。

## 出口与正式资源界限

API/content、ID 直读、列表、搜索、ContextBundle、事件、SQLite/cache、实际服务日志、派生降级、重启与撤销均有本地合成输入证据。实际备份引擎遇到受限 Artifact 拒绝创建备份，这是拒绝能力，不是受限备份可用能力。猜测的 preview/export/log/backup HTTP 路由返回 404 仅证明该路由未提供，不能冒充已实现的数据出口。

CanaryStore 明确 `IndependentIdentity=false` 且同 OS 用户可读。只有受限 AppContainer 候选得到本轮实际 OS 文件拒绝证明；同用户不同 Agent 不构成独立 Verifier。冻结正文导出方法 `FrozenProvider.Read` 的 fail-closed 是有意的控制面限制，本卡只验证其本地拒绝，不据此否认既有受保护 summary → ImportFrozenQualifications → prepare/accept/record qualification 生产链。

| 资源或正式用例 | 本卡观测 | 未完成事项 |
| --- | --- | --- |
| 本地开发 | AVAILABLE，154 断言 PASS | 等待独立复核当前源码与回执 |
| C22 正式独立留出 | NOT_OBSERVED，本卡仅 FIXTURE | 独立身份持有的正式标签/逐例详情与正式受保护链的当前运行未探测；不能声称资源缺失、正式可用或已完成 |
| A11 LIVE_WINDOWS | PARENT_LIVE_NOT_RUN | 本卡只覆盖应用级凭据/grant 撤销；实际设备配对、UI 密钥掩码与完整 Live 用例未执行 |
| C07 FIXTURE | 本地资源可用，PARENT_CASE_NOT_RUN | C22 自评分/判据篡改拒绝已覆盖；最高模型分覆盖失败硬证据的完整 C07 及 H02 反例不在本卡增量结果内 |

没有扩展正式 provider 正文导出、没有读取正式留出、没有授予 BOUNDED_AUTO。资格保持 ADVISORY 的断言只属于本轮合成夹具。正式服务资源状态不能从本轮未探测推导为不存在。
