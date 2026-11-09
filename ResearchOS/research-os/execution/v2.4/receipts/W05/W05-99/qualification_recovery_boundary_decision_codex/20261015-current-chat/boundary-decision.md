# CP515：恢复边界决策

结论：**当前没有已实现、已接受且获准执行的替代恢复边界。建议仅为未来单独登记的 `POST_RESTART_CURRENT_QUIESCENCE_V1`：在实际启动围栏生效、完成独立审查后，由用户明确执行一次完整 Windows Restart，再证明同一产品根的当前执行静默。** 这是规范允许的恢复方向，不是现有 STOP/C proof 的另一种填写方式。本轮不要求用户现在重启，不执行任何 OS、进程、DB 或产品操作。所有新类均为 `NOT_IMPLEMENTED_NOT_ACCEPTED`，`actual_authority=false`，formal 增量 0，22 个父任务仍全开。

不可补齐的历史事实保持原样：原 verifier successful Wait 不可用；原 raw error、ACK、Run UNKNOWN、cost、失败计数和已发生副作用均不因未来重启而改变。此前初始化审计只按 CP515 `audit-adopted-limits.json` 的非操作性负面结论采用，不能扩大成完整 NO_EFFECT。

## 三个选项

| 选项 | 能证明的边界 | 不足与结论 |
| --- | --- | --- |
| 另建 CORE-ONLY quiesce | 未来用 exact owned Core 的原 retained handle、一次 durable intent、一次 native terminate、同句柄 numeric wait，证明该 Core 本次关闭；结果最多 `CORE_CLOSED_MAINTENANCE_UNPROVEN` | 当前进程 census 是瞬时列表；没有覆盖历史 verifier 任意后代的出生记录/隔离域，也没有完整 no-new-launch fence。路径/哈希和 ParentProcessId 不足以找全全部后代，访问拒绝不是不存在。**不足以独立解除 maintenance 阻塞**；不得借此删除现有 STOP 的 verifier-Wait 前置条件或终止未知进程。 |
| 未来完整 OS Restart + 持续启动围栏 | 在下列条件全部成立时，消除所有先前 boot 的本机执行，并在同一根下建立新的、有限时间的 current-quiescence 边界 | **有条件推荐**。需要新的 proof 类、最小 Source 卡、真实 Windows 验证、独立接受和后续用户重启决定。只证明当前执行边界；不证明历史 Wait、事务回滚或外部任务结束。 |
| 隔离旧根，启用空的新普通产品根 | 可以承载另一个明确授权的新项目；不自动证明旧项目恢复 | 对原目标不是合规替代：空根丢失 Task/Run/预算/失败/恢复关联；完整恢复旧根则 UNKNOWN 仍存在。目录隔离也不是同一 SID 内的进程隔离。**不能用新根充抵旧根 C11/A12/A14 或 formal 结果**。若确需放弃旧目标，这是明确的目标/资源决策，旧失败和门禁仍保留。 |

Microsoft 将 Toolhelp 描述为某一时点的只读快照，并明确进程状态随后可能改变；ParentProcessId 会受父进程退出和 PID 重用影响。由此推断 census 不能补出历史后代全集或阻止随后启动。[Toolhelp 快照](https://learn.microsoft.com/en-us/windows/win32/toolhelp/snapshots-of-the-system)、[Win32_Process](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-process)、[OpenProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess)。

## 规范依据与当前实现边界

- `spec/v2.0/03_DATA_CONTRACTS.md:82–101,140–159`：失败历史不可擦除，丢失执行需要 RECONCILING；不明确的外部状态阻塞，不盲目重放；恢复须保留 DB/artifacts/cursor/outbox 和原凭证语义。
- `spec/v2.0/06_ACCEPTANCE_TESTS.md:521–523`（C11）：同一项目/Goal/Cycle/Task 关联及未知外部状态；`:1578–1595`（A12）：可恢复到干净工作目录，但保留备份关联、ID/revision/ledger/cursor，使用明确维护路径；`:1658–1681`（A14）：规范本就允许真实主机重启/休眠场景，恢复或可见 BLOCKED，保留业务身份、不重复副作用。
- `spec/v2.0/06_ACCEPTANCE_TESTS.md:7–44` 和 `08_AGENT_EXECUTION_GOAL.md:32,80,90`：一套权威状态、正式真实证据、失败/无进展历史延续；独立支路可继续。由这些条款推断：可以新建“当前执行恢复边界”，不能把它等同历史 Wait 或新根替考。
- 冻结 STOP-r2 `f5db4a9639f1a50380eb5929ee6295887baeb756` 的 `internal/ownedcorestop/proof_windows.go` 与 `contract.go` 仍要求原 worker/verifier handles 的 numeric Wait；`stop_windows.go:227–254` 在缺失证据时先拒绝，`:288–347` 才处理 intent/native stop/后续 lease 与 census。此设计、19 个 cuts 及并行独立审查均不变。
- 当前 `apps/control/main.go:110–131` 的 lease/startup gate/store/domain 顺序是未来入口整合定位，不代表新 gate 已存在；当前 Main `4f4023c956f84d65743f39ce77d6c8899a21ada1` 不认识新 recovery journal。C 的 CP511 采纳约束继续适用，新边界须通过单独范围追加接入 C，不得隐式降级任何已接受类。

原始逐行读取及文件 SHA256 见 `004/006/008-source-spec-refs.json` 与对应 `.stdout.raw`。本报告没有改写规范，也没有宣称这些条款已经接受本新类。

## 推荐方案的最小必需条件

**阶段一：重启前准备与见证；旧 Core 可以仍 ONLINE。** 先独立接受新类和 helper，并准备可检查的操作清单：同一 Windows 主机、SID、native DataRoot/DB file identity、原 subject/hash、schema 24、backup ID、唯一 operation ID、完整旧 UNKNOWN/成本/失败状态引用。ONLINE 阶段不能声称取得旧 Core 正占有的 product-root exclusive lease，也不能以抢占 lease 或旁路 DB 读取完成见证。若需在线一致性备份，必须使用另获授权且已验证的在线备份路径；无法形成可用备份/清单便不能 arm。这里只冻结边界前证据，不执行 C maintenance。

**持久启动围栏必须在 arm 前覆盖真正已安装/正在使用的全部相关启动入口，跨 Restart 生效并保持至维护结束。** 至少覆盖正常 Desktop/Core CLI、replay/release host、backup/maintenance 入口、OS/app 自动重启入口，并在 DB、密钥、provider 初始化前拒绝普通启动。只给新源码增加 journal 判断不够：旧包仍能忽略它。需单独验证实际包早期 gate 的部署覆盖，或受支持且可审查的外部 OS/launcher 启动阻断，证明旧 binary、旧 launcher 和自动启动不能绕过。此项当前未实现；如果无法证明覆盖，推荐方案仍然 BLOCKED，不能用“用户暂时不启动”代替。

围栏的 bootstrap/恢复观察器必须不经普通 DB/provider 初始化；其允许项只绑定已接受 C journal 的唯一 own-operation permit（subject/root/operation/hash/expiry），拒绝通用 maintenance bypass。阶段一只持有自身操作协调能力，不假称 product-root lease；阶段二才在普通入口受围栏约束时取得同一根的真实独占 lease，并按 C 约束一直持有至收尾。旧 Core 在 Restart 前自然持续运行的事实不会被预见证改写；不能在这段时间修改 C 状态或宣称静默。

**阶段二：用户后续明确完整 Restart，受信观察器在新启动后建立边界。** Windows Restart 不使用 Fast Startup；普通关机可能使用保留内核状态的混合关机，休眠也会恢复内存，因此本建议只支持明确的完整 Restart。[Restart 与 Fast Startup](https://learn.microsoft.com/en-us/troubleshoot/windows-client/setup-upgrade-and-drivers/fast-startup-causes-system-hibernation-shutdown-fail)、[系统电源状态](https://learn.microsoft.com/en-us/windows/win32/power/system-power-states)。API 返回发起成功不能证明重启完成，注册的 app 还可能自动重启，因此必须观察完成后的平台状态并保留围栏。[ExitWindowsEx](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-exitwindowsex)。

未来 proof 应保守地组合：受信同机/SID/root 连续性、持久且防篡改/防重放的前后见证、明确完整 Restart 操作证据、`GetTickCount64` 前后 uptime、新 boot 的 `LastBootUpTime` 辅证、围栏连续性、真实 exclusive lease 及新 DB/census。`GetTickCount64` 文档定义为系统启动后的毫秒数；在受支持的可信 Windows、无 VM/checkpoint 内存回滚/调试 tick 操纵的范围内，**要求 `post_uptime < pre_uptime` 是保守的新 boot 推断**，而非 Windows 提供的密码学 boot attestation。应设置受审查的见证新鲜度范围；若重启后延迟导致不满足严格下降，即使真重启也拒绝本次凭证，不能通过改系统时钟补齐。`LastBootUpTime` 或 wall clock 单独不够，nonce 只标识操作，也不是 kernel boot ID。不采用未经本文官方资料支持的 BootIdentifier API。[GetTickCount64](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-gettickcount64)、[Win32_OperatingSystem](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-operatingsystem)。上述组合的充分性尚待实现与独立接受，本报告本身不授予信任。

没有原 verifier 的 PID/creation time 不妨碍未来观察一次覆盖整台主机的 boot 边界，但不能因此补造它们；只要可能仍在执行的旧本机进程存在于该重启前，它就属于前一 boot。重启后的 census 仅验证受围栏约束的当前启动状态，不被当作历史 lineage 证据。任何旧 binary 在围栏建立前已于新 boot 启动、任何未知进程/权限错误、身份或 backup 漂移、围栏/lease 中断，均拒绝当前边界，保留旧 UNKNOWN。重启会中断本机进程，但磁盘提交和远端 provider 作业可能继续存在；后续 C 仍需其独立、精确的 Host/effect/B 证据，外部状态 UNKNOWN 仍阻塞。任何持久化状态变化都须在 C own-operation 下验证，不从 boot proof 推出 NO_EFFECT。

## 最小后续 Source 卡与验证切面

这是待授权的路径建议，不能视为本轮 Source 写权限：新增 `internal/recoveryboundary/{contract.go,boot_windows.go,boot_windows_test.go}` 与 `ops/qualification_recovery_boundary/{main_windows.go,main_nonwindows.go,main_windows_test.go}`；只在已登记 C 的 `internal/qualificationmaintenancejournal/*`、`internal/host/maintenance_startup_gate_windows.go`、`apps/control/qualification_failure_maintenance_windows.go` 等必要入口接入独立类型与 own-operation permit。具体文件集合由最小卡冻结；不展开 51 路径替换架构，不改 STOP-r2。实际安装包/旧入口围栏覆盖必须成为明确部署/验收项，不仅是 Source 单测项。

最小有意义的 tests/cuts：同 boot、重启取消、sleep/hibernate、改 wall clock 和 `post_uptime >= pre_uptime` 全部拒绝；wrong machine/SID/root、篡改/重放/超时见证拒绝；旧 launcher/自动重启/旧 binary 绕过围栏拒绝；观察器在普通 store/key/provider 初始化前工作且 permit 不可泛化；lease 丢失与 census 权限失败拒绝；旧 proof 类仍拒绝 boot-only receipt；原 UNKNOWN、raw ACK、费用、失败和身份不变，外部 UNKNOWN 继续阻塞。还需后续获准的真实 Windows 完整 Restart 及实际安装入口验证；fixture 通过不能代替此项。

所需用户资源/决定精确限定为：未来在围栏部署、可用一致性备份、Source/Windows fixture/独立接受均完成后，选择一次可中断当前 Windows 会话的完整 Restart 窗口。现在无需提问或执行。若用户不能提供这个窗口，或实际旧入口无法被持久围栏覆盖，则该恢复分支保留 BLOCKED；只继续规范允许的独立支路。新根不能作为此阻塞的无条件替代。

## 本轮证据限制

本轮进行了 8 组（上限 12）有界查询，没有当前 OS census、DB 查询、程序启动/终止、GUI/API/model/key/private-pipe 操作或 Source 编辑。shell recipe 保存 child argv、工作目录、明确环境、完整 stdout/stderr 和 native exit；网页调用无 native exit，记录为 null/platform-managed。Q3/Q5 的结构化调用参数在调用前存在于工具请求，但独立磁盘封装在调用后补存；Q7 单独请求文件在调用前保存。初始 locator 包含较宽的 receipts 文件名清单，未继续搜索全历史正文；Q2 中不存在的 `spec/v2.4` 造成嵌套 rg exit 2，outer capture exit 0，不隐去失败。随后只读取 AGENTS 指定的 `spec/v2.0`。网页仅依据所列官方 primary 文档，不采用搜索结果中的社区回答。详细诊断、查询计数与封存规则见 ledger。所有本轮产物仅支持此决策建议。
