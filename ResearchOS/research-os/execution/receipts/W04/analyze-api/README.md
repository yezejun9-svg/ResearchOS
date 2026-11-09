# W04 analyzeChangeImpact construction receipt

Source commit: `9e419e7361eb8b4586b7d9da637d8be90bc73d2f` on `work/change-impact`.

The public `POST /v1/projects/{project_id}/change-proposals/{object_id}/analyze` route accepts only a current project-scoped proposal with `If-Match`, idempotency key, and the OpenAPI planner/scheduler role. A normal settled FIXTURE Run supplies one sealed report bound to the proposal ID, frozen edit contract, exact edit target/value Artifact inputs, requested additional references, conflict IDs, and reason. The service checks its current runtime observation, output manifest, artifact-use proof, frozen Task contract/context/dependencies, and current execution authority. It merges semantic links into the deterministic impact closure without discarding prior impacts. Reported conflicts keep the proposal `BLOCKED` and remain `OPEN`; a later report can continue only after a different independently accepted and applied change formally resolves them. The latest report points to the previous Run, so acceptance and apply recheck the report chain and all candidate executors. Existing C03/C04/W15 formal conflict resolution remains available.

Evidence is limited to local `FIXTURE` execution and structural/provenance checks. Neither the service nor these tests establish natural-language semantic truth or LIVE runtime qualification. No independent verifier acceptance is recorded here.

Runner: `D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe` (also set as `RESEARCHOS_GO`). Working directory: `D:/作品集/ResearchOS/research-os/.local/worktrees/change-impact`.

Targeted command: `go test ./internal/domain -run '^(TestW04Analyze|TestW04C03$|TestW04C04$|TestW15SourceConflictFormalResolution$)' -count=1 -v`. Captured stdout is `targeted-test.stdout.log` (LF-normalized SHA-256 `a9b62724c1e0efa693a72e556ec17cd440b6be573f2912e49f5b9acb64c88439`); exit is `targeted-test.exit.txt` (`0`). The log has 15 top-level passing tests, 15 explicit non-2xx rejection assertions with zero failures, 13 existing W04/W15 assertions, and one final `PASS`.

Coverage command: `go test ./internal/domain -run '^TestW03OperationCoverage$' -count=1 -v`. Captured stdout is `coverage-test.stdout.log` (LF-normalized SHA-256 `e4534902fb03695555df8e7be05cc4ca96840bf7a532626a4d25951f35ef7b43`); exit is `coverage-test.exit.txt` (`0`).

`source-sha256.txt` records the SHA-256 hashes of all six changed source/coverage files at the source commit. `git diff --check` passed before the source commit; the frozen `spec/v2.0/` tree was unchanged.
