# W18 CLI continuation independent review round 1

Verdict: NEEDS_FIX. One confirmed P2 correctness finding, W1802-CLI-R1-001. Review covers only apps/cli/cli_verbs.go, cli_continuation.go and cli_continuation_test.go at production commit be528afc918d862e48d057b462ed818d62c3a710. Candidate HEAD 7d2422adfa9f1823f7d47b4cb23126f551013e50. All three scoped files match that production commit byte-for-byte and remained unchanged through review.

## Finding W1802-CLI-R1-001: terminal Run classified as ACTIVE_RUN

apps/cli/cli_continuation.go:169-173 validates the fetched Run identity/project/task but never checks its status before appending an ACTIVE_RUN candidate. The existing production domain explicitly treats SETTLED, FAILED and CANCELLED Runs as terminal (internal/domain/runtime.go:137-138); reportRun retains Task.active_run_id when it changes a settled Task to EXECUTION_REPORTED (runtime.go:273-282). Thus a valid saved/restored unaccepted task may still reference a terminal Run.

Independent overlay creates and claims tasks through real API/SQLite, constructs the valid persisted terminal state of the older Run (SETTLED) and Task (EXECUTION_REPORTED), then creates and claims a newer Run. Reading continuation returns AVAILABLE with selection AMBIGUOUS and next_step null, although only the newer Run is active. The old completed Run obscures the unique actual active task. This can also promote a terminal Run as the sole ACTIVE_RUN candidate, and the else-if prevents consulting that task's ContextBundle.

Expected: classify the fetched Run by its actual status, use only nonterminal allowed statuses as ACTIVE_RUN candidates, preserve terminal unaccepted Tasks in unfinished_tasks, and allow their ContextBundle/remaining-task fallback. Unknown or invalid Run states should fail closed. Keep ambiguity when two genuinely active candidates exist. Add settled/failed/cancelled historical Run cases, including coexistence with exactly one active Run.

Reproduction: terminal-run.command.json, terminal-run-overlay.json and independent_terminal_run_test.go. Raw result terminal-run.stdout.txt: INDEPENDENT_TERMINAL_RUN_HIDES_ACTIVE, AVAILABLE/AMBIGUOUS, exit 1. The added overlay test checks that read projection itself does not change business state. The terminal transition is explicitly a constructed restored-state fixture, not evidence of a live runtime settling.

## Verified behavior

- Pinned Go 1.27.1 binary hash validated; actual argv, cwd, environment, duration, raw stdout/stderr, exit code and skips saved.
- Author's 7 top-level new tests and 5 transport subtests rerun successfully (baseline exit 0); 6 existing CLI/session regressions rerun successfully (regression exit 0). No skipped tests.
- status preserves both session.get and host.status; added projection uses authenticated GETs with the same credential and project scope.
- Goal.task_ids is checked for valid unique IDs; every project task page is bounded and read, membership mismatch/missing Tasks are rejected, and duplicate tasks/cursors fail closed. Actual 101-task fixture traversed two pages.
- Total response body budget is 2 MiB, at most 10 pages of 100 tasks, with an 8-second total request context. Redirects are not followed. Oversize, page-limit, timeout, redirect and cross-project response failures were tested.
- Real ContextBundle content and Run identity binding are queried through production API. Unique saved context, a sole unfinished task and ambiguity are tested. The Run-status defect above remains.
- Missing Goal/read authorization returns continuation.UNAVAILABLE, a reason and nonzero CLI exit; no-Goal legacy behavior sends no added reads. CLI process JSON preserves its original operations.
- Real API/SQLite fixture assertions compare all domain_objects (including Task/Run/Budget objects) and effect/dispatch/outbox counts before and after reads. The status projection created no new business Task, Run, effect or cost in these checks.

## Limits

This is a scoped CLI continuation code review. No backend backup tests were rerun, and no old backend conclusion is relabelled. No W13 workspace permission/read/write/diff audit was performed. No GUI, provider, live business database or formal 42-case acceptance is claimed. New continuation/status process tests execute the real CLI function in a Go child test process against the actual API/SQLite; this does not itself qualify a packaged release binary. The six prior CLI regressions exercise their existing fixture/native paths but do not constitute independent whole-card acceptance. No production/test source edits, state/checkpoint changes, commit, push or deployment occurred. Only new review evidence and overlay copies were written; prior evidence remains intact.
