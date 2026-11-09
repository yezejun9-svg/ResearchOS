# F08 pure evaluator candidate — receipt preparation only

The proposed single Go file contains concrete source-derived implementations, not an all-error mode switch. It is nevertheless **incomplete and prohibited from installation with SQL24**. No Go parser, compiler, gofmt, SQLite, driver registration, product or native test ran. Text assembly and metadata hashing do not establish compilation or correctness.

## Implemented source components

- Fixed 34-category widths, SQL storage/null classes and actual unique keys; `domain_refs` retains duplicate occurrences. Versions are strict-decoded and schema checked, receipt/content hashes recomputed, current heads compared with immutable version bytes.
- R1 walks the existing `relationKind` semantics, retains relation-array multiplicity and ordinary array indexes, resolves ID-only historical targets from actual immutable relation rows, and derives exact closure/unique pins. This requires future real producer fixtures; a source tuple supplied directly to a unit test is not database authority.
- Mode0 derives original global identity/private header, request Q and exact current Session/target/membership, and implements NO_RUN admission. Modes1/5/6 implement a NO_EXECUTION/empty-queue subset, source Task/event versions, exact pending-ID union, final response staging and sole-journal raw byte closure. Mode7 verifies actual complete parent/member/pin materialization.
- Mode4 implements monotone dispatch transitions and original OLD/source matching, preserving identity/manifest/observation fields; SQLite's deferred observation obligation remains necessary and is not replaced by this function.
- Modes2/8 implement initial qualification origin derivation from actual Run revision1, immutable Task claim/event/outbox, qualification plan/marker/profile facts and exact closure. The first epoch is taken from Run and is not assumed to be1.
- Effect sequence/prefix and later Run/route/carry logic are concrete reusable components. They are **not complete native authorization** and are not presented as such.

## Still incomplete — implementation work, not merely missing execution permission

1. Ordinary qualified admission: reconstruct all original qualification evidence, profile/model and purpose/permission predicates, accepted dependency vector/context, not just profile labels. Existing bootstrap source code checks retained facts but has not yet duplicated all pure model/profile validity predicates. Its acceptance path requires independent review before any integration.
2. Native admission and finalization: all original runtime binding/epoch/origin history, full native observation artifacts and sealed use bytes, SDK consumption/drop/clear/abort/idle chains, and same-generation queue receipts. `f08NativeProofGap` prevents the corresponding admission/final paths from returning success. An arbitrary `proof_kind` never selects the empty subset.
3. Accounting: `effectHistories` and `f08EffectPrefix` preserve original keys/sequences/epochs and raw digests, reject unresolved latest outcomes and preserve earlier UNKNOWN. They do not yet implement complete receipt-to-cost causal correspondence or authentic local-launch/qualification reserve classification. More than one cost row currently refuses. This is incomplete policy code, not evidence that the contract forbids legitimate reconciliations. SQL rowid ordering cannot be invented from ID/timestamp sorting.
4. Historical final/backup verification: captured immutable Run/Task/Session/queue facts must be revalidated without replacing them by today's heads. `finalGroup(...,false)` currently refuses; no backup acceptance is claimed. Existing generic replay/source/SQL guards must remain until this is complete.
5. Later epochs: actual `currentRuntimeAdmission` does not persist its `operation` parameter. The separate proposed one-field patch is unapplied. The real checkpoint caller already passes `checkpoint_resume`, and replacement passes `replacement`; no alias mapping is necessary. Even after this patch, full contiguous prior-origin/native/effect closure and ordinary qualification remain implementation work. No future RUN_CHANGED is sought.
6. Mode3: the frozen SQL contains no mode3 action literal. It remains `F08_CALLER_CONTRACT_UNBOUND`; a reviewed exact caller/source23 inventory interface is needed. No invented `legacy.insert` alias or backfill exists.
7. The 34-source registry omits client event/message tables. The specified final snapshot binding can be checked against Session rows and exact pending union; full transcript/projection semantics cannot independently be reconstructed from these tuples alone. Full response schema validation still runs. A source review must decide whether the fixed binding plus real projection producer is the intended contract boundary; adding categories is not authorized here.
8. Driver opt-in/pin and physical connection installation/PRAGMA/upgrade are unchanged, unexecuted dependencies. The actual pinned modernc v1.60.1 lacks `FunctionImpl.Innocuous`; the candidate intentionally requires a separately registered fork/pin change before it can compile.

## Clarifications supported by actual source

- Queue `content_hash` and receipt `body_hash` are `Digest(original Bytes(...))`, not a re-encoded canonical `Hash`. Candidate checks use original raw decoded bytes.
- `rebuildResourceSession` actually emits `native_resume:false`. The later-row component retains that actual field; the R2 prose's abbreviated list does not authorize stripping it.
- `dependenciesReady` refuses duplicate Task dependency IDs at actual claim. This does not remove legal duplicate `domain_refs` tuples or permit deduplicating an ordered retained dependency snapshot. R1 multiset controls and actual claim positive controls must use their respective producer rules.
- Request `request_hash` is original `Envelope.ContentHash()`, not SHA(raw envelope). Header digest and original response digest are raw-byte hashes. Changing one supplied digest does not repair changed original bytes.
- Same-process pure callbacks establish internal consistency of SQL-supplied immutable facts. They do not authenticate an attacker who replaces the entire database or all schema/producer history.

## Proposed verification and execution conditions

New pure source proposals include 33 named leaf controls in 8 top-level functions. They are NOT_RUN, as are the preserved prior12 top-level proposal controls. Structural parent/member tests intentionally do not qualify source admission. The old malformed one-column proof cases still require errors; only the obsolete expectation that every mode is an unimplemented stub changes.

Before execution: independent source/purity review; reviewed driver fork and exact dependency pin; explicit source lease; full build/dependency/OS/input closure; compile and test-only component grant. Before SQL24: finish all implementation gaps above, bind mode3 caller, preserve existing SQL22/23 and original default-deny semantics, and run the original frozen 40 causal/upgrade/backup controls on physical connections with trusted_schema OFF, foreign_keys ON and both recursive trigger settings. No current proposal author can sign acceptance.

Old 6ed source and registry-label erratum are preserved. Four metadata/read failures remain separate original receipts. Nothing modifies Root counters or canonical state. All new code is proposed text inside this receipt namespace.
