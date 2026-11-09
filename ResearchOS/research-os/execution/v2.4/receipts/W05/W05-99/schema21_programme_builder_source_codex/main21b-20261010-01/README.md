# Historical old21 programme builder — Source only

Status: `SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION`.

This package supplies a minimal Root-owned build leaf for the original historical `apps/control` and `ops/backup` at commit `f6e4a0ed54d697c7214a75743cd1b83dc3685ddb`, tree `9696c3a456a4786cbb5518c75ead66e6d8120a83`. It has not built or executed either programme. Source controls are author checks; a different Source author must review the package before Root registration. It neither grants runtime authority nor qualifies its own result.

The final calling contract is `contract.v2.json`, as identified by HDF. The initial `contract.json` is retained unchanged with its original Source controls and guard evidence. V2 clarifies pre-build versus post-build host evidence without changing the builder, frozen inputs or phase projection.

## Original source and bootstrap boundary

`frozen_source` contains exactly the 272 files in Task63's bounded control/backup/runtime input set: 3,105,007 original bytes. Source extraction used the already sealed real `git cat-file --batch` output; it did not run Git, create a worktree, clone a repository, copy a cache, or touch Main. Every materialized file retains its original Git blob SHA-1, whole-blob SHA-256, byte length and Git mode in `frozen-source-manifest.json`. The same manifest binds the Task63 source scope, source-object inventory and original batch output. Files are marked read-only. An independent reviewer can follow those explicit Source refs without recursively traversing business receipt dependencies.

The runtime input contract requires the full original consecutive numbered SQL sequence **1 through 21**, the original `next_v24_sessions.sql`, and the two original spec contracts. A maximum version of 21 alone cannot satisfy it. The public bootstrap source refs bind `apps/control/main.go`, `internal/domain/store.go`, `internal/domain/client_session_fence.go`, `internal/store/sqlite.go`, `ops/backup/main.go` and the exact go.mod/go.sum.

At this historical commit, `domain.New` applies the original numbered migrations and session addon, then `installClientSessionFence(ctx, tx, false)`, before committing the same transaction. The original control administrative command is:

```text
<independently-qualified-old21-control.exe> --bootstrap-owner --credential-file <new-scope-private-owner-output>
```

Its working directory must be the matching frozen historical SourceRoot and `RESEARCHOS_DATA_DIR` must name a new isolated data root. The admin action returns before HTTP/runtime coordinator startup and does not require a web build. This describes a separate future public-bootstrap scope. The builder does not execute that command, create credentials, read Owner files or private keys, query SQLite, or grant permission to run the product. Actual schema and bootstrap outcomes remain unobserved.

## Small adaptation of the accepted builder

The exact independently accepted Main23 Source builder is pinned as a library of pure primitives: path checks, environment projection, JSON stream parsing, OwnedJobs result validation, file inventory/pin checks, sparse input copying, and frozen-copy membership checks. Its accepted non-author decision is also pinned. This package never calls that builder's `run_registered_build`, `main_inventory`, or current-Main request/compiler projection. No current Main Source is consulted by this old21 builder.

The new leaf changes only the necessary boundary:

- The original historical 272-file set replaces the current-Main inventory; it is checked for exact membership, complete Git object identity and byte pins.
- Two fixed entrypoints replace a single backup entrypoint. Each gets its own declared dependency closure, export closure, programme output and binary metadata check.
- `require_resources` adds explicit live binding to independent Source review, qualified resources, Python/native runtime manifest and a previously completed Root authority-observation hostpair.
- Original errors retain raw stream/result paths and launch exceptions. A secondary raw-receipt publication error does not replace the primary launch error.
- New raw-output read guards, alongside source/frozen/export/programme guards, remain held until the single serialized cleanup pass.

`frozen_main` is an internal dictionary key inherited by the accepted pure helpers. Here it always names the new output scope's historical source copy. It never points to the current repository's Main Source.

## Calling contract

```text
old21_builder.run_registered_build(contract_ref, request_ref, live_root_scope)
```

Both refs have exactly `path`, `sha256`, `bytes`. Request JSON has exactly `case_id` and `output_root`. The case ID is 32 lowercase hexadecimal characters and the output is the contract's exact `output_parent/old21-build-<case_id>`. The package creates no actual request, scope, owner, lease, role change, registration or runtime grant.

The live Root object implements:

```text
require_registered(contract_ref, request_ref, source_author=...)
require_resources(contract_ref, input_manifest_ref)
require_phase(phase, request_ref, output_root)
receipt_context()
```

`require_registered` must verify actual current registration, owner, scope and lease, exact independent Source review, and the held bootstrap refs before any leaf file read. It must reject revoked/stale or merely serialized authority. Root owns the current build's actual outer host call and full original tool output capture, which is completed externally after this build call returns or fails.

`require_resources` returns exactly the fields listed in `contract.v2.json`: the same input manifest ref, independent Source review ref, resource qualification ref, runtime manifest ref, prior completed host binding ref, source author and different reviewer actor. The leaf checks their exact typed shape and repeats the live call before each Go phase and completion. Root's separately reviewed implementation must verify the underlying qualifications and actual host binding; a dictionary of refs is not itself authority. Python/runtime/loaded-DLL and Go/child-loader dependencies must remain held through the final Job and guard cleanup. The builder neither manufactures nor accepts a self-issued programme qualification.

`outer_host_binding_ref` has a strict causal meaning: it identifies a real, already completed Root registration/qualification/activation/current-four-files observation hostpair, bound by the caller to this build's scope and exact inputs. It must predate entering the build leaf. It cannot identify the current build's not-yet-returned complete call/output pair, a future timestamp, or a caller-authored JSON document pretending to be actual host evidence. Root's caller validates original host-log bytes, Root identity and observation ordering. Requiring the current build's full return before entering that build would be a cycle and is expressly prohibited.

The current build's complete original call/return pair is a separate **post-return external_capture obligation**. Root captures and binds it after the call returns or fails; independent actual programme review must inspect it before qualification. Its future actual ref, future Root scope, activation and runtime grant are all null in the Source contract. No future completed pair is manufactured by this package.

Root must persist any exception from the initial bootstrap gate and any returned state whose local close receipt could not be published. Root alone assigns original failure ordinals. No failure counter, canonical status or automatic retry is written by the leaf.

## Bounded future build

After Root's independent qualification and registration, execution has at most nine Go child processes:

1. `go version` against the exact pinned Windows/AMD64 Go 1.27.1.
2. For control: declared `go list -deps -compiled -json`, matching `-export` list, `go build -x -work`, then `go version -m` on the output.
3. For backup: the same four stages using `./ops/backup`.

Every child uses the existing exact-pinned Windows OwnedJobs runner. The primary is created suspended, assigned to its unnamed Job before resume, and checked for real exit, exact uint32 PID and uint64 FILETIME, Job idle, zero active children and closed handles. Compiler-descendant individual exit codes are not independently observed and stay null. `go version -m` reads the programme metadata; it does not launch the built programme.

The environment is the accepted allowlist with Go 1.27.1, Windows/AMD64/v1, CGO disabled, telemetry off, GOENV/GOWORK off, GOTOOLCHAIN local, offline module fetching, and `-mod=readonly -trimpath -buildvcs=false`. The original commit/tree is proven by the Source manifest. The builder rejects unexpected embedded VCS identity rather than inventing it for a blob-extracted source root.

The output GOCACHE starts empty, is shared only between these two fixed targets within the same new scope, and is never copied from a preexisting cache. Each target records declared/export closure, export BuildIDs and refs, cache vectors before/after build, retained `-work` files, environment and actual IO. Declared files, embedded data, go.mod and toolchain inputs must all belong to the already held input set; missing or new inputs stop execution. Source and sparse module copies are read-only and checked before every phase and completion. Whole historical source membership is also checked at each gate.

## Offline modules: what the eight missing ZIPs mean

`input-manifest.json` contains 272 historical source files, plus the 2,047 selected module-source/metadata files and 12,051 Go toolchain files already pinned by the accepted builder. This Source preparation held and verified their bytes; it copied only the 272 historical source files. No toolchain, module cache or GOCACHE was copied.

The module manifest covers all 19 versions in the original historical go.mod and all directly imported external packages in Task63's static source set. Each module has an expanded directory/go.mod, `.mod`, `.info` and `.ziphash`; there are no observed `.partial` markers. The eight missing ZIPs are enumerated individually in `offline-module-static-map.json`.

The exact locked Go `src/cmd/go/internal/modfetch/cache.go` is pinned. Its `DownloadDir` checks for an expanded directory, absence of `.partial` and presence of `.ziphash`; that path does not require retaining the original ZIP. The `.ziphash` text matches the frozen go.sum entry for each of the 19 versions. Therefore ZIP absence alone is not a demonstrated blocker to the proposed sparse offline cache.

This is a static source/resource mapping, not actual offline-build qualification, a module-content reconstruction from an official ZIP, or proof that the real compiler closure is complete. The future real declared/export lists must fit the pinned sparse files. Any missing compiler/tag/embed/transitive input leaves **this old21 branch** OPEN and stops; the builder must not download dependencies, change a version, rewrite go.mod/go.sum, copy unrelated caches, or retry automatically.

## Evidence and remaining boundary

Author preparation and 75 pure Source controls passed. Controls cover both fixed targets, exact SQL continuity (including a hole despite max=21), original addon/public-bootstrap pins, source Git blob mismatches, namespace escapes, Source self-review rejection, live-object shape, resource binding drift, per-target dependency closure, binary identity, lossless FILETIME and guard cleanup. They do not call `run_registered_build`, load OwnedJobs, spawn a child, execute Go, query SQL or exercise a product flow.

Actual SourceReadGuard acquisition uses Windows read handles. Each author guard was explicitly closed once in its `finally` block, with a serialized closed/zero-retained-handle audit. This is real read-only Source evidence, distinct from Native product execution. The existing guard internally unwinds failed acquisitions; no such failure occurred in this preparation or controls.

Successful future execution returns `BUILT_OLD21_CANDIDATES_PENDING_NONAUTHOR_PROGRAMME_REVIEW`, two programme refs, provenance and original Source refs, with `qualification_ref=null`. Independent actual programme provenance review and Root binding remain required. Historical formal release status, actual public bootstrap/backup/restore, observed database schema,21→22 compatibility and formal old21 Case are still OPEN for this branch. Main/Canon, old evidence, old22 programmes and completed Development13 are unchanged and not rerun.
