import sys
sys.dont_write_bytecode=True
import hashlib,json,re,traceback
from datetime import datetime,timezone
from pathlib import Path
Q=Path(__file__).resolve().parent
def ref(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def verify(item):
    actual=ref(item["path"])
    assert actual["sha256"]==item["sha256"] and actual["bytes"]==item["bytes"],"fingerprint mismatch"
def load(name): return json.loads((Q/name).read_text(encoding="utf-8"))
def write(name,value):
    with (Q/name).open("x",encoding="utf-8",newline="\n") as f: f.write(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
def excerpt(path,name):
    lines=Path(path).read_text(encoding="utf-8").splitlines()
    starts=[n for n,line in enumerate(lines) if re.match(r"^func\s+"+re.escape(name)+r"\s*\(",line)]
    assert len(starts)==1
    start=starts[0]; following=[n for n in range(start+1,len(lines)) if lines[n].startswith("func ")]
    end=following[0] if following else len(lines)
    return {"source_ref":ref(path),"function":name,"start_line":start+1,"end_line":end,
            "lines":[{"line":n+1,"text":lines[n]} for n in range(start,end)]}
def main():
    info=load("inspection.json"); st=load("static-evidence.json"); actual=load("actual835-public-evidence.json"); failure=load("failure-origin.841.json")
    verify(info["base_ref"]); verify(info["TTL_HDF_ref"]); verify(info["TTL_MF_ref"]); verify(info["compile_closed_ref"])
    verify(st["candidate_ref"]); verify(st["minimal_diff_ref"])
    for row in info["snapshots"]:
        verify(row["source_ref"]); verify(row["snapshot_ref"])
    for group in info["compile_bindings"].values():
        verify(group["actual_ref"]); assert group["closed_matching_refs"]
    for row in info["TTL_member_checks"]: verify(row["actual_ref"])
    for key in ["failure835_ref","test_invocation_ref","test_stdout_ref","test_stderr_ref"]: verify(actual[key])
    assert st["exact_inverse_recovers_entire_T7_bytes"] and st["original_assertion_calls"]==84
    assert st["candidate_assertion_calls"]==90 and st["missing_original_assertions"]==[]
    assert failure["ordinal"]==841 and failure["actual_outer_exit"]==1 and failure["actual_Python_exit"] is None
    assert failure["ROOT_PYTHON_EXIT_marker"] is None and failure["inferred_Python_exit"]==1
    p=Path(st["candidate_ref"]["path"])
    chain=[excerpt(p,name) for name in [
        "nativeHarnessBroker","nativeHarnessBrokerPublicEnvironment","nativeHarnessTempWithin",
        "TestNativeHarnessBrokerIsolatedTempEnvironment","TestNativeHarnessBrokerTempBoundaryComparison"]]
    write("call-chain-excerpts.json",{"authority":"NONE","static_only":True,"excerpts":chain,
          "backup_MkdirTemp_ref":next(row["source_ref"] for row in info["snapshots"] if Path(row["source_ref"]["path"]).name=="backup_prepared_abandonment_upgrade.go"),
          "backup_MkdirTemp_lines":info["backup_MkdirTemp_lines"]})
    tests=["TestNativeHarnessBrokerIsolatedTempEnvironment","TestNativeHarnessBrokerTempBoundaryComparison"]
    write("public-environment-contract.json",{
        "authority":"NONE","formal_acceptance":False,
        "Root_harness_only_public_proof_key":"RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT",
        "Root_required_values":"fixed isolated absolute existing physical temp root; TEMP/TMP contained in that root",
        "forwarded_keys_exactly":["SystemRoot","WINDIR","TEMP","TMP"],
        "proof_key_forwarded":False,"os_Environ_inherited":False,
        "guards":st["physical_checks"],"CWD_Schema_timeout180_privatepipe_unchanged":True,
        "Root_source_only_authorization":"explicit parent message adopted this fixed key and strict Root public environment boundary",
        "new_test_selectors":tests,
        "targeted_component_regex":"^(TestNativeHarnessBrokerIsolatedTempEnvironment|TestNativeHarnessBrokerTempBoundaryComparison)$",
        "new_component_leaf_count":28,"new_component_leaf_names":st["added_env_leaf_names"],
        "physical_junction_execution_claimed":False,"root_fresh_positive_native_case_after_review":True,
        "execution_status":"NOT_RUN","native_authority":"NONE",
    })
    write("source-pins.json",{
        "authority":"NONE","base_ref":info["base_ref"],"candidate_ref":st["candidate_ref"],
        "TTL_HDF_ref":info["TTL_HDF_ref"],"TTL_MF_ref":info["TTL_MF_ref"],
        "T7_compile_closed_ref":info["compile_closed_ref"],
        "T7_formatted_and_actual_inventory_refs":{k:v["actual_ref"] for k,v in info["compile_bindings"].items()},
        "T7_selected_source_binding_refs":info["formatted_source_matches"]+info["compiler_inventory_source_matches"],
        "TTL_candidate_equals_actual_T7":True,"input_snapshots":info["snapshots"],
        "original835_public_refs":{k:actual[k] for k in ["failure835_ref","test_invocation_ref","test_stdout_ref","test_stderr_ref"]},
        "failure841_ref":ref(Q/"failure-origin.841.json"),"minimal_diff_ref":st["minimal_diff_ref"],
    })
    hdf={
        "schema":"researchos.native-broker-temp-source-handoff.v1",
        "created_at":datetime.now(timezone.utc).isoformat(),"namespace":str(Q),
        "authority":"NONE","formal_acceptance":False,
        "status":"SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_FRESH_ACTUAL",
        "candidate_ref":st["candidate_ref"],"base_ref":info["base_ref"],
        "compile_closed_ref":info["compile_closed_ref"],
        "TTL_HDF_ref":info["TTL_HDF_ref"],"TTL_MF_ref":info["TTL_MF_ref"],
        "source_pins_ref":ref(Q/"source-pins.json"),"contract_ref":ref(Q/"CONTRACT.md"),
        "public_environment_contract_ref":ref(Q/"public-environment-contract.json"),
        "call_chain_excerpts_ref":ref(Q/"call-chain-excerpts.json"),
        "static_evidence_ref":ref(Q/"static-evidence.json"),
        "minimal_diff_ref":st["minimal_diff_ref"],
        "actual835_public_evidence_ref":ref(Q/"actual835-public-evidence.json"),
        "failure841_ref":ref(Q/"failure-origin.841.json"),
        "original_tool_io_ref":ref(Q/"original-tool-io.json"),
        "change_scope":{"candidate_test_files":1,"three_broker_environment_replacements":True,
                       "two_synthetic_helper_Test_functions_added":True,
                       "original84_assertions_preserved":True,"candidate_assertion_calls":90,
                       "original9_native_cases_unchanged":True,
                       "TTL15min_grant4min_Schema_CWD_Sourcepins_privatepipe_180s_unchanged":True,
                       "exact_inverse_recovers_entire_T7":True},
        "Root_next":{"review":"independent Source review first",
                     "build":"fresh guarded isolated composition/compiler/resource freezes",
                     "component_tests":tests,"component_leaf_count":28,
                     "native":"one fresh positive under Root owned Jobs and explicit approvals; no old attempt replay",
                     "public_environment":"Root fixed harness sets proof-root plus TEMP/TMP; proof key never forwarded"},
        "execution":{"fixed_Python_flags":"-I -S -B -X utf8",
                     "inspection_and_actual_public_read_and_revision_construct_markers":0,
                     "failed_first_construct_actual_outer":1,"failed_first_construct_marked_Python":None,
                     "failed_first_construct_inferred_Python":1,
                     "seal_result_pending_postseal_IO":True,
                     "Go_AST":None,"Go":None,"gofmt":None,"compiler":None,"SQL":None,
                     "native":None,"model":None,"private_payloads_read":False},
        "failure_history":{"new_mechanical_errors":1,"new_ordinal":841,
                           "835_and_all_history_preserved":True,"no_count_reset":True,
                           "old_failed_construct_not_retried":True},
        "writes":{"unique_namespace_only":True,"Main":0,"T5":0,"T6":0,"T7":0,
                  "old_Source":0,"production":0,"canonical":0,"baseline_lock_held":False},
        "manifest_exclusions":{"MF.json":"top-level self fingerprint only",
                               "postseal-tool-io.json":"later seal/write invocation IO, separately pinned"},
    }
    write("HDF.json",hdf)
    members=[]
    for p in sorted(Q.rglob("*")):
        if p.is_file():
            relative=p.relative_to(Q).as_posix()
            if relative not in {"MF.json","postseal-tool-io.json"}:
                members.append({"relative_path":relative,**ref(p)})
    write("MF.json",{"schema":"researchos.native-broker-temp-source-manifest.v1","authority":"NONE",
          "formal_acceptance":False,"status":hdf["status"],"members":members,
          "exclusions":hdf["manifest_exclusions"]})
    for item in members: verify(item)
    print(json.dumps({"authority":"NONE","formal_acceptance":False,"status":hdf["status"],
          "refs":{name:ref(Q/name) for name in ["HDF.json","MF.json","CONTRACT.md","source-pins.json",
                  "public-environment-contract.json","call-chain-excerpts.json","static-evidence.json",
                  "broker-temp.patch","actual835-public-evidence.json","failure-origin.841.json","original-tool-io.json"]},
          "candidate_ref":st["candidate_ref"],"member_count":len(members),
          "new_test_selectors":tests,"component_leaf_count":28,
          "new_mechanical_errors":1,"failure841_Python_actual":None,"failure841_Python_inferred":1,
          "prior835_not_reset":True,"Go_SQL_native_model_execution":None},ensure_ascii=False))
code=0
try: main()
except Exception: traceback.print_exc(); code=1
finally: print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)

