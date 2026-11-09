# CP517 C+boot 有限设计补充

结论：**FINITE_BLOCKED_NO_IMPLEMENTABLE_SOURCE_CARD_YET**。本次能冻结 C51+6 的接线边界、候选机制及一次性资源判据，不能以现有两包各58 member和两个PID映射签发完整实施卡。此结论不等于 Windows 机制永远不可施工，也不要求先有实现证据才允许 Source。全部新增类为 NOT_IMPLEMENTED_NOT_ACCEPTED；actual_authority=false；source_edit_authority=false；formal_increment=0。作者不签发接受。

已逐一匹配CP517九个输入hash。C51来自 revision03/C-lease-exact-scope.json，受CP511 C-LD01..03和F01-D01..03/W-D01约束；revision02 C-exact-scope只列33个路径，不可当完整C。B候选75e5257c19b2e21e6cabd5e912e2ac6a3e2fe603仍待独立审查。STOP-r2和原Wait要求不变。详细接口差异见B-API-compatibility.md。

## 1. 唯一候选及停止条件

候选 OFFICIAL_ENTRY_FILE_DACL_FENCE_V1 只在冻结的、完整官方启动集合内成立。对每一官方路径找到**新boot后执行其产品行为前必经的产品专属文件**：PE映像以精确 FILE_EXECUTE 拒绝普通产品用户SID；解释型入口以其必读脚本/包文件的 FILE_READ_DATA 拒绝该SID。不能只改快捷方式或只禁止一个已知Core副本；每个直启、旧包、当前包、Desktop、CLI、verifier、release host、backup、recovery、自动重启路径都必须有必经阻断点。禁止把共享electron/node/python/powershell整机执行权撤掉当成产品专属方案。现有运行程序在Restart前可以继续执行，不能从ACL写入推断关闭或静默。

持久清单建议位于受管理的 C:\ProgramData\ResearchOS\RecoveryBoundary\<root-identity-hash>\<operation-id>，这只是拟定位置，不是已有设施。控制目录和围栏目标的所有者、WRITE_DAC/WRITE_OWNER/DELETE/父目录DELETE_CHILD必须在可信管理边界；普通产品token不能撤围栏或替换目标。Exact helper映像独立绑定hash/native file ID，普通CLI和旧包均没有“maintenance bypass”。管理提升只用于部署/读回/撤除围栏；业务身份始终是冻结的原Owner/SID。不得把提升后的管理员token冒充业务Owner。

这是可信Windows、可信管理员、无恶意同SID任意程序/管理员主动绕过的有限官方入口合同。即便采用该假设，普通官方自动重启、更新器、开发启动器和用户正常直启仍须被覆盖；不能以假设把实际入口排除。若官方入口使用内联解释代码、复制/重新构建后直启，且不存在可冻结的产品专属必经文件，本候选即不适用。不得扩成WDAC、驱动、SYSTEM服务或新根方案。本轮不再搜索新机制。

官方文档确认文件访问按token与目标对象描述符判断，父目录ACL本身不控制已有子文件；因此“给根加DACL”不能替代逐目标有效权限与路径覆盖。这里选择精确文件权限而非GENERIC_READ/WRITE掩码，避免共享SYNCHRONIZE位带来的意外拒绝。[Microsoft文件访问权限](https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights)。

在线部署时，对目标和所有可替换祖先持有经native identity核验、禁止delete sharing的元数据句柄；读回安全描述符、hash和file ID后才记录ARMED。句柄只保护当前进程存活期，**不能跨Restart保留**；跨Restart防替换必须由持久ACL/所有者/父级权限及冻结部署登记保证，post重新打开和匹配identity。任何无法获得所需句柄或权限的对象均阻塞，不声称已锁住。[CreateFileW共享语义](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)。

## 2. C51+6接线

完整精确路径见 C-boot-exact-scope.json，总计57：原16 existing production、16 new production、19 tests，加4个boot production和2个boot tests。它是未授权、待资源闭合的候选路径集合；不是允许Source施工的卡。未来基线为 Main4f及已接受A/B的Root串行合成快照；当前不能把B75当已接受基线。Schema24，不引入Source25或DDL。

- internal/recoveryboundary/contract.go：定义版本化pre/post witness、EntryFencePlan、typed CurrentQuiescence、single-operation binding和纯校验。opaque permit私有状态绑定root/DB native identity、operation、plan hash、helper hash、expiry、当前held lease generation；序列化JSON和bool不能构造权限。boot receipt只是输入证据，不是可直接反序列化的capability。
- internal/recoveryboundary/boot_windows.go：实现独立于store/domain/provider的native witness、精确围栏目标检查、pre/post推导和受保护外部状态读写接口。若资源包显示需要服务/installer/额外production文件，此57路径候选停止，不能隐式扩展。
- ops/qualification_recovery_boundary/main_windows.go：独立helper。仅固定 plan/arm/observe/status/disarm-request 状态机；命令是未来设计名称，本轮未建程序也未执行。先验证管理部署和原业务SID绑定，拒绝任意SQL、路径通配符、裸bypass和普通server模式。post通过后调用已有C路径的窄host入口，不启动普通Core。main_nonwindows.go无条件unsupported，不能fallback为无围栏模式。
- apps/control/main.go：顶层唯一mode classifier，早于既有early branches；ordinary normal/replay/replacement/inherited modes各沿C gate取得真实lease后检查双journal再store.Open。当前源码103取得lease、116 replacement gate、119 store.Open、131 NewCurrentMu；这些是插入定位，不是新gate已存在。
- apps/control/qualification_failure_maintenance_windows.go 与 internal/host/qualification_failure_maintenance_windows.go：接受typed CurrentQuiescence候选；重验boundary evidence和exact C own-operation后传递同一真实held lease；绝不从bool或boot JSON直接进入事务。
- internal/qualificationmaintenancejournal/{contract.go,journal_windows.go,replacement_windows.go}：保持两namespace普通/own-inspection两种纯判据。boot外部ARMED记录不是C BEGIN；只在post取到真实lease并完整C preflight后创建C journal。pending boot或不一致fence状态使新ordinary入口拒绝，旧入口靠外部围栏。
- adapters/runtime/data_root_windows.go/bridge_windows.go：单heap owner-state与generation/borrow identity，覆盖C-LD01；同一lease持有跨census、DB reservation、CAS、commit、receipt；内层borrow不能Close外层。C-LD02所有五类upgrade统一normalization+native identity guard；C-LD03 exact-own replacement applied/unapplied不降级。
- replay、prepared recovery、backup、release host及store防御检查沿完整C51既定接线；nested inherited token/borrow交接不重复Acquire，不释放再重取；other平台fail closed。
- internal/domain/runtime_qualification_failure_windows.go：仅在已接受B后串行加入私有历史variant消费者；C写入由internal/domain/qualification_failure_maintenance_windows.go的单事务planned writer完成。boot class只能证明当前本机执行边界，不满足Host/effect历史事实；详见兼容表。

两新增测试文件负责boot contract/native boundary与CLI phase；既有C test路径承接真实入口pending fence/journal、private Tx、borrow和五版本保护。完整cuts见JSON。不会新增Desktop源码patch去假装旧安装包已升级；旧Desktop覆盖是外部围栏资源合同。

## 3. ONLINE -> ARM：消除root lease与backup循环

ONLINE阶段旧Core仍可能持有root exclusive lease。本helper不Acquire该lease，不打开当前DB、不调用store.Open、NewCurrentMu、Host.New、key/provider/listener，不创建C BEGIN，不修改原Run。它只消费另行接受的在线一致性备份/身份导出清单，并记录自身外部operation。

Backup契约必须一次原子视图绑定schema24、project/Goal/Cycle/Task/Run/epoch/profile/owner、DB/artifacts/cursor/outbox/ledger/失败历史、原证据hash和backup ID；可用性来自独立恢复验证与所需凭证仍有效的验证，不在这里读取私钥。文件复制或静态hash清单不等于一致性备份。该备份接口必须在旧Core占有root lease时可用，否则循环仍在，不能arm。Source前只需有可实现且另行接受的生产接口合同；实际在线backup执行和可用性证据是arm门槛，不能反向要求本轮先执行。

备份后旧Core可继续变动；pre witness不是最终C计划。post获取root lease后对当前DB重新census/冻结C PlanCore；原subject身份漂移或无法解释的差异阻塞。旧backup是可用安全副本与身份锚，不得用还原覆盖当前root来抹去备份后的副作用。禁止抢占lease、暂停/杀Core、制造离线副本来掩盖这个前提。

只有Source/native fixture独立接受、入口完整性闭合、已授权部署读回成功、可用一致性在线备份和独立恢复包齐全，才允许未来arm。**本轮这些条件均未完成，不要求用户现在Restart。**

## 4. pre/post witness与抗重放

拟定v1支持的Windows build/文件系统/token类型必须由资源包定值并在Source fixture接受；未列平台拒绝，不以“Windows都支持”外推。受信管理员且无VM/checkpoint内存回滚、kernel/debug tick操纵。不是密码学boot attestation。

pre绑定host identity、业务SID、root/DB volume+file ID、canonical paths和全部祖先identity、schema24、原subject/evidence hashes、backup manifest digest、唯一operation随机值、helper hash、fence manifest digest/version、pre GetTickCount64、LastBootUpTime、受保护存储序号和wall-clock UTC。Root无native file ID时不能拿path/hash代替。

建议待审freshness固定为pre到post UTC至多30分钟，post native uptime至多10分钟且严格小于pre uptime；pre uptime不足10分钟则不arm。wall-clock负向或与uptime/corroboration矛盾均拒绝，不能调时钟补证。30/10是本轮提出的保守策略值，未获接受；资源与操作窗口不支持就不arm。post LastBootUpTime必须改变且与UTC/uptime窗口相容，结合未来明确用户FullRestart完成证据。sleep/hibernate/shutdown FastStartup/发起Restart API返回均不能代替。严格post<pre导致真实Restart仍可能被保守拒绝，拒绝不会擦除操作历史。

受保护外部记录create-new/hash-chain/flush/单operation generation；每阶段记录expected predecessor与helper+plan digest；启动时拒绝重复序号、旧generation、缺文件、unknown inventory、截断和hash漂移。operation nonce本身不是boot ID。完整目录备份回滚/恶意管理员篡改在可信平台假设之外，不能声称hash chain能抵抗它；普通重复提交必须由protected consumed-state拒绝。没有受信时间和防回滚持久状态就不接受witness。

post先确认持久围栏仍覆盖原完整入口、未有新boot普通启动，再取得真实root lease、dispatch owner lock，保持至C完成；未知进程、权限拒绝、fence discontinuity、lease lost全部失败关闭。当前census不补造历史lineage。C permit窄绑定本operation，不能豁免其他pending C/replacement。任意外部effect UNKNOWN继续阻塞；money UNKNOWN保留不是零费用。

## 5. 事务、撤除和失败界限

历史raw frames=3、ACK=2、queue_empty=false、原Wait缺失、Run UNKNOWN、cost和失败次数全部不被boot改写。新派生FAILED观察仅在C/Host/effect/B各独立条件满足时可构造；仍只5个新version和既定ancillary rows，0 runtime_uploads/artifact_uses/artifact_use_proofs。STOP现有类仍拒绝boot-only receipt。

外部围栏状态PREPARED -> APPLYING -> ARMED -> BOOT_OBSERVED -> C_HELD -> C_DURABLE -> DISARMING -> CLOSED；每个状态定义见deployment文档。expiry只取消权限，不自动撤围栏。撤除需要同operation exact before/installed security descriptor、全目标readback和最终C classification；只还原自己确实写入且仍匹配的descriptor，不覆盖他人更新。跨Restart无法维持native handle，必须post重取验证。

必须在部署前交付受保护离线恢复清单、原始descriptor、全部native identity与唯一recovery operation。若helper/证明失败，管理恢复只能恢复产品入口可用性且记录BOUNDARY_ABORTED/UNPROVEN，不能宣告C、NO_EFFECT、formal通过；未知C journal仍由新gate阻断业务写入。不能自动删journal或以失败/到期触发旧包普通启动。没有可行恢复责任主体和恢复路径就不得arm，避免先制造永久锁死再补设计。

## 6. 有限收口

见finiteblockeddecision.md和minimal-resource-package.md。Root可另行只读采集精确事实；资源齐备且每条入口存在产品专属必经文件时，足以把这一既定方案收敛为Source卡，不需要先部署围栏。若有无法覆盖入口或无法建立可信ACL/恢复主体，则本机制退出，保持原恢复分支BLOCKED，不进入第三轮推测方案。备份生产接口、可信管理主体和未来用户FullRestart窗口是另外的资源/决策；窗口只能在部署与独立接受后询问。

