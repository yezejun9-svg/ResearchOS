import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
OUT = Path(__file__).resolve().parent
WT = ROOT / ".local/worktrees/codex-w0599-provider-binding"
BASE = "execution/v2.4/receipts/W05/W05-99/"
AUTHOR = BASE + "provider_binding_executor_codex/causal-repair-481c0dc455c643f5a2e70b7178c97fe2/"
REVIEW = BASE + "provider_inventory_epoch_cause_review_codex/fa6d4045-d881-41bb-b220-ef0066de934a/"
OLD = BASE + "integration_codex/provider-inventory-scope-clarification-r280/scope_registration.corrected.json"
CANON = [ROOT / ("execution/v2.4/" + n) for n in ["checkpoint.json", "path_ownership.json", "step_state.json", "commands.json"]]


def enc(v):
    return (json.dumps(v, ensure_ascii=False, indent=2) + "\n").encode()


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
assert cp["revision"] == 282 and ow["revision"] == 110 and len(cp["failure_counters"]) == 238
review_ref = ref(REVIEW + "review.json", "1ca73c8fa6d4b84fb046c61b8d4762577c4ac83b1dc565a7c23db891250d97f3")
review_failure_ref = ref(REVIEW + "failure_origins.json", "7b536503c9a5611116b4911e72da33d209e14e850fcf317c96081eaf58bc3c78")
review = json.loads((ROOT / review_ref["path"]).read_bytes())
assert review["decision"] == "SOURCE_SCOPE_READY_NARROW_TYPED_EPOCH_CORRECTION_NOT_SOURCE_ACCEPTANCE"
assert review["new_case_runs"] == review["new_db_queries"] == 0
for r in review["observed_sources"]:
    assert hashlib.sha256(Path(r["path"]).read_bytes()).hexdigest() == r["sha256"]
manifest_source = WT / (AUTHOR + "stopped_manifest.json")
assert hashlib.sha256(manifest_source.read_bytes()).hexdigest() == "9d6f61a5f99c822bf4fbe492224a66121f46fb59fa60ab0b10526d6cedb5fdaf"
manifest = json.loads(manifest_source.read_bytes())
assert len(manifest["files"]) == 69
for r in manifest["files"]:
    p = Path(r["path"])
    assert p.resolve().is_relative_to((WT / AUTHOR).resolve())
    raw = p.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == r["sha256"] and len(raw) == r["bytes"]
    target = ROOT / p.relative_to(WT)
    if target.exists():
        assert target.read_bytes() == raw
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as f:
            f.write(raw)
target = ROOT / (AUTHOR + "stopped_manifest.json")
if target.exists():
    assert target.read_bytes() == manifest_source.read_bytes()
else:
    with target.open("xb") as f:
        f.write(manifest_source.read_bytes())
author_failure_ref = ref(AUTHOR + "failure_origins.json", "10da140ee535336a6cdd56c97889f01c502382b491690763533ed92b2189e0dc")
proposal_ref = ref(AUTHOR + "epoch_parameter_correction_proposal.json", "125832246f8eda072b80935abbaf588fa227b46c351b412ac5f30ebc1808a50e")
origins = json.loads((ROOT / author_failure_ref["path"]).read_bytes())
assert len(origins) == 1
origin = origins[0]
for n in ["input", "invocation", "stdout", "stderr", "result", "actual", "closed_db"]:
    r = origin[n]
    assert hashlib.sha256(Path(r["path"]).read_bytes()).hexdigest() == r["sha256"]
assert json.loads(Path(origin["invocation"]["path"]).read_bytes())["actual_exit"] == 1
rf = json.loads((ROOT / review_failure_ref["path"]).read_bytes())["origins"]
assert len(rf) == 2 and rf[0]["actual_exit"] == 1 and rf[1]["shell_exit"] == 0
old_origins = copy.deepcopy(cp["failure_counters"])
new = [("W05-99/P9-P12-SR01/author-causal-epoch/" + origin["invocation"]["sha256"], "ACTUAL_UNCHANGED_PREPARED_FALSE_REJECTION_TYPED_EPOCH_CAUSE", author_failure_ref, origin), ("W05-99/provider-epoch-review/b53ca2", "ACTUAL_READONLY_QUOTE_COMMAND_EXIT1_TRANSCRIPT_ONLY", review_failure_ref, rf[0])]
for key, status, ev, detail in new:
    assert key not in {v.get("origin_key") for v in cp["failure_counters"]}
    cp["failure_counters"].append({"origin_key": key, "attempts": 1, "retries_used": 0, "status": status, "evidence_ref": ev, "detail": detail, "counter_reset": False, "formal_increment": 0})
assert cp["failure_counters"][:238] == old_origins and len(cp["failure_counters"]) == 240
cp.setdefault("preserved_unindexed_tool_diagnostics", []).append({"evidence_ref": review_failure_ref, "observation": rf[1], "reason": "Actual shell0 after literal Windows glob error; not a failed invocation or product test."})
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
scope = {"schema": "researchos.root.narrow-causal-correction-scope.v1", "actor": "codex:/root", "executor": "codex:/root/command_queue_impl", "at": now, "card": "W05-99", "issue": "P9-P12-SR01", "original_scope_ref": ref(OLD, "d6111c412b43994b964342e0d27584a3bb6b9498cfe31534c4b61815d899e25c"), "original_candidate": "976c8c9a6bdf8703475e02b79b77f4c5fab2d650", "failed_attempt_source_freeze": review["observed_sources"], "prior_failed_attempt_ref": author_failure_ref, "proposal_ref": proposal_ref, "independent_cause_review_ref": review_ref, "production_change": review["allowed_minimal_change"], "source_scope": "Exactly same2 original-owned files. Only providerOriginalRun parameter conversion and bounded strengthened epoch/provenance assertions; other first-repair code frozen. No third source file/schema/wire/history/SDK/API/CLI/backups changes.", "validation": {"additional_author_attempts": 1, "author_source_repair_attempts_total_after_this": 2, "cumulative_same_issue_failed_invocations_before": 2, "counter_reset": False, "maximum_zero_model_control_cases": 64, "first_case": "Unchanged original sealed PREPARED closed DB must yield nonempty bound original MODEL inventory and both validators accept. If not, STOP; no red credit.", "second_case": "Original P12 exact red copy must resolve original Run and reject at correct missing dispatch/provenance boundary in both validators, with specific cause asserted. Generic any-error is not a passing control.", "remaining": "Only original registered C10 sixDB bounded states/mutations and explicit SYNTHETIC_NOT_PRODUCT integer epoch/no-policy/legacy controls, plus specific cause-review required controls if both prerequisites pass. Source-defined generic lacking original exact revision remains explicitly compatibility blocked; no marker/current/latest fallback.", "freeze": "Rebuild and freeze complete actual current source9/exact2 diff/compiler dependencies/SQL/API/SDK locks/tools/environment/test executable/bundle inputs before firstcase and after/current. Original source/red/7 original DB hashes preserved. No old vectors stand in for current.", "optional_public_backup": "Original scope at most6 unchanged local public chains and6 corrupted CreateBackup controls only if validator prerequisites pass; preserve actual rejection layer; no forged archive changes.", "stop": "First unexpected accept/reject/missing provenance immediately stops corresponding lane with original raw/DB/source. No automatic third repair. Original five model-history failures and two held positives remain stopped.", "model_calls": 0, "worker_starts": 0, "http_calls": 0, "paid_calls": 0, "held_positive_tests": 0}, "acceptance": "Cause scope only. Repair outcome still requires nonself replay/current Main composition. Original red early-layer exit0 gets no P1 credit; no qualification/formal acceptance.", "formal_increment": 0}
save("scope_registration.json", scope)
scope_ref = ref((OUT / "scope_registration.json").relative_to(ROOT).as_posix())
for p, b in before.items():
    with (OUT / (p.stem + ".original.json")).open("xb") as f:
        f.write(b)
sub = ow["card_path_bindings"]["W05-99"]["subtasks"]["provider_transport_reasoning_binding"]
sub.update(state="FIRST_REPAIR_FALSE_REJECTION_PRESERVED_NARROW_TYPED_EPOCH_ADDITIONAL_ONCE_AUTHORIZED", current_source_writer=True, p12_causal_repair_scope_ref=scope_ref, p12_typed_epoch_cause_review_ref=review_ref)
chain = cp["failure_chains"]["W05-99/P9-P12-SR01"]
assert chain["actual_failed_invocations"] == 1
chain.update(actual_failed_invocations=2, repair_scope_ref=scope_ref, latest_author_failed_origin_ref=author_failure_ref, author_source_repair_attempts=2, status="TWO_ACTUAL_FAILURES_RETAINED_NARROW_TYPE_CAUSAL_CORRECTION_ONCE_AUTHORIZED", counter_reset=False)
assert cp["failure_chains"]["W05-99/provider9-original-history-refusal"]["actual_failed_invocations"] == 5
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
assert head == "1b3cda2ee974916f864b9a0af988076d01ca65bd"
cp.update(revision=283, expected_previous_revision=282, head=head, updated_at=now, updated_by="codex:/root")
ow.update(revision=111, amended_at=now, amended_by="codex:/root")
cp["work_in_progress"].update(provider_inventory_causal_repair_scope_ref=scope_ref, configuration_main_source_head=head, configuration_main_current_nonself_test="W05 reviewer active; source16/L02/stream combination not yet accepted")
cp["integrity_events"].append({"at": now, "actor": "codex:/root", "event": "PROVIDER_TYPED_EPOCH_CAUSAL_CORRECTION_REGISTERED_TWO_FAILURES_PRESERVED", "scope_ref": scope_ref, "failure_origins": [238, 240], "original_model_history5_held": True, "original_red_early_error_credit": False, "formal_increment": 0})
for v in [scope_ref, review_ref, author_failure_ref, review_failure_ref, proposal_ref]:
    if v["path"] not in cp["evidence_index"]:
        cp["evidence_index"].append(v["path"])
save("record.json", {"checkpoint": [282, 283], "ownership": [110, 111], "failure_origins": [238, 240], "same_issue_failed_invocations": 2, "scope_ref": scope_ref, "formal_increment": 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, v in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + ".root283.tmp")
    with tmp.open("xb") as f:
        f.write(enc(v))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({"checkpoint": 283, "ownership": 111, "failure_origins": 240, "scope_ref": scope_ref, "formal_increment": 0}))
