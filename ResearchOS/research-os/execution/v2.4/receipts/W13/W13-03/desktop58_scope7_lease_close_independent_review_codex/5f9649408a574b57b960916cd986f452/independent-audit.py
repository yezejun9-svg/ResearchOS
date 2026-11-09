import ast, copy, hashlib, json, os
from pathlib import Path
ROOT=Path(r"D:\作品集\ResearchOS\research-os")
OUT=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_scope7_lease_close_independent_review_codex/5f9649408a574b57b960916cd986f452"
SRC=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_scope7_failed_lease_close_source_codex/b342fa5adb1e42d8813317e11e9f22c0"
checks=[]; pins={}; details={}
def check(name,ok,detail=None):
    checks.append({"name":name,"ok":bool(ok),"detail":detail})
def read(p):
    p=Path(p); p=p if p.is_absolute() else ROOT/p
    raw=p.read_bytes()
    rel=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)
    pins[rel]={"path":rel,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
    return raw
def pairs(items):
    out={}
    for k,v in items:
        if k in out: raise ValueError("duplicate key "+k)
        out[k]=v
    return out
def j(p): return json.loads(read(p),object_pairs_hook=pairs)
def verify(r):
    raw=read(r["path"])
    check("pin:"+r["path"],hashlib.sha256(raw).hexdigest()==r["sha256"] and len(raw)==r["bytes"])
    return raw
def refs(x):
    if isinstance(x,dict):
        if {"path","sha256","bytes"} <= x.keys():
            yield {k:x[k] for k in ("path","sha256","bytes")}
        else:
            for v in x.values(): yield from refs(v)
    elif isinstance(x,list):
        for v in x: yield from refs(v)
def walk(x):
    yield x
    if isinstance(x,dict):
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
def ptr(x,p):
    for seg in p.split("/")[1:]:
        seg=seg.replace("~1","/").replace("~0","~")
        x=x[int(seg)] if isinstance(x,list) else x[seg]
    return x
def diff(a,b,path=""):
    if a==b: return []
    if type(a)==dict and type(b)==dict:
        result=[]
        for k in sorted(a.keys()|b.keys()):
            child=path+"/"+k.replace("~","~0").replace("/","~1")
            result.extend([child] if k not in a or k not in b else diff(a[k],b[k],child))
        return result
    return [path]
h=j(SRC/"handoff.json"); q=j(h["input_ref"]["path"]); p=j(h["prepared_ref"]["path"])
cas=ROOT/q["namespace"]; audit=j(h["audit_ref"]["path"]); inv=j(h["inverse_ref"]["path"])
om=j(h["origin_map_ref"]["path"]); io=j(h["original_io_inventory_ref"]["path"])
mf=j(h["manifest_ref"]["path"]); dm=j(h["draft_manifest_ref"]["path"])
seen=set()
for data in (h,q,p,inv,om,io,mf,dm):
    for r in refs(data):
        key=(r["path"],r["sha256"],r["bytes"])
        if key not in seen: verify(r); seen.add(key)
check("source_manifest_exact_inventory",
    {x["path"] for x in mf["members"]}=={f.relative_to(ROOT).as_posix() for d in (SRC,cas) for f in d.iterdir() if f.is_file() and f not in (SRC/"manifest.json",SRC/"handoff.json")},
    {"source_files":[f.name for f in SRC.iterdir()],"cas_files":[f.name for f in cas.iterdir()]})
check("draft_manifest_exact_inventory",{x["path"] for x in dm["members"]}=={f.relative_to(ROOT).as_posix() for f in cas.iterdir() if f.is_file() and f.name!="manifest.draft.json"})
before=[read(x["path"]) for x in q["canonical_before"]]
copies=[read(x["path"]) for x in p["original_refs"]]
target=[read(x["path"]) for x in p["desired_refs"]]
check("four_original_live_bytes",before==copies)
check("step_state_commands_unchanged",target[2:]==before[2:])
bc,bo=map(json.loads,before[:2]); ac,ao=map(json.loads,target[:2])
check("before_tuple",[bc["revision"],bo["revision"],len(bc["failure_counters"])]==[339,167,645])
check("after_tuple",[ac["revision"],ao["revision"],len(ac["failure_counters"])]==[340,168,672])
check("645_prefix_exact",ac["failure_counters"][:645]==bc["failure_counters"])
check("origin_indices_contiguous",[x["failure_index"] for x in om["rows"]]==list(range(646,673)))
check("io_origin_map_exact",io["origin_refs_by_index"]==om["rows"])
allold={x.get("origin_key") or x.get("evidence_ref",{}).get("sha256") for x in bc["failure_counters"]}
append=ac["failure_counters"][645:]; origin_details=[]
for x,row in zip(om["rows"],append):
    n=x["failure_index"]; ref=x["evidence_ref"]; body=j(ref["path"])
    check("origin_payload_exact:"+str(n),row=={"origin_key":ref["sha256"],"evidence_ref":ref,"original_payload":body,"counter_reset":False,"counted_once":True,"automatic_retry":False})
    check("origin_unique:"+str(n),ref["sha256"] not in allold); allold.add(ref["sha256"])
    prov=x["count_provenance"]; mapping=prov.get("mapping_ref"); mapped=None
    if mapping:
        mapped=ptr(j(mapping["path"]),prov["json_pointer"])
        if prov.get("derived_receipt"):
            check("derived_origin_exact:"+str(n),body["source_original_ref"]==mapping and body["source_json_pointer"]==prov["json_pointer"] and body["source_original_record"]==mapped)
        else:
            check("origin_mapping_contains_ref:"+str(n),any(z==ref or (isinstance(z,dict) and z.get("path")==ref["path"] and z.get("sha256")==ref["sha256"]) for z in walk(mapped)))
    else:
        check("direct_origin_index:"+str(n),n in [z for z in walk(body) if type(z)==int])
    origin_details.append({"failure_index":n,"evidence_ref":ref,"mapping_value":mapped,"top_keys":list(body)})
cpdiff=diff(bc,ac); owdiff=diff(bo,ao)
check("audit_pointers_exact",cpdiff==audit["changed_checkpoint_pointers"] and owdiff==audit["changed_ownership_pointers"])
trimc=copy.deepcopy(ac); trimo=copy.deepcopy(ao)
for k in ("revision","expected_previous_revision","updated_at","updated_by"):
    if k in bc: trimc[k]=bc[k]
    else: trimc.pop(k,None)
trimc["failure_counters"]=bc["failure_counters"]
for k in ("desktop58_finite_validation_state","desktop58_finite_validation_failed_closure_review_ref","desktop58_finite_validation_failed_closure_root_ref"):
    if k in bc["work_in_progress"]: trimc["work_in_progress"][k]=bc["work_in_progress"][k]
    else: trimc["work_in_progress"].pop(k,None)
for k in ("revision","amended_at","amended_by"):
    if k in bo: trimo[k]=bo[k]
    else: trimo.pop(k,None)
trimo["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]=bo["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
check("only_two_authorized_state_subtrees",trimc==bc and trimo==bo)
lease=ao["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
check("failed_closure_withholds_authority",lease["state"]=="FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD" and lease["execution_grant"] is False and lease["qualification"] is False and lease["formal_increment"]==0)
check("full_byte_inverse",inv["canonical_before_refs"]==q["canonical_before"] and inv["draft_before_refs"]==p["original_refs"] and inv["draft_desired_refs"]==p["desired_refs"] and all(x["canonical_path"]==a["path"] and x["restore_bytes_ref"]==b and x["proposed_bytes_ref"]==d for x,a,b,d in zip(inv["byte_inverse_for_review"],q["canonical_before"],p["original_refs"],p["desired_refs"])))
failure_review=j(q["review_ref"]["path"]); original669=j(om["rows"][23]["evidence_ref"]["path"])
check("prior_independent_review_49_exact",failure_review["independent_checks"]==49 and failure_review["failed_checks"]==[] and failure_review["decision"]=="FAILED_ONCE_EVIDENCE_CLOSED_FOR_LEASE_REVIEW")
check("unchanged_failure_native_chain",failure_review["actual_exit_chain"]=={"outer_tool":1,"root_python":1,"launcher_native":1,"controller_native":1,"builder_native":3758097160})
check("withheld_runtime_qualification",failure_review["incomplete_qualification_preserved"]["debug_complete"] is False and failure_review["not_started"]["remaining_top_native_commands"]==173 and failure_review["not_started"]["offscreen_controls_declared"]==2)
source=read(q["source_ref"]["path"]).decode("utf8"); tree=ast.parse(source)
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {"need","differences","desired","job_ok"}]
ns={"copy":copy,"STATE":"FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD"}
exec(compile(ast.Module(body=selected,type_ignores=[]),"<selected-pure-source-functions>","exec"),ns)
nc,no,cd,od=ns["desired"](q,bc,bo,append)
check("pure_desired_rederives_exact",nc==ac and no==ao and cd==cpdiff and od==owdiff)
good={"actual_exit":0,"error":None,"timed_out":False,"resumed":True,"job_cleanup":{"errors":[],"active_processes_last_observed":0,**{k:True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")}}}
ns["job_ok"](good); check("owned_git_good_pure_control",True)
mutations=[("actual_exit",1),("error","bad"),("timed_out",True),("resumed",False)]
for k,v in mutations:
    bad=copy.deepcopy(good); bad[k]=v
    try: ns["job_ok"](bad); rejected=False
    except RuntimeError: rejected=True
    check("owned_git_reject_"+k,rejected)
for k,v in [("errors",["bad"]),("active_processes_last_observed",1),("assigned_before_resume",False),("primary_exit_confirmed",False),("job_idle_confirmed",False),("handles_closed",False)]:
    bad=copy.deepcopy(good); bad["job_cleanup"][k]=v
    try: ns["job_ok"](bad); rejected=False
    except RuntimeError: rejected=True
    check("owned_git_reject_cleanup_"+k,rejected)
check("no_old_commit_marker",not (cas/"commit.started.json").exists() and not (cas/"manifest.closed.json").exists())
for r in q["canonical_before"]: verify(r)
details={"source":q["source_ref"],"canonical_before":q["canonical_before"],"desired_refs":p["desired_refs"],"checkpoint_pointers":cpdiff,"ownership_pointers":owdiff,"origins":origin_details,"io_inventory_keys":list(io),"binding_helper_ref":q["helper_ref"],"git_jobs_planned":12,"git_jobs_executed":0,"source_execution":"AST pure functions need,differences,desired,job_ok only","actual_cas_executed":False,"native_product_calls":0,"candidate_calls":0}
report={"schema":"researchos.scope7-failed-lease-close-independent-audit.v1","checks":checks,"failed_checks":[x for x in checks if not x["ok"]],"checked_pins":list(pins.values()),"details":details}
with (OUT/"audit.json").open("x",encoding="utf8",newline="\n") as f: json.dump(report,f,ensure_ascii=False,indent=2); f.write("\n")
print(json.dumps({"checks":len(checks),"failed":report["failed_checks"],"pins":len(pins),"audit_path":str(OUT/"audit.json"),"io_keys":list(io)},ensure_ascii=False))
