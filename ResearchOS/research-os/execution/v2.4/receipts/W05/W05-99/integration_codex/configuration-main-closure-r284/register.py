import copy
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
WT = ROOT / ".local/worktrees/codex-w0599-provider-binding"
BASE = "execution/v2.4/receipts/W05/W05-99/"
MAIN = BASE + "main_configuration_composition_independent_review_codex/c34b6453-73e7-42ad-8ac0-511231cf78ab/"
AUTHOR = BASE + "provider_binding_executor_codex/epoch-correction-69a52b78d491456792bf394b01629e02/"
ROUTE = BASE + "provider_inventory_route_cause_review_codex/acde0511-095b-434e-890a-fc433561221a/"
CLARIFY = AUTHOR + "byte-difference-clarification-77968e4aac9749178ee8c8d2e73c0882/"
CANON = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def save(n, v):
    with (OUT / n).open("xb") as f:
        f.write(enc(v))


def ref(p, expected=None):
    raw = (ROOT / p).read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    if expected:
        assert h == expected, p
    return {"path": p, "sha256": h, "bytes": len(raw)}


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert cp["revision"] == 283 and ow["revision"] == 111 and len(cp["failure_counters"]) == 242
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "1b3cda2ee974916f864b9a0af988076d01ca65bd"
review_ref = ref(MAIN + "review.json", "ef848689f2eb795ca54c870a35e874b6d4aa2f5981165fc76159cd62b29db0fa")
handoff_ref = ref(MAIN + "handoff.json", "6cc499b3000aa1bba33a30400694bbd034c804ce85033a6f3ce8bb2669007c92")
manifest_ref = ref(MAIN + "manifest.json", "2380429debb05784074a2da86c429b9dae8e1c70c319ed3702a30fe7d5bf302a")
review = json.loads((ROOT / review_ref["path"]).read_bytes())
assert review["decision"] == "MAIN_CONFIGURATION_COMPOSITION_VERIFIED_WITH_DECLARED_OPEN_GATES"
assert review["main_head"] == head and review["counts"] == {"pass": 444, "top_pass": 123, "fail": 0, "skip": 0}
assert review["formal_increment"] == 0 and review["product_source_changes"] == 0
manifest = json.loads((ROOT / manifest_ref["path"]).read_bytes())
assert len(manifest["files"]) == manifest["count"] == 171
for r in manifest["files"]:
    assert (ROOT / r["path"]).resolve().is_relative_to((ROOT / MAIN).resolve())
    assert ref(r["path"]) == r, r["path"]
vectors = json.loads((ROOT / (MAIN + "inputs.current.json")).read_bytes())
assert len(vectors) == 42561
for p, h in vectors.items():
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == h, p
for cohort in review["cohorts"]:
    n = "test-" + cohort["cohort"]
    invocation = json.loads((ROOT / (MAIN + n + ".invocation.json")).read_bytes())
    assert invocation["exit"] == 0
    for stream in ["stdout", "stderr"]:
        assert ref(MAIN + n + "." + stream + ".raw")["sha256"] == invocation[stream + "_sha256"]
    assert json.loads((ROOT / (MAIN + n + ".counts.json")).read_bytes()) == cohort["counts"]
delta = json.loads((ROOT / (MAIN + "source-delta.audit.json")).read_bytes())
assert delta["actual_source_count"] == len(delta["source_rows"]) == 16
for r in delta["source_rows"]:
    blob = subprocess.check_output(["git", "cat-file", "blob", head + ":" + r["path"]], cwd=ROOT)
    assert blob == (ROOT / r["path"]).read_bytes() and hashlib.sha256(blob).hexdigest() == r["sha256"]

copied = []
for suffix, expected, count in [("stopped_manifest.v2.json", "d3cead72141f975e8dbbb67c21eb4ef9ad37b061de30b671bc8e61da8b72a2bf", 78), ("byte-difference-clarification-77968e4aac9749178ee8c8d2e73c0882/manifest.json", "156982f2327898137ed4cb09b31e9ccea0f972a631ba4dbb48afa0ff76491f62", 1)]:
    source = WT / (AUTHOR + suffix)
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    m = json.loads(raw)
    assert len(m["files"]) == count
    rows = m["files"] + [{"path": str(source), "sha256": expected, "bytes": len(raw)}]
    for r in rows:
        p = Path(r["path"])
        assert p.resolve().is_relative_to((WT / AUTHOR).resolve())
        data = p.read_bytes()
        assert hashlib.sha256(data).hexdigest() == r["sha256"] and len(data) == r["bytes"]
        target = ROOT / p.relative_to(WT)
        if target.exists():
            assert target.read_bytes() == data
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as f:
                f.write(data)
        copied.append(ref(target.relative_to(ROOT).as_posix()))
save("public_provider_evidence_copy_audit.json", {"copied_files": copied, "exact_count": len(copied), "source_prefix_only": str(WT / AUTHOR), "private_resources_copied": False})
author_failure_ref = ref(AUTHOR + "failure_origins.json", "4b2ae8ae1d035b12a7d52e17d1b36aa136a6bec0c0884173d6166b93cc31e7ac")
clarification_ref = ref(CLARIFY + "clarification.json", "f6c8e6854d79b5b09947f40c8a57b40fc46a592f421cecef6c8681638093a559")
origin = json.loads((ROOT / author_failure_ref["path"]).read_bytes())[0]
for n in ["invocation", "stdout", "stderr", "result", "actual", "closed_db", "original_input"]:
    r = origin[n]
    assert hashlib.sha256(Path(r["path"]).read_bytes()).hexdigest() == r["sha256"]
invocation = json.loads(Path(origin["invocation"]["path"]).read_bytes())
actual = json.loads(Path(origin["result"]["path"]).read_bytes())
assert actual["exit"] == 1 and actual["argv"] == invocation["argv"]
assert origin["author_source_attempt"] == 2 and origin["issue_failed_invocations_after"] == 3
assert origin["original_input"]["sha256"] != origin["closed_db"]["sha256"]
main_failure_ref = ref(MAIN + "failure_origins.json", "0fd2cbd78c994be8bab4e53ec4f9a92f7937b475553e18ba98fbb7bbb386edbb")
main_origins = json.loads((ROOT / main_failure_ref["path"]).read_bytes())["origins"]
assert [r["actual_outer_exit"] for r in main_origins] == [1, 0]
route_review_ref = ref(ROUTE + "source_scope_review.json", "c145312ae48c21259735649ee1ec4a54881a904f9a8183ffd5f15bc9f8f95370")
route_failure_ref = ref(ROUTE + "failure_origins.json", "74ed86d5dc185d19bcecc63dcdd12a4f9c4996041b9c7973cea000bb91fe5b33")
route_origins = json.loads((ROOT / route_failure_ref["path"]).read_bytes())["tooling_diagnostics"]
assert [r["actual_outer_exit"] for r in route_origins] == [0, 1]
prior = copy.deepcopy(cp["failure_counters"])
new = [("W05-99/P9-P12-SR01/typed-route/" + origin["invocation"]["sha256"], "ACTUAL_SAME_RUN_TOOL_FALSE_MODEL_CLASSIFICATION_EXIT1", author_failure_ref, origin), ("W05-99/main-configuration-prep/845357", "ACTUAL_READONLY_WINDOWS_LITERALGLOB_EXIT1_TRANSCRIPT_ONLY", main_failure_ref, main_origins[0]), ("W05-99/provider-route-cause-seal/2455de", "ACTUAL_READONLY_RECEIPT_LOCATOR_EXIT1_TRANSCRIPT_ONLY", route_failure_ref, route_origins[1])]
for key, status, ev, detail in new:
    assert key not in {r.get("origin_key") for r in cp["failure_counters"]}
    cp["failure_counters"].append({"origin_key": key, "attempts": 1, "retries_used": 0, "status": status, "evidence_ref": ev, "detail": detail, "counter_reset": False, "formal_increment": 0})
assert cp["failure_counters"][:242] == prior and len(cp["failure_counters"]) == 245
for ev, detail in [(main_failure_ref, main_origins[1]), (route_failure_ref, route_origins[0])]:
    cp.setdefault("preserved_unindexed_tool_diagnostics", []).append({"evidence_ref": ev, "observation": detail, "reason": "Outer shell exit0 retained unindexed; not a failed invocation."})
chain = cp["failure_chains"]["W05-99/P9-P12-SR01"]
assert chain["actual_failed_invocations"] == 2 and chain["author_source_repair_attempts"] == 2
chain.update(actual_failed_invocations=3, latest_author_failed_origin_ref=author_failure_ref, status="TWO_REGISTERED_PREREQUISITES_PROGRESS_THIRD_ACTUAL_FAILURE_STOPPED_TYPED_ROUTE_CAUSE_REVIEW_ONLY", typed_route_cause_review_ref=route_review_ref, byte_difference_clarification_ref=clarification_ref, counter_reset=False)
assert cp["failure_chains"]["W05-99/provider9-original-history-refusal"]["actual_failed_invocations"] == 5

byte_review_ref = ref(BASE + "provider_inventory_route_cause_review_codex/byte-limit-supplement-da6c6277-c38c-49ad-9428-8eba35f590ba/supplement.json", "6fa20397c0b7b235250028298c60af06afaef2e20065b5fbc09aee84423cf1d5")
chain["independent_byte_limitation_ref"] = byte_review_ref
spec = importlib.util.spec_from_file_location("current_formal", ROOT / "execution/v2.4/formal_case_index.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
plan = ROOT / ".local/worktrees/v24-continuation/spec/v2.4/contracts/execution.plan.json"
assert hashlib.sha256(plan.read_bytes()).hexdigest() == "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17"
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
formal = module.derive_formal_cases(ROOT, CANON[2], plan)
save("formal-index.json", formal)
save("formal-index.invocation.json", {"kind": "ACTUAL_READ_ONLY_DERIVE_CALL", "function": "formal_case_index.derive_formal_cases", "repo": str(ROOT), "plan": str(plan), "state": str(CANON[2]), "started_at": start, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "formal_cases_accepted": formal["formal_cases_accepted"], "derived_integrity": formal["integrity"], "product_gate_executed": False})
formal_ref = ref((OUT / "formal-index.json").relative_to(ROOT).as_posix())
assert formal["required_formal_cases"] == 42 and formal["formal_cases_accepted"] == 0
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
sub = ow["card_path_bindings"]["W05-99"]["subtasks"]["host_configuration_upgrade_prerequisites"]
sub.update(state="MAIN_EXACT16_CURRENT_SOURCE_COMPOSITION_VERIFIED_DECLARED_OPEN_GATES", current_source_writer=False, main_source_head=head, main_composition_review_ref=review_ref, final_test_supplement_state="INTEGRATED_NONSELF_MAIN_CURRENT_VALIDATED")
provider = ow["card_path_bindings"]["W05-99"]["subtasks"]["provider_transport_reasoning_binding"]
provider.update(state="EPOCH_ATTEMPT_TWO_PREREQUISITES_PROGRESS_TOOL_FALSE_REJECTION_STOPPED_NO_THIRD_AUTHORIZATION", current_source_writer=False, typed_route_cause_review_ref=route_review_ref)
cp.update(revision=284, expected_previous_revision=283, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=112, amended_at=now, amended_by="codex:/root")
cp["work_in_progress"].update(configuration_main_current_nonself_test="444PASS/123TOP/0FAIL/0SKIP; current42561 stable; source16 only, formal0/42", configuration_main_composition_review_ref=review_ref, formal_current_index_ref=formal_ref, current_formal_index_ref=formal_ref, formal_cases_current=0, provider_typed_route_cause_review_ref=route_review_ref, next_action="Freeze reviewed handler interface decisions/exact16 or precise extra paths; nonauthor scope review before writes. Provider original3 failures/history5 preserved; no automatic third repair. F08 remains later serial branch.")
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "MAIN_CONFIGURATION_444_CURRENT_NONSELF_COMPOSITION_REGISTERED_PROVIDER_TYPED_ROUTE_FAILURE_PRESERVED", "main_head": head, "review_ref": review_ref, "formal_index_ref": formal_ref, "failure_origins": [242, 245], "provider_issue_failed_invocations": 3, "provider_author_attempts": 2, "original_history5_held": True, "closed_case_original_semantic_equivalence": "UNPROVEN_DIFFERENT_BYTES_NO_PAIRED_ALL_ROWS", "formal_increment": 0})
refs = [review_ref, handoff_ref, manifest_ref, author_failure_ref, clarification_ref, main_failure_ref, route_review_ref, route_failure_ref, byte_review_ref, formal_ref]
for r in refs:
    if r["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(r["path"])
save("record.json", {"checkpoint": [283, 284], "ownership": [111, 112], "failure_origins": [242, 245], "main_review_ref": review_ref, "formal_index_ref": formal_ref, "provider_failure_ref": author_failure_ref, "provider_byte_limitation_ref": clarification_ref, "scope": "Current Main source composition only; no parent/formal acceptance or third provider execution authorization", "formal_increment": 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root284.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 284, "ownership": 112, "failure_origins": 245, "main_pass": 444, "formal_current": 0, "formal_increment": 0}))
