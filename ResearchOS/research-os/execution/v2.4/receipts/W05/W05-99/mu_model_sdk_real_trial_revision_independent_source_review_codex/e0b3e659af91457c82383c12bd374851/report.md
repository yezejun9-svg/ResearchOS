## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** SDK v2 完整正反差异与封存哈希成立。R01–R04 均有具体改进，但仍有四项必须修复的 Source 缺口，不能把缺真实 Root producer 与这些代码缺陷混为一谈。

### Critical Issues

- 未确认 Critical 项。

### Important Issues

- **R01-v2**：The real Root grant still does not bind the executable and full phase input。D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029/mu_sdk_trial.v2.proposed.py，行 119, 164, 336, 350, 403, 414, 668, 707。Registration/review/grant compare only selected fields. cli_binary, discovery_file, cli_config_file, outcome_dir, prompt, goal_objective, workspace_witness, project_id, goal_id, config_revision, cancel/bootstrap evidence and qualification_owner_root are absent from authority_binding. cli_binary is only hash-verified against its replaceable input ref, so another hash-valid executable/config path can run under the same real registration/grant/checkpoint. Exact input raw/hash and actual command/env are not bound. Claimed authority is substantially stronger than v1, but its important omissions remain a code gap rather than only a missing producer. 修复：Define a closed finite phase projection that fixes every consumed input field, executable ref, exact argv/cwd/environment and canonical roots. Bind its raw/hash or complete deterministic projection in the real Root registration, nonauthor review and grant; recompare before consuming the one-time marker or any DB/output/product effect. Keep mutable Root checkpoint as the current authority and preserve the current single-use/deadline guards. Avoid a whole-input hash cycle: registration/grant refs are excluded from a separate immutable input basis, then explicitly bound. Reject changed executable/config/discovery/Goal/prompt/witness/evidence/root and replay/foreign phase; NULL stays OPEN.

- **R02-v2**：A genuine qualification cannot pass the actual EntityRef and approval ABI。D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029/mu_sdk_trial.v2.proposed.py，行 541, 552。domain.Ref (internal/domain/contracts.go:141) emits entity_type,id,revision,content_hash. Candidate line544 checks approval.receipt_ref.entity_id against Task.acceptance_id and line546 reads profile_ref['entity_id']; neither field exists in the real EntityRef. runtime_admission.go:247 stores b.receipt_artifact_ref (Artifact) in approval.receipt_ref, while Task.acceptance_id names an AcceptanceReceipt. Thus genuine approved qualifications are rejected at544 and wait_qualification loops until deadline; replacing entity_id with id alone would retain the Artifact-vs-AcceptanceReceipt mismatch. 修复：Use the existing EntityRef ABI id throughout. Verify approval.run and qualification_hash against the selected run and exact runtime.qualification_ids/Task.acceptance_id. Treat approval.receipt_ref as the sealed runtime observation/log Artifact: verify its entity/version/content hash/bytes and the appropriate run/profile observation relation using the real runtimeReceipt contract. Keep the independent AcceptanceReceipt as a separate subject/run/contract/inputs/executor/validity link. Preserve project+run effects, one-to-one MODEL UNKNOWN ledger and complete SSE checks; do not make the producer fabricate the wrong EntityRef shape or artifact type.

- **R03-v2**：A later raw-evidence hash error can replace an already-known child failure as first cause。D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029/mu_sdk_trial.v2.proposed.py，行 465, 503。actual_exit is captured at465, but nonzero exit becomes first_cause only at489, after raw pinning478-484. If a child exits nonzero and pin_path then fails, secondary is nonempty, the parsing/nonzero branch486 is skipped, and497 assigns the later secondary as first_cause. The actual exit remains present, but the promised earliest cause is misclassified. 修复：Freeze a known nonzero child exit as first_cause immediately when it is observed, before raw hash/parse/receipt IO. Append later evidence/cleanup errors only as secondary. Preserve nullable status when no process/terminal status exists. Keep both pre-Popen deadline/reserve checks, single Root absolute deadline and no retry. Actual Root Job hard stop and outer evidence reserves remain OPEN until the real producer/independent lifecycle closure exists.

- **R04-v2**：The actual new host leaf is not checked before mkdir/private ACL work。D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029/internal_host_host.v2.proposed.go；D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029/internal_host_vault.v2.proposed.go；D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029/apps_control_main.v2.proposed.go，行 {"host":[111,138],"vault":[113,151],"control":[64,86]}。Host.New passes only filepath.Dir(cfg.Dir) into ValidateTrialVaultIsolation and checks filepath.Base(cfg.Dir)=='host'. The helper checks dataRoot and oldHostDir/parent, not cfg.Dir. With canonical disjoint data roots and a preexisting new dataRoot/host junction to the old Host directory, the guard can pass and os.MkdirAll/privateDir(cfg.Dir) at135-138 follows the child alias and touches the old protected Host. Moving the parent guard before lease/Open fixed the original ordering, but does not close the descendant alias. 修复：Before any Host mkdir/privateDir/domain setup, validate the exact cfg.Dir path and every existing ancestor/leaf against reparse/alias and the frozen new root. Allow the legitimate absent new host leaf under a verified ordinary parent; if present it must be an ordinary canonical directory with disjoint identity. Apply equivalent checks to the Control DB/host paths before mutable initialization so root isolation cannot be defeated by an existing child. Preserve the early partial-tuple rejection and original nontrial path. Verify actual Windows behavior separately; do not claim EvalSymlinks/SameFile name checks alone reject every future reparse tag.

### Suggestions

- 只修上列具体缺口，保留 v2 原封存，在新 namespace 构造候选并交非作者复核。

### What's Done Well

- 27 个 Source 成员、6 个原 basis REF 实际 SHA/bytes 全部一致；四份完整 Go 正反 diff 与 Python 整份正反 diff 独立核验成立。
- 金额资格候选与上一轮同 SHA，UNLIMITED cap-null/UNKNOWN 与 CAPPED 正金额 reserve 路径保持。
- 早期隔离排序、项目内 effect 查询、MODEL UNKNOWN 对应以及两次 Popen 前绝对 deadline 检查均有具体改进。

### Verification Story

- Tests reviewed: yes。实读作者 precheck 源码和七个负控记录；本审没有运行这些候选函数。假授权反例只在 DENY 早退，资格 mock 只覆盖旧 marker，未覆盖真实正向 ABI。
- Build verified: no。Python AST 与源码字节 diff 已核；Go AST/compile/build/gofmt、Windows 和 SDK 均 NOT_RUN。
- Security checked: yes。公开源码边界已审；Root producer/Job/probe/lifecycle/实际资格仍 OPEN。未读取或解封凭据。
- 本轮新增工具失败 0；三个继承作者 origin 已核且不重计。
- candidate/CLI/SDK/provider/canonical 0；Source/42formal 接受增量 0。

具体反例、最小修复、下一独立审查和实际资格门见 review.json。本轮结束 STOPPED。
