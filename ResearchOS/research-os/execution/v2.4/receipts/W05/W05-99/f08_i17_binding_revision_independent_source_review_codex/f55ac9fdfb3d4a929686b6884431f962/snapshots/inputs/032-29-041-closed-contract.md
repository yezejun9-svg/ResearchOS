# F08 closed-contract revision 5 — read-only, not implementation authorization

This document and candidate.sql.txt form one design. The prior v3, v4 and supplements remain unchanged. No SQL, compiler, tests, Node, generator, native process or model is executed. The fixed product input is Main 2cdb0d43d5a600eef13c8f1735946a9adf52d079. Handler source is still leased elsewhere: its final private-header reader and Execute coupling must be checked after freeze, without changing the contract below.

## Decision and exact scope

Keep the nineteen paths in review-required_closed_contract.json and propose a twentieth narrow path, internal/domain/client_command_queue.go:ensureClientQueue, because its existing INSERT ... ON CONFLICT DO NOTHING conflicts with a pre-REPLACE protection trigger. The exact preserved-repeat algorithm and expanded observeRuntime bound are in source-contract.md. The runtime.go producer is private caller-Tx; runtime_coordinator_windows.go changes only dispatchGate/RunAdmitted before STARTED CAS. No persistent native QUEUED-before-dispatch phase is introduced. claimTaskMode already creates Run and native PREPARED dispatch in one transaction. Missing native dispatch is corruption; positively identified generic/old no-dispatch execution still needs genuine existing terminal evidence. No orchestration.go, runtime_dispatch.go, store.go, driver, public contract, SQL1..23, API, CLI or SDK change is assumed.

The proposed20-path design expands the new client_cancel_finalization.go responsibility: a pure SQL guard evaluates a complete SQL-built source bundle rather than ready/hash flags or callback DB reads. The explicitly added origin-derivation mode8, SQL24 tables/views/triggers and twentieth caller path require independent scope review. If final handler reuse needs another path, stop and name it before implementation.

Root rejected the proposed 1MiB response limit. Remove it completely. Do not add a witness/member count or body cap unsupported by the frozen protocol. Only existing decoded-envelope 1MiB and approved private-header bounds remain. Responses, source bundles and witnesses are processed in full, including legal >1MiB SessionSnapshot. Existing SQLite/Go parser/resource limits remain failure conditions; they are not a new accepted-response policy. The source-bundle reference implementation can consume substantial memory; measure it during the future tests. Optimization must preserve exact source selection and raw-byte validation. No truncation, pagination or partial validation is allowed.

## Scalar, byte and digest rules

All keys listed below are required; unknown keys are rejected recursively. Strings are strict UTF8, nonempty for identifiers, with no implicit conversion. Nullable fields are explicitly listed. JSON and driver integers must be exact int64 and satisfy their schema bounds; bool, string, fractional and non-lossless numbers fail. VersionRef is exactly {entity_type,id,revision,content_hash}; content_hash may be the actual SQL NULL, never invented. A project belongs to relational context, not the VersionRef object.

R(b) = "sha256:" + lowercase hex SHA256 of exact byte sequence b.
J(v) = R(canonical.JSON(strict JSON bytes encoding v)), RFC8785.
Q(e) = existing Envelope.ContentHash from the actual original strict DecodeEnvelope, preserving the project's existing custom canonicalBytes algorithm. Q is not replaced by J.
MemberHash = J(member payload).
GroupHash = J(array of {task_id,member_hash}, sorted by task_id's UTF8 byte sequence, unique).
RootHash = J(root payload). Root payload has no self hash or GroupHash; group hash is an independently checked SQL column.
A proof ref is exactly {phase,task_id,content_hash}; phase is ADMITTED or FINALIZED, root task_id is null, member task_id nonempty. It is resolved only inside the same principal/project/command/request_hash parent locator.
An event ref is the frozen EventEnvelope VersionRef plus actual outbox id/sequence/raw digest in a separate closed {version_ref,outbox_id,sequence,body_digest} object.
An artifact-byte ref is {artifact_ref,storage_key,byte_size,bytes_digest}; digest is recomputed from actual sealed uploaded_content bytes and exact Artifact/use rows.
A control-receipt ref is {receipt_id,body_hash,previous_receipt_id}; last field is nullable.

ADMITTED and FINALIZED transport columns are closed:
{root: <root payload>, members: [<member payload>...], pins: [<pin>...]}.
A pin is {project,kind,id,revision,content_hash}; nullable content_hash equals actual original domain_versions. Pins are the exact sorted unique set of every referenced domain version needed by the payloads and their declared proof closure. A missing or extra pin fails. Derived member and pin tables are materializations of this immutable transport, not another response authority.

There is no root/member hash cycle: admitted root contains the task-ID set but not member hashes; each admitted member references RootHash; final members reference admitted members but not final RootHash; GroupHash is outside both root payloads. The final root contains actual response digests and references the admitted root, but not its own hash.

## Complete payloads

Use format researchos.cancel-finalization/1 throughout.

ADMITTED_ROOT keys:
format,phase,principal,project,command_id,method,operation,key,request_hash,client_id,session_binding,target_binding,private_header_digest,member_task_ids,member_count.
phase=ADMITTED, method=session.control, operation=v2:session.control, key=command_id.
session_binding = {session_id,accepted_revision,writer_client_id,writer_epoch,lease_expires_at,event_watermark}; all original real values, positive revision/epoch, nonnegative watermark, actual date-time expiry.
target_binding = {kind,id,version_ref}; kind Goal or Run. VersionRef is exact current pre-mutation target. Goal task set is SELECT all current Tasks with this goal_id; Run target set is its exact task_id. Both directions of set equality and all members' current versions must hold before any mutation. Array sorted/unique/nonempty; member_count exact length. private_header_digest=R(actual stored original header).

ADMITTED_MEMBER keys:
format,phase,admitted_root_ref,task_ref,goal_ref,run_ref,runtime_binding,dispatch_stage,dispatch_origin_ref,queue_admission,reference_closure.
phase=ADMITTED. task_ref/goal_ref are nonnull.
runtime_binding = {run_id,runtime_id,executor_principal_id,lease_epoch,lease_token_hash,lease_expires_at}, or null only NO_RUN.
dispatch_stage enum NO_RUN,NATIVE_PREPARED,NATIVE_STARTED,NATIVE_OBSERVED,NATIVE_UNKNOWN,GENUINE_LEGACY_NO_DISPATCH.
dispatch_origin_ref = {project,run_id,epoch,dispatch_key,content_hash}, or null if legacy/noRun; new native requires exact actual origin.
queue_admission = {variant,session_id,generation,revision,state,accepted_through,sealed_through,run_id,runtime_epoch,dispatch_key,manifest_hash,process_identity,restore_fenced}.
NO_SESSION: all other fields null, actual Session absent.
REAL_SESSION_NO_ORIGINAL_FENCE: session_id actual; all fence fields null. No original generation invented.
ORIGINAL_FENCE: every field equals actual original row; schema22 null run/epoch/dispatch/process fields remain null when genuinely unbound; restore_fenced integer0/1, original watermarks nonnegative.
NO_RUN: run_ref/runtime_binding/origin null and no current or historical Run, dispatch, execution effect/lease for Task.
GENUINE_LEGACY_NO_DISPATCH: actual Run/runtime binding nonnull; requires positive original compatible fixture provenance and no contradictory native admission; never native-fastfinalizes. An unprovable legacy classification fails closed.

FINALIZED_ROOT keys:
format,phase,admitted_root_ref,principal,project,command_id,request_hash,control_request_id,completion_mode,original_response_digest,final_response_digest,final_snapshot_binding,member_count.
phase=FINALIZED; completion_mode ORIGINAL_COMPLETED or ACK_TO_COMPLETED.
control_request_id = ctrl-<original command_id>.
final_snapshot_binding = {session_id,project_id,revision,event_sequence,pending_command_ids_digest}.
Digests R(actual original control response) and R(actual final journal bytes); immediate completion uses the very same actual bytes for both, never a fake ACK.
pending_command_ids_digest=J(actual final snapshot array), preserving its actual order. Only this exact command may be removed by its genuine confirmation; other pending controls remain. Root count equals original admitted count.

FINALIZED_MEMBER keys:
format,phase,admitted_member_ref,proof_kind,task_admitted_ref,run_admitted_ref,run_before_settlement_ref,run_final_ref,task_final_ref,dispatch_origin_ref,dispatch_final_binding,queue_final_binding,effect_closure,observation_ref,native_artifact_refs,sdk_receipt_refs,run_event_ref,task_event_ref,reference_closure,prior_epoch_closure,prelaunch_checkpoint_carry.
phase=FINALIZED. proof_kind NO_EXECUTION,NEVER_LAUNCHED_NATIVE,TRUSTED_STARTED_TERMINAL.
task refs nonnull. NO_EXECUTION: all run/dispatch/observation/run_event fields null, native_artifact_refs/sdk_receipt_refs empty; no invented SDK facts.
dispatch_final_binding = null or {project,run_id,epoch,dispatch_key,manifest_digest,manifest_bytes_digest,state,worker,journal_locator,identity,observation_sequence,observation_hash}. Identity is exact original typed native identity object; original empty object remains empty only never-launched. Never-launched retains PREPARED, zero observation, empty worker/locator/identity.
queue_final_binding = {variant,session_id,generation,revision,state,accepted_through,sealed_through,run_id,runtime_epoch,dispatch_key,manifest_hash,process_identity,restore_fenced,entry_refs,receipt_refs}.
Same null variants as admission. A genuine newly-created fence has variant CREATED_SAME_TRANSACTION and original actual Session; bind its real row and CANCEL_FENCE receipts separately from original absence. entry_refs = sorted [{principal,project,command_id,queue_sequence,request_hash,content_hash,state,last_receipt_id}]; last receipt must exist for cancellation-created changes. receipt_refs are the exact ordered original chains, no gaps/aliases; same-generation facts must agree.
effect_closure = {run_id,epoch,histories,non_effect_reservations}.
For NO_EXECUTION run_id/epoch null and arrays empty.
histories = sorted [{effect_key,rows,latest_sequence,request_hash,reservation_ref,cost_refs}].
rows = ordered [{sequence,body_digest}], actual resource_effects body R recomputed; exact sequence starts1 with no gap, complete Run-wide set of keys through the admitted epoch, preserving each row's actual original epoch, latest only CONFIRMED or NOT_APPLIED; PREPARED,STARTED,UNKNOWN forbid completion.
reservation_ref and each cost_ref are actual BudgetLedgerEntry VersionRefs with original request/body/hash/policy/principal/runtime route closure; no unmatched original MODEL reserve allowed.
non_effect_reservations = sorted [{classification,reservation_ref,cost_refs,original_claim_ref}]. Only authentic runtime-local-launch or qualification-dispatch full producer tuple can appear, using original manifest/admission/claim evidence. Prefix/amount0 alone insufficient. All ledger rows unchanged; no unknown release.
observation_ref = null or {project,run_id,epoch,receipt_hash,body_digest}. Both digest actual immutable runtime_observations body according to existing Hash versus raw R; raw hash not substituted for canonical receipt_hash.
native_artifact_refs binds complete exact observation and cleanup/sealed native artifacts. sdk_receipt_refs bind actual original clear/drop/abort_observed/cancelled-idle and consumption chain as applicable. No SDK fields in NO_EXECUTION/NEVER_LAUNCHED.
run/task event refs use the closed event shape above and exact final versions. An already-terminal historical Task need not be mutated again: task_final_ref is its original proven terminal version, not later active Task head. Historical proof validation never cancels a newer Run.

DISPATCH_ORIGIN and reference_closure payloads are fully defined in evaluator-v5.md (R1/R2); that definition is part of this closed contract. Origins are epoch-specific, with permanent birth separated from epoch_authority and a complete source_closure. The first Run epoch need not equal1. Every post24 later epoch derives from the real already-written new Run and actual earlier settled dispatch/route/checkpoint/dependency facts; its future RUN_CHANGED is not required. Original32 source tuples remain unchanged; exact checkpoint_carries and run_dependencies extend the source registry to34.

LEGACY_RUN exclusion payload:
{format,source_schema_version,project,run_id,versions,dispatches}.
source_schema_version=23; versions is the full ordered old domain_versions Run array {revision,body_hex,content_hash}; dispatches is full ordered old runtime_dispatches column array, preserving epoch/key/raw manifest/identity/observations. It is a migration exclusion inventory, not completion evidence.
Migration captures every preexisting Run ID from current objects OR version history OR dispatch table; rejects missing/invalid source closure before migration under the matching-source plan. Exclusion is by project+Run ID, not timestamp or mutable max revision; later epoch/reinsert using old ID cannot become new-native. All exclusion table INSERT/UPDATE/DELETE/REPLACE become forbidden immediately after the initial population. Fresh24 has empty immutable exclusion.
The cohort hash J(sorted exclusion rows) is in schema24 inventory and must match the authenticated source23 all-table inventory in the exact upgrade plan; the external archive snapshot hash remains in the upgrade receipt/manifest, not falsely described as generated by SQL. No ADMITTED/FINALIZED/origin is backfilled for old rows.

## UDF contract and source binding

Keep exactly three names, all registered sequentially by domain package init before ANY default-driver Open; private schema compiled once from cloned embedded protocol8943... and externalb53d... using existing localOnly/AssertFormat/pattern checks. Registration failure panics before main. No DB/Host/clock/FS/env/network reads or validation flag in callbacks. No retained argument/context references.

1. researchos_f08_cancel_request_v1(header BLOB,identity BLOB) -> int64(1) or error.
Identity is the exact closed identity object from supplement. SQL constructs it from actual immutable admission/identity/journal columns, never from caller metadata. Existing header byte limit and decoded raw 1MiB enforced; strict base64 StdEncoding.Strict plus reencode; strict JSON/UTF8/duplicates/numbers; exact frozen Envelope and CANCEL payload; recompute Q(original) and R(header), compare original tuple.

2. researchos_f08_cancel_response_v1(header BLOB,binding BLOB,old BLOB-or-NULL,new BLOB,mode INTEGER) -> int64(1) or error.
mode0 initial ACK, mode1 original COMPLETED, mode2 ACK->COMPLETED. No response cap.
binding exactly {identity,response_proof}.
response_proof mode0 = {admitted_root_hash,original_response_digest,final_root_hash:null,final_response_digest:null,final_snapshot_binding:null}; original_response_digest recomputed from actual new bytes and matches actual control.original_response.
mode1/2 = {admitted_root_hash,original_response_digest,final_root_hash,final_response_digest,final_snapshot_binding}; fields come from actual stored FINALIZED root and actual control, not two supplied digest strings.
Recompute R(old/new) from actual SQL OLD/NEW BLOB arguments; mode1 old=NULL and new is both original/final. Compare recomputed digests to root, actual control.original_response/final_response, and the request/identity tuple. Validate both raw responses in full with strict parser, DecodeResponse, full SchemaDoc.ValidateDef CommandResponse, ValidateResultAgainstMethod and exact nested snapshot. Check new snapshot binding and exact removal of this command from actual pending controls. Mode2 preserves every other idempotency column byte/type and original header separately in SQL. Changed source/root hash, even if attacker changes another supplied hash, fails actual-byte recomputation.

3. researchos_f08_proof_v1(mode INTEGER,input BLOB) -> result or error:
mode -1 returns J(parsed complete strict JSON input); mode -2 returns R(exact input bytes). These pure digest modes grant no write authorization.
mode0 validates atomic ADMITTED transport against actual original source bundle; mode1 validates atomic FINALIZED transport; mode2 verifies DISPATCH_ORIGIN; mode3 validates LEGACY_RUN inventory; mode4 checks a protected dispatch OLD->NEW transition; mode5 verifies journal commit closure; mode6 validates original/final control change; mode7 verifies exact generated materialization/pins; mode8 derives the complete origin document as canonical JSON text. Modes2/8 and historical origin evaluation obey evaluator-v5.md.
Modes0..7 return int64(1), never NULL, only after recomputation. They receive exactly {action,row,old,sources}; old null for INSERT, row is actual NEW SQL column tuple including raw hex, action is fixed per trigger. No omitted/extra source category or variable action alias. Atomic group transport itself is parsed from row.document bytes; source bodies remain hex and are decoded strictly before maps lose duplicate keys.

Sources is built by the SQL view described below from real rows in the same SQL statement/connection/transaction. It is not passed into Go by an external caller. It contains actual relevant project rows, original global identity, full versions/refs/outbox/idempotency/controls/queue/effects/dispatch/observations/uploaded bytes plus F08 cohorts/origins/groups/materializations. SQL source selection includes every matching row; UDF rechecks counts, keys, cross-relations, raw/canonical hashes and current/history requirements. Missing required rows and duplicate real table keys error. domain_refs has no key and preserves legal duplicate tuples with exact multiplicity; see evaluator-v5.md for complete two-way occurrence and historical-anchor rules. This makes complex schema/content validation part of the SQL-trigger path, not an ordinary Go-only precheck. Whole-file/trigger replacement remains outside this in-file consistency guarantee.

Every raw value crosses UDF boundary as CAST(... AS BLOB), after original typeof gate; sqlite TEXT nonvolatile conversion uses libc.GoString and is unsuitable for byte identity. JSON source bundles use hex(actual body bytes), not json(body), so invalid Unicode/duplicates/NUL cannot be normalized away. Binding JSON uses typed columns and must itself be strictly parsed. No UDF output cache/ready flag and no stored digest equality alone grants mutation.

## Atomic group mechanism and transaction order

The candidate uses physical admitted_groups/admitted_members and final_groups/final_members. Each group stores immutable closed full transport and typed root/hash/group-digest columns. Its one INSERT validates complete source set first and then AFTER INSERT derives every member/pin via json_each and verifies exact materialization. Direct child insert must equal exactly its parent member at its index; after the root statement no missing member can exist. Member UPDATE/DELETE/REPLACE/extra insertion all refuse. Child row completeness is still verified again at journal transition and backup.

ADMITTED group has deferred exact original journal FK and exact command identity FK. Its initial trigger checks original target+Session+all Tasks/Run/fences while still pre-mutation, and child pins tie actual versions. As all children are derived within the root statement, raw root/member partial commit is impossible; deferred journal/identity FK prevents admission-only commit without actual original response.

FINAL group has deferred FK to final_commit(exact locator,final_root_hash). The final_commit has reverse FK to that FINAL group. It is inserted ONLY by the original journal completed AFTER trigger; its BEFORE trigger independently rereads and validates the actual completed journal, group, materializations and CONFIRMED control. Direct INSERT has identical real-journal requirements. Thus a FINAL group alone, even with self-consistent hashes, cannot commit while journal remains ACK or absent. Group alone does not authorize a response.

Stage order:
1. Execute authenticates/CAS/reserves identity as final handler requires; original replay lookup preserves first raw header. Enter business SAVEPOINT.
2. Under resourceWriteLock, capture original pre-mutation target and all members. INSERT complete ADMITTED group; exact child materialization/pins occur atomically, journal FK deferred.
3. Perform original Goal/Task/control/fence mutations. Preserve original complete membership and every no-Session variant; no new generation invented.
4. If not settled, stage control.original_response once, insert original ACK journal, validate and commit. No final group exists. ACK replay retains exact old bytes.
5. Recheck every member's exact original facts under the same writer transaction. Keep the actual pre-settlement VersionRefs in transaction-local Go values. Do not insert a prospective FINAL group or guess an event/time/hash.
6. The private runtime.go producer writes the real original CANCELLED Run, runtimeTaskTerminal Task and actual events and returns their actual VersionRefs/event objects. It creates no native observation, process artifact or SDK receipt and releases no budget. Any later failure rolls these writes back with the business SAVEPOINT.
7. Project the actual resulting SessionSnapshot with only this genuinely completed command removed from pending IDs; encode the actual complete response bytes. Build and INSERT the complete FINAL transport from the actual pre-settlement and final versions, response bytes and events. Its trigger checks existing source facts and defers only final journal closure. Fixed order: actual producer writes -> actual snapshot/bytes -> complete FINAL group -> control staging -> journal. There are no placeholder or mutable final proof rows.
8. Stage final_response once only when complete FINAL group exists and actual bytes satisfy its root. Set control CONFIRMED only with that group, exact task set/original reply and prospective final body. These writes have a final-group deferred final_commit obligation.
9. INSERT initial COMPLETED or CAS UPDATE old ACK body with RowsAffected1. BEFORE trigger recomputes all actual OLD/NEW/header/schema/group/source facts. AFTER trigger inserts final_commit. No terminal response before outer commit.
10. Exact replay reads sole journal only. Recovery may change pending REQUESTED->RECONCILING without proof creation; CONFIRMED and finalized history remain byte exact. Typed rejection rolls back business SAVEPOINT, including all F08/group/Run changes, preserving only handler-authorized rejection identity/journal.

Step7 fixes a detail from earlier prose: no timestamp/event/snapshot hashes are invented in advance. The actual private producer returns actual version/event objects inside Tx. Final group is built from those real facts; full source assertions at journal time plus normal transactional rollback are the authority. SQL protects original persisted anchors, finalization guards, and relational commit obligations; it does not authenticate a hostile writer that rewrites all canonical Run/Task/event history as an alternate producer.

## Legacy, launch monotonicity and real completion

SQL24 populates immutable legacy exclusion before enabling new-dispatch origin triggers. Old Run IDs can never obtain a new origin, including after later epoch/version changes. This does not forbid a genuine old Run's new-epoch dispatch under unchanged admission/lease/reconciliation guards: it starts PREPARED but retains null origin and cannot use never-launched finalization. New post-boundary Run native dispatch requires exact PREPARED, worker/locator empty, identity {}, observation0/hash empty plus its immutable actual birth and claim event. No backfill.

Dispatch transitions allowed with all immutable manifest/locator keys untouched:
PREPARED->STARTED: fresh nonempty worker, journal_locator=dispatch_key, empty identity, zero observations; no F08 completed never-launch member, current original Run nonterminal and uncancelled, same lease/executor/Task/epoch; coordinator admission still checked.
STARTED->STARTED: only first empty->actual bound native identity before resume; same worker/locator and zero observations. Other fields unchanged except updated_at. Repeating identical identity without changing any authority may remain existing behavior but never advances origin.
PREPARED->UNKNOWN or STARTED->UNKNOWN: actual existing markUnknown may set reason/updated_at, preserving worker/identity/observation; unknown is never eligibility for never-launch.
UNKNOWN->UNKNOWN: reason/updated_at only, no identity erasure.
STARTED/UNKNOWN->OBSERVED: exact original nonempty identity/worker, actual observation sequence >= old with hash equality on same sequence and real stopped/drained/cleanup observation. Existing ObserveRuntime updates dispatch before observation INSERT, so SQL permits that source order with a deferred observation tuple obligation supplied by SQL24; before commit actual observation must exist and match.
OBSERVED->OBSERVED: only higher sequence or identical exact observation permitted under original observation semantics; no new worker/identity or rewind. OBSERVED cannot become UNKNOWN/PREPARED.
Everything else fails. No state rewrite to PREPARED, no empty-PID shortcut. Protected INSERT collisions reject before REPLACE/UPSERT independent of recursive_triggers.

Native never-launched requires current post24 origin, original PREPARED never STARTED, actual original ownership/lease hash, no selected-epoch execution/observation contradiction (only the exact proven prelaunch checkpoint carry is allowed), with complete settled prior-epoch history revalidated, no SENDING/SDK_ACCEPTED/UNKNOWN queue entries, every queued original member genuinely dropped/consumed and restore_fenced=0, and no unresolved effect or orphan MODEL reserve. Authentic non-MODEL local-launch reserve remains unchanged. Hold resourceWriteLock through settlement. If cancellation wins, actual Run/Task become CANCELLED, original command becomes COMPLETED and a released coordinator cannot start. If STARTED wins, preserve original ACK until real cleanup and ledger/queue facts settle, then complete the same original command. Repeated missing-proof ACK is not acceptance of this happy path.

Legacy old ACK without immutable original header/membership/proof remains typedblocked/reconciling and recoverable through original genuine reconciliation. It is neither rewritten nor silently backfilled. Old23 PREPARED with no origin cannot use new-fastpath. No new lifecycle/lease/token reset, scheduler, retry, budget release or fake observation.

## Backup/upgrade and remaining gates

New SQL24 source and all its objects are inventoried separately; SQL22 four queue tables and SQL23 three tables/fourteen objects remain byte-frozen. Added indexes/triggers are separately named F08 objects, never hidden in old accepted fingerprints. All legacy cohorts, origins, complete group documents, derived rows/pins, final commits and observation obligations are included in backup typed inventory; validate exact source schemas and full closures before archive/publication/recovery and after restore. Pending restore adds only existing fence/reconciliation facts; no proof creation. Completed historical original Run proof is checked against immutable source versions/artifacts, not current dispatch/Task head after restore.

23->24 public plan holds exact old23 source lock through snapshot/migration/recovery/validation/rename/report/final publication. Capture source cohort against authenticated snapshot before schema-only migration, validate all old rows unchanged before recovery and exact permitted recovery deltas afterwards. No old program/source self-attestation. Actual accepted old22/23 programs must prove correct ownDB behavior, future24 refusal and read-vs-write outcomes; package init in new binary is not old-binary evidence. Fresh source, malformed/future/host-only guards remain.

All twelve groups in review-minimal_verification.json remain mandatory, including real legal >1MiB response, raw row/REPLACE/UPSERT controls with recursive_triggers OFF, incomplete group at COMMIT, forged both digest columns, deleted dispatch, legacy origin insertion, real before_launch_fence/dispatch_started barriers, public backup/restore and original program writer contention. Every named control is FUTURE_NOT_RUN here. Source20 is the newly proposed scope requiring whole independent review; complete DDL semantics and connection behavior must pass actual isolated controls before source acceptance.


## v5 precedence and explicit scope extension

The complete R1/R2 algorithm, private payload additions, exact34-category registry and new controls are in evaluator-v5.md and future-gates-v5.json. These supersede every all-epochs-as-birth or generic duplicate-row reading of earlier text. No permanent-birth field is treated as the current rebuilt lease/runtime. No response cap or new public lifecycle is introduced. All other v4 atomic group, journal, UDF, publication, old-writer and compatibility obligations remain.
