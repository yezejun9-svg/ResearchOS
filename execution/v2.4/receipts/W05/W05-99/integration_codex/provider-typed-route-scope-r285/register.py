import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
WT = ROOT / ".local/worktrees/codex-w0599-provider-binding"
BASE = "execution/v2.4/receipts/W05/W05-99/"
CAUSE = BASE + "provider_inventory_route_cause_review_codex/acde0511-095b-434e-890a-fc433561221a/"
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
assert cp["revision"] == 284 and ow["revision"] == 112 and len(cp["failure_counters"]) == 245
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip() == "1b3cda2ee974916f864b9a0af988076d01ca65bd"
review_ref = ref(CAUSE + "source_scope_review.json", "c145312ae48c21259735649ee1ec4a54881a904f9a8183ffd5f15bc9f8f95370")
review = json.loads((ROOT / review_ref["path"]).read_bytes())
assert review["decision"] == "SOURCE_SCOPE_READY_NARROW_TYPED_ROUTE_CORRECTION_PENDING_ROOT_AUTHORIZATION"
assert review["execution_boundary"]["this_review_tests"] == review["execution_boundary"]["sql_probes"] == 0
source_freeze = {}
for p, expected in [("internal/domain/runtime_model_verification.go", "4ba4845d63db4cd4a74f819fbe1b52cbae2210f7748b0122872d867c18e11256"), ("internal/domain/runtime_provider_binding_windows_test.go", "026a0a6dd47d04132cef53f8eabfc616513ce77ff0359847d99ec251d298399b")]:
    raw = (WT / p).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected
    source_freeze[p] = {"path": str(WT / p), "sha256": expected, "bytes": len(raw)}
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {"schema": "researchos.root.provider-typed-route-causal-scope.v1", "actor": "codex:/root", "executor": "codex:/root/command_queue_impl", "created_at": now, "card": "W05-99", "issue": "P9-P12-SR01", "source_scope": review["exact_scope"], "source_before": source_freeze, "independent_cause_review_ref": review_ref, "previous_scope_ref": cp["failure_chains"]["W05-99/P9-P12-SR01"]["repair_scope_ref"], "algorithm_in_order": review["required_algorithm_in_order"], "precision": review["precision_notes"], "mandatory_control_groups": review["controls_for_root_to_register_not_executed"], "authorization_reason": "Distinct first TOOL input false classification has an independently identified cause. Prior registered PREPARED acceptance and precise red refusal are two actual measured advances. One targeted repair of this distinct failure is authorized; neither original red nor history5 is restarted/reset.", "attempt_accounting": {"cumulative_actual_issue_failed_invocations_before": 3, "author_source_repair_attempts_before": 2, "author_source_repair_attempts_after_authorized_once": 3, "automatic_retries_of_this_tool_failure": 0, "original_model_history_failures_held": 5, "counter_reset": False}, "validation": {"maximum_control_cases": 64, "source_attempts": 1, "execution_plan": "Seal exact named <=64 control plan and expected specific layers before first case; include R01/R02/R03 as first three, remaining R04-R09 with genuine original or explicit SYNTHETIC_NOT_PRODUCT inputs. Group labels are not assertion counts. Do not rerun held original model positive tests.", "database_semantic_gate": "For unmutated positive fixtures capture paired complete deterministic public schema and all table/row multisets from exact input copy before store.Open and from closed output after validators; capture SQL/schema objects, triggers, all original rows and original input file hash. Require exact semantic equality for positive case acceptance. Register expected mutation deltas for negative copies, restore triggers exactly. Header/WAL byte changes stay explicit; old case02 has no retrospective equivalence credit.", "first": "Original sealed PREPARED: both validators accept, nonempty original MODEL inventory1, complete paired semantic equality.", "second": "Original P12 exact red: both specifically reject missing original dispatch/provenance; no generic early error credit.", "third": "Original mixed same Run fixture: both validators accept exact original three MODEL inventory keys and exclude only original positively proven TOOL, full paired semantic equality including budget rows. No history/qualification acceptance inferred.", "freeze": "Freeze actual complete current source9/exact2 diff, original7 DBs, whole compiled dependencies/SQL/API/SDK locks/tool binaries/environment/test executable/bundle before firstcase and after/current. No old input vectors used as current proof.", "stop": "First unexpected acceptance/refusal, wrong cause, ambiguity, semantic drift or missing original proof immediately stops this repair lane and dependent public chains. Preserve actual raw/input/closed DB/source; no automatic fourth source repair, new case run or old-history retry. Unsupported original provenance remains explicitly blocked.", "optional_public_backup": "At most6 original unchanged local CreateBackup/RestoreBackup/rebackup chains and6 corrupted CreateBackup controls, within64 cap, only after complete internal prereqs and full legacy/public proof. No forged archive or rewritten original snapshots.", "models": 0, "worker_starts": 0, "provider_http_calls": 0, "paid": 0, "held_positive_tests": 0, "private_or_holdout_reads": 0}, "protected": ["Other original7 provider source and all nonprovider source", "MODEL typed epoch/original Run/admission/profile/runtime joins and budget/history/UNKNOWN semantics", "SDK/wire/API/CLI/Host credentials/SQL migrations", "Original input DB/red/raw and prior failure chains", "Root canonical/acceptance state"], "acceptance": "Source scope only. Nonself actual frozen replay/source review and current Main composition still required. No author self-acceptance, provider qualification, public restore proof or formal acceptance is created.", "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
argv = [sys.executable, "-B", "-X", "utf8", r"D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4\tools\task_packet.py", "next", "--state", str(CANON[2])]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
p = subprocess.run(argv, cwd=ROOT, capture_output=True)
for name, raw in [("task_packet.stdout.raw", p.stdout), ("task_packet.stderr.raw", p.stderr)]:
    with (OUT / name).open("xb") as f:
        f.write(raw)
save("task_packet.invocation.json", {"argv": argv, "cwd": str(ROOT), "started_at": started, "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "actual_exit": p.returncode, "stdout_sha256": hashlib.sha256(p.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(p.stderr).hexdigest(), "product_gate_executed": False})
assert p.returncode == 0
packet = json.loads(p.stdout)
save("task_packet.observed.json", {"actual_packet": packet, "authority": "Read-only specification structure/selector; not source or business acceptance"})
for p, raw in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(raw)
chain = cp["failure_chains"]["W05-99/P9-P12-SR01"]
assert chain["actual_failed_invocations"] == 3 and chain["author_source_repair_attempts"] == 2
assert cp["failure_chains"]["W05-99/provider9-original-history-refusal"]["actual_failed_invocations"] == 5
chain.update(status="THREE_FAILURES_RETAINED_DISTINCT_TYPED_TOOL_ROUTE_CAUSAL_CORRECTION_ONCE_AUTHORIZED", author_source_repair_attempts=3, repair_scope_ref=scope_ref, counter_reset=False)
sub = ow["card_path_bindings"]["W05-99"]["subtasks"]["provider_transport_reasoning_binding"]
sub.update(state="DISTINCT_TYPED_ROUTE_CAUSAL_CORRECTION_ONE_EXACT2_ATTEMPT_AUTHORIZED", current_source_writer=True, typed_route_scope_ref=scope_ref)
cp.update(revision=285, expected_previous_revision=284, updated_at=now, updated_by="codex:/root")
ow.update(revision=113, amended_at=now, amended_by="codex:/root")
cp["work_in_progress"].update(provider_inventory_causal_repair_scope_ref=scope_ref, provider_typed_route_semantic_gate="New positive cases require complete paired schema+row equality; old case02 remains unproven")
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "DISTINCT_TYPED_TOOL_ROUTE_CAUSAL_SCOPE_ONCE_REGISTERED_NO_FAILURE_RESET", "scope_ref": scope_ref, "actual_failed_invocations": 3, "author_attempts": 3, "counter_reset": False, "old_history5_held": True, "formal_increment": 0})
cp["evidence_index"].append(scope_ref["path"])
save("record.json", {"checkpoint": [284, 285], "ownership": [112, 113], "failure_origins": [245, 245], "scope_ref": scope_ref, "author_attempts": [2, 3], "formal_increment": 0})
assert all(p.read_bytes() == raw for p, raw in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root285.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 285, "ownership": 113, "failure_origins": 245, "scope_ref": scope_ref, "formal_increment": 0}))
