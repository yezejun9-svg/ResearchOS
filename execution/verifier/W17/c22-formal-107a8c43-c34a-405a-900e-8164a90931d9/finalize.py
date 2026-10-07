"""Produce the independently reviewed, narrowly scoped C22 acceptance record."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RUN = "107a8c43-c34a-405a-900e-8164a90931d9"
PACK = ROOT / "execution/receipts/W17" / RUN
PRIOR = ROOT / "execution/verifier/W17/c22-6d070c8"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return path.relative_to(ROOT).as_posix()

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def canonical(value):
    # This receipt deliberately uses only the JCS subset of ASCII keys,
    # strings, integers, booleans, null, arrays and objects (no floats).
    def check(item):
        if isinstance(item, dict):
            assert all(key.isascii() for key in item)
            for child in item.values():
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)
        else:
            assert item is None or isinstance(item, (str, int, bool))
    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

audit = read(OUT / "audit-report.json")
route = read(OUT / "route-and-boundary-review.json")
prior = read(PRIOR / "review.json")
executor = read(PACK / "receipt.json")
assert audit["status"] == "PASS"
assert executor["receipt_hash"] == audit["executor_receipt_jcs_hash"]
assert sha(PACK / "receipt.json") == audit["executor_receipt_sha256"]
assert sha(PACK / "artifacts.json") == audit["artifact_manifest_sha256"]
assert sha(PACK / "C22.json") == audit["global_case_sha256"]

limits = [
    "Formal acceptance is limited to frozen C22-01 through C22-04 in FIXTURE mode and W17-G03. Whole W17, A10/A11, remote-phone acceptance and upstream dependency clearance remain false. Prior C02 acceptance is not reassessed or overwritten.",
    "The host is trusted and can read the synthetic CanaryStore. OS isolation is demonstrated for fresh constrained AppContainer candidates, not arbitrary unrestricted same-user processes.",
    "Host-issued scoped-credential HTTP probes and native AppContainer file/network probes are distinct evidence layers. The native candidate does not issue the authenticated API probes.",
    "SafeSummary is computed by the synthetic fixture host from actual per-question arithmetic child outputs. This does not certify actual frozen-provider evaluation or production declassification authority; LIVE and BOUNDED_AUTO remain closed.",
    "Dedicated preview/export/log/backup HTTP routes are absent and return 404. Existing content protection and the actual backup engine refusal are separately exercised.",
    "Prior independent handle probes terminated with Windows STATUS_INVALID_HANDLE before normal result output. Both failed harness commands and full raw evidence remain preserved; a successful normal handle-read rejection result is not claimed.",
    "The final independent network probe observed a bounded owned-loopback connection timeout (errno 10060), no child request at a host-positive listener, and empty inherited host environment values. No arbitrary external destination or universal packet-level zero-traffic claim is made. The earlier overly strict 10013 expectation remains recorded as a failed harness command.",
    "No actual product database, protected service 79136, real holdout payload, real provider, service activation or external network target was accessed during this formal reconciliation. Existing policy-denied activation, CLI and author intermediate-directory cleanup actions were not retried.",
    "The three registered runs execute current integrated source 9bdec8fdfb41329b72ad130c1ac63c6a2a4e50c1. The earlier independent replay and adversarial probes were performed on the original C22 source; unchanged security sources, the routing increment, S1 visibility compatibility and fresh integrated reports were explicitly reconciled here.",
]

review = {
    "artifact_kind": "INDEPENDENT_FORMAL_CASE_REVIEW",
    "task_id": "W17", "run_id": RUN,
    "verifier_identity": "codex:/root/evolution_verifier",
    "verdict": "PASS_IN_SCOPE", "status": "PARTIAL_ACCEPTANCE",
    "scope": "Complete frozen C22 in FIXTURE mode and W17-G03 only",
    "source_revision": audit["source_revision"],
    "findings": [], "blocking_P1_findings": [],
    "verification_summary": audit,
    "route_and_boundary_review": route,
    "case_mapping": prior["case_mapping"],
    "case_mapping_note": "Mappings are verified against all three current integrated reports and their raw evidence; prior independent current-authority/network probes remain supplementary evidence with the exact limitations recorded below.",
    "limits": limits,
    "prior_independent_review_reference": ref(PRIOR / "review.json"),
    "prior_independent_review_sha256": sha(PRIOR / "review.json"),
    "prior_independent_evidence_index_reference": ref(PRIOR / "index.json"),
    "prior_independent_evidence_index_sha256": sha(PRIOR / "index.json"),
}
write(OUT / "review.json", review)
(OUT / "review.md").write_text(
    "# W17 C22 independent formal review\n\n"
    "Verdict: **PASS_IN_SCOPE / PARTIAL_ACCEPTANCE**. Complete frozen C22-01 through C22-04 in FIXTURE mode and W17-G03 are accepted. Whole W17, A10/A11, remote phone, upstream dependency clearance, LIVE and BOUNDED_AUTO remain unaccepted.\n\n"
    "Two registered case commands and the registered W17-G03 command each passed 137 assertions and recorded 304 actual HTTP requests. This is 411 assertion execution instances, 912 HTTP requests, 12 distinct fresh AppContainer SIDs and 9 control-plane launches; it is not 411 unique assertions. The verifier reconciled 197 manifested evidence files, 320 current source hashes/Git blobs, three 211-file source manifests, seven rejected selector cases, and the 79-file prior independent review index. No confirmed finding remains in this scope.\n\n"
    "Raw HTTP wire requests/responses, authorized full-body controls, native process/OS-denial receipts, marker/metadata scans, private results, restart/revocation behavior, missing-provider refusal, public summaries and frozen expected/actual assertion mappings were checked. Routing changes affect only the intended registered commands; integrated S1 visibility changes preserve ordinary Qualification and protected Artifact boundaries.\n\n"
    "All earlier independent harness failures remain visible and are not converted into passing commands. No new product execution or production access was required for this formal increment.\n\n"
    + "\n".join("- " + item for item in limits) + "\n",
    encoding="utf-8",
)

index = {
    "artifact_kind": "INDEPENDENT_REVIEW_EVIDENCE_INDEX", "run_id": RUN,
    "scope": "This review directory only; final signed receipt is outside the index to avoid circular hashing.",
    "files": [
        {"path": ref(path), "sha256": sha(path), "bytes": path.stat().st_size}
        for path in sorted(OUT.rglob("*"))
        if path.is_file() and path.name != "evidence-index.json"
    ],
}
write(OUT / "evidence-index.json", index)
gate_run = next(row for row in audit["registered_runs"] if row["check_id"] == "W17-G03")
receipt = {
    "artifact_kind": "INDEPENDENT_LIMITED_CONSTRUCTION_ACCEPTANCE_WITH_OWNED_CASE_VERDICTS",
    "task_id": "W17", "run_id": RUN, "project_id": executor["project_id"],
    "status": "PARTIAL_ACCEPTANCE", "verdict": "PASS_IN_SCOPE",
    "stage_accepted": False, "whole_W17_accepted": False,
    "C22_accepted": True, "W17_G03_accepted": True,
    "A10_accepted": False, "A11_accepted": False, "remote_phone_accepted": False,
    "upstream_dependencies_cleared": False, "LIVE_qualified": False, "BOUNDED_AUTO_granted": False,
    "scope": "Complete frozen C22 assertions C22-01 through C22-04 in FIXTURE mode and W17-G03 only.",
    "executor_identity": "codex:/root", "verifier_identity": "codex:/root/evolution_verifier",
    "independence_basis": "Verifier did not implement product code or prepare the executor GLOBAL package. Independently replayed original C22 source with additional adversarial probes, then reconciled current integrated raw wire/native evidence, Git blobs, source hashes, command receipts and exact frozen assertions.",
    "executed_code_revision": audit["source_revision"],
    "executor_receipt_reference": ref(PACK / "receipt.json"),
    "executor_receipt_sha256": audit["executor_receipt_sha256"],
    "executor_receipt_jcs_hash": audit["executor_receipt_jcs_hash"],
    "artifact_manifest_reference": ref(PACK / "artifacts.json"),
    "artifact_manifest_sha256": audit["artifact_manifest_sha256"],
    "artifact_count_verified": audit["manifest_files"],
    "acceptance_baseline_reference": "spec/v2.0/contracts/acceptance.json",
    "acceptance_baseline_sha256": sha(ROOT / "spec/v2.0/contracts/acceptance.json"),
    "task_baseline_reference": "spec/v2.0/contracts/tasks.json",
    "task_baseline_sha256": sha(ROOT / "spec/v2.0/contracts/tasks.json"),
    "task_gates": [{"check_id": "W17-G03", "verdict": "PASS", "mode": "FIXTURE", "actual_invocation_reference": gate_run["invocation_reference"], "basis": "Registered gate executes complete C22 fixture; access subjects, protected content, restricted full-body positives, native OS denial and zero candidate marker/metadata matches are reconciled from raw evidence."}],
    "owned_case_verdicts": [{
        "case_id": "C22", "verdict": "PASS", "mode": "FIXTURE",
        "assertion_ids": ["C22-01", "C22-02", "C22-03", "C22-04"],
        "assertion_verdicts": {key: "PASS" for key in ["C22-01", "C22-02", "C22-03", "C22-04"]},
        "all_frozen_assertions_covered": True,
        "expected_actual_status_reference": ref(PACK / "C22.json"),
        "executor_global_evidence_sha256": audit["global_case_sha256"],
        "basis": "Both required registered case commands cover all frozen assertions: private fixture content is unreadable by constrained candidates, per-question execution exposes only allowed input and safe aggregate output, current restricted authority controls exact private reads, restart/revocation retains isolation, missing provider fails closed and automatic/LIVE qualification remains refused.",
    }],
    "open_findings": [],
    "open_blockers": executor["open_blockers"],
    "resource_request_ids": executor["resource_request_ids"],
    "verification_summary": audit, "limits": limits,
    "signed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "evidence_index_reference": ref(OUT / "evidence-index.json"),
    "evidence_index_sha256": sha(OUT / "evidence-index.json"),
    "semantic_audit_reference": ref(OUT / "audit-report.json"),
    "semantic_audit_sha256": sha(OUT / "audit-report.json"),
    "review_reference": ref(OUT / "review.json"),
    "review_sha256": sha(OUT / "review.json"),
    "prior_independent_review_reference": ref(PRIOR / "review.json"),
    "prior_independent_review_sha256": sha(PRIOR / "review.json"),
}
receipt["receipt_hash"] = "sha256:" + hashlib.sha256(canonical(receipt)).hexdigest()
target = ROOT / "execution/verifier/W17" / (RUN + ".json")
write(target, receipt)
check = read(target)
signature = check.pop("receipt_hash")
assert signature == "sha256:" + hashlib.sha256(canonical(check)).hexdigest()
for row in index["files"]:
    assert sha(ROOT / row["path"]) == row["sha256"]
print(json.dumps({"receipt": ref(target), "receipt_file_sha256": sha(target), "receipt_hash": signature, "review_sha256": sha(OUT / "review.json"), "index_sha256": sha(OUT / "evidence-index.json"), "indexed_files": len(index["files"]), "status": "PASS_IN_SCOPE"}, indent=2))
