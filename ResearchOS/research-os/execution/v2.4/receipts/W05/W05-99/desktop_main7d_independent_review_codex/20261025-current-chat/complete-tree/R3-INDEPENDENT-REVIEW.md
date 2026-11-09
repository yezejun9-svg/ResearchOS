# Desktop complete development tree — independent final review

**Verdict: SOURCE_BUILD_REVIEW_PASS_NOT_NATIVE_ACCEPTED.** No blocking finding remains in D01-D03 or the r3 UTF-8 correction. The exact committed candidate and complete development output can proceed to a separately registered, owned native observation. This report does not grant native or formal acceptance.

## Exact candidate and output

- Candidate `ecc28dd3c91a0f68dcddb41b53325aa7f0e81419`, tree `1d44a02c9483fc529b08ffe81895ec443920bdd1`, parent `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e`.
- Independently checked clean worktree and exact seven-path delta: six added files and modified `apps/desktop/main/main.js`. Every committed blob and current source file matches r3 frozen bytes.
- CP552 scope SHA-256 `a9e0c1b29282468b2d7a10d2cbd3db88feaa673b8480e0aab3d6176019bc7ab3`.
- r3 source-freeze SHA-256 `c6ac8745f27d91a7d74aa804acdc05f3a50932b0d414a91f63daefe75c00c113`; patch SHA-256 `7da9b434521f14857766b4d502738fbdff0aadcb1e780228b26d0020c85213d4`.
- Source digest `8c32c66c6e5b330ea997d33f7737dbd8028d8c14ba0d12d87fd010d79d546e9c` covers 591 files. Build-before/build-after agree and differ from independently checked r2 in only launcher and its focused test.
- Output `D:/作品集/ResearchOS/research-os/.local/worktrees/desktop-main7d-native-20261025/.local/desktop-complete-20261025-02`.
- Development manifest SHA-256 `e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620`; all 132 actual output files independently checked, 508,462,215 bytes, including 75 Electron files and 25 SQLite migrations.

Build metadata records the precommit Main7d base plus explicit seven-file delta/digest. The later candidate commit was independently bound to those exact blobs; the build is not misrepresented as a build invoked after that commit.

## Review coverage and conclusion

**D01 — complete development tree: pass at source/build level.** The unchanged client-wire builder is wrapped by the new complete-tree builder. Actual output contains the current Core and verifier executables, bound verifier registration, current Mu worker and Node, full Electron distribution, React assets, SQLite migrations and four Core cwd contracts. Source, tools, package inputs and output inventory are recorded. In r2 the reviewer independently read actual bytes for 2309 Core/verifier inputs (693 package entries), all 5083 vendored Mu files, 2156 compiled-Mu/tool files (2146 metafile inputs), four external public producer inputs and all 6451 client-wire inputs. Selected source sets were independently derived from go-list and esbuild metadata, rather than accepted only from a count.

r3's new before/after Go, Mu vendor, Mu compiled and external-public manifests are exactly equal to those r2 independently verified manifests. That unaffected evidence is explicitly reused. The new client-wire input set differs only in the changed launcher test and two same-byte files whose fresh client-stage path moved (negative fixture source and one generated Go cache source); these changed/relocated inputs were read again. All seven new build command raw-output hashes and native exits were checked. All 132 new output bytes were read again. Output changes are limited to launcher, client-wire descriptor/bound validator, verifier registration's absolute path, and Mu metadata's stage path; Core, verifier executable, Mu worker, Electron, React and migrations remain byte-identical.

**D02 — isolated launch: pass at source/mock/actual-dry-run level.** Launcher validates inventory and verifier/Mu bindings before mutation, requires a fresh nonoverlapping state path, rejects aliases and environment-key case collisions, and builds a child environment using new state-specific data/discovery/userData/profile/temp paths. Ambient project, data, discovery, Node and Electron overrides are not forwarded. A fresh actual r3 bundle dry-run using its bundled Node exited zero, validated all 132 files, and created no state or GUI/Core process.

**D03 — smoke evidence: pass at source/mock level only.** Main requires management READY, native host.status success, React evidence and matching owned identity. Its shutdown success requires STOPPED plus actual process exit, no unconfirmed child, and matching PID, creation time, image hash and Host ID. Launcher checks matching ready/shutdown identities and successful Electron exit. Actual native behavior remains unobserved in this review.

**r3 UTF-8 change: pass.** Only launcher and its test changed after r2. StringDecoder preserves multibyte sequences across chunks, its end flush is checked, trailing fragments are refused, and malformed reports cannot produce successful smoke. The one affected test ran independently and passed its cross-chunk Chinese character, missing final newline and incomplete UTF-8 tail assertions. An additional direct probe without node:test emitted the 660-byte transcript one byte at a time, including `研究工作台🙂é`; both parsed title and strict-decoded stdout.raw were exact, with zero replacement characters. This also resolves the observed node:test display-channel replacement artifacts without changing product code.

## Tests, limitations and retained diagnostics

Independent r2 focused evidence: Node 6 passed; Python 3 passed, 2 explicit skips. Its absent-built-tree skip was subsequently covered by the exact actual-bundle test passing. The Windows file-symlink privilege skip remains a skip; the separate Node junction rejection test actually ran and passed. r3 runs only the affected test, the direct byte-stream probe, new actual inventory/binding checks and new bundle dry-run. Unchanged suites were not needlessly rerun.

Nonblocking observation R2-N01: Node `removeFixture()` returned without removing synthetic directories at this review's long temporary paths. The reviewer inventoried the synthetic leftovers and removed them only within its approved fresh fixture root using Python. Future test use at long paths should assert cleanup or use a shorter approved temporary root. No generated state or fixture leftovers remain in this review directory.

Four reviewer nonzero attempts remain intact: 011 cleanup assertion, 018 missing canonical LF in the review harness, 029 omitted Mu stage metadata path in the expected delta, and 031 omitted the relocated Go-generated cache source. The latter three are review-harness expectation corrections, not candidate changes. Corrected additive checks passed; all original scripts/raw/results remain. Author diagnostics also retain focused-01 cleanup failure, interrupted freeze-01, r2 supersession and seal-02 receipt-script failure before corrected seal-03. `REVIEW-DIAGNOSTICS.json` binds the copied raw diagnostic inputs and explanations. No historical failure counter was reset.

No blocking finding is hidden by these diagnostics. No source mutation, native GUI/Core start, provider call, original database/credential access, ACL change or unrelated process control was performed by this reviewer. Only approved review evidence and fresh synthetic test fixtures were written. Optional proposed-native-runner review was read-only and is separate from this source verdict.

This is a location-bound development output, not an installer or relocation claim. It is not C57 recovery, W20 completion, parent-task acceptance, live-provider proof or formal v2.4 acceptance. Native GUI/Core runs and formal increments are both zero for this review. A later native scope must bind this exact candidate, bundle and review seal and establish its own actual owned lifecycle evidence.
