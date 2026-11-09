PREPARED ONLY. No Electron, wrapper, Native, model or GUI execution was performed.

Root must first review this source, make a new exact authorized scope from
SCOPE.template.json, record its checkpoint, and invoke the pinned f13 owned Job
supervisor. The template is deliberately not an authorization. Do not invoke
smoke.mjs directly, reuse an existing scope, or retry an uncertain outcome.

The wrapper hashes the fixed build02 manifest and launcher before dynamically
importing the actual validateBundle/buildChildEnv/validateStatePath/
validateSmokeReports exports. validateBundle rechecks the complete inventory.
It launches only bundled Electron apps/desktop and retains that ChildProcess.
It performs no process/PID lookup or kill. The outer f13 Job owns the overall
180-second budget, original handles and whole-tree stop proof. The wrapper
drains both pipes with 1MiB retention limits, performs no filesystem logging
while awaiting the child, and does not prevent the outer Job timeout.

Fresh smoke-state-01 contains data/, electron-user-data/, tmp/, discovery.json,
home.png, WRAPPER-CONSUMED.json, electron.stdout.raw, electron.stderr.raw, and
SMOKE-RESULT.json (files are created only when actually run). Existing state
is refused. All application state/capture outputs are C-owned. No old App DB,
ResearchOS data root, resource scope or consumed fixture is reused.

buildChildEnv receives only fixed OS paths. The explicit child environment
adds normal USERPROFILE/HOME/APPDATA/LOCALAPPDATA and a fixed PATH containing
nvm Node/npm and normal Codex metadata lookup locations. It does not inherit
ambient variables, API keys, token values, proxy settings, NODE_OPTIONS,
NODE_PATH or ROS settings. The wrapper does not read or copy auth/config.
Normal Windows profile visibility is intentional; this is not an OS-level
claim that Electron/Core cannot read a profile file.

Explicit flags are ROS_DESKTOP_SMOKE=1, ROS_DESKTOP_NATIVE_SMOKE=1 and
ROS_DESKTOP_CAPTURE_PATH=<fresh state>/home.png. The pinned Main loads its
default React homepage, calls host.status, captures and performs its existing
graceful shutdown. The wrapper performs zero folder chooser/project/model
submission actions and supplies no model credentials. It is not a Codex task,
model/runtime qualification or formal/business acceptance.

Acceptance requires all of: original Electron close code 0 without signal,
bounded untruncated UTF-8 raw reports; the bundled validateSmokeReports result
(READY/UP/Native probe/React mounted/original Core identity shutdown evidence);
ready PID equal to the spawned Electron PID; exact owned screenshot path and
regular PNG with dimensions/hash; and separately the outer supervisor's
stop_proved=true, original root signal and Job ActiveProcess=0. Wrapper success
is deliberately NATIVE_REPORTS_AND_CAPTURE_OBSERVED_PENDING_OUTER_JOB_STOP.
Do not infer whole-tree stop from its result alone. On timeout/missing proof,
keep every receipt/state and classify UNKNOWN; never auto-retry.

Only syntax was checked: fixed Node --check smoke.mjs (no module body/import
execution), efb3b0 exit 0. Actual launcher/main were read-only inspected in
264d6c and 2dad52. No screenshot currently exists.
