import json
import hashlib
from pathlib import Path

OWN = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_next_ready_gates_readonly_codex/ad2dc8822ba647b79b84664f8ee93078")
ACTOR = "codex:/root/f08_i17_binding_impl"

def pin(p):
    b = p.read_bytes()
    return {"path": p.as_posix(), "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

def create(name, value):
    p = OWN / name
    if p.exists():
        raise ValueError("Refuse overwrite: " + name)
    p.write_bytes((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    return pin(p)

result = json.loads((OWN / "next-ready-gates.json").read_bytes())
audit = json.loads((OWN / "static-read-audit.json").read_bytes())
assert result["point_in_time"]["checkpoint_revision"] == 329
assert result["current_progress"]["formal_cases_total"] == 42
assert result["current_progress"]["reported_effective_formal_cases_accepted"] == 0
assert len(result["next_ready_candidates"]) == 2
assert all(v == 0 for v in result["execution"].values())
hdf = {
 "schema": "researchos.next-ready-gates-readonly-handoff.v1",
 "actor": ACTOR, "writer_status": "STOPPED_AFTER_SEAL",
 "decision": "READONLY_PREPARATION_ONLY_NO_PRODUCT_ACCEPTANCE",
 "point_in_time": result["point_in_time"],
 "next_ready_gates_ref": pin(OWN / "next-ready-gates.json"),
 "static_read_audit_ref": pin(OWN / "static-read-audit.json"),
 "original_tool_observations_ref": pin(OWN / "tool-observations.json"),
 "final_preseal_tool_observations_ref": pin(OWN / "final-preseal-tool-observations.json"),
 "point_in_time_observation_ref": pin(OWN / "point-in-time.json"),
 "companion_whole_manifest_path": (OWN / "manifest.json").as_posix(),
 "whole_manifest_rule": "All receipt files including this handoff; only manifest itself excluded. External caller pins manifest after creation to avoid self-hash cycles.",
 "summary": "最小可推进门为 W09-NEXT-01 非作者 controller 复审；W09-NEXT-02 在复审后准备 45 resource-free 调用的 Root scope。全部实际产品调用 NOT_RUN，4 OS-dependent 保持 HOLD。",
 "candidate_ids": [c["candidate_id"] for c in result["next_ready_candidates"]],
 "candidate_original_refs": result["next_ready_candidates"][0]["exact_original_refs"],
 "reported_progress": result["current_progress"],
 "new_failed_tool_invocations": 0, "new_failure_origins": [],
 "registered_failure_counter_rows_at_observation": 481,
 "historical_failure_counter_updates": 0,
 "sealer_actual_native_exit_at_write": None,
 "actual_native_exit_policy": "Original observations preserve bridged numbers or NULL; caller records this metadata sealer return after immutable files exist. Never count static checks as native product calls.",
 "controller_manifest_members_verified": audit["controller_manifest_members_verified"],
 "no_native_raw_gate_qualified_by_this_receipt": True,
 "execution_and_mutation_counts": result["execution"],
 "preserved": ["old I17 sealed source-preparation package STOPPED", "Main and canonical state", "Root CAS330 work", "all other writers", "all historical raw failure diagnostics and counts"],
 "checkpoint_re_read_during_root_CAS330": False,
 "no_self_acceptance": True
}
hdf_ref = create("handoff.json", hdf)
files = sorted(p for p in OWN.rglob("*") if p.is_file() and p.name != "manifest.json")
members = [pin(p) for p in files]
manifest_ref = create("manifest.json", {
 "schema": "researchos.readonly-receipt-whole-manifest.v1", "actor": ACTOR,
 "member_count": len(members), "member_bytes": sum(v["bytes"] for v in members),
 "self_excluded": True, "handoff_included": True, "members": members,
 "canonical_or_product_acceptance": False
})
checks = []
for v in members:
    actual = pin(Path(v["path"]))
    checks.append(actual == v)
assert all(checks)
print(json.dumps({"handoff": hdf_ref, "whole_manifest": manifest_ref, "next_ready_gates": pin(OWN / "next-ready-gates.json"), "members_verified": len(checks), "new_failed_tool_invocations": 0, "writer_status": "STOPPED"}, ensure_ascii=False))

