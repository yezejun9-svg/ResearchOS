# ATTACH-RESTORE-001 Source revision

Status: SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_BUILD_AND_TEST. Not production readiness or native acceptance.

The rejected prior Source and its independent review are preserved by pinned HDF/MF references in public-input-pins.json. This revision owns only candidate-root/internal/domain/client_protocol.go and the supplied test Sources. The prior contract test file is an exact byte copy; the restore test file is new. Main, T6, prior Source, shared migrations, Root canonical files, and the other author's legacy test branch are not modified.

## Contract and producer mapping

- client_protocol.go handleWrite session.attach now calls clientAttachRestoreState after the existing authentication/project/session/revision/epoch/archive gates and before any lease update. Existing Execute identity and cached response lookup are unchanged.
- No run or no (project, run) backup_restore_barriers row preserves ordinary live-owner lease-only renewal, including an active Run.
- A barrier requires the current Run lease_epoch and current Run children_stopped=true plus queue_empty=true. Terminal status alone never replaces those flags.
- The read gate selects runtime_observations only for that exact project/run/current Run epoch. The latest record must parse, have receipt_hash=Hash(body), producer spec.run_id/task_id/epoch matching the current Run, observed_at strictly after the latest restore barrier, and both children_stopped=true and queue_empty=true. It rejects absent, wrong project/run/epoch/spec/hash, stale/equal, or partial evidence. Source does not synthesize or insert valid evidence. runtime.go observeRuntime remains the trusted producer; its coordinator/dispatch checks are unchanged.
- Once the latest observation is valid, the gate records the earliest valid fresh observation of that same epoch. A session generation is recovered only if its durable CLIENT_HANDOFF has actual producer fields: matching outbox project, event session/run/protocol/command/sequence; payload target client and writer client equal current owner; writer epoch equals current session epoch; previous_epoch equals current epoch minus one; effective_at strictly after barrier and at or after matching fresh observation; writer expiry after effective_at. This uses no invented event fields or updated_at surrogate. A newer legitimate observation does not unnecessarily invalidate an already recovered generation.
- If fresh settled evidence is valid but no such event exists, renew is disabled and the existing HandoffEpoch/CAS plus writer attribution plus CLIENT_HANDOFF plus actual terminal AttachResult transaction performs one real transfer. Exact-command replay still returns the persisted response without another write.
- An already recovered generation can use normal same-owner valid-lease renewal. Another client or an expired lease follows existing settled transfer. No barrier, observation, run state, queue/control fence, or resume policy is changed by the new helper: it contains SELECT operations only.
- No schema field, migration, new epoch relation, invented pause, CANCEL, provider call, owner signature, or cached ACK rewrite is introduced.

## Source test coverage (not executed)

client_protocol_attach_restore_windows_test.go contains ten deliberately invalid restore fixtures: absent, wrong-project, wrong-run, wrong-epoch, stale, equal-barrier, children-only, queue-only, wrong-spec, wrong-receipt. Each verifies both same-client future-lease renewal and different-client acquisition are REJECTED/SESSION_BUSY, Session lease/revision/epoch/owner/watermark/bindings remain unchanged, no CLIENT_HANDOFF is emitted, exact replay is stable, and Run/barrier bytes are unchanged. Old Run settlement flags are deliberately true, so missing fresh evidence cannot be hidden by those flags. Invalid observation INSERT statements are test Source only and have not been executed. No valid fresh correctly bound settled observation is authored.

TestClientAttachRestoreGatePreservesOrdinaryActiveRenewal reuses the preexisting active-owner real orchestration fixture. The previous five attach contract test functions are carried unchanged, including original profile/runtime/session binding gates.

## Remaining resource and acceptance gap

BLOCKED/PENDING_ROOT_RESOURCE for a true post-restore valid-fresh positive fixture. Root must supply an authorized real runtime/coordinator observation and settled current Run under a real restore barrier. The Source author has no such resource and has not called ObserveRuntime with synthetic positive input, executed SQL, run Go/gofmt/native/model, or replaced missing real evidence with skip/PASS.

After independent Source review and isolated composition, Root must verify:
1. A valid fresh current-epoch observation with no recovered Session generation causes one real epoch increment, the existing two revision increments (HandoffEpoch plus journal), one CLIENT_HANDOFF, and true COMPLETED/AttachResult preserving bindings.
2. Exact command replay does not repeat that transfer or lease write.
3. A different command from the same owner on that recovered generation renews only the lease; a new later valid observation of the same epoch does not force another transfer.
4. A later restore barrier or changed current Run epoch invalidates the old recovery proof; no new valid observation means SESSION_BUSY. Fresh valid current evidence then needs a new post-barrier generation.
5. Existing queue restore_fenced/resume_requires_user and control gates remain set; the helper never clears them.
6. Execute the negative and ordinary active Source tests and reconcile the separately owned legacy ACK test before broad-suite claims.

Known open branches remain active asynchronous takeover and historical cached ACK reconciliation. Original native failures, prior Source rejection, and mechanical ordinals 827/829/831 remain historical facts; this revision adds actual Source read failures 832 and 834 without resetting counters.

## Verification limits

Only Python stdlib file hashing, exact inverse edits, manifest checks and a Go lexical delimiter scan are performed by this author. These do not constitute Go parsing, compilation, test execution, native evidence, or independent approval. Input pin checks intentionally exclude canonical Root progress files which advanced legitimately to CP359.

