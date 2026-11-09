# 资格失败收尾架构独立审查

结论：可接受 B/C/STOP/D 的权限与证据分层原则；当前包还不是可以直接执行 C、STOP、D 的完整施工合同。F01–F05 需先收敛，F06/F07 必须进入后续 Source/fixture 卡。此回执不接受 Source、实际失败收尾或新资格调用，formal_increment=0。

40 项冻结输入哈希全部匹配。Main HEAD 为 4f4023c956f84d65743f39ce77d6c8899a21ada1；审查开始时 tracked dirty20、indexempty。源码与冻结诊断公开摘要均只读；未打开 actual DB、凭据或私钥，未运行当前 Core、调用模型、停止进程或改共享状态。

实际状态仅据冻结诊断：request bc269e77 已消费，Run f3dcb996 仍 RUNNING、dispatch UNKNOWN；MODEL CONFIRMED 与 UNKNOWN 金额是两个不同维度。历史worker native closure已有公开回执，但历史Core源码到binary链、独立verifier精确native退出和console可行性尚未由本审查证明。

## F01 [P1] 冻结输入尚未把历史 Core 可执行文件绑定到审查过的 gate/sandbox 源码

现有冻结输入证明当前 Main 源码和公开运行摘要；不能据此签发历史 NO_EFFECT 重建证明。此为所审输入包的证据缺口，不声称整个仓库不存在相关证据。

证据：`ARCHITECTURE.md:45`；`internal/domain/runtime_broker_windows.go:149`；`internal/domain/runtime_broker_windows.go:203`；`ops/experiment_sandbox/sandbox_windows.go:264`；`ops/experiment_sandbox/sandbox_windows.go:301`。

限定修正：增加公开 provenance matrix：实际 Core image digest及可信构建来源 -> exact source tree/dirty patch/toolchain/build flags；worker.exe、worker.mjs及bundle/profile digest -> 实际staged输入；历史AppContainer/handle/env/网络边界与host tool/provider路由全链。已捕获安装/构建证明优先；新fixture只能验证代码语义，不能替代历史执行身份。任一缺项保持NOT_PROVABLE/UNKNOWN。

安全下一范围：仅收集既有公开构建/安装回执并复核哈希，或隔离历史fixture；不读密钥，不读写当前DB，不运行当前Core。

## F02 [P1] 历史重建证明不能沿用原 executor 输出的 provenance

recoverArtifact把produced_by、artifact_use.principal固定为manifest原executor，input_refs只来自原运行。若原样导入当前重建证明，会把维护作者的推导归给原worker，且新增证明不能加入旧native artifacts清单冒充历史输出。

证据：`ARCHITECTURE.md:56`；`internal/domain/runtime_recovery_windows.go:100`；`internal/domain/runtime_recovery_windows.go:124`；`internal/domain/runtime_recovery_windows.go:137`；`internal/domain/runtime_recovery_windows.go:165`；`internal/domain/runtime.go:244`。

限定修正：冻结独立maintenance proof envelope，含当前actor/Owner-root、observed_at、operation/plan hash、historical subject、每个证据hash、推导规则版本和原native manifest。外层Artifact作者应真实表示Host/维护主体；若现有contract迫使沿用executor outer association，必须明确该字段仅为subject association，并经独立contract决策，不能默称原executor生成。证明LOG/maintenance artifact与旧result_artifact_ids分开；保持旧native output manifest精确匹配。

安全下一范围：先做schema24 contract兼容性fixture；选择现有允许Artifact字段/类型表达，不能改spec/v2.0原快照。

## F03 [P1] 精确写集需要包括事件水位与全部 provenance 辅表，并固定幂等行映射

现有event helper除EventEnvelope/outbox外还推进ProjectState版本；put生成domain_versions/domain_refs，artifact helper写uploaded_content/runtime_uploads/artifact_uses/ImpactLink。当前设计的高层允许增量尚不足以形成精确CAS/禁止增量比较。recoverTerminal在artifact与Run之间主动提交，不能直接满足单事务承诺。

证据：`ARCHITECTURE.md:56`；`internal/domain/store.go:189`；`internal/domain/store.go:234`；`internal/domain/store.go:375`；`internal/domain/store.go:401`；`internal/domain/store.go:410`；`internal/domain/runtime_recovery_windows.go:221`；`migrations/sqlite/0002_domain.sql:31`。

限定修正：冻结schema24表/键/字段级before-and-after集合：精确Run、dispatch、runtime_observations；新增Artifact及其versions/refs/uploads/uses/ImpactLink；ProjectState revision/event_sequence、EventEnvelope与outbox watermark；idempotency固定namespace例如host:qualification-failure-maintenance，key=operationID，principal=currentOwner，request_hash=planHash，body包含outcomeHash/确切subject。只抽取接受现有tx的helper；全部新facts+Run+marker一次commit。schema fingerprint包括sqlite_master的表/索引/触发器以及合同hash，不能仅max(schema_migrations)=24。

安全下一范围：先冻结事务写集和schema24 isolated fixture，做每条写入前后crash cut、同operation冲突、已提交重入零增量；不修改实际schema。

## F04 [P1] BEGIN 意图的固定发现位置和与现有 early commands 的互锁尚未指定

只有外部preflight plan文件不能让正常启动知道哪里有未完成BEGIN。现有startup gate只扫描verifier replacement journal；其他early maintenance分支在普通startup gate之前返回。若仅给正常路径加一个检查，另一个正式维护入口仍可能在未分类的qualification intent期间获得同一lease并改状态。

证据：`ARCHITECTURE.md:60`；`apps/control/main.go:34`；`apps/control/main.go:37`；`apps/control/main.go:103`；`apps/control/main.go:116`；`apps/control/main.go:119`；`internal/host/runtime_verifier_replacement_journal_windows.go:469`。

限定修正：固定data-root/host下私有非reparse journal namespace；持lease先create-new并flush完整plan+BEGIN，再允许DB修改；所有会修改同data-root的official early entry都先组合检查各maintenance namespaces，recover只可豁免自己的exactoperation。定义空目录/半写plan/torn BEGIN、未知文件、外部plan丢失均fail closed；preflight保持外部且无BEGIN。NOT_APPLIED分类是否允许退出block、是否需显式同plancommit或append-onlyabort必须冻结，禁止默认重放。

安全下一范围：单独early parser/startup gate source卡；若要改现有replacement/prepared maintenance入口，先扩展C文件allowlist并串行交接；隔离crash fixture验证。

## F05 [P1] 新 Task/Plan 需要同时修复 binding 创建与所有 runtime-only 查找

同runtime创建新plan会撞runtime_bindings主键；即使绕过此处，两个plan会使setup/confirmation取到任意旧Task。runtimeSetupGrants按runtime取一个task后逐一比较历史grants，使合法旧新executorgrant不能同时通过。

证据：`internal/domain/runtime_qualification.go:163`；`internal/domain/client_runtime_setup_windows.go:196`；`internal/domain/client_runtime_setup_windows.go:368`；`internal/domain/client_runtime_setup_windows.go:398`；`internal/domain/runtime_qualification_execution_windows.go:253`；`migrations/sqlite/0016_runtime_qualification.sql:2`。

限定修正：复用runtime绑定仅在profile_ref/hash、technical_hash、owner及当前Owner-root全部精确一致时允许，否则显式重配置scope；禁止INSERT OR IGNORE吞掉漂移。计划/确认/UI选定不可变attemptID/taskID/planHash；历史grant按grant.TaskID+grant.RunID+runtime+epoch查它自己的plan和qualification marker。普通mu_turn按原dispatch验证，不绑定最新qualificationTask；不删除历史grant。当前fresh-intent与新attempt事务唯一，lineage单调，旧CONFIRM永不重定向。

安全下一范围：D独立schema/contract卡明确runtime_qualification.go、client_runtime_setup_windows.go、runtime_qualification_execution_windows.go及精确GUI/Host调用点；测试至少两个历史qualificationgrants+普通mu_turngrant、冲突binding、并发intent、旧CONFIRM。

## F06 [P2] typed NO_EFFECT 构造点需明确在首次prepare之前且不能靠原generic gate返回值辨识

非MODEL会在marker和route验证前返回generic503；providerRoute还会在PREPARED之后第二次调用。直接把这一generic故障换成typed或在共享helper上升级错误会扩大proof资格。冻结文字要求正确，源码落点还应显式锁定。

证据：`internal/domain/runtime_model.go:100`；`internal/domain/runtime_model.go:106`；`internal/domain/runtime_broker_windows.go:84`；`internal/domain/runtime_broker_windows.go:149`；`internal/domain/runtime_broker_windows.go:226`；`internal/domain/runtime_command_queue_windows.go:457`。

限定修正：B实现卡指定首次broker gate的私有构造函数，先精确核验marker/manifest/task/epoch/knownroute/key/frame及零历史effectstage；第二次gate或任何已有stage只能generic UNKNOWN。closure必须证明所有broker completion已结束/可逐帧归责；nativeworker结束本身不替代hostinflight结算。最小v1严格只许3帧/ACK2/rejection1，无额外suffix。

安全下一范围：在A冻结交接后只做B原scope；补拒绝unknownroute、marker缺失、已PREPARED重检、并发额外frame和错误持久化失败fixture。

## F07 [P2] 隔离 console 成员快照尚未证明到广播时的独占性

当前spawn参数不是已有私有console证明。设计先枚举再CTRL_C_EVENT广播的间隔没有成员稳定性依据；精确Core handle只固定Core身份，不能固定console其他成员。尚无nativefixture，所以不能批准actualsignal。crashstop同样不能用新ro连接PRAGMA冒充liveCore设置证据。

证据：`ARCHITECTURE.md:66`；`apps/desktop/main/lib/desktop-management.js:440`；`apps/control/main.go:220`；`internal/store/sqlite.go:44`。

限定修正：STOP source卡先固定console隔离威胁/所有权模型，验证真实Electron启动方式的console可用性；至少插入join-before-signal fixture，无法建立成员稳定性就STOP_UNAVAILABLE。不要将重复枚举称为原子排他。保持单独exacthandlecrashstop计划、没有自动fallback；构建来源证明liveCore执行了Ready校验，取得SQLiteonlinebackup并最终lease后逻辑CAS；原nativeworker及verifier闭合证据均须独立齐全。

安全下一范围：仅独立nativeWindowsconsole/handle/WALfixture；不向当前Core发信号、不调用当前进程句柄terminate、不做当前DBbackup。

## 已接受的边界

- FAILED-only closure; original frames ACK2/native cancellation facts preserved; generic faults UNKNOWN
- C separate historical reconstruction observed now, no fabricated old rejection
- early schema24 constructor without migration; same SID/Host/Owner; native lease; exact-plan CAS; single SQLite commit decision
- STOP separately scoped; no automatic crash fallback; console feasibility unproven
- D explicit fresh Owner intent, newTask immutablePlan, append-only lineage, ancestor budget conservation, new one-call confirmation

## 交付与判据

B 可在 A 的明确文件交接后按原有限范围实施，不能依赖本审查补发 actual 权限。C 先分别冻结 provenance、证明归属、schema24 精确事务写集及启动互锁；任何新增共享文件必须修订 allowlist。STOP 只做隔离 native fixture。D 的显式 intent、immutable lineage 与预算祖先约束保留，并补全 F05 四个生产调用点。

独立复核应以行级 before/after 哈希、真实断言和 crash cuts 为证据；只编译通过、零行查询、当前源码一致或一次 console 枚举均不能替代相应的历史/原生证据。此轮运行测试 0；这是只读架构审查，不把静态分析计作 fixture PASS。

模型按 repo/parent 策略分配 gpt-6-astra/high；没有独立运行时模型 introspection，因此不将配置声明提升为已测运行时事实。
