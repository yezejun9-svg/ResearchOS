import sys
sys.dont_write_bytecode = True
import ast
import difflib
import hashlib
import json
import traceback
from pathlib import Path

Q = Path(__file__).resolve().parent

def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def verify(value):
    actual = ref(value["path"])
    assert (actual["sha256"],actual["bytes"]) == (value["sha256"],value["bytes"]), "pinned input differs"

def save(name, value):
    raw = (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    with (Q/name).open("xb") as stream:
        assert stream.write(raw) == len(raw)
    return ref(Q/name)

def main():
    inspection = json.loads((Q/"inspection.json").read_text(encoding="utf-8"))
    verify(inspection["base_HDF_ref"]); verify(inspection["base_MF_ref"]); verify(inspection["base_ref"])
    for value in inspection["all_base_MF_member_refs_verified"]:
        verify(value)
    for pair in inspection["snapshots"]:
        verify(pair["source_ref"]); verify(pair["snapshot_ref"])
    raw = Path(inspection["base_ref"]["path"]).read_bytes()
    before = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in before else "\n"
    old = '        if set(request["Environment"]) != {"SystemRoot", "WINDIR"}:\n            raise ValueError("native environment must be the fixed public pair")\n'.replace("\n",newline)
    new = '        require_public_environment(request["Environment"])\n'.replace("\n",newline)
    helper = '''
def require_public_environment(env):
    expected = {"SystemRoot", "WINDIR", "TEMP", "TMP"}
    if not isinstance(env, dict) or set(env) != expected:
        raise ValueError("native environment must be the fixed public four keys")
    if any(not isinstance(value, str) or not value.strip() or "\\0" in value
           for value in env.values()):
        raise ValueError("nonempty public environment strings required")
    if env["TEMP"] != env["TMP"]:
        raise ValueError("fixed TEMP TMP binding differs")

    def contains(parent, child):
        parent_key, child_key = str(parent).casefold(), str(child).casefold()
        try:
            return os.path.commonpath([parent_key, child_key]) == parent_key
        except ValueError:
            return False

    def directory(value):
        path = Path(value)
        if not path.is_absolute() or str(path.resolve()).casefold() != str(path).casefold():
            raise ValueError("canonical absolute public directory required")
        if not path.is_dir():
            raise ValueError("existing public directory required")
        return path

    local = Path("D:/作品集/ResearchOS/research-os/.local")
    trial = local/"mu-sdk-isolated-project-ed84838046934329a76733a005c9b162"
    declared = Path(os.path.normpath(env["TEMP"]))
    if not declared.is_absolute() or declared == local or not contains(local, declared):
        raise ValueError("temporary directory must be a child of repository local directory")
    # Reject the original trial namespace before resolving/statting proof paths.
    # Directory metadata only: no file reads, directory listing or private resource.
    if contains(trial, declared) or contains(declared, trial):
        raise ValueError("original trial temporary directory forbidden")
    local = directory(str(local))
    root = directory(env["TEMP"])
    if root == local or not contains(local, root):
        raise ValueError("physical temporary directory outside isolated local root")
    physical_trial = local/"mu-sdk-isolated-project-ed84838046934329a76733a005c9b162"
    if contains(physical_trial, root) or contains(root, physical_trial):
        raise ValueError("original trial physical temporary directory forbidden")
    for name in ("SystemRoot", "WINDIR"):
        system = directory(env[name])
        if contains(system, root) or contains(root, system):
            raise ValueError("temporary directory overlaps system directory")

'''.replace("\n",newline)
    assert before.count(old)==1 and before.count("def main():")==1
    after = before.replace(old,new,1).replace("def main():",helper+"def main():",1)
    inverse = after.replace(helper,"",1).replace(new,old,1)
    assert inverse.encode("utf-8") == raw
    btree, atree = ast.parse(before), ast.parse(after)
    compile(atree,"root_only_native_broker.py","exec")
    bdefs = {n.name:n for n in btree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    adefs = {n.name:n for n in atree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    assert set(adefs)==set(bdefs)|{"require_public_environment"}
    unchanged = []
    for name in bdefs:
        if name!="main":
            assert ast.dump(bdefs[name],include_attributes=False)==ast.dump(adefs[name],include_attributes=False)
            assert ast.get_source_segment(before,bdefs[name])==ast.get_source_segment(after,adefs[name])
            unchanged.append(name)
    main_after = ast.get_source_segment(after,adefs["main"])
    restored_main = ast.parse(main_after.replace(new,old,1)).body[0]
    assert ast.dump(restored_main,include_attributes=False)==ast.dump(bdefs["main"],include_attributes=False)
    helper_node = adefs["require_public_environment"]
    calls = [n for n in ast.walk(helper_node) if isinstance(n,ast.Call)]
    assert not any(isinstance(n.func,ast.Name) and n.func.id in
        {"open","raw_pin","require_pin","read_private_pipe","write_new","main"} for n in calls)
    assert not any(isinstance(n.func,ast.Attribute) and n.func.attr in
        {"read_bytes","read_text","open","iterdir","glob","rglob","exec_module","run_owned_private_stdin"}
        for n in calls)
    assert "os.environ" not in helper.casefold()
    main_calls = [n for n in ast.walk(adefs["main"]) if isinstance(n,ast.Call)]
    guard_line = next(n.lineno for n in main_calls if isinstance(n.func,ast.Name) and n.func.id=="require_public_environment")
    private_line = next(n.lineno for n in main_calls if isinstance(n.func,ast.Name) and n.func.id=="read_private_pipe")
    import_line = next(n.lineno for n in main_calls if isinstance(n.func,ast.Attribute) and n.func.attr=="exec_module")
    child_line = next(n.lineno for n in main_calls if isinstance(n.func,ast.Attribute) and n.func.attr=="run_owned_private_stdin")
    spec_line = next(n.lineno for n in main_calls if isinstance(n.func,ast.Attribute) and n.func.attr=="spec_from_file_location")
    mkdir_line = next(n.lineno for n in main_calls if isinstance(n.func,ast.Attribute) and n.func.attr=="mkdir")
    assert guard_line < min(private_line,import_line,child_line,spec_line,mkdir_line)
    unit_path = Q/"broker_temp_environment_boundary_test.py"
    unit_source = unit_path.read_text(encoding="utf-8")
    unit_tree = ast.parse(unit_source)
    compile(unit_tree,unit_path.name,"exec")
    unit_class = next(n for n in unit_tree.body if isinstance(n,ast.ClassDef) and n.name=="PublicEnvironmentBoundaryTests")
    test_names = [n.name for n in unit_class.body if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")]
    assert len(test_names)==17
    no_process_methods = {"Popen","run","call","check_call","check_output","system","spawn","run_owned","run_owned_private_stdin","read_private_pipe","main"}
    unit_test_nodes = [n for n in unit_class.body if isinstance(n,ast.FunctionDef)]
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in no_process_methods
        for function in unit_test_nodes for n in ast.walk(function))
    candidate_path = Q/"root_only_native_broker.py"
    with candidate_path.open("xb") as stream:
        encoded = after.encode("utf-8")
        assert stream.write(encoded)==len(encoded)
    patch = "".join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
        fromfile="base/root_only_native_broker.py",tofile="candidate/root_only_native_broker.py"))
    with (Q/"broker-temp-env.patch").open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(patch)
    save("exact-inverse-edits.json",{"schema":"researchos.python-broker-exact-inverse.v1",
        "authority":"NONE","base_ref":inspection["base_ref"],"candidate_ref":ref(candidate_path),
        "old_single_guard":old,"new_single_guard":new,"inserted_helper_text":helper,
        "inverse_procedure":"remove inserted_helper_text once, replace new_single_guard with old_single_guard once",
        "complete_base_bytes_restored":True})
    result = {"authority":"NONE","formal_acceptance":False,"base_ref":inspection["base_ref"],
        "candidate_ref":ref(candidate_path),"patch_ref":ref(Q/"broker-temp-env.patch"),
        "boundary_test_Source_ref":ref(unit_path),"boundary_test_names":test_names,
        "boundary_Source_test_count":len(test_names),"boundary_actual":"NOT_RUN",
        "unchanged_other_top_level_raw_AST_definitions":unchanged,
        "main_AST_after_exact_single_guard_inverse_equals_base":True,
        "complete_base_bytes_exact_inverse":True,
        "guard_before_output_creation_import_private_pipe_child":{
            "guard_line":guard_line,"mkdir_line":mkdir_line,"spec_line":spec_line,
            "helper_import_line":import_line,"private_pipe_line":private_line,"native_child_line":child_line},
        "new_ENV_exact_four_only":["SystemRoot","WINDIR","TEMP","TMP"],
        "proof_provider_secret_userprofile_extra_keys_rejected":True,
        "no_whole_environment_inheritance":True,"new_helper_directory_metadata_only":True,
        "Schema_CWD_RawPins_PrivateStdin_Timeout_wipe_ownedhelper_returnexit_error_suppression_publisher_unchanged":True,
        "Python_AST_compile_only":True,"broker_or_unit_Source_imported":False,
        "private_pipe_context_SQL_native_model_sign_execution":None,
        "new_mechanical_errors":0,"original868_and_historical_failures_counter_not_reset":True}
    static_ref=save("static-evidence.json",result)
    print(json.dumps({"authority":"NONE","candidate_ref":result["candidate_ref"],
        "patch_ref":result["patch_ref"],"static_ref":static_ref,
        "boundary_Source_test_count":len(test_names),"boundary_actual":"NOT_RUN",
        "unchanged_original_definition_count":len(unchanged),"main_single_guard_only":True,
        "env_guard_precedes_private_import_child":True,"new_mechanical_errors":0},ensure_ascii=False))

code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
