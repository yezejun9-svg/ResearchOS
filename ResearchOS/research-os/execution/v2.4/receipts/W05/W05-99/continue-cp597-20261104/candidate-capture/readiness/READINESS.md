# CP598 coding delivery 下一切片只读准备

基线是 Main `001f7e5a4d95152c8f83874a60d9fbd3bbace538`、CP598。当前两个建设 owner 是 core 与 clients；本报告未占建设 owner，只读公开源码并写这一份新 C 证据。未写 D、打开业务 DB、运行 Go/进程/native/模型/probe，未触旧 REAL_ISSUE_SCOPE 或正式 holdout。formal 仍 0/42、22 个 parent 不宣称完成；历史 Cstate、attempt04 vet UNKNOWN 和所有失败记录均未改。

Root 已选定下一段：**最终沙箱私有副本的 candidate source-only 同字节见证**。六个建议源码/测试路径和时序详见 [NEXT_SLICE.json](NEXT_SLICE.json)。这是待 Root 在两个 owner 归稳后登记的可施工范围，不是现已实现或授权的第三建设任务。

## 可复用与还缺什么

| 层 | 真实当前接点 | 可复用能力与缺口 |
|---|---|---|
| Catalog / binding | `store.go:19/54`、`coding_delivery_binding_store.go:142/225/277/311` | 必须传 owning `s.Contracts`，沿正常 persistence 版本分派。已有闭 DTO/hash、真实 Goal/Task/NPR、mandatory command_key、双合同及全局 qualified 唯一性；零生产 caller，完整性不能当认证。独立 SQL 源不在迁移/backup adoption 中。 |
| 普通创建 | `client_protocol_goal.go:18/34/65/75` | `finiteGoalSpec.Contract` 同时给 Goal 和 Task；普通 `session.send` 继续现有单响应合同。未来 typed branch 必须显式双合同并在 AdmitTurn 前原子绑定，不能由 prompt、check 名、Artifact 名或 worker 参数识别。 |
| 首次准入审计 | `client_protocol_configuration.go:86 pendingClientTask` | `:146` 强制同合同；`:195–226` 重建普通 goal 合同与身份。未来完整 binding 的私有分支要保留原始命令、事件、版本和输入核查，普通分支维持现状。 |
| 历史恢复审计 | 同文件 `:826 originalSessionTasks` | `:974–1002` 再按普通 goal identity 检查 NPR。创建与 pending 两处改完仍不够；以后必须一并处理该恢复路径。 |
| 原进度 | `operations.go:189/213–237` | origin/candidate 属于真实 NPR；Task 仅有 `no_progress_record_id`。沿旧 `Hash([]any{origin,candidate,Hash(input_refs)})`，不能加 Task 非 schema 字段或重置计数。 |
| 权限 | `client_runtime_coding_windows.go:172/235/266/280/412` | 原确认/安装/authorization 绑定真实 Owner、currentAuthorityRoot、Host、parent、workspace、writer 和冻结配置。它批准配置安装，不等于具体业务交付批准。typed 分支遇缺 authorization 必须拒绝；普通 nil 兼容语义不变。 |
| Host 原父进程 | `host/desktop_management_windows.go:49/79/198/226/228` | inherited pipe + OS ObserveProcess/原父 identity + boundPrincipal/配置 Host；不能从 caller root、client ID、locator 字符串取权限。 |
| 最终执行副本 | `host/runtime_check_windows.go:443/539/551/560` | 当前复读 workspace 后用 sandbox.Run，只有 manifest/真实日志/receipt，没有最终私有 source bytes。沙箱第二次 copy 之后的 BeforeResume 尚未被该 Host 检查使用。 |
| Canonical fact / artifact | `runtime_tools_windows.go:197–218` → `runtime_broker_windows.go:349` → `runtime_session_events_windows.go:123/183` | Host evidence 从模型 reply 删除，绑定实际 run/epoch/request/effect，再封 REPORT/LOG 和 ArtifactUse。此路可带 candidate 字节；严禁带 verifier test/holdout 源码字节。 |
| Task checker / REPORT | `acceptance.go:244/280/378/383` | 暂无 coding.pure-scalar-delivery-v1 handler；现服务 REPORT 没 candidate bundle。未来 snapshot 从 canonical facts 取同字节见证，独立重验，再由服务写 REPORT/evidence_refs。请求自带 ref 不是来源。 |
| Goal 聚合 | `acceptance.go:421 acceptedTaskBinding`、`acceptance_goal.go:45/79/111/156` | 已有 current PASS receipt/Run/output/ArtifactUse 核查；未来仅沿 accepted Task 的服务验证 REPORT 取 checked candidate bundle，再核完整 binding/双合同/当前 native admission。普通非 planning LIVE503 维持。 |

上表路径均相对 repo；详细接口与行锚在 [source-map.json](source-map.json)，38 份当前源 pins 在 [source-pins.json](source-pins.json)。这四份 binding 源 pins 与最终旧 author freeze 相同，未借旧手工正例或 attempt04 UNKNOWN 重新签署接受。

## 原 origin、原批准、UNKNOWN 的真实边界

`RuntimeCodingIntent`、confirmation 和 `FreezeRuntimeCoding` 当前没有可信原业务 problem anchor、原 requirement/business-input 内容 hash、具体 approved plan 或稳定 suite 语义版本。普通 goal identity 包含 project/principal/objective/VersionRefs，普通 session.send 还使用随机 ProblemID；它们不能升级为 DB-wide business anchor。

未来 Host origin reader 必须读取原权威来源的实际内容并确认原业务 lineage。稳定 anchor 仅含原 problem anchor、原需求/业务输入内容 hash 和稳定 suite ref/hash/version；project、Owner/root、approval、存储 ref 向量 ID、新对象/命令和时间均不参与。完整 ref 向量 hash 另作 provenance。现有结构 hash 函数不能自称认证该来源。

`host:coding-installation` 缺行只表示该配置状态查询没找到安装记录；不证明外部 native approval 未用。binding 缺行或 Tx 回滚也不退款批准。`durability.go:123/226` 的原 resource_effects、`runtime_tools_windows.go:113` 的 UNKNOWN、`runtime_dispatch.go:111/184` 的真实 dispatch/stream/cleanup 与原外部批准 journal 都须保留。当前尚无 delivery-specific 原批准 consumer；本片不会伪造一个。NPR 非零计数、defer、retained result 继续原 `taskFailed` / `retainAcceptedResult` 路径。

## SDK 单输出与 candidate-only seal

`worker.mjs:951–960` 只写 result.json；`client_runtime_setup_windows.go:228` 只声明它，`runtime_coordinator_windows.go:738/758` 将原输出交 reportRun。`runtime_model_stream.go:438` 与 `runtime_model_verification.go:410` 都要求 len1。candidate 不加入 worker 输出、Run result IDs 或 reportRun 向量。

下一片只从最终 private `input/source` 捕获 `pkg/solution.go`，字节上限沿现 `deliverygate.MaxSourceBytes=16384`。三文件 roster 为 go.mod / pkg/solution.go / pkg/solution_test.go；固定文件只记录大小和 digest，**不把 go.mod、Verifier test 或 holdout 字节放 bundle、host_evidence 或模型 reply**。生产固定 suite provisioning、保密边界和原批准来源是后续实现；本片只用自建临时 fake fixture，不读取正式 holdout。

BeforeResume 在最终 copy 和 suspended process 建立后、ResumeThread 前执行（sandbox_windows.go:178/320/331）。捕获只读一次 candidate，Validate 与之后序列化均消费拥有的同一份字节，不重读可变路径。context/manifest/固定文件/toolchain/identity 不符则拒绝。发生 Start/callback 错误时进程可能已经创建，必须维持原 UNKNOWN，不能改成 NOT_APPLIED 或重试。完整 Wait receipt 的 native identity 须与 hook 一致，cleanup/streams/stopped 等未确认不发布可用见证。exit0 仍只是执行结果，capture/AST 见证不等于业务 PASS。

最小 opt-in 是 `RuntimeToolRequest` 中未导出的 opaque capture 指针；没有 wire/JSON 字段、没有 exported setter，getter 防御复制。当前不注册 producer；未来只有经过真实 binding/current authority/plan 验证的 runtimeToolGate 可以设置。worker 仍只能交原 check_id。nil 走原 sandbox.Run；未知 nonnil 失败且不退回普通路径。context 是来源快照，不是认证凭据。

## 后续闭环顺序与真正阻塞

本片可在 Root 登记独立 worktree 后离线实现和临时目录验证，不需用户重复许可或模型资源。建议先把 source-only capture 和普通 nil 兼容冻结，再接真实 origin/approval resolver、双合同 factory 及两个创建/恢复审计分支，随后 Task checker/服务 REPORT，最后 accepted Task 的 Goal aggregation。不可把这些尚未实现的代码包装为资源或 permission 阻塞。

真实有限 CLI 业务接受仍需要当前可用且合格的 native/模型资源、原审批 scope 和业务原 origin。CP598 metadata 观察不是 inference 资格；已消费/UNKNOWN scope 不得重放。如果此前用户已经给出原业务来源，应由实现读取既有来源，不能重复索取批准；只有来源确实未提供且不能从可信连接/当前记录解析时，才需要用户指定实际原业务对象/验收语义。当前两个建设 owner 只影响 Root 排期。

本报告与下一片临时夹具均不能证明真实 suspended-copy 时序、AppContainer ACL、进程清理、LIVE repair correctness 或正式接受。没有任何 Go/native/model/DB test 在本次只读任务中运行。查询过程的命名/通配/展示截断诊断独立保存在 [diagnostics.json](diagnostics.json)，不修改既有控制记录。


