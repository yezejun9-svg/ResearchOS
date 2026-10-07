# C22 独立权限夹具施工边界

状态：`DESIGN_ONLY_NOT_EXECUTED`。源码基线 `5f53994`。本文件不接受 C22，也不改变现有正式留出服务、资格或权限。

冻结 C22 允许 FIXTURE，但要求真实独立受保护环境、全部读取面、逐次必要输入、授权追溯和重启后继续拒绝。现有 `internal/domain/protected_artifacts_test.go` 只证明同用户 CanaryStore 的 API 授权；不能单独满足操作系统隔离。现有正式服务证据也不覆盖 C22 指定标记和完整读取面。

## 可复用的最小方案

采用新建临时 fixture authority DB 和 `CanaryStore`，仅存公开合成标记 `fixture_holdout_private_marker`。候选原生程序通过现有 `ops/experiment_sandbox.Run` 进入每次新建、零 capability 的 AppContainer。可信测试宿主持有 private store 和受限 Verifier/Owner 授权；候选没有宿主 token、DB 或 store 目录授权。AppContainer SID 是实际权限边界；不同 Agent 名称不是边界。

不修改 CanaryStore 的 LIVE 拒绝策略。它对一般宿主用户不构成正式留出隔离，即使此 fixture 的特定受限候选确实被操作系统拒绝，也不能开放普通 LIVE 执行器或 BOUNDED_AUTO。

测试使用临时目录中新建的 fixture 数据。不得调用、重启、读取或修改已冻结的 protected service 79136、主产品数据库、真实留出正文和任何 provider；不得重试被 policy 拒绝的操作。

## 必需证据

1. 实际候选 AppContainer 尝试读取、枚举和修改 fixture 的完整输入、标签、逐例详情、日志和基线文件，保存 SID、PID、系统错误码和返回字节数。先由可信宿主确认这些文件存在且标记可读，避免将不存在误报为权限拒绝。
2. 通过实际 HTTP 服务对普通 Executor/Planner 检查已知 ID、内容下载、列表、搜索、ContextBundle、事件、预览、导出和备份。复用现有拒绝/分类传播路径；不得仅匹配错误字符串。检查实际响应、DB/cache/日志/public report 不泄漏标记或可恢复原文的细节。fixture 宿主的候选凭据请求与 AppContainer 文件拒绝是两个明确标注的证据面，不宣称已在零网络 child 内发 HTTP。
3. 候选每次仅获一个公开合成题目输入，不获得标签、全集或逐例评分。可信宿主在 private store 保存原始结果，只产生现有 `SafeSummary` 的固定枚举/计数。优先复用已有 frozen engine 的逐次输入、一次执行和无中间进度测试；若不能无新生产接口组合，说明该子断言仍缺失。
4. 受限内容不能通过 PROJECT 派生、改权重/标签/基线、伪造汇总或资格来降级。显式受限 Verifier 与 Owner 的完整证据读取成功且 no-store；普通同名 role 不够。候选失败时不能靠向候选目录复制全集补救。
5. 用新的控制面进程重开同一临时 DB/store，重新发出实际 API 请求和新的 AppContainer 文件探针，确认业务 ID、分类和权限保留。关闭/重开 Go 对象只算较窄证据，不代替新进程。
6. 隔离缺失/凭据撤销/提供方不可用时失败关闭，资格保持 BLOCKED/ADVISORY。原始输出与 assertion IDs 分别对应 C22-01 至 C22-04，未覆盖面不得 PASS。

## 范围与施工次序

预期只增加一个边界测试文件和最小 native fixture 入口，复用现有受保护存储、沙箱与协议。不得为测试新增公开 holdout 读取 API、临时服务安装或系统用户。只有出现真实产品缺陷才提出最小修复。

先独立审查上述权限模型是否足以覆盖冻结 C22 的 FIXTURE 范围，再分配施工 lease。当前两个施工槽用于 runtime S1 和 W07 修复，本文件不启动第三个施工任务。完成后由另一 Verifier 检查原始 OS/HTTP/重启证据，原有正式服务证据只作历史旁证。
