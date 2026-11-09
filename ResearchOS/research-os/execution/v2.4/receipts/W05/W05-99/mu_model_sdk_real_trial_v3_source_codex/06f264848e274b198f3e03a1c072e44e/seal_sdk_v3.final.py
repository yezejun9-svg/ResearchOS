"""Seal the SDK v3 SOURCE_ONLY proposal with exact byte inverses."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_source_codex/1ccdc0cec995488c82400608ed275029"
REVIEW = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_revision_independent_source_review_codex/e0b3e659af91457c82383c12bd374851/review.json"
EXPECTED_REVIEW = "8d4608706e4cc70287a6f711fccaa208fbdc90075ee79cfcb2eee1992ca2fa88"
FILES = {
    "mu_sdk_trial.v2.proposed.py": ("mu_sdk_trial.v3.proposed.py",
                                    "6f03caf4885f2d85012549e1790aab8896cc2980e90fdcc6668e7aad263aaec2"),
    "internal_host_vault.v2.proposed.go": ("internal_host_vault.v3.proposed.go",
                                            "1994a00fe224ddd9f4a5d064a029356304ea5aaee118a096fabaee7418fd7e0e"),
    "internal_host_host.v2.proposed.go": ("internal_host_host.v3.proposed.go",
                                          "58a1c6b6ceeb57a852560e759ba6e06a2db5acade97a1b400a83fbd6bb07826a"),
    "apps_control_main.v2.proposed.go": ("apps_control_main.v3.proposed.go",
                                         "3ec7e36ac5f7d3b711b85350f882f82da4b77c3f3241daef5651969ae952c058"),
    "runtime_qualification.unlimited.v3.proposed.go":
        ("runtime_qualification.unlimited.v4.proposed.go",
         "420aaec664f877806af079d47cf5e5a0cc4950f2cdc42b8ae1dc16ef7a4c5c54"),
}

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path).replace("\\", "/"), "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw)}

def put(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with (HERE / name).open("xb") as stream:
        stream.write(raw)

def diff(name, before, after, fromfile, tofile):
    patch = "".join(difflib.unified_diff(before.splitlines(keepends=True),
                                         after.splitlines(keepends=True),
                                         fromfile=fromfile, tofile=tofile)).encode("utf-8")
    with (HERE / name).open("xb") as stream:
        stream.write(patch)

assert pin(REVIEW)["sha256"] == EXPECTED_REVIEW
review = json.loads(REVIEW.read_bytes())
assert review["decision"] == "REQUEST_CHANGES" and len(review["requested_changes"]) == 4
changes = []
for old_name, (new_name, expected_sha) in FILES.items():
    old, new = OLD / old_name, HERE / new_name
    assert pin(old)["sha256"] == expected_sha
    before, after = old.read_text(encoding="utf-8"), new.read_text(encoding="utf-8")
    if new_name.endswith(".py"):
        ast.parse(after, filename=str(new))
    forward = new_name + ".patch"
    inverse = new_name + ".inverse.patch"
    diff(forward, before, after, "a/" + old_name, "b/" + new_name)
    diff(inverse, after, before, "a/" + new_name, "b/" + old_name)
    changes.append({"old": pin(old), "new": pin(new), "forward": pin(HERE / forward),
                    "inverse": pin(HERE / inverse), "byte_identical": before == after})

template = json.loads((HERE / "input.v3.template.json").read_bytes())
assert template["input_basis_ref"] is None and template["root_grant"] is None
assert template["maximum_provider_requests"] == 3 and template["requested_output_tokens_total"] == 8192
assert template["total_wall_seconds"] == 300
precheck = json.loads((HERE / "precheck.v3.final.json").read_bytes())
assert not precheck["candidate_imported"] and precheck["go_cli_sdk_provider_executions"] == 0
origins = [HERE / "tool-failure-origin-001.json", HERE / "tool-failure-origin-002.json",
           HERE / "tool-failure-origin-003.json"]
assert all(json.loads(path.read_bytes())["counter_increment"] == 1 for path in origins)
report = {
    "schema": "researchos.mu-sdk-real-trial-v3-source-report.v1",
    "decision": "SOURCE_PREPARATION_ONLY", "review_basis_ref": pin(REVIEW),
    "changes": changes,
    "R01": "Closed phase basis excludes only later authority refs; Root registration/review/grant pin basis; full consumed fields and exact child argv/cwd/env rechecked before each child.",
    "R02": "Actual EntityRef.id links profile Artifact and independent AcceptanceReceipt; approval receipt_ref is separately verified Run observation LOG Artifact with sealed bytes/use and exact current epoch.",
    "R03": "Observed child nonzero exit is frozen before raw hashing; later hash errors remain secondary; NULL exit preserved.",
    "R04": "Control and Host check actual host/DB leaf before lease/Open/mkdir/privateDir; Go helper rejects existing alias/reparse/old-file identity. Real Windows junction test remains NOT_RUN.",
    "actual_root_registration_grant_controller": None,
    "old_sdk_v2_and_earlier_untouched": True,
    "precheck_ref": pin(HERE / "precheck.v3.final.json"),
    "failure_origins": [pin(path) for path in origins],
    "new_tool_failure_count": 3, "candidate_executions": 0,
    "go_cli_sdk_provider_executions": 0, "source_acceptance": False,
    "formal_case_accepted_delta": 0, "status": "STOPPED_AFTER_SEAL"
}
put("report.json", report)
members = [pin(path) for path in sorted(HERE.iterdir()) if path.is_file()
           and path.name not in {"manifest.json", "handoff.json"}]
put("manifest.json", {"schema": "researchos.mu-sdk-real-trial-v3-source-manifest.v1",
                      "namespace": str(HERE).replace("\\", "/"), "members": members,
                      "members_count": len(members), "source_only": True,
                      "actual_sdk_calls": 0})
handoff = {
    "schema": "researchos.mu-sdk-real-trial-v3-source-handoff.v1",
    "decision": "SOURCE_PREPARATION_ONLY", "manifest_ref": pin(HERE / "manifest.json"),
    "report_ref": pin(HERE / "report.json"),
    "runner_ref": pin(HERE / "mu_sdk_trial.v3.proposed.py"),
    "go_refs": [pin(HERE / pair[0]) for pair in FILES.values() if pair[0].endswith(".go")],
    "template_ref": pin(HERE / "input.v3.template.json"),
    "precheck_ref": pin(HERE / "precheck.v3.final.json"),
    "failure_origins": [pin(path) for path in origins],
    "actual_authority": None, "source_acceptance": False,
    "formal_case_accepted_delta": 0, "status": "STOPPED_AFTER_SEAL"
}
put("handoff.json", handoff)
print(json.dumps({"report": pin(HERE / "report.json"), "manifest": pin(HERE / "manifest.json"),
                  "handoff": pin(HERE / "handoff.json"), "members": len(members)}, ensure_ascii=False))
