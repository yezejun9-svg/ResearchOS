"""Root-only narrow failed-lease metadata CAS. No product or model invocation."""
import sys
sys.dont_write_bytecode = True
import argparse, copy, datetime, hashlib, json, os, traceback, types
from pathlib import Path
ROOT=Path("D:/作品集/ResearchOS/research-os")
NS=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_old_failed_lease_closure_cas_codex/5e2a75ea3da546b28b20975cc6a4d18f"
CANON=["execution/v2.4/"+x+".json" for x in ("checkpoint","path_ownership","step_state","commands")]
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def safe(p,existing=True):
    p=Path(p)
    if not p.is_absolute(): p=ROOT/p
    need(".." not in p.parts and p.is_relative_to(ROOT) and p!=ROOT,"outside Root")
    need(p.resolve(strict=existing)==p.absolute(),"alias")
    for a in [p,*p.parents]:
        if os.path.lexists(a): need(not a.is_symlink() and not (getattr(a.lstat(),"st_file_attributes",0)&0x400),"reparse")
        if a==ROOT: break
    return p
def parse(raw):
    def pairs(items):
        d={}
        for k,v in items: need(k not in d,"duplicate JSON key"); d[k]=v
        return d
    return json.loads(raw.decode("utf8"),object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
def encode(d): return (json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf8")
def pin(p):
    p=Path(p); raw=p.read_bytes()
    return {"path":p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def verify(r):
    need(type(r)is dict and set(r)=={"path","sha256","bytes"},"exact ref")
    p=Path(r["path"])
    if not p.is_absolute(): p=ROOT/p
    if p.is_relative_to(ROOT): p=safe(p)
    raw=p.read_bytes()
    need(len(raw)==r["bytes"] and hashlib.sha256(raw).hexdigest()==r["sha256"],"pin mismatch: "+str(p))
    return raw
def doc(r): return parse(verify(r))
def save(p,d):
    p=safe(p,False); raw=encode(d)
    with p.open("xb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    return pin(p)
def copy_bytes(p,raw):
    with safe(p,False).open("xb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
    return pin(p)
def load_module(r,name):
    raw=verify(r); m=types.ModuleType(name); m.__file__=str(safe(r["path"]))
    exec(compile(raw,m.__file__,"exec"),m.__dict__); return m
def differences(a,b,path=""):
    if a==b:return []
    if isinstance(a,dict) and isinstance(b,dict):
        rows=[]
        for k in sorted(set(a)|set(b)):
            child=path+"/"+k.replace("~","~0").replace("/","~1")
            if k not in a or k not in b: rows.append(child)
            else: rows.extend(differences(a[k],b[k],child))
        return rows
    return [path]
def draft(q):
    save(NS/"draft.started.json",{"actor":"codex:/root","once":True})
    need(q["before"]==[335,163,580] and q["after"]==[336,164,614] and q["formal_increment"]==0 and not q["source_execution_grant"],"fixed narrow transition")
    need(q["actor"]=="codex:/root" and q["namespace"]==NS.relative_to(ROOT).as_posix(),"actor/namespace")
    verify(q["python_pin"]); need(Path(sys.executable).resolve()==Path(q["python_pin"]["path"]).resolve(),"pinned Python")
    b=doc(q["fifth_binding_ref"]["binding_ref"])
    c=doc(b["canonical_before_ref"]); need([x["canonical_path"] for x in c["entries"]]==CANON,"canonical order")
    before=[verify(x["ref"]) for x in c["entries"]]
    need(all(safe(p).read_bytes()==raw for p,raw in zip(CANON,before)),"current exact four")
    cp,ow=map(parse,before[:2])
    need([cp["revision"],ow["revision"],len(cp["failure_counters"])]==q["before"] and cp["head"]==q["main_head"],"current tuple/head")
    prefix=doc(b["failure_prefix430_ref"])["failure_counters"]
    need(len(prefix)==430 and cp["failure_counters"][:430]==prefix,"original 430 prefix")
    closure=doc(q["closure_review_ref"]); root_closure=doc(q["closure_report_ref"])
    need(closure["decision"]=="FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD" and closure["reviewer"]=="codex:/root/w05_merge_review","actual independent failed closure")
    lease=ow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
    need(lease["run_uuid"]==q["old_run_uuid"] and lease["state"]=="REGISTERED_PENDING_ONCE_EXECUTION" and lease["source_commit"]==q["main_head"] and lease["owner"]=="codex:/root" and lease["current_source_writer"] is None,"exact old lease")
    need(cp["work_in_progress"]["desktop58_finite_validation_state"]=="REGISTERED_PENDING_ONCE_EXECUTION","old WIP")
    f=q["prepare_failure"]
    need(f["failure_index"]==614 and f["actual_outer_tool_exit"]==1 and f["actual_python_exit"]==1 and f["actual_stage_native_exit"] is None and f["counter_reset"] is False and f["automatic_retry"] is False,"actual failed prepare")
    phase_refs=[]
    reg=safe(q["fifth_registry"])
    for p in sorted(reg.iterdir()):
        if p.is_file() and (p.name.startswith("prepare.") or p.name.startswith("failure.prepare")):
            phase_refs.append(pin(safe(p)))
    need(any("failure.prepare" in x["path"] for x in phase_refs),"original phase failure preserved")
    origin=save(NS/"failure-origin-614.original.json",{"schema":"researchos.failure-origin.v1","origin":"ROOT_FIFTH_PREPARE_ACTIVE_OLD_DESKTOP_LEASE","failure_index":614,"phase":"metadata_prepare","original_tool_records":f["tool_records"],"actual_outer_tool_exit":1,"actual_python_exit":1,"actual_stage_native_exit":None,"error":f["source"],"original_phase_refs":phase_refs,"binding_ref":q["fifth_binding_ref"]["binding_ref"],"old_failed_run_closure_ref":q["closure_review_ref"],"counted_once":True,"counter_reset":False,"automatic_retry":False,"candidate_execution_calls":0,"canonical_writes":0})
    refs=q["pending_origin_refs"]+[origin]
    need(len(refs)==34,"34 original events")
    rows=[{"origin_key":r["sha256"],"evidence_ref":r,"original_payload":doc(r),"counter_reset":False,"counted_once":True,"automatic_retry":False} for r in refs]
    cut=save(NS/"origin-cut.json",{"schema":"researchos.failure-origin-cut.v1","owner":"codex:/root","before":q["before"],"after":q["after"],"origins":rows,"counter_reset":False})
    pipeline=load_module(q["pipeline_ref"],"reviewed_desktop_metadata_origin_formatter")
    need(pipeline.origins({"origin_cut_ref":cut,"before":q["before"],"after":q["after"]},cp)==rows,"reviewed opaque origin verifier")
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    newcp,newow=copy.deepcopy(cp),copy.deepcopy(ow)
    newcp.update(revision=336,expected_previous_revision=335,updated_at=stamp,updated_by="codex:/root")
    newcp["failure_counters"].extend(copy.deepcopy(rows))
    newcp["work_in_progress"].update(desktop58_finite_validation_state="FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD",desktop58_finite_validation_failed_closure_review_ref=q["closure_review_ref"],desktop58_finite_validation_failed_closure_root_ref=q["closure_report_ref"])
    newow.update(revision=164,amended_at=stamp,amended_by="codex:/root")
    newlease=newow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]
    newlease.update(state="FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD",failed_closure_review_ref=q["closure_review_ref"],failed_closure_root_ref=q["closure_report_ref"])
    need(newcp["failure_counters"][:580]==cp["failure_counters"],"all original 580 preserved")
    cpdiff=differences(cp,newcp); owdiff=differences(ow,newow)
    cpallowed={"/revision","/expected_previous_revision","/updated_at","/updated_by","/failure_counters","/work_in_progress/desktop58_finite_validation_state","/work_in_progress/desktop58_finite_validation_failed_closure_review_ref","/work_in_progress/desktop58_finite_validation_failed_closure_root_ref"}
    owbase="/card_path_bindings/W13-03/subtasks/desktop58_finite_validation/"
    owallowed={"/revision","/amended_at","/amended_by",owbase+"state",owbase+"failed_closure_review_ref",owbase+"failed_closure_root_ref"}
    need(set(cpdiff)<=cpallowed and set(owdiff)<=owallowed,"exact pointer allowlist")
    desired=[encode(newcp),encode(newow),before[2],before[3]]
    original_refs=[copy_bytes(NS/(Path(p).stem+".before.json"),raw) for p,raw in zip(CANON,before)]
    desired_refs=[copy_bytes(NS/(Path(p).stem+".desired.json"),raw) for p,raw in zip(CANON,desired)]
    audit=save(NS/"audit.json",{"schema":"researchos.desktop58-old-lease-closure-cas-audit.v1","author":"codex:/root","before":q["before"],"after":q["after"],"checkpoint_changed_pointers":cpdiff,"ownership_changed_pointers":owdiff,"original_failure_prefix580_equal":True,"original_failure_prefix430_equal":True,"original_origin_count":34,"step_state_commands_byte_identical":True,"main_source_head":q["main_head"],"old_run_uuid":q["old_run_uuid"],"old_run_native_closed_by_independent_review_ref":q["closure_review_ref"],"old_failed_root_report_ref":q["closure_report_ref"],"qualification_granted":False,"formal_increment":0,"parent_acceptance_increment":0,"new_execution_scope":False,"new_execution_grant":False,"counter_reset":False,"automatic_retry":False})
    prepared=save(NS/"prepared.json",{"schema":"researchos.desktop58-old-lease-closure-cas-prepared.v1","author":"codex:/root","input_ref":pin(NS/"original-input.json"),"source_ref":pin(Path(__file__)),"before":q["before"],"after":q["after"],"original_refs":original_refs,"desired_refs":desired_refs,"origin_cut_ref":cut,"origin614_ref":origin,"audit_ref":audit,"old_closed_run_review_ref":q["closure_review_ref"],"formal_increment":0,"execution_grant":False})
    members=[pin(p) for p in sorted(NS.iterdir()) if p.is_file()]
    manifest=save(NS/"manifest.draft.json",{"schema":"researchos.receipt-manifest.v1","owner":"codex:/root","purpose":"old_failed_lease_closure_metadata_only","members":members,"self_excluded":True})
    print(json.dumps({"prepared_ref":prepared,"audit_ref":audit,"manifest_ref":manifest,"origin614_ref":origin,"before":q["before"],"after":q["after"],"native_product_calls":0,"canonical_writes":0},ensure_ascii=False))
def job_ok(r):
    need(isinstance(r,dict) and r["actual_exit"]==0 and r["error"] is None and not r["timed_out"] and r["resumed"] is True,"metadata Git native failure")
    c=r["job_cleanup"]
    need(c["errors"]==[] and c["active_processes_last_observed"]==0 and all(c[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")),"metadata Git cleanup")
def git_guard(q,b,label):
    helper=load_module(q["helper_ref"],"old_failed_lease_owned_git")
    lock=doc(b["toolchain_lock_ref"])["tools"]
    verify({"path":lock["git"]["path"],"sha256":lock["git"]["sha256"],"bytes":46480})
    env=dict(b["public_environment"]);env.update(GIT_OPTIONAL_LOCKS="0",GIT_NO_REPLACE_OBJECTS="1",GIT_CONFIG_NOSYSTEM="1",GIT_CONFIG_GLOBAL="nul",GIT_TERMINAL_PROMPT="0",GIT_CONFIG_COUNT="2",GIT_CONFIG_KEY_0="core.fsmonitor",GIT_CONFIG_VALUE_0="false",GIT_CONFIG_KEY_1="core.untrackedCache",GIT_CONFIG_VALUE_1="false")
    outputs=[]
    for kind,args in [("head",["rev-parse","HEAD"]),("status",["status","--porcelain=v1","--untracked-files=no"]),("index",["diff","--cached","--name-only"])]:
        a=NS/(label+"."+kind+".stdout.raw");z=NS/(label+"."+kind+".stderr.raw")
        argv=[lock["git"]["path"]]+args;result=None;error=None
        try:
            with a.open("xb") as out,z.open("xb") as err: result=helper.run_owned(argv,str(ROOT),env,out,err,30)
        except BaseException as e: error=repr(e);raise
        finally:
            save(NS/(label+"."+kind+".invocation.json"),{"actor":"codex:/root","metadata_only":True,"argv":argv,"cwd":str(ROOT),"public_environment":env,"result":result,"wrapper_error":error,"actual_stage_native_exit":result["actual_exit"] if result else None,"stdout_ref":pin(a) if a.exists() else None,"stderr_ref":pin(z) if z.exists() else None,"qualifies_product_runtime":False})
        job_ok(result);outputs.append(a.read_bytes())
    need(outputs[0].decode("ascii").strip()==q["main_head"] and outputs[2]==b"","Main/index")
    need(hashlib.sha256(outputs[1]).hexdigest()==q["main_git"]["status_sha256"] and len(outputs[1])==q["main_git"]["status_bytes"],"protected tracked Git")
def commit(q,review_ref):
    p=doc(pin(NS/"prepared.v2.json"));rev=doc(review_ref)
    need(safe(p["input_ref"]["path"])==NS/"original-input.json" and q==doc(p["input_ref"]),"prepared original input exact hash/path/value")
    need(rev["reviewer"]=="codex:/root/f08_whole_scope_review" and rev["decision"]=="READY_FOR_ROOT_OLD_FAILED_LEASE_CLOSURE_CAS_ONCE" and rev["requested_changes"]==[] and rev["prepared_ref"]==pin(NS/"prepared.v2.json") and rev["source_ref"]==pin(Path(__file__)),"exact independent CAS approval")
    save(NS/"commit.started.json",{"actor":"codex:/root","once":True,"review_ref":review_ref,"input_ref":p["input_ref"]})
    before=[verify(r) for r in p["original_refs"]];desired=[verify(r) for r in p["desired_refs"]]
    b=doc(q["fifth_binding_ref"]["binding_ref"])
    need(p["before"]==q["before"] and p["after"]==q["after"] and p["execution_grant"] is False and p["formal_increment"]==0,"narrow prepared")
    need(all(safe(x).read_bytes()==r for x,r in zip(CANON,before)),"initial four CAS")
    git_guard(q,b,"commit.before")
    intent=save(NS/"canonical-write.intent.json",{"actor":"codex:/root","prepared_ref":pin(NS/"prepared.v2.json"),"review_ref":review_ref,"before":q["before"],"after":q["after"],"write_paths":CANON[:2],"unchanged_paths":CANON[2:],"automatic_retry":False,"counter_reset":False,"recovery":"FORWARD_ONLY_SEPARATE_ROOT_DECISION_NO_ROLLBACK"})
    expected=list(before)
    for i,name in enumerate(CANON[:2]):
        target=safe(name);tmp=target.with_name(target.name+"."+q["run_uuid"]+".tmp")
        copy_bytes(tmp,desired[i])
        git_guard(q,b,"commit.pre-replace-"+str(i))
        need(all(safe(x).read_bytes()==r for x,r in zip(CANON,expected)),"four immediately before replace CAS")
        os.replace(tmp,target);expected[i]=desired[i]
        need(target.read_bytes()==desired[i],"verified individual write")
        save(NS/("canonical-write."+target.stem+".done.json"),{"intent_ref":intent,"desired_ref":p["desired_refs"][i]})
    git_guard(q,b,"commit.after")
    need(all(safe(x).read_bytes()==r for x,r in zip(CANON,desired)),"final exact four")
    verified=save(NS/"canonical-write.verified.json",{"schema":"researchos.desktop58-old-lease-closure-cas-verified.v1","actor":"codex:/root","before":q["before"],"after":q["after"],"intent_ref":intent,"review_ref":review_ref,"canonical_refs":[pin(safe(x)) for x in CANON],"step_state_commands_unchanged":True,"old_lease_closed_failed":True,"execution_grant":False,"formal_increment":0,"counter_reset":False})
    resume=save(NS/"RESUME.old-failed-lease.closed.json",{"schema":"researchos.resume.v1","actor":"codex:/root","canonical_tuple":q["after"],"old_run_uuid":q["old_run_uuid"],"old_state":"FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD","fifth_prepare":"FAILED_614_NO_RETRY_NO_GRANT","next_action":"fresh sixth scope with new UUID/Root caller and actual current tuple; preserve any post614 original events","goal_status":"ACTIVE","parent_accepted":6,"parents_total":22,"formal_accepted":0,"formal_total":42,"verified_ref":verified})
    mf=save(NS/"manifest.closed.json",{"schema":"researchos.receipt-manifest.v1","owner":"codex:/root","members":[pin(x) for x in sorted(NS.iterdir()) if x.is_file()],"self_excluded":True,"metadata_only":True,"formal_increment":0})
    print(json.dumps({"verified_ref":verified,"resume_ref":resume,"manifest_ref":mf,"canonical_tuple":q["after"],"canonical_refs":[pin(safe(x)) for x in CANON]},ensure_ascii=False))
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--commit-review-ref",required=True);a=ap.parse_args()
    q=parse(safe(NS/"original-input.json").read_bytes())
    commit(q,parse(a.commit_review_ref.encode("utf8")))
if __name__=="__main__":
    try: main()
    except BaseException as e:
        print(repr(e),file=sys.stderr);traceback.print_exc()
        raise
