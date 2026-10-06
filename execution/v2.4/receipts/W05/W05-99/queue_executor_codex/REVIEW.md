# S6 implementation candidate

Source frozen at `7f46cb59bdb4215fc5072b17b50e186e5ae0a429`; production code at `49e1d2b5ce3756575ffc098a90b3d8d8d55d311a`. Only the additional Goal-cancel/claim test differs. This is an implementation submission for independent review, not formal acceptance.

Current final runs: full CLI **108 PASS / 0 skip** (42 top-level tests); queue/bridge/upgrade/W18/W04 matrix **88 PASS / 0 skip**; actual pinned SDK **2 PASS / 0 skip**; current built control startup **1 PASS / 0 skip**. Each has exact before/after source vectors with no drift, tool/bundle hashes, actual argv and raw output. Counts include Go subtests and must not be added as unique independent assertions.

Implemented durable same-worker queues, real Mu stable-ID consumption, globally ordered initialization/control ACKs, SDK-backed prepare/commit seal, original-request Goal/Run cancel with no-Run/UNKNOWN truth, recovery fencing, numbered0022, explicit typed21-to22 isolated upgrade and portable queue inventory, and active CLI stdin through one flow writer. Two real races found and fixed: prompt started before durable init ACK; aborted effect late ACK lost its pending identity. Final Node tests exercise both counterexamples.

Full broader regression was **980 PASS events, 5 failures, 6 skips**. Original W04 test now passes using an exact frozen-manifest fixture. Four historical gates remain blocked: `TestW17UpgradeActiveRecovery`, `TestW17UpgradeCLI`, `TestW16ControlReplayNative`, `TestW16ControlBusinessNoGain`. No schema17 table was injected into schema14 and no legacy release guard was widened. Q10 is therefore not blanket green. See `execution_report.json` for exact source lines, causes and unrun LIVE gates.

`run_index.json` retains every attempted run and failure; `scope_boundaries.json` proves registered legacy spans and S5 suffix unchanged. `source_after.json` pins all33 authorized source files. `receipt_manifest.json` pins receipts. `current-control-build/control.exe` is a retained local tested artifact, excluded from Git.

Automatic approval review rejected cleanup of one abandoned SDK temp directory with “blocked by policy”; no deletion occurred and no alternate deletion route was attempted.
