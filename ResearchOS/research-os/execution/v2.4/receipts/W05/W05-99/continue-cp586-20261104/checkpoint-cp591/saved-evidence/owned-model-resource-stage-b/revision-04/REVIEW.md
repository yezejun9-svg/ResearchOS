# Stage B revision04 — two P1 repairs, not executed

This revision is a source/build candidate only. The old controller remains prohibited by ../reviews/source-review.json, SHA133d48e1dc460fc218f11c874a0128bf42ce06423cabb52440cf73fe3d812c26. The old76 pinned files, scope, executable, BUILD-01 failure, revision02 and rejection report are retained. This candidate does not self-accept that review or authorize a native run. Baseline is Root's CP590; no D source/state write was performed here.

## P1-001: actual connected socket ownership

connection.go implements the only transport DialContext. It dials only tcp4 127.0.0.1:43861, obtains the returned connection's actual local/remote addresses and ports, and requests server-side ESTABLISHED owner rows matching the exact inverse four-tuple. A unique PID must be validated against a held, live identity in this owned Job. Missing, ambiguous, wrong-client-port, listener-only or foreign ownership closes the connection and returns an error before the HTTP transport can obtain or Write to it. A listening-port snapshot no longer authorizes a request. Windows uses TCP_TABLE_OWNER_PID_CONNECTIONS and ESTABLISHED state, not the LISTENER table.

The client retains the one-use version/tags calls, nil proxy, no redirects, disabled keepalive/reused-connection retry,5s/64KiB bounds, no body/credentials and no other routes. The prelaunch exact bind is a conflict/capability check only; it is not relied on for request ownership. No other port is scanned, adopted or killed.

## P1-002: kernel lifecycle has one owner

lifecycle.go is the sole owner loop for kernel_windows.go. Only that loop uses the private Job, completion port, thread and process handles. Its timer is an event consumed in the same loop; there is no watchdog goroutine capturing a numeric Job handle and no monitor join. Late stop/validate calls encounter the closed owner and cannot invoke the backend.

The owner does suspended atomic JOB_LIST creation, membership/identity collection, resume, bounded completion-port polling, owned-PID validation, terminate and final close. Its backend does not hash files, call journal/Sync, or invoke user diagnostics. The last Job handle closes FIRST in nativeKernel.Close, before closing ancillary handles or publishing its terminal outcome. A failed terminate, missing child, incomplete roster or active process at the absolute cleanup deadline still reaches final Job close and yields unproved cleanup, never success.

The same absolute cleanup deadline is carried in the stop request/outcome and bounds owner waiting and raw stream drain. Main-side disk persistence, source/asset hashes and stream log writes are outside this owner. If those diagnostics stall, the owner independently consumes its native deadline and closes the Job. An unobserved terminal outcome or undrained stream remains failure. After the owner has closed the Job, all981 StageA asset hashes are checked only when cleanup/stream evidence permits it. An uncertain stop has null/absent unchanged-assets evidence, not a fabricated match.

## Explicitly adjusted diagnostic promise

Child executable hashing was removed from the lifecycle and from request admission. Child image paths and exact decimal FILETIME/held-handle records remain kernel metadata. This scope does not claim child image hashes. StageA's executable/runtime/model asset hashes remain mandatory before launch and after proved stop. All child roster/event/handle gaps still prevent success, but no diagnostic gap may delay the final kill-on-close path. Process/Job ownership, exact returned primary handle, terminate, primary signal, Job active0, stream completion and actual-connection ownership remain hard gates.

Atomic suspended Job membership, HANDLE_LIST, the fresh profile/environment, NO_CLOUD/NOPRUNE, fixed43861, zero chat/pull/inference and unchanged old data/counters retain their original meaning. StageA empty profiles are unused; the one-use new run directory is revision04/run-01, currently absent. Kernel cleanup is policy-bound, not a native result established by these mock tests.

## Actual offline verification

The observed batch ec2670/session61279 terminated80d257 with exit0: build0, seven top-level pure tests plus five subcases pass, vet0. fixtures-04-attempt-01.jsonl retains Action=run/pass and package terminal evidence. In-memory net.Conn spies model the listener-replacement race, missing/ambiguous/wrong-tuple/listener-only/query-error proof and accepted actual tuple. No real socket is opened by fixtures. Fake kernel tests inject a stalled diagnostic and failed terminate, prove final close still occurs, verify late timer/stop cannot use the closed backend, and reject tracking/stream gaps as post-stop integrity.

The controller executable and native backend were never run; no server/GPU/native Job or real HTTP request was started. Mock tests do not qualify Windows native lifecycle or model readiness. Independent review must inspect source, source manifest, scope, binary and evidence before Root decides any serial native operation. Use only this revision's scope/executable after such review; the old executable remains rejected.

AUTHOR-DIAGNOSTICS.json references the existing BUILD-01 origin rather than creating a duplicate. Transport errors are recorded initially UNCERTAIN, followed by explicit disk readback and the later observed batch terminal; no preexecution outcome or numeric exit is invented. No batch should be repeated after80d257.
