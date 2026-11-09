# C22 独立 fixture 安全审查

**PASS_C22_FIXTURE_READY_FOR_FORMAL**。固定源码 `6d070c8aeb9aa11c4fc48ced8048aa99ba45c84a`，证据工作树 `3057b9cf21cd2f4756a2d18799f6973d7ff4e309`。未发现阻挡该 fixture 范围的 P1；本结论供主 Agent 进入正式验收，不签发全局 C22/W17 正式通过。

独立实际重跑通过 137 项断言，产生 304 次 HTTP、4 个不同 SID 的 AppContainer、3 个控制面进程。宿主先确认完整合成私密文件存在且可读；候选文件读取、写入及枚举实际返回 OS code 5 和零字节/条目。公开 API、缓存、事件、日志与报告未发现私密标记或私密元数据泄漏；受限 Owner/Verifier 的完整证据读取成功并带 no-store。相同临时数据库与 store 经新进程重启后仍保持边界，撤销和 missing-provider 均失败关闭。

新增实际 HTTP 检查覆盖 provider IO 后 grant、role、principal、credential 和 provider 变化，15 项断言通过；每种场景均先成功读取，再验证当前拒绝及无私密缓存。另一个 AppContainer 网络探针通过 4 项断言：宿主可达的临时回环监听器没有收到候选请求，候选连接返回 10060，宿主环境变量未继承。通过的行为断言合计 156 项，另有 4 个独立负面 validator 检查全部拒绝不完整/失败输入。

全部 5 次 Go 命令的退出码为 **0、1、1、1、0**，完整 stdout/stderr 已保留。第一次附加命令的 HTTP 子测试通过，但唯一合成文件句柄的 ReadFile 探针被 Windows STATUS_INVALID_HANDLE 终止；改用 GetHandleInformation 的第二次句柄探针也被同一保护终止，之后未重试句柄、未关闭保护。两次均进程已停止、stdout 为零且无私密正文；不将其报告为正常通过的句柄读取测试。首个网络探针因错误码预期过严（预期 10013、实际 10060）失败；最终定向检查以连接失败、非零错误和宿主无候选请求为判据通过。上述失败、原始源码及修订源码均可追溯。

204 个源码文件已与固定 Git blob 比较，33 个作者索引文件全部核验；执行后源码和作者报告/索引保持不变。五个先前清理遭 policy 拒绝的作者目录原样保留，没有删除、重试或绕过。

本证据仅涵盖公开合成题目、临时 DB/store 和受限候选。宿主 API 请求与子进程 OS 证据分开记录；没有访问真实 79136 服务、生产数据库、真实留出正文或 provider。CanaryStore 对一般同用户进程不构成独立隔离，LIVE 与 BOUNDED_AUTO 仍未开放。完整命令、限界和 C22-01 至 C22-04 映射见 `review.json`，逐文件哈希见 `index.json`。
