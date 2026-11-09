from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("D:/作品集/ResearchOS/research-os")
OWN = ROOT / "execution/v2.4/receipts/W05/W05-99/f08_next_ready_gates_readonly_codex/ad2dc8822ba647b79b84664f8ee93078"
PACKAGE = Path("D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4")
ACTOR = "codex:/root/f08_i17_binding_impl"
READS = []

def ref(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    value = {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    READS.append(value)
    return value, raw

def read_json(path, expected=None):
    pinned, raw = ref(path)
    if expected is not None and pinned["sha256"] != expected:
        raise ValueError("Pinned immutable input drift: " + pinned["path"])
    return pinned, json.loads(raw)

def write(name, value):
    path = OWN / name
    if path.exists():
        raise ValueError("New own artifact already exists: " + name)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    return ref(path)[0]

def verify(reference):
    actual, raw = ref(reference["path"])
    return {"original_ref": reference, "actual_ref": actual,
            "match": actual["sha256"] == reference["sha256"] and
                     ("bytes" not in reference or actual["bytes"] == reference["bytes"])}

point = json.loads((OWN / "point-in-time.json").read_bytes())
plan_ref, plan = read_json(PACKAGE / "contracts/execution.plan.json", "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17")
tasks_ref, tasks = read_json(PACKAGE / "contracts/tasks.json", "37e1bc901a8843b91ae750c90164ef58560bccc50fa011908b5f3c30809cb8d4")
acceptance_ref, acceptance = read_json(PACKAGE / "contracts/acceptance.json", "ae8aa1ce632aecce595b2adbcb05fd73aa7360b8fd4186fcef6fd5e7872caa66")
index_ref, index = read_json("execution/v2.4/receipts/W05/W05-99/integration_codex/configuration-main-closure-r284/formal-index.json", "0e9c052b3ddb2abf138d818d87b0488cf4835717e52253fc035a997a3a1118f3")
scope_ref, scope = read_json("execution/v2.4/receipts/W05/W05-99/integration_codex/parallel-source-and-go3-r320/w09_source_scope.json", "e0b18f962807912e7c1acbfda31a4051ae061f86fbb4d996939d8643e4b97500")
review_ref, review = read_json("execution/v2.4/receipts/W09/W09-99/test_only_causal_exact4_source_independent_review_codex/09742ae11ada43268282343cc78c6e0d/review.json", "227a4a32deace4f6212ead2b36c6c6c5ef896eacbacd9615cdb7ecee2630d344")
finite = ROOT / "execution/v2.4/receipts/W09/W09-99/finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0"
hdf_ref, hdf = read_json(finite / "handoff.json")
mf_ref, mf = read_json(finite / "manifest.json", "14845c9ac15153481dd051fd7be2c996dce79c5807507fd33fbcbe6ec87c2b0d")
members = [verify(v) for v in mf["members"]]
hdf_children = [verify(hdf[k]) for k in ["spec_ref", "finite_roster_ref", "conditions_ref", "grant_false_ref"]]
author_hdf = verify(review["author_handoff_ref"])
author_mf = verify(review["author_manifest_ref"])
cards = {row["id"]: row for row in plan["steps"]}
accepted = set(point["raw_accepted_card_ids"])
owners = {row["task_id"]: row for row in index["owners"]}
parents = []
for idx, row in enumerate(plan["steps"]):
    if row["phase"] != "PARENT_FINAL_GATE":
        continue
    owner = owners[row["parent_task"]]
    raw_status = "ACCEPTED" if row["id"] in accepted else ("IN_PROGRESS" if row["id"] == "W05-99" else "NOT_STARTED")
    unmet = [{"id": dep, "observed_raw_status": "IN_PROGRESS" if dep == "W05-99" else
              ("BLOCKED" if dep in ["W10-02", "W11-02", "W13-03", "W14-01"] else "NOT_STARTED")}
             for dep in row["dependencies"] if dep not in accepted]
    parents.append({"task_id": row["parent_task"], "card_id": row["id"], "observed_raw_status": raw_status,
                    "final_owned_case_ids": owner["owned_case_ids"], "reported_formal_integrity": owner["integrity"],
                    "effective_accepted_case_ids": owner["accepted_case_ids"], "reported_reasons": owner["reasons"],
                    "unmet_raw_dependencies": unmet, "plan_pointer": "/steps/" + str(idx),
                    "formal_evidence_pointer": "/owners/" + str(index["owners"].index(owner))})
cases = [{k: row[k] for k in ["case_id", "final_owner_task", "required_mode", "status", "reasons"]} for row in index["cases"]]
w09 = cards["W09-99"]
shared = {"card_id": "W09-99", "final_owned_case_ids": ["C19", "A06"], "affected_nonowned_case_not_claimed": ["C02"],
          "exact_original_refs": {"registered_source_scope": scope_ref, "source_independent_review": review_ref,
                                  "author_handoff": author_hdf["actual_ref"], "author_whole_manifest": author_mf["actual_ref"],
                                  "controller_handoff": hdf_ref, "controller_whole_manifest": mf_ref,
                                  "controller_spec": hdf_children[0]["actual_ref"], "finite_roster": hdf_children[1]["actual_ref"],
                                  "implementation_conditions": hdf_children[2]["actual_ref"], "false_root_grant": hdf_children[3]["actual_ref"]},
          "source_commit": hdf["source_commit"], "source_base": hdf["source_parent"],
          "all_actual_cases": hdf["all_actual_cases"], "current_parent_accepted": False,
          "formal_increment_created": 0, "CLI43_or_F08_execution_dependency_for_this_preparation": False}
candidates = [
 dict(shared, candidate_id="W09-NEXT-01", readiness="READY_FOR_NONAUTHOR_READONLY_CONTROLLER_REVIEW",
      smallest_next_action="对封存 controller/case_worker/common/launch/DEBUG_PROCESS helper、固定 roster 和条件做非作者只读复审。",
      why_can_advance="W09 的四文件测试候选已有独立静态复审、无 REQUEST 且 writer 已停止；controller 准备包已存在且 hash 可核对。可独立消除下一运行门的 controller 审查缺口。",
      actual_unpassed_conditions=["controller 及 DEBUG_PROCESS descendant/nested Job 尚无独立复审；全部编译和目标调用 NOT_RUN。",
       "Root true execution grant、完整 GOROOT/module-cache membership 与独立资源 hash allowlist 未提供。",
       "15000 秒 whole-wall 提案相对先前 9000 仍待 Root 决定。",
       "DB 证明只含部分四表 JSON multiset；typeof、implicit rowid、whole DB、8 新 domain 与 6 原 domain closed-copy 缺口保持 OPEN。",
       "49 最大调用、预期 89 RUN/PASS 和 49 leaf 是预期清单，不能计作实际通过；六条正式 handler 路由/模式/独立签收未完成。"]),
 dict(shared, candidate_id="W09-NEXT-02", readiness="PREPARE_RESOURCE_FREE_EXECUTION_SCOPE_AFTER_W09_NEXT_01",
      smallest_next_action="在 controller 独审后准备独立 Root scope：固定 cd0 source/full input closure、45 resource-free 调用，四个 OS 调用分开 HOLD；不由本回执发放执行权。",
      why_can_advance="封存 controller 已把 45 个资源无关调用与 4 个 OS 依赖调用分开，前者不要求模型、SDK、网络或 CLI43/F08 运行结果；可先完成本地资源目录和有限授权准备。",
      actual_unpassed_conditions=["W09-NEXT-01 必须先闭合；false Root grant 不能执行。",
       "资源目录、完整编译输入闭包、fresh output/nonce、实际输入 currentness、limits 审查和真实 Root source/execution lease 尚未建立。",
       "cd0 候选以 2cdb 为基线，本回执 CP329 Main 是 a510；当前 Main/handler source integration 并未授权或证明。",
       "本候选不能直接签收 W09-99；其 raw plan 依赖均历史 ACCEPTED，但 W07 当前 A05 仍 NEEDS_REVALIDATION。",
       "资源无关 45 调用也仍需真实 native/raw 运行及非作者签收；4 OS 调用缺真实 symlink/junction capability，保持 HOLD/NOT_RUN。"])
]
output = {
 "schema": "researchos.next-ready-gates.readonly.v1", "actor": ACTOR,
 "status": "READONLY_CP329_PREPARATION_SEALED_NO_EXECUTION_OR_ACCEPTANCE",
 "point_in_time": {"checkpoint_revision": 329, "ownership_revision": 157, "Main_head": point["head"],
                   "registered_failure_counter_rows": 481, "checkpoint_ref": point["checkpoint_ref"],
                   "Root_r330_progress_not_observed_or_inferred": True},
 "current_progress": {"parent_tasks_total": len(parents), "formal_cases_total": len(cases),
                      "raw_ACCEPTED_cards": len(accepted), "historical_parent_registrations": 6,
                      "reported_effective_formal_cases_accepted": index["formal_cases_accepted"],
                      "accepted_case_ids": index["accepted_case_ids"],
                      "formal_index_integrity": index["integrity"], "independent_native_gate_acceptance_created": False},
 "field_locations": {"checkpoint": ["revision", "head", "failure_counters", "accepted_steps", "parent_tasks_accepted",
                        "current_effective_formal_status", "work_in_progress.current_formal_index_ref"],
                     "step_state": ["steps[].id", "steps[].status", "steps[].evidence", "steps[].executor_id", "steps[].verifier_id", "steps[].accepted_at"],
                     "frozen_plan": ["steps[].id", "steps[].parent_task", "steps[].dependencies", "steps[].formal_final_cases", "steps[].verification_commands"],
                     "reported_formal_index": ["owners[].integrity", "owners[].owned_case_ids", "cases[].status", "cases[].reasons", "input_hashes"],
                     "registered_481_meaning": "len(checkpoint.failure_counters), observed directly; not derived from a command registry revision"},
 "status_reference_limits": ["CP329 continues to reference r284 reported formal index; this receipt reads it, does not execute a new formal validity derivation.",
   "Its W04/W07 NEEDS_REVALIDATION reasons name adapters/runtime/bridge_windows.go; stale standalone ledger named internal/domain/runtime_broker_windows.go and had 39 cards/W07 NOT_STARTED.",
   "Current raw parent states come from previously observed CP329 accepted IDs and step_state reads preserved in tool-observations, not stale ledger/frontier.",
   "Parent requested no checkpoint reread during concurrent Root CAS330; no CP330/current-future state is claimed.",
   "No current unsigned successful native other-parent evidence was proven reusable by this limited read; W09 source/controller preparation is NOT_RUN."],
 "source_refs": {"frozen_plan": plan_ref, "frozen_tasks": tasks_ref, "frozen_acceptance": acceptance_ref,
                 "reported_formal_index": index_ref, "point_in_time_observation": ref(OWN / "point-in-time.json")[0]},
 "parents": parents, "formal_cases": cases, "next_ready_candidates": candidates,
 "deferred": [
  {"cards": ["W04-99", "W07-99"], "why": "历史原始回执存在，但当前 index 为 NEEDS_REVALIDATION；fresh context/version vector、适用 runtime 源码和独立复验/签收缺失，不能作为当前未签收成功证据直接复用。", "ref": index_ref},
  {"cards": ["W06-99", "W08-99", "W12-99", "W18-99"], "why": "仍有 W05/W06/W12 父门前置依赖；已接受构造子卡不能替代父门拥有的正式 case。", "ref": plan_ref},
  {"cards": ["W10-02", "W10-99"], "why": "已读状态 BLOCKED：zero-cap AppContainer 中 Bash 原始 0xC0000142/NtCreateDirectoryObjectDenied 0xC0000022；兼容隔离 Bash/独审有限 fallback 未证明，不从旧工具安装状态推定资源已备。", "evidence_basis": "original CP329 tool-observations nr_branches_1"},
  {"cards": ["W11-02", "W11-99"], "why": "真实 provider eval/reuse_selection、独立标签、授权冻结和 live 服务资格未闭合；source/fixture slice 不签收 LIVE。", "evidence_basis": "original CP329 tool-observations nr_branches_1"},
  {"cards": ["W13-03", "W13-99", "W14-01"], "why": "Desktop15 HOLD 和 fresh43 已由 Root 当前支路处理；不产生并行重跑或假定资源授权。", "evidence_basis": "parent active-task instruction"}
 ],
 "execution": {"dispatcher": 0, "task_packet_show": 0, "formal_reader_run": 0, "Go": 0, "SQL": 0, "network": 0, "SDK_MODEL": 0, "native_product_helper": 0, "source_adoption": 0, "canonical_writes": 0},
 "task_packet_location": (PACKAGE / "tools/task_packet.py").as_posix(),
 "task_packet_show_disposition": "Not needed after frozen plan/card read; avoid a new state-consistency query during Root CAS330.",
 "new_failed_tool_invocations": 0, "historical_failure_rows_modified": 0,
 "writer_status_after_seal": "STOPPED"
}
assert len(plan["steps"]) == 71 and len(parents) == 22 and len(cases) == 42
assert len({c["case_id"] for c in cases}) == 42 and len(candidates) <= 8
assert len(accepted) == 40 and index["formal_cases_accepted"] == 0
assert all(row["match"] for row in members + hdf_children + [author_hdf, author_mf])
assert len(members) == mf["member_count"] == 43
assert review["requested_changes"] == [] and review["source_accepted"] is False
assert hdf["resource_free_call_count"] == 45 and hdf["OS_dependent_call_count"] == 4 and hdf["all_actual_cases"] == "NOT_RUN"
assert hdf["resource_free_call_count"] + hdf["OS_dependent_call_count"] == hdf["future_max_calls"]
result_ref = write("next-ready-gates.json", output)
audit_ref = write("static-read-audit.json", {"schema": "researchos.next-ready-gates-static-read-audit.v1",
 "actor": ACTOR, "time_utc": datetime.now(timezone.utc).isoformat(), "status": "READS_AND_METADATA_ONLY",
 "immutable_read_refs": READS[:], "controller_manifest_members_verified": len(members),
 "controller_manifest_member_checks": members, "handoff_selected_refs_verified": hdf_children,
 "source_author_ref_checks": [author_hdf, author_mf],
 "checks": {"frozen_plan_SHA": True, "frozen_task_SHA": True, "frozen_acceptance_SHA": True,
 "22_parent_owners": True, "42_unique_formal_cases": True, "40_raw_ACCEPTED_cards_preserved": True,
 "0_effective_formal_acceptance_preserved": True, "candidates_max8": True,
 "W09_all_NOT_RUN_preserved": True, "controller43_members_exact": True, "45_plus4_equals49": True},
 "checkpoint_re_read": False, "target_or_controller_executed": False, "new_failure_origins": []})
print(json.dumps({"next_ready_ref": result_ref, "audit_ref": audit_ref, "candidate_ids": [c["candidate_id"] for c in candidates]}, ensure_ascii=False))

