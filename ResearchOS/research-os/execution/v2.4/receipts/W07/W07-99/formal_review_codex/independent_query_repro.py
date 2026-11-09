from pathlib import Path
import importlib.util,json,copy,os
p=Path(os.environ["W07_CANDIDATE_ROOT"])/"execution/v2.4/formal_profile_w07_test.py";s=importlib.util.spec_from_file_location("query_helpers",p);m=importlib.util.module_from_spec(s);exec(compile(p.read_bytes(),str(p),"exec"),m.__dict__)
m.W07RawControls.setUpClass()
try:
 t=m.W07RawControls();row=copy.deepcopy(t.template["source_invocations"][0]);report=m.PROFILE._document(m.API,t.reader(),row["report_ref"]);inputs=m.PROFILE._document(m.API,t.reader(),row["request_inputs_ref"]);original=report["query"]
 report["query"]=inputs["query"]="forged unrelated query that never ran"
 row["report_ref"]=t.write_control("query-forged-report.json",report);row["stdout_ref"]=row["report_ref"];row["request_inputs_ref"]=t.write_control("query-forged-input.json",inputs)
 reader=t.reader()
 try:m.PROFILE._source(m.API,reader,row,t.bounds,{},t.template["live_binary_ref"]);reader.finish();result="ACCEPTED"
 except Exception as e:result="REJECTED: "+str(e)
 print(json.dumps({"classification":"INDEPENDENT_LOW_LEVEL_SOURCE_NEGATIVE_NOT_CURRENT","original_query":original,"forged_query":report["query"],"db_modified":False,"result":result},indent=2))
finally:m.W07RawControls.tearDownClass()
