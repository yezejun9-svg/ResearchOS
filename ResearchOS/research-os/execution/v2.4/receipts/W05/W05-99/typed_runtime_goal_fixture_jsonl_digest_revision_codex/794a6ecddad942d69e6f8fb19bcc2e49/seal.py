import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
Q=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49")
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9")
REVIEW=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_independent_review_codex/715d9054a9ee4de4a201bd86b1438ed38")
OFFICIAL=Path("D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/src/cmd/internal/test2json/test2json.go")
def pin(p):
    b=p.read_bytes()
    return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write_new(name,content):
    text=content if isinstance(content,str) else json.dumps(content,ensure_ascii=False,indent=2)+"\n"
    with (Q/name).open("x",encoding="utf-8",newline="\n") as f:f.write(text)
review_expected={"MF.json":("493eb65bf0d0dba3446d0d6fe7a9ad7aac791611b700564dea2f4c4e26a26167",2719),"HDF.json":("0ccced7d07fb3338a3b7d66a20120c126924991df118d00d4157ef7b47b58b19",19865),"report.md":("bcf9940c354fe8f04c54b91fbefe30c252b9489baec0b40159691668ec5ab503",6888)}
review_refs=[]
for name,expected in review_expected.items():
    actual=pin(REVIEW/name)
    assert (actual["sha256"],actual["bytes"])==expected,actual
    review_refs.append(actual)
write_new("revision-review-refs.json",{"authority":"NONE","status":"Q2_REQUEST_CHANGES_SOURCE_COMPONENT_NOT_ACCEPTED","findings_count":2,"findings_are_not_mechanical_failures":True,"refs":review_refs})
base=json.loads((Q/"base-refs.json").read_text(encoding="utf-8"))
members=json.loads((Q/"source-refs.json").read_text(encoding="utf-8"))["refs"]
static=json.loads((Q/"static-checks.json").read_text(encoding="utf-8"))
for ref in base["refs"]+members:
    assert pin(Path(ref["path"]))==ref,ref
old_mf=json.loads((BASE/"MF.json").read_text(encoding="utf-8"))
for ref in old_mf["members"]:assert pin(Path(ref["path"]))==ref,ref
helper=Q/"candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go"
new=helper.read_text(encoding="utf-8")
old=(BASE/"candidate-root/internal/domain/runtime_typed_client_fixture_windows_test.go").read_text(encoding="utf-8")
state="func typedRuntimeFixtureVerifyJSONL("
pin_marker="func typedRuntimeFixturePin("
tail="func typedRuntimeFixtureChild("
assert new[new.index(state):new.index(pin_marker)]==old[old.index(state):old.index(pin_marker)]
assert new[new.index(tail):]==old[old.index(tail):]
line_refs={}
for i,line in enumerate(new.splitlines(),1):
    if line.startswith("func typedRuntimeFixture") or "case \"OutputType\"" in line or 'Digest(raw) != "sha256:"+expectedSHA' in line or 'if event.OutputType != nil' in line:
        line_refs[str(i)]=line.strip()
report=[
"# Q3 minimal helper Source revision",
"",
"结论：仅两个已确认Source阻断的最小修订候选；authority=NONE、formal_acceptance=false，等待Root独立复核及新组合实际执行。",
"旧Q2 REQUEST_CHANGES与两finding保持历史事实；finding不是机械执行失败，不改/归零任何失败计数。",
"Q3 Source namespace："+Q.as_posix(),
"",
"1. Digest资源比较只将裸expectedSHA加一次明确sha256:前缀；固定Go裸常量与test2json裸SHA环境约束不变。",
"保存pin仍是Digest(raw)合法sha256:<64hex>格式，调用后比较也是Digest对Digest，不改生产Digest或TLS/profile领域hash。",
"依据T5 contracts.go97实际Digest定义，公开Source指纹已绑定base-refs；禁止通过更改固定Root Go hash使比较通过。",
"2. DecodeEvent增加可选nonnull string OutputType并跟踪字段presence；只允许Action=output和省略/空串/frame/error/error-continue。",
"非output携带OutputType即使空串也拒绝；null、错类型、未知值、重复字段、未知字段或额外JSONvalue仍拒绝。",
"Output/OutputType都不提供run/pass权威；FailedBuild/Key/Value/Path及fail/attr/artifacts scope没有泛化接受。",
"",
"固定官方来源："+OFFICIAL.as_posix(),
"官方Source SHA/bytes：81b811cc3af1cc49da5faec1a93aabf12b769a69a5dbc60505c125edb19d288b /19217；selected inventory SHA/bytes：4f7c76bea3116f31806ef15f655e692f7507e34585fc10e9a0be5e9507e77287 /190768（build_inputs748）。",
"实际Source38是OutputType string/omitempty；run378→framing380/386，writeOutputEvent425–508只发output及上述值；官方writeEvent515–531负责package/time/LF。",
"",
"四个原测试Source逐字节保持Q2/4396；完整VerifyJSONL状态机、child到TLS/configure/profile/provider/attach文件尾逐字节保持Q2。",
"181原t.Fatal/Error/Skip调用、20原顶层Test名、196 assertion_or_error_if（190严格t断言+6fmt.Errorf返回块）由字节相同继承，scope仍8native+2Goal原leaf。",
"Root required resource/env与Q2完全相同：固定Go/GOROOT、explicit官方test2json及裸SHA、Node/Mu bundle/fresh absolute evidence directory。",
"Root仍须real parent JSONL/exit、test2json→compiled child→SDK所有descendant Go Job、physicalchild PID/exit及lease关闭对账。",
"child.stdout.jsonl/raw是官方reporter stdout；官方reporter把native stdout/stderr合并为Output，child.stderr.raw仅reporter stderr，不冒称native stderr独立分流。",
"",
"本轮仅固定Python短script构造/指纹和Go文本/词法分隔符检查；Go AST/compiler/gofmt/native/SQL/model/provider/private/sign/canonical均0。",
"新机械失败0；全部公开工具IO见tool-io.json，封存运行IO单独列MF排除。没有运行、独立Source接受或formal产品接受结论。",
"精确diff：runtime_typed_client_fixture_windows_test.patch；完整五文件pins：source-refs.json；官方字段合同：official-outputtype-contract.json。",
"实际helper修订行："+json.dumps(line_refs,ensure_ascii=False),
"作者封存后STOP。由Root独立review→fresh integration→actual，不能把static或resource compilation当10leaf/正式接受。",
""
]
write_new("report.md","\n".join(report))
hdf={
"version":"MINIMAL_TEST_HELPER_REVISION_HDF_V1","status":"SEALED_SOURCE_CANDIDATE_NOT_EXECUTED","authority":"NONE","formal_acceptance":False,"namespace":Q.as_posix(),"baseline":BASE.as_posix(),
"Q2_review":{"namespace":REVIEW.as_posix(),"status":"REQUEST_CHANGES","findings_count":2,"findings_are_mechanical_failures":False,"refs":review_refs},
"scope":{"source_members":5,"changed_member_count":1,"changed_member":helper.as_posix(),"unchanged_original_test_count":4,"production_members":0,"native_original_leaves":8,"Goal_original_leaves":2},
"members":members,"base_refs":pin(Q/"base-refs.json"),"review_refs":pin(Q/"revision-review-refs.json"),"static_checks":pin(Q/"static-checks.json"),"official_outputtype_contract":pin(Q/"official-outputtype-contract.json"),
"delta":{"Digest_compare":"Digest(raw) != single literal sha256: + Root bare expectedSHA","saved_runtime_pin_format":"Digest(raw): sha256:<64 lowercase hex> (unchanged)","fixed_Root_Go_bare_SHA_unchanged":True,"OutputType":"optional nonnull string, presence tracked","OutputType_allowed_action":"output","OutputType_allowed_values":["","frame","error","error-continue"],"omitted_OutputType_allowed":True,"nonoutput_OutputType_even_empty_rejected":True},
"unchanged":{"four_original_Source_bytes_Q2_4396":True,"whole_strict_JSONL_state_machine_Q2_bytes":True,"whole_child_TLS_configure_profile_provider_attach_Q2_bytes":True,"unknown_duplicate_null_wrong_type_trailing_guards":True,"fail_skip_unknown_outofscope_missing_run_duplicate_terminal_rejections":True,"Output_not_run_pass_authority":True,"original_counts":{"calls":181,"Test_names":20,"assertion_or_error_if":196,"strict_t_assertion_if":190,"fmt_Errorf_if":6},"production_Digest":True,"Root_resource_contract":True},
"official_source":pin(OFFICIAL),"selected_inventory":pin(Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/official-test2json-resource-build-root-3e9129c5f7c9461e/selected-official-compiler-inputs.json")),
"official_source_line_refs":{"OutputType":38,"run_framing":[378,380,386],"writeOutputEvent":[425,508],"writeEvent":[515,531]},
"helper_line_refs":line_refs,"diff":pin(Q/"runtime_typed_client_fixture_windows_test.patch"),"report":pin(Q/"report.md"),"tool_io":pin(Q/"tool-io.json"),
"execution":{"Go_AST":False,"Go_compile":False,"Go_test":False,"gofmt":False,"native":False,"SQL":False,"model_provider":False,"private_read":False,"signing":False,"canonical_write":False},
"new_mechanical_failures":[],"failure_counter_reset":False,"protected_writes":[],
"remaining_required_work":["independent Q3 Source review","Root fresh composition and actual compile/test","original10leaf and parent terminal/exit reconciliation","complete descendant Go Job/lease closure","independent actual review"],
"evidence_limit":"official reporter stdout JSONL combines native stdout/stderr as Output; reporter stderr not independent native stderr capture"}
write_new("HDF.json",hdf)
all_members=[pin(p) for p in sorted(Q.rglob("*")) if p.is_file()]
mf={"version":"IMMUTABLE_MINIMAL_TEST_HELPER_SOURCE_MANIFEST_V1","status":"SEALED_SOURCE_CANDIDATE_NOT_EXECUTED","authority":"NONE","formal_acceptance":False,"namespace":Q.as_posix(),"source_members":5,"changed_source_members":1,"production_members":0,"members":all_members,"self_hash_excluded":["MF.json"],"postseal_IO_excluded":["seal-tool-io.json"]}
write_new("MF.json",mf)
assert all(pin(Path(x["path"]))==x for x in all_members)
assert all(pin(Path(x["path"]))==x for x in base["refs"])
print(json.dumps({"namespace":Q.as_posix(),"MF":pin(Q/"MF.json"),"HDF":pin(Q/"HDF.json"),"report":pin(Q/"report.md"),"source_refs":pin(Q/"source-refs.json"),"static_checks":pin(Q/"static-checks.json"),"diff":pin(Q/"runtime_typed_client_fixture_windows_test.patch"),"tool_io":pin(Q/"tool-io.json"),"members":len(all_members),"member_drift":0,"baseline_drift":0,"source_members":members,"helper_only_delta":True,"new_mechanical_failures":0,"Go_native_SQL_model_execution":0,"authority":"NONE","formal_acceptance":False},ensure_ascii=False))
