# Owned Ollama Stage B — prepared, never executed

Root must independently review this source, scope and binary before any execution. The author has NOT run controller.exe, Ollama, a Job, a GPU probe, or any metadata request. Only locked offline Go compilation and go vet were run. This C packet is not a ResearchOS checkpoint write or qualification. Preparation began at CP587/Main556cdc35; Root subsequently reported CP588/Main556cdc35 as the last confirmed D state. That later state does not imply this controller executed.

## Fixed operation and identities

- Only Stage A's pinned C executable/runtime/model copies are used; all 981 files are checked before creation and again after proved shutdown. Stage A profiles remain empty and unused.
- One new, exclusive run-01 directory; a fresh run-01/profile with .ollama and AppData, and run-01/tmp. No existing key/config/profile values are read or copied. New key files created by Ollama stay there and are never opened by the controller.
- A fresh explicit UTF-16 environment with only SystemRoot, WINDIR, USERPROFILE, APPDATA, LOCALAPPDATA, TEMP, TMP, PATH and six named OLLAMA settings. No inherited proxy, token, API key, experiment or debugging environment. OLLAMA_NO_CLOUD=1, OLLAMA_NOPRUNE=1, OLLAMA_DEBUG=0; endpoint 127.0.0.1:43861, Stage A models only. stdout prints a short outcome, not the environment. Child raw logs are bounded to 2 MiB each and contain only this isolated child's output.
- The sole server executable is the pinned runtime/ollama.exe, argument serve, hidden/no console. No installer, app.exe, shell, pull, run, chat, qualification or model prompt.

## Process and cleanup contract

The existing ResearchOS sandbox uses PROC_THREAD_ATTRIBUTE_JOB_LIST and HANDLE_LIST; this controller reuses those Windows mechanisms. Its private, unnamed Job is kill-on-close, has a 32-active-process limit and no breakaway flags. Atomic JOB_LIST attachment during CREATE_SUSPENDED avoids an unassigned orphan if the controller dies between creation and a later AssignProcess call. It verifies IsProcessInJob and saves exact creation FILETIME as a decimal string before ResumeThread. This is job assignment at suspended creation, not a resume-before-assignment shortcut. Only the NUL/stdout/stderr handles are inherited; the Job and monitoring handles are not inherited.

A private completion port obtains NEW_PROCESS events. Every observed process gets an owned-job check and a held query/synchronize handle, image path/hash and decimal creation FILETIME. The returned primary handle is retained separately. GPU-discovery processes count as native children. NEW_PROCESS/OpenProcess can race or Windows can omit notifications: any missing handle/event, tracking error or final TotalProcesses mismatch makes the run fail. The controller does not pretend that its notification scheme guarantees it can always acquire a very short-lived child.

Before resume, unproved membership blocks execution; only the exact newly returned primary handle may be terminated as a suspended fallback. After resume, only the owned Job is terminated. No process is adopted, killed by name, or killed merely because it owns a port. A watchdog bounds native execution; the shared 15-second cleanup deadline must establish ActiveProcesses=0, every held handle signaled, all process identities/events accounted, and true EOF/drained stdout/stderr. Then all Stage A hashes/roster and its empty profiles are checked. If cleanup is uncertain, the post-stop integrity claim is skipped and failure is retained. Closing the last Job handle is a final fail-safe; it is not fabricated cleanup evidence.

## One endpoint and two GETs

The fixed port gets one exclusive bind/capability preflight. Conflict or access denial stops before process creation; no port scan, changing ports, foreign GET or foreign termination. A passive OS TCP-table lookup emits only the declared endpoint and must map its listener PID to a held live process in this owned Job. Root must explicitly review this passive ownership query as part of the native controller.

For pinned Ollama 0.30.0-rc31, wait at most30 seconds for its cloud-disabled and post-GPU-discovery vram-context log markers and its owned listener. Then GET /api/version once, GET /api/tags once, each bounded to5 seconds/64 KiB. No proxy, redirect or keepalive/reused-connection retry. Both attempts are recorded before transmission. Version must match0.30.0-rc31; tags must contain exactly qwen3:4b-instruct, manifest0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0, size2497293803. These metadata checks are not model inference or runtime qualification.

## Terminal boundaries and honest limits

Success: both metadata checks match, all native child identities/handles are accounted, owned Job is empty, handles signal, streams fully drain, and all981 assets remain unchanged. Status is METADATA_VERIFIED_AND_OWNED_JOB_STOPPED_ASSETS_UNCHANGED; resource_ready remains false because the server was stopped. Its forced cleanup exit is recorded, not disguised as a natural exit0.

Failure: bad pins/old run directory/port conflict means no launch; job/setup/tracking/marker/version/tags/timeout/raw-log/integrity mismatch means stop this owned Job and preserve evidence. There is no automatic retry, directory deletion, old qualification reuse or failure-counter reset. If Root's execution channel loses the process, first inspect this exact run-01 directory, saved suspended identity, events, RESULT and held session; do not repeat a one-use operation on an uncertain outcome.

No native lifecycle, GPU compatibility, HTTP readiness, global lack of unrelated client requests, or crash cleanup has been exercised by the author. Root's independent review and actual captured execution are still required. An unexpected external POST would not have been issued by this controller; the reviewer must inspect isolated raw logs rather than upgrading author request counts to universal provider/billing evidence. C57, runtime qualification and business Goal acceptance stay separate.

## Review and execution boundary

Review SCOPE.json, main_windows.go, PUBLIC-DEPENDENCY.json, BUILD-01/02/03 and VET-01, failed source archive and revision-02. BUILD-01's WAIT_TIMEOUT type mismatch and old bytes/log are retained; BUILD-03 and VET-01 passed. The dependency was copied from the existing public x/sys@v0.48.0 cache (61 files, source/target hashes), not installed or downloaded.

Only Root, after review and a stable execution channel, may invoke controller.exe with -execute -scope <this exact SCOPE.json> -expected-scope-sha256 <reviewed digest>. The controller is not run by any preparation script. SCOPE hash is printed in the preparation tool receipt. Do not execute while Root's other native action has an uncertain outcome.
