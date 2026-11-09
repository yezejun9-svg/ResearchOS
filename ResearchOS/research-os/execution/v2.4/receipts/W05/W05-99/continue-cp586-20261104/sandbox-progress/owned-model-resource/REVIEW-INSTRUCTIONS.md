# Stage A independent review

This directory belongs to `codex:/root/runtime_readiness`. It is a C-workspace continuation, not a ResearchOS checkpoint update. Expected terminal status is `ASSETS_STAGED_NOT_STARTED`; the author cannot issue independent acceptance.

After `MANIFEST.json` exists, an independent reviewer should:

1. Read `SCOPE.json`, `source-index.json`, `MANIFEST.json`, `PROFILE-AND-STATUS.txt` and the append-only `copy.jsonl`. Verify the manifest's pins for the immutable scope, source index, copy log and staging script. Preserve any `FAILED-*.json` and partial files; do not rerun the staging script.
2. Verify exactly 981 declared asset files, totalling 5,686,303,776 bytes: one `runtime/ollama.exe`, 974 files under `runtime/lib/ollama`, one Qwen3 manifest and its five blobs. Every recorded source path must be in the two allowed public source roots. Recompute source and target SHA256 for every asset and compare size/digest to both the source index and final manifest.
3. Enumerate only the staged runtime/model asset roots. Reject missing or extra asset files, escaped paths, duplicate destinations, reparse points or a source/target alias. The script uses read-only source handles and exclusive newly created destination streams; it never requests links, junctions or installer actions.
4. Verify `profile/.ollama`, `profile/AppData/Local`, `profile/AppData/Roaming` and `tmp` remain empty. No previous keys, profile, configuration, credentials or ResearchOS database should be present. Do not open any private-key or credential values during review.
5. Check the actual tool trace as well as these author reports: no Ollama/server/runner/installer was invoked, no endpoint was queried, no inference occurred, no elevated execution or D-write occurred. The selected Qwen3 official digest and its Apache license are copied as model assets, not treated as a current runtime qualification.
6. Report this review only as an asset-staging review. Any later server start, GPU discovery, metadata readiness, runtime qualification or coding task requires its own scope. Do not call these staged assets `RESOURCE_READY`, and do not infer a CP587 write, current model qualification or formal acceptance.

The parent SESSION/README remain unchanged. Original failures, consumed scopes and unknown monetary cost remain unchanged and are not transferred away by this new directory.
