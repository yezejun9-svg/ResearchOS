# 资格失败 revision02 独立架构与 F01 语义审查

结论：B、D 的设计方向可继续进入各自受控施工；C 还需要冻结具体租约交接与遗漏入口。历史 Core/worker 身份链现已补足，但完整历史 NO_EFFECT 重建仍为 **NOT_PROVABLE**。当前严格 STOP actual 为 **STOP_UNAVAILABLE**。本审查不接受 Source、实际停止/维护/新调用或正式用例；formal_increment=0。

冻结 scope、四个输入 manifest 及其58个文件验证匹配；新增 semantics01 manifest 与4个文件也匹配。相关源码从不可变4f4023 Git blob捕获，并与架构冻结哈希比对。未检查正在施工的 A/STOP源码或改变共享状态。运行测试0、断言0；静态分析不记作fixture PASS。

## 影响与阻塞

### R2-F01 [High / P1] 历史 Host 拒绝成立，完整所有路径的 NO_EFFECT 缺证

位置：`internal/domain/runtime_broker_windows.go:82,149,203,255`、`runtime_model.go:100`、`ops/experiment_sandbox/sandbox_windows.go:59,264`。

Core c4a3b498、2294历史编译输入、13项关键源码及新增5项源码、原worker5f364598/bundle2a8e7013已绑定。SDK8df与wrapper292ad区别已澄清，原native128探针保留。SDK完整历史transitive build input closure仍未证明。

TOOL在首次providerRoute内被MODEL-only检查拒绝，发生于prepareEffectTx之前；Host所有工具/模型/来源/实验执行在PREPARED和STARTED提交之后。dispatchGate已有resourceWriteLock。wrapper292ad的makeTools.execute只await protocol.effect(TOOL)，不直接执行该工具。可以据此形成**Host代理路径拒绝**的历史推论；不得把generic503改称原在线typed NO_EFFECT。

更广的“任何允许路径均无外部效应”需要额外前提。源码设置普通AppContainer空capabilities、仅三条标准管道、隔离环境、input只读/output可写和job限制，均有历史绑定。但普通AppContainer没有LPAC的ALL APPLICATION PACKAGES opt-out；OS共享授权/IPC并非由该源码完整枚举。网络默认拒绝有平台依据，历史有效WFP/loopback例外状态未捕获。微软资料仅说明平台机制，不能证明本次历史机状态。[AppContainer/LPAC](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer)、[资源隔离](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation)、[网络隔离与例外](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall)。

没有发现或声称一次真实沙箱逃逸。缺口是把局部控制推成完整历史事实。私有scratch写入本身不是外部TOOL效果；仍不能据此跳过更广证明。保留完整15项 `premise-matrix.json`，缺项不签发C重建。若合同只需某一具体Host工具路径，应先明确缩窄证明命题和消费方，不在实现时偷偷缩窄。

native receipt实际job_total_processes=2；ActiveProcessLimit1不能改写成历史总共一个进程。可接受原回执证明最终job active0、exit124、timeout、streams/cleanup/output完成。artifacts=[]、queue_required=false、无queue_control支持窄分支，原始frame语义和DB全量census须由另行接受的实际preflight核验。

### R2-F02 [High / P1] C具体lease handoff与supervisor入口尚未闭合

位置：`backup_prepared_abandonment_handoff.go:181`、`backup_prepared_abandonment_upgrade.go:416`、`backup_upgrade.go:245`、`ops/supervisor/release_host/main.go:39`。

两个prepared升级工作流会内部取得源租约。外层为combined gate先持锁会造成再次获取失败；放锁后再进内部则留下检查至执行间隙。其他upgrade-local分支也必须被同一外层租约覆盖。release_host在OpenCanary之后才取lease并直接store.Open；C中心qualification检查不等于replacement gate，它不在当前production allowlist。

限定修订见 `C-minimal-addendum.json`：外层一次取得精确native lease→两namespace组合检查→读取key/protected/DB→全工作流结束后释放；两个prepared分支接收不可由JSON构造的借用capability，重新验证Held/root，不重复取得、不关闭外层lease。release_host先经过同一组合检查，或通过可测硬规则证明只接受全新disposable root。没有宽泛callback、skip布尔或解除锁再检查。

最小新增现有文件：backup_upgrade.go、backup_prepared_abandonment_upgrade.go、backup_prepared_abandonment_handoff.go、backup_prepared_abandonment_upgrade_other.go、ops/supervisor/release_host/main.go。另加domain平台借用adapter与release_host平台gate及对应4组测试；完整准确列表在JSON。其余原C范围保留，需先冻结addendum再开Source卡。

### R2-F03 [High / P1] 原verifier closure仍不能满足严格STOP

位置：`internal/host/runtime_verifier_process_windows.go:219-226`。

源码defer close会cancel、关闭管道并调用原cmd.Wait；管理同步响应可以支持此收尾路径已执行的推论。Wait返回值被丢弃，不能写成captured native wait成功、numeric exit0或已获原始退出回执。原worker closure与verifier closure是独立事实；当前strict STOP仍不可执行。

可分析另一类证明：若本次确实在Host196行Execute错误返回，则204行短Token及process.verify(job)不可到达；verifier main握手后仅等待完整job，Verify之前无HTTP业务调用。ensureRuntimeVerifier创建principal/grants不等于给子进程发credential。但实际installed verifier二进制与main/protocol/client及init闭合绑定、本次历史错误路径绑定、所有stdin/凭据传递路径还需补齐。即使补齐，只能叫SOURCE_DERIVED_NEVER_JOB_AUTHORIZED，不能叫nativeclosed，也不能自动替换现STOP合同。最小缺证与独立Source/操作边界见 `STOP-alternative-proof-prerequisites.json`。不重放旧request，不凭PIDabsence通过。

### R2-F04 [High / P1] STOP须冻结具体接受锚点

位置：STOP架构的accepted F01/plan输入边界。

caller JSON与expect-plan-sha256只能证明自洽，不能证明外部接受。最小可行方案是一次operation专用构建中固定已审plan和证据manifest hash，或有明确owner/更新规则的受保护registry；仍逐项校验事实，不能只查allowlist。默认空表可使功能安全禁用，但不能当可操作Source已完整交付。具体anchor合同与测试需另冻；它不能凭空对同SID管理员形成密码学独立性，local receipt/Owner trust必须如实声明。

## 已解决的设计项与后续验收

- B：首次gate私有构造点、knownroute/marker/key/零effect-stage、不可由第二gate或generic503提升；admission close、所有broker goroutine join/completion drain、heartbeat join全部明确。实现后要用并发晚帧/晚completion/持久化失败测试证明；不得只等Bridge.Done。
- C F02/F03：schema24允许MANIFEST、GENERATED、LIVE、currentOwner、run_id=null。artifact_uses在run=nil立即返回；五个domain version及refs、upload、observation、outbox、snapshot、marker写集覆盖现有event/put附带写。保持原Task/NoProgress/财务/原输出清单；FullPlan hash避免自引用。当前是合同比对，未运行事务fixture。
- D F05：三个runtime-only查找、精确binding reuse、历史grant按自身Run/Task/epoch、schema24幂等索引与原子单调链、相同Goal/输入/NoProgress均已明确。D-addendum01有效覆盖原stub声明：必须接受真实B的validatedQualificationFailureTx并经真实firstgate/drain/terminal路径生成fixture。
- D runner：node:test真实desktop库和现有Python Playwright实际React workbench路径合理。新测试不得以组件mock、插入FAILED行或总返回true替代production proof与UI交互。
- STOP：console广播分支明确禁用；exact handle/creation/SID/image/parent、一次terminate、原handle wait及停止后真实lease设计合理。BEGIN IMMEDIATE后query_only=ON是明确限定的zero-row例外，不是普通C lease替代；必须用真实driver/native WAL fixture证实保留writer reservation与DML/DDL拒绝。

本轮STRIDE从worker→broker、sandbox→OS、maintenance plan→DB/journal、prepare UI→fresh authority四个边界展开；相关OWASP类别为A01/A04/A08、LLM05/LLM06/LLM10。依赖未变，本轮未做全仓CVE扫描，不把源码设计审查写成供应链安全接受。

优点：权限由代码gate执行；raw ACK/frames和UNKNOWN money保留；证明作者与历史subject分离；新调用必须真实失败闭合后另行明确确认。仍应按本报告阻塞项修订并独立验收，不增加任何正式计数。

补充E（29872605）及3个文件哈希匹配：f255f4d4安装二进制、installation、main/protocol/client三项真实历史编译输入的绑定已补入。2294是两个binary的联合vector，不等于verifier精确init依赖闭合；公开响应refs也尚未独立证明历史196分支。该补充缩小never-job缺证清单，不改变本报告strict STOP_UNAVAILABLE或native closure结论。
