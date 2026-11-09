import ast,collections,difflib,hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
Q=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9")
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931")
T5=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2")
REVIEW=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_independent_review_codex/6e7346b6ae004d219524f5049151f9fd")
def pin(p):
    b=p.read_bytes()
    return {"path":p.as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write_new(name,value):
    p=Q/name
    p.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(value,bytes):
        with p.open("xb") as f:f.write(value)
    else:
        raw=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+"\n"
        with p.open("x",encoding="utf-8",newline="\n") as f:f.write(raw)
def check_pin(path,sha,size):
    actual=pin(path)
    assert (actual["sha256"],actual["bytes"])==(sha,size),actual
    return actual
check_pin(BASE/"MF.json","dcb1812c7b5d44a8db70fe0bb98ba93c9013ae016487f952a392565ec7715299",6789)
check_pin(REVIEW/"report.md","3e35ae3c70a8320895105c080c5de2ecdb2b236697ad69e096224486757317fe",5935)
check_pin(REVIEW/"MF.json","cd320ab25ef0879d09499099f8428121fa7f8a16207d6ae6f3fd0d68acc857d4",4426)
check_pin(REVIEW/"HDF.json","7e2b1d7818b6938d9f6815ab199f92daad171e433e8b09ba4422683c6ecc1a9c",20540)
mf=json.loads((BASE/"MF.json").read_text(encoding="utf-8"))
for member in mf["members"]:
    assert pin(Path(member["path"]))==member,member
all_base_pins={Path(x["path"]).name:x for x in mf["members"]}
utilities_source=(BASE/"construct.py").read_text(encoding="utf-8")
syntax=ast.parse(utilities_source)
wanted={"tokens","close_index","call_nodes","assertion_if_nodes","balanced"}
pure=[node for node in syntax.body if isinstance(node,ast.FunctionDef) and node.name in wanted]
assert {node.name for node in pure}==wanted
namespace={}
exec(compile(ast.Module(body=pure,type_ignores=[]),str(BASE/"construct.py"),"exec"),namespace)
tokens=namespace["tokens"]
call_nodes=namespace["call_nodes"]
assertion_if_nodes=namespace["assertion_if_nodes"]
balanced=namespace["balanced"]
relatives=[
"internal/domain/runtime_permission_windows_test.go",
"internal/domain/runtime_tool_integration_windows_test.go",
"internal/domain/runtime_session_events_windows_test.go",
"internal/domain/client_protocol_goal_test.go",
"internal/domain/runtime_typed_client_fixture_windows_test.go"]
helper_rel=relatives[-1]
base_refs=[]
source_refs=[]
checks=[]
for rel in relatives[:-1]:
    source=BASE/"candidate-root"/rel
    raw=source.read_bytes()
    assert pin(source)==all_base_pins[source.name]
    write_new("candidate-root/"+rel,raw)
    result=Q/"candidate-root"/rel
    assert result.read_bytes()==raw
    assert balanced(tokens(raw.decode("utf-8")))
    base_refs.append(pin(source))
    source_refs.append(pin(result))
    checks.append({"relative_path":rel,"byte_equal_4396":True,"changes":0})
source=BASE/"candidate-root"/helper_rel
raw=source.read_bytes()
assert pin(source)==all_base_pins[source.name]
old=raw.decode("utf-8")
fragment=(Q/"child-jsonl.fragment.go.txt").read_text(encoding="utf-8")
start=old.index("// Each original native case runs its complete original assertions")
end=old.index("func typedMuBrokerFixtureProgram(")
prefix=old[:start]
assert prefix.count('\t"regexp"\n')==1 and prefix.count('\t"testing"\n')==1
new_prefix=prefix.replace('\t"regexp"\n','\t"regexp"\n\t"runtime"\n').replace('\t"testing"\n','\t"testing"\n\t"time"\n\t"unicode/utf8"\n')
revised=new_prefix+fragment+old[end:]
assert revised[revised.index("func typedMuBrokerFixtureProgram("):]==old[end:]
assert balanced(tokens(revised))
assert "bytes.Contains(stdout" not in revised
assert '"=== RUN   "+leaf' not in revised and '"--- PASS: "+leaf' not in revised
assert "tool\", \"test2json" not in revised
assert '"pkg", "tool"' not in revised
required=[
'typedRuntimeFixtureJSONPackage = "researchos.local/research-os/internal/domain"',
'typedRuntimeFixtureGoSHA256 = "d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"',
'json.NewDecoder(bytes.NewReader(raw))','fields[key]','decoder.Decode(&trailing); err != io.EOF',
'!utf8.Valid(raw)','raw[len(raw)-1] !=',
'event.Package != typedRuntimeFixtureJSONPackage','event.Time','time.Parse(time.RFC3339Nano',
'event follows package terminal pass','has unexpected scoped Test',
'scoped run missing, misplaced or duplicate','scoped terminal pass missing run or duplicate',
'parent passed with incomplete original leaf','package passed with incomplete exact Test scope',
'rejects fail, skip or unexpected action','!started || !ended',
'os.Getenv("RESEARCHOS_GO")','os.Getenv("GOROOT")',
'os.SameFile(goInfo, rootInfo)','os.Getenv("RESEARCHOS_TEST2JSON")',
'os.Getenv("RESEARCHOS_TEST2JSON_SHA256")','exec.Command(Str(test2json, "resolved_path"), args...)',
'"-test.v=test2json"','"-test.count=1"','"-test.timeout=180s"',
'len(os.Args)-1 == len(childArgs)','"-p", typedRuntimeFixtureJSONPackage, "-t", Str(childResource, "resolved_path")',
'"child.stdout.jsonl"','"child.stdout.raw"','"child.stderr.raw"','"child-invocation.json"',
'"child-result.json"','"child-event-verdict.json"','"parent-result.json"',
'"actual_runner_exit": exit','"actual_native_child_exit": nil','"actual_parent_exit": nil',
'"PENDING_ROOT_RECONCILIATION"','"PENDING_ROOT_GO_JOB"','"REQUIRES_ROOT_GO_JOB_RECEIPT"',
'resourcesStable && eventErr == nil','len(raw) == resource["bytes"].(int)',
'"formal_acceptance": false','"authority": "NONE"']
for needle in required:assert needle in revised,needle
for forbidden in ("InsecureSkipVerify","t.Skip(", "t.Skipf(", "exec.Command(\"go\"", "go tool test2json"):
    assert forbidden not in revised,forbidden
assert all("handlerTLSRootsOnce.Do" in revised and "cert.Verify" in revised for _ in [0])
write_new("candidate-root/"+helper_rel,revised)
write_new("runtime_typed_client_fixture_windows_test.patch","".join(difflib.unified_diff(old.splitlines(keepends=True),revised.splitlines(keepends=True),fromfile=source.as_posix(),tofile=(Q/"candidate-root"/helper_rel).as_posix())))
base_refs.append(pin(source))
source_refs.append(pin(Q/"candidate-root"/helper_rel))
checks.append({"relative_path":helper_rel,"changed":True,"normal_TLS_configuration_profile_provider_attach_tail_byte_equal_4396":True,"prefix_only_adds_runtime_time_utf8_imports":True,"lexical_delimiters_balanced":True,"strict_JSONL_required_source_checks":len(required),"ordinary_RUN_PASS_substring_evidence_removed":True,"Go_tool_auto_build_not_invoked":True,"Root_official_test2json_binary_direct":True})
prior_base=json.loads((BASE/"base-refs.json").read_text(encoding="utf-8"))
original_pins=prior_base["refs"]
original_call_count=0
original_if_count=0
original_strict_if_count=0
original_tests=0
for p in original_pins:
    actual=pin(Path(p["path"]))
    assert actual==p
    original=Path(p["path"]).read_text(encoding="utf-8")
    candidate=(Q/"candidate-root"/("internal/domain/"+Path(p["path"]).name)).read_text(encoding="utf-8")
    ots,nts=tokens(original),tokens(candidate)
    old_calls,new_calls=call_nodes(ots),call_nodes(nts)
    old_ifs,new_ifs=assertion_if_nodes(ots),assertion_if_nodes(nts)
    assert all(collections.Counter(new_calls)[v]>=count for v,count in collections.Counter(old_calls).items())
    assert all(collections.Counter(new_ifs)[v]>=count for v,count in collections.Counter(old_ifs).items())
    old_names=re.findall(r"^func (Test\w+)\(t \*testing\.T\)",original,re.M)
    new_names=re.findall(r"^func (Test\w+)\(t \*testing\.T\)",candidate,re.M)
    assert old_names==new_names
    original_call_count+=len(old_calls)
    original_if_count+=len(old_ifs)
    original_strict_if_count+=sum(any(node[i:i+3] in [("t",".","Fatal"),("t",".","Fatalf"),("t",".","Error"),("t",".","Errorf")] for i in range(len(node)-2)) for node in old_ifs)
    original_tests+=len(old_names)
assert (original_call_count,original_if_count,original_strict_if_count,original_tests)==(181,196,190,20)
files=list((Q/"candidate-root").rglob("*"))
actual_files=sorted(p for p in files if p.is_file())
assert len(actual_files)==5 and all(p.name.endswith("_test.go") for p in actual_files)
inputs=base_refs+[pin(BASE/"MF.json"),pin(BASE/"HDF.json"),pin(BASE/"construct.py"),pin(BASE/"scope-map.json"),pin(REVIEW/"MF.json"),pin(REVIEW/"HDF.json"),pin(REVIEW/"report.md"),pin(REVIEW/"if-node-supplement.json")]+original_pins
write_new("base-refs.json",{"version":"SOURCE_REVISION_BASE_REFS_V1","refs":inputs})
write_new("source-refs.json",{"version":"SOURCE_REVISION_MEMBERS_V1","authority":"NONE","refs":source_refs,"changed_member_count":1,"unchanged_original_member_count":4,"production_member_count":0})
write_new("static-checks.json",{"version":"SOURCE_LEXICAL_CHECKS_ONLY_V1","Go_AST_or_compile_executed":False,"Go_native_SQL_model_private_execution":0,"Python_AST_used_only_to_extract_pinned_pure_lexical_utilities":True,"source_checks":checks,"original_calls_181_preserved":True,"original_test_names_20_preserved":True,"original_assertion_or_error_if_nodes_196_preserved":True,"original_strict_t_assertion_if_nodes_190_preserved":True,"additional_fmt_Errorf_if_nodes":6,"candidate_member_count":5,"changed_member_count":1,"source_authority":"NONE","formal_acceptance":False,"new_source_errors":[]})
write_new("resource-contract.json",{"authority":"NONE","execution_state":"NOT_EXECUTED","Root_required_environment":{"RESEARCHOS_GO":{"absolute_required":True,"SHA256":"d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490","use":"Go1.27.1 provenance only, not invoked by this helper"},"GOROOT":{"absolute_required":True,"VERSION_first_line":"go1.27.1","bin_go_same_file_as_RESEARCHOS_GO":True},"RESEARCHOS_TEST2JSON":{"absolute_required":True,"use":"Root built/frozen official cmd/test2json executable, no builtin/cache path assumption","binary_ref":"PENDING_ROOT_RESOURCE"},"RESEARCHOS_TEST2JSON_SHA256":{"format":"64 lowercase hexadecimal characters","expected_value":"PENDING_ROOT_RESOURCE"},"RESEARCHOS_NODE":{"use":"unchanged Root pinned Node input"},"RESEARCHOS_MU_BUNDLE":{"use":"unchanged Root immutable Mu bundle"},"RESEARCHOS_TYPED_RUNTIME_EVIDENCE_DIR":{"absolute_required":True,"fresh_run_required":True}},"exact_package":"researchos.local/research-os/internal/domain","Root_required_actual_closure":["official test2json Source/build/dependency/binary provenance","same compiled child pin","all test2json/compiled child/SDK descendant Job membership and cleanup","actual external parent JSONL, terminal event and exit","original 10 leaf results, no unexecuted/skipped acceptance"]})
print(json.dumps({"namespace":Q.as_posix(),"source_members":source_refs,"base_members_4396_unchanged":4,"helper_changed_only":True,"static_checks":pin(Q/"static-checks.json"),"source_refs":pin(Q/"source-refs.json"),"original_assertion_calls_preserved":original_call_count,"original_test_names_preserved":original_tests,"original_assertion_or_error_if_nodes_preserved":original_if_count,"original_strict_t_assertion_if_nodes_preserved":original_strict_if_count,"source_tail_byte_equal":True,"formal_acceptance":False},ensure_ascii=False))
