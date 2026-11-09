import sys
sys.dont_write_bytecode=True
import hashlib,json,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
def ref(p):
    raw=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def write(n,v):
    with (O/n).open("xb") as f:
        f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
def main():
    refs=json.loads((O/"revision/input-pins.json").read_bytes())
    current=[(r,ref(Path(r["path"]))) for r in refs]
    content_drift=[r["path"] for r,a in current if (r["sha256"],r["bytes"])!=(a["sha256"],a["bytes"])]
    canonical_mismatch=[r["path"] for r,a in current if str(Path(r["path"])).casefold()!=str(Path(a["path"])).casefold()]
    assert not content_drift and not canonical_mismatch
    g=json.loads((O/"revision/guard-closure.json").read_bytes())
    assert all(x["verification"]=="PASSED" and x["closed"] and x["retained_handles_count"]==0 and not x["errors"] for x in g)
    write("final-no-drift.json",{"checked":len(refs),"sha_bytes_drift":content_drift,"canonical_path_mismatches":canonical_mismatch,"all_guards_closed":True})
    hdf={"schema":"researchos.independent-CTL3-source-handoff.v1","authority":"NONE","formal_acceptance":False,"decision":"SOURCE_ACCEPTED_PENDING_ROOT_FRESH_CONTEXT_AND_ACTUAL","namespace":str(O),"report_ref":ref(O/"report.md"),"source_check_ref":ref(O/"revision/source-check.json"),"input_pins_ref":ref(O/"revision/input-pins.json"),"guard_closure_ref":ref(O/"revision/guard-closure.json"),"final_no_drift_ref":ref(O/"final-no-drift.json"),"original_tool_io_ref":ref(O/"original-tool-io.json"),"failure850_ref":ref(O/"failure-origin.850.json"),"candidate_ref":json.loads((O/"revision/source-check.json").read_bytes())["candidate_ref"],"full_manifests_checked":{"CTL3":31,"CTL2":13,"EnvSource":27},"guarded_public_inputs":len(refs),"other_definitions_raw_AST_unchanged":30,"inverse_CTL2_bytes_equal":True,"boundary_expected_count":16,"boundary_actual":"NOT_RUN","context_helper_controller_observer_executed":False,"actual_native_formal_accepted":False,"new_mechanical_errors":1,"new_failure_ordinal":850,"original_failures_not_reset":True,"Root_next":"Fresh fixed full public context/retained guard and resources; fresh compile/component/native evidence under existing Root authority; independent actual review required.","Main_canonical_old_Source_writes":False,"stop":True}
    write("HDF.json",hdf)
    files=sorted(p for p in O.rglob("*") if p.is_file() and p.relative_to(O).as_posix() not in ("MF.json","postseal-tool-io.json"))
    write("MF.json",{"schema":"researchos.independent-CTL3-source-manifest.v1","authority":"NONE","formal_acceptance":False,"members":[{"relative_path":p.relative_to(O).as_posix(),**ref(p)} for p in files],"exclusions_exact_relative_paths":["MF.json","postseal-tool-io.json"]})
    print(json.dumps({"HDF":ref(O/"HDF.json"),"MF":ref(O/"MF.json"),"source_check":ref(O/"revision/source-check.json"),"member_count":len(files)},ensure_ascii=False))
code=0
try: main()
except Exception:
    traceback.print_exc()
    code=1
finally: print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)

