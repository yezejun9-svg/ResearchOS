# Main23 public backup to Main24 isolated handoff

Status: SOURCE_IMPLEMENTED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_RUNTIME.
Author: codex:/root/attach_restore_independent_review.
No execution grant, Source acceptance, Main adoption, production acceptance, W05 acceptance or Goal completion is issued here.

## Public entry and exact boundary

New public CLI command: backup upgrade-prepared-backup. New library API: UpgradePreparedAbandonmentBackup.
Inputs are the existing original schema23 database, the existing ordinary public backup created by the preserved Main23 program, the separate recovery key path, exact source23/target24 release roots, distinct preserved source/target executables, a new destination, the fixed schema23-to24-prepared-abandonment-v1 plan, and a Root-reviewed binding file with its expected sha256: digest.

This target coordinator must equal TargetProgram bytes. SourceProgram and TargetProgram must have distinct SHA-256 digests. It never starts the old executable, recreates the existing backup, edits its manifest, or calls the old schema23-to24 upgrade-local entry. The unchanged old entry still has its source-program identity rule. The new command uses the already-produced public create result.

A valid binding is an external provenance input. Matching its JSON fields and file hashes does not authenticate the asserted producer or prove an execution took place. Root must independently verify the original Native invocation, exact old program identity, zero exit and stdout/manifest relationship before constructing the binding. Existing Root GEN02 actual inputs are reported by Root, not independently accepted by this Source author. No "review passed" input is manufactured.

Binding schema is researchos.public23-to24-backup-handoff.v1. All hashes inside this product binding include sha256:. The three-key Source package references in HDF/MF instead use plain hexadecimal hashes. observed_backup_exit must explicitly be 0; null/omission is refused. producer_stdout must be the raw JSON manifest stdout from the source create command, and producer_observation points to the finite actual invocation evidence independently reviewed by Root. Its bytes are pinned, not interpreted as an authorization token. The binding template contains nulls and is deliberately unusable until populated from actual observations.

## Existing validation and new refusal gates

- The ordinary RESEARCHOS_BACKUP_V1 MAC and encrypted file digest/length validation, required portable export, queue sidecar, workspace path checks, contracts, integrity and foreign keys remain in force.
- A private fixed-policy marker permits only the existing same-host workspace identity preservation and the late isolated DDL callback. The public handoff policy does not set allowProtected; ordinary public protected-artifact refusal remains in force.
- The existing Windows source-root lease and exclusive source database connection span the operation. Source rows, schema, workspace identity, both exact release inventories, both program hashes, binding/manifest/stdout/observation pins and encrypted backup are rechecked during handoff.
- Existing backup rows must exactly match the live offline source snapshot before recovery. A stale or mixed snapshot is refused. Recovery effects are checked separately from migration effects.
- The original may have either the fixed template Source23 shape or the fixed Restored23 shape produced by an earlier public restore/upgrade. The latter includes backup_restore_barriers and its trigger. Arbitrary schemas are refused. The receipt records the selected source and corresponding target shape.
- Original recovery, relocation, fence and acceptance recomputation precede the fixed SQL24 DDL. Rehearsal first rolls back and checks restoration, then commits only within the isolated restored copy. Existing business rows must remain unchanged by DDL; only migration24 and the empty prepared-abandonment proof table are added.

The completed receipt is prepared-abandonment-public-backup-handoff.json. It has a separate receipt schema and is not named prepared-abandonment-rehearsal.json. It does not satisfy the existing original-root Native apply path's receipt contract. Original-root DDL still needs separately reviewed Native MigrationToken / Owner / lease authority and a compatible original-apply contract. This source slice does not extend that authority.

Errors after the generic restore has published the isolated destination can leave that isolated directory present. No automatic cleanup or reuse is attempted. Root must retain the failed invocation and output, use a fresh destination for an authorized next attempt, and not infer success from a restore report when the command returned an error. The original and existing backup remain the recovery base.

## Integration and actual checks still required

The base is prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6. Its prior composition prerequisites (prepared-abandonment v4 and the reviewed Native authority source) still apply. Eleven base candidate files are copied byte-for-byte for provenance. Incremental integration changes only internal/domain/backup.go and ops/backup/main.go, and adds internal/domain/backup_prepared_abandonment_handoff.go plus its new test file. Existing Main dirty work and older evidence must be preserved. Root must not copy the candidate wholesale over independently changed source.

Root should first arrange nonauthor Source review. In its separately owned candidate, Root can then compose dependencies, gofmt/build, run only the new metadata boundary tests and relevant regression checks justified by these two changed production files, and perform the new real dual-program boundary. The actual boundary must use the preserved Main23 public backup and a genuinely different Main24 executable. Re-running successful Main20→21→22→23, old fixtures, SQL suites or unrelated W09 stages is not a requirement of this source package.

The targeted future command has the following shape (placeholders require actual pinned inputs):

    TARGET24.exe upgrade-prepared-backup --db ORIGINAL23.sqlite --backup EXISTING_BACKUP23 --out NEW_ISOLATED24 --key-file SEPARATE_KEY --source-root PRESERVED_RELEASE23 --root RELEASE24 --source-program MAIN23.exe --target-program TARGET24.exe --plan schema23-to24-prepared-abandonment-v1 --handoff-binding REVIEWED_BINDING.json --handoff-binding-sha256 sha256:ACTUAL_BINDING_HASH

Root must separately verify schema24 backup/restore with the matching target program before broader W05 claims. This handoff receipt alone is only the isolated 23→24 leg.

New Go tests include missing/nonzero producer exit, wrong command/schema, identical/swapped/malformed program pins, mixed backup identity, wrong migration inventory/format/purpose/stdout, preservation of ordinary-public policy selection and strict digest shape. They were authored but not compiled or run here. No synthetic test fixture is a historical producer qualification.

## Author evidence

build_source.py ran once: actual chunk 50a0d6, outer 0 and explicit Python 0. It held verified source handles, generated the candidate, checked exact inverse patches for the modified existing files, and proved preservation of eleven base candidate files. source-controls.json describes source-text/byte checks only. The subsequent final manifest re-read guard is an explicit three-line source addition, recorded in final-source-checks.json; it does not replay the builder or old controls. The newly authored Go tests were added after that initial source build.

Diagnostic appendix preserves Root-assigned originals 1227 (a27c9f) and 1228 (81ce7e), including complete original call/result and successful prefix. Both are non-product read diagnostics with outer 1 and Python/Native/SQL null. Their original calls were not replayed. capture_originals.py completed as actual decd2b with outer 0 and explicit Python 0.

No Go, gofmt, SQL, Native product command, model, Root stage, canonical writer, Main mutation, provider or network call was performed by this source author.

