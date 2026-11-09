"""Root-only append of observed execution evidence; never accepts a parent."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[6]
CP = ROOT / "execution/v2.4/checkpoint.json"
OWN = ROOT / "execution/v2.4/path_ownership.json"
OUT = Path(__file__).resolve().parent / "resume-r240"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path)}


def write(path, value, crlf=False):
    content = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if crlf:
        content = content.replace("\n", "\r\n")
    path.write_bytes(content.encode("utf-8"))


def main():
    checkpoint = json.loads(CP.read_bytes())
    ownership = json.loads(OWN.read_bytes())
    assert checkpoint["revision"] == 239 and ownership["revision"] == 69
    assert checkpoint["project_id"] == "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
    old_checkpoint, old_ownership = digest(CP), digest(OWN)
    old_origins = json.loads(json.dumps(checkpoint["failure_counters"]))
    OUT.mkdir(exist_ok=True)
    assert not list(OUT.glob("*")), "partially recorded evidence requires explicit recovery"
    now = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    reviews = []
    for name, expected, candidate, proof in (
        ("ingress_fix_source_evidence_review.json", "dcf6fdae01d7ad86f9a6d2d586ecca249e2b38cf6b7b4199dcf8d1d1fa1254bb", "49143af141255f65465154d14e255852ff66b897", "be55cec5bb18e285ad5d933e784fac8d04b8035fe5c0f0bc81c8d8769a2a454c"),
        ("h07_relocation_source_review.json", "84e3e83cc463d1f6af483a152111752f2d291f9256d5c8c81ee0dcab800d19eb", "2da28a73e2ef8b8fea62eac5c68a4397c9d7a3f9", "be55cec5bb18e285ad5d933e784fac8d04b8035fe5c0f0bc81c8d8769a2a454c"),
    ):
        path = ROOT / "execution/v2.4/receipts/W07/W07-99/scope_review_codex" / name
        assert digest(path) == expected
        review = json.loads(path.read_bytes())
        assert review.get("decision", review.get("verdict")) == "SOURCE_READY"
        reviews.append({"review_ref": ref(path), "candidate_commit": candidate, "proof_sha256": proof,
                        "sender": "codex:/root/w05_merge_review", "event_type": "MESSAGE",
                        "root_observed_at": now, "formal_acceptance_delta": 0})
    observed = {"schema": "researchos.root-observed-source-reviews.v1", "actor": "codex:/root",
                "recorded_at": now, "received_in_active_chat": True, "reviews": reviews,
                "scope": "SOURCE_READY_ONLY_NOT_FORMAL_ACCEPTANCE",
                "main_integrated": {"source": "14edd36f", "ingress_guard": "3075ad6c"},
                "relocation": "independently reviewed, pending main merge and new current freeze"}
    write(OUT / "observed-source-reviews.json", observed)
    formal_root = ROOT / ".local/worktrees/codex-w0799-formal"
    formal_receipts = formal_root / "execution/v2.4/receipts/W07/W07-99/formal_executor_codex"
    failed_runs, all_runs = [], []
    for result_path in sorted(formal_receipts.glob("tooling-*/result.json")):
        result = json.loads(result_path.read_bytes())
        row = {"candidate_receipt_path": str(result_path), "sha256": digest(result_path),
               "actual_exit_code": result.get("exit_code"), "actual_test_count": result.get("test_count"),
               "source_before": result.get("source_before"), "source_after": result.get("source_after"),
               "formal_acceptance_delta": 0}
        all_runs.append(row)
        if result.get("exit_code") not in (None, 0):
            failed_runs.append(row)
    write(OUT / "formal-tooling-history.json", {"schema": "researchos.root-recorded-development-failures.v1",
          "scope": "LOCAL_TOOLING_NOT_PRODUCT_LIVE_ACCEPTANCE", "failed_command_count": len(failed_runs),
          "runs": all_runs, "failed_runs": failed_runs, "candidate_receipts_retained": True,
          "last_actual_pass": "tooling-20261006T091358Z-a5344ac2", "last_actual_test_count": 54,
          "independent_f03": "OPEN_PENDING_REVIEW_OF_NEW_CLOSURE", "formal_acceptance_delta": 0})
    legacy = ROOT / ".local/bin/researchos-remote.exe"
    assert digest(legacy) == "aeda2d5eff0028529eaa53e9f5cc91fbcd668842577315eb744bd5f066834032"
    write(OUT / "legacy14-resource-mapping.json", {"schema": "researchos.root-observed-resource-mapping.v1",
          "actor": "codex:/root", "received_from": "codex:/root/legacy14_resource_lookup", "recorded_at": now,
          "candidate_binary": str(legacy), "binary_sha256": digest(legacy), "source_commit": "09a6a5ecfba40c1596a3ec46be25c34ba1f2fce0",
          "go_build_entry": "researchos.local/research-os/apps/control", "vcs_modified": True,
          "source_root": str(ROOT / ".local/releases/schema14-09a6a5e"), "schema_versions": list(range(1, 15)),
          "build_receipt_ref": ref(ROOT / "execution/receipts/W17/local-upgrade/integration-10cbc005-9ccd-4c20-8517-fac98e08d454/report.json"),
          "actual_upgrade_receipt_ref": ref(ROOT / "execution/receipts/W17/local-upgrade/actual-20260930T142007Z/upgrade.stdout.json"),
          "activation": "operator target_started=false; activation_policy_blocked", "runtime_tested_this_search": False,
          "web_gap": "Historical source root has no apps/web/dist/index.html; needs compatible prior web build for ordinary serve",
          "schema14_own_cli": "NOT_FOUND; first apps/cli commit ad4cf1180dc36a3e5b35d03183cdc78bad6cb5b8",
          "qualification": "READ_ONLY_RESOURCE_MAPPING_NOT_CURRENT_PRODUCT_ACCEPTANCE"})
    checkpoint["failure_counters"].extend([
        {"origin_key": "W07-99/formal-tooling-development", "attempts": len(failed_runs), "retries_used": 0,
         "status": "REPAIRED_CURRENT_54_PASS_PENDING_INDEPENDENT_REVIEW", "history_ref": ref(OUT / "formal-tooling-history.json"),
         "rule": "Each corrective invocation changed its actual input/source vector; failed originals retained; no same-input retry or reset"},
        {"origin_key": "W07-99/formal-profile-independent-F01-F05", "attempts": 3, "retries_used": 0,
         "status": "F01_F02_F04_F05_CLOSED_F03_PENDING_NEW_CLOSURE_REVIEW",
         "review_refs": [ref(ROOT / "execution/v2.4/receipts/W07/W07-99/formal_review_codex" / name) for name in ("initial_review.json", "revision2_review.json", "revision3_review.json")],
         "rule": "Initial five P1 defects and second whole-package omission negative remain preserved"},
        {"origin_key": "W07-99/native-main-proof-relocation", "attempts": 1, "retries_used": 0,
         "status": "REPAIRED_IN_REVIEWED_CANDIDATE_AWAITING_MAIN_CURRENT_FREEZE",
         "original_receipt_ref": ref(ROOT / "execution/invocations/e92cd69e-af32-4a77-9f00-d9b3af56e1da/receipt.json"),
         "independent_review_ref": reviews[1]["review_ref"]},
        {"origin_key": "W07-99/source-executor-development-history", "attempts": 4, "retries_used": 0,
         "status": "HISTORICAL_FAILURES_RETAINED_SOURCE_CANDIDATE_REVIEWED",
         "history_ref": ref(ROOT / "execution/v2.4/receipts/W07/W07-99/source_executor_codex/development-failure-history.json")},
        {"origin_key": "ROOT/checkpoint-registration-r240/preflight", "attempts": 1, "retries_used": 0,
         "status": "REPAIRED_REVIEW_SCHEMA_KEY_SELECTION", "actual_exit_code": 1,
         "observed_tool_error": "KeyError: 'decision'; second narrow review uses verdict",
         "retention_limit": "Actual tool output observed in this chat; no separate raw file captured. Canonical checkpoint remained239 and ownership69."},
    ])
    assert checkpoint["failure_counters"][:len(old_origins)] == old_origins
    checkpoint.update(revision=240, expected_previous_revision=239, head=head, updated_at=now, updated_by="codex:/root")
    checkpoint["work_in_progress"] = {"step_id": "W05-99", "owner": "codex:/root/command_queue_impl",
       "status": "S6_FINAL_CURRENT_MATRIX_AND_INDEPENDENT_REVIEW_PENDING", "worktree": ".local/worktrees/codex-w0599-command-queue",
       "next_action": "Review and integrate current queue/control/upgrade; preserve four historical14/20 gates; then one W07 source-current freeze/native dispatcher/profile qualification"}
    for worker in checkpoint["workers"]:
        if worker.get("slice_id") == "FIXED21TO22_UPGRADE":
            worker["state"] = "SOURCE_REVIEWED_INTEGRATED_IN_S6_CANDIDATE_PENDING_MAIN"
        elif worker.get("slice_id") == "W05-99-S6":
            worker["state"] = "FINAL_CURRENT_REGRESSION_PENDING_SOURCE_REVIEW"
        elif worker.get("step_id") == "W07-99" and not worker.get("slice_id"):
            worker["state"] = "SOURCE_AND_INGRESS_INTEGRATED_RELOCATION_SOURCE_REVIEWED"
            worker["observed_review_ref"] = ref(OUT / "observed-source-reviews.json")
    ownership.update(revision=70, updated_at=now, updated_by="codex:/root")
    w07 = ownership["card_path_bindings"]["W07-99"]
    w07["state"] = "SOURCE_AND_INGRESS_INTEGRATED_RELOCATION_REVIEWED_CURRENT_FREEZE_PENDING"
    w07["observed_review_ref"] = ref(OUT / "observed-source-reviews.json")
    checkpoint["note"] += " | R240: W07 source/ingress independent SOURCE_READY integrated; relocation independently reviewed. Formal tooling54 actual pass/F03 review pending; original failures appended, formal0/42 and parent5/22 unchanged."
    write(OUT / "registration.json", {"schema": "researchos.root-resume-registration.v1", "recorded_at": now,
          "expected_checkpoint_revision": 239, "checkpoint_revision": 240, "previous_checkpoint_sha256": old_checkpoint,
          "expected_ownership_revision": 69, "ownership_revision": 70, "previous_ownership_sha256": old_ownership,
          "main_head": head, "old_failure_origin_count": len(old_origins), "failure_origin_count": len(checkpoint["failure_counters"]),
          "formal_current": "0/42", "parents_accepted": "5/22", "source_reviews_ref": ref(OUT / "observed-source-reviews.json")})
    assert digest(CP) == old_checkpoint and digest(OWN) == old_ownership
    write(CP, checkpoint)
    write(OWN, ownership, crlf=True)
    print(json.dumps({"checkpoint": 240, "ownership": 70, "failure_origins": len(checkpoint["failure_counters"]), "parents": 5, "formal_current": 0}))


if __name__ == "__main__":
    main()
