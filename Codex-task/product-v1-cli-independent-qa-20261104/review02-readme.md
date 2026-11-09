# Independent CLI S04 freeze02 review

Decision: APPROVED_SOURCE_FIXTURE_ONLY. This approves the exact three source pins in review02/review.json, not a real CLI/Native/Harness/model or product qualification. Root alone integrates and authorizes later real journeys. Formal/product increment0.

Independent execution used C snapshots/Go overlay for only the exact three candidate files and a C-owned independent test. Baseline Go dependencies were read from the existing worktree; no full Git baseline was copied. Native/bootstrap/credentials were injected fakes. Actual HTTP tests used only owned loopback traps. A minimal child environment used fresh C profile/temp/cache paths and offline locked Go/modules. No user auth/config files or old database were read. No D source was changed.

Freeze01 was rejected for CLI-QA-001: a Root rev2 schema-valid RUN_STARTED event with payload.task=null was rejected. The same frame with a matching snapshot passed. The initial counterexample,59PASS/2FAIL full-v1 narrow run and vet0 are retained; the two fail events are a parent/subtest for one origin. Freeze02 removes only that extra snapshot requirement and preserves identity/status/run checks whenever a snapshot exists. The same independent counterexample and the author's additional negatives now pass.

Final actual checks:132 named pass events (25 top/107 sub),0fail/skip. These comprise29 independent events,71 author S04 events and32 existing pure Mu events. Offline vet exited0; independent gofmt-d exited0 with empty output. Git diff-check/status exited0 and identified exactly the allowed three files. Final live/author/C snapshots agree.

Coverage includes strict22 definitions and Root contract pin; duplicate/escaped-duplicate/trailing/UTF8/alias/unknown/type/int64 rejection; original request-id/prompt/workspace binding and actual request-byte hashes; one POST then read-only recovery; nullable queued versus exact active cancellation; environment-token refusal; native failure/Host URI/identity rejection; no proxy, global transport or redirect authority transfer; output redaction; preserved legacy Mu parsing semantics. Native filesystem/ACL/pipe enforcement and actual model/owned-job cleanup were deliberately not qualified by these fixtures.

The INTERNAL_ERROR500 probe records current non-retrying behavior only; this review does not infer that any server-side commit was absent. Existing source/Runtime acceptance boundaries remain independent.

ARCHIVE_FILES.json gives the selected archive files. It includes immutable review01 failures/raw plus final source3 and validation evidence, and excludes caches, temp/profile directories and executables. Author installer/setup diagnostics and Root72ad13 carryforward are preserved without recounting the Root origin.
