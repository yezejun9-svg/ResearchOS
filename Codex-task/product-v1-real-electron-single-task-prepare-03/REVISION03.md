# Revision 03 provenance and boundary

Revision 03 is a new C-only candidate copied from the frozen revision 02.
Revision 01 and 02 remain unchanged. The old revision-02 freeze is preserved
here as `02-FROZEN.json`; its independent security report is
`product-v1-real-electron-single-task-security-review-02/REVIEW.json`
(SHA-256 `f9da90a1925045434db54e91f8555244213ebcbc7b5b34fdee5d9aebca94a2cd`).

This revision copies Native path controller 04's helper, changing only its
scope guard to require a zero-task/zero-model Native stage inside the global
one-Harness-Task scope. It also integrates Native 03's bounded helper-result
parser and phase-preserving blocked-result observation. The Native helper's
direct owned chooser and warning-button checks, active-dialog/owner guards,
final action deadlines, and streaming history are retained. Native 04 still
requires its independent review and a successful actual zero-model path flow.

The task observer addresses the review's F1/F2/F3 cases:

- Every nonnull typed Main pending reply must be a matching submit operation.
  Its first request ID is pinned; a later mismatch fails. If Main clears the
  journal before observation, the first validated singleton Task pins the ID
  with `FIRST_AUTHORITATIVE_TASK` provenance. Null pending never clears a pin.
- Readonly UNKNOWN reconciliation validates pending/list against existing IDs
  and records conflicts separately. It never overwrites an original request,
  Task, or Run, and never resubmits or cancels.
- List/Get Tasks, event-page snapshots, embedded public Task payloads, and
  event RunRefs all bind to one original Task/request and at most one observed
  RunRef. Event reset does not clear the RunRef. The final same-Run terminal
  payload must match the pinned Task and request.

`budget.model_calls=1` is legacy scope terminology for one native Codex
Harness invocation/Task. Internal LLM API calls are `NOT_MEASURED`; a public
turn event or process start does not establish a billable API-call count.

The Native prerequisite is still blocked: flow 01 stopped before OK, and flow
02 showed the real invalid-path warning but did not dismiss it or reach valid
selection/Main binding. This template retains null prerequisite result hashes,
null harness hashes and Root approval pins, and `NOT_RUN` status. No real
one-task scope is registered or executed. Future changes require revision 04;
do not overwrite this freeze.
