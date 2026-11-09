# 重连控制边界只读复核

结论：READONLY_RECONNECT_CHECKS_CLEAR。观测时间为 2026-11-06 09:39:46 UTC。所选保存控制范围内未发现 pending 或 uncertain mutation，build14 的工作树、D 登记目录、C scope 和 C run 均不存在。Root 可在自己的 Git、资源及其他既有前置检查通过后注册新 build14；此报告不是构建成功或产品验收凭证。

本次独立重读确认 CP693、保存 HEAD `360c3eefd06ba82255352357c05ece00dae00d3a`、70 项源文件散列与 union `954c293b52e5b83dcb8a779410e89fc3c74a4bad3550d3620ba0938cc67e15c2`、18 项原保护项、leases revision 33、IMPLEMENTING 数量 0、历史记录 2648。此审查没有调用 Git；实际 HEAD/index 由 Root 另行核对。

| 保存范围 | 原 ROOT PID | 原 creation FILETIME | 当前观察 |
|---|---:|---|---|
| native-synthetic-flow-01 | 74020 | 134383424926828964 | OpenProcess 错误 87，PID 不存在 |
| workbench-refinement-tests-03 | 53676 | 134383498475709078 | OpenProcess 错误 87，PID 不存在 |
| workbench-refinement-vite-01 | 76352 | 134383504784467138 | OpenProcess 错误 87，PID 不存在 |
| visual12-purechecks-01 | 2288 | 134383517320787101 | OpenProcess 错误 87，PID 不存在 |
| 公共 owned-core receipt | 55436 | 134383424970975846 | OpenProcess 错误 87，PID 不存在 |

进程查询程序仅申请 `PROCESS_QUERY_LIMITED_INFORMATION (0x1000)`，为打开成功的句柄声明 `GetProcessTimes`、`GetExitCodeProcess` 和 `CloseHandle`。本次五次打开都返回 Windows 错误 87，因而没有取得句柄，也没有对任何进程执行后续查询或改变。不存在 PID 复用误认；程序若取得进程，先比较完整 creation FILETIME，复用 PID 会明确分类为非原进程。

Core 范围严格限于 C 的 `product-v1-native-synthetic-acceptance-中文-run-01/receipts/owned-core.json`。其中 `created_ns=1793868897097584600` 按 Unix 纳秒精确整数换算为 FILETIME；创建时间的 Go `Nanoseconds()` 用法亦见当前仓库 `ops/supervisor/control_authority_windows.go`。本次 PID 不存在结论不依赖对活跃 Core 身份的推断。没有读取 Core 私有 DB、进程映像、命令行、环境、令牌或凭据。

四份 RESULT 及其列出的 stdout/stderr 原始文件均通过散列复核。历史 RESULT 均有 `job_active_zero=true`、`stop_proved=true`、`root_signaled=true`、空 errors、`close_order=[job,thread,process]`；synthetic 原状态为 TIMED_OUT_STOPPED/exit125，其余三项为 COMPLETED_OWNED_JOB_STOPPED/exit0。保留原失败，不改写为产品成功。原 Job 累计进程数为 58、6、7、6，不代表当前进程数。

历史句柄已关闭，本次没有恢复、打开或复用这些历史句柄，没有声称当前持有 Job 或重新查询历史 Job 成员。没有全机枚举、终止进程、OS 修改、D 写入、产品/测试/构建/GUI 执行、模型调用或重放旧 scope。本次只创建本 C 报告目录中的审计脚本及报告文件。

剩余范围：资源实时可用性和实际 Git/index 由 Root 自行核对；fresh build14、后续真实窗口验收及任何另行授权的新模型任务尚不是本报告执行或证明的事项。没有本审计操作遭拒或结果不确定的工具调用；早期若干只读代码定位命令遇到不存在的候选路径，不产生变更。
