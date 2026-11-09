## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** SDK v3 closes the requested EntityRef/log-Artifact ABI and actual host/DB leaf guards, but consumed file bytes and first-cause ordering still need two small source corrections. This is source-only review; Root producer, Windows runtime qualification, source acceptance and formal cases remain OPEN/0.

### Critical Issues

- None identified in the reviewed delta.

### Important Issues

- **R01-v3**, mu_sdk_trial.v3.proposed.py:114, 141, 837, 871, 547: the basis freezes claimed executable ref and config/discovery path strings, while actual bytes can change under the same grant. Re-pin the actual executable before each launch; bind discovery/config preimages and finite authorized config transitions, including same-invocation postimage and semantic identity checks. Preserve valid bootstrap/config transitions without future-hash cycles.
- **R03-v3**, mu_sdk_trial.v3.proposed.py:559, 570, 573: native exit1 is known before output context managers close, but a late close OSError becomes first cause before the nonzero freeze. Freeze nonzero where wait/poll returns and append later IO as secondary.

### Suggestions

- Keep Root source/scope acceptance, actual Windows Job lifecycle, actual qualification and provider cost/usage claims separate from this source gate. Actual billed tokens and amount stay NULL.

### What's Done Well

- The 27 sealed members and five complete forward/inverse deltas match exact bytes; the qualification Go patch remains identical to v2.
- EntityRef uses id, and AcceptanceReceipt is now separate from the approved log Artifact with version, sealed raw digest and run/epoch linkage.
- Control and Host check actual host/DB leaf aliases before mutable initialization; the original nontrial branch and partial-tuple rejection remain.
- Windows cwd string construction is consistent between phase_basis and actual child calls; the earlier pure-IO test repair changes only the fixture's cwd argument.

### Verification Story

- Tests reviewed: author precheck source/result inspected first; fixture uses extracted functions, fake DB/Popen and bypassed Job/authority. No reviewer candidate function, Go, CLI, SDK or provider executed.
- Build verified: no. Python AST parsed, 22 original definitions unchanged, four changed, six added; Go syntax/compile/Windows junction behavior NOT_RUN.
- Security checked: exact input/command authority, actual consumed file content, write-before-isolation order, chronological first cause and no secret material reads.
- No new reviewer tool failures; author's three inherited failures retained once without recount. Main/canonical/old receipts unchanged. Source/formal acceptance increment 0.
