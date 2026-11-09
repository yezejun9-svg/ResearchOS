# C6 Source proposal

This immutable packet addresses C5 independent review findings R01 and R02.
It is Source-only and has not performed Windows process, provider, SQL or
canonical execution.

R01: C6 checks the exact 11-role Source author provenance against constants at
the pre-import gate and again under SourceReadGuard in the before-resume callback.
O4 independently checks the same tuple and excludes Root, w05 and live authors.
The generated O4 nonauthor receipt has its actor checked separately.

R02: C6 holds duplicate handles for the actual assigned Job and primary process,
plus PID and creation time captured before ResumeThread. Reconciliation accepts
no caller callback. The held producer reads current Job active count and primary
signaled state; C6 checks fresh bounded call time and exact run, owner, Job
binding, PID and creation identity. A failed or mismatched observation retains
the Source guard and resident owner. A failed duplicate close remains retriable.

The seven pure controls use a fake kernel. They include stale/future and
identity-forgery rejection. They do not prove actual WinAPI behavior or parent
process survival. Actual launch, qualification, provider traffic and formal
acceptance remain outside this Source packet.
