"""Pure IO/AST sealer for the whole-Go Root cap-producer source proposal."""

import ast
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
OLD = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_configuration_sync_source_preparation_codex/4a8dca58606d4a4db695aa6dc9f082cb")
REVIEW = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/current58_whole_go_configuration_sync_independent_source_review_codex/758c3b04780a4cafb26d4ec35dc1a5a1/review.json")
PIN_HDF = ("532e769ecd7b968b6cc32a94453ba5ed7b8f1c123bede764dc86a1d85095cbf1", 4433)
PIN_MF = ("00d5d0a33b07f199b95a5aa18d4fc171026a643a99296af939aee2724885ecbd", 5341)
PIN_REVIEW = ("5c0dbca02fdab6345db73455c0d9b3a4e2689f5817ed9b4a6304c56b504fac7f", 3909)


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def write_new(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    path = HERE / name
    with path.open("xb") as out:
        out.write(raw)
    return pin(path)


def expected(path, sha, size):
    actual = pin(path)
    assert actual["sha256"] == sha and actual["bytes"] == size, path
    return actual


hdf_ref = expected(OLD / "handoff.selected.json", *PIN_HDF)
mf_ref = expected(OLD / "manifest.selected.json", *PIN_MF)
review_ref = expected(REVIEW, *PIN_REVIEW)
hdf = json.loads((OLD / "handoff.selected.json").read_text(encoding="utf-8"))
review = json.loads(REVIEW.read_text(encoding="utf-8"))
assert review["decision"] == "READY_SOURCE_PREPARATION_ONLY"
assert hdf["manifest_ref"] == mf_ref
for selected in hdf["selected_source_refs"].values():
    actual = pin(Path(selected["path"]))
    assert actual == selected
source = HERE / "wholego_cap_metadata.proposed.py"
text = source.read_text(encoding="utf-8")
tree = ast.parse(text, filename=str(source))
compile(tree, str(source), "exec", dont_inherit=True)
imports = {alias.name for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
           for alias in node.names}
assert not (imports & {"subprocess", "requests", "urllib", "socket"})
assert all("def " + stage + "(" in text for stage in ("attest", "scope", "arm", "close"))
limits = json.loads((HERE / "root-limits.template.json").read_text(encoding="utf-8"))
keys = json.loads((OLD / "whole58-execution.contract.rev4.proposed.json").read_text(encoding="utf-8"))["numeric_budget_keys"]
assert len(keys) == 13 and set(limits["budgets"]) == set(keys)
assert limits["budgets"]["max_model_requests"] == 0
json.loads((HERE / "root-cap-input.template.json").read_text(encoding="utf-8"))
for name in ("failure-origin-001.json", "failure-origin-002.json"):
    json.loads((HERE / name).read_text(encoding="utf-8"))

inverse_ref = write_new("source-inverse.json", {
    "schema": "researchos.current58-whole-go-cap-producer-source-inverse.v1",
    "main_modified": False,
    "source_action": "ADD_NEW_SOURCE_ONLY",
    "addition_ref": pin(source),
    "inverse": "Remove only the exact candidate source bytes if Root later copies them; current Main has no diff and requires no reversal.",
    "old_selected_handoff_ref": hdf_ref,
    "old_selected_manifest_ref": mf_ref,
})
report_ref = write_new("report.json", {
    "schema": "researchos.current58-whole-go-root-cap-producer-source-report.v1",
    "status": "SOURCE_PREPARATION_ONLY",
    "main_modified": False,
    "go_or_cli_or_model_executed": False,
    "candidate_imported_or_executed": False,
    "whole58_test_suite_qualified": False,
    "formal_case_accepted_delta": 0,
    "selected_source_handoff_ref": hdf_ref,
    "selected_source_manifest_ref": mf_ref,
    "non_author_selected_source_review_ref": review_ref,
    "source_ref": pin(source),
    "source_inverse_ref": inverse_ref,
    "numeric_provenance": "Exactly 13 budget values copied from Root's pinned, non-author reviewed limits; 6 runtime values read from actual outer Job, active meter and fresh heartbeat facts. No default positive amount or guessed process/HTTP cap is inserted.",
    "stages": ["attest: Root actual native Go hash + typed tree -> immutable attestation without review back-reference", "scope: reviewed attestation + exact finite plan + reviewed Root limits -> proposed scope before registration", "arm: current checkpoint/registration/review/grant/lease + actual Job/PID/meter/path facts -> authority bundle and 19-value provenance", "close: single Root invocation + original runner/terminal/final controller facts -> observation with UNKNOWN cost preserved"],
    "actual_authority_open": ["Root has not supplied this new run UUID, limits, source manifest, current checkpoint, registration, lease, grant, Windows Job/PID, meter, controller implementation, cap reviews or final observation.", "A matching JSON claim alone does not prove OS Job ownership or network interception. The selected gate must independently self-check actual Job membership and live heartbeat before launching Go; non-author review must validate controller semantics.", "The six observed runtime numbers are metadata with exact source refs, not permission to start a process."],
    "held": {"local_selected_source_ids": 743, "fixed_codex_live_ids": 2, "real_model_lane": "REAL_MODEL_B01_HOLD"},
    "static_checks": {"python_ast": "PASS", "json_templates": "PASS", "selected_source_pins": "PASS", "review_pin": "PASS", "Go_calls": 0},
    "new_tool_failure_origins": [pin(HERE / "failure-origin-001.json"), pin(HERE / "failure-origin-002.json")],
})
members = [pin(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name not in {"manifest.json", "handoff.json"}]
manifest_ref = write_new("manifest.json", {"schema": "researchos.current58-whole-go-root-cap-producer-source-manifest.v1", "members": members, "member_count": len(members), "source_acceptance": False, "formal_case_accepted_delta": 0})
handoff_ref = write_new("handoff.json", {"schema": "researchos.current58-whole-go-root-cap-producer-source-handoff.v1", "status": "STOPPED_SOURCE_PREPARATION_ONLY", "source_ref": pin(source), "report_ref": report_ref, "manifest_ref": manifest_ref, "source_inverse_ref": inverse_ref, "Root_next": "Independent code and controller review, fresh Root UUID/limits/cap review, native Go hash and review, source manifest, scope, checkpoint CAS/registration/lease/review/grant, actual Windows Job+meter/path authority, then one runner invocation. This source does not grant execution.", "whole_suite_qualified": False, "formal_case_accepted_delta": 0})
print(json.dumps({"report": report_ref, "manifest": manifest_ref, "handoff": handoff_ref, "members": len(members)}, ensure_ascii=False))
