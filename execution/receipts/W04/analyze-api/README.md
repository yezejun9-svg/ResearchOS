# W04 analyzeChangeImpact construction receipt

Source commit: `9e419e7361eb8b4586b7d9da637d8be90bc73d2f` on `work/change-impact`.

The public `POST /v1/projects/{project_id}/change-proposals/{object_id}/analyze` route accepts only a current project-scoped proposal with `If-Match`, idempotency key, and the OpenAPI planner/scheduler role. A normal settled FIXTURE Run supplies one sealed report bound to the proposal ID, frozen edit contract, exact edit target/value Artifact inputs, requested additional references, conflict IDs, and reason. The service checks its current runtime observation, output manifest, artifact-use proof, frozen Task contract/context/dependencies, and current execution authority. It merges semantic links into the deterministic impact closure without discarding prior impacts. Reported conflicts keep the proposal `BLOCKED` and remain `OPEN`; a later report can continue only after a different independently accepted and applied change formally resolves them. The latest report points to the previous Run, so acceptance and apply recheck the report chain and all candidate executors. Existing C03/C04/W15 formal conflict resolution remains available.

Evidence is limited to local `FIXTURE` execution and structural/provenance checks. Neither the service nor these tests establish natural-language semantic truth or LIVE runtime qualification. No independent verifier acceptance is recorded here.

Runner: `D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe` (also set as `RESEARCHOS_GO`). Working directory: `D:/作品集/ResearchOS/research-os/.local/worktrees/change-impact`.

Targeted command: `go test ./internal/domain -run '^(TestW04Analyze|TestW04C03$|TestW04C04$|TestW15SourceConflictFormalResolution$)' -count=1 -v`. Raw stdout is `targeted-test.stdout.log` (SHA-256 `6e5e3b288ce5195eaf912751b980be2deeed5f3983f8067afede19a94414b6e4`); exit is `targeted-test.exit.txt` (`0`). The raw log has 15 top-level passing tests, 15 explicit non-2xx rejection assertions with zero failures, 13 existing W04/W15 assertions, and one final `PASS`.

Coverage command: `go test ./internal/domain -run '^TestW03OperationCoverage$' -count=1 -v`. Raw stdout is `coverage-test.stdout.log` (SHA-256 `70c5e4c4e23ce06f30e76c667929717d566e1e966e0d1215b863628fcea60873`); exit is `coverage-test.exit.txt` (`0`).

`source-sha256.txt` records the SHA-256 hashes of all six changed source/coverage files at the source commit. `git diff --check` passed before the source commit; the frozen `spec/v2.0/` tree was unchanged.
