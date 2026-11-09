import ast,difflib,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
Q=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_digest_revision_codex/794a6ecddad942d69e6f8fb19bcc2e49")
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_jsonl_revision_codex/3adf21aec07c4b5db6eb2fcf317f85e9")
ORIGINAL=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_source_codex/4396cf0cc13f1f247afbd3c567b1d931")
OFFICIAL=Path("D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/src/cmd/internal/test2json/test2json.go")
T5=Path("D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2")
ROOT_RESOURCE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/official-test2json-resource-build-root-3e9129c5f7c9461e")
def pin(p):
    raw=p.read_bytes()
    return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def new(name,content):
    p=Q/name;p.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(content,bytes):
        with p.open("xb") as f:f.write(content)
    else:
        text=content if isinstance(content,str) else json.dumps(content,ensure_ascii=False,indent=2)+"\n"
        with p.open("x",encoding="utf-8",newline="\n") as f:f.write(text)
def replace_one(text,before,after):
    assert text.count(before)==1,before
    return text.replace(before,after,1)
assert (pin(BASE/"MF.json")["sha256"],pin(BASE/"MF.json")["bytes"])==("65cd84d5c0b440f0c70acbb808c1960102bf03107e10aca1a83f0081f7035ca4",5997)
mf=json.loads((BASE/"MF.json").read_text(encoding="utf-8"))
for member in mf["members"]:assert pin(Path(member["path"]))==member,member
selected=ROOT_RESOURCE/"selected-official-compiler-inputs.json"
assert (pin(selected)["sha256"],pin(selected)["bytes"])==("4f7c76bea3116f31806ef15f655e692f7507e34585fc10e9a0be5e9507e77287",190768)
inventory=json.loads(selected.read_text(encoding="utf-8"))
entry=inventory["build_inputs"][748]
actual=pin(OFFICIAL)
assert (actual["sha256"],actual["bytes"])==(entry["sha256"],entry["bytes"])==("81b811cc3af1cc49da5faec1a93aabf12b769a69a5dbc60505c125edb19d288b",19217)
official=OFFICIAL.read_text(encoding="utf-8")
assert 'OutputType  string     '+chr(96)+'json:",omitempty"'+chr(96) in official
for marker in ['func (c *Converter) writeOutputEvent(', 'typ = "frame"', 'typ = "error"', 'typ = "error-continue"', 'typ = ""', 'Action:     "output"']:
    assert marker in official,marker
digest_source=T5/"internal/domain/contracts.go"
digest_text=digest_source.read_text(encoding="utf-8")
assert 'return "sha256:" + hex.EncodeToString(h[:])' in digest_text
utilities=ast.parse((ORIGINAL/"construct.py").read_text(encoding="utf-8"))
pure=[n for n in utilities.body if isinstance(n,ast.FunctionDef) and n.name in {"tokens","balanced"}]
assert {n.name for n in pure}=={"tokens","balanced"}
ns={}
exec(compile(ast.Module(body=pure,type_ignores=[]),str(ORIGINAL/"construct.py"),"exec"),ns)
refs=json.loads((BASE/"source-refs.json").read_text(encoding="utf-8"))["refs"]
base_refs=[]
source_refs=[]
checks=[]
helper="runtime_typed_client_fixture_windows_test.go"
for item in refs:
    path=Path(item["path"])
    raw=path.read_bytes()
    assert pin(path)==item
    base_refs.append(item)
    dest=Q/"candidate-root/internal/domain"/path.name
    if path.name!=helper:
        new(dest.relative_to(Q).as_posix(),raw)
        assert dest.read_bytes()==raw
        source_refs.append(pin(dest))
        checks.append({"file":path.name,"byte_equal_Q2_and_4396":True,"changes":0})
        continue
    old=raw.decode("utf-8")
    revised=replace_one(old,'\tOutput *string\n','\tOutput *string\n\tOutputType *string\n')
    revised=replace_one(revised,'\t\tcase "Elapsed":\n', '''\t\tcase "OutputType":
\t\t\tvar outputType string
\t\t\terr = json.Unmarshal(value, &outputType)
\t\t\tevent.OutputType = &outputType
\t\tcase "Elapsed":
''')
    revised=replace_one(revised,'\tif _, err := time.Parse(time.RFC3339Nano, event.Time); err != nil {\n', '''\t// Fixed Go1.27.1 emits OutputType only on output; it never grants a
\t// run/pass verdict. Preserve presence to reject it even empty on other actions.
\tif event.OutputType != nil && (event.Action != "output" || (*event.OutputType != "" && *event.OutputType != "frame" && *event.OutputType != "error" && *event.OutputType != "error-continue")) {
\t\treturn event, fmt.Errorf("OutputType differs from fixed Go1.27.1 output schema")
\t}
\tif _, err := time.Parse(time.RFC3339Nano, event.Time); err != nil {
''')
    revised=replace_one(revised,'if expectedSHA != "" && Digest(raw) != expectedSHA {','if expectedSHA != "" && Digest(raw) != "sha256:"+expectedSHA {')
    assert ns["balanced"](ns["tokens"](revised))
    before_state=old[old.index("func typedRuntimeFixtureVerifyJSONL("):old.index("func typedRuntimeFixturePin(")]
    after_state=revised[revised.index("func typedRuntimeFixtureVerifyJSONL("):revised.index("func typedRuntimeFixturePin(")]
    assert before_state==after_state
    marker="func typedRuntimeFixtureChild("
    assert old[old.index(marker):]==revised[revised.index(marker):]
    assert 'typedRuntimeFixtureGoSHA256 = "d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490"' in revised
    assert 'return Object{"requested_path": path, "resolved_path": resolved, "sha256": Digest(raw), "bytes": len(raw)}' in revised
    assert 'fields[key]' in revised and 'decoder.Decode(&trailing); err != io.EOF' in revised
    assert 'bytes.Equal(value, []byte("null"))' in revised
    assert '"FailedBuild"' not in revised and '"Key"' not in revised and '"Value"' not in revised and '"Path"' not in revised
    assert "bytes.Contains(stdout" not in revised
    new(dest.relative_to(Q).as_posix(),revised)
    source_refs.append(pin(dest))
    new("runtime_typed_client_fixture_windows_test.patch","".join(difflib.unified_diff(old.splitlines(keepends=True),revised.splitlines(keepends=True),fromfile=path.as_posix(),tofile=dest.as_posix())))
    checks.append({"file":helper,"changed":True,"Digest_compare_uses_single_explicit_sha256_prefix":True,"saved_pin_Digest_format_unchanged":True,"fixed_Go_bare_hash_constant_unchanged":True,"OutputType_presence_pointer_string":True,"OutputType_only_output":True,"OutputType_allowed_values":["","frame","error","error-continue"],"omitted_OutputType_allowed":True,"unknown_duplicate_null_type_trailing_guards_unchanged":True,"complete_JSONL_state_machine_byte_equal_Q2":True,"entire_child_TLS_configuration_profile_provider_attach_tail_byte_equal_Q2":True,"FailedBuild_attr_artifact_fields_not_generalized":True,"lexical_delimiters_balanced":True})
assert len(source_refs)==5
new("source-refs.json",{"authority":"NONE","refs":source_refs,"changed_member_count":1,"unchanged_original_member_count":4,"production_member_count":0})
inputs=base_refs+[pin(BASE/"MF.json"),pin(BASE/"HDF.json"),pin(BASE/"static-checks.json"),pin(BASE/"base-refs.json"),pin(ORIGINAL/"construct.py"),pin(selected),pin(OFFICIAL),pin(digest_source),pin(ROOT_RESOURCE/"resource-build.closed.json")]
new("base-refs.json",{"authority":"NONE","refs":inputs,"selected_inventory_entry":entry,"selected_inventory_entry_index":748})
new("static-checks.json",{"authority":"NONE","formal_acceptance":False,"checks":checks,"Go_AST_compile_native_SQL_model_private_execution":0,"original_181_calls_20_Test_names_196_assertion_or_error_if_190_strict_t_nodes_inherited_byte_equal":True,"new_source_errors":[],"failure_counter_reset":False})
new("official-outputtype-contract.json",{"authority":"NONE","official_source":pin(OFFICIAL),"inventory":pin(selected),"inventory_entry":748,"line_refs":{"event_OutputType":38,"run_sets_framing":[378,380,386],"writeOutputEvent":[425,508]},"field":"OutputType","type":"optional string, nonnull when present","presence_allowed_action":"output","allowed_values":["","frame","error","error-continue"],"omitted_allowed":True,"nonoutput_presence_even_empty_rejected":True,"Output_or_OutputType_terminal_authority":False,"scope_still_rejects":["fail","attr","artifact","artifacts","unknown action or key","FailedBuild","Key","Value","Path"]})
print(json.dumps({"namespace":Q.as_posix(),"source_members":source_refs,"helper_changed_only":True,"four_originals_byte_equal_Q2":True,"JSONL_state_machine_byte_equal_Q2":True,"child_and_TLS_tail_byte_equal_Q2":True,"official_source":pin(OFFICIAL),"selected_inventory":pin(selected),"source_refs":pin(Q/"source-refs.json"),"static_checks":pin(Q/"static-checks.json"),"new_source_errors":0,"Go_native_SQL_model_execution":0,"authority":"NONE","formal_acceptance":False},ensure_ascii=False))
