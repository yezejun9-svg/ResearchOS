# Fresh current Main23 programme builder — Source only

Status: **SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_REGISTRATION**.

This package prepares one bounded Root-owned build of the current Main `ops/backup` programme. It does not execute Go during Source preparation, run the built product, touch SQLite, register a scope, or qualify its own output. Main, Canon and prior evidence remain unchanged.

## Reused components and current facts

`contract.json` binds the accepted public22 v2 helper, existing Windows OwnedProcess and SourceReadGuard by exact three-key refs. The historical schema22 builder and historical Main23 review builder are preserved as provenance references in `source-facts.json`; their ordinary subprocess/inherited-environment entrypoints are not reused as this Root build executor.

The current canonical toolchain lock pins Go 1.27.1 `go.exe`. Current Main has numbered migrations 1 through 23 and the public `schema22-to23-host-model-configuration-v1` plan. Its `backup_host_configuration.go` differs from the old Main23 candidate's compile vector. The old executable cannot supply a fresh Main binding.

Main has not adopted the 23-to-24 implementation or migration. That stage is locally blocked; schema21 and the complete 20-to-24 chain remain open.

## Frozen calling interface

Entry: `main23_builder.run_registered_build(contract_ref, request_ref, live_root_scope)`.

Both refs contain exactly `path`, `sha256`, `bytes`. The request JSON contains exactly `case_id` and `output_root`: a 32-character lowercase hexadecimal identifier and `<registered output_parent>/fresh-main23-<case_id>`. This package creates no actual request.

The Root caller must independently bind and hold the leaf, helper, contract, runtime/native closure and reviewed Source package before entering. Its live object implements the three methods listed in `contract.json`. JSON actor/approval flags are not an authority source. Registration, owner/scope/lease, the outer wrapper's raw tool request/response, and original-failure numbering remain Root responsibilities. If local receipt publication fails, Root must persist the returned state. The caller must preserve large FILETIME integers in Python or a lossless format; it must not round-trip them through IEEE-754 numbers.

The finite phases are:

1. Verify `go version` matches the pinned Windows AMD64 Go 1.27.1 tool.
2. Run `go list -deps -compiled -json ./ops/backup`; every declared file and go.mod must belong to the already frozen input set.
3. Run the corresponding `-export` list. Verify the declared closure is unchanged; pin the resulting export files and BuildIDs inside the new GOCACHE.
4. Run `go build -x -work -o <unique programme> ./ops/backup`. Retain raw commands, generated work and before/after cache vectors.
5. Run pinned `go version -m <programme>` to read its metadata. This does not launch the product executable.

All five children use the existing suspended-child/unnamed typed Job runner, with exact primary PID and integer FILETIME, actual primary exit, final Job idle and handle closure. Individual compiler-descendant exit codes are not separately observed and remain null; aggregate Job cleanup and Go's primary exit are the evidence.

## Input closure and cache policy

`input-manifest.json` enumerates 572 Main files (6,905,991 bytes), 2,047 explicitly selected module-source/metadata files (124,495,939 bytes), and 12,051 Go toolchain files (226,226,341 bytes). The historical Go-list output is only an enumeration hint; current bytes were independently hashed, and actual Go-list output must close over frozen inputs before the build proceeds.

The builder checks current Main file membership as well as content, holds original refs, copies Main and selected module inputs to unique directories, marks copies read-only and holds their read handles. It compares the frozen inventory and exact refs before each Go phase and at completion. It retains go.mod/go.sum, source before/after, declared/export closure, environment, build work and cache vectors.

GOCACHE starts empty and is never copied from the historical shared cache. GOMODCACHE is a sparse exact copy of the selected source and metadata; no zip archives are copied. Go's pinned `modfetch.DownloadDir` source requires the extracted directory and ziphash and rejects partial extraction; those metadata inputs are included. GOPROXY/GOSUMDB are off, GOENV/GOWORK are off, GOTOOLCHAIN is local, module changes are readonly, CGO is disabled, and Windows/AMD64/v1 are explicit. Undeclared module inputs stop the case. Additional empty module lock files are allowed and do not constitute build inputs.

## Output and qualification boundary

Successful execution returns `BUILT_CANDIDATE_PENDING_NONAUTHOR_PROGRAMME_REVIEW`, with `program_ref`, the `build.closed.json` provenance ref and the exact current Main five-source binding. `qualification_ref` remains null. A non-author must review the actual provenance; only then may Root supply the accepted independent qualification ref to public22's `qualified_current_main23` capability.

Any original error stops the sequence. Unknown exits remain null. Source guards close in `finally`; partial output and raw receipts remain available. There is no automatic rebuild, retry, recovery, deletion or re-registration. A separate new Root decision is required after an actual failure.

## Source checks

`source-controls.json` records 105 passing pure Source controls. They invoke the real validation/orchestration primitives with synthetic in-memory failure boundaries, covering directory-creation failure receipts, request/path constraints, large integer FILETIME, missing declared inputs, export scope, binary identity and no JSON authority. These are author checks, not independent review or actual build evidence. `source-seal-checks.json` verifies all 14,670 current input pins and Main inventory; no read-handle guard, Go process, product, native API or SQLite call was executed during this Source preparation.
