from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[7]
HERE = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ref(path):
    target = ROOT / path
    return {"path": path, "sha256": digest(target.read_bytes())}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def immutable(path, raw):
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def main():
    paths = ["execution/v2.4/checkpoint.json", "execution/v2.4/path_ownership.json", "execution/v2.4/step_state.json"]
    originals = {path: (ROOT / path).read_bytes() for path in paths}
    cp = json.loads(originals[paths[0]])
    ownership = json.loads(originals[paths[1]])
    if cp["revision"] != 249 or ownership["revision"] != 78:
        raise RuntimeError("unexpected canonical revision")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    review_path = "execution/v2.4/receipts/W04/W04-99/independent_revalidation_codex/45df75e6-cb54-4c3f-9fba-b437b7442a7c/source_review.json"
    review = json.loads((ROOT / review_path).read_bytes())
    if ref(review_path)["sha256"] != "d12df9c0b22b7f5dd78a0d1788b8247925c85cb70740f38cf32521eef1b53dcd" or review["decision"] != "SOURCE_READY":
        raise RuntimeError("source review mismatch")
    amendment = "execution/v2.4/receipts/W04/W04-99/revalidation_scope_review_codex/e4e2caf5-70e2-4568-86e0-1611eb0dee5a/acyclic_transition_scope_amendment.json"
    if ref(amendment)["sha256"] != "ba95eb6c1608ea201ac40aed1988d023b556d1ae4238aeba396d512508890d65":
        raise RuntimeError("scope amendment mismatch")
    integration_path = "execution/v2.4/receipts/W04/W04-99/integration_codex/collector-source-integration-407c9fc61d4b43c9b8e87bc28e1dd8e7/result.json"
    integration = json.loads((ROOT / integration_path).read_bytes())
    if integration["actual_exit"] != 0 or integration["verified_candidate_files"] != 224 or integration["preserved_old_tracked_files"] != 1436:
        raise RuntimeError("integration mismatch")
    failures = list(cp["failure_counters"])
    new_failures = []
    for index, item in enumerate(review["preserved_review_failures"], 1):
        new_failures.append({"origin_key": f"W04-99/collector-independent-tooling-{index}", "attempts": 1, "retries_used": 0, "status": "ORIGINAL_REVIEW_TOOL_FAILURE_PRESERVED_CORRECTED_WITH_ACTUAL_RAW", "evidence_ref": item["raw_ref"], "review_ref": ref(review_path), "detail": item["origin"], "counter_reset": False, "product_acceptance_increment": 0})
    archive = "execution/v2.4/receipts/W07/W07-99/integration_codex/git-archive-tooling-6d0f4a01bce142e2985393a2b1f329c1/"
    for key, count, evidence, detail in [
        ("all-receipt-whitespace", 3, "result.json", "Three actual git whitespace inspections reported immutable CRLF receipt bytes. Bytes preserved; no product or acceptance retry."),
        ("gbk-diagnostic-reader", 1, "result.json", "Actual default GBK subprocess reader failed on UTF8 raw. Subsequent inspection captured bytes. No canonical write occurred."),
        ("archived-audit-eof-whitespace", 1, "preservation-decision.json", "Actual source-only whitespace guard found final blank lines in two independently reviewed archival audit scripts. Exact reviewed bytes retained.")
    ]:
        new_failures.append({"origin_key": "W07-99/root-archive-" + key, "attempts": count, "retries_used": 0, "status": "ACTUAL_ROOT_TOOLING_FAILURE_PRESERVED", "evidence_ref": ref(archive + evidence), "detail": detail, "counter_reset": False, "product_acceptance_increment": 0})
    old_keys = {item["origin_key"] for item in failures}
    if len(failures) != 117 or any(item["origin_key"] in old_keys for item in new_failures):
        raise RuntimeError("failure origin mismatch")
    cp["failure_counters"] = failures + new_failures
    cp["revision"] = 250
    cp["expected_previous_revision"] = 249
    cp["head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode("ascii").strip()
    cp["updated_at"] = now
    cp["updated_by"] = "codex:/root"
    cp["next_command"] = "Independently review W04 Root transition helper and W05 doctor exact scope. Keep registry r39 and A05 CURRENT until reviewed final freeze. Then authorize three W04 command registrations and fresh MAIN collection; retain original W07 acceptance as historical on any captured-input change."
    cp["work_in_progress"]["construction_active_parents"] = ["W04"]
    cp["work_in_progress"]["next_action"] = cp["next_command"]
    cp["note"] = "W07 actual independent Root registration completed with CURRENT A05; six historical parent registrations include stale W04. W04 224 reviewed collector files integrated; no current capture, native11 or registry mutation yet. Doctor proposal remains read-only pending independent scope review. All 117 prior failure origins retained, plus five actual tooling origins."
    cp["evidence_index"] = list(dict.fromkeys(cp["evidence_index"] + [review_path, integration_path, amendment, (HERE / "W05-task-packet.invocation.json").relative_to(ROOT).as_posix()]))
    for worker in cp["workers"]:
        if worker.get("step_id") == "W04-99" and worker.get("slice_id") == "CURRENT_APPLICABILITY_REVALIDATION":
            worker["state"] = "INDEPENDENT_SOURCE_READY_INTEGRATED_CURRENT_COLLECTION_NOT_AUTHORIZED_YET"
            worker["independent_review_ref"] = ref(review_path)
            worker["main_integration_ref"] = ref(integration_path)
        if worker.get("step_id") == "W07-99" and worker.get("slice_id") == "STRICT_FORMAL_PROFILE":
            worker["state"] = "INTEGRATED_FULL_NATIVE_AND_INDEPENDENT_CURRENT_A05_ACCEPTED"
    ownership["revision"] = 79
    ownership["updated_at"] = now
    ownership["updated_by"] = "codex:/root"
    binding = ownership["card_path_bindings"]["W04-99"]["subtasks"]["current_applicability_revalidation"]
    binding["state"] = "SOURCE_READY_INTEGRATED_FRESH_COLLECTION_AND_CANONICAL_REBINDING_PENDING"
    binding["independent_source_review_ref"] = ref(review_path)
    binding["main_integration_ref"] = ref(integration_path)
    binding["acyclic_transition_scope_amendment_ref"] = ref(amendment)
    record = {"schema": "Root.continuation.v1", "actor": "codex:/root", "at": now, "previous_checkpoint_revision": 249, "new_checkpoint_revision": 250, "previous_ownership_revision": 78, "new_ownership_revision": 79, "source_review_ref": ref(review_path), "integration_ref": ref(integration_path), "amendment_ref": ref(amendment), "prior_failure_origins_preserved": len(failures), "new_failure_origins": new_failures, "registry_changed": False, "canonical_owner_rows_changed": False, "formal_increment": 0, "construction_active_parents": ["W04"], "W07_construction_lease_released": True}
    for path, raw in originals.items():
        immutable(HERE / (Path(path).stem + ".original.json"), raw)
    immutable(HERE / "registration.json", encode(record))
    desired = {paths[0]: encode(cp), paths[1]: (json.dumps(ownership, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n").encode("utf-8")}
    for path in paths:
        if (ROOT / path).read_bytes() != originals[path]:
            raise RuntimeError("canonical compare-and-swap changed")
    for path, raw in desired.items():
        temp = ROOT / (path + ".r250.tmp")
        immutable(temp, raw)
        os.replace(temp, ROOT / path)
    if (ROOT / paths[2]).read_bytes() != originals[paths[2]] or cp["failure_counters"][:117] != failures:
        raise RuntimeError("owner state or previous failures changed")
    immutable(HERE / "completed.json", encode({"at": now, "canonical_sha256": {path: digest((ROOT / path).read_bytes()) for path in paths}, "checkpoint_revision": 250, "ownership_revision": 79, "failure_origins": len(cp["failure_counters"]), "formal_increment": 0}))
    print(json.dumps({"checkpoint_revision": 250, "ownership_revision": 79, "failure_origins": len(cp["failure_counters"]), "formal_increment": 0, "construction_active_parents": ["W04"]}))


if __name__ == "__main__":
    main()
