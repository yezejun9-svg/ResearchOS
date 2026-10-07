# S2 asynchronous sandbox boundary review

Verdict: **NEEDS_FIX_ASYNC_WRITE_CANCELLATION** for frozen source `2f30646`. No P1 finding.

The primary native replay passed the three author test groups and 34 independent assertions. A targeted concurrent-writer probe then reproduced one P2: a second `Write(ctx)` whose 40ms deadline expired remained queued after 200ms, returning only after explicit cancellation released the first blocked writer. The final count is 36 passing and one failing independent assertions, with command exits 0 and 1 preserved.

The fix should make serialized write admission context/process-aware while preserving frame atomicity and blocked in-flight cancellation. Raw reproduction: `queued.stdout.jsonl`, `native/queued-write.json`, and `queued_write_test.go`.

- Only the native asynchronous AppContainer boundary at source 2f30646 is reviewed. No complete S2 coordinator/domain/typed-bridge/workbench acceptance, construction gate, LIVE or BOUNDED_AUTO qualification is granted.
- Three frozen source files are overlaid on main 33d9230. The two remaining package files match the frozen source after line-ending normalization; product source and the active author worktree were not edited.
- All native processes use newly created no-secret fixtures, fresh owned AppContainers and temporary directories. No protected production service, provider or external network destination is contacted.
- BeforeResume and OnStream are trusted host callbacks; this review exercises callback rejection and prompt consumption, not indefinitely hung arbitrary callback code. The API documents prompt stream consumption.
- Stream bounds are 4MiB per stream. A cancelled process can legitimately have drained EOF streams; callback rejection and stream overflow correctly produce StreamsDrained=false.
- Run compatibility covers ordinary completion, timeout and existing root-overlap refusal. The older TestNativeSandbox external-network probe was intentionally excluded because external access was outside this task.
- Three standard pipe handles remain the only explicit inherited handles; zero capabilities, minimal environment, active-process limit and private staging ACL logic were preserved by source comparison. Child host-canary/proxy environment absence and capabilities were also checked natively; arbitrary handle enumeration was not performed.
- The author original SetWriteDeadline failure and subsequent successful run are retained as immutable Git-sourced evidence. This review also retains the failing queued-deadline probe and does not report it as PASS.
