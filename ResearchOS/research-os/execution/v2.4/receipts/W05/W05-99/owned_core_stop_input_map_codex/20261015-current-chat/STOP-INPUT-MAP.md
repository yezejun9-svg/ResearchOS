# Owned Core stop follow-up map

DISCOVERY_ONLY. No stop/helper fixture/actual signal/Source write is authorized by this note. The complete B/C/STOP architecture is under independent review at CP498. Original Core and Desktop continue running; prior PID observations are not current authority.

Existing ops/supervisor ObserveProcess obtains creation time through one transient handle and later image hash through a second transient handle. It returns PID/CreatedNS/ImageSHA256 only. It is useful observational input; an actual stop must open and retain ONE exact target handle, obtain identity and SID/path from that handle, validate the plan, signal only after native console census revalidation, then wait that same handle. Do not use ObserveProcess's PID observation alone as a stop capability.

release_process_windows.go already has bounded image hashing and no-reparse checks; exactImage is fixture launch policy with 128MiB bound, while observedProcessImageDigest supports a distinct 256MiB observation bound for Electron. Keep those purposes separate. NativeFixtureDriver uses CREATE_NEW_PROCESS_GROUP, which is not proof of a dedicated console or safe console-wide Ctrl-C target.

apps/control/main.go:220 subscribes to os.Interrupt. A separately reviewed helper can fixture-test AttachConsole + GetConsoleProcessList + one GenerateConsoleCtrlEvent(CTRL_C_EVENT,0) only when exact Core/helper are the only attached processes. Source and native fixture acceptance must establish behavior before any original Core action. A third process or unavailable console means zero signals. No automatic force fallback after timeout/unavailability.

The proposed stop can be an independent supervisor library and standalone helper, avoiding early control main flag overlap with C. Exact file/command/plan format remains undecided, requires revised Source scope and independent review. A controlled crash-stop, if needed, requires its own exact operation mode and reviewed plan, SQLite online consistent backup and committed/in-flight WAL fixture evidence; it must never be reported as graceful shutdown.

Original native worker closure and all external effect outcome proof are prerequisites. UNKNOWN money on a confirmed MODEL is separate from UNKNOWN effect outcome. Existing request/Run/effects/ledger and raw bridge/native receipts must remain append-only. Stop is only a means to obtain native DataRootLease for an official terminal-only maintenance command; it neither resolves nor retries the old Run.
