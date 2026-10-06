# W04 evidence integrity convention (implementation, not frozen schema)

`validate.py` is a read-only stdlib checker. It creates no files, runs no product
commands, grants no identity, signs no verdict, and creates no business
Acceptance object. The shapes below are implementation conventions. Frozen
ownership, assertion IDs, command bindings, modes, expected text, dependencies
and GLOBAL_EVIDENCE requirements are read from hash-pinned v2.4 contracts.

## API and phases

```python
check(repo, state, spec, current_index,
      independent_review=None, root_observed_issuance=None,
      phase="execution")
```

The function raises `InvalidEvidence` with a stable reason code. The CLI emits a
JSON result and exits nonzero on rejection. `--repo`, `--state`, `--spec` and
`--current-index` are required. Review phases also require `--independent-review`
and `--root-observed-issuance`. All phases are read-only.

* `execution`: four execution GLOBAL parts per case and five gates are complete
  and current. Formal accepted count is **0**, eligible cases are empty.
* `reviewed`: independent review, actual root-observed issuance and eleven exact
  registered dispatches are also valid. Eligible case IDs are C03/C04/A01;
  formal accepted count remains **0**. No prior ACCEPTED owner row is required.
* `registered`: additionally requires canonical `step_state.json` owner-99
  ACCEPTED, matching identities, dependencies and registered reference hashes.
  Only this phase may derive formal accepted count **3**.

These counts remain distinct: **10 unique assertion IDs**, **3 formal cases**,
**6 formal command bindings**, **5 parent gates**. Repeating complete IDs through
two keys does not double the assertion count. Any failure yields no accepted
count. A parent/card ACCEPTED does not manufacture case PASS.

## References and root authority

`Ref` means `{ "path": "repository/relative/file", "sha256": "64 lowercase hex" }`.
Use forward slashes. No absolute paths, drive paths, `..`, duplicate resolved
references in one group, or links/junctions escaping the allowed root.
`RawRef` adds exactly one locator:

```json
{"path":"...","sha256":"...","locator":{"json_pointer":"/observations/0"}}
```

or `{"line_start":1,"line_end":3}` (inclusive, nonempty). JSON is parsed with
duplicate keys, NaN/Infinity and overflowing numeric literals rejected.

The caller supplies the actual root-owned `current_index` and issuance paths;
both must be inside W04-99/integration_codex. Those are trust inputs. A filesystem
checker cannot authenticate a human/agent merely from strings or re-created
message JSON. Root must preserve a real independently delivered issuance record.

## Execution layout (executor writes)

`execution_index.json`:

```json
{
  "schema":"researchos.w04.execution-index.v1",
  "task_id":"W04", "step_id":"W04-99", "run_id":"<actual run>",
  "executor_id":"<actual executor>",
  "cases":{
    "C03":{"run_receipt":"Ref","version_manifest":"Ref","command_receipt":"Ref","assertion_results":"Ref"},
    "C04":{"run_receipt":"Ref","version_manifest":"Ref","command_receipt":"Ref","assertion_results":"Ref"},
    "A01":{"run_receipt":"Ref","version_manifest":"Ref","command_receipt":"Ref","assertion_results":"Ref"}
  },
  "parent_gates":{"W04-G01":"Ref","W04-G02":"Ref","W04-G03":"Ref","W04-H01":"Ref","W04-B01":"Ref"}
}
```

`"Ref"` strings in examples are notation only; real files contain reference
objects. The index must not include the independent review or root context.
Each parent gate ref points to a command object described below.

Each case has four distinct JSON files:

| File | Required fields |
|---|---|
| run_receipt | `schema=researchos.w04.run-receipt.v1`, case_id, run_id, environment_mode=FIXTURE, os, arch, timezone, started_at, ended_at, executor_id, verifier_id |
| version_manifest | `schema=researchos.w04.version-manifest.v1`, case_id, run_id, code_revision (actual 40-hex commit), dirty (boolean), version_vector_ref |
| command_receipt | `schema=researchos.w04.command-receipt.v1`, case_id, run_id, commands (exactly two command objects) |
| assertion_results | `schema=researchos.w04.assertion-results.v1`, case_id, run_id, assertions, scenario |

The shared version vector has:

```json
{
  "schema":"researchos.w04.version-vector.v1", "package_version":"2.4.0",
  "spec_files":["Ref"], "source_files":["Ref"], "input_files":["Ref"],
  "lock_files":["Ref"], "tool_files":["Ref"],
  "environment":{"os":"Windows","arch":"amd64","timezone":"Asia/Shanghai"},
  "components":{
    "model":{"status":"not_applicable","reason":"<actual reason>"},
    "adapter":{"status":"applicable","version":"<actual version>","refs":["Ref"]},
    "rubric":{"status":"not_applicable","reason":"<actual reason>"},
    "policy":{"status":"applicable","version":"<actual version>","refs":["Ref"]}
  }
}
```

Each file group is nonempty. `spec_files` includes exact byte copies or originals
of frozen acceptance.json, tasks.json and execution.plan.json, plus applicable
manifest/rules such as file 15. The supplied authoritative spec is independently
checked against fixed hashes. Root owns the determination that source/input/
rule/dependency coverage is complete; the validator then checks every byte and
exact equality to the root-pinned vector. Receipt-only commit changes do not
invalidate unchanged applicable bytes. Actual execution commit/dirty state are
still recorded, never replaced with a synthetic value.

`tool_files` may reference a tool identity JSON instead of copying binaries:
`{schema:"researchos.w04.tool-identity.v1",locked_ref:Ref,tools:[{name,version,path,sha256}]}`.
`path` here is the actual absolute local executable path; hashes are re-read
without executing the binary. No UNC/network paths. Applicable component refs
must also be pinned in the vector; not_applicable requires a specific reason.

An execution command object has:

```json
{
  "schema":"researchos.w04.command.v1",
  "command_key":"test.context", "task_id":"W04", "mode":"FIXTURE",
  "run_id":"<actual run>", "executor_id":"<actual executor>",
  "selector":{"case_id":"C03"},
  "invocation_kind":"DIRECT_DRIVER", "registered_command_revision":null,
  "actual_argv":["<actual executable>","<actual arguments>"], "cwd":"<actual absolute cwd>",
  "environment_variable_names":[], "started_at":"<timestamp>", "ended_at":"<timestamp>",
  "exit_code":0, "stdout":"Ref", "stderr":"Ref", "source_invocation_refs":["Ref"]
}
```

For a gate use `selector:{check_id:"W04-G01"}`. This W04 implementation uses the
same two source invocations for all selectors: locked Go tests and locked Python
frozen package validation. Both source_invocation_refs are required. Each has
schema `researchos.w04.source-invocation.v1`, status, mode, actual_argv, cwd,
environment_variable_names, exit_code, executable_sha256, started_at, ended_at,
stdout, stderr and version_vector_ref. Actual exit/raw hashes/current vector and
tool bytes are checked. Go needs nonempty complete run/pass/package events with
no fail/skip; package validation must retain SPECIFICATION_PACKAGE_ONLY and
product_tests NOT_RUN. This process layout is a W04 implementation convention,
not a new frozen rule for other owners. Keep actual invocation records; never label a direct
driver run as dispatcher execution. Stdout must be a strict JSON object with
status PASS, task_id W04, the exact case/check selector, mode FIXTURE, and the
exact complete assertion_ids. If `assertions` exists it is an integer matching
that set. Empty output, boolean/nonzero exit and contradictory errors fail.

Each assertion row is `{id, expected, actual, status, command_keys,
raw_evidence_refs, refusal_evidence_refs?}`. Expected text exactly matches the
frozen assertion; actual must be present, and status must be PASS for completion.
Both frozen command keys must be named. All raw refs resolve to nonempty data.
`scenario` is `{expected:<nonempty object>, actual:<nonempty object>,
raw_evidence_refs:[RawRef]}`. These observations do not prove their own business
meaning. Independent review must inspect C03 precise propagation/T2/stale
promotion/refusals, C04 concurrency/duplicates/out-of-order/integration, and A01
isolation/tamper/package-only scope/two-project local inventory explicitly.

## Root current context and real registered dispatch

The root-owned current context is:

```json
{
  "schema":"researchos.w04.current-context.v1", "scope":"ROOT_CURRENT_APPLICABILITY",
  "task_id":"W04", "step_id":"W04-99", "execution_index":"Ref",
  "version_vector":"<complete vector object>",
  "execution_source_snapshot":{"code_revision":"<actual execution commit>","dirty":false,"version_vector_sha256":"<canonical vector digest>"},
  "source_coverage":{"roots":[{"path":"internal/domain","patterns":["*.go","*.json"]}],"exact_files":[],"paths_sha256":"<canonical sorted source paths digest>"},
  "registry_ref":"Ref",
  "registered_dispatches":[
    {"command_key":"test.context","case_id":"C03","mode":"FIXTURE","receipt_ref":"Ref"}
  ]
}
```

Execution phase does not require registered_dispatches. Review phases require
all eleven exact frozen bindings: six formal entries and five parent checks.
For gates replace case_id with check_id. Receipts are actual existing dispatcher
records, not normalized replacements: registered_command_revision is the
registry file SHA256, argv/cwd/environment_names describe the child actually
run, exit_code and child_exit_code must be integer zero. Input refs, dispatcher
hash, toolchain hash, registry key/selector, raw stdout/stderr and exact mode/IDs
are checked. The registered child stdout adds `execution_index_ref:Ref` to the
already fixed executor index, connecting reuse to that proof. Direct candidate
stdout does not add this ref, preventing a circular index hash.

Root pins the actual execution snapshot, including a truthful dirty boolean.
Every case's commit/dirty values must match this snapshot, and every applicable
file is rehashed. Root defines complete source_coverage roots/patterns and exact
files; the discovered set must exactly equal vector.source_files. Added/deleted
matching files invalidate old coverage. Paths digest and vector digest use UTF-8
`json.dumps(...,ensure_ascii=False,sort_keys=True,separators=(",",":"))`.
Coverage declaration remains a root responsibility; arbitrarily listing a small
subset and calling it complete is not independent coverage review.

## Independent fifth GLOBAL part and root-observed issuance

`independent_review.json` fields:

* schema `researchos.w04.independent-review.v1`; scope `EXTERNAL_FIXTURE_VERIFICATION`;
  task_id W04; step_id W04-99; executor_id; verifier_id; issued_at.
* acceptance_baseline_ref; evidence_index_ref; current_context_ref.
* owned_case_verdicts: exact C03/C04/A01 rows `{case_id,final_owner_task:"W04",
  mode:"FIXTURE",assertion_ids:[exact frozen set],status:"PASS",
  evidence_pointer:"/cases/C03",semantic_review:{status:"CONFIRMED",statement,
  raw_evidence_refs:[RawRef]}}`.
* parent_gate_verdicts: exact five rows `{check_id,mode:"FIXTURE",status:"PASS",
  command_ref:<same execution command ref as index>}`.
* open_blockers `[]`; construction_decision `ACCEPTED`.

The review is not executor-owned. It references the execution index and current
context; neither references the review. The root-observed issuance comes later
and refers to the completed review, so no hashes are cyclic.

Root-observed issuance fields: schema `researchos.w04.root-observed-issuance.v1`,
scope `ROOT_OBSERVED_INDEPENDENT_ISSUANCE`, observer_id, observed_at, issuer_id,
review_ref, current_context_ref, channel `independent_agent_message`, message_id,
message_ref. The root-retained message JSON has sender, message_id,
review_sha256 and actual content. Root must supply a real received message;
constructing an alternative identity string is not independent issuance.

Canonical step_state evidence paths retain their existing convention: relative
to `execution/v2.4`. Registered phase requires refs for review, root context and
root-observed issuance, identity/time consistency and accepted dependencies.
Competing registered reviews fail closed unless an explicit validated
supersession chain is supplied; never choose by file mtime. Current review may
include `supersedes_review_refs:[Ref]` and a nonempty `supersession_reason`.
The set must exactly match other registered same-schema W04 reviews, each hash
must match and each issue time must precede the current review. An unregistered
old review or an unmentioned conflicting registered review fails closed.

## Global derivation and tests

A future generic reader enumerates all 42 IDs from the frozen catalog and follows
only canonical step_state registered final-owner-99 references. This W04 module
is not a permanent shared import and does not write a separate manual ledger.

`test_validate.py` uses an isolated synthetic directory under this owned folder.
Its positive controls do not represent real product PASS or real identities.
`run_synthetic.py` records actual test invocation, raw output and source hashes
in immutable UUID folders marked SYNTHETIC_INTEGRITY_CONTROLS_NOT_PRODUCT_EVIDENCE.
Failed attempts are preserved. These are validator tests, never the ten formal
assertions or three accepted cases.
