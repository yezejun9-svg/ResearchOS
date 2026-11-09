import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
Q=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9")
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931")
REVIEW=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd")
TOOL=Path("D:/作品集/ResearchOS/research-os/.local/official-test2json-resource-8a1fba36028c4c0b9ed30c0a7aca54cc/programs/test2json.exe")
CLOSED=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/official-test2json-resource-build-root-3e9129c5f7c9461e/resource-build.closed.json")
def pin(p):
    raw=p.read_bytes()
    return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def write_new(name,value):
    text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+"\n"
    with (Q/name).open("x",encoding="utf-8",newline="\n") as f:f.write(text)
base=json.loads((Q/"base-refs.json").read_text(encoding="utf-8"))
source=json.loads((Q/"source-refs.json").read_text(encoding="utf-8"))
static=json.loads((Q/"static-checks.json").read_text(encoding="utf-8"))
resources=json.loads((Q/"resource-contract.json").read_text(encoding="utf-8"))
for member in base["refs"]+source["refs"]:
    assert pin(Path(member["path"]))==member,member
tool_ref=pin(TOOL)
closed_ref=pin(CLOSED)
assert (tool_ref["sha256"],tool_ref["bytes"])==("dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c",4932608)
assert (closed_ref["sha256"],closed_ref["bytes"])==("bf9a9df9448be2df121455460378d895441a244684ca053bbf288f92276dbf01",24186)
helper=Q/"candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go"
text=helper.read_text(encoding="utf-8")
old=(BASE/"candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go").read_text(encoding="utf-8")
marker="func typedMuBrokerFixtureProgram("
assert text[text.index(marker):]==old[old.index(marker):]
line_refs={}
for i,line in enumerate(text.splitlines(),1):
    if line.startswith("func typedRuntimeFixture") or line.startswith("func typedMuBrokerFixtureProgram") or line.startswith("func attachTypedRuntimeFixture"):
        line_refs[line.split("(")[0].removeprefix("func ")]=i
scope_ref=pin(BASE/"scope-map.json")
summary=[
"# Test-only child JSONL Source revision",
"",
"结论：新 Source 候选已封存，authority=NONE / formal_acceptance=false；等待 Root 独立复核和全新组合实际执行。",
"本轮未执行 Go、gofmt、native、SQL、model、provider、私密凭据、签名或 canonical 写入。",
"",
"只修订 runtime_typed_client_fixture_windows_test.go；其余四个4396测试Source逐字节保持。旧4396 HDF/MF及T5/Main均未修改。",
"8个原native叶 + 2个原Goal租约叶范围不变，逐失败映射继续绑定4396 scope-map.json；其他失败/skip不接受。",
"原181个t.Fatal/Error/Skip调用、20个顶层Test名称及顺序保留；196个assertion_or_error_if节点中190个严格含t断言，另6个fmt.Errorf返回块，全部保留。",
"",
"## 改动和拒绝条件",
"",
"Root冻结的官方cmd/test2json binary直接执行同一compiled child。Go/GOROOT是来源校验，不调用Go tool、不假设builtin/cache可用。",
"RESEARCHOS_GO固定SHA；GOROOT/VERSION首行go1.27.1，GOROOT/bin/go.exe必须os.SameFile；test2json显式绝对路径和冻结SHA。",
"调用参数：-p researchos.local/research-os/internal/domain -t <same compiled child> -test.run=^<exact parent>$ -test.v=test2json -test.count=1 -test.timeout=180s。",
"调用前保存Go/rootGo/VERSION/test2json/child真实path、SHA、bytes；调用后复查无漂移。子argv必须精确，GODEBUG强制正常fallback trust。",
"JSONL逐行解析真实JSONobject；拒绝空/未完整LF/非UTF8、重复或未知字段、null、类型错、额外JSONvalue、包名错或非法Time。",
"状态机要求包唯一start和terminal pass，exactparent及expectedleaf各唯一run后唯一terminal pass；不从Output文本/RUN/PASS子串放行。",
"拒绝fail、skip、其他action、范围外Test、重复run/terminal、没有run的pass、父先于叶通过、包先于完整scope通过、包terminal之后事件或缺失scope。",
"只接受此parent及其expectedleaf（所有6parent合计8leaf），不扩大case。四个原Source和TLS/configure/provider/qualification/attach尾部均保持字节。",
"",
"## Root资源与实际证据边界",
"",
"必须提供绝对RESEARCHOS_GO、GOROOT、RESEARCHOS_TEST2JSON、RESEARCHOS_TEST2JSON_SHA256、原RESEARCHOS_NODE/RESEARCHOS_MU_BUNDLE及全新绝对RESEARCHOS_TYPED_RUNTIME_EVIDENCE_DIR。",
"Root Go1.27.1 SHA：d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490。",
"Root实际官方test2json.exe："+TOOL.as_posix(),
"Root工具SHA/bytes："+tool_ref["sha256"]+" / "+str(tool_ref["bytes"])+"；资源build.closed SHA/bytes："+closed_ref["sha256"]+" / "+str(closed_ref["bytes"])+"。",
"这里只读取并核对Root构建回执与二进制pins；tool只compiled，未替Root宣布执行或独立接受。源码不固定该绝对路径，Root通过env提供。",
"保存child.stdout.jsonl与逐字节相同stdout.raw、stderr.raw、invocation、event-verdict、child-result、parent-result；父/子均可独立读取。",
"actual_runner_pid/exit明确是test2json进程；physical child PID/exit为null/PENDING_ROOT_GO_JOB，不伪称观察。parent_exit=null/PENDING_ROOT_RECONCILIATION。",
"Root外层真实parent JSONL/terminal/exit及覆盖test2json→compiled child→SDK所有descendants的Go Job与lease关闭必须对账。",
"synthetic TLS/model/metadata/Goal port边界不变；不使用生产model或真实provider，不是formal产品证据。",
"",
"## 验证和交接",
"",
"固定Python短script path构造exit0；仅Python AST提取已pin纯词法工具 + Go文本/分隔符静态检查。Go AST/类型/编译/执行均未验证。",
"Source相关独立review原REQUEST_CHANGES_CHILD_JSONL保持历史事实，新revision尚待独立复核。",
"完整公开工具输入输出见tool-io.json；新机械错误0，不重置全局失败计数。旧814/815及旧FULL1261pass/25fail/4skip不改写。",
"精确成员pins见source-refs.json、base-refs.json；最小helper差分见runtime_typed_client_fixture_windows_test.patch。",
"实际helper行号："+json.dumps(line_refs,ensure_ascii=False),
"本作者封存后STOP。Root独立review→fresh integration→actual→Job/lease对账；未执行/缺资源/skip不得PASS。",
""
]
write_new("report.md","\n".join(summary))
write_new("root-resource-refs.json",{"authority":"NONE","refs":[tool_ref,closed_ref],"read_only_pin_verification":True,"resource_status":"ROOT_COMPILED_ONLY_PENDING_ACTUAL_AND_INDEPENDENT_ACCEPTANCE","Go_or_tool_execution_by_source_author":0})
hdf={
"version":"TEST_ONLY_SOURCE_REVISION_HDF_V1",
"status":"SEALED_SOURCE_CANDIDATE_NOT_EXECUTED",
"authority":"NONE","formal_acceptance":False,
"source_namespace":Q.as_posix(),
"baseline_Source_namespace":BASE.as_posix(),
"baseline_Source_review":{"namespace":REVIEW.as_posix(),"status":"REQUEST_CHANGES_CHILD_JSONL","MF":pin(REVIEW/"MF.json"),"HDF":pin(REVIEW/"HDF.json"),"report":pin(REVIEW/"report.md")},
"scope":{"source_member_count":5,"changed_member_count":1,"changed_member":helper.as_posix(),"unchanged_original_source_count":4,"production_member_count":0,"native_original_leaf_count":8,"Goal_original_leaf_count":2,"original_failed_leaf_mapping_ref":scope_ref},
"members":source["refs"],
"base_refs":pin(Q/"base-refs.json"),
"static_checks":pin(Q/"static-checks.json"),
"static_assertion_counts":{"original_calls":181,"original_top_level_Test_names":20,"assertion_or_error_if_nodes":196,"strict_t_assertion_if_nodes":190,"fmt_Errorf_return_if_nodes":6,"all_preserved":True},
"execution":{"Go_AST":False,"Go_compile":False,"Go_test":False,"gofmt":False,"native":False,"SQL":False,"real_model_or_provider":False,"private_credential_or_claim_read":False,"signing":False,"canonical_write":False},
"protected_writes":[],
"TLS_configure_profile_provider_attach_tail_byte_equal_4396":True,
"child_protocol":{"official_test2json_direct":True,"automatic_Go_tool_or_cache_build":False,"package":"researchos.local/research-os/internal/domain","argv":["-p","researchos.local/research-os/internal/domain","-t","SAME_CURRENT_COMPILED_CHILD","-test.run=^EXACT_PARENT$","-test.v=test2json","-test.count=1","-test.timeout=180s"],"strict_JSONL_objects":True,"no_RUN_PASS_substring_acceptance":True,"exact_parent_and_original_leaf_unique_run_terminal_pass":True,"fail_skip_duplicate_malformed_out_of_scope_rejected":True,"package_unique_start_terminal_pass_required":True,"actual_runner_exit_source":"test2json.ProcessState","actual_native_child_exit":None,"actual_parent_exit":None,"parent_reconciliation":"PENDING_ROOT_RECONCILIATION","native_child_reconciliation":"PENDING_ROOT_GO_JOB"},
"required_resources":resources,
"Root_actual_tool_refs":{"tool":tool_ref,"build_closed":closed_ref,"status":"ROOT_COMPILED_ONLY_NOT_SELF_ACCEPTED"},
"helper_line_refs":line_refs,
"runtime_outputs":["child-invocation.json","child.stdout.jsonl","child.stdout.raw","child.stderr.raw","child-event-verdict.json","child-result.json","parent-result.json"],
"remaining_required_work":["independent Source review","Root fresh composition and compile","Root actual original10leaf execution","Root external parentJSONL/exit reconciliation","Root complete Job descendant and lease closure","independent actual review"],
"excluded_scope":["production legacy compatibility","epoch","ledger","W16","other FULL failures and4skips","product holdout","formal product acceptance"],
"report":pin(Q/"report.md"),
"public_tool_io":pin(Q/"tool-io.json"),
"new_source_errors":[],
"failure_counter_reset":False}
write_new("HDF.json",hdf)
all_members=[pin(p) for p in sorted(Q.rglob("*")) if p.is_file()]
manifest={"version":"IMMUTABLE_TEST_SOURCE_REVISION_MANIFEST_V1","status":"SEALED_SOURCE_CANDIDATE_NOT_EXECUTED","authority":"NONE","formal_acceptance":False,"namespace":Q.as_posix(),"source_member_count":5,"changed_source_member_count":1,"production_member_count":0,"members":all_members,"self_hash_excluded":["MF.json"],"postseal_IO_excluded":["seal-tool-io.json"]}
write_new("MF.json",manifest)
assert all(pin(Path(m["path"]))==m for m in all_members)
assert all(pin(Path(m["path"]))==m for m in base["refs"])
print(json.dumps({"namespace":Q.as_posix(),"MF":pin(Q/"MF.json"),"HDF":pin(Q/"HDF.json"),"report":pin(Q/"report.md"),"source_refs":pin(Q/"source-refs.json"),"static_checks":pin(Q/"static-checks.json"),"root_resource_refs":pin(Q/"root-resource-refs.json"),"tool_io":pin(Q/"tool-io.json"),"source_members":source["refs"],"members":len(all_members),"member_drift":0,"baseline_drift":0,"original_calls_preserved":181,"original_Test_names_preserved":20,"assertion_or_error_if_nodes_preserved":196,"strict_t_assertion_if_nodes_preserved":190,"source_changed_only_helper":True,"new_source_errors":0,"Go_native_SQL_model_execution":0,"authority":"NONE","formal_acceptance":False},ensure_ascii=False))
