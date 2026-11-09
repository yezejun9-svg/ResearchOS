# Frozen doctor diagnostic oracle, revision 1

This supplement freezes the observable diagnostic contract before product-agent
work on `ISSUE-DOCTOR-JSON-001`. Its source is
`execution/v2.4/live/w1401/issue_freeze.json`. It does not modify the frozen client
protocol, authorize provider calls, or implement candidate CLI behavior.

Run the independent checker with the actual built candidate:

```powershell
go run ./tests/e2e/doctor_check --binary <absolute-researchos.exe> --candidate-source <candidate-repository-root>
```

The checker records binary, candidate CLI source, contract, and issue hashes. It
does not compile or edit the candidate. Its stdout is one JSON report; exit 0
means only the implemented diagnostic checks passed, exit 1 means an assertion
failed, and exit 2 means the checker itself could not run. The three construction
provenance/cost rows always remain `NOT_CHECKED` for the parent verifier.

## Machine report

`researchos doctor --json` accepts the flag and emits exactly one JSON object on
stdout, with no banners or other stdout text. It retains `command: "doctor"`,
`status`, and integer `exit_code` equal to the real process exit code. It adds a
`layers` object containing all seven keys below. Each value is an object with
`status` equal to `VERIFIED`, `FAILED`, or `NOT_CHECKED`, and a nonempty textual
`reason`. Additional truthful fields are allowed. Reasons describe the measured
boundary or missing prerequisite, not credentials or raw untrusted responses.

| Layer | Meaning of VERIFIED |
| --- | --- |
| `host` | This invocation reached the discovered local host. |
| `directory` | A real directory selection/authorization has been independently established. Merely having a current working directory is insufficient. |
| `credential` | A usable local credential value is present; this alone does not prove server authentication. |
| `authentication` | A separate authenticated `POST /v2/command` `host.status` completed with a valid typed response and a nonempty `result.authenticated_principal_ref`. A generic HTTP 200 is insufficient. |
| `model_catalog` | A model-list operation actually succeeded; host liveness or authentication is insufficient. |
| `inference` | An authorized inference operation actually round-tripped; a listed model or credential is insufficient. |
| `tool` | An authorized tool actually executed; inference capability or a declared tool name is insufficient. |

The oracle provides no native folder-selection witness, provider configuration,
inference authorization, or tool-execution witness. Thus `directory` must be
`NOT_CHECKED`; `model_catalog`, `inference`, and `tool` must not be `VERIFIED` in
these scenarios. If an actual applicable probe was refused it may be `FAILED`;
otherwise it must be `NOT_CHECKED`. Inference/tool must remain `NOT_CHECKED` when
discovery is missing, stale, nonlocal, or authentication has not succeeded.

The HTTP fixtures use the existing `/healthz` and `/v2/command` interfaces only.
The positive `host.status` fixture supplies every required `HostStatusResult`
field from `internal/api/contracts/client.protocol.schema.json`. It reports an
authenticated principal but empty credentials/model configurations/workspaces;
it cannot establish those other layers. Other command methods return a typed
`NOT_IMPLEMENTED` response. A credential-present case must actually attempt
authentication: a 401 means `authentication: FAILED`; the valid positive fixture
means `authentication: VERIFIED`. A malformed HTTP 200 or wrong command identity
must never verify authentication.

## Refusal, privacy, and compatibility

- Missing discovery: exit 3 and top-level `reason: "NOT_FOUND"`. Inference and
  tool are `NOT_CHECKED`; host is not `VERIFIED`.
- Stale discovery pointing at a closed local port: exit 1, no inference/tool
  verification. No reuse of a previous successful report is permitted.
- Any unknown doctor flag (including a typo of `--json`) is a usage error, exit
  2, and no HTTP request is sent. `--json --unknown` remains machine-readable.
- Discovery must be admitted as local loopback before any HTTP request or
  credential use. The nonlocal test endpoint is an address of this machine,
  bound by the checker, so this test contacts no outside service. It must receive
  zero requests; the diagnostic is a nonzero refusal, never host/auth VERIFIED.
- A local host redirect to that nonlocal endpoint must likewise not be followed.
- No fixture credential value, bearer authorization value, or echoed credential
  may appear in stdout/stderr. An untrusted health response may intentionally
  echo the fake credential to test this property. The checker passes no real
  credentials and strips inherited application/provider environment variables.
- Bare `doctor` preserves accepted W05 behavior: stdout remains a single JSONL
  record; missing discovery exits 3 with `NOT_FOUND`; unhealthy host exits 1 with
  `health: "DOWN"`, `http_code: 503`, `status: "REJECTED"`; healthy host exits 0
  with `health: "UP"`, `status: "COMPLETED"`. Human diagnostics may use stderr.
  Bare doctor and `--json` need not have different bytes if both honor this
  machine contract. This oracle checks these doctor compatibility rows only;
  the complete W05-03 regression remains the parent verifier's responsibility.

## Scope of the eight frozen rows

The five `W1401-DOCTOR-JSON-*` rows are executable here. Additional assertions
cover credential privacy, nonlocal/redirect refusal, malformed auth replies,
and the accepted doctor compatibility behavior. These three original rows are
reported `NOT_CHECKED` and cannot become PASS merely from this report:

- `W1401-PRODUCT-AGENT-DIFF-IS-NON-EMPTY-AND-REVIEWABLE`
- `W1401-PROVIDER-COST-AND-WALLCLOCK-RECORDED`
- `W1401-NO-EXECUTOR-EDITS-PRESENTED-AS-PRODUCT-WORK`

The parent must independently verify actual production diff provenance, actual
provider accounting, and same-session Desktop consistency. Fixture diagnostics
do not qualify a LIVE provider, prove directory selection, or accept W14.
