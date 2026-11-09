## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** Five proposed Python files add a fixed W05 A04 profile, LIVE dispatcher and four-part exporter. The immutable source package is intact, but its validators can accept incomplete or semantically wrong evidence. This is a SOURCE-only review; no product or formal acceptance was run.

### Critical Issues

None identified within this bounded source review.

### Important Issues

- **R01 — runtime_w05_live.proposed.py:139,177,186; export_a04_live.proposed.py:41.** Empty facts/source maps pass the universal predicate; missing argv/cwd/env fields compare as None==None. A closed-memory pure AST control returned A04 and H08 PASS rows without DB/JSONL/Job/native proof. Require complete typed invocations and a shared assertion/gate semantic verifier before dispatcher PASS or exporter output. Missing full LIVE evidence stays OPEN/NOT_RUN.
- **R02 — formal_profile_w05.proposed.py:185,218,280.** A refusal saying PASS/rejected=false/foreign run is accepted; cancellation consistently relabeled as success is accepted; False is accepted as zero for process/request/late-launch counts. Enforce frozen lane mapping, actual same-run negative semantics and exact integer counts. Bind the recovery context as an actual verified object.
- **R03 — formal_profile_w05.proposed.py:139,198,238,251,262,370,424; export_a04_live.proposed.py:42,64.** Selected scalar pointers and self-declared Root/message records do not establish the required full LIVE DB/JSONL/owned process, H08 parent/child scopes, installed P01 actions, U02 file/test causes or original fifth-part delivery. Define and verify a fixed original-tool/terminal/Job/domain-witness ABI. Derive predicates from actual same-task observations and keep unsupported/missing witness types OPEN. This is a static consumer gap, not an assertion that a real LIVE run failed.

### Suggestions

No scope-expanding refactor requested. Keep the fixed module boundary and frozen command routing.

### What's Done Well

The proposal uses a fixed Main profile rather than importing receipt code, retains W04/W07 and existing W05-G01 routing, and preserves four producer parts plus a later independent fifth part. UNKNOWN amounts remain null, and exporter output does not self-accept a formal case.

### Verification Story

- Tests reviewed: author 25 pure controls and their fixture shapes; they were not used as independent acceptance.
- Independent verification: 11/11 source members have exact SHA/bytes; five source ASTs parse; both modified files have exact textual inverse and lossless byte restoration. The index retains 33 other definition ASTs and runtime retains one.
- Seven bounded pure AST counterexamples were accepted by the selected validators. IO was replaced with closed memory maps; no entire dispatcher/exporter/profile, product, native tool or model was executed.
- Build verified: no. Security checked: fixed import/path boundary, identity/ref provenance and typed semantic guards.
- New tool failures: zero. Prior unsealed tool observations listed in the continuation were unavailable in this resumed store; their input/result are not fabricated. All current tool calls are recorded exactly.
- Source adoption, finite Root LIVE authority, full Windows runtime evidence, independent LIVE review and Root issuance remain OPEN. Source/formal acceptance increment is zero.

