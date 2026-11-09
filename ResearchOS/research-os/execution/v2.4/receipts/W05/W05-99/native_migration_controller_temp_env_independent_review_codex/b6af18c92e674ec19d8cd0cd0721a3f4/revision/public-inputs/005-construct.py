import sys
sys.dont_write_bytecode=True
import ast,difflib,hashlib,json,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
def ref(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def verify(item):
    a=ref(item["path"]); assert (a["sha256"],a["bytes"])==(item["sha256"],item["bytes"]),"fingerprint mismatch"
def main():
    inspected=json.loads((Q/"inspection.json").read_text(encoding="utf-8"))
    verify(inspected["base_controller_ref"])
    for pair in inspected["snapshots"]:
        verify(pair["source_ref"]); verify(pair["snapshot_ref"])
    raw=Path(inspected["base_controller_ref"]["path"]).read_bytes()
    base=raw.decode("utf-8"); newline="\r\n" if "\r\n" in base else "\n"
    old_global="    \"RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER_ROOT\", \"RESEARCHOS_NODE\", \"RESEARCHOS_MU_BUNDLE\",\n}".replace("\n",newline)
    new_global="    \"RESEARCHOS_CONFIGURATION_SCHEMA22_HELPER_ROOT\", \"RESEARCHOS_NODE\", \"RESEARCHOS_MU_BUNDLE\",\n    \"RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT\",\n}".replace("\n",newline)
    old_context="    if not {\"SystemRoot\", \"WINDIR\", \"TEMP\", \"TMP\"}.issubset(env):\n        raise ValueError(\"public Windows/temp environment required\")\n    for prefix in (\"RootProgram\", \"ControlProgram\"):".replace("\n",newline)
    new_context="    if not {\"SystemRoot\", \"WINDIR\", \"TEMP\", \"TMP\"}.issubset(env):\n        raise ValueError(\"public Windows/temp environment required\")\n    if \"RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT\" in env:\n        _require_isolated_temp_environment(env)\n    for prefix in (\"RootProgram\", \"ControlProgram\"):".replace("\n",newline)
    helper="\ndef _require_isolated_temp_environment(env):\n    proof_key = \"RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT\"\n    proof = env[proof_key]\n    if not isinstance(proof, str) or not proof.strip() or \"\\0\" in proof:\n        raise ValueError(\"isolated temporary proof root required\")\n    if env[\"TEMP\"] != proof or env[\"TMP\"] != proof:\n        raise ValueError(\"fixed proof root TEMP TMP binding differs\")\n\n    def contains(parent, child):\n        parent_key, child_key = str(parent).casefold(), str(child).casefold()\n        try:\n            return os.path.commonpath([parent_key, child_key]) == parent_key\n        except ValueError:\n            return False\n\n    local = Path(\"D:/作品集/ResearchOS/research-os/.local\")\n    trial = local/\"mu-sdk-isolated-project-ed84838046934329a76733a005c9b162\"\n    declared = Path(os.path.normpath(proof))\n    if not declared.is_absolute() or declared == local or not contains(local, declared):\n        raise ValueError(\"temporary proof root must be a child of this repository local directory\")\n    # Reject the original trial namespace before resolving/statting proof paths.\n    # Directory metadata only; no directory enumeration or private file reads.\n    if contains(trial, declared) or contains(declared, trial):\n        raise ValueError(\"original trial temporary root forbidden\")\n    local = canonical_path(str(local))\n    root = canonical_path(proof)\n    if not local.is_dir() or not root.is_dir() or root == local or not contains(local, root):\n        raise ValueError(\"isolated physical temporary directory unavailable\")\n    physical_trial = local/\"mu-sdk-isolated-project-ed84838046934329a76733a005c9b162\"\n    if contains(physical_trial, root) or contains(root, physical_trial):\n        raise ValueError(\"original trial physical temporary root forbidden\")\n    for name in (\"SystemRoot\", \"WINDIR\"):\n        system = canonical_path(env[name])\n        if not system.is_dir():\n            raise ValueError(\"public system directory unavailable\")\n        if contains(system, root) or contains(root, system):\n            raise ValueError(\"isolated temporary root overlaps system directory\")\n\n".replace("\n",newline)
    assert base.count(old_global)==1 and base.count(old_context)==1
    candidate=base.replace(old_global,new_global,1).replace(old_context,new_context,1)
    anchor="def context(config_ref):"
    assert candidate.count(anchor)==1
    candidate=candidate.replace(anchor,helper+anchor,1)
    inverse=candidate.replace(helper,"",1).replace(new_context,old_context,1).replace(new_global,old_global,1)
    assert inverse.encode("utf-8")==raw
    before,after=ast.parse(base),ast.parse(candidate)
    compile(after,"root_native_migration_controller.py","exec")
    base_defs={n.name:n for n in before.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    new_defs={n.name:n for n in after.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    assert set(new_defs)==set(base_defs)|{"_require_isolated_temp_environment"}
    unchanged=[]
    for name,node in base_defs.items():
        if name!="context":
            assert ast.dump(node,include_attributes=False)==ast.dump(new_defs[name],include_attributes=False)
            assert ast.get_source_segment(base,node)==ast.get_source_segment(candidate,new_defs[name])
            unchanged.append(name)
    old_env=next(n for n in before.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="ENV_KEYS" for t in n.targets))
    new_env=next(n for n in after.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="ENV_KEYS" for t in n.targets))
    oldkeys=ast.literal_eval(old_env.value); newkeys=ast.literal_eval(new_env.value)
    assert newkeys-oldkeys=={"RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT"} and not oldkeys-newkeys
    context_before=base_defs["context"]
    restored_context=ast.parse(ast.get_source_segment(candidate,new_defs["context"]).replace(
        '    if "RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT" in env:'+newline+'        _require_isolated_temp_environment(env)'+newline,"",1)).body[0]
    assert ast.dump(context_before,include_attributes=False)==ast.dump(restored_context,include_attributes=False)
    helpernode=new_defs["_require_isolated_temp_environment"]
    forbidden_calls={"open","public_ref","require_ref","read_ref","load_public_module","snapshot","sign_reviewed","publish_signed","release_fixture"}
    calls=[n for n in ast.walk(helpernode) if isinstance(n,ast.Call)]
    assert not any(isinstance(n.func,ast.Name) and n.func.id in forbidden_calls for n in calls)
    assert not any(isinstance(n.func,ast.Attribute) and n.func.attr in {"read_bytes","read_text","open","iterdir","glob","rglob"} for n in calls)
    assert "os.environ" not in helper.casefold()
    output=Q/"root_native_migration_controller.py"
    with output.open("xb") as f: f.write(candidate.encode("utf-8"))
    diff="".join(difflib.unified_diff(base.splitlines(True),candidate.splitlines(True),fromfile="CTL2/root_native_migration_controller.py",tofile="CTL3/root_native_migration_controller.py"))
    with (Q/"controller-temp-env.patch").open("x",encoding="utf-8",newline="\n") as f: f.write(diff)
    result={"authority":"NONE","formal_acceptance":False,"source_execution":False,
       "base_ref":ref(Path(inspected["base_controller_ref"]["path"])),"candidate_ref":ref(output),
       "patch_ref":ref(Q/"controller-temp-env.patch"),"exact_inverse_restores_CTL2_bytes":True,
       "old_ENV_KEYS":sorted(oldkeys),"new_ENV_KEYS":sorted(newkeys),"only_new_ENV_KEY":"RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT",
       "all_other_top_level_functions_classes_raw_and_AST_equal":unchanged,
       "context_AST_after_remove_optional_guard_equals_CTL2":True,
       "controller_schema_case9_atomicpublication_signing_owner_jobclosure_privatepipe_unchanged":True,
       "existing_context_string_unknownkey_frozencompiled_pin_gates_unchanged":True,
       "legacy_cfg_without_proof_guard_keeps_prior_context_behavior":True,
       "new_helper_no_file_contents_reads_or_private_Snapshot_import":True,
       "observer_snapshot_ref":next(x["snapshot_ref"] for x in inspected["snapshots"] if Path(x["snapshot_ref"]["path"]).name=="windows_owned_observed.py"),
       "API_snapshot_ref":next(x["snapshot_ref"] for x in inspected["snapshots"] if Path(x["snapshot_ref"]["path"]).name=="root-controller-api.json"),
       "Python_AST_compile_only_no_controller_import":True,"Go_native_SQL_signing_crypto_model_execution":None,
       "new_mechanical_errors":0,"prior835_841_843_and_all_history_not_reset":True}
    (Q/"static-evidence.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"authority":"NONE","candidate_ref":result["candidate_ref"],"patch_ref":result["patch_ref"],
         "inverse_equal":True,"unchanged_function_count":len(unchanged),"new_key":result["only_new_ENV_KEY"],
         "new_helper_no_file_contents_reads":True,"controller_imported":False,
         "actual_context_helper_or_launch_calls":0,"new_mechanical_errors":0},ensure_ascii=False))
code=0
try: main()
except Exception: traceback.print_exc(); code=1
finally: print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)

