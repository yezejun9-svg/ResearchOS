C4 + O3 完整 Source 组合独立审查

结论：REQUEST_CHANGES，剩余 1 个 P1 问题 C4-R01。六个 Source/Python 引用均为本次核验的完整非 NULL pin；本结论没有发放 READY 或执行权限。

C4-R01：当 native 结果显示 active_processes_last_observed=1、job_idle_confirmed=false、handles_closed=false 时，inner finally 仍调用 source_guard.close()，outer finally 再次调用 close()。没有 native 结果的分支也如此。两个纯 AST 反例均确认锁已释放。canonical lease 保留不能代替 Source 文件句柄的保留；可能仍活跃的子进程随后通过路径加载代码时，已失去 deny-write/deny-delete 保护。必须把 guard 和所属 owner 状态保留到 child tree/Job 结束得到确认，再通过明确恢复流程释放，不能由外层 finally 无条件释放。

既有修复有效：复用了上一轮独立内存事务 fixture，真正模拟 close 的第二次文件写入失败，使 CP 已清 active、OW 仍 ACTIVE；使用当前 refs 再准入被 C4 拒绝，canonical bytes 不再被第二次调用覆盖。两种一致的 CLOSED 状态允许准入，UUID 不一致、缺失和畸形记录拒绝。watchdog Thread.start 失败后不再 join 未启动线程，duplicate 可以关闭并保留失败原因；stop_and_close 异常被 controller 记录，不再阻断后续 cleanup 记录路径。

C4 wrapper 的 17/17 新独立控制通过：六个完整引用及五个附加引用合计 11 个锁定对象在 inner 前取得，拒绝错误 reviewer、旧 schema、REQUEST_CHANGES、formal acceptance、未准备 phase、错 runner/observer/Python/controller/hooks/worker、取得 guard 失败和 review 在取得 guard 前变化。回归控制 15 项中 13 符合、2 个反例归同一个 P1 finding，共 32 项新独立控制、30 符合。

O3 与 O2 的完整函数字节一致，仅 RUNNER_REF 的 path/hash 改为 v9；独立正逆字节恢复精确，其他 AST 一致。O2 既有 39 项及 v9 已封存 8 项控制复用，未重跑。C4 controller/watchdog diff 独立重新生成完全相同，其余 transaction/hooks/phase_worker/job_probe_helper 原始字节不变。

SourceReadGuard v2 的非作者 PASS_SOURCE_ONLY 已按其 review、manifest、controls 和 Source pin 核验并作为附加证据：31 个新内存控制、28 个既有控制复用。本轮没有把作者控制当成独立结论；guard 自身的 Source PASS 不证明 C4 的持有期正确，也不证明真实 Windows API 行为。

本轮自身新增工具失败 694（误含空格的只读规则路径，shell=1，Python/native NULL）和 695（元数据 intake 用错 C3 HDF 字段，shell=1、Python=1、产品 native NULL），完整调用/原始返回及失败脚本均封存。693 属其他 agent 的协作路由失败，无本轮原始证据，不伪造或重复计数。此前 690/691 已封存在 v9 审查中，本轮不再计数。

所有动态控制仅运行选定 AST 与独立内存路径、句柄、线程、时钟及 transaction 替身。没有候选模块导入、真实 WinAPI/线程/native/SQL/provider 执行；Main/canonical 未写。实际 Windows 私有目标 probe、实际 Job 生命周期、可信 Host、资格和正式 trial 保持 OPEN。

封存补记：另有第三次自身 metadata 工具失败 829703：Guard 独审 MF 实际为 files，却索引 members，shell=1、Python=1、产品 native NULL。原始脚本、完整调用与 IO 已单独封存；失败总数为 3。693 的他方原始 origin 后由其 MF 提供并核验，只附引用不重复计数。
