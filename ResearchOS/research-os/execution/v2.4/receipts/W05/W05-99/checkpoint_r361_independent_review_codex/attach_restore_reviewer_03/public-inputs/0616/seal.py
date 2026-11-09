import sys
sys.dont_write_bytecode = True
import hashlib
import json
import traceback
from pathlib import Path
O = Path(__file__).resolve().parent
def ref(p):
    b=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,obj):
    with (O/n).open("xb") as f:
        f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
def main():
    pins=json.loads((O/"revision/input-pins.json").read_bytes())
    assert all(ref(Path(r["path"])) == r for r in pins)
    guard=json.loads((O/"revision/guard-closure.json").read_bytes())
    assert all(g["closed"] and g["retained_handles_count"]==0 and not g["errors"] and g["verification"]=="PASSED" for g in guard)
    write("final-source-no-drift.json",{"checked":len(pins),"drift":[],"all_guards_closed":True})
    hdf={"schema":"researchos.independent-temp-source-handoff.v1","decision":"SOURCE_ACCEPTED_WITH_ROOT_EXECUTION_PREREQUISITES","authority":"NONE","formal_acceptance":False,"namespace":str(O),"report_ref":ref(O/"report.md"),"source_check_ref":ref(O/"revision/source-check.json"),"input_pins_ref":ref(O/"revision/input-pins.json"),"guard_closure_ref":ref(O/"revision/guard-closure.json"),"final_no_drift_ref":ref(O/"final-source-no-drift.json"),"failure846_ref":ref(O/"failure-origin.846.json"),"failed_tool_io_ref":ref(O/"failed-original-tool-io.json"),"revision_tool_io_ref":ref(O/"revision-tool-io.json"),"native_positive_accepted":False,"Go_SQL_native_model_run":False,"old_controller_proof_key_connected":False,"Root_next":"Fresh separately reviewed controller proof-key/environment/resource prerequisites; fresh compile; exactly two component parents/28 leaves; then one Root-owned manually approved fresh positive. Independent actual review required.","new_mechanical_errors":1,"failure_ordinals_preserved":[835,841,843,846],"Main_T7_author_canonical_writes":False,"stop":True}
    write("HDF.json",hdf)
    files=sorted(p for p in O.rglob("*") if p.is_file() and p.name not in ("MF.json","postseal-tool-io.json"))
    write("MF.json",{"schema":"researchos.independent-temp-source-manifest.v1","authority":"NONE","formal_acceptance":False,"members":[{"relative_path":p.relative_to(O).as_posix(),**ref(p)} for p in files],"exclusions":{"MF.json":"self fingerprint","postseal-tool-io.json":"final seal return separately pinned"}})
    print(json.dumps({"HDF":ref(O/"HDF.json"),"MF":ref(O/"MF.json"),"source_check":ref(O/"revision/source-check.json"),"member_count":len(files)},ensure_ascii=False))
code=0
try:
    main()
except Exception:
    traceback.print_exc()
    code=1
finally:
    print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)
