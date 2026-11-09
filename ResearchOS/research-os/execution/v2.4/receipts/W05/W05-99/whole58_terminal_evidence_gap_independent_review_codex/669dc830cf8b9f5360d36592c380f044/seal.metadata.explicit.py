from pathlib import Path
import hashlib, json, re

BASE = Path(__file__).resolve().parent
seed = json.loads((BASE / "review.seed.json").read_bytes())
ROOT = Path(seed["project_root"])
SPEC = Path(seed["package_root"])
REVIEWER = seed["reviewer"]
refs = {}

def pin(p):
    p = Path(p); b = p.read_bytes()
    return {"path": str(p), "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}

def read(label, p):
    r = pin(p); refs[label] = r
    b = Path(p).read_bytes()
    return json.loads(b) if str(p).endswith(".json") else b.decode("utf-8")

def save(name, data):
    p = BASE / name
    if p.exists():
        raise ValueError("Own immutable output already exists: " + name)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return pin(p)

plan = read("execution_plan", SPEC/"contracts/execution.plan.json")
tasks = read("parent_tasks", SPEC/"contracts/tasks.json")
cases = read("formal_acceptance_contract", SPEC/"contracts/acceptance.json")
card = read("W05_99_card", SPEC/"tasks/steps/W05-99.md")
read("execution_goal", SPEC/"08_AGENT_EXECUTION_GOAL.md")
read("formal_acceptance_reading_view", SPEC/"06_ACCEPTANCE_TESTS.md")
read("product_reading_view", SPEC/"14_CLI_DESKTOP_PRODUCT.md")
read("desktop_blueprint", SPEC/"19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md")
packet = read("task_packet_source_only", SPEC/"tools/task_packet.py")

P05 = ROOT/"execution/v2.4/receipts/W05/W05-99"
P13 = ROOT/"execution/v2.4/receipts/W13/W13-03"
public = P13/"fresh58_public_source_authority_codex/16e288f44f104376898cde4336c705a1"
pub_review = read("publication_independent_review", P13/"fresh58_public_source_publication_independent_review_codex/66b4835ecfe240cca4e481900d9897a7/review.json")
pub_mf = read("public58_manifest", public/"manifest.json")
for i, r in enumerate(pub_mf["entries"]):
    actual = pin(r["path"])
    if (actual["sha256"], actual["bytes"]) != (r["sha256"], r["bytes"]):
        raise ValueError("Frozen public metadata drift")
    refs["public58_member_"+str(i)] = actual
authority = read("public_source_authority", public/"current43-authority.json")
combined = read("combined58_source_set", public/"combined58-source-set.json")
source_review = read("source15_actual_independent_closure", P13/"desktop58_source_execution_independent_review_codex/a76cb528a87f45529adb3da26418eabb/review.json")
forward = read("actual_E2_forward_registration", P05/"integration_codex/desktop58-post-integration-r333-6cd1a3bb23fb45e1bcb26091d2b0a031/registration-audit.json")
cli_ns = P05/"cli58_successful_execution_independent_review_codex/83c89c410a1744b8b77d121fd44e5c5e"
cli_q = read("current58_CLI2_qualification", cli_ns/"qualification.json")
cli_review = read("current58_CLI2_independent_review", cli_ns/"review.json")
cli_result = read("current58_CLI2_actual_result", cli_q["evidence_refs"]["result_ref"]["path"])
cli_actual = []
for x in cli_result["stages"]:
    if x["label"] in ["case-00", "case-01"]:
        d = read("CLI2_actual_"+x["label"], x["result_ref"]["path"])
        cli_actual.append({"label":x["label"], "ref":refs["CLI2_actual_"+x["label"]], "argv":d["request"]["argv"], "cwd":d["request"]["cwd"], "timeout_seconds":d["request"]["timeout_seconds"], "actual_exit":d["actual_exit"], "scope":"Already independently qualified current58 exact held2; never a current whole suite grant"})

old38 = P05/"handler38_final_source_review_codex/a639cfcf998f4c7fb182db19c6788c3b"
whole_static = read("old_whole38_static_review", old38/"review.json")
whole_plan = read("old_whole38_selected_plan", old38/"execution_plan.json")
whole_map = read("old_whole38_static_mapping", old38/"whole38_static_map.json")
old_cohorts = read("old_whole38_separate_cohort_review", P05/"handler38_final_source_review_codex/1bfca99c7bd04ec7842ab2c810c35522/review.json")
read("old_whole38_integration_scope", P05/"handler38_main_integration_scope_review_codex/93e055d33951419a8607de84ccb10e9e/scope_review.json")
read("old_CLI5_scope_review", P05/"handler_cli_product_scope_independent_review_codex/e510a242-5d8f-484d-80f4-464580eed502/scope_review.json")
suitability = read("source15_import_suitability", P13/"desktop15_source_import_suitability_independent_review_codex/d2215541c83c463db77326ffb2077dd7/review.json")
read("original_source15_REQUEST_preserved", P13/"desktop_http_exact15_source_independent_review_codex/094badb378bf4323a24a5d8bb2c09ab1/source_review.json")
old_scope = read("old_Desktop58_scope_review_not_new_grant", P13/"desktop58_current_bound_scope_independent_review_codex/1c4ea6999d4d4437a0202c4e81ce581b/review.json")
desktop_ns = P13/"fresh58_desktop169_go3_revision_preparation_codex/736e757cdbc148a286c1d2426b8a7382"
desktop_hdf = read("Desktop172_preparation_handoff", desktop_ns/"handoff.json")
desktop_scope = read("Desktop172_preparation_scope", desktop_hdf["scope_ref"]["path"])
read("Desktop172_revision_contract", desktop_hdf["contract_ref"]["path"])
controller = read("Desktop172_controller_source_only", desktop_hdf["selected_refs"]["controller_ref"]["path"])
roster = read("Desktop172_original_finite_roster", desktop_scope["roster_ref"]["path"])

task_index = {x["task_id"]: x for x in tasks["tasks"]}
step_index = {x["id"]:x for x in plan["steps"]}
formal_by_id = {x["id"]:x for x in cases["cases"]}
w05 = task_index["W05"]
gaps = json.loads((BASE/"gap-table.json").read_bytes())

suite = {
    "schema":"researchos.whole58-suite-selector-gap-map.v1",
    "source_commit_current":cli_q["source_commit"],
    "whole58_test_suite_qualified":False,
    "current_full_suite_contract_state":"NOT_ESTABLISHED_IN_REVIEWED_FROZEN_INPUTS",
    "current_CLI2_actual_commands":cli_actual,
    "current_CLI2_exact_qualified_ids":cli_q["qualified_case_ids"],
    "old_whole38_plan_ref":refs["old_whole38_selected_plan"],
    "old_whole38_candidate":whole_plan["candidate"],
    "old_whole38_status":whole_plan["status"],
    "old_whole38_selected_batches":whole_plan["batches"],
    "old_whole38_go_graph_argv_suffix":whole_plan["capture"]["go_graph"],
    "old_whole38_held":whole_plan["held"],
    "old_formal_harness_rule":whole_plan["formal_harness"],
    "current_Desktop172_source_contract":{
        "controller_ref":refs["Desktop172_controller_source_only"],
        "scope_ref":refs["Desktop172_preparation_scope"],
        "roster_ref":refs["Desktop172_original_finite_roster"],
        "roster_counts":{"node_exact_leaves":len(roster["leaves"]),"regression_programs_or_exact_leaves":len(roster["regressions"]),"Go_original_assertions":len(roster["go_units"])},
        "Go3_selector":"^("+"|".join(roster["go_units"])+")$",
        "Go3_argv_template":["<FRESH_VALIDATOR_TEST_EXE>","-test.run","^("+"|".join(roster["go_units"])+")$","-test.v","-test.count=1","-test.failfast","-test.timeout=120s"],
        "Go3_original_names":roster["go_units"],
        "node162_argv_template":["<PINNED_NODE>","--require","<PINNED_OBSERVER_SOURCE>","--test","--test-reporter=tap","--test-name-pattern","^"+re.escape("<EXACT_ROSTER_LEAF_NAME>")+"$","tests/ui/desktop/http-wire-boundary.test.mjs"],
        "node162_pattern_rule":"Actual controller uses '^'+re.escape(each exact frozen leaf name)+'$'; above placeholder is not a runnable selector.",
        "node162_ids":[x["name"] for x in roster["leaves"]],
        "regression7_original_rows":roster["regressions"],
        "regression7_prefix_rule":"Actual controller substitutes pinned Node and --require observer, retaining original argv[1:]",
        "scope_boundary":"172 development assertions, 176 native top-op cap; one Go3 executable invocation has three original assertions. Installed visible GUI0/offscreen2; no model/SDK/private/paid qualification."
    },
    "W05_final_check_bindings":step_index["W05-99"]["verification_commands"],
    "W13_final_check_bindings":step_index["W13-99"]["verification_commands"],
    "W20_final_check_bindings":step_index["W20-99"]["verification_commands"],
    "qualification_gap":"New current E2 whole finite expected-ID/selector contract and actual complete qualification/valid-reuse verdict are required. Old selectors are concrete predecessor plans, not new Root authority or completed current tests.",
    "counter_policy":"Preserve original failures and held inputs. Never automatically run predecessor ^Test, held1811/provider/historical14/Q10 or known formal failures under a new name."
}
suite_ref = save("suite-map.json", suite)

signing = {
    "schema":"researchos.source58-signing-entry-gap-map.v1",
    "existing_false_sinks":[
        {"ref":refs["source15_actual_independent_closure"],"pointer":"/source_acceptance","actual":False,"decision":source_review["decision"]},
        {"ref":refs["public_source_authority"],"pointer":"/source_acceptance","actual":False,"immutable_original_must_not_be_rewritten":True},
        {"ref":refs["current58_CLI2_qualification"],"pointer":"/source_acceptance","actual":False,"whole_suite_pointer":"/whole58_test_suite_qualified","whole_suite_actual":False}
    ],
    "designated_source58_acceptance_consumer":"NOT_ESTABLISHED_BY_THE_REVIEWED_INPUTS; no invented source.accept command or accepted schema",
    "task_packet_real_entry":{"source_ref":refs["task_packet_source_only"],"CLI_commands":["list","show","next"],"read_only":True,"product_acceptance":"NOT_ASSERTED","line_range":[186,200],"identity_validation_is_not_identity_authentication":True},
    "existing_step_state_registration_fields":{"plan_sha256":refs["execution_plan"]["sha256"],"schema_version":"1.0","package_version":"2.4.0","steps_item":{"id":"W05-99","status":"ACCEPTED only after all actual card/parent criteria pass","executor_id":"actual executor, distinct from verifier_id","verifier_id":"actual independent verifier","evidence":[{"path":"relative to execution/v2.4 state parent; not an ABS path or traversal","sha256":"actual current immutable evidence hash"}]},"dependencies":step_index["W05-99"]["dependencies"],"source":"task_packet.py lines124-166; structural validation cannot sign the product"},
    "actual_parent_task_receipt_required_fields":tasks["receipt_required_fields"],
    "actual_verification_result_required_fields":tasks["receipt_verification_fields"],
    "actual_GLOBAL_EVIDENCE_V1":cases["global_evidence"],
    "source58_proposed_minimum_signature_not_adopted":{
        "status":"PROPOSAL_REQUIRED_ROOT_FREEZE_AND_NONAUTHOR_REVIEW; this report adopts nothing",
        "fields":["actual executor/verifier identities and non-author proof","source_commit=E2/source_parent and exact combined58-source-set REF","source15/source43 import closure and actual forward-registration refs","immutable current inputs/artifact/lock/environment/model-policy manifests","current CLI2, Desktop172 and actual current whole-suite qualification refs with exact accepted coverage","source_acceptance decision bound to those artifacts; independently justified whole58_test_suite_qualified","explicit remaining product/SDK/GUI/install/formal boundaries, formal_increment=0","new immutable signature and actual Root registration reference; no rewrite of old false sinks"],
        "signing_path":"New immutable W05 owner receipt in registered scope, after Root freezes actual signature schema/consumer; no future filename or hash is fabricated"
    },
    "source_acceptance":False,"parent_acceptance":False,"formal_increment":0
}
signing_ref = save("signing-map.json", signing)

case_matrix = [{"case_id":x["id"],"owner":x["final_owner_task"],"mode":x["mode"],"mandatory":x["mandatory_gate"],"assertion_ids":[a["id"] for a in x["assertions"]],"result_from_this_review":"NOT_ACCEPTED_BY_THIS_METADATA_AUDIT"} for x in cases["cases"]]
index = {
    "schema":"researchos.whole58-terminal-readonly-input-index.v1",
    "reviewer":REVIEWER,"input_refs":refs,
    "counts":{"parent_tasks":len(tasks["tasks"]),"task_cards":len(plan["steps"]),"formal_cases":len(cases["cases"]),"combined_source_paths":authority["unique_combined_source_paths"],"public_metadata_output_members":pub_mf["count"],"Node162":len(roster["leaves"]),"regression7":len(roster["regressions"]),"Go3":len(roster["go_units"])},
    "Parent_context_declaration_only":seed["parent_context"],
    "known_done":{"source_commit":source_review["decision"],"forward_head":forward["registered_head"],"publication":pub_review["decision"],"CLI2":cli_review["decision"]},
    "current_false_flags":{"source15_acceptance":source_review["source_acceptance"],"public_acceptance":authority["source_acceptance"],"CLI2_source_acceptance":cli_q["source_acceptance"],"whole58_test_suite_qualified":cli_q["whole58_test_suite_qualified"],"CLI2_Desktop169_authorization":cli_q["desktop169_execution_authorized"]},
    "predecessor_cohorts_never_summed":old_cohorts["cohorts"],
    "predecessor_local_OPEN_not_formal_IDs":old_cohorts["open"],
    "old_Desktop_scope_limits":old_scope["frozen_limits"],
    "formal_owner_matrix":case_matrix,
    "source_reuse":"Sealed peers' existing resource/tree/native evidence retained as provenance; only listed public metadata was read, no 24k resource-tree scan or new product execution.",
    "failure_origin_refs":[pin(BASE/"failure-origin.plan-catalog-no-match.json"),pin(BASE/"failure-origin.metadata-v8-sealer-parser.json")]
}
index_ref = save("inputs.index.json", index)

md = "# Review Summary\n\n**Verdict: REQUEST CHANGES — terminal acceptance evidence incomplete.** 本次缺口定位已闭合；未接受 Source58、父任务或正式用例。source15 提交、E2 forward-head、public58 发布和当前 CLI2 两例的证据均可复用，当前证据没有给出 whole58 完整 suite 或源码接受签署。\n\n"
md += "| 顺序/层 | 当前有效证据与边界 | 尚缺证据 / 下一动作 | 接受判据 |\n|---|---|---|---|\n"
for x in gaps["rows"]:
    md += "| "+x["id"]+" "+x["layer"]+" | "+x["known"].replace("|","\\|")+" | "+x["missing"].replace("|","\\|")+" "+x["action"].replace("|","\\|")+" | "+x["criterion"].replace("|","\\|")+" |\n"
md += "\n### Important Issues\n\n- **WHOLE58-01：当前完整 suite 资格未建立。** CLI2 仅两个叶子；Desktop172 仅其冻结开发范围。旧 whole38 A–E 计划及失败 cohort 不能直接晋升当前 E2。请先冻结当前全 suite 的 expected IDs、selector、资源/环境/原始回执，再独审实际完整运行或仍有效的精确复用。具体命令见 [SUITE_SELECTORS.md](SUITE_SELECTORS.md) 与机器清单 [suite-map.json](suite-map.json)。\n- **WHOLE58-02：Source58 接受签署入口尚未在所读输入中建立。** 既有 `/source_acceptance` 全 false；`task_packet` 只读选卡。请由 Root 固定真正接受 consumer/签署合同后提交新的非作者回执；不要改旧标志或发明 accept CLI。现有字段和明确未采用的最小提案见 [SIGNING_BOUNDARIES.md](SIGNING_BOUNDARIES.md) / [signing-map.json](signing-map.json)。\n- **W05-FINAL：开发资格不覆盖五个父门/A04。** 使用真实已登记 `test.runtime --task-id W05 --check-id <W05-G01/G02/H08/P01/U02>` 和 `--case-id A04`，按合同报告全部 A04-01..06；缺 live/SDK/安装资源仅阻塞相应支路。\n\n### Critical Issues\n\n本次没有运行产品或审新实现，不新判定生产缺陷。上述接受证据缺口足以阻止终验。\n\n### Suggestions\n\n按卡依赖与受资源影响的支路并行补证；不额外制造全局顺序。早期安装切片可以先行，A15 全例签署仍须其余41有效。正式 FIXTURE 是合同允许的模式，必须另按完整 frozen assertion/全球证据与独立验收接受；开发测试不能改名充数。\n\n### What's Done Well\n\n- 实际 source15 只做一次 apply/commit并经独审；public58 完整58集合与当前CLI2资格分开保留，所有 source/formal 标志没有被错误晋升。\n- 原失败 cohort、旧 REQUEST/held 原件和 metadata origins 保持不可变，新的 scope 不借旧 grant。\n\n### Verification Story\n\n- Tests reviewed: acceptance contract42/唯一owner、W05五门/A04、旧whole38选择器、Node162+7与Go3冻结roster、实际CLI2两条原argv；不执行测试。\n- Build verified: 本评审未编译；复用已有独立 CLI2 有限资格，Desktop172 最新动态运行不读取、不声明通过。\n- Security checked: 独立身份/不可变hash/授权与验收边界、资源缺口隔离和无自批/无权限继承。\n- 本轮产品/native target/Git/Go/Node/SQL/网络/模型/CAS/canonical写入均0；formal增量0。两条独立 metadata origin：Main plan-catalog no-match 原outer/rg1/1、PythonNULL；V8 sealer parser 原outer/native均NULL。原I/O各保留一次，无原输入重跑。Parent当前状态仅作为声明保存，固定cut不改。\n"
(BASE/"REPORT.md").write_text(md, encoding="utf-8", newline="\n")

suite_md = "# Frozen suite selectors and qualified coverage\n\n当前 `whole58_test_suite_qualified=false`。所读证据不存在已经封好的 E2 全suite consumer/资格签署；下面的真实旧计划和有限当前控制不能自行拼成完整资格。\n\n## 已资格：current58 CLI2 actual argv\n\n"
for x in cli_actual:
    suite_md += "- "+x["label"]+": `"+json.dumps(x["argv"],ensure_ascii=False)+"`，cwd `"+x["cwd"]+"`，actual exit0；原REF "+json.dumps(x["ref"],ensure_ascii=False)+"。\n"
suite_md += "\n只覆盖 "+", ".join(cli_q["qualified_case_ids"])+"；原 `TestCLIProtocolInteractiveAuthority` 的其它叶子和 full CLI `^Test` 不在这份资格内，不重跑原两例。\n\n## 原 whole38 A–E（22752旧候选；未授当前E2执行权）\n\n"
for x in whole_plan["batches"]:
    suite_md += "### "+x["id"]+" "+x["package"]+"\n\nFrozen selector: `"+x["run_regex"]+"`。\n\n`-test.timeout="+x["test_timeout"]+"`；原 outer预算 "+x["outer_timeout"]+"；必须新scope绑定实际 freshly compiled test exe/actual argv/cwd。"+x["purpose"]+"\n\n"
suite_md += "保留原 graph argv suffix：`"+json.dumps(whole_plan["capture"]["go_graph"])+"`。固定当前Go/SDK/source/embed/migrations/schema/locks/工具/runtime依赖与before-first-case/after/current vectors；原 plan 本身不是新的参数授权。Full CLI E 必须有完整当前事件/leaf proof，旧282PASS/12FAIL和affected78分别保存。\n\nHeld 原范围："+json.dumps(whole_plan["held"],ensure_ascii=False)+"。不运行 `go test ./...` 或新名字重跑held/旧失败。\n\n## 当前 Desktop169+Go3 源冻结命令（实际结果尚待新Rootterminal独审）\n\nGo3一条testexe调用：`"+json.dumps(suite["current_Desktop172_source_contract"]["Go3_argv_template"])+"`。三个原test：`"+json.dumps(roster["go_units"])+"`。\n\n162个Node逐叶：`[PINNED_NODE, --require, PINNED_OBSERVER, --test, --test-reporter=tap, --test-name-pattern, ^re.escape(exact_roster_name)$, tests/ui/desktop/http-wire-boundary.test.mjs]`。全部精确名称存于 [suite-map.json](suite-map.json)，没有用count替代名单。\n\n7原regression（前加pinned observer，完整保留argv[1:]）：\n\n"
for x in roster["regressions"]:
    suite_md += "- "+x["name"]+": `"+json.dumps(x["argv"],ensure_ascii=False)+"`；"+x["count_kind"]+"。\n"
suite_md += "\n源码位置：controller行88/201/204/205/220–228。Go3确切三原PASS，无FAIL/SKIP；Node逐叶恰一TAP pass/0fail/0skip；两legacy program须保原正文/显式PASS，不发明内部assertion数。Transport/source断言/OS生命周期各自闭合；176是包含Git/builder/buildinfo等的top native cap，172是169+3开发断言单位，不是172个formal或172次native。\n\n## W05正式入口\n\n"
for x in step_index["W05-99"]["verification_commands"]:
    suite_md += "- `"+ " ".join(x["argv_template"]) +"`；expected IDs `"+json.dumps(x["expected_assertion_ids"])+"`。\n"
suite_md += "\n必须核实际registered command revision/真实handler及完整required mode；计划argv和零断言不是PASS。A04-01..06分别是完成语义、取消、崩溃/超时恢复、嵌套/版本兼容、自有CLI交互/JSONL、完整真实编码任务。\n"
(BASE/"SUITE_SELECTORS.md").write_text(suite_md,encoding="utf-8",newline="\n")

sign_md = "# Source58 signing boundary\n\n指定的**现有只读事实字段**是 source15 review/public authority/CLI2 qualification 的 `/source_acceptance`（目前全false），以及CLI2 `/whole58_test_suite_qualified`（false）。这些不可变原件不能改成新的签署。\n\n所读合同没有提供 `source.accept` 命令，也没有已冻结的 Source58 全suite accepting consumer。`task_packet.py:186–200` 只有list/show/next，输出read_only与product_acceptance NOT_ASSERTED；它不签收。要设置新source接受语义，Root还须固定新不可变签署合同及真实consumer，然后非作者在同一E2/58输入上提交签署，Root再串行登记。这一缺口不能用字段存在来掩盖。\n\n**已经固定的施工/父回执入口字段**：\n\n- step_state：schema_version1.0/package_version2.4.0/plan_sha256；steps[].id/status/executor_id/verifier_id/evidence[].path+sha256。ACCEPTED须不同真实身份、非空当前hash evidence及所有依赖卡接受；evidence为状态目录下安全相对路径。`task_packet.py:124–166` 仅验证结构/hash，不认证身份，不接受产品。\n- W05父receipt："+", ".join(tasks["receipt_required_fields"])+"。\n- verification_results各项："+", ".join(tasks["receipt_verification_fields"])+"。\n- GLOBAL_EVIDENCE_V1：case/run/mode/OS时间/独立身份、code/spec/lock/input版本、actual command argv/cwd/rawstdoutstderr、全部 assertion 原证据locator+SHA、独立 acceptance 基线/索引/结论。\n\n新source58 signature的最小绑定提案保存于 [signing-map.json](signing-map.json)，明确未被Root采用；不写未来hash/路径/权限。Source接受、W05父门/A04、W13 GUI与formal、发行A15和Goal全验收是分别签署的对象，不能从某一签署推导其它层。\n\nW05-99前置："+", ".join(step_index["W05-99"]["dependencies"])+"；只拥有A04。C11/C15最终owner W12。W13拥有C17/C18/C23/C24/C25/C26，模式FIXTURE；W20 A15 LIVE_WINDOWS。P02/C01协议fixture在W06，真正双端P06/A13在W14，发行件在W20；无需以尚未实现的后置live门阻塞无关前置切片。\n"
(BASE/"SIGNING_BOUNDARIES.md").write_text(sign_md,encoding="utf-8",newline="\n")

review = {
    "schema":"researchos.whole58-terminal-evidence-gap-independent-review.v1","reviewer":REVIEWER,"non_author":True,
    "decision":"EVIDENCE_GAP_MAP_COMPLETE_NOT_TERMINAL_ACCEPTED","verdict":"REQUEST_CHANGES_FOR_TERMINAL_ACCEPTANCE",
    "requested_changes":[{"id":"WHOLE58-01","severity":"Important","requirement":gaps["rows"][3]},{"id":"WHOLE58-02","severity":"Important","requirement":gaps["rows"][4]},{"id":"W05-FINAL","severity":"Important","requirement":gaps["rows"][5]}],
    "gap_table_ref":pin(BASE/"gap-table.json"),"input_index_ref":index_ref,"suite_map_ref":suite_ref,"signing_map_ref":signing_ref,
    "report_ref":pin(BASE/"REPORT.md"),"suite_selectors_ref":pin(BASE/"SUITE_SELECTORS.md"),"signing_boundaries_ref":pin(BASE/"SIGNING_BOUNDARIES.md"),
    "source_commit":cli_q["source_commit"],"source_parent":source_review["actual_parent"],
    "known_valid_scope":{"source15_commit_evidence":True,"forward_head_metadata":True,"public58_metadata":True,"CLI2_exact_cases":cli_q["qualified_case_ids"]},
    "source_acceptance":False,"whole58_test_suite_qualified":False,"parent_acceptance":False,"formal_increment":0,"goal_complete":False,
    "new_failure_origins":[pin(BASE/"failure-origin.plan-catalog-no-match.json"),pin(BASE/"failure-origin.metadata-v8-sealer-parser.json")],"new_metadata_failure_origin_count":2,"new_metadata_nonzero_count":1,"new_product_failure_count":0,
    "failed_original_inputs_rerun":0,"failure_counts_reset":False,"current_canonical_probed":False,"Parent_context_declaration":seed["parent_context"],
    "actual_calls":{"candidate_import_execute":0,"native_targets":0,"Git":0,"Go":0,"Node":0,"SQL":0,"HTTP_SDK_models_paid":0,"canonical_writes":0,"source_writes":0},
    "verification_story":{"tests_reviewed":"Frozen contracts/selectors/rosters and qualified CLI2 raw argv; no test execution","build_verified_by_this_review":False,"security_checked":"Hash-bound immutable sources, independent identity, exact owner/mode/authority boundaries","resource_tree_rescan":False},
    "status":"STOPPED_AFTER_SEAL"
}
review_ref = save("review.json",review)
handoff = {
    "schema":"researchos.readonly-evidence-gap-review-handoff.v1","owner":REVIEWER,"status":"STOPPED_AFTER_SEAL",
    "decision":review["decision"],"review_ref":review_ref,"report_ref":review["report_ref"],"gap_table_ref":review["gap_table_ref"],"input_index_ref":index_ref,
    "suite_map_ref":suite_ref,"signing_map_ref":signing_ref,"original_tool_observations_ref":pin(BASE/"original-tool-observations.json"),
    "new_origin_refs":review["new_failure_origins"],"new_origin_count":2,"native_product_calls":0,"canonical_writes":0,"source_acceptance":False,"formal_increment":0,
    "next_action":"Root can use gap/suite/signature maps; latest Desktop scope/run requires its own non-author actual review. No old scope/grant reuse. Source58 signing protocol/current whole suite and W05 five gates/A04 remain OPEN; do not promote development172 or metadata to formal.",
    "immutable_input_refs":list(refs.values())
}
handoff_ref = save("handoff.json",handoff)
members=[]
for p in sorted(BASE.iterdir(),key=lambda x:x.name):
    if p.is_file() and p.name != "manifest.json":
        members.append(pin(p))
mf_ref = save("manifest.json",{"schema":"researchos.immutable-readonly-review-manifest.v1","entries":members,"count":len(members),"self_excluded":True})
print(json.dumps({"review_ref":review_ref,"handoff_ref":handoff_ref,"manifest_ref":mf_ref,"members":len(members),"input_refs":len(refs),"failure_ref":review["new_failure_origins"][0],"new_failure_origins":2,"source_acceptance":False,"formal_increment":0,"status":"STOPPED_AFTER_SEAL"},ensure_ascii=False))
