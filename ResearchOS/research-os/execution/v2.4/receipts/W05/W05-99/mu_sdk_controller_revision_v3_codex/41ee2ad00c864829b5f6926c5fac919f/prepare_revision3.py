import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,difflib
from pathlib import Path
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_revision_v2_codex/6a02e12c83da4d4c80fc3f322fe8d397");P=Path(__file__).resolve().parent
def pin(p):
 b=Path(p).read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
for name in ("canonical_transactions.py","job_deadline_watchdog.py"):ast.parse((P/name).read_bytes());compile((P/name).read_bytes(),str(P/name),"exec")
source=(BASE/"controller.py").read_text(encoding="utf-8");assert pin(BASE/"controller.py")["sha256"]=="9dfad55126c68bc02a3a16c45b0d487c3af363182d45914fb409850c63309487"
tree=ast.parse(source); lines=source.splitlines(True); functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
activate='''def activate_canonical_lease(doc,lease_ref,expected_cp,expected_ownership,phase_dir):
    transaction=module(CANONICAL_TRANSACTION_REF,"root_owned_canonical_transaction")
    def transform(cp,ow):
        require(cp["head"]==SOURCE_COMMIT and cp["current_step_id"]=="W05-99","current card/source mismatch")
        require(cp["work_in_progress"].get("mu_sdk_active_run_uuid") in (None,""),"another SDK trial lease remains active")
        cp["expected_previous_revision"]=cp["revision"];cp["revision"]+=1
        cp["updated_at"]=stamp();cp["updated_by"]="codex:/root"
        cp["work_in_progress"].update({"mu_sdk_active_run_uuid":doc["run_uuid"],
            "mu_sdk_registration_ref":doc["root_registration"],"mu_sdk_owner_lease_ref":lease_ref,
            "mu_sdk_live_trial_state":"ASSIGNED_PROCESS_STARTUP_OBSERVATION_PENDING",
            "mu_sdk_runtime_qualification":False})
        ow["revision"]+=1;ow["updated_at"]=stamp();ow["updated_by"]="codex:/root"
        subtasks=ow["card_path_bindings"]["W05-99"].setdefault("subtasks",{})
        subtasks["mu_sdk_trial"]={"owner":"codex:/root","run_uuid":doc["run_uuid"],
            "state":"ACTIVE_ISOLATED_PHASE","source_head":SOURCE_COMMIT,
            "data_root":doc["data_root"],"registration_ref":doc["root_registration"],"lease_ref":lease_ref}
        return cp,ow
    result=transaction.update_pair([expected_cp,expected_ownership],transform,phase_dir,"activate")
    exclusive_json(phase_dir/"canonical-lease.activated.json",result)
    return result
'''
close='''def close_canonical_lease(doc,phase_dir,native_result,error):
    if not cleanup_confirmed(native_result):
        return exclusive_json(phase_dir/"canonical-lease.retained-unconfirmed.json",{
            "run_uuid":doc["run_uuid"],"state":"CLEANUP_UNCONFIRMED_ACTIVE_LEASE_RETAINED",
            "native_result":native_result,"exception":error,
            "checkpoint_ref":pin(ROOT/"execution/v2.4/checkpoint.json"),
            "ownership_ref":pin(ROOT/"execution/v2.4/path_ownership.json"),
            "automatic_recovery":False,"formal_acceptance":False})
    transaction=module(CANONICAL_TRANSACTION_REF,"root_owned_canonical_transaction")
    expected=[pin(ROOT/"execution/v2.4/checkpoint.json"),pin(ROOT/"execution/v2.4/path_ownership.json")]
    def transform(cp,ow):
        require(cp["work_in_progress"].get("mu_sdk_active_run_uuid")==doc["run_uuid"],"cannot close another active phase")
        record=ow["card_path_bindings"]["W05-99"]["subtasks"]["mu_sdk_trial"]
        require(record["run_uuid"]==doc["run_uuid"],"ownership lease UUID changed")
        cp["expected_previous_revision"]=cp["revision"];cp["revision"]+=1;cp["updated_at"]=stamp()
        cp["work_in_progress"].update({"mu_sdk_active_run_uuid":None,
            "mu_sdk_live_trial_state":"PHASE_EXECUTION_REPORTED_PENDING_INDEPENDENT_REVIEW" if error is None else "FAILED_PHASE_CLOSED",
            "mu_sdk_last_phase_uuid":doc["run_uuid"],"mu_sdk_runtime_qualification":False})
        record["state"]="CLOSED_PENDING_INDEPENDENT_EVIDENCE_REVIEW" if error is None else "FAILED_EXECUTION_CLOSED"
        ow["revision"]+=1;ow["updated_at"]=stamp()
        return cp,ow
    result=transaction.update_pair(expected,transform,phase_dir,"close")
    return exclusive_json(phase_dir/"canonical-lease.closed.json",{
        **result,"run_uuid":doc["run_uuid"],"native_result":native_result,"exception":error,
        "runtime_qualification":False,"formal_acceptance":False})
'''
for name,replacement in sorted((("activate_canonical_lease",activate),("close_canonical_lease",close)),key=lambda item:functions[item[0]].lineno,reverse=True):
 n=functions[name];lines[n.lineno-1:n.end_lineno]=[replacement]
source="".join(lines)
source=source.replace('HERE=Path(__file__).resolve().parent','HERE=Path(__file__).resolve().parent\nCANONICAL_TRANSACTION_REF='+repr(pin(P/"canonical_transactions.py"))+'\nJOB_WATCHDOG_REF='+repr(pin(P/"job_deadline_watchdog.py")))
old='''    allowed_env={"SystemRoot","WINDIR","ComSpec","PATH","PATHEXT",
                 "USERPROFILE","LOCALAPPDATA","APPDATA","TEMP","TMP"}'''
new='''    allowed_env={"SystemRoot","WINDIR","PATH",
                 "USERPROFILE","LOCALAPPDATA","APPDATA","TEMP","TMP"}'''
assert source.count(old)==1;source=source.replace(old,new)
old='''    stop_heartbeat=threading.Event();heartbeat_thread=None;activated=False;result=None;error=None'''
new='''    stop_heartbeat=threading.Event();heartbeat_thread=None;activated=False;result=None;error=None
    watchdog_module=module(JOB_WATCHDOG_REF,"root_independent_job_deadline")
    watchdog=None;watchdog_observation=None'''
assert source.count(old)==1;source=source.replace(old,new)
old='''        nonlocal activated,heartbeat_thread'''
new='''        nonlocal activated,heartbeat_thread,watchdog
        watchdog=watchdog_module.JobDeadlineWatchdog(actual["job_handle"],actual["absolute_deadline_monotonic"])
        watchdog.start()'''
assert source.count(old)==1;source=source.replace(old,new)
old='''                 "phase_dir":str(phase_dir),"public_environment":public_env}'''
new='''                 "phase_dir":str(phase_dir),"public_environment":public_env,
                 "phase_worker_source":pin(HERE/"phase_worker.py"),"python_binary":seed["python_binary"]}'''
assert source.count(old)==1;source=source.replace(old,new)
old='''        assert_native_closed(result)'''
new='''        assert_native_closed(result)
        require(watchdog is not None,"actual Job watchdog missing")'''
assert source.count(old)==1;source=source.replace(old,new)
old='''    finally:
        stop_heartbeat.set()'''
new='''    finally:
        if watchdog is not None:
            watchdog_observation=watchdog.stop_and_close()
            if watchdog_observation["errors"] or not watchdog_observation["duplicate_handle_closed"]:
                error=error or "absolute Job watchdog cleanup unconfirmed"
                if result is not None:
                    result["job_cleanup"]["errors"].append(error)
        stop_heartbeat.set()'''
assert source.count(old)==1;source=source.replace(old,new)
old='''            "source_runtime_qualification":False,"formal_acceptance":False})'''
new='''            "watchdog_observation":watchdog_observation,
            "source_runtime_qualification":False,"formal_acceptance":False})'''
assert source.count(old)==1;source=source.replace(old,new)
(P/"controller.py").write_text(source,encoding="utf-8",newline="")
for name in ("owned_job_hooks.py","phase_worker.py","job_probe_worker.py"):(P/name).write_bytes((BASE/name).read_bytes())
refs=[]
for name in ("controller.py","canonical_transactions.py","job_deadline_watchdog.py","owned_job_hooks.py","phase_worker.py","job_probe_worker.py"):
 raw=(P/name).read_bytes();ast.parse(raw);compile(raw,str(P/name),"exec");refs.append(pin(P/name))
(P/"controller.forward.diff").write_text("".join(difflib.unified_diff((BASE/"controller.py").read_text().splitlines(True),source.splitlines(True),fromfile="v2/controller.py",tofile="v3/controller.py")),encoding="utf-8",newline="")
(P/"controller.inverse.diff").write_text("".join(difflib.unified_diff(source.splitlines(True),(BASE/"controller.py").read_text().splitlines(True),fromfile="v3/controller.py",tofile="v2/controller.py")),encoding="utf-8",newline="")
def save(n,v):
 path=P/n
 with path.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(path)
report=save("report.json",{"schema":"researchos.mu-sdk-controller-revision-v3.v1","actor_id":"codex:/root",
"source_refs":refs,"base_ref":pin(BASE/"handoff.json"),"six_sources_compiled":True,
"proposed_changes":["Mandatory exclusive existing-file handles across canonical compare/update/verify with durable two-file before/after/partial journal","Duplicate Job handle deadline watchdog starts before synchronous callback work and records termination/cleanup","Exactly8 public OS env keys bound by v8 basis","Observer v2 Python/phase-worker context pins"],"source_execution_ready":False,
"open":["NONAUTHOR_SIX_SOURCE_AND_OBSERVER_REVIEW","ACTUAL_NATIVE_CANONICAL_OWNERSHIP_AND_CALLBACK_WATCHDOG_PROBES","ACTUAL_HOST_JOB_OR_MULTICHILD_INTEGRATION","LIVE_PHASE_REGISTRATION_GRANT_NOT_ISSUED"],
"native_candidate_executions":0,"model_calls":0,"formal_acceptance":False,"registered_failures":681,"observed_failures":682})
mf=save("manifest.json",{"schema":"researchos.immutable-source-manifest.v1","members":[pin(x) for x in sorted(P.iterdir(),key=lambda x:x.name) if x.is_file() and x.name not in ("manifest.json","handoff.json")]})
hdf=save("handoff.json",{"schema":"researchos.mu-sdk-controller-revision-v3-handoff.v1","state":"SOURCE_PREPARATION_ONLY_WITH_OPEN","actor_id":"codex:/root","manifest_ref":mf,"report_ref":report,"source_refs":refs,"source_execution_ready":False,"source_writes_stopped":True})
print(json.dumps({"handoff_ref":hdf,"manifest_ref":mf,"report_ref":report,"controller_ref":pin(P/"controller.py")}),flush=True)
