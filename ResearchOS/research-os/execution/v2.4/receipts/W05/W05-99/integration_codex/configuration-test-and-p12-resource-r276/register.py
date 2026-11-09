import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
WT = ROOT / ".local/worktrees/codex-w0599-host-configuration-upgrade"
OUT = Path(__file__).resolve().parent
BASE = "execution/v2.4/receipts/W05/W05-99/"
HP = BASE + "host_configuration_upgrade_executor_codex/handoff-5375496dd2b24206b5db17fc9bc358c3/"
FP = BASE + "host_configuration_upgrade_executor_codex/implementation-df2b17aedb254da9b0fb902ca7f8575f/"
PP = BASE + "provider_binding_zero_model_adjudication_codex/d7f95235-03e1-464f-b3b0-374ca7394fda/attempt2/"
CANON = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode()


def save(n, v):
    with (OUT / n).open("xb") as f:
        f.write(enc(v))


def ref(p, expected=None, source=ROOT, import_file=False):
    p = p.replace("\\", "/")
    raw = (source / p).read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    if expected:
        assert h == expected, p
    if import_file:
        assert p.startswith(BASE + "host_configuration_upgrade_executor_codex/")
        target = ROOT / p
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == raw, p
        else:
            with target.open("xb") as f:
                f.write(raw)
    return {"path": p, "sha256": h, "bytes": len(raw)}


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert cp["revision"] == 275 and ow["revision"] == 103 and len(cp["failure_counters"]) == 227
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "26e1043751c989d4e6016a76f113e343c9e38382"
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
proposal = ref(HP + "followup_test_scope_proposal.json", "9cb659c739a9869642b5691854ac8c531900abdbcd9f0ff3322ed9f13f3439b7", WT, True)
final_failures = ref(HP + "failure_origins.final.json", "99ab3b54cea0b2bf42f05c250e8f7c57b4d89cfda5a0a4e6a4bd75783ffcc75b", WT, True)
first_failures = ref(FP + "failure_origins.first.json", "05e50bf94104a8c57a9e0280bf0945bed1b2e2dcf4333fc1c7c681ff0aeb2c6b", WT, True)
prop = json.loads((ROOT / proposal["path"]).read_bytes())
ff = json.loads((ROOT / final_failures["path"]).read_bytes())
first = json.loads((ROOT / first_failures["path"]).read_bytes())
assert hashlib.sha256((WT / prop["requested_exact_path"]).read_bytes()).hexdigest() == prop["original_source_ref"]["sha256"] == "97746789f50114faf6917783f02d9e0cec49f7d4c2cfcc551217e2052c0e838d"
old = copy.deepcopy(cp["failure_counters"])
imported = []
seen = set()
for item in ff["actual_test_failures"]:
    assert item["actual_exit"] == 1
    for k in ["invocation", "stdout"]:
        imported.append(ref(item[k]["path"], item[k]["sha256"], WT, True))
    inv = item["invocation"]["sha256"]
    assert inv not in seen
    seen.add(inv)
    cp["failure_counters"].append({"origin_key": "W05-99/configuration23/" + inv, "attempts": 1, "retries_used": 0, "status": item["classification"], "evidence_ref": final_failures, "detail": item, "counter_reset": False, "formal_increment": 0})
for item in first["product_failure_origins"] + first["tooling_failure_origins"]:
    inv = ref(item["invocation"], source=WT, import_file=True)
    if inv["sha256"] in seen:
        continue
    assert item["actual_exit"] == 1
    seen.add(inv["sha256"])
    imported.append(inv)
    cp["failure_counters"].append({"origin_key": "W05-99/configuration23/" + inv["sha256"], "attempts": 1, "retries_used": 0, "status": "ORIGINAL_CAPTURED_PREBUILD_FAILURE", "evidence_ref": first_failures, "detail": item, "counter_reset": False, "formal_increment": 0})
assert len(seen) == 4
cp.setdefault("preserved_unindexed_tool_diagnostics", []).append({"source_ref": first_failures, "observations": {k: first[k] for k in ["prior_apply_patch_tool_errors", "read_only_diagnostics"]}, "supplement_ref": final_failures, "supplement_observation": ff["tool_read_diagnostic"], "note": "Conversation-only/component/outer-exit diagnostics preserved; no fabricated raw/exit or ambiguous duplicate count. Expected missing-mirror build refusal is a passing negative control, not a failed product execution."})
p12failure = ref(PP + "failure_origins.json", "1e2ff9c3444fec49d074cbb436ae559e9a59a5b4d813931205c5b48a74d47f6c")
f12 = json.loads((ROOT / p12failure["path"]).read_bytes())
assert len(f12["entries"]) == 1
for item in f12["entries"]:
    for n in ["invocation", "stdout", "stderr"]:
        p = Path(item[n]["path"])
        assert p.resolve().is_relative_to(ROOT.resolve()) and hashlib.sha256(p.read_bytes()).hexdigest() == item[n]["sha256"]
    assert item["actual_exit"] == 1 and item["model_calls"] == item["test_cases"] == 0
    cp["failure_counters"].append({"origin_key": "W05-99/p12-independent-precompile/" + item["id"], "attempts": 1, "retries_used": 0, "status": "SECOND_CAUSAL_PUBLIC_COMPILATION_DEPENDENCY_STOP", "evidence_ref": p12failure, "detail": item, "counter_reset": False, "formal_increment": 0})
assert len(cp["failure_counters"]) == 232 and cp["failure_counters"][:227] == old
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
testscope = {"schema": "researchos.root.test-source-scope.v1", "state": "AUTHORIZED_EXACT_ONE_TEST_FILE_AFTER_INDEPENDENT_ROOT_SCOPE_REVIEW", "actor": "codex:/root", "executor": "codex:/root/sources_parent_impl", "at": now, "parent": "W05", "card": "W05-99", "proposal_ref": proposal, "path": prop["requested_exact_path"], "original_sha256": prop["original_source_ref"]["sha256"], "allowed_changes": prop["minimal_change"], "fixed_current_schema": 23, "fixed_historical_schema": 22, "sql23_sha256": "07feef35d8d114f3d31aa99684ce85be9d2fafd2d5090a2c8548789b636cf794", "protected": "All original assertions outside precise fresh-current expectation and new explicit historical22 fixture; all production10/foundation5/API/numberedSQL bytes frozen. No >= version relaxation, historical recovery changes, fake generation or source22 startup qualification from numbered-only fixture.", "validate": "New actual current/historical exact schema controls and original queue/backup suite with current frozen inputs/test executable. Preserve every oldfailed raw. Historical14 current-helper incompatibility remains OPEN separately; fixed14CLI rerun fact does not qualify ActiveRecovery. New scope does not grant Main23 or formal acceptance.", "formal_increment": 0}
save("test_scope_registration.json", testscope)
testref = ref((OUT / "test_scope_registration.json").relative_to(ROOT).as_posix())
candidate = "976c8c9a6bdf8703475e02b79b77f4c5fab2d650"
deps = []
for p in ["evaluation/evolution/control_current.go", "evaluation/evolution/control_protocol.go", "evaluation/evolution/control_release.go", "evaluation/evolution/holdout.go", "evaluation/evolution/suite.go", "evaluation/skills/compare.go", "evaluation/skills/rubric.go"]:
    raw = subprocess.check_output(["git", "show", candidate + ":" + p], cwd=ROOT)
    assert b"func init(" not in raw and b"//go:embed" not in raw
    deps.append({"path": p, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
recovery = {"schema": "researchos.root.public-compile-dependency-recovery.v1", "actor": "codex:/root", "executor": "codex:/root/w05_merge_review", "at": now, "source_candidate": candidate, "original_scope_ref": ref(BASE + "integration_codex/provider-zero-model-scope-r274/scope_registration.json"), "preceding_stop_failure_ref": p12failure, "allowed_files": deps, "source9_unchanged": True, "actual_holdout_private_data_reads": 0, "test_dataset_generator_or_DPAPI_execution": 0, "models_paid_worker": 0, "automatic_retry": False, "original_history_failures": 5, "counter_reset": False, "restoration_condition": "Root independently checked all7 original Git production compile blobs and absence of init/embed side effects; reviewer compared complete original compile vector missing paths. Export only7 non-test files into isolated checkout with exact blobs then one precompile attempt. No further missing-resource repair without Root, and no third same-input automatic retry. Complete frozen driver and existing sixDB budget only; held positive tests remain held.", "formal_increment": 0}
save("p12_resource_scope_registration.json", recovery)
p12ref = ref((OUT / "p12_resource_scope_registration.json").relative_to(ROOT).as_posix())
sub = ow["card_path_bindings"]["W05-99"]["subtasks"]
config = sub["host_configuration_upgrade_prerequisites"]
config.setdefault("scope_history", []).append({"scope_ref": config["scope_ref"], "paths": list(config["paths"]), "state": config["state"]})
assert len(config["paths"]) == 10
config["paths"].append(prop["requested_exact_path"])
config.update(state="FROZEN_EXACT10_PLUS_AUTHORIZED_ONE_TEST_FILE_SCHEMA23_CURRENT_HISTORICAL22_EXPECTATIONS_MAIN_HOLD", current_source_writer=True, test_supplement_scope_ref=testref, executor_failures_ref=final_failures)
sub["durable_queue_control"]["current_source_writer"] = False
ow.setdefault("path_lease_transfers", []).append({"at": now, "path": prop["requested_exact_path"], "from": "historical durable_queue_control construction, no current writer", "to": "codex:/root/sources_parent_impl schema23 onefile test supplement", "scope_ref": testref})
sub["provider_transport_reasoning_binding"].update(zero_model_second_precompile_stop_ref=p12failure, zero_model_second_public_dependency_recovery_ref=p12ref, author_retry_authorized=False)
cp.update(revision=276, expected_previous_revision=275, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=104, amended_at=now, amended_by="codex:/root")
cp["next_command"] = "Schema23 exact10 frozen then registered1test supplement (currentstrict23 plus explicitimmutable22fixture) closes freshhardpin without altering production/legacyguards; historical14ActiveRecovery inherited OPEN, fixed14CLI truePASS. P12 two distinct missingpublic package precompile originals preserved, Root causal exact7Git dependency recovery then only fixedsixDB zero-model controls; original-history5 held. Sourceindependentfreeze/Main23pending, F08/configure readonlyfuture;22/42 required."
cp["note"] = "227counterprefix immutable+4unique actualconfiguration23 failedinvocations (3testclosures+oneold22Go-list) +oneP12secondprecompile=232. Firstfixture duplicate finalfile not recounted; transcript-only unknown/outer-component diagnostics stored separately, no fabricated raw. Test-only1path change authorized alongside exact10 frozenproduction; numbered22/23 SQL untouched. P12 resource5prior+7additional exact immutable public compile sources, no test/privateheld/generator execution, samehistory5 noreset."
cp["work_in_progress"].update(status="SCHEMA23_EXACT10_FROZEN_ONE_TEST_SUPPLEMENT_AND_P12_EXACT7_CAUSAL_DEPENDENCY_RECOVERY", next_action=cp["next_command"], configuration_test_supplement_scope_ref=testref, provider_zero_model_second_recovery_ref=p12ref)
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "SCHEMA23_EXACT_ONE_TEST_SCOPE_AND_P12_EXACT7_PUBLIC_DEPENDENCIES_REGISTERED", "test_scope_ref": testref, "p12_scope_ref": p12ref, "failure_origins": [227, 232], "formal_increment": 0})
for v in [proposal, first_failures, final_failures, p12failure, testref, p12ref]:
    if v["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(v["path"])
save("record.json", {"checkpoint": [275, 276], "ownership": [103, 104], "failure_origins": [227, 232], "test_scope_ref": testref, "p12_scope_ref": p12ref, "copied_public_failure_refs": imported, "formal_increment": 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root276.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 276, "ownership": 104, "failure_origins": 232, "test_scope_ref": testref, "p12_scope_ref": p12ref, "formal_increment": 0}))
