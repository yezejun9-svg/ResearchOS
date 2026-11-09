# W05 runtime

`ops/ci/runtime.py` runs nonzero W05 assertions and preserves command/environment/version evidence before execution. Set `RESEARCHOS_GO` to the pinned Go 1.27.1 binary. Select `W05-G01` for protocol fixtures plus real Windows process tests; `W05-G02`/`A04` requires explicit `RESEARCHOS_RUNTIME_LIVE=1`.

The Windows adapter owns one admitted Run and its finite command queue. Durable intent precedes an atomic Job Object process assignment; the job disallows breakaway and kills descendants on worker handle loss. A process is suspended at creation and resumed inside the job. PID plus creation time is recorded. A named exclusive journal lock prevents another worker from taking the same run. Unknown outcome after a worker crash is retained as UNKNOWN and never automatically retried. Monotonic lease/time deadlines stop launches and terminate the complete job. Default heartbeat/lease is 15s/90s. Parent exit alone is insufficient while children remain.

This is process lifecycle management, not W17 sandbox/credential isolation. Native session resume is unsupported; recovery uses a new current ContextBundle only after the previous outcome is reconciled. CLI `turn.completed`, tool exit and process exit are separate observations; none accepts a Task. Model revision and cost remain null when the provider does not disclose them.
