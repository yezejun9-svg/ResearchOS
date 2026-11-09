import sys
sys.dont_write_bytecode=True
import ast,difflib,hashlib,json,shutil
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os")
O=Path(__file__).resolve().parent
OLD=R/"execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_revision_v3_codex/41ee2ad00c864829b5f6926c5fac919f"
GUARD_REF={'path': 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py', 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}
PYTHON_REF={"path":"C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe","sha256":"cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b","bytes":106328}
BASE_PROCESS_REF={"path":str(R/"execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"),"sha256":"6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad","bytes":18901}
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,v):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
assert GUARD_REF is not None
assert pin(Path(GUARD_REF["path"]))==GUARD_REF
assert pin(Path(PYTHON_REF["path"]))==PYTHON_REF
assert pin(Path(BASE_PROCESS_REF["path"]))==BASE_PROCESS_REF
frozen_paths=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
frozen={p:p.read_bytes() for p in frozen_paths}
old_controller=(OLD/"controller.py").read_bytes()
assert hashlib.sha256(old_controller).hexdigest()=="273523f540f3ad1d3cb6adab1791d6887af2f8682f8fece9d840d6e0979c9c4f" and len(old_controller)==17627
old_watch=(OLD/"job_deadline_watchdog.py").read_bytes()
assert hashlib.sha256(old_watch).hexdigest()=="0c859dfc70a366f2ab98e1c47cc639e4b182e370f5d2ef8e5e2ff90feb72fc6e"
for n in ("owned_job_hooks.py","phase_worker.py","job_probe_worker.py","canonical_transactions.py"):
 with (O/n).open("xb") as f:f.write((OLD/n).read_bytes())
watch=old_watch.decode()
def replace_once(raw,old,new):
 assert raw.count(old)==1,old[:100]
 return raw.replace(old,new,1)
watch=replace_once(watch,"self.deadline=deadline;self.stop=threading.Event();self.thread=None",
 "self.deadline=deadline;self.stop=threading.Event();self.thread=None;self.thread_started=False")
watch=replace_once(watch,'self.thread=threading.Thread(target=watch,daemon=True);self.thread.start()',
 '''self.thread=threading.Thread(target=watch,daemon=True)
        try:
            self.thread.start()
            self.thread_started=True
        except BaseException as exc:
            self.observation["errors"].append("Thread.start failed: "+repr(exc))
            raise''')
watch=replace_once(watch,'if self.thread is not None:\n            self.thread.join(2)',
 'if self.thread is not None and self.thread_started:\n            self.thread.join(2)')
with (O/"job_deadline_watchdog.py").open("xb") as f:f.write(watch.encode())
controller=old_controller.decode()
tree=ast.parse(controller)
for name,ref in (("CANONICAL_TRANSACTION_REF",pin(O/"canonical_transactions.py")),("JOB_WATCHDOG_REF",pin(O/"job_deadline_watchdog.py"))):
 node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
 old_line=controller.splitlines()[node.lineno-1]
 controller=replace_once(controller,old_line,name+"="+repr(ref))
controller=replace_once(controller,"\ndef require(ok,message):",
 "\nSOURCE_READ_GUARD_REF="+repr(GUARD_REF)+"\nPINNED_PYTHON_REF="+repr(PYTHON_REF)+"\nBASE_OWNED_PROCESS_REF="+repr(BASE_PROCESS_REF)+"\n\ndef require(ok,message):")
controller=replace_once(controller,
 'require(cp["work_in_progress"].get("mu_sdk_active_run_uuid") in (None,""),"another SDK trial lease remains active")',
 '''require(cp["work_in_progress"].get("mu_sdk_active_run_uuid") in (None,""),"another SDK trial lease remains active")
        prior=ow["card_path_bindings"]["W05-99"].get("subtasks",{}).get("mu_sdk_trial")
        if prior is not None:
            require(type(prior) is dict and prior.get("state") in
                    ("CLOSED_PENDING_INDEPENDENT_EVIDENCE_REVIEW","FAILED_EXECUTION_CLOSED"),
                    "ownership SDK trial unresolved; Root reconciliation required")
            require(prior.get("run_uuid") and
                    cp["work_in_progress"].get("mu_sdk_last_phase_uuid")==prior["run_uuid"],
                    "canonical SDK trial pair inconsistent; Root reconciliation required")''')
controller=replace_once(controller,'def launch_reviewed_phase(seed):','def _launch_reviewed_phase_with_guard(seed,source_guard):')
controller=replace_once(controller,'watchdog=None;watchdog_observation=None','watchdog=None;watchdog_observation=None;source_guard_observation=None')
controller=replace_once(controller,
 '''        if watchdog is not None:
            watchdog_observation=watchdog.stop_and_close()
            if watchdog_observation["errors"] or not watchdog_observation["duplicate_handle_closed"]:
                error=error or "absolute Job watchdog cleanup unconfirmed"
                if result is not None:
                    result["job_cleanup"]["errors"].append(error)''',
 '''        if watchdog is not None:
            try:
                watchdog_observation=watchdog.stop_and_close()
            except BaseException as cleanup_error:
                watchdog_observation={"duplicate_handle_closed":False,"errors":[repr(cleanup_error)]}
            if watchdog_observation["errors"] or not watchdog_observation["duplicate_handle_closed"]:
                error=error or "absolute Job watchdog cleanup unconfirmed"
                if result is not None:result["job_cleanup"]["errors"].append(error)
        try:
            source_guard_observation=source_guard.close()
        except BaseException as cleanup_error:
            source_guard_observation={"closed":False,"errors":[repr(cleanup_error)],"retained_handles_count":None}
        if source_guard_observation.get("closed") is not True or source_guard_observation.get("errors"):
            error=error or "source guard cleanup unconfirmed"
            if result is not None:result["job_cleanup"]["errors"].append(error)''')
controller=replace_once(controller,
 '''        if heartbeat_thread is not None:heartbeat_thread.join(2)
        if heartbeat_path.exists():
            old=json.loads(heartbeat_path.read_bytes());old["active"]=False;old["monotonic_tick"]=time.monotonic()
            atomic_json(heartbeat_path,old)''',
 '''        if heartbeat_thread is not None:
            try:
                if heartbeat_thread.ident is not None:heartbeat_thread.join(2)
                if heartbeat_thread.is_alive():raise RuntimeError("heartbeat thread cleanup unconfirmed")
            except BaseException as cleanup_error:
                error=error or repr(cleanup_error)
                if result is not None:result["job_cleanup"]["errors"].append(error)
        try:
            if heartbeat_path.exists():
                old=json.loads(heartbeat_path.read_bytes());old["active"]=False;old["monotonic_tick"]=time.monotonic()
                atomic_json(heartbeat_path,old)
        except BaseException as cleanup_error:
            error=error or repr(cleanup_error)
            if result is not None:result["job_cleanup"]["errors"].append(error)''')
controller=replace_once(controller,
 '"watchdog_observation":watchdog_observation,',
 '"watchdog_observation":watchdog_observation,"source_guard_observation":source_guard_observation,')
controller=replace_once(controller,
 '    return pin(phase_dir/"phase-launch.invocation.json")',
 '    if error is not None:raise RuntimeError(error)\n    return pin(phase_dir/"phase-launch.invocation.json")')
controller += '''

def launch_reviewed_phase(seed):
    """Hold the reviewed Sources and interpreter across every path consumer."""
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
    try:
        guard.acquire(references)
        require(guard.get_buffer(seed["controller_source_review"]["path"])==review_raw,
                "Source review changed before guard acquisition")
        # The files below remain deny-write/deny-delete while existing consumers
        # open those exact paths. Parent modules and the child cannot load new bytes.
        return _launch_reviewed_phase_with_guard(seed,guard)
    finally:
        observation=guard.close()
        if observation.get("closed") is not True:
            raise RuntimeError("Source guard retains handles after phase cleanup")
'''
with (O/"controller.py").open("xb") as f:f.write(controller.encode())
for p in O.glob("*.py"):compile(p.read_bytes(),str(p),"exec")
for name,a,b in (("controller.forward.diff",old_controller,controller.encode()),("controller.inverse.diff",controller.encode(),old_controller),("watchdog.forward.diff",old_watch,watch.encode()),("watchdog.inverse.diff",watch.encode(),old_watch)):
 with (O/name).open("xb") as f:f.write("".join(difflib.unified_diff(a.decode().splitlines(keepends=True),b.decode().splitlines(keepends=True),fromfile="before",tofile="after")).encode())
assert all(p.read_bytes()==b for p,b in frozen.items())
report=save("report.json",{"schema":"researchos.mu-sdk-controller-v4-author-source-preparation.v1","actor":"codex:/root",
 "decision":"SOURCE_PREPARATION_ONLY","old_controller_ref":pin(OLD/"controller.py"),"source_ref":pin(O/"controller.py"),
 "fixes":["admission rejects OW active/unresolved or inconsistent last UUID even if CP is empty","Thread.start failure does not join an unstarted thread; duplicate is closed in controller finally and invocation preserved","exact reviewed tuple and pinned Python under SourceReadGuard before modules and across Resume/path consumption; guard close failure retains lease"],
 "actual_source_execution":False,"real_WinAPI_calls":0,"provider_requests":0,"formal_acceptance":False,
 "helper_refs":[CANON for CANON in (pin(O/"canonical_transactions.py"),pin(O/"job_deadline_watchdog.py"),GUARD_REF)],
 "python_binary_ref":PYTHON_REF,"frozen_canonical_refs":[pin(p) for p in frozen_paths]})
manifest=save("manifest.json",{"schema":"researchos.mu-sdk-controller-v4-source-manifest.v1","actor":"codex:/root","members":[pin(p) for p in sorted(O.iterdir()) if p.is_file()],"excludes":["manifest.json","handoff.json"]})
hdf=save("handoff.json",{"schema":"researchos.mu-sdk-controller-v4-source-handoff.v1","actor":"codex:/root",
 "decision":"SOURCE_PROPOSED_UNEXECUTED","source_ref":pin(O/"controller.py"),"hooks_ref":pin(O/"owned_job_hooks.py"),
 "phase_worker_ref":pin(O/"phase_worker.py"),"canonical_transactions_ref":pin(O/"canonical_transactions.py"),
 "job_watchdog_ref":pin(O/"job_deadline_watchdog.py"),"source_read_guard_ref":GUARD_REF,"python_binary_ref":PYTHON_REF,
 "old_handoff_ref":pin(OLD/"handoff.json"),"manifest_ref":manifest,"report_ref":report,
 "provider_requests":0,"runtime_qualification":False,"formal_acceptance":False,
 "open":["Non-author C4 and new O3/v9 full Source tuple review must be READY_SOURCE_ONLY","Actual no-provider mandatory locks/source fences/Job same-PID before Resume/deadline/cleanup probes","Separate trusted Host whole-trial lifecycle and pinned input preparation","No seed ready flag, runtime registration or Root model grant supplied"]})
print(json.dumps({"handoff_ref":hdf,"manifest_ref":manifest,"source_ref":pin(O/"controller.py"),"watchdog_ref":pin(O/"job_deadline_watchdog.py"),"status":"SOURCE_PROPOSED_UNEXECUTED"}),flush=True)

