$ErrorActionPreference='Stop'
$E='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat'
$review=@'
{
  "schema": "researchos.qualification-failure-B-independent-source-review-result.v1",
  "status": "NEEDS_CHANGES",
  "candidate": "75e5257c19b2e21e6cabd5e912e2ac6a3e2fe603",
  "tree": "ba3f9d4c101df39ab17856158d5fc72a9f0600ce",
  "base": "f48fca0e4013bda19913a34d91da0cd23157a08b",
  "scope_sha256": "17ed51fb0d7eaa837afc4d4826b72f315fa2c3b305d67af6eb802a0c9ca14331",
  "owner": "codex:/root/qualification_failure_b_review",
  "model_configuration": {
    "model": "gpt-6-astra",
    "reasoning_effort": "high",
    "source": "delegation and frozen scope; no runtime introspection"
  },
  "formal_increment": 0,
  "actual_model_calls": 0,
  "external_provider_calls": 0,
  "production_data_or_process_actions": 0,
  "source_edits": 0,
  "git_writes": 0,
  "source_acceptance": false,
  "main_acceptance": false,
  "package_acceptance": false,
  "actual_acceptance": false,
  "formal_acceptance": false,
  "findings": [
    {
      "id": "B-F01",
      "priority": "P1",
      "title": "Protected DACL with Everyone full access is accepted",
      "path": "adapters/runtime/qualification_failure_proof_windows.go",
      "lines": [
        47,
        53
      ],
      "evidence": "r09-focused-tests.raw.txt; TestIndependentQualificationProtectedWorldWritableDirectoryRejected FAIL; Go native exit 1; reconfirmed r20.go.stdout.raw with separate native output",
      "detail": "Own fresh temp directory received PrivateDirectory then icacls /grant *S-1-1-0:(OI)(CI)F. Native icacls succeeded and displayed Everyone and current user full access. PersistQualificationRejection returned nil and created receipt. D:P plus current SID presence is insufficient privacy. The reader uses the same predicate.",
      "fix": "Enumerate native DACL ACEs and reject untrusted write/delete/WRITE_DAC/WRITE_OWNER grants; validate actual owner and allow only explicitly intended trusted principals. Validate source-file ACL/reparse/file identities as well as directories, retain native no-delete/rename identity handles across checking/opening/flushing/reading rather than repeated pathname checks. Reject unsafe inputs without creating a receipt; do not repair an externally permissive directory to make the check pass.",
      "minimal_paths": [
        "adapters/runtime/qualification_failure_proof_windows.go",
        "adapters/runtime/qualification_failure_proof_windows_test.go"
      ],
      "limits": "Independent fixture shows privacy predicate failure, not a production exploit or current user data mutation. Same-SID independent agent is not protected holdout."
    },
    {
      "id": "B-F02",
      "priority": "P1",
      "title": "Existing ordinary queue/cancel/recovery tests were deleted",
      "path": "internal/domain/runtime_command_queue_windows_test.go",
      "lines": [
        5,
        63
      ],
      "base_lines": [
        22,
        356
      ],
      "evidence": "full-candidate-diff.patch and r11-followup-reads.raw.txt; numstat 42 added / 333 deleted in this file",
      "detail": "Candidate replaces the pre-existing ordinary Mu queue test suite and helper with registry tests. Removed TestRuntimeClientQueueActualMuSameProcess, TestRuntimeClientQueueActualMuCancelUnknownEffect, TestRuntimeClientQueueGoalCancelClaimOrdering and testRuntimeClientQueueActual, including same-process delivery, unknown cancellation, claim ordering and exact-original recovery checks.",
      "fix": "Restore all pre-existing base-f48 content and helper behavior, then append the new registry tests. Do not delete, Skip or weaken old failures to make B appear green. Preserve known historical ordinary-Mu limitations separately and use local frozen fixtures for any authorized focused regression.",
      "minimal_paths": [
        "internal/domain/runtime_command_queue_windows_test.go"
      ]
    },
    {
      "id": "B-F03",
      "priority": "P1",
      "title": "Private consumer does not bind confirmed MODEL request and receipt to sealed proof",
      "path": "internal/domain/runtime_qualification_failure_windows.go",
      "lines": [
        792,
        795
      ],
      "additional_lines": [
        340,
        341,
        443,
        450
      ],
      "evidence": "r15-private-tamper-tests.raw.txt; TestIndependentQualificationPrivateConsumerModelReceiptTamper FAIL; Go native exit 1; reconfirmed r20.go.stdout.raw with separate native output",
      "detail": "After a real owned loopback first-gate closure, baseline validatedQualificationFailureTx succeeds. In a rolled-back owned fixture transaction, disable resource_effects append-only triggers and change exactly one CONFIRMED row receipt.receipt_id to sha256:forged-independent. Sealed proof, marker and observation remain unchanged; the actual private consumer still returns a closure. It currently checks only CONFIRMED plus nonnil receipt. This is proof validation of corrupted source data, not a claim production exposes arbitrary SQL.",
      "fix": "At initial verification bind the exact MODEL effect project/run/epoch/key, sequence/history and canonical request body/request_hash, route/capability/credential revision, canonical receipt and receipt_id/provider_response_hash to the exact acknowledged frame2 and durable host MODEL fact/response bytes. Persist those immutable digests in sealed proof and marker-bound plan. Recompute them from stored resource_effects and original durable fact at the private consumer, and reject changed request, receipt, key/subject/epoch/route/history. Define canonical Hash(Bytes-decoded Object) versus raw Digest explicitly: frame payload/raw source retain raw digests, stored canonical objects use one canonical algorithm; never hash only state or receipt existence. Add independent request and receipt tamper controls while proof/marker stay fixed.",
      "minimal_paths": [
        "internal/domain/runtime_qualification_failure_windows.go",
        "internal/domain/runtime_qualification_failure_windows_test.go"
      ],
      "limits": "Only receipt_id corruption was independently executed here; request replacement is a static omission and required companion test."
    }
  ],
  "coverage": {
    "B01": "Fresh controlled native loopback PASS, raw3 ACK2/rejected1, one local MODEL request and derived FAILED closure. Not actual Mu bundle or external model proof.",
    "B02": "Refusal matrix executed but relevant later guard claims need valid seed positive control; wrong task/lease/technical/marker-field permutations not exhaustive.",
    "B03": "Known-route positive, generic unknown-route/malformed-tool/second-model negatives PASS. No complete malformed wire byte suite.",
    "B04": "First constructor is only before first providerRoute/prepareEffectTx, under dispatchGate resourceWriteLock. Existing negative seed arguments=Empty() ([]any) is invalid for validateRuntimeToolArguments, so later effect/ledger guards are not independently isolated; PREPARED only rather than all requested historical stages. Existing purpose_expired_after_prepare generic regression PASS.",
    "B05": "Existing create-new, ordinary permissive directory, reparse ancestor and conflicting receipt tests PASS; protected Everyone DACL independently FAIL. Write/flush fault, per-file source identity and racing ancestor/receipt replacement not proven.",
    "B06": "Blocked MODEL overlap generic UNKNOWN test PASS; registry unit pending/late completion tests PASS. Production post-denial suffix, late auxiliary/model observation and bounded drain timeout not separately fault-injected.",
    "B07": "Registry duplicate/missing/unadmitted guards and native blocked MODEL scenario PASS. Exact goroutine-lifetime proof reviewed statically; no protected holdout.",
    "B08": "Raw stdout/stderr/bridge changes refused; stopped/drained/cleanup/output predicates read. Missing each field and identity replacement not individually injected.",
    "B09": "Four existing coordinator tests plus two subtests PASS. Entire ordinary queue/cancel/claim/recovery test suite deleted (B-F02); no complete ordinary Mu session acceptance.",
    "B10": "16 precommit trigger cuts PASS; exact claimed all-writer coverage absent: ImpactLink domain_objects and domain_refs writers not independently injected; commit failure not injected. Positive test checks selected counts, not full five-version/all-table unchanged census. Its duplicate test invokes RunAdmitted and observes terminal refusal; it does not exercise closeOnlineQualificationFailure completed-marker replay branches.",
    "B11": "First cause and frozen-plan heartbeat race PASS; coordinator cancels and joins heartbeat before closure CAS. Secondary native facts retained; no universal cancellation/join theorem.",
    "B12": "Existing 8 tamper cuts PASS; independent actual current Owner-root revocation PASS with distinct scheduler still unrevoked. Independent MODEL receipt corruption FAIL (B-F03). Request corruption and current grant/lineage mutation cuts remain."
  },
  "input_audit": {
    "frozen_refs": 13,
    "matched": 13,
    "author_source_files": 9,
    "source_matches": 9,
    "author_command_records": 110,
    "recipe_stdout_stderr_hash_mismatches": 0
  },
  "tests": [
    {
      "id": "r09-focused-tests",
      "native_exit": 1,
      "pass_nodes": 56,
      "fail_nodes": 1,
      "skip_nodes": 0,
      "domain": "PASS",
      "adapter": "FAIL independent unsafe DACL expectation"
    },
    {
      "id": "r15-private-tamper-tests",
      "native_exit": 1,
      "pass_nodes": 0,
      "fail_nodes": 1,
      "skip_nodes": 0
    },
    {
      "id": "r16-existing-regression",
      "native_exit": 0,
      "pass_nodes": 6,
      "fail_nodes": 0,
      "skip_nodes": 0
    },
    {
      "id": "r20-independent-native-capture",
      "native_exit": 1,
      "pass_nodes": 1,
      "fail_nodes": 2,
      "skip_nodes": 0,
      "capture": "Separate native Go stdout/stderr byte redirection, bounded repeat for evidence quality",
      "purpose": "Reconfirmed ACL and MODEL receipt failures; true current Owner-root revocation rejection remains PASS."
    }
  ],
  "minimal_repair_paths": [
    "adapters/runtime/qualification_failure_proof_windows.go",
    "adapters/runtime/qualification_failure_proof_windows_test.go",
    "internal/domain/runtime_command_queue_windows_test.go",
    "internal/domain/runtime_qualification_failure_windows.go",
    "internal/domain/runtime_qualification_failure_windows_test.go"
  ],
  "historical_incident": "Author b91 auto-GC/repack deviation retained. Root selected input/object/header availability check is not missing-history restoration; historical missing62 remains outside this review.",
  "limitations": [
    "Tests are owned local Windows/native loopback fixtures, not actual current product root or external model qualification.",
    "Same-user independent namespace does not provide protected holdout.",
    "All formal and parent acceptance remains open.",
    "Read recipes capture merged PowerShell text stdout/stderr; exact original separate native streams are not asserted for review commands. Explicit go-native-exit files, not wrapper exit0, are authoritative.",
    "Earlier review command logs are full merged PowerShell text captures, not original separate streams. r20 captures separate native Go stdout/stderr bytes for all three independent cuts; explicit go-native-exit files are authoritative, wrapper exit0 is not test PASS."
  ]
}
'@
$md=@'
# CP517 B 独立 Source 审查：NEEDS_CHANGES

候选 `75e5257c19b2e21e6cabd5e912e2ac6a3e2fe603`，tree `ba3f9d4c101df39ab17856158d5fc72a9f0600ce`，base `f48fca0e4013bda19913a34d91da0cd23157a08b`。当前不能接受 B Source；不授予 Main、安装包、actual 或正式验收。formal_increment=0，外部模型调用0。审查仅写本次 own evidence/temp，未改候选源码或实际产品数据/进程。

## 三项必须修复的问题

### B-F01 / P1：受保护 DACL 中含 Everyone 全权限仍被当作私有目录

位置：`adapters/runtime/qualification_failure_proof_windows.go:47-53`。真实 Windows 夹具先调用 PrivateDirectory，再用 icacls 给 Everyone 增加继承 Full Control，保留当前 SID 和保护标志。读取实际 ACL 后调用 PersistQualificationRejection，函数返回 nil 并写回执。独立拒绝断言失败，r09 和独立原生字节采集 r20 均复现。

当前谓词仅找 D:P 与当前 SID，不能证明私有。应按原生 ACE/owner 校验明确允许主体，拒绝其他主体的写、删除、改 DACL/owner 权限；同时覆盖读取端、源文件 ACL/reparse/身份，并以保留的原生文件/目录身份句柄消除路径检查到使用的间隙。当前仅反复 EvalSymlinks/Stat/Open，没有持续身份 guard；竞态本身本轮未动态利用，不声称已证明一次生产攻击。

最小路径：该生产文件及其 qualification_failure_proof_windows_test.go。不得通过修改外部目录权限来使其被接受。

### B-F02 / P1：原普通队列回归测试被整体替换

位置：当前 `internal/domain/runtime_command_queue_windows_test.go:5-63`；base-f48 测试入口第22、23、26行，helper 延续到文件结尾。完整 diff 该文件新增42行、删除333行，原约356行变成65行。删除了 TestRuntimeClientQueueActualMuSameProcess、TestRuntimeClientQueueActualMuCancelUnknownEffect、TestRuntimeClientQueueGoalCancelClaimOrdering 与 testRuntimeClientQueueActual，丢失同进程队列、UNKNOWN取消、claim顺序、原身份恢复与重放等既有断言。

应完整恢复 base 的原测试与 helper，再追加 registry 测试；不能删除、Skip 或弱化旧失败。本轮没有重跑无关历史普通 Mu 全套，既有历史失败仍是独立限制，不能据测试缺席宣布通过。最小路径仅该测试文件。

### B-F03 / P1：真实 private consumer 没有绑定 MODEL 请求与回执内容

位置：`internal/domain/runtime_qualification_failure_windows.go:792-795`，相关初始验证443-450和proof构造340-341。真实本地 B01 首门闭合后，未修改基线能通过 validatedQualificationFailureTx。在仅属本次夹具的事务内，按作者原tamper测试方法临时移除 resource_effects 的 append-only triggers，只改一个 CONFIRMED 行的 receipt.receipt_id；sealed proof、marker、observation均不改，真实 private consumer 仍返回有效closure。事务最终回滚。r15与r20独立拒绝断言均失败。

这是校验器不能发现源证据破坏的反例，不意味着生产公开了任意SQL写入。现消费入口只检查 CONFIRMED 和 receipt非nil；proof也未固定整个 MODEL request/receipt。最小修复为此生产文件及 runtime_qualification_failure_windows_test.go：初始验证绑定 MODEL subject/epoch/key/sequence/history、canonical request/request_hash、route/capability/credential revision、canonical receipt/receipt_id、provider_response_hash，与已确认frame2、原始Host MODEL fact及response bytes一致；sealed proof与marker固定这些digest。消费时从存储重新算，拒绝request或receipt替换。明确 canonical object hash 与 raw bytes digest 的区别，保留frame/raw源字节哈希，不用状态或存在性代替内容绑定。独立只实测receipt_id改动，request替换是源码确认缺口，r2须补成相邻负例。

## 已验证的生产接线与有限正面结果

唯一 typed constructor 位于 brokerEffect 首次 dispatchGate 后、首次 providerRoute和prepareEffectTx前；dispatchGate在读取主体前获取 resourceWriteLock，并验证当前scheduler/executor/lease/admission。第二门未调用typed constructor；generic错误没有文本提升路径。known MODEL route 被用于禁止 TOOL 的窄判断，失败持久化返回普通错误。

runCommandBridge 使用本地 admission/completion registry 和专用broker context，typed拒绝后关入口、取消、消费结果并拒绝suffix；15秒排空边界不会给出可接受ticket。heartbeat被取消并等待done后才进入闭合。局部源码检查支持这些接线，但不能把registry单测等同于所有并发调度实测。

本地fresh native loopback B01通过：raw3/ACK2/rejected1、单次本地MODEL、派生FAILED；generic Observation/Finalize严格ACK规则未放宽。16个现有事务触发器故障切口通过，失败保留RUNNING/UNKNOWN；现有4个协调器回归加2个子测试通过。Task、UNKNOWN金额和runtime_uploads/artifact_uses/proofs零行的选定断言通过。

真实current Owner-root独立负例通过：从实际closure marker读出root，确认与scheduler不同，撤销root后确认scheduler自身revoked仍为0，validatedQualificationFailureTx拒绝。没有用作者声明代替该测试，也没有假C/D授权。

## B01-B12覆盖与必须补验的缺口

- **B01**：Fresh controlled native loopback PASS, raw3 ACK2/rejected1, one local MODEL request and derived FAILED closure. Not actual Mu bundle or external model proof.
- **B02**：Refusal matrix executed but relevant later guard claims need valid seed positive control; wrong task/lease/technical/marker-field permutations not exhaustive.
- **B03**：Known-route positive, generic unknown-route/malformed-tool/second-model negatives PASS. No complete malformed wire byte suite.
- **B04**：First constructor is only before first providerRoute/prepareEffectTx, under dispatchGate resourceWriteLock. Existing negative seed arguments=Empty() ([]any) is invalid for validateRuntimeToolArguments, so later effect/ledger guards are not independently isolated; PREPARED only rather than all requested historical stages. Existing purpose_expired_after_prepare generic regression PASS.
- **B05**：Existing create-new, ordinary permissive directory, reparse ancestor and conflicting receipt tests PASS; protected Everyone DACL independently FAIL. Write/flush fault, per-file source identity and racing ancestor/receipt replacement not proven.
- **B06**：Blocked MODEL overlap generic UNKNOWN test PASS; registry unit pending/late completion tests PASS. Production post-denial suffix, late auxiliary/model observation and bounded drain timeout not separately fault-injected.
- **B07**：Registry duplicate/missing/unadmitted guards and native blocked MODEL scenario PASS. Exact goroutine-lifetime proof reviewed statically; no protected holdout.
- **B08**：Raw stdout/stderr/bridge changes refused; stopped/drained/cleanup/output predicates read. Missing each field and identity replacement not individually injected.
- **B09**：Four existing coordinator tests plus two subtests PASS. Entire ordinary queue/cancel/claim/recovery test suite deleted (B-F02); no complete ordinary Mu session acceptance.
- **B10**：16 precommit trigger cuts PASS; exact claimed all-writer coverage absent: ImpactLink domain_objects and domain_refs writers not independently injected; commit failure not injected. Positive test checks selected counts, not full five-version/all-table unchanged census. Its duplicate test invokes RunAdmitted and observes terminal refusal; it does not exercise closeOnlineQualificationFailure completed-marker replay branches.
- **B11**：First cause and frozen-plan heartbeat race PASS; coordinator cancels and joins heartbeat before closure CAS. Secondary native facts retained; no universal cancellation/join theorem.
- **B12**：Existing 8 tamper cuts PASS; independent actual current Owner-root revocation PASS with distinct scheduler still unrevoked. Independent MODEL receipt corruption FAIL (B-F03). Request corruption and current grant/lineage mutation cuts remain.

特别要纠正作者报告的范围：FirstGateRefusalMatrix第191-192行使用arguments=Empty()，而Empty返回[]any，validateRuntimeToolArguments需要map。后段history负例会先被无效payload拒绝，应修正有效seed并加未改正对照。B10的16点没有覆盖ImpactLink对象、domain_refs各实际writer或commit失败；正例是选定计数，未证明全部五个version及全表不变集合。所谓replay实测调用RunAdmitted并被terminal gate拒绝，没有执行closeOnlineQualificationFailure中completed-marker重放分支。这些是缺失证据，不虚构为已观察到生产事务部分提交。

## 证据、隔离与诊断

13个冻结输入引用全部hash/size匹配；作者9个源码与110条recipe/stdout/stderr记录哈希全部匹配。读取了完整9路径diff、B架构/testcut、C写集、已接受A-r2与classification审查。候选HEAD/tree/source hashes与clean tracked worktree保持。

r09：56 PASS测试节点、1 FAIL、0 SKIP；domain现有切口及新增Owner-root通过，adapter新增ACL负例失败。r15：1 FAIL（MODEL回执改动）。r16：6 PASS、0 FAIL/SKIP。r20为三项独立切口的有限重采集：1 PASS、2 FAIL、0 SKIP，并单独保存原生Go stdout/stderr bytes及native exit1。节点数不是动态断言数，native exit文件才是测试状态，外层PowerShell exit0不是PASS。

前期读取日志是完整合并文本捕获，未把它冒充分别捕获的原始stdout/stderr bytes；r20补足三项独立切口的原生字节。首次bootstrap读取只有tool记录、未预写own recipe；r08嵌套here-string在执行测试前解析失败；r05和r11的路径查询错误、r19一次被显式静默的不存在占位路径查询以及行号纠正均列入diagnostic-ledger，不删失败。

作者22项nonzero/unavailable、3项preexecution、aggregate未捕获读取、b82 stderr以及b91实际auto-GC/repack偏离保持，不计作本轮产品失败也不重置。Root已验证selected对象/header/inputrefs可用不代表历史修复，missing62仍未恢复。本轮无Git写、GC/repack/prune/config/旧日志清理。独立own namespace不是受保护holdout。

下一步最小修复共5路径，列于review.json；修复后按本报告三项反例、有效seed与缺失切口重新独立审查。当前结论保持NEEDS_CHANGES。

'@
$diag=@'
{
  "schema": "researchos.independent-review-diagnostic-ledger.v1",
  "history_preserved": true,
  "product_defects": [
    "B-F01",
    "B-F02",
    "B-F03"
  ],
  "review_attempts": [
    {
      "id": "bootstrap",
      "kind": "capture_gap",
      "detail": "Initial AGENTS/scope read performed before own recipe/raw setup. Output retained in tool conversation; not claimed as a fully logged command."
    },
    {
      "id": "r05",
      "kind": "lookup_failure",
      "detail": "rg supplied literal nonexistent wildcard paths; native error2 occurred inside batch then later successful commands. Full merged output retained; aggregate wrapper native exit does not characterize every subcommand."
    },
    {
      "id": "r08",
      "kind": "preexecution_parser_failure",
      "detail": "Nested here-string delimiter collided with command wrapper; tool exit1 with empty output. No native tests launched. Corrected r08b used safe single-quoted literal serialization."
    },
    {
      "id": "r11",
      "kind": "lookup_failure",
      "detail": "rg named absent schema directory; native exit2 retained; valid migration reads followed r13/r14."
    },
    {
      "id": "r17",
      "kind": "line_range_error",
      "detail": "Requested lines816-851 exceeded820-line source; blank outputs not treated as source. Correct exact MODEL consumer lines792-795 established r18."
    },
    {
      "id": "r19",
      "kind": "suppressed_lookup_error",
      "detail": "One accidental nonexistent PLACEHOLDER Get-Content with explicit SilentlyContinue ran in node-count loop. No result used; real file reads and counts succeeded."
    },
    {
      "id": "read_capture",
      "kind": "capture_limit",
      "detail": "r01-r19 use merged PowerShell textual output; individual native exits in multi-command read batches not exhaustive. Test native exits separately persisted; r20 uses separate native Go byte redirection."
    },
    {
      "id": "r09",
      "kind": "test_failure",
      "native_exit": 1,
      "reason": "Independent unsafe DACL refusal assertion failed; 56 PASS/1 FAIL/0 SKIP nodes."
    },
    {
      "id": "r15",
      "kind": "test_failure",
      "native_exit": 1,
      "reason": "Independent changed MODEL receipt refusal assertion failed."
    },
    {
      "id": "r20",
      "kind": "bounded_evidence_repeat",
      "native_exit": 1,
      "reason": "Separate byte stdout/stderr capture for three independent cuts; same two defects reconfirmed; current Owner-root revocation PASS."
    }
  ],
  "author_history": {
    "nonzero_or_unavailable": 22,
    "preexecution": 3,
    "unlogged_reads": "aggregate gap retained",
    "b82": "native0 with nonterminating removal stderr retained",
    "b91": "auto GC/repack deviation retained",
    "missing_history62": "not restored; Root selected input availability is narrower"
  },
  "counting": "No historical counters or acceptance counts reset. Formal increment0."
}
'@
[IO.File]::WriteAllText("$E\review.json",$review)
[IO.File]::WriteAllText("$E\review.md",$md)
[IO.File]::WriteAllText("$E\diagnostic-ledger.json",$diag)
Get-FileHash "$E\review.json","$E\review.md","$E\diagnostic-ledger.json"

