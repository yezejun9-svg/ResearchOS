"""Record independently accepted W01 qualification without accepting formal cases."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
V24 = ROOT / "execution/v2.4"
SPEC = ROOT / ".local/worktrees/v24-continuation/spec/v2.4"
def load(path):
    return json.loads(path.read_bytes())
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def ref(path, base=V24):
    return {"path": path.relative_to(base).as_posix(), "sha256": digest(path)}

review_path = HERE.parent / "independent_review_codex.json"
review = load(review_path)
assert digest(review_path) == "02ecf26d51702be1647c19fb85b85307f63d95e2c10f7a34404bbcc283b9c143"
head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
assert head == review["source_revision"] == "265137d9566c8f56d793ad75c6f16877176924a1"
assert review["verdict"] == "ACCEPT_W01_PARENT_QUALIFICATION"
assert review["independent_of_executor"] and not review["findings"]
assert set(review["card_checks"].values()) == {"PASS"}
assert len(review["development_checklist_mapping"]) == 8
assert all(row["decision"] == "PASS_IN_PARENT_QUALIFICATION_SCOPE" for row in review["development_checklist_mapping"])
assert review["owned_acceptance_ids"] == review["formal_cases_accepted"] == []
assert review["formal_case_count_delta"] == 0
for name, expected in review["evidence_artifacts"].items():
    assert digest(HERE.parent / "independent-review-codex" / name) == expected, name
verification = load(HERE.parent / "independent-review-codex/verification.json")
assert all(row["ok"] for row in verification["checks"])
assert len(review["gate_decisions"]) == 4
gate_refs = []
for gate in review["gate_decisions"]:
    assert gate["decision"] == "ACCEPT" and gate["child_exit_code"] == 0
    assert gate["assertion_ids"] == [gate["check_id"]]
    original = ROOT / "execution/invocations" / gate["invocation_id"] / "receipt.json"
    mirror = HERE.parent / "registered-dispatch" / gate["invocation_id"] / "receipt.json"
    assert original.read_bytes() == mirror.read_bytes()
    assert digest(mirror) == gate["dispatcher_receipt_sha256"]
    child = Path(gate["child_receipt"])
    assert digest(child) == gate["child_receipt_sha256"]
    gate_refs.extend([ref(mirror), ref(child)])

state_path, cp_path = V24 / "step_state.json", V24 / "checkpoint.json"
state, cp = load(state_path), load(cp_path)
assert cp["revision"] == 198
before_origins = json.loads(json.dumps(cp["failure_counters"]))
row = next(row for row in state["steps"] if row["id"] == "W01-99")
assert row["status"] == "IN_PROGRESS" and row["executor_id"] != review["reviewer"]
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
row.update(status="ACCEPTED", verifier_id=review["reviewer"], accepted_at=now,
           scope_note="W01 parent qualification gates only; final-owner list empty, no formal case acceptance. Actual qualification package and bounded source inheritance are disclosed in independent review.",
           execution_note="Four registered current gates and eight development requirements independently accepted; original failed attempts and route repair history preserved.")
row["evidence"].extend(gate_refs + [ref(review_path)])
write(state_path, state)
cp.update(head=head, current_step_id=None, next_step_id="W02-99", work_in_progress=None,
          parent_tasks_accepted=["W00(gates only, via W00-99 independent acceptance)", "W01(gates only, via W01-99 independent acceptance)"],
          updated_at=now, updated_by="codex:/root",
          note="36 accepted materialized cards, including two parents; parent2/22, formal0/42. W01 parent qualification independently accepted. W02 next, not yet started. All53 old failure origins preserved plus3 resolved qualification-harness failures and1 resolved reviewer-harness correction; no failure budget reset.")
cp["accepted_steps"].append("W01-99")
cp["blocked_steps"] = [sid for sid in cp["blocked_steps"] if sid != "W01-99"]
for worker in cp["workers"]:
    if worker["step_id"] == "W01-99":
        worker.update(state="ACCEPTED_PARENT_QUALIFICATION_NOT_FORMAL_CASES", independent_review=ref(review_path))
failures = [
    ("W01-parent-G02-source-and-output-parser", "20261005T200612Z-6b39ef79143a/receipt.json", "RESOLVED_CHANGED_CURRENT_SAMPLE_AND_SPLIT_OUTPUT_PARSER", "Original qualification harness BLOCKED on old sample source drift and split Go JSON Output parsing. Underlying seven Go tests passed; current29 dual-end sample and assembled per-test output subsequently passed."),
    ("W01-parent-G03-optional-smoke-and-sqlite-path-lock", "20261005T200831Z-f27d7e6ef06b/receipt.json", "RESOLVED_CHANGED_HARNESS_SECOND_SAMPLE", "Optional startup smoke timed out; subsequent15 normal GUI observations passed. Python SQLite path locking blocked aggregation. Original attempt preserved; changed second actual sample passed29 observations."),
    ("W01-parent-G03-post-observation-temporary-cleanup", "20261005T201056Z-411792f6015e/receipt.json", "RESOLVED_SEPARATE_POST_EXIT_CLEANUP_EVIDENCE", "Second installed package/startup/29dual-end observations passed. Temporary cleanup failed because SQLite connection remained open; separate post-exit absence and contained-directory cleanup evidence resolved it without third GUI replay."),
    ("W01-independent-registry-added-entry-harness", "independent-review-codex/supplement.stdout.txt", "RESOLVED_REVIEW_HARNESS_OLD30_PLUS_NEW31", "Reviewer initially treated core.qualify as modification instead of31st added entry. Corrected comparison independently passed14 supplemental checks; original failing script/log preserved, no product fix.")
]
for key, relative, status, detail in failures:
    assert not any(old["origin_key"] == key for old in cp["failure_counters"])
    path = HERE.parent / relative
    cp["failure_counters"].append(dict(origin_key=key, attempts=1, status=status, evidence=ref(path, ROOT), detail=detail))
assert cp["failure_counters"][:len(before_origins)] == before_origins
cp["integrity_events"].append(dict(at=now, actor="codex:/root", card="W01-99", event="INDEPENDENT_PARENT_QUALIFICATION_ACCEPTED", evidence=ref(review_path), detail="Record independent W01 qualification acceptance only; parent2/22, formal0/42. Prior route, raw failures, W11/W13/NVDA/W14 blockers unchanged."))
for path in [review_path, HERE / "exact_dispatch_results.json"]:
    relative = path.relative_to(ROOT).as_posix()
    if relative not in cp["evidence_index"]:
        cp["evidence_index"].append(relative)
write(cp_path, cp)
event_path = HERE / "value_round_codex.json"
write(event_path, dict(schema="researchos.value-round.v1", round_id="W01-parent-qualification-independent-20261005", delta="INFRASTRUCTURE", summary="Independently accepted current W01 parent qualification. Actual29 CLI/native Desktop qualification observations are bounded inherited evidence, not a newly shipped final installer or formal LIVE/provider/NVDA qualification.", evidence_refs=[ref(review_path, ROOT), ref(HERE.parent / "implementation_summary_codex.json", ROOT)]))
argv = [sys.executable,"-B","-X","utf8",str(ROOT / "bootstrap/v24_checkpoint.py"),"--checkpoint",str(cp_path),"--state",str(state_path),"--plan",str(SPEC / "contracts/execution.plan.json"),"--delivery",str(SPEC / "contracts/delivery.contract.json"),"--expected-revision","198","--round-event",str(event_path),"--actor","codex:/root"]
result = subprocess.run(argv, cwd=ROOT, capture_output=True)
(HERE / "checkpoint199.stdout.txt").write_bytes(result.stdout)
(HERE / "checkpoint199.stderr.txt").write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
next_argv = [sys.executable,"-B","-X","utf8",str(ROOT / "bootstrap/v24_checkpoint.py"),"--checkpoint",str(cp_path),"--state",str(state_path),"--plan",str(SPEC / "contracts/execution.plan.json"),"--delivery",str(SPEC / "contracts/delivery.contract.json"),"--next-packet"]
selected = subprocess.run(next_argv, cwd=ROOT, capture_output=True)
(HERE / "checkpoint199_next_packet.json").write_bytes(selected.stdout)
(HERE / "checkpoint199_next_packet.stderr.txt").write_bytes(selected.stderr)
assert selected.returncode == 0, selected.stderr.decode("utf-8", "replace")
packet = json.loads(selected.stdout)
assert packet["step"]["id"] == "W02-99" and packet["eligible"] is True
after = load(cp_path)
assert after["revision"] == 199 and after["failure_counters"][:len(before_origins)] == before_origins
assert after["value_checkpoint"]["source_hashes"]["step_state"] == digest(state_path)
assert after["value_checkpoint"]["formal_gate"]["accepted_parent_step_ids"] == ["W00-99", "W01-99"]
write(HERE / "acceptance_record_codex.json", dict(recorded_at=now, actor="codex:/root", status="INDEPENDENT_ACCEPTANCE_RECORDED", step_id="W01-99", review_sha256=digest(review_path), checkpoint_revision=199, materialized_accepted=36, parent_accepted=2, parent_required=22, formal_accepted=0, formal_required=42, failure_origins_preserved=len(before_origins), failure_origins_total=len(after["failure_counters"]), next_step=packet["step"]["id"], state_sha256=digest(state_path)))
print(json.dumps(dict(status="PASS", checkpoint=199, parent_accepted=2, formal_accepted=0, next_step=packet["step"]["id"], failure_origins=len(after["failure_counters"]))))
