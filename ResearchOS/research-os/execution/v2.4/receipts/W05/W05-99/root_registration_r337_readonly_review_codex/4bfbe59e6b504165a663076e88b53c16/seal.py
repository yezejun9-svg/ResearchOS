import ast,copy,hashlib,json
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).parent
N=R/"execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-b4d53db07f1e4ab8b9c0b37e291a6da5"
def path(s):
 p=Path(s);return p if p.is_absolute() else R/p
def raw(p):return path(p).read_bytes()
def doc(p):return json.loads(raw(p))
def pin(p):
 p=path(p);b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def verify(r):
 b=raw(r["path"]);assert len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"];return b
def rd(r):return json.loads(verify(r))
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
C=[]
def ck(k,v):C.append({"check":k,"passed":bool(v)})
a=doc(O/"audit.json");assert not a["failed"]
toolref={"path":str(N/"tool-observations.sixth-prepare.closed.original.json"),"sha256":"1191049af62c6948f54f0ed9834c106e63624e40b71e3ace0f2b9a53f0dd9338","bytes":14635}
toolobs=rd(toolref)
assert toolobs['actual_prepare_outer_exit']==toolobs['actual_prepare_python_exit']==0 and len(toolobs['records'])==5
rr={x['kind']:x for x in toolobs['records']}
assert rr['prepare']['result']['session_id']==rr['prepare_terminal']['input']['session_id']==3944
assert rr['prepare_terminal']['result']['exit_code']==0 and 'ACTUAL_PYTHON_EXIT=0' in rr['prepare_terminal']['result']['output']
p=doc(N/"prepared_refs.json");b=p["binding"];s=rd(p["scope_ref"]);g=verify(s["authorization_verifier_ref"]).decode()
module=[r for r in b["metadata_code_refs"] if r["sha256"]=="c0a085f9b720ebdb89a78fb5cf367bd262d2823fe15a9f2686545b99aebe7755"][0]
m=verify(module).decode(); ast.parse(m);ast.parse(g)
expected_scope={"path":(N/"scope_registration.json").relative_to(R).as_posix(),"sha256":"0caa54d359072e7200b7cbbc9fb72742ffb325adc82ad3b4622310ac7549e9c1","bytes":25595}
ck("prepared exactScopeRef ROOTrelative",p["scope_ref"]==expected_scope)
phases=["admission.runtime","grant-final.runtime","grant-final.runtime.after"]
expectedpaths=[str(path(s["new_authorization_root"])/(x+".json")) for x in phases]
ck("runtime observations exact canonicalABS",s["expected_runtime_observation_paths"]==expectedpaths)
ck("runtime observation ordered phases",s["runtime_observation_phases"]==[{"stage":x,"path":y} for x,y in zip(phases,expectedpaths)])
ck("full metadata projection same as wholeScope",s["Root_metadata_binding_inputs"]["metadata_code_refs"]==b["metadata_code_refs"])
review=rd(b["controller_review_ref"]);ck("actual sourceReview bound 07d5",b["controller_review_ref"]["sha256"]=="07d5b1e69beff42e2a99e987f240d09ca530ed3579cdb6c11428b6ff56084649")
ck("same fullscope binding reviewed",review["binding_ref"]==pin(N/"binding.pre-review.json") or
 review["binding_ref"]["sha256"]==pin(N/"binding.pre-review.json")["sha256"])
ck("current actual fullscope review all pass",review["effective_all_checks_passed"] is True)
oldcp,oldow=[rd(x) for x in p["original_refs"][:2]];cp,ow=[rd(x) for x in p["desired_refs"][:2]]
oldlease=oldow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
ck("activelease replaced only after actualclosed",oldlease["state"]=="FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD")
# Store the complete allowed-delta map without assuming hidden field names.
def dif(a,b,path="$"):
 if type(a)!=type(b):return [path]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append(path+"."+k)
   else:out+=dif(a[k],b[k],path+"."+k)
  return out
 if isinstance(a,list):return [] if a==b else [path]
 return [] if a==b else [path]
cpdiff=dif(oldcp,cp);owdiff=dif(oldow,ow)
ck("CP head source preserved",cp["head"]==oldcp["head"]==s["source_commit"])
ck("617 exact failures not latepending",[cp["revision"],ow["revision"],len(cp["failure_counters"])]==[337,165,617])
for name in ["register.py","run.py","seal.py","grant_preflight.py"]:
 rr=next(x for x in b["metadata_code_refs"] if path(x["path"])==N/name)
 ck("exact Root-relative wrapper "+name,rr["path"]==(N/name).relative_to(R).as_posix())
 verify(rr);ast.parse(raw(N/name))
for needle in [
"d['schema']=='researchos.root-registration-source-review.v1'",
"d['reviewer']=='codex:/root/w05_merge_review'",
"d['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION'",
"d['requested_changes']==[]",
"d['actual_registration_executed'] is False",
"d['canonical_before']==p['canonical_before']",
"safe(copied['path']).parent==safe(r['path']).parent",
"helper.run_owned(argv,str(ROOT),dict(b['public_environment']),stdout,stderr,600)",
"scope_ref':scope_ref",
"gate.validate_grant(str(safe(scope_ref['path'])),scope_ref['sha256']",
"post-source-guard seal four CAS",
"immediate pre-grant live four CAS",
"save(out/(mode+'.started.json')"
]:ck("pipeline exact static contract "+needle,needle in m)
for key in ["output_root","outer_output_root","export_root","new_authorization_root","new_grant_preflight_root"]:
 ck("still absent "+key,not path(s[key]).exists())
ck("Root caller output absent",not (R/"execution/v2.4/receipts/W13/W13-03/desktop58_root_terminal_closure_codex/d8a016ddc71e440fb386a11957c098ea").exists())
for old,can,cop in zip(p["original_refs"],p["canonical_before"],a["copied_canonical_before_refs"]):
 ck("final live+copy byteequal "+can["path"],verify(old)==verify(can)==verify(cop))
for name in ["run.started.json","register.started.json","seal.started.json","grant.started.json","invocation.json","canonical-write.intent.json","registration-audit.json","manifest.json"]:
 ck("no registration/grant execution "+name,not (N/name).exists())
assert all(x["passed"] for x in C),[x for x in C if not x["passed"]]
supp=save("compatibility-and-final-guards.json",{"schema":"researchos.root-registration-independent-compatibility-review.v1","checks":C,"all_passed":True,
"scope_ref":expected_scope,"runtime_observation_paths":expectedpaths,"old_closed_lease":oldlease,
"checkpoint_changed_paths":cpdiff,"ownership_changed_paths":owdiff,
"prior_full_scope_review_ref":b["controller_review_ref"],"actual_prepare_tool_observation_ref":toolref,"review_source_not_executed":True,"new_failure_count":0})
rv={"schema":"researchos.root-registration-source-review.v1","reviewer":"codex:/root/w05_merge_review",
"source_author":"codex:/root","non_author":True,"decision":"REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION",
"requested_changes":[],"actual_registration_executed":False,"expected_before":[336,164,614],"expected_after":[337,165,617],
"register_sha256":pin(N/"register.py")["sha256"],"wrapper_sha256":pin(N/"run.py")["sha256"],
"prepared_refs_sha256":pin(N/"prepared_refs.json")["sha256"],"audit_sha256":pin(N/"audit.json")["sha256"],
"canonical_before":p["canonical_before"],"copied_canonical_before_refs":a["copied_canonical_before_refs"],
"scope_ref":p["scope_ref"],"binding_ref":pin(N/"binding.json"),"source_scope_review_ref":b["controller_review_ref"],"actual_prepare_tool_observation_ref":toolref,
"independent_audit_ref":pin(O/"audit.json"),"compatibility_supplement_ref":supp,
"checks":{"main":len(a["checks"]),"supplement":len(C),"failed":0},
"prepared_resource_reuse":a["resource_reuse"],"source_commit":s["source_commit"],
"source_acceptance":False,"formal_increment":0,"parent_acceptance_increment":0,
"review_issues_execution_grant":False,"candidate_product_calls":0,"native_Git_calls_by_reviewer":0,
"new_failure_origins":[],"new_failure_count":0,
"protocol":"Actual scope_ref ROOT-relative three-key passes unchanged prepare/WIP/sublease/grant; runtime observation paths remain canonical ABS. No global ref normalization.",
"boundaries":["Only Root may run run.py once, internally invoking register.py once; no separate duplicate register.",
"Existing CLI2 bounded qualification does not accept whole58/whole-suite or Desktop runtime.",
"Sixth scope admission still requires actual CAS+seal+unique grant and a separately reviewed once caller.",
"Original 614 failure rows and three exact opaque new rows retained; later pending not included.",
"Old72ff closure metadata is actually FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD; original failed runtime remains withheld."],
"status":"STOPPED"}
rref=save("review.json",rv)
h=save("handoff.json",{"schema":"researchos.root-registration-review-handoff.v1","review_ref":rref,"decision":rv["decision"],
"expected_before":rv["expected_before"],"expected_after":rv["expected_after"],"new_failure_count":0,"status":"STOPPED"})
entries=[pin(x) for x in sorted(O.iterdir()) if x.is_file()]
mf=save("manifest.json",{"schema":"researchos.public-review-manifest.v1","entries":entries,"count":len(entries),"self_excluded":True})
print(json.dumps({"review":rref,"handoff":h,"manifest":mf,"checks":len(C),"new_failure_count":0},ensure_ascii=False))

