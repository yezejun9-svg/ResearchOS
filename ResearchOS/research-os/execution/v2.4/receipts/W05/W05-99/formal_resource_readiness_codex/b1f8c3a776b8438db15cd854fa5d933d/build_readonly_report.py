import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path

REPO = Path("D:/作品集/ResearchOS/research-os")
PKG = Path("D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4")
OWN = Path(__file__).resolve().parent
PINNED_PYTHON = "C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe"

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def pin(path):
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

files = {
    "repo_agents": REPO / "AGENTS.md",
    "start_here": PKG / "00_START_HERE.md",
    "agent_goal": PKG / "08_AGENT_EXECUTION_GOAL.md",
    "acceptance_text": PKG / "06_ACCEPTANCE_TESTS.md",
    "tasks": PKG / "contracts/tasks.json",
    "acceptance": PKG / "contracts/acceptance.json",
    "plan": PKG / "contracts/execution.plan.json",
    "task_packet_source": PKG / "tools/task_packet.py",
    "current_spec": REPO / "execution/v2.4/current_spec.json",
    "checkpoint": REPO / "execution/v2.4/checkpoint.json",
    "step_state": REPO / "execution/v2.4/step_state.json",
    "commands": REPO / "execution/v2.4/commands.json",
    "parent_gate_ledger": REPO / "execution/v2.4/parent_gate_ledger.json",
    "formal_case_requirements": REPO / "execution/v2.4/formal_case_requirements.json",
    "source_authority": REPO / "execution/v2.4/receipts/W13/W13-03/fresh58_public_source_authority_codex/16e288f44f104376898cde4336c705a1/current43-authority.json",
    "desktop_resume": REPO / "execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-1c4ea6999d4d4437a0202c4e81ce581b/RESUME.desktop58.scope-built.independent-review.pending.json",
    "desktop_scope": REPO / "execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-1c4ea6999d4d4437a0202c4e81ce581b/scope_registration.json",
    "b01_conclusion": REPO / "execution/v2.4/receipts/W05/W05-99/provider_budget_resource_readonly_codex/budget-4d5e48bb6b764a34ac537990b10290f2/conclusion.json",
    "dispatcher_source": REPO / "execution/command_dispatcher/dispatch.py",
}
refs = {k: pin(v) for k, v in files.items()}
tasks_doc = read_json(files["tasks"])
cases_doc = read_json(files["acceptance"])
plan_doc = read_json(files["plan"])
state_doc = read_json(files["step_state"])
commands_doc = read_json(files["commands"])
checkpoint_doc = read_json(files["checkpoint"])
current_spec_doc = read_json(files["current_spec"])
source_authority_doc = read_json(files["source_authority"])
desktop_resume_doc = read_json(files["desktop_resume"])
b01_doc = read_json(files["b01_conclusion"])
state_rows = state_doc["steps"]
state = {row["id"]: row for row in state_rows}
plan_rows = plan_doc["steps"]
steps_by_parent = {}
for row in plan_rows:
    steps_by_parent.setdefault(row["parent_task"], []).append(row)
case_rows = cases_doc["cases"]
case_by_owner = {}
for row in case_rows:
    case_by_owner.setdefault(row["final_owner_task"], []).append(row["id"])
formal_bindings = tasks_doc["verification_command_selection"]["formal_case_bindings"]
bindings_by_case = {}
for row in formal_bindings:
    bindings_by_case.setdefault(row["case_id"], []).append(row)
commands = commands_doc["commands"]

def selector_match(registered, owner, cid):
    if not isinstance(registered, dict):
        return False
    selectors = registered.get("selectors")
    if not isinstance(selectors, dict):
        return False
    t = selectors.get("task_id", [])
    c = selectors.get("case_id", [])
    return (owner in t or "*" in t) and (cid in c or "*" in c)

parents = []
for task in tasks_doc["tasks"]:
    tid = task["task_id"]
    final = task["final_step_id"]
    actual = state.get(final, {})
    cards = steps_by_parent.get(tid, [])
    resource_union = sorted({resource for card in cards for resource in card.get("resource_requirements", []) if isinstance(resource, str)})
    parents.append({
        "task_id": tid,
        "title": task["title"],
        "depends_on": task.get("depends_on", []),
        "final_step_id": final,
        "actual_final_card_status": actual.get("status", "NOT_STARTED"),
        "actual_final_card_evidence": actual.get("evidence", []),
        "actual_final_card_verifier_id": actual.get("verifier_id"),
        "actual_final_card_accepted_at": actual.get("accepted_at"),
        "owned_formal_cases": case_by_owner.get(tid, []),
        "planned_card_count": len(cards),
        "recorded_card_statuses": {card["id"]: state.get(card["id"], {}).get("status", "NOT_STARTED") for card in cards},
        "all_card_resource_requirements": resource_union,
        "final_card_resource_requirements": next((card.get("resource_requirements", []) for card in cards if card["id"] == final), []),
        "independent_review_required": next((card.get("handoff", {}).get("independent_review_required") for card in cards if card["id"] == final), None),
    })

cases = []
for case in case_rows:
    cid = case["id"]
    owner = case["final_owner_task"]
    owner_cards = steps_by_parent.get(owner, [])
    owner_resources = sorted({resource for card in owner_cards for resource in card.get("resource_requirements", []) if isinstance(resource, str)})
    bindings = []
    for binding in bindings_by_case.get(cid, []):
        key = binding["key"]
        registered = commands.get(key)
        bindings.append({
            "frozen": binding,
            "current_command_revision": commands_doc["revision"],
            "current_registered_state": registered.get("state") if isinstance(registered, dict) else None,
            "current_registered_argv": registered.get("argv") if isinstance(registered, dict) else None,
            "current_registered_case_selector": selector_match(registered, owner, cid),
            "registered_key_exists": isinstance(registered, dict),
        })
    cases.append({
        "id": cid,
        "title": case["title"],
        "final_owner_task": owner,
        "related_wbs_ids": case.get("wbs_ids", []),
        "mode": case["mode"],
        "frozen_status": case.get("status"),
        "effective_accepted": False,
        "mandatory_gate": case.get("mandatory_gate"),
        "assertions": case.get("assertions", []),
        "evidence_required": case.get("evidence_required", []),
        "setup": case.get("setup", []),
        "actions": case.get("actions", []),
        "expected": case.get("expected", []),
        "command_keys": case.get("command_keys", []),
        "exact_formal_entry_templates": bindings,
        "missing_or_unbound_keys": [b["frozen"]["key"] for b in bindings if not b["current_registered_case_selector"] or b["current_registered_state"] != "BOUND"],
        "owner_card_resource_requirements": owner_resources,
        "owner_final_card_status": state.get(owner + "-99", {}).get("status", "NOT_STARTED"),
        "owner_parent_dependencies": next((t.get("depends_on", []) for t in tasks_doc["tasks"] if t["task_id"] == owner), []),
        "resource_lane": "local_fixture" if case["mode"] == "FIXTURE" else ("windows_and_service" if case["mode"] == "LIVE_WINDOWS_AND_SERVICE" else ("windows" if case["mode"] == "LIVE_WINDOWS" else "service")),
    })
mode_counts = {}
for case in cases:
    mode_counts[case["mode"]] = mode_counts.get(case["mode"], 0) + 1
parent_status_counts = {}
for parent in parents:
    s = parent["actual_final_card_status"]
    parent_status_counts[s] = parent_status_counts.get(s, 0) + 1
top_eligible = []
for card in sorted(plan_rows, key=lambda row: row.get("priority", 999999)):
    s = state.get(card["id"], {}).get("status", "NOT_STARTED")
    if s not in ("ACCEPTED", "BLOCKED"):
        deps = card.get("dependencies", [])
        if all(state.get(dep, {}).get("status") == "ACCEPTED" for dep in deps):
            top_eligible.append({"step_id": card["id"], "status": s, "priority": card.get("priority"), "dependencies": deps})
report = {
    "schema": "researchos.formal-resource-readiness.readonly.v1",
    "authority": "Current local snapshot; not an acceptance receipt or executable authorization.",
    "input_refs": refs,
    "snapshot": {
        "checkpoint_revision": checkpoint_doc.get("revision"),
        "checkpoint_head": checkpoint_doc.get("head"),
        "checkpoint_registered_failure_origin_count": len(checkpoint_doc.get("failure_counters", [])),
        "checkpoint_blocked_resources_count": len(checkpoint_doc.get("blocked_resources", [])),
        "step_state_record_count": len(state_rows),
        "commands_revision": commands_doc.get("revision"),
        "formal_accepted_count": checkpoint_doc.get("current_effective_formal_status", {}).get("formal_cases_accepted"),
        "formal_accepted_ids": checkpoint_doc.get("current_effective_formal_status", {}).get("accepted_case_ids"),
        "parent_tasks_accepted_checkpoint_strings": checkpoint_doc.get("parent_tasks_accepted"),
    },
    "counts": {
        "parents": len(parents),
        "parent_final_card_statuses": parent_status_counts,
        "cases": len(cases),
        "case_modes": mode_counts,
        "frozen_formal_command_bindings": len(formal_bindings),
        "current_registered_commands": len(commands),
        "formal_cases_newly_accepted_by_this_report": 0,
    },
    "parent_tasks": parents,
    "formal_cases": cases,
    "formal_gate_policy": cases_doc.get("gate_policy"),
    "formal_global_evidence": cases_doc.get("global_evidence"),
    "task_packet_readonly_next_entry": {
        "actual_call_made": False,
        "argv_template_exact_cli": [PINNED_PYTHON, "-I", "-S", "-X", "utf8", files["task_packet_source"].as_posix(), "--plan", files["plan"].as_posix(), "next", "--state", files["step_state"].as_posix()],
        "derived_eligible_priority_head": top_eligible[:10],
        "independent_review_required_for_each_plan_card": all(card.get("handoff", {}).get("independent_review_required") is True for card in plan_rows),
        "actual_task_packet_output": None,
    },
    "desktop169_go3": {
        "scope_built": True,
        "scope_registration_ref": refs["desktop_scope"],
        "resume_ref": refs["desktop_resume"],
        "resume_state": desktop_resume_doc.get("state"),
        "independent_scope_review_result": None,
        "actual_development_qualification_result": None,
        "formal_case_acceptance_result": None,
    },
    "b01": {
        "conclusion_ref": refs["b01_conclusion"],
        "verdict": b01_doc.get("verdict"),
        "strict_live_provider_upper_bound_established": False,
        "model_or_gateway_request_made_by_this_report": False,
        "applies_to": "Genuine billable provider LIVE qualification, when invoked; local fixture work remains separately eligible.",
    },
    "source_authority": {
        "ref": refs["source_authority"],
        "record": source_authority_doc,
        "fresh_compilation_or_cases_accepted_by_this_report": False,
    },
    "current_spec": current_spec_doc,
    "interpretation": {
        "parent_gate_ledger_is_stale_projection": True,
        "formal_case_requirements_is_stale_projection": True,
        "registered_selector_does_not_prove_assertions_or_required_mode": True,
        "accepted_parent_does_not_imply_any_formal_case_accepted": True,
        "fixture_cannot_substitute_live": True,
        "no_case_execution_in_this_report": True,
        "no_parent_acceptance_in_this_report": True,
    },
    "read_only_local_failure_origins": ["failure-origin-01.json", "failure-origin-02.json"],
    "unknowns": {
        "task_packet_actual_result": None,
        "desktop169_go3_actual_result": None,
        "current_live_provider_billable_upper_bound": None,
        "current_cases_pass_by_required_mode": None,
    },
}
dump(OWN / "report.json", report)
accepted = [p["task_id"] for p in parents if p["actual_final_card_status"] == "ACCEPTED"]
missing = [c["id"] for c in cases if c["missing_or_unbound_keys"]]
live = [c["id"] for c in cases if c["mode"] != "FIXTURE"]
lines = [
    "# v2.4 正式用例资源就绪盘点（只读）",
    "",
    f"当前快照：checkpoint rev {report['snapshot']['checkpoint_revision']}，commands rev {report['snapshot']['commands_revision']}；父任务终卡 ACCEPTED {len(accepted)}/22：{', '.join(accepted)}。冻结42个正式case，当前有效接受0；本报告新增接受0。",
    "",
    "Desktop169+Go3 的完整范围已构建，但独立scope复核与真实开发资格结果仍为 NULL；它不能替代42个正式case。B01 当前没有同路由可计费 token/思考输出的严格费用上限证据，只限制需要真实付费模型调用的 LIVE 资格；本机 FIXTURE 可继续。",
    "",
    f"冻结case模式：{json.dumps(mode_counts, ensure_ascii=False, sort_keys=True)}。非 FIXTURE case：{', '.join(live)}。42项逐一的owner、冻结断言、证据和63条精确命令模板见 report.json/formal_cases。",
    "",
    f"当前命令登记 rev {commands_doc['revision']}；至少一个冻结模板缺少可用精确selector的case：{', '.join(missing)}。selector存在只说明调度入口，不能证明断言运行、要求的 LIVE 模式或独立签收。",
    "",
    "Root 下一次可对当前 plan/state 运行 task_packet.py next，只读得到实际任务包。按同一算法的静态筛选，W05-99（IN_PROGRESS）优先，W09-99（NOT_STARTED）随后；本报告没有调用 task_packet。W09 依赖的 W03/W07 已 ACCEPTED，W09 本地证据索引和 FIXTURE 分支可独立推进。W06、W08、W12 等父任务仍有 W05/W06 依赖，不能越门签收。",
    "",
    "正式验收必须执行冻结命令模板并保存原始运行回执、版本/输入、断言结果、独立复核和签收。现有 W04/W07 父门登记与42个正式case当前有效接受0并存，不能以父门文字推断case PASS。LIVE_SERVICE A05 涉及外部来源，不自动等于模型 B01；A08/A13/A14 等实际 provider 调用需各自核费用门。",
    "",
    "本盘点只做本机文件读取。没有运行产品、CLI/桌面、浏览器、Go/Node/Git、模型、SDK、task_packet 或正式case，也没有修改canonical。两次本地只读汇总脚本形状假设失败，各有独立 failure-origin 原始回执；不会重试或重置计数。",
]
(OWN / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({"report": pin(OWN / "report.json"), "markdown": pin(OWN / "report.md"), "parents": len(parents), "cases": len(cases), "bindings": len(formal_bindings), "accepted": accepted, "next_static": top_eligible[:2]}, ensure_ascii=False))
