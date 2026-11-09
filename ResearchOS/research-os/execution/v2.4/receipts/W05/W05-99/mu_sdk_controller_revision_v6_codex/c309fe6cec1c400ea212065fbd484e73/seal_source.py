"""One-shot metadata seal for the unexecuted C6 Source proposal."""
from pathlib import Path
import difflib
import hashlib
import json
import os
import subprocess
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
C5=BASE/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc"
C5_REVIEW=BASE/"mu_sdk_controller_v5_independent_review_codex/ca1965e9f0b449b786c4e6925d7018fb"
O4=BASE/"mu_sdk_job_observer_revision_v4_codex/cbb82ea19cf84175baf61427251b983c"
GUARD=BASE/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9"
RUNNER=BASE/"mu_model_sdk_real_trial_v9_source_codex/8c135404809b41a5a795574699bd0249"
BASE_JOB=BASE/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"

def pin(path):
    path=Path(path).resolve()
    raw=path.read_bytes()
    return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def write(name,raw):
    path=HERE/name
    with path.open("xb") as out:out.write(raw)
    return pin(path)

def jbytes(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode("utf-8")

def jwrite(name,value):
    return write(name,jbytes(value))

def diff(a,b,old,new):
    return "".join(difflib.unified_diff(
        a.decode("utf-8").splitlines(keepends=True),
        b.decode("utf-8").splitlines(keepends=True),
        fromfile=old,tofile=new)).encode("utf-8")

assert HERE.name=="c309fe6cec1c400ea212065fbd484e73"
assert all(not (HERE/name).exists() for name in (
    "manifest.json","handoff.json","source-pins.json","pure-controls.stdout.raw"))

for name in ("canonical_transactions.py","owned_job_hooks.py","phase_worker.py",
             "job_deadline_watchdog.py","job_probe_worker.py"):
    assert (HERE/name).read_bytes()==(C5/name).read_bytes(),name

for name in ("controller.py","held_job_cleanup_producer.py","pure_controls.py"):
    compile((HERE/name).read_bytes(),str(HERE/name),"exec")

sources={
    "controller":pin(HERE/"controller.py"),
    "cleanup_producer":pin(HERE/"held_job_cleanup_producer.py"),
    "observer_o4":pin(O4/"mu_sdk_job_observer.v4.proposed.py"),
    "source_guard":pin(GUARD/"source_read_guard.py"),
    "canonical_transactions":pin(HERE/"canonical_transactions.py"),
    "owned_job_hooks":pin(HERE/"owned_job_hooks.py"),
    "phase_worker":pin(HERE/"phase_worker.py"),
    "job_watchdog":pin(HERE/"job_deadline_watchdog.py"),
    "job_probe_worker":pin(HERE/"job_probe_worker.py"),
    "runner_v9":pin(RUNNER/"mu_sdk_trial.v9.proposed.py"),
    "base_owned_process":pin(BASE_JOB),
    "python_binary":pin(sys.executable)}
inputs={
    "c5_handoff":pin(C5/"handoff.json"),
    "c5_manifest":pin(C5/"manifest.json"),
    "c5_independent_review":pin(C5_REVIEW/"independent-source-review.json"),
    "o4_handoff":pin(O4/"handoff.json"),
    "o4_manifest":pin(O4/"manifest.json"),
    "guard_v2_handoff":pin(GUARD/"HANDOFF.md")}

assert sources["cleanup_producer"]["sha256"]=="17ebea83cedcb443b5e5c3669eb9d9d7178b376c3d90557e008aaf3965e58cee"
assert sources["observer_o4"]["sha256"]=="15495afc9b17b2e1a4e54a7f4fbace2fc4f8c5d00a2897dcc939892eb5045011"

source_pins=jwrite("source-pins.json",{
    "schema":"researchos.mu-sdk-controller-c6-source-pins.v1",
    "sources":sources,"inputs":inputs,
    "actual_process_or_provider_execution":False})

old=(C5/"controller.py").read_bytes()
new=(HERE/"controller.py").read_bytes()
forward=write("controller.forward.diff",diff(old,new,"C5/controller.py","C6/controller.py"))
inverse=write("controller.inverse.diff",diff(new,old,"C6/controller.py","C5/controller.py"))
new_producer=(HERE/"held_job_cleanup_producer.py").read_bytes()
producer_forward=write("cleanup-producer.forward.diff",
                       diff(b"",new_producer,"/dev/null","C6/held_job_cleanup_producer.py"))
producer_inverse=write("cleanup-producer.inverse.diff",
                       diff(new_producer,b"","C6/held_job_cleanup_producer.py","/dev/null"))

argv=[sys.executable,str(HERE/"pure_controls.py")]
completed=subprocess.run(argv,cwd=str(HERE),capture_output=True,check=False,
                         env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
stdout=write("pure-controls.stdout.raw",completed.stdout)
stderr=write("pure-controls.stderr.raw",completed.stderr)
tool_io=jwrite("pure-controls.original-tool-io.json",{
    "schema":"researchos.mu-sdk-controller-c6-pure-tool-io.v1",
    "argv":argv,"cwd":str(HERE),"exit_code":completed.returncode,
    "stdout_ref":stdout,"stderr_ref":stderr,
    "execution_class":"FAKE_KERNEL_ONLY_NO_NATIVE_PROCESS_OR_PROVIDER"})
assert completed.returncode==0 and completed.stderr==b"",completed.stderr
controls=json.loads(completed.stdout)
assert controls["status"]=="PASS" and len(controls["checks"])==7
assert controls["real_winapi_calls"]==0 and controls["canonical_writes"]==0

first_failure=jwrite("author-control-first-failure.json",{
    "schema":"researchos.mu-sdk-controller-c6-author-control-failure.v1",
    "origin":"first direct pure_controls.py invocation before fake owner fixture correction",
    "observed_exit_code":1,
    "observed_error":"RuntimeError: Root must pass the current process-resident Source owner explicitly",
    "reason":"test fixture constructed ResidentSourceOwner directly rather than using get_resident_source_owner",
    "correction":"fixture uses the process-resident owner; seven current controls pass",
    "raw_original_stdout_stderr_capture":False,
    "capture_gap":"First failing tool result was displayed in chat but not written as raw file at invocation time. This record transcribes the observed error; it is not represented as raw original I/O.",
    "native_or_provider_execution":False})

report=write("report.md",("""# C6 Source proposal

This immutable packet addresses C5 independent review findings R01 and R02.
It is Source-only and has not performed Windows process, provider, SQL or
canonical execution.

R01: C6 checks the exact 11-role Source author provenance against constants at
the pre-import gate and again under SourceReadGuard in the before-resume callback.
O4 independently checks the same tuple and excludes Root, w05 and live authors.
The generated O4 nonauthor receipt has its actor checked separately.

R02: C6 holds duplicate handles for the actual assigned Job and primary process,
plus PID and creation time captured before ResumeThread. Reconciliation accepts
no caller callback. The held producer reads current Job active count and primary
signaled state; C6 checks fresh bounded call time and exact run, owner, Job
binding, PID and creation identity. A failed or mismatched observation retains
the Source guard and resident owner. A failed duplicate close remains retriable.

The seven pure controls use a fake kernel. They include stale/future and
identity-forgery rejection. They do not prove actual WinAPI behavior or parent
process survival. Actual launch, qualification, provider traffic and formal
acceptance remain outside this Source packet.
""").encode("utf-8"))

members=[pin(path) for path in sorted(HERE.iterdir(),key=lambda p:p.name)
         if path.is_file() and path.name not in ("manifest.json","handoff.json")]
manifest=jwrite("manifest.json",{
    "schema":"researchos.mu-sdk-controller-c6-source-manifest.v1",
    "actor":"codex:/root/live_resource_lookup",
    "decision":"SOURCE_PROPOSED_UNEXECUTED",
    "directory":str(HERE),
    "derived_from_c5":inputs["c5_manifest"],
    "c5_independent_review":inputs["c5_independent_review"],
    "o4_source_package":inputs["o4_handoff"],
    "members":members,
    "native_calls":0,"provider_calls":0,"canonical_writes":0})
handoff=jwrite("handoff.json",{
    "schema":"researchos.mu-sdk-controller-c6-source-handoff.v1",
    "actor":"codex:/root/live_resource_lookup",
    "decision":"SOURCE_PROPOSED_UNEXECUTED",
    "controller_source_ref":sources["controller"],
    "cleanup_producer_source_ref":sources["cleanup_producer"],
    "observer_o4_source_ref":sources["observer_o4"],
    "manifest_ref":manifest,
    "source_pins_ref":source_pins,
    "forward_diff_ref":forward,"inverse_diff_ref":inverse,
    "producer_forward_diff_ref":producer_forward,
    "producer_inverse_diff_ref":producer_inverse,
    "pure_controls_original_tool_io_ref":tool_io,
    "pure_controls_checks":controls["checks"],
    "first_author_control_failure_ref":first_failure,
    "report_ref":report,
    "formal_acceptance":False,
    "open":["Independent C6+O4 exact tuple Source review",
            "Root same-PID adoption and real held-Job cleanup lifecycle verification",
            "Trusted Host and provider integration remain separate"]})
print(jbytes({"handoff_ref":handoff,"manifest_ref":manifest,
              "source_ref":sources["controller"],"controls":controls}).decode("utf-8"))
