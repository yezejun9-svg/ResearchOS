# fresh legacy 首轮与 Goal lease：窄合同复核

结论：本轮恢复正式测试应补齐 host.configure typed fixture；不扩展 fresh-legacy 生产兼容，不改生产 gate 或错误优先级。Root 已明确选择这个范围。现有 legacy 创建成功而首轮被拒绝的额外兼容行为仍未闭合，不能把 fixture 修复称为该行为已修复。

状态：READONLY_CONTRACT_REVIEW_COMPLETE；authority NONE；formal_acceptance false。未执行 Go/native/SQL/model，未读凭据原值或私密资源，未修改 Main/T3/T4/T5/canonical。原 FULL 25 fail/4 skip 不因本报告获得接受。

R = D:/作品集/ResearchOS/research-os
T5 = R/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2
S = D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4
所有下列代码行号以本次实际读取的 T5 为准；Main 对应字节比较见 refs.json，不以字节相同推断没有产品缺陷。

1. 当前合同保证什么

[22_CLIENT_INTERFACE_DETAILS.md:55](D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/22_CLIENT_INTERFACE_DETAILS.md:55)–58 明定首次顺序：native credential → host.configure → 同 workspace 与返回的 model_config_ref 创建 Session → attach 取得 writer → 发送任务；107 明定 model_config_ref 的来源是 host.configure，固定 provider/base_url/model/credential/config_revision；92 要求既有 Session/Run 保留使用版本。

因此，同一仍合法的 typed 配置应能进入首轮正常的授权、租约、runtime admission 和资源检查，不能因不存在先前 Task 构造循环前置条件。但合同不保证 create 成功即模型在线或首轮执行成功：55 不自动请求模型，56 允许真实探针失败，117 的 session.send COMPLETED 仅表示合法入队，203 允许 MODEL_UNAVAILABLE/资源阻塞并保持历史可读。

[client.protocol.schema.json:418](D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4/contracts/client.protocol.schema.json:418)–438 只约束 CreateSessionPayload 的非空字符串；128–155 允许 NORMAL 首轮且没有 prior Task 参数。字符串通过 Schema 不等于获得任意 legacy model 来源授权。未发现当前合同保证“无 host.configure 的任意 legacy ref 只要 create 被接受就必须可执行首轮”。

2. 已确认的 legacy 循环与当前 proof

[client_protocol_sessions.go:193](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/client_protocol_sessions.go:193)–211：没有 typed 配置/host.configure 回执时仍调用 checkClientBinding；[runtime_sessions_windows.go:162](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/runtime_sessions_windows.go:162)–177 检查授权真实目录并由 sessionModel 验证当前绑定 profile、同 model ref 和 host route，故合法 frozen-runtime fixture 可以 create 成功。

[client_protocol.go:961](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/client_protocol.go:961)–965 在 session.send/既有 Session goal.start 的 handler 前调用 validateSessionConfiguration；[client_protocol_configuration.go:776](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/client_protocol_configuration.go:776)–791：typed 原配置通过 visibleClientConfiguration；legacy 必须由 ValidateLegacySession 验证，缺 port 返回 MODEL_UNAVAILABLE。

[runtime_sessions_windows.go:103](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/runtime_sessions_windows.go:103)–159：核对唯一创建主体，从 originalSessionTasks 提取 Task，核对 Task revision1 的 input_refs 与当前 Task 相同，使用 sealed Artifact 精确版本和唯一 trusted runtime binding，读取 exact hash 的 sealed profile，验证 backend、model ref、模型结构。没有原 Task 时最终拒绝。

[client_protocol_configuration.go:797](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/client_protocol_configuration.go:797)–824 仅取此主体/项目/Session 的 COMPLETED session.send 或 goal.start；831–853 验证原请求/身份回执；794–796 说明原 TASK_CHANGED 事件绑定 immutable Task，公共快照不含 task_id。真正 first send 尚无这样的 producer，因此出现循环。

从原 Task 取 profile 是现有历史兼容实现的防偷换证明方式，合同没有规定“永远只能从 Task 取”。要求不可削弱的是 original Session/command 与精确 frozen profile 的可验证关联；不能以当前 head、命名样式、同 ref 的新 runtime 或其他 Session 的 Task 代替历史 authority。

3. create 的保存内容能否安全派生首轮

[client_protocol_sessions.go:187](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/client_protocol_sessions.go:187) 保存 workspace/model 字符串、Session/native ID、writer/lease/core；170 返回普通 SessionSnapshot。[v24_sessions.go:101](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/v24_sessions.go:101)–110 不保存 Session 对应 RuntimeRegistration ID、ArtifactRef/profile_hash/provider route/credential revision 的冻结关联。

原创建回执和 request hash 可以证明创建主体、请求及 model ref：[client_protocol_configuration.go:701](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/client_protocol_configuration.go:701)–777 验证唯一创建、原请求/身份、配置历史及绑定 ref；它没有一个 legacy 创建时 profile_ref。

宿主确有独立的 sealed runtime profile：[runtime_qualification.go:74](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/runtime_qualification.go:74)–93/110–155 用 Owner 资格计划和 Task inputs 注册；173–214 验证 profile ref、technical identity、effective version 与 sealed bytes。独立冻结存在不等于证明它就是此 Session 创建时选中的 profile。

[0016_runtime_qualification.sql:2](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/migrations/sqlite/0016_runtime_qualification.sql:2)–8 的 binding 以 project/runtime 为键，保存 profile_ref/hash/technical_hash/owner，并禁止 UPDATE；未绑定 Session/creation command。公开 snapshot 只携带 model_config_ref（Schema856），故现有 public 返回与内部创建记录不足以安全派生 legacy first-turn 历史 proof。

4. 最小修复边界

正式 native fixture：先用真实公共 host.configure 和受控测试 ConfigurationAuthority 产生 typed ref，再以该 ref 构造并封存原 RuntimeProfile；同步 runtime ModelConfig、provider/model/endpoint、credential ref/revision、同 project/runtime/route，ClientService 与 RuntimeCoordinator 使用同一宿主配置 authority。保留原 physical TOOL/MODEL、权限、事件、回滚、费用、取消、独立接受断言。不能只添 authority 而继续用旧 ref，或手写 configuration/idempotency/Task 来制造来源。

生产兼容：现有 legacy 新建接受后 first-turn 必拒绝是确实存在的实现不一致，但缺少当前规范的额外 legacy 首轮承诺。本轮按 Root 决定不修生产；若以后明确支持它，须在创建同一事务内保存不可替换的 Session/creation command→精确 profile/runtime/provider identity provenance，并在首轮复核；或明确规定新建只接 typed ref、保留已有 legacy 的历史恢复。不能只在 originalTasks 为空时 return nil，也不能从当前 head 补造“创建时”proof。

这两个生产选项需要各自明确契约与回归范围，本报告未替 Root 选择或批准。typed fixture 修好后仍需 Root 真实执行和独立复核；本报告不证明 live 模型可用。

5. 不得削弱的检查

| 边界 | 实际出处与保持条件 |
|---|---|
| 身份与目录 | sessions54–61/129–146：当前 OWNER/项目授权、workspace 同主体/项目且 ACTIVE；runtime_sessions162–177：真实 path ConfirmPath。配置 owner/host 必须由受信 ConfigurationAuthority 产生，不让请求冒充。 |
| 原命令/版本 | configuration649–777、client_configuration170–251：原 creator、canonical request/scope/config hashes、唯一 command identity、COMPLETED 原 host.configure 回执、Session 原始与 scoped 配置 revision；不借别的 Session/head，忙时不静默换模型。 |
| 凭据与宿主 | configuration477–495/513–527：本机 host/principal 一致，credential 的同 ref/provider、API_KEY/OAUTH_TOKEN、AVAILABLE；MISSING/REVOKED 拒绝。host/client_configuration13–42 保持本机身份/HostInstance/principal 绑定，元数据不暴露或读取原值。 |
| provider/model route | runtime_sessions11–50/69–99：唯一同 project/runtime 模型；model/provider/api/endpoint 与 typed 原配置相等，route endpoint、credential ref/revision、ModelConfig hash 相同，无重复 Purpose，必须有匹配 MODEL route；configuration423–474 保留 HTTPS、无 userinfo/query/fragment/错误路径等 URL 限制。 |
| 冻结与派发 | runtime_model51–97：冻结 API/model/provider/ref/route、输出/call/tool 上限、bundle hash、资格 exact model hash；runtime_qualification173–214：精确有效 profile/technical identity/sealed bytes；runtime_sessions180–200 保留真实 currentRuntimeAdmission。创建不是资格、资源、provider 凭据可用或独立接受的替代证明。 |

6. Goal mock 与 lease 错误优先级

[client_protocol_goal_test.go:14](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/client_protocol_goal_test.go:14)–43：goalClientPort 只提供 ResolveGoalBinding/ValidateBinding/AdmitTurn，没有 ValidateLegacySession，也没有 host.configure typed provenance；合法创建后第二次请求在配置 gate 被拒绝，expired/missing lease 两支于309–310期待 LEASE_EXPIRED。

本例应补 fixture 的模型前置条件：优先 typed configure 路径；若仅保留隔离 unit mock，ValidateLegacySession 必须有明确作用域，核对 original creator/项目/Session/固定 model/workspace 与真实 fixture 创建回执，错误来源必须拒绝。不能给全局恒 nil verifier，不能把 mock 成功称为 native/model 接受。

[client_protocol_goal.go:304](D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2/internal/domain/client_protocol_goal.go:304)–309 是实际租约拒绝；外层 protocol961–965 的模型来源 gate 在其前。合同 §22:128/143–145 要求有效 writer/lease 与不双写，Schema1037/1057 和5680–5707/6280–6307分别允许 LEASE_EXPIRED 与 MODEL_UNAVAILABLE、要求 error_code=error.code；这些条件没有多错误优先级规定。

故本例不能证明 lease 优先级生产回归，也不能取消其 LEASE_EXPIRED 断言。恢复 valid model 前置条件后，应保持 expired/missing lease 的 typed 错误及 goals/tasks/runs 不增断言（test309–313）；本轮不重排生产 gate，不允许过期 lease 越过任何写入或派发。

7. 回执与限制

refs.json 给出本次精确 Main/T5/规范绝对路径、SHA256、bytes 与字节比较；tool-io.json 保存实际查询输入/返回。一次 Windows literal-wildcard rg os123 已由 Root 分配808，完整原返回保存在 failure-origin.808.json；outer exit0，出错 inner rg exit NULL，第二条独立成功 rg 保留，Python/product native NULL。原无效 wildcard 未重跑。

首个宽范围路径枚举只读完成 exit0，输出被工具截断，未用于猜私密路径或接受判断；随后只读取已列的 Source/规范和 Root 明确给出的 T5。报告不声称恢复工具未返回的截断内容。封存后 STOP，后续 Source 施工等待 Root 的新明确任务。

