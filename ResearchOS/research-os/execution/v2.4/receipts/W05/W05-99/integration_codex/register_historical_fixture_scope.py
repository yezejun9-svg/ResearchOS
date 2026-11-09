"""Root grants the independently reviewed narrow historical fixture scope."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

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
    cp, own = [ROOT / ("execution/v2.4/" + name) for name in ("checkpoint.json", "path_ownership.json")]
    checkpoint, ownership = [json.loads(p.read_bytes()) for p in (cp, own)]
    assert (checkpoint["revision"], ownership["revision"]) == (242, 72)
    original = {p.name: sha(p) for p in (cp, own)}
    review = ROOT / "execution/v2.4/receipts/W05/W05-99/resume_review_codex/historical_fixture_scope_63c2e06e-276a-44d0-8baf-4c9f2bd45ef8/review.json"
    assert sha(review) == "6b4afb070798551659be7e500cbeb084a4e057d94da937773fc7c50cfaa92bee"
    verified = json.loads(review.read_bytes())
    assert verified["decision"] == "RECOMMEND_NARROW_SCOPE_WITH_PREEXECUTION_PROVENANCE_CONDITIONS"
    boundary = verified["approved_source_boundary"]
    assert sha(ROOT / boundary["path"]) == boundary["source_sha256"]
    registration = HERE / "historical_fixture_root_registration.json"
    assert not registration.exists()
    now = datetime.now(timezone.utc).isoformat()
    scope = {"schema": "researchos.root-historical-fixture-scope-registration.v1", "actor": "codex:/root", "created_at": now,
        "owner": "codex:/root/command_queue_impl", "step_id": "W05-99", "active_parent": "W05",
        "worktree": ".local/worktrees/codex-w0599-command-queue", "review_ref": ref(review),
        "root_received_in_active_chat": True, "source_boundary": boundary,
        "receipt_namespace": "execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/**",
        "historical14_snapshot_conditions": verified["historical14_active_recovery"],
        "historical20_snapshot_conditions": verified["historical20_native"],
        "required_followup": verified["required_followup"], "source_changes_outside_original_span_allowed": False,
        "qualification": "HISTORICAL_REGRESSION_AND_NARROW_CURRENT_UPGRADE_CLI_WITH_LOCKED14_TARGET",
        "parent_acceptance_delta": 0, "formal_acceptance_delta": 0, "Q10_closed": False,
        "four_original_main_failures_retained": True, "counter_reset": False}
    save(registration, scope)
    ownership.update(revision=73, updated_at=now, updated_by="codex:/root")
    ownership["card_path_bindings"]["W05-99"].setdefault("subtasks", {})["historical_fixture_qualification"] = {
        "owner": scope["owner"], "worktree": scope["worktree"], "state": "ACTIVE_IN_REVIEWED_EXACT_TEST_SPAN",
        "source_path": boundary["path"], "original_lines": boundary["replace_original_lines"],
        "protected_exterior": boundary["protected_exterior"], "scope_ref": ref(registration),
        "receipt_namespace": scope["receipt_namespace"], "formal_authority": False}
    checkpoint.update(revision=243, expected_previous_revision=242, updated_at=now, updated_by="codex:/root")
    checkpoint["evidence_index"].append(ref(registration)["path"])
    checkpoint["note"] += " | R243: independently approved W17 exact original975–981 historical14 selector scope registered; all exterior bytes/assertions protected. Historical14 active recovery/exact20 original tests use new source-only snapshots. No failure/cost reset, Q10 or CURRENT acceptance; other current22 guards untouched."
    assert all(sha(p) == original[p.name] for p in (cp, own))
    save(cp, checkpoint)
    save(own, ownership, crlf=True)
    print(json.dumps({"checkpoint": 243, "ownership": 73, "scope": ref(registration), "formal_current": 0}))


if __name__ == "__main__":
    main()
