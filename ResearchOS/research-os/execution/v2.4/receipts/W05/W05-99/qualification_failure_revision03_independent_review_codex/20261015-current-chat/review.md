# CP509 independent review

C 单锁设计有条件可进入 Source：Root 卡必须纳入 C-LD01..03。F01 的 Host 首门 TOOL 未派发窄主张成立；原 worker 可以使用独立的 Job accounting 历史推论类别。原 verifier 只证明 Host 未传 Job/token，原生退出缺失、完整初始化/后台能力未闭合，因此实际 STOP/C 仍不可用。本件不是 Source 或 actual acceptance，formal increment=0。

冻结 revision03 manifest 104 项和 scope 引用合计110项全部匹配；另核验22项历史冻结引用、13项公开采集文件全部匹配。Main HEAD4f、tracked dirty20、index empty；只写本回执目录。模型配置来自冻结卡，reviewer 无运行时 introspection，未把配置写成实测身份。

## 分支结论

- `C_lease`: DESIGN_ACCEPTABLE_ONLY_WITH_MANDATORY_C_LD01_TO_03_IN_ROOT_SOURCE_CARD
- `F01_host`: SUPPORTED_NARROW_SOURCE_RECONSTRUCTION; CONDITIONAL_FAILED_ONLY_DESIGN_WITH_F01_D01_TO_03
- `F01_universal_OS_no_effect`: NOT_PROVABLE; NO_OBSERVED_ESCAPE_CLAIM
- `worker`: ACCEPT_DISTINCT_HISTORICAL_JOB_ACCOUNTING_CLASS_WITH_W_D01; NOT_RAW_NATIVE_WAIT
- `verifier_host_Job_token`: SUPPORTED_SOURCE_RECONSTRUCTION_OF_NOT_TRANSFERRED
- `verifier_original_native_wait`: MISSING
- `verifier_NEVER_JOB_AUTHORIZED_operational_substitute`: NOT_PROVABLE_TRANSITIVE_INIT_BACKGROUND_CLOSURE
- `actual_STOP`: UNAVAILABLE; UNCHANGED
- `actual_C`: BLOCKED_ON_CURRENT_STOP_VERIFIER_AND_ACCEPTED_SOURCE; NO_AUTHORITY_FROM_THIS_REVIEW

## C 必须补充的约束

### C-LD01 — Parent lease copies and legacy borrow release share one lifetime

Current exported DataRootLease value contains mutex, file and borrowed flag directly. External code can copy the value without touching private fields. Revision03 explicitly protects borrow copies but does not explicitly protect parent copies or distinguish old ReturnBorrow from the new maintenance borrower. A copied parent could Close its copied state while a maintenance borrower is active; a reused boolean could let ReturnBorrow clear the wrong borrow.

Make every DataRootLease value point to one private heap owner-state containing mutex, file, generation, closed state and active borrow identity/kind. Copies, Root/Held/Close, old Borrow/ReturnBorrow and new Maintenance methods must consult that same state. Nil/zero parent and borrow must fail closed without panic. Legacy ReturnBorrow may release only an active legacy coordinator borrow; it must reject an active maintenance borrow. Maintenance Release consumes only its exact private generation-bound token, and cannot release a later or legacy borrow. Parent Close refuses either live borrow and invalidates all copies atomically on successful close. No lock held while recursively calling a method that takes it.

证据：adapters/runtime/data_root_windows.go:16-22, adapters/runtime/data_root_windows.go:58-107, 18.stdout.raw

验证切口：

- Copy parent before borrow; copied Close refuses and original Held remains true.
- Copy parent/borrow; release one borrow; stale copy cannot release a newly acquired borrow.
- Legacy ReturnBorrow during maintenance borrow fails and cannot enable Close; concurrent legacy/maintenance borrow admits only one.
- Zero-value Close/Check/Borrow never panics and never claims Held.

### C-LD02 — One normalization and identity guard across all upgrade branches

All five plans enter the new adapter, but queue/configuration branches call upgradePaths again and then open templates/source later. Merely retaining coordinator.lock and checking a path at adapter entry does not stop a source/root rename or alias change before a downstream open. The text requires revalidation after normalization but does not place it in these existing common call sites.

Within the existing allowed backup_upgrade.go, make the shared upgradePaths path finish by validating opt.sourceLease against the final normalized root/source for guarded production workflows, before returning to any branch. The private adapter/source borrow must retain native no-delete/rename guards for the exact root path components and source file identity until all downstream DB defers complete; metadata handles may share read/write needed by SQLite but cannot permit identity replacement. Check canonical containment, no reparse and exact native file identities. Existing prepared wrapper Check remains required. Public UpgradeLocal/UpgradePreparedAbandonmentBackup stay fail-closed before any provider/key/template/store work. Isolated private legacy algorithm fixtures cannot count as guarded entry proof. This selected central implementation avoids adding queue/configuration production files; if the builder cannot implement these persistent guards, STOP and request an exact scope addition for explicit checks, rather than omit the invariant.

证据：internal/domain/backup_upgrade.go:120-135,245-253, internal/domain/backup_configuration_upgrade.go:174-191, internal/domain/backup_queue_upgrade.go:320-337, 19.stdout.raw

验证切口：

- Exercise every five-plan dispatch using a real held lease, including normalized option copy.
- Attempt source file/root component replacement after adapter borrow and before template/source open; deny replacement or fail before forbidden setup.
- Prepared nested local/handoff inner Close/error leaves outer Held and cannot release the native owner.
- Forbidden Canary/key/provider/template/store sentinel remains untouched for invalid plans, wrong identity and pending journals.

### C-LD03 — Exact-own recovery validates the pending transition, not only prior terminal target

Replacement can die after ReplaceFile while journal remains PUBLISHING and target already equals NewBytes. Applying ordinary history-current/latest-terminal-target comparison before granting its exact own inspection permit would reject this legitimate recovery. Treating the permit as a broad pending exemption would create the opposite flaw.

Freeze two separate pure predicates in the shared reader: ordinary acquisition validates complete history and current terminal target; exact-own inspection validates the full causal history including the one exact pending operation and its permitted current old/new state using the existing replacementRecover applied/unapplied evidence predicates. Include exact namespace/root/operation/plan digest and bounded file inventory. PREPARED/PUBLISHING partial histories may enter only the exact recovery inspection that existing recovery rules permit; no ordinary lease or backup borrow may pass. The other namespace and every non-own pending operation always deny. PUBLISHING with exact applied NewBytes may be inspected/completed; it cannot abort or replay ReplaceFile. Unknown/mixed/tampered backup/stage/hash evidence denies. C own inspection must similarly preserve its existing NOT_APPLIED/ABORTED rules. Revalidate under the held lock; no serialized permit, callback, bool or raw handle supplies authority.

证据：internal/host/runtime_verifier_replacement_windows.go:752-771, internal/host/runtime_verifier_replacement_journal_windows.go:315-405, 12.stdout.raw, 19.stdout.raw

验证切口：

- Both PUBLISHING-before-ReplaceFile and PUBLISHING-after-ReplaceFile retain the exact existing recovery result.
- A prior completed replacement followed by pending own replacement never requires target to remain predecessor bytes once own publish applied.
- Own C permit cannot exempt replacement; own replacement cannot exempt C; backup borrow rejects both exceptions.
- Unknown inventory, wrong plan/root/operation, concurrent second pending entry and changed target all fail closed.

## F01 与 worker 的私有消费者边界

### F01-D01

The new historical type states only HOST_TOOL_EFFECT_NOT_DISPATCHED for the exact qualification MODEL-only first-gate TOOL frame, with the exact frozen subject, raw evidence digests, actual compiled Core/source bindings and rule version. It is generated by current Owner and run_id=null. It cannot satisfy a UNIVERSAL_OS_NO_EFFECT consumer, become an original online denial or claim raw denial text that was not recorded.

验证切口：Changing route/capability/key/subject/first-gate source digest, a TOOL prepare/start/provider/ledger row, extra suffix frame or missing raw bytes denies construction.

### F01-D02

Keep raw frames=3, ACK=2 and raw queue_empty=false. A separately named derived FAILED-only observation may classify all three exact frames only after complete census, exact MODEL ACK/receipt/effect binding, no unresolved extra external effect or queue/control/checkpoint, accepted worker native class, accepted current STOP including original verifier prerequisite, held root+dispatch owner locks, and accepted private consumer. Never change generic Finalize/Observation, fabricate ACK3 or historical broker join, or equate queue_required=false to empty.

验证切口：Missing/UNKNOWN effect outcome denies; CONFIRMED MODEL with UNKNOWN money preserves ledger/budget and does not become zero money. Missing any current closure premise denies even when historical native receipt matches.

### F01-D03

Keep B actual online private drain ticket distinct from historical reconstruction. The historical constructor must independently prove current quiescence after accepted STOP and root/owner locks; it cannot manufacture a B ticket or call an online constructor with a bool. The common FAILED-only transaction accepts only the verified private variant and preserves the exact prior C five-version write set and all frozen protected rows. B Source must be independently accepted before D; F01 alone opens no D or actual C action.

验证切口：Forged JSON/caller booleans/wrong proof-kind/online-ticket substitution reject. Exact frozen write-set census shows only Run and ProjectState updates plus Artifact/ImpactLink/EventEnvelope new versions and the existing enumerated ancillary rows; no Task/consumption/effect/ledger/budget/NoProgress/lease/qualification/schema/history edits.

### W-D01

HISTORICAL_NATIVE_JOB_ACCOUNTING_CLOSURE_V1 is a distinct source-derived class, bound to bridge SHA256 10b1a3bfa74132fbed965df31fd90125b90b1470556001e254af360c35451bce, PID69860, creation1792057406096619100, Job Local\ResearchOS.W10.1792057404322293200, profile/SID/manifest/build/source identities and exact public receipt fields. Its fact is the recorded Stopped=true backed by successful Job accounting query ActiveProcesses==0 plus streams_drained. It has no raw WAIT result, no exit0, no historical successful owner Close receipt and no proof DeleteAppContainerProfile succeeded. Current owner lock possession remains a separate future prerequisite.

验证切口：Reject changed binary/source/receipt hashes, any mismatched identity, stopped=false, undrained streams, missing chain to runSandbox completion, or a consumer requiring raw WAIT_OBJECT_0.

## 覆盖与路径

不新增现有冻结 allowlist 以外的生产或测试路径。C-LD02 选择在既有 backup_upgrade.go 的共享归一化函数中检查，再由已允许的 native source-borrow 文件持续持有文件/目录身份 guard。若无法实现此路径，不得静默放弃约束或编辑未列文件。

| 入口 | 结论及必须保持的条件 |
|---|---|
| normal Core | covered conditionally; combined two-namespace gate under real lease before DB/bootstrap/provider/protected setup |
| raw LockDataRoot/coordinator | covered conditionally; checked public acquisition wraps package-private raw OS acquire; no recursion and no unguarded coordinator route |
| backup create/export | covered conditionally; one CLI lease and identity guards before key/provider/store; DB closes before lease |
| all five upgrade-local plans | covered with C-LD02; typed adapter then shared normalized Check and persistent identity guards; old exported API fails before setup |
| prepared local and handoff | covered conditionally; private borrowed wrapper; no second acquire; handoff option copy retains private sourceLease; inner Close does not Release |
| legacy release_host | covered conditionally; wrapper and lease before OpenCanary; DB then Canary then lease close |
| disposable control bootstrap/resume and Core handoff | covered conditionally; strict existing fixture binding and checked Driver Start/Restore/Compatible acquire; Start releases parent before child acquires; child rejects any pending intent inserted in the handoff gap |
| inherited recovery/migration | covered conditionally; adoption/binding token.Check, pure combined gate, token.Check before exclusive DB/PRAGMA; preserve native token ownership |
| fixture replay | covered conditionally; lease/gate before store.Open |
| replacement and C maintenance | covered with C-LD03; ordinary or exact-own private inspection; cross-namespace deny before SQLite |
| keygen/restore/non-Windows | boundary preserved; keygen no root; restore new destination cannot target aliased live/pending root; non-Windows native adapter fails explicitly |

internal/qualificationmaintenancejournal may import bounded low-level filesystem/ACL/native-path/hash/strict-JSON Windows helpers but no domain/host/runtime cycle. Duplicate replacement reader must prove grammar/state/file/digest equivalence including terminal and own-pending cases, never merely last state string.

## 证据范围与缺口

原 worker receipt 记录 children_stopped=true、streams_drained=true、exit124、job_total_processes=2；绑定源码表明 Stopped 来自成功 OS Job accounting 查询的 ActiveProcesses==0。该链不产生原始 WAIT_OBJECT_0、exit0 或 owner Close 成功回执。当前 exact owner lock 必须由后续已授权维护实持，本轮未 probe。

原 verifier 在 Host 执行错误后、token/Job 发送前返回是窄源码推论。它早已启动；Go selected-source initializer 和传递依赖后台闭包未完成。defer cmd.Wait 被调用和当前 PID 缺席均不能替代原句柄成功退出记录。未重新审查 STOP anchor，也未扩展到 verifier init 审计。

原始 frames3/ACK2/queue_empty=false 与金额 UNKNOWN 保持。新的 FAILED-only 分类不能使 generic Finalize/Observation 变宽、不能补造历史 ACK/drain/join，也不能生成 B 的在线 ticket。B 必须先真实实现并独立接受，D 不得绕过。C 的五个版本和全部逐表写集保持 revision02 原约束。

## 验证与审计

本轮没有执行 Source/native tests、current DB 读取、OS/进程操作、模型调用或实际维护。source-refs.json 固定31项实际读取源码的哈希；input-verification-v2.json、historical-input-verification.json、public-collection-verification.json 保留核验。命令 recipes 先写再执行并保留 raw stdout/stderr/native exit。

diagnostics.jsonl 保留 bootstrap/context 恢复读取未存 receipt-local raw 的缺口、02 Unicode 失败、04 exit0但Get-FileHash报错的无效核验、06 syntax failure、11非阻断警告及16路径猜测失误；没有重置失败或删改旧记录。04 的核验不计入通过，05独立Python核验才作为结果。

精确结构化结论与测试切口见 review.json / mandatory-addenda.json；证据包由 FINAL-manifest.json 固定。Root 只能把本件作为下一张受控 Source 卡的设计审查输入，不能据此进行 actual STOP/C 或宣布正式用例完成。
