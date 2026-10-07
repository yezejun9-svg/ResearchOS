from pathlib import Path
import json,sys
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'execution/v2.4'))
import formal_case_index as api
import formal_profile_w07 as profile
context=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"));reader=api.Reader(ROOT);results=[]
pinned,tools=profile._vector(api,reader,context)
proof=reader.document(context["proof_ref"])
for name,action in [("product",lambda:profile.product(api,reader,context,tools)),("_dispatches",lambda:profile._dispatches(api,reader,context,pinned,proof))]:
 try:action();results.append({"stage":name,"status":"PASS"})
 except api.InvalidEvidence as exc:results.append({"stage":name,"status":"FAIL","code":exc.code,"detail":str(exc)})
reader.finish()
print(json.dumps({"status":"PRE_REGISTRATION_REJECTED" if any(r["status"]=="FAIL" for r in results) else "PRE_REGISTRATION_NO_ACCEPTANCE","stages":results,"formal_acceptances":0}))
sys.exit(1 if any(r["status"]=="FAIL" for r in results) else 0)
