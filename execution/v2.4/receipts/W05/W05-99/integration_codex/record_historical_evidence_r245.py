"""Retain a scoped historical review without granting CURRENT acceptance."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def save(path, value, crlf=False):
    data = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_bytes((data.replace("\n", "\r\n") if crlf else data).encode("utf-8"))


def main():
    paths = [ROOT / ("execution/v2.4/" + n) for n in ("checkpoint.json", "path_ownership.json")]
    cp, own = [json.loads(p.read_bytes()) for p in paths]
    assert (cp["revision"], own["revision"]) == (244, 74)
    previous = {p.name: sha(p) for p in paths}
    failures = json.loads(json.dumps(cp["failure_counters"]))
    assert len(failures) == 115
    review = ROOT / "execution/v2.4/receipts/W05/W05-99/resume_review_codex/historical_lanes_review_3ebdeb25-dbbc-4400-9066-c6d20aa2632e/review.json"
    assert sha(review) == "68c33b9698e030cc0e629a37525d921977042225abf4d787c40440242b3ceeec"
    data = json.loads(review.read_bytes())
    assert data["verdict"] == "PASS_SCOPED_HISTORICAL_EVIDENCE"
    assert not data["qualifications"]["Q10_closed"]
    audit = ROOT / "execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/historical-final-audit.json"
    assert sha(audit) == "f80c17edc0a7160f8b0563dbe164c19925f6969824ca7adc22f8f2c94193c4b0"
    now = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    out = HERE / "resume-r245"
    out.mkdir(exist_ok=True)
    assert not list(out.iterdir())
    observed = {"schema": "researchos.root-observed-historical-evidence.v1", "actor": "codex:/root", "at": now,
        "main_head": head, "review_ref": ref(review), "executor_audit_ref": ref(audit),
        "received_message_actor": "codex:/root/w05_merge_review", "received_in_active_chat": True,
        "actual_message_digest": "PASS_SCOPED_HISTORICAL_EVIDENCE SHA68c33b9698e030cc0e629a37525d921977042225abf4d787c40440242b3ceeec; independently51receiptblobs,14one test7assertions,20two tests21assertions,0skip,3394/3573dependencies unchanged; newcontrol92b788bc actualproof stable_hash/candidate_hash equal; originalfour fail events retained.",
        "classification": "HISTORICAL_REGRESSION_EVIDENCE_ONLY", "Q10_closed": False, "current22_qualification": False,
        "formal_acceptance_delta": 0, "parent_acceptance_delta": 0, "old_failure_records_modified": False}
    save(out / "observed-historical-review.json", observed)
    report = ROOT / "execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/historical-lanes-report.json"
    cp["failure_counters"].append({"origin_key": "W05-99/historical20-report-wrong-baseline-field", "attempts": 1,
        "retries_used": 0, "status": "ORIGINAL_REPORT_ERROR_RETAINED_RAW_CORRECTION_INDEPENDENTLY_REVIEWED",
        "evidence_ref": ref(report), "review_ref": ref(review),
        "detail": "Old report compared absent baseline_hash and yielded false. Actual stable_hash/candidate_hash match fresh same-source compiled control. Original report untouched, no product retry or counter reset."})
    assert cp["failure_counters"][:115] == failures
    cp.update(revision=245, expected_previous_revision=244, head=head, updated_at=now, updated_by="codex:/root")
    cp["work_in_progress"].update(status="MAIN_SCOPED_CHECKS_PASS_HISTORICAL_EVIDENCE_REVIEWED_Q10_OPEN",
        historical_review_ref=ref(out / "observed-historical-review.json"))
    cp["note"] += " | R245: independent historical14/20 original7+21 assertions accepted only as scoped historical evidence. Fresh20 AppContainer proofs and full source/dependency provenance checked; originalfour current-main failures/Q10 remain. Old erroneous baseline-field report retained as116th origin; parent5/CURRENT0 unchanged."
    own.update(revision=75, updated_at=now, updated_by="codex:/root")
    own["card_path_bindings"]["W05-99"]["subtasks"]["historical_fixture_qualification"].update(
        state="SCOPED_HISTORICAL_EVIDENCE_INDEPENDENTLY_REVIEWED_INTEGRATED_Q10_OPEN", historical_review_ref=ref(review),
        historical_evidence_commit=head, current22_qualified=False)
    save(out / "handoff.json", {"schema": "researchos.root-resume-handoff.v1", "created_at": now,
        "project_id": cp["project_id"], "main_head": head, "checkpoint_revision": 245, "ownership_revision": 75,
        "historical_review_ref": ref(out / "observed-historical-review.json"), "goal_status": "ACTIVE", "accepted_cards": 39,
        "accepted_parents": 5, "formal_current": 0, "required_parents": 22, "required_formal_cases": 42,
        "failure_origin_count": len(cp["failure_counters"]), "next_action": cp["next_command"], "counter_reset": False})
    cp["evidence_index"].extend([ref(out / n)["path"] for n in ("observed-historical-review.json", "handoff.json")])
    save(out / "registration.json", {"schema": "researchos.root-resume-registration.v1", "at": now,
        "previous_sha256": previous, "checkpoint_revision": 245, "ownership_revision": 75,
        "old_failure_origins": 115, "failure_origins": 116, "parent_acceptance_delta": 0, "formal_acceptance_delta": 0})
    assert all(sha(p) == previous[p.name] for p in paths)
    save(paths[0], cp)
    save(paths[1], own, crlf=True)
    print(json.dumps({"checkpoint": 245, "ownership": 75, "failure_origins": 116, "formal_current": 0}))


if __name__ == "__main__":
    main()
