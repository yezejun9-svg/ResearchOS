# Build binding Source3 independent review

Decision: **BLOCKED**. Exact three files, baseline pins and both patch hashes match manifest `35f048d916950fbcaba1c9e6a25940f9b8255434baab8978342ed54ab2fa1338` and lease `43700c29f92112a21e608cfb9ca097f182f03bff2b138697b88c93b4923ec566`.

## BUILD-F1: protected-root-output-overlap

apps/desktop/build-development.py:432-438,473-491,530-536

Qualification root is validated independently, but no guard makes it disjoint from output, receipts and derived cache/tmp/stage/receipt directories. The builder can therefore create or write inside the external protected root/S, violating BUILD-C3/C5 and the lease before any final drift check.

Counterexample: Existing qualification-root R with receipts=R/receipts passes initial freshness checks and creates the exact directory that B3 later requires to be absent. Alternatively root=ROOT/.local and output=ROOT/.local/S creates/populates S before qualification_inputs detects a changed S validation status at the end.

Minimal correction: Before any mkdir, subprocess or failure-receipt write, validate all prospective writable destinations (output, receipts and derived scratch/stages) are disjoint from the protected qualification root tree and cannot overwrite the helper input. Check canonical Windows relationships using verified existing ancestry; reject overlap early. Add inert overlap counterexamples asserting zero build calls and no root/S/receipt mutation. Preserve the old candidate.

## BUILD-F2: detached-prebuilt-provenance

apps/desktop/build-development.py:170-197; tests/desktop/test_qualification_build.py:111-137

qualification_original_build hashes scope.json only against POSTCHECK.scope_sha256. It never links RESULT.scope_sha256/scope_id to that scope, parses its actual build command/output/cwd, or binds MANIFEST selected source claims to the scope's registered input pins. A successful RESULT from another run and a detached prepared MANIFEST can be accepted as the original owned build. Hardcoded helper digest still blocks arbitrary binary substitution; this finding concerns claimed source/run provenance.

Counterexample: Keep the valid helper bytes and POSTCHECK; replace RESULT with another successful stopped-run record, or change prepared MANIFEST source hashes to match changed current sources while the actual build scope pins remain old. Current validation accepts. The existing unit fixture even uses scope={} and a RESULT without scope identity, so it cannot detect this gap.

Minimal correction: Parse the original scope; require the expected helper-build scope identity and exact matching RESULT/POSTCHECK scope hash, normal stopped result flags, fixed build argv/output/cwd and controller/compiler identity coherence. Bind the prepared MANIFEST hash and each selected helper/probe/module source hash to actual scope.inputs, then compare to current snapshot. Reject duplicate/ambiguous or missing required records. Add wrong-result-scope, changed registered source pin, wrong target/argv, detached manifest and contradictory stop-record counterexamples. Do not claim a historical complete transitive helper closure that was not collected.

The all-three/default-closed inputs, expected helper hash/size, exact Core-only linker symbols, GOFLAGS clearing, path spelling/reparse checks, fixed copy/hash drift checks, helper/test snapshots and zero-acceptance manifest structure otherwise match the frozen design. Common Main lookup is correctly bound to git-common-dir parent; no receipt copy into the clean worktree is needed.

No tests, builds, helper, Native or model were executed. The current original helper receipts contain the needed cross-binding fields, but their complete build was not re-audited. Root's pure test outcome does not resolve the two source gaps. Preserve this candidate and apply fixes in a new freeze. Formal/product increment0.

