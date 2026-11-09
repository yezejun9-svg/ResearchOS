"""Read-only overlay of the current generated v2.4 plan and state."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
SPEC = ROOT / ".local/worktrees/v24-continuation/spec/v2.4"
RECEIPT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


plan_path = SPEC / "contracts/execution.plan.json"
state_path = ROOT / "execution/v2.4/step_state.json"
selection_path = ROOT / "execution/v2.4/current_spec.json"
commands_path = ROOT / "execution/v2.4/commands.json"
ownership_path = ROOT / "execution/v2.4/path_ownership.json"
resume_path = ROOT / "execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp550/RESUME.current.json"
plan, state, commands = load(plan_path), load(state_path), load(commands_path)
statuses = {step["id"]: step for step in state["steps"]}
rows = []
for step in plan["steps"]:
    record = statuses.get(step["id"], {})
    blockers = [dep for dep in step["dependencies"] if statuses.get(dep, {}).get("status") != "ACCEPTED"]
    rows.append({
        "id": step["id"],
        "phase": step["phase"],
        "state": record.get("status", "NO_STATE"),
        "all_direct_deps_accepted": not blockers,
        "unaccepted_direct_deps": blockers,
        "resource_requirements": step.get("resource_requirements", []),
        "blocked_reason": record.get("blocked_reason"),
        "block_reason": record.get("block_reason"),
    })
summary = {
    "mode": "READ_ONLY_DAG_OVERLAY_NO_ACCEPTANCE",
    "authority_sha256": {str(p.relative_to(ROOT)): digest(p) for p in [selection_path, plan_path, state_path, commands_path, ownership_path, resume_path]},
    "plan_sha256_matches_state": digest(plan_path) == state.get("plan_sha256"),
    "plan_count": len(rows),
    "state_count": len(statuses),
    "status_counts": {name: sum(record.get("status", "NO_STATE") == name for record in statuses.values()) for name in sorted({record.get("status", "NO_STATE") for record in statuses.values()})},
    "unaccepted_with_all_direct_deps_accepted": [row for row in rows if row["state"] != "ACCEPTED" and row["all_direct_deps_accepted"]],
    "selected_downstream": [row for row in rows if row["id"] in {"W13-03", "W17-03", "W18-02", "W20-01", "W20-02", "W20-99"}],
    "command_bindings": {key: commands["commands"].get(key, {}).get("state", "ABSENT") for key in ["desktop.shell_launch", "desktop.installer_build", "test.ui.visual", "test.runtime", "package.validate_v24", "release.reproduce"]},
}
(RECEIPT / "dag-overlay.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"plan_count": summary["plan_count"], "state_count": summary["state_count"], "status_counts": summary["status_counts"], "ready_ids": [x["id"] for x in summary["unaccepted_with_all_direct_deps_accepted"]], "plan_sha256_matches_state": summary["plan_sha256_matches_state"]}, ensure_ascii=False))
