# Root-only private stdin helper Source

Status: SOURCE_IMPLEMENTED_PENDING_ROOT_NATIVE_TESTS_AND_INDEPENDENT_REVIEW.

This adjunct supplies a real Windows anonymous PIPE to an independently reviewed child. It does not mint Token/MigrationToken, verify a release, sign a grant, choose an Owner or read any private resource. Its caller must be Root's reviewed orchestration; no production command/JSON/env key setter is added.

## API

`run_owned_private_stdin(argv, cwd, env, stdout, stderr, timeout, private_input, creation_flags=0)`

The mutable `private_input` bytearray holds 1..4096 current-Owner bytes supplied in memory by Root. The helper clears this supplied bytearray in place on every return path. Root remains responsible for any prior copies and for keeping Owner bytes out of command line, environment, stdout/stderr, raw tool input, receipts and files.

Each invocation requests an anonymous pipe, validates both ends as FILE_TYPE_PIPE, then queries GetNamedPipeInfo on the read handle. It selects inbound capacity for a server-end reader and outbound capacity for a client-end reader, rejects message/unknown type, zero capacity or capacity below the bounded input, and uses PeekNamedPipe to require an empty pipe. Both original handles are non-inherited, exclusive and unpublished at this point. Only then does it perform its sole <=4096-byte WriteFile, with preparation-deadline checks immediately before and after. It clears the buffer and closes the writer before child creation. The requested 65536 size is treated only as a suggestion. Root must independently review these per-invocation checks and run the dummy native matrix before real credential use.

Only the read end plus stdout/stderr duplicates enter the explicit inherited-handle allowlist. CreateProcess remains CREATE_SUSPENDED; the unnamed exclusive KILL_ON_JOB_CLOSE Job owns the child before ResumeThread. PID/birth, primary exit, whole Job idle, timeout termination and handle cleanup preserve the pinned original implementation after normalizing line endings, apart from unconditional private-buffer clearing in finally. Raw line-ending equality is not claimed.

Caller stdout/stderr streams remain open. The helper returns only booleans about pipe preparation and buffer clearing, plus the original process/Job receipt. It never records input content, hash or path. A trusted child's output must also be reviewed for non-disclosure; this helper cannot prevent a selected executable from echoing its input.

## Root independent validation

Review revision.patch against original windows_owned_process.py SHA6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad. Pin/freeze this Source, the original helper, Python source/dependencies and runtime_resource_paths() native module inventory using the already reviewed SourceReadGuard. Importing this helper starts no process.

Run `python -I -S -B -X utf8 root_verify_private_pipe.py <fresh-absolute-output-directory>` only under Root's existing owned-process harness. The supplied probe uses fixed public dummy values. It checks real PIPE + EOF, exact 4096-byte input, a nonzero child exit, timeout/whole-Job termination, and empty/oversized-input rejection with caller-buffer clearing. Inspect every actual invocation, stdout/stderr and validation.closed.json. The probe driver stops after a failed case.

These tests do not prove the enrolled recovery protocol. After they pass, Root must separately review/sign fresh canonical payloads, invoke accepted recovery_root through this private pipe and verify SQLite whole-row/schema invariants.

## Migration fixture integration interface draft

The later synthetic fixture process must remain alive so its temporary DB and Owner credential remain valid. It creates fixture business state through existing public fixture APIs, issues all credentials before backup, closes DB, and runs the real ops/backup executable with `upgrade-local` and fixed schema23-to24 plan. SourceProgram must be this actual backup executable; TargetProgram must be the accepted apps/control executable used for native apply.

Root reviews the signed-release source/binary pins, native root/database identities, exact Go-marshal Options, complete source/target inventories, backup manifest/encrypted payloads, rehearsal receipt and original typed row hash. Grant lifetime is <=5 minutes and each attempt uses a fresh nonce. The fixture retains Owner only in memory and needs a separately reviewed private delivery path to the Root launcher; that bridge is not implemented or accepted in this adjunct.

Negative cases remain required: missing native channel, wrong purpose, mismatched native DB identity, release/source pin change, expired grant and replay. Negative rejection must preserve whole typed DB rows/schema. Positive migration must reach actual Root→Control→nonzero MigrationToken→schema24 commit with all prior rows unchanged, proof table empty and no abandonment. Exact native abandonment is a later distinct-purpose gate.


## Capacity review sources

[CreatePipe](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-createpipe) defines suggested buffer sizing and behavior when a synchronous write fills the pipe. [GetNamedPipeInfo](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-getnamedpipeinfo) supplies end/type flags and buffer sizes, including for anonymous pipes. [PeekNamedPipe](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-peeknamedpipe) supplies available-byte count without consuming input. This revision preserves the prior process, Job, inheritance and cleanup suffix after normalizing line endings.

The dummy child uses fixed Python flags -I -S -B -X utf8 so site/user startup and bytecode cache writes do not enter the probe. The capacity finding is a source-level boundedness gap; no host hang was reproduced by the Source author or claimed here.
