"""Root trial phase controller. No action occurs on import.

The caller must supply a frozen, independently reviewed phase seed. This module
does not invent project, runtime, qualification, discovery or budget facts.
Qualification Host dispatch integration is a separate prerequisite.
"""
import sys
sys.dont_write_bytecode=True
import hashlib, json, os, threading, time, types, uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT=Path("D:/作品集/ResearchOS/research-os")
SOURCE_COMMIT="adc460c2138528f163f7fdab5e8d81dde157b7fb"
LIMITS={"maximum_provider_requests":3,"requested_output_tokens_total":8192,"total_wall_seconds":300}
HERE=Path(__file__).resolve().parent
CANONICAL_TRANSACTION_REF={'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\mu_sdk_controller_revision_v3_codex\\41ee2ad00c864829b5f6926c5fac919f\\canonical_transactions.py', 'sha256': '094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9', 'bytes': 6877}
JOB_WATCHDOG_REF={'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\mu_sdk_controller_revision_v3_codex\\41ee2ad00c864829b5f6926c5fac919f\\job_deadline_watchdog.py', 'sha256': '0c859dfc70a366f2ab98e1c47cc639e4b182e370f5d2ef8e5e2ff90feb72fc6e', 'bytes': 2705}

def require(ok,message):
    if not ok: raise RuntimeError(message)

def pin(path):
    path=Path(path);raw=path.read_bytes()
    return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def pinned(reference):
    path=Path(reference["path"])
    require(path.is_absolute() and path.is_file(),"absolute existing pin required")
    raw=path.read_bytes()
    require({"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}==reference,"pinned input changed")
    return path,raw

def module(reference,name):
    path,raw=pinned(reference);m=types.ModuleType(name);m.__file__=str(path)
    exec(compile(raw,str(path),"exec"),m.__dict__)
    return m

def exclusive_json(path,value):
    path=Path(path)
    with path.open("xb") as out:
        out.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
    return pin(path)

def atomic_json(path,value):
    path=Path(path);temp=path.with_name(path.name+"."+uuid.uuid4().hex)
    exclusive_json(temp,value)
    os.replace(temp,path)

def stamp():
    return datetime.now(timezone.utc).isoformat()

def assert_native_closed(result):
    c=result["job_cleanup"]
    require(result["actual_exit"]==0 and not result["timed_out"] and result["error"] is None,"phase native operation failed")
    require(c["errors"]==[] and c["active_processes_last_observed"]==0 and
            all(c[k] for k in ("unnamed_exclusive_job","kill_on_job_close_configured",
            "assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")),
            "owned Job cleanup incomplete")

def activate_canonical_lease(doc,lease_ref,expected_cp,expected_ownership,phase_dir):
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

def cleanup_confirmed(result):
    if type(result) is not dict:return False
    c=result.get("job_cleanup",{})
    return (type(c) is dict and c.get("errors")==[] and
            c.get("active_processes_last_observed")==0 and
            all(c.get(k) is True for k in
                ("primary_exit_confirmed","job_idle_confirmed","handles_closed")))

def close_canonical_lease(doc,phase_dir,native_result,error):
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

def launch_reviewed_phase(seed):
    """Create the reviewed phase in a suspended Job, observe, then resume once.

    started_monotonic/deadline and registration UTC come from the Root trial
    start before creating the qualification Run; they are never reset here.
    The trusted Host admission/dispatch prerequisite must be separately wired
    and reviewed before using this function for execute.
    """
    require(seed["phase_ready_for_execution"] is True,"phase preparation is not ready")
    doc=dict(seed["input_doc"]);phase=doc["phase"]
    require(phase in ("bootstrap","execute") and doc["source_commit"]==SOURCE_COMMIT,"wrong phase/source")
    for key,value in LIMITS.items():require(doc[key]==value,"trial limits changed")
    phase_dir=Path(seed["phase_dir"])
    require(phase_dir.is_absolute() and not phase_dir.exists() and phase_dir.parent.is_dir(),"fresh phase directory required")
    phase_dir.mkdir()
    started,deadline=seed["started_monotonic"],seed["absolute_deadline_monotonic"]
    require(type(started) in (float,int) and type(deadline) in (float,int) and
            0<deadline-started<=300 and time.monotonic()>=started and
            deadline-time.monotonic()>1,"invalid or exhausted trial deadline")
    source_path,_=pinned(seed["runner_source"]);engine=module(seed["runner_source"],"root_phase_basis_engine")
    public_env=dict(seed["public_environment"])
    allowed_env={"SystemRoot","WINDIR","PATH",
                 "USERPROFILE","LOCALAPPDATA","APPDATA","TEMP","TMP"}
    require(set(public_env)<=allowed_env and all(type(k) is str and type(v) is str
            and "\x00" not in k and "\x00" not in v for k,v in public_env.items()),
            "public process environment is not closed")
    require(public_env.get("SystemRoot")=="C:/Windows" and
            public_env.get("WINDIR")=="C:/Windows","unexpected Windows system root")
    public_os=types.ModuleType("root_frozen_public_os")
    public_os.__dict__.update(vars(os));public_os.environ=public_env
    engine.os=public_os
    require(engine.SOURCE_COMMIT==SOURCE_COMMIT and engine.MAX_PROVIDER_REQUESTS==3 and
            engine.MAX_WALL_SECONDS==300 and engine.MAX_OUTPUT_TOKENS_TOTAL_REQUESTED==8192,"reviewed runner limits changed")
    observer=module(seed["observer_source"],"independently_authored_startup_observer")
    hooks=module(pin(HERE/"owned_job_hooks.py"),"root_hooked_owned_process")
    controller_ref=pin(Path(__file__).resolve())
    basis=engine.phase_basis(doc,phase);doc["input_basis_ref"]=exclusive_json(phase_dir/"phase-basis.json",basis)
    reg={"schema":"researchos.mu-sdk-trial-root-registration.v1","actor_id":"codex:/root",
         "owner":"codex:/root/mu-sdk-isolated-trial","run_uuid":doc["run_uuid"],"phase":phase,
         "source_commit":SOURCE_COMMIT,"source_ref":seed["runner_source"],"limits":LIMITS,
         "input_basis_ref":doc["input_basis_ref"],"started_at_utc":doc["root_registration_started_at_utc"],
         "started_monotonic":started,"absolute_deadline_monotonic":deadline}
    for key in ("data_root","workspace","repository_root","once_path","qualification_task_id",
                "qualification_run_id","qualification_epoch","runtime_id","profile_entity_ref","qualification_profile_hash"):
        reg[key]=doc.get(key)
    reg["public_route_manifest_ref"]=doc.get("public_route_manifest");reg["runtime_profile_ref"]=doc.get("runtime_profile")
    reg["phase_dir"]=str(phase_dir)
    doc["root_registration"]=exclusive_json(phase_dir/"root-registration.json",reg)
    lease={"schema":"researchos.mu-sdk-trial-owner-lease.v1","state":"ACTIVE","owner":reg["owner"],
           "run_uuid":doc["run_uuid"],"data_root":doc["data_root"],"phase_dir":str(phase_dir),
           "expires_at_utc":(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()}
    doc["owner_lease"]=exclusive_json(phase_dir/"owner-lease.json",lease)
    heartbeat_path=Path(doc["data_root"])/"trial-control"/(doc["run_uuid"]+".heartbeat.json")
    require(heartbeat_path.parent.is_dir(),"actual trial-control directory missing")
    input_path=phase_dir/"input.execute.json"
    stop_heartbeat=threading.Event();heartbeat_thread=None;activated=False;result=None;error=None
    watchdog_module=module(JOB_WATCHDOG_REF,"root_independent_job_deadline")
    watchdog=None;watchdog_observation=None
    require(engine.cli_environment(doc)==basis["child_environment"],"Root environment differs from sealed basis")
    argv=[str(pinned(seed["python_binary"])[0]),"-I","-S","-X","utf8",str(HERE/"phase_worker.py"),str(input_path)]
    exclusive_json(phase_dir/"phase-launch.intent.json",{"argv":argv,"environment":public_env,
        "cwd":str(ROOT),"deadline_monotonic":deadline,"limits":LIMITS,
        "controller_source_ref":controller_ref,"observer_source_ref":seed["observer_source"],
        "hooks_source_ref":pin(HERE/"owned_job_hooks.py"),"phase_worker_ref":pin(HERE/"phase_worker.py")})
    def before_resume(actual):
        nonlocal activated,heartbeat_thread,watchdog
        watchdog=watchdog_module.JobDeadlineWatchdog(actual["job_handle"],actual["absolute_deadline_monotonic"])
        watchdog.start()
        require(actual["assigned_before_resume"] and actual["kill_on_job_close_configured"] and
                not actual["resumed"] and actual["absolute_deadline_monotonic"]<=deadline,
                "actual bounded suspended Job preconditions failed")
        pid=actual["runner_pid"]
        outer={"schema":"researchos.mu-sdk-trial-outer-job.v1","run_uuid":doc["run_uuid"],
               "runner_pid":pid,"kill_on_close":True,"owns_child_tree":True,"wall_seconds":300,
               "controller_source_ref":controller_ref,"heartbeat_path":str(heartbeat_path),
               "absolute_deadline_monotonic":deadline,
               "actual_owned_runner_deadline_monotonic":actual["absolute_deadline_monotonic"],
               "actual_creation_time_100ns":actual["creation_time_100ns"]}
        doc["outer_job_contract"]=exclusive_json(phase_dir/"outer-job.json",outer)
        doc["controller_source"]=controller_ref
        canonical=activate_canonical_lease(doc,doc["owner_lease"],seed["parent_checkpoint"],seed["parent_ownership"],phase_dir)
        activated=True;doc["root_checkpoint"]=canonical["checkpoint_ref"]
        def write_heartbeat():
            atomic_json(heartbeat_path,{"schema":"researchos.mu-sdk-trial-job-heartbeat.v1",
                "run_uuid":doc["run_uuid"],"runner_pid":pid,"active":True,"monotonic_tick":time.monotonic()})
        write_heartbeat()
        def heartbeat():
            while not stop_heartbeat.is_set():
                write_heartbeat()
                stop_heartbeat.wait(0.5)
        heartbeat_thread=threading.Thread(target=heartbeat,daemon=True);heartbeat_thread.start()
        context={"input_doc":doc,"outer_job_contract":doc["outer_job_contract"],
                 "controller_source":controller_ref,"hooks_source":pin(HERE/"owned_job_hooks.py"),
                 "observer_source":seed["observer_source"],"independent_source_review":seed["controller_source_review"],
                 "phase_dir":str(phase_dir),"public_environment":public_env,
                 "phase_worker_source":pin(HERE/"phase_worker.py"),"python_binary":seed["python_binary"]}
        observed=observer.observe_assigned_before_resume(context,
            process_handle=actual["process_handle"],thread_handle=actual["thread_handle"],
            job_handle=actual["job_handle"],pid=pid,creation_filetime=actual["creation_time_100ns"])
        doc["job_probe_receipt"]=observed["job_probe"];doc["controller_review"]=observed["controller_review"]
        doc["root_review"]=observed["nonauthor_review"]
        review_doc=json.loads(pinned(doc["root_review"])[1])
        require(review_doc["actor_id"] not in ("codex:/root",reg["owner"]),"automatic observer lacks independent author provenance")
        grant={"schema":"researchos.mu-sdk-trial-root-grant.v1","actor_id":"codex:/root",
               "decision":"ALLOW_ISOLATED_MU_SDK_TRIAL","phase":phase,"run_uuid":doc["run_uuid"],
               "registration_ref":doc["root_registration"],"review_ref":doc["root_review"],
               "source_ref":seed["runner_source"],"input_basis_ref":doc["input_basis_ref"],"limits":LIMITS,
               "outer_job_ref":doc["outer_job_contract"],"controller_review_ref":doc["controller_review"],
               "absolute_deadline_monotonic":deadline}
        for key in ("once_path","data_root","workspace","repository_root","qualification_run_id","runtime_id","profile_entity_ref"):
            grant[key]=doc.get(key)
        grant["runtime_profile_ref"]=doc.get("runtime_profile");grant["public_route_manifest_ref"]=doc.get("public_route_manifest")
        doc["root_grant"]=exclusive_json(phase_dir/"root-grant.json",grant)
        exclusive_json(input_path,doc)
        require(time.monotonic()<actual["absolute_deadline_monotonic"],"startup review exhausted actual Job deadline")
    try:
        with (phase_dir/"phase.stdout.raw").open("xb") as out,(phase_dir/"phase.stderr.raw").open("xb") as err:
            timeout=deadline-time.monotonic()-0.25
            require(timeout>0,"trial deadline expired before CreateProcess")
            result=hooks.run_owned_hooked(argv,str(ROOT),public_env,out,err,timeout,before_resume,creation_flags=0x08000000)
        assert_native_closed(result)
        require(watchdog is not None,"actual Job watchdog missing")
    except BaseException as exc:
        error=repr(exc)
        raise
    finally:
        if watchdog is not None:
            watchdog_observation=watchdog.stop_and_close()
            if watchdog_observation["errors"] or not watchdog_observation["duplicate_handle_closed"]:
                error=error or "absolute Job watchdog cleanup unconfirmed"
                if result is not None:
                    result["job_cleanup"]["errors"].append(error)
        stop_heartbeat.set()
        if heartbeat_thread is not None:heartbeat_thread.join(2)
        if heartbeat_path.exists():
            old=json.loads(heartbeat_path.read_bytes());old["active"]=False;old["monotonic_tick"]=time.monotonic()
            atomic_json(heartbeat_path,old)
        exclusive_json(phase_dir/"phase-launch.invocation.json",{"argv":argv,"cwd":str(ROOT),
            "result":result,"exception":error,"actual_native_exit":result["actual_exit"] if result else None,
            "stdout_ref":pin(phase_dir/"phase.stdout.raw") if (phase_dir/"phase.stdout.raw").exists() else None,
            "stderr_ref":pin(phase_dir/"phase.stderr.raw") if (phase_dir/"phase.stderr.raw").exists() else None,
            "watchdog_observation":watchdog_observation,
            "source_runtime_qualification":False,"formal_acceptance":False})
        if activated:close_canonical_lease(doc,phase_dir,result,error)
    return pin(phase_dir/"phase-launch.invocation.json")
