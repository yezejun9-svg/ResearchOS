# Security Audit Report — STOP-anchor 独立设计审查

## Summary

结论：**接受两阶段专用 compiled grant 的设计方向，但原三文件不能不加补充直接作为 Source 卡。Root Source 卡纳入本报告 SA-D01 至 SA-D05 后，可开始有限修复；不需要重复广域架构审查。** 这是一份设计审查，未接受 Source、夹具、实际 STOP 或正式用例。

- Critical: 0
- High: 0
- Medium: 5（设计约束缺口，不声称已证明当前 Source 可被利用）
- Low: 0
- 原 19 路径足够；无需新密钥、注册表、用户确认流程或 proof class。
- scope SHA256：`4e6df8550087d4fdf0ae8294ecba3a0a7d788e132a5316409b05af4421ed5802`。6 个冻结 input_refs 的 SHA256 与字节数全部匹配。
- F01 / 旧 verifier native closure 仍为 NOT_PROVABLE；实际 STOP 仍为 UNAVAILABLE；formal_increment=0。

## 信任边界与 STRIDE

| 边界 | STRIDE 推导 | 本次结论 |
| --- | --- | --- |
| caller CLI/JSON → compiled authority | Spoofing / Elevation：caller 修改计划与 hash 不能取得权限 | 非空私有编译 grant 和 action 枚举方向正确；入口及混合参数须落实 SA-D03 |
| 预检产物 → 人工独立 review → STOP grant | Tampering / Repudiation：哈希完整性不能替代独立批准 | 不引新 signer；Root/独立 reviewer 先审实有产物，再构建 STOP；SA-D01 必须无环 |
| 文件路径 → native handles / 所读字节 | Tampering / Spoofing：path 检查后替换、同文件原位修改 | retain handle 本身不禁止写入；须落实 SA-D04 |
| 两个 phase/binary → 同一 operation journal | Repudiation / Elevation / Denial：重复 signal、并发和错误 phase transition | 永久消费方向正确；需 SA-D02 明确唯一合法接续 |
| grant 时间 → lock/backup/barrier/signal | Elevation / Denial：等待后过期仍 signal、失败后重试 | 30 分钟 wall + 单次 monotonic 方向正确；需 SA-D05 闭合 intent 后间隙 |
| 公共证据 → DB/Core/Owner/Host/parent | Spoofing / Information disclosure | 全元组和语义核验保留；不读私钥/pipe/model，grant 不能代替事实证明 |

同 SID Owner/operator 可重编任意程序不在本机制提供密码学隔离的承诺内。该声明明确且必要；“独立 review”指独立流程证据，不意味着受保护留出环境。OWASP 关联集中于访问控制、完整性、身份与审计；此有限设计不处理 LLM 运行路径，不新增 LLM 风险判断。没有依赖变更或版本清单审查，因此无 CVE 清洁声明。

## Findings 与 Source 卡强制 addendum

### [MEDIUM] SA-D01 无环字节谱系和先存在的操作目录

- **Location:** `STOP-anchor-addendum.md:14,26,30,38; STOP-anchor-exact-scope.json:4`（均为冻结设计文件）。
- **Description / Impact:** L38 让 plan 同时绑定 grant digest 和 final plan SHA；若指 STOP grant 或 plan 自身哈希，就与 L30 的 STOP→plan 约束循环。目录/未来文件 identity 若等待预检才产生，也无法事先编译。scope 的 accepted base 文案还会阻止修复待接受基线。
- **Recommendation（纳入 Source 卡）：**

1. Root Source card may select its frozen 56e44e1b candidate without implying it is accepted. Repair must not wait for acceptance of the defect being repaired. Final whole Source acceptance remains mandatory before actual use.
2. Prepare an empty private non-reparse operation directory in the separately authorized preparation scope BEFORE materializing PREFLIGHT_ONLY grant. Pin its existing canonical native volume/file ID and SID/ACL. Source fixtures do this only for new owned fixtures. Grant-aware command never creates its own pinned operation directory.
3. Use an acyclic DAG: existing proposal/scope/review/historical documents -> PREFLIGHT grant -> preflight binary/external build receipt -> generated plan and backup artifacts -> preflight manifest -> stop review/scope -> STOP grant -> STOP binary/external build receipt. References point only backward. Scope/review identify exact subject/action and already-existing artifact digests, not hashes of future grant/binary.
4. Final plan may include predecessor PREFLIGHT grant/binary digests, but NOT its own SHA or successor STOP grant/binary digest. Manifest pins plan/member byte hashes and measured postcreation identities, but not its own hash. STOP BEGIN/INTENT pin successor grant and final plan; external detached receipts bind executable output. The phrase in L38 requiring plan to bind both hashes is replaced by this directional rule.
5. Proposal pins future output canonical names and creation constraints, not nonexistent future native file identities. Once files exist, plan/manifest and STOP grant freeze the required identities. No self-member in manifests and no recursive final-manifest members.

- **必要验证：** SA12: build both real grants without placeholders or post-build patching; assert full dependency graph acyclic; SA13: missing/recreated/swapped pinned directory and output alias/reparse rejected; final-output identities are measured only after creation

### [MEDIUM] SA-D02 阶段接续与永久消费属于同一个 operation

- **Location:** `STOP-anchor-addendum.md:12,38,40; STOP-anchor-test-cuts.json:11-12`（均为冻结设计文件）。
- **Description / Impact:** L38 一律拒绝不同 grant 指向同一 journal，会误拒绝正常两阶段接续；如果实现者为修复该问题放宽 grant mismatch，又可能重置已经消费的操作。需要唯一明确的单向 phase transition。
- **Recommendation（纳入 Source 卡）：**

1. Specify immutable preflight-complete record plus one shared operation lock and durable STOP attempt/intent state under the same pinned directory. STOP accepts exactly the predecessor grant/binary/manifest compiled into it. This single forward transition is the sole exception to different-grant conflict; arbitrary replacement STOP grants remain conflicts.
2. Do not rewrite predecessor records. PREFLIGHT replay may only observe its frozen completed output; it cannot overwrite/refresh backup or plan. At any STOP attempt/intent state, PREFLIGHT must not reset the operation.
3. Create/claim durable attempt state atomically under the exclusive operation lock and use create-new/nontruncating writes with explicit flush failures handled as UNKNOWN/consumed. Existing intent permanently consumes the operation across all binaries/grants. BEGIN-only, torn, missing-required state or uncertain durability must fail closed; no automatic delete/repair/rebuild retry.
4. Completed commit replay only reads the immutable outcome; inspect never repairs or creates state. Distinguish a fresh, structurally valid preflight-complete state from an invalid/missing commit state. Do not claim resistance to malicious same-SID rollback/deletion beyond the declared operator trust boundary.

- **必要验证：** SA14: legitimate predecessor→successor succeeds; third grant/same-op substitution, preflight rerun and concurrent phases fail to reset state; extend SA06/SA07: crashes before/after claim, BEGIN, intent flush and native call; torn/missing-required journal cannot enable a second call

### [MEDIUM] SA-D03 入口先验证授权，过期 inspect 独立只读

- **Location:** `STOP-anchor-addendum.md:20,22,36; STOP-anchor-test-cuts.json:6,8,15`（均为冻结设计文件）。
- **Description / Impact:** 全局 loader 拒绝 expired 与 expired inspect 的例外存在实现歧义；CLI 组合 action/flags 和过早构造副作用尚未显式约束。错误实现会把只读 inspect 或 malformed route 引向有副作用路径。
- **Recommendation（纳入 Source 卡）：**

1. Strictly parse exactly one command/action and an action-specific flag set. Reject mixed action flags, duplicate flags, conflicting positional actions and unexpected arguments before filesystem/DB/process/journal side effects. Resolve proposal-vs-plan expected SHA by grant kind; preflight cannot be forced to supply a nonexistent final plan hash.
2. Entrypoints first perform pure argument parsing and compiled-grant schema/canonical validation/action selection. No constructor, route setup or error-output setup may open DB, process handles, backup or output journal before this gate. Package init must not perform these actions.
3. Separate grant structural validation (including interval ordering and <=30 minutes) from live freshness. Expired inspect accepts only structurally valid grants and reads existing matching immutable receipts with no target-process/DB/backup probes or new lock/journal creation. Filesystem read handles needed to read receipts are allowed; no interpretation that bans filesystem access itself.
4. Inspect for either phase reads only its existing authorized receipt subset. If a writer currently owns the operation or no immutable outcome exists, return bounded unavailable/in-progress without mutation.

- **必要验证：** extend SA01/SA03/SA10: malformed and cross-phase mixed CLI arguments show zero side-effect counters; expired inspect is DB/process-free and writes zero files

### [MEDIUM] SA-D04 同一文件句柄读取、拒绝写入替换，闭合 TOCTOU

- **Location:** `STOP-anchor-addendum.md:26,32,38,40; STOP-anchor-test-cuts.json:9,13`（均为冻结设计文件）。
- **Description / Impact:** non-reparse retained handle + byte hash 尚未规定拒写/拒删 sharing，也没有明确 hash 与 decode 必须来自相同 buffer。若允许原位修改或按 path 重开，可在批准字节与实际解析内容间制造差异；当前 Source 是否存在该漏洞未审查。
- **Recommendation（纳入 Source 卡）：**

1. Do not merely retain a handle after hashing by path. Open every authority document/manifest member through validated non-reparse ancestry and a handle whose sharing denies write/delete for its required lifetime (or an equally strong proved native primitive). Reject writable sharing conflicts/hardlink aliases where identity constraints require distinct artifacts.
2. Hash and strict-decode the same bounded byte buffer read from that handle; verify file identity/size/canonical root and do not reopen by name for semantics or action. Retain directory/image/authority handles across waits/barrier/native action as applicable. Validate ancestor identity, ACL and same-owner rules without a check-then-open path race.
3. Pin and compare exact Core and parent process creation identities, parent canonical executable path/native file identity+hash, current SID/Owner principal/root, Host public identity/hash, DB/root identity and full old-window tuple. A matching hash alone does not accept a semantically different document or silently choose another proof class.
4. The Windows implementation must use existing allowed wrappers/files; if any needed primitive cannot be implemented there, stop that branch and request a narrow explicit scope amendment rather than silently reopening by path.

- **必要验证：** SA15: mutate/replace authority file, directory ancestor and parent image between hash/decode/action; write-sharing or identity mismatch denies before action; extend SA04/SA08: hash-matching semantically wrong acceptance/subject and Host/Owner/parent mismatches rejected

### [MEDIUM] SA-D05 有效期覆盖最终 signal 边界且不恢复已消费权限

- **Location:** `STOP-anchor-addendum.md:36,40; STOP-anchor-test-cuts.json:10-12`（均为冻结设计文件）。
- **Description / Impact:** 只在 intent 前检查有效期，intent 持久化与 native call 间仍可过期。必须明确此时零 signal 但权限已消费，并对等待/后验收尾给出有限边界。
- **Recommendation（纳入 Source 卡）：**

1. Compute invocation monotonic deadline from the initial remaining wall-clock validity and never extend it on revalidation. Enforce wall AND monotonic conditions after waits and immediately before intent and native call; no unbounded lock/backup wait may outrun the budget.
2. If expiry/cancellation occurs after durable intent but before TerminateProcess, perform zero native calls and retain consumed state with explicit zero-signal/unknown outcome as evidence permits. It is not refundable and cannot authorize a later retry.
3. After one native call, expiry allows only bounded wait/postflight/error recording under a separately finite completion bound, no new preflight/backup/stop. Preserve UNKNOWN or MAINTENANCE_BLOCKED when outcome/lease/baseline cannot be proved.
4. Cross-invocation clock rollback resistance is not newly claimed; the selected design guarantees the stated <=30-minute wall interval plus monotonic bound within each invocation, under the declared trusted OS/operator clock assumption.

- **必要验证：** extend SA05/SA06: expiry between intent flush and native call yields zero signal and consumed operation; expiry after signal still cannot retry; long waits honor finite cancellation/deadlines


这些条款不增加授权类型，不要求重做原生闭合证明，也不认可 NEVER_JOB_AUTHORIZED。Root 可以在已经冻结、尚未接受的 `56e44e1b` 上修 anchor；完整最终 Source 接受仍须在 actual 前完成，不能把修复前必须接受缺陷基线设成循环前置条件。

## 精确路径与验证门槛

主要生产改动限于：
`internal/ownedcorestop/{contract.go,proof_windows.go,stop_windows.go,journal_windows.go}`、
`ops/owned_core_stop/{main_windows.go,main_nonwindows.go}`。
对应既有 proof/stop/journal/main Windows tests 与 `ops/owned_core_stop/fixture/main_windows.go` 承载测试。
若保留父目录/父进程/镜像句柄原语需要改动，原 19 中的
`ops/supervisor/owned_core_handle_windows.go`、
`internal/host/owned_core_stop_identity_windows.go` 及对应 tests 已在总范围内；Source 卡应显式列入实际需要的子集。本报告判断原 19 的设计容量足够，不声称已验证具体实现。

必须由两个真实、非空 `-ldflags -X` grant binary 经生产 CLI 跑完隔离 disposable fixture 的 preflight → actual online backup/census/plan → 冻结 synthetic review/scope → STOP commit → 一次真实 TerminateProcess → 原句柄 wait → DataRootLease/postflight → immutable inspect。测试中给全局变量赋值、空 grant 全拒绝、纯 JSON 断言均不替代该正向链。SA01–SA11 保留，增加/细化 SA12–SA15 与上述断点；S209/S216 通过 grant 路径复验。实现者报告 PASS 不能替代独立 Source 接受。

## Positive Observations

- runtime caller 的 hash、环境和 flag 不被当作批准；默认空 grant 在副作用前拒绝。
- 两个专用编译产物、先真实预检后独立 review，解决“先批准未来 plan”的根本依赖问题。
- SID/Owner/Host/data root/DB/Core/parent/旧任务元组和 proof class 共同绑定；完整语义与证据成员核验明确。
- 单 intent 永久消费、原目标句柄 signal/wait、不得按 PID 重开、不自动重试和保留 UNKNOWN 的方向正确。
- Source fixture、actual operation 与正式接受明确分开；旧失败证据未被默认拒绝测试覆盖。

## Evidence and Limits

只读取了项目 AGENTS、精确 scope、3 个 anchor 文件、此前独立审查 manifest/prerequisites 和原19路径 Source scope。没有读取或运行 Source、构建、测试、当前 DB/Core/model/GUI/私有 pipe/key/backup，也没有改 shared state。此前 manifest 只用于确认保留结论，未重跑其中测试或重审 callgraph。

命令 recipe、raw 和 native exit 见本目录 `001-*` 至 `004-*`。初始化 discovery 首次执行早于证据目录创建，已逐字重放留 raw 与 exit；此捕获时序缺口明确记录在 review.json 的 D01，未宣称预先捕获。所有实际读取/hash 命令 exit=0。Root 后续更正的可选 Source index 哈希不在6个强制输入中，本次未读取/依赖该 index，相关文本转写错误仅记录为 D02。

冻结由 `freeze.ps1` 重新核对6输入与路径子集，产生 `FINAL-manifest.json` 和 `FINAL-SHA256.txt`。manifest 不包含自身、detached hash 与执行结束后才产生的 tool-result envelope，以避免证据自身哈希循环。

<oai-mem-citation>
<citation_entries>
MEMORY.md:33-34|note=[fixture source and formal acceptance separation checked against current scope]
</citation_entries>
<rollout_ids>
01a11007-5233-7ca1-b71f-9e9e5ce84c98
</rollout_ids>
</oai-mem-citation>

