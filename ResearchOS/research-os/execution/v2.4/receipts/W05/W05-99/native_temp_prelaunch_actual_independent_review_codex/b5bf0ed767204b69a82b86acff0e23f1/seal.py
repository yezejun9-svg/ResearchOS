import sys
sys.dont_write_bytecode=True
import json,hashlib,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
def main():
 review=json.loads((O/"revision/source-check.json").read_bytes())
 assert review["decision"]=="COMPONENT_ACCEPTED_PRELAUNCH_CONDITIONAL" and len(review["checks"])==95 and all(x["passed"] for x in review["checks"])
 guards=json.loads((O/"revision/guard-closure.json").read_bytes())
 assert all(g["closed"] and g["verification"]=="PASSED" and g["retained_handles_count"]==0 and not g["errors"] for g in guards)
 h={"schema":"researchos.independent-native-temp-prelaunch-handoff.v1","authority":"NONE","formal_acceptance":False,"decision":review["decision"],"namespace":str(O),"report_ref":pin(O/"report.md"),"source_check_ref":pin(O/"revision/source-check.json"),"input_pins_ref":pin(O/"revision/input-pins.json"),"guard_closure_ref":pin(O/"revision/guard-closure.json"),"actual_jobs_ref":pin(O/"revision/actual-owned-jobs.json"),"caller_baseline_pins_ref":pin(O/"revision/own-callers-and-baseline-pins.json"),"full_original_tool_io_ref":pin(O/"original-tool-io.json"),"failure856_ref":pin(O/"failure-origin.856.json"),"failure858_ref":pin(O/"failure-origin.858.json"),"original_false_negative_verdict_ref":pin(O/"source-check.json"),"checks_passed":95,"checks_total":95,"guarded_public_inputs":4590,"actual_compile_unit_context_components_accepted":True,"fixed_callers_Source_accepted":True,"Root_may_one_manually_approved_fresh_synthetic_positive":True,"independent_native_positive_accepted":False,"Owner_nine_cases_original_business_formal_accepted":False,"reviewer_Go_native_context_SQL_sign_model_execution":False,"global_provider_requests":None,"formal_progress":"0/42","new_mechanical_errors":2,"new_failure_ordinals":[856,858],"history_reset":False,"canonical_Source_Main_writes":False,"stop":True}
 save("HDF.json",h)
 files=sorted(p for p in O.rglob("*") if p.is_file() and p.relative_to(O).as_posix() not in ("MF.json","postseal-tool-io.json"))
 save("MF.json",{"schema":"researchos.independent-native-temp-prelaunch-manifest.v1","authority":"NONE","formal_acceptance":False,"members":[{"relative_path":p.relative_to(O).as_posix(),**pin(p)} for p in files],"exclusions_exact_relative_paths":["MF.json","postseal-tool-io.json"]})
 print(json.dumps({"HDF":pin(O/"HDF.json"),"MF":pin(O/"MF.json"),"source_check":pin(O/"revision/source-check.json"),"member_count":len(files)},ensure_ascii=False))
code=0
try:main()
except Exception:traceback.print_exc();code=1
finally:print("ROOT_PYTHON_EXIT="+str(code))
sys.exit(code)

