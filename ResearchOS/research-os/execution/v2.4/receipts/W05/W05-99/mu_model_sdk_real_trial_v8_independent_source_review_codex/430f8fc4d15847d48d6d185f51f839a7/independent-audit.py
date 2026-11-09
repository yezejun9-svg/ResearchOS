import ast,copy,difflib,hashlib,json,os,stat
from pathlib import Path
R=Path(r"D:\作品集\ResearchOS\research-os");O=R/"execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_independent_source_review_codex/430f8fc4d15847d48d6d185f51f839a7"
S=R/"execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v8_source_codex/8251b1ed21754f7cbd6c2f8e7ff574eb"
OLD=R/"execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v7_source_codex/73cdde53fe0e4da2ae29fb6898d4b7ef/mu_sdk_trial.v7.final.proposed.py"
checks=[];pins={};controls=[]
def ck(n,v,d=None):checks.append({"name":n,"passed":bool(v),"detail":d})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);b=p.read_bytes();key=p.relative_to(R).as_posix();pins[key]={"path":key,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)};return b
def j(p):return json.loads(read(p))
def ref(p):p=path(p);read(p);return pins[p.relative_to(R).as_posix()]
def verify(r):
 b=read(r["path"]);ck("pin:"+r["path"],hashlib.sha256(b).hexdigest()==r["sha256"] and len(b)==r["bytes"]);return b
def allrefs(x):
 if isinstance(x,dict):
  if set(x)>={"path","sha256","bytes"}:yield {k:x[k] for k in ("path","sha256","bytes")}
  else:
   for v in x.values():yield from allrefs(v)
 elif isinstance(x,(list,tuple)):
  for v in x:yield from allrefs(v)
h=j(S/"handoff.json");mf=j(S/"manifest.json")
for r in allrefs(h):verify(r)
for r in mf["members"]:verify(r)
actual={p.relative_to(R).as_posix() for p in S.iterdir() if p.is_file()}
declared={path(r["path"]).relative_to(R).as_posix() for r in mf["members"]}
ck("source_inventory_exact",actual==declared|{(S/"manifest.json").relative_to(R).as_posix(),(S/"handoff.json").relative_to(R).as_posix()})
oldraw=read(OLD);newraw=verify(h["source_ref"]);old=oldraw.decode("utf8");new=newraw.decode("utf8")
ck("old_v7_exact_pin",hashlib.sha256(oldraw).hexdigest()=="d527eaf03d83208751c046d024747cb42bdc2f806474f8dda7f8ae70c2716a98" and len(oldraw)==84032)
ot,nt=ast.parse(old),ast.parse(new)
of={n.name:n for n in ot.body if isinstance(n,ast.FunctionDef)};nf={n.name:n for n in nt.body if isinstance(n,ast.FunctionDef)}
changed=[n for n in of if ast.dump(of[n])!=ast.dump(nf[n])]
ck("40_functions_only_validate_input_ast_changes",len(of)==len(nf)==40 and of.keys()==nf.keys() and changed==["validate_input"])
ck("39_function_bytes_unchanged",all(ast.get_source_segment(old,of[n])==ast.get_source_segment(new,nf[n]) for n in of if n!="validate_input"))
def literal_assigns(tree):
 out={}
 for n in tree.body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
   try:out[n.targets[0].id]=ast.literal_eval(n.value)
   except (ValueError,TypeError):pass
 return out
oa,na=literal_assigns(ot),literal_assigns(nt)
newnames={"SDK_FIVE_GO_COMMIT_REF","CANCEL_V4_CANCEL_REF","CANCEL_V4_ROOT_IO_REF","CANCEL_V4_BUILD_INTENT_REF","FIVE_GO_MAIN_REFS"}
ck("only_expected_constants",set(na)-set(oa)==newnames and {k for k in oa if oa[k]!=na[k]}=={"SOURCE_COMMIT"})
ck("limits_phase_basis_unchanged",all(oa[k]==na[k] for k in ("MAX_PROVIDER_REQUESTS","MAX_OUTPUT_TOKENS_TOTAL_REQUESTED","MAX_OUTPUT_TOKENS_PER_REQUEST","MAX_WALL_SECONDS","PHASE_BASIS_KEYS")) and [na[k] for k in ("MAX_PROVIDER_REQUESTS","MAX_OUTPUT_TOKENS_TOTAL_REQUESTED","MAX_OUTPUT_TOKENS_PER_REQUEST","MAX_WALL_SECONDS")]==[3,8192,2730,300])
reconstructed=new
for n in nt.body:
 if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in newnames:
  reconstructed=reconstructed.replace(ast.get_source_segment(new,n)+"\n","",1)
reconstructed=reconstructed.replace(na["SOURCE_COMMIT"],oa["SOURCE_COMMIT"],1)
reconstructed=reconstructed.replace(ast.get_source_segment(new,nf["validate_input"]),ast.get_source_segment(old,of["validate_input"]),1)
ck("full_inverse_exact_old_bytes",reconstructed.encode("utf8")==oldraw)
insertion="".join(ast.get_source_segment(new,n)+"\n" for n in nt.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in newnames)
forward=old.replace(oa["SOURCE_COMMIT"],na["SOURCE_COMMIT"],1).replace('ROOT = Path("D:/作品集/ResearchOS/research-os")\n','ROOT = Path("D:/作品集/ResearchOS/research-os")\n'+insertion,1)
forward=forward.replace(ast.get_source_segment(old,of["validate_input"]),ast.get_source_segment(new,nf["validate_input"]),1)
ck("full_forward_exact_new_bytes",forward.encode("utf8")==newraw)
fd="".join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=OLD.as_posix(),tofile=path(h["source_ref"]["path"]).as_posix()))
rd="".join(difflib.unified_diff(new.splitlines(True),old.splitlines(True),fromfile=path(h["source_ref"]["path"]).as_posix(),tofile=OLD.as_posix()))
ck("full_author_forward_diff_matches",fd==verify(h["forward_diff_ref"]).decode("utf8").replace("\r\n","\n"))
ck("full_author_inverse_diff_matches",rd==verify(h["inverse_diff_ref"]).decode("utf8").replace("\r\n","\n"))
for n,t in (("independent.forward.diff",fd),("independent.inverse.diff",rd)):
 with (O/n).open("x",encoding="utf8",newline="\n") as f:f.write(t)
for name in newnames:
 for r in allrefs(na[name]):verify(r)
template=j(h["input_template_ref"]["path"]);ck("template_binding",template["source_commit"]==na["SOURCE_COMMIT"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and template["cancel_fixture_receipt"]==na["CANCEL_V4_CANCEL_REF"])
ck("unissued_template_authorities",all(template[k] is None for k in ("input_basis_ref","root_registration","root_review","root_grant","owner_lease","root_checkpoint","outer_job_contract","job_probe_receipt","controller_source","controller_review","cli_binary","bootstrap_receipt")))
# Compile only strict readonly helpers and the exact changed AST spans, never the runner or main.
helpers=[n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name in {"require","json_file","pin_file"}]
env={"Path":Path,"hashlib":hashlib,"json":json,"stat":stat,"ROOT":R,**na}
exec(compile(ast.Module(body=helpers,type_ignores=[]),"<three-readonly-helpers>","exec"),env)
v=nf["validate_input"]
commit_start=next(i for i,n in enumerate(v.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="committed" for t in n.targets))
commit_nodes=v.body[commit_start:commit_start+3]
execute=next(n for n in v.body if isinstance(n,ast.If) and ast.unparse(n.test)=='mode == \'execute\'')
cancel_start=next(i for i,n in enumerate(execute.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="cancel" for t in n.targets))
cancel_nodes=execute.body[cancel_start:]
commit_code=compile(ast.Module(body=commit_nodes,type_ignores=[]),"<exact-new-commit-block>","exec")
cancel_code=compile(ast.Module(body=cancel_nodes,type_ignores=[]),"<exact-new-cancel-block>","exec")
def run_commit():
 exec(commit_code,env)
def run_cancel(doc):
 env["doc"]=doc
 env["pin_file"](doc["cancel_fixture_receipt"],"cancel fixture original")
 exec(cancel_code,env)
def control(name,fn,reject=False):
 try:
  fn();ok=not reject;error=None
 except ValueError as e:ok=reject;error=str(e)
 controls.append({"name":name,"passed":ok,"expected_rejection":reject,"error":error})
control("actual_frozen_commit_block_accepts",run_commit)
control("actual_v4_cancel_block_accepts",lambda:run_cancel(copy.deepcopy(template)))
wrong=copy.deepcopy(template);wrong["cancel_fixture_receipt"]["sha256"]="0"*64
control("tampered_receipt_pin_rejected",lambda:run_cancel(wrong),True)
# Payload overrides test only semantic branches after their real immutable pin checks.
realjson=env["json_file"];overrides={}
def overridden(p):
 d=copy.deepcopy(realjson(p));fn=overrides.get(str(Path(p)).casefold())
 return fn(d) if fn else d
env["json_file"]=overridden
def changed_payload(ref,mutation,operation):
 overrides[str(Path(ref["path"])).casefold()]=mutation
 try:operation()
 finally:overrides.clear()
cancelref=na["CANCEL_V4_CANCEL_REF"];cancel=j(cancelref["path"])
cases=[
 ("old_cancel_schema",cancelref,lambda x:{**x,"schema":"legacy"}),
 ("nonzero_cancel_result",cancelref,lambda x:{**x,"native_exit":1}),
 ("external_provider_usage",cancelref,lambda x:{**x,"actual_external_provider_requests":1}),
 ("missing_invocation",cancelref,lambda x:{**x,"invocation_refs":[]}),
 ("incomplete_native_cleanup",cancel["invocation_refs"][1],lambda x:{**x,"result":{**x["result"],"job_cleanup":{**x["result"]["job_cleanup"],"job_idle_confirmed":False}}}),
 ("wrong_actual_bundle_path",cancel["invocation_refs"][1],lambda x:{**x,"environment":{**x["environment"],"RESEARCHOS_MU_BUNDLE":"wrong"}}),
 ("wrong_case_selector",cancel["invocation_refs"][1],lambda x:{**x,"argv":["go","test","-run","Other"]}),
 ("wrong_metadata_worker_hash",cancel["bundle_metadata_ref"],lambda x:{**x,"source_sha256":"0"*64}),
 ("failed_root_terminal",na["CANCEL_V4_ROOT_IO_REF"],lambda x:{**x,"terminal":{**x["terminal"],"result":{**x["terminal"]["result"],"exit_code":1}}}),
 ("wrong_root_commit",na["SDK_FIVE_GO_COMMIT_REF"],lambda x:{**x,"new_head":oa["SOURCE_COMMIT"]}),
]
for name,r,mut in cases:
 operation=run_commit if name=="wrong_root_commit" else lambda:run_cancel(copy.deepcopy(template))
 control(name+"_rejected",lambda r=r,mut=mut,operation=operation:changed_payload(r,mut,operation),True)
ck("independent_changed_block_controls",all(x["passed"] for x in controls),controls)
# Bind prior independent actual facts without claiming the trial ran.
commitreview=j(R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_commit_binding_independent_review_codex/f04a0b572d2141b4b2a2f45dbd885394/review.json")
cancelreview=j(R/"execution/v2.4/receipts/W05/W05-99/sdk_typed_cancel_actual_independent_review_codex/b8612c056c734cd2b2b299cfba761338/review.json")
ck("actual_precommit_same_bytes_independent_binding",commitreview["new_head"]==na["SOURCE_COMMIT"] and commitreview["decision"]=="VERIFIED_FIVE_GO_COMMIT_OF_IDENTICAL_LOCALLY_TESTED_BYTES" and cancelreview["decision"]=="PASS_LOCAL_TYPED_CANCEL_WITH_ACTUAL_CURRENT_MU_BUNDLE")
cp=j(R/"execution/v2.4/checkpoint.json")
ck("current_checkpoint341679_adc460",cp["revision"]==341 and len(cp["failure_counters"])==679 and cp["head"]==na["SOURCE_COMMIT"])
ck("fixed_checkpoint_pin",ref(R/"execution/v2.4/checkpoint.json")["sha256"]=="7f63366f8bbe9cd5cf4cee781e8a81b5fd9cc69e20b865cac47db0fff5babd0a")
report={"schema":"researchos.mu-sdk-v8-independent-source-audit.v1","checks":checks,"failed_checks":[x for x in checks if not x["passed"]],"controls":controls,"pins":list(pins.values()),"changed_functions":changed,"source_ref":h["source_ref"],"template_ref":h["input_template_ref"],"selected_ast_scope":["require","json_file","pin_file","exact added commit block","exact replaced cancel block"],"candidate_entry_execution":False,"native_calls":0,"provider_calls":0,"main_canonical_writes":0}
with (O/"audit.json").open("x",encoding="utf8",newline="\n") as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")
print(json.dumps({"checks":len(checks),"failed_checks":report["failed_checks"],"controls":len(controls),"pins":len(pins),"audit_ref":ref(O/"audit.json")},ensure_ascii=False))
