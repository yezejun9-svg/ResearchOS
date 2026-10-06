from pathlib import Path
import importlib.util,json,copy,os
candidate=Path(os.environ["W07_CANDIDATE_ROOT"])
p=candidate/"execution/v2.4/formal_profile_w07_test.py"
s=importlib.util.spec_from_file_location("independent_candidate_test_helpers",p);m=importlib.util.module_from_spec(s);exec(compile(p.read_bytes(),str(p),"exec"),m.__dict__)
m.W07RawControls.setUpClass()
try:
 t=m.W07RawControls();results=[]
 for scenario in ("baseline_h07","arbitrary_non_go_h07_argv","missing_run_and_package_completion_events","cached_h07_test_result"):
  row=copy.deepcopy(t.template["h07_invocations"][0])
  if scenario=="arbitrary_non_go_h07_argv":row["actualargv"]=["C:/nonexistent/forged-python.exe","-c","print(1)"]
  if scenario in {"missing_run_and_package_completion_events","cached_h07_test_result"}:
   events=[m.API.strict_json(x) for x in m.PROFILE._bytes(m.API,t.reader(),row["stdout_ref"]).splitlines()]
   if scenario=="missing_run_and_package_completion_events":events=[x for x in events if x.get("Action") not in {"run","start"} and not(x.get("Action")=="pass" and not x.get("Test"))]
   else:
    row["actualargv"]=[str(Path(row["actualargv"][0])),"test","-json","./internal/domain"]
    for x in events:
     if not x.get("Test") and x.get("Action")=="output" and "ok" in x.get("Output",""):x["Output"]="ok production-package (cached)\n"
   row["stdout_ref"]=t.write_bytes(scenario+".jsonl",b"\n".join(json.dumps(x).encode() for x in events)+b"\n")
  reader=t.reader()
  try:
   rows=m.PROFILE._h07(m.API,reader,row,t.bounds);reader.finish();results.append({"scenario":scenario,"validator_result":"ACCEPTED","scenario_count":len(rows),"actualargv":row["actualargv"]})
  except Exception as e:results.append({"scenario":scenario,"validator_result":"REJECTED","error":str(e)})
 print(json.dumps({"classification":"INDEPENDENT_LOW_LEVEL_NEGATIVE_REPRO_NOT_CURRENT_ACCEPTANCE","results":results},ensure_ascii=False,indent=2))
 assert results[0]["validator_result"]=="ACCEPTED"
 assert all(r["validator_result"]=="ACCEPTED" for r in results[1:]),"candidate changed; inspect controls"
finally:m.W07RawControls.tearDownClass()
