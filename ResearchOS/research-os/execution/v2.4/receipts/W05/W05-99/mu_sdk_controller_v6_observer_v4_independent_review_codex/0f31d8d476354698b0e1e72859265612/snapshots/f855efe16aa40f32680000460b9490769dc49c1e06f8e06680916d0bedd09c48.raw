"""Pure fake-kernel controls for C6; never loads WinAPI or starts processes."""
import importlib.util
import ast
import json
import os
from pathlib import Path
import sys
import time
import uuid

HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True

def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+".py"))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

c=load("controller")
p=load("held_job_cleanup_producer")
checks=[]

def check(name,body):
    body()
    checks.append(name)

def rejected(body):
    try:body()
    except (RuntimeError,ValueError,TypeError,KeyError):return
    raise AssertionError("negative case accepted")

class FakeKernel:
    def __init__(self):
        self.active=1
        self.signaled=False
        self.pid=42117
        self.creation=71940000000000000
        self.member=True
        self.closed=[]
        self.fail_close=False
    def duplicate(self,handle):return handle+10000
    def process_id(self,handle):return self.pid
    def creation_time_100ns(self,handle):return self.creation
    def in_job(self,process,job):return self.member
    def active_processes(self,job):return self.active
    def primary_exit(self,process):return self.signaled, 259 if self.signaled else None
    def close(self,handle):
        if self.fail_close:raise OSError("synthetic close failure")
        self.closed.append(handle)

def make_producer(run_uuid=None,fake=None):
    run_uuid=run_uuid or uuid.uuid4().hex
    fake=fake or FakeKernel()
    producer=p.HeldJobCleanupProducer(run_uuid,os.getpid(),lambda:fake)
    actual={"assigned_before_resume":True,"kill_on_job_close_configured":True,
        "resumed":False,"runner_pid":fake.pid,"creation_time_100ns":fake.creation,
        "job_handle":151,"process_handle":152}
    return producer,actual,fake

def capture_baseline():
    producer,actual,fake=make_producer()
    identity=producer.capture_before_resume(actual)
    assert identity["runner_pid"]==fake.pid
    assert producer.observe_current()["active_processes"]==1
    assert producer.close()["closed"] is True
check("capture and observed identity from duplicate handles",capture_baseline)

def capture_negatives():
    for mutate in (
        lambda a:a.update(resumed=True),
        lambda a:a.update(assigned_before_resume=False),
        lambda a:a.update(runner_pid=111),
        lambda a:a.update(creation_time_100ns=111)):
        producer,actual,fake=make_producer()
        mutate(actual)
        rejected(lambda:producer.capture_before_resume(actual))
    producer,actual,fake=make_producer()
    fake.member=False
    rejected(lambda:producer.capture_before_resume(actual))
    assert producer.job_handle is not None and producer.primary_handle is not None
    assert producer.close()["closed"] is True
check("reject wrong suspended frame and Job membership",capture_negatives)

class FakeGuard:
    def __init__(self):
        self._entries=[{"handle":55,"closed":False}]
        self.closed=False
    def close(self):
        self.closed=True
        self._entries[0]["closed"]=True
        return {"closed":True,"retained_handles_count":0,"errors":[]}

class FakeWatchdog:
    def stop_and_close(self):return {"duplicate_handle_closed":True,"errors":[]}

def make_retained():
    producer,actual,fake=make_producer()
    owner=c.get_resident_source_owner()
    guard=FakeGuard()
    owner.reserve(producer.run_uuid,guard)
    owner.invoked(producer.run_uuid)
    owner.attach_producer(producer.run_uuid,producer)
    identity=producer.capture_before_resume(actual)
    owner.bind_job_identity(producer.run_uuid,identity)
    owner.attach_watchdog(producer.run_uuid,FakeWatchdog())
    owner.retain(producer.run_uuid,"simulated uncertain cleanup")
    return owner,producer,fake,guard

def reconcile_cases():
    owner,producer,fake,guard=make_retained()
    run=producer.run_uuid
    rejected(lambda:c.reconcile_retained_sources(run,os.getpid()+1,owner))
    rejected(lambda:c.reconcile_retained_sources(run,os.getpid(),owner,
                                                  lambda **kw:{"native_result":{}}))
    rejected(lambda:c.reconcile_retained_sources(run,os.getpid(),owner))
    assert not guard.closed
    fake.active=0
    rejected(lambda:c.reconcile_retained_sources(run,os.getpid(),owner))
    assert not guard.closed
    fake.signaled=True
    fake.pid+=1
    rejected(lambda:c.reconcile_retained_sources(run,os.getpid(),owner))
    assert not guard.closed
    fake.pid-=1
    fake.creation+=1
    rejected(lambda:c.reconcile_retained_sources(run,os.getpid(),owner))
    assert not guard.closed
    fake.creation-=1
    result=c.reconcile_retained_sources(run,os.getpid(),owner)
    assert result["state"]=="RELEASED_AFTER_CONFIRMED_CLEANUP"
    assert result["current_cleanup_proof"]["strict_current_cleanup_confirmed"]
    assert result["current_cleanup_proof"]["native_observation"]["primary_exit_code"]==259
    assert guard.closed and owner.record(run) is None
check("fresh held-Job OS proof rejects active, unsignaled, wrong PID/creation",reconcile_cases)

def forged_observation_cases():
    for key,value in (("run_uuid","other-run"),
                      ("job_binding_id","other-job"),
                      ("observed_monotonic",time.monotonic()+9999)):
        owner,producer,fake,guard=make_retained()
        fake.active=0;fake.signaled=True
        original=producer.observe_current
        def altered(key=key,value=value):
            observed=original()
            observed[key]=value
            return observed
        producer.observe_current=altered
        rejected(lambda:c.reconcile_retained_sources(producer.run_uuid,os.getpid(),owner))
        assert not guard.closed and owner.record(producer.run_uuid) is not None
        producer.observe_current=original
        result=c.reconcile_retained_sources(producer.run_uuid,os.getpid(),owner)
        assert result["state"]=="RELEASED_AFTER_CONFIRMED_CLEANUP"
check("forged run/Job binding and future observation cannot release Source",forged_observation_cases)

def producer_close_retry():
    owner,producer,fake,guard=make_retained()
    fake.active=0;fake.signaled=True;fake.fail_close=True
    result=c.reconcile_retained_sources(producer.run_uuid,os.getpid(),owner)
    assert result["state"]=="RETAINED_UNCONFIRMED" and guard.closed
    assert owner.record(producer.run_uuid)["guard_released"]
    fake.fail_close=False
    result=c.reconcile_retained_sources(producer.run_uuid,os.getpid(),owner)
    assert result["state"]=="RELEASED_AFTER_CONFIRMED_CLEANUP"
check("duplicate-handle close failure retains parent record for retry",producer_close_retry)

def review_actor_cases():
    refs={key:{"path":key,"sha256":key,"bytes":1} for key in (
        "controller_source","observer_source","hooks_source","phase_worker_source",
        "runner_source","canonical_transactions_source","job_watchdog_source",
        "source_guard_source","base_owned_process_source","cleanup_producer_source",
        "python_binary")}
    provenance=c.expected_source_provenance(refs)
    for actor in ("codex:/root","codex:/root/w05_merge_review",
                  "codex:/root/live_resource_lookup","ACTOR",""):
        rejected(lambda actor=actor:c.validate_review_actor(
            {"actor_id":actor,"source_provenance":provenance},refs))
    forged=json.loads(json.dumps(provenance))
    forged["sources"]["controller"]["authors"]=[]
    rejected(lambda:c.validate_review_actor(
        {"actor_id":"external:reviewer","source_provenance":forged},refs))
    c.validate_review_actor(
        {"actor_id":"external:reviewer","source_provenance":provenance},refs)
check("Source author exclusion cannot be altered by review payload",review_actor_cases)

def o4_cross_contract():
    o4_path=Path(c.OBSERVER_SOURCE_REF["path"])
    tree=ast.parse(o4_path.read_bytes(),filename=str(o4_path))
    wanted={"SOURCE_PROVENANCE_SCHEMA","SOURCE_AUTHOR_POLICY","RUNNER_REF"}
    function_names={"require","source_author_provenance"}
    nodes=[]
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and
                t.id in wanted for t in node.targets):
            nodes.append(node)
        elif isinstance(node,ast.FunctionDef) and node.name in function_names:
            nodes.append(node)
    assert len(nodes)==5
    isolated=ast.Module(body=nodes,type_ignores=[])
    namespace={}
    exec(compile(ast.fix_missing_locations(isolated),str(o4_path)+"::pure-extract","exec"),namespace)
    refs={
        "controller_source":c.pin(HERE/"controller.py"),
        "observer_source":c.OBSERVER_SOURCE_REF,
        "hooks_source":c.pin(HERE/"owned_job_hooks.py"),
        "phase_worker_source":c.pin(HERE/"phase_worker.py"),
        "runner_source":namespace["RUNNER_REF"],
        "canonical_transactions_source":c.CANONICAL_TRANSACTION_REF,
        "job_watchdog_source":c.JOB_WATCHDOG_REF,
        "source_guard_source":c.SOURCE_READ_GUARD_REF,
        "base_owned_process_source":c.BASE_OWNED_PROCESS_REF,
        "cleanup_producer_source":c.CLEANUP_PRODUCER_REF,
        "python_binary":c.PINNED_PYTHON_REF}
    assert c.expected_source_provenance(refs)==namespace["source_author_provenance"](refs)
check("C6 fixed provenance equals O4 pure extracted policy on actual tuple",o4_cross_contract)

print(json.dumps({"status":"PASS","checks":checks,"real_winapi_calls":0,
                  "process_starts":0,"canonical_writes":0},ensure_ascii=False,indent=2))
