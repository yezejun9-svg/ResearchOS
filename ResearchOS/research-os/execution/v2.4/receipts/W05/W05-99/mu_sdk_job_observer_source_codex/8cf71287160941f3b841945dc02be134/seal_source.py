"""Seal own source-preparation namespace only; no target execution."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/作品集/ResearchOS/research-os")
CONTROLLER = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_source_codex/2e716ffb2df44199b7d3d28cdbdddbed"


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def put(name, obj):
    path = HERE / name
    with path.open("xb") as handle:
        handle.write((json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    return pin(path)


def main():
    source = HERE / "mu_sdk_job_observer.proposed.py"
    tree = ast.parse(source.read_bytes())
    frozen = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ("RUNNER_REF", "BASE_REF"):
                frozen[node.targets[0].id] = ast.literal_eval(node.value)
    for ref in frozen.values():
        assert pin(Path(ref["path"])) == ref or (pin(Path(ref["path"]))["sha256"] == ref["sha256"] and pin(Path(ref["path"]))["bytes"] == ref["bytes"])
    controller_refs = {name: pin(CONTROLLER / name) for name in
                       ("controller.py", "owned_job_hooks.py", "phase_worker.py", "job_probe_worker.py", "handoff.json", "manifest.json")}
    assert controller_refs["controller.py"]["sha256"] == "ddcf54587a9cb32cff4470ebf2fa2d34a57ef061dc64e27c71b5f7b610a39ae8"
    for name in ("controller.py", "owned_job_hooks.py", "phase_worker.py", "job_probe_worker.py"):
        compile((CONTROLLER / name).read_bytes(), str(CONTROLLER / name), "exec")
    controls = json.loads((HERE / "pure-controls.v3.report.json").read_bytes())
    assert controls["source_ref"] == pin(source) and controls["count"] == 52 and controls["failed"] == 0
    history = []
    for report, snapshot in (("pure-controls.report.json", "mu_sdk_job_observer.initial.py"),
                             ("pure-controls.v2.report.json", "mu_sdk_job_observer.pre-bootstrap-null.py")):
        prior = json.loads((HERE / report).read_bytes())
        actual = pin(HERE / snapshot)
        assert actual["sha256"] == prior["source_ref"]["sha256"] and actual["bytes"] == prior["source_ref"]["bytes"]
        history.append({"report_ref": pin(HERE / report), "preserved_source_ref": actual})
    template = {"schema": "researchos.mu-sdk-controller-observer-independent-source-review.v1",
                "decision": None, "actor_id": None, "controller_source_ref": controller_refs["controller.py"],
                "observer_source_ref": pin(source), "hooks_source_ref": controller_refs["owned_job_hooks.py"],
                "runner_source_ref": frozen["RUNNER_REF"],
                "callback_contract": "REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME", "formal_acceptance": False,
                "note": "INPUT TEMPLATE ONLY: must be independently reviewed and issued, not copied into a grant."}
    template_ref = put("independent-source-review.template.json", template)
    canonical = {name: pin(ROOT / "execution/v2.4" / name) for name in
                 ("checkpoint.json", "path_ownership.json", "source_state.json", "command_manifest.json")
                 if (ROOT / "execution/v2.4" / name).is_file()}
    report = {"schema": "researchos.mu-sdk-job-observer-source-preparation.v1",
              "decision": "SOURCE_PREPARATION_ONLY_WITH_OPEN", "actor_id": "codex:/root/w05_merge_review",
              "source_ref": pin(source), "controller_refs": controller_refs, "frozen_refs": frozen,
              "pure_controls_ref": pin(HERE / "pure-controls.v3.report.json"), "pure_controls": 52,
              "controls_failed": 0, "source_history": history, "source_review_template_ref": template_ref,
              "canonical_read_pins_at_seal": canonical,
              "actual_observer_calls": 0, "target_native_invocations": 0, "provider_requests": 0,
              "main_writes": 0, "canonical_writes": 0, "formal_acceptance_delta": 0,
              "source_qualification": False, "runtime_probe_issued": False, "root_execution_grant_issued": False,
              "limits": {"maximum_provider_requests": 3, "requested_output_tokens_total": 8192, "total_wall_seconds": 300},
              "open": ["independent controller/observer source review", "actual Windows callback execution",
                       "concrete authorized phase seeds", "trusted qualification Host admission boundary"],
              "limits_of_evidence": ["Pure controls do not prove Windows runtime behavior.",
                                     "No separate protected-process or human onsite observer is claimed.",
                                     "No full lifecycle cleanup or product acceptance is claimed."]}
    report_ref = put("source-preparation.json", report)
    members = [pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name not in ("manifest.json", "handoff.json")]
    manifest_ref = put("manifest.json", {"schema": "researchos.source-preparation-manifest.v1",
                     "members": members, "excluded": ["manifest.json", "handoff.json"],
                     "inventory_scope": "Every existing direct file except manifest and subsequent handoff"})
    handoff_ref = put("handoff.json", {"schema": "researchos.mu-sdk-observer-source-handoff.v1",
                    "decision": "SOURCE_PREPARATION_ONLY_WITH_OPEN", "source_ref": pin(source),
                    "report_ref": report_ref, "manifest_ref": manifest_ref,
                    "independent_source_review_template_ref": template_ref,
                    "source_author": "codex:/root/w05_merge_review", "actual_native_invocations": 0,
                    "provider_requests": 0, "formal_acceptance_delta": 0, "stop_source_writes": True})
    print(json.dumps({"source": pin(source), "report": report_ref, "manifest": manifest_ref, "handoff": handoff_ref,
                      "members": len(members), "controls": 52}, ensure_ascii=False))


if __name__ == "__main__":
    main()
