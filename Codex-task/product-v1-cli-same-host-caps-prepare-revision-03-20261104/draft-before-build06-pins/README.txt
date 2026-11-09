REVISION 03 DRAFT, BUILD06 PINS PENDING. No application, CLI, Host, Native or model is launched in this preparation.
Both older freezes remain unchanged, including the independent P2 counterexample and its approved freeze02 repair.

Root must independently review/freeze this source, register a fresh exact f13
Job scope/checkpoint, then run this Node wrapper once with --scope FILE
--scope-sha256 SHA. SCOPE.template.json is intentionally not authorization.
The wrapper consumes its fresh C run root before importing/launching Playwright.
Do not precreate that root, reuse old state/DB/discovery or replay uncertainty.

Fixed action after Root supplies and freezes build06 pins: build06 Desktop -> original owned Core ready -> exactly
one existing 881e26... CLI invocation with argv [harness,caps] and stdin ignored
-> app.close. No picker, project, submit, task, event, model, login, download,
install, paid API action or network discovery/probe is added. Capabilities may
report can_submit=false or missing model account and still complete this
metadata query. No model/account readiness is inferred.

Direct reuse: imported makeEnvironment from frozen reviewed R04 flow SHA68458e...
Only that function is called; its full run() with picker/submit is never called.
R04's pinned cached Playwright 1.62.1, SDK inventory, launch, Main report filtering,
original Core identity checks and bounded app.close pattern are reused in the
small wrapper. No new supervisor/SDK is introduced. The pinned bundle's actual
validateBundle and validateStatePath are reused before launch.

Environment is explicit R04 normal Windows profile + Codex/Node/Windows PATH,
fresh C data/userData/discovery/tmp, shared Host locator disabled. No ambient
API keys/tokens/proxies/ROS settings/NODE_OPTIONS/CODEX_HOME are inherited.
After R04 makeEnvironment, SystemDrive is explicitly derived from SystemRoot's
Windows drive root; no ambient SystemDrive is inherited. Electron cwd is this
already-created owned run root. This does not change or claim to change Core's
product-defined cwd=REPO; build06 separately contains Root's managed Core env fix.
Normal Windows profile metadata visibility is intentional, not an OS ACL claim.
Wrapper reads only pinned public code/assets and this new discovery's public
url/pid/data_dir/host_instance_id metadata. It never reads session/auth/key files;
the CLI's existing Native bootstrap/private application credential handling is
left to the CLI itself. It never copies credentials to renderer or receipts.

Same-Host evidence: before/after discovery exact URL/PID/dataRoot/hostID equals
the Main ready original owned Core identity and URL, with expected Core image
hash, creation metadata, READY/UP and React mount. The CLI source internally
rechecks discovery URL/PID/dataRoot/HostID before its native bootstrap and GET.
Current caps output does not export a HostID/PID; any such fields added to output
must match if present. This is application/internal-identity evidence, not
independent HTTP interception or Windows named-pipe server-PID attestation.
No independent Native server PID observation is claimed.

The original CLI ChildProcess is retained until close, must exit0/no signal, and
must return JSON command=harness caps/status=COMPLETED/completion_scope=HOST_QUERY/
exit_code=0 with harness.v1 Codex capabilities. CLI streams persist only byte
counts, retained-byte hashes, exit/signal, overflow and spawn code; no stream text
is persisted. UTF-8/JSON parsing errors become a fixed input-free code. Before
writing any caps values, the complete parsed object is scanned to reject secret
keys, including credential_value and client_secret. Only a closed public summary
is written: fixed command/protocol/harness identifiers, can_submit boolean and
reason_code_count. Original free-text values and unknown fields are not copied.
No retry or arbitrary PID/process-name kill exists. App close is
bounded; the existing outer f13 original Job owns final timeout and containment.

Success is only SAME_HOST_CLI_CAPS_OBSERVED_PENDING_OUTER_JOB_STOP. Root must also
check its scope/result pins, original root signal, Job Active0, stop_proved=true,
no forced termination and source/binary pins. Wrapper never self-certifies Job
stop, Core exit, formal/business acceptance, model/runtime qualification, or
network-level identity proof. On timeout/failure retain all state and do not retry.
