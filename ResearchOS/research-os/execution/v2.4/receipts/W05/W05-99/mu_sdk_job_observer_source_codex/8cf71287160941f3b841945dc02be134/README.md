# Mu SDK Job observer source proposal

Status: `SOURCE_PREPARATION_ONLY_WITH_OPEN`. This package contains proposed code,
pure source controls and author evidence. It does not issue an execution grant,
source qualification, runtime observation, formal acceptance or cleanup verdict.

`mu_sdk_job_observer.proposed.py` exports:

```python
observe_assigned_before_resume(
    context,
    process_handle=actual["process_handle"],
    thread_handle=actual["thread_handle"],
    job_handle=actual["job_handle"],
    pid=actual["runner_pid"],
    creation_filetime=actual["creation_time_100ns"],
)
```

`context` has `input_doc`, `outer_job_contract`, `controller_source`, `hooks_source`,
`observer_source`, `independent_source_review`, `phase_dir` and
`public_environment`. The real Root callback supplies it while the reviewed
`run_owned` frame is paused in its unique synchronous `before_resume` call.
The return value has `job_probe`, `controller_review` and `nonauthor_review`, each
an actual `{path, sha256, bytes}` pin for an exclusively created JSON file.

The observer derives expected executable code from the frozen 18,901-byte
owned-process helper and reviewed hook literal, compiles it without execution,
then compares it with the real callback frame code and line. It reads original
handles, PID, creation time, creation flags, assigned state, unresumed state,
clock and child environment from that same live frame. It also queries Windows
for exact Job membership, PID and thread owner, creation FILETIME, process exit
state, process signaled state, complete initial Job PID list and Job limit flags.
The Job must contain exactly the one suspended primary process and have
kill-on-close without either breakaway flag.

The before-resume conclusion combines a pinned, independently reviewed
CREATE_SUSPENDED -> assignment -> synchronous callback source path with the
actual live frame and OS queries. It is not presented as a separate OS
suspend-count query, a different human's live tool observation, an adversarial
process isolation guarantee, or a completed lifecycle cleanup observation.

The current 39-field phase projection, child argv, cwd and public environment are
re-derived from frozen v8 semantics. Registration, canonical checkpoint, lease,
300-second global deadline, tighter real Job deadline, 3/8192 scope, unused once
path, protected-root separation, heartbeat and receipt ownership are checked.
Bootstrap preserves explicit null runtime-profile/public-route fields; execute
requires actual profile, route, cancel and bootstrap pins. Runtime source/profile
semantics and native precheck remain v8's responsibility.

Receipts belong only under
`execution/v2.4/receipts/W05/W05-99/mu_sdk_real_trial_root_codex/<32hex>/<phase>`;
registration and lease both bind `phase_dir`. The heartbeat remains directly
under isolated `data_root/trial-control`. All assertions complete before receipt
publication. File creation is exclusive; failures propagate to Root's Job cleanup
path, and existing partial files cannot be retried into success.

Before this module can produce a receipt, a different source reviewer must issue
`researchos.mu-sdk-controller-observer-independent-source-review.v1` with
`READY_SOURCE_ONLY`, all four exact source refs, callback contract
`REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME`, and `formal_acceptance: false`.
The module rejects Root, its own source author, its program actor and missing
reviewer identities. The template in this package deliberately leaves the actor
and decision null. No generated receipt claims the source author personally
executed the observation: actor is `program:researchos.mu-sdk-job-observer.v1`,
actual executor is Root, and the independent source review is linked.

The final 52 pure controls exercise rejection boundaries and compare both phase
projections to only the extracted pure v8 functions. They never call the observer
entry point or Windows APIs and produce no synthetic runtime receipts. Historical
40/44-control reports retain their exact previous source snapshots. Remaining
OPEN items are independent controller/observer source review, real Windows
callback execution, concrete phase seeds, and the trusted qualification Host
boundary identified by Root. Real models remain unauthorized by this package.

API basis: [IsProcessInJob](https://learn.microsoft.com/en-us/windows/win32/api/jobapi/nf-jobapi-isprocessinjob),
[QueryInformationJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject),
[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes),
[Job PID list](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_process_id_list),
and [process creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags).
