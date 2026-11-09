# FULL 其余失败节点只读分类

状态 READONLY_DIAGNOSIS_COMPLETE_PENDING_ROOT_DECISION；authority NONE；不构成接受。

已关闭 FULL 共1290个测试终态：1261 pass、25 fail、4 skip。扣除已单独处理三当前fixture对应的4个failed事件，本报告精确覆盖21个事件：17个失败叶节点及4个父重复。它们归入8个原因组。原25 fail与4 skip保持原样，不因分类而减计数。

这17叶尚不能建立schema24新增生产回归：相关旧测试与模型来源代码同Main；三生产文件差异仅inventory最大23→24、Service添加prepared authority字段及upgradeLocal添加24计划dispatch，未改此次拒绝条件。但Main未在本任务执行，因此这只是源码归因，且fresh legacy创建成功/首轮拒绝及lease错误顺序保留为Root待决策，不能据此声明无产品bug。

闭合输入 validation.closed.json SHA256 0ce4a6303446250249c5d8b2344e2ca3d298b3f2ac5618b71f5404976f40df34 / 236066 bytes；raw SHA256 b4d15819134bd1d16c976828022c76aad741859967bbf0a3617986b0ca0308ae / 2661892 bytes。report.json保留21事件的原始失败输出、terminal raw行、Source/合同证据全文行与精确pins；source-pins.json同时标明Main和实际compiler inventory匹配。

| 原因组 | failed事件/真实叶 | 分类 |
|---|---:|---|
| GOAL_LEGACY_PORT | 3/2 | LEGACY_FIXTURE_MISSING_PROVENANCE_CAPABILITY |
| RUNTIME_FRESH_LEGACY_MODEL | 10/8 | LEGACY_FRESH_FIXTURE_INCOMPATIBLE_WITH_CURRENT_PROVENANCE_GATE |
| SESSION_TRANSCRIPT_ORDINARY | 2/1 | LEGACY_FIXTURE_INVALID_POPULATED_SCHEMA_MUTATION |
| WORKSPACE_WRITER_EPOCH | 1/1 | LEGACY_FIXTURE_INVALID_ENVELOPE |
| W04_LEGACY_PYTHON_PATH | 1/1 | RESOURCE_MISSING_EXECUTABLE_PATH |
| W04_CURRENT_FROZEN_INPUT | 1/1 | RESOURCE_MISSING_PINNED_PACKAGE_INPUT |
| W16_FROZEN20 | 2/2 | LEGACY_RELEASE_FIXTURE_CURRENT_ROOT_MISMATCH |
| W09_GAPPED_LEDGER | 1/1 | LEGACY_FIXTURE_INVALID_MIGRATION_LEDGER |

父重复仅为 `TestClientGoalSessionWriterAndSettlementGates`、`TestClientTranscriptIndexUpgradesExistingSessionTable`、`TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite`、`TestW05RuntimeEventBrokerBeforeIOAndRollback`。

## GOAL_LEGACY_PORT

Goal mock只有 ResolveGoalBinding/ValidateBinding/AdmitTurn，没有 ValidateLegacySession；创建的 goal-model 也没有 typed host.configure 原始配置。现有 ClientService 在现有Session写入前先验证模型来源，因此两个 lease 用例先得到 MODEL_UNAVAILABLE，未到 goal.start 的 LEASE_EXPIRED 分支。

测试、ClientService、Goal/Session runtime 来源检查与 Main byte identical；不是本次schema24新增代码。没有运行Main套件，不能把静态相同称为Main实际fail。

恢复条件：让 Goal fixture 具备真实 typed host.configure 与同ref绑定，或一个只认可本fixture原创建/模型/profile事实的明确测试端口；不得以无条件nil verifier代替模型来源。先建立有效模型前置条件，再保留现有 expired/missing LEASE_EXPIRED、业务计数及其它 writer/settlement 断言。

最低待决策Source范围：internal/domain/client_protocol_goal_test.go。

对应事件：`TestClientGoalSessionWriterAndSettlementGates/expired_lease`、`TestClientGoalSessionWriterAndSettlementGates/missing_lease`、`TestClientGoalSessionWriterAndSettlementGates`。

证据：[internal/domain/client_protocol_goal_test.go:14](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol_goal_test.go:14)；[internal/domain/client_protocol_goal_test.go:279](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol_goal_test.go:279)；[internal/domain/client_protocol.go:939](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol.go:939)；[internal/domain/client_protocol_configuration.go:776](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol_configuration.go:776)；[internal/domain/client_protocol_goal.go:299](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol_goal.go:299)。

未关闭：合同列出LEASE_EXPIRED但未在所查JSON条款规定它与MODEL_UNAVAILABLE同时失效的优先级。若Root要求lease错误必须优先，属于既有生产错误排序待决策，不能由这两个缺模型前置条件的case直接证明。

## RUNTIME_FRESH_LEGACY_MODEL

三native旧helper直接session.create(既有RuntimeProfile的model_config.ref)后首次session.send，没有host.configure配置记录；新sid还没有已完成session.send/goal.start的Task来源。originalSessionTasks只读取此sid的completed原始命令，ValidateLegacySession又要求原Task初版inputs中sealed且runtime_bindings精确可信的profile。所以8叶在session.send前得到legacy original frozen profile unavailable；尚未执行它们后续的物理权限、事件提交/回滚、工具或独立接受断言。

三fixture和client_protocol_configuration/runtime_sessions_windows/client_protocol都与Main byte identical，现象来自已存legacy/current-contract边界，而非schema24新增模型代码。

恢复条件：若这些用例验当前正式路径，先真实host.configure生成typed ref，再生成并封存引用同ref、匹配provider/model/endpoint/credential元数据的RuntimeProfile，注册/绑定/qualification和provider route必须一致，ClientService及RuntimeCoordinator具备相同ConfigurationAuthority，然后真实create/send。不能只加ConfigurationAuthority或直接伪造host_model_configurations/idempotency/Task历史。若保留旧路线，需匹配冻结历史程序与真实来源夹具另行验证。原8叶所有后续正反断言必须继续执行。

最低待决策Source范围：internal/domain/runtime_permission_windows_test.go；internal/domain/runtime_session_events_windows_test.go；internal/domain/runtime_tool_integration_windows_test.go；a narrowly owned shared typed-runtime test helper only if existing helpers cannot express those pins。

对应事件：`TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite/ALLOW_ONCE`、`TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite/DENY`、`TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite`、`TestRuntimeOriginalToolPermissionExpiresWithoutPhysicalWrite`、`TestRuntimePermissionDecisionWaitsForAnotherRequiredResource`、`TestW05RuntimeEventBrokerBeforeIOAndRollback/rollback=false`、`TestW05RuntimeEventBrokerBeforeIOAndRollback/rollback=true`、`TestW05RuntimeEventBrokerBeforeIOAndRollback`、`TestRuntimeMuSessionToolAndIndependentAcceptance`、`TestRuntimeMuToolRefusalAllowsNextTurn`。

证据：[internal/domain/runtime_permission_windows_test.go:174](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/runtime_permission_windows_test.go:174)；[internal/domain/runtime_tool_integration_windows_test.go:138](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/runtime_tool_integration_windows_test.go:138)；[internal/domain/runtime_session_events_windows_test.go:470](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/runtime_session_events_windows_test.go:470)；[internal/domain/client_protocol_configuration.go:797](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol_configuration.go:797)；[internal/domain/runtime_sessions_windows.go:103](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/runtime_sessions_windows.go:103)；[internal/domain/runtime_sessions_windows.go:53](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/runtime_sessions_windows.go:53)；[internal/domain/client_protocol_sessions.go:193](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol_sessions.go:193)。

未关闭：既有生产creation binding仍允许没有typed配置记录但有当前RuntimeProfile的legacy ref（sessionModel/matchStoredClientConfiguration），而fresh legacy首turn来源永远为空。这是已存可用性/兼容性边界，Root须判定该路线是否仍属支持合同。它不能因Main byteequal或fixture分类而自动关闭；当前typed-model/native功能回归也不能由此无效前置条件确证。

## SESSION_TRANSCRIPT_ORDINARY

fixture先以当前New建立数据库，再DROP已安装的transcript_artifact_id并写入Session；ordinary随后要求New自动修补两次。CheckMigrationSafety对已有authority的additive/fence结构差异要求matching backup和isolated restore，实际正确触发MIGRATION_PREBACKUP_REQUIRED。restore subcase通过，但不能抵消ordinary未接受。

测试与Main相同；backup_migration只把库存上限23改24，结构差异拒绝及New调用顺序逐字相同。

恢复条件：保留真实历史session升级的字段/行数保存断言，使用匹配历史来源和显式允许的backup/restore升级路径；另外将当前数据库被人为破坏时的ordinary startup明确验证为prebackup refusal与零额外改变。不得去掉guard，或把普通New改成隐式repair。仅直接EnsureFence的restore pass不构成产品历史升级接受。

最低待决策Source范围：internal/domain/client_session_bootstrap_test.go；an existing explicit historical upgrade fixture if Root chooses the product migration case。

对应事件：`TestClientTranscriptIndexUpgradesExistingSessionTable/ordinary`、`TestClientTranscriptIndexUpgradesExistingSessionTable`。

证据：[internal/domain/client_session_bootstrap_test.go:60](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_session_bootstrap_test.go:60)；[internal/domain/backup_migration.go:15](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/backup_migration.go:15)；[internal/domain/backup_migration.go:126](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/backup_migration.go:126)；[internal/domain/store.go:66](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/store.go:66)。

未关闭：目前该fixture不是可信旧release。若必须保留其原ordinary正向语义，需要Root先确认哪个历史版本与显式升级契约真正支持该行为。

## WORKSPACE_WRITER_EPOCH

line191设置revPtr(0)，该函数对v<=0返回nil；handlerDecode调用DecodeEnvelope在缺writer epoch时报MISSING_FIELD，测试在Execute前中止。合同writer_epoch整数minimum1，0不是可用的过期epoch测试输入。不是DecodeEnvelope直接以minimum检查0。

测试、revPtr、DecodeEnvelope及协议JSON与Main byte identical。

恢复条件：改用合法正整数但与当前epoch不同的值，例如当前fixture实际epoch=1时提交2，保持原STALE_WRITER_EPOCH与no-file-IO断言以及随后正常导入/精确bytes/replay断言；不得把minimum降0。也可通过真实takeover构造较旧的正epoch，但不是本次最低必需范围。

最低待决策Source范围：internal/domain/client_workspace_test.go。

对应事件：`TestClientWorkspaceImportExactBytesReplayAndEpoch`。

证据：[internal/domain/client_workspace_test.go:176](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_workspace_test.go:176)；[internal/domain/client_workspace_test.go:123](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_workspace_test.go:123)；[internal/domain/client_protocol.go:1264](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol.go:1264)；[internal/domain/client_protocol.go:164](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol.go:164)；[internal/domain/client_protocol.go:950](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/client_protocol.go:950)；[internal/api/contracts/client.protocol.schema.json:3826](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/api/contracts/client.protocol.schema.json:3826)。

## W04_LEGACY_PYTHON_PATH

原测试已执行ImportSpecification及攻击校验，随后exec.Command("python", copied/tools/validate_package.py)因PATH找不到python失败，尚未执行A01-03的PASS/SPECIFICATION_PACKAGE_ONLY/NOT_RUN及readonly manifest断言。

context_test.go与Main byte identical；这是FULL运行环境资源未接线，未证明Importer regression。

恢复条件：在Root受控测试环境提供已锁定的python.exe可执行目录给PATH，并保持复制包的原validator；不以系统任意Python、替换validator或跳过断言来完成。若改Source使用显式RESEARCHOS_PYTHON，也须Root决定接口并保留原validator执行。

最低待决策Source范围：none required if Root wires its pinned Python directory into test PATH。

对应事件：`TestW04A01`。

证据：[internal/domain/context_test.go:252](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/context_test.go:252)；[internal/domain/context_test.go:312](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/context_test.go:312)。

## W04_CURRENT_FROZEN_INPUT

RESEARCHOS_W04_PACKAGE_INPUT为空，line264 fail发生在CopyFS/ImportSpecification之前。输入必须是明确冻结目录，PACKAGE_MANIFEST.json SHA256固定4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964。资源存在性未由本报告扫描/验证。

w04_current_context_test.go与Main byte identical，当前缺env接线，Importer实际分支未运行。

恢复条件：Root提供被审查的固定package目录并验证manifest和其closure，再给受控进程RESEARCHOS_W04_PACKAGE_INPUT；不得从待导入包manifest自动生成信任pin或复用不匹配的当前目录。保留当前MU route、rules和全部import拒绝断言。

最低待决策Source范围：none required for resource wiring。

对应事件：`TestW04CurrentA01`。

证据：[internal/domain/w04_current_context_test.go:259](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/w04_current_context_test.go:259)。

未关闭：现有资源是否满足此exact manifest/closure仍需Root验证；不能称BLOCKED缺文件，仅能确认本次env缺失。

## W16_FROZEN20

controlSnapshotFixture在当前setup DB上取得snapshot并传当前root。PrepareEvolutionControlBundle要求exact1..20 release；Main当前有23个numbered SQL，T3有24，二者都不是20。只更换root也不足：该函数随后要求snapshot真实ledger1..20及source/target backupSchema相同。

control test/projection与Main相同；upgradeRelease exact函数亦逐字相同（backup_upgrade仅另处新增24计划dispatch）。T3增加SQL24使既有当前root失配继续存在，不能只归因于新增SQL24。

恢复条件：使用真实冻结20编号/contract目录、匹配schema20的真实DB constructor和control binary/source pins，再生成快照。保留原AppContainer拒绝、public/private-auth/stale覆盖及business no-gain断言，不重标当前24DB ledger为20，不删更高表或放宽exact20。若迁到当前Control API必须作为明确的新用例合同另行决定，不能静默替换历史case。

最低待决策Source范围：internal/domain/evolution_control_test.go；a narrowly scoped historical20 setup/constructor helper and its frozen resources。

对应事件：`TestW16ControlReplayNative`、`TestW16ControlBusinessNoGain`。

证据：[internal/domain/evolution_control_test.go:95](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/evolution_control_test.go:95)；[internal/domain/evolution_control_test.go:169](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/evolution_control_test.go:169)；[internal/domain/evolution_control_test.go:219](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/evolution_control_test.go:219)；[internal/domain/evolution_control_test.go:276](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/evolution_control_test.go:276)；[internal/domain/evolution_control_projection.go:24](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/evolution_control_projection.go:24)；[internal/domain/evolution_control_projection.go:67](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/evolution_control_projection.go:67)；[internal/domain/backup_upgrade.go:159](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/backup_upgrade.go:159)。

未关闭：本报告没有验证已有historical20 resource是否可用；Root需先配齐真实matching source/DB/control pins。

## W09_GAPPED_LEDGER

store.Bootstrap记录version1，fixture只执行SQL7并手工记录version7，形成{1,7}并插入旧root。New在任何domain/additive/fence DDL前逐条要求v=n，因此对v7!=2正确拒绝MIGRATION_UNSUPPORTED_OR_GAPPED_VERSION，根本未到0009 root identity migration。

retrieval test、Bootstrap及库存连续编号条件与Main相同；上限23→24不改变{1,7}拒绝。

恢复条件：用真实连续历史库存构造旧DB。若仅验SQL9语义，在隔离历史1..8夹具上通过明确测试事务应用冻结0009并保留identity空/revoked1/revision2断言，单列gapped ledger拒绝；这仍不是产品升级接受。若验New/产品历史升级，必须先有匹配历史程序及受支持的显式backup/rehearsal/upgrade路径，不能伪造ledger填空或放宽New。

最低待决策Source范围：internal/domain/retrieval_test.go；an exact contiguous historical fixture only if Root authorizes it。

对应事件：`TestW09LegacyRootMigrationRevokesUnidentifiedRoot`。

证据：[internal/domain/retrieval_test.go:493](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/retrieval_test.go:493)；[internal/store/sqlite.go:74](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/store/sqlite.go:74)；[internal/domain/backup_migration.go:60](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/backup_migration.go:60)；[internal/domain/store.go:66](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/store.go:66)；[migrations/sqlite/0009_retrieval_root_identity.sql:1](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/migrations/sqlite/0009_retrieval_root_identity.sql:1)。

未关闭：当前已查代码未证明schema7/8→current的正式升级plan可用；不应凭测试名发明该产品能力。

## 四个显式skip

全部为NOT_ACCEPTED；只打开环境变量不能代替真实资源、执行及独立审查。

| 用例 | 未打开的入口 | 恢复边界 |
|---|---|---|
| `TestControlCurrentActualOwnerNoGain` | `W16_CURRENT_NATIVE`: 1 | Root bounded current-control native harness with its actual owner/resource bindings and independent review; setting env alone is not acceptance. [internal/domain/evolution_control_current_native_test.go:131](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/evolution_control_current_native_test.go:131) |
| `TestControlCurrentPreservedPreparation` | `W16_CURRENT_OFFLINE_WORK`: explicit preserved diagnostic directory | Root separately reviewed preserved setup-only diagnostic; it never grants qualified owner/evaluation or native acceptance. [internal/domain/evolution_control_current_offline_test.go:24](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/evolution_control_current_offline_test.go:24) |
| `TestW06ContextContinuation` | `RESEARCHOS_C01_MODEL`: 1 | Root real model C01/G02 runner with approved resource wiring and closed actual evidence. [internal/domain/orchestration_context_test.go:11](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/orchestration_context_test.go:11) |
| `TestW05Live` | `RESEARCHOS_RUNTIME_LIVE`: 1 | Root separately authorized live executable/provider/resource harness. This report does not run it. [internal/domain/runtime_test.go:277](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-prepared-historical-regression-v3-6cbe02cc48b14409/internal/domain/runtime_test.go:277) |

## Source归因与边界

共29个参与证据的Source/contract配对：26个Main字节相同、3个有差异。逐文件SHA/bytes及actual compiler出处见source-pins.json，完整差异见Main-to-T3-deltas.patch。Main编号库存23份、T3为24份；都不是W16要求的20份。

- Read-only diagnosis of closed Root actual receipts and public Source/contract text; no Source construction or code mutation.
- Main has not been executed by this agent; Main attribution is based on exact bytes and focused deltas, not a claimed Main runtime result.
- No cause classification grants acceptance or removes an original failed node. All25 fail and all4 skip remain in the original closed result.
- No proof of schema24-introduced production regression is established by these17 remaining leaves; existing legacy creation/first-turn compatibility and error ordering remain explicit decisions.
- No Go/SQL/native/Git/provider execution; no private key/credential, original database or product holdout reads. Public Source and closed receipt metadata were read.
- No failure counter is reset and no existing sealed Source package is modified.
