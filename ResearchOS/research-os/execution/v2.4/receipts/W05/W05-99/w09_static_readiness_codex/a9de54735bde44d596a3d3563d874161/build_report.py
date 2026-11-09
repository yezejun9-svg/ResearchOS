"""Read-only W09-99 task-card and formal-selector map; no product command execution."""
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode = True

REPO = Path("D:/作品集/ResearchOS/research-os")
PKG = Path("D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4")
OWN = Path(__file__).resolve().parent
PYTHON = "C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def ref(path):
    b = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

files = {
    "plan": PKG/"contracts/execution.plan.json",
    "tasks": PKG/"contracts/tasks.json",
    "acceptance": PKG/"contracts/acceptance.json",
    "task_packet": PKG/"tools/task_packet.py",
    "W09-01_card": PKG/"tasks/steps/W09-01.md",
    "W09-02_card": PKG/"tasks/steps/W09-02.md",
    "W09-99_card": PKG/"tasks/steps/W09-99.md",
    "data_contracts": PKG/"03_DATA_CONTRACTS.md",
    "component_decisions": PKG/"09_COMPONENT_DECISIONS.md",
    "checkpoint": REPO/"execution/v2.4/checkpoint.json",
    "step_state": REPO/"execution/v2.4/step_state.json",
    "current_spec": REPO/"execution/v2.4/current_spec.json",
    "commands_v24": REPO/"execution/v2.4/commands.json",
    "commands_legacy": REPO/"execution/commands.json",
    "dispatcher": REPO/"execution/command_dispatcher/dispatch.py",
    "w0901_review": REPO/"execution/v2.4/receipts/W09/W09-01/independent_review.json",
    "w0902_review": REPO/"execution/v2.4/receipts/W09/W09-02/independent_review.json",
    "w0902_post_review": REPO/"execution/v2.4/receipts/W09/W09-02/post_review_actions_round1.json",
    "formal_resource_report": REPO/"execution/v2.4/receipts/W05/W05-99/formal_resource_readiness_codex/b1f8c3a776b8438db15cd854fa5d933d/report.json",
    "b01_conclusion": REPO/"execution/v2.4/receipts/W05/W05-99/provider_budget_resource_readonly_codex/budget-4d5e48bb6b764a34ac537990b10290f2/conclusion.json",
    "evidence_origin": REPO/"internal/domain/evidence_origin.go",
    "evidence_verification": REPO/"internal/domain/evidence_verification.go",
    "retrieval_service": REPO/"internal/domain/retrieval.go",
    "retrieval_local": REPO/"internal/domain/retrieval_local.go",
    "retrieval_adapter": REPO/"adapters/retrieval/local.go",
    "retrieval_tests": REPO/"internal/domain/retrieval_test.go",
    "w0901_tests": REPO/"internal/domain/evidence_w0901_test.go",
    "w0902_tests": REPO/"internal/domain/evidence_w0902_test.go",
    "w0901_handler": REPO/"tests/evidence/check/main.py",
    "legacy_retrieval_handler": REPO/"ops/ci/retrieval.py",
    "migration_0007": REPO/"migrations/sqlite/0007_retrieval.sql",
    "migration_0009": REPO/"migrations/sqlite/0009_retrieval_root_identity.sql",
}
refs = {name: ref(path) for name,path in files.items()}
plan = read(files["plan"])
tasks = read(files["tasks"])
acceptance = read(files["acceptance"])
state = read(files["step_state"])
commands = read(files["commands_v24"])
legacy = read(files["commands_legacy"])
cp = read(files["checkpoint"])
pointer = read(files["current_spec"])
b01 = read(files["b01_conclusion"])
formal = read(files["formal_resource_report"])
w09 = next(t for t in tasks["tasks"] if t["task_id"]=="W09")
cards = [s for s in plan["steps"] if s["parent_task"]=="W09"]
state_map = {s["id"]:s for s in state["steps"]}
cases = [c for c in acceptance["cases"] if c["id"] in ("C19","A06","C02")]
frozen_bindings = [b for b in tasks["verification_command_selection"]["formal_case_bindings"] if b["task_id"]=="W09"]

def selected(entry, task, check=None, case=None):
    if not isinstance(entry,dict) or entry.get("state")!="BOUND":
        return False
    selectors = entry.get("selectors",{})
    for name,value in (("task_id",task),("check_id",check),("case_id",case)):
        if value is not None and value not in selectors.get(name,[]) and "*" not in selectors.get(name,[]):
            return False
    return True

all_entries = []
for card in cards:
    for binding in card["verification_commands"]:
        key = binding["key"]
        task = binding.get("task_id","W09")
        check = binding.get("check_id")
        case = binding.get("case_id")
        v24 = commands["commands"].get(key)
        old = legacy["commands"].get(key)
        all_entries.append({
            "card": card["id"],
            "frozen": binding,
            "v24_key_state": v24.get("state") if isinstance(v24,dict) else None,
            "v24_exact_selector_bound": selected(v24,task,check,case),
            "legacy_exact_selector_bound": selected(old,task,check,case),
            "auto_registry_resolution": "v2.4" if key in commands["commands"] and
                pointer.get("pointer")=="v2.4" and
                pointer.get("plan_sha256")==commands.get("plan_sha256") else "v2.0",
        })
assert len(all_entries)==8 and len(frozen_bindings)==4
required = {s["id"]:{"status":state_map.get(s["id"],{}).get("status","NOT_STARTED"),
                      "evidence":state_map.get(s["id"],{}).get("evidence",[]),
                      "verifier_id":state_map.get(s["id"],{}).get("verifier_id"),
                      "accepted_at":state_map.get(s["id"],{}).get("accepted_at")}
            for s in cards}
dependencies = {sid:state_map.get(sid,{}).get("status","NOT_STARTED")
                for sid in ("W09-01","W09-02","W17-01","W03-99","W07-99")}
owned = [c for c in cases if c["final_owner_task"]=="W09"]
related = [c for c in cases if c["final_owner_task"]!="W09"]
task_packet_show = [PYTHON,"-I","-S","-X","utf8",str(files["task_packet"]),
                    "--plan",str(files["plan"]),"show","W09-99","--state",str(files["step_state"])]
report = {
    "schema":"researchos.w09-99-static-readiness.v1",
    "stage":"READ_ONLY_PREPARATION",
    "snapshot_refs":refs,
    "snapshot":{"checkpoint_revision":cp["revision"],"head":cp["head"],
                "step_state_sha256":refs["step_state"]["sha256"],
                "commands_v24_revision":commands["revision"],
                "formal_cases_effectively_accepted":cp["current_effective_formal_status"]["formal_cases_accepted"]},
    "task":{"task_id":"W09","title":w09["title"],"parent_dependencies":w09["depends_on"],
            "owned_formal_case_ids":w09["owned_acceptance_ids"],
            "related_case_ids":w09["acceptance_ids"],
            "development_checklist":w09["development_checklist"],
            "parent_gate_checks":w09["task_gate_checks"],
            "cards":cards},
    "actual_card_status":required,
    "dependency_status":dependencies,
    "W09_99_static_eligible":all(value=="ACCEPTED" for value in dependencies.values())
        and required["W09-99"]["status"] in ("NOT_STARTED","IN_PROGRESS"),
    "task_packet":{"actual_call_made":False,"show_argv":task_packet_show,
                   "next_argv":[PYTHON,"-I","-S","-X","utf8",str(files["task_packet"]),
                                "--plan",str(files["plan"]),"next","--state",str(files["step_state"])],
                   "show_result":None,
                   "next_is_expected_to_prefer_W05_99_in_progress":True,
                   "notes":"Global --plan precedes show/next; --state belongs to subcommand. The tool validates accepted evidence hashes, selects, but does not accept."},
    "formal_cases":{
        "owned":owned,"related_other_owner":related,
        "frozen_case_bindings":frozen_bindings,
        "all_card_command_entries":all_entries,
        "required_mode":{"C19":"FIXTURE","A06":"FIXTURE","W09-G01":"FIXTURE","W09-G02":"LIVE_WINDOWS"},
        "formal_accepted_delta":0,
    },
    "registry":{"pointer":pointer.get("pointer"),"v24_plan_matches_pointer":pointer.get("plan_sha256")==commands.get("plan_sha256"),
                "v24_revision":commands["revision"],
                "finding":"All six W09-99 frozen entry templates and the W09-02 subcard template lack their exact selectors in the active v2.4 registry; W09-01 remains bound. v2.4 key presence takes precedence over legacy BOUND entries. Old handlers/Go tests exist, but formal dispatch is not bound.",
                "current_v24_entries":{key:commands["commands"].get(key) for key in ("test.retrieval","test.research.fixture","test.security")},
                "legacy_entries":{key:legacy["commands"].get(key) for key in ("test.retrieval","test.research.fixture","test.security")}},
    "static_source_map":[
        {"requirement":"Evidence origin, observed/simulated separation, independent roots and stale propagation","files":["evidence_origin","evidence_verification","retrieval_tests","w0901_tests"],"limit":"W09-01 independent review left some origin hash/kind legs unasserted; do not inherit a formal C19 PASS."},
        {"requirement":"Authorized local snapshots, hashes, revocation and FTS/bounded-scan fallback","files":["retrieval_service","retrieval_local","retrieval_adapter","migration_0007","migration_0009","retrieval_tests","w0902_tests"],"limit":"W09-02 review and post-review actions record corrected cache-key claims and remaining hard-link/client-projection limitations; actual W09-99 must use current inputs."},
        {"requirement":"Current W09-01 selector handler","files":["w0901_handler","w0901_tests","w0902_tests"],"limit":"Handler explicitly serves W09-01 only, and current v2.4 test.retrieval selector is only W09-01."},
        {"requirement":"Historical W09-G01/G02, C19/A06 named Go assertions","files":["legacy_retrieval_handler","retrieval_tests"],"limit":"Legacy execution/commands.json selectors and tests do not bind the active v2.4 registry; the v2.4 research/security handlers serve other cards."},
    ],
    "known_acceptance_gaps":[
        "Register exact W09-G01 and W09-G02 selectors with real handlers and nonempty W09-G01/W09-G02 assertion IDs at required FIXTURE/LIVE_WINDOWS modes.",
        "Register both C19 frozen selectors (test.research.fixture and test.retrieval) with actual W09 C19-01/02/03 implementation and evidence graph/simulated/unknown cases.",
        "Register both A06 frozen selectors (test.retrieval and test.security) with actual W09 A06-01/02/03 implementation and authorized local file/revoke/fallback proof.",
        "Review accepted W09-01/02 limitations and W09-02 post-review corrections against current head; do not rerun accepted cards without changed-input reason. Keep C02 with W17 final owner.",
        "Resolve Sirchmunk priority qualification or document the prescribed FTS/rg substitute; NOT_SELECTED is not Sirchmunk qualification.",
        "Independently verify parent gates, two owned cases, input hashes and acceptance receipts before any W09-99 state change.",
    ],
    "resource_boundary":{"fixture_cases_can_progress_without_paid_provider":True,
                         "W09_G02_needs_real_local_Windows_file_checks":True,
                         "provider_live_or_B01_required_for_W09":False,
                         "b01_verdict":b01["verdict"],
                         "b01_ref":refs["b01_conclusion"]},
    "source_acceptance":False,"formal_increment":0,"product_or_task_packet_executed":False,
}
out = OWN/"report.json"
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
summary = [
    "# W09-99 静态接续卡",
    "",
    "当前 W09-01、W09-02、W17-01、W03-99、W07-99 均已在 step_state 登记 ACCEPTED，W09-99 未登记，依赖上可推进；父任务 W09 和正式 C19/A06 仍未接受。C02 只是关联回归，最终 owner 为 W17。",
    "",
    "W09-99 的冻结入口共 6 条：W09-G01/G02 各 1 条，C19 两条，A06 两条；W09 子卡另有 2 条。当前 v2.4 命令登记包含同名 key，却没有这些 W09-99 的精确 selectors。dispatcher 在 current_spec=v2.4 且 plan hash 对齐时优先选 v2.4，不能回退调用旧版 W09 同名 handler 视作正式验证。",
    "",
    "已有 domain Evidence/retrieval/local-root/FTS 与 Go 断言源码；W09-01/02 的独立复核留有限制，且 W09-02 post-review 记录了纠正。Root 下一步先按冻结 task_packet.py 的 show W09-99 实际读包，再由登记 owner 让当前 v2.4 入口能真实运行冻结断言与 G02 本机 Windows 检查，独立复核后才签收。task_packet 未在本盘点中执行。",
    "",
    "C19、A06 是 FIXTURE；W09-G02 需要真实本机 Windows 文件验证。B01 严格费用门只挡付费 provider LIVE，不挡这些本地工作。Sirchmunk 当前仅 NOT_SELECTED；需固定源码资格或明确采用已规定 FTS/rg 替代并留证。",
    "",
    "本报告只读，没有运行 Git、task_packet、dispatcher、Go、CLI、provider 或产品，也没有领取 lease、修改源码或 canonical；新增正式接受数 0。",
]
(OWN/"report.md").write_text("\n".join(summary)+"\n",encoding="utf-8")
print(json.dumps({"report":ref(out),"summary":ref(OWN/"report.md"),
                  "status":required["W09-99"]["status"],"eligible":report["W09_99_static_eligible"],
                  "entries":len(all_entries),"all_unbound":all(not x["v24_exact_selector_bound"] for x in all_entries)},ensure_ascii=False))
