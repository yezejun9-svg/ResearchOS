# Root-only R4 supervisor — prepared, not executed

Single execution entry: the fixed absolute Python3.14 executable with -I -S -X utf8 and this directory's supervise.py. This packet is not runtime authorization. Root must independently review it, create a new public D receipt scope and a checkpoint newer than591, and bind their actual digests before using --execute. ROOT-AUTHORIZATION-TEMPLATE.json is deliberately invalid and cannot authorize anything. Do not execute archived failed sources.

## Fixed target and one-use gate

Only frozen R4 controller332334cef1028a8c56f0127d4438e8cf1852ff08bc16544ea0d6e726994f3297 and scope49a78cf270e40f4e76131bd9a1cd98e929548f39d36e9e1d203507f6ab67bdab may run. The conditional review627a3d31af529584495e739c5f892b732a3d1eef6c86b326dd09629a48c0282f, original43861 and original R4/run-01 remain fixed. No R4 file is changed and no alternative endpoint/profile/run is substituted.

Before launch, verify the reviewed supervisor manifest/files, Python/R4/review pins, exact public D Root authorization and its current checkpoint revision/hash/project. A stale checkpoint or either pre-existing attempt-01/R4 run-01 blocks launch and requires readback. Then os.mkdir exclusively consumes supervisor attempt-01 and a CONSUMED record is flushed before Popen. Any failure or uncertain construction consumes this attempt; nothing deletes it or retries it. The actual Root authorization must have status ROOT_AUTHORIZED_ONCE_AFTER_REVIEW, the final supervisor manifest/scope pins and checkpoint revision greater than591. It is a public operation scope, never a token/credential file.

## Independent outer timeout

The core holds the exact original subprocess.Popen object in ManagedOutcome.process. Windows stdlib Popen stores its original process handle in self._handle; wait uses WaitForSingleObject(self._handle), kill aliases terminate using TerminateProcess(self._handle). STDLIB-HANDLE-EVIDENCE.json records the installed public source hash/locations. No PID, name, port scan or reopened handle is used to terminate or rediscover a process.

Immediately after Popen returns, the first potentially blocking operation is process.wait(timeout=180). There is no logging, Sync, read, hash, poll, pipe wait or callback in between.180 seconds covers R4's pre/post981 asset hashing, native60 seconds, cleanup15 seconds and explicit margin. stdin/stdout/stderr are DEVNULL; no new pipe-drain dependency exists. CREATE_NO_WINDOW, shell=false, close_fds=true and a fresh minimal controller environment are fixed; existing proxy/token/profile values are not inherited or serialized.

On timeout or wait exception/cancellation, call kill exactly once on that same Popen object, then one wait(timeout=5) confirmation at most. Kill errors and confirmation timeouts remain structured UNKNOWN. A constructor exception with no returned handle is UNKNOWN, never 'known not launched'. No process scan or second launch is attempted. The exact original object remains retained through cleanup/report preparation. No environment values, exception args/raw tokens or process object representations are written.

The timeout path is complete before any RESULT read or receipt write. Timeout/uncertain waits never consult a late RESULT to promote status. After a confirmed exit0 only, read the bounded public R4 RESULT and require complete reported cleanup/Job-close/primary-signal/zero-active/roster/stream/asset/no-inference/request-count proof. Missing/unreadable/malformed/incomplete proof is INCONCLUSIVE. Complete reported proof is only REPORTED_PROOF_COMPLETE_ROOT_REVIEW_REQUIRED, always resource_ready=false and independent_acceptance=false. This wrapper does not establish native cleanup, qualification, business correctness or formal acceptance itself.

## Limits and uncertain outcomes

The outer wait/kill-confirmation path cannot be blocked by R4's logger mutex because it never touches R4's stdout/stderr, logs, hashes or RESULT while waiting. File reporting after terminal wait can itself fail or block, but cannot postpone the already-issued timeout/owned-handle termination. The policy does not guarantee progress after power loss, a non-returning OS kernel/CreateProcess/TerminateProcess operation, or external destruction of the supervisor. An unconfirmed exit or missing receipt is UNKNOWN; it is not a cleanup proof or permission to replay.

If any tool/transport/receipt outcome is uncertain, inspect the consumed attempt and original R4 run artifacts/held execution session first. Do not relaunch by choosing another name, scope, port or attempt. Root alone decides any subsequent scoped action and owns D/checkpoint updates. No old modelstore, profile, key, credential, failure counter or qualification is changed or read as part of this preparation.

## Actual offline checks and preserved failure

13 pure-memory mock tests passed, followed by py_compile exit0 (e0e0e5). Tests forbid real subprocess.Popen, filesystem/log/Sync actions in the active-child core, PID kill and pipe/poll access. They cover immediate bounded wait, hung logger timeout, single owned-handle kill+bounded confirmation, kill failure, constructor/wait/interrupt uncertainty, no late RESULT promotion, missing/forged proof, minimal environment and exclusive-record mode.

First batch edb15c exit1 had three auxiliary fixture errors from default sandbox AC/Temp permissions. The10 core mocks already passed. Sources and raw log remain in failed-attempt-01. Those fixtures were changed to in-memory models; their assertions were retained. Original temp residues were not removed or retried. AUTHOR-DIAGNOSTICS.json preserves this new author failure and only references the old BUILD-01 origin without duplicating it.

No supervisor actual entry, real Popen child, controller, native backend, Ollama/model/GPU or real HTTP request was run. attempt-01 and original R4/run-01 are absent at freeze. This packet awaits independent review and Root's later D scope/checkpoint.
