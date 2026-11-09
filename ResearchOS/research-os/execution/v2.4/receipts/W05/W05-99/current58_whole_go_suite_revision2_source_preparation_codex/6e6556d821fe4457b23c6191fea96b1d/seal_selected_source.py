"""Seal SOURCE-only current58 Go revision once; no candidate import or Go execution."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
root = here.parents[6]
review_path = (root / "execution/v2.4/receipts/W05/W05-99/"
               "current58_whole_go_suite_revision_independent_source_review_codex/"
               "4d91a96a40554889a6cc05d57711834a/review.final.json")
review_expected = ("422117629ebe8b8bb27baebf4a98f6447583c65ef343f05add7bded443aa5568", 19165)
finite = (root / "execution/v2.4/receipts/W05/W05-99/"
          "current58_whole_go_suite_source_preparation_codex/"
          "bbeb0e9d8d1b4c8fb367a5c45d80adea/whole58-finite.contract.proposed.json")
finite_expected = ("52828991f4f23d6957a3f7aa6343b50d8840efbe0ca42121871aa6bc8ce8c904", 275734)

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def emit(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with (here / name).open("xb") as stream: stream.write(raw)
    return pin(here / name)

review_ref = pin(review_path)
finite_ref = pin(finite)
assert (review_ref["sha256"], review_ref["bytes"]) == review_expected
assert (finite_ref["sha256"], finite_ref["bytes"]) == finite_expected
review = json.loads(review_path.read_bytes())
assert review["decision"] == "REQUEST_CHANGES"
assert {item["id"] for item in review["requested_changes"]} == {
    "GO58-REV-R01-OVERFLOW-AND-FIRSTCAUSE",
    "GO58-REV-R02-ATTESTATION-REVIEW-HASH-CYCLE",
    "GO58-REV-R03-BOOTSTRAP-INTEGRITY-AND-CWD",
}
audit_path = here / "static-audit.selected.json"
audit = json.loads(audit_path.read_bytes())
assert audit["all_static_checks_pass"] is True and len(audit["checks"]) == 17
selected = {name: pin(here / filename) for name, filename in {
    "gate": "whole58_gate.rev4.proposed.py",
    "runner": "whole58_finite_runner.rev9.proposed.py",
    "execution_contract": "whole58-execution.contract.rev4.proposed.json",
    "authority_interface": "authority-interface.rev9.proposed.json",
}.items()}
assert all(audit["pairs"][name]["after"] == ref for name, ref in selected.items())
origin_refs = []
for label in ("failure-origin-001", "failure-origin-002"):
    items = {name: pin(here / label / name) for name in ("input.json", "result.json", "origin.json")}
    origin = json.loads((here / label / "origin.json").read_bytes())
    assert origin["failure_count_delta"] == 1 and origin["actual_python_exit"] == 1
    assert origin["native_go_exit"] is None and origin["automatic_retry"] is False
    origin_refs.append({"label": label, "files": items})

template_ref = emit("root-source-members.template.json", {
    "schema": "researchos.current58-whole-go-source-preparation-manifest.v1",
    "stage": "SOURCE_PREPARATION_ONLY",
    "root_registration_ref": None,
    "source_acceptance": False,
    "members": [selected["runner"], selected["gate"], selected["execution_contract"],
                selected["authority_interface"], finite_ref],
    "future_root_must_bind_exact_pins_and_obtain_non_author_review": True,
})
report_ref = emit("report.selected.json", {
    "schema": "researchos.current58-whole-go-source-revision2-report.v1",
    "stage": "SOURCE_PREPARATION_ONLY",
    "decision": "SOURCE_CANDIDATE_REVIEWABLE",
    "prior_non_author_review_ref": review_ref,
    "prior_review_decision": "REQUEST_CHANGES",
    "selected_source_refs": selected,
    "frozen_finite_contract_ref": finite_ref,
    "root_source_members_template_ref": template_ref,
    "static_audit_ref": pin(audit_path),
    "whole_inverse_patch_ref": pin(here / "source-inverse.selected.patch"),
    "requested_change_disposition": {
        "R01": "Static candidate: OUTPUT_OVERFLOW records stream/read lower bound/cap under lock; both readers reject overflow, incomplete drain and NULL/incomplete raw; launch rechecks remaining wall after filesystem setup; no native exit is fabricated.",
        "R02": "Static candidate: native result then attestation then distinct non-author review; no attestation↔review SHA cycle. Scope and Root authority pin both. Actual W14 native tool evidence, directory snapshot and review remain future inputs.",
        "R03": "Static candidate: embedded gate SHA/bytes, parent reparse check, raw compile/exec after byte check, no SourceFileLoader or pyc; canonical ROOT, actual cwd, scope, registration, grant, lease and path authority bind one worktree.",
    },
    "source_inverse_basis": "Prior sealed 6a9 files; unified patch has exact before/after paths and all changed lines. The static audit lists AST-identical versus changed top-level functions.",
    "root_execution_prerequisites": [
        "Fresh Root UUID/registration, current checkpoint worker and lease, reviewed source manifest, separate grant and actual scope bytes",
        "Real pinned curated Go tree and actual native FrozenGoToolchainHash original tool evidence with independent review",
        "Actual Windows Job/process/HTTP/model-zero controller and authorized current resources, exact finite local lanes and budgets",
        "Fresh output/cache paths, source closure before/after, literal argv and cwd, real 58 list rosters and selected Go calls",
    ],
    "limitations": {"candidate_imported_or_executed": False, "go_executed": False,
                    "source_acceptance": False, "whole58_test_suite_qualified": False,
                    "formal_case_accepted_delta": 0, "external_effect_zero": None,
                    "actual_runtime_control": None, "model_cost_usd": None},
    "new_tool_failure_origins": origin_refs,
    "failure_count_delta": 2,
    "fixed_prior_cut_48_to_580_unchanged": True,
    "canonical_source_modified": False,
})
members = [pin(path) for path in sorted(here.rglob("*")) if path.is_file() and path.name not in
           {"manifest.selected.json", "handoff.selected.json"}]
manifest_ref = emit("manifest.selected.json", {
    "schema": "researchos.source-preparation-sealed-members.v1",
    "namespace": str(here), "stage": "SOURCE_PREPARATION_ONLY",
    "members": members, "member_count": len(members), "report_ref": report_ref,
    "source_acceptance": False, "formal_case_accepted_delta": 0,
})
handoff_ref = emit("handoff.selected.json", {
    "schema": "researchos.current58-whole-go-revision2-handoff.v1",
    "stage": "STOPPED_SOURCE_PREPARATION_ONLY",
    "selected_source_refs": selected,
    "root_source_members_template_ref": template_ref,
    "static_audit_ref": pin(audit_path),
    "whole_inverse_patch_ref": pin(here / "source-inverse.selected.patch"),
    "prior_non_author_review_ref": review_ref,
    "report_ref": report_ref, "manifest_ref": manifest_ref,
    "failure_count_delta": 2,
    "candidate_imported_or_executed": False, "go_executed": False,
    "source_acceptance": False, "formal_case_accepted_delta": 0,
})
print("SEALED_SOURCE_ONLY", manifest_ref["sha256"], manifest_ref["bytes"],
      handoff_ref["sha256"], handoff_ref["bytes"], len(members))
