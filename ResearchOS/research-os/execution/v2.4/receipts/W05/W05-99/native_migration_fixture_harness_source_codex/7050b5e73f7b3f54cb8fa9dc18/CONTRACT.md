# Native migration fixture harness — Root execution contract

Status: SOURCE_IMPLEMENTED_PENDING_ROOT_BUILD_NATIVE_EXECUTION_AND_INDEPENDENT_REVIEW.
This is a synthetic, local schema23-to24 migration harness. It adds one build-tagged test and one Root-only Python broker. The author has not executed Go, native programs, SQL, signing, enrollment, DPAPI, private resource reads or provider calls. It creates no production entry point and installs no authority.

## Source composition and ownership

Overlay candidate-root/internal/domain/native_migration_authority_harness_windows_test.go only into Root's new isolated accepted composition. The test requires Windows and build tag researchos_native_recovery_harness. Root must preserve accepted native-authority production files and current historical/schema22 fixture corrections. The broker stays outside production code and receives only a public request path.

The test reuses preparedUpgradePublicFixture, which constructs an exact schema23 synthetic database through existing versioned fixture and public business APIs. It does not construct MigrationToken, Token, nativeSession or an authority setter. Real migration authority must come from the enrolled recovery_root -> production apps/control inherited native channel. The synthetic queued Run is an invariant subject; it is not an eligible native-abandonment fixture.

Static input provenance includes both original native20/migration10 Source refs and the actual API files read in the earlier accepted worktree. Root's current four program paths, build invocation receipts and compiler inventory are separate inputs. Matching binary bytes do not make their build/source paths interchangeable. Root must freeze the actual composition used now.

## Prerequisites and frozen public configuration

Root must first independently accept the private-stdin helper revision and its actual six public dummy cases. Its exact Source pin is recorded in base-pins.json. Root must freeze the Go toolchain/selected compiler inputs, Python runtime/native dependencies, reviewed helper, broker, product programs and source inventories with existing read guards, and launch the Go test inside its owned Job. Source author does not assert that an inherited outer Job is the recovery Root's distinct inner Control Job.

Use one fresh case directory per attempt, with new copies of the accepted Root and Control executables in the same directory. There must be no recovery-release.json, current-schema23-to24-grant.json or consumed-schema23-to24-grants there. Do not reuse an old fixed-file/nonce namespace.

Set RESEARCHOS_NATIVE_MIGRATION_HARNESS_CONFIG to an absolute public JSON path. Exact PascalCase keys:

- Schema: researchos.synthetic-native-migration-config.v1
- Case: one case from the matrix below
- CaseID: unique public identifier
- OutputDirectory: absolute fresh path whose parent exists; the test creates it exclusively
- BuildRoot: actual isolated module root used by this test
- RootSigningPublicKey: reviewed 32-byte public Ed25519 key in hex; no private key or private resource reference
- RootProgram, ControlProgram, BackupProgram, EnrollmentProgram, PythonProgram, BrokerSource, PrivateStdinHelper: exact RawPin objects

Each RawPin has lowercase keys role, path, sha256 and bytes; SHA must include sha256: prefix and paths must be absolute/canonical/non-reparse regular files. Roles respectively are root-program, control-program, backup-program, enrollment-program, python-program, broker-source and private-stdin-helper. The runtime verifies both role and actual bytes. EnrollmentProgram is pinned for Root's external signing workflow; the test never invokes it.

Retain existing reviewed public fixture environment, especially the schema22 helper/source hash and historical configuration fixture resources. They remain fixture-construction dependencies. Do not substitute a current-schema database for the required exact schema23 fixture.

Root's reviewed invocation uses the pinned Go executable, -tags researchos_native_recovery_harness, -run ^TestNativeMigrationAuthorityHarness$, -count=1, -timeout=25m and ./internal/domain. A 20-minute internal review window bounds one case. Freeze source before compilation and preserve compile-list/build provenance. The Source author has not run gofmt or compiled this file.

## Credential and process boundary

The test issues current local Owner and actual Executor credentials for one hour before its baseline snapshot and backup. They stay in Go process memory. Only the selected input is copied by os/exec through its anonymous stdin pipe to the reviewed Python broker. The broker checks FILE_TYPE_PIPE, reads at most 4097 bytes into a mutable buffer, rejects outside 1..4096, and gives the mutable buffer to the accepted helper. Python runs with -I -S -B -X utf8, a fixed public SystemRoot/WINDIR environment and a fixed public request path. The helper creates the bounded native input PIPE and starts the selected binary suspended, assigns its owned Job, then resumes it.

No Owner token enters argv, environment, approval files, configuration, receipt fields or logs. Go strings cannot be guaranteed securely erased; clearing string variables drops references and is not a memory-erasure claim. The Python helper and broker clear known mutable buffers. Public database snapshots contain complete typed-row hashes/column inventories, not the original credential plaintext. Root must review selected child output for non-disclosure.

The broker preserves the original helper result and stdout/stderr raw files; it does not convert nonzero native exit into success. Broker exit zero means process/Job cleanup completed, including native failures expected by the test. Every native case still checks the actual native exit plus exact designated rejection. The broker's NativeAuthorityAcceptance remains false.

## Phase sequence

1. Construct exact23 fixture, issue credentials, capture before.rows.json and fixture.public.json, close the database. Execute the actual accepted backup program with upgrade-local and exact Go LocalUpgradeOptions. SourceProgram is that same backup binary; TargetProgram is the Control binary that will execute the migration. Backup uses a public dummy stdin input, never an Owner.
2. Verify original complete typed-row hashes/schema unchanged after actual encrypted backup plus isolated restore/rehearsal. Preserve all native raw outputs, encrypted payloads, manifest and the production rehearsal receipt.
3. Write 01-release.payload.json as exact Go-marshaled bytes and 01-release.ready.json. Root independently verifies public source/binary pins and the actual enrolled public key, then uses its separate private signing workflow to create the fixed recovery-release.json. Root publishes 01-release.approval.json with Action=release-signed, PayloadSHA256 and SignedSHA256. Both digests have sha256: prefix. The test compares exact payload bytes and wrapper digest; signature/capability acceptance is performed only by production Root.
4. Build the complete MigrationBinding from actual SID, native root/DB file identities, full source/target SQL inventories, exact Options JSON, all encrypted payloads, rehearsal receipt, baseline row hash and program identities. Create 02-grant.payload.json and 02-grant.ready.json. The normal grant lifetime is four minutes, with a fresh 32-byte nonce. Root independently reviews and signs the indicated sign_kind at current-schema23-to24-grant.json, then publishes 02-grant.approval.json with Action=grant-signed-and-invoke and the two exact digests. No author-signed grant is supplied.
5. Invoke Root schema23-to24 through the private pipe, except the intentional missing-channel case which invokes the production Control private argument directly. Parse actual native exit and stderr/result. Capture after.rows.json and verify exact versions and complete row/schema invariants. Positive alone runs one explicitly planned replay of the same signed grant.
6. Emit 05-case.result.json only after the case assertions pass. This says EXECUTION_REPORTED_PENDING_ROOT_INDEPENDENT_REVIEW, formal=false. Cleanup always writes 06-fixture-retained.ready.json after successful fixture construction, including assertion failure, and keeps temporary fixture resources alive while Root inspects them. Root then publishes 06-release-fixture.approval.json with Action=release-fixture (other approval fields may be omitted). Only then may normal test cleanup remove temporary fixture paths. A hard kill/Go timeout or expired review window cannot guarantee this graceful retention.

Approval files are created by Root only after concrete review. Do not place private signing material or Owner credentials in them. Empty/newline-reformatted payloads fail the exact byte comparison. A failed case is inspected and closed; no automatic repeat with a fresh grant is implemented.

## Required nine-case matrix

| Case | Intended native evidence |
| --- | --- |
| positive-replay | Real nonzero MigrationToken commits schema24. Exact 1..24 versions, exact target schema, all original typed rows unchanged, only one migration row added, empty abandonment proof table. Result says committed=true, abandonment_performed=false, financial_closed=false, provider_requests=null. Same grant then rejects AUTHORITY_MIGRATION_GRANT_ALREADY_USED without changing post-migration state. |
| missing-native-channel | Direct Control migration argument, public dummy input, no bootstrap; rejects AUTHORITY_PRIVATE_INHERITANCE_REQUIRED and exact23 rows/schema remain unchanged. |
| wrong-purpose | Root signs a valid adoption-purpose Grant using sign_kind=grant; it is intentionally placed at the migration fixed path. It must reject AUTHORITY_ISSUER_SIGNATURE before accepting the migration channel. No adoption history is fabricated. |
| mismatched-database | Grant uses a measured native identity from a separate real temporary file while the binding path remains the fixture DB; rejects AUTHORITY_MIGRATION_GRANT_NATIVE_ID. |
| release-pin-mismatch | Independently reviewed negative release deliberately contains one wrong source hash; accepted source bytes are not edited. Rejects AUTHORITY_RAW_PIN_MISMATCH. |
| expired-grant | Deliberately old valid four-minute issue/expiry interval; rejects AUTHORITY_MIGRATION_GRANT. |
| missing-dynamic-pin | Remove exactly one source-inventory role, preserving five mandatory raw roles, valid Owner and native channel. Must reach AUTHORITY_MIGRATION_REQUIRED_RAW_PIN_ABSENT from the real MigrationToken.RequirePin gate, not an earlier channel/credential failure. |
| wrong-owner | Send the real local Executor credential issued before the baseline. Valid native channel/token/pins must reach current project Owner required; original state unchanged. |
| lease-occupied | Test actually acquires DataRootLease after signed grant review and holds it throughout the native call. A second acquisition must produce errors.Is(ERROR_SHARING_VIOLATION); its measured localized error becomes the exact expected native rejection. Record actual holder PID/birth and lease closure; original exact23 state unchanged. |

All eight negative cases compare whole original table/typed-row hash inventories and exact schema fingerprint; the positive replay compares the exact post-migration state. Root must independently read the retained fixture and raw outputs, verify actual Job/guard closure and negative rejection layers, then decide acceptance.

## Explicit remaining scope

No native case has been executed by this Source author. Go compilation, Root release/grant signing, actual Root->Control token acceptance, SQLite positive commit and nine-case outcomes are unverified here. Root's separate full offline domain run had failures; this focused harness cannot declare that broader run passed.

Exact native prepared abandonment remains a separate unfinished gate. It needs a genuinely matching public prepared fixture, live/expired lease semantics, exact Run/Task/qualification/admission linkage and all sixteen historical evidence roles tied to actual original processes/Jobs/source guards. This migration fixture supplies none of that history and must not be promoted into an abandonment positive by inventing records or injecting authority.

Failure-origin.798.json preserves the one new nonexistent-path read error. The earlier rg no-match is preserved as NO_MATCH with no new failure ordinal. All source-author operations remain read/static/own-namespace writes.

