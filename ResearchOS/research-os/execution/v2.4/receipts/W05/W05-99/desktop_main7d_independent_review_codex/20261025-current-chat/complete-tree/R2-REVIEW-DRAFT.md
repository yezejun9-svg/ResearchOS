# Desktop complete development tree: independent review draft

Status: SOURCE/BUILD REVIEW PASSES; final candidate commit binding pending. No native acceptance is granted.

The frozen r2 change resolves D01-D03 within the seven-file CP552 scope. The output is a development tree at its recorded absolute location. No blocking finding was identified in the bounded review. A separately owned native run remains necessary to establish actual renderer, management, native probe and shutdown behavior.

## Frozen inputs and observed output

- Base commit: `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e`; tree: `de59625ee5c1d360c741c95ec3f84b6f2764bb0e`.
- CP552 scope SHA-256: `a9e0c1b29282468b2d7a10d2cbd3db88feaa673b8480e0aab3d6176019bc7ab3`.
- Frozen source record SHA-256: `6d885a649bb020d702487d5331f394cc43b3fd1c22d00a11822289ba7d644d3b`.
- Patch SHA-256: `a9c8ca42f6b660481aee70457fa6aa19aa52bbd6c265f6b7a9d5f31336c09515`.
- Independent verification of all 591 source files matches source digest `5515cf413e840469eb5c2c14b226295f14648762137fd80cac12aa13c01d09f1`.
- Output development manifest SHA-256: `288ac604fbcc09b11d04148c970df8830c59d1352431832b06640e30fbf82a3e`.
- Exact output inventory: 132 files, 508,461,785 bytes; 75 Electron runtime files; 25 SQLite migrations.

## Findings D01-D03

D01 passes source/build review. `build-development.py` wraps the unchanged client-wire builder and supplies Core, runtime verifier and installation registration, current Mu worker/runtime Node, complete Electron distribution, migrations and Core cwd contracts. The seven changed source hashes, source snapshot and actual output inventory are bound to the manifest. Independent checks derived the Go selected source set from retained go-list output and Mu compiled input set from esbuild metafile output, then verified actual bytes, not only labels or counts. Core/verifier closure contains 2309 files and 693 package entries; Mu has 5083 vendor files and 2146 compiled inputs, with tool/package additions bringing that closure to 2156 files. The client-wire closure's 6451 actual files and its digest were independently checked. Every recorded before/after closure is unchanged; all seven build commands have native exit zero and matching raw-output digests.

D02 passes source/mock/actual-dry-run review. The launcher verifies the whole inventory and verifier/Mu bindings before creating state or spawning. It requires a fresh state path and rejects bundle/state aliases and overlaps. Child environment construction drops ambient project, discovery, data, Node and Electron overrides; case-insensitive key collisions are rejected. A dry-run against the actual 132-file tree exited zero and did not create its requested state directory. The normal launch still needs separately authorized native observation.

D03 passes source/mock review only. Main requires management READY, native host.status success, React evidence and a matching owned process identity. Successful smoke shutdown requires the management return to confirm STOPPED and actual process exit, no unconfirmed child, and unchanged PID/creation/image hash/Host ID. The launcher independently requires matching ready/shutdown report identities and successful Electron exit. Actual READY, probe, renderer and shutdown were not exercised by this review.

## Independent test results and retained diagnostics

The review copied and hashed the frozen seven files and direct baseline dependencies into its own evidence tree. Node focused tests: 6 passed, 0 failed, 0 skipped. Python focused tests initially produced 3 passed and 2 explicit skips; the missing-built-tree skip was subsequently covered by running that exact test alone against the real bundle, which passed. The Windows file-symlink privilege skip remains a skip. The separate Node junction rejection check executed and passed. Actual bundle dry-run exited zero and no state was created.

Nonblocking observation R2-N01: the Node tests' `removeFixture()` at `tests/ui/desktop/development-launcher.test.mjs:14-17` returned without removing four synthetic fixture directories under this review's long evidence path. Both test processes themselves exited zero. The review's post-test cleanup assertion correctly failed at ordinal 011. All 110 remaining synthetic files were inventoried by hash and removed only within the verified fresh review fixture root using Python; raw results were retained, and tests were not rerun. This does not invalidate runtime source/build evidence; future use of these tests at long paths should verify removal or use a shorter approved temporary root.

Reviewer harness diagnostic at ordinal 018: initial independent digest reconstruction omitted the builder's canonical trailing LF and failed before the byte loop. The original script and failure are retained. An additive corrected script at ordinal 020 reproduced the documented canonical format and independently verified all 591 actual source files. Neither diagnostic changed candidate source, historical failures, old receipts or acceptance counters.

## Boundary

No source or candidate mutation, native GUI/Core start, provider call, old database/credential access, ACL operation or unrelated process control was performed. All review writes are inside the approved independent evidence directory; only current synthetic fixture files were removed. This finding is not installer, relocation, native flow, live-provider, C57, parent-task or formal v2.4 acceptance. The original source and prior evidence remain authoritative outside this bounded review.

Final status and candidate binding will be issued in a separate sealed final report after candidate commit verification.
