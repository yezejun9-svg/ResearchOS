"""Retain the first complete main-profile rejection and its exact origins."""
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
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))


def main():
    cp, own, state = [ROOT / ("execution/v2.4/" + name) for name in ("checkpoint.json", "path_ownership.json", "step_state.json")]
    checkpoint, ownership, steps = [json.loads(p.read_bytes()) for p in (cp, own, state)]
    assert (checkpoint["revision"], ownership["revision"]) == (241, 71)
    previous = {p.name: sha(p) for p in (cp, own, state)}
    original_failures = json.loads(json.dumps(checkpoint["failure_counters"]))
    candidate = ROOT / "execution/v2.4/receipts/W07/W07-99/source_executor_codex/current-context-2881cfa84dd64156b59d12795e6375a2"
    preflight = json.loads((candidate / "preflight.json").read_bytes())
    assert preflight["status"] == "PRE_REGISTRATION_REJECTED"
    rejected = {row["code"] for row in preflight["stages"] if row["status"] == "FAIL"}
    assert rejected == {"SOURCE_COVERAGE", "DISPATCH_EXECUTION_LINK"}
    integration = ROOT / "execution/v2.4/receipts/W05/W05-99/queue_integration_codex/integration_report.json"
    assert sha(integration) == "49722e4fbd3ec80c5bab11f113280c29b2027316c44342dbff60c62ad55c64b4"
    now = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    out = HERE / "resume-r242"
    out.mkdir(exist_ok=True)
    assert not list(out.iterdir())
    event = {"schema": "researchos.root-observed-current-qualification.v1", "actor": "codex:/root",
        "recorded_at": now, "main_head": head, "W05_integration_ref": ref(integration),
        "W05_actual": {"cli_pass_events": 108, "queue_health_pass_events": 112, "actual_sdk_tests": 2,
                       "actual_current_control_startup": 1, "fail": 0, "skip": 0, "source_drift": 0,
                       "complete_slice": "PARTIAL_Q10_OPEN", "historical_failures_remaining": 4},
        "W07_native_result_ref": ref(HERE / "native-runs/20261006T094133Z-84f33c70d7/result.json"),
        "W07_source_proof_ref": ref(ROOT / "execution/v2.4/receipts/W07/W07-99/source_executor_codex/run-c495292dee2d4e4fba7bb11a06979907/proof.json"),
        "W07_complete_context_ref": ref(candidate / "context.json"), "W07_actual_preflight_ref": ref(candidate / "preflight.json"),
        "W07_complete_profile": "REJECTED_PENDING_COLLECTOR_INPUT_FIX",
        "gaps": [{"code": "SOURCE_COVERAGE", "missing_local_package_files": 27,
                  "raw_ref": ref(candidate / "capture-coverage-gaps.json")},
                 {"code": "DISPATCH_EXECUTION_LINK", "fixture_source_count": 1614, "live_source_count": 2256,
                  "different_files": 642, "difference_origin": "GOPATH module-cache defaults",
                  "raw_ref": ref(candidate / "dispatch-source-gap.json")}],
        "correction_scope": "Existing authorized ops/ci/sources.py and necessary parent_gate_test.py only; no formal reader or registry change",
        "old_raw_modified": False, "formal_current": 0, "parent_acceptance_delta": 0}
    save(out / "qualification.json", event)
    checkpoint["failure_counters"].append({"origin_key": "W07-99/full-main-current-profile-c495",
        "attempts": 1, "retries_used": 0, "status": "COLLECTOR_INPUT_FIX_PENDING_INDEPENDENT_REVIEW",
        "failed_stages": sorted(rejected), "actual_preflight_ref": ref(candidate / "preflight.json"),
        "rule": "Original source proof/native4/complete context remain unchanged. New capture requires corrected source/input vector; no retry counter reset or changed window to erase failure."})
    assert checkpoint["failure_counters"][:len(original_failures)] == original_failures
    checkpoint.update(revision=242, expected_previous_revision=241, head=head, updated_at=now, updated_by="codex:/root",
        next_command="Independently review collector full-local-package freeze and consistent project Go-cache defaults; integrate exact candidate, fresh capture and native4, then complete context/independent formal review. Preserve W05 Q10 historical failures.")
    for worker in checkpoint["workers"]:
        if worker.get("slice_id") == "W05-99-S6":
            worker["state"] = "MAIN_INTEGRATION_PASS_Q10_HISTORICAL_OPEN"
            worker["integration_ref"] = ref(integration)
        elif worker.get("step_id") == "W07-99" and not worker.get("slice_id"):
            worker["state"] = "FULL_MAIN_PROFILE_REJECTED_COLLECTOR_FIX_IN_ISOLATED_WORKTREE"
    ownership.update(revision=72, updated_at=now, updated_by="codex:/root")
    binding = ownership["card_path_bindings"]["W07-99"]
    binding["state"] = "FULL_MAIN_PROFILE_REJECTED_COLLECTOR_CAPTURE_FIX_PENDING"
    binding["qualification_ref"] = ref(out / "qualification.json")
    for row in steps["steps"]:
        if row["id"] == "W07-99":
            assert row["status"] == "IN_PROGRESS"
            row["previous_preparation_executor_id"] = row["executor_id"]
            row["executor_id"] = "codex:/root/sources_parent_impl"
            row["note"] = "Actual source executor assigned; main complete formal candidate rejected on two input-freeze gaps. Preserve preparation and original evidence. No parent/formal acceptance."
            row["evidence"].append({"path": ref(out / "qualification.json")["path"].removeprefix("execution/v2.4/"), "sha256": sha(out / "qualification.json")})
    checkpoint["note"] += " | R242: actualmain CLI108/queue-health112/SDK2/currentcontrol1 all scoped PASS0skip, Q10 four historical failures retained. NativeW07four PASS and tool56 did not imply formal acceptance; actualfullcontext rejects27 missing compiled-local-package files and642 GOPATH-vector difference. Old evidence unchanged, collector-only fix in existing scope;112 origins retained/added, CURRENT0/42 and parent5/22."
    save(out / "handoff.json", {"schema": "researchos.root-resume-handoff.v1", "created_at": now,
        "project_id": checkpoint["project_id"], "main_head": head, "checkpoint_revision": 242,
        "ownership_revision": 72, "qualification_ref": ref(out / "qualification.json"), "goal_status": "ACTIVE",
        "accepted_cards": 39, "accepted_parents": 5, "formal_current": 0, "required_parents": 22,
        "required_formal_cases": 42, "failure_origin_count": len(checkpoint["failure_counters"]),
        "next_action": checkpoint["next_command"], "counter_reset": False})
    checkpoint["evidence_index"].extend([ref(out / name)["path"] for name in ("qualification.json", "handoff.json")])
    save(out / "registration.json", {"schema": "researchos.root-resume-registration.v1", "at": now,
        "previous_sha256": previous, "checkpoint_revision": 242, "ownership_revision": 72,
        "old_failure_origins": len(original_failures), "failure_origins": len(checkpoint["failure_counters"]),
        "formal_current": 0, "parent_acceptance_delta": 0})
    assert all(sha(p) == previous[p.name] for p in (cp, own, state))
    save(cp, checkpoint)
    save(own, ownership, crlf=True)
    save(state, steps, crlf=True)
    print(json.dumps({"checkpoint": 242, "ownership": 72, "failure_origins": len(checkpoint["failure_counters"]), "formal_current": 0}))


if __name__ == "__main__":
    main()
