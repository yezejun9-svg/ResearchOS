"""Append Root's observed integrations without accepting a parent or case."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[6]
CP = ROOT / "execution/v2.4/checkpoint.json"
OWN = ROOT / "execution/v2.4/path_ownership.json"
OUT = Path(__file__).resolve().parent / "resume-r241"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path)}


def write(path, value, crlf=False):
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    path.write_bytes((data.replace("\n", "\r\n") if crlf else data).encode("utf-8"))


def main():
    checkpoint, ownership = (json.loads(p.read_bytes()) for p in (CP, OWN))
    assert (checkpoint["revision"], ownership["revision"]) == (240, 70)
    assert checkpoint["project_id"] == "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
    previous = {"checkpoint": digest(CP), "ownership": digest(OWN)}
    old_failures = json.loads(json.dumps(checkpoint["failure_counters"]))
    OUT.mkdir(exist_ok=True)
    assert not list(OUT.iterdir()), "Existing registration must be recovered explicitly"
    now = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    source = ROOT / "execution/v2.4/receipts/W05/W05-99/queue_executor_codex/source_after.json"
    rows = json.loads(source.read_bytes())["files"]
    assert len(rows) == 33
    assert all(digest(ROOT / row["path"]) == row["sha256"] for row in rows)
    reviews = []
    for path, expected, verdict in (
        ("execution/v2.4/receipts/W05/W05-99/resume_review_codex/s6_final_source_review.json",
         "6f2465763028e5a76f07052c9596d6720f501e6b15c65371467308e9e8650c6f",
         "SOURCE_READY_FOR_CONDITIONAL_INTEGRATION"),
        ("execution/v2.4/receipts/W07/W07-99/formal_review_codex/revision5_source_ready_review.json",
         "c84599edba4f859e678f1f8f342b6c51335c3b9ed65bb4b839e7d94faa4c3152", "SOURCE_READY_RECOMMEND_LOCAL_CANDIDATE_INTEGRATION_ONLY"),
        ("execution/v2.4/receipts/W07/W07-99/scope_review_codex/h07_relocation_source_review.json",
         "84e3e83cc463d1f6af483a152111752f2d291f9256d5c8c81ee0dcab800d19eb", "SOURCE_READY"),
    ):
        target = ROOT / path
        assert digest(target) == expected
        document = json.loads(target.read_bytes())
        assert document.get("verdict", document.get("decision")) == verdict
        reviews.append({"review_ref": ref(target), "verdict": verdict,
                        "root_received_in_active_chat": True, "root_observed_at": now})
    observed = {"schema": "researchos.root-observed-integrated-source-reviews.v1",
                "actor": "codex:/root", "recorded_at": now, "reviews": reviews,
                "main_head": head, "queue_source_vector_ref": ref(source), "queue_sources_equal": 33,
                "integrated_commits": {"W07_relocation": "9caedee40d6c90a3515cb547e711253b62fe3559",
                                      "W07_formal": ["151bd7b8ceba706f9006a799d337762afaf39d63", "d7d933761f5395b45ddadf62ba06742e57b227d9"],
                                      "W05_queue": ["4b8c34b62315007850f1e6723d5f51df5219bf4c", "a7d5a60e5814c005a8a25167883c57a93bfdffb6",
                                                    "288e4f19c851b5b6d487afbf2cee4cb6fbb79d8c", "7f6fb44a55b2f8a62980b0353cddc0c210239473", "bb9704327738699136a4e85960f66597b87e0e51"]},
                "scope": "SOURCE_INTEGRATION_ONLY", "queue_complete_slice": "PARTIAL_Q10_OPEN",
                "historical_regression_failures_remaining": 4, "formal_current": 0, "parents_accepted": 5,
                "formal_source_tests": 56, "fresh_native_and_live_current_qualification": "PENDING"}
    write(OUT / "observed-integrations.json", observed)
    round4 = ROOT / "execution/v2.4/receipts/W07/W07-99/formal_review_codex/revision4_review.json"
    checkpoint["failure_counters"].append({
        "origin_key": "W07-99/formal-profile-independent-r4-embedded-input",
        "attempts": 1, "retries_used": 0, "status": "REPAIRED_SOURCE_READY_R5_NATIVE_CURRENT_PENDING",
        "original_review_ref": ref(round4), "closure_review_ref": reviews[1]["review_ref"],
        "rule": "Original embedded-input omission reproduction is retained; no prior counter or original receipt reset"})
    checkpoint["failure_counters"].append({
        "origin_key": "ROOT/checkpoint-registration-r241/preflight", "attempts": 2,
        "retries_used": 0, "status": "REPAIRED_SYNTAX_AND_EXACT_SOURCE_REVIEW_DECISION", "actual_exit_codes": [1, 1],
        "observed_errors": ["SyntaxError: closing parenthesis ')' does not match opening parenthesis '['",
                            "AssertionError: exact R5 decision is SOURCE_READY_RECOMMEND_LOCAL_CANDIDATE_INTEGRATION_ONLY"],
        "retention_limit": "Both actual stderr outputs observed in active chat; no separate raw captured. Canonical checkpoint240/ownership70 preserved; second invocation created only empty resume-r241 directory. Inputs changed after each corrective edit."})
    assert checkpoint["failure_counters"][:len(old_failures)] == old_failures
    checkpoint.update(revision=241, expected_previous_revision=240, head=head, updated_at=now,
                      updated_by="codex:/root", next_command="Validate integrated W05 CLI/queue/SDK; finish one main-current W07 collection, native G01/G02/H07/A05, complete GLOBAL evidence and independent parent/formal qualification.")
    checkpoint["dirty_paths"] = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
    checkpoint["work_in_progress"] = {"step_id": "W05-99", "owner": "codex:/root/command_queue_impl",
        "status": "S6_INDEPENDENTLY_REVIEWED_INTEGRATED_MAIN_REGRESSION_RUNNING",
        "review_ref": reviews[0]["review_ref"], "main_source_head": head,
        "complete_slice": "PARTIAL_Q10_OPEN", "historical_failures": 4,
        "next_action": checkpoint["next_command"]}
    for worker in checkpoint["workers"]:
        if worker.get("slice_id") in {"W05-99-S6", "FIXED21TO22_UPGRADE"}:
            worker["state"] = "INDEPENDENTLY_REVIEWED_INTEGRATED_MAIN_CHECKS_PENDING"
            worker["main_source_head"] = head
        elif worker.get("slice_id") == "STRICT_FORMAL_PROFILE":
            worker["state"] = "SOURCE_READY_INTEGRATED_FULL_NATIVE_CURRENT_CONTEXT_PENDING"
            worker["independent_review"] = reviews[1]["review_ref"]
        elif worker.get("step_id") == "W07-99" and not worker.get("slice_id"):
            worker["state"] = "SOURCE_READY_INTEGRATED_MAIN_CURRENT_COLLECTION_RUNNING"
            worker["current_collection_root"] = str(ROOT)
            worker["main_source_head"] = head
    pending = checkpoint.setdefault("temporary_cleanup_pending", [])
    for path, owner, review_ref in (
        (".local/s6-independent-review-20261006", "codex:/root/w05_merge_review", reviews[0]["review_ref"]),
        ("C:/Users/yqyyds/AppData/Local/Temp/researchos-queue-sdk-kak0GL", "codex:/root/command_queue_impl", reviews[0]["review_ref"]),
    ):
        if not any(row["path"] == path for row in pending):
            pending.append({"path": path, "owner": owner, "reason": "Automatic approval review rejected native exact-path cleanup: blocked by policy; retained, no alternate deletion attempted", "review_ref": review_ref, "at": now})
    ownership.update(revision=71, updated_at=now, updated_by="codex:/root")
    w05, w07 = (ownership["card_path_bindings"][key] for key in ("W05-99", "W07-99"))
    w05["state"] = "S6_SOURCE_READY_INTEGRATED_MAIN_CHECKS_PENDING_Q10_OPEN"
    w05["main_integration_ref"] = ref(OUT / "observed-integrations.json")
    w07["state"] = "SOURCE_READY_INTEGRATED_MAIN_CURRENT_COLLECTION_AND_NATIVE_CONTEXT_PENDING"
    w07["main_integration_ref"] = ref(OUT / "observed-integrations.json")
    w07["current_collection_execution"] = {"owner": "codex:/root/sources_parent_impl", "root": str(ROOT),
        "source_write_authority": False, "receipt_namespace": "execution/v2.4/receipts/W07/W07-99/source_executor_codex/run-UUID/**",
        "rationale": "Read-only collection against integrated source; old worktree compilation vector is historical"}
    w07["subtasks"]["strict_formal_profile"]["state"] = "SOURCE_READY_INTEGRATED_NATIVE_CURRENT_PENDING"
    checkpoint["note"] += " | R241: S6 exact33-source reviewed candidate integrated; main组合 checks pending; four historical Q10 failures retained. W07 relocation and 56-pass/R5 formal tooling integrated; one fresh main source collection/native4/actual GLOBAL independent acceptance pending. All109 prior origins retained; parent5/22 and CURRENT0/42 unchanged."
    handoff = {"schema": "researchos.root-resume-handoff.v1", "created_at": now,
        "project_id": checkpoint["project_id"], "package_version": "2.4.0", "head": head,
        "checkpoint_revision": 241, "ownership_revision": 71, "commands_revision": 39,
        "source_integration_ref": ref(OUT / "observed-integrations.json"),
        "accepted_cards": 39, "accepted_parents": 5, "current_formal_cases": 0,
        "required_parents": 22, "required_formal_cases": 42, "goal_status": "ACTIVE",
        "failure_origin_count": len(checkpoint["failure_counters"]), "failure_count_reset": False,
        "active_parents": ["W05", "W07"], "next_actions": [checkpoint["next_command"],
            "Revalidate W04 owned current formal cases after integrated domain stabilizes",
            "Use discovered historical schema14 control only with independently scoped test fixture selection; do not mutate historical schemas or weaken guards"],
        "blocked_resource_cards": checkpoint["blocked_steps"], "cleanup_pending": pending,
        "temporary_or_fixture_evidence_is_formal": False}
    write(OUT / "handoff.json", handoff)
    checkpoint["evidence_index"].extend([ref(OUT / "observed-integrations.json")["path"], ref(OUT / "handoff.json")["path"]])
    write(OUT / "registration.json", {"schema": "researchos.root-resume-registration.v1", "recorded_at": now,
        "previous_sha256": previous, "checkpoint_revision": 241, "ownership_revision": 71, "main_head": head,
        "old_failure_origin_count": len(old_failures), "new_failure_origin_count": len(checkpoint["failure_counters"]),
        "parents_accepted": 5, "formal_current": 0, "handoff_ref": ref(OUT / "handoff.json")})
    assert digest(CP) == previous["checkpoint"] and digest(OWN) == previous["ownership"]
    write(CP, checkpoint)
    write(OWN, ownership, crlf=True)
    print(json.dumps({"checkpoint": 241, "ownership": 71, "failure_origins": len(checkpoint["failure_counters"]), "head": head}))


if __name__ == "__main__":
    main()
