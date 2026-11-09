"""Only new routing-delta controls; all Main collaborators below are synthetic stubs."""
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;P=N/"w09_root_bridge.source.py"
raw=P.read_bytes();tree=ast.parse(raw,str(P))
m=types.ModuleType("bridge02_delta_subject");m.__file__=str(P)
exec(compile(tree,str(P),"exec"),m.__dict__)
rows=[]
def ok(name,condition):
 if not condition:raise AssertionError(name)
 rows.append({"name":name,"PASS":True,"kind":"PURE_DELTA_STUB_NOT_MAIN_RUNTIME"})
def reject(name,action,code):
 try:action()
 except ValueError as e:ok(name,code in str(e))
 else:raise AssertionError(name+": unexpectedly admitted")
context={"registered_commands":[]}
proofs={}
for route in m.ROUTES:
 key=route[1] or route[2]
 row=dict(zip(("command_key","check_id","case_id"),route))
 row.update(native_report_ref={"path":key+"/report","sha256":key},native_tool_run_ref={"path":key+"/tool","sha256":key},
   mode_decision_ref={"path":route[0]+key+"/mode","sha256":key},receipt_ref={"path":route[0]+key+"/receipt","sha256":key})
 context["registered_commands"].append(row);proofs[route]=({}, {}, {"mode":key}, ())
api=types.SimpleNamespace(_profile_api=lambda:None)
class Reader:
 def __init__(self):self.bridge_native_checks=copy.deepcopy(proofs)
 def path(self,name):return name
 def read(self,path):return {"revision":40}
 def document(self,ref):
  key=ref["selector"]
  return {"native_tool_run_ref":key+"/tool","mode_evidence":{"mode":key},
          "source_pins":[{"path":key+"/report","sha256":key}]}
class Profile:
 def __init__(self):self.history=[];self.leases=[]
 def _doc(self,api,reader,ref,prefix):
  return {"stdout":{"selector":"C19"}}
 def _historical_registry(self,api,reader,row,receipt,registry,current_hash):
  self.history.append(row["command_key"]);return True
 def _route_execution_actor(self,api,reader,row,receipt,decision,authority):
  self.leases.append(row["command_key"])
req={"c19_policy":"RUN_CURRENT_CM40","c19_reuse_registry_ref":{"path":"synthetic"}}
m.document=lambda ref:{"roles":{"executor":m.ROOT_ACTOR}}
p=Profile();r=Reader();eng=(api,r,p);pinned={"execution/v2.4/commands.json":"exact-CM40"}
ok("fresh_current_six_routes",m.consumer_plan(req,eng,context,pinned)==m.ROUTES)
ok("fresh_does_not_claim_old_receipt_gate",p.history==[] and p.leases==[])
reuse=dict(req,c19_policy="REUSE_CURRENT_SOURCE21")
ok("reuse_after_both_existing_Main_gates",m.consumer_plan(reuse,eng,context,pinned)==m.NEW
   and p.history==["test.research.fixture","test.retrieval"] and p.leases==p.history)
reject("unknown_policy",lambda:m.consumer_plan(dict(req,c19_policy="FORCE_OLD"),eng,context,pinned),"C19_POLICY")
missing=Reader();missing.bridge_native_checks.pop(("test.retrieval","","C19"))
reject("missing_current_C19_gate",lambda:m.consumer_plan(req,(api,missing,Profile()),context,pinned),"MAIN_CURRENT_NATIVE_GATE_REQUIRED")
bad=copy.deepcopy(context);bad["registered_commands"][2]["native_report_ref"]["path"]="W09-G01/report"
reject("two_C19_bundles_must_match",lambda:m.consumer_plan(req,eng,bad,pinned),"SAME_SELECTOR_NATIVE_BUNDLE")
bad=copy.deepcopy(context)
for item in bad["registered_commands"]:
 if item["case_id"]=="C19":item["native_report_ref"]["path"]="W09-G01/report"
reject("three_native_cannot_replace_four",lambda:m.consumer_plan(req,eng,bad,pinned),"FOUR_CURRENT_NATIVE_REPORTS")
pfalse=Profile();pfalse._historical_registry=lambda *args:False
reject("not_fixed_CM39_cannot_reuse",lambda:m.consumer_plan(reuse,(api,Reader(),pfalse),context,pinned),"ONLY_FIXED_CM39_C19_REUSE")
for field in ("mode_evidence","native_tool_run_ref","source_pins"):
 badreader=Reader();original=badreader.document
 def mismatched(ref,field=field,original=original):
  output=original(ref);output[field]=[] if field=="source_pins" else "different";return output
 badreader.document=mismatched
 reject("historical_output_"+field+"_binding",lambda:m.consumer_plan(reuse,(api,badreader,Profile()),context,pinned),"HISTORICAL_CONSUMER_SAME_NATIVE")
def rejectlease(*args):raise ValueError("MAIN_EXECUTION_LEASE")
lease=Profile();lease._route_execution_actor=rejectlease
reject("historical_lease_failure_not_waived",lambda:m.consumer_plan(reuse,(api,Reader(),lease),context,pinned),"MAIN_EXECUTION_LEASE")
# Exercise new native_inputs orchestration with an existing-Main rejection represented as a stub.
maincalls=[]
class NativeProfile:
 def _vector(self,*args):return {}
 def _trusted_closure(self,*args):return {}
 def _router_contract(self,*args):return {}
 def _producer_sources(self,*args):return set()
 def _native(self,api,reader,row,*args):
  maincalls.append(row["check_id"] or row["case_id"])
  raise ValueError("MAIN_SOURCE21_CHANGED")
m.document=lambda ref:copy.deepcopy(context)
reject("current_Source21_failure_stops_before_plan",lambda:m.native_inputs({"context_seed_ref":{}},(api,Reader(),NativeProfile())),"MAIN_SOURCE21_CHANGED")
ok("Source21_rejection_not_retried",len(maincalls)==1)
source=raw.decode()
ok("Scope_command_keys_and_exact_selectors", 'routes = list(dict.fromkeys(route[0] for route in planned))' in source
  and 'routes=routes, route_bindings=route_bindings' in source)
ok("registered_plan_cannot_expand_silently",'"REGISTERED_EXACT_CONSUMER_ROUTES"' in source
  and '"REGISTERED_C19_POLICY"' in source and '"PROPOSAL_C19_POLICY"' in source)
ok("CM40_pin_unchanged",m.TRUSTED["execution/v2.4/commands.json"]==
 ("12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97",67323))
inverse=json.loads((N/"exact-inverse.json").read_bytes());back=source
for delta in reversed(inverse["edits"]):back=back.replace(delta["after"],delta["before"])
ok("exact_v1_inverse",hashlib.sha256(back.encode()).hexdigest()==inverse["base_ref"]["sha256"])
result={"schema":"researchos.bridge02-finite-delta-controls.v1","status":"PASS","controls":rows,
 "count":len(rows),"subject":{"path":str(P),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)},
 "Main_executed":False,"Native_TP_dispatcher_model_calls":0,"old_controls_rerun":False,"execution_grant":False}
with (N/"delta-controls.json").open("x",encoding="utf-8") as out:
 json.dump(result,out,ensure_ascii=False,indent=2);out.write("\n")
print(json.dumps({"status":"PASS","delta_controls":len(rows),"subject":result["subject"]}))

