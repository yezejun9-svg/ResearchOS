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
CANONICAL_TRANSACTION_REF={'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\mu_sdk_controller_revision_v5_codex\\e5953a6723c44426a05b5bb540186cdc\\canonical_transactions.py', 'sha256': '094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9', 'bytes': 6877}
JOB_WATCHDOG_REF={'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\mu_sdk_controller_revision_v5_codex\\e5953a6723c44426a05b5bb540186cdc\\job_deadline_watchdog.py', 'sha256': '6af03123b3d8c47f07f9aa1a65d0b1b8bdc2c020244d36e51e4cc6568df035ba', 'bytes': 2953}

SOURCE_READ_GUARD_REF={'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\source_read_guard_revision_v2_codex\\d6d10c192b1940ed9c11a957411aecd9\\source_read_guard.py', 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}
PINNED_PYTHON_REF={'path': 'C:\\Users\\yqyyds\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe', 'sha256': 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b', 'bytes': 106328}
BASE_OWNED_PROCESS_REF={'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\integration_codex\\independent-cli-list-scopes-r308\\windows_owned_process.py', 'sha256': '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad', 'bytes': 18901}
_RESIDENT_OWNER_ATTR="_researchos_mu_sdk_resident_source_owner_v1"

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
        prior=ow["card_path_bindings"]["W05-99"].get("subtasks",{}).get("mu_sdk_trial")
        if prior is not None:
            require(type(prior) is dict and prior.get("state") in
                    ("CLOSED_PENDING_INDEPENDENT_EVIDENCE_REVIEW","FAILED_EXECUTION_CLOSED"),
                    "ownership SDK trial unresolved; Root reconciliation required")
            require(prior.get("run_uuid") and
                    cp["work_in_progress"].get("mu_sdk_last_phase_uuid")==prior["run_uuid"],
                    "canonical SDK trial pair inconsistent; Root reconciliation required")
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
            type(c.get("active_processes_last_observed")) is int and
            c["active_processes_last_observed"]==0 and
            all(c.get(k) is True for k in
                ("primary_exit_confirmed","job_idle_confirmed","handles_closed")))

class ResidentSourceOwner:
    """Process-resident strong references; no cross-process persistence claim."""
    def __init__(self):
        self.owner_pid=os.getpid()
        self._records={}
        self._lock=threading.RLock()

    def reserve(self,run_uuid,guard):
        require(type(run_uuid) is str and run_uuid and self.owner_pid==os.getpid(),
                "resident owner/run UUID mismatch")
        with self._lock:
            require(run_uuid not in self._records,"run UUID already has resident Source ownership")
            self._records[run_uuid]={"run_uuid":run_uuid,"owner_pid":self.owner_pid,
                "guard":guard,"watchdog":None,"state":"PRE_NATIVE",
                "native_invoked":False,"retained_monotonic":None,"reason":None}

    def record(self,run_uuid):
        with self._lock:
            return self._records.get(run_uuid)

    def invoked(self,run_uuid):
        with self._lock:
            record=self._records[run_uuid]
            require(record["state"]=="PRE_NATIVE","native invocation state changed")
            record["state"]="NATIVE_INVOKED"
            record["native_invoked"]=True

    def attach_watchdog(self,run_uuid,watchdog):
        with self._lock:
            record=self._records[run_uuid]
            require(record["state"]=="NATIVE_INVOKED","watchdog ownership without native invocation")
            record["watchdog"]=watchdog

    def retain(self,run_uuid,reason):
        with self._lock:
            record=self._records[run_uuid]
            record["state"]="RETAINED_UNCONFIRMED"
            record["reason"]=reason
            record["retained_monotonic"]=time.monotonic()
            return self.observation(run_uuid)

    def release(self,run_uuid):
        with self._lock:
            require(run_uuid in self._records,"resident Source record missing")
            del self._records[run_uuid]

    def observation(self,run_uuid):
        with self._lock:
            record=self._records[run_uuid]
            guard=record["guard"]
            retained=sum(1 for entry in guard._entries
                         if entry["handle"] is not None and not entry["closed"])
            return {"schema":"researchos.mu-sdk-source-retention.v1",
                "run_uuid":run_uuid,"owner_pid":record["owner_pid"],
                "state":record["state"],"reason":record["reason"],
                "native_invoked":record["native_invoked"],
                "retained_handles_count":retained,
                "watchdog_object_retained":record["watchdog"] is not None,
                "owner_process_resident_required":True,"cross_process_persistence":False}

def get_resident_source_owner():
    """Explicit Root parent owner, anchored in sys only while this PID lives."""
    owner=getattr(sys,_RESIDENT_OWNER_ATTR,None)
    if owner is None:
        owner=ResidentSourceOwner()
        setattr(sys,_RESIDENT_OWNER_ATTR,owner)
    require(getattr(owner,"owner_pid",None)==os.getpid() and
            callable(getattr(owner,"reserve",None)) and
            callable(getattr(owner,"record",None)),
            "resident Source owner belongs to a different process or contract")
    return owner

def _require_source_owner(source_owner):
    require(source_owner is get_resident_source_owner(),
            "Root must pass the current process-resident Source owner explicitly")

def _append_cleanup_error(result,message):
    if type(result) is dict and type(result.get("job_cleanup")) is dict:
        errors=result["job_cleanup"].get("errors")
        if type(errors) is list:errors.append(message)

def source_retention_status(run_uuid,source_owner):
    _require_source_owner(source_owner)
    record=source_owner.record(run_uuid)
    return source_owner.observation(run_uuid) if record is not None else None

def reconcile_retained_sources(run_uuid,owner_pid,source_owner,fresh_cleanup_probe=None):
    """Release only after a fresh Root-owned Job probe confirms strict cleanup."""
    _require_source_owner(source_owner)
    require(type(owner_pid) is int and owner_pid==os.getpid()==source_owner.owner_pid,
            "reconcile owner PID differs from the resident parent")
    record=source_owner.record(run_uuid)
    require(record is not None and record["state"]=="RETAINED_UNCONFIRMED",
            "no retained Source record for this run UUID")
    proof_observation={"run_uuid":run_uuid,"owner_pid":owner_pid,
                       "native_invoked":record["native_invoked"],
                       "strict_current_cleanup_confirmed":False}
    if record["native_invoked"]:
        require(callable(fresh_cleanup_probe),"fresh owned-Job cleanup probe required")
        proof=fresh_cleanup_probe(run_uuid=run_uuid,owner_pid=owner_pid,
                                  watchdog=record["watchdog"])
        require(type(proof) is dict and proof.get("run_uuid")==run_uuid and
                type(proof.get("owner_pid")) is int and proof["owner_pid"]==owner_pid and
                type(proof.get("observed_monotonic")) in (int,float) and
                proof["observed_monotonic"]>=record["retained_monotonic"] and
                cleanup_confirmed(proof.get("native_result")),
                "fresh matching owned-Job cleanup remains unconfirmed")
        proof_observation.update({"observed_monotonic":proof["observed_monotonic"],
                                  "strict_current_cleanup_confirmed":True})
    else:
        require(fresh_cleanup_probe is None,
                "no native invocation occurred; Job cleanup probe must be absent")
    watchdog=record["watchdog"]
    watchdog_observation=None
    if watchdog is not None:
        try:
            watchdog_observation=watchdog.stop_and_close()
        except BaseException as cleanup_error:
            watchdog_observation={"duplicate_handle_closed":False,
                                  "errors":[repr(cleanup_error)]}
        if watchdog_observation.get("duplicate_handle_closed") is not True:
            return {"state":"RETAINED_UNCONFIRMED","source":source_owner.retain(
                run_uuid,"watchdog duplicate cleanup unconfirmed"),
                "watchdog_observation":watchdog_observation,
                "current_cleanup_proof":proof_observation}
    try:
        guard_observation=record["guard"].close()
    except BaseException as cleanup_error:
        guard_observation={"closed":False,"retained_handles_count":None,
                           "errors":[repr(cleanup_error)]}
    if (guard_observation.get("closed") is not True or
            guard_observation.get("retained_handles_count")!=0):
        return {"state":"RETAINED_UNCONFIRMED","source":source_owner.retain(
            run_uuid,"Source guard cleanup unconfirmed"),
            "watchdog_observation":watchdog_observation,
            "source_guard_observation":guard_observation,
            "current_cleanup_proof":proof_observation}
    source_owner.release(run_uuid)
    return {"state":"RELEASED_AFTER_CONFIRMED_CLEANUP","run_uuid":run_uuid,
            "owner_pid":owner_pid,"watchdog_observation":watchdog_observation,
            "source_guard_observation":guard_observation,
            "current_cleanup_proof":proof_observation}

def close_canonical_lease(doc,phase_dir,native_result,error,transaction_module=None):
    if not cleanup_confirmed(native_result):
        return exclusive_json(phase_dir/"canonical-lease.retained-unconfirmed.json",{
            "run_uuid":doc["run_uuid"],"state":"CLEANUP_UNCONFIRMED_ACTIVE_LEASE_RETAINED",
            "native_result":native_result,"exception":error,
            "checkpoint_ref":pin(ROOT/"execution/v2.4/checkpoint.json"),
            "ownership_ref":pin(ROOT/"execution/v2.4/path_ownership.json"),
            "automatic_recovery":False,"formal_acceptance":False})
    require(transaction_module is not None,
            "canonical transaction Source was not loaded while guarded")
    transaction=transaction_module
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

def _launch_reviewed_phase_with_guard(seed,source_guard,source_owner):
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
    watchdog=None;watchdog_observation=None;source_guard_observation=None
    require(engine.cli_environment(doc)==basis["child_environment"],"Root environment differs from sealed basis")
    argv=[str(pinned(seed["python_binary"])[0]),"-I","-S","-X","utf8",str(HERE/"phase_worker.py"),str(input_path)]
    exclusive_json(phase_dir/"phase-launch.intent.json",{"argv":argv,"environment":public_env,
        "cwd":str(ROOT),"deadline_monotonic":deadline,"limits":LIMITS,
        "controller_source_ref":controller_ref,"observer_source_ref":seed["observer_source"],
        "hooks_source_ref":pin(HERE/"owned_job_hooks.py"),"phase_worker_ref":pin(HERE/"phase_worker.py")})
    def before_resume(actual):
        nonlocal activated,heartbeat_thread,watchdog
        watchdog=watchdog_module.JobDeadlineWatchdog(actual["job_handle"],actual["absolute_deadline_monotonic"])
        source_owner.attach_watchdog(doc["run_uuid"],watchdog)
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
            source_owner.invoked(doc["run_uuid"])
            result=hooks.run_owned_hooked(argv,str(ROOT),public_env,out,err,timeout,before_resume,creation_flags=0x08000000)
        assert_native_closed(result)
        require(watchdog is not None,"actual Job watchdog missing")
    except BaseException as exc:
        error=repr(exc)
        raise
    finally:
        native_invoked=source_owner.record(doc["run_uuid"])["native_invoked"]
        native_cleanup_safe=cleanup_confirmed(result)
        transaction_module=None
        if watchdog is not None:
            if native_cleanup_safe:
                try:
                    watchdog_observation=watchdog.stop_and_close()
                except BaseException as cleanup_error:
                    watchdog_observation={"duplicate_handle_closed":False,
                        "errors":[repr(cleanup_error)]}
            else:
                watchdog_observation={"state":"RETAINED_UNCONFIRMED",
                    "duplicate_handle_closed":False,
                    "errors":list(watchdog.observation.get("errors",[]))}
        watchdog_safe=(watchdog is None or (
            watchdog_observation.get("duplicate_handle_closed") is True))
        if watchdog is not None and watchdog_observation.get("errors"):
            error=error or "absolute Job watchdog cleanup reported errors"
            _append_cleanup_error(result,error)
        if activated and native_cleanup_safe and watchdog_safe:
            try:
                transaction_module=module(CANONICAL_TRANSACTION_REF,
                                          "root_owned_canonical_transaction")
            except BaseException as cleanup_error:
                error=error or "canonical transaction Source load failed: "+repr(cleanup_error)
                _append_cleanup_error(result,error)
        if not native_invoked or (native_cleanup_safe and watchdog_safe):
            try:
                source_guard_observation=source_guard.close()
            except BaseException as cleanup_error:
                source_guard_observation={"closed":False,
                    "errors":[repr(cleanup_error)],"retained_handles_count":None}
            if (source_guard_observation.get("closed") is True and
                    source_guard_observation.get("retained_handles_count")==0 and
                    not source_guard_observation.get("errors")):
                source_owner.release(doc["run_uuid"])
            else:
                error=error or "source guard cleanup unconfirmed"
                _append_cleanup_error(result,error)
                close_attempt=source_guard_observation
                source_guard_observation={"state":"RETAINED_UNCONFIRMED",
                    "retention":source_owner.retain(doc["run_uuid"],error),
                    "close_attempt":close_attempt}
        else:
            error=error or "owned Job cleanup unconfirmed; Source handles retained"
            _append_cleanup_error(result,error)
            source_guard_observation=source_owner.retain(doc["run_uuid"],error)
        stop_heartbeat.set()
        if heartbeat_thread is not None:
            try:
                if heartbeat_thread.ident is not None:heartbeat_thread.join(2)
                if heartbeat_thread.is_alive():raise RuntimeError("heartbeat thread cleanup unconfirmed")
            except BaseException as cleanup_error:
                error=error or repr(cleanup_error)
                _append_cleanup_error(result,error)
        try:
            if heartbeat_path.exists():
                old=json.loads(heartbeat_path.read_bytes());old["active"]=False;old["monotonic_tick"]=time.monotonic()
                atomic_json(heartbeat_path,old)
        except BaseException as cleanup_error:
            error=error or repr(cleanup_error)
            _append_cleanup_error(result,error)
        exclusive_json(phase_dir/"phase-launch.invocation.json",{"argv":argv,"cwd":str(ROOT),
            "result":result,"exception":error,"actual_native_exit":result["actual_exit"] if result else None,
            "stdout_ref":pin(phase_dir/"phase.stdout.raw") if (phase_dir/"phase.stdout.raw").exists() else None,
            "stderr_ref":pin(phase_dir/"phase.stderr.raw") if (phase_dir/"phase.stderr.raw").exists() else None,
            "watchdog_observation":watchdog_observation,"source_guard_observation":source_guard_observation,
            "source_runtime_qualification":False,"formal_acceptance":False})
        if activated:close_canonical_lease(doc,phase_dir,result,error,transaction_module)
    if error is not None:raise RuntimeError(error)
    return pin(phase_dir/"phase-launch.invocation.json")


def launch_reviewed_phase(seed,source_owner):
    """Hold the reviewed Sources and interpreter across every path consumer."""
    _require_source_owner(source_owner)
    require(seed["phase_ready_for_execution"] is True,"phase preparation is not ready")
    _,review_raw=pinned(seed["controller_source_review"])
    review=json.loads(review_raw)
    require(review.get("schema")=="researchos.mu-sdk-controller-observer-independent-source-review.v2" and
            review.get("decision")=="READY_SOURCE_ONLY" and
            review.get("actor_id") not in (None,"","codex:/root","codex:/root/w05_merge_review") and
            review.get("formal_acceptance") is False,"independent exact Source review required before import")
    require(review.get("runner_source_ref")==seed["runner_source"] and
            review.get("observer_source_ref")==seed["observer_source"] and
            review.get("python_binary_ref")==seed["python_binary"]==PINNED_PYTHON_REF and
            Path(review["controller_source_ref"]["path"])==Path(__file__).resolve() and
            Path(review["hooks_source_ref"]["path"])==HERE/"owned_job_hooks.py" and
            Path(review["phase_worker_source_ref"]["path"])==HERE/"phase_worker.py",
            "guarded Source tuple differs from independent review")
    references=[review[k] for k in ("controller_source_ref","observer_source_ref","hooks_source_ref",
                "runner_source_ref","phase_worker_source_ref","python_binary_ref")]
    references += [seed["controller_source_review"],SOURCE_READ_GUARD_REF,
                   CANONICAL_TRANSACTION_REF,JOB_WATCHDOG_REF,BASE_OWNED_PROCESS_REF]
    guard_module=module(SOURCE_READ_GUARD_REF,"reviewed_source_read_guard")
    guard=guard_module.SourceReadGuard()
    run_uuid=seed["input_doc"]["run_uuid"]
    source_owner.reserve(run_uuid,guard)
    try:
        guard.acquire(references)
        require(guard.get_buffer(seed["controller_source_review"]["path"])==review_raw,
                "Source review changed before guard acquisition")
        # The files below remain deny-write/deny-delete while existing consumers
        # open those exact paths. Parent modules and the child cannot load new bytes.
        return _launch_reviewed_phase_with_guard(seed,guard,source_owner)
    finally:
        record=source_owner.record(run_uuid)
        if record is not None and record["state"]=="PRE_NATIVE":
            try:
                observation=guard.close()
            except BaseException as cleanup_error:
                source_owner.retain(run_uuid,"pre-native Source close raised: "+repr(cleanup_error))
                raise
            if observation.get("closed") is True and observation.get("retained_handles_count")==0:
                source_owner.release(run_uuid)
            else:
                source_owner.retain(run_uuid,"pre-native Source close unconfirmed")
        elif record is not None and record["state"]=="NATIVE_INVOKED":
            source_owner.retain(run_uuid,"native finalization interrupted; Source and Job objects retained")
