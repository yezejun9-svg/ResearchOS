# Trusted qualification Host 独立源码审查

结论：**REQUEST_CHANGES**。四项阻断均针对原始 Source 的固定字节及其与冻结 observer v2 / runner v8 的组合。已确认 Host 使用真实 Main Service/HTTP/Coordinator 链路、Begin 与 RunAdmitted 分阶段、执行前保存本地 fence；这些正确做法不能关闭下面的输入和契约问题。

审查者为非作者 /root/w05_merge_review；审查范围是源码、JSON 模板和 Main 对应实现。未运行候选 Python、Go、gofmt、Host、CLI、native pipe、provider、DB 或 Job。Root 独立编译结果不属于本回执。29 个作者 manifest 引用均按 SHA-256/bytes 核对一致；额外 11 个当前实现/组合契约已逐字节快照。intake.json 为完整证据索引，raw-read-io.json 为原始读取输出；static-evidence-controls.json 只证明源码定位，不冒充动态复现。

## 🔴 R1 / P1：GO 证据校验与实际消费不是同一字节

位置：原 Source execute.go:111–118、121–131。

readGO 先循环 verifyPin 检查七个文件，再通过 verifyGOEvidence 调用 readPinnedObject；后者重新 os.ReadFile(p.Path)，直接 domain.Decode(raw)，没有将这次 raw 的 hash 和 bytes 与 p 比较。RootGrant、OnceMarker、OuterJobContract、HostJobProbe 的决策实际使用第二次读取。若文件在两次读之间替换，第一次通过的 pin 不约束实际用于批准执行的 JSON。

建议：单次读入 raw，验证 hash/bytes，随后从同一个 raw 解码，传递已验证对象；或者 readPinnedObject 自身完成完整 pin 验证并消费同一 raw。所有四个 GO 决策记录必须走此路径，不能仅增加一次更早的 preflight。

## 🔴 R2 / P1：prepare 会将 pin 校验后被替换的输入重新封存

位置：main.go:133–136；prepare.go:78–83、97。

readSeed 检查 profile、Node、bundle 的 seed digest 后丢弃读取字节；preparedProfile 再次 os.ReadFile 三个路径，未经 seed pin 验证便读取模型配置、生成 build_hash/bundle_hash 并封存。这会让替换后的输入被赋予新的“合法”profile hash。后续 Main staging 验证的是这份新 profile 的 hash，无法还原为原 seed 授权的字节。

建议：将已验证 raw 传到 prepare，或在 preparedProfile 读取 raw 后当场与 seed pin 匹配，再只消费该 raw。执行阶段 Node/bundle 的路径打开还需由 Main staging 的冻结 hash 绑定和 Root 文件生命周期约束；本发现具体针对 prepare 自行重新确立错误 hash 的窗口。

## 🔴 R3 / P1：Host 与 observer 的 Workspace 边界没有交集

位置：main.go:132；observer v2 mu_sdk_job_observer.v2.proposed.py:279–282。

Host 拒绝 workspace 位于 RepoRoot 或 DataRoot 下；冻结 observer 要求 DataRoot 位于 repo/.local 且 workspace 严格位于 DataRoot 内。任何满足 observer 的路径都会被 Host 拒绝，因而无法按现有组合进入准备/观察流程。

建议：Root 选择一个明确布局，更新必要组件并重新冻结。保留 canonical/non-reparse 验证、严格 evidence.txt 单文件目录、vault 隔离及只读工具边界。不能仅调整具体 seed 路径声称问题关闭。

## 🔴 R4 / P1：Host 封存的工具策略必被冻结 v8 拒绝

位置：prepare.go:107；runner v8 mu_sdk_trial.v8.proposed.py:931–935；Main internal/host/runtime_tools_windows.go:204 起 runtimeToolPaths。

Host 固定 max_calls=2、max_read_bytes=max_write_bytes=65536、write_paths=[]；v8 固定 1、4096 和 {}。该校验使用精确比较，因此准备出的 profile 不可能通过 v8。Host 字节上限和调用数也比试验边界更宽。

建议：Host 按已批准试验固定 1/4096，并让 read 工具 schema 的 maximum 同步为4096；write_paths 应保留 []，Main runtimeToolPaths 使用 []any 类型断言。Root 需把 v8 的 {} 修成 [] 并对新 runner 独立复审，不应把 Host 改为 {} 来迎合旧错误。

## 🟡 S1 / P2：prepare 的一次性存在性检查在租约之外

位置：prepare.go:20–27；hostapi.go:45；main.go:152–161。

两个调用可以都先看到 state 不存在，其中一个暂停，另一个完成并释放 lease；前者恢复取得 lease 后不重新检查，saveState 会替换已存在的状态，再创建一组重复对象。AcquireDataRootLease 只排除同时持有租约，没有消除检查到使用之间的延迟调度窗口。

建议：获得租约后再检查 state，并在同一租约内创建 PREPARE_CLAIMED。admit/execute 的 loadState 也应在租约内重新读取并核对阶段。此项为源码并发推理，未执行竞态复现。

## 已核对的 API 与语义

- Main domain.Object 为 map[string]any，domain.Num 返回 int64，domain.Hash/Bytes/Digest 的调用匹配源码；候选使用 Hash，未使用不存在的 JSONHash。
- ProvisionPrincipal、IssueCredential、RegisterRuntimeQualificationPlan、BeginRuntimeQualification 及 RuntimeCoordinatorConfig 字段/回调与当前 Main 定义相符。此为静态类型/签名比对，不能等同编译通过。
- NewCurrentMu 为明确构造策略，固定 MU_FORK；Begin 实际走 OWNER、已冻结 plan/task/profile、orchestrate SUBMIT、claimTaskMode、qualification bootstrap 和原生 PREPARED dispatch。claimTaskMode 仍检查 context、ACTIVE Goal、依赖、并发、attempt limit 等。所检查链路未发现“只设置环境变量就可以跳过”的构造开关。
- acceptance 请求中的 PASS 由 Main DETERMINISTIC_SERVICE 独立计算并覆盖，随后 Host 检查响应 PASS，调用实际 qualify API；未把请求自身当作实际成功。
- Host state ProfileHash 是 sealed artifact content_hash；v8 qualification_profile_hash 绑定 runtime_bindings/qualification marker 的 Hash(profile_ref)，两者含义不同。Root 构造实际输入时必须分别从对应真实对象读取，不能直接混用。
- 本地 IsProcessInJob 只证明 any Job；exact Root Job 祖先、Host/CLI/Mu 全树终止、总共最多3次 provider request 和完整300秒 deadline 仍依赖 Root 的独立执行控制。本 Source HANDOFF 已标为 OPEN，本审查不将 JSON probe 自述提升为现场证明。

## 修复验收

新 Source 必须新目录新 hashes；先核对 R1/R2 每个决策都消费同一被验证 raw，再核对 Host/observer/v8 的同一布局及1/4096/[] profile。S1 可用取得 lease 后的状态检查关闭。完成源码复审和 Root 独立编译之后，仍需实际 native/Job/provider 证据才可讨论运行资格。

本回执不授权 Main merge、不授权 provider 调用、不改变产品/资格状态。原 Source 和 Main 未修改。

