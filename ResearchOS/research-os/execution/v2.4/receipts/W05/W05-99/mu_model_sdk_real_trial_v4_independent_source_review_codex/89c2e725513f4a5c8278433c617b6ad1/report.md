## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** SDK v4 repairs executable/config byte checks and native first-cause ordering, but its new config transition guard rejects the real CLI's lawful session-context write.

### Critical Issues
- None identified in this narrow source review.

### Important Issues
- [mu_sdk_trial.v4.proposed.py:252] `cli-goal`/`cli-run` require identical pre/post config bytes. The actual run flow creates a session and `saveCLIContext` persists session/revision/epoch/writer fields (cli_verbs.go:159,183; cli_stream.go:816,829). A successful trial can execute model effects and then be rejected. Add explicit context transitions derived from the same original invocation and authoritative current snapshot, preserve all other config fields, and export/pin those raw postimages. Add a real-shape empty-session run positive and foreign-context negatives.

### Suggestions
- No separate optional change requested.

### What's Done Well
- Raw stdout parsing and hashing now share one byte buffer.
- Nonzero poll/wait status is locked before stream-close/hash errors.
- All four Go sources preserve the independently reviewed v3 qualification/storage guards.

### Verification Story
- Tests reviewed first: selected final_v2 and its original metadata0/0 result. Init/config component positives and eight negatives reviewed; full real run transition is absent.
- 28 manifest members match, six complete forward/inverse groups match, four Go sources are identical. Python AST parsed; 27 definitions unchanged, five changed, four added.
- Build verified: no. No candidate/helper/Go/CLI/provider/OS probe executed.
- Security checked: executable/discovery/config byte binding and reparse/path gates reviewed. Actual Root authority/Job producer remains OPEN.
- One metadata-reader IndexError occurred (outer/Python1/1); original I/O is preserved once. Product/canonical/source/formal changes0.
