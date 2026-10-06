"""Record independently reviewed integration before a new MAIN capture."""
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
    paths = [ROOT / ("execution/v2.4/" + n) for n in ("checkpoint.json", "path_ownership.json", "step_state.json")]
    cp, own, state = [json.loads(p.read_bytes()) for p in paths]
    assert (cp["revision"], own["revision"]) == (243, 73)
    previous = {p.name: sha(p) for p in paths}
    failures = json.loads(json.dumps(cp["failure_counters"]))
    assert len(failures) == 112
    sources = {
        "internal/domain/backup_upgrade_test.go": "46fd30bba4b2ab2f3438bae151592090ba693a841fde21d71689f42dab7838a4",
        "ops/ci/sources.py": "24c4af577a52637f62703d186d2675a2fd9878384618c6469299cfc90b99281c",
        "tests/sources/check/parent_gate_test.py": "6b60756ec9d3654508e83cabc3913f0952b5dbb2df7c3ce058099cecf316f22b",
    }
    assert all(sha(ROOT / p) == v for p, v in sources.items())
    reviews = [
        ("execution/v2.4/receipts/W05/W05-99/resume_review_codex/historical_fixture_source_review_2ba70c50-03f2-4a3a-b0c4-0a21ed85e2c0/review.json", "98118f799cc543d93fa6996531b129e59ba9e98032b072391d5f734af288d12b"),
        ("execution/v2.4/receipts/W07/W07-99/scope_review_codex/compiled-package-capture-e7955b76-5602-4c16-93c7-e49a1174f57a/source_review.json", "5ced80bab1b9574bf25df854c4c9c65e1c9bd0b936a155a5129c9c2001285626"),
    ]
    for p, digest in reviews:
        assert sha(ROOT / p) == digest
        assert json.loads((ROOT / p).read_bytes())["verdict"] == "SOURCE_READY"
    now = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert head == "0fc177dcab114db9392facdce036dfd0cb8acffa"
    dirty = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
    assert set(dirty) == {p.relative_to(ROOT).as_posix() for p in paths}
    out = HERE / "resume-r244"
    out.mkdir(exist_ok=True)
    assert not list(out.iterdir())
    observed = {"schema": "researchos.root-observed-source-integration.v1", "actor": "codex:/root", "at": now,
        "main_source_head": head, "source_hashes": sources, "actual_independent_reviewer": "codex:/root/w05_merge_review",
        "reviews_received_in_active_chat": [ref(ROOT / p) for p, _ in reviews],
        "integrated_commits": {"collector": "bd5cc457", "historical_selector": head},
        "source_ready_scope_only": True, "W07_current_capture": "PENDING_FRESH_PROOF_AND_NATIVE4",
        "W05_historical_lanes": "EXECUTOR_COMPLETE_INDEPENDENT_REVIEW_PENDING", "Q10_closed": False,
        "old_four_main_failures_retained": True, "formal_current": 0, "accepted_parents": 5,
        "independent_message_evidence": "SOURCE_READY candidate3dffadd source46fd30bb review SHA98118f799cc543d93fa6996531b129e59ba9e98032b072391d5f734af288d12b; actual36blobs/3706inputs/5originalassertions PASS and missing/hash expected refusals. Collector80dad SOURCE_READY review SHA5ced80bab1b9574bf25df854c4c9c65e1c9bd0b936a155a5129c9c2001285626; independently observed2283 MAIN inputs in both modes and all27 historical omissions captured. Neither is CURRENT formal issuance."}
    save(out / "observed-integrations.json", observed)
    origins = [
        ("W05-99/historical-selector-report-parser", "execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/selector-report.json", "Old parser returned zero assertions; original report retained and original raw independently establishes5 assertions without product retry."),
        ("W05-99/historical-source-review-utf8-attempt1", "execution/v2.4/receipts/W05/W05-99/resume_review_codex/historical_fixture_source_review_2ba70c50-03f2-4a3a-b0c4-0a21ed85e2c0/attempt1.result.json", "Actual independent verification subprocess failed on UTF8 path parsing; original script/stdout/stderr retained; subsequent parser correction did not rerun product."),
        ("W07-99/collector-candidate-isolated-27-assumption", "execution/v2.4/receipts/W07/W07-99/source_executor_codex/complete-package-freeze-47ff332401e24eb8bb43964dcf79a113/qualification-initial-failure.json", "Initial candidate worktree check wrongly expected MAIN-only bridge test among all27 paths; retained actual failure, later readonly actual MAIN audit verifies27 and isolated worktree26. No proof alteration."),
    ]
    for key, path, detail in origins:
        assert not any(x.get("origin_key") == key for x in failures)
        cp["failure_counters"].append({"origin_key": key, "attempts": 1, "retries_used": 0,
            "status": "ORIGINAL_VERIFICATION_FAILURE_RETAINED_CORRECTION_REVIEWED", "evidence_ref": ref(ROOT / path), "detail": detail, "counter_reset": False})
    assert cp["failure_counters"][:112] == failures
    cp.update(revision=244, expected_previous_revision=243, head=head, dirty_paths=dirty, updated_at=now, updated_by="codex:/root",
        next_command="Fresh current MAIN three-source/H07 capture on frozen integrated input vector; actual native G01/G02/H07/A05; full current context and independent GLOBAL review. Historical Q10 and W04 current revalidation remain separate obligations.")
    cp["work_in_progress"].update(status="MAIN_INTEGRATION_PASS_HISTORICAL_LANES_INDEPENDENT_REVIEW_PENDING", main_source_head=head,
        integration_ref=ref(out / "observed-integrations.json"), next_action=cp["next_command"])
    for worker in cp["workers"]:
        if worker.get("step_id") == "W07-99" and not worker.get("slice_id"):
            worker.update(state="CORRECTED_SOURCE_INTEGRATED_READY_FRESH_MAIN_CAPTURE", main_source_head=head, current_collection_root=ROOT.as_posix())
        if worker.get("slice_id") == "FIXED21TO22_UPGRADE":
            worker["state"] = "INTEGRATED_MAIN_SCOPED_CHECKS_PASS_HISTORICAL_Q10_OPEN"
    own.update(revision=74, updated_at=now, updated_by="codex:/root")
    own["card_path_bindings"]["W07-99"].update(state="CORRECTED_SOURCE_INTEGRATED_READY_FRESH_MAIN_CAPTURE", main_source_head=head,
        current_integration_ref=ref(out / "observed-integrations.json"), actual_full_context_verifier="codex:/root/w05_merge_review")
    hist = own["card_path_bindings"]["W05-99"]["subtasks"]["historical_fixture_qualification"]
    hist.update(state="SOURCE_INDEPENDENTLY_REVIEWED_INTEGRATED_HISTORICAL_LANES_REVIEW_PENDING", integrated_commit=head,
        source_review_ref=ref(ROOT / reviews[0][0]))
    cp["note"] += " | R244: reviewed collector and exact W17 historical selector integrated; product source clean. Fresh MAIN capture pending, old c495/native/context remain historical. Three actual evidence-verification failure origins appended; all112 prior origins unchanged. 39cards/5parents/CURRENT0; Q10 historical lanes separate pending independent review."
    save(out / "handoff.json", {"schema": "researchos.root-resume-handoff.v1", "created_at": now, "project_id": cp["project_id"],
        "main_source_head": head, "checkpoint_revision": 244, "ownership_revision": 74, "goal_status": "ACTIVE",
        "observed_integrations_ref": ref(out / "observed-integrations.json"), "accepted_cards": 39, "accepted_parents": 5,
        "formal_current": 0, "required_parents": 22, "required_formal_cases": 42, "failure_origin_count": len(cp["failure_counters"]),
        "next_action": cp["next_command"], "counter_reset": False})
    cp["evidence_index"].extend([ref(out / n)["path"] for n in ("observed-integrations.json", "handoff.json")])
    save(out / "registration.json", {"schema": "researchos.root-resume-registration.v1", "at": now, "previous_sha256": previous,
        "checkpoint_revision": 244, "ownership_revision": 74, "old_failure_origins": 112, "failure_origins": len(cp["failure_counters"]),
        "parent_acceptance_delta": 0, "formal_acceptance_delta": 0})
    assert all(sha(p) == previous[p.name] for p in paths)
    save(paths[0], cp)
    save(paths[1], own, crlf=True)
    save(paths[2], state, crlf=True)
    print(json.dumps({"checkpoint": 244, "ownership": 74, "failure_origins": len(cp["failure_counters"]), "formal_current": 0}))


if __name__ == "__main__":
    main()
