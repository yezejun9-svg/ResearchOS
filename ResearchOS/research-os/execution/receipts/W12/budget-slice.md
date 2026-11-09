# W12 budget slice — EXECUTION_REPORTED / DEVELOPMENT_ONLY

Base: 201040bafdbe068a0e0cd3add2b84427d4e27635; lease W12-development-v1.
Implemented: immutable ledger; exact integer rational decimal accounting; goal/project/global scope chain; atomic concurrent reservations; unknown liabilities; event dedupe; late accounting after cancel request; budget/run-policy HTTP update proposal.
Command (cwd this worktree): D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe test ./internal/domain -run ^TestW12Budget$ -count=1 -> exit 0.
Observed C13-01/C14-01/C14-02/C14-03 and W12-BUDGET-REPLAY; full reproducible receipt runner follows.
Shared integration proposal: http.go routes resource operations and policy preconditions, skips project outbox for global policy.
Outstanding: dispatch admission/queue integration, resource switching, recovery process evidence, remaining assertions. W12-G01 NOT_YET_COMPLETE. W12-G02 BLOCKED by RQ-W05-CLI-POLICY-001; no live retries.
Assumptions: W06 development gates independently passed, no live runtime qualification. Revalidate W05 admission and W06 interfaces when upstream changes. No independent acceptance claimed.
