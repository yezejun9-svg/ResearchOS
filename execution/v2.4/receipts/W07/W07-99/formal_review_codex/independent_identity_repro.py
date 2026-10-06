from pathlib import Path
import importlib.util,json,os
p=Path(os.environ["W07_CANDIDATE_ROOT"])/"execution/v2.4/formal_profile_w07_test.py";s=importlib.util.spec_from_file_location("identity_helpers",p);m=importlib.util.module_from_spec(s);exec(compile(p.read_bytes(),str(p),"exec"),m.__dict__)
m.W07RawControls.setUpClass()
try:
 t=m.W07RawControls();rows=[]
 for case,reviewer in [("case_alias_self_review","FIXTURE-EXECUTOR"),("root_self_delivered_review","codex:/root")]:
  owner,cp,rp,ip,c=t.independent_control()
  review=m.API.strict_json(rp.read_bytes());issuance=m.API.strict_json(ip.read_bytes());message=m.PROFILE._document(m.API,t.reader(),issuance["delivery_ref"])
  review["reviewer_id"]=reviewer;rr=t.write_control(case+"review.json",review)
  message.update(sender=reviewer,review_ref=rr,content="Shape-only counterfeit: review "+rr["sha256"]+" proof "+c["proof_ref"]["sha256"]);mr=t.write_control(case+"message.json",message)
  issuance.update(reviewer_id=reviewer,review_ref=rr,delivery_ref=mr);ir=t.write_control(case+"issuance.json",issuance)
  reader=t.reader()
  try:m.PROFILE._independent(m.API,reader,owner,cp,t.repo/rr["path"],t.repo/ir["path"],c);reader.finish();result="ACCEPTED"
  except Exception as e:result="REJECTED: "+str(e)
  rows.append({"scenario":case,"executor":c["executor_id"],"reviewer":reviewer,"observer":"codex:/root","result":result})
 print(json.dumps({"classification":"SHAPE_NEGATIVE_ONLY_NOT_CURRENT_ACCEPTANCE","results":rows},indent=2))
finally:m.W07RawControls.tearDownClass()
