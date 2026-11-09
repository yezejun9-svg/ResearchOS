import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
import traceback
from pathlib import Path

Q = Path(__file__).resolve().parent

def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def verify(pin):
    actual = ref(pin["path"])
    assert (actual["sha256"],actual["bytes"])==(pin["sha256"],pin["bytes"]), "fingerprint differs"
    return actual

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save(name, value):
    raw = (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    with (Q/name).open("xb") as stream:
        assert stream.write(raw)==len(raw)
    return ref(Q/name)

def main():
    inspection, static = read(Q/"inspection.json"), read(Q/"static-evidence.json")
    for field in ("base_HDF_ref","base_MF_ref","base_ref","failure868_ref"):
        verify(inspection[field])
    for pin in inspection["all_base_MF_member_refs_verified"]:
        verify(pin)
    for pair in inspection["snapshots"]:
        verify(pair["source_ref"]); verify(pair["snapshot_ref"])
    for field in ("base_ref","candidate_ref","patch_ref","boundary_test_Source_ref"):
        verify(static[field])
    assert static["candidate_ref"]["sha256"]=="70b8eba1de168849d041488ac9268da60fd2ae8a059cc9518e9dc93d0cd4b87c"
    assert static["candidate_ref"]["bytes"]==8562
    base_raw = Path(static["base_ref"]["path"]).read_bytes()
    candidate_raw = (Q/"root_only_native_broker.py").read_bytes()
    candidate = candidate_raw.decode("utf-8")
    inverse = read(Q/"exact-inverse-edits.json")
    assert candidate.count(inverse["inserted_helper_text"])==1
    restored = candidate.replace(inverse["inserted_helper_text"],"",1)
    assert restored.count(inverse["new_single_guard"])==1
    restored = restored.replace(inverse["new_single_guard"],inverse["old_single_guard"],1)
    assert restored.encode("utf-8")==base_raw
    ctree, btree = ast.parse(candidate), ast.parse(base_raw.decode("utf-8"))
    compile(ctree,"root_only_native_broker.py","exec")
    cdefs = {n.name:n for n in ctree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    bdefs = {n.name:n for n in btree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    assert set(cdefs)==set(bdefs)|{"require_public_environment"}
    for name in static["unchanged_other_top_level_raw_AST_definitions"]:
        assert ast.dump(cdefs[name],include_attributes=False)==ast.dump(bdefs[name],include_attributes=False)
        assert ast.get_source_segment(candidate,cdefs[name])==ast.get_source_segment(base_raw.decode("utf-8"),bdefs[name])
    assert len(static["unchanged_other_top_level_raw_AST_definitions"])==4
    main_inverse = ast.get_source_segment(candidate,cdefs["main"]).replace(inverse["new_single_guard"],inverse["old_single_guard"],1)
    assert ast.dump(ast.parse(main_inverse).body[0],include_attributes=False)==ast.dump(bdefs["main"],include_attributes=False)
    source_lines = candidate.splitlines()
    excerpts=[]
    for name in ("require_pin","require_public_environment","read_private_pipe","main"):
        node=cdefs[name]
        excerpts.append({"name":name,"source_ref":static["candidate_ref"],"line":node.lineno,"end_line":node.end_lineno,
            "lines":[{"line":index+1,"text":source_lines[index]} for index in range(node.lineno-1,node.end_lineno)]})
    excerpts_ref=save("source-call-chain-excerpts.json",{"authority":"NONE","excerpts":excerpts,"source_executed":False})
    unit_source=(Q/"broker_temp_environment_boundary_test.py").read_text(encoding="utf-8")
    unit_tree=ast.parse(unit_source); compile(unit_tree,"broker_temp_environment_boundary_test.py","exec")
    unit_class=next(n for n in unit_tree.body if isinstance(n,ast.ClassDef) and n.name=="PublicEnvironmentBoundaryTests")
    methods=[n for n in unit_class.body if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")]
    assert [n.name for n in methods]==static["boundary_test_names"]
    expected={methods[0].name:"PERMIT pure environment guard only", **{n.name:"REJECT" for n in methods[1:]}}
    cases=[{"test_name":n.name,"test_Source_ref":static["boundary_test_Source_ref"],
        "line":n.lineno,"end_line":n.end_lineno,"expected":expected[n.name],"actual":"NOT_RUN",
        "qualification":"synthetic public directories; alias/escape use metadata mock; no formal/native authority"}
        for n in methods]
    boundary_ref=save("boundary-matrix.json",{"schema":"researchos.python-broker-public-env-boundaries.v1",
        "authority":"NONE","formal_acceptance":False,"actual":"NOT_RUN","Source_test_method_count":len(methods),"cases":cases})
    environment_ref=save("public-environment-contract.json",{
        "schema":"researchos.python-broker-fixed-public-environment.v1","authority":"NONE",
        "exact_keys":["SystemRoot","WINDIR","TEMP","TMP"],
        "values":"nonempty nonwhitespace strings without NUL","TEMP_equals_TMP":"exact string",
        "TEMP_root":"absolute existing canonical strict child of fixed D:/作品集/ResearchOS/research-os/.local",
        "trial_root":"D:/作品集/ResearchOS/research-os/.local/mu-sdk-isolated-project-ed84838046934329a76733a005c9b162",
        "trial_namespace_reject":"lexical and physical root/descendant/ancestor; lexical proof guard before directory metadata",
        "system_reject":"canonical existing SystemRoot/WINDIR overlap in either ancestor direction",
        "whole_os_environment_inherited":False,"controller_proof_key_forwarded_to_broker":False,
        "guard_reads":"directory metadata only","guard_precedes":static["guard_before_output_creation_import_private_pipe_child"],
        "legacy_two_key_requests":"REJECT; original failure868 immutable",
        "no_private_resource_read_or_Snapshot":True,"actual_guard_validation":"NOT_RUN"})
    root_mapping_ref=save("root-actual-public-prerequisites.json",{
        "schema":"researchos.python-broker-root-actual-prerequisites.v1","authority":"NONE","formal_acceptance":False,
        "Source_units":{"Python":"C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe",
            "argv":["-I","-S","-B","-X","utf8",str(Q/"broker_temp_environment_boundary_test.py"),
                    "--broker-source",static["candidate_ref"]["path"],"--broker-sha256",static["candidate_ref"]["sha256"],
                    "--verbosity","2"],
            "boundary_Source_pin":static["boundary_test_Source_ref"],"actual":"NOT_RUN",
            "Root_required":"fixed Python/resource guards; actual stdout/stderr/exit; no broker private-pipe/native helper invocation"},
        "native_runtime":{"BrokerSource_RawPin_required":{
            "role":"broker-source",
            "path":static["candidate_ref"]["path"],"sha256":"sha256:"+static["candidate_ref"]["sha256"],
            "bytes":static["candidate_ref"]["bytes"]},
            "role_contract_ref":{"source_ref":next(pin for pin in inspection["all_base_MF_member_refs_verified"]
                if pin["relative_path"]=="candidate-root/internal/domain/native_migration_authority_harness_windows_test.go"),
                "line":295,"scope":"actual pinned original role assertion; Root reconciles unchanged role in T8 actual composition"},
            "Root_must_bind":"fresh HarnessConfig.BrokerSource + exact FrozenInputs + public cfg refs + full retained Source guard",
            "request_Environment":"exact four keys only; Go proof key stays in controller/harness boundary",
            "compiled_provenance":"preserve all T8 actual compiler/product/test/embed pins and receipts; reconcile runtime new PythonSource pins without assuming cache/closure",
            "actual":"NOT_RUN","private_stdin_sign_release_Job_original_database_gates":"unchanged Root requirements"},
        "Root_reported_prior_inputs":{"T8_compile_28_units_CTL3_context_resource_independently_accepted":
            "Parent task reports existing actual acceptance; not re-executed/self-accepted by this author",
            "failure868_ref":inspection["failure868_ref"]},
        "original_trial_or_private_files_opened":False})
    closure_ref=save("source-guard-closure.json",{
        "schema":"researchos.python-broker-Source-static-closure.v1","authority":"NONE",
        "base_HDF_ref":inspection["base_HDF_ref"],"base_MF_ref":inspection["base_MF_ref"],
        "base_MF_actual_shape":"dict","base_member_count":inspection["actual_base_member_count"],
        "all_base_member_refs_reverified":inspection["all_base_MF_member_refs_verified"],
        "copied_input_source_and_snapshot_refs_reverified":inspection["snapshots"],
        "candidate_ref":static["candidate_ref"],"boundary_Source_ref":static["boundary_test_Source_ref"],
        "actual_Root_retained_guard":"NOT_RUN; Root requires full fresh runtime public resource closure",
        "Root_prerequisites_ref":root_mapping_ref,"old_Sources_Main_canonical_Tstar_writes":0,
        "failure868_and_all_history_counter_unchanged":True,"new_mechanical_errors":0})
    original_io_ref=ref(Q/"original-tool-io.json")
    assert read(Q/"original-tool-io.json")["calls"]
    hdf_ref=save("HDF.json",{
        "schema":"researchos.python-broker-temp-env-source-handoff.v1","authority":"NONE",
        "formal_acceptance":False,"status":"SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL",
        "packet_root":str(Q),"candidate_ref":static["candidate_ref"],"base_ref":static["base_ref"],
        "base_HDF_ref":inspection["base_HDF_ref"],"base_MF_ref":inspection["base_MF_ref"],
        "failure868_original_and_snapshot_refs":next(pair for pair in inspection["snapshots"] if Path(pair["source_ref"]["path"]).name=="failure-origin.868.json"),
        "contract_ref":ref(Q/"CONTRACT.md"),"delta_ref":static["patch_ref"],"inverse_ref":ref(Q/"exact-inverse-edits.json"),
        "static_ref":ref(Q/"static-evidence.json"),"source_call_chain_ref":excerpts_ref,"Source_guard_closure_ref":closure_ref,
        "public_environment_ref":environment_ref,"boundary_Source_ref":static["boundary_test_Source_ref"],
        "boundary_matrix_ref":boundary_ref,"Root_actual_prerequisites_ref":root_mapping_ref,
        "original_tool_io_ref":original_io_ref,"exact_single_guard_replace_and_one_helper_insert":True,
        "unchanged_other_definition_count":4,"exact_inverse_recovers_all_base_bytes":True,
        "boundary_Source_test_method_count":17,"all_boundary_actual":"NOT_RUN",
        "controller_broker_unit_import_or_guard_call_performed":False,
        "Go_native_SQL_privatepipe_crypto_sign_model_context_execution":None,
        "old_Sources_Main_canonical_Tstar_writes":0,"new_mechanical_errors":0,
        "failure868_all_history_counter_not_reset":True,
        "Root_next":"non-author Source review then fixed pure boundary actual; fresh runtime BrokerSource/frozen guards; Root native case under existing authority",
        "MF_exclusions_exact_relative_paths":["MF.json","postseal-tool-io.json"]})
    members=[]
    for path in sorted(Q.rglob("*"),key=lambda p:p.relative_to(Q).as_posix()):
        if path.is_file():
            relative=path.relative_to(Q).as_posix()
            if relative not in {"MF.json","postseal-tool-io.json"}:
                members.append(dict(ref(path),relative_path=relative))
    assert any(pin["relative_path"]=="inputs/base/MF.json" for pin in members)
    mf_ref=save("MF.json",{"schema":"researchos.python-broker-temp-env-source-manifest.v1",
        "authority":"NONE","formal_acceptance":False,"HDF_ref":hdf_ref,"members":members,
        "exclusions_exact_relative_paths":["MF.json","postseal-tool-io.json"]})
    for pin in members:
        verify(pin)
    print(json.dumps({"authority":"NONE","formal_acceptance":False,"HDF_ref":hdf_ref,"MF_ref":mf_ref,
        "candidate_ref":static["candidate_ref"],"boundary_Source_ref":static["boundary_test_Source_ref"],
        "contract_ref":ref(Q/"CONTRACT.md"),"delta_ref":static["patch_ref"],
        "inverse_ref":ref(Q/"exact-inverse-edits.json"),"Source_guard_closure_ref":closure_ref,
        "member_count":len(members),"base_actual_member_count":inspection["actual_base_member_count"],
        "all_boundary_actual":"NOT_RUN","new_mechanical_errors":0,"stop_after_seal":True},ensure_ascii=False))

code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
